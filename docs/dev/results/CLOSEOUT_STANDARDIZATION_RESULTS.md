# Close-Out Standardization — Implementation Results

**Status:** Shipped
**Author:** Ray
**Date:** 20260825
**Spec:** n/a — this issue carried no spec; see §1
**Released as:** n/a — `chore/*`, which §2.2 allows no release

---

## 1. Summary

Issue #91 reconciled the `/closeout` skill with the governing documents, corrected the rules the skill was citing that were wrong at their source, extended close-out to cover design artifacts, and cleared the artifact-status backlog that the missing coverage had produced. Documents and skill instructions only — no application code, no tests, no schema.

**This issue carried no spec.** It was authored, decided and executed directly against the issue's acceptance criteria, on the basis that it edits governing documents rather than implementing against them, and that its stated acceptance method is a walk-through rather than a mechanical check. Its ACs are therefore the issue's own, which is also the set close-out verifies — `RECON_CLOSEOUT_PERFORMS.md` F15 records that decision as already taken: *"Issue ACs, not spec ACs."* §4 records this as the first deviation.

The work is **complete**. AC14's reconciliation walk-through — the issue's stated acceptance method — was performed by Ray with Spanner on 20260827. It confirmed §6's census, found three fragments the census had not classified and two defects, and corrected both in the same commit. Every AC is met and evidenced below.

One repair outside #91's scope rode this branch: the §1.3 reflow in `a7176e0` had removed the phrase `automation/issue_validator.py` parses, breaking every issue creation, and the branch could not merge without shipping that regression to `main` and `dev`. It is recorded as deviation 8 and delivered in §2.

## 2. What shipped, by document

There is no spec, so there are no numbered steps. The table is organised by document, with the ACs each one satisfies.

| Document | Delivered | ACs |
| --- | --- | --- |
| `docs/DEVELOPMENT_STANDARDS.md` | §1.1 close-out bullet rewritten to match the skill; §1.4 carve-out sentence rewritten and the authorization set narrowed to branches on `origin`; §1.5 requires exactly one `Status:` field; §2.2 `main` block separates a release-carrying merge from a `chore/*` merge and adds `chore/*` as a source; §2.3 rewritten for a workflow in which no working branch is pushed; §2.8's two lines reconciled and an unclosed backtick fixed | AC1, AC2, AC7, AC8, AC11 |
| `CLAUDE.md` | § Critical Rules no longer cites a DR1a that does not exist there — the carve-out is stated and resolves to both preambles; the authorization-points entry narrowed to a branch on `origin` | AC9 |
| `.claude/skills/closeout/SKILL.md` | Frontmatter description updated; P4 accepts `Approved` or `Shipped`; P5 relaxed to any status §1.5 defines; P5a added for the design artifact; new § Resume point; § The two stops replaced by § The stop; new § The closing comment. Under AC14: § Choosing the variant corrected from *"the two authorization points"* to the singular, and § The stop's answer enumeration dropped, since the answers differ by variant | AC3, AC6, AC10, AC14 |
| `.claude/skills/closeout/references/{chore,feature,hotfix}.md` | All three rewritten as step tables with a `Done when` observable per step. Every §2.x rule cited rather than restated. `feature.md` retains its four-item rationale block; the other two carry none. Under AC14: the six merge steps' citations made uniform, and `feature.md` step 1 gained the "before any merge" clause the other two already carried | AC3, AC4, AC5, AC6, AC14 |
| `docs/dev/design/`, `docs/dev/specs/` | Two specs advanced `Approved` → `Shipped`; four recons `Active` → `Shipped`; one `Superseded`; every stale Disposition repointed at the artifact it produced | AC11, AC12 |
| `docs/DEVELOPMENT_STANDARDS.md` §1.3, `automation/**` | §1.3's discriminator line restored to a parseable form and the pair renamed `bug`/`enhancement` → `defect`/`gap`, with the defect-versus-gap test stated for the first time; `DISCRIMINATOR_PHRASE` retired in favour of `discriminator pair`; eleven JSON fixtures, the standards fixture and four assertions in `issue_validator_test.py` updated to the new pair; one regression test added over the live parse | n/a — see deviation 8 |
| `docs/archive/` | Nine artifacts moved out of the live directories | AC13 |

## 3. Acceptance criteria

Every AC on **issue #91**, checked against the delivered documents. Verified by reading the files in the working tree on 20260825; a third-party read of the same tree confirmed each row independently.

| AC | Status | Evidence |
| --- | --- | --- |
| AC1 | Met | `docs/DEVELOPMENT_STANDARDS.md` §2.3. Every step of the delete rule is performable: no branch type is pushed, so no remote delete is ordered. The pushed-branch case is named as an exception and carries its own authorization point |
| AC2 | Met | §2.2 `main` block, §2.2 `chore/*` block and §2.8's line each read alone give one answer: a `chore/*` merge to `main` takes no bump, no `CHANGELOG.md` entry, no tag and no Release. The `main` block's source list now includes `chore/*` |
| AC3 | Met | `SKILL.md` P4 accepts `Approved` or `Shipped`; § Resume point defines the resume state as read from the repository; every step in all three reference files carries a `Done when` observable. No file directs a commit that blocks re-entry |
| AC4 | Met | No reference file explains a §2.x rule. `--no-ff`, the delete, the restart and the bump magnitude are citations. The reconciliation record required by the second clause is AC14's walk-through, performed 20260827, which also closed the citation gaps that rule had left in the merge steps — see deviation 9 |
| AC5 | Met | `feature.md` § Why this order carries exactly the four fragments: version recorded before bumped, PR number unavailable, restart before the PR, branch deleted early. `chore.md` and `hotfix.md` carry no rationale block |
| AC6 | Met | `SKILL.md` § The stop and § The closing comment each state their subject once. No reference file repeats either; the three `## Finishing` blocks are gone |
| AC7 | Met | §1.1's close-out bullet names the invocation the skill accepts and names posting the comment and closing the issue as Ray's |
| AC8 | Met | §1.4's carve-out reads as plain English. §1.4 and §2.6 read separately give the same answer on the post-merge restart |
| AC9 | Met | Every citation in `CLAUDE.md` § Critical Rules resolves. The DR1a citation is replaced by a statement resolving to both documents' preambles. The stop-and-surface entry states that its full statement lives in § Critical Rules rather than citing elsewhere |
| AC10 | Met | `SKILL.md` P5a reads the spec's `**Design study:**` field and checks the artifact exists with a status §1.5 defines. Step 1 of all three variants sets it to `Shipped` alongside the spec |
| AC11 | Met | `grep -c "^\*\*Status:\*\*"` returns 1 for every artifact in `docs/dev/{design,specs,results}/`. Each status matches whether its work has shipped: six specs `Shipped`, four recons `Shipped`, one `Superseded`, `DESIGN_CLOSEOUT_STANDARDIZATION.md` `Active` because #91 is live |
| AC12 | Met | No Disposition, Open Questions table or Promoted-to line describes pending work that is not pending. `RECON_STEPS_AUTHORIZATION_POINTS.md` §5's blank table removed and §6 rewritten; `RECON_CYCLE_MECHANICS.md`, `RECON_CLOSEOUT_PERFORMS.md` and `RECON_CYCLE_CLOSEOUT.md` Dispositions repointed |
| AC13 | Met | No retired name form remains in the three live directories. Nine artifacts moved to `docs/archive/`: three specs, two design artifacts, two session handoffs, and the `CYCLE_CLOSEOUT` spec and results pair. Dispositions citing moved artifacts repointed; citations inside findings left as written — see §4 |
| AC14 | Met | Performed by Ray with Spanner on 20260827 against `DESIGN_CLOSEOUT_STANDARDIZATION.md` §6, row by row, and against the pre-rewrite reference files at `4262951` to test the census itself for completeness. All 23 rows are disposed as §6 directs — four by a different route than it specifies, each in its own direction, the clearest being `hotfix.md` step 5, where a D1 rationale became a `Done when` observable rather than being deleted. Three rationale fragments §6 never classified were found — the old `chore.md:3` and `feature.md:3` preambles and the `feature.md:17` tail — each already correctly disposed across `SKILL.md` and the Why-this-order block, so nothing was lost. Two defects were found and fixed: `SKILL.md` § Choosing the variant still read *"the two authorization points"* against § The stop's *"exactly one"*, and this artifact existed twice, the second a stale pre-deviation-8 copy under `docs/archive/results/`. The walk-through's own record is `afb11d9`, the commit carrying these corrections; deviations 9 and 10 carry its two out-of-scope findings |

## 4. Deviations

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | No spec was written; the issue's ACs governed directly | The work edits the governing documents rather than implementing against them, and its acceptance method is a walk-through, not a mechanical check. `RECON_CLOSEOUT_PERFORMS.md` F15 already establishes issue ACs as the set close-out verifies | Ray, 20260825 |
| 2 | Re-entry (AC3) resolved by reading repository state rather than by moving the artifact commit after the last stop | The alternative breaks §2.2 — those artifacts are committed on the branch so they reach `main` and `dev` through the merge — and covers only the declined-prompt case, leaving a crash mid-run un-re-enterable | Ray, 20260825 (D1) |
| 3 | **§1.4's authorization set narrowed: deleting a branch is an authorization point only where the branch exists on `origin`** | Follows from AC1. Once no working branch is pushed, a local delete is not a GitHub object deletion under §1.4's own definition. Close-out therefore crosses one authorization point, not two. **This is the widest deviation — it changes a rule the issue did not name** | Ray, 20260825 (D2) |
| 4 | §2.2's `main` block source list corrected, which the design study did not record | *"Receives merges only from `dev` or `hotfix/*`"* excluded `chore/*` while the `chore/*` block sent chore branches there — a fourth reading of the rule AC2 covers | Ray, 20260825 |
| 5 | §1.5 gained an exactly-one-`Status:`-field rule | AC11 requires each artifact to carry a status §1.5 defines, and §1.5 did not say how many were permitted. Two archived specs carried five | Ray, 20260825 |
| 6 | Problems 5–8 were evidenced by a third-party review session rather than a filed design artifact | Ray's decision that no further design documents enter the project for this work. The file:line evidence for each is carried in the issue body instead | Ray, 20260825 |
| 7 | Citations to moved artifacts were repathed only where they are Dispositions or pointers, not where they appear inside findings | A finding records where a thing was when the finding was made. Repathing `RECON_RELEASE_CHECK_RELOCATION.md` F14 — an inventory of where citations were — would falsify the finding it records | Ray, 20260825 |
| 8 | **The §1.3 discriminator repair and the `defect`/`gap` rename rode this branch, and neither is an AC on #91** | `a7176e0` reflowed §1.3 and removed the literal phrase `automation/issue_validator.py:32` parses, so `parse_type_labels` aborted on every input. Because that module computes its label pair at import, the whole of `issue_validator_test.py` failed to import — `pytest automation/` was red, not merely the CLI. `main` and `dev` were clean, so merging this branch without the repair would have shipped the regression to both. The rename was folded in because it edits the same sentence: `bug` is the name of a native GitHub issue type and `enhancement` is a GitHub default label, and `Repository.issueTypes` is null for this repository, so labels are the only discriminator mechanism available. `automation/**` is `chore/*`-eligible under §2.2, so no branch-type escalation follows | Ray, 20260826 |
| 9 | **The six merge steps' citations were made uniform, dropping §2.1 in favour of §2.2** | Found by AC14's walk-through. `--no-ff` was performed at six merge steps and cited at two; routing was cited as §2.1 at two steps, §2.2 at one, and nowhere at the other three. §2.1's table and §2.2's per-type blocks state the same routing fact, and §2.2 is the fuller home — it carries the release-versus-`chore/*` distinction as well — so every merge step now reads `— §2.2, §2.3`. This is AC4's own rule applied to the steps it had missed, not a new rule | Ray, 20260827 |
| 10 | **`docs/archive/results/CLOSEOUT_STANDARDIZATION_RESULTS.md` deleted as a stale duplicate of this artifact** | Found by AC14's walk-through. Committed in `a9396fb`, it predates deviation 8 and still lists the §1.3 regression as an open hazard, so the two copies disagree about whether a shipped fix shipped. AC11 reads `docs/dev/{design,specs,results}/` and AC13 reads the same three directories for retired name forms; neither can see a live artifact duplicated into `docs/archive/`. Deleting a local file is not a §1.4 authorization point | Ray, 20260827 |

## 5. Verification

- **Test suite:** `pytest` → **934 passed, 0 failed** — equal to the baseline recorded in `CLOSEOUT_PERFORMS_RESULTS.md` §5, and expected: no file under `workmain/**` or `tests/**` was touched. `pytest automation/` → **37 passed, 0 failed**, against a baseline of 36, the `+1` being the regression test added under deviation 8 over the live §1.3 parse.
- **Live verification:** every AC row in §3 was checked by reading the delivered files in the working tree on 20260825, independently of the person who wrote them. `markdownlint` should be run over the four modified `.md` files under `.claude/` and the two governing documents before the merge — §1.4's new sub-bullet indentation was corrected once already for `MD007`.
- **Regression guard:** `parse_type_labels` against the live `docs/DEVELOPMENT_STANDARDS.md` now returns `['defect', 'gap']`, asserted by test. The coupling that broke was a prose document parsed as a configuration file with nothing checking it; the repair without that test would have left the same failure available to the next reflow.
- **Daemon restart:** `n/a`. §2.6 requires no restart on `chore/*`, which changes no application code.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #92 | Proving the re-entry and delete behaviours this issue specifies, on all three branch types, plus the design-artifact preflight row | Blocked by this issue by design; #92 exists for it |
| — | `SKILL.md` P5 derives the results-artifact path from the spec. An issue with no spec — such as this one — has no derivable path, so close-out cannot run against it | Surfaced by this issue being spec-less. Not a defect in what shipped |
| — | `CLOSEOUT_PERFORMS_SPEC.md` DR10 describes `SKILL.md` as carrying *"the two stops"*. Now one | Deliberately not edited. It is a `Shipped` spec — a record of what was approved, not a description of current state, and §1.2's surgical-edit rule exists to stop shipped specs being rewritten to match later work |
| — | Nothing checks whether a live artifact has been duplicated into `docs/archive/`. AC11 and AC13 both read only the three live directories, so the two trees are never compared | Surfaced by deviation 10, which found exactly that and only by hand. Proposed as a preflight row or a `comm` over the two trees; not added here |
| — | §1.5 has no rule distinguishing a citation inside a finding from a Disposition or pointer when an artifact is archived. Deviation 7 decided it once; the next archiving will decide it again | Proposed as a §1.5 addition, not made here |
