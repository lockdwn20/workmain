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
| 20261027 | Spanner | Outside scope: `/closeout`'s `P9` takes its base as `git merge-base main <branch>` and has the same exposure for `feature/*` (`.claude/skills/closeout/SKILL.md` § When this runs, "Base ref"). An issue for it needs: the defect (a `feature/*` branch cut while `dev` is ahead of `main` diffs against the wrong base), and a criterion that `/closeout` takes the base from the branch's §2.2 parent. `gh issue list --state open` searched for `merge-base`, `Base ref` and `P9` finds no open issue covering it. | Ray decides under `docs/DEVELOPMENT_STANDARDS.md` §1.2. |
| 20261027 | Spanner | Post-implementation rows carry Source `Caliper (post-implementation)` and check ids `I1`–`I5`. Reusing `Caliper` would make the Review stage read as not done whenever a post-implementation finding is open, and would leave nothing to show the new stage done (design study F4). | Steps 1, 2 and 3. |
| 20261027 | Spanner | No `/closeout` check for the new stage. Issue #240 keeps `P7` reserved, and `/closeout` does not gate the pre-implementation review either. | No step. |
| 20261027 | Spanner | Issue AC4 runs on the first full-path cycle after this closes, so it cannot be `Met` before this close-out's `P6`. Issue #240's second criterion is the same run: one full-path cycle after all of #240's children close, read with Caliper's findings table. | AC4.1 is `Carried` to #240. |
| 20261027 | Spanner | AC3.1 runs the review on this branch, which on the direct path needs a pre-implementation Caliper review of this spec (Q2). That Caliper session loads `references/caliper.md` at open, before Step 2 writes the new section. | AC3.1's request names the section, so the session reads it from the branch. Ray decides whether Caliper reviews this spec. |

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
| 1 | §1.1 places the Implementation review stage, states its done condition and the disposition of an unstopped departure; §1.2 states when each review is required | `docs/DEVELOPMENT_STANDARDS.md` |
| 2 | Role 2 covers both review points; Caliper's reference states the post-implementation review | `.claude/skills/session-start/SKILL.md`, `.claude/skills/session-start/references/caliper.md` |
| 3 | Spanner's session open reads post-implementation rows; the templates carry the new Source and cite the disposition | `.claude/skills/session-start/references/spanner.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/dev/specs/_TEMPLATE_SPEC.md` |
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
  - Either way, results §4 lists the departure with `Step stopped at` set to `none`, so the record still shows the stop was skipped. Role 1 writes the outcome into the spec, and the implementing role carries it out.
```

**1c.** In §1.1 **Direct path**, replace:

```text
**All four are required.** Nothing on this path is optional except the two things named below as optional.
```

with:

```text
**All four are required.** Nothing on this path is optional except the Role 2 review, which runs at Ray's discretion before approval and, where it ran, again after implementation (§1.2). Where it runs, it is the full path's Review and Implementation review.
```

**1d.** In §1.1 **What the direct path trades**, replace:

```text
**What the direct path trades.** With no recon, no Role 2 pass and no separate implementer,
```

with:

```text
**What the direct path trades.** With no recon, no required Role 2 pass and no separate implementer,
```

**1e.** In §1.1's table of what shows each stage done, replace:

```text
| Close-out | The spec's `**Status:**` is `Shipped`, and the artifact set is in `docs/archive/`. |
```

with:

```text
| Implementation review | The spec's Decision Log carries at least one `Caliper (post-implementation)` row, and every one has a resolution. A clean pass is the `No findings.` row the review emits for one. On the direct path the stage is `n/a` where the spec carries no `Caliper` row, because it runs only where the Review stage ran (§1.2). |
| Close-out | The spec's `**Status:**` is `Shipped`, and the artifact set is in `docs/archive/`. |
```

**1f.** In §1.2, replace:

```text
- At least one Role 2 review pass before a spec is approved — on the full path. On the direct path a Role 2 pass is optional and at Ray's discretion.
```

with:

```text
- At least one Role 2 review pass before a spec is approved, and a post-implementation review before close-out (§1.1 Implementation review) — on the full path. On the direct path both are at Ray's discretion, decided once, at the start: the post-implementation review runs exactly when Ray had Role 2 review the spec.
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

Run when Ray requests it in this session after the results artifact exists — `docs/DEVELOPMENT_STANDARDS.md` §1.1 Implementation review. `<branch>` is the branch named in the spec's `**Branch:**` field. Every file is read from it with `git show <branch>:<path>`, never from the working tree, because the branch under review need not be the one checked out.

### Reads, in order

1. The spec, end to end.
2. The results artifact in the `results/` directory beside the spec that names the spec in its `**Spec:**` field.
3. The originating issue: `gh issue view <N> --json number,title,body,labels,milestone,parent`
4. `git diff <base>..<branch>` and `git log --format='%h %s%n%b' <base>..<branch>`. `<base>` is `git merge-base <parent> <branch>`, and `<parent>` is the branch `docs/DEVELOPMENT_STANDARDS.md` §2.2 names for the branch type: `main` for `chore/*` and `hotfix/*`, `dev` for `feature/*`.

### Checks

- **I1** — A change in the diff that traces to no spec step, no entry in the spec's §4 `Files` column and no acceptance criterion. Two kinds of change are not checked: the artifact set (the spec, the design study its `**Design study:**` field names, and the results artifact), and a commit `docs/DEVELOPMENT_STANDARDS.md` §2.2 defines as an operational change from live use.
- **I2** — A departure in the diff that results §4 does not list.
- **I3** — A results §4 row whose `Step stopped at` is `none`.
- **I4** — A results §3 row marked `Met` whose evidence does not exercise the property its criterion names (`docs/DEVELOPMENT_STANDARDS.md` §1.2). A row whose check names Ray is `Not met` with `Awaiting Ray` under that section, and is not a finding.
- **I5** — A results §4 row whose `Step stopped at` is `within approved meaning` and whose change altered the meaning, scope or file set Ray approved.

### Emits

The table § Emits states, with `Caliper (post-implementation)` in the Source column and the check id in place of the criterion number:

```markdown
| <YYYYMMDD> | Caliper (post-implementation) | <check id>: <finding, with the evidence that grounds it> | |
```

With no finding, the review emits one row, `| <YYYYMMDD> | Caliper (post-implementation) | No findings. | n/a |`, and nothing else. No other commentary. A finding under I1, I3 or I5 is an unstopped departure, and so is one under I2 whose change required a stop. What happens to it is `docs/DEVELOPMENT_STANDARDS.md` §1.1 Implementation review, and the review does not propose an outcome.

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

**3b.** In `docs/dev/results/_TEMPLATE_RESULTS.md` § 4, replace:

```text
`Resolution` is what was done, and `Resolved by` is `Awaiting Ray` until Ray rules on it, then `Ray, <date>`.
```

with:

```text
`Resolution` is what was done, and `Resolved by` is `Awaiting Ray` until Ray rules on it with one of the outcomes `docs/DEVELOPMENT_STANDARDS.md` §1.1 Implementation review states, then `Ray, <date>`.
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
| AC2.1 | Role 2 covers both review points: the spec before implementation, and the delivered branch after it. | Stated reading by Ray of `.claude/skills/session-start/SKILL.md` § Role 2 |
| AC2.2 | On the full path, the Implementation review stage sits between Implementation and Close-out, with a done condition that tells it apart from the Review stage. | Stated reading by Ray of `docs/DEVELOPMENT_STANDARDS.md` §1.1: the full-path diagram, the stage list and the done table |
| AC2.3 | §1.2 states when each review is required on each path, and §1.1's direct path names the Role 2 review as its only optional item, citing §1.2. | Stated reading by Ray of `docs/DEVELOPMENT_STANDARDS.md` §1.1 Direct path and §1.2 |
| AC2.4 | Spanner's session open reads post-implementation rows, so its Next stage sees the Implementation review stage. | `grep -n 'Caliper (post-implementation)' .claude/skills/session-start/references/spanner.md` returns § Reads 4's line |
| AC3.1 | Run against this spec's branch carrying a known untraced change, the review reports it as an I1 finding. Restated from issue AC3, which planted the change on a separate test branch. | After Step 4, Ray commits a change to a file no step names, asks the Caliper session for the post-implementation review under `references/caliper.md` § Post-implementation review, reports the I1 row, and reverts the commit |
| AC4.1 | Run against a branch whose every change traces and whose §4 rows all record a stop, the review emits the `No findings.` row and nothing else. | `Carried` to #240, whose second criterion is the same run. Ray reports the output on the first full-path cycle after this closes |
| AC5.1 | The disposition of an unstopped departure is stated in the standards in one place, and the results template cites it instead of restating it. | Stated reading by Ray of `docs/DEVELOPMENT_STANDARDS.md` §1.1 Implementation review and `docs/dev/results/_TEMPLATE_RESULTS.md` § 4, with `grep -rn 'still wanted' CLAUDE.md docs/DEVELOPMENT_STANDARDS.md .claude/ docs/dev/*/_TEMPLATE_*.md` returning only §1.1's line |

## 6. Test plan

Omitted: no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes.

## 7. Risks and rollback

- **A quote does not match.** DR1 stops the step. Rollback: none needed.
- **I1 reports the artifact set or an operational-change commit.** The exclusion in I1 is wrong or incomplete; AC3.1's run shows it. Rollback: correct I1 under this spec before close-out.
- **A live Caliper session predates Step 2.** It loaded the old reference. AC3.1's request names the section so the session reads it; any later cycle's session opens after this ships. Rollback: none needed.
- **A step is wrong.** Rollback: revert that step's commit.
