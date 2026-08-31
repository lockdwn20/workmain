"""
Validate a WorkmAIn issue JSON file against the schema and against live
GitHub state, then create the issue through `gh issue create`.

    python3 automation/issue_validator.py --new              # print the skeleton
    python3 automation/issue_validator.py issue.json         # validate, print command
    python3 automation/issue_validator.py issue.json --create  # validate, then create

The schema (`.github/ISSUE_TEMPLATE/issue.schema.json`) declares the key set
and each key's type and required-ness. This script owns the rules the schema
file cannot express: the §1.3 label-pair rule and existence checks
against live GitHub state (labels, milestones, referenced issues).

Why this exists: GitHub carries no type-vs-area marking on a label
(`Repository.issueTypes` is null for this repository), so the label
pair lives only in `docs/DEVELOPMENT_STANDARDS.md` §1.3, parsed at run
time rather than hardcoded here — a hardcoded pair would go stale the first
time §1.3 changes.
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA_RELATIVE_PATH = Path(".github/ISSUE_TEMPLATE/issue.schema.json")
TEMPLATE_RELATIVE_PATH = Path(".github/ISSUE_TEMPLATE/issue.template.json")
STANDARDS_RELATIVE_PATH = Path("docs/DEVELOPMENT_STANDARDS.md")
LABEL_PAIR_PHRASE = "label pair"
PROJECT_NAME = "WorkmAIn Queue"


class ValidationAbort(Exception):
    """Raised when the §1.3 label-pair parse itself fails (DR4's ordering exception)."""


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise ValidationAbort(f"could not find a repository root above {start}")


def parse_label_pair(standards_path: Path) -> list:
    """Parse the §1.3 label pair out of the standards file.

    Locates the section from a line starting `### 1.3` to the next line
    starting `###` or `---`, finds the first line containing the phrase
    "label pair", and returns its backtick-delimited tokens. That line
    must carry no other backticked text — every token on it is returned.
    """
    if not standards_path.exists():
        raise ValidationAbort(f"{standards_path}: file not found")

    lines = standards_path.read_text().splitlines()

    start = None
    for i, line in enumerate(lines):
        if line.startswith("### 1.3"):
            start = i
            break
    if start is None:
        raise ValidationAbort(f"{standards_path}: could not find section '### 1.3'")

    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("###") or lines[i].startswith("---"):
            end = i
            break

    target_line = None
    for line in lines[start:end]:
        if LABEL_PAIR_PHRASE in line:
            target_line = line
            break
    if target_line is None:
        raise ValidationAbort(
            f"{standards_path}: could not find the phrase '{LABEL_PAIR_PHRASE}' in section 1.3"
        )

    tokens = re.findall(r"`([^`]+)`", target_line)
    if not tokens:
        raise ValidationAbort(
            f"{standards_path}: no backtick-delimited tokens found on the "
            f"'{LABEL_PAIR_PHRASE}' line"
        )
    return tokens


def load_schema(schema_path: Path) -> dict:
    return json.loads(schema_path.read_text())


def _has_line_break(value: str) -> bool:
    """A line break in a single-line field is refused, not repaired (#88).

    `render_body()` emits one `- ` marker per `acs` item, so an embedded
    newline renders as a bullet followed by a loose line belonging to no AC,
    and the created issue silently misrepresents its own AC list.
    """
    return "\n" in value or "\r" in value


def _check_type(value, type_name: str) -> bool:
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "array":
        return isinstance(value, list)
    return False


def validate_schema(data, schema: dict):
    """Check `data` against `schema`. Returns (errors, normalized_data).

    Every declared key is checked; unknown keys fail by name. Missing
    optional keys are filled with their default so downstream checks never
    have to special-case absence.
    """
    if not isinstance(data, dict):
        return (["issue data must be a JSON object"], {})

    errors = []
    for key in data:
        if key not in schema:
            errors.append(f"unknown key: {key}")

    normalized = dict(data)
    for key, spec in schema.items():
        required = spec.get("required", False)
        if key not in data:
            if required:
                errors.append(f"missing required key: {key}")
            else:
                normalized[key] = spec.get("default")
            continue

        value = data[key]
        if value is None:
            if not spec.get("nullable", False):
                errors.append(f"key '{key}' must not be null")
            continue

        expected = spec["type"]
        if not _check_type(value, expected):
            errors.append(f"key '{key}' must be of type {expected}")
            continue

        if expected == "string":
            if not value.strip():
                errors.append(f"key '{key}' must be non-empty")
            max_length = spec.get("max_length")
            if max_length is not None and len(value) > max_length:
                errors.append(f"key '{key}' must be at most {max_length} characters")
            if spec.get("single_line") and _has_line_break(value):
                errors.append(f"key '{key}' must be a single line")

        if expected == "array":
            min_items = spec.get("min_items")
            if min_items is not None and len(value) < min_items:
                errors.append(f"key '{key}' must have at least {min_items} entry(ies)")
            item_type = spec.get("items")
            for i, item in enumerate(value):
                if item_type and not _check_type(item, item_type):
                    errors.append(f"key '{key}[{i}]' must be of type {item_type}")
                elif item_type == "string" and not item.strip():
                    errors.append(f"key '{key}[{i}]' must be non-empty")
                elif item_type == "string" and spec.get("single_line") and _has_line_break(item):
                    errors.append(f"key '{key}[{i}]' must be a single line")

    return errors, normalized


def validate_label_pair_rule(data: dict, label_pair: list) -> list:
    """§1.3: an issue carries at most one of the label pair, and exactly one when unscheduled.

    The two halves are gated differently, on purpose. *At most one* holds
    whatever the milestone: two pair labels is incoherent however the issue
    was scheduled. *At least one* applies only with no milestone — a pair
    label kept after the work was scheduled is the normal record of
    something pulled in from the unscheduled pool, and a scheduled issue
    need not carry one at all.
    """
    named = "/".join(label_pair)
    present = [label for label in data.get("labels") or [] if label in set(label_pair)]

    if len(present) > 1:
        return [f"issue carries more than one of {named}: {', '.join(present)}"]
    if not present and data.get("milestone") is None:
        return [f"unscheduled issue carries none of {named}"]
    return []


def _check_open_issue(field: str, number: int, get_issue_state) -> list:
    state = get_issue_state(number)
    if state is None:
        return [f"{field}: issue #{number} does not exist"]
    if state == "CLOSED":
        return [f"{field}: issue #{number} is closed"]
    return []


def validate_live_state(data: dict, live_labels: set, live_milestones: set, get_issue_state) -> list:
    """Check `data` against live GitHub state. `get_issue_state` is the per-number lookup seam."""
    errors = []

    for label in data.get("labels", []):
        if label not in live_labels:
            errors.append(f"label does not exist: {label}")

    milestone = data.get("milestone")
    if milestone is not None and milestone not in live_milestones:
        errors.append(f"milestone does not exist: {milestone}")

    parent = data.get("parent")
    if parent is not None:
        errors.extend(_check_open_issue("parent", parent, get_issue_state))

    for field in ("blocked_by", "blocking"):
        for number in data.get(field) or []:
            errors.extend(_check_open_issue(field, number, get_issue_state))

    return errors


def render_body(context: str, acs: list) -> str:
    lines = [context.strip(), "", "**ACs**", ""]
    lines.extend(f"- {ac.strip()}" for ac in acs)
    return "\n".join(lines) + "\n"


def build_command(data: dict, body_file: Path) -> list:
    """Map validated issue data to a `gh issue create` argv, per §4.3."""
    cmd = ["gh", "issue", "create", "--title", data["title"], "--body-file", str(body_file)]

    if data.get("milestone") is not None:
        cmd += ["--milestone", data["milestone"]]
    if data.get("parent") is not None:
        cmd += ["--parent", str(data["parent"])]

    for label in data.get("labels", []):
        cmd += ["--label", label]

    blocked_by = data.get("blocked_by") or []
    if blocked_by:
        cmd += ["--blocked-by", ",".join(str(n) for n in blocked_by)]

    blocking = data.get("blocking") or []
    if blocking:
        cmd += ["--blocking", ",".join(str(n) for n in blocking)]

    cmd += ["--project", PROJECT_NAME]
    return cmd


def gh_issue_state(number: int):
    """Live `gh issue view` lookup. Returns the issue's state, or None if it does not exist."""
    result = subprocess.run(
        ["gh", "issue", "view", str(number), "--json", "number,state"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)["state"]


def gh_live_labels() -> set:
    result = subprocess.run(
        ["gh", "label", "list", "--limit", "100", "--json", "name"],
        capture_output=True,
        text=True,
        check=True,
    )
    return {item["name"] for item in json.loads(result.stdout)}


def gh_live_milestones() -> set:
    result = subprocess.run(
        ["gh", "api", "repos/:owner/:repo/milestones", "--jq", ".[].title"],
        capture_output=True,
        text=True,
        check=True,
    )
    return {line for line in result.stdout.splitlines() if line}


def validate_issue(data: dict, schema: dict, label_pair: list, live_labels: set, live_milestones: set, get_issue_state):
    """Run every check and return (errors, normalized_data). Total reporting — DR4."""
    errors, normalized = validate_schema(data, schema)
    errors += validate_label_pair_rule(normalized, label_pair)
    errors += validate_live_state(normalized, live_labels, live_milestones, get_issue_state)
    return errors, normalized


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", help="path to the issue JSON file")
    parser.add_argument("--new", action="store_true", help="print the skeleton template to stdout")
    parser.add_argument("--create", action="store_true", help="run gh issue create after validation succeeds")
    args = parser.parse_args(argv)

    repo_root = find_repo_root(Path(__file__))

    if args.new:
        template_path = repo_root / TEMPLATE_RELATIVE_PATH
        print(template_path.read_text(), end="")
        return 0

    if not args.file:
        parser.error("file is required unless --new is given")

    data = json.loads(Path(args.file).read_text())

    standards_path = repo_root / STANDARDS_RELATIVE_PATH
    try:
        label_pair = parse_label_pair(standards_path)
    except ValidationAbort as exc:
        print(str(exc), file=sys.stderr)
        return 1

    schema = load_schema(repo_root / SCHEMA_RELATIVE_PATH)
    live_labels = gh_live_labels()
    live_milestones = gh_live_milestones()

    errors, normalized = validate_issue(
        data, schema, label_pair, live_labels, live_milestones, gh_issue_state
    )

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as body_file:
        body_file.write(render_body(normalized["context"], normalized["acs"]))
        body_path = Path(body_file.name)

    try:
        cmd = build_command(normalized, body_path)
        print(" ".join(_shell_quote(part) for part in cmd))

        if args.create:
            result = subprocess.run(cmd)
            if result.returncode != 0:
                return result.returncode
    finally:
        body_path.unlink(missing_ok=True)

    return 0


def _shell_quote(part: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9._/:-]+", part):
        return part
    return "'" + part.replace("'", "'\\''") + "'"


if __name__ == "__main__":
    sys.exit(main())
