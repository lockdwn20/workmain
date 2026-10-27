# Post-Implementation Review — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261027
**Originating item:** Issue #243

---

## 1. Purpose

Issue #243 adds a second review point for Caliper (Role 2). Today Caliper reviews a spec before it is approved, and nothing checks the delivered branch against the spec. `/closeout`'s `P6` check confirms that every acceptance criterion has a results row; it does not check that every change traces to the spec. Spanner has done that check informally, which means it judges the gaps in its own spec. The issue fixes the four checks the new review makes and asks the spec to settle two questions: what happens to an unstopped departure the review finds, and whether the review is required on the direct path (`chore/*`). This study holds the census of everything the change touches, the mechanics no rule leaves open, and those two questions. The direct path permits this artifact and requires it where the work raises questions whose answers change it (`docs/DEVELOPMENT_STANDARDS.md` §1.1). Both of the issue's questions do.

## 2. Scope of the read

- **Read in full:** `.claude/skills/session-start/SKILL.md` and its three references `references/caliper.md`, `references/spanner.md`, `references/anvil.md`; `.claude/skills/closeout/SKILL.md`; `docs/DEVELOPMENT_STANDARDS.md` §1.1–§1.6 and §2.2; `docs/dev/results/_TEMPLATE_RESULTS.md`; `docs/dev/specs/_TEMPLATE_SPEC.md`; `docs/dev/design/_TEMPLATE_DESIGN.md`; issues #240, #243 and #245.
- **Searched:** the document set `docs/DEVELOPMENT_STANDARDS.md` §1.5 names for a rule change (`CLAUDE.md`, `docs/DEVELOPMENT_STANDARDS.md`, `.claude/`, the three `docs/dev/*/_TEMPLATE_*.md` files), plus `docs/AI_SETTINGS_GUIDE.md`, `.github/` and `automation/` excluding `automation/fixtures/`. The search ran on 20261027 from branch `chore/issue-243-post-implementation-review` at `ee91112`, as `grep -rniE 'caliper|role 2|before implementation|review stage|post-implementation'`, and every hit was read in its paragraph. §3 lists the hits that bear on the change. The rest are template-compliance disclaimers, which are unaffected, and one code comment in `automation/closeout_acs.py:49`, a historical citation.
- **Read for practice:** the commits on two shipped branches, `feature/issue-202-clockify-service` (`git log a19e7cf^1..a19e7cf^2`, full path) and `chore/issue-246-main-push-route` (`git log 77f6ac7^1..77f6ac7^2`, direct path), to find what a branch diff carries besides the implementation.
- **Not in scope:** a `/closeout` preflight check that the review ran. Issue #240 keeps `P7` reserved ("a mechanical scope check is revisited only if Caliper's review proves inconsistent"), and `/closeout` does not gate the pre-implementation review either: `P4` checks only that the spec's `**Status:**` is `Approved` or `Shipped`. The decision for issue #245 is also out of scope. This work only produces the evidence it decides from.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | Role 2 is defined as a review "before implementation begins". Its seven criteria are about a spec. None of them is about a delivered branch. | `.claude/skills/session-start/SKILL.md` § Role 2, "Reviews every spec before implementation begins, against these criteria" | High |
| F2 | Caliper's session open takes one target, a spec path. It reads the spec, the issue, the design study and every cited source, and it emits findings numbered by the Role 2 criteria. It reads no results artifact and no diff. | `.claude/skills/session-start/references/caliper.md` § Reads and § Emits | High |
| F3 | The skill declares two arguments, and Step 0 refuses a Caliper call with no target. A third token, such as a branch name, has no declared argument to land in. The usage line says Caliper requires only a spec path. | `.claude/skills/session-start/SKILL.md` frontmatter `arguments: [role, target]` and `argument-hint`; § Step 0 and its `Usage:` line | High |
| F4 | The full path has no stage between Implementation and Close-out: not in the diagram, not in the stage list, not in the table of what shows each stage done. The Review row of that table reads "at least one `Caliper` row, and every `Caliper` row has a resolution". If post-implementation findings were logged under the same Source, two things would go wrong. An open post-implementation row would make the Review stage read as not done after implementation. And nothing would show whether the post-implementation review had run. | `docs/DEVELOPMENT_STANDARDS.md` §1.1, the `RECON → … → CLOSE-OUT` block, the stage bullets, the "What shows each stage done" table | High |
| F5 | Spanner's session open emits the Decision Log rows whose Source is exactly `Caliper`, and derives its Next stage from §1.1's done table. A new Source value or a new stage row has to be reflected there, or `/session-start Spanner` reports the wrong stage. | `.claude/skills/session-start/references/spanner.md` § Reads 4 and § Emits "Next stage" | Medium |
| F6 | No standard says what can happen to an unstopped departure. The results template has a `none` row (a change made without the stop it required) carry `Resolved by` = `Awaiting Ray` "until Ray rules on it". It does not say what Ray may rule. The nearest rule covers a finding outside a spec's scope: Ray decides whether it becomes its own issue, joins an open one, or is bundled. That rule is about a finding not yet acted on, not a change already on the branch. | `docs/dev/results/_TEMPLATE_RESULTS.md` § 4, third bullet; `docs/DEVELOPMENT_STANDARDS.md` §1.2, "A finding outside the spec's scope is not fixed in it" | High |
| F7 | On the direct path a pre-implementation Role 2 pass is optional, at Ray's discretion. §1.1 says the direct path runs "with no recon, no Role 2 pass and no separate implementer". Its diagram lists four required stages, then "Nothing on this path is optional except the two things named below as optional", but nothing below that line is named as optional. The design artifact is "permitted", and the optional Role 2 pass is stated in §1.2, not below. Issue #245 says its evidence comes from "the first direct-path cycles reviewed under #243". That evidence exists only if direct-path cycles are reviewed. | `docs/DEVELOPMENT_STANDARDS.md` §1.1 lines 40 and 51; §1.2 line 90; issue #245 body | High |
| F8 | A branch diff carries more than the implementation. Both branches read carry the design study, the spec, its Decision Log edits and the results artifact. #202's branch has commits `bd501e6`, `77a7541`, `06c8f93`, `12487eb`, `bf4fb7b`, `a770630`. #246's has `eee95ed`, `a9a9110`, `7f64b7f`, `7e92186`. §2.2 also lets any branch carry one operational-change commit (`chore(config)` or `chore(templates)`, a file a `workmain` command wrote), which "is not scope of the issue the branch serves". None of these traces to a spec step, so the first check would report every one of them unless they are excluded by rule. | `git log` of the two branches; `docs/DEVELOPMENT_STANDARDS.md` §2.2 "Operational changes from live use" | High |
| F9 | The issue's first check names a "Summary of Files entry". The spec template has no such section. A spec's file set is the `Files` column of its §4 step table. | `docs/dev/specs/_TEMPLATE_SPEC.md` § 4 Steps | Low |
| F10 | `/closeout` takes the base of a branch's diff as `git merge-base main <branch>`, and so does the issue. That base is right for `chore/*` and `hotfix/*`, which branch from `main`. `feature/*` branches from `dev`, and §2.2 lets `dev` be "one feature ahead of `main`". A feature branch cut while `dev` is ahead would carry the previous feature in a diff against `main`'s merge base, and every change in it would be reported as untraced. `/closeout`'s `P9` has the same exposure; that is outside this issue. | `.claude/skills/closeout/SKILL.md` § When this runs, "Base ref"; `docs/DEVELOPMENT_STANDARDS.md` §2.2 `dev`, `feature/*` | Low |
| F11 | Caliper's reads are taken from the working tree: "The spec at the target path". At post-implementation time the branch under review need not be checked out, and the issue's own third criterion has Ray plant a change on a separate test branch. Reading the spec and results from the working tree would review whatever is checked out, not the branch named. | `.claude/skills/session-start/references/caliper.md` § Reads 1 | Medium |

## 4. Options and decided mechanics

### 4.1 Decided by rule

Each of these is settled by a standing rule or by the findings, and is stated here so that the spec can cite it.

- **Where findings are recorded.** In the spec's Decision Log. `docs/DEVELOPMENT_STANDARDS.md` §1.5 gives specs a Decision Log for "decisions and review findings with their resolution", and gives results artifacts none. Spanner writes the rows in, as it does for pre-implementation findings, and findings go back to Role 1, never forward (`.claude/skills/session-start/SKILL.md` § Role 2).
- **How they are told apart (F4, F5).** A distinct Source value for post-implementation rows, with the four checks numbered within it. §1.1 gets a new stage and a done row keyed on that Source value. `references/spanner.md` read 4 emits both Source values. Reusing `Caliper` is defeated by F4.
- **The target (F3, F11).** `/session-start Caliper <spec path> <branch>`. The skill gets a third declared argument. When it is present, the run is the post-implementation review. Its reads come from the branch through `git show <branch>:<path>`, not from the working tree. If the spec's `**Branch:**` field names a different branch, that is emitted as a finding. The run is not refused, so the issue's planted-change check can run on a test branch. Inferring the mode from whether a results artifact exists is defeated: if the results artifact is missing, the run would silently fall back to a pre-implementation review of an implemented branch.
- **The reads.** The spec, the results artifact beside it that names it in its `**Spec:**` field, the originating issue, and `git diff <base>..<branch>`. The base is `git merge-base <parent> <branch>`, where the parent is the one §2.2 names for the branch type: `main` for `chore/*` and `hotfix/*`, `dev` for `feature/*` (F10). That is a change from the issue's literal command, made on the merits under `docs/DEVELOPMENT_STANDARDS.md` §1.2 ("criteria validate the work; they do not design it"). The spec's §5 restates the criterion it affects.
- **The checks.** The issue's four checks, plus the check the issue's 20261027 addition requires: every `within approved meaning` row in results §4 is read for a change of meaning, scope or file set. The first check traces to a spec step, a §4 `Files` entry or an acceptance criterion (F9). It excludes the artifact set and any §2.2 operational-change commit, each identified by rule, not by judgement (F8). The fourth check reads an AC row against the criterion's property, under `docs/DEVELOPMENT_STANDARDS.md` §1.2. A row that names Ray is `Not met` / `Awaiting Ray` by that rule, so it is not a finding.
- **What shows the stage done.** The spec's Decision Log carries at least one post-implementation row, and every one has a resolution. A clean pass is the `No findings.` row, as for the pre-implementation review.
- **A fix the review leads to.** It goes through the spec. Spanner writes the resolution into the spec, and the implementing role on that path (Anvil on the full path, Role 1 on the direct path) carries it out and updates results §4. That is § Spanner → Anvil handoff unchanged: the spec is the whole instruction.
- **The F7 sentence.** "The two things named below as optional" is corrected wherever Q2's answer lands, because that answer changes the same list.

### 4.2 Disposition of an unstopped departure (Q1)

"Unstopped departure" covers three cases: a change the review traces to nothing (check 1); a results §4 row with `Step stopped at` = `none` (check 3); and a `within approved meaning` row the review finds changed meaning (the added check). Each is a change already on the branch that should have stopped first.

The issue's "split to its own issue on the §1.3 rule" is not a third option: a change kept on the branch cannot also be the work of a new issue. Splitting is the second half of reverting, so it appears inside Option A.

#### Option A — Always revert

- **Approach:** the change is reverted on the branch before close-out. If it is still wanted, it is carried to an issue under `docs/DEVELOPMENT_STANDARDS.md` §1.3, joining an open issue that covers it where one exists.
- **Pros:** the stop has a cost, so skipping it gains nothing. Nothing is approved after the fact. The shipped spec describes exactly what shipped.
- **Cons:** a departure that an acceptance criterion depends on cannot be reverted without leaving the branch unable to meet that criterion. §1.3 requires an issue to leave the repository coherent and verifiable, so such a branch cannot close out. And it costs a revert plus a new issue cycle for whitespace-level changes like those #241's results recorded.

#### Option B — Ray decides each finding, between two stated outcomes

- **Approach:** for each finding Ray rules one of two outcomes, recorded as the resolution of its Decision Log row. (i) **Revert**: Option A for this change. (ii) **Keep**: Spanner amends the spec so that the change traces to it, and Ray's resolution of the row is the approval. Either way the results §4 row keeps `none` as its `Step stopped at`, so the record still shows the stop was skipped. The standards state the two outcomes in one place. The results template's `none` bullet cites that place instead of saying only "until Ray rules".
- **Pros:** covers the case Option A cannot, where the change is one the delivered work needs. The breach stays visible in results §4 and in the review's findings, which are what issue #240's second criterion and issue #245's measures read. The shipped spec still describes what shipped.
- **Cons:** outcome (ii) is approval after the change, which is the pattern issue #240 sets out to close. Its only check is Ray's ruling on each row, and the visible `none` record behind it.

**Recommendation: B.** Issue #240 says departures "will occur however good the spec is", and requires that each one *show* whether a stop happened. It does not require that each one be undone. #242 built the record that shows the stop. Option B keeps that record intact and gives Ray a bounded ruling. Option A would make Ray revert changes the branch needs in order to close out. That outcome blocks the issue, and nothing in the standards asks for it.

### 4.3 The review on the direct path (Q2)

#### Option A — Required on both paths

- **Approach:** §1.1's direct path gains the stage between Implementation and Close-out as a fifth required stage, and the F7 sentence is corrected to name only the pre-implementation Role 2 pass as optional.
- **Pros:** the direct path is where one role writes the spec, implements it and records its own departures. That makes it the path where no independent check exists today. `within approved meaning` rows exist only on the direct path, and the issue's added check reads them. Issue #245's three measures come from direct-path cycles reviewed under this issue, so a required review supplies them on every cycle.
- **Cons:** a Caliper session on every `chore/*` branch, including one-line documentation fixes.

#### Option B — Optional, at Ray's discretion

- **Approach:** the same rule as the pre-implementation review on the direct path: §1.2's sentence is extended to cover both review points.
- **Pros:** no added session for small direct-path changes, and the same treatment for both review points.
- **Cons:** the role that wrote and implemented the spec also decides whether its own `within approved meaning` rows changed meaning, unless Ray calls for the review. That is the self-grading the issue names as the defect. Issue #245's evidence arrives only from the cycles Ray elects to review.

**Recommendation: A.** The pre-implementation review is optional on the direct path because Ray's approval of the spec is a review at that point. No equivalent review exists after implementation. A docs spec quotes its replacement text, so tracing its diff is quick. The cost is one session, and the defect the issue names is concentrated on this path.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | When the post-implementation review finds an unstopped departure (a change on the branch that traces to nothing in the spec, a results §4 row recording no stop, or a `within approved meaning` change that altered meaning), what happens to it? Option A in §4.2: always revert, and carry the change to an issue if it is still wanted. Option B: Ray rules each finding as either revert, or keep with the spec amended so the change traces; results §4 records the skipped stop either way. Recommendation: B, because a change the branch needs to meet a criterion cannot be reverted without blocking close-out, and the record of the breach survives either outcome. | |
| Q2 | Is the post-implementation review required on the direct path (`chore/*`), where Role 1 implements its own spec and records its own `within approved meaning` changes, or optional at Ray's discretion as the pre-implementation review is there? Option A in §4.3: required. Option B: optional. Recommendation: A, because the direct path has no independent check after implementation, and issue #245 decides from the direct-path cycles this review covers. | |

## 6. Disposition

- Promoted to:
