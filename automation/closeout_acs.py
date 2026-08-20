"""
Path derivation and the AC guard for `/closeout` (`.claude/skills/closeout/SKILL.md`).

Answers two questions, both stated in `docs/dev/specs/CLOSEOUT_PERFORMS_SPEC.md` §4.4
because nothing else states them: which results artifact belongs to a branch, and does
that artifact carry a disposed row for every AC on the branch's approved spec.
Judgement — whether an AC is genuinely met — is not here; Anvil settles that before
this ever runs (DR4).

    python3 automation/closeout_acs.py --branch <name> [--tree <ref>]

`--tree <ref>` reads the spec and the artifact from that git ref instead of the
working tree, for the case where the branch has already merged and been deleted
(§4.1). Absent, both are working-tree reads.

Exit 0 — every check passed.
Exit 1 — one or more AC checks failed. Each is named on stderr, one line per
failure, and every check runs before the module exits (DR3).
Exit 2 — there was nothing to compare: no spec names the branch, several do, the
spec filename is unparseable, or the derived results artifact does not exist.

Every external read (`git ls-tree`, `git show`) sits behind a named module-level
function so a test can replace it with `monkeypatch`, mirroring `issue_validator.py`
(C19).
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise SystemExit(f"could not find a repository root above {start}")


ROOT = find_repo_root(Path(__file__))

SPECS_DIR = Path("docs/dev/specs")
RESULTS_DIR = Path("docs/dev/results")

_SPEC_BRANCH_FIELD_RE = re.compile(r"^\*\*Branch:\*\*\s*`([^`]+)`", re.MULTILINE)
_SPEC_SUFFIX_RE = re.compile(r"_SPEC(_v[0-9_]+)?\.md$")
_SPEC_AC_ROW_RE = re.compile(r"^\|\s*(AC[0-9]+\.[0-9]+)\s*\|")
_FOLLOWUP_ISSUE_RE = re.compile(r"#\d+")


# ---------------------------------------------------------------------------
# Seams — every external read, named and module-level (C19, Caliper G8).
# ---------------------------------------------------------------------------

def git_ls_tree_paths(ref: str, dir_path: str):
    """File paths under `dir_path` at `ref`, recursive."""
    result = subprocess.run(
        ["git", "ls-tree", "--name-only", "-r", ref, "--", dir_path],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        return []
    return sorted(line for line in result.stdout.splitlines() if line.strip())


def git_show_file(ref: str, path: str):
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        return None
    return result.stdout


# ---------------------------------------------------------------------------
# §4.4 — Path derivation
# ---------------------------------------------------------------------------

def _list_spec_files(specs_dir: Path, tree_ref: str = None):
    """(path_label, text) pairs for every spec markdown file — working tree or `tree_ref`."""
    if tree_ref is None:
        return [(str(p), p.read_text()) for p in sorted(Path(specs_dir).glob("*.md"))]
    pairs = []
    for path in git_ls_tree_paths(tree_ref, str(SPECS_DIR)):
        text = git_show_file(tree_ref, path)
        if text is not None:
            pairs.append((path, text))
    return pairs


def find_spec(branch_name: str, specs_dir: Path, tree_ref: str = None):
    """The spec whose `**Branch:**` field names `branch_name`. Returns
    `(path_label, text, error)` — `path_label` and `text` are `None` on error."""
    matches = [
        (path_label, text)
        for path_label, text in _list_spec_files(specs_dir, tree_ref)
        if (m := _SPEC_BRANCH_FIELD_RE.search(text)) and m.group(1) == branch_name
    ]
    if not matches:
        return None, None, f"no spec names branch {branch_name} in its **Branch:** field"
    if len(matches) > 1:
        names = ", ".join(Path(path_label).name for path_label, _ in matches)
        return None, None, f"more than one spec names branch {branch_name}: {names}"
    path_label, text = matches[0]
    return path_label, text, None


def derive_results_path(spec_path_label: str):
    """§4.4 steps 2-3: strip the spec suffix, append `_RESULTS.md`."""
    filename = Path(spec_path_label).name
    suffix_m = _SPEC_SUFFIX_RE.search(filename)
    if not suffix_m:
        return None, f"spec filename does not match _SPEC(_vN).md: {filename}"
    subject = filename[: suffix_m.start()]
    return RESULTS_DIR / f"{subject}_RESULTS.md", None


# ---------------------------------------------------------------------------
# §4.4 — The AC guard
# ---------------------------------------------------------------------------

def parse_spec_ac_ids(spec_text: str):
    """Spec AC ids from the §5 table: rows matching `^\\| AC[0-9]+\\.[0-9]+ \\|`,
    first cell only. Identifiers, never prose (Q5)."""
    lines = spec_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s*5\.", line):
            start = i + 1
            break
    if start is None:
        return []
    ids = []
    for line in lines[start:]:
        if re.match(r"^##\s", line):
            break
        m = _SPEC_AC_ROW_RE.match(line.strip())
        if m:
            ids.append(m.group(1))
    return ids


def _split_table_row(line: str):
    """Cells of one markdown table row, respecting `\\|` as a literal pipe rather
    than a column separator — an unescaped split on `|` mis-parses any evidence
    cell that quotes a pipe-bearing command or regex (the `CYCLE_CLOSEOUT_SPEC.md`
    F12 lesson)."""
    parts = re.split(r"(?<!\\)\|", line)
    cells = [p.strip().replace("\\|", "|") for p in parts]
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def parse_artifact_ac_rows(text: str):
    """Rows of the artifact's §3 table: `(id, status, evidence)`. Skips the header
    and separator rows."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s*3\.", line):
            start = i + 1
            break
    if start is None:
        return []
    rows = []
    for line in lines[start:]:
        if re.match(r"^##\s", line):
            break
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = _split_table_row(line)
        if len(cells) != 3:
            continue
        if set(cells[0]) <= {"-"}:
            continue
        if cells[0].upper() == "AC" and cells[1].lower() == "status":
            continue
        rows.append((cells[0], cells[1], cells[2]))
    return rows


def evaluate(spec_ids, artifact_rows):
    """The AC guard's verdict (§4.4). Returns a list of failure descriptions, empty
    when every check passes."""
    if not spec_ids:
        return ["the spec carries no ACn.m ids in its §5 table"]

    artifact_by_id = {row[0]: row for row in artifact_rows}

    failures = [f"missing row: {ac_id}" for ac_id in spec_ids if ac_id not in artifact_by_id]
    failures += [
        f"extra row, no spec AC claims it: {row[0]}"
        for row in artifact_rows
        if row[0] not in spec_ids
    ]

    for ac_id, status, evidence in artifact_rows:
        if ac_id not in spec_ids:
            continue
        status_norm = status.strip().casefold()
        if status_norm == "met":
            if not evidence.strip():
                failures.append(f"Met row with no evidence: {ac_id}")
        elif status_norm == "carried":
            if not _FOLLOWUP_ISSUE_RE.search(evidence):
                failures.append(f"Carried row with no cited follow-up (#N): {ac_id}")
        else:
            failures.append(f"row not Met or Carried: {ac_id} ({status.strip()})")

    return failures


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run(branch_name: str, tree_ref: str = None) -> int:
    specs_dir = ROOT / SPECS_DIR
    spec_label, spec_text, error = find_spec(branch_name, specs_dir, tree_ref)
    if error:
        print(error, file=sys.stderr)
        return 2

    results_rel_path, error = derive_results_path(spec_label)
    if error:
        print(error, file=sys.stderr)
        return 2

    if tree_ref is None:
        results_full_path = ROOT / results_rel_path
        if not results_full_path.exists():
            print(f"results artifact absent: {results_rel_path}", file=sys.stderr)
            return 2
        results_text = results_full_path.read_text()
    else:
        results_text = git_show_file(tree_ref, str(results_rel_path))
        if results_text is None:
            print(f"results artifact absent: {results_rel_path}", file=sys.stderr)
            return 2

    spec_ids = parse_spec_ac_ids(spec_text)
    artifact_rows = parse_artifact_ac_rows(results_text)
    failures = evaluate(spec_ids, artifact_rows)

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="The AC guard for /closeout.")
    parser.add_argument("--branch", required=True)
    parser.add_argument("--tree", default=None)
    args = parser.parse_args(argv)
    return run(args.branch, args.tree)


if __name__ == "__main__":
    sys.exit(main())
