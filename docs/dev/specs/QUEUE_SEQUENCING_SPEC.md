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
| 20260814 | Ray | Recon Q1 — rank comes from drag `POSITION`, not a `NUMBER` field. No custom field is created | Accepted. DR1, DR2 |
| 20260814 | Ray | Recon Q5 — milestone sequence is migrated into the Project and **does not remain in prose** | Accepted. Step 2 strips the ordering prose; AC4.2 checks it |
| 20260814 | Ray | Recon Q5a — a board holds issues, not milestones, so milestone order is expressed through the milestone carried on each ranked item | Accepted, and confirmed by F31/C2: one `item-list` call returns rank and milestone together |
| 20260819 | Ray | Placing issues in the Project is for the express purpose of ordering them. **The next issue on the list is what comes next.** `--format json` exists to make that simple to read | Accepted. DR1, and the whole of §4.1 |
| 20260819 | Spanner | A first draft specified `automation/queue.py` over GraphQL, on two claims about `gh project item-list` | **Withdrawn, both claims were wrong.** `--query "is:open"` filters on issue state and does not read `Status` (C3); F30's truncation is handled by `--limit`, which F30 itself already says to pass (C4). Neither is a defect, so neither justifies code. This spec ships documentation only |
| 20260819 | Ray | We are still building the standards while planning against them; allowances are made so the standards can be written | Accepted. #84 is a documentation issue. Its deliverable is a new `docs/DEVELOPMENT_STANDARDS.md` §1.6, not a tool |
| 20260819 | Spanner | #84's third AC — *"no Status"* — could not be met as worded: `Status` is auto-populated and un-deletable (C6) | **Closed.** Ray updated the AC on the issue, 20260819, qualifying that clause and leaving the rest of his wording. AC3.1 and AC3.2 test the live text |
| 20260819 | Ray | An AC guarding against a custom field checks a thing that would never happen — the concept was never in consideration | Accepted. It leaked in from recon Q1's rejected `NUMBER`-field option. Removed from AC3, which now tests that the board holds position and nothing of its own |
| 20260819 | Spanner | The rule lands as a **new §1.6**, not inside §1.3 | #81 deliberately kept §1.3 mechanism-free and its AC1.4 greps §1.3 to prove it. Appending §1.6 renumbers nothing, so no citation breaks |

---

## 1. Scope

**In scope:**

- `docs/DEVELOPMENT_STANDARDS.md` — a new **§1.6 Sequencing**, appended after §1.5. The board is the order, how to read it, and the preemption rule. **Every bare `§1.6` in this spec means that new section**, which does not exist until step 1 writes it; its full wording is quoted in §4.1.
- `CLAUDE.md` Project Status — a pointer to §1.6.
- The five milestone descriptions on GitHub — ordering prose removed, per Ray's Q5 answer.

**Out of scope:**

- **Any code.** No script, no test, no `automation/` file. The mechanism is a `gh` command that already works; writing a wrapper for it would be inventing a problem.
- **#85's session-open skills.** #85 reads the queue; it is not built here.
- **#89's `Issue: #NN` commit trailer.** Its own issue.
- **Board membership.** Every issue joins Project #3 at creation — #82's DR6, already shipped.
- **Any project write.** No field created, no item moved, no item archived. Ordering is Ray's, in the Web UI.
- **Removing the built-in `Status` field.** It cannot be removed (C6).
- **Milestone description content beyond ordering prose.** The `Source: implementation-checklist.md` provenance line stays — see §7.
- **`workmain/**` and `tests/**`.** Untouched, which is what keeps this on `chore/*` per §2.2.

## 2. Verified current state

Verified 20260819 against live GitHub and the working tree.

| # | Claim | Evidence |
| --- | --- | --- |
| C1 | Project **#3 "WorkmAIn Queue"** is linked to `lockdwn20/workmain` and holds 61 items, 56 open | `gh project item-list 3 --owner lockdwn20 --format json --limit 200` |
| C2 | **One command returns the ranked open queue with milestone per item**, in board order, no browser: `gh project item-list 3 --owner lockdwn20 --format json --limit 200 --query "is:open"`. `milestone`, `labels` and `status` sit at the item top level, `number` and `title` under `.content` | Live run, 20260819 — head is `#80, #84, #85, #89, #29, #30 …`, matching the board after Ray's reorder. Recon F31 |
| C3 | **`--query "is:open"` filters on issue state, not on the `Status` field.** It returns 56 of 61 | Live run. `-status:Done` returns the same 56, but `is:open` is an issue-state filter and reads nothing from the project |
| C4 | `item-list` defaults to `--limit 30` and truncates silently. Recon F30 already states the handling: pass an explicit limit above the current issue count rather than a remembered number | `gh project item-list --help`; recon F30 |
| C5 | Project #3 carries **zero custom fields**. Its field set is identical to that of Project #2 — closed, empty, never edited — so every field on it is a GitHub built-in | `gh project field-list` on #2 and #3; the set difference is empty. Recon F29 |
| C6 | `Status` is auto-populated by GitHub on every item added, **cannot be deleted**, and persists in `--format json` output even when hidden in the Web UI view. Closed items read `Done` | Recon F32, re-confirmed 20260819 |
| C7 | `docs/DEVELOPMENT_STANDARDS.md` states **no rule for what comes next**. `grep -nEi "next\|priority\|sequenc\|order\|queue\|rank\|preempt\|schedul"` returns eight hits, all unrelated — spec §4 step ordering, CLI group ordering, `rich.Table` columns, the `schedule` command group | `grep` over the file |
| C8 | §1.3 names no sequencing mechanism **by design**, and #81's AC1.4 greps §1.3 for `Project #3`, `WorkmAIn Queue` and `item-list` requiring zero hits | `docs/dev/specs/TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md:63,95,179` |
| C9 | `CLAUDE.md` Project Status asserts *"Item state, priority, and sequencing live in GitHub Issues — never in a document"*, supplies an **unranked** `gh issue list --json …` command, and points to §1.3 | `CLAUDE.md`, § Project Status |
| C10 | All five milestones carry `due_on: null`. **Phase 14's description carries ordering prose verbatim:** *"Blocked until both Slack sprints close (Pre-Phase 14 Gate)."* Phases 15 and 18 state no relation to any other milestone | `gh api repos/lockdwn20/workmain/milestones`; recon F11, F12 |
| C11 | §2.2 makes `docs/**` chore-eligible and exempts `chore/*` from version bump, `CHANGELOG.md`, tag and Release | `docs/DEVELOPMENT_STANDARDS.md` §2.2 |
| C12 | Baselines at authoring time: `pytest tests/` → **934 passed**; `pytest automation/` → **45 passed**. This spec changes neither | Both run on this branch, 20260819 |

## 3. Design rules

- **DR1 — The board is the order.** Position in Project #3 is the sequence, and the next open item on the list is what comes next (Ray, 20260819). No document restates the order and no document names a next item.
- **DR2 — Rank is read, never written.** Ordering is Ray's, set in the Web UI. Nothing in this repository writes to the board.
- **DR3 — The mechanism is a documented command, not a tool.** `gh project item-list --format json` is the read. It is documented in the new §1.6 this spec writes (§4.1), with the `--limit` note beside it, and that is the whole mechanism. If it later proves insufficient in use, a tool is a new issue with the shortfall named — not an anticipation of one.
- **DR4 — `Status` is ignored.** It is auto-populated and un-deletable (C6). Nothing reads it, nothing writes it, and no rule depends on it.
- **DR5 — Nothing is enumerated that can be derived.** No document holds a list of issues, a milestone order table, or a rank number.
- **DR6 — Anything this spec does not cover stops the step.** Role 3 escalation procedure, `CLAUDE.md` Role 3. Do not self-resolve.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | §1.6 Sequencing, and the `CLAUDE.md` pointer | `docs/DEVELOPMENT_STANDARDS.md`, `CLAUDE.md` |
| 2 | Milestone descriptions — ordering prose removed | GitHub milestones 1–5 (no file) |

### 4.1 Step 1 — §1.6 Sequencing

Appended after §1.5, so §2 onward is untouched and no citation moves. Wording:

> ### 1.6 Sequencing
>
> **The board is the order.** Every issue joins the `WorkmAIn Queue` project at creation (§1.3), and its position there is the sequence. The next open item on the list is what comes next — there is no priority label, no rank field, and no document that names what to work on.
>
> ```bash
> gh project item-list 3 --owner lockdwn20 --format json --limit 200 --query "is:open" \
>   | jq -r '.items[] | "#\(.content.number)\t\(.milestone.title // "—")\t\(.title)"'
> ```
>
> Items come back in board order. `milestone` and `labels` arrive on each item, so rank within a milestone and rank across milestones are the same single read — filter with `jq`, do not re-sort. **Pass `--limit` above the current issue count**: it defaults to 30 and truncates without saying so.
>
> Ordering is Ray's. Position is set in the Web UI, and nothing in this repository writes to the board. The project's `Status` field is auto-populated by GitHub and cannot be removed; it is ignored.
>
> **Preemption is expressed by position, and by nothing else.** Work that preempts the schedule is moved to the top of the board. The cycle-mechanics parent (#80) and its children hold that position today: they preempt all scheduled work, because until they close the cycle has no working mechanics to schedule against. **No general category of preempting work is defined.** Future preemption is decided case by case, by Ray, and takes effect as a move on the board — not as a label, a milestone, or a rule added here.

`CLAUDE.md` Project Status gains one line after the existing `gh issue list` block:

> That command reads issue *content*. Order is separate and lives in the `WorkmAIn Queue` project — see `docs/DEVELOPMENT_STANDARDS.md` §1.6.

The `gh issue list` block itself is unchanged: it is the content read, and §1.6 owns order. No rule ends up in both documents.

### 4.2 Step 2 — milestone descriptions

Ordering prose comes out, because board position now carries it (Ray, Q5). `gh api --method PATCH repos/lockdwn20/workmain/milestones/<n>` against `description`.

| Milestone | Change |
| --- | --- |
| 3 — Phase 14 | Remove the sentence *"Blocked until both Slack sprints close (Pre-Phase 14 Gate)."* Nothing else changes |
| 1, 2, 4, 5 | Re-read and strip any ordering or blocking sentence found. C10 records none today; the step is a verification, and if it finds none it says so and changes nothing |

The exit condition in each description stays — that is §1.3's requirement and not ordering.

### Authorization points

**This spec contains none.** Its only GitHub write is a milestone description edit, which is not on §1.4's set — that set covers *deleting* a GitHub object, not editing one, and the edit is reversible from the before-text quoted in §4.2. No migration, no merge to `main` inside these steps, no force-push, no service state change. `chore/*` carries no restart per §2.6.

## 5. Acceptance criteria

Mapped to #84's four acceptance criteria. Every check is a command, run against live state.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | §1.6 carries a single command that returns the ranked open queue with no browser | Run the block quoted in §4.1 verbatim; it exits `0` and prints the open queue |
| AC1.2 | That output is in board order | Its issue-number sequence equals `gh api graphql` on `items(orderBy:{field:POSITION,direction:ASC})` filtered to open — see the fenced block below |
| AC1.3 | The `--limit` note is present, so the truncation trap is documented where the command is | The §1.6 range contains `truncates` |
| AC2.1 | Milestone arrives on every item of the same read, so no second call is needed | The §4.1 command's output carries a milestone column for every row |
| AC2.2 | Rank within a milestone is a `jq` filter on that one read | See the fenced block below — it returns `#49, #50, #51, #52, #53, #67` in board order |
| AC3.1 | Nothing is recorded on the board that is not already on the issue | See the fenced block below — every value the §1.6 read prints for an item, other than its position, equals the issue's own |
| AC3.2 | `Status` is ignored: no rule depends on it, and nothing in this repository writes to the board | See the fenced block below |
| AC4.1 | §1.6 exists and states that the next open item on the list is what comes next | The §1.6 range contains `next open item on the list` |
| AC4.2 | No milestone description carries ordering or blocking prose | See the fenced block below. It returns `1` today — Phase 14's *"Blocked until both Slack sprints close"* (C10) — and must return `0` after step 2 |
| AC4.3 | §1.3 still names no sequencing mechanism, so #81's AC1.4 continues to pass | See the fenced block below |
| AC4.4 | No rule is stated in both `CLAUDE.md` and §1.6 | `CLAUDE.md`'s added line is a pointer only — `grep -c 'next open item' CLAUDE.md` returns `0` |
| AC4.5 | Both suites are unchanged | `pytest tests/` → 934 passed; `pytest automation/` → 45 passed (C12) |

AC3.1 and AC3.2 are written against #84's third AC as it now reads on the issue:

> The Project carries order and nothing else — no dates, no notes, nothing recorded on the board that is not already on the issue. GitHub's Status field auto-populates and cannot be deleted; it is ignored.

```bash
# AC1.2 — the documented command's order is the board's own POSITION order
diff <(gh project item-list 3 --owner lockdwn20 --format json --limit 200 --query "is:open" \
        | jq -r '.items[].content.number') \
     <(gh api graphql -f query='query{user(login:"lockdwn20"){projectV2(number:3){
         items(first:100,orderBy:{field:POSITION,direction:ASC}){nodes{content{
           ... on Issue{number state}}}}}}}' \
        | jq -r '.data.user.projectV2.items.nodes[] | select(.content.state=="OPEN") | .content.number')

# AC2.2 — rank within one milestone, from the same single read
gh project item-list 3 --owner lockdwn20 --format json --limit 200 --query "is:open" \
  | jq -r '.items[] | select(.milestone.title == "Phase 18 — Packaging & Deployment")
           | "#\(.content.number)"'

# AC3.1 — the board holds position and nothing of its own. For every item, the title,
# milestone and labels the read prints are the issue's own values, not board-local ones.
gh project item-list 3 --owner lockdwn20 --format json --limit 200 --query "is:open" \
  | jq -r '.items[] | "\(.content.number)\t\(.title)\t\(.milestone.title // "-")"' \
  | while IFS=$'\t' read -r n title ms; do
      gh issue view "$n" --json title,milestone \
        --jq "\"$n\t\(.title)\t\(.milestone.title // \"-\")\"" \
        | diff - <(printf '%s\t%s\t%s\n' "$n" "$title" "$ms") > /dev/null || echo "DIVERGES: #$n"
    done                                  # prints nothing

# AC3.2 — Status is named once, to say it is ignored, and nothing writes the board
sed -n '/^### 1.6/,/^## 2\./p' docs/DEVELOPMENT_STANDARDS.md | grep -c 'it is ignored'   # 1
grep -rnE 'gh project (item-|field-)?(add|create|edit|delete|archive)' docs/ CLAUDE.md automation/

# AC4.2 — no ordering or blocking prose in any milestone description
gh api repos/lockdwn20/workmain/milestones --jq '.[].description' \
  | grep -ciE 'blocked until|precede|follows|after (phase|the) '

# AC4.3 — §1.3 still names no sequencing mechanism (#81's AC1.4)
sed -n '/^### 1.3/,/^### 1.4/p' docs/DEVELOPMENT_STANDARDS.md \
  | grep -cE 'Project #3|WorkmAIn Queue|item-list'
```

## 6. Test plan

**No new tests.** This spec ships two documentation edits and five GitHub description reads. There is no code to cover, and inventing a test file to have one would be the same mistake as inventing the tool.

- `pytest tests/` → **934 passed**, unchanged (C12).
- `pytest automation/` → **45 passed**, unchanged (C12).
- Both are run at the end of step 2 as AC4.5, to prove the branch touched nothing it should not have.

## 7. Risks and rollback

| Risk | Blast radius | Control |
| --- | --- | --- |
| The board grows past the `--limit` passed in §1.6's example | The tail of the queue is silently lost | §1.6 states the rule — pass a limit above the current issue count, not a remembered number. The example uses `200` against 61 items |
| Project #3 is renamed or renumbered | The §1.6 command returns nothing | The failure is immediate and visible. §1.6 is the only place the project number appears |
| Milestone description edits lose text | Five descriptions on GitHub, not in git | §4.2 changes one sentence in one description and re-reads the other four. Rollback is a `PATCH` restoring the before-text, quoted verbatim in §4.2 |
| Projects #1 and #2 are deleted, removing AC3.1's baseline | AC3.1 becomes uncheckable | Any ProjectV2 with no custom field serves; the check names no field. Deleting a GitHub object is an authorization point in any case (§1.4) |
| The `Source: implementation-checklist.md` line in all five milestone descriptions cites an archived document | None today — it is provenance, not a decision basis | Left alone deliberately (§1 out of scope). If it should go, it is its own issue |

**Rollback:** step 1 is one commit on a `chore/*` branch and reverts. Step 2 is a `PATCH` restoring the before-text in §4.2. Nothing on the board is modified at any point.
