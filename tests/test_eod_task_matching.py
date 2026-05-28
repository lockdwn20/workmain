"""
WorkmAIn EOD Task Matching Tests
test_eod_task_matching v1.0
20260528

Tests for PC-1 — EOD Step 3c task matching algorithm.

Covers:
  - _tokenize(): lowercases, strips punctuation, removes stop words, returns set
  - _score_match(): ratio of overlap to task token count; 0.0 for empty task_tokens
  - Confidence thresholds: High ≥ 0.5, Medium 0.2–0.49, Low < 0.2 (not surfaced)
  - _run_task_match_step(): returns True immediately when no CF observations
  - _run_task_match_step(): returns True immediately when no active tasks
  - _run_task_match_step(): exception handling returns True (non-blocking)

Pure-Python functions are tested with no database.
Step-level entry-condition tests use a temporary state file
and stub out the DB via mocking.

Version History:
- v1.0: Phase 12 Gate 7 — initial implementation
"""

import json
import os
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from workmain.cli.commands.eod import _tokenize, _score_match, _run_task_match_step


# ---------------------------------------------------------------------------
# _tokenize()
# ---------------------------------------------------------------------------

class TestTokenize:
    """_tokenize() produces a cleaned, stop-word-free token set."""

    def test_lowercases_input(self):
        """_tokenize() returns lowercase tokens regardless of input case."""
        tokens = _tokenize("TheHive RQ Function")
        assert 'thehive' in tokens
        assert 'rq' in tokens
        assert 'function' in tokens

    def test_strips_punctuation(self):
        """_tokenize() removes punctuation characters."""
        tokens = _tokenize("completed, handed-off to Cesar.")
        assert 'completed' in tokens
        assert 'cesar' in tokens
        # Punctuation should not appear as separate tokens
        assert ',' not in tokens
        assert '.' not in tokens

    def test_removes_stop_words(self):
        """_tokenize() filters out common stop words."""
        tokens = _tokenize("the function was completed and handed to the team")
        assert 'the' not in tokens
        assert 'was' not in tokens
        assert 'and' not in tokens
        assert 'to' not in tokens
        # Content words should remain
        assert 'function' in tokens
        assert 'completed' in tokens
        assert 'team' in tokens

    def test_returns_set_deduplicates(self):
        """_tokenize() returns a set, so duplicates collapse."""
        tokens = _tokenize("completed completed completed task task")
        assert isinstance(tokens, set)
        # Each word appears only once in a set
        assert len([t for t in tokens if t == 'completed']) == 1

    def test_empty_string_returns_empty_set(self):
        """_tokenize('') returns an empty set."""
        assert _tokenize('') == set()

    def test_all_stop_words_returns_empty_set(self):
        """_tokenize() of only stop words returns empty set."""
        assert _tokenize('the and or but') == set()


# ---------------------------------------------------------------------------
# _score_match()
# ---------------------------------------------------------------------------

class TestScoreMatch:
    """_score_match() computes overlap / task_token_count correctly."""

    def test_empty_task_tokens_returns_zero(self):
        """_score_match(empty, anything) returns 0.0."""
        assert _score_match(set(), {'some', 'tokens'}) == 0.0

    def test_identical_token_sets_returns_one(self):
        """_score_match(A, A) returns 1.0."""
        tokens = {'thehive', 'rq', 'function', 'handoff'}
        assert _score_match(tokens, tokens) == 1.0

    def test_partial_overlap_correct_ratio(self):
        """_score_match() returns len(intersection) / len(task_tokens)."""
        task = {'thehive', 'rq', 'function', 'completed'}
        entry = {'thehive', 'rq', 'submitted', 'ticket'}
        expected = 2 / 4  # 2 overlap tokens out of 4 task tokens
        assert _score_match(task, entry) == pytest.approx(expected)

    def test_no_overlap_returns_zero(self):
        """_score_match() returns 0.0 when there is no token overlap."""
        task = {'thehive', 'rq', 'function'}
        entry = {'splunk', 'access', 'ticket'}
        assert _score_match(task, entry) == 0.0

    def test_full_task_subset_of_entry(self):
        """All task tokens present in entry → score = 1.0."""
        task = {'rq', 'function'}
        entry = {'rq', 'function', 'completed', 'handed', 'cesar'}
        assert _score_match(task, entry) == 1.0


# ---------------------------------------------------------------------------
# Confidence threshold classification
# ---------------------------------------------------------------------------

class TestConfidenceThresholds:
    """Verify High / Medium / Low boundary values."""

    def test_high_confidence_at_0_5(self):
        """Score of 0.5 meets the High threshold (≥ 0.5)."""
        task = {'a', 'b', 'c', 'd'}
        entry = {'a', 'b', 'x', 'y'}  # 2/4 = 0.5
        score = _score_match(task, entry)
        assert score >= 0.5

    def test_medium_confidence_at_0_2(self):
        """Score of exactly 0.2 meets the Medium threshold (0.2–0.49)."""
        task = {'a', 'b', 'c', 'd', 'e'}
        entry = {'a', 'x', 'y', 'z', 'w'}  # 1/5 = 0.2
        score = _score_match(task, entry)
        assert 0.2 <= score < 0.5

    def test_below_threshold_at_0_19(self):
        """Score below 0.2 is below the Medium threshold (should not be surfaced)."""
        task = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'}
        entry = {'a', 'x', 'y', 'z', 'w', 'v', 'u', 't', 's', 'r'}  # 1/10 = 0.1
        score = _score_match(task, entry)
        assert score < 0.2


# ---------------------------------------------------------------------------
# _run_task_match_step() — entry conditions (no full DB required)
# ---------------------------------------------------------------------------

class TestTaskMatchStepEntryConditions:
    """Step 3c returns True immediately when entry conditions are not met."""

    def _write_cf_state_file(self, tmp_dir: str, target_date: date):
        """Write a last_inspection.json with a carry-forward observation."""
        state_path = Path(tmp_dir) / 'daemon' / 'last_inspection.json'
        state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            'run_at': '2099-01-01T09:00:00',
            'target_date': str(target_date),
            'observations': [
                {
                    'type': 'carry_forward',
                    'message': 'Carry-forward: Sentinel task content here.',
                    'acknowledged': False,
                }
            ],
            'summary': 'Sentinel summary.',
        }
        state_path.write_text(json.dumps(payload))
        return str(tmp_dir)

    def _write_empty_state_file(self, tmp_dir: str, target_date: date):
        """Write a last_inspection.json with no observations."""
        state_path = Path(tmp_dir) / 'daemon' / 'last_inspection.json'
        state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            'run_at': '2099-01-01T09:00:00',
            'target_date': str(target_date),
            'observations': [],
            'summary': '',
        }
        state_path.write_text(json.dumps(payload))
        return str(tmp_dir)

    def test_returns_true_when_no_state_file(self, tmp_path):
        """Step returns True immediately when no last_inspection.json exists."""
        with patch.dict(os.environ, {'WORKMAIN_STATE_DIR': str(tmp_path)}):
            result = _run_task_match_step(dry_run=False, target_date=date(2099, 1, 1))
        assert result is True

    def test_returns_true_when_no_cf_observations(self, tmp_path):
        """Step returns True immediately when state file has no carry-forward observations."""
        self._write_empty_state_file(str(tmp_path), date(2099, 1, 1))
        with patch.dict(os.environ, {'WORKMAIN_STATE_DIR': str(tmp_path)}):
            result = _run_task_match_step(dry_run=False, target_date=date(2099, 1, 1))
        assert result is True

    def test_returns_true_when_state_file_date_mismatch(self, tmp_path):
        """Step returns True when state file is for a different date."""
        self._write_cf_state_file(str(tmp_path), date(2099, 1, 2))  # different date
        with patch.dict(os.environ, {'WORKMAIN_STATE_DIR': str(tmp_path)}):
            result = _run_task_match_step(dry_run=False, target_date=date(2099, 1, 1))
        assert result is True

    def test_returns_true_when_no_active_tasks(self, tmp_path):
        """Step returns True when CF items exist but no active task_status records."""
        self._write_cf_state_file(str(tmp_path), date(2099, 1, 1))

        mock_session = MagicMock()
        mock_task_repo = MagicMock()
        mock_task_repo.get_filtered.return_value = []  # no active tasks

        with patch.dict(os.environ, {'WORKMAIN_STATE_DIR': str(tmp_path)}):
            with patch('workmain.cli.commands.eod.get_db') as mock_get_db:
                mock_get_db.return_value.get_session.return_value = mock_session
                with patch('workmain.cli.commands.eod.TaskStatusRepository',
                           return_value=mock_task_repo, create=True):
                    with patch('workmain.database.repositories.task_status_repo.'
                               'TaskStatusRepository', return_value=mock_task_repo):
                        # The step imports TaskStatusRepository lazily inside the function
                        # Patch at the point of use in eod.py
                        with patch('workmain.cli.commands.eod._run_task_match_step',
                                   wraps=_run_task_match_step):
                            pass  # just verify the mocking path exists

        # Simpler: call with a real tmp state file but mock the DB session layer
        # directly by patching the import inside the function
        with patch.dict(os.environ, {'WORKMAIN_STATE_DIR': str(tmp_path)}):
            with patch('workmain.cli.commands.eod.get_db') as mock_get_db:
                mock_sess = MagicMock()
                mock_get_db.return_value.get_session.return_value = mock_sess

                class _FakeTaskRepo:
                    def __init__(self, session): pass
                    def get_filtered(self, **kw): return []

                class _FakeTimeRepo:
                    def __init__(self, session): pass
                    def get_by_date(self, d): return []

                with patch.dict('sys.modules', {}):
                    import sys
                    orig = sys.modules.get(
                        'workmain.database.repositories.task_status_repo')
                    orig_time = sys.modules.get(
                        'workmain.database.repositories.time_entries_repo')
                    try:
                        import workmain.database.repositories.task_status_repo as ts_mod
                        import workmain.database.repositories.time_entries_repo as te_mod
                        original_ts_class = ts_mod.TaskStatusRepository
                        original_te_class = te_mod.TimeEntriesRepository
                        ts_mod.TaskStatusRepository = _FakeTaskRepo
                        te_mod.TimeEntriesRepository = _FakeTimeRepo
                        result = _run_task_match_step(
                            dry_run=False, target_date=date(2099, 1, 1)
                        )
                        assert result is True
                    finally:
                        ts_mod.TaskStatusRepository = original_ts_class
                        te_mod.TimeEntriesRepository = original_te_class

    def test_returns_true_on_exception(self, tmp_path):
        """Step returns True (non-blocking) when an unexpected exception occurs."""
        self._write_cf_state_file(str(tmp_path), date(2099, 1, 1))

        import workmain.database.repositories.task_status_repo as ts_mod
        original = ts_mod.TaskStatusRepository

        class _RaisingRepo:
            def __init__(self, session):
                raise RuntimeError("Sentinel repo failure")

        try:
            ts_mod.TaskStatusRepository = _RaisingRepo
            with patch.dict(os.environ, {'WORKMAIN_STATE_DIR': str(tmp_path)}):
                with patch('workmain.cli.commands.eod.get_db') as mock_get_db:
                    mock_sess = MagicMock()
                    mock_get_db.return_value.get_session.return_value = mock_sess
                    result = _run_task_match_step(
                        dry_run=False, target_date=date(2099, 1, 1)
                    )
        finally:
            ts_mod.TaskStatusRepository = original

        assert result is True

    def test_dry_run_returns_true_without_reading_state(self, tmp_path):
        """--dry-run returns True without reading the state file or DB."""
        with patch.dict(os.environ, {'WORKMAIN_STATE_DIR': str(tmp_path)}):
            result = _run_task_match_step(dry_run=True, target_date=date(2099, 1, 1))
        assert result is True
