"""
Checks the lines a branch changed against the style rules a tool can check.

Python lines are checked with ruff, configured in pyproject.toml to the rules
docs/standards/3-code.md states: import order (§3.2), docstrings (§3.1, §3.5)
and type hints (§3.5). Python lines are also checked for citations of the
process that produced them (§3.1). Markdown lines are checked for hard wrapping
(docs/standards/1-workflow.md §1.5). Only lines the branch added or changed
are checked, against the point where it left its base branch, so code is
brought up to the rules as it is touched rather than all at once. Uncommitted
and untracked files count as changed. CHANGELOG.md is history and is never
checked.

Every changed line, in a file of any type, and every commit message since the
branch left its base are also checked for the real values listed in
DEV_REAL_VALUES, read from .env in the main working tree, so a linked
worktree reads the same file. The report names where a value is,
never the value. With no values listed the check cannot run, and fails.
Requires git, ruff and python-dotenv.

Exit 0 when every changed line passes, 1 otherwise.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
REAL_VALUES_KEY = "DEV_REAL_VALUES"
PYTHON_DIRS = ("workmain/", "tests/", "automation/", "scripts/")
SKIPPED = ("CHANGELOG.md", "docs/archive/", "scripts-deprecated/", "staging/")

# A citation of the process that produced the code: a gate, phase, sprint, backlog item or open question.
_HISTORY = re.compile(r"\bGate \d+[A-Z]?\b|\bPhase \d+\b|_Sprint\b|\bSprint\b|\bItem #?\d+\b|\bOQ\d+\b")
# This module and its tests name the forms they look for.
_HISTORY_EXEMPT = ("automation/style_check.py", "automation/style_check_test.py")

# A Markdown line that starts a block of its own rather than continuing a paragraph.
_BLOCK_START = re.compile(r"\s*([-*+]\s|\d+[.)]\s|#|\||>|<!--|---\s*$|\[\^?[^\]]*\]:|\*\*[^*]+:\*\*)")

Violation = Tuple[str, int, int, str]


# ---------------------------------------------------------------- git

def _git(*args: str) -> str:
    """Run git in the repository and return its output."""
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT, check=True).stdout


def _main_worktree() -> Path:
    """Return the root of the repository's main working tree, from any of its worktrees."""
    return Path(_git("rev-parse", "--path-format=absolute", "--git-common-dir").strip()).parent


def base_branch(branch: str) -> str:
    """
    Name the branch a working branch was cut from (docs/standards/2-git.md §2.1).

    Args:
        branch: The working branch's name.

    Returns:
        `dev` for a `feature/*` branch, `main` for any other.
    """
    return "dev" if branch.startswith("feature/") else "main"


def changed_lines(base: str) -> Dict[str, Optional[Set[int]]]:
    """
    Find every file and line the working tree changed since it left `base`.

    Args:
        base: The base branch, or any commit.

    Returns:
        Changed line numbers keyed by repository-relative path. A file that is
        new, or untracked, maps to None: every line in it counts as changed.
    """
    fork = _git("merge-base", "HEAD", base).strip()
    out: Dict[str, Optional[Set[int]]] = {}
    current = None
    for line in _git("diff", "--unified=0", "--diff-filter=AM", fork).splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else None
            if current is not None:
                out.setdefault(current, set())
        elif line.startswith("@@") and current is not None and out[current] is not None:
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            start, count = int(m.group(1)), int(m.group(2) or 1)
            out[current].update(range(start, start + count))
    for line in _git("diff", "--name-only", "--diff-filter=A", fork).splitlines():
        out[line] = None
    for line in _git("ls-files", "--others", "--exclude-standard").splitlines():
        out[line] = None
    return {path: lines for path, lines in out.items() if not path.startswith(SKIPPED)}


# ---------------------------------------------------------------- real values

def real_values(env: Path) -> List[str]:
    """
    List the real values a `.env` file names in DEV_REAL_VALUES.

    Args:
        env: The `.env` file to read.

    Returns:
        The comma-separated entries of DEV_REAL_VALUES, in order, each with the
        whitespace around it dropped and empty entries left out. Empty when the
        file, the key or its value is missing.
    """
    raw = dotenv_values(env).get(REAL_VALUES_KEY) or ""
    return [entry.strip() for entry in raw.split(",") if entry.strip()]


def _value_patterns(values: Sequence[str]) -> List[re.Pattern]:
    """Compile each value to match in any case, bounded only by ASCII letters and digits."""
    return [re.compile(rf"(?<![A-Za-z0-9]){re.escape(value)}(?![A-Za-z0-9])", re.IGNORECASE) for value in values]


def real_value_violations(path: str, text: str, values: Sequence[str]) -> List[Violation]:
    """
    Find the lines of a file that hold a listed real value.

    A value matches in any letter case wherever the character on each side of
    it is absent or not an ASCII letter or digit, so it is found inside a
    snake_case or hyphenated word but not inside a longer word. Lines are
    numbered by newline alone, as git numbers them. The message names the
    value's position in the list, never the value.

    Args:
        path: The file's repository-relative path, for the report.
        text: The file's contents.
        values: The listed real values, in list order.

    Returns:
        One (path, line, line, message) entry per line and value matched.
    """
    patterns = _value_patterns(values)
    return [(path, number, number, f"holds value {position} of {REAL_VALUES_KEY}")
            for number, line in enumerate(text.split("\n"), 1)
            for position, pattern in enumerate(patterns, 1) if pattern.search(line)]


def commit_violations(base: str, values: Sequence[str]) -> List[Tuple[str, int]]:
    """
    Find the branch's own commit messages that hold a listed real value.

    Every commit since the branch left `base` is read, merge commits
    included, subject and body; a commit reachable from `base` is not.

    Args:
        base: The base branch, or any commit.
        values: The listed real values, in list order.

    Returns:
        One (short hash, position) entry per commit and value matched.
    """
    fork = _git("merge-base", "HEAD", base).strip()
    found = []
    for entry in _git("log", "--format=%h%x00%B%x1e", f"{fork}..HEAD").split("\x1e"):
        if "\x00" not in entry:
            continue
        short, message = entry.strip("\n").split("\x00", 1)
        found += [(short, position) for position, pattern in enumerate(_value_patterns(values), 1)
                  if pattern.search(message)]
    return found


# ---------------------------------------------------------------- the checks

def python_violations(paths: List[str]) -> List[Violation]:
    """
    Run ruff over the given Python files.

    Args:
        paths: Repository-relative paths of Python files.

    Returns:
        One (path, first line, last line, "<code> <message>") entry per violation
        ruff reports; the lines are the span ruff names.

    Raises:
        SystemExit: ruff is not on PATH, or it failed rather than reporting.
    """
    if not paths:
        return []
    ruff = shutil.which("ruff")
    if ruff is None:
        raise SystemExit("ruff was not found on PATH (requirements-dev.txt)")
    result = subprocess.run([ruff, "check", "--output-format", "json", *paths],
                            capture_output=True, text=True, cwd=ROOT)
    if result.returncode not in (0, 1):
        raise SystemExit(f"ruff failed: {result.stderr.strip()}")
    return [(Path(v["filename"]).resolve().relative_to(ROOT).as_posix(), v["location"]["row"],
             v["end_location"]["row"], f"{v['code']} {v['message']}") for v in json.loads(result.stdout or "[]")]


def history_violations(path: str, text: str) -> List[Violation]:
    """
    Find citations of the process that produced the code in a Python file.

    Comments, docstrings and strings are all searched: a citation of a gate,
    phase, sprint, backlog item or open question records how the code came to
    be, which git and the issue already hold.

    Args:
        path: The file's repository-relative path, for the report.
        text: The file's contents.

    Returns:
        One (path, line, line, message) entry per citation.
    """
    if path in _HISTORY_EXEMPT:
        return []
    return [(path, number, number, f"history citation \"{match.group(0)}\": git and the issue are the record")
            for number, line in enumerate(text.splitlines(), 1) for match in _HISTORY.finditer(line)]


def markdown_violations(path: str, text: str) -> List[Violation]:
    """
    Find hard-wrapped lines in a Markdown file.

    A line is hard-wrapped when it continues the paragraph or list item on the
    line before it. Tables, headings, quotes, list items, field lines such as
    `**Status:** Draft`, fenced code, front matter, and a line after an explicit
    break (two trailing spaces or a backslash) are not.

    Args:
        path: The file's repository-relative path, for the report.
        text: The file's contents.

    Returns:
        One (path, line, line, message) entry per wrapped line.
    """
    out = []
    fence = front = False
    prev = ""
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip("\n")
        if number == 1 and line.strip() == "---":
            front = True
            continue
        if front:
            front = line.strip() != "---"
            continue
        if line.lstrip().startswith(("```", "~~~")):
            fence, prev = not fence, ""
            continue
        if fence:
            continue
        if not line.strip():
            prev = ""
            continue
        if prev and not prev.endswith(("  ", "\\")) and not prev.lstrip().startswith(("|", "#", "<!--")) \
                and not _BLOCK_START.match(line):
            out.append((path, number, number, "hard-wrapped: continues the line above; one line per paragraph"))
        prev = line
    return out


def check(changes: Dict[str, Optional[Set[int]]], values: Sequence[str] = ()) -> List[Violation]:
    """
    Check every changed line.

    Args:
        changes: Changed lines by path, as `changed_lines` returns them.
        values: The listed real values to look for in every changed file;
            none are looked for when empty.

    Returns:
        Every violation whose span includes a changed line, sorted by path and line.
    """
    python = [p for p in changes if p.endswith(".py") and p.startswith(PYTHON_DIRS) and (ROOT / p).exists()]
    found = python_violations(python)
    for path in python:
        found += history_violations(path, (ROOT / path).read_text(encoding="utf-8"))
    for path in changes:
        if path.endswith(".md") and (ROOT / path).exists():
            found += markdown_violations(path, (ROOT / path).read_text(encoding="utf-8"))
    if values:
        for path in changes:
            if (ROOT / path).is_file():
                text = (ROOT / path).read_bytes().decode("utf-8", errors="replace")
                found += real_value_violations(path, text, values)
    return sorted(v for v in found
                  if changes.get(v[0]) is None or any(n in changes[v[0]] for n in range(v[1], v[2] + 1)))


# ---------------------------------------------------------------- main

def main(argv: Optional[Sequence[str]] = None) -> int:
    """
    Check the current branch's changed lines and print the report.

    Args:
        argv: Command-line arguments; the process's own when None.

    Returns:
        0 when every changed line passes, 1 otherwise, and 1 when no real
        values are listed.
    """
    parser = argparse.ArgumentParser(description="Check the lines this branch changed against the style rules.")
    parser.add_argument("--base", help="the branch to compare against; by default dev for feature/*, main otherwise")
    args = parser.parse_args(argv)

    branch = _git("rev-parse", "--abbrev-ref", "HEAD").strip()
    base = args.base or base_branch(branch)
    changes = changed_lines(base)
    values = real_values(_main_worktree() / ".env")
    violations = check(changes, values)
    commits = commit_violations(base, values) if values else []

    print(f"{branch} against {base}: {len(changes)} changed file(s), "
          f"{len(violations) + len(commits)} violation(s)")
    for path, line, _, message in violations:
        print(f"  {path}:{line} — {message}")
    for short, position in commits:
        print(f"  commit {short} — holds value {position} of {REAL_VALUES_KEY}")
    if not values:
        print(f"  real-value check not run: {REAL_VALUES_KEY} is not set in .env in the main working tree")
    failed = bool(violations) or bool(commits) or not values
    print("\nFAIL" if failed else "\nPASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
