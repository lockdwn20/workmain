# Spec Self-Consistency — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261029
**Branch:** `chore/issue-253-spec-self-consistency` (from `main`)
**Target release:** n/a — `chore/*`
**Originating item:** Issue #253
**Design study:** `../design/DESIGN_SPEC_SELF_CONSISTENCY.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261029 | Ray | Branch type `chore/*`, direct path. | Applied. |
| 20261029 | Ray | Design study Q1: the post-implementation review runs in a fresh Caliper session, and the run chooses its mode from whether a results artifact names the spec on its branch (Option A). The check is written into the Caliper skill. | Step 3, Step 4. |
| 20261029 | Ray | Design study Q2: the issue's AC1 misread the defect. A reference by ID is what the one-home rule wants. The ranges that went stale were of labels a spec invented, which no template defines and no rule governs. A spec numbers only the sets its template defines, and names a test by its pytest node ID. The revision rule applies to every numbered set; no rule singles out some of them. | Restated issue AC1 as AC1.1. Step 1b states the rule. The issue body needs the edit at close-out (`docs/standards/1-workflow.md` §1.2). |
| 20261029 | Ray | Design study Q3: Caliper reviews this spec, so the post-implementation review also runs (`docs/standards/1-workflow.md` §1.2). | Applied. |
| 20261029 | Spanner | The Review stage's done condition compares the spec text at the commit that recorded the `No findings.` row with the text at the commit that set `**Status:**` to `Approved`, and not with the text now. After approval the spec changes by rule: a departure ruled Keep amends it (`docs/standards/1-workflow.md` §1.1 Implementation review). Compared with the text now, every such amendment would show Review undone, and `/session-start Spanner`'s Next stage would name Review on a spec under implementation. | Superseded by the resolution of the 20261030 Caliper rows on Step 2a: the comparison moved to the Approval row, where it runs once, before the `**Status:**` edit. |
| 20261030 | Caliper | 2, 5: Step 2a's Review condition needs the spec's text at two commits, so `/session-start Spanner`, whose read 4 reads no git history, cannot evaluate it, and §1 Out of scope's claim about `references/spanner.md` fails. No artifact or field shows the condition, against §1.1's preamble. | Accepted. The Review row is shown by a field: the last `Caliper` row is a `No findings.` row naming the commit the pass read. The comparison of texts moves to the Approval row, as a check run before the `**Status:**` edit. Spanner's read 4 already reads the `Caliper` rows, so §1 Out of scope holds. Step 2a. |
| 20261030 | Caliper | 7, 3: "The commit that recorded that row" is not the text the pass read. Caliper reads the working tree, which can hold uncommitted edits, and the recording commit can carry other edits. Either way AC6.1 reads green on text no pass read. | Accepted. The spec review reads the spec as committed at `HEAD`, and its `No findings.` row names that commit (Steps 4d, 4e). The Approval row's check is `git diff <that commit> -- <spec path>`, against the working tree, and passes only when nothing but the lines recording the row changed. It catches uncommitted edits and edits riding the recording commit alike. Step 2a. |
| 20261030 | Caliper | 3: Step 2a leaves open which commit counts as the approval after a spec is set back to `Draft` and approved again, what "latest" is ordered by, and whether a `Caliper (post-implementation)` row is a `Caliper` row. | Accepted. The check runs at every edit that sets `Approved`, so no approval commit has to be identified. "Last" is by position in the Decision Log. A `Caliper` row is one whose Source is exactly `Caliper`. Step 2a. The check's timing is superseded by the resolution of the 20261030 Ray row on re-approval: it runs at the first approval only. |
| 20261030 | Caliper | 8, 3: Step 1b's rule says "the sets its template defines" and then lists them, and the two disagree: the design template letters its options, which the list omits; the rule does not say whether a sub-step label such as "Step 3.2" or "1a" is a step; and its subject is "A spec" while it states what a design study numbers. | Accepted. The rule reads "A spec or design study numbers or letters only what its template numbers or letters", with no list. A step's parts labelled under its number are the stated exception. Steps 1b and 5, AC1.1 and AC3.1. |
| 20261030 | Caliper | 2, 3: §2 says the Step 1b rule was run over its live set and the set is empty, but since the first review's resolution the rule governs design studies too, so the live set includes this spec and its design study. The study numbers subsections and a list its template does not, the rule does not say whether those count, and the F1 census cannot see either form. | Accepted. The rule is reworded with no template boundary (Ray, 20261030, below): an item with a name of its own is cited by that name and never given a label. Section numbers and list items are their own names, outside the rule. §2 records the run over this spec and its study. |
| 20261030 | Caliper | 8, 5: Step 1b makes the template the boundary and Step 5 makes crossing it an Anvil discrepancy, while `docs/standards/1-workflow.md` §1.5 and both templates call templates advisory. The spec does not search for statements that conflict with the change. | Accepted. The reworded rule does not depend on a template, so §1.5's statement stands. |
| 20261030 | Caliper | 3, 5: Step 5's check needs the spec template, which no read in `references/anvil.md` names. | Accepted. Under the reworded rule, Step 5's check reads only the spec. |
| 20261030 | Caliper | 3, 5: Step 4a does not say whether `<branch>` comes from the working tree or `HEAD`, and when the checked-out branch does not hold the spec, the run cannot find `<branch>` and nothing says what it does. | Accepted. Step 4a reads `<branch>` from the spec as committed at `HEAD`, the copy Step 4d reads. Where `HEAD` holds no file at the target path, the run reports the spec unreadable and reviews nothing. |
| 20261030 | Caliper | 8: Step 3b restates the mode condition in a weaker form than Step 4a. | Accepted. Step 3b cites `references/caliper.md` § Choosing the review. AC7.1 follows. |
| 20261030 | Caliper | 7: AC7.1's search for three phrases cannot see a statement of the session in other wording. | Accepted. AC7.1's evidence is a reading of every line that names the post-implementation review, which any statement of its session has to do. |
| 20261030 | Ray | The Step 1b rule is reworded with no template boundary: an item that has a name of its own is cited by that name, never given a label; a label that is an item's only name is its one home. | Steps 1b and 5, AC1.1 and AC3.1. AC1.1 remains a restatement of issue AC1. |
| 20261030 | Caliper | 8, 3: Step 3a's criterion 8 cites §1.2 for "how a reference to a set another section owns is written", the framing Q2 replaced; the rule criterion 8 asks about is 1a. 1a says "ID" and 1b says "label" for the same thing. | Accepted. Criterion 8 cites §1.2 for how a revision keeps every statement in step. 1a says "label". |
| 20261030 | Caliper | 7, 3: Approval checks the text only at the edit that sets `Approved`. A spec defect fixed after Anvil's session open, or a departure ruling that amends the spec, edits an `Approved` spec no pass read, so Review and AC6.1 read green on unread text. | Accepted (Ray, 20261030). The Approval row adds: an edit to the spec's text while `**Status:**` is `Approved`, other than the amendment a Keep ruling makes, sets it back to `Draft` in the same commit, and it is approved again only as the row states. A Keep amendment records code that exists, and the post-implementation review covers it. Step 2a, AC6.1. Re-approval is superseded by the 20261030 Ray row on re-approval: Ray approves it again. |
| 20261030 | Caliper | 2, 8: The design study still states the retired template rule in §4.1 item 6 and frames Q2 by the AC1 wording in §1. | Accepted. Both state the reworded rule. |
| 20261030 | Caliper | 3: AC3.1, §1 In scope and Step 5 cite `references/anvil.md` § Reads; the heading is `## Reads, in order`. | Accepted. All three cite § Reads, in order. |
| 20261030 | Caliper | 3, 5: Step 2a does not say whether a Decision Log row is an edit that returns an `Approved` spec to `Draft`. The rules require rows after approval (a departure's row, post-implementation rows with Ray's rulings). If they count, the spec is `Draft` once the results artifact exists, Step 4a then selects only the post-implementation review so no clean pass can re-approve it, and `/closeout` P4 refuses it. | Accepted. A Decision Log row is a record, not text a pass reviews: the Approval row exempts it with the Keep amendment. Step 2a, AC6.1. |
| 20261030 | Caliper | 5, 3: Step 4d moves only read 1 to `HEAD`. Reads 3 and 4 still read the working tree, so the commit the `No findings.` row names need not hold what they read, and a step quote matching only an uncommitted edit to a cited file passes. | Accepted. The spec review runs only on a clean working tree, which makes every read one of the commit at `HEAD`; otherwise it emits the paths and reviews nothing. Steps 4d, 4e. |
| 20261030 | Caliper | 3: The spec does not say how its own record meets the Review row it introduces: its passes run under the current reference, which emits `No findings.` without a commit. | Accepted. Superseded by the resolution of the 20261030 Caliper row on §7's second bullet. |
| 20261030 | Caliper | 3, 5: The Approval row's exemptions do not cover a change to the `**Status:**` field itself, so close-out's Approved → Shipped edit would have to set `Draft`, and `/closeout` P4 then refuses the spec. | Accepted. A change to the `**Status:**` field is exempt with a Decision Log row and a Keep amendment. Step 2a, AC6.1. |
| 20261030 | Caliper | 3, 7: Steps 4a and 4d add runs that review nothing, but § Emits still has a run with no finding and no amendment emit the clean-pass row, which the Review row counts as done. Step 4d's "emits each path" also conflicts with "No other commentary". | Accepted. Step 4e adds to § Emits: a run that reviews nothing emits no table and no row, only `Not reviewed:`, the reason and any unclean paths. Steps 4a and 4d cite § Emits. |
| 20261030 | Caliper | 8: Step 1b lets any reference to a labelled item name its label, while `docs/standards/1-workflow.md` §1.5 limits a label to the file that defines it. | Accepted. Step 1b's reference rule holds within the defining file and cites §1.5 for anywhere else. AC1.1 follows. |
| 20261030 | Caliper | 3, 5: Once a results artifact exists, an `Approved` spec sent back to `Draft` can never be approved again: the Approval row allows re-approval only through a fresh spec-review clean pass, which Step 4a no longer selects. `/closeout` P4 then refuses the spec. The Approval row's "the last `No findings.` row" also does not say its Source is `Caliper`. | Accepted. Resolved by the Ray row below. |
| 20261030 | Ray | Ray is the approving authority: a spec sent back to `Draft` is approved again by Ray. The text check is what shows the text first approved is the text a clean pass read. | The Approval row's check runs at the first approval only, with the commit the Review row's `No findings.` row names, and a spec returned to `Draft` is approved again by Ray. Step 2a, AC6.1. |
| 20261030 | Caliper | 3, 5: §7's second bullet records this spec's clean pass with a commit the Caliper session states, but the reference these passes run under emits only `No findings.` and no other commentary, and does not check the tree. | Accepted (Ray, 20261030). The rules this spec writes govern the specs reviewed after it merges. Its own passes and approval run under the rules before Steps 2 and 4, and its clean pass's row is `No findings.` with no commit. §7. Superseded by the resolution of the 20261030 Caliper row on the Review row's boundary. |
| 20261030 | Caliper | 8: The design study's §4.3 heading, "What a spec may number (Q2)", still frames Q2 as numbering. | Accepted. The heading reads "What a document may label (Q2)". |
| 20261030 | Caliper | 7, 3: The design no longer meets issue AC6 as worded ("the latest Caliper pass, made on the spec text that is approved"): the text condition moved to the Approval row, and a spec returned to `Draft` is approved again by Ray with no new pass. Only AC1.1 is marked restated, and only issue AC1 is named for the issue-body edit `docs/standards/1-workflow.md` §1.2 requires. | Accepted. AC6.1 is marked restated from issue AC6. The issue body needs the AC6 edit at close-out, with the AC1 edit (`docs/standards/1-workflow.md` §1.2). |
| 20261030 | Caliper | 3: Step 4b keeps "because the branch under review need not be the one checked out", but under Step 4a the checked-out branch must hold the spec, so before close-out it is `<branch>` or one cut from it. | Accepted. Step 4b's reason reads: the branch checked out need only hold the spec, and need not be `<branch>`. |
| 20261030 | Caliper | 3, 8: Step 5 defines the label check in read 5 but `references/anvil.md` § Emits lists no discrepancy it fits: a label that points at the right row resolves. Read 5's bullet covers only a step's citation, so a label given in §6 that no step cites is outside it, though AC3.1 covers it. | Accepted. Step 5 states the label check once, as a § Emits discrepancy over the whole spec, which read 1 reads end to end; read 5's bullet keeps the reference check only. §1 In scope, the step table and AC3.1 follow. |
| 20261030 | Caliper | 3: Steps 4d and 4e say every read is of the commit at `HEAD`, but read 2 (`gh issue view`) and any `gh` command read 4 resolves read GitHub's current state. | Accepted. Both say the spec and every repository file read are of that commit. |
| 20261030 | Caliper | 8: §1 Out of scope ("design study Q2", "Q1 Option A") and §2 ("the design study's F1") use the design study's IDs outside the Decision Log, against `docs/standards/1-workflow.md` §1.5. | Accepted. Each states the thing or cites the study's section. |
| 20261030 | Caliper | 3, 5: The Review row Step 2a writes has no boundary exempting this spec, and only §7 states one. From Step 2's commit, `/session-start Spanner` applies the new row to this spec's record, finds a last `Caliper` row with no commit, and names Review as Next stage on an `Approved` spec. | Accepted (Ray, 20261030). The record meets the row: Spanner commits and confirms a clean tree before each pass, so the commit a clean pass read is the one it was opened on, and its row is recorded as `No findings. Read at <commit>.` with it. The Approval row's check runs against it. §7. |
| 20261030 | Caliper | 8, 3: Step 1b and 1a say "label" where `docs/standards/1-workflow.md` §1.5 says "ID" for the same thing, and nothing ties the two terms. | Accepted (Ray, 20261030). The spec and design study say "ID", §1.5's term, throughout. |
| 20261030 | Caliper | 8, 3: §7's third bullet says a spec whose branch was deleted after close-out has no live review to run, but Step 4a would run a spec review of it where `HEAD` holds the spec. | Accepted (Ray, 20261030). Nobody reviews a shipped spec, and the spec states no rule for it: the sentence is removed. |

---

## 1. Scope

**In scope:**

- `docs/standards/1-workflow.md`: two authoring rules in §1.2 (Step 1), the Review and Approval rows of §1.1's done-condition table, and §1.1 Implementation review's session (Step 2).
- `.claude/skills/session-start/SKILL.md` § Role 2: criterion 8, and one session for each pass (Step 3).
- `.claude/skills/session-start/references/caliper.md`: how the run chooses which review it is, the post-implementation review's trigger, the amendment rule, the spec review reading the committed spec, and the commit its `No findings.` row names (Step 4).
- `.claude/skills/session-start/references/anvil.md` § Reads, in order and § Emits: a reference to another part of the same spec, and an item with a name of its own given an ID (Step 5).

**Out of scope:**

- The Implementation review stage's done condition. The issue does not name it.
- `docs/dev/specs/_TEMPLATE_SPEC.md`. Under the rule Step 1b states, no section of the template changes form.
- `.claude/skills/session-start/SKILL.md` Step 0's usage line. Caliper's target is still a spec path: the run chooses its review from the spec's branch (Step 4a).
- `.claude/skills/session-start/references/spanner.md`. Its Next stage applies whatever §1.1's table states, and its amendment sentence ("Ray approves the wording, and Spanner then writes it into the spec") still holds.
- Archived specs, which are a record (`docs/standards/1-workflow.md` §1.5).

## 2. Verified current state

On the direct path, each step quotes the text it replaces. The findings behind each change, with their evidence, are in the design study's §3. The quotes below were taken on 20261029 at `eca8083`.

The Step 1b rule refuses authored text, so it was run over the live set it will judge (`docs/standards/1-workflow.md` §1.2): this spec and its design study, the only live artifacts. Neither gives an ID to an item with a name of its own. Their IDs are design rules, steps and their parts, criteria, findings, questions and options, each its item's only name, and their tests, files and symbols are cited by node ID, path and symbol. The archive census of invented IDs is in the design study's §3.

## 3. Design rules

- **DR1 — Exact text.** Each edit is made as quoted. A wording or mechanical change within the meaning, scope and file set approved here is recorded in the results artifact's §4 as `within approved meaning`. A quote that does not match the file stops the step.
- **DR2 — One home.** Each rule this spec adds or changes is stated once. The session rule for Caliper passes is stated in `SKILL.md` § Role 2. The authoring rules are stated in `docs/standards/1-workflow.md` §1.2. The Review done condition is stated in §1.1's table. Every other file cites these.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | §1.2 states that a revision finds every statement of what it changes, and that an item with a name of its own is cited by that name and never given an ID | `docs/standards/1-workflow.md` |
| 2 | §1.1's Review row requires a clean pass naming the commit it read, its Approval row requires the approved text to be that commit's, and Implementation review cites Role 2 for its session | `docs/standards/1-workflow.md` |
| 3 | Role 2 carries criterion 8 and the rule that each pass runs in its own session | `.claude/skills/session-start/SKILL.md` |
| 4 | Caliper's reference chooses its review from the artifacts, its amendment rule matches the Review row, and its spec review reads the committed spec and names that commit | `.claude/skills/session-start/references/caliper.md` |
| 5 | Anvil's read 5 resolves a reference to another part of the same spec, and its § Emits reports an item with a name of its own given an ID | `.claude/skills/session-start/references/anvil.md` |
| 6 | Results artifact | `docs/dev/results/SPEC_SELF_CONSISTENCY_RESULTS.md` |

Close-out is not in this table. It is `/closeout`.

### Step 1 — authoring rules

**1a.** In `docs/standards/1-workflow.md` §1.2, replace:

```text
- Changes to an existing spec are surgical, not wholesale rewrites.
```

with:

```text
- Changes to an existing spec are surgical, not wholesale rewrites.
- **A revision finds every statement of what it changes.** A change to a spec, including the resolution of a review finding, searches the whole spec for every other statement of what it changes and every reference to an ID it adds, removes or alters, and changes each one. A change that edits one statement and leaves another standing hands the implementer a spec that disagrees with itself. §1.5 states the same duty across the document set for a rule change.
```

**1b.** Directly after the bullet 1a adds, insert:

```text
- **An item that has a name of its own is cited by that name, never given an ID.** A test is cited by its pytest node ID, a file by its path, a function or class by its symbol. An ID a document invents for such an item is a second name that nothing keeps in step with the first. An ID is the only name of an item that has no other, such as a design rule, a criterion or a finding, and it is that item's one home. Within the file that defines it, every reference to it names that ID or cites its section; anywhere else, §1.5 states how it is cited. The rule above keeps each reference true when a set changes.
```

### Step 2 — the Review stage and the post-implementation session

**2a.** In `docs/standards/1-workflow.md` §1.1, replace:

```text
| Review | The spec's Decision Log carries at least one `Caliper` row, and every `Caliper` row has a resolution. A clean pass is the `No findings.` row `/session-start Caliper` emits for one. On the direct path the stage is `n/a` where the spec's `**Status:**` is `Approved` and it carries no `Caliper` row. |
| Approval | The spec's `**Status:**` is `Approved`. |
```

with:

```text
| Review | The spec's last `Caliper` row, by its position in the Decision Log, is the `No findings.` row `/session-start Caliper` emits for a clean pass, naming the commit the pass read, and every other `Caliper` row has a resolution. A `Caliper` row is one whose Source is exactly `Caliper`. A Caliper pass is `.claude/skills/session-start/SKILL.md` § Role 2. On the direct path the stage is `n/a` where the spec's `**Status:**` is `Approved` and it carries no `Caliper` row. |
| Approval | The spec's `**Status:**` is `Approved`. Where the spec carries a `Caliper` row, `**Status:**` is first set to `Approved` only when `git diff <commit> -- <spec path>`, run before that edit with the commit the Review row's `No findings.` row names, shows no change but the lines that record that row: the text approved is the text the pass read. An edit to the spec while `**Status:**` is `Approved`, other than a Decision Log row, a change to the `**Status:**` field itself, and the amendment a Keep ruling makes (§1.1 Implementation review), sets `**Status:**` back to `Draft` in the same commit, and Ray approves it again. |
```

**2b.** In `docs/standards/1-workflow.md` §1.1, replace:

```text
on Ray's request in the Caliper session that reviewed the spec.
```

with:

```text
on Ray's request, in a Caliper session of its own (`.claude/skills/session-start/SKILL.md` § Role 2).
```

### Step 3 — Role 2

**3a.** In `.claude/skills/session-start/SKILL.md` § Role 2, replace:

```text
7. Which acceptance criteria could be satisfied by a change that does not achieve what the criterion is for? — how a criterion is worded so that difference is visible: `docs/standards/1-workflow.md` §1.2.
```

with:

```text
7. Which acceptance criteria could be satisfied by a change that does not achieve what the criterion is for? — how a criterion is worded so that difference is visible: `docs/standards/1-workflow.md` §1.2.
8. Where does this spec state the same thing in more than one place, and do the statements agree? — how a revision keeps every statement in step: `docs/standards/1-workflow.md` §1.2.
```

**3b.** Replace:

```text
After implementation, on Ray's request in the same session, reviews the delivered branch against the spec and its results artifact — `references/caliper.md` § Post-implementation review. When each review is required: `docs/standards/1-workflow.md` §1.2.
```

with:

```text
**Each pass runs in a session of its own**, opened with `/session-start Caliper <spec path>`, and a session runs one pass. A session that has run a pass carries the text it read, and a later pass in that session can read the spec as it was rather than as it is. Before implementation, each pass, the first or a later one, reviews the whole spec as it then stands against every criterion above, not only the findings of an earlier pass. After implementation, on Ray's request, the pass reviews the delivered branch against the spec and its results artifact. Which review a run is: `references/caliper.md` § Choosing the review. When each review is required: `docs/standards/1-workflow.md` §1.2.
```

### Step 4 — Caliper's reference

**4a.** In `.claude/skills/session-start/references/caliper.md`, replace:

```text
**Role:** `SKILL.md` § Role 2. **Target:** a spec path, required.
```

with:

```text
**Role:** `SKILL.md` § Role 2. **Target:** a spec path, required.

## Choosing the review

A run is one Caliper pass, in a session of its own (`SKILL.md` § Role 2). `<branch>` is the first backtick-quoted name in the `**Branch:**` field of the spec as committed at `HEAD` (`git show HEAD:<target path>`). Where `HEAD` holds no file at the target path, the run reports the spec unreadable (`SKILL.md` § Rules every run holds) and reviews nothing (§ Emits): it is run with a branch checked out that holds the spec. When `git rev-parse --verify --quiet <branch>` exits 0 and § Post-implementation review's read 2 finds a results artifact on `<branch>`, the run is § Post-implementation review. Otherwise it is the spec review: § Reads, in order and § Emits.
```

**4b.** Replace:

```text
Run when Ray requests it in this session after the results artifact exists — `docs/standards/1-workflow.md` §1.1 Implementation review. `<branch>` is the first backtick-quoted name in the spec's `**Branch:**` field. Every file is read from it with `git show <branch>:<path>`, never from the working tree, because the branch under review need not be the one checked out.
```

with:

```text
Run when § Choosing the review selects it — `docs/standards/1-workflow.md` §1.1 Implementation review. Every file is read from `<branch>` with `git show <branch>:<path>`, never from the working tree, because the branch checked out need only hold the spec (§ Choosing the review) and need not be `<branch>`.
```

**4c.** Replace:

```text
It is an amendment row (§ Emits) with suggested wording, and it does not hold the spec. Ray approves the wording, and Spanner then writes it into the spec.
```

with:

```text
It is an amendment row (§ Emits) with suggested wording, and not a finding against the spec. Ray approves the wording, and Spanner then writes it into the spec, where the next pass reviews it like any other text (`docs/standards/1-workflow.md` §1.1, the Review row).
```

**4d.** Replace:

```text
1. The spec at the target path, end to end.
```

with:

```text
1. The spec at the target path, end to end, read with a clean working tree. Where `git status --porcelain` prints anything, the run reviews nothing (§ Emits). A clean tree makes this read, and every read of a repository file below, one of the commit at `HEAD`.
```

**4e.** Replace:

```text
With no finding and no amendment, the run emits the same table with one row, `| <YYYYMMDD> | Caliper | No findings. | n/a |`, and nothing else.
```

with:

```text
With no finding and no amendment, the run emits the same table with one row, `| <YYYYMMDD> | Caliper | No findings. Read at <commit>. | n/a |`, where `<commit>` is `git rev-parse --short HEAD`, the commit the spec and every repository file were read at, and nothing else. A run that reviews nothing, because `HEAD` holds no spec at the target path (§ Choosing the review) or the working tree is not clean (read 1), emits no table and no row to record. It emits one line, `Not reviewed:` and the reason, followed by each path `git status --porcelain` lists where the tree is not clean.
```

### Step 5 — Anvil's reference

In `.claude/skills/session-start/references/anvil.md` § Reads, in order, directly after:

```text
   - **Section** — the file named has the heading, and the section says what the spec says it says.
```

insert:

```text
   - **Reference to another part of the spec** — a step's citation of another section of the same spec, or of an item that section gives an ID: the section exists, and each item cited is there and is what the step says it is.
```

In § Emits, directly after:

```text
  - a reference that does not resolve, or resolves to something other than what the spec says is there
```

insert:

```text
  - an item with a name of its own given an ID anywhere in the spec, such as a test named other than by its node ID (`docs/standards/1-workflow.md` §1.2)
```

### Step 6 — results

`docs/dev/results/SPEC_SELF_CONSISTENCY_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`, with `**Spec:** `../specs/SPEC_SELF_CONSISTENCY_SPEC.md``. Every criterion below whose check names Ray is recorded `Not met`, with `Awaiting Ray` as its evidence (`docs/standards/1-workflow.md` §1.2).

### Authorization points

None. The merge to `main` is `/closeout`'s, which stops at it.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | An item that has a name of its own, such as a test, a file or a symbol, is cited by that name and never given an ID, and a reference to an item's ID within the file that defines it names that ID or cites its section, as stated in the standards' spec authoring rules. Restated from issue AC1 (Decision Log). | Stated reading by Ray of `docs/standards/1-workflow.md` §1.2, for the rule |
| AC2.1 | A revision of a spec, including the resolution of a review finding, finds every statement in the spec of what it changes, and changes each one, as stated in the standards' spec authoring rules | Stated reading by Ray of `docs/standards/1-workflow.md` §1.2, for the rule |
| AC3.1 | Anvil's session-open run resolves a step's reference to another part of the same spec only when that part holds what the step says, and reports any other result, and any item with a name of its own given an ID, as a discrepancy | Stated reading by Ray of `.claude/skills/session-start/references/anvil.md` § Reads, in order, read 5, and § Emits |
| AC4.1 | Every pre-implementation Caliper pass, the first or a later one, is a full review of the spec as it then stands, in a session of its own opened with `/session-start Caliper`, and not a check of earlier findings only | Stated reading by Ray of `.claude/skills/session-start/SKILL.md` § Role 2 and `references/caliper.md` § Choosing the review |
| AC5.1 | Caliper's review criteria ask where the spec states the same thing in more than one place, and whether the statements agree | Stated reading by Ray of `SKILL.md` § Role 2's criteria list |
| AC6.1 | The Review stage is done only when the latest Caliper pass reports no findings and names the commit it read, a spec is first set `Approved` only when its text is that commit's apart from the recording of that row, an edit to an `Approved` spec other than a Decision Log row, a `**Status:**` change or a Keep amendment returns it to `Draft` until Ray approves it again, and an amendment's wording written into the spec is reviewed by a later pass. Restated from issue AC6 (Decision Log). | Stated reading by Ray of the Review and Approval rows in `docs/standards/1-workflow.md` §1.1's done-condition table, and `references/caliper.md` § Reads, in order, § Emits and § Working rules |
| AC7.1 | Which Caliper session runs the post-implementation review is stated once, in `SKILL.md` § Role 2, as a session of its own whose run chooses its review as `references/caliper.md` § Choosing the review states, and §1.1 Implementation review and `references/caliper.md` cite it | Stated reading by Ray of `docs/standards/1-workflow.md` §1.1 Implementation review, `SKILL.md` § Role 2, and `references/caliper.md` § Choosing the review and § Post-implementation review; and a reading by Ray of every line `git grep -n -i -e 'post-implementation' -e 'implementation review' -e 'after implementation' -e 'delivered branch' -- CLAUDE.md docs/standards .claude 'docs/dev/*/_TEMPLATE_*.md'` prints, for any other statement of which session runs the review. A statement of it has to name the review, so the search sees every form; at `7c95654` it prints 15 lines |

## 6. Test plan

No file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes, so no suite count is recorded here. Close-out runs the suites.

## 7. Risks and rollback

- **A Caliper session opened before the merge** loads the old rules from whichever branch is checked out. This spec's own reviews run on this branch, so the post-implementation review runs under the new § Choosing the review.
- **This spec's own Review record.** Its pre-implementation passes run under `references/caliper.md` as it stands before Step 4, which emits `No findings.` without a commit. Spanner commits and confirms a clean working tree before each pass, and the pass is opened on that commit. Its clean pass's row is recorded as `No findings. Read at <commit>.`, with that commit, so the record meets the Review row Step 2a writes, and the Approval row's check runs against that commit before `**Status:**` is set to `Approved`.
- **The mode check selects the wrong review.** It reads the branch the spec names, not the working tree.
- **Rollback:** each step is one commit. Reverting them in reverse order restores the previous text. Before close-out, `git branch -D` the unmerged branch.
