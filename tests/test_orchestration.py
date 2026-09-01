"""
Tests for Phase 13 Sprint 3 deliverables: WorkmAInDaemon socket dispatch,
Block Kit ConfirmationGate, T2/T3 meeting triggers, T4 random check-in,
T6 correction re-presentation, and T5 session persistence.

All Slack API and Ollama calls mocked. No live network calls.
No DB writes for unit tests — DB-touching tests use the db_session fixture.
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

# Sentinel date: far future ensures no real DB/production data matches
SENTINEL_DATE = date(2099, 1, 1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_store(tmp_path=None):
    """A ConversationStore backed by a throwaway temp file."""
    from workmain.daemon.conversation_state import ConversationStore
    base = Path(tmp_path) if tmp_path else Path(tempfile.mkdtemp())
    return ConversationStore(path=base / 'daemon' / 'conversation_state.json')


def _make_daemon(dm_channel='D_TEST', store=None):
    """Build a WorkmAInDaemon with a mock socket client (no real Slack)."""
    from workmain.daemon.daemon import WorkmAInDaemon
    from workmain.integrations.slack.slack_eod import SlackEodManager
    from workmain.orchestration.confirmation_gate import ConfirmationGate

    daemon = WorkmAInDaemon.__new__(WorkmAInDaemon)
    daemon._dm_channel = dm_channel
    daemon._operator_user_id = 'U_OP'
    daemon._store = store or _make_store()
    daemon._gate = ConfirmationGate()
    daemon._intent_parser = None
    daemon._socket_client = MagicMock()
    daemon._eod_manager = MagicMock(spec=SlackEodManager)
    daemon._eod_manager.has_session.return_value = False
    daemon._eod_manager.has_any_session.return_value = False
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


def _block_action_payload(action_id, value, action_ts='2000000001.000000', user='U_OP'):
    payload = {
        'type': 'block_actions',
        'actions': [
            {
                'action_id': action_id,
                'action_ts': action_ts,
                'value': value,
            }
        ],
    }
    if user is not None:
        payload['user'] = {'id': user}
    return payload


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
        """wm_approve correlates by token and reaches _execute_action."""
        daemon = _make_daemon()
        action_dict = {'action': 'create_note', 'content': 'test'}
        pending = daemon._store.put_pending('U_OP', action_dict)
        payload = _block_action_payload('wm_approve', pending.action_id)

        with patch.object(daemon, '_execute_action') as mock_exec:
            daemon.handle_block_action(payload)
        mock_exec.assert_called_once_with(action_dict)

    def test_block_actions_reject_sends_rejection_message(self):
        """wm_reject with a matching token posts 'Action rejected.' and clears."""
        daemon = _make_daemon()
        pending = daemon._store.put_pending('U_OP', {'action': 'create_note', 'content': 'x'})
        payload = _block_action_payload('wm_reject', pending.action_id)
        daemon.handle_block_action(payload)
        daemon._socket_client.post_message.assert_called_once_with('D_TEST', 'Action rejected.')
        self.assertIsNone(daemon._store.take_pending('U_OP'))

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
        blocks = self.gate.format_blocks(action, 'ID1')
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]['type'], 'section')
        self.assertEqual(blocks[1]['type'], 'actions')

    def test_format_blocks_approve_action_id(self):
        action = {'action': 'create_note', 'content': 'test'}
        blocks = self.gate.format_blocks(action, 'ID1')
        elements = blocks[1]['elements']
        approve = next(e for e in elements if e.get('action_id') == 'wm_approve')
        self.assertEqual(approve['style'], 'primary')

    def test_format_blocks_reject_action_id(self):
        action = {'action': 'create_note', 'content': 'test'}
        blocks = self.gate.format_blocks(action, 'ID1')
        elements = blocks[1]['elements']
        reject = next(e for e in elements if e.get('action_id') == 'wm_reject')
        self.assertEqual(reject['style'], 'danger')

    def test_format_blocks_opaque_id_in_both_values(self):
        """Both button values carry the opaque correlation id — never the
        serialized action (delivers #102 AC3 early; deviations table)."""
        action = {'action': 'create_note', 'content': 'hello'}
        blocks = self.gate.format_blocks(action, 'ID-XYZ')
        elements = blocks[1]['elements']
        for e in elements:
            self.assertEqual(e['value'], 'ID-XYZ')

    def test_format_blocks_truncates_long_description(self):
        long_content = 'x' * 200
        action = {'action': 'create_note', 'content': long_content}
        blocks = self.gate.format_blocks(action, 'ID1')
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

    def _run_reschedule(self, now_dt, is_working_day=True, is_working_hours=True,
                        delay_minutes=30, t4_interval=(30, 120)):
        """Call _reschedule_t4_checkin with a mocked ScheduleService, controlled
        datetime.now(), and delay. Operations_Config_Correction_Sprint Gate 1
        §1.3 moved the weekend/non-working-day and working-hours checks (plus
        the T4 interval bounds) onto ScheduleService — mocked here rather than
        exercising its real logic, which has its own dedicated coverage in
        tests/test_schedule_service.py (Gate 7)."""
        import workmain.daemon.scheduler as sched_mod
        mock_scheduler = MagicMock()
        daemon = MagicMock()
        mock_service = MagicMock()
        mock_service.is_working_day.return_value = is_working_day
        mock_service.is_working_hours.return_value = is_working_hours
        mock_service.get_t4_interval.return_value = t4_interval
        with patch.object(sched_mod, '_scheduler', mock_scheduler), \
             patch('workmain.daemon.scheduler.get_db') as mock_get_db, \
             patch('workmain.daemon.scheduler.ScheduleService', return_value=mock_service), \
             patch('workmain.daemon.scheduler.random') as mock_rand, \
             patch('workmain.daemon.scheduler.datetime') as mock_dt:
            mock_get_db.return_value.get_session.return_value = MagicMock()
            mock_rand.randint.return_value = delay_minutes
            mock_dt.now.return_value = now_dt
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            sched_mod._reschedule_t4_checkin(daemon)
        return mock_scheduler, mock_service

    def test_t4_suppressed_before_0900(self):
        """is_working_hours(fire_at) returning False (e.g. fire_at before
        09:00) → no job scheduled."""
        now = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        sched, service = self._run_reschedule(now, is_working_hours=False, delay_minutes=30)
        sched.add_job.assert_not_called()

    def test_t4_suppressed_after_1800(self):
        """is_working_hours(fire_at) returning False (e.g. fire_at at or
        after 18:00) → no job scheduled."""
        now = datetime.now().replace(hour=17, minute=31, second=0, microsecond=0)
        sched, service = self._run_reschedule(now, is_working_hours=False, delay_minutes=30)
        sched.add_job.assert_not_called()

    def test_t4_suppressed_on_weekend(self):
        """is_working_day() returning False (e.g. Saturday/Sunday) → no job scheduled."""
        today = date.today()
        days_until_sat = (5 - today.weekday()) % 7
        saturday = today + timedelta(days=days_until_sat if days_until_sat > 0 else 7)
        now = datetime(saturday.year, saturday.month, saturday.day, 10, 0)
        sched, service = self._run_reschedule(now, is_working_day=False, delay_minutes=30)
        sched.add_job.assert_not_called()

    def test_t4_suppressed_on_non_working_day(self):
        """is_working_day() returning False (e.g. a schedule_exceptions
        holiday/timeoff range) → no job scheduled."""
        now = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        sched, service = self._run_reschedule(now, is_working_day=False, delay_minutes=30)
        sched.add_job.assert_not_called()

    def test_t4_suppressed_during_active_t5_session(self):
        """_send_t4_checkin does not post DM if T5 EOD session is active."""
        import workmain.daemon.scheduler as sched_mod
        daemon = MagicMock()
        daemon._eod_manager.has_any_session.return_value = True
        with patch('workmain.daemon.scheduler._reschedule_t4_checkin') as mock_resched:
            sched_mod._send_t4_checkin(daemon)
        daemon.post_message.assert_not_called()
        mock_resched.assert_called_once_with(daemon)

    def test_t4_scheduled_in_30_to_120_min_window(self):
        """fire_at is between 30 and 120 minutes from now when window is valid;
        interval bounds come from ScheduleService.get_t4_interval()."""
        now = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        sched, service = self._run_reschedule(now, delay_minutes=60, t4_interval=(30, 120))
        sched.add_job.assert_called_once()
        service.get_t4_interval.assert_called_once()

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

    def _run_send_t4_checkin(self, daemon, note_hit=None, entry_hit=None,
                              t4_interval=(30, 90)):
        """Call _send_t4_checkin with the activity-gap dependencies mocked.
        Item #58 — NotesRepository/TimeEntriesRepository are imported locally
        inside _send_t4_checkin(), so they must be patched at their source
        modules (Opus Finding A), not as scheduler-module attributes."""
        import workmain.daemon.scheduler as sched_mod
        mock_service = MagicMock()
        mock_service.get_t4_interval.return_value = t4_interval
        with patch('workmain.database.repositories.notes_repo.NotesRepository') as mock_notes_cls, \
             patch('workmain.database.repositories.time_entries_repo.TimeEntriesRepository') as mock_entries_cls, \
             patch('workmain.daemon.scheduler.get_db') as mock_get_db, \
             patch('workmain.daemon.scheduler.ScheduleService', return_value=mock_service), \
             patch('workmain.daemon.scheduler._reschedule_t4_checkin') as mock_resched:
            mock_get_db.return_value.get_session.return_value = MagicMock()
            mock_notes_cls.return_value.get_most_recent_since.return_value = note_hit
            mock_entries_cls.return_value.get_most_recent_since.return_value = entry_hit
            sched_mod._send_t4_checkin(daemon)
        return mock_resched

    def test_t4_rescheduled_after_firing(self):
        """_send_t4_checkin reschedules the next window after posting the DM."""
        daemon = MagicMock()
        daemon._eod_manager.has_any_session.return_value = False
        mock_resched = self._run_send_t4_checkin(daemon, note_hit=None, entry_hit=None)
        daemon.post_message.assert_called_once_with('What are you working on right now?')
        mock_resched.assert_called_once_with(daemon)

    def test_t4_checkin_fires_normally_with_no_recent_activity(self):
        """No recent Note or TimeEntry → DM sent, reschedule called (AC 3)."""
        daemon = MagicMock()
        daemon._eod_manager.has_any_session.return_value = False
        mock_resched = self._run_send_t4_checkin(daemon, note_hit=None, entry_hit=None)
        daemon.post_message.assert_called_once_with('What are you working on right now?')
        mock_resched.assert_called_once_with(daemon)

    def test_t4_checkin_suppressed_by_recent_note(self):
        """Recent Note found → DM suppressed, reschedule called (AC 1/2/5)."""
        daemon = MagicMock()
        daemon._eod_manager.has_any_session.return_value = False
        note = MagicMock()
        note.created_at = datetime.now()
        mock_resched = self._run_send_t4_checkin(daemon, note_hit=note, entry_hit=None)
        daemon.post_message.assert_not_called()
        mock_resched.assert_called_once_with(daemon)

    def test_t4_checkin_suppressed_by_recent_time_entry(self):
        """Recent TimeEntry found → DM suppressed, reschedule called (AC 1/2/5)."""
        daemon = MagicMock()
        daemon._eod_manager.has_any_session.return_value = False
        entry = MagicMock()
        entry.created_at = datetime.now()
        mock_resched = self._run_send_t4_checkin(daemon, note_hit=None, entry_hit=entry)
        daemon.post_message.assert_not_called()
        mock_resched.assert_called_once_with(daemon)

    def test_t4_checkin_suppression_logs_debug(self):
        """Suppression path logs at DEBUG level (AC 6)."""
        import workmain.daemon.scheduler as sched_mod
        daemon = MagicMock()
        daemon._eod_manager.has_any_session.return_value = False
        note = MagicMock()
        note.created_at = datetime.now()
        mock_service = MagicMock()
        mock_service.get_t4_interval.return_value = (30, 90)
        with patch('workmain.database.repositories.notes_repo.NotesRepository') as mock_notes_cls, \
             patch('workmain.database.repositories.time_entries_repo.TimeEntriesRepository') as mock_entries_cls, \
             patch('workmain.daemon.scheduler.get_db') as mock_get_db, \
             patch('workmain.daemon.scheduler.ScheduleService', return_value=mock_service), \
             patch('workmain.daemon.scheduler._reschedule_t4_checkin'), \
             self.assertLogs('workmain.daemon.scheduler', level='DEBUG') as log_ctx:
            mock_get_db.return_value.get_session.return_value = MagicMock()
            mock_notes_cls.return_value.get_most_recent_since.return_value = note
            mock_entries_cls.return_value.get_most_recent_since.return_value = None
            sched_mod._send_t4_checkin(daemon)
        self.assertTrue(any('suppressed' in msg for msg in log_ctx.output))

    def test_t4_checkin_suppression_logs_latest_of_both(self):
        """When both Note and TimeEntry are recent, the debug log reflects the
        later of the two timestamps (observability-only, non-blocking)."""
        import workmain.daemon.scheduler as sched_mod
        daemon = MagicMock()
        daemon._eod_manager.has_any_session.return_value = False
        earlier = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        later = datetime.now().replace(hour=9, minute=45, second=0, microsecond=0)
        note = MagicMock()
        note.created_at = earlier
        entry = MagicMock()
        entry.created_at = later
        mock_service = MagicMock()
        mock_service.get_t4_interval.return_value = (30, 90)
        with patch('workmain.database.repositories.notes_repo.NotesRepository') as mock_notes_cls, \
             patch('workmain.database.repositories.time_entries_repo.TimeEntriesRepository') as mock_entries_cls, \
             patch('workmain.daemon.scheduler.get_db') as mock_get_db, \
             patch('workmain.daemon.scheduler.ScheduleService', return_value=mock_service), \
             patch('workmain.daemon.scheduler._reschedule_t4_checkin'), \
             self.assertLogs('workmain.daemon.scheduler', level='DEBUG') as log_ctx:
            mock_get_db.return_value.get_session.return_value = MagicMock()
            mock_notes_cls.return_value.get_most_recent_since.return_value = note
            mock_entries_cls.return_value.get_most_recent_since.return_value = entry
            sched_mod._send_t4_checkin(daemon)
        self.assertTrue(any(later.strftime('%H:%M') in msg for msg in log_ctx.output))


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

def _eod_session(user_id='U_OP', channel_id='D_TEST', step_idx=2,
                 completed=None, skipped=None, paused=False, started_at=None):
    from workmain.daemon.conversation_state import SlackEodSession
    kwargs = dict(
        user_id=user_id,
        channel_id=channel_id,
        target_date=date(2099, 1, 1),
        steps=[
            {'key': 'note_review', 'num': 1, 'desc': 'Note review'},
            {'key': 'task_match', 'num': 2, 'desc': 'Task match'},
            {'key': 'time_review', 'num': 3, 'desc': 'Time review'},
        ],
        current_step_idx=step_idx,
        paused=paused,
        completed=completed if completed is not None else ['note_review', 'task_match'],
        skipped=skipped or [],
    )
    session = SlackEodSession(**kwargs)
    if started_at is not None:
        session.started_at = started_at
    return session


class TestT5SessionPersistence(unittest.TestCase):
    """ConversationStore persists and restores EOD sessions across restarts."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._path = Path(self._tmpdir.name) / 'daemon' / 'conversation_state.json'

    def tearDown(self):
        self._tmpdir.cleanup()

    def _store(self):
        from workmain.daemon.conversation_state import ConversationStore
        return ConversationStore(path=self._path)

    def test_save_session_creates_file_mode_600(self):
        self._store().save_session(_eod_session())
        self.assertTrue(self._path.exists())
        self.assertTrue(oct(os.stat(self._path).st_mode).endswith('600'))
        data = json.loads(self._path.read_text())
        self.assertEqual(data['sessions'][0]['user_id'], 'U_OP')
        self.assertEqual(data['sessions'][0]['current_step_idx'], 2)

    def test_store_round_trip(self):
        """Both record types survive a fresh load()."""
        s1 = self._store()
        s1.put_pending('U_OP', {'action': 'create_note', 'content': 'hi'})
        s1.save_session(_eod_session(step_idx=1, completed=['note_review']))

        s2 = self._store()
        s2.load()
        self.assertEqual(s2.take_pending('U_OP'), {'action': 'create_note', 'content': 'hi'})
        restored = s2.get_session('U_OP')
        self.assertIsNotNone(restored)
        self.assertEqual(restored.current_step_idx, 1)
        self.assertEqual(restored.completed, ['note_review'])
        self.assertIsNone(restored.pending_action)

    def test_store_load_corrupt_file(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text('not valid json {{{{')
        store = self._store()
        store.load()   # must not raise
        self.assertFalse(store.has_any_session())
        self.assertIsNone(store.take_pending('U_OP'))

    def test_load_absent_file_is_empty_state(self):
        store = self._store()
        store.load()
        self.assertFalse(store.has_any_session())

    def test_stale_session_not_restored(self):
        """A session older than EOD_SESSION_TTL is dropped on load (DR9a)."""
        s1 = self._store()
        s1.save_session(_eod_session(started_at=datetime.now() - timedelta(hours=25)))
        s2 = self._store()
        s2.load()
        self.assertFalse(s2.has_any_session())
        self.assertEqual(s2.restored_sessions(), [])

    def test_legacy_session_file_removed_on_load(self):
        legacy = self._path.parent / 'eod_session.json'
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_text('{}')
        self._store().load()
        self.assertFalse(legacy.exists())

    def test_discard_session_removes_from_memory_and_disk(self):
        store = self._store()
        store.save_session(_eod_session())
        store.discard_session('U_OP')
        self.assertFalse(store.has_session('U_OP'))
        fresh = self._store()
        fresh.load()
        self.assertFalse(fresh.has_session('U_OP'))

    def test_session_not_started_when_one_already_active(self):
        """handle_start_eod guard fires when a session is already registered."""
        from workmain.integrations.slack.slack_eod import SlackEodManager
        mock_client = MagicMock()
        store = self._store()
        store.save_session(_eod_session())
        manager = SlackEodManager(mock_client, MagicMock(), store)
        manager.handle_start_eod('U_OP', 'D_TEST')
        mock_client.post_message.assert_called_once()
        self.assertIn('resume', mock_client.post_message.call_args[0][1].lower())


# ---------------------------------------------------------------------------
# Group 7 — Morning briefing content (Gate 4 Item #50)
# ---------------------------------------------------------------------------

class TestMorningBriefingContent(unittest.TestCase):
    """build_morning_briefing() includes meetings and carry-forward tasks."""

    def _meeting(self, title, hour=9, duration_hours=1.0):
        m = MagicMock()
        m.title = title
        m.start_time = datetime(2099, 1, 5, hour, 0)
        m.duration_hours = duration_hours
        return m

    def _task(self, content):
        t = MagicMock()
        t.id = 1
        t.note = MagicMock()
        t.note.content = content
        return t

    def test_meetings_included_in_briefing(self):
        from workmain.integrations.slack.slack_eod import build_morning_briefing
        meeting = self._meeting('Standup')
        body = build_morning_briefing(date(2099, 1, 5), [meeting], [], [])
        self.assertIn('Standup', body)

    def test_no_meetings_shows_placeholder(self):
        from workmain.integrations.slack.slack_eod import build_morning_briefing
        body = build_morning_briefing(date(2099, 1, 5), [], [], [])
        self.assertIn('No meetings scheduled today.', body)

    def test_carry_forward_tasks_included(self):
        from workmain.integrations.slack.slack_eod import build_morning_briefing
        task = self._task('Write the spec')
        body = build_morning_briefing(date(2099, 1, 5), [], [task], [])
        self.assertIn('Write the spec', body)
        self.assertIn('Carry-forward tasks', body)

    def test_no_tasks_omits_section_entirely(self):
        from workmain.integrations.slack.slack_eod import build_morning_briefing
        body = build_morning_briefing(date(2099, 1, 5), [], [], [])
        self.assertNotIn('Carry-forward tasks', body)

    def test_unresolved_observations_shown_when_present(self):
        from workmain.integrations.slack.slack_eod import build_morning_briefing
        observations = [{'type': 'coverage', 'message': 'Gap detected 14:00-15:00'}]
        body = build_morning_briefing(date(2099, 1, 5), [], [], observations)
        self.assertIn('[coverage] Gap detected 14:00-15:00', body)
        self.assertIn('Unresolved from yesterday', body)

    def test_unresolved_observations_omitted_when_empty(self):
        from workmain.integrations.slack.slack_eod import build_morning_briefing
        body = build_morning_briefing(date(2099, 1, 5), [], [], [])
        self.assertNotIn('Unresolved from yesterday', body)

    def test_meetings_and_tasks_together(self):
        from workmain.integrations.slack.slack_eod import build_morning_briefing
        meeting = self._meeting('Design Review')
        task = self._task('Finish the doc')
        observations = [{'type': 'tag_anomaly', 'message': 'Untagged note found'}]
        body = build_morning_briefing(date(2099, 1, 5), [meeting], [task], observations)
        self.assertIn('Design Review', body)
        self.assertIn('Finish the doc', body)
        self.assertIn('[tag_anomaly] Untagged note found', body)

    def test_date_line_renders(self):
        from workmain.integrations.slack.slack_eod import build_morning_briefing
        from workmain.utils.date_format import format_date_display
        target_date = date(2099, 1, 5)
        body = build_morning_briefing(target_date, [], [], [])
        self.assertIn(format_date_display(target_date), body.splitlines())

    def test_multiple_observations_each_get_own_bullet(self):
        from workmain.integrations.slack.slack_eod import build_morning_briefing
        observations = [
            {'type': 'coverage', 'message': 'Gap detected 14:00-15:00'},
            {'type': 'tag_anomaly', 'message': 'Untagged note found'},
        ]
        body = build_morning_briefing(date(2099, 1, 5), [], [], observations)
        self.assertIn('• [coverage] Gap detected 14:00-15:00', body)
        self.assertIn('• [tag_anomaly] Untagged note found', body)


# ---------------------------------------------------------------------------
# Group 8 — Exactly one start-of-day notification (Gate 4 Item #50)
# ---------------------------------------------------------------------------

class TestSingleStartOfDayNotification(unittest.TestCase):
    """register_all_jobs() registers exactly one 05:30-class job —
    'workday_start' — never the retired parallel 'morning_briefing' job
    (Gate 4 §4.1 consolidation)."""

    def test_only_workday_start_job_registered(self):
        import workmain.daemon.scheduler as sched_mod
        mock_scheduler = MagicMock()
        mock_scheduler.get_job.return_value = None
        daemon = MagicMock()
        mock_session = MagicMock()
        with patch.object(sched_mod, '_scheduler', mock_scheduler), \
             patch('workmain.daemon.scheduler.get_db') as mock_get_db, \
             patch('workmain.daemon.scheduler._schedule_today_meeting_triggers'), \
             patch('workmain.daemon.scheduler._reschedule_t4_checkin'):
            mock_get_db.return_value.get_session.return_value = mock_session
            sched_mod.register_all_jobs(daemon)
        job_ids = [c.kwargs.get('id', '') for c in mock_scheduler.add_job.call_args_list]
        self.assertIn('workday_start', job_ids)
        self.assertNotIn('morning_briefing', job_ids)
        # Exactly one job carries the workday-start responsibility
        self.assertEqual(job_ids.count('workday_start'), 1)

    def test_morning_briefing_function_no_longer_exists(self):
        """_send_morning_briefing() was removed entirely as dead code once
        its only registration was gone (Gate 4 §4.1)."""
        import workmain.daemon.scheduler as sched_mod
        self.assertFalse(hasattr(sched_mod, '_send_morning_briefing'))


# ---------------------------------------------------------------------------
# Group 9 — notify_method=slack delivers for all five relocated triggers
# (Gate 3 Finding 1 direct regression coverage)
# ---------------------------------------------------------------------------

class TestNotifyMethodSlackDelivery(unittest.TestCase):
    """Each of the five relocated triggers threads a daemon handle through
    to deliver(method='slack', daemon=daemon) when notify_method=slack —
    the exact gap Gate 3's Finding 1 fixed (job registration previously
    split across two daemon-unaware/daemon-aware surfaces)."""

    def _slack_config(self):
        cfg = MagicMock()
        cfg.method = 'slack'
        cfg.enabled = True
        return cfg

    def _run_enriched_job(self, job_fn):
        """Run one of the four _enriched_notify-based jobs with
        notify_method=slack and capture the deliver() call."""
        daemon = MagicMock()
        mock_session = MagicMock()
        with patch('workmain.daemon.daemon.get_db') as mock_get_db, \
             patch('workmain.daemon.daemon.ScheduleService') as mock_svc_cls, \
             patch('workmain.daemon.daemon.NotificationConfigRepository') as mock_cfg_cls, \
             patch('workmain.daemon.daemon._assemble_notification_content', return_value='summary'), \
             patch('workmain.daemon.daemon.deliver') as mock_deliver:
            mock_get_db.return_value.get_session.return_value = mock_session
            mock_svc_cls.return_value.is_working_day.return_value = True
            mock_cfg_cls.return_value.get_config.return_value = self._slack_config()
            job_fn(daemon)
        return mock_deliver, daemon

    def test_daily_closeout_delivers_via_slack(self):
        import workmain.daemon.scheduler as sched_mod
        mock_deliver, daemon = self._run_enriched_job(sched_mod.job_daily_closeout)
        mock_deliver.assert_called_once()
        self.assertEqual(mock_deliver.call_args.kwargs.get('daemon'), daemon)
        self.assertEqual(mock_deliver.call_args.kwargs.get('method'), 'slack')

    def test_weekly_draft_delivers_via_slack(self):
        import workmain.daemon.scheduler as sched_mod
        mock_deliver, daemon = self._run_enriched_job(sched_mod.job_weekly_draft)
        mock_deliver.assert_called_once()
        self.assertEqual(mock_deliver.call_args.kwargs.get('daemon'), daemon)
        self.assertEqual(mock_deliver.call_args.kwargs.get('method'), 'slack')

    def test_eow_delivers_via_slack(self):
        import workmain.daemon.scheduler as sched_mod
        mock_deliver, daemon = self._run_enriched_job(sched_mod.job_eow)
        mock_deliver.assert_called_once()
        self.assertEqual(mock_deliver.call_args.kwargs.get('daemon'), daemon)
        self.assertEqual(mock_deliver.call_args.kwargs.get('method'), 'slack')

    def test_eod_prompt_delivers_via_slack(self):
        import workmain.daemon.scheduler as sched_mod
        mock_deliver, daemon = self._run_enriched_job(sched_mod.job_eod_prompt)
        mock_deliver.assert_called_once()
        self.assertEqual(mock_deliver.call_args.kwargs.get('daemon'), daemon)
        self.assertEqual(mock_deliver.call_args.kwargs.get('method'), 'slack')

    def test_workday_start_delivers_via_slack(self):
        """job_workday_start doesn't go through _enriched_notify — it
        assembles its own content and calls deliver() directly (Gate 4)."""
        import workmain.daemon.scheduler as sched_mod
        daemon = MagicMock()
        mock_session = MagicMock()
        with patch('workmain.daemon.scheduler.get_db') as mock_get_db, \
             patch('workmain.daemon.scheduler.ScheduleService') as mock_svc_cls, \
             patch('workmain.daemon.daemon._get_unresolved_observations', return_value=([], None)), \
             patch('workmain.daemon.daemon._schedule_meeting_reminders'), \
             patch('workmain.database.repositories.meetings_repo.MeetingsRepository') as mock_mtg_cls, \
             patch('workmain.database.repositories.notification_repository.NotificationConfigRepository') as mock_cfg_cls, \
             patch('workmain.database.repositories.task_status_repo.TaskStatusRepository') as mock_task_cls, \
             patch('workmain.daemon.delivery.deliver') as mock_deliver:
            mock_get_db.return_value.get_session.return_value = mock_session
            mock_svc_cls.return_value.is_working_day.return_value = True
            mock_mtg_cls.return_value.get_active_for_date.return_value = []
            mock_task_cls.return_value.get_filtered.return_value = []
            mock_cfg_cls.return_value.get_config.return_value = self._slack_config()
            sched_mod.job_workday_start(daemon)
        mock_deliver.assert_called_once()
        self.assertEqual(mock_deliver.call_args[0][2], 'slack')
        self.assertEqual(mock_deliver.call_args.kwargs.get('daemon'), daemon)


# ---------------------------------------------------------------------------
# Group 10 — Item #60 Gate 2: T1 freshness gate
# ---------------------------------------------------------------------------

class TestGetUnresolvedObservationsBranches:
    """Direct (unpatched) coverage of daemon._get_unresolved_observations()'s
    three branches: fresh, stale-with-notice, no-file-with-notice."""

    def test_fresh_match_returns_observations_no_notice(self, tmp_path, monkeypatch):
        from workmain.daemon import daemon as daemon_mod
        from workmain.daemon import state_io
        from workmain.daemon.models import Observation, ObservationType

        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        state_io.write_last_inspection(
            [Observation(type=ObservationType.CARRY_FORWARD, message='CF item.')],
            'Summary.', SENTINEL_DATE,
        )
        observations, notice = daemon_mod._get_unresolved_observations([SENTINEL_DATE])
        assert notice is None
        assert observations == [{'type': 'carry_forward', 'message': 'CF item.'}]

    def test_stale_returns_notice_naming_last_recorded_date(self, tmp_path, monkeypatch):
        from workmain.daemon import daemon as daemon_mod
        from workmain.daemon import state_io

        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        state_io.write_last_inspection([], 'Summary.', SENTINEL_DATE)
        observations, notice = daemon_mod._get_unresolved_observations([date(2099, 1, 2)])
        assert observations == []
        assert notice == f"Inspection data unavailable — last recorded {SENTINEL_DATE}."

    def test_missing_file_returns_no_data_notice(self, tmp_path, monkeypatch):
        from workmain.daemon import daemon as daemon_mod

        monkeypatch.setenv('WORKMAIN_STATE_DIR', str(tmp_path))
        observations, notice = daemon_mod._get_unresolved_observations([SENTINEL_DATE])
        assert observations == []
        assert notice == "No inspection data available."


class TestJobWorkdayStartFreshnessAcceptableDates(unittest.TestCase):
    """AC3 — job_workday_start() treats the state file as fresh when its
    target_date matches schedule.previous_working_day(target_date), not
    just target_date itself. previous_working_day() is mocked here (this
    file mocks DB access throughout — the real skip-weekend/skip-holiday
    logic is covered in test_schedule_service.py); SENTINEL_MONDAY/
    SENTINEL_TUESDAY are reused from there for the two AC3 narratives."""

    def _run(self, target_date, previous_working_day, state_file_date):
        import workmain.daemon.scheduler as sched_mod
        daemon = MagicMock()
        mock_session = MagicMock()
        with patch('workmain.daemon.scheduler.get_db') as mock_get_db, \
             patch('workmain.daemon.scheduler.date') as mock_date_cls, \
             patch('workmain.daemon.scheduler.ScheduleService') as mock_svc_cls, \
             patch('workmain.daemon.daemon._schedule_meeting_reminders'), \
             patch('workmain.database.repositories.meetings_repo.MeetingsRepository') as mock_mtg_cls, \
             patch('workmain.database.repositories.notification_repository.NotificationConfigRepository') as mock_cfg_cls, \
             patch('workmain.database.repositories.task_status_repo.TaskStatusRepository') as mock_task_cls, \
             patch('workmain.daemon.state_io.read_last_inspection') as mock_read, \
             patch('workmain.daemon.delivery.deliver') as mock_deliver:
            mock_get_db.return_value.get_session.return_value = mock_session
            mock_date_cls.today.return_value = target_date
            mock_svc_cls.return_value.is_working_day.return_value = True
            mock_svc_cls.return_value.previous_working_day.return_value = previous_working_day
            mock_mtg_cls.return_value.get_active_for_date.return_value = []
            mock_task_cls.return_value.get_filtered.return_value = []
            mock_read.return_value = {
                'target_date': str(state_file_date),
                'observations': [
                    {'type': 'carry_forward', 'message': 'CF item.', 'acknowledged': False}
                ],
            }
            cfg = MagicMock(enabled=True, method='slack')
            mock_cfg_cls.return_value.get_config.return_value = cfg
            sched_mod.job_workday_start(daemon)
        return mock_deliver.call_args[0][1]

    def test_friday_state_file_fresh_on_monday(self):
        """T1 fires Monday; Friday's inspection (the previous working day
        across the weekend) is treated as fresh — no stale notice."""
        from tests.test_schedule_service import SENTINEL_MONDAY
        friday = date(2099, 1, 2)  # the Friday immediately before SENTINEL_MONDAY
        body = self._run(target_date=SENTINEL_MONDAY, previous_working_day=friday,
                          state_file_date=friday)
        self.assertNotIn("Inspection data unavailable", body)
        self.assertNotIn("No inspection data available", body)
        self.assertIn("CF item.", body)

    def test_pre_holiday_workday_state_file_fresh_after_holiday(self):
        """T1 fires Tuesday, the workday after a recorded Monday holiday;
        the last actual working day's inspection (Friday, skipping the
        holiday) is treated as fresh."""
        from tests.test_schedule_service import SENTINEL_TUESDAY
        friday = date(2099, 1, 2)  # last workday before the SENTINEL_MONDAY holiday
        body = self._run(target_date=SENTINEL_TUESDAY, previous_working_day=friday,
                          state_file_date=friday)
        self.assertNotIn("Inspection data unavailable", body)
        self.assertNotIn("No inspection data available", body)
        self.assertIn("CF item.", body)


class TestJobWorkdayStartNoticeSplice(unittest.TestCase):
    """AC4/AC5 — job_workday_start() prepends the notice to the briefing
    body when _get_unresolved_observations() returns one; leaves the body
    untouched when notice is None."""

    def _run(self, notice):
        import workmain.daemon.scheduler as sched_mod
        daemon = MagicMock()
        mock_session = MagicMock()
        with patch('workmain.daemon.scheduler.get_db') as mock_get_db, \
             patch('workmain.daemon.scheduler.ScheduleService') as mock_svc_cls, \
             patch('workmain.daemon.daemon._get_unresolved_observations', return_value=([], notice)), \
             patch('workmain.daemon.daemon._schedule_meeting_reminders'), \
             patch('workmain.database.repositories.meetings_repo.MeetingsRepository') as mock_mtg_cls, \
             patch('workmain.database.repositories.notification_repository.NotificationConfigRepository') as mock_cfg_cls, \
             patch('workmain.database.repositories.task_status_repo.TaskStatusRepository') as mock_task_cls, \
             patch('workmain.integrations.slack.slack_eod.build_morning_briefing',
                   return_value='BRIEFING_BODY') as mock_build, \
             patch('workmain.daemon.delivery.deliver') as mock_deliver:
            mock_get_db.return_value.get_session.return_value = mock_session
            mock_svc_cls.return_value.is_working_day.return_value = True
            mock_svc_cls.return_value.previous_working_day.return_value = date.today()
            mock_mtg_cls.return_value.get_active_for_date.return_value = []
            mock_task_cls.return_value.get_filtered.return_value = []
            cfg = MagicMock(enabled=True, method='slack')
            mock_cfg_cls.return_value.get_config.return_value = cfg
            sched_mod.job_workday_start(daemon)
        return mock_deliver.call_args[0][1]

    def test_notice_prepended_when_present(self):
        body = self._run("Inspection data unavailable — last recorded 2099-01-01.")
        self.assertTrue(
            body.startswith("Inspection data unavailable — last recorded 2099-01-01.\n\n")
        )
        self.assertIn("BRIEFING_BODY", body)

    def test_body_unchanged_when_notice_none(self):
        body = self._run(None)
        self.assertEqual(body, "BRIEFING_BODY")


class TestPreviousWorkingDayGuard(unittest.TestCase):
    """Rule 7 (F3) — a previous_working_day() failure (pathological
    schedule_exceptions) must not crash job_workday_start(); it falls back
    to acceptable_dates=[target_date] and logs a warning, and the
    briefing still sends."""

    def test_value_error_falls_back_to_today_only_and_logs_warning(self):
        import workmain.daemon.scheduler as sched_mod
        daemon = MagicMock()
        mock_session = MagicMock()
        with patch('workmain.daemon.scheduler.get_db') as mock_get_db, \
             patch('workmain.daemon.scheduler.ScheduleService') as mock_svc_cls, \
             patch('workmain.daemon.scheduler.logger') as mock_logger, \
             patch('workmain.daemon.daemon._get_unresolved_observations',
                   return_value=([], None)) as mock_get_obs, \
             patch('workmain.daemon.daemon._schedule_meeting_reminders'), \
             patch('workmain.database.repositories.meetings_repo.MeetingsRepository') as mock_mtg_cls, \
             patch('workmain.database.repositories.notification_repository.NotificationConfigRepository') as mock_cfg_cls, \
             patch('workmain.database.repositories.task_status_repo.TaskStatusRepository') as mock_task_cls, \
             patch('workmain.daemon.delivery.deliver') as mock_deliver:
            mock_get_db.return_value.get_session.return_value = mock_session
            mock_svc_cls.return_value.is_working_day.return_value = True
            mock_svc_cls.return_value.previous_working_day.side_effect = ValueError("pathological")
            mock_mtg_cls.return_value.get_active_for_date.return_value = []
            mock_task_cls.return_value.get_filtered.return_value = []
            cfg = MagicMock(enabled=True, method='slack')
            mock_cfg_cls.return_value.get_config.return_value = cfg
            sched_mod.job_workday_start(daemon)

        mock_deliver.assert_called_once()
        mock_logger.warning.assert_called_once()
        acceptable_dates_arg = mock_get_obs.call_args[0][0]
        self.assertEqual(acceptable_dates_arg, [date.today()])


# ---------------------------------------------------------------------------
# Group 11 — Atomic state-file writer (Issue #101 step 1)
# ---------------------------------------------------------------------------

class TestWriteJsonAtomic(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._dir = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_write_json_atomic(self):
        """Replaces content rather than appending, sets mode 600, leaves no
        temp sibling behind, and creates the parent directory itself."""
        from workmain.daemon.state_io import write_json_atomic
        path = self._dir / 'nested' / 'state.json'

        write_json_atomic(path, {'a': 1, 'b': [1, 2, 3]})
        self.assertEqual(json.loads(path.read_text()), {'a': 1, 'b': [1, 2, 3]})

        write_json_atomic(path, {'a': 2})
        self.assertEqual(json.loads(path.read_text()), {'a': 2})

        self.assertTrue(oct(os.stat(path).st_mode).endswith('600'))
        self.assertEqual(list(path.parent.glob('*.tmp')), [])


# ---------------------------------------------------------------------------
# Group 12 — Conversation store: pending actions, correlation, concurrency
# (Issue #101 steps 2 & 5)
# ---------------------------------------------------------------------------

class TestConversationStorePending(unittest.TestCase):

    def _store(self):
        return _make_store()

    def test_mismatched_action_id_leaves_record(self):
        store = self._store()
        pa = store.put_pending('U_OP', {'action': 'create_note', 'content': 'x'})
        self.assertIsNone(store.take_pending('U_OP', 'not-the-id'))
        self.assertEqual(store.take_pending('U_OP', pa.action_id),
                         {'action': 'create_note', 'content': 'x'})

    def test_expired_pending_not_executed(self):
        store = self._store()
        store.put_pending('U_OP', {'action': 'create_note', 'content': 'x'})
        store._pending['U_OP'].created_at = datetime.now() - timedelta(minutes=30)
        self.assertIsNone(store.take_pending('U_OP'))
        # and the expired record is gone
        self.assertIsNone(store.take_pending('U_OP'))

    def test_concurrent_take_pending_returns_one_winner(self):
        import threading as _t
        store = self._store()
        store.put_pending('U_OP', {'action': 'create_note', 'content': 'x'})
        results = []
        barrier = _t.Barrier(2)

        def grab():
            barrier.wait()
            results.append(store.take_pending('U_OP'))

        threads = [_t.Thread(target=grab) for _ in range(2)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        self.assertEqual(sum(1 for r in results if r is not None), 1)

    def test_long_action_button_value_under_slack_cap(self):
        from workmain.orchestration.confirmation_gate import ConfirmationGate
        store = self._store()
        action = {'action': 'write_correction_note', 'note': 'z' * 4000}
        pa = store.put_pending('U_OP', action)
        blocks = ConfirmationGate().format_blocks(action, pa.action_id)
        for e in blocks[1]['elements']:
            self.assertLess(len(e['value']), 2000)


class TestDoubleExecution(unittest.TestCase):
    """A confirmed action executes exactly once regardless of the order the
    button click and the affirmative text arrive in (AC2)."""

    def test_block_approve_then_yes_executes_once(self):
        daemon = _make_daemon()
        action = {'action': 'create_note', 'content': 'once'}
        pa = daemon._store.put_pending('U_OP', action)
        with patch.object(daemon, '_execute_action') as mock_exec, \
             patch.object(daemon, '_dispatch_message') as mock_dispatch:
            daemon.handle_block_action(_block_action_payload('wm_approve', pa.action_id))
            daemon.handle_message(_dm_event(text='yes'))
        mock_exec.assert_called_once_with(action)
        mock_dispatch.assert_called_once()   # 'yes' fell through to a fresh parse

    def test_yes_then_block_approve_executes_once(self):
        daemon = _make_daemon()
        action = {'action': 'create_note', 'content': 'once'}
        pa = daemon._store.put_pending('U_OP', action)
        with patch.object(daemon, '_execute_action') as mock_exec, \
             patch.object(daemon, '_dispatch_message'):
            daemon.handle_message(_dm_event(text='yes'))
            daemon.handle_block_action(_block_action_payload('wm_approve', pa.action_id))
        mock_exec.assert_called_once_with(action)
        # the stale click was refused
        self.assertTrue(any(
            'no longer active' in c.args[1]
            for c in daemon._socket_client.post_message.call_args_list
        ))

    def test_block_reject_clears_pending(self):
        daemon = _make_daemon()
        pa = daemon._store.put_pending('U_OP', {'action': 'create_note', 'content': 'x'})
        with patch.object(daemon, '_execute_action') as mock_exec, \
             patch.object(daemon, '_dispatch_message'):
            daemon.handle_block_action(_block_action_payload('wm_reject', pa.action_id))
            daemon.handle_message(_dm_event(text='yes'))
        mock_exec.assert_not_called()

    def test_stale_reject_does_not_clear_current_pending(self):
        daemon = _make_daemon()
        pa = daemon._store.put_pending('U_OP', {'action': 'create_note', 'content': 'x'})
        daemon.handle_block_action(_block_action_payload('wm_reject', 'stale-id'))
        self.assertTrue(any(
            'no longer active' in c.args[1]
            for c in daemon._socket_client.post_message.call_args_list
        ))
        self.assertEqual(daemon._store.take_pending('U_OP', pa.action_id),
                         {'action': 'create_note', 'content': 'x'})

    def test_actor_resolution(self):
        # payload with user.id present → used
        daemon = _make_daemon()
        pa = daemon._store.put_pending('U_ALICE', {'action': 'create_note', 'content': 'x'})
        with patch.object(daemon, '_execute_action') as mock_exec:
            daemon.handle_block_action(_block_action_payload('wm_approve', pa.action_id, user='U_ALICE'))
        mock_exec.assert_called_once()

        # payload without user → falls back to cached operator id
        daemon2 = _make_daemon()
        pa2 = daemon2._store.put_pending('U_OP', {'action': 'create_note', 'content': 'x'})
        with patch.object(daemon2, '_execute_action') as mock_exec2:
            daemon2.handle_block_action(_block_action_payload('wm_approve', pa2.action_id, user=None))
        mock_exec2.assert_called_once()

    def test_empty_result_message_posts_fallback(self):
        from workmain.orchestration.action_executor import ActionResult
        daemon = _make_daemon()
        with patch('workmain.daemon.daemon.get_db') as mock_db, \
             patch('workmain.orchestration.action_executor.ActionExecutor') as mock_ae, \
             patch.object(daemon, '_maybe_post_correction_summary'):
            mock_db.return_value.get_session.return_value = MagicMock()
            mock_ae.return_value.execute.return_value = ActionResult(success=True, message='')
            daemon._execute_action({'action': 'create_note', 'content': 'x'})
        daemon._socket_client.post_message.assert_any_call('D_TEST', 'Action completed.')


class TestEodStateThroughStore(unittest.TestCase):
    """EOD session lifecycle and session.pending_action go through the store
    (AC6, AC14, AC16, AC17)."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._path = Path(self._tmpdir.name) / 'daemon' / 'conversation_state.json'

    def tearDown(self):
        self._tmpdir.cleanup()

    def _store(self):
        from workmain.daemon.conversation_state import ConversationStore
        return ConversationStore(path=self._path)

    def _manager(self, store):
        from workmain.integrations.slack.slack_eod import SlackEodManager
        return SlackEodManager(MagicMock(), MagicMock(), store)

    def test_eod_error_leaves_no_resumable_state(self):
        daemon = _make_daemon(store=self._store())
        daemon._store.save_session(_eod_session())
        daemon._eod_manager.has_session.return_value = True
        daemon._eod_manager.handle_reply.side_effect = RuntimeError('boom')
        daemon.handle_message(_dm_event(text='anything'))
        fresh = self._store()
        fresh.load()
        self.assertFalse(fresh.has_any_session())

    def test_start_eod_discards_pending_action(self):
        store = self._store()
        store.put_pending('U_OP', {'action': 'create_note', 'content': 'stale offer'})
        manager = self._manager(store)
        with patch.object(manager, '_advance_step'):
            manager.handle_start_eod('U_OP', 'D_TEST')
        self.assertIsNone(store.take_pending('U_OP'))

    def test_start_eod_persists_session_on_insert(self):
        store = self._store()
        manager = self._manager(store)
        with patch.object(manager, '_advance_step'):
            manager.handle_start_eod('U_OP', 'D_TEST')
        fresh = self._store()
        fresh.load()
        self.assertTrue(fresh.has_session('U_OP'))

    def test_resume_offer_from_restored_session(self):
        s1 = self._store()
        s1.save_session(_eod_session(step_idx=1, paused=True))
        s2 = self._store()
        s2.load()
        daemon = _make_daemon(store=s2)
        daemon._maybe_offer_eod_resume()
        self.assertTrue(any(
            'Welcome back' in c.args[1]
            for c in daemon._socket_client.post_message.call_args_list
        ))

    def test_cleared_inline_pending_not_resurrected(self):
        store = self._store()
        session = _eod_session()
        session.pending_action = {'action': 'create_note', 'content': 'inline'}
        store.save_session(session)
        self.assertEqual(store.take_session_pending('U_OP'),
                         {'action': 'create_note', 'content': 'inline'})
        fresh = self._store()
        fresh.load()
        self.assertIsNone(fresh.get_session('U_OP').pending_action)

    def test_set_inline_pending_persisted(self):
        store = self._store()
        store.save_session(_eod_session())
        store.set_session_pending('U_OP', {'action': 'create_note', 'content': 'inline'})
        fresh = self._store()
        fresh.load()
        self.assertEqual(fresh.get_session('U_OP').pending_action,
                         {'action': 'create_note', 'content': 'inline'})

    def test_concurrent_take_session_pending_returns_one_winner(self):
        import threading as _t
        store = self._store()
        session = _eod_session()
        session.pending_action = {'action': 'create_note', 'content': 'inline'}
        store.save_session(session)
        results = []
        barrier = _t.Barrier(2)

        def grab():
            barrier.wait()
            results.append(store.take_session_pending('U_OP'))

        threads = [_t.Thread(target=grab) for _ in range(2)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        self.assertEqual(sum(1 for r in results if r is not None), 1)

    def test_async_dispatch_persists_before_thread_start(self):
        import workmain.integrations.slack.slack_eod as se
        store = self._store()
        manager = self._manager(store)
        session = _eod_session(step_idx=0, paused=False)
        store.save_session(session)

        order = []
        real_save = store.save_session
        store.save_session = lambda s: (order.append('save'), real_save(s))

        class _FakeThread:
            def __init__(self, *a, **kw):
                pass
            def start(self):
                order.append('start')

        with patch.object(se.threading, 'Thread', _FakeThread):
            manager._run_step_async(session, {'key': 'task_match', 'num': 1, 'desc': 'Task match'})

        self.assertEqual(order, ['save', 'start'])


if __name__ == '__main__':
    unittest.main()
