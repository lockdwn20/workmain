# Deviation Record and Self-Resolution Passages — Implementation Results

**Status:** Active
**Author:** Spanner (Role 1)
**Date:** 20261027
**Spec:** `../specs/DEVIATION_RECORD_SPEC.md`
**Released as:** n/a — `chore/*`

---

## 1. Summary

Complete. The results template's §4 records how each departure was handled, with `Step stopped at` taking the step, `within approved meaning` or `none`. The three standards passages issue #242 names are rewritten or removed, the search's further hits are rewritten, and `references/spanner.md` bounds Role 1's judgment when it implements a direct-path spec.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | Results §4: one definition of a departure, three `Step stopped at` values, the new columns (`a697db6`) | `docs/dev/results/_TEMPLATE_RESULTS.md` | none |
| 2 | §1.1 and §2.2 rewritten, §2.4's deviation sentence and §6.4 removed (`468d562`) | `docs/DEVELOPMENT_STANDARDS.md` | none |
| 3 | Design rules no longer stand in for a stop (`bc78168`) | `docs/dev/specs/_TEMPLATE_SPEC.md` | none |
| 4 | Role 1's direct-path implementation rule (`b926718`) | `.claude/skills/session-start/references/spanner.md` | none |
| 5 | Study disposition and this artifact | `docs/dev/design/DESIGN_DEVIATION_RECORD.md`, `docs/dev/results/DEVIATION_RECORD_RESULTS.md` | none |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | Stated reading by Ray, 20261027 |
| AC1.2 | Met | `grep -c 'Departure or ambiguity . Step stopped at . Resolution . Resolved by' docs/dev/results/_TEMPLATE_RESULTS.md` printed `1`; `grep -c 'Approved by' docs/dev/results/_TEMPLATE_RESULTS.md` printed `0`, 20261027 |
| AC2.1 | Met | Stated reading by Ray, 20261027 |
| AC3.1 | Met | Stated reading by Ray, 20261027 |
| AC4.1 | Met | Stated reading by Ray, 20261027 |
| AC4.2 | Met | `grep -rni -e 'document the deviation' -e 'note any deviations' -e 'falls back on' CLAUDE.md docs/DEVELOPMENT_STANDARDS.md docs/AI_SETTINGS_GUIDE.md .claude/ docs/dev/*/_TEMPLATE_*.md` returned nothing (exit 1), 20261027 |
| AC4.3 | Met | Stated reading by Ray, 20261027 |
| AC5.1 | Met | `pytest` exit 0, `pytest automation/` exit 0, 20261027 — § 5 Verification |

## 4. Deviations from spec

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |

None. Every edit was applied as quoted, by a script that read each quoted block from the spec and refused any block that did not occur exactly once in its file.

## 5. Verification

- **Test suite:** 1541 passed, 0 failed, 0 skipped (baseline: 1541 passed, 0 failed, 0 skipped, from the most recent `CHANGELOG.md` entry). `pytest automation/`: 58 passed, 0 failed, 0 skipped. Both run 20261027 at `b926718`.
- **Live verification:** none needed; the change is to documents only.
- **Daemon restart:** none — `chore/*` (`docs/DEVELOPMENT_STANDARDS.md` §2.6).

### Search hits

The search, its terms and its scope are the design study's §2. Each hit's finding is its §3 and its adjudication its §4.

| Hit | Adjudication | Delivered by |
| --- | --- | --- |
| Results template §4 (study F1) | Rewritten | Step 1 |
| `docs/DEVELOPMENT_STANDARDS.md` §1.1 "What the direct path trades" (F2) | Rewritten | Step 2 |
| §2.2 hotfix-into-feature exception (F3) | Rewritten | Step 2 |
| §6.4 (F4) | Removed | Step 2 |
| §2.4 commit body (F5) | Rewritten: sentence removed | Step 2 |
| Spec template §3 design rules (F6) | Rewritten | Step 3 |
| `references/spanner.md` § Working rules (F7, F8) | Rewritten: two rules limited, one rule added | Step 4 |
| §1.4 Steps and the spec template's "no approval stop" | Read, left unchanged (study §3.2) | — |
| Spec template Decision Log `Anvil` row | Read, left unchanged (study §3.2) | — |
| `.claude/skills/closeout/SKILL.md` § Anything not covered here | Read, left unchanged (study §3.2) | — |
| `docs/AI_SETTINGS_GUIDE.md` model-change stop | Read, left unchanged (study §3.2) | — |
| `CLAUDE.md` § Common Pitfalls, standard-versus-practice | Read, left unchanged (study §3.2) | — |
| Results template §3 unmet-criterion carry | Read, left unchanged (study §3.2) | — |

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #245 | Whether a direct-path spec states what each passage must say instead of its exact text. | Ray deferred it until #243's first reviewed direct-path cycles supply the evidence. |
| #243 body | Carries the `within approved meaning` check and #245's evidence. | #243's own work. |
| #242 body | The fourth criterion is restated as AC4.1 (spec Decision Log). | The issue body is edited at close-out. |
