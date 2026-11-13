# Published Real Values — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261113
**Branch:** `chore/issue-276-published-real-values` (from `main`, merges to `main` and `dev`)
**Target release:** none — `chore/*` carries no version bump, no `CHANGELOG.md` entry, no tag, no Release
**Originating item:** Issue #276
**Design study:** `../design/DESIGN_PUBLISHED_REAL_VALUES.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261113 | Ray | History is kept. The current tree is cleaned, and git history is not rewritten (design study Q1) | §1 |
| 20261113 | Ray | Five commit messages on `main` and `dev` hold value 4 and are kept: `98198cb`, `1789b0b`, `0ee9ebf`, `e7c1255`, `3334ab9` (design study F5). Rewriting them gives new SHAs to 1,758 commits and moves 75 tags (design study F6, F7), and the values stay in the history of the files regardless, so rewriting the messages alone removes nothing that the kept history does not still publish | AC2.1 |
| 20261113 | Ray | All published GitHub text is in scope: every issue and pull request body and comment, every review comment, and all Release notes. Edit-history versions that hold a value are listed for Ray to delete by hand in the web UI. Git history, the fork and clones are out of scope (design study Q2) | §1, Step 2, AC3.1, AC3.2 |
| 20261113 | Ray | The first criterion is restated to leave `tests/test_slack_channel_config.py:186` to #214, whose own criterion checks that file for the workspace name (design study Q3) | AC1.1 |
| 20261113 | Ray | Value 1 stays listed in `DEV_REAL_VALUES`, and the line at `docs/archive/specs/OLLAMA_PROVIDER_ALIGNMENT_SPEC.md:225` is reworded. A census reports every match as a hit, and Ray decides any exception (design study Q4) | Step 1, C1 |
| 20261113 | Ray | The `WorkmAIn Queue` project is private, so it publishes nothing and is out of scope | §1 |
| 20261113 | Ray | AC1's check reruns the census over the whole tree with #275's matcher (`real_values` and `_value_patterns` in `automation/style_check.py`), not `git grep`. `SKIPPED` in `automation/style_check.py` holds `docs/archive/`, so #275's own check does not read this branch's archive edits | C1 |
| 20261113 | Ray | The PR #11 step checks that the new body file is non-empty and holds the rest of the current body before `gh pr edit --body-file` | Step 2 |
| 20261113 | Ray | Approved. #276 runs the direct path without Role 2 review: no Caliper pass on the spec and no post-implementation review (`docs/standards/1-workflow.md` §1.2) | **Status:** |
| 20261113 | Spanner | A value is replaced by a placeholder in braces that names where the value is held, as `CLAUDE.md` § Client Reference requires. Braces are used because `<…>` outside a code span is read by GitHub's Markdown as an HTML tag and is not shown, and many of the lines are prose or table cells | DR1 |
| 20261113 | Spanner | Value 1 at `docs/archive/specs/PHASE6_DISCOVERY_RESULTS.md:179` takes value 2's placeholder. Value 1 is part of value 2 (design study F3), and the only place it is held is `workspace_name` in `~/.workmain/integrations/slack/config.json`, where value 2 is held | DR1 |
| 20261113 | Spanner | The census checks are written into §5 as commands, not added as a tracked script. The issue asks for the census to be run, not kept, and a script under `automation/` would be a mechanism the issue does not name | C1, C2, C3 |
| 20261113 | Spanner | Step 2 changes no tracked file, so it ends with no commit. What it did is recorded in the results artifact, which Step 3 commits | Step 2 |

---

## 1. Scope

**In scope:**

- The nine files under `docs/archive/` that hold a value (design study F1, F2). Each line that holds a value is rewritten as Step 1 lists.
- PR #11's body, the only published GitHub text that holds a value (design study F11), and the edit-history version that editing it creates.
- The five commit messages that hold a value, which are kept by Ray's decision (Decision Log).

**Out of scope:**

- Git history: earlier commits, tags and Releases are not rewritten, and nothing is force-pushed (design study Q1).
- The one fork, existing clones and outside caches, which no change to this repository reaches (design study F10, F12).
- The `WorkmAIn Queue` project, which is private and publishes nothing.
- `tests/test_slack_channel_config.py:186`, which #214 removes and checks.
- `automation/style_check.py` and its `SKIPPED` list, which are not changed. The checks this spec runs over `docs/archive/` are its own (§5).
- Which values `DEV_REAL_VALUES` lists, which is Ray's (`CLAUDE.md` § Client Reference).
- Reflowing the hard-wrapped lines in the archived files. A line is changed only where it holds a value.

## 3. Design rules

- **DR1 — A value is replaced by the placeholder for its position, and nothing else on the line changes.** Each match spans exactly what #275's matcher matches, and the characters around it stay as they are. The placeholders are:
  - value 4 → `{WORKMAIN_DEFAULT_CLIENT}`, the `.env` key that holds it
  - value 6 → `{clients.slack_channel}`, the table and column that hold it
  - value 1 and value 2 → `{workspace_name in ~/.workmain/integrations/slack/config.json}`, the file and key that hold them

  Value 6 contains value 4, and value 2 contains value 1 (design study F3). A line is therefore replaced longest value first, so that a match of value 6 or value 2 is replaced whole, before the shorter value inside it could be. The one line not handled by a placeholder is `docs/archive/specs/OLLAMA_PROVIDER_ALIGNMENT_SPEC.md:225`, which is reworded (Step 1).
- **DR2 — No real value is written into anything this branch publishes:** this spec, its results artifact, a commit message or a command's output that the results artifact quotes. A hit is named by its location and its position in `DEV_REAL_VALUES`, never by the value, as #275's check reports one. A file that holds a value, such as the saved PR #11 body, is written only to the session's scratchpad directory, outside the repository.
- **DR3 — Every match is a hit.** A census does not classify a match as an ordinary word or as anything else. An exception is Ray's, and is recorded as a row in this spec's Decision Log.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Every value in the nine archived files replaced by DR1's placeholder, and the line at `docs/archive/specs/OLLAMA_PROVIDER_ALIGNMENT_SPEC.md:225` reworded | the nine files listed below |
| 2 | PR #11's body edited by DR1, and the edit-history version that the edit creates listed for Ray | none |
| 3 | Results artifact | `docs/dev/results/PUBLISHED_REAL_VALUES_RESULTS.md` |

### Step 1 — Archived files

Each line is quoted as it stands at `959c52c`. `‹value N›` marks the place where value N stands; it is not text in the file. Each replacement applies DR1.

| File:line | Now | After |
| --- | --- | --- |
| `docs/archive/design/DESIGN_TIME_ENTRIES_REFACTOR_20260608_v1.2md:387` | `\| 2026-03-09 \| "‹value 4› Internal: Scheduled Wednesday..." \|` | `\| 2026-03-09 \| "{WORKMAIN_DEFAULT_CLIENT} Internal: Scheduled Wednesday..." \|` |
| `docs/archive/handoffs/PHASE11_GATE0_ASSESSMENT_20260512.md:77` | `"workspace_name": "‹value 2›",`, after its leading spaces | `"workspace_name": "{workspace_name in ~/.workmain/integrations/slack/config.json}",`, the leading spaces unchanged |
| `docs/archive/handoffs/PHASE11_GATE0_ASSESSMENT_20260512.md:78` | `"default_channel": "#‹value 6›"`, after its leading spaces | `"default_channel": "#{clients.slack_channel}"`, the leading spaces unchanged |
| `docs/archive/handoffs/SESSION_HANDOFF_PHASE11_5_COMPLETE_20260522.md:25` | `` `config.json default_channel` was migrated to `‹value 4›.slack_channel`; the config file now ``, after its leading spaces | `` `config.json default_channel` was migrated to `{WORKMAIN_DEFAULT_CLIENT}.slack_channel`; the config file now ``, the leading spaces unchanged |
| `docs/archive/handoffs/SESSION_HANDOFF_PHASE11_5_COMPLETE_20260522.md:143` | `` `config.json` previously held `default_channel: "#‹value 6›"`. This value was `` | `` `config.json` previously held `default_channel: "#{clients.slack_channel}"`. This value was `` |
| `docs/archive/handoffs/SESSION_HANDOFF_PHASE11_5_COMPLETE_20260522.md:144` | `` written to `‹value 4›.slack_channel` and removed from the config file. The file now contains `` | `` written to `{WORKMAIN_DEFAULT_CLIENT}.slack_channel` and removed from the config file. The file now contains `` |
| `docs/archive/handoffs/SESSION_HANDOFF_PHASE11_COMPLETE_20260512.md:36` | `\| 3 \| ClientRepository with atomic set_active(); migrate_client_attribution.py script; ‹value 4› seeded as active client \| 98198cb \|` | `\| 3 \| ClientRepository with atomic set_active(); migrate_client_attribution.py script; {WORKMAIN_DEFAULT_CLIENT} seeded as active client \| 98198cb \|` |
| `docs/archive/handoffs/SESSION_HANDOFF_PHASE11_COMPLETE_20260512.md:56` | `` \| `scripts/migrate_client_attribution.py` \| v1.0 \| 3 \| One-time script: backfills existing rows to ‹value 4› client_id \| `` | `` \| `scripts/migrate_client_attribution.py` \| v1.0 \| 3 \| One-time script: backfills existing rows to {WORKMAIN_DEFAULT_CLIENT} client_id \| `` |
| `docs/archive/handoffs/SESSION_HANDOFF_PHASE11_COMPLETE_20260512.md:122` | `` 3. `_restore_‹value 4›_active()` after each test to restore production state `` | `` 3. `_restore_{WORKMAIN_DEFAULT_CLIENT}_active()` after each test to restore production state `` |
| `docs/archive/handoffs/SESSION_HANDOFF_PHASE11_COMPLETE_20260512.md:182` | `feat(phase11): Gate 3 — client_repository, data attribution script, ‹value 4› seeded` | `feat(phase11): Gate 3 — client_repository, data attribution script, {WORKMAIN_DEFAULT_CLIENT} seeded` |
| `docs/archive/handoffs/SESSION_HANDOFF_PHASE8_COMPLETE.md:246` | `"default_channel": "#‹value 6›"`, after its leading spaces | `"default_channel": "#{clients.slack_channel}"`, the leading spaces unchanged |
| `docs/archive/handoffs/SESSION_HANDOFF_PHASE8_COMPLETE.md:283` | `workmain slack channel set ‹value 6›   # current default channel` | `workmain slack channel set {clients.slack_channel}   # current default channel` |
| `docs/archive/specs/OLLAMA_PROVIDER_ALIGNMENT_SPEC.md:225` | `- **‹value 1› EOD when Ollama is unreachable.** Each probe now waits the configured 30 s instead of 15 s.` | `- **Longer EOD wait when Ollama is unreachable.** Each probe now waits the configured 30 s instead of 15 s.` |
| `docs/archive/specs/PHASE11_5_DISTRIBUTION_SPEC_v1_4.md:134` | `` - Active client = ‹value 4› → recipient gets `client_id = ‹value 4›.id` `` | `` - Active client = {WORKMAIN_DEFAULT_CLIENT} → recipient gets `client_id = {WORKMAIN_DEFAULT_CLIENT}.id` `` |
| `docs/archive/specs/PHASE11_5_DISTRIBUTION_SPEC_v1_4.md:224` | `` recorded at Phase 11 Gate 0 (`"#‹value 6›"`). Confirm active client `` | `` recorded at Phase 11 Gate 0 (`"#{clients.slack_channel}"`). Confirm active client `` |
| `docs/archive/specs/PHASE11_5_DISTRIBUTION_SPEC_v1_4.md:293` | `'Slack channel for this client (e.g. #‹value 6›). '`, after its leading spaces | `'Slack channel for this client (e.g. #{clients.slack_channel}). '`, the leading spaces unchanged |
| `docs/archive/specs/PHASE11_5_DISTRIBUTION_SPEC_v1_4.md:439` | `` - Positional: `channel` — Slack channel name (e.g. `#‹value 6›` or `` | `` - Positional: `channel` — Slack channel name (e.g. `#{clients.slack_channel}` or `` |
| `docs/archive/specs/PHASE11_5_DISTRIBUTION_SPEC_v1_4.md:440` | `` `‹value 6›` — normalize by adding `#` if absent) ``, after its leading spaces | `` `{clients.slack_channel}` — normalize by adding `#` if absent) ``, the leading spaces unchanged |
| `docs/archive/specs/PHASE11_5_DISTRIBUTION_SPEC_v1_4.md:462` | `Current workspace: ‹value 2›` | `Current workspace: {workspace_name in ~/.workmain/integrations/slack/config.json}` |
| `docs/archive/specs/PHASE11_5_DISTRIBUTION_SPEC_v1_4.md:486` | `"workspace_name": "‹value 2›"`, after its leading spaces | `"workspace_name": "{workspace_name in ~/.workmain/integrations/slack/config.json}"`, the leading spaces unchanged |
| `docs/archive/specs/PHASE11_5_DISTRIBUTION_SPEC_v1_4.md:558` | `` - Display format: `"Channel: #‹value 6› (Client: ‹value 4›)"` `` | `` - Display format: `"Channel: #{clients.slack_channel} (Client: {WORKMAIN_DEFAULT_CLIENT})"` `` |
| `docs/archive/specs/PHASE11_5_DISTRIBUTION_SPEC_v1_4.md:597` | `"#‹value 6›" (migrated value confirmed)`, after its leading spaces | `"#{clients.slack_channel}" (migrated value confirmed)`, the leading spaces unchanged |
| `docs/archive/specs/PHASE13_DB_SCHEMA_REFACTOR_SPRINT_SPEC_v1_2.md:559` | `` - `"‹value 4› Internal: Scheduled Wednesday scope meeting..."` — 2026-03-09 — 4 matches `` | `` - `"{WORKMAIN_DEFAULT_CLIENT} Internal: Scheduled Wednesday scope meeting..."` — 2026-03-09 — 4 matches `` |
| `docs/archive/specs/PHASE6_DISCOVERY_RESULTS.md:179` | `SUMMARY: vText(b'Copy: Splunk Follow Up: ‹value 4› and ‹value 1› ')`, after its leading spaces | `SUMMARY: vText(b'Copy: Splunk Follow Up: {WORKMAIN_DEFAULT_CLIENT} and {workspace_name in ~/.workmain/integrations/slack/config.json} ')`, the leading spaces unchanged |

That is 24 lines. A line whose text at the time of the edit differs from its quote here, or a hit that C1 reports on a line not in this table, stops the step (`.claude/skills/session-start/references/spanner.md` § Working rules).

Commit: `docs(archive): replace real values with where each is held`.

### Step 2 — PR #11's body

1. Save the current body: `gh pr view 11 --json body --jq .body` to a file in the scratchpad directory (DR2), `before.md`.
2. Write `after.md` from `before.md` by DR1, in the scratchpad directory. The one hit, value 4 on body line 5, becomes `{WORKMAIN_DEFAULT_CLIENT}`.
3. Before the edit, check in one block, reading stderr, and stop on any failure:
   - `after.md` is non-empty.
   - `after.md` has as many lines as `before.md`, and every line but line 5 is identical.
   - Line 5 of `after.md` equals line 5 of `before.md` with the value 4 match replaced by `{WORKMAIN_DEFAULT_CLIENT}`.
   - `after.md` holds no value, by C3's matcher.
4. `gh pr edit 11 --body-file <scratchpad>/after.md`, run from the repository root.
5. Read the body back with `gh pr view 11 --json body --jq .body` and check that it equals `after.md`.
6. Run C3. Each edit-history version it reports with a hit is listed in the results artifact by its item and `editedAt` timestamp, for Ray to delete by hand in the web UI. The expected list is one entry: PR #11's body as it stood before step 4.
7. Delete `before.md` and `after.md`.

Rollback: `gh pr edit 11 --body-file <scratchpad>/before.md` restores the body. The value would then be published again, so rollback is Ray's call.

### Step 3 — Results artifact

`docs/dev/results/PUBLISHED_REAL_VALUES_RESULTS.md`, with each criterion's evidence written in DR2's form.

### Authorization points

None. Nothing is force-pushed, no GitHub object is deleted, and nothing is merged to `main` by this spec (`docs/standards/1-workflow.md` §1.4). Editing PR #11's body is not an authorization point, and Ray's approval of this spec approves it. Deleting the edit-history version is done by Ray by hand.

## 5. Acceptance criteria

The issue's criteria are restated here and its body needs the edit at close-out (`docs/standards/1-workflow.md` §1.2). AC1 now leaves `tests/test_slack_channel_config.py:186` to #214, and AC3 is added by Ray's Q2 ruling.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No tracked file on `main` holds a real value, apart from `tests/test_slack_channel_config.py:186`, which #214 removes and checks. The operator's own name as authorship is not a real value (`CLAUDE.md` § Client Reference) | C1 with `REF=main` reports no hit, or exactly `tests/test_slack_channel_config.py:186` holding values 1 and 2. Its per-value counts are recorded in the results artifact. Before the merge to `main`, C1 is run with `REF` set to this branch, for the results artifact |
| AC1.2 | Step 1 changes only the 24 lines its table lists, and changes each one as the table states | `git diff --unified=0 main -- docs/archive/` shows 24 removed and 24 added lines, one pair at each listed line; C1 reports no hit under `docs/archive/` |
| AC2.1 | Each commit message on `main` or `dev` that holds a real value is one Ray has recorded as kept, with his reason | C2 reports exactly `98198cb`, `1789b0b`, `0ee9ebf`, `e7c1255` and `3334ab9`, the five this spec's Decision Log records as kept |
| AC3.1 | No published GitHub text holds a real value in its current version: no issue or pull request title or body, issue or pull request comment, review body or review comment, Release name or notes, commit comment, milestone, label, or the repository's description, homepage or topics | C3 reports no current-version hit and no collection cut off by a page limit |
| AC3.2 | No edit-history version of published GitHub text that is still shown holds a real value | Ray, after deleting the versions Step 2 listed: C3 reports no edit-history hit |

### C1 — Tracked files

Reports every line of every tracked file at `REF`, and every path, that holds a value. A line is numbered from 1; a path hit is reported as line `path`.

```bash
REF=main python3 -I - <<'EOF'
import collections, os, subprocess, sys
from pathlib import Path
root = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip())
sys.path.insert(0, str(root / "automation"))
from style_check import _main_worktree, _value_patterns, real_values
values = real_values(_main_worktree() / ".env")
if not values:
    sys.exit("DEV_REAL_VALUES is not set in .env in the main working tree")
patterns = _value_patterns(values)
ref = os.environ["REF"]
git = lambda *a: subprocess.run(["git", *a], cwd=root, capture_output=True, check=True).stdout
counts = collections.Counter()
for path in filter(None, git("ls-tree", "-r", "-z", "--name-only", ref).decode().split("\0")):
    lines = [(f"{path}:path", path)] + [(f"{path}:{n}", line) for n, line in enumerate(git("show", f"{ref}:{path}").decode("utf-8", "replace").split("\n"), 1)]
    for where, line in lines:
        for position, pattern in enumerate(patterns, 1):
            if pattern.search(line):
                counts[position] += 1
                print(f"{where} holds value {position}")
print("hits per value:", {p: counts[p] for p in range(1, len(values) + 1)})
EOF
```

### C2 — Commit messages

Reports every commit on `main` or `dev` whose message, subject or body, holds a value, merge commits included.

```bash
python3 -I - <<'EOF'
import subprocess, sys
from pathlib import Path
root = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip())
sys.path.insert(0, str(root / "automation"))
from style_check import _main_worktree, _value_patterns, real_values
values = real_values(_main_worktree() / ".env")
if not values:
    sys.exit("DEV_REAL_VALUES is not set in .env in the main working tree")
patterns = _value_patterns(values)
log = subprocess.run(["git", "log", "--format=%h%x00%B%x1e", "main", "dev"], cwd=root, capture_output=True, text=True, check=True).stdout
read = 0
for entry in log.split("\x1e"):
    if "\x00" not in entry:
        continue
    read += 1
    short, message = entry.strip("\n").split("\x00", 1)
    found = [p for p, pattern in enumerate(patterns, 1) if pattern.search(message)]
    if found:
        print(f"commit {short} holds values {found}")
print("commits read:", read)
EOF
```

### C3 — Published GitHub text

Reports every item of published GitHub text, in its current version and in each edit-history version GitHub still shows, that holds a value, and any collection a page limit cut off. Run from the repository root.

```bash
python3 -I - <<'EOF'
import json, subprocess, sys
from pathlib import Path
root = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip())
sys.path.insert(0, str(root / "automation"))
from style_check import _main_worktree, _value_patterns, real_values
values = real_values(_main_worktree() / ".env")
if not values:
    sys.exit("DEV_REAL_VALUES is not set in .env in the main working tree")
patterns = _value_patterns(values)
REPO = "repos/lockdwn20/workmain"
EDITS = "userContentEdits(first:100){totalCount nodes{editedAt deletedAt diff}}"

def run(*args):
    out = subprocess.run(["gh", *args], cwd=root, capture_output=True, text=True)
    if out.returncode:
        sys.exit(out.stderr)
    return out.stdout

def gql(query, **variables):
    data = json.loads(run("api", "graphql", "-f", f"query={query}", *sum((["-F", f"{k}={v}"] for k, v in variables.items()), [])))
    if "errors" in data:
        sys.exit(json.dumps(data["errors"]))
    return data["data"]["repository"]

def rest(path):
    out = run("api", "--paginate", "--slurp", path)
    pages = json.loads(out)
    return [item for page in pages for item in (page if isinstance(page, list) else [page])]

def scan(where, text):
    found = [p for p, pattern in enumerate(patterns, 1) if pattern.search(text or "")]
    if found:
        print(f"{where} holds values {found}")

def scan_node(where, node, *fields):
    scan(where, "\n".join(node.get(f) or "" for f in fields))
    edits = node["userContentEdits"]
    if edits["totalCount"] > 100:
        print(f"CUT OFF: {where} edit history")
    for edit in edits["nodes"]:
        if not edit["deletedAt"]:
            scan(f"{where} edit-history version {edit['editedAt']}", edit["diff"])

def cut(where, connection, limit):
    if connection["totalCount"] > limit:
        print(f"CUT OFF: {where}")

cursor = None
while True:
    page = gql("""query($c:String){repository(owner:"lockdwn20",name:"workmain"){issues(first:20,after:$c){pageInfo{hasNextPage endCursor}
      nodes{number title body %s comments(first:100){totalCount nodes{url body %s}}}}}}""" % (EDITS, EDITS), **({"c": cursor} if cursor else {}))["issues"]
    for issue in page["nodes"]:
        scan_node(f"issue #{issue['number']}", issue, "title", "body")
        cut(f"issue #{issue['number']} comments", issue["comments"], 100)
        for comment in issue["comments"]["nodes"]:
            scan_node(comment["url"], comment, "body")
    if not page["pageInfo"]["hasNextPage"]:
        break
    cursor = page["pageInfo"]["endCursor"]

for number in (pr["number"] for pr in rest(f"{REPO}/pulls?state=all&per_page=100")):
    pr = gql("""query($n:Int!){repository(owner:"lockdwn20",name:"workmain"){pullRequest(number:$n){title body %s
      comments(first:100){totalCount nodes{url body %s}}
      reviews(first:40){totalCount nodes{url body %s comments(first:100){totalCount nodes{url body %s}}}}}}}""" % (EDITS, EDITS, EDITS, EDITS), n=number)["pullRequest"]
    scan_node(f"PR #{number}", pr, "title", "body")
    cut(f"PR #{number} comments", pr["comments"], 100)
    cut(f"PR #{number} reviews", pr["reviews"], 40)
    for comment in pr["comments"]["nodes"]:
        scan_node(comment["url"], comment, "body")
    for review in pr["reviews"]["nodes"]:
        scan_node(review["url"], review, "body")
        cut(f"{review['url']} comments", review["comments"], 100)
        for comment in review["comments"]["nodes"]:
            scan_node(comment["url"], comment, "body")

for release in rest(f"{REPO}/releases?per_page=100"):
    scan(f"Release {release['tag_name']}", f"{release['name'] or ''}\n{release['body'] or ''}")
for comment in rest(f"{REPO}/comments?per_page=100"):
    scan(comment["html_url"], comment["body"])
for milestone in rest(f"{REPO}/milestones?state=all&per_page=100"):
    scan(f"milestone {milestone['number']}", f"{milestone['title']}\n{milestone['description'] or ''}")
for label in rest(f"{REPO}/labels?per_page=100"):
    scan(f"label {label['name']}", f"{label['name']}\n{label['description'] or ''}")
repo = json.loads(run("api", REPO))
scan("repository description, homepage and topics", "\n".join([repo.get("description") or "", repo.get("homepage") or "", " ".join(repo.get("topics") or [])]))
print("done")
EOF
```

## 6. Test plan

Omitted. The change touches no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` (`docs/dev/specs/_TEMPLATE_SPEC.md`, direct path).

## 7. Risks and rollback

- **Step 1 changes a line it should not, or misses one.** AC1.2 compares the diff with the table, and C1 reports any hit that is left. Rollback is `git revert` of the step's commit.
- **Step 2 blanks or corrupts PR #11's body.** GitHub cannot restore an overwritten body except from its edit history. Step 2's checks run before the edit, and it reads the body back after. Rollback is Step 2's rollback line.
- **Deleting the edit-history version is a manual step**, and until Ray deletes it the value stays readable in PR #11's edit history. AC3.2 is not met until C3 shows it gone.
- **What this spec cannot reach:** git history, the fork, clones and caches keep every value (design study F6–F10, F12).
