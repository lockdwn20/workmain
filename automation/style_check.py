"""
Checks the lines a branch changed against the style rules a tool can check.

Python lines are checked with ruff, configured in pyproject.toml to the rules
docs/standards/3-code.md states: import order (§3.2), docstrings (§3.1, §3.5)
and type hints (§3.5). Markdown lines are checked for hard wrapping
(docs/standards/1-workflow.md §1.5). Only lines the branch added or changed
are checked, against the point where it left its base branch, so code is
brought up to the rules as it is touched rather than all at once. Uncommitted
and untracked files count as changed. CHANGELOG.md is history and is never
checked. Requires git and ruff.

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

ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIRS = ("workmain/", "tests/", "automation/", "scripts/")
SKIPPED = ("CHANGELOG.md", "docs/archive/", "scripts-deprecated/", "staging/")

# A Markdown line that starts a block of its own rather than continuing a paragraph.
_BLOCK_START = re.compile(r"\s*([-*+]\s|\d+[.)]\s|#|\||>|<!--|---\s*$|\[\^?[^\]]*\]:|\*\*[^*]+:\*\*)")

Violation = Tuple[str, int, int, str]


# ---------------------------------------------------------------- git

def _git(*args: str) -> str:
    """Run git in the repository and return its output."""
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT, check=True).stdout


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


def check(changes: Dict[str, Optional[Set[int]]]) -> List[Violation]:
    """
    Check every changed line.

    Args:
        changes: Changed lines by path, as `changed_lines` returns them.

    Returns:
        Every violation whose span includes a changed line, sorted by path and line.
    """
    python = [p for p in changes if p.endswith(".py") and p.startswith(PYTHON_DIRS) and (ROOT / p).exists()]
    found = python_violations(python)
    for path in changes:
        if path.endswith(".md") and (ROOT / path).exists():
            found += markdown_violations(path, (ROOT / path).read_text(encoding="utf-8"))
    return sorted(v for v in found
                  if changes.get(v[0]) is None or any(n in changes[v[0]] for n in range(v[1], v[2] + 1)))


# ---------------------------------------------------------------- main

def main(argv: Optional[Sequence[str]] = None) -> int:
    """
    Check the current branch's changed lines and print the report.

    Args:
        argv: Command-line arguments; the process's own when None.

    Returns:
        0 when every changed line passes, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description="Check the lines this branch changed against the style rules.")
    parser.add_argument("--base", help="the branch to compare against; by default dev for feature/*, main otherwise")
    args = parser.parse_args(argv)

    branch = _git("rev-parse", "--abbrev-ref", "HEAD").strip()
    base = args.base or base_branch(branch)
    changes = changed_lines(base)
    violations = check(changes)

    print(f"{branch} against {base}: {len(changes)} changed file(s), {len(violations)} violation(s)")
    for path, line, _, message in violations:
        print(f"  {path}:{line} — {message}")
    print("\nFAIL" if violations else "\nPASS")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
