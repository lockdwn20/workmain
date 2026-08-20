# Queue Sequencing — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20260819
**Branch:** `chore/issue-84-queue-sequencing` (from `main`, merges to `main` and `dev`)
**Target release:** none — `chore/*` carries no version bump, no `CHANGELOG.md` entry, no tag, no Release
**Originating item:** Issue #84, child of #80
**Design study:** `docs/dev/design/RECON_CYCLE_MECHANICS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260814 | Ray | Recon Q1 — rank comes from drag `POSITION`, not a `NUMBER` field. No custom field is created | Accepted. DR1, DR2. #84's third AC is satisfied literally |
| 20260814 | Ray | Recon Q5 — milestone sequence is migrated into the Project and **does not remain in prose**. Resolving F11/F12 is the reason the Project exists | Accepted. Step 5 strips the ordering prose; AC4.3 checks it |
| 20260814 | Ray | Recon Q5a — a board holds issues, not milestones, so milestone order is expressed through the milestone carried on each ranked item | Accepted, and superseded in mechanism by F31/C5: one read returns rank and milestone together, so no grouping behaviour is relied on. AC2.1 |
| 20260819 | Ray | Placing issues in the Project is for the express purpose of ordering them. **The next issue on the list is what comes next** | Accepted. DR1 — this is the sequencing rule §1.6 states |
| 20260819 | Spanner | The recon never asked how closed items leave the read. They do not: the board holds 61 items of which 56 are open (C1) | C3/C4 record the two candidate filters and DR3 selects the one that does not read `Status` |
| 20260819 | Spanner | Read mechanism — `automation/queue.py` over GraphQL, not a documented `gh project item-list` command | Decided by §1.2, which requires mechanically testable ACs: a documented command yields ACs that grep a document for its own text, and leaves F30's truncation trap silent. The two-issue precedent (#82 `issue_validator.py`, #83 `closeout_checks.py`) puts cycle mechanics in `automation/` |
| 20260819 | Spanner | The rule lands as a **new §1.6**, not inside §1.3 | #81 deliberately kept §1.3 mechanism-free and its AC1.4 greps §1.3 to prove it. Appending §1.6 renumbers nothing, so no citation breaks |
| 20260819 | Spanner | Ordering #84 ahead of #89 was itself unresolvable by any written rule until this spec ships | Recorded, not acted on. Ray restored #84's board position on 20260819; the board answered it, which is the mechanism this spec writes down |

---

## 1. Scope

**In scope:**

- `automation/queue.py` — the read that returns Project #3 in board order, open items only, with no browser.
- `automation/queue_test.py` and its fixtures in `automation/fixtures/`.
- `docs/DEVELOPMENT_STANDARDS.md` — a new **§1.6 Sequencing**, appended after §1.5. The board is the order; the next open item is what comes next; the preemption rule.
- `CLAUDE.md` Project Status — a pointer to §1.6. The existing `gh issue list` block stays: it reads issue *content*, and §1.6 owns *order*.
- The five milestone descriptions on GitHub — ordering prose removed, per Ray's Q5 answer.

**Out of scope:**

- **#85's session-open skills.** #85 consumes `queue.py`; it is not built here.
- **#89's `Issue: #NN` commit trailer.** Different mechanism, different file (`.githooks/commit-msg`), its own issue.
- **Board membership.** Every issue joins Project #3 at creation — that is #82's DR6 and it already ships. This spec adds nothing to how items get on the board, only how their order is read.
- **Any project write.** No field is created, no item is moved, no item is archived. Ordering is Ray's, through the Web UI (DR2).
- **Removing the built-in `Status` field.** It cannot be removed (C8). DR3 makes it unread instead, which is the reachable form of #84's third AC.
- **Milestone description content beyond ordering prose.** The `Source: implementation-checklist.md` provenance line in all five descriptions cites an archived document. It is provenance, not a decision basis, so it stays — see §7.
- **`workmain/**`, `tests/**` and `scripts/**`.** No application behaviour changes, which is what keeps this on `chore/*` per §2.2.

## 2. Verified current state

Verified 20260819 against live GitHub and the working tree. Findings carried from the recon are marked as such and were re-checked, not copied.

| # | Claim | Evidence |
| --- | --- | --- |
| C1 | Project **#3 "WorkmAIn Queue"** is linked to `lockdwn20/workmain` and holds **61 items, of which 56 are open**. Closed issues stay on the board and stay in every read | `gh project item-list 3 --owner lockdwn20 --format json --limit 200` → 61; `--query "is:open"` → 56 |
| C2 | GraphQL `items(orderBy:{field:POSITION,direction:ASC})` returns the board's own order. Live head at authoring time: `80, 81, 82, 86, 87, 83, 89, 84, 85, 29 …`, and after Ray's 20260819 reorder `80, 84, 85, 89, 29 …` | `gh api graphql` on `user(login:"lockdwn20"){projectV2(number:3){items(orderBy:…)}}`; recon F30 re-confirmed |
| C3 | `gh project item-list --format json` carries **no issue state**. Its only state-shaped field is the project's built-in `status`, which reads `Done` for closed items. Filtering closed work out of an `item-list` read therefore means reading `Status` | Item JSON for #81: keys are `content{body,number,repository,title,type,url}`, `id`, `labels`, `repository`, `status`, `title`. No `state` |
| C4 | `--query "is:open"` **does** filter on real issue state — 56 of 61 — but the filtered output still carries no state field, so a caller cannot verify the filter applied | `gh project item-list … --query "is:open"` → 56 items, none with `status: Done` |
| C5 | A **single** GraphQL query returns, per item: `content.number`, `content.state`, `content.title`, `content.milestone.title`, `content.labels`, `content.parent.number`, `content.subIssuesSummary{total,completed}` — plus `items.totalCount` and `items.pageInfo.hasNextPage` | Live query, 20260819. `#80` returns `state: OPEN`, `subIssuesSummary{total:6,completed:4}`, `parent: null` |
| C6 | `gh project item-list` defaults to `--limit 30` and truncates **silently** — no warning, no count. GraphQL `pageInfo.hasNextPage` makes the same condition detectable; at `first:100` it is `false` against 61 items | `gh project item-list --help`; live query `totalCount=61 hasNextPage=false`; recon F6, F30 |
| C7 | Project #3 carries **13 fields, all GitHub built-ins** — `Title`, `Assignees`, `Status`, `Labels`, `Linked pull requests`, `Milestone`, `Repository`, `Reviewers`, `Parent issue`, `Sub-issues progress`, `Created`, `Updated`, `Closed`. **Zero custom fields** | `gh project field-list 3 --owner lockdwn20`; recon F29 re-confirmed |
| C8 | `Status` is auto-populated by GitHub, cannot be deleted, and persists in `--format json` output even when hidden in the Web UI view | Recon F32, re-confirmed: every item carries `status`, and closed items read `Done` |
| C9 | `docs/DEVELOPMENT_STANDARDS.md` states **no rule for what comes next**. `grep -nEi "next\|priority\|prioriti\|sequenc\|order\|queue\|rank\|preempt\|schedul"` returns eight hits, all unrelated — spec §4 step ordering, CLI group ordering, `rich.Table` column ordering, the `schedule` command group | `grep` over `docs/DEVELOPMENT_STANDARDS.md` |
| C10 | §1.3 names no sequencing mechanism **by design**, and #81's AC1.4 greps §1.3 for `Project #3`, `WorkmAIn Queue` and `item-list` requiring zero hits | `docs/dev/specs/TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md:63,95,179` |
| C11 | `CLAUDE.md` Project Status asserts *"Item state, priority, and sequencing live in GitHub Issues — never in a document"*, supplies an **unranked** `gh issue list --json …` command, and points to §1.3 for what milestones and labels mean | `CLAUDE.md`, § Project Status |
| C12 | All five milestones carry `due_on: null`, so milestone numbers are creation order and GitHub supplies no ordering. **Phase 14's description carries ordering prose verbatim:** *"Blocked until both Slack sprints close (Pre-Phase 14 Gate)."* Phases 15 and 18 state no relation to any other milestone | `gh api repos/lockdwn20/workmain/milestones`; recon F11, F12 re-confirmed |
| C13 | `automation/` precedent: stdlib only, a module docstring stating why the file exists, `find_repo_root(Path(__file__))` rather than a fixed parent, and **every external read behind a named module-level function** that tests replace with `monkeypatch` | `automation/issue_validator.py:256-285` (`gh_issue_state`, `gh_live_labels`, `gh_live_milestones`); `automation/closeout_checks.py:26-50` (`find_repo_root`, `gh_issue_view`); `automation/issue_validator_test.py:145-152` |
| C14 | `pyproject.toml` sets `testpaths = ["tests"]`, so a bare `pytest` runs the application suite only and `automation/` tests run when named | `pyproject.toml` `[tool.pytest.ini_options]` |
| C15 | §2.2 makes `docs/**` and `automation/` chore-eligible, and exempts `chore/*` from version bump, `CHANGELOG.md`, tag and Release | `docs/DEVELOPMENT_STANDARDS.md` §2.2 |
| C16 | Baselines at authoring time: `pytest tests/` → **934 passed**; `pytest automation/` → **45 passed** | Both run on this branch, 20260819 |

## 3. Design rules

- **DR1 — The board is the order.** Position in Project #3 is the sequence, and the next open item is what comes next (Ray, 20260819). No document restates the order, no document names a next item, and the order exists in exactly one place.
- **DR2 — Rank is read, never written.** `queue.py` issues one read-only GraphQL query and makes no GitHub write of any kind: no item moved, no field created, no item archived. Ordering is Ray's, set through the Web UI. This is what keeps the tool re-runnable and keeps the board the single authority rather than a cache of one.
- **DR3 — Issue state comes from the issue, never from `Status`.** `Status` is auto-populated, un-deletable and duplicates issue state (C8) — exactly what #84's third AC rules out. `queue.py` reads `content.state` and never references the project's `status` field, which AC3.2 checks by grep. This is also why the read is GraphQL and not `item-list --query "is:open"`: the latter's output cannot prove the filter applied (C4).
- **DR4 — Truncation is fatal, never silent.** If `pageInfo.hasNextPage` is true the run exits non-zero with the page size and `totalCount` named. A queue that silently loses its tail is worse than no queue, and F30 recorded exactly that trap in `item-list`'s default `--limit 30`.
- **DR5 — Nothing is enumerated that can be derived.** No document holds a list of issues, a milestone order table, or a rank number. The rank integers `queue.py` prints are computed from position at read time and stored nowhere.
- **DR6 — A parent with open children is not the next item.** An issue is workable only if it is independently verifiable on its own (§1.3); a parent holding open children is a container for work, not the work. `queue.py` marks such an item and `--next` skips past it, deriving the fact from `subIssuesSummary` (C5) rather than from any list.
- **DR7 — Preemption is expressed by position.** Preempting work is placed at the top of the board; nothing else marks it. There is no preempting label, no priority field, and no general category of preempting work — see §4.3.
- **DR8 — Anything this spec does not cover stops the step.** Role 3 escalation procedure, `CLAUDE.md` Role 3. Do not self-resolve.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `queue.py` — the GraphQL read, board ordering, open-only default, truncation guard | `automation/queue.py` |
| 2 | Output modes — ranked listing, `--next`, `--milestone`, `--all`, `--json` | `automation/queue.py` |
| 3 | Tests over steps 1–2 | `automation/queue_test.py`, `automation/fixtures/queue_*.json` |
| 4 | §1.6 Sequencing, and the `CLAUDE.md` pointer | `docs/DEVELOPMENT_STANDARDS.md`, `CLAUDE.md` |
| 5 | Milestone descriptions — ordering prose removed | GitHub milestones 1–5 (no file) |

### 4.1 Step 1 — the read

One module-level function performs the GraphQL call and nothing else calls out of process, per C13:

```python
def gh_project_items(project_number: int, owner: str, page_size: int):
    """Live read of a ProjectV2 in board (POSITION) order. Returns the items payload."""
```

The query is fixed text with the owner, project number and page size substituted:

```graphql
query($owner: String!, $number: Int!, $first: Int!) {
  user(login: $owner) {
    projectV2(number: $number) {
      items(first: $first, orderBy: {field: POSITION, direction: ASC}) {
        totalCount
        pageInfo { hasNextPage }
        nodes {
          content {
            ... on Issue {
              number state title
              milestone { title }
              labels(first: 20) { nodes { name } }
              parent { number }
              subIssuesSummary { total completed }
            }
          }
        }
      }
    }
  }
}
```

- `OWNER = "lockdwn20"` and `PROJECT_NUMBER = 3` are module constants with a comment naming Project #3 by title, so a rename is a one-line fix rather than a hunt.
- `PAGE_SIZE = 100`, GitHub's per-page maximum for this connection.
- `hasNextPage` true → exit non-zero, naming `PAGE_SIZE` and `totalCount` (DR4). No pagination loop is written: at 61 items a second page is a fact worth surfacing, not a fact worth hiding behind a loop.
- Nodes with no `content.number` — draft items and pull requests — are dropped before ranking. The board holds none today (C1: 61 items, all issues), and a draft appearing later must not shift the numbering of everything below it.
- The project's `status` field is not requested and not read (DR3).

### 4.2 Step 2 — output

| Mode | Behaviour |
| --- | --- |
| default | Open items in board order, one per line: rank, `#N`, milestone or `—`, title. Rank is the 1-based index **after** the open filter, so the printed queue is contiguous |
| `--next` | The first open item that is not a parent with open children (DR6), one line. Exit non-zero if the queue is empty |
| `--milestone <title>` | Board order restricted to one milestone. Ranks stay the full-queue ranks, so an item's position across milestones is still visible from a within-milestone read |
| `--all` | Include closed items, each marked `closed`. The default is open-only |
| `--json` | The same records as JSON, for #85 to consume without parsing text |

A parent with open children is printed in the default listing with a marker and its `subIssuesSummary` counts — it is skipped as *the next item*, not hidden from the queue.

### 4.3 Step 4 — §1.6 Sequencing

Appended after §1.5, so §2 onward is untouched and no citation moves. Wording:

> ### 1.6 Sequencing
>
> **The board is the order.** Every issue joins the `WorkmAIn Queue` project at creation (§1.3), and its position there is the sequence. The next open item on the board is what comes next — there is no priority label, no rank field, and no document that names what to work on.
>
> Read it with `python3 automation/queue.py`; `--next` returns the single next item, `--milestone` restricts to one milestone, `--json` is the machine-readable form. Never read the board through `gh project item-list`: it defaults to 30 items and truncates without saying so, and its output carries no issue state.
>
> Ordering is Ray's. Position is set in the Web UI, and nothing in this repository writes to the board.
>
> A parent issue holding open children is not itself workable — it is a container, and §1.3 requires an issue be independently verifiable on its own.
>
> **Preemption is expressed by position, and by nothing else.** Work that preempts the schedule is moved to the top of the board. The cycle-mechanics parent (#80) and its children hold that position today: they preempt all scheduled work, because until they close the cycle has no working mechanics to schedule against. **No general category of preempting work is defined.** Future preemption is decided case by case, by Ray, and takes effect as a move on the board — not as a label, a milestone, or a rule added here.

`CLAUDE.md` Project Status gains one line after the existing `gh issue list` block:

> That command reads issue *content*. Order is separate and lives in the `WorkmAIn Queue` project — see `docs/DEVELOPMENT_STANDARDS.md` §1.6.

The `gh issue list` block itself is unchanged: it is the content read, and §1.6 owns order. This satisfies C11's assertion rather than restating it — no rule ends up in both documents.

### 4.4 Step 5 — milestone descriptions

Ordering prose comes out, because board position now carries it (Ray, Q5). Five `gh api --method PATCH repos/lockdwn20/workmain/milestones/<n>` calls against `description`.

| Milestone | Change |
| --- | --- |
| 3 — Phase 14 | Remove the sentence *"Blocked until both Slack sprints close (Pre-Phase 14 Gate)."* Nothing else in the description changes |
| 1, 2, 4, 5 | Re-read at implementation time and strip any ordering or blocking sentence found. C12 records none today; the step is a verification, and if it finds none it says so and changes nothing |

The exit condition in each description stays — that is §1.3's requirement and not ordering.

### Authorization points

**This spec contains none.** Its GitHub write is a milestone description edit, which is not on §1.4's authorization set — that set covers *deleting* a GitHub object, not editing one, and a description edit is reversible from this spec's own before-text (§4.4). No DB migration, no merge to `main` inside these steps, no force-push, no service state change. `chore/*` carries no restart per §2.6.

The merge to `main` that closes this branch is an authorization point in its own right, as it is for every branch, and is not one of these steps.

## 5. Acceptance criteria

Mapped to #84's four acceptance criteria.

### AC1 — Spanner obtains the ranked queue without opening a browser

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | `python3 automation/queue.py` prints the open queue in board order | `pytest automation/queue_test.py::TestAC1` — fixture payload in a known position order, output row order asserted |
| AC1.2 | The order is the board's `POSITION` order, not any client-side sort | `grep -c 'orderBy: {field: POSITION' automation/queue.py` returns `1`, and no `sort`/`sorted` call touches the item sequence — `pytest …::TestAC1::test_order_is_not_resorted` feeds a payload in non-numeric order and asserts it is preserved |
| AC1.3 | Closed items are absent by default and present under `--all` | `pytest …::TestAC1::test_closed_filtered` — fixture with three closed items; default output omits them, `--all` marks them `closed` |
| AC1.4 | A truncated read fails loudly | `pytest …::TestAC1::test_truncation_fatal` — `hasNextPage: true` fixture, non-zero exit, message names the page size and `totalCount` |
| AC1.5 | `--next` returns one item and skips a parent holding open children | `pytest …::TestAC1::test_next_skips_open_parent` — fixture where rank 1 is a parent with `subIssuesSummary{total:6,completed:4}`; output is rank 2 |
| AC1.6 | The live read runs against real GitHub and agrees with the board | `python3 automation/queue.py --next` exits `0` and names the same issue as `gh api graphql` on `items(orderBy:{field:POSITION})` filtered to the first open non-parent |

### AC2 — Rank is expressible within a milestone as well as across milestones

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC2.1 | One read returns rank and milestone together, so both orders come from the same call | `grep -c 'milestone' automation/queue.py` ≥ 1 within the query text, and `pytest …::TestAC2::test_milestone_on_every_row` asserts each record carries `milestone` or `None` |
| AC2.2 | `--milestone` restricts to one milestone in board order | `pytest …::TestAC2::test_milestone_filter` — mixed-milestone fixture, filtered output is that milestone's items in board order |
| AC2.3 | Within-milestone rows keep their full-queue rank, so cross-milestone position is readable from a filtered read | `pytest …::TestAC2::test_ranks_are_global` — filtered output's ranks are non-contiguous and match the unfiltered ranks |

### AC3 — The Project carries order and nothing else

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC3.1 | Project #3 carries zero custom fields | Its field set minus an untouched empty project's field set is empty — see the fenced block below |
| AC3.2 | Nothing reads the built-in `Status` field | See the fenced block below |
| AC3.3 | Nothing in this repository writes to the board | See the fenced block below |
| AC3.4 | Neither document this spec edits holds a rank, a next item, or an ordered list of issues | See the fenced block below |

```bash
# AC3.1 — no custom field. Projects #1 and #2 are closed, empty scratch (recon F10) and were
# never edited, so either one's field set is GitHub's built-in default. Any project with no
# custom fields serves as the baseline; nothing here enumerates the built-ins.
python3 - <<'EOF'
import json, subprocess
def fields(n):
    out = subprocess.run(["gh", "project", "field-list", str(n), "--owner", "lockdwn20",
                          "--format", "json"], capture_output=True, text=True)
    return {f["name"] for f in json.loads(out.stdout)["fields"]}
print(sorted(fields(3) - fields(2)))      # []
EOF

# AC3.2 — no read of the project Status field
grep -nE '"?status"?' automation/queue.py            # zero hits
grep -n 'fieldValue' automation/queue.py             # zero hits

# AC3.3 — no board write
grep -nE 'gh project (item-|field-)?(add|create|edit|delete|archive)' automation/ docs/ CLAUDE.md   # zero hits
grep -nE 'mutation' automation/queue.py              # zero hits

# AC3.4 — no rank, next item, or ordered issue list in either document this spec edits
grep -cE '^[[:space:]]*[0-9]+\.[[:space:]]+#[0-9]+' docs/DEVELOPMENT_STANDARDS.md CLAUDE.md   # 0 and 0
```

### AC4 — A written preemption rule exists

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC4.1 | §1.6 exists and states that the next open item on the board is what comes next | `sed -n '/^### 1.6/,/^## 2\./p' docs/DEVELOPMENT_STANDARDS.md \| grep -c 'next open item'` returns `1` |
| AC4.2 | §1.6 states the preemption rule: #80 and its children preempt all scheduled work, no general category is defined, future preemption is case by case | `sed -n '/^### 1.6/,/^## 2\./p' docs/DEVELOPMENT_STANDARDS.md \| grep -c '#80'` returns `1`, and the same range contains `No general category` and `case by case` |
| AC4.3 | No milestone description carries ordering or blocking prose | See the fenced block below. It returns `1` today — Phase 14's *"Blocked until both Slack sprints close"* (C12) — so the AC is demonstrated live before step 5 and must return `0` after it |
| AC4.4 | §1.3 still names no sequencing mechanism, so #81's AC1.4 continues to pass | `sed -n '/^### 1.3/,/^### 1.4/p' docs/DEVELOPMENT_STANDARDS.md \| grep -cE 'Project #3\|WorkmAIn Queue\|item-list'` returns `0` |
| AC4.5 | No rule is stated in both `CLAUDE.md` and §1.6 | `CLAUDE.md`'s added line is a pointer only — `grep -c 'next open item' CLAUDE.md` returns `0` |
| AC4.6 | Every AC row above resolves to a command that was run | Every `pytest` node id in this section exists — `pytest automation/queue_test.py --collect-only -q` lists each one |

```bash
# AC4.3 — no ordering or blocking prose in any milestone description
gh api repos/lockdwn20/workmain/milestones --jq '.[].description' \
  | grep -ciE 'blocked until|precede|follows|after (phase|the) '
```

## 6. Test plan

- **Baseline before this work:** `pytest tests/` → **934 passed**; `pytest automation/` → **45 passed** (C16, both run on this branch at authoring time).
- **Expected after:** `pytest tests/` → **934 passed, unchanged** — no application code is touched. `pytest automation/` → **45 + 14 = 59 passed**.
- **New file:** `automation/queue_test.py`, organised `TestAC1` / `TestAC2` mirroring §5, following `issue_validator_test.py`'s structure.
- **Fixtures:** `automation/fixtures/queue_*.json` — saved GraphQL payloads, one per condition: a normal board, a truncated board (`hasNextPage: true`), a board whose head is a parent with open children, a mixed-milestone board, and a board containing a draft node with no `content.number`.
- **Seam:** `monkeypatch.setattr(queue, "gh_project_items", …)` replaces the only external read (C13). No test reaches GitHub. AC1.6 is the one live check and is run by hand, not by pytest.

## 7. Risks and rollback

| Risk | Blast radius | Control |
| --- | --- | --- |
| GitHub changes the ProjectV2 GraphQL surface | `queue.py` fails; the queue is unreadable until fixed | The failure is loud — a GraphQL error exits non-zero. The board itself is untouched, so nothing is lost; DR2 keeps the tool a reader |
| The board grows past `PAGE_SIZE` | The tail of the queue would be lost | DR4 makes this fatal rather than silent, which is the whole reason `item-list` is not used. AC1.4 pins it |
| Project #3 is renamed or renumbered | `queue.py` returns nothing | `OWNER` and `PROJECT_NUMBER` are named module constants with a comment; the fix is one line. No other file names the project |
| A future reader filters on `Status` because it is right there in the JSON | #84's third AC quietly stops holding | DR3 states it and AC3.2 greps for it. `queue.py` never requests the field, so it is not in its payload to be tempted by |
| Milestone description edits lose text | Five descriptions on GitHub, not in git | §4.4 changes one sentence in one description and re-reads the other four. Rollback is a `PATCH` restoring the before-text, quoted verbatim in §4.4 |
| Projects #1 and #2 are deleted, removing AC3.1's baseline | AC3.1 becomes uncheckable | Any ProjectV2 with no custom field serves — the check names no field, so a fresh throwaway project restores it. Deleting a GitHub object is an authorization point in any case (§1.4) |
| The `Source: implementation-checklist.md` line in all five milestone descriptions cites an archived document | None today — it is provenance, not a decision basis | Left alone deliberately (§1 out of scope). If it should go, it is its own issue; removing it here would be scope this issue did not ask for |

**Rollback:** steps 1–4 are ordinary commits on a `chore/*` branch and revert individually. Step 5 is five `PATCH` calls whose before-text is in §4.4. Nothing on the board is modified at any point, so there is no project state to restore.
