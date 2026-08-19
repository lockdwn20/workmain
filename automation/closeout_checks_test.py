"""Tests for automation/closeout_checks.py, named for the AC they cover (§6, AC6.1)."""

import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"

_spec = importlib.util.spec_from_file_location(
    "closeout_checks", ROOT / "automation" / "closeout_checks.py"
)
cc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cc)


def fixture_text(name):
    return (FIXTURES / name).read_text()


# ---------------------------------------------------------------------------
# AC1 — Issue resolution and AC parsing
# ---------------------------------------------------------------------------

def test_ac1_1_acs_shape_parses_one_per_bullet():
    acs = cc.parse_acs(fixture_text("closeout_issue_bullets.md"))
    assert acs == [
        "First AC, walks every check",
        "Second AC, cannot report success early",
        "Third AC, is the final line of the body",
    ]


def test_ac1_2_checkbox_shape_parses_and_discards_checkbox_state():
    acs = cc.parse_acs(fixture_text("closeout_issue_checkbox.md"))
    assert acs == ["First unchecked AC", "Second checked AC, checkbox state discarded"]
    assert all("[" not in ac for ac in acs)


def test_ac1_3_no_ac_section_is_reported_not_failed():
    acs = cc.parse_acs(fixture_text("closeout_issue_no_acs.md"))
    assert acs == []


def test_ac1_4_acs_parse_runs_to_end_of_body():
    acs = cc.parse_acs(fixture_text("closeout_issue_bullets.md"))
    assert acs[-1] == "Third AC, is the final line of the body"


def test_ac1_5_continuation_line_joined_in_both_shapes():
    bullet_acs = cc.parse_acs(fixture_text("closeout_issue_bullets_continuation.md"))
    assert bullet_acs == [
        "First AC, whose text spans two physical lines",
        "Second AC, single line",
    ]

    checkbox_acs = cc.parse_acs(fixture_text("closeout_issue_checkbox_continuation.md"))
    assert checkbox_acs == [
        "First AC, whose text spans two physical lines",
        "Second AC, single line",
    ]


def test_ac1_6_failure_to_resolve_issue_aborts(monkeypatch, capsys):
    monkeypatch.setattr(cc, "gh_issue_view", lambda number: None)
    exit_code = cc.run(999)
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "999" in captured.err
    assert captured.out == ""


# ---------------------------------------------------------------------------
# AC2 — Branch resolution and branch type
# ---------------------------------------------------------------------------

def test_ac2_1_branch_flag_overrides_derivation(monkeypatch):
    monkeypatch.setattr(cc, "git_merge_log", lambda ref: [("deadbeef", "Merge branch 'hotfix/issue-123-other'")])
    monkeypatch.setattr(cc, "git_ref_exists", lambda ref: False)
    res = cc.resolve_branch(123, explicit_branch="chore/whatever-123")
    assert res.name == "chore/whatever-123"
    assert res.branch_type == "chore"


def test_ac2_2_derivation_tries_main_then_dev(monkeypatch):
    def merge_log(ref):
        if ref == "main":
            return [("aaa111", "Merge branch 'chore/issue-50-docs'")]
        return []

    monkeypatch.setattr(cc, "git_merge_log", merge_log)
    monkeypatch.setattr(cc, "git_diff_paths", lambda a, b: [])
    res_a = cc.resolve_branch(50)
    assert res_a.resolved_on == "main"
    assert res_a.name == "chore/issue-50-docs"

    def merge_log_feature(ref):
        if ref == "main":
            return []
        if ref == "dev":
            return [("bbb222", "Merge feature/issue-60-thing into dev")]
        return []

    monkeypatch.setattr(cc, "git_merge_log", merge_log_feature)
    res_b = cc.resolve_branch(60)
    assert res_b.resolved_on == "dev"
    assert res_b.name == "feature/issue-60-thing"


def test_ac2_3_unresolvable_branch_is_a_finding_not_an_abort(monkeypatch, capsys):
    monkeypatch.setattr(cc, "gh_issue_view", lambda number: {
        "body": "**ACs**\n\n- Only AC\n"
    })
    monkeypatch.setattr(cc, "git_merge_log", lambda ref: [])
    monkeypatch.setattr(cc, "run_pytest", lambda args: (0, "ok"))

    exit_code = cc.run(404)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "could not be resolved" in captured.err
    assert "issue ACs" in captured.out
    assert "application suite" in captured.out


def test_ac2_4_changed_paths_from_merge_commit_parents_not_branch_ref(monkeypatch):
    monkeypatch.setattr(
        cc, "git_merge_log",
        lambda ref: [("cccc333", "Merge branch 'chore/issue-70-thing'")] if ref == "main" else [],
    )

    def diff_paths(a, b):
        assert a == "cccc333^1"
        assert b == "cccc333^2"
        return ["workmain/x.py"]

    monkeypatch.setattr(cc, "git_diff_paths", diff_paths)

    def ref_exists(ref):
        raise AssertionError("git_ref_exists must not be called on the derived-branch path")

    monkeypatch.setattr(cc, "git_ref_exists", ref_exists)

    res = cc.resolve_branch(70)
    assert res.changed_paths == ["workmain/x.py"]


def test_ac2_5_unknown_prefix_fails_naming_it():
    res = cc.resolve_branch(99, explicit_branch="spike/issue-99-thing")
    assert res.error is not None
    assert "spike" in res.error


# ---------------------------------------------------------------------------
# AC3 — The workpaths
# ---------------------------------------------------------------------------

def _fake_resolution(branch_type, merge_sha="mmmm444", changed_paths=None):
    return cc.BranchResolution(
        name=f"{branch_type}/issue-1-thing",
        merge_sha=merge_sha,
        resolved_on="main",
        changed_paths=changed_paths or [],
        branch_type=branch_type,
    )


def _quiet_workpath_seams(monkeypatch, version_before="1.29.0", version_after="1.30.0"):
    monkeypatch.setattr(cc, "read_version_at", lambda ref: version_before if ref.endswith("^1") else version_after)
    monkeypatch.setattr(cc, "run_check_release_integrity", lambda: (0, "ok"))
    monkeypatch.setattr(cc, "run_pytest", lambda args: (0, "ok"))
    monkeypatch.setattr(cc, "git_commit_timestamp", lambda ref: "2026-08-20T10:00:00+00:00")
    monkeypatch.setattr(cc, "get_active_enter_timestamp", lambda: "2026-08-20T11:00:00+00:00")
    monkeypatch.setattr(cc, "git_is_ancestor", lambda ref, target: True)
    monkeypatch.setattr(cc, "dev_merge_sha_for", lambda issue_number, resolution: "dddd555")


def test_ac3_1_branch_type_selects_rows_and_na_states_a_reason(monkeypatch):
    _quiet_workpath_seams(monkeypatch, version_before="1.29.0", version_after="1.29.0")
    checks = cc.evaluate_workpaths(1, _fake_resolution("chore"))
    release_rows = {c.name: c for c in checks if c.name in (
        "version bump", "changelog entry for the new version",
        "tag for the new version", "GitHub Release for the tag",
    )}
    assert len(release_rows) == 4
    for check in release_rows.values():
        assert check.status == "n/a"
        assert "§2.2" in check.detail

    _quiet_workpath_seams(monkeypatch, version_before="1.29.0", version_after="1.30.0")
    feature_checks = cc.evaluate_workpaths(1, _fake_resolution("feature"))
    feature_release_rows = {c.name: c for c in feature_checks if c.name in release_rows}
    assert all(c.status != "n/a" for c in feature_release_rows.values())


def test_ac3_2_chore_branch_that_bumped_version_fails(monkeypatch):
    _quiet_workpath_seams(monkeypatch, version_before="1.29.0", version_after="1.30.0")
    check = cc.check_version_bump(_fake_resolution("chore"))
    assert check.status == "fail"
    assert "1.29.0" in check.detail and "1.30.0" in check.detail


def test_ac3_3_bump_magnitude_checked_per_type(monkeypatch):
    monkeypatch.setattr(cc, "read_version_at", lambda ref: "1.29.0" if ref.endswith("^1") else "1.29.1")
    feature_check = cc.check_version_bump(_fake_resolution("feature"))
    assert feature_check.status == "fail"

    hotfix_check = cc.check_version_bump(_fake_resolution("hotfix"))
    assert hotfix_check.status == "pass"


def test_ac3_4_release_object_checked_for_feature_and_hotfix(monkeypatch):
    monkeypatch.setattr(cc, "run_check_release_integrity", lambda: (1, "no Release found for v1.30.0"))
    checks = cc.check_release_ledger("feature")
    release_row = next(c for c in checks if c.name == "GitHub Release for the tag")
    assert release_row.status == "fail"
    assert "v1.30.0" in release_row.detail


def test_ac3_5_daemon_check_fires_on_feature_and_hotfix_not_chore(monkeypatch):
    monkeypatch.setattr(cc, "dev_merge_sha_for", lambda issue_number, resolution: "dddd555")
    monkeypatch.setattr(cc, "git_commit_timestamp", lambda ref: "2026-08-20T12:00:00+00:00")
    monkeypatch.setattr(cc, "get_active_enter_timestamp", lambda: "2026-08-20T09:00:00+00:00")

    feature_check = cc.check_daemon_restart("feature", 1, _fake_resolution("feature"))
    assert feature_check.status == "fail"

    hotfix_check = cc.check_daemon_restart("hotfix", 1, _fake_resolution("hotfix"))
    assert hotfix_check.status == "fail"

    chore_check = cc.check_daemon_restart("chore", 1, _fake_resolution("chore"))
    assert chore_check.status == "n/a"


def test_ac3_6_check_release_integrity_is_invoked_not_reimplemented():
    source = (ROOT / "automation" / "closeout_checks.py").read_text()
    assert len(re.findall(r"check_release_integrity", source)) >= 1
    assert len(re.findall(r"CHANGELOG", source)) == 0
    assert len(re.findall(r"gh release view", source)) == 0


def test_ac3_7_failing_application_suite_fails_every_branch_type(monkeypatch):
    monkeypatch.setattr(cc, "run_pytest", lambda args: (1, "FAILED tests/test_x.py"))
    for branch_type in ("chore", "feature", "hotfix"):
        check = cc.check_application_suite()
        assert check.status == "fail"


def test_ac3_8_automation_suite_runs_only_when_touched(monkeypatch):
    monkeypatch.setattr(cc, "run_pytest", lambda args: (0, "ok"))
    touched = cc.check_automation_suite(["automation/x.py"])
    assert touched.status == "pass"

    not_touched = cc.check_automation_suite(["docs/x.md"])
    assert not_touched.status == "n/a"


def test_ac3_9_merge_targets_checked_per_branch_type(monkeypatch):
    monkeypatch.setattr(cc, "git_is_ancestor", lambda ref, target: target == "main")
    chore_check = cc.check_merge_targets("chore", _fake_resolution("chore"))
    assert chore_check.status == "fail"
    assert "dev" in chore_check.detail

    monkeypatch.setattr(cc, "git_is_ancestor", lambda ref, target: target == "dev")
    feature_check_b = cc.check_merge_targets("feature", _fake_resolution("feature"))
    assert feature_check_b.status == "pass"

    monkeypatch.setattr(cc, "git_is_ancestor", lambda ref, target: False)
    feature_check_c = cc.check_merge_targets("feature", _fake_resolution("feature"))
    assert feature_check_c.status == "fail"


# ---------------------------------------------------------------------------
# AC4 — Results artifact and verdict
# ---------------------------------------------------------------------------

def test_ac4_1_missing_results_artifact_fails(tmp_path):
    missing_path = tmp_path / "docs" / "dev" / "results" / "NOTHING_HERE_RESULTS.md"
    checks = cc.verify_results_artifact(missing_path, ["Only AC text"])
    assert checks[0].status == "fail"
    assert str(missing_path) in checks[0].detail


def test_ac4_2_bad_status_fails():
    checks = cc.verify_results_artifact(
        FIXTURES / "closeout_results_bad_status.md", ["Only AC text"],
    )
    status_check = next(c for c in checks if c.name == "results artifact status")
    assert status_check.status == "fail"
    assert "Active" in status_check.detail


def test_ac4_3_dropped_ac_fails():
    checks = cc.verify_results_artifact(
        FIXTURES / "closeout_results_dropped_ac.md",
        ["First AC text", "Second AC text", "Third AC text"],
    )
    coverage_check = next(c for c in checks if c.name == "every issue AC appears in the table")
    assert coverage_check.status == "fail"
    assert "Third AC text" in coverage_check.detail


def test_ac4_4_not_met_and_uncited_carried_both_fail():
    not_met_checks = cc.verify_results_artifact(
        FIXTURES / "closeout_results_not_met.md", ["Only AC text"],
    )
    not_met_status = next(c for c in not_met_checks if c.name == "every row is Met or a cited Carried")
    assert not_met_status.status == "fail"

    carried_checks = cc.verify_results_artifact(
        FIXTURES / "closeout_results_carried_uncited.md", ["Only AC text"],
    )
    carried_status = next(c for c in carried_checks if c.name == "every row is Met or a cited Carried")
    assert carried_status.status == "fail"


def _wire_clean_run(monkeypatch, tmp_path, issue_number=42, branch_type="chore"):
    monkeypatch.setattr(cc, "ROOT", tmp_path)

    specs_dir = tmp_path / "docs" / "dev" / "specs"
    specs_dir.mkdir(parents=True)
    branch_name = f"{branch_type}/issue-{issue_number}-thing"
    (specs_dir / "FIXTURE_SPEC.md").write_text(f"**Branch:** `{branch_name}`\n")

    results_dir = tmp_path / "docs" / "dev" / "results"
    results_dir.mkdir(parents=True)
    (results_dir / "FIXTURE_RESULTS.md").write_text(fixture_text("closeout_results_clean.md"))

    issue_body = (
        "**ACs**\n\n"
        "- First AC text\n"
        "- Second AC text\n"
        "- Third AC text\n"
    )
    monkeypatch.setattr(cc, "gh_issue_view", lambda number: {"body": issue_body})
    monkeypatch.setattr(
        cc, "git_merge_log",
        lambda ref: [("mmmm666", f"Merge branch '{branch_name}'")] if ref == "main" else [],
    )
    monkeypatch.setattr(cc, "git_diff_paths", lambda a, b: [])
    _quiet_workpath_seams(monkeypatch, version_before="1.29.0", version_after="1.29.0")
    return branch_name


def test_ac4_5_clean_case_exits_zero(monkeypatch, tmp_path, capsys):
    _wire_clean_run(monkeypatch, tmp_path)
    exit_code = cc.run(42)
    assert exit_code == 0


def test_ac4_6_passing_run_prints_postable_comment_failing_run_does_not(monkeypatch, tmp_path, capsys):
    _wire_clean_run(monkeypatch, tmp_path)
    exit_code = cc.run(42)
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "gh issue comment" in captured.out
    assert "mmmm666" in captured.out
    assert "FIXTURE_RESULTS.md" in captured.out

    monkeypatch.setattr(cc, "run_pytest", lambda args: (1, "boom"))
    exit_code_fail = cc.run(42)
    captured_fail = capsys.readouterr()
    assert exit_code_fail == 1
    assert "gh issue comment" not in captured_fail.out
