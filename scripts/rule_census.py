"""
Surveys every tracked file under tests/, workmain/, automation/, scripts/ and
config/ for text that may be a process rule rather than a description, and
writes one report of candidates for Ray to adjudicate.

It gathers; it never decides. Every pattern is tuned for recall, not
precision, and every tracked file gets a row whether or not anything matched.
"""

import ast
import json
import re
import subprocess
import sys
import tokenize
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TREES = ["tests/", "workmain/", "automation/", "scripts/", "config/"]
SELF_PATH = "scripts/rule_census.py"

COMMAND_PY_RE = re.compile(r"\bpython3?\s+\S+\.py\b")
COMMAND_PYTEST_RE = re.compile(r"\bpytest\b")
COMMAND_GH_RE = re.compile(r"(?<![\w-])gh\s+[a-z]")
USAGE_LABEL_RE = re.compile(r"^\s*Usage:")

FLAG_WORD_RE = re.compile(r"--[A-Za-z][\w-]*")
FLAG_ENV_RE = re.compile(r"\b[A-Z][A-Z0-9_]{2,}=")

TRIGGER_OPENER_RE = re.compile(r"^\s*(Run|Increment|Update|Do not|Don't|Never|Always|Use )")
TRIGGER_GATE_RE = re.compile(r"as part of .*Gate")
TRIGGER_ORDERING_RE = re.compile(r"\b(before|after)\b.{0,80}\.(py|sql|sh|json|txt|md)\b")
TRIGGER_PHRASES = ("before deploying", "run once", "run manually", "must not")

VERSION_FILE_RE = re.compile(r"\S+\.py\s+v\d+")
VERSION_DATE_RE = re.compile(r"(?<!\d)\d{8}(?!\d)")

INVENTORY_BULLET_RE = re.compile(r"^\s*[-*\u2022]\s")
INVENTORY_NUMBERED_RE = re.compile(r"^\s*\d+[.)]\s")
INVENTORY_LABEL_RE = re.compile(r"^\s*(Commands|Covers|Features|Steps|Usage|Tests):")

ALL_CATEGORIES = ("COMMAND", "FLAG", "TRIGGER", "VERSION", "INVENTORY")
DOCSTRING_CATEGORIES = ("TRIGGER", "COMMAND")


def is_command(line):
    return bool(
        COMMAND_PY_RE.search(line)
        or COMMAND_PYTEST_RE.search(line)
        or COMMAND_GH_RE.search(line)
        or USAGE_LABEL_RE.match(line)
    )


def is_flag(line):
    return bool(FLAG_WORD_RE.search(line) or FLAG_ENV_RE.search(line))


def is_trigger(line):
    if TRIGGER_OPENER_RE.match(line):
        return True
    low = line.lower()
    if any(phrase in low for phrase in TRIGGER_PHRASES):
        return True
    if TRIGGER_GATE_RE.search(line):
        return True
    if TRIGGER_ORDERING_RE.search(line):
        return True
    return False


def is_version(line):
    return bool(VERSION_FILE_RE.search(line) or VERSION_DATE_RE.search(line))


def is_inventory(line):
    return bool(
        INVENTORY_BULLET_RE.match(line)
        or INVENTORY_NUMBERED_RE.match(line)
        or INVENTORY_LABEL_RE.match(line)
    )


CHECKS = {
    "COMMAND": is_command,
    "FLAG": is_flag,
    "TRIGGER": is_trigger,
    "VERSION": is_version,
    "INVENTORY": is_inventory,
}


def categorize(line, allowed=ALL_CATEGORIES):
    return [name for name in allowed if CHECKS[name](line)]


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files", *TREES],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    files = sorted(set(out.splitlines()))
    return [f for f in files if f != SELF_PATH]


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, ValueError):
        return None


def scan_py(rel_path, source):
    rows = []
    lines = source.splitlines()
    try:
        tree = ast.parse(source, filename=rel_path)
    except SyntaxError as exc:
        rows.append((1, "NOT_TEXT", f"file does not parse as Python: {exc}"))
        return rows

    module_doc = ast.get_docstring(tree, clean=False)
    if module_doc is None:
        rows.append((1, "NO_HEADER", "(no module docstring)"))
    else:
        first = tree.body[0]
        rows.extend(_scan_docstring_lines(lines, first.lineno, first.end_lineno, ALL_CATEGORIES))

    for node in ast.walk(tree):
        if node is tree:
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None and node.body:
                first = node.body[0]
                rows.extend(
                    _scan_docstring_lines(lines, first.lineno, first.end_lineno, DOCSTRING_CATEGORIES)
                )

    rows.extend(_scan_py_comments(rel_path, source))
    return rows


def _scan_docstring_lines(lines, start, end, allowed):
    rows = []
    for lineno in range(start, end + 1):
        text = lines[lineno - 1]
        cats = categorize(text, allowed)
        if cats:
            rows.append((lineno, ",".join(cats), text))
    return rows


def _scan_py_comments(rel_path, source):
    rows = []
    try:
        tokens = tokenize.generate_tokens(iter(source.splitlines(keepends=True)).__next__)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                text = tok.string
                cats = categorize(text, ALL_CATEGORIES)
                if cats:
                    rows.append((tok.start[0], ",".join(cats), text))
    except tokenize.TokenizeError:
        pass
    return rows


_JSON_KV_STRING_RE = re.compile(r'^\s*"([^"]+)"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,?\s*$')
_JSON_OPEN_OBJ_RE = re.compile(r'^\s*"([^"]+)"\s*:\s*\{\s*$')
_JSON_OPEN_ARR_RE = re.compile(r'^\s*"([^"]+)"\s*:\s*\[\s*$')
_JSON_CLOSE_OBJ_RE = re.compile(r'^\s*\},?\s*$')
_JSON_CLOSE_ARR_RE = re.compile(r'^\s*\],?\s*$')
_JSON_BARE_STRING_RE = re.compile(r'^\s*"((?:[^"\\]|\\.)*)"\s*,?\s*$')


def scan_json(rel_path, source):
    # DR8.4: every JSON string value is a row, keyed by its path, matched
    # against nothing. json.loads has no line numbers, so the value's
    # position is tracked by walking the pretty-printed source directly.
    try:
        json.loads(source)
    except json.JSONDecodeError as exc:
        return [(1, "NOT_TEXT", f"file does not parse as JSON: {exc}")]

    rows = []
    path_stack = []
    array_index_stack = []
    lines = source.splitlines()
    for lineno, raw in enumerate(lines, start=1):
        m = _JSON_KV_STRING_RE.match(raw)
        if m:
            key, value = m.group(1), m.group(2)
            full_key = ".".join(path_stack + [key])
            cats = categorize(value, ALL_CATEGORIES)
            category = ",".join(cats) if cats else "PROSE"
            rows.append((lineno, category, f"{full_key} = {value!r}"))
            continue
        m = _JSON_OPEN_OBJ_RE.match(raw)
        if m:
            path_stack.append(m.group(1))
            continue
        m = _JSON_OPEN_ARR_RE.match(raw)
        if m:
            path_stack.append(m.group(1))
            array_index_stack.append(0)
            continue
        if _JSON_CLOSE_OBJ_RE.match(raw):
            if path_stack:
                path_stack.pop()
            continue
        if _JSON_CLOSE_ARR_RE.match(raw):
            if path_stack:
                path_stack.pop()
            if array_index_stack:
                array_index_stack.pop()
            continue
        m = _JSON_BARE_STRING_RE.match(raw)
        if m and array_index_stack:
            idx = array_index_stack[-1]
            full_key = ".".join(path_stack) + f"[{idx}]"
            value = m.group(1)
            cats = categorize(value, ALL_CATEGORIES)
            category = ",".join(cats) if cats else "PROSE"
            rows.append((lineno, category, f"{full_key} = {value!r}"))
            array_index_stack[-1] += 1
            continue
    return rows


def scan_text(source):
    rows = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        cats = categorize(line, ALL_CATEGORIES)
        if cats:
            rows.append((lineno, ",".join(cats), line))
    return rows


def census_file(rel_path):
    path = REPO_ROOT / rel_path
    source = read_text(path)
    if source is None:
        return [(0, "NOT_TEXT", "file does not decode as text")]

    if rel_path.endswith(".py"):
        rows = scan_py(rel_path, source)
    elif rel_path.endswith(".json"):
        rows = scan_json(rel_path, source)
    else:
        rows = scan_text(source)

    if not rows:
        n = len(source.splitlines())
        rows = [(0, "NO_HIT", f"no match in {n} lines")]
    return rows


def render_report(results):
    lines = []
    lines.append(
        f"`scripts/rule_census.py` excludes itself by name (DR8.5) — its own "
        f"source is the literal text of the categories it defines."
    )
    lines.append("")
    lines.append("| File | Line | Category | Text | Determination | Reason |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for rel_path in sorted(results):
        for lineno, category, text in results[rel_path]:
            cell = text.replace("|", "\\|").replace("\n", " ").strip()
            line_cell = str(lineno) if lineno else ""
            lines.append(f"| `{rel_path}` | {line_cell} | {category} | `{cell}` |  |  |")
    return "\n".join(lines) + "\n"


def main():
    files = tracked_files()
    results = {}
    for rel_path in files:
        results[rel_path] = census_file(rel_path)

    report = render_report(results)
    results_path = REPO_ROOT / "docs/dev/results/PROCESS_RULE_HOME_RESULTS.md"
    existing = results_path.read_text(encoding="utf-8")
    marker = "## Census report (Step 3)"
    section = f"{marker}\n\n{report}"
    if marker in existing:
        before = existing.split(marker, 1)[0]
        existing = before + section
    else:
        existing = existing.rstrip("\n") + "\n\n" + section
    results_path.write_text(existing, encoding="utf-8")
    sys.stdout.write(f"Surveyed {len(files)} files, wrote census into {results_path}\n")


if __name__ == "__main__":
    main()
