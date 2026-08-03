"""
Verifies Phase 13 prompt builder behaviors:
  - data_sources gating: time_entries omitted from prompt when absent from section config
  - client filter forwarding: filter_client=True propagated to repo calls
  - preview_report filter parity: same client filter applied as full report generation

All repository calls are mocked; no DB writes occur in this file.
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, call

from workmain.ai.prompt_builder import PromptBuilder
from workmain.ai.report_generator import ReportGenerator

_SENTINEL = date(2099, 6, 1)
_DAILY_TEMPLATE = {"metadata": {"frequency": "daily"}, "sections": []}


def _mock_builder() -> PromptBuilder:
    """Return a PromptBuilder with all external dependencies mocked."""
    session = MagicMock()
    builder = PromptBuilder(
        session,
        template_loader=MagicMock(),
        style_adapter=MagicMock(),
    )
    builder.notes_repo = MagicMock()
    builder.time_repo = MagicMock()
    builder.meetings_repo = MagicMock()
    # Default: all queries return empty lists
    builder.notes_repo.get_for_date_client.return_value = []
    builder.time_repo.get_for_date_client.return_value = []
    builder.meetings_repo.get_for_date_client.return_value = []
    return builder


def _mock_time_entry(content: str, hours: float = 1.0) -> MagicMock:
    """Return a mock TimeEntry whose note.content is the given string."""
    entry = MagicMock()
    entry.note.content = content
    entry.entry_time = None
    entry.duration_hours = hours
    entry.project = None
    return entry


# ---------------------------------------------------------------------------
# data_sources gating
# ---------------------------------------------------------------------------

class TestDataSourcesGating:
    """_format_section_data() respects the data_sources list on each section."""

    def test_time_entries_excluded_when_not_in_data_sources(self):
        """Section with data_sources=["notes"] does not include time entry content."""
        builder = _mock_builder()
        section = {"type": "work", "data_sources": ["notes"]}

        result = builder._get_section_data(section, _SENTINEL, _DAILY_TEMPLATE)

        assert "Work Entries" not in result
        builder.time_repo.get_for_date_client.assert_not_called()

    def test_time_entries_included_when_in_data_sources(self):
        """Section with data_sources=["notes","time_entries"] includes time entry content."""
        builder = _mock_builder()
        entry = _mock_time_entry("Deployment pipeline work", hours=2.0)
        builder.time_repo.get_for_date_client.return_value = [entry]
        section = {"type": "work", "data_sources": ["notes", "time_entries"]}

        result = builder._get_section_data(section, _SENTINEL, _DAILY_TEMPLATE)

        assert "Work Entries" in result
        assert "Deployment pipeline work" in result


# ---------------------------------------------------------------------------
# client filter forwarding
# ---------------------------------------------------------------------------

class TestClientFilterForwarding:
    """filter_client=True is correctly passed to time_repo.get_for_date_client()."""

    def test_client_report_excludes_internal_only_time_entries(self):
        """With filter_client=True the repo is queried with filter_client=True; no internal entries surface."""
        builder = _mock_builder()
        # Repo returns empty when filter_client=True (simulates DB excluding internal-only entries
        # with client_id=None from a filtered query)
        builder.time_repo.get_for_date_client.return_value = []
        builder._filter_client = True
        builder._client_id = 1
        section = {"type": "work", "data_sources": ["notes", "time_entries"]}

        result = builder._get_section_data(section, _SENTINEL, _DAILY_TEMPLATE)

        assert "Work Entries" not in result
        builder.time_repo.get_for_date_client.assert_called_once_with(
            start_date=_SENTINEL,
            end_date=_SENTINEL,
            client_id=1,
            filter_client=True,
        )

    def test_client_report_includes_client_report_time_entries(self):
        """With filter_client=True, entries returned by the repo appear in the prompt string."""
        builder = _mock_builder()
        entry = _mock_time_entry("Client deliverable X", hours=3.0)
        builder.time_repo.get_for_date_client.return_value = [entry]
        builder._filter_client = True
        builder._client_id = 1
        section = {"type": "work", "data_sources": ["notes", "time_entries"]}

        result = builder._get_section_data(section, _SENTINEL, _DAILY_TEMPLATE)

        assert "Client deliverable X" in result
        assert "Work Entries" in result


# ---------------------------------------------------------------------------
# preview_report filter parity
# ---------------------------------------------------------------------------

class TestPreviewReportFilterParity:
    """preview_report() forwards filter_client and client_id to prompt_builder.build_prompt()."""

    def test_preview_report_applies_client_filter(self):
        """preview_report(filter_client=True, client_id=1) passes those args to build_prompt."""
        mock_pb = MagicMock()
        mock_pb.build_prompt.return_value = ("system prompt", "user prompt")
        mock_pb.estimate_tokens.return_value = 500
        mock_tl = MagicMock()
        mock_tl.load.return_value = {"metadata": {"ai_provider": "claude"}}

        generator = ReportGenerator(
            session=MagicMock(),
            prompt_builder=mock_pb,
            provider_manager=MagicMock(),
            cost_tracker=MagicMock(),
            template_loader=mock_tl,
            reports_repository=MagicMock(),
        )

        generator.preview_report(
            template_name="daily_internal",
            report_date=_SENTINEL,
            filter_client=True,
            client_id=1,
        )

        mock_pb.build_prompt.assert_called_once_with(
            template_name="daily_internal",
            report_date=_SENTINEL,
            filter_client=True,
            client_id=1,
        )
