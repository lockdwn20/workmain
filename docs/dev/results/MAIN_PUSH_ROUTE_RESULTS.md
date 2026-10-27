# Route to `main` for `chore/*` and `hotfix/*` — Implementation Results

**Status:** Active
**Author:** Spanner (Role 1)
**Date:** 20261027
**Spec:** `../specs/MAIN_PUSH_ROUTE_SPEC.md`
**Released as:** n/a — chore/*

---

## 1. Summary

Complete. `docs/DEVELOPMENT_STANDARDS.md` §2.2 now states that a `hotfix/*` or `chore/*` merge reaches `main` as a pushed local merge, that the push passes `main-pr-required` through its admin bypass, and that the warning it prints is expected. Nothing changed on GitHub or in `.claude/skills/closeout/`. AC3.1 is checked on this branch's own close-out.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | §2.2 states the route to `main` for `hotfix/*` and `chore/*` and the expected warning | `docs/DEVELOPMENT_STANDARDS.md` | +0 |
| 2 | Study disposition and this artifact | `docs/dev/design/DESIGN_MAIN_PUSH_ROUTE.md`, `docs/dev/results/MAIN_PUSH_ROUTE_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Not met | Awaiting Ray |
| AC1.2 | Met | `grep -rn -e 'main-pr-required' -e 'admin role' CLAUDE.md docs/DEVELOPMENT_STANDARDS.md docs/AI_SETTINGS_GUIDE.md .claude/ docs/dev/*/_TEMPLATE_*.md` returned one line, `docs/DEVELOPMENT_STANDARDS.md:190`, inside §2.2, 20261027 at `1f55333` |
| AC2.1 | Not met | Awaiting Ray |
| AC3.1 | Not met | Awaiting Ray — checked on this branch's close-out |

## 4. Deviations from spec

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |

None. Step 1's quoted line occurred once in its file and was replaced as quoted.

## 5. Verification

- **Test suite:** 1541 passed, 0 failed, 0 skipped (baseline: 1541 passed, 0 failed, 0 skipped, from the most recent `CHANGELOG.md` entry). `pytest automation/`: 58 passed, 0 failed, 0 skipped. Both run 20261027 at `1f55333`.
- **Live verification:** none needed; the change is to documents only. The `remote:` line §2.2 quotes is checked by AC3.1 on this branch's close-out push.
- **Daemon restart:** none — `chore/*` (`docs/DEVELOPMENT_STANDARDS.md` §2.6).

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #247 | Agent sessions act on GitHub as the admin account, so no ruleset can bind them | Ray, 20261027: a separate issue. Its design changes the route this spec states. |
