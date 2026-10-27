# Deviation Record and Self-Resolution Passages — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261027
**Branch:** `chore/issue-242-deviation-record` (from `origin/main`)
**Target release:** n/a — `chore/*`
**Originating item:** Issue #242
**Design study:** `../design/DESIGN_DEVIATION_RECORD.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261026 | Ray | Branch type `chore/*`, direct path. | Applied. |
| 20261027 | Ray | Design study Q1: the stop rule in `.claude/skills/session-start/SKILL.md` § Role 3 binds whichever role implements, including Role 1 on the direct path. | Step 4. Results §4 names the stop rule, not "Role 3" (Step 1). |
| 20261027 | Ray | Design study Q2: `docs/DEVELOPMENT_STANDARDS.md` §6.4 is removed. The case it covers already stops before step 1, at the Anvil session-open check of every file a spec names. | Step 2d. |
| 20261027 | Spanner | The binding for Role 1 goes in `references/spanner.md` § Working rules, not in §1.1 or `SKILL.md`. `CLAUDE.md` § THREE-ROLE MODEL puts a rule for how a single role works in that role's reference file, and #241's spec applied the same rule (its DR3). | Step 4. Design study §4.7 states it. |
| 20261027 | Spanner | Adjudication of the three passages issue #242 names, per design study §4.2–§4.4: §1.1 "What the direct path trades" is rewritten to stop; §2.2's hotfix-into-feature "Document the deviation" is rewritten so the feature spec's Decision Log records the folded hotfix at authoring time; §6.4 is removed (Ray, Q2). | Steps 2a, 2b, 2d. |
| 20261027 | Spanner | Adjudication of the hits the search found, per design study §4.5–§4.7: §2.4's "Note any deviations from spec." is removed; the spec template's "falls back on" sentence is rewritten; `references/spanner.md`'s working rules are scoped off a direct-path implementation step (Ray, Q1). | Steps 2c, 3, 4. |
| 20261027 | Spanner | No passage is kept as a named exception to the stop rule, so issue #242's third criterion holds with no passage to read. AC3.1 checks that. | AC3.1. |
| 20261027 | Spanner | The issue's fourth criterion records the search and its adjudications in the results artifact. They are decided before the spec, so their one home is the design study's §2–§4, and the results artifact cites it. #241's spec settled the same case the same way. Restated as AC4.1. | The issue body is edited at close-out. |

## 1. Scope

**In scope:**

- `docs/dev/results/_TEMPLATE_RESULTS.md` §4.
- `docs/DEVELOPMENT_STANDARDS.md` §1.1 "What the direct path trades", §2.2 "hotfix/* → feature/* exception", §2.4's commit body placeholder, and §6.4.
- `docs/dev/specs/_TEMPLATE_SPEC.md` §3.
- `.claude/skills/session-start/references/spanner.md` § Working rules.
- The design study's §6 Disposition and this spec's results artifact.

**Out of scope:**

- Caliper's post-implementation review and what happens to an unstopped departure it finds. Both are #243's.
- Existing results artifacts. Their §4 tables are the record of what happened and are not rewritten.
- `automation/fixtures/closeout_results_*.md`. They carry `## 4. Deviations from spec` with `None.` under it, which stays valid, and nothing parses §4 (design study F11).
- `.claude/skills/session-start/SKILL.md` § Role 3. Its text already states the rule; this spec changes who it binds by Step 4, not what it says.

## 2. Verified current state

Direct path: each step below quotes the text it replaces. Each quoted block was confirmed to occur exactly once in its file on 20261027.

## 3. Design rules

- **DR1 — Exact text.** Each edit is made exactly as quoted. A quote that does not match the file stops the step (`.claude/skills/session-start/SKILL.md` § Role 3, binding Role 1 here by Ray's answer to design study Q1).
- **DR2 — One home.** Results §4 is the only record of a departure. No other document is told to record one.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Results §4 records the stop | `docs/dev/results/_TEMPLATE_RESULTS.md` |
| 2 | Standards passages adjudicated | `docs/DEVELOPMENT_STANDARDS.md` |
| 3 | Design rules no longer stand in for a stop | `docs/dev/specs/_TEMPLATE_SPEC.md` |
| 4 | Role 1 stops when it implements | `.claude/skills/session-start/references/spanner.md` |
| 5 | Study disposition and results artifact | `docs/dev/design/DESIGN_DEVIATION_RECORD.md`, `docs/dev/results/DEVIATION_RECORD_RESULTS.md` |

Close-out is not in this table. It is `/closeout`.

### Step 1 — `docs/dev/results/_TEMPLATE_RESULTS.md`

Replace:

```markdown
Where the implementation differs from what was specified, and why. Includes anything surfaced during implementation and resolved by Ray mid-flight.

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
```

with:

```markdown
Every item discovered during implementation that departs from the approved spec, including an ambiguity the spec did not settle, is listed here with the step the implementer stopped at, how it was resolved, and who resolved it. A departure with no recorded stop breaks the stop rule in `.claude/skills/session-start/SKILL.md` § Role 3, which binds whichever role implements, and is not a deviation. It is still listed, with `none` under `Step stopped at`, because a record that leaves it out hides it.

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |
```

### Step 2 — `docs/DEVELOPMENT_STANDARDS.md`

**2a.** In §1.1, replace:

```text
and scope that no acceptance criterion named is caught *after* implementation, by the results artifact's deviations table, rather than *before* it by recon and review.
```

with:

```text
and scope that no acceptance criterion named is found only *during* implementation, when the implementer stops on it (`.claude/skills/session-start/SKILL.md` § Role 3), rather than *before* it by recon and review.
```

**2b.** In §2.2 "hotfix/* → feature/* exception", replace:

```text
  - Document the deviation in the feature spec.
```

with:

```text
  - The feature spec's Decision Log records the folded hotfix before the spec is approved.
```

**2c.** In §2.4, replace:

```text
<body — what and why, not how. Files changed, decisions made, expected test count. Note any deviations from spec.>
```

with:

```text
<body — what and why, not how. Files changed, decisions made, expected test count.>
```

**2d.** In §6, delete these lines, together with the blank line that follows them, so that §6.3's last bullet is followed by one blank line and the `---` before `## 7. File Placement`:

```text
### 6.4 Spec-named test file doesn't exist

- If a spec names a test file that isn't there, use the established file for that coverage and document the deviation.
```

### Step 3 — `docs/dev/specs/_TEMPLATE_SPEC.md`

Replace:

```text
Numbered invariants the implementation must hold to. These are what an implementer falls back on when the spec doesn't cover a case.
```

with:

```text
Numbered invariants the implementation must hold to. A case a design rule decides is covered by this spec. A case none decides is not, and the implementer stops on it.
```

### Step 4 — `.claude/skills/session-start/references/spanner.md`

**4a.** Replace:

```text
These hold for the whole Spanner session. The run neither reads nor emits them, and no other role's session loads them.
```

with:

```text
These hold for the whole Spanner session, except while it implements a direct-path spec: then only "Implementing a direct-path spec stops on every departure" applies. The run neither reads nor emits them, and no other role's session loads them.
```

**4b.** After the last bullet of § Working rules, which begins `- **Keep the open items visible.**`, append:

```markdown
- **Implementing a direct-path spec stops on every departure.** On the direct path Role 1 implements its own spec (`docs/DEVELOPMENT_STANDARDS.md` §1.1), and the stop rule in `SKILL.md` § Role 3 binds it as it binds Anvil. Anything the spec does not cover — an ambiguity it does not settle, a quote that does not match the file, a change that seems too small to ask about — stops at the current step and goes to Ray, who decides it. The stop and its resolution are recorded in the results artifact's §4.
```

### Step 5 — Study disposition and results artifact

**5a.** In the design study's §6, replace `- Promoted to:` with ``- Promoted to: `../specs/DEVIATION_RECORD_SPEC.md` ``.

**5b.** Write `docs/dev/results/DEVIATION_RECORD_RESULTS.md` from `docs/dev/results/_TEMPLATE_RESULTS.md` as Step 1 leaves it, with `**Released as:** n/a — chore/*`. Its §4 uses Step 1's table. Its §5 cites the design study's §2 for the search and §3–§4 for each hit's adjudication, and states for each hit the step that delivered it, or that it was read and left unchanged (design study §3.2).

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The results template's §4 requires every departure and ambiguity to be listed with the step the implementer stopped at, its resolution and who resolved it, and says that a departure with no recorded stop breaks the stop rule and is not a deviation. | Stated reading by Ray of §4 of `docs/dev/results/_TEMPLATE_RESULTS.md`, for the instruction issue #242 states |
| AC1.2 | The template's §4 table records the stop, and has no column for approving a departure after it was made. | `grep -c 'Departure or ambiguity . Step stopped at . Resolution . Resolved by' docs/dev/results/_TEMPLATE_RESULTS.md` prints `1`, and `grep -c 'Approved by' docs/dev/results/_TEMPLATE_RESULTS.md` prints `0` |
| AC2.1 | Each of the three passages issue #242 names has a recorded adjudication, and the standards text matches it: §1.1 rewritten to stop, §2.2 rewritten to the feature spec's Decision Log, §6.4 removed. | Stated reading by Ray of this spec's Decision Log against `docs/DEVELOPMENT_STANDARDS.md` §1.1, §2.2 and §6 |
| AC3.1 | No passage is kept as an exception to the stop rule, so none needs to be marked as one. | Stated reading by Ray of this spec's Decision Log: every adjudication is a rewrite or a removal |
| AC4.1 | The search for further self-resolution passages and every hit's adjudication are recorded, and the results artifact cites that record and states what was delivered for each hit. | Stated reading by Ray of the design study's §2–§4 and the results artifact's §5 |
| AC4.2 | No live document tells anyone to record a departure from a spec in place of stopping, or to resolve an uncovered case from the spec's design rules. | `grep -rni -e 'document the deviation' -e 'note any deviations' -e 'falls back on' CLAUDE.md docs/DEVELOPMENT_STANDARDS.md docs/AI_SETTINGS_GUIDE.md .claude/ docs/dev/*/_TEMPLATE_*.md` returns nothing |
| AC4.3 | Role 1 is bound by the stop rule when it implements a direct-path spec, and Spanner's authoring rules do not apply to that implementation. | Stated reading by Ray of `.claude/skills/session-start/references/spanner.md` § Working rules |
| AC5.1 | Both test suites pass. | `pytest` and `pytest automation/` each run as written and exit `0` |

## 6. Test plan

Omitted: no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes.

## 7. Risks and rollback

- **A quote does not match.** DR1 stops the step. Rollback: none needed.
- **The new §4 wording conflicts with #243's review.** #243 checks for a §4 entry with no recorded stop; the `none` value under `Step stopped at` is what it reads. Rollback: revert Step 1's commit.
- **Removing §6.4 leaves a case uncovered.** A spec-named file that does not exist is emitted as a discrepancy by `.claude/skills/session-start/references/anvil.md` before step 1, and on the direct path Step 4's rule stops it. Rollback: revert Step 2's commit.
