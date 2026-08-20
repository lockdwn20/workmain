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
| 20260814 | Ray | Recon Q5 — milestone sequence is migrated into the Project and **does not remain in prose** | Accepted, and **already true on the board**: the one sentence that carried it was removed on 20260820. Step 2 is the verification, AC4.3 the regression guard |
| 20260814 | Ray | Recon Q5a — a board holds issues, not milestones, so milestone order is expressed through the milestone carried on each ranked item | Accepted, and confirmed by F31/C2: one `item-list` call returns rank and milestone together |
| 20260819 | Ray | Placing issues in the Project is for the express purpose of ordering them. **The next issue on the list is what comes next.** `--format json` exists to make that simple to read | Accepted. DR1, and the whole of §4.1 |
| 20260819 | Spanner | A first draft specified `automation/queue.py` over GraphQL, on two claims about `gh project item-list` | **Withdrawn, both claims were wrong.** `--query "is:open"` filters on issue state and does not read `Status` (C3), and the `--limit` default is not a defect. Neither justifies code. This spec ships documentation only |
| 20260819 | Ray | We are still building the standards while planning against them; allowances are made so the standards can be written | Accepted. #84 is a documentation issue. Its deliverable is a new `docs/DEVELOPMENT_STANDARDS.md` §1.6, not a tool |
| 20260819 | Spanner | #84's third AC — *"no Status"* — could not be met as worded: `Status` is auto-populated and un-deletable (C6) | **Closed.** Ray updated the AC on the issue, 20260819, qualifying that clause and leaving the rest of his wording. AC3.1 and AC3.2 test the live text |
| 20260819 | Ray | An AC guarding against a custom field checks a thing that would never happen — the concept was never in consideration | Accepted. It leaked in from recon Q1's rejected `NUMBER`-field option. Removed from AC3, which now tests that the board holds position and nothing of its own |
| 20260819 | Spanner | The rule lands as a **new §1.6**, not inside §1.3 | #81 deliberately kept §1.3 mechanism-free and its AC1.4 greps §1.3 to prove it. Appending §1.6 renumbers nothing, so no citation breaks |

| 20260820 | Caliper | F1 — no milestone description carries ordering prose, so step 2 has no deliverable and AC4.2 can never demonstrate it | Accepted in full. **Attribution corrected:** C10 was verified live at authoring time and the sentence was present — milestone 3's `updated_at` is `2026-08-20T00:49:14Z`, after that read. The world changed, the claim was not carried from recon. §4.2 is now a verification, AC4.3 a regression guard reading `0` before and after, and recon F12 is superseded |
| 20260820 | Caliper | F2 — AC3.2's board-write grep hits `RECON_CYCLE_MECHANICS.md:96`, permanently, since recon artifacts are never rewritten | Accepted. Scoped to the surfaces the rule governs, with the expected count stated |
| 20260820 | Caliper | F3 — #84's fourth AC, the preemption rule, is tested by nothing | Accepted, and it was the headline AC. AC4.1 and AC4.2 now test the preemption clauses; the "§1.6 exists" check moves to AC1.4 where its substance belongs |
| 20260820 | Caliper | F4 — AC4.5 hard-codes `934` and `45`, so it fails when unrelated tests land on `main` | Accepted. The counts leave the document entirely; the check is that this branch changes no Python file and both suites pass. C12 loses its numbers for the same reason |
| 20260820 | Ray | `--limit` is not a defect and does not belong in the standard, an AC or a risk row. We work the next issue on the list; the default never bites | Accepted, and Caliper's F5 falls with it. Every mention of truncation is removed — C4, the §1.6 sentence, AC1.3, the risk row, and AC1.2's limit assertions |
| 20260820 | Caliper | F6 — AC3.1's comment claims labels are checked; the diff compares title and milestone only | Accepted. Labels are added to both sides rather than dropped from the comment — a board-local label is exactly what the AC exists to catch |
| 20260820 | Caliper | F7 — §1.6's *"no document that names what to work on"* restates the rule #81 left `CLAUDE.md` owning, and AC4.4 greps a phrase that could never appear there | Accepted. The clause is removed from §1.6, `CLAUDE.md` keeps the rule, and AC4.5 tests the boundary by proving it lives in exactly one file |
| 20260820 | Caliper | F8 — §7 attributes the Projects #1/#2 dependency to AC3.1, which never touches Project #2 | Accepted. Repointed to C5 |
| 20260820 | Caliper | #84's body says the token lacks `project` scope; it has it now | Not this spec's to fix — DR2 forbids board writes either way. The stale line is Ray's to strike from the issue |
| 20260820 | Caliper | §1.5's `Status:` vocabulary omits `Draft` and `Approved`, which every spec uses | **Fixed in step 1, not deferred** (Ray, 20260820). A one-word documentation fix in a file this branch already edits does not need its own issue, a risk row and a log entry. AC4.7 checks it |

---

## 1. Scope

**In scope:**

- `docs/DEVELOPMENT_STANDARDS.md` — a new **§1.6 Sequencing**, appended after §1.5. The board is the order, how to read it, and the preemption rule. **Every bare `§1.6` in this spec means that new section**, which does not exist until step 1 writes it; its full wording is quoted in §4.1.
- `CLAUDE.md` Project Status — a pointer to §1.6.
- `docs/DEVELOPMENT_STANDARDS.md` §1.5 — the `Status:` vocabulary, which omits `Draft` and `Approved` and so is wrong for every spec in the repository.
- The five milestone descriptions on GitHub — ordering prose removed, per Ray's Q5 answer.

**Out of scope:**

- **Any code.** No script, no test, no `automation/` file. The mechanism is a `gh` command that already works; writing a wrapper for it would be inventing a problem.
- **#85's session-open skills.** #85 reads the queue; it is not built here.
- **#89's `Issue: #NN` commit trailer.** Its own issue.
- **Board membership.** Every issue joins Project #3 at creation — #82's DR6, already shipped.
- **Any project write.** No field created, no item moved, no item archived. Ordering is Ray's, in the Web UI.
- **Removing the built-in `Status` field.** It cannot be removed (C6).
- **`workmain/**` and `tests/**`.** Untouched, which is what keeps this on `chore/*` per §2.2.

## 2. Verified current state

Verified 20260819 against live GitHub and the working tree.

| # | Claim | Evidence |
| --- | --- | --- |
| C1 | Project **#3 "WorkmAIn Queue"** is linked to `lockdwn20/workmain` and holds 61 items, 56 open | `gh project item-list 3 --owner lockdwn20 --format json --limit 200` |
| C2 | **One command returns the ranked open queue with milestone per item**, in board order, no browser: `gh project item-list 3 --owner lockdwn20 --format json --limit 200 --query "is:open"`. `milestone`, `labels` and `status` sit at the item top level, `number` and `title` under `.content` | Live run, 20260819 — head is `#80, #84, #85, #89, #29, #30 …`, matching the board after Ray's reorder. Recon F31 |
| C3 | **`--query "is:open"` filters on issue state, not on the `Status` field.** It returns 56 of 61 | Live run. `-status:Done` returns the same 56, but `is:open` is an issue-state filter and reads nothing from the project |
| C5 | **Nothing has been added to the board beyond what GitHub supplies.** Project #3's field set is identical to Project #2's — closed, empty, never edited — so the difference between them is empty | `gh project field-list` on #2 and #3. Recon F29 |
| C6 | `Status` is auto-populated by GitHub on every item added, **cannot be deleted**, and persists in `--format json` output even when hidden in the Web UI view. Closed items read `Done` | Recon F32, re-confirmed 20260819 |
| C7 | `docs/DEVELOPMENT_STANDARDS.md` states **no rule for what comes next**. `grep -nEi "next\|priority\|sequenc\|order\|queue\|rank\|preempt\|schedul"` returns eight hits, all unrelated — spec §4 step ordering, CLI group ordering, `rich.Table` columns, the `schedule` command group | `grep` over the file |
| C8 | §1.3 names no sequencing mechanism **by design**, and #81's AC1.4 greps §1.3 for `Project #3`, `WorkmAIn Queue` and `item-list` requiring zero hits | `docs/dev/specs/TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md:63,95,179` |
| C9 | `CLAUDE.md` Project Status asserts *"Item state, priority, and sequencing live in GitHub Issues — never in a document"*, supplies an **unranked** `gh issue list --json …` command, and points to §1.3 | `CLAUDE.md`, § Project Status |
| C10 | All five milestones carry `due_on: null`, and **none carries ordering or blocking prose today.** Phase 14's description held *"Blocked until both Slack sprints close (Pre-Phase 14 Gate)."* when this spec was authored on 20260819 and no longer does: milestone 3's `updated_at` is `2026-08-20T00:49:14Z`, the other four are unchanged since `2026-08-12`. **Recon F12 is superseded** | `gh api repos/lockdwn20/workmain/milestones` — descriptions and `updated_at`, re-read 20260820 |
| C11 | §2.2 makes `docs/**` chore-eligible and exempts `chore/*` from version bump, `CHANGELOG.md`, tag and Release | `docs/DEVELOPMENT_STANDARDS.md` §2.2 |
| C12 | Both suites pass on this branch, and this spec changes no Python file, so neither count is this branch's to move. **No count is written down** — a literal here fails the moment unrelated tests land on `main` | `pytest tests/`, `pytest automation/`, both run on this branch |

## 3. Design rules

- **DR1 — The board is the order.** Position in Project #3 is the sequence, and the next open item on the list is what comes next (Ray, 20260819). No document restates the order and no document names a next item.
- **DR2 — Rank is read, never written.** Ordering is Ray's, set in the Web UI. Nothing in this repository writes to the board.
- **DR3 — The mechanism is a documented command, not a tool.** `gh project item-list --format json` is the read, documented in the new §1.6 this spec writes (§4.1). That is the whole mechanism. If it later proves insufficient in use, a tool is a new issue with the shortfall named — not an anticipation of one.
- **DR4 — `Status` is ignored.** It is auto-populated and un-deletable (C6). Nothing reads it, nothing writes it, and no rule depends on it.
- **DR5 — Nothing is enumerated that can be derived.** No document holds a list of issues, a milestone order table, or a rank number.
- **DR6 — Anything this spec does not cover stops the step.** Role 3 escalation procedure, `CLAUDE.md` Role 3. Do not self-resolve.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | §1.6 Sequencing, the §1.5 `Status:` fix, and the `CLAUDE.md` pointer | `docs/DEVELOPMENT_STANDARDS.md`, `CLAUDE.md` |
| 2 | Milestone descriptions — ordering prose removed | GitHub milestones 1–5 (no file) |

### 4.1 Step 1 — §1.6 Sequencing

Appended after §1.5, so §2 onward is untouched and no citation moves. Wording:

> ### 1.6 Sequencing
>
> **The board is the order.** Every issue joins the `WorkmAIn Queue` project at creation (§1.3), and its position there is the sequence. The next open item on the list is what comes next. There is no priority label and no rank field.
>
> ```bash
> gh project item-list 3 --owner lockdwn20 --format json --limit 200 --query "is:open" \
>   | jq -r '.items[] | "#\(.content.number)\t\(.milestone.title // "—")\t\(.title)"'
> ```
>
> Items come back in board order. `milestone` and `labels` arrive on each item, so rank within a milestone and rank across milestones are the same single read — filter with `jq`, do not re-sort.
>
> Ordering is Ray's. Position is set in the Web UI, and nothing in this repository writes to the board. The project's `Status` field is auto-populated by GitHub and cannot be removed; it is ignored.
>
> **Preemption is expressed by position, and by nothing else.** Work that preempts the schedule is moved to the top of the board. The cycle-mechanics parent (#80) and its children hold that position today: they preempt all scheduled work, because until they close the cycle has no working mechanics to schedule against. **No general category of preempting work is defined.** Future preemption is decided case by case, by Ray, and takes effect as a move on the board — not as a label, a milestone, or a rule added here.

§1.5's `Status:` line becomes: *specs carry `Draft`, `Approved`, `Shipped` or `Superseded`; design and results artifacts carry `Active`, `Shipped` or `Superseded`.*

`CLAUDE.md` Project Status gains one line after the existing `gh issue list` block:

> That command reads issue *content*. Order is separate and lives in the `WorkmAIn Queue` project — see `docs/DEVELOPMENT_STANDARDS.md` §1.6.

The `gh issue list` block itself is unchanged: it is the content read, and §1.6 owns order. No rule ends up in both documents.

### 4.2 Step 2 — milestone descriptions

Ordering prose comes out of milestone descriptions, because board position carries it now (Ray, Q5). **The one sentence that carried it is already gone** (C10), so this step is a verification, not an edit.

Read all five descriptions and run AC4.3. If it returns `0`, record that in the results artifact and change nothing. If it returns anything else, strip the offending sentence with `gh api --method PATCH repos/lockdwn20/workmain/milestones/<n>` against `description`, quoting the before-text in the results artifact so the edit is reversible.

The exit condition in each description stays — that is §1.3's requirement and not ordering.

A step that changes no file still commits: the results artifact records the verification and its finding. A check that vanishes cannot be distinguished from a check that passed.

### Authorization points

**This spec contains none.** Its only GitHub write is a milestone description edit, which is not on §1.4's set — that set covers *deleting* a GitHub object, not editing one, and the edit is reversible from the before-text quoted in §4.2. No migration, no merge to `main` inside these steps, no force-push, no service state change. `chore/*` carries no restart per §2.6.

## 5. Acceptance criteria

Mapped to #84's four acceptance criteria as they read on the issue. Every check is a command run against live state; the longer ones are in the fenced block below the table.

### AC1 — Spanner obtains the ranked queue without opening a browser

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | §1.6 carries a single command that returns the ranked open queue with no browser | Run the block quoted in §4.1 verbatim; it exits `0` and prints the open queue |
| AC1.2 | That output is in the board's own `POSITION` order | Fenced block — the issue-number sequences are diffed |
| AC1.3 | §1.6 states that the next open item on the list is what comes next | The §1.6 range contains `next open item on the list is what comes next` |

### AC2 — Rank is expressible within a milestone as well as across milestones

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC2.1 | Milestone arrives on every item of the same read, so no second call is needed | The §4.1 command's output carries a milestone column for every row |
| AC2.2 | Rank within a milestone is a `jq` filter on that one read, and the ranks are the full-queue ranks | Fenced block — returns `#49, #50, #51, #52, #53, #67` in board order |

### AC3 — The Project carries order and nothing else

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC3.1 | Nothing is recorded on the board that is not already on the issue | Fenced block — for all 56 open items, the title, milestone and labels the read prints are diffed against the issue's own. Position is the only thing the board contributes |
| AC3.2 | `Status` is ignored: §1.6 names it once, to say so | The §1.6 range contains `it is ignored`, and `Status` appears in that range exactly once |
| AC3.3 | Nothing in this repository writes to the board | Fenced block, scoped to the surfaces the rule governs — `docs/DEVELOPMENT_STANDARDS.md`, `CLAUDE.md`, `automation/` — returns `0`. `docs/dev/design/` and `docs/dev/specs/` are excluded: recon and shipped specs are never rewritten, and `RECON_CYCLE_MECHANICS.md:96` records the board's own creation as a permanent historical fact |

### AC4 — A written preemption rule exists

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC4.1 | §1.6 states that #80 and its children preempt all scheduled work | The §1.6 range contains `#80` and `preempt all scheduled work` |
| AC4.2 | §1.6 states that no general category is defined and that future preemption is case by case | The §1.6 range contains `No general category` and `case by case` |
| AC4.3 | No milestone description carries ordering or blocking prose | Fenced block. It returns `0` **before and after** step 2 — the sentence it guarded was removed on the board on 20260820 (C10), so this is a regression guard, not a demonstration of an edit |
| AC4.4 | §1.3 still names no sequencing mechanism, so #81's AC1.4 continues to pass | Fenced block — returns `0` |
| AC4.5 | *"sequencing lives in GitHub Issues, never in a document"* is stated in exactly one file | Fenced block — `CLAUDE.md` only. §1.6 owns the mechanism; `CLAUDE.md` owns that rule, and neither restates the other |
| AC4.6 | This branch changes no Python file, and both suites pass | Fenced block. **No count is asserted** — a literal count fails the moment unrelated tests land on `main`, on a branch that touched no code |
| AC4.7 | §1.5's `Status:` vocabulary covers `Draft` and `Approved` | The §1.5 range contains `Draft` |

```bash
# AC1.2 — the documented command's order is the board's own POSITION order
diff <(gh project item-list 3 --owner lockdwn20 --format json --limit 200 --query "is:open" \
        | jq -r '.items[].content.number') \
     <(gh api graphql -f query='query{user(login:"lockdwn20"){projectV2(number:3){
         items(first:100,orderBy:{field:POSITION,direction:ASC}){nodes{content{
           ... on Issue{number state}}}}}}}' \
        | jq -r '.data.user.projectV2.items.nodes[]
                 | select(.content.state=="OPEN") | .content.number')

# AC2.2 — rank within one milestone, from the same single read
gh project item-list 3 --owner lockdwn20 --format json --limit 200 --query "is:open" \
  | jq -r '.items[] | select(.milestone.title == "Phase 18 — Packaging & Deployment")
           | "#\(.content.number)"'

# AC3.1 — the board holds position and nothing of its own. For every open item, the title,
# milestone and labels the read prints are the issue's own values, not board-local ones.
gh project item-list 3 --owner lockdwn20 --format json --limit 200 --query "is:open" \
  | jq -r '.items[] | [(.content.number|tostring), .title, (.milestone.title // "-"),
                       (.labels // [] | sort | join(","))] | @tsv' \
  | while IFS=$'\t' read -r n title ms labels; do
      board=$(printf '%s\t%s\t%s\t%s' "$n" "$title" "$ms" "$labels")
      issue=$(gh issue view "$n" --json title,milestone,labels \
                --jq "[\"$n\", .title, (.milestone.title // \"-\"),
                       ([.labels[].name] | sort | join(\",\"))] | @tsv")
      [ "$board" = "$issue" ] || echo "DIVERGES: #$n"
    done                                  # prints nothing

# AC3.3 — nothing writes the board, on the surfaces the rule governs
grep -rnE 'gh project (item-|field-)?(add|create|edit|delete|archive)' \
  docs/DEVELOPMENT_STANDARDS.md CLAUDE.md automation/ | wc -l          # 0

# AC4.3 — no ordering or blocking prose in any milestone description
gh api repos/lockdwn20/workmain/milestones --jq '.[].description' \
  | grep -ciE 'blocked until|precede|follows|after (phase|the) '       # 0

# AC4.4 — §1.3 still names no sequencing mechanism (#81's AC1.4)
sed -n '/^### 1.3/,/^### 1.4/p' docs/DEVELOPMENT_STANDARDS.md \
  | grep -cE 'Project #3|WorkmAIn Queue|item-list'                     # 0

# AC4.5 — the never-in-a-document rule lives in exactly one file
grep -rl 'never in a document' CLAUDE.md docs/DEVELOPMENT_STANDARDS.md # CLAUDE.md only

# AC4.6 — no Python changed, both suites pass. No count is asserted.
git diff --name-only main...HEAD | grep -cE '\.py$'                    # 0
pytest tests/ -q | tail -1
pytest automation/ -q | tail -1
```

## 6. Test plan

**No new tests.** This spec ships two documentation edits and five GitHub description reads. There is no code to cover, and inventing a test file to have one would be the same mistake as inventing the tool.

- Both suites are run at the end of step 2 as AC4.6, to prove the branch touched nothing it should not have.
- **Neither count is written down here.** The assertion is that this branch changes no Python file and both suites pass — a literal count would fail the moment unrelated work lands on `main` ahead of this merge, on a branch that touched no code (Caliper F4).

## 7. Risks and rollback

| Risk | Blast radius | Control |
| --- | --- | --- |
| Project #3 is renamed or renumbered | The §1.6 command returns nothing | The failure is immediate and visible. §1.6 is the only place the project number appears |
| A milestone description edit is needed after all and loses text | One description on GitHub, not in git | Step 2 edits nothing unless AC4.3 says otherwise, and quotes the before-text in the results artifact first |
| Projects #1 and #2 are deleted, removing C5's baseline | C5 becomes unverifiable; no AC depends on it | Any ProjectV2 that was never edited serves. Deleting a GitHub object is an authorization point in any case (§1.4) |

**Rollback:** step 1 is one commit on a `chore/*` branch and reverts. Step 2 changes nothing unless AC4.3 finds something, in which case rollback is a `PATCH` restoring the before-text the results artifact quoted. Nothing on the board is modified at any point.
