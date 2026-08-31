"""Tests for automation/closeout_acs.py, named for the AC they cover (§6, AC6.1)."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"

_spec = importlib.util.spec_from_file_location(
    "closeout_acs", ROOT / "automation" / "closeout_acs.py"
)
ca = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ca)


def fixture_text(name):
    return (FIXTURES / name).read_text()


BRANCH = "chore/issue-999-fixture"


# ---------------------------------------------------------------------------
# AC1.1, AC1.2 — parsing
# ---------------------------------------------------------------------------

def test_ac1_1_spec_ac_ids_parse_from_5_table_by_identifier():
    ids = ca.parse_spec_ac_ids(fixture_text("closeout_spec_clean.md"))
    assert ids == ["AC1.1", "AC1.2", "AC2.1"]


def test_ac1_2_artifact_ac_rows_parse_to_id_status_evidence():
    rows = ca.parse_artifact_ac_rows(fixture_text("closeout_results_clean.md"))
    assert rows == [
        ("AC1.1", "Met", "`pytest automation/closeout_acs_test.py` passes"),
        ("AC1.2", "Met", "`pytest automation/closeout_acs_test.py` passes"),
        ("AC2.1", "Met", "`pytest automation/closeout_acs_test.py` passes"),
    ]


def test_ac1_2_evidence_cell_may_quote_an_escaped_pipe():
    rows = ca.parse_artifact_ac_rows(fixture_text("closeout_results_escaped_pipe.md"))
    assert rows == [
        ("AC1.1", "Met", "`grep -cE '^| P[0-9]+ |'` returns `11`"),
    ]


# ---------------------------------------------------------------------------
# AC1.3 - AC1.6 — the AC guard's verdict
# ---------------------------------------------------------------------------

def test_ac1_3_missing_ac_row_fails_naming_the_id():
    spec_ids = ["AC1.1", "AC1.2", "AC2.1"]
    rows = ca.parse_artifact_ac_rows(fixture_text("closeout_results_missing_row.md"))
    failures = ca.evaluate(spec_ids, rows)
    assert any("AC2.1" in f for f in failures)


def test_ac1_4_not_met_and_uncited_carried_both_fail():
    not_met_rows = ca.parse_artifact_ac_rows(fixture_text("closeout_results_not_met.md"))
    assert ca.evaluate(["AC1.1"], not_met_rows) != []

    carried_rows = ca.parse_artifact_ac_rows(fixture_text("closeout_results_carried_uncited.md"))
    assert ca.evaluate(["AC1.1"], carried_rows) != []


def test_ac1_5_met_row_with_empty_evidence_fails_naming_the_id():
    rows = ca.parse_artifact_ac_rows(fixture_text("closeout_results_unevidenced_met.md"))
    failures = ca.evaluate(["AC1.1"], rows)
    assert any("AC1.1" in f for f in failures)


def test_ac1_6_extra_row_fails_naming_the_id():
    rows = ca.parse_artifact_ac_rows(fixture_text("closeout_results_extra_row.md"))
    failures = ca.evaluate(["AC1.1"], rows)
    assert any("AC9.9" in f for f in failures)


# ---------------------------------------------------------------------------
# AC1.7 — path derivation
# ---------------------------------------------------------------------------

def test_ac1_7_one_match_derives_the_results_path():
    specs_dir = FIXTURES / "closeout_specs_one_match"
    spec_label, spec_text, error = ca.find_spec(BRANCH, (specs_dir,))
    assert error is None
    assert spec_text is not None
    results_path, error = ca.derive_results_path(spec_label)
    assert error is None
    assert results_path == specs_dir.parent / "results" / "ONLY_SUBJECT_RESULTS.md"


def test_ac1_7_no_match_fails():
    specs_dir = FIXTURES / "closeout_specs_no_match"
    spec_label, spec_text, error = ca.find_spec(BRANCH, (specs_dir,))
    assert spec_label is None
    assert error is not None


def test_ac1_7_two_matches_fails_naming_both():
    specs_dir = FIXTURES / "closeout_specs_two_match"
    spec_label, spec_text, error = ca.find_spec(BRANCH, (specs_dir,))
    assert spec_label is None
    assert "A_SUBJECT_SPEC.md" in error
    assert "B_SUBJECT_SPEC.md" in error


def test_ac1_7_unparseable_filename_fails_naming_it():
    specs_dir = FIXTURES / "closeout_specs_bad_filename"
    spec_label, spec_text, error = ca.find_spec(BRANCH, (specs_dir,))
    assert error is None
    results_path, error = ca.derive_results_path(spec_label)
    assert results_path is None
    assert "WEIRD_NAME.md" in error


# ---------------------------------------------------------------------------
# AC1.8 — exit codes distinguish nothing-to-compare from a real AC failure
# ---------------------------------------------------------------------------

def _wire(monkeypatch, tmp_path, spec_text, results_text=None):
    monkeypatch.setattr(ca, "ROOT", tmp_path)
    specs_dir = tmp_path / "docs" / "dev" / "specs"
    specs_dir.mkdir(parents=True)
    (specs_dir / "FIXTURE_SPEC.md").write_text(spec_text)
    if results_text is not None:
        results_dir = tmp_path / "docs" / "dev" / "results"
        results_dir.mkdir(parents=True)
        (results_dir / "FIXTURE_RESULTS.md").write_text(results_text)


def test_ac1_8_no_spec_exits_2(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(ca, "ROOT", tmp_path)
    (tmp_path / "docs" / "dev" / "specs").mkdir(parents=True)
    exit_code = ca.main(["--branch", BRANCH])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.err != ""


def test_ac1_8_resolved_spec_missing_artifact_exits_2_naming_path(monkeypatch, tmp_path, capsys):
    _wire(monkeypatch, tmp_path, fixture_text("closeout_spec_clean.md"))
    exit_code = ca.main(["--branch", BRANCH])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "FIXTURE_RESULTS.md" in captured.err


def test_ac1_8_ac_failure_exits_1(monkeypatch, tmp_path, capsys):
    _wire(
        monkeypatch, tmp_path,
        fixture_text("closeout_spec_clean.md"),
        fixture_text("closeout_results_missing_row.md"),
    )
    exit_code = ca.main(["--branch", BRANCH])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "AC2.1" in captured.err


def test_ac1_8_clean_run_exits_0(monkeypatch, tmp_path, capsys):
    _wire(
        monkeypatch, tmp_path,
        fixture_text("closeout_spec_clean.md"),
        fixture_text("closeout_results_clean.md"),
    )
    exit_code = ca.main(["--branch", BRANCH])
    assert exit_code == 0


# ---------------------------------------------------------------------------
# AC1.9 — an empty spec-id set fails rather than passing vacuously
# ---------------------------------------------------------------------------

def test_ac1_9_bare_acn_ids_yield_empty_set_and_fail():
    ids = ca.parse_spec_ac_ids(fixture_text("closeout_spec_bare_acn.md"))
    assert ids == []
    failures = ca.evaluate(ids, [("AC1", "Met", "evidence")])
    assert len(failures) == 1
    assert "no ACn.m ids" in failures[0]


def test_ac1_9_bare_acn_spec_exits_1_through_main(monkeypatch, tmp_path, capsys):
    _wire(
        monkeypatch, tmp_path,
        fixture_text("closeout_spec_bare_acn.md"),
        fixture_text("closeout_results_clean.md"),
    )
    exit_code = ca.main(["--branch", BRANCH])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "no ACn.m ids" in captured.err


# ---------------------------------------------------------------------------
# AC2.3, AC2.4 — the archived set stays resolvable, so close-out can re-enter
# ---------------------------------------------------------------------------

def _wire_archived(monkeypatch, tmp_path, spec_text, results_text):
    """A set that has already been archived: nothing under docs/dev/ at all."""
    monkeypatch.setattr(ca, "ROOT", tmp_path)
    (tmp_path / "docs" / "dev" / "specs").mkdir(parents=True)
    (tmp_path / "docs" / "dev" / "results").mkdir(parents=True)
    specs_dir = tmp_path / "docs" / "archive" / "specs"
    specs_dir.mkdir(parents=True)
    (specs_dir / "FIXTURE_SPEC.md").write_text(spec_text)
    results_dir = tmp_path / "docs" / "archive" / "results"
    results_dir.mkdir(parents=True)
    (results_dir / "FIXTURE_RESULTS.md").write_text(results_text)


def test_ac2_3_archived_set_resolves_and_passes(monkeypatch, tmp_path, capsys):
    _wire_archived(
        monkeypatch,
        tmp_path,
        fixture_text("closeout_spec_clean.md"),
        fixture_text("closeout_results_clean.md"),
    )
    exit_code = ca.main(["--branch", BRANCH])
    assert exit_code == 0
    assert capsys.readouterr().err == ""


def test_ac2_3_results_root_follows_the_spec_root():
    """DR6 — a set is archived whole, so the results artifact is looked for beside
    the spec rather than at a fixed docs/dev/ constant."""
    archived, error = ca.derive_results_path("docs/archive/specs/SUBJECT_SPEC.md")
    assert error is None
    assert archived == Path("docs/archive/results/SUBJECT_RESULTS.md")

    live, error = ca.derive_results_path("docs/dev/specs/SUBJECT_SPEC.md")
    assert error is None
    assert live == Path("docs/dev/results/SUBJECT_RESULTS.md")


def test_ac2_4_spec_in_both_roots_is_reported_not_resolved(monkeypatch, tmp_path):
    """A half-finished move leaves the spec in both roots. Resolving it silently
    would pick one arbitrarily; the collision is the existing two-match failure."""
    monkeypatch.setattr(ca, "ROOT", tmp_path)
    spec_text = fixture_text("closeout_spec_clean.md")
    for root in ("docs/dev/specs", "docs/archive/specs"):
        d = tmp_path / root
        d.mkdir(parents=True)
        (d / "FIXTURE_SPEC.md").write_text(spec_text)

    spec_label, _, error = ca.find_spec(BRANCH, ca.SPEC_ROOTS)
    assert spec_label is None
    assert "more than one spec" in error


def test_ac2_3_live_root_wins_when_a_stale_copy_sits_in_the_archive():
    """DR5 — dev-first ordering, asserted on the constant itself so a reordering
    that would make close-out prefer an archived spec fails here."""
    assert ca.SPEC_ROOTS == (Path("docs/dev/specs"), Path("docs/archive/specs"))
