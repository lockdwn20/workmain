# Call Site Confirmation — Implementation Results

**Status:** Active
**Author:** Spanner (Role 1)
**Date:** 20261015
**Spec:** `../specs/CALL_SITE_CONFIRMATION_SPEC.md`
**Released as:** n/a — `chore/*`

---

## 1. Summary

Complete. `docs/DEVELOPMENT_STANDARDS.md` §1.2 has a new bullet, applied verbatim from #232, after **A contract change enumerates its call sites.**: a name-search hit is confirmed by reading what the call is made on, and a no-caller claim states that references by name were also searched. The call-sites row in `docs/dev/specs/_TEMPLATE_SPEC.md` §2 now asks for confirmed call sites and cites §1.2.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | §1.2 bullet inserted after the call-sites bullet, before the surgical-changes bullet (`d9645e2`) | `docs/DEVELOPMENT_STANDARDS.md` | +0 |
| 2 | Call-sites row evidence cell replaced with the spec's quoted text (`8c03b40`) | `docs/dev/specs/_TEMPLATE_SPEC.md` | +0 |
| 3 | This artifact | `docs/dev/results/CALL_SITE_CONFIRMATION_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | Reviewed by Ray. Both greps return 1 at `8c03b40`; output in §5 |
| AC2.1 | Met | Reviewed by Ray. Both greps return 1 at `8c03b40`; output in §5 |

## 4. Deviations from spec

None.

## 5. Verification

- **Test suite:** not run during implementation; close-out runs the suites on the branch tip. The branch changes no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/`.
- **Live verification:** n/a — the branch changes documents only; no command or service behaviour changed.
- **Daemon restart:** n/a — `chore/*`, which `docs/DEVELOPMENT_STANDARDS.md` §2.6 requires no restart for.
- **AC1.1 greps**, at `8c03b40`:

  ```text
  $ grep -cF 'A call site found by a name search is confirmed by reading what the call is made on' docs/DEVELOPMENT_STANDARDS.md
  1
  $ grep -cF 'A claim that a method has no caller states that references by name (getattr, a method passed uncalled) were also searched.' docs/DEVELOPMENT_STANDARDS.md
  1
  ```

- **AC2.1 greps**, at `8c03b40`:

  ```text
  $ grep -cF 'every `file:line` the search returns that is confirmed a call site — `docs/DEVELOPMENT_STANDARDS.md` §1.2' docs/dev/specs/_TEMPLATE_SPEC.md
  1
  $ grep -cF 'every `file:line` the search returns' docs/dev/specs/_TEMPLATE_SPEC.md
  1
  ```

## 6. Follow-ups

None.
