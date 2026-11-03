"""
Tests for automation/architecture_check.py.

Each test builds a small repository in a temporary folder, a map and a few
modules, and points the module at it, so no test depends on the state of the
real code.
"""

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import pytest

ROOT = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "architecture_check", ROOT / "automation" / "architecture_check.py"
)
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)


MAP = """# Test architecture

## 1. Layers

| Layer | Packages | Rule |
| --- | --- | --- |
| **Surfaces** | `workmain/cli/` | Present. |
| **Application** | `workmain/services/` | Decide. |
| **Capabilities** | `workmain/ai/` | Compute. |
| **Data** | `workmain/database/repositories/`, `workmain/database/models.py`, `workmain/database/connection.py` | Store. |
| **Shared** | `workmain/utils/` | Help. |

## 2. Who owns what

- `workmain/cli/commands/<group>.py` — one command group each.
- `workmain/services/` — the services.
- `workmain/ai/report.py` — reports.
- `workmain/database/repositories/` — repositories.
- `workmain/database/models.py` — models.
- `workmain/database/connection.py` — sessions.
- `workmain/utils/dates.py` — dates.

## 3. Known deficiencies
{deficiencies}
"""

CLEAN = {
    "workmain/__init__.py": '"""The application."""\n',
    "workmain/cli/__init__.py": '"""The CLI."""\n',
    "workmain/cli/commands/__init__.py": '"""Command groups."""\n',
    "workmain/cli/commands/notes.py": (
        "from workmain.database.connection import get_db\n"
        "from workmain.services.notes_service import list_notes\n"
    ),
    "workmain/services/__init__.py": '"""Services."""\n',
    "workmain/services/notes_service.py": (
        "from workmain.database.repositories.notes_repo import NotesRepository\n"
        "from workmain.utils.dates import today\n"
        "class NoteRow:\n    pass\n"
    ),
    "workmain/ai/__init__.py": '"""AI."""\n',
    "workmain/ai/report.py": "from workmain.utils.dates import today\n",
    "workmain/database/__init__.py": '"""Database."""\n',
    "workmain/database/connection.py": "def get_db():\n    pass\n",
    "workmain/database/models.py": "class Note:\n    pass\n",
    "workmain/database/repositories/__init__.py": '"""Repositories."""\n',
    "workmain/database/repositories/notes_repo.py": "from workmain.database.models import Note\n",
    "workmain/utils/__init__.py": '"""Utilities."""\n',
    "workmain/utils/dates.py": "def today():\n    pass\n",
}


Build = Callable[..., Path]


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Build:
    """
    Provide a builder for a test repository.

    Args:
        tmp_path: pytest's temporary folder for the test.
        monkeypatch: pytest's patcher, used to point the module at the folder.

    Returns:
        A function that writes CLEAN, overlaid with its `changes`, and a map whose
        §3 holds its `deficiencies`, and returns the repository's root.
    """

    def build(changes: Optional[Dict[str, str]] = None, deficiencies: str = "") -> Path:
        files = dict(CLEAN)
        files.update(changes or {})
        for rel, text in files.items():
            path = tmp_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        (tmp_path / "docs").mkdir(exist_ok=True)
        (tmp_path / "docs" / "ARCHITECTURE.md").write_text(MAP.format(deficiencies=deficiencies))
        monkeypatch.setattr(ac, "ROOT", tmp_path)
        monkeypatch.setattr(ac, "MAP_PATH", tmp_path / "docs" / "ARCHITECTURE.md")
        return tmp_path

    return build


def run(capsys: pytest.CaptureFixture, *args: str) -> Tuple[int, str]:
    """
    Run the module's main with arguments and capture its report.

    Args:
        capsys: pytest's output capture.
        *args: Command-line arguments.

    Returns:
        The exit code and the printed report.
    """
    code = ac.main(list(args))
    return code, capsys.readouterr().out


def new_findings(out: str) -> List[str]:
    """
    Read the new findings out of a report.

    Args:
        out: The printed report.

    Returns:
        The lines under "New findings", stripped.
    """
    block = out.split("New findings:")[1].split("\n\n")[0]
    return [line.strip() for line in block.splitlines()[1:]]


# ---------------------------------------------------------------- reading the map

def test_layers_come_from_the_table_in_order(repo: Build) -> None:
    repo()
    layers = ac.read_layers(ac._sections(ac.MAP_PATH.read_text()))
    assert [name for name, _ in layers] == ["Surfaces", "Application", "Capabilities", "Data", "Shared"]


def test_a_path_ending_in_a_slash_covers_everything_under_it() -> None:
    rx = ac._pattern("workmain/services/")
    assert rx.match("workmain/services/notes_service.py")
    assert not rx.match("workmain/servicesx.py")


def test_a_named_segment_matches_one_segment_only() -> None:
    rx = ac._pattern("workmain/cli/commands/<group>.py")
    assert rx.match("workmain/cli/commands/notes.py")
    assert not rx.match("workmain/cli/commands/sub/notes.py")


def test_a_double_star_matches_any_depth_including_none() -> None:
    rx = ac._pattern("workmain/**/__init__.py")
    assert rx.match("workmain/__init__.py")
    assert rx.match("workmain/ai/__init__.py")
    assert rx.match("workmain/ai/providers/__init__.py")
    assert not rx.match("workmain/ai/report.py")


def test_covers_reads_dotted_paths_and_stops_at_its_sentence(repo: Build) -> None:
    repo(deficiencies=(
        "\n**An entry — #12.** Covers `workmain/ai/report.py` and `workmain/utils/dates.py`."
        " It moves to `workmain/services/notes_service.py`.\n"
    ))
    [(title, issues, patterns)] = ac.read_deficiencies(ac._sections(ac.MAP_PATH.read_text()))
    assert title == "An entry — #12"
    assert issues == [12]
    assert [p.pattern for p in patterns] == ["^workmain/ai/report\\.py$", "^workmain/utils/dates\\.py$"]


# ---------------------------------------------------------------- the checks

def test_a_clean_repository_passes(repo: Build, capsys: pytest.CaptureFixture) -> None:
    repo()
    code, out = run(capsys)
    assert code == 0
    assert new_findings(out) == []


def test_an_upward_import_is_a_new_finding(repo: Build, capsys: pytest.CaptureFixture) -> None:
    repo({"workmain/services/notes_service.py": "from workmain.cli.commands.notes import x\n"})
    code, out = run(capsys)
    assert code == 1
    assert any("Application imports Surfaces (upward)" in f for f in new_findings(out))


def test_a_nested_import_is_checked_too(repo: Build, capsys: pytest.CaptureFixture) -> None:
    repo({"workmain/utils/dates.py": "def today():\n    from workmain.ai.report import x\n"})
    code, out = run(capsys)
    assert code == 1
    assert any("Shared imports Capabilities (upward)" in f for f in new_findings(out))


def test_a_surface_may_own_its_session_but_not_reach_a_repository(repo: Build, capsys: pytest.CaptureFixture) -> None:
    repo({"workmain/cli/commands/notes.py": (
        "from workmain.database.connection import get_db\n"
        "from workmain.database.repositories.notes_repo import NotesRepository\n"
    )})
    code, out = run(capsys)
    findings = new_findings(out)
    assert code == 1
    assert len(findings) == 1
    assert "a surface reaches data directly: workmain/database/repositories/notes_repo.py" in findings[0]


def test_a_capability_may_not_import_models(repo: Build, capsys: pytest.CaptureFixture) -> None:
    repo({"workmain/ai/report.py": "from workmain.database.models import Note\n"})
    code, out = run(capsys)
    assert code == 1
    assert any("a capability imports from the database" in f for f in new_findings(out))


def test_a_class_name_defined_twice_is_a_new_finding(repo: Build, capsys: pytest.CaptureFixture) -> None:
    repo({"workmain/services/other_service.py": "class NoteRow:\n    pass\n"})
    code, out = run(capsys)
    assert code == 1
    assert any("class NoteRow is defined 2 times" in f for f in new_findings(out))


def test_a_function_name_may_repeat_across_modules(repo: Build, capsys: pytest.CaptureFixture) -> None:
    repo({
        "workmain/services/a_service.py": "def get_status():\n    pass\n",
        "workmain/services/b_service.py": "def get_status():\n    pass\n",
    })
    code, _ = run(capsys)
    assert code == 0


def test_a_module_with_no_owner_line_is_a_new_finding(repo: Build, capsys: pytest.CaptureFixture) -> None:
    repo({"workmain/utils/strays.py": "x = 1\n"})
    code, out = run(capsys)
    assert code == 1
    assert "workmain/utils/strays.py — no owner in §2" in new_findings(out)


def test_an_init_holding_more_than_its_docstring_is_a_new_finding(repo: Build, capsys: pytest.CaptureFixture) -> None:
    repo({"workmain/ai/__init__.py": '"""AI."""\nfrom workmain.ai.report import x\n'})
    code, out = run(capsys)
    assert code == 1
    assert any("workmain/ai/__init__.py:2 — holds 1 statement(s)" in f for f in new_findings(out))


def test_an_init_with_no_docstring_is_a_new_finding(repo: Build, capsys: pytest.CaptureFixture) -> None:
    repo({"workmain/ai/__init__.py": ""})
    code, out = run(capsys)
    assert code == 1
    assert "workmain/ai/__init__.py — has no docstring" in new_findings(out)


def test_a_package_with_no_modules_is_a_new_finding(repo: Build, capsys: pytest.CaptureFixture) -> None:
    repo({"workmain/web/__init__.py": '"""Reserved."""\n'})
    code, out = run(capsys)
    assert code == 1
    assert "workmain/web/__init__.py — a package with no modules" in new_findings(out)


def test_a_package_holding_only_other_files_is_named_as_such(repo: Build, capsys: pytest.CaptureFixture) -> None:
    root = repo({"workmain/database/migrations/__init__.py": '"""Migrations."""\n'})
    (root / "workmain/database/migrations/001_init.sql").write_text("select 1;\n")
    code, out = run(capsys)
    assert code == 1
    assert ("workmain/database/migrations/__init__.py — makes a package of a folder that holds no Python module"
            in new_findings(out))


# ---------------------------------------------------------------- known deficiencies

def test_a_finding_inside_covered_code_is_known_and_does_not_fail(repo: Build, capsys: pytest.CaptureFixture) -> None:
    repo(
        {"workmain/ai/report.py": "from workmain.database.models import Note\n"},
        deficiencies="\n**Capabilities fetching data — #40.** Covers `workmain/ai/report.py`.\n",
    )
    code, out = run(capsys)
    assert code == 0
    assert new_findings(out) == []
    assert "Capabilities fetching data — #40: 1" in out


def test_a_path_mentioned_outside_covers_excuses_nothing(repo: Build, capsys: pytest.CaptureFixture) -> None:
    repo(
        {"workmain/ai/report.py": "from workmain.database.models import Note\n"},
        deficiencies="\n**Something else — #41.** Covers `workmain/utils/dates.py`. Unrelated to `workmain/ai/report.py`.\n",
    )
    code, out = run(capsys)
    assert code == 1
    assert any("workmain/ai/report.py" in f for f in new_findings(out))


def test_an_entry_with_no_issue_is_listed_and_does_not_fail(repo: Build, capsys: pytest.CaptureFixture) -> None:
    repo(deficiencies="\n**Waiting for an issue.** Covers `workmain/utils/dates.py`.\n")
    code, out = run(capsys)
    assert code == 0
    assert "§3 entries awaiting an issue: 1" in out


def test_an_entry_whose_issues_are_all_closed_fails_with_check_issues(repo: Build, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    repo(deficiencies="\n**Finished work — #50, #51.** Covers `workmain/utils/dates.py`.\n")

    def fake_gh(cmd: List[str], **kwargs: object) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps({"state": "CLOSED"}), stderr="")

    monkeypatch.setattr(ac.subprocess, "run", fake_gh)
    code, out = run(capsys, "--check-issues")
    assert code == 1
    assert "every issue it names is closed" in out


def test_an_entry_with_one_open_issue_passes_with_check_issues(repo: Build, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    repo(deficiencies="\n**Half done — #50, #51.** Covers `workmain/utils/dates.py`.\n")
    states = {"50": "CLOSED", "51": "OPEN"}

    def fake_gh(cmd: List[str], **kwargs: object) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps({"state": states[cmd[3]]}), stderr="")

    monkeypatch.setattr(ac.subprocess, "run", fake_gh)
    code, _ = run(capsys, "--check-issues")
    assert code == 0
