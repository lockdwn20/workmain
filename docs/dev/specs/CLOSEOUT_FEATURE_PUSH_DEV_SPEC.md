# /closeout feature variant pushes dev after the bump — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261005
**Branch:** `chore/closeout-feature-push-dev` (from `main`)
**Target release:** n/a — `chore/*` carries no release (`docs/DEVELOPMENT_STANDARDS.md` §2.2)
**Originating item:** Ray request, 20261005 — surfaced while closing issue #172
**Design study:** `n/a` — direct path, no recon was run

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261005 | Ray | Fix by adding "and pushed" to step 4, with no new issue. | Decided |
| 20261005 | Spanner | The push follows the integrity check: pushing before it passes would publish the mismatch #172 exists to stop. The Done when gains `dev` equal to `origin/dev`, so a re-run can tell the push happened. | Decided |

---

## 1. Scope

**In scope:** step 4 of `.claude/skills/closeout/references/feature.md`.

**Out of scope:** every other step and variant. `hotfix.md` merges `dev` at step 7, which pushes it, so it has no gap.

## 3. Design rules

- **DR1 —** Step 3 pushes `dev` before the bump, and step 7 opens a PR from `origin/dev`. Nothing between them pushes the bump commit, so step 4 must.
- **DR2 —** The push comes after the integrity check passes (`CLOSEOUT_BUMP_INTEGRITY_SPEC.md` DR1), never before.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Replace the step 4 text `committed on \`dev\`` with `committed on \`dev\` and, once the check below passes, pushed`. Replace the Done when ending `exits 0 on \`dev\`` with `exits 0 on \`dev\`, and \`dev\` equals \`origin/dev\`` | `.claude/skills/closeout/references/feature.md` |

### Authorization points

None.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Step 4 pushes the bump commit, and only after the integrity check passes, so a bump that fails the check is never published; a re-run can tell the push happened | Stated reading by Ray of step 4 in `.claude/skills/closeout/references/feature.md`, read for the push, its ordering after the check, and `dev` equal to `origin/dev` in the Done when |

## 6. Test plan

No file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes. Close-out runs the suites regardless.

## 7. Risks and rollback

Revert the one commit. Nothing else depends on the wording.
