# Framework Mechanism First — Implementation Results

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20261014
**Spec:** `../specs/FRAMEWORK_MECHANISM_FIRST_SPEC.md`
**Released as:** n/a — `chore/*`

---

## 1. Summary

Complete. `docs/DEVELOPMENT_STANDARDS.md` has a new §3.8, *Framework mechanisms first*, applied verbatim from the spec. Caliper's criterion 6 in `.claude/skills/session-start/SKILL.md` § Role 2 now asks whether a spec writes its own version of a mechanism §3.8 says to use, and cites §3.8 for the rule.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | §3.8 inserted after §3.7, before the `---` closing §3 (`4b1b506`) | `docs/DEVELOPMENT_STANDARDS.md` | +0 |
| 2 | Criterion 6 replaced with the spec's quoted text (`1271cb2`) | `.claude/skills/session-start/SKILL.md` | +0 |
| 3 | This artifact | `docs/dev/results/FRAMEWORK_MECHANISM_FIRST_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | Ray reading of `docs/DEVELOPMENT_STANDARDS.md` §3.8 |
| AC2.1 | Met | Ray reading of `.claude/skills/session-start/SKILL.md` § Role 2 criterion 6 |
| AC3.1 | Met | the grep and diff output are in §5 |

## 4. Deviations from spec

None.

## 5. Verification

- **Test suite:** 1316 passed, 0 failed, 0 skipped (baseline: 1316 passed, 0 failed, 0 skipped, v1.48.0 `CHANGELOG.md`), run at close-out on the branch tip. `pytest automation/` not run: the branch changes no path under `automation/`.
- **Live verification:** n/a — the branch changes documents only; no command or service behaviour changed.
- **Daemon restart:** n/a — `chore/*`, which `docs/DEVELOPMENT_STANDARDS.md` §2.6 requires no restart for.
- **AC3.1 grep**, `git grep -n -i -e framework -e mechanism -e '§3\.8' -- docs/DEVELOPMENT_STANDARDS.md .claude CLAUDE.md`, at `1271cb2`:

  ```text
  .claude/skills/session-start/SKILL.md:81:6. Does this spec introduce a new path where an existing service, orchestrator, or workflow already covers the case, or write its own version of a mechanism `docs/DEVELOPMENT_STANDARDS.md` §3.8 says to use?
  docs/DEVELOPMENT_STANDARDS.md:404:### 3.8 Framework mechanisms first
  docs/DEVELOPMENT_STANDARDS.md:406:- **Use the mechanism Python's standard library, Click, Rich or SQLAlchemy provides before writing your own.** Where two of them do the job, either meets this rule, unless another section names one.
  docs/DEVELOPMENT_STANDARDS.md:407:- **A spec that writes its own records why.** Its Decision Log names the mechanism it set aside and the reason it does not fit.
  ```

- **AC3.1 diff**, `git diff --stat main...HEAD -- docs/DEVELOPMENT_STANDARDS.md .claude CLAUDE.md`, at `1271cb2`:

  ```text
   .claude/skills/session-start/SKILL.md |  2 +-
   docs/DEVELOPMENT_STANDARDS.md         | 13 +++++++++++++
   2 files changed, 14 insertions(+), 1 deletion(-)
  ```

## 6. Follow-ups

None.
