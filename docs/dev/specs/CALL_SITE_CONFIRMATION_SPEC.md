# Call Site Confirmation — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261015
**Branch:** `chore/issue-232-call-site-confirmation` (from `main`, merges to `main` and `dev`)
**Target release:** none — `chore/*` carries no version bump, no `CHANGELOG.md` entry, no tag, no Release
**Originating item:** Issue #232
**Design study:** `n/a` — direct path, no recon was run

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261015 | Ray | #232 is a `chore/*` on the direct path; the §1.2 bullet is applied in the wording the issue gives | Accepted. Branch and path as in the header; step 1 quotes the issue's wording verbatim |
| 20261015 | Spanner | `docs/dev/specs/_TEMPLATE_SPEC.md` §2's call-sites row asks for "every `file:line` the search returns". Under the new §1.2 bullet a hit is not a call site until it is confirmed, so the template would keep asking authors for exactly the unconfirmed list #232 describes | In scope: the row is changed to ask for the confirmed call sites and cite §1.2 for how a hit is confirmed (step 2, AC1.2). The template restates no part of the rule. The issue's ACs gain AC1.2's wording at close-out |

---

## 1. Scope

**In scope:**

- `docs/DEVELOPMENT_STANDARDS.md` §1.2 — one new bullet after **A contract change enumerates its call sites.**
- `docs/dev/specs/_TEMPLATE_SPEC.md` §2 — the evidence cell of the call-sites example row.

**Out of scope:**

- **`CLAUDE.md` § Common Pitfalls.** Its "Component-verified ≠ integration-verified" entry cites §1.2 for the call-site rule and restates none of it, so it is already correct.
- **`.claude/skills/session-start/SKILL.md` § Role 2.** Criteria 2 and 5 ask whether claims were checked against live source; they do not describe how a search hit is confirmed, so nothing there contradicts the new bullet.
- **Specs and studies already written**, including the #223 study's F10. §1.2 applies forward; no archived artifact is corrected.
- **`workmain/**`, `tests/**`, `automation/**`, `config/**`.** Untouched, which is what keeps this on `chore/*` under §2.2.

## 3. Design rules

- **DR1 —** The rule is stated once, in §1.2. The template cites §1.2 and does not restate how a hit is confirmed.
- **DR2 —** Text is applied exactly as quoted in §4. Anything not covered here stops and goes to Ray, per `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps. Implementation is Spanner's, in this session (`docs/DEVELOPMENT_STANDARDS.md` §1.1, direct path).

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | §1.2 call-site confirmation bullet | `docs/DEVELOPMENT_STANDARDS.md` |
| 2 | Template call-sites row | `docs/dev/specs/_TEMPLATE_SPEC.md` |
| 3 | Results artifact | `docs/dev/results/CALL_SITE_CONFIRMATION_RESULTS.md` |

### Step 1 — §1.2 bullet

Insert after the bullet beginning `- **A contract change enumerates its call sites.**` (ending `...without any criterion covering them (#130).`) and before `- Changes to an existing spec are surgical, not wholesale rewrites.`:

```markdown
- A call site found by a name search is confirmed by reading what the call is made on: a same-named method on another object is not a caller. A claim that a method has no caller states that references by name (getattr, a method passed uncalled) were also searched.
```

### Step 2 — Template call-sites row

Replace, in `docs/dev/specs/_TEMPLATE_SPEC.md` §2:

```markdown
| Call sites of `<symbol>`, found by `grep -rn '<pattern>' --include='*.py' .` | every `file:line` the search returns |
```

with:

```markdown
| Call sites of `<symbol>`, found by `grep -rn '<pattern>' --include='*.py' .` | every `file:line` the search returns that is confirmed a call site — `docs/DEVELOPMENT_STANDARDS.md` §1.2 |
```

### Step 3 — Results artifact

`docs/dev/results/CALL_SITE_CONFIRMATION_RESULTS.md` from `_TEMPLATE_RESULTS.md`, recording each AC in §5 below. Both name Ray and are recorded `Not met` / `Awaiting Ray` (§1.2).

### Authorization points

None. No migration, no GitHub object deleted, no merge to `main`, no force-push, no service run-state change. The merges are `/closeout`'s.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | `docs/DEVELOPMENT_STANDARDS.md` §1.2 states that a name-search hit is confirmed by reading what the call is made on, and that a no-caller claim states that references by name were also searched, in the wording given in #232 | A stated reading by Ray of §1.2, and `grep -cF 'A call site found by a name search is confirmed by reading what the call is made on' docs/DEVELOPMENT_STANDARDS.md` returning 1 (0 on `main` at authoring) |
| AC1.2 | The spec template's call-sites row asks for confirmed call sites rather than every search hit, and cites §1.2 for how a hit is confirmed without restating it | A stated reading by Ray of `docs/dev/specs/_TEMPLATE_SPEC.md` §2, and `grep -c 'every .file:line. the search returns |' docs/dev/specs/_TEMPLATE_SPEC.md` returning 0 (1 on `main` at authoring) |

## 6. Test plan

Omitted: no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes (`_TEMPLATE_SPEC.md`, direct path). Close-out runs the suites regardless.

## 7. Risks and rollback

| Risk | Mitigation |
| --- | --- |
| The bullet is read as requiring a non-name search on every contract change | Its second sentence binds only a claim that a method has no caller |

Rollback: revert the step commits. Both edits are text in two documents.
