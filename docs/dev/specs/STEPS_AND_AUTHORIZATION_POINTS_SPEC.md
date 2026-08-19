# Steps and Authorization Points — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20260818
**Branch:** `chore/issue-86-steps-authorization` (from `main`, merges to `main` and `dev`)
**Target release:** none — `chore/*` carries no version bump, no `CHANGELOG.md` entry, no tag, no Release
**Originating item:** Issue #86, child of #80
**Design study:** `docs/dev/design/RECON_STEPS_AUTHORIZATION_POINTS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260814 | Ray | §4 of a spec is **Steps**, not gates. Approval attaches to irreversible *actions*. Recorded in `TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md:20`, which adopted the shape ahead of codification | This spec codifies it. #81 and #82 are the working precedents |
| 20260818 | Ray | **Ownership test agreed.** `DEVELOPMENT_STANDARDS.md` owns any rule governing *how work is built*. `CLAUDE.md` owns *who does what*, *what this project is*, and *domain decisions* | Adopted as DR1. Resolves every duplication in recon F14–F25 by one test rather than case-by-case |
| 20260818 | Ray | **Q4 — fix it.** The F26 collision between "restarting a live service" as an authorization point and §2.6's mandatory post-merge restart | Authorization is scoped to service state changes *outside* the documented post-merge restart, with the carve-out named in §1.4. §2.6 and §2.8 are not edited — a fix there would have weakened a rule added after the Item #58 false regression, which is the circularity Ray's rule 3 forbids |
| 20260818 | Ray | **Q3 — `_TEMPLATE_RESULTS.md` is in scope**, though no #86 acceptance criterion names it | Declared here rather than left implicit, so Caliper's criterion 4 sees a stated scope extension. Leaving it would have the results template reporting "by gate" against specs that no longer have gates |
| 20260818 | Ray | **Q5 — the unmerged recon rides this branch.** `docs/dev/design/RECON_CYCLE_MECHANICS.md` exists only on local `chore/cycle-mechanics-recon`, and `ISSUE_CREATION_VALIDATION_SPEC.md:9` cites it from a spec already merged to `main` | Step 6. The citation is broken on both integration branches today |
| 20260818 | Ray | **Q6 — the two stale `Status: Approved` specs are advanced here.** #81 and #82 shipped without their status advancing (recon F29, F30) | Step 6. #83 owns the close-out *process* that would have caught it; two stale values are simply wrong now and do not wait on it |
| 20260818 | Ray | Recon carried findings with no dispositions, because §1.1 forbids suggestions in a recon. Information was nearly lost to the absence of a mechanism | Where no artifact can yet hold a decision, it goes in this Decision Log rather than being dropped. This row is that rule applied to itself |
| 20260818 | Spanner | Recon's first pass missed `DEVELOPMENT_STANDARDS.md:185`, found by a later word-boundary sweep and recorded as F35 | Every acceptance criterion in §5 derives its own set from a command. No AC is checked against a list transcribed from the recon |

---

## 1. Scope

**In scope** — four files:

- `CLAUDE.md` — § Critical Rules gate bullet, Role 3's residual `Gate 1`, § Common Pitfalls
  duplication, the OQ4 historical gate citation.
- `docs/DEVELOPMENT_STANDARDS.md` — preamble ownership sentence, §1.1 pipeline and bullets,
  §1.3 split rule, §2.2, §2.4, §2.7, §4.5, §6.3, §6.4, §7, plus a new §1.4 defining steps
  and authorization points.
- `docs/dev/specs/_TEMPLATE_SPEC.md` — §3, §4, §7.
- `docs/dev/results/_TEMPLATE_RESULTS.md` — §2, §3.

Plus two housekeeping actions carried by Decision Log Q5 and Q6: merging
`chore/cycle-mechanics-recon`, and advancing two `Status:` values.

**Out of scope:**

- **The four `Status: Shipped` specs and both session handoffs.** They are historical
  records of work performed under gate discipline. Rewriting them would falsify the record
  of how that work actually ran.
- **`workmain/**`, `tests/**`, `config/*`, `templates/*`.** No application behaviour
  changes. Recon F33 establishes that `.github/ISSUE_TEMPLATE/` and
  `automation/issue_validator.py` carry neither vocabulary, and F34 that `.claude/` does
  not exist.
- **The close-out mechanism.** #83's deliverable. §1.1's pipeline terminates at
  `IMPLEMENTATION` here and #83 extends it — this spec deliberately does not add a
  close-out stage it cannot define.
- **`CHANGELOG.md`.** Append-only historical record; recon N2 leaves it unread and nothing
  here depends on it.
- **Any change to §2.6 or §2.8.** See DR6.

## 2. Verified current state

All claims verified against source on 20260818 at recon time; findings cited as `Fn` are
from `docs/dev/design/RECON_STEPS_AUTHORIZATION_POINTS.md`.

| Claim | Evidence (file:line) | Recon |
| --- | --- | --- |
| Gate rule stated in CLAUDE.md § Critical Rules | `CLAUDE.md:118-120` | F1 |
| Role 3 says "Gate 1" at `:48` but "the current step" at `:52`; the `:52` edit was #82's, documented as covered by no AC | `CLAUDE.md:48`, `:52`; `ISSUE_CREATION_VALIDATION_SPEC.md:89` | F2, F3 |
| Preamble assigns gate discipline to CLAUDE.md | `docs/DEVELOPMENT_STANDARDS.md:3-4` | F4 |
| Pipeline reads `… → IMPLEMENTATION → GATE REVIEW → COMMIT` | `docs/DEVELOPMENT_STANDARDS.md:19` | F5 |
| §1.1 bullets: "gate by gate"; "human approval at every gate" | `docs/DEVELOPMENT_STANDARDS.md:27-28` | F6 |
| §1.3 split rule ends "never one issue spanning several gates"; the independent-verifiability sentence sits immediately above it | `docs/DEVELOPMENT_STANDARDS.md:52-53` | F7, F27 |
| §2.2 hotfix→feature exception says "at Gate 0" | `docs/DEVELOPMENT_STANDARDS.md:118` | F8 |
| §2.4 commit-subject rule worked in `Gate 3 of 7` terms | `docs/DEVELOPMENT_STANDARDS.md:139-140` | F9 |
| §2.7 routes branch type by "phase/multi-gate" | `docs/DEVELOPMENT_STANDARDS.md:185` | F35 |
| §4.5 states the migration rule with the same "the gate is the approval" clause as `CLAUDE.md:120` | `docs/DEVELOPMENT_STANDARDS.md:350-351` | F14 |
| §6.4 ends "does not stop a gate" | `docs/DEVELOPMENT_STANDARDS.md:598` | F10 |
| Spec template §3, §4, §7 carry gate structure | `_TEMPLATE_SPEC.md:65`, `:67-78`, `:103` | F11 |
| Results template §2 titled "What shipped, by gate"; §3 refers to a gate | `_TEMPLATE_RESULTS.md:27-29`, `:50` | F12 |
| Two historical gate citations exist that are facts, not process rules | `docs/DEVELOPMENT_STANDARDS.md:57`; `CLAUDE.md:223` | §3.1 census |
| Both documents assert "nothing is duplicated" and both are false | `CLAUDE.md:7`; `docs/DEVELOPMENT_STANDARDS.md:7` | §3.2 |
| A set of process rules is stated in both documents, enumerated at recon §3.2 | `docs/dev/design/RECON_STEPS_AUTHORIZATION_POINTS.md` §3.2 | F14–F25 |
| Stop-and-surface stated in three places, two tied to a boundary | `CLAUDE.md:121`, `:50-55`; `_TEMPLATE_SPEC.md:65` | F28 |
| `#81` and `#82` specs already use `## 4. Steps` | `TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md:108`; `ISSUE_CREATION_VALIDATION_SPEC.md:162` | F13 |
| Those two specs are `Status: Approved` despite having shipped and merged | `grep "^\*\*Status:\*\*" docs/dev/specs/*.md`; `git log origin/main..origin/dev` | F29, F30 |
| `RECON_CYCLE_MECHANICS.md` is on an unmerged local branch and cited by a merged spec | `git branch -a`; `ISSUE_CREATION_VALIDATION_SPEC.md:9` | F31 |
| `origin/main` and `origin/dev` are content-identical | `git diff origin/main origin/dev` empty | F32 |

## 3. Design rules

- **DR1 — Ownership test.** `docs/DEVELOPMENT_STANDARDS.md` owns any rule governing *how
  work is built* — process, git, code, database, CLI, testing, file placement. `CLAUDE.md`
  owns *who does what* (the three-role model), *what this project is* (stack,
  architecture), and *domain decisions* (tag system, time format, trigger terminology,
  write-path map). When a rule could plausibly sit in either, it is a "how work is built"
  rule and goes to `DEVELOPMENT_STANDARDS.md`.

- **DR2 — A pointer is not a duplicate.** One document may name another's rule and cite the
  section, provided it states no part of the rule's content. `§4.6` already does this in
  the CLAUDE.md direction and is the precedent. A sentence that would still be actionable
  with the cited section deleted is a duplicate, not a pointer.

- **DR3 — Steps.** Ordered work inside a spec. Committed individually, reviewable and
  revertible individually. **No approval stop.** A step ends with a commit, not with a
  request to continue.

- **DR4 — Authorization points.** Attached to specific *actions* that are irreversible or
  reach outside the working tree. This is a property of the action, so it does not scale
  with scope: a one-step issue can contain one and a twenty-step issue can contain none. An
  authorization point is a hard stop — state what is about to happen, then wait for Ray's
  explicit approval.

- **DR5 — The authorization set.** Executing a DB migration; deleting a GitHub object
  (issue, label, milestone, branch, release); merging to `main`; force-pushing any branch;
  changing the run state of a live service beyond DR6's carve-out. Anything not on this
  list is a step.

- **DR6 — The post-merge restart is not an authorization point.** §2.6 requires restarting
  `workmain-notify.service` after a merge to `dev`, and §2.8 forbids reporting a merge as
  deployed without it. That restart is carried by the approval for the merge itself. DR5
  covers service state changes *other than* the documented post-merge restart. §2.6 and
  §2.8 are not edited by this spec.

- **DR7 — The split test.** Split into sub-issues only where each piece leaves the
  repository in a coherent state its own acceptance criteria can verify. Where steps are
  strictly sequential and individually meaningless, they stay inline as steps — an issue
  whose closure leaves the repository worse than before is already forbidden by §1.3.

- **DR8 — Stop and surface is unconditional.** It is triggered by encountering something
  the spec does not cover or that requires a design decision — not by reaching a boundary.
  It must be stated without reference to steps, gates, or any position in a sequence.

- **DR9 — Historical citations are facts, not rules.** Where an existing document cites a
  gate as part of a historical record, the citation is reworded to name the release instead
  of the gate. No information is lost — the version is the durable identifier — and the
  acceptance criteria can then use an unqualified zero-hit sweep.

When something is not covered here, **STOP and surface to Ray**. No self-resolution, no
scope adjustment, no in-flow architecture calls.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | New `§1.4 Steps and authorization points` carrying DR3–DR6, the authorization set, and the DR6 carve-out named in place. Preamble ownership sentence rewritten to DR1 | `docs/DEVELOPMENT_STANDARDS.md` |
| 2 | §1.1 pipeline terminates at `IMPLEMENTATION`; §1.1 bullets reworded to steps with a §1.4 pointer; §1.3 split rule replaced by DR7; §2.2, §2.4, §2.7, §6.4 reworded to step vocabulary; §4.5 keeps the migration rule as a §1.4 pointer per DR2; §1.3 and §6.3 absorb the rules arriving from `CLAUDE.md` in step 3 | `docs/DEVELOPMENT_STANDARDS.md` |
| 3 | Gate bullet removed from § Critical Rules and replaced by a §1.4 pointer; Role 3 `:48` reworded; § Common Pitfalls reduced to the bullets with no `DEVELOPMENT_STANDARDS.md` counterpart; every other duplicated rule removed per DR1; OQ4 citation reworded per DR9; the "nothing is duplicated" claims in both preambles left standing and now true | `CLAUDE.md` |
| 4 | §3 stop-and-surface restated per DR8 as a pointer to `CLAUDE.md` Role 3; §4 retitled **Steps** with a `Step / Deliverable / Files` table and an **Authorization points** subsection; §7 reworded to steps | `docs/dev/specs/_TEMPLATE_SPEC.md` |
| 5 | §2 retitled "What shipped, by step" with a `Step / Delivered / Files changed / Tests` table; §3 reworded | `docs/dev/results/_TEMPLATE_RESULTS.md` |
| 6 | `chore/cycle-mechanics-recon` merged into this branch, restoring `RECON_CYCLE_MECHANICS.md` and fixing #82's broken citation; `Status:` advanced to `Shipped` on `TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md` and `ISSUE_CREATION_VALIDATION_SPEC.md` | `docs/dev/design/RECON_CYCLE_MECHANICS.md`, two spec headers |
| 7 | Full acceptance sweep per §5, then merge | — |

### Authorization points

This spec contains **one**, at step 7: the merge to `main`. It carries no DB migration, no
GitHub object deletion, no force push, and no service state change. Per DR3, steps 1–6
proceed without stopping.

Per §2.2 this is a `chore/*` branch — it merges to `main` and `dev` with no version bump,
no `CHANGELOG.md` entry, no tag, and no Release.

## 5. Acceptance criteria

Every criterion derives its own set from a command. None is checked against a list
transcribed from the recon.

| AC | Criterion | How it is checked | Issue AC |
| --- | --- | --- | --- |
| AC1 | No gate vocabulary survives in the four in-scope files | `grep -inE '\bgates?\b' CLAUDE.md docs/DEVELOPMENT_STANDARDS.md docs/dev/specs/_TEMPLATE_SPEC.md docs/dev/results/_TEMPLATE_RESULTS.md` returns zero hits | 2, 3, 5 |
| AC2 | The historical citations were reworded, not deleted — the underlying facts survive | `grep -n "v1.24.0" CLAUDE.md docs/DEVELOPMENT_STANDARDS.md` still returns both the OQ4 row and the §1.3 Item 32 narrative | 1 |
| AC3 | `DEVELOPMENT_STANDARDS.md` defines both concepts in one section, and defines authorization by irreversibility rather than by position | `grep -n "^### 1.4" docs/DEVELOPMENT_STANDARDS.md` returns one hit; that section contains the words `irreversible` and `reach outside the working tree`, and contains neither `sequence` nor `position` as the defining property | 2 |
| AC4 | The DB-migration rule survives, expressed as an authorization point | `grep -n "migration" docs/DEVELOPMENT_STANDARDS.md` returns the §4.5 rule; §4.5 contains a `§1.4` citation and does **not** restate the definition — verified by DR2's test, that the sentence is not actionable with §1.4 deleted | 3 |
| AC5 | A stated split test exists, keyed on independent verifiability | §1.3 contains the DR7 sentence; `grep -n "independently verifiable" docs/DEVELOPMENT_STANDARDS.md` returns a hit inside §1.3 | 4 |
| AC6 | Spec template §4 matches the revised standard and matches the two working precedents | `grep -n "^## 4. Steps" docs/dev/specs/_TEMPLATE_SPEC.md docs/dev/specs/TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md docs/dev/specs/ISSUE_CREATION_VALIDATION_SPEC.md` returns three hits | 5 |
| AC7 | Stop-and-surface is retained and stated independent of any boundary | `CLAUDE.md` Role 3 retains the four-step procedure; neither it nor `CLAUDE.md:121` contains `gate`, `step boundary`, or `at the gate` — covered by AC1's sweep plus `grep -in "step boundary" CLAUDE.md` returning zero | 6 |
| AC8 | No process rule is stated in both documents | Every rule listed in recon §3.2 F14–F25 appears in exactly one of the two files. Checked per rule with a distinguishing phrase; e.g. `grep -c "own hotfix" CLAUDE.md docs/DEVELOPMENT_STANDARDS.md` returns `0` and `1` | 7, 1 |
| AC9 | The `CLAUDE.md` § Common Pitfalls bullets that survive are exactly those with no counterpart in `DEVELOPMENT_STANDARDS.md` | For each surviving bullet, its distinguishing phrase returns zero hits in `docs/DEVELOPMENT_STANDARDS.md` | 7 |
| AC10 | #82's design-study citation resolves | `test -f docs/dev/design/RECON_CYCLE_MECHANICS.md` succeeds on this branch, and the path matches `ISSUE_CREATION_VALIDATION_SPEC.md:9` | — (Q5) |
| AC11 | No spec is `Status: Approved` while its issue is closed | `grep "^\*\*Status:\*\*" docs/dev/specs/*.md` returns no `Approved` for #81's or #82's spec | — (Q6) |
| AC12 | No application behaviour changed | `git diff --stat main -- workmain/ tests/ config/ templates/ automation/ .github/` is empty | — |

## 6. Test plan

No application code changes, so no test changes. The suite must be **identical** before and
after — same collected set, same result.

- Run `python -m pytest tests/` on `main` before step 1 and record the result outside this
  document; run it again after step 7 and compare. No count is transcribed here — per the
  standing rule, live counts are derived at point of use, not written into artifacts.
- `automation/` carries its own suite (`*_test.py`), reached only by an explicit path per
  §6.3. It is untouched, but run it once at step 7 to confirm F33's finding still holds.
- AC12 is the mechanical guard: if the application diff is empty, the suite cannot have
  moved.

## 7. Risks and rollback

| Risk | Blast radius | Mitigation |
| --- | --- | --- |
| A rule is deleted from `CLAUDE.md` as a duplicate when the `DEVELOPMENT_STANDARDS.md` copy says something subtly different | A standard silently weakens | Step 3 diffs each pair before deleting, and any wording the two do not share is merged into the surviving copy rather than dropped. AC8 checks presence, not equivalence — this is the one place a human read is required |
| Removing the gate bullet from `CLAUDE.md` § Critical Rules leaves the always-loaded context without the authorization list | An irreversible action is taken without a stop | The replacement is a pointer that names the trigger condition, not a bare cross-reference. DR2 permits the pointer; DR5's list stays in one place |
| Step 6's branch merge drags in unrelated commits | Scope creep on a `chore/*` branch | `chore/cycle-mechanics-recon` touches one file. Verified with `git diff --stat main...chore/cycle-mechanics-recon` before merging; if it shows anything but `RECON_CYCLE_MECHANICS.md`, stop and surface |
| The four Shipped specs still read in gate vocabulary, contradicting the new standard | A reader treats a historical spec as current guidance | Accepted deliberately — they are records of how that work ran. Their `Status: Shipped` is the signal. #83 may add an explicit banner; not this spec's call |

Rollback is per step: each is a single commit on a `chore/*` branch touching documentation
only. `git revert` of any one step restores the prior wording with no application impact.
Nothing here is irreversible before the step 7 merge.
