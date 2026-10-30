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
| 20261030 | Caliper | 3: Step 2a leaves open which commit counts as the approval after a spec is set back to `Draft` and approved again, what "latest" is ordered by, and whether a `Caliper (post-implementation)` row is a `Caliper` row. | Accepted. The check runs at every edit that sets `Approved`, so no approval commit has to be identified. "Last" is by position in the Decision Log. A `Caliper` row is one whose Source is exactly `Caliper`. Step 2a. |
| 20261030 | Caliper | 8, 3: Step 1b's rule says "the sets its template defines" and then lists them, and the two disagree: the design template letters its options, which the list omits; the rule does not say whether a sub-step label such as "Step 3.2" or "1a" is a step; and its subject is "A spec" while it states what a design study numbers. | Accepted. The rule reads "A spec or design study numbers or letters only what its template numbers or letters", with no list. A step's parts labelled under its number are the stated exception. Steps 1b and 5, AC1.1 and AC3.1. |

---

## 1. Scope

**In scope:**

- `docs/standards/1-workflow.md`: two authoring rules in §1.2 (Step 1), the Review and Approval rows of §1.1's done-condition table, and §1.1 Implementation review's session (Step 2).
- `.claude/skills/session-start/SKILL.md` § Role 2: criterion 8, and one session for each pass (Step 3).
- `.claude/skills/session-start/references/caliper.md`: how the run chooses which review it is, the post-implementation review's trigger, the amendment rule, the spec review reading the committed spec, and the commit its `No findings.` row names (Step 4).
- `.claude/skills/session-start/references/anvil.md` § Reads: a reference to another part of the same spec (Step 5).

**Out of scope:**

- The Implementation review stage's done condition. The issue does not name it.
- `docs/dev/specs/_TEMPLATE_SPEC.md`. With design study Q2 answered, no section of the template changes form.
- `.claude/skills/session-start/SKILL.md` Step 0's usage line. Under Q1 Option A, Caliper's target is still a spec path.
- `.claude/skills/session-start/references/spanner.md`. Its Next stage applies whatever §1.1's table states, and its amendment sentence ("Ray approves the wording, and Spanner then writes it into the spec") still holds.
- Archived specs, which are a record (`docs/standards/1-workflow.md` §1.5).

## 2. Verified current state

On the direct path, each step quotes the text it replaces. The findings behind each change, with their evidence, are in the design study's §3. The quotes below were taken on 20261029 at `eca8083`.

The Step 1 rule refuses authored text, so it was run over the live set it will judge (`docs/standards/1-workflow.md` §1.2). `docs/dev/specs/` holds no spec but its template, so the live set is empty. The archive census is the design study's F1.

## 3. Design rules

- **DR1 — Exact text.** Each edit is made as quoted. A wording or mechanical change within the meaning, scope and file set approved here is recorded in the results artifact's §4 as `within approved meaning`. A quote that does not match the file stops the step.
- **DR2 — One home.** Each rule this spec adds or changes is stated once. The session rule for Caliper passes is stated in `SKILL.md` § Role 2. The authoring rules are stated in `docs/standards/1-workflow.md` §1.2. The Review done condition is stated in §1.1's table. Every other file cites these.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | §1.2 states that a revision finds every statement of what it changes, and that a spec or design study numbers or letters only what its template does and names a test by its node ID | `docs/standards/1-workflow.md` |
| 2 | §1.1's Review row requires a clean pass naming the commit it read, its Approval row requires the approved text to be that commit's, and Implementation review cites Role 2 for its session | `docs/standards/1-workflow.md` |
| 3 | Role 2 carries criterion 8 and the rule that each pass runs in its own session | `.claude/skills/session-start/SKILL.md` |
| 4 | Caliper's reference chooses its review from the artifacts, its amendment rule matches the Review row, and its spec review reads the committed spec and names that commit | `.claude/skills/session-start/references/caliper.md` |
| 5 | Anvil's read 5 resolves a reference to another part of the same spec | `.claude/skills/session-start/references/anvil.md` |
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
- **A revision finds every statement of what it changes.** A change to a spec, including the resolution of a review finding, searches the whole spec for every other statement of what it changes and every reference to an ID it adds, retires or alters, and changes each one. A change that edits one statement and leaves another standing hands the implementer a spec that disagrees with itself. §1.5 states the same duty across the document set for a rule change.
```

**1b.** Directly after the bullet 1a adds, insert:

```text
- **A spec or design study numbers or letters only what its template numbers or letters.** A step may be divided into parts labelled under its own number (`2a`, `3.2`). A test is named by its pytest node ID, its name in the file that is its one home, and never by a label the document invents. An invented label is a second name for the test that no template defines and no rule keeps in step with the test or with the table that lists it. A reference to a numbered or lettered item, from any section, names it by its label or cites its section, and the rule above keeps each reference true when the set changes.
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
| Approval | The spec's `**Status:**` is `Approved`. Where the spec carries a `Caliper` row, `**Status:**` is set to `Approved` only when `git diff <commit> -- <spec path>`, run before that edit with the commit the last `No findings.` row names, shows no change but the lines that record that row: the text approved is the text the pass read. |
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
8. Where does this spec state the same thing in more than one place, and do the statements agree? — how a reference to a set another section owns is written: `docs/standards/1-workflow.md` §1.2.
```

**3b.** Replace:

```text
After implementation, on Ray's request in the same session, reviews the delivered branch against the spec and its results artifact — `references/caliper.md` § Post-implementation review. When each review is required: `docs/standards/1-workflow.md` §1.2.
```

with:

```text
**Each pass runs in a session of its own**, opened with `/session-start Caliper <spec path>`, and a session runs one pass. A session that has run a pass carries the text it read, and a later pass in that session can read the spec as it was rather than as it is. Before implementation, each pass, the first or a later one, reviews the whole spec as it then stands against every criterion above, not only the findings of an earlier pass. After implementation, on Ray's request, the pass reviews the delivered branch against the spec and its results artifact. The run chooses which review it is from whether the results artifact exists — `references/caliper.md` § Choosing the review. When each review is required: `docs/standards/1-workflow.md` §1.2.
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

A run is one Caliper pass, in a session of its own (`SKILL.md` § Role 2). `<branch>` is the first backtick-quoted name in the `**Branch:**` field of the spec at the target path. When `git rev-parse --verify --quiet <branch>` exits 0 and § Post-implementation review's read 2 finds a results artifact on `<branch>`, the run is § Post-implementation review. Otherwise it is the spec review: § Reads, in order and § Emits.
```

**4b.** Replace:

```text
Run when Ray requests it in this session after the results artifact exists — `docs/standards/1-workflow.md` §1.1 Implementation review. `<branch>` is the first backtick-quoted name in the spec's `**Branch:**` field. Every file is read from it with `git show <branch>:<path>`, never from the working tree, because the branch under review need not be the one checked out.
```

with:

```text
Run when § Choosing the review selects it — `docs/standards/1-workflow.md` §1.1 Implementation review. Every file is read from `<branch>` with `git show <branch>:<path>`, never from the working tree, because the branch under review need not be the one checked out.
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
1. The spec at the target path, end to end, as committed: `git show HEAD:<target path>`. Edits in the working tree are not read.
```

**4e.** Replace:

```text
With no finding and no amendment, the run emits the same table with one row, `| <YYYYMMDD> | Caliper | No findings. | n/a |`, and nothing else.
```

with:

```text
With no finding and no amendment, the run emits the same table with one row, `| <YYYYMMDD> | Caliper | No findings. Read at <commit>. | n/a |`, where `<commit>` is `git rev-parse --short HEAD`, the commit read 1 read, and nothing else.
```

### Step 5 — Anvil's reference

In `.claude/skills/session-start/references/anvil.md` § Reads, directly after:

```text
   - **Section** — the file named has the heading, and the section says what the spec says it says.
```

insert:

```text
   - **Reference to another part of the spec** — a step's citation of another section of the same spec, or of an item that section numbers or letters: the section exists, and each item cited is there and is what the step says it is. A label the spec gives outside what its template numbers or letters, other than a part of a step labelled under its number, is a discrepancy (`docs/standards/1-workflow.md` §1.2).
```

### Step 6 — results

`docs/dev/results/SPEC_SELF_CONSISTENCY_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`, with `**Spec:** `../specs/SPEC_SELF_CONSISTENCY_SPEC.md``. Every criterion below whose check names Ray is recorded `Not met`, with `Awaiting Ray` as its evidence (`docs/standards/1-workflow.md` §1.2).

### Authorization points

None. The merge to `main` is `/closeout`'s, which stops at it.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A spec or design study numbers or letters only what its template does, with a step's parts labelled under its number as the stated exception, and names a test by its pytest node ID, and a reference from one section to another names what it cites by its label or by the section, as stated in the standards' spec authoring rules. Restated from issue AC1 (Decision Log). | Stated reading by Ray of `docs/standards/1-workflow.md` §1.2, for the rule |
| AC2.1 | A revision of a spec, including the resolution of a review finding, finds every statement in the spec of what it changes, and changes each one, as stated in the standards' spec authoring rules | Stated reading by Ray of `docs/standards/1-workflow.md` §1.2, for the rule |
| AC3.1 | Anvil's session-open run resolves a step's reference to another part of the same spec only when that part holds what the step says, and reports any other result, and any label given outside what its template numbers or letters, as a discrepancy | Stated reading by Ray of `.claude/skills/session-start/references/anvil.md` § Reads, read 5 |
| AC4.1 | Every pre-implementation Caliper pass, the first or a later one, is a full review of the spec as it then stands, in a session of its own opened with `/session-start Caliper`, and not a check of earlier findings only | Stated reading by Ray of `.claude/skills/session-start/SKILL.md` § Role 2 and `references/caliper.md` § Choosing the review |
| AC5.1 | Caliper's review criteria ask where the spec states the same thing in more than one place, and whether the statements agree | Stated reading by Ray of `SKILL.md` § Role 2's criteria list |
| AC6.1 | The Review stage is done only when the latest Caliper pass reports no findings and names the commit it read, a spec is set `Approved` only when its text is that commit's apart from the recording of that row, and an amendment's wording written into the spec is reviewed by a later pass | Stated reading by Ray of the Review and Approval rows in `docs/standards/1-workflow.md` §1.1's done-condition table, and `references/caliper.md` § Reads, in order, § Emits and § Working rules |
| AC7.1 | Which Caliper session runs the post-implementation review is stated once, in `SKILL.md` § Role 2, as a session of its own whose run chooses the review from the artifacts, and §1.1 Implementation review and `references/caliper.md` cite it | Stated reading by Ray of `docs/standards/1-workflow.md` §1.1 Implementation review, `SKILL.md` § Role 2, and `references/caliper.md` § Choosing the review and § Post-implementation review; and `git grep -n -e 'same session' -e 'in this session' -e 'session that reviewed' -- CLAUDE.md docs/standards .claude 'docs/dev/*/_TEMPLATE_*.md'` printing no line about a Caliper review (at `eca8083` it prints three: `SKILL.md:86`, `references/caliper.md:27`, `docs/standards/1-workflow.md:24`) |

## 6. Test plan

No file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes, so no suite count is recorded here. Close-out runs the suites.

## 7. Risks and rollback

- **A Caliper session opened before the merge** loads the old rules from whichever branch is checked out. This spec's own reviews run on this branch, so the post-implementation review runs under the new § Choosing the review.
- **The mode check selects the wrong review.** It reads the branch the spec names, not the working tree. A spec whose branch was deleted after close-out has no live review to run.
- **Rollback:** each step is one commit. Reverting them in reverse order restores the previous text. Before close-out, `git branch -D` the unmerged branch.
