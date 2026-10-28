# Post-Implementation Review — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261027
**Branch:** `chore/issue-243-post-implementation-review` (from `main`)
**Target release:** n/a — `chore/*`
**Originating item:** Issue #243
**Design study:** `../design/DESIGN_POST_IMPLEMENTATION_REVIEW.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261027 | Ray | Branch type `chore/*`, direct path. | Applied. |
| 20261027 | Ray | The post-implementation review is a request made in the live Caliper session, as a re-review is. It is not a new `/session-start` target (design study §4.1). | Step 2. AC1.1 and AC3.1 restated. |
| 20261027 | Ray | Design study Q1: B. Ray rules on each unstopped departure as revert, or keep with the spec amended so the change traces. Results §4 records the skipped stop either way. | Step 1, §1.1 Implementation review. Step 3 cites it from the results template. |
| 20261027 | Ray | Design study Q2: on the direct path the post-implementation review runs exactly when the pre-implementation review ran, and Ray decides at the start. | Step 1, §1.2 and §1.1 direct path. |
| 20261027 | Spanner | Issue AC1 ("`/session-start Caliper` accepts a post-implementation target") and AC3 (a change planted "on a test branch") assume a new target, which Ray's direction replaces. Restated as AC1.1 and AC3.1 under `docs/DEVELOPMENT_STANDARDS.md` §1.2. | The issue body needs both edits, made at close-out. |
| 20261027 | Spanner | The diff base is `git merge-base <parent> <branch>`, where the parent is the one §2.2 names for the branch type, not the issue's `git merge-base main <branch>`. Against `main`, a `feature/*` branch cut while `dev` is a feature ahead would carry that feature as untraced changes (design study F10). | Step 2, read 4. |
| 20261027 | Spanner | Outside scope: `/closeout`'s `P9` takes its base as `git merge-base main <branch>` and has the same exposure for `feature/*` (`.claude/skills/closeout/SKILL.md` § When this runs, "Base ref"). An issue for it needs: the defect (a `feature/*` branch cut while `dev` is ahead of `main` diffs against the wrong base), and a criterion that `/closeout` takes the base from the branch's §2.2 parent. `gh issue list --state open` searched for `merge-base`, `Base ref` and `P9` finds no open issue covering it. | **Withdrawn** — Spanner, 20261028. For `feature/*`, `P9` is the only `/closeout` check that reads that base (`P11` is `n/a` on `feature/*`). An over-wide diff can only make `P9` run `pytest automation/` when it could have been skipped. It can never skip a run that was needed, so there is no defect and no issue. |
| 20261027 | Spanner | Post-implementation rows carry Source `Caliper (post-implementation)` and check ids `I1`–`I5`. Reusing `Caliper` would make the Review stage read as not done whenever a post-implementation finding is open, and would leave nothing to show the new stage done (design study F4). | Steps 1, 2 and 3. |
| 20261027 | Spanner | No `/closeout` check for the new stage. Issue #240 keeps `P7` reserved, and `/closeout` does not gate the pre-implementation review either. | No step. |
| 20261027 | Spanner | Issue AC4 runs on the first full-path cycle after this closes, so it cannot be `Met` before this close-out's `P6`. Issue #240's second criterion is the same run: one full-path cycle after all of #240's children close, read with Caliper's findings table. | AC4.1 is `Carried` to #240. |
| 20261027 | Spanner | AC3.1 runs the review on this branch, which on the direct path needs a pre-implementation Caliper review of this spec (Q2). That Caliper session loads `references/caliper.md` at open, before Step 2 writes the new section. | AC3.1's request names the section, so the session reads it from the branch. Ray decides whether Caliper reviews this spec. |
| 20261028 | Caliper | 5: The direct-path diagram is left as `SPEC → APPROVAL → IMPLEMENTATION → CLOSE-OUT`. `references/spanner.md`'s Next stage walks the stages on the item's §1.1 path, so on the direct path it never reaches Implementation review. 1e's `n/a` clause is unreachable, and AC2.4's purpose fails on the path this spec runs on. | Accepted. 1c marks Review and Implementation review on the direct-path diagram as at Ray's discretion. 1f gives Review a direct-path `n/a` condition. 3a tells Next stage to pass over an `n/a` stage, and to name a discretionary stage that is neither done nor `n/a` together with the stage after it. |
| 20261028 | Caliper | 7: AC2.4's grep is met by 3a's string alone and does not test the property that Next stage reports the Implementation review stage. | Accepted. AC2.4 is checked by Ray's `/session-start Spanner 243` run after Step 4, plus a reading of the `n/a` pass-over. |
| 20261028 | Caliper | 7: I1 counts a change as traced if it touches a file in the §4 `Files` column, so any edit inside a named file passes. AC3.1 plants its change in a file no step names, the one case a file-level trace catches. | Accepted. I1 traces each change to a step's deliverable or quoted text; naming the file is not enough. AC3.1 plants its change inside `docs/DEVELOPMENT_STANDARDS.md`, in a section no step quotes. |
| 20261028 | Caliper | 3: I2 leaves the reviewer to judge whether an unlisted departure "required a stop", with no method and no field to record it. | Accepted. The judgment is removed. A departure §4 does not list has no stop on record, so every I2 finding is an unstopped departure. I1 and I2 no longer overlap: I1 is a change no step covers, I2 a change a step covers that departs from it. |
| 20261028 | Caliper | 3: It is unspecified whether AC3.1's planted-change run is the branch's Implementation review, whether the plant and revert commits are findings in a later run, and how the commit is removed. | Accepted. AC3.1's run is a test. Its row is AC3.1's evidence and is not logged here. The Implementation review is a separate request after the revert. The plant is removed with `git revert`, so the two commits leave no change in the diff I1 reads. |
| 20261028 | Caliper | 3: Ray's ruling has two homes, the Decision Log row (1b) and results §4 `Resolved by` (3b). It is also unstated whether I3 reports a `none` row Ray has already ruled on. | Accepted. The ruling's home is the Decision Log row (`docs/DEVELOPMENT_STANDARDS.md` §1.5). Results §4 `Resolved by` names Ray and that row's date. I3 reports only a `none` row still `Awaiting Ray`. |
| 20261028 | Caliper | 3: I4 does not cover a row whose check names Ray that the implementer marked `Met` on its own reading, which §1.2 forbids. | Accepted. Such a row is an I4 finding unless its evidence names Ray with a date, the form Ray's sign-off takes in results §3. |
| 20261028 | Caliper | 3: Read 2 gives no command to find the results artifact on the branch, and read 4 gives no rule for taking the branch name out of the `**Branch:**` field. | Accepted. Read 2 finds it with `git grep`. `<branch>` is the first backtick-quoted name in the `**Branch:**` field. |
| 20261028 | Caliper | 3: 1c's "Nothing on this path is optional except the Role 2 review" contradicts the next paragraph, under which a design artifact is optional where it is not required. AC2.3 inherits the contradiction. | Accepted. 1d drops the "only optional" claim and states the four unmarked stages as required and the two marked stages as Ray's discretion. AC2.3 is reworded. |
| 20261028 | Caliper | Amendment: 3: No rule covers a post-implementation review when the Caliper session that reviewed the spec has ended. Suggested wording for §1.1 Implementation review: "Where that session has ended, Ray opens `/session-start Caliper <spec path>` and requests the review in the new session; the session-open emit is not logged against an `Approved` spec." | **Not taken** — Ray, 20261028: a session that crashes is resumed, not replaced. Each Claude Code session can be reopened from the session picker, so the review stays in the Caliper session that reviewed the spec, and no rule for a replacement session is needed. |
| 20261028 | Caliper | 3: 3a names a discretionary stage that is neither done nor `n/a` together with the stage after it, as Ray's choice. On a direct-path spec with `Caliper` rows and a results artifact, Implementation review is neither, so Spanner would emit "Implementation review or Close-out". But 1g makes that review required once Review ran, and AC2.4 expects Implementation review alone. The choice wording fits only Review before approval. | Accepted. 3a names only Review, before the spec is `Approved`, together with Approval as Ray's choice. Implementation review is decided by 1f's done condition, done or `n/a`, so there is no choice to name. |
| 20261028 | Caliper | 3: 1f's direct-path `n/a` clauses contradict the unchanged sentence above the table, "A stage on both paths has the same condition on each", and 1d's "with the same done conditions". | Accepted. 1f also amends that sentence to except a row's stated direct-path `n/a`, and 1d cites the table instead of claiming the same conditions. |
| 20261028 | Caliper | 2: I4 relies on "the form Ray's sign-off takes in results §3", but no standard states that form. `docs/DEVELOPMENT_STANDARDS.md` §1.2 says only "Ray changes the row once he has checked it", and archived rows vary: `docs/archive/results/AUTO_MEMORY_RETIREMENT_RESULTS.md` § 3 has undated sign-offs. | Accepted. Setting the form establishes a method, so under §1.2 it is written into §1.2 in this spec (1h), with AC1.2. I4 cites §1.2. The form applies from here forward; archived rows are not rewritten, and I4 reads only new cycles. |

---

## 1. Scope

**In scope:**

- `docs/DEVELOPMENT_STANDARDS.md` §1.1 and §1.2.
- `.claude/skills/session-start/SKILL.md` § Role 2.
- `.claude/skills/session-start/references/caliper.md`, a new § Post-implementation review.
- `.claude/skills/session-start/references/spanner.md` § Reads 4.
- `docs/dev/results/_TEMPLATE_RESULTS.md` § 4 and `docs/dev/specs/_TEMPLATE_SPEC.md` § Decision Log.
- The design study's §6 Disposition and this spec's results artifact.

**Out of scope:**

- `SKILL.md`'s frontmatter, Step 0 and usage line. Ray's direction: no new target.
- `.claude/skills/closeout/`. See the Decision Log on `P7` and `P9`.
- `references/anvil.md`. A fix the review leads to reaches Anvil through the spec, under the unchanged § Spanner → Anvil handoff.
- The decision for issue #245, which this review only feeds.

## 2. Verified current state

Direct path: each step quotes the text it replaces. Every quoted line was confirmed to occur exactly once in its file on 20261027, at `d89ea26`.

## 3. Design rules

- **DR1 — Exact text.** Each edit is made as quoted. A wording or mechanical change within the meaning, scope and file set approved here is recorded in the results artifact's §4 as `within approved meaning`. A quote that does not match the file stops the step.
- **DR2 — One home.** The review's stage, its done condition and the disposition of an unstopped departure are stated in §1.1. When each review is required is stated in §1.2. The review's reads, checks and emits are stated in `references/caliper.md` § Post-implementation review. Every other passage cites one of these.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | §1.1 places the Implementation review stage on both paths, states its done condition and the disposition of an unstopped departure; §1.2 states when each review is required and the evidence form of Ray's sign-off | `docs/DEVELOPMENT_STANDARDS.md` |
| 2 | Role 2 covers both review points; Caliper's reference states the post-implementation review | `.claude/skills/session-start/SKILL.md`, `.claude/skills/session-start/references/caliper.md` |
| 3 | Spanner's session open reads post-implementation rows and walks the discretionary stages; the templates carry the new Source and cite the disposition | `.claude/skills/session-start/references/spanner.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/dev/specs/_TEMPLATE_SPEC.md` |
| 4 | Study disposition and results artifact | `docs/dev/design/DESIGN_POST_IMPLEMENTATION_REVIEW.md`, `docs/dev/results/POST_IMPLEMENTATION_REVIEW_RESULTS.md` |

Close-out is not in this table. It is `/closeout`.

### Step 1 — `docs/DEVELOPMENT_STANDARDS.md`

**1a.** In §1.1 **Full path**, replace:

```text
RECON  →  ANALYSIS  →  SPEC  →  REVIEW  →  APPROVAL  →  IMPLEMENTATION  →  CLOSE-OUT
```

with:

```text
RECON  →  ANALYSIS  →  SPEC  →  REVIEW  →  APPROVAL  →  IMPLEMENTATION  →  IMPLEMENTATION REVIEW  →  CLOSE-OUT
```

**1b.** In the same list, replace:

```text
- **Implementation** — Role 3, step by step, from the approved spec only.
```

with:

```text
- **Implementation** — Role 3, step by step, from the approved spec only.
- **Implementation review** — Role 2 reviews the delivered branch against the spec and its results artifact, on Ray's request in the Caliper session that reviewed the spec. `.claude/skills/session-start/references/caliper.md` § Post-implementation review states its reads and checks. Findings go back to Role 1, never forward to the implementer.
  - **An unstopped departure** is a change on the branch made without the stop it required: a change that traces to nothing in the spec, a results §4 row whose `Step stopped at` is `none`, or a `within approved meaning` change that altered the meaning, scope or file set Ray approved. Ray rules on each one, as the resolution of its Decision Log row, with one of two outcomes:
    - **Revert** — the change is reverted on the branch, and carried to an issue under §1.3 if it is still wanted.
    - **Keep** — the spec is amended so the change traces to it.
  - The ruling's home is the resolution of the finding's Decision Log row. Role 1 writes it there and writes the outcome into the spec, and the implementing role carries it out. Either way, results §4 lists the departure with `Step stopped at` set to `none`, so the record still shows the stop was skipped, and its `Resolved by` names Ray and the date of that Decision Log row.
```

**1c.** In §1.1 **Direct path**, replace:

```text
SPEC  →  APPROVAL  →  IMPLEMENTATION  →  CLOSE-OUT
```

with:

```text
SPEC  →  REVIEW*  →  APPROVAL  →  IMPLEMENTATION  →  IMPLEMENTATION REVIEW*  →  CLOSE-OUT
```

**1d.** In the same block, replace:

```text
**All four are required.** Nothing on this path is optional except the two things named below as optional.
```

with:

```text
**The four unmarked stages are required.** The two marked `*` are the Role 2 review, which Ray calls for or not at the start (§1.2). Where they run, they are the full path's Review and Implementation review, done when the table below shows them done.
```

**1e.** In §1.1 **What the direct path trades**, replace:

```text
**What the direct path trades.** With no recon, no Role 2 pass and no separate implementer,
```

with:

```text
**What the direct path trades.** With no recon, no required Role 2 pass and no separate implementer,
```

**1f.** In §1.1 **What shows each stage done**, replace:

```text
A stage on both paths has the same condition on each.
```

with:

```text
A stage on both paths has the same condition on each, except where its row states a direct-path `n/a`.
```

In the table that follows, replace:

```text
| Review | The spec's Decision Log carries at least one `Caliper` row, and every `Caliper` row has a resolution. A clean pass is the `No findings.` row `/session-start Caliper` emits for one. |
```

with:

```text
| Review | The spec's Decision Log carries at least one `Caliper` row, and every `Caliper` row has a resolution. A clean pass is the `No findings.` row `/session-start Caliper` emits for one. On the direct path the stage is `n/a` where the spec's `**Status:**` is `Approved` and it carries no `Caliper` row. |
```

and replace:

```text
| Close-out | The spec's `**Status:**` is `Shipped`, and the artifact set is in `docs/archive/`. |
```

with:

```text
| Implementation review | The spec's Decision Log carries at least one `Caliper (post-implementation)` row, and every one has a resolution. A clean pass is the `No findings.` row the review emits for one. On the direct path the stage is `n/a` where the spec carries no `Caliper` row, because it runs only where the Review stage ran (§1.2). |
| Close-out | The spec's `**Status:**` is `Shipped`, and the artifact set is in `docs/archive/`. |
```

**1g.** In §1.2, replace:

```text
- At least one Role 2 review pass before a spec is approved — on the full path. On the direct path a Role 2 pass is optional and at Ray's discretion.
```

with:

```text
- At least one Role 2 review pass before a spec is approved, and a post-implementation review before close-out (§1.1 Implementation review) — on the full path. On the direct path both are at Ray's discretion, decided once, at the start: the post-implementation review runs exactly when Ray had Role 2 review the spec.
```

**1h.** In §1.2, replace:

```text
Ray changes the row once he has checked it.
```

with:

```text
Once he has checked it, the row becomes `Met` with evidence in the form `Ray, <YYYYMMDD>: <what he read or ran>`.
```

### Step 2 — Role 2 and Caliper's reference

**2a.** In `.claude/skills/session-start/SKILL.md` § Role 2, replace:

```text
Findings go BACK to Role 1, never forward. You do not implement.
```

with:

```text
After implementation, on Ray's request in the same session, reviews the delivered branch against the spec and its results artifact — `references/caliper.md` § Post-implementation review. When each review is required: `docs/DEVELOPMENT_STANDARDS.md` §1.2.

Findings go BACK to Role 1, never forward. You do not implement.
```

**2b.** In `.claude/skills/session-start/references/caliper.md`, replace:

```text
## Working rules
```

with:

````text
## Post-implementation review

Run when Ray requests it in this session after the results artifact exists — `docs/DEVELOPMENT_STANDARDS.md` §1.1 Implementation review. `<branch>` is the first backtick-quoted name in the spec's `**Branch:**` field. Every file is read from it with `git show <branch>:<path>`, never from the working tree, because the branch under review need not be the one checked out.

### Reads, in order

1. The spec, end to end.
2. The results artifact that names the spec in its `**Spec:**` field, found with `git grep -l '^\*\*Spec:\*\* .*<spec file name>' <branch> -- <results dir>`, where `<results dir>` is the `results/` directory beside the spec.
3. The originating issue: `gh issue view <N> --json number,title,body,labels,milestone,parent`
4. `git diff <base>..<branch>` and `git log --format='%h %s%n%b' <base>..<branch>`. `<base>` is `git merge-base <parent> <branch>`, and `<parent>` is the branch `docs/DEVELOPMENT_STANDARDS.md` §2.2 names for the branch type: `main` for `chore/*` and `hotfix/*`, `dev` for `feature/*`.

### Checks

- **I1** — A change in the diff that no spec step's deliverable or quoted text covers and no acceptance criterion requires. A change inside a file the step table names is traced only if a step covers that change; naming the file is not enough. Two kinds of change are not checked: the artifact set (the spec, the design study its `**Design study:**` field names, and the results artifact), and a commit `docs/DEVELOPMENT_STANDARDS.md` §2.2 defines as an operational change from live use.
- **I2** — A change a step covers that departs from the step's quoted text or deliverable, and that results §4 does not list.
- **I3** — A results §4 row whose `Step stopped at` is `none` and whose `Resolved by` is `Awaiting Ray`.
- **I4** — A results §3 row marked `Met` whose evidence does not exercise the property its criterion names (`docs/DEVELOPMENT_STANDARDS.md` §1.2). A row whose check names Ray is a finding when it is `Met` and its evidence is not in the form `docs/DEVELOPMENT_STANDARDS.md` §1.2 states for Ray's sign-off. Marked `Not met` with `Awaiting Ray`, it is not a finding.
- **I5** — A results §4 row whose `Step stopped at` is `within approved meaning` and whose change altered the meaning, scope or file set Ray approved.

### Emits

The table § Emits states, with `Caliper (post-implementation)` in the Source column and the check id in place of the criterion number:

```markdown
| <YYYYMMDD> | Caliper (post-implementation) | <check id>: <finding, with the evidence that grounds it> | |
```

With no finding, the review emits one row, `| <YYYYMMDD> | Caliper (post-implementation) | No findings. | n/a |`, and nothing else. No other commentary. Every finding under I1, I2, I3 or I5 is an unstopped departure: a departure results §4 does not list has no stop on record. What happens to it is `docs/DEVELOPMENT_STANDARDS.md` §1.1 Implementation review, and the review does not propose an outcome.

## Working rules
````

### Step 3 — Spanner's session open and the templates

**3a.** In `.claude/skills/session-start/references/spanner.md` § Reads 4, replace:

```text
For each spec found, its Decision Log rows whose Source is `Caliper`,
```

with:

```text
For each spec found, its Decision Log rows whose Source is `Caliper` or `Caliper (post-implementation)`,
```

and in § Emits **Next stage**, replace:

```text
that §1.1's done conditions, applied to the artifacts found, do not show done.
```

with:

```text
that §1.1's done conditions, applied to the artifacts found, do not show done. A stage §1.1 shows `n/a` is passed over. On the direct path, Review before the spec is `Approved` is named together with Approval, as Ray's choice.
```

**3b.** In `docs/dev/results/_TEMPLATE_RESULTS.md` § 4, replace:

```text
`Resolution` is what was done, and `Resolved by` is `Awaiting Ray` until Ray rules on it, then `Ray, <date>`.
```

with:

```text
`Resolution` is what was done, and `Resolved by` is `Awaiting Ray` until Ray rules on it with one of the outcomes `docs/DEVELOPMENT_STANDARDS.md` §1.1 Implementation review states, then `Ray, <date>`, the date of the spec's Decision Log row that holds the ruling.
```

**3c.** In `docs/dev/specs/_TEMPLATE_SPEC.md` § Decision Log, replace:

```text
| YYYYMMDD | Anvil | | |
```

with:

```text
| YYYYMMDD | Anvil | | |
| YYYYMMDD | Caliper (post-implementation) | | |
```

### Step 4 — Study disposition and results artifact

**4a.** In the design study's §6, replace `- Promoted to:` with ``- Promoted to: `../specs/POST_IMPLEMENTATION_REVIEW_SPEC.md` ``.

**4b.** Write `docs/dev/results/POST_IMPLEMENTATION_REVIEW_RESULTS.md` from `docs/dev/results/_TEMPLATE_RESULTS.md`, with `**Released as:** n/a — chore/*`.

### Authorization points

None in Steps 1–4. Merging this branch to `main` is close-out's, at its own stop.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Caliper's reference states a post-implementation review, run on Ray's request in the live Caliper session, with its reads (spec, results artifact, issue, and the branch diff against its §2.2 parent's merge base) and its checks: the issue's four, plus a check of each `within approved meaning` row for a change of meaning. Restated from issue AC1, which assumed a new `/session-start` target. | Stated reading by Ray of `.claude/skills/session-start/references/caliper.md` § Post-implementation review |
| AC1.2 | §1.2 states the evidence form of Ray's sign-off on a criterion whose check names him, and I4 judges a `Met` row by that form. | Stated reading by Ray of `docs/DEVELOPMENT_STANDARDS.md` §1.2 and `references/caliper.md` § Post-implementation review I4 |
| AC2.1 | Role 2 covers both review points: the spec before implementation, and the delivered branch after it. | Stated reading by Ray of `.claude/skills/session-start/SKILL.md` § Role 2 |
| AC2.2 | On the full path, the Implementation review stage sits between Implementation and Close-out, with a done condition that tells it apart from the Review stage. | Stated reading by Ray of `docs/DEVELOPMENT_STANDARDS.md` §1.1: the full-path diagram, the stage list and the done table |
| AC2.3 | §1.2 states when each review is required on each path, and §1.1's direct path marks its two Role 2 stages as at Ray's discretion, citing §1.2, without contradicting the design-artifact paragraph that follows. | Stated reading by Ray of `docs/DEVELOPMENT_STANDARDS.md` §1.1 Direct path and §1.2 |
| AC2.4 | Spanner's session open reports Implementation review as the next stage on a branch whose implementation is done and whose spec had a Role 2 review, and passes over the stage where §1.1 shows it `n/a`. | After Step 4 and before the Implementation review, Ray runs `/session-start Spanner 243` and reports its Next stage as Implementation review; and a stated reading by Ray of `.claude/skills/session-start/references/spanner.md` § Emits **Next stage** for the `n/a` pass-over |
| AC3.1 | Run against this spec's branch carrying a known untraced change inside a file a step names, the review reports it as an I1 finding. Restated from issue AC3, which planted the change on a separate test branch. | After Step 4, Ray commits an edit to `docs/DEVELOPMENT_STANDARDS.md` in a section no step quotes, asks the Caliper session for the post-implementation review under `references/caliper.md` § Post-implementation review, reports the I1 row, and removes the edit with `git revert`. The run is a test: its row is this AC's evidence and is not logged in the Decision Log. The Implementation review is a separate request after the revert |
| AC4.1 | Run against a branch whose every change traces and whose §4 rows all record a stop, the review emits the `No findings.` row and nothing else. | `Carried` to #240, whose second criterion is the same run. Ray reports the output on the first full-path cycle after this closes |
| AC5.1 | The disposition of an unstopped departure is stated in the standards in one place, and the results template cites it instead of restating it. | Stated reading by Ray of `docs/DEVELOPMENT_STANDARDS.md` §1.1 Implementation review and `docs/dev/results/_TEMPLATE_RESULTS.md` § 4, with `grep -rn 'still wanted' CLAUDE.md docs/DEVELOPMENT_STANDARDS.md .claude/ docs/dev/*/_TEMPLATE_*.md` returning only §1.1's line |

## 6. Test plan

Omitted: no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes.

## 7. Risks and rollback

- **A quote does not match.** DR1 stops the step. Rollback: none needed.
- **I1 reports the artifact set or an operational-change commit.** The exclusion in I1 is wrong or incomplete; AC3.1's run shows it. Rollback: correct I1 under this spec before close-out.
- **A live Caliper session predates Step 2.** It loaded the old reference. AC3.1's request names the section so the session reads it; any later cycle's session opens after this ships. Rollback: none needed.
- **A step is wrong.** Rollback: revert that step's commit.
