# What § Client Reference forbids — Spec

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20261112
**Branch:** `chore/issue-274-client-reference-scope` (from `main`)
**Target release:** n/a — `chore/*` carries no release (`docs/standards/2-git.md` §2.2)
**Originating item:** Issue #274
**Design study:** `../design/DESIGN_CLIENT_REFERENCE_SCOPE.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261112 | Ray | The branch is `chore/*`: the change is to `CLAUDE.md` only. | — |
| 20261112 | Ray | The rule covers a class of real values, not a list (design study Q1). | DR1 |
| 20261112 | Ray | The operator's own name used as authorship is not covered (design study Q2). | DR1 |
| 20261112 | Ray | The rule reaches everything published from the repository: tracked files, commit messages, and issue and pull request text (design study Q3). | DR1 |
| 20261112 | Ray | The real values are listed in `.env` key `DEV_REAL_VALUES`, which `.env.example` does not declare; a check that reads it is #275 (design study Q5, §4 Enforcement). | DR3, §1 Out of scope |
| 20261112 | Ray | Ray adds each new real value to `DEV_REAL_VALUES`; a session that meets one not listed tells Ray and writes it nowhere. Step 1's replacement text is Ray's wording. | DR3, step 1 |
| 20261112 | Ray | #274's first criterion reads "into a tracked file"; per design study Q3 the rule reaches everything published from the repository. | §5 restatement of AC1.1 |

---

## 1. Scope

**In scope:** `CLAUDE.md` § Client Reference, replaced whole.

**Out of scope:**

- The check that reads `DEV_REAL_VALUES`: #275.
- Putting the real values into `DEV_REAL_VALUES` in `.env`. `.env` is untracked and the values are real, so this is Ray's, outside the branch.
- Removing real values already published in `docs/archive/` and in five commit messages on `main` (design study F5, F6). Whether that becomes an issue is Ray's.
- `tests/test_slack_channel_config.py:186`, which asserts the real workspace name: #214 removes it.

## 3. Design rules

- **DR1 — The rule forbids a class, with examples, and states what it reaches.** A real value is a client's name, or an identifier of the operator's Slack workspace, its channels or users, a report recipient or a Drive location, as held in `.env`, `~/.workmain/` or the database. It reaches everything published from the repository: tracked files, commit messages, and issue and pull request text. The operator's own name used as authorship is not a real value.
- **DR2 — The rule states how each kind of text references a real value.** A test or fixture uses an invented value and never reads the real one. Any other text names where the value is held, never the value.
- **DR3 — The rule names `DEV_REAL_VALUES` and states its status.** It lists the real values, and Ray adds each new one. A session that meets a real value not listed tells Ray and writes it nowhere. Only development tooling reads it, and `.env.example` does not declare it.
- **DR4 — The rule states why it exists and when it ends** (design study Q4): the application is developed while in live use, the repository is public, and the rule holds until development no longer runs against live data.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | § Client Reference states the widened rule | `CLAUDE.md` |
| 2 | Results artifact | `docs/dev/results/CLIENT_REFERENCE_SCOPE_RESULTS.md` |

### Step 1 — § Client Reference states the widened rule

Replace the body of `CLAUDE.md` § Client Reference. The heading `### Client Reference` stays.

Current text:

```markdown
During development, reference the default client via `WORKMAIN_DEFAULT_CLIENT` in `.env` — never the actual client name.
```

Replacement:

```markdown
WorkmAIn is developed while in live use, and the repository is public. Until development no longer runs against live data, nothing published from this repository — a tracked file, a commit message, or issue or pull request text — contains a real value: a client's name, or an identifier of the operator's Slack workspace, its channels or users, a report recipient or a Drive location, as held in `.env`, `~/.workmain/` or the database. The operator's own name as authorship is not one.

- **Tests and fixtures:** an invented value unlike the real one. A test never reads a real value from `.env`, `~/.workmain/` or the live database.
- **Any other text:** where the value is held — the `.env` key (such as `WORKMAIN_DEFAULT_CLIENT`), the `~/.workmain/` file and key, or the table and column — never the value.

`DEV_REAL_VALUES` in `.env` lists the real values. Ray adds each new one; a session that meets a real value not listed tells Ray and writes it nowhere. Only development tooling reads the key, and `.env.example` does not declare it.
```

Commit: `docs(claude): widen § Client Reference to every real value`.

### Step 2 — Results artifact

Written from `docs/dev/results/_TEMPLATE_RESULTS.md`, with each criterion in §5 recorded as met or not, with its evidence.

### Authorization points

None.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | `CLAUDE.md` § Client Reference forbids every real client name and every real identifier of internal-only data, the Slack workspace among them, in everything published from the repository, and states how a test and any other text reference each | A stated reading by Ray of `CLAUDE.md` § Client Reference, read for which real values it forbids, where it reaches, how each is referenced, and whether its stated reason makes the condition for removing it clear |
| AC1.2 | `DEV_REAL_VALUES` is named only by the rule and is not part of the application's configuration | `grep -rn DEV_REAL_VALUES CLAUDE.md docs/standards .claude .github workmain config templates .env.example` returns only `CLAUDE.md` § Client Reference |
| AC2.1 | The rule has one statement in the document set | `grep -rn 'Client Reference' CLAUDE.md docs/standards .claude .github` returns only the `CLAUDE.md` heading and citations of it |

**Restated for close-out.** AC1.1 restates #274's first criterion, which reads "into a tracked file": per design study Q3 the rule reaches everything published from the repository, so the criterion does too. The issue body needs that edit, made at close-out (`docs/standards/1-workflow.md` §1.2).

## 7. Risks and rollback

- **Risk:** the wording forbids a value development needs to write, or misses one it should forbid. AC1.1's reading by Ray is where this is caught.
- **Rollback:** revert step 1's commit.
