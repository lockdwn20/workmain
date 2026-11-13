"""
Tests for automation/style_check.py.

Each test that needs a branch builds a git repository in a temporary folder,
commits a base on main, cuts a working branch from it, and points the module
at it. Tests that run ruff are skipped when ruff is not installed.
"""

import importlib.util
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Dict, Optional

import pytest

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location("style_check", ROOT / "automation" / "style_check.py")
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)

needs_ruff = pytest.mark.skipif(shutil.which("ruff") is None, reason="ruff is not installed")

PYPROJECT = """
[tool.ruff]
target-version = "py312"

[tool.ruff.lint]
select = ["I", "D100", "D103", "D205", "D213", "ANN001", "ANN201"]

[tool.ruff.lint.isort]
known-first-party = ["workmain"]

[tool.ruff.lint.pydocstyle]
convention = "google"
"""

# An invented real value, unlike any real one; the fixture's .env lists it.
VALUE = "Qzx"
ENV = f"DEV_REAL_VALUES={VALUE}\n"

BASE = {
    ".gitignore": ".env\n",
    "pyproject.toml": PYPROJECT,
    "workmain/__init__.py": '"""\nThe application.\n"""\n',
    "workmain/old.py": (
        '"""Summary on the first line, which this repository\'s rules flag."""\n'
        "\n"
        "import os\n"
        "\n"
        "\n"
        "def untyped(x):\n"
        "    return os.sep\n"
    ),
    "docs/guide.md": "# Guide\n\nOne paragraph,\nwrapped before this branch existed.\n",
    "CHANGELOG.md": "# Changelog\n\n- An entry\n  wrapped long ago.\n",
}

Build = Callable[..., Path]


def _git(root: Path, *args: str) -> None:
    """Run git quietly in the test repository."""
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Build:
    """
    Provide a builder for a test repository with a working branch.

    Args:
        tmp_path: pytest's temporary folder for the test.
        monkeypatch: pytest's patcher, used to point the module at the folder.

    Returns:
        A function that commits BASE on main, writes an ignored `.env` listing
        VALUE, cuts `branch` from main, writes its `changes` into the working
        tree uncommitted, and returns the root.
    """

    def build(changes: Dict[str, str], branch: str = "chore/test") -> Path:
        for rel, text in BASE.items():
            path = tmp_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        (tmp_path / ".env").write_text(ENV)
        _git(tmp_path, "init", "-q", "-b", "main")
        _git(tmp_path, "add", "-A")
        _git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "base")
        _git(tmp_path, "checkout", "-q", "-b", branch)
        for rel, text in changes.items():
            path = tmp_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        monkeypatch.setattr(sc, "ROOT", tmp_path)
        return tmp_path

    return build


def violations(root: Path) -> list:
    """
    Check the test repository's working branch.

    Args:
        root: The repository built by `repo`.

    Returns:
        The violations, as `check` returns them.
    """
    return sc.check(sc.changed_lines("main"))


# ---------------------------------------------------------------- the base branch

def test_a_feature_branch_is_compared_with_dev() -> None:
    assert sc.base_branch("feature/issue-1-x") == "dev"


def test_any_other_branch_is_compared_with_main() -> None:
    assert sc.base_branch("chore/x") == "main"
    assert sc.base_branch("hotfix/issue-2-y") == "main"


# ---------------------------------------------------------------- Markdown

def _wrapped(text: str) -> list:
    """The line numbers `markdown_violations` reports for `text`."""
    return [line for _, line, _, _ in sc.markdown_violations("x.md", text)]


def test_a_paragraph_broken_across_lines_is_hard_wrapped() -> None:
    assert _wrapped("First half of a sentence\nand its second half.\n") == [2]


def test_a_list_item_broken_across_lines_is_hard_wrapped() -> None:
    assert _wrapped("- An item that runs\n  onto a second line.\n") == [2]


def test_blocks_of_their_own_are_not_wrapping() -> None:
    text = (
        "# Heading\n"
        "- one\n- two\n1. first\n2. second\n"
        "| a | b |\n| --- | --- |\n"
        "> a quote\n"
        "**Status:** Draft\n**Branch:** `chore/x`\n"
    )
    assert _wrapped(text) == []


def test_fenced_code_and_front_matter_are_not_checked() -> None:
    assert _wrapped("---\nname: x\ndescription: y\n---\n\n```text\nline one\nline two\n```\n") == []


def test_a_line_after_an_explicit_break_is_not_wrapping() -> None:
    assert _wrapped("Ends with two spaces  \nthen continues.\n\nEnds with a backslash\\\nthen continues.\n") == []


# ---------------------------------------------------------------- history citations

def _cited(text: str) -> list:
    """The citations `history_violations` reports for `text`."""
    return [message.split('"')[1] for _, _, _, message in sc.history_violations("workmain/x.py", text)]


def test_each_form_of_history_citation_is_found() -> None:
    text = "# Gate 5 §5.3\n# Gate 5A\n# Phase 11\n# per Operations_Config_Correction_Sprint\n# the Slack Sprint\n# Item 32 and Item #57\n# (OQ2)\n"
    assert _cited(text) == ["Gate 5", "Gate 5A", "Phase 11", "_Sprint", "Sprint", "Item 32", "Item #57", "OQ2"]


def test_ordinary_words_are_not_citations() -> None:
    assert _cited("# the gate opens in this phase; a sprint of items\n# Phase out the old reader\n") == []


def test_the_checker_and_its_tests_are_exempt() -> None:
    assert sc.history_violations("automation/style_check.py", "# Gate 5\n") == []


def test_a_citation_on_an_untouched_line_is_not_reported(repo: Build) -> None:
    text = BASE["workmain/old.py"].replace("import os\n", "import os  # Gate 5\n")
    repo({"workmain/old.py": text + "\n\ndef added() -> None:\n    \"\"\"Do nothing.\"\"\"\n"})
    found = [v for v in sc.check({"workmain/old.py": {9, 10, 11, 12}}) if "history" in v[3]]
    assert found == []


def test_a_citation_on_a_changed_line_is_reported(repo: Build) -> None:
    root = repo({"workmain/old.py": BASE["workmain/old.py"] + "\n\n# Phase 6 leftover\n"})
    found = [(path, line) for path, line, _, message in violations(root) if "history" in message]
    assert found == [("workmain/old.py", 10)]


# ---------------------------------------------------------------- changed lines

def test_only_the_lines_a_branch_changed_are_collected(repo: Build) -> None:
    repo({"workmain/old.py": BASE["workmain/old.py"] + "\n\ndef added() -> None:\n    pass\n"})
    changes = sc.changed_lines("main")
    assert changes["workmain/old.py"] == {8, 9, 10, 11}


def test_new_and_untracked_files_count_as_wholly_changed(repo: Build) -> None:
    root = repo({"workmain/new.py": '"""\nNew.\n"""\n'})
    _git(root, "add", "workmain/new.py")
    (root / "docs" / "untracked.md").write_text("# Untracked\n")
    changes = sc.changed_lines("main")
    assert changes["workmain/new.py"] is None
    assert changes["docs/untracked.md"] is None


def test_changelog_is_never_collected(repo: Build) -> None:
    repo({"CHANGELOG.md": BASE["CHANGELOG.md"] + "- Another entry\n  wrapped too.\n"})
    assert "CHANGELOG.md" not in sc.changed_lines("main")


# ---------------------------------------------------------------- the ratchet

@needs_ruff
def test_a_violation_on_an_untouched_line_is_not_reported(repo: Build) -> None:
    added = '\n\ndef added() -> None:\n    """Do nothing."""\n'
    root = repo({"workmain/old.py": BASE["workmain/old.py"] + added})
    assert violations(root) == []


@needs_ruff
def test_a_violation_on_a_changed_line_is_reported(repo: Build) -> None:
    root = repo({"workmain/old.py": BASE["workmain/old.py"] + "\n\ndef added(y):\n    pass\n"})
    codes = [message.split()[0] for _, _, _, message in violations(root)]
    assert codes == ["ANN001", "ANN201", "D103"]


@needs_ruff
def test_an_unsorted_import_is_caught_wherever_the_block_was_touched(repo: Build) -> None:
    text = BASE["workmain/old.py"].replace("import os\n", "import os\n\nfrom workmain import x\nimport sys\n")
    root = repo({"workmain/old.py": text})
    found = violations(root)
    assert [message.split()[0] for _, _, _, message in found] == ["I001"]
    assert found[0][1] == 3


def test_a_wrapped_line_added_to_an_existing_document_is_reported(repo: Build) -> None:
    root = repo({"docs/guide.md": BASE["docs/guide.md"] + "\nA new paragraph,\nalso wrapped.\n"})
    assert [(path, line) for path, line, _, _ in violations(root)] == [("docs/guide.md", 7)]


def test_a_wrapped_line_that_predates_the_branch_is_not_reported(repo: Build) -> None:
    root = repo({"docs/guide.md": BASE["docs/guide.md"] + "\nA new paragraph on one line.\n"})
    assert violations(root) == []


@needs_ruff
def test_main_exits_1_on_a_violation_and_0_without(repo: Build) -> None:
    root = repo({"docs/guide.md": BASE["docs/guide.md"] + "\nNew,\nwrapped.\n"})
    assert sc.main([]) == 1
    (root / "docs" / "guide.md").write_text(BASE["docs/guide.md"] + "\nNew, on one line.\n")
    assert sc.main([]) == 0


# ---------------------------------------------------------------- real values

def _commit(root: Path, message: str) -> None:
    """Commit everything in the test repository with `message`."""
    _git(root, "add", "-A")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", message)


def test_values_are_split_on_commas_with_whitespace_and_empty_entries_dropped(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text('DEV_REAL_VALUES=" Qzx , ,quillbrook-hollow,"\n')
    assert sc.real_values(env) == ["Qzx", "quillbrook-hollow"]


def test_a_missing_env_file_lists_no_values(tmp_path: Path) -> None:
    assert sc.real_values(tmp_path / ".env") == []


def test_a_value_is_matched_in_any_case_and_joined_by_underscore_or_hyphen() -> None:
    text = "a qzx here\nfoo_QZX_bar\nint-Qzx-team\n"
    assert [line for _, line, _, _ in sc.real_value_violations("x.md", text, [VALUE])] == [1, 2, 3]


def test_a_value_inside_a_longer_word_is_not_matched() -> None:
    assert sc.real_value_violations("x.md", "aqzxb\nqzx9 and 9qzx\n", [VALUE]) == []


def test_a_listed_value_on_a_changed_line_fails_without_printing_it(
        repo: Build, capsys: pytest.CaptureFixture) -> None:
    repo({"docs/guide.md": BASE["docs/guide.md"] + "\nWritten for qzx today.\n"})
    assert sc.main([]) == 1
    out = capsys.readouterr().out
    assert "docs/guide.md:6 — holds value 1 of DEV_REAL_VALUES" in out
    assert VALUE.lower() not in out.lower()


def test_a_listed_value_on_an_untouched_line_is_not_reported(repo: Build) -> None:
    repo({"docs/notes.md": f"{VALUE} was here.\n\nA new line.\n"})
    assert sc.check({"docs/notes.md": {3}}, [VALUE]) == []
    assert [line for _, line, _, _ in sc.check({"docs/notes.md": {1}}, [VALUE])] == [1]


@pytest.mark.parametrize("env", [None, "OTHER_KEY=1\n", "DEV_REAL_VALUES=\n"],
                         ids=["no-env-file", "no-key", "empty-value"])
def test_without_listed_values_the_check_fails_with_a_message(
        repo: Build, capsys: pytest.CaptureFixture, env: Optional[str]) -> None:
    root = repo({"docs/guide.md": BASE["docs/guide.md"] + "\nNew, on one line.\n"})
    if env is None:
        (root / ".env").unlink()
    else:
        (root / ".env").write_text(env)
    assert sc.main([]) == 1
    out = capsys.readouterr().out
    assert "0 violation(s)" in out
    assert "real-value check not run: DEV_REAL_VALUES is not set in .env in the main working tree" in out


def test_values_are_read_from_the_main_working_tree_in_a_linked_worktree(
        repo: Build, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch,
        tmp_path_factory: pytest.TempPathFactory) -> None:
    root = repo({"docs/guide.md": BASE["docs/guide.md"] + "\nWritten for qzx today.\n"})
    _commit(root, "add a line")
    worktree = tmp_path_factory.mktemp("worktree")
    _git(root, "worktree", "add", "-q", "--detach", str(worktree), "chore/test")
    assert not (worktree / ".env").exists()
    monkeypatch.setattr(sc, "ROOT", worktree)
    assert sc.main(["--base", "main"]) == 1
    out = capsys.readouterr().out
    assert "docs/guide.md:6 — holds value 1 of DEV_REAL_VALUES" in out
    assert "real-value check not run" not in out


def test_a_listed_value_in_a_branch_commit_message_fails_without_printing_it(
        repo: Build, capsys: pytest.CaptureFixture) -> None:
    root = repo({"docs/first.md": "First.\n"})
    _commit(root, "Add the first note\n\nWritten for qzx, in the body.")
    flagged = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, check=True,
                             capture_output=True, text=True).stdout.strip()
    (root / "docs" / "second.md").write_text("Second.\n")
    _commit(root, "Add the second note")
    assert sc.main([]) == 1
    out = capsys.readouterr().out
    assert f"commit {flagged} — holds value 1 of DEV_REAL_VALUES" in out
    assert out.count("commit ") == 1
    assert VALUE.lower() not in out.lower()


def test_a_value_in_a_commit_before_the_branch_is_not_reported(
        repo: Build, capsys: pytest.CaptureFixture) -> None:
    root = repo({})
    _git(root, "checkout", "-q", "main")
    _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty",
         "-m", f"Base work for {VALUE}")
    _git(root, "checkout", "-q", "-b", "chore/later")
    assert sc.main([]) == 0
    assert "commit " not in capsys.readouterr().out
