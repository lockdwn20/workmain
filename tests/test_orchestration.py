"""
WorkmAIn Orchestration Tests
test_orchestration.py v1.0
20260625

Tests for Phase 13 Sprint 3 deliverables: WorkmAInDaemon socket dispatch,
Block Kit ConfirmationGate, T2/T3 meeting triggers, T4 random check-in,
T6 correction re-presentation, and T5 session persistence.

All Slack API and Ollama calls mocked. No live network calls.
No DB writes for unit tests — DB-touching tests use the db_session fixture.

Version History:
- v1.0: Phase 13 Sprint 3 Gate 7 — initial 42-test suite
"""

import json
import os
import tempfile
import time
import unittest
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_daemon(dm_channel='D_TEST'):
    """Build a WorkmAInDaemon with a mock socket client (no real Slack)."""
    from workmain.daemon.daemon import WorkmAInDaemon
    from workmain.integrations.slack.slack_eod import SlackEodManager
    from workmain.orchestration.confirmation_gate import ConfirmationGate

    daemon = WorkmAInDaemon.__new__(WorkmAInDaemon)
    daemon._dm_channel = dm_channel
    daemon._pending = {}
    daemon._gate = ConfirmationGate()
    daemon._intent_parser = None
    daemon._socket_client = MagicMock()
    daemon._eod_manager = MagicMock(spec=SlackEodManager)
    daemon._eod_manager.has_session.return_value = False
    daemon._eod_manager._sessions = {}
    return daemon


def _make_socket_client(message_handler, block_action_handler):
    """Build a WorkmAInSocketClient with a real (non-network) instance."""
    from workmain.integrations.slack.socket_client import WorkmAInSocketClient
    client = WorkmAInSocketClient.__new__(WorkmAInSocketClient)
    client._message_handler = message_handler
    client._block_action_handler = block_action_handler
    client._seen_ts = set()
    client._seen_ts_times = {}
    client._web_client = MagicMock()
    client._socket_client = MagicMock()
    return client


def _dm_event(ts='1000000001.000000', text='log 1h for testing', user='U_OP',
              channel='D_TEST', channel_type='im'):
    return {
        'type': 'message',
        'ts': ts,
        'text': text,
        'user': user,
        'channel': channel,
        'channel_type': channel_type,
    }


def _block_action_payload(action_id, value, action_ts='2000000001.000000'):
    return {
        'type': 'block_actions',
        'actions': [
            {
                'action_id': action_id,
                'action_ts': action_ts,
                'value': value,
            }
        ],
    }


# ---------------------------------------------------------------------------
# Group 1 — WorkmAInDaemon socket event dispatch
# ---------------------------------------------------------------------------

class TestDaemonSocketDispatch(unittest.TestCase):

    def test_message_event_routed_to_handle_message(self):
        """DM message event is dispatched to message_handler in background thread."""
        handler = MagicMock()
        client = _make_socket_client(handler, MagicMock())
        event = _dm_event()
        req = MagicMock()
        req.type = 'events_api'
        req.envelope_id = 'env1'
        req.payload = {'event': event}
        client._handle_request(client._socket_client, req)
        time.sleep(0.05)
        handler.assert_called_once_with(event)

    def test_non_dm_message_event_ignored(self):
        """Messages from non-IM channels are not dispatched."""
        handler = MagicMock()
        client = _make_socket_client(handler, MagicMock())
        event = _dm_event(channel_type='channel')
        req = MagicMock()
        req.type = 'events_api'
        req.envelope_id = 'env2'
        req.payload = {'event': event}
        client._handle_request(client._socket_client, req)
        time.sleep(0.05)
        handler.assert_not_called()

    def test_bot_message_subtype_ignored(self):
        """Messages with a subtype (bot echoes, etc.) are not dispatched."""
        handler = MagicMock()
        client = _make_socket_client(handler, MagicMock())
        event = _dm_event()
        event['subtype'] = 'bot_message'
        req = MagicMock()
        req.type = 'events_api'
        req.envelope_id = 'env3'
        req.payload = {'event': event}
        client._handle_request(client._socket_client, req)
        time.sleep(0.05)
        handler.assert_not_called()

    def test_block_actions_approve_routes_to_executor(self):
        """wm_approve block action payload reaches handle_block_action."""
        daemon = _make_daemon()
        action_dict = {'action': 'create_note', 'content': 'test'}
        payload = _block_action_payload('wm_approve', json.dumps(action_dict))

        with patch.object(daemon, '_execute_action') as mock_exec, \
             patch.object(daemon, '_maybe_post_correction_summary'):
            # Simulate block_actions directly (not via socket) to stay synchronous
            from workmain.orchestration.action_executor import ActionResult
            mock_result = ActionResult(success=True, message='Done.')
            with patch('workmain.daemon.daemon.get_db') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value.get_session.return_value = mock_session
                with patch('workmain.orchestration.action_executor.ActionExecutor') as mock_ae:
                    mock_ae.return_value.execute.return_value = mock_result
                    daemon.handle_block_action(payload)
            daemon._socket_client.post_message.assert_called()

    def test_block_actions_reject_sends_rejection_message(self):
        """wm_reject block action posts 'Action rejected.' DM."""
        daemon = _make_daemon()
        payload = _block_action_payload('wm_reject', 'reject')
        daemon.handle_block_action(payload)
        daemon._socket_client.post_message.assert_called_once_with('D_TEST', 'Action rejected.')

    def test_acknowledgment_sent_before_dispatch(self):
        """Socket ack (send_socket_mode_response) is called before handler thread."""
        ack_order = []
        def track_ack(*a, **kw):
            ack_order.append('ack')
        def track_handler(*a, **kw):
            ack_order.append('handler')

        mock_socket = MagicMock()
        mock_socket.send_socket_mode_response.side_effect = track_ack
        client = _make_socket_client(track_handler, MagicMock())
        client._socket_client = mock_socket
        event = _dm_event(ts='3000000001.000000')
        req = MagicMock()
        req.type = 'events_api'
        req.envelope_id = 'env4'
        req.payload = {'event': event}
        client._handle_request(mock_socket, req)
        time.sleep(0.05)
        self.assertEqual(ack_order[0], 'ack')

    def test_dm_channel_captured_from_inbound_message(self):
        """handle_message updates _dm_channel from the inbound event channel."""
        daemon = _make_daemon(dm_channel=None)
        event = _dm_event(channel='D_DYNAMIC', text='hello')
        with patch.object(daemon, '_dispatch_message'):
            daemon.handle_message(event)
        self.assertEqual(daemon._dm_channel, 'D_DYNAMIC')

    def test_dm_channel_resolved_proactively_at_startup(self):
        """_resolve_dm_channel calls conversations_open and returns channel id."""
        from workmain.daemon.daemon import WorkmAInDaemon
        daemon = WorkmAInDaemon.__new__(WorkmAInDaemon)
        mock_web = MagicMock()
        mock_web.conversations_open.return_value = {'channel': {'id': 'D_PROACTIVE'}}
        with patch('workmain.daemon.daemon.WebClient', return_value=mock_web):
            result = daemon._resolve_dm_channel('xoxb-bot', 'U_OPERATOR')
        self.assertEqual(result, 'D_PROACTIVE')
        mock_web.conversations_open.assert_called_once_with(users=['U_OPERATOR'])

    def test_duplicate_event_ts_discarded(self):
        """Second message with identical ts is not dispatched."""
        handler = MagicMock()
        client = _make_socket_client(handler, MagicMock())
        event = _dm_event(ts='5000000001.000000')
        for _ in range(2):
            req = MagicMock()
            req.type = 'events_api'
            req.envelope_id = f'env_{_}'
            req.payload = {'event': event}
            client._handle_request(client._socket_client, req)
        time.sleep(0.05)
        handler.assert_called_once()

    def test_seen_ts_evicted_after_60_seconds(self):
        """_evict_old_entries removes entries older than 60 s."""
        client = _make_socket_client(MagicMock(), MagicMock())
        ts = '6000000001.000000'
        client._seen_ts.add(ts)
        client._seen_ts_times[ts] = time.monotonic() - 61.0
        client._evict_old_entries()
        self.assertNotIn(ts, client._seen_ts)
        self.assertNotIn(ts, client._seen_ts_times)


# ---------------------------------------------------------------------------
# Group 2 — Block Kit payload (ConfirmationGate)
# ---------------------------------------------------------------------------

class TestConfirmationGateBlocks(unittest.TestCase):

    def setUp(self):
        from workmain.orchestration.confirmation_gate import ConfirmationGate
        self.gate = ConfirmationGate()

    def test_format_blocks_returns_two_block_list(self):
        action = {'action': 'create_note', 'content': 'test note'}
        blocks = self.gate.format_blocks(action)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]['type'], 'section')
        self.assertEqual(blocks[1]['type'], 'actions')

    def test_format_blocks_approve_action_id(self):
        action = {'action': 'create_note', 'content': 'test'}
        blocks = self.gate.format_blocks(action)
        elements = blocks[1]['elements']
        approve = next(e for e in elements if e.get('action_id') == 'wm_approve')
        self.assertEqual(approve['style'], 'primary')

    def test_format_blocks_reject_action_id(self):
        action = {'action': 'create_note', 'content': 'test'}
        blocks = self.gate.format_blocks(action)
        elements = blocks[1]['elements']
        reject = next(e for e in elements if e.get('action_id') == 'wm_reject')
        self.assertEqual(reject['style'], 'danger')

    def test_format_blocks_action_serialized_in_value(self):
        action = {'action': 'create_note', 'content': 'hello'}
        blocks = self.gate.format_blocks(action)
        elements = blocks[1]['elements']
        approve = next(e for e in elements if e.get('action_id') == 'wm_approve')
        deserialized = json.loads(approve['value'])
        self.assertEqual(deserialized, action)

    def test_format_blocks_truncates_long_description(self):
        long_content = 'x' * 200
        action = {'action': 'create_note', 'content': long_content}
        blocks = self.gate.format_blocks(action)
        section_text = blocks[0]['text']['text']
        # format_prompt truncates at 80 chars for create_note
        self.assertNotIn('(yes/no)', section_text)
        self.assertLess(len(section_text), 250)

    def test_format_prompt_still_works(self):
        action = {'action': 'create_note', 'content': 'still works'}
        prompt = self.gate.format_prompt(action)
        self.assertIn('(yes/no)', prompt)
        self.assertIn('still works', prompt)


# ---------------------------------------------------------------------------
# Group 3 — Meeting triggers (mock MeetingsRepository + _scheduler)
# ---------------------------------------------------------------------------

def _make_meeting(mid, title, start_offset_min, end_offset_min=None,
                  is_cancelled=False):
    """Return a mock Meeting-like object with datetime start_time/end_time."""
    now = datetime.now()
    m = MagicMock()
    m.id = mid
    m.title = title
    m.is_cancelled = is_cancelled
    m.start_time = now + timedelta(minutes=start_offset_min)
    m.end_time = (
        now + timedelta(minutes=end_offset_min)
        if end_offset_min is not None else None
    )
    m.duration_hours = abs(end_offset_min - start_offset_min) / 60.0 if end_offset_min else 0.0
    return m


class TestMeetingTriggers(unittest.TestCase):

    def _run_schedule(self, meetings):
        """Run _schedule_today_meeting_triggers with mocked DB and scheduler."""
        import workmain.daemon.scheduler as sched_mod
        mock_scheduler = MagicMock()
        daemon = MagicMock()
        with patch.object(sched_mod, '_scheduler', mock_scheduler), \
             patch('workmain.database.connection.get_db') as mock_db, \
             patch('workmain.database.repositories.meetings_repo.MeetingsRepository') as mock_repo_cls:
            mock_session = MagicMock()
            mock_db.return_value.get_session.return_value = mock_session
            mock_repo_cls.return_value.get_by_date.return_value = meetings
            sched_mod._schedule_today_meeting_triggers(daemon)
        return mock_scheduler

    def test_t2_job_scheduled_for_future_meeting(self):
        meetings = [_make_meeting(1, 'Stand-up', start_offset_min=30, end_offset_min=60)]
        sched = self._run_schedule(meetings)
        job_ids = [c.kwargs.get('id') or c[1].get('id') for c in sched.add_job.call_args_list]
        self.assertTrue(any('t2_1' in str(jid) for jid in job_ids))

    def test_t2_job_not_scheduled_for_past_meeting(self):
        meetings = [_make_meeting(2, 'Old', start_offset_min=-60, end_offset_min=-30)]
        sched = self._run_schedule(meetings)
        job_ids = [str(c) for c in sched.add_job.call_args_list]
        self.assertFalse(any('t2_2' in j for j in job_ids))

    def test_t3_job_scheduled_using_end_time(self):
        meetings = [_make_meeting(3, 'Design Review', start_offset_min=10, end_offset_min=70)]
        sched = self._run_schedule(meetings)
        job_ids = [str(c) for c in sched.add_job.call_args_list]
        self.assertTrue(any('t3_3' in j for j in job_ids))

    def test_t3_job_not_scheduled_if_end_time_none(self):
        meetings = [_make_meeting(4, 'No End', start_offset_min=10, end_offset_min=None)]
        sched = self._run_schedule(meetings)
        job_ids = [str(c) for c in sched.add_job.call_args_list]
        self.assertFalse(any('t3_4' in j for j in job_ids))

    def test_cancelled_meeting_skipped(self):
        meetings = [_make_meeting(5, 'Cancelled', start_offset_min=30, is_cancelled=True)]
        sched = self._run_schedule(meetings)
        sched.add_job.assert_not_called()

    def test_schedule_idempotent_on_double_call(self):
        """replace_existing=True means a second call re-registers without error."""
        meetings = [_make_meeting(6, 'Sprint', start_offset_min=20, end_offset_min=80)]
        import workmain.daemon.scheduler as sched_mod
        mock_scheduler = MagicMock()
        daemon = MagicMock()
        with patch.object(sched_mod, '_scheduler', mock_scheduler), \
             patch('workmain.database.connection.get_db') as mock_db, \
             patch('workmain.database.repositories.meetings_repo.MeetingsRepository') as mock_repo_cls:
            mock_session = MagicMock()
            mock_db.return_value.get_session.return_value = mock_session
            mock_repo_cls.return_value.get_by_date.return_value = meetings
            sched_mod._schedule_today_meeting_triggers(daemon)
            sched_mod._schedule_today_meeting_triggers(daemon)
        call_count = mock_scheduler.add_job.call_count
        # Two calls, two meetings each = 4 add_job calls total; no exception
        self.assertEqual(call_count, 4)

    def test_meeting_triggers_rescheduled_on_15min_rescan(self):
        """register_all_jobs wires an IntervalTrigger for rescan."""
        import workmain.daemon.scheduler as sched_mod
        from apscheduler.triggers.interval import IntervalTrigger
        mock_scheduler = MagicMock()
        daemon = MagicMock()
        with patch.object(sched_mod, '_scheduler', mock_scheduler), \
             patch('workmain.daemon.scheduler._schedule_today_meeting_triggers'), \
             patch('workmain.daemon.scheduler._reschedule_t4_checkin'):
            sched_mod.register_all_jobs(daemon)
        job_ids = [c.kwargs.get('id', '') for c in mock_scheduler.add_job.call_args_list]
        self.assertIn('t2t3_interval_rescan', job_ids)


# ---------------------------------------------------------------------------
# Group 4 — T4 check-in
# ---------------------------------------------------------------------------

class TestT4Checkin(unittest.TestCase):

    def _run_reschedule(self, now_dt, non_working=None, delay_minutes=30):
        """Call _reschedule_t4_checkin with controlled datetime.now() and delay."""
        import workmain.daemon.scheduler as sched_mod
        mock_scheduler = MagicMock()
        daemon = MagicMock()
        nwd = non_working or set()
        with patch.object(sched_mod, '_scheduler', mock_scheduler), \
             patch('workmain.daemon.scheduler._load_non_working_days', return_value=nwd), \
             patch('workmain.daemon.scheduler.random') as mock_rand, \
             patch('workmain.daemon.scheduler.datetime') as mock_dt:
            mock_rand.randint.return_value = delay_minutes
            mock_dt.now.return_value = now_dt
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            sched_mod._reschedule_t4_checkin(daemon)
        return mock_scheduler

    def test_t4_suppressed_before_0900(self):
        """fire_at < 09:00 → no job scheduled (08:00 + 30 min = 08:30)."""
        now = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        sched = self._run_reschedule(now, delay_minutes=30)
        sched.add_job.assert_not_called()

    def test_t4_suppressed_after_1800(self):
        """fire_at >= 18:00 → no job scheduled (17:31 + 30 min = 18:01)."""
        now = datetime.now().replace(hour=17, minute=31, second=0, microsecond=0)
        sched = self._run_reschedule(now, delay_minutes=30)
        sched.add_job.assert_not_called()

    def test_t4_suppressed_on_weekend(self):
        """Saturday/Sunday → no job scheduled."""
        today = date.today()
        days_until_sat = (5 - today.weekday()) % 7
        saturday = today + timedelta(days=days_until_sat if days_until_sat > 0 else 7)
        now = datetime(saturday.year, saturday.month, saturday.day, 10, 0)
        sched = self._run_reschedule(now, delay_minutes=30)
        sched.add_job.assert_not_called()

    def test_t4_suppressed_on_non_working_day(self):
        """Day in non_working_days set → no job scheduled."""
        import workmain.daemon.scheduler as sched_mod
        mock_scheduler = MagicMock()
        daemon = MagicMock()
        today = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        nwd = {today.date().isoformat()}
        with patch.object(sched_mod, '_scheduler', mock_scheduler), \
             patch('workmain.daemon.scheduler._load_non_working_days', return_value=nwd), \
             patch('workmain.daemon.scheduler.datetime') as mock_dt:
            mock_dt.now.return_value = today
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            sched_mod._reschedule_t4_checkin(daemon)
        mock_scheduler.add_job.assert_not_called()

    def test_t4_suppressed_during_active_t5_session(self):
        """_send_t4_checkin does not post DM if T5 EOD session is active."""
        import workmain.daemon.scheduler as sched_mod
        daemon = MagicMock()
        daemon._eod_manager._sessions = {'U_OP': MagicMock()}
        daemon._eod_manager.has_session.return_value = True
        with patch('workmain.daemon.scheduler._reschedule_t4_checkin') as mock_resched:
            sched_mod._send_t4_checkin(daemon)
        daemon.post_message.assert_not_called()
        mock_resched.assert_called_once_with(daemon)

    def test_t4_scheduled_in_30_to_120_min_window(self):
        """fire_at is between 30 and 120 minutes from now when window is valid."""
        import workmain.daemon.scheduler as sched_mod
        mock_scheduler = MagicMock()
        daemon = MagicMock()
        now = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        with patch.object(sched_mod, '_scheduler', mock_scheduler), \
             patch('workmain.daemon.scheduler._load_non_working_days', return_value=set()), \
             patch('workmain.daemon.scheduler.datetime') as mock_dt, \
             patch('workmain.daemon.scheduler.random') as mock_rand:
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            mock_rand.randint.return_value = 60
            sched_mod._reschedule_t4_checkin(daemon)
        mock_scheduler.add_job.assert_called_once()
        mock_rand.randint.assert_called_once_with(30, 120)

    def test_t4_rescheduled_when_t2_fires(self):
        """_send_t2 calls _reschedule_t4_checkin after posting."""
        import workmain.daemon.scheduler as sched_mod
        daemon = MagicMock()
        meeting = MagicMock()
        meeting.title = 'Stand-up'
        meeting.duration_hours = 0.5
        with patch('workmain.database.connection.get_db') as mock_db, \
             patch('workmain.database.repositories.meetings_repo.MeetingsRepository') as mock_repo_cls, \
             patch('workmain.daemon.scheduler._reschedule_t4_checkin') as mock_resched:
            mock_session = MagicMock()
            mock_db.return_value.get_session.return_value = mock_session
            mock_repo_cls.return_value.get_by_id.return_value = meeting
            sched_mod._send_t2(1, daemon)
        mock_resched.assert_called_once_with(daemon)

    def test_t4_rescheduled_when_t3_fires(self):
        """_send_t3 calls _reschedule_t4_checkin after posting."""
        import workmain.daemon.scheduler as sched_mod
        daemon = MagicMock()
        meeting = MagicMock()
        meeting.title = 'Stand-up'
        with patch('workmain.database.connection.get_db') as mock_db, \
             patch('workmain.database.repositories.meetings_repo.MeetingsRepository') as mock_repo_cls, \
             patch('workmain.daemon.scheduler._reschedule_t4_checkin') as mock_resched:
            mock_session = MagicMock()
            mock_db.return_value.get_session.return_value = mock_session
            mock_repo_cls.return_value.get_by_id.return_value = meeting
            sched_mod._send_t3(1, daemon)
        mock_resched.assert_called_once_with(daemon)

    def test_t4_rescheduled_after_firing(self):
        """_send_t4_checkin reschedules the next window after posting the DM."""
        import workmain.daemon.scheduler as sched_mod
        daemon = MagicMock()
        daemon._eod_manager._sessions = {}
        daemon._eod_manager.has_session.return_value = False
        with patch('workmain.daemon.scheduler._reschedule_t4_checkin') as mock_resched:
            sched_mod._send_t4_checkin(daemon)
        daemon.post_message.assert_called_once_with('What are you working on right now?')
        mock_resched.assert_called_once_with(daemon)


# ---------------------------------------------------------------------------
# Group 5 — T6 correction re-presentation
# ---------------------------------------------------------------------------

@dataclass
class _FakeResult:
    success: bool
    message: str
    entity_id: Optional[int] = None
    error: Optional[str] = None


class TestT6CorrectionRepresentation(unittest.TestCase):

    def _daemon(self):
        return _make_daemon()

    def test_t6_summary_posted_after_correct_report(self):
        """Successful correct_report posts Block Kit summary with report fields."""
        daemon = self._daemon()
        result = _FakeResult(success=True, message='Done.', entity_id=99)
        action = {'action': 'correct_report', 'correction': 'Fix typo'}

        mock_report = MagicMock()
        mock_report.report_date = date(2026, 6, 25)
        mock_report.status = 'draft'
        mock_report.correction_note = 'Fix typo'

        with patch('workmain.daemon.daemon.get_db') as mock_db, \
             patch('workmain.database.repositories.reports_repo.ReportsRepository') as mock_repo_cls:
            mock_session = MagicMock()
            mock_db.return_value.get_session.return_value = mock_session
            mock_repo_cls.return_value.get_by_id.return_value = mock_report
            daemon._maybe_post_correction_summary(result, action)

        daemon._socket_client.post_blocks.assert_called_once()
        blocks = daemon._socket_client.post_blocks.call_args[0][1]
        text_content = str(blocks)
        self.assertIn('2026-06-25', text_content)

    def test_t6_summary_posted_after_write_correction_note(self):
        """write_correction_note action also triggers T6 re-presentation."""
        daemon = self._daemon()
        result = _FakeResult(success=True, message='Done.', entity_id=42)
        action = {'action': 'write_correction_note', 'note': 'Clarify section'}

        mock_report = MagicMock()
        mock_report.report_date = date(2026, 6, 25)
        mock_report.status = 'confirmed'
        mock_report.correction_note = 'Clarify section'

        with patch('workmain.daemon.daemon.get_db') as mock_db, \
             patch('workmain.database.repositories.reports_repo.ReportsRepository') as mock_repo_cls:
            mock_session = MagicMock()
            mock_db.return_value.get_session.return_value = mock_session
            mock_repo_cls.return_value.get_by_id.return_value = mock_report
            daemon._maybe_post_correction_summary(result, action)

        daemon._socket_client.post_blocks.assert_called_once()

    def test_t6_fallback_on_missing_report(self):
        """Falls back to plain text when entity_id resolves to None."""
        daemon = self._daemon()
        result = _FakeResult(success=True, message='Done.', entity_id=999)
        action = {'action': 'correct_report'}

        with patch('workmain.daemon.daemon.get_db') as mock_db, \
             patch('workmain.database.repositories.reports_repo.ReportsRepository') as mock_repo_cls:
            mock_session = MagicMock()
            mock_db.return_value.get_session.return_value = mock_session
            mock_repo_cls.return_value.get_by_id.return_value = None
            daemon._maybe_post_correction_summary(result, action)

        daemon._socket_client.post_message.assert_called_once_with('D_TEST', 'Correction applied.')

    def test_t6_not_posted_for_non_correction_actions(self):
        """create_time_entry and similar actions do not trigger T6."""
        daemon = self._daemon()
        result = _FakeResult(success=True, message='Logged.', entity_id=1)
        action = {'action': 'create_time_entry', 'duration_minutes': 60}
        daemon._maybe_post_correction_summary(result, action)
        daemon._socket_client.post_blocks.assert_not_called()
        daemon._socket_client.post_message.assert_not_called()

    def test_t6_not_posted_on_failed_result(self):
        """T6 is suppressed when result.success is False."""
        daemon = self._daemon()
        result = _FakeResult(success=False, message='Error.', entity_id=5)
        action = {'action': 'correct_report'}
        daemon._maybe_post_correction_summary(result, action)
        daemon._socket_client.post_blocks.assert_not_called()
        daemon._socket_client.post_message.assert_not_called()


# ---------------------------------------------------------------------------
# Group 6 — T5 session persistence
# ---------------------------------------------------------------------------

class TestT5SessionPersistence(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._state_dir = self._tmpdir.name
        # Patch _SESSION_PATH to use temp dir
        from workmain.integrations.slack.slack_eod import SlackEodSession
        self._original_path = SlackEodSession._SESSION_PATH
        SlackEodSession._SESSION_PATH = (
            Path(self._state_dir) / 'daemon' / 'eod_session.json'
        )

    def tearDown(self):
        from workmain.integrations.slack.slack_eod import SlackEodSession
        SlackEodSession._SESSION_PATH = self._original_path
        self._tmpdir.cleanup()

    def _make_session(self, user_id='U_OP', channel_id='D_TEST',
                      step_idx=2, completed=None, skipped=None):
        from workmain.integrations.slack.slack_eod import SlackEodSession
        session = SlackEodSession(
            user_id=user_id,
            channel_id=channel_id,
            target_date=date(2099, 1, 1),
            steps=[
                {'key': 'note_review', 'num': 1, 'desc': 'Note review'},
                {'key': 'task_match', 'num': 2, 'desc': 'Task match'},
                {'key': 'time_review', 'num': 3, 'desc': 'Time review'},
            ],
            current_step_idx=step_idx,
            paused=False,
            completed=completed or ['note_review', 'task_match'],
            skipped=skipped or [],
        )
        return session

    def test_session_save_creates_file(self):
        session = self._make_session()
        session.save()
        self.assertTrue(session._SESSION_PATH.exists())
        data = json.loads(session._SESSION_PATH.read_text())
        self.assertEqual(data['user_id'], 'U_OP')
        self.assertEqual(data['channel_id'], 'D_TEST')
        self.assertEqual(data['current_step_idx'], 2)
        self.assertEqual(data['completed'], ['note_review', 'task_match'])

    def test_session_save_sets_permissions_600(self):
        session = self._make_session()
        session.save()
        import stat
        mode = oct(os.stat(session._SESSION_PATH).st_mode)
        self.assertTrue(mode.endswith('600'), f'Expected 600, got {mode}')

    def test_session_load_restores_correct_fields(self):
        from workmain.integrations.slack.slack_eod import SlackEodSession
        session = self._make_session(step_idx=1, completed=['note_review'])
        session.save()
        with patch('workmain.workflows.eod_workflow.get_step_sequence',
                   return_value=session.steps):
            restored = SlackEodSession.load()
        self.assertIsNotNone(restored)
        self.assertEqual(restored.user_id, 'U_OP')
        self.assertEqual(restored.current_step_idx, 1)
        self.assertEqual(restored.completed, ['note_review'])
        self.assertIsInstance(restored.completed, list)
        self.assertFalse(restored.paused)
        self.assertIsNone(restored.pending_action)

    def test_session_load_returns_none_if_absent(self):
        from workmain.integrations.slack.slack_eod import SlackEodSession
        result = SlackEodSession.load()
        self.assertIsNone(result)

    def test_session_load_returns_none_if_stale(self):
        from workmain.integrations.slack.slack_eod import SlackEodSession
        session = self._make_session()
        # Write with started_at > 24h ago
        session._SESSION_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        stale_time = (datetime.now() - timedelta(hours=25)).isoformat()
        payload = {
            'user_id': session.user_id,
            'channel_id': session.channel_id,
            'target_date': str(session.target_date),
            'current_step_idx': session.current_step_idx,
            'completed': session.completed,
            'skipped': session.skipped,
            'started_at': stale_time,
        }
        session._SESSION_PATH.write_text(json.dumps(payload))
        result = SlackEodSession.load()
        self.assertIsNone(result)
        self.assertFalse(session._SESSION_PATH.exists())

    def test_session_load_returns_none_on_corrupt_json(self):
        from workmain.integrations.slack.slack_eod import SlackEodSession
        session = self._make_session()
        session._SESSION_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        session._SESSION_PATH.write_text('not valid json {{{{')
        result = SlackEodSession.load()
        self.assertIsNone(result)
        self.assertFalse(session._SESSION_PATH.exists())

    def test_session_clear_deletes_file(self):
        from workmain.integrations.slack.slack_eod import SlackEodSession
        session = self._make_session()
        session.save()
        self.assertTrue(session._SESSION_PATH.exists())
        SlackEodSession.clear()
        self.assertFalse(session._SESSION_PATH.exists())

    def test_session_not_started_when_one_already_active(self):
        """handle_start_eod guard fires when session already in _sessions."""
        from workmain.integrations.slack.slack_eod import SlackEodManager, SlackEodSession
        mock_client = MagicMock()
        mock_daemon = MagicMock()
        manager = SlackEodManager(mock_client, mock_daemon)
        existing = self._make_session()
        manager._sessions['U_OP'] = existing
        manager.handle_start_eod('U_OP', 'D_TEST')
        # Should send the guard message, not start a new session
        mock_client.post_message.assert_called_once()
        msg = mock_client.post_message.call_args[0][1]
        self.assertIn('resume', msg.lower())
        # Session count unchanged
        self.assertEqual(len(manager._sessions), 1)


if __name__ == '__main__':
    unittest.main()
