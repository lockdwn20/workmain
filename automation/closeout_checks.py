"""
Mechanical checks for the `/closeout` skill (`.claude/skills/closeout/SKILL.md`).

Answers what can be answered by running something: does the issue resolve, what ACs
does it carry, what branch and branch type produced the merge, did the release and
deployment record clear, does the results artifact carry every AC as Met or cited
Carried. Judgement — whether an AC is met by delivered code — is not here; it lives
in the skill (DR3, `docs/dev/specs/CYCLE_CLOSEOUT_SPEC.md`).

    python3 automation/closeout_checks.py <issue-number> [--branch NAME]

Every external read (gh, git, systemctl, pytest, check_release_integrity.py) sits
behind a named module-level function so a test can replace it with `monkeypatch`,
mirroring `issue_validator.py` (DR10). Nothing here calls `issue_validator.gh_issue_state`:
that function returns open/closed only, while this needs body, labels and milestone
from a single call (DR10 / F14).
"""

import json
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


# ---------------------------------------------------------------------------
# Seams — every external read, named and module-level (DR10).
# ---------------------------------------------------------------------------

def gh_issue_view(number: int):
    """Live `gh issue view` lookup. Returns the issue dict, or None on failure."""
    result = subprocess.run(
        ["gh", "issue", "view", str(number), "--json",
         "number,title,state,body,labels,milestone,closedAt"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# §4.2 — Issue resolution and AC parsing
# ---------------------------------------------------------------------------

_ACS_MARKER_RE = re.compile(r"^\*\*ACs\*\*$")
_ACS_BULLET_RE = re.compile(r"^-\s+(.*)$")
_HEADING_ACS_RE = re.compile(r"^#+\s+Acceptance criteria", re.IGNORECASE)
_HEADING_ANY_RE = re.compile(r"^#+\s")
_CHECKBOX_BULLET_RE = re.compile(r"^-\s+\[[ xX]\]\s+(.*)$")


def _collect_bullets(lines, bullet_re, stop_at_heading):
    acs = []
    for line in lines:
        if stop_at_heading and _HEADING_ANY_RE.match(line):
            break
        if not line.strip():
            continue
        m = bullet_re.match(line)
        if m:
            acs.append(m.group(1).strip())
        elif acs:
            acs[-1] = acs[-1] + " " + line.strip()
    return acs


def parse_acs(body: str):
    """Returns the list of ACs, per the three shapes read in order (§4.2, C4)."""
    lines = body.splitlines()

    for i, line in enumerate(lines):
        if _ACS_MARKER_RE.match(line):
            return _collect_bullets(lines[i + 1:], _ACS_BULLET_RE, stop_at_heading=False)

    for i, line in enumerate(lines):
        if _HEADING_ACS_RE.match(line):
            return _collect_bullets(lines[i + 1:], _CHECKBOX_BULLET_RE, stop_at_heading=True)

    return []


class IssueResolutionError(Exception):
    pass


def resolve_issue(number: int):
    """Fetches the issue and parses its ACs. Raises IssueResolutionError on failure (DR4's exception)."""
    issue = gh_issue_view(number)
    if issue is None:
        raise IssueResolutionError(f"could not resolve issue #{number}")
    acs = parse_acs(issue.get("body") or "")
    return issue, acs


if __name__ == "__main__":
    print("closeout_checks.py: step 1 only — issue resolution and AC parsing.", file=sys.stderr)
    sys.exit(2)
