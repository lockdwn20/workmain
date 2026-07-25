"""
WorkmAIn Tests
Slack Integration Tests
test_slack.py v1.1
20260724

Integration tests for Phase 8 Slack integration.

Test classes:
- TestSlackReportsIntegration      — real DB, reports table
- TestSlackAuth                    — token loading
- TestFormatForSlack                — markdown conversion
- TestDraftDateRange                — date range calculation
- TestSlackClient                   — mocked Slack API
- TestDraftLabel                    — DRAFT label prepend behaviour
- TestSlackPostWeeklySharedRunner   — slack_post() driving the shared
  eod_workflow review runner + separate delivery step (Item #61 Gate 4)

All Slack API calls are mocked via unittest.mock.patch.
No real API calls are made in these tests.

Test report rows use slack_message_ts values prefixed 'test-ts-' for cleanup
by conftest.py.

Version History:
- v1.0: Initial implementation (Phase 8 Gate 5) — 18 test cases
- v1.1: Item #61 Gate 4 — add TestSlackPostWeeklySharedRunner (real
        committed session, mirrors test_report_correction.py's CLI-level
        classes). Placed here rather than the spec-named
        tests/test_slack_commands.py — that file doesn't exist in this
        repo. Deviation noted, same pattern as Item #61 Gate 2.
"""

import os
import unittest
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from dotenv import load_dotenv

load_dotenv()

from workmain.database.models import Report
from workmain.integrations.slack.auth import (
    SlackAuthError,
    get_token,
    is_authenticated,
)
from workmain.integrations.slack.client import (
    SlackClient,
    SlackClientError,
    already_posted,
    format_for_slack,
)
from workmain.cli.commands.slack import get_draft_date_range, slack


# ---------------------------------------------------------------------------
# TestSlackReportsIntegration — real DB
# ---------------------------------------------------------------------------

class TestSlackReportsIntegration:
    """Tests that query the real reports table to verify already_posted() logic."""

    def test_01_already_posted_false(self, db_session):
        """No report row for date → already_posted returns False."""
        test_date = date(2099, 1, 1)  # Far future — guaranteed no row
        assert already_posted(db_session, test_date) is False

    def test_02_already_posted_true(self, db_session):
        """Report row with slack_message_ts set → returns True."""
        test_date = date(2099, 1, 2)
        row = Report(
            report_type="weekly_client",
            report_date=test_date,
            content="Test content",
            slack_message_ts="test-ts-001",
            slack_channel="#test-channel",
            slack_workspace_name="Test WS",
        )
        db_session.add(row)
        db_session.commit()

        assert already_posted(db_session, test_date) is True

        # Cleanup
        db_session.delete(row)
        db_session.commit()

    def test_03_already_posted_ignores_null_ts(self, db_session):
        """Report row exists but slack_message_ts is NULL → returns False."""
        test_date = date(2099, 1, 3)
        row = Report(
            report_type="weekly_client",
            report_date=test_date,
            content="Generated but not yet posted",
            slack_message_ts=None,
        )
        db_session.add(row)
        db_session.commit()

        assert already_posted(db_session, test_date) is False

        # Cleanup
        db_session.delete(row)
        db_session.commit()

    def test_04_upsert_updates_existing_row(self, db_session):
        """Existing report row gets slack fields populated after a simulated post."""
        test_date = date(2099, 1, 4)
        row = Report(
            report_type="weekly_client",
            report_date=test_date,
            content="Report content",
            slack_message_ts=None,
        )
        db_session.add(row)
        db_session.commit()

        # Simulate the upsert that post-weekly performs
        existing = db_session.query(Report).filter(
            Report.report_type == "weekly_client",
            Report.report_date == test_date,
        ).first()
        assert existing is not None
        existing.slack_message_ts = "test-ts-004"
        existing.slack_channel = "#int-gmf-csirt"
        existing.slack_workspace_name = "slower-midwest"
        db_session.commit()

        # Verify
        updated = db_session.query(Report).filter(
            Report.report_type == "weekly_client",
            Report.report_date == test_date,
        ).first()
        assert updated.slack_message_ts == "test-ts-004"
        assert updated.slack_channel == "#int-gmf-csirt"
        assert updated.slack_workspace_name == "slower-midwest"
        assert already_posted(db_session, test_date) is True

        # Cleanup
        db_session.delete(updated)
        db_session.commit()


# ---------------------------------------------------------------------------
# TestSlackAuth
# ---------------------------------------------------------------------------

class TestSlackAuth:
    """Tests for token loading and is_authenticated()."""

    def test_05_get_token_success(self):
        """SLACK_BOT_TOKEN set in env → get_token returns it."""
        with patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test-token-12345"}):
            token = get_token()
            assert token == "xoxb-test-token-12345"

    def test_06_get_token_missing(self):
        """SLACK_BOT_TOKEN not set → raises SlackAuthError."""
        env_without_token = {k: v for k, v in os.environ.items() if k != "SLACK_BOT_TOKEN"}
        with patch.dict(os.environ, env_without_token, clear=True):
            with pytest.raises(SlackAuthError):
                get_token()

    def test_07_is_authenticated_true(self):
        """Token present → is_authenticated returns True."""
        with patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test-token-12345"}):
            assert is_authenticated() is True

    def test_08_is_authenticated_false(self):
        """Token absent → is_authenticated returns False."""
        env_without_token = {k: v for k, v in os.environ.items() if k != "SLACK_BOT_TOKEN"}
        with patch.dict(os.environ, env_without_token, clear=True):
            assert is_authenticated() is False


# ---------------------------------------------------------------------------
# TestFormatForSlack
# ---------------------------------------------------------------------------

class TestFormatForSlack:
    """Tests for markdown → Slack mrkdwn conversion."""

    def test_09_heading_conversion(self):
        """# Title → *Title*"""
        result = format_for_slack("# Weekly Report")
        assert result == "*Weekly Report*"

    def test_10_bold_conversion(self):
        """**word** → *word*"""
        result = format_for_slack("**bold text**")
        assert result == "*bold text*"

    def test_11_italic_conversion(self):
        """*word* (no conflict with bold rule) → _word_"""
        # Italic only — no bold present
        result = format_for_slack("*italic text*")
        assert result == "_italic text_"

        # Bold and italic on same line — must not interfere
        result2 = format_for_slack("**bold** and *italic*")
        assert "*bold*" in result2
        assert "_italic_" in result2

    def test_11b_heading_not_double_converted(self):
        """# Heading must become *Heading*, not _Heading_ (italic must not re-match)."""
        result = format_for_slack("# Weekly Report\n## Summary")
        assert "*Weekly Report*" in result
        assert "*Summary*" in result
        assert "_Weekly Report_" not in result
        assert "_Summary_" not in result

    def test_11c_list_and_hr_conversion(self):
        """- item → • item; --- removed."""
        result = format_for_slack("- list entry\n---\n- another")
        assert "• list entry" in result
        assert "• another" in result
        assert "---" not in result


# ---------------------------------------------------------------------------
# TestDraftDateRange
# ---------------------------------------------------------------------------

class TestDraftDateRange:
    """Tests for get_draft_date_range() date arithmetic."""

    def test_12_thursday_range(self):
        """Anchor = Thursday → returns (Monday, Thursday)."""
        thursday = date(2026, 3, 12)  # Known Thursday
        monday, anchor = get_draft_date_range(thursday)
        assert monday == date(2026, 3, 9)
        assert anchor == thursday
        assert monday.weekday() == 0  # Monday

    def test_13_monday_anchor(self):
        """Anchor = Monday → returns (Monday, Monday) — single-day range."""
        monday = date(2026, 3, 9)
        start, end = get_draft_date_range(monday)
        assert start == monday
        assert end == monday

    def test_14_custom_date(self):
        """Arbitrary mid-week date returns correct Monday."""
        wednesday = date(2026, 3, 11)  # Known Wednesday
        monday, anchor = get_draft_date_range(wednesday)
        assert monday == date(2026, 3, 9)
        assert anchor == wednesday
        assert monday.weekday() == 0


# ---------------------------------------------------------------------------
# TestSlackClient — mocked API
# ---------------------------------------------------------------------------

class TestSlackClient:
    """Tests for SlackClient with fully mocked slack_sdk.WebClient."""

    def test_15_post_message_success(self):
        """Mock chat_postMessage returns ts → post_message returns it."""
        mock_response = {"ts": "1678900000.123456", "ok": True}

        with patch("workmain.integrations.slack.client.WebClient") as MockWebClient:
            mock_instance = MagicMock()
            MockWebClient.return_value = mock_instance
            mock_instance.chat_postMessage.return_value = mock_response

            client = SlackClient("xoxb-fake-token")
            ts = client.post_message("#test-channel", "Hello world")

            assert ts == "1678900000.123456"
            mock_instance.chat_postMessage.assert_called_once_with(
                channel="#test-channel", text="Hello world"
            )

    def test_16_post_message_failure(self):
        """Mock raises SlackApiError → SlackClientError is raised."""
        from slack_sdk.errors import SlackApiError

        with patch("workmain.integrations.slack.client.WebClient") as MockWebClient:
            mock_instance = MagicMock()
            MockWebClient.return_value = mock_instance

            error_response = MagicMock()
            error_response.__getitem__ = lambda self, key: "channel_not_found" if key == "error" else None
            mock_instance.chat_postMessage.side_effect = SlackApiError(
                message="channel_not_found", response=error_response
            )

            client = SlackClient("xoxb-fake-token")
            with pytest.raises(SlackClientError):
                client.post_message("#nonexistent", "Hello")


# ---------------------------------------------------------------------------
# TestDraftLabel
# ---------------------------------------------------------------------------

class TestDraftLabel:
    """Tests verifying the DRAFT label prepend behaviour."""

    def test_17_draft_label_prepended(self):
        """DRAFT header is the first line of the formatted slack content."""
        report_content = "# Weekly Report\n\nSome content here."
        monday_str = "Mon 09 Mar 2026"
        anchor_str = "Thu 12 Mar 2026"

        draft_header = f"*[DRAFT — For Review]* Week of {monday_str}–{anchor_str}\n\n"
        slack_content = draft_header + format_for_slack(report_content)

        first_line = slack_content.splitlines()[0]
        assert first_line.startswith("*[DRAFT — For Review]*")
        assert monday_str in first_line
        assert anchor_str in first_line

    def test_18_draft_label_not_in_reports_ts(self, db_session):
        """slack_message_ts stored on reports row does not contain the DRAFT label."""
        test_date = date(2099, 1, 18)
        ts_value = "test-ts-018"

        row = Report(
            report_type="weekly_client",
            report_date=test_date,
            content="# Weekly Report\n\nRaw markdown stored in DB — slack label is prepended at post time only.",
            slack_message_ts=ts_value,
            slack_channel="#int-gmf-csirt",
            slack_workspace_name="slower-midwest",
        )
        db_session.add(row)
        db_session.commit()

        # Query by primary key to ensure we get the row we just inserted
        db_session.refresh(row)

        assert row is not None
        assert row.slack_message_ts == ts_value
        assert "DRAFT" not in row.slack_message_ts
        assert "DRAFT" not in row.content

        # Cleanup
        db_session.delete(row)
        db_session.commit()


# ---------------------------------------------------------------------------
# TestSlackPostWeeklySharedRunner — Item #61 Gate 4
# ---------------------------------------------------------------------------

class TestSlackPostWeeklySharedRunner(unittest.TestCase):
    """Item #61 Gate 4 (Design Rules 9-11) — slack_post() now drives the
    shared eod_workflow._run_report_review_step() runner, then a separate
    post-review delivery step. The review runner itself is mocked to a
    no-op here (its own generate-or-reuse + [v/e/c/s] menu is already
    covered by TestReportReviewStepCollapse/TestReportReviewStepEditBranch
    in test_eod_workflow.py) — these tests seed the Report row directly to
    represent what that runner would have produced, then exercise only
    slack_post()'s delivery-step logic.

    Placed here (test_slack.py) rather than the spec-named
    tests/test_slack_commands.py — that file doesn't exist in this repo;
    test_slack.py is the established home for slack.py CLI coverage. Same
    filename-deviation pattern as Item #61 Gate 2
    (see tests/test_report_correction.py's docstring).

    Real committed-session pattern (mirrors test_report_correction.py's
    CLI-level classes) — slack_post() opens its own get_db() session, so
    a db_session-fixture-flushed row would be invisible to it.
    """

    def setUp(self):
        from workmain.database.connection import get_db
        db = get_db()
        self.session = db.get_session()
        self._seeded_ids: list = []
        self.runner = CliRunner()

    def tearDown(self):
        for rid in self._seeded_ids:
            self.session.query(Report).filter(Report.id == rid).delete()
        self.session.commit()
        self.session.close()

    def _seed(self, report_date, status='unconfirmed', content='Weekly content.',
              corrected_content=None):
        r = Report(
            report_type='weekly_client',
            report_date=report_date,
            content=content,
            status=status,
        )
        if corrected_content is not None:
            r.corrected_content = corrected_content
        self.session.add(r)
        self.session.commit()
        self.session.refresh(r)
        self._seeded_ids.append(r.id)
        return r

    def _invoke(self, date_str, input_text=None, extra_args=None):
        args = ['post', 'weekly', '-d', date_str, '--channel', '#gate4-test']
        if extra_args:
            args += extra_args
        with patch('workmain.cli.commands.slack.get_token', return_value='xoxb-fake'), \
             patch('workmain.workflows.eod_workflow._run_report_review_step') as mock_runner, \
             patch('workmain.cli.commands.slack.load_slack_config',
                   return_value={'workspace_name': 'Test WS'}), \
             patch('workmain.cli.commands.slack.SlackClient') as mock_client_cls:
            mock_client = MagicMock()
            mock_client.post_message.return_value = 'test-ts-gate4'
            mock_client_cls.return_value = mock_client
            result = self.runner.invoke(
                slack, args, input=input_text, catch_exceptions=False,
            )
        return result, mock_client, mock_runner

    def test_uses_shared_runner_no_duplicate_logic(self):
        """No duplicate generate/edit/upsert logic remains in slack_post()."""
        import inspect
        from workmain.cli.commands import slack as slack_module
        src = inspect.getsource(slack_module.slack_post.callback)
        self.assertIn('_run_report_review_step', src)
        self.assertNotIn('_edit_in_editor', src)
        self.assertNotIn('_run_generation', src)

    def test_regenerate_flag_removed(self):
        result = self.runner.invoke(slack, ['post', 'weekly', '--help'])
        self.assertNotIn('--regenerate', result.output)

    def test_posts_only_when_confirmed(self):
        d = date(2098, 10, 1)
        self._seed(d, status='confirmed', content='Confirmed weekly content.')
        result, mock_client, mock_runner = self._invoke('20981001', input_text='y\n')
        self.assertEqual(result.exit_code, 0, result.output)
        mock_runner.assert_called_once()
        mock_client.post_message.assert_called_once()
        _, posted_content = mock_client.post_message.call_args[0]
        self.assertIn('Confirmed weekly content.', posted_content)

    def test_no_post_offered_when_unconfirmed(self):
        """A [s]kip (or any non-confirmed exit) from the review runner
        offers no post — matches prior default-to-no-post behavior."""
        d = date(2098, 10, 2)
        self._seed(d, status='unconfirmed', content='Unconfirmed weekly content.')
        result, mock_client, mock_runner = self._invoke('20981002')
        self.assertEqual(result.exit_code, 0, result.output)
        mock_client.post_message.assert_not_called()
        self.assertIn('no message posted', result.output.lower())

    def test_declining_the_post_prompt_sends_nothing(self):
        d = date(2098, 10, 3)
        self._seed(d, status='confirmed', content='Content.')
        result, mock_client, mock_runner = self._invoke('20981003', input_text='n\n')
        self.assertEqual(result.exit_code, 0, result.output)
        mock_client.post_message.assert_not_called()

    def test_posts_corrected_content_over_content(self):
        d = date(2098, 10, 4)
        self._seed(d, status='corrected', content='Original.',
                  corrected_content='Corrected weekly content.')
        result, mock_client, mock_runner = self._invoke('20981004', input_text='y\n')
        self.assertEqual(result.exit_code, 0, result.output)
        _, posted_content = mock_client.post_message.call_args[0]
        self.assertIn('Corrected weekly content.', posted_content)
        self.assertNotIn('Original.', posted_content)

    def test_slack_fields_persist_on_same_row_no_second_row(self):
        d = date(2098, 10, 5)
        r = self._seed(d, status='confirmed', content='Content.')
        result, mock_client, mock_runner = self._invoke('20981005', input_text='y\n')
        self.assertEqual(result.exit_code, 0, result.output)
        self.session.refresh(r)
        self.assertEqual(r.slack_message_ts, 'test-ts-gate4')
        self.assertEqual(r.slack_channel, '#gate4-test')
        self.assertEqual(r.slack_workspace_name, 'Test WS')
        rows = self.session.query(Report).filter(
            Report.report_type == 'weekly_client', Report.report_date == d,
        ).all()
        self.assertEqual(len(rows), 1)

    def test_already_posted_blocks_without_force(self):
        d = date(2098, 10, 11)
        r = self._seed(d, status='confirmed', content='Content.')
        r.slack_message_ts = 'existing-ts'
        self.session.commit()
        result, mock_client, mock_runner = self._invoke('20981011', input_text='y\n')
        self.assertEqual(result.exit_code, 0, result.output)
        mock_client.post_message.assert_not_called()
        self.assertIn('already posted', result.output.lower())

    def test_force_reposts_when_already_posted(self):
        d = date(2098, 10, 12)
        r = self._seed(d, status='confirmed', content='Content.')
        r.slack_message_ts = 'existing-ts'
        self.session.commit()
        result, mock_client, mock_runner = self._invoke(
            '20981012', input_text='y\n', extra_args=['--force'],
        )
        self.assertEqual(result.exit_code, 0, result.output)
        mock_client.post_message.assert_called_once()

    def test_thursday_and_friday_produce_independent_rows(self):
        """Regression guard against the discarded anchor-date design —
        Thursday's draft and Friday's weekly review remain two independent
        rows on their own actual dates, no lookup between them."""
        thursday = date(2098, 10, 8)
        friday = date(2098, 10, 9)
        self._seed(thursday, status='confirmed', content='Thursday content.')
        self._seed(friday, status='confirmed', content='Friday content.')
        result_thu, _, _ = self._invoke('20981008', input_text='y\n')
        result_fri, _, _ = self._invoke('20981009', input_text='y\n')
        self.assertEqual(result_thu.exit_code, 0, result_thu.output)
        self.assertEqual(result_fri.exit_code, 0, result_fri.output)
        rows = self.session.query(Report).filter(
            Report.report_type == 'weekly_client',
            Report.report_date.in_([thursday, friday]),
        ).all()
        self.assertEqual(len(rows), 2)
        contents = {r.report_date: (r.corrected_content or r.content) for r in rows}
        self.assertIn('Thursday content.', contents[thursday])
        self.assertIn('Friday content.', contents[friday])

    def test_dry_run_no_side_effects(self):
        with patch('workmain.cli.commands.slack.get_token', return_value='xoxb-fake'), \
             patch('workmain.workflows.eod_workflow._run_report_review_step') as mock_runner, \
             patch('workmain.cli.commands.slack.SlackClient') as mock_client_cls:
            result = self.runner.invoke(
                slack,
                ['post', 'weekly', '-d', '20981010', '--channel', '#gate4-test', '--dry-run'],
                catch_exceptions=False,
            )
        self.assertEqual(result.exit_code, 0, result.output)
        mock_runner.assert_not_called()
        mock_client_cls.assert_not_called()
        self.assertIn('DRY RUN', result.output)
        self.assertIn('#gate4-test', result.output)
