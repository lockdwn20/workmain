"""Tests for automation/issue_validator.py, named for the AC they cover (§6, AC4.1)."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"

_spec = importlib.util.spec_from_file_location(
    "issue_validator", ROOT / "automation" / "issue_validator.py"
)
issue_validator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(issue_validator)

SCHEMA = issue_validator.load_schema(ROOT / ".github" / "ISSUE_TEMPLATE" / "issue.schema.json")
TYPE_LABELS = issue_validator.parse_type_labels(ROOT / "docs" / "DEVELOPMENT_STANDARDS.md")
LIVE_LABELS = {"cli", "bug", "enhancement", "tests", "documentation"}
LIVE_MILESTONES = {"Phase 14 — Setup Wizard & Configuration"}


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


def fake_issue_state(open_numbers=(), closed_numbers=()):
    open_set = set(open_numbers)
    closed_set = set(closed_numbers)

    def get_issue_state(number):
        if number in closed_set:
            return "CLOSED"
        if number in open_set:
            return "OPEN"
        return None

    return get_issue_state


def run_validate(data, type_labels=TYPE_LABELS, live_labels=LIVE_LABELS, live_milestones=LIVE_MILESTONES, get_issue_state=None):
    if get_issue_state is None:
        get_issue_state = fake_issue_state(open_numbers=(100, 101, 102))
    return issue_validator.validate_issue(data, SCHEMA, type_labels, live_labels, live_milestones, get_issue_state)


class TestAC1:
    def test_ac1_4_shapes_satisfying_the_type_rule_validate(self):
        for name in (
            "shape_scheduled_standalone.json",
            "shape_scheduled_child.json",
            "shape_unscheduled_standalone.json",
            "shape_unscheduled_child.json",
        ):
            errors, _ = run_validate(fixture(name))
            assert errors == [], f"{name} unexpectedly failed: {errors}"

    def test_ac1_4_shapes_violating_the_type_rule_fail(self):
        for name in (
            "shape_invalid_unscheduled_no_type_standalone.json",
            "shape_invalid_unscheduled_no_type_child.json",
            "shape_invalid_scheduled_with_type_standalone.json",
            "shape_invalid_scheduled_with_type_child.json",
        ):
            errors, _ = run_validate(fixture(name))
            assert errors, f"{name} unexpectedly passed"


class TestAC2:
    def test_ac2_1_missing_required_key_names_it(self):
        errors, _ = run_validate(fixture("ac2_1_missing_milestone.json"))
        assert any("milestone" in e for e in errors)

    def test_ac2_2_unknown_key_names_it(self):
        errors, _ = run_validate(fixture("ac2_2_unknown_key.json"))
        assert any("mileston" in e for e in errors)

    def test_ac2_3_both_halves_of_the_type_rule_are_distinguishable(self):
        errors_a, _ = run_validate(fixture("shape_invalid_unscheduled_no_type_standalone.json"))
        errors_b, _ = run_validate(fixture("shape_invalid_scheduled_with_type_standalone.json"))
        assert "unscheduled issue carries no type label" in errors_a
        assert "a scheduled issue must not carry a type label" in errors_b
        assert errors_a != errors_b

    def test_ac2_4_type_label_inside_labels_fails(self):
        errors, _ = run_validate(fixture("ac2_4_type_label_in_labels.json"))
        assert any("type label" in e for e in errors)

    def test_ac2_5_nonexistent_label_milestone_and_parent_each_fail(self):
        errors, _ = run_validate(fixture("ac2_5_bad_label.json"))
        assert any("not-a-real-label" in e for e in errors)

        errors, _ = run_validate(fixture("ac2_5_bad_milestone.json"))
        assert any("Not A Real Milestone" in e for e in errors)

        errors, _ = run_validate(fixture("ac2_5_bad_parent.json"), get_issue_state=fake_issue_state())
        assert any("999999" in e and "does not exist" in e for e in errors)

    def test_ac2_6a_type_label_names_are_not_hardcoded(self):
        source = (ROOT / "automation" / "issue_validator.py").read_text()
        import re

        assert re.findall(r"['\"](bug|enhancement)['\"]", source) == []

    def test_ac2_6b_type_labels_are_parsed_from_the_standards_file(self):
        tokens = issue_validator.parse_type_labels(FIXTURES / "standards_alpha_beta.md")
        assert tokens == ["alpha", "beta"]
        assert "bug" not in tokens

    def test_ac2_7_validation_is_total(self):
        errors, _ = run_validate(fixture("ac2_7_three_errors.json"))
        assert any("unknown key: extra_bogus_key" in e for e in errors)
        assert any("not-a-real-label" in e for e in errors)
        assert any("type label" in e for e in errors)
        assert len(errors) >= 3

    def test_ac2_8_missing_discriminator_line_aborts_before_other_checks(self):
        with pytest.raises(issue_validator.ValidationAbort) as excinfo:
            issue_validator.parse_type_labels(FIXTURES / "standards_missing_discriminator.md")
        message = str(excinfo.value)
        assert "standards_missing_discriminator.md" in message
        assert "type discriminator" in message

    def test_ac2_9_closed_parent_is_reported_as_closed_not_missing(self):
        data = fixture("shape_scheduled_child.json")
        errors = issue_validator.validate_live_state(
            data, TYPE_LABELS, LIVE_LABELS, LIVE_MILESTONES, fake_issue_state(closed_numbers=(100,))
        )
        assert any("closed" in e for e in errors)
        assert not any("does not exist" in e for e in errors)

    def test_ac2_9_nonexistent_parent_is_reported_as_missing_not_closed(self):
        data = fixture("shape_scheduled_child.json")
        errors = issue_validator.validate_live_state(
            data, TYPE_LABELS, LIVE_LABELS, LIVE_MILESTONES, fake_issue_state()
        )
        assert any("does not exist" in e for e in errors)
        assert not any("closed" in e for e in errors)


class TestAC3:
    def test_ac3_1_default_run_creates_nothing(self, tmp_path, monkeypatch, capsys):
        issue_file = tmp_path / "issue.json"
        issue_file.write_text(json.dumps(fixture("valid_minimal.json")))

        monkeypatch.setattr(issue_validator, "gh_live_labels", lambda: LIVE_LABELS)
        monkeypatch.setattr(issue_validator, "gh_live_milestones", lambda: LIVE_MILESTONES)
        monkeypatch.setattr(issue_validator, "gh_issue_state", fake_issue_state())
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *a, **k: pytest.fail("gh issue create must not run without --create"),
        )

        exit_code = issue_validator.main([str(issue_file)])
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "gh issue create" in captured.out

    def test_ac3_2_printed_command_carries_every_populated_field(self, tmp_path):
        body_file = tmp_path / "body.md"
        cmd = issue_validator.build_command(fixture("valid_full.json"), body_file)
        assert "--title" in cmd
        assert "--body-file" in cmd
        assert "--parent" in cmd and "100" in cmd
        assert cmd.count("--label") == 3
        blocked_by_index = cmd.index("--blocked-by")
        assert cmd[blocked_by_index + 1] == "201,202"
        assert cmd.count("--blocked-by") == 1
        assert "--milestone" not in cmd  # valid_full.json's milestone is null

    def test_ac3_3_project_flag_always_present(self, tmp_path):
        body_file = tmp_path / "body.md"
        cmd = issue_validator.build_command(fixture("valid_minimal.json"), body_file)
        assert "--project" in cmd
        assert "WorkmAIn Queue" in cmd

    def test_ac3_4_type_flag_is_never_passed(self):
        source = (ROOT / "automation" / "issue_validator.py").read_text()
        assert source.count("--type") == 0

    def test_ac3_5_empty_blocked_by_and_blocking_omit_the_flag(self, tmp_path):
        body_file = tmp_path / "body.md"
        cmd = issue_validator.build_command(fixture("valid_minimal.json"), body_file)
        assert "--blocked-by" not in cmd
        assert "--blocking" not in cmd


class TestSchema:
    def test_new_skeleton_matches_schema_keys(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "automation" / "issue_validator.py"), "--new"],
            capture_output=True,
            text=True,
            check=True,
        )
        skeleton_keys = sorted(json.loads(result.stdout))
        assert skeleton_keys == sorted(SCHEMA)
