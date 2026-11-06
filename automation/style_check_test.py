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
from typing import Callable, Dict

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

BASE = {
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
        A function that commits BASE on main, cuts `branch` from it, writes its
        `changes` into the working tree uncommitted, and returns the root.
    """

    def build(changes: Dict[str, str], branch: str = "chore/test") -> Path:
        for rel, text in BASE.items():
            path = tmp_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
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
