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


def git_merge_log(ref: str):
    """(sha, subject) pairs on `ref`'s first-parent chain, merges only."""
    result = subprocess.run(
        ["git", "log", "--merges", "--first-parent", "--format=%H%x09%s", ref],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        return []
    pairs = []
    for line in result.stdout.splitlines():
        if "\t" in line:
            sha, subject = line.split("\t", 1)
            pairs.append((sha, subject))
    return pairs


def git_ref_exists(ref: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return result.returncode == 0


def git_diff_paths(ref_a: str, ref_b: str):
    result = subprocess.run(
        ["git", "diff", "--name-only", ref_a, ref_b],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return [line for line in result.stdout.splitlines() if line]


def git_merge_base(ref_a: str, ref_b: str):
    result = subprocess.run(
        ["git", "merge-base", ref_a, ref_b],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_is_ancestor(ref: str, target: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ref, target],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return result.returncode == 0


# ---------------------------------------------------------------------------
# §4.3 — Branch resolution and branch type
# ---------------------------------------------------------------------------

BRANCH_TYPES = ("chore", "feature", "hotfix")


class BranchResolution:
    def __init__(self, name=None, merge_sha=None, resolved_on=None, changed_paths=None,
                 error=None, branch_type=None):
        self.name = name
        self.merge_sha = merge_sha
        self.resolved_on = resolved_on
        self.changed_paths = changed_paths or []
        self.error = error
        self.branch_type = branch_type


def _branch_name_in_subject(subject: str, issue_number: int):
    pattern = re.compile(
        rf"\b(?:{'|'.join(BRANCH_TYPES)})/issue-{issue_number}(?!\d)[\w-]*"
    )
    m = pattern.search(subject)
    return m.group(0) if m else None


def _find_merge_for_issue(ref: str, issue_number: int):
    for sha, subject in git_merge_log(ref):
        name = _branch_name_in_subject(subject, issue_number)
        if name:
            return name, sha
    return None, None


def branch_type_of(branch_name: str):
    return branch_name.split("/", 1)[0]


def resolve_branch(issue_number: int, explicit_branch: str = None) -> BranchResolution:
    """§4.3 resolution order: `--branch` first, then main's first-parent chain, then dev's."""
    if explicit_branch:
        prefix = branch_type_of(explicit_branch)
        if prefix not in BRANCH_TYPES:
            return BranchResolution(
                name=explicit_branch,
                error=f"branch prefix is not one of {BRANCH_TYPES}: {prefix}",
                branch_type=prefix,
            )
        if git_ref_exists(explicit_branch):
            base = git_merge_base("main", explicit_branch) or git_merge_base("dev", explicit_branch)
            changed = git_diff_paths(base, explicit_branch) if base else []
            return BranchResolution(
                name=explicit_branch, resolved_on=explicit_branch,
                changed_paths=changed, branch_type=prefix,
            )
        return BranchResolution(name=explicit_branch, branch_type=prefix, changed_paths=[])

    name, sha = _find_merge_for_issue("main", issue_number)
    resolved_on = "main"
    if not name:
        name, sha = _find_merge_for_issue("dev", issue_number)
        resolved_on = "dev"

    if not name:
        return BranchResolution(error=f"no merge commit resolves issue #{issue_number}")

    prefix = branch_type_of(name)
    if prefix not in BRANCH_TYPES:
        return BranchResolution(
            name=name, merge_sha=sha, resolved_on=resolved_on,
            error=f"branch prefix is not one of {BRANCH_TYPES}: {prefix}",
            branch_type=prefix,
        )

    changed = git_diff_paths(f"{sha}^1", f"{sha}^2")
    return BranchResolution(
        name=name, merge_sha=sha, resolved_on=resolved_on,
        changed_paths=changed, branch_type=prefix,
    )


def dev_merge_sha_for(issue_number: int, resolution: BranchResolution):
    """The dev-side merge commit, used for the §2.6 restart-timestamp comparison."""
    if resolution.resolved_on == "dev":
        return resolution.merge_sha
    _, sha = _find_merge_for_issue("dev", issue_number)
    return sha or resolution.merge_sha


def merge_tip_ref(resolution: BranchResolution):
    if resolution.merge_sha:
        return f"{resolution.merge_sha}^2"
    return resolution.resolved_on or resolution.name


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


def git_commit_timestamp(ref: str):
    result = subprocess.run(
        ["git", "show", "-s", "--format=%cI", ref],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def run_pytest(args):
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return result.returncode, result.stdout + result.stderr


def run_check_release_integrity():
    result = subprocess.run(
        [sys.executable, str(CHECK_RELEASE_INTEGRITY_PATH)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return result.returncode, result.stdout + result.stderr


def get_active_enter_timestamp():
    result = subprocess.run(
        ["systemctl", "--user", "show", DAEMON_SERVICE, "--property=ActiveEnterTimestamp"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    if "=" in value:
        value = value.split("=", 1)[1]
    return value or None


# ---------------------------------------------------------------------------
# §4.1 — The workpaths
# ---------------------------------------------------------------------------

CHECK_RELEASE_INTEGRITY_PATH = Path("automation/check_release_integrity.py")
VERSION_FILE_PATH = Path("workmain/__version__.py")
DAEMON_SERVICE = "workmain-notify.service"
BUMP_MAGNITUDE = {"feature": "minor", "hotfix": "patch"}
MERGE_TARGETS = {
    "chore": ("main", "dev"),
    "hotfix": ("main", "dev"),
    "feature": ("dev",),
}

_VERSION_RE = re.compile(r'__version__\s*=\s*"([^"]+)"')


class Check:
    def __init__(self, name, status, detail=""):
        self.name = name
        self.status = status  # "pass" | "fail" | "n/a"
        self.detail = detail

    def __repr__(self):
        return f"Check({self.name!r}, {self.status!r}, {self.detail!r})"


def read_version_at(ref: str):
    content = git_show_file(ref, str(VERSION_FILE_PATH))
    if content is None:
        return None
    m = _VERSION_RE.search(content)
    return m.group(1) if m else None


def classify_bump(before: str, after: str):
    if before == after:
        return "none"
    b = tuple(int(x) for x in before.split("."))
    a = tuple(int(x) for x in after.split("."))
    if a[0] != b[0]:
        return "major"
    if a[1] != b[1]:
        return "minor"
    return "patch"


def merge_tip_ref(resolution):
    if resolution.merge_sha:
        return f"{resolution.merge_sha}^2"
    return resolution.resolved_on or resolution.name


def dev_merge_sha_for(issue_number: int, resolution):
    """The dev-side merge commit, used for the §2.6 restart-timestamp comparison."""
    if resolution.resolved_on == "dev":
        return resolution.merge_sha
    _, sha = _find_merge_for_issue("dev", issue_number)
    return sha or resolution.merge_sha


def check_version_bump(resolution):
    branch_type = resolution.branch_type
    if not resolution.merge_sha:
        return Check("version bump", "n/a", "no merge commit to compare parents on")
    before = read_version_at(f"{resolution.merge_sha}^1")
    after = read_version_at(f"{resolution.merge_sha}^2")
    if branch_type == "chore":
        if before != after:
            return Check("version bump", "fail",
                          f"§2.2 forbids a version bump on chore/*: {before} -> {after}")
        return Check("version bump", "n/a", "§2.2 forbids it")
    if before == after:
        return Check("version bump", "fail", f"no version bump: stayed at {before}")
    expected = BUMP_MAGNITUDE[branch_type]
    actual = classify_bump(before, after)
    if actual != expected:
        return Check("version bump", "fail",
                      f"expected a {expected} bump per §2.5, got {actual}: {before} -> {after}")
    return Check("version bump", "pass", f"{before} -> {after} ({actual})")


def check_release_ledger(branch_type):
    """The changelog entry, the tag and the GitHub Release for the new version,
    plus the repo-wide check_release_integrity.py invocation (DR9)."""
    rc, output = run_check_release_integrity()
    checks = []
    for label in ("changelog entry for the new version",
                  "tag for the new version",
                  "GitHub Release for the tag"):
        if branch_type == "chore":
            checks.append(Check(label, "n/a", "§2.2 forbids it"))
        elif rc != 0:
            checks.append(Check(label, "fail", output.strip()))
        else:
            checks.append(Check(label, "pass", "check_release_integrity.py exited 0"))
    if rc != 0:
        checks.append(Check("check_release_integrity.py exits zero", "fail", output.strip()))
    else:
        checks.append(Check("check_release_integrity.py exits zero", "pass", "exited 0"))
    return checks


def check_application_suite():
    rc, output = run_pytest(["tests/"])
    if rc != 0:
        return Check("application suite passes", "fail", output.strip()[-2000:])
    return Check("application suite passes", "pass", "pytest tests/ passed")


def check_automation_suite(changed_paths):
    touched = any(p.startswith("automation/") for p in changed_paths)
    if not touched:
        return Check("automation/ suite passes", "n/a", "branch did not touch automation/")
    rc, output = run_pytest(["automation/"])
    if rc != 0:
        return Check("automation/ suite passes", "fail", output.strip()[-2000:])
    return Check("automation/ suite passes", "pass", "pytest automation/ passed")


def check_daemon_restart(branch_type, issue_number, resolution):
    if branch_type == "chore":
        return Check("daemon restarted after the dev merge", "n/a", "no application code")
    dev_sha = dev_merge_sha_for(issue_number, resolution)
    if not dev_sha:
        return Check("daemon restarted after the dev merge", "fail",
                      "could not resolve the dev merge commit")
    merge_time = git_commit_timestamp(dev_sha)
    active_time = get_active_enter_timestamp()
    if not active_time:
        return Check("daemon restarted after the dev merge", "fail",
                      "could not read ActiveEnterTimestamp")
    if merge_time and active_time < merge_time:
        return Check("daemon restarted after the dev merge", "fail",
                      f"ActiveEnterTimestamp {active_time} predates the merge {merge_time}")
    return Check("daemon restarted after the dev merge", "pass",
                 f"ActiveEnterTimestamp {active_time} postdates the merge {merge_time}")


def check_merge_targets(branch_type, resolution):
    tip = merge_tip_ref(resolution)
    expected = MERGE_TARGETS[branch_type]
    missing = [ref for ref in expected if not git_is_ancestor(tip, ref)]
    if missing:
        return Check("merged to both main and dev", "fail",
                      f"not reachable from: {', '.join(missing)}")
    return Check("merged to both main and dev", "pass",
                 f"reachable from: {', '.join(expected)}")


def evaluate_workpaths(issue_number: int, resolution):
    """Runs every applicable check for the branch's type (§4.1). `n/a` rows carry a reason (DR1)."""
    branch_type = resolution.branch_type
    checks = [check_version_bump(resolution)]
    checks.extend(check_release_ledger(branch_type))
    checks.append(check_application_suite())
    checks.append(check_automation_suite(resolution.changed_paths))
    checks.append(check_daemon_restart(branch_type, issue_number, resolution))
    checks.append(check_merge_targets(branch_type, resolution))
    return checks


if __name__ == "__main__":
    print("closeout_checks.py: steps 1-3 only — no results-artifact verification yet.",
          file=sys.stderr)
    sys.exit(2)
