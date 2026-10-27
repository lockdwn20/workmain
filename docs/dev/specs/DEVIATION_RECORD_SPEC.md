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
| 20261027 | Ray | Design study Q1: the stop rule in `.claude/skills/session-start/SKILL.md` § Role 3 binds Anvil on every departure. Role 1, implementing its own direct-path spec, keeps its judgment over wording and mechanics within the meaning, scope and file set Ray approved, and stops on any change to them. Revised from the first answer; the revision row below gives the reason. | Steps 1 and 4. |
| 20261027 | Ray | Design study Q2: `docs/DEVELOPMENT_STANDARDS.md` §6.4 is removed. The case it covers already stops before step 1, at the Anvil session-open check of every file a spec names. | Step 2d. |
| 20261027 | Spanner | The binding for Role 1 goes in `references/spanner.md` § Working rules, not in §1.1 or `SKILL.md`. `CLAUDE.md` § THREE-ROLE MODEL puts a rule for how a single role works in that role's reference file, and #241's spec applied the same rule (its DR3). | Step 4. Design study §4.7 states it. |
| 20261027 | Spanner | Adjudication of the three passages issue #242 names, per design study §4.2–§4.4: §1.1 "What the direct path trades" is rewritten to stop; §2.2's hotfix-into-feature "Document the deviation" is rewritten so the feature spec's Decision Log records the folded hotfix at authoring time; §6.4 is removed (Ray, Q2). | Steps 2a, 2b, 2d. |
| 20261027 | Spanner | Adjudication of the hits the search found, per design study §4.5–§4.7: §2.4's "Note any deviations from spec." is removed; the spec template's "falls back on" sentence is rewritten; two of `references/spanner.md`'s working rules no longer decide a change of meaning, scope or file set during a direct-path implementation (Ray, Q1). | Steps 2c, 3, 4. |
| 20261027 | Ray | **Design study Q1 answer revised.** The stop rule binds Anvil on every departure, because Anvil holds no design authority. When Role 1 implements its own direct-path spec, it holds design authority, and Ray's approval of the spec is the only review between the spec and the edit (`docs/DEVELOPMENT_STANDARDS.md` §1.1). So Role 1 keeps its judgment over wording and mechanics within the meaning, scope and file set Ray approved. It stops on any change to meaning, scope or file set. The earlier answer ("binds whichever role implements") made Role 1 an Anvil for docs work, the work its judgment is most needed for. Design study §4.7 and Q1 are updated to record this answer and its reason. | Accepted. Design study §4.1, §4.7 and Q1 record the revised answer. Steps 1 and 4 and DR1 carry it. |
| 20261027 | Ray | **Step 4a scopes off every working rule, not the two F7 names.** As drafted, only the new stop bullet applies during a direct-path implementation. That also switches off "Keep the open items visible", "A position Ray brings from an outside review is his decision", "A design holds for every provider…" and the rest, none of which F7 found to read as self-resolution. Required: scope off only the two rules F7 names ("Apply a rule; do not ask" and "A spec that builds the process can outrun the standards"), and only for a change of meaning, scope or file set. | Accepted. The second rule's heading in `references/spanner.md` is "A case no standard yet covers does not block the work", which is the rule F7 names; Step 4 names it by that heading. Step 4a now says only that the new rule limits two of the others; Step 4b names both and limits them only for a change of meaning, scope or file set. |
| 20261027 | Ray | **Step 4b stops on every departure, including the trivial.** "A change that seems too small to ask about — stops" would have stopped both of #241's whitespace fixes (design study F10). Required: rewrite 4b to the revised Q1 answer. Role 1, implementing a direct-path spec, stops on a change to the meaning, scope or file set it was approved for. A wording or mechanical change within them is made and recorded in results §4 as within approved meaning (next row). An ambiguity about which kind a change is counts as a change of meaning, and stops. | Accepted. Step 4b rewritten. |
| 20261027 | Ray | **Results §4 needs a value for an in-scope change by Role 1.** Under the revised Q1 answer, Role 1 makes wording and mechanical changes within the approved meaning without stopping. Required: Step 1's instruction defines `within approved meaning` as a `Step stopped at` value, used only by Role 1 on the direct path and never by Anvil. #243's post-implementation review checks each such row for a change of meaning. Nothing else in Step 1's table changes. | Accepted. Step 1 defines the value. The check belongs to #243 and is not specified here. |
| 20261027 | Ray | **Step 1's §4 text contradicts itself.** It says a departure with no recorded stop "is not a deviation", then has it listed under `## 4. Deviations from spec` with `none` under `Step stopped at`. Required: one definition. A departure is any difference from the approved spec. Each is listed with how it was handled: the step stopped at, `within approved meaning` (Role 1, direct path), or `none`, and `none` breaks the stop rule. | Accepted. Step 1 rewritten; AC1.1 restated. |
| 20261027 | Ray | **Text that names the old Q1 answer.** Step 1's "which binds whichever role implements", DR1's "binding Role 1 here by Ray's answer to design study Q1", AC4.3, and the Decision Log row for Q1 all state the earlier answer. Required: each is restated to the revised answer. AC4.3 checks that Role 1 stops on a change of meaning, scope or file set when implementing a direct-path spec, and that only the two rules F7 names are scoped off it. | Accepted. Each restated. Step 2a also cited § Role 3 for the direct-path implementer; it now cites `references/spanner.md` § Working rules (Spanner row below). |
| 20261027 | Ray | **Option B (a direct-path spec states what each passage must say, not its exact new text) is deferred until after #243.** It is decided from the first direct-path cycles reviewed under #243, judged on three things: how often the spec's exact wording is revised during implementation, how many `within approved meaning` rows Caliper finds changed meaning, and how many review rounds a docs spec takes before approval. Out of scope here. Ray decides whether it is a line in #243's body or a `gap` issue placed after #243. It is sequenced after this issue in either case, because both edit `docs/dev/specs/_TEMPLATE_SPEC.md`. | Accepted. § 1 Out of scope. This option B is not design study §4.7's option B. Ray, 20261027: both a note in #243's body and a `gap` issue. Opened as #245, blocked by #242 and #243 and added to the board for Ray to place; #243's body carries the note, with the `within approved meaning` check. |
| 20261027 | Spanner | Step 2a's rewrite of §1.1 "What the direct path trades" cited `SKILL.md` § Role 3 for the implementer who stops. That passage is about the direct path, where the implementer is Role 1, and Role 1's stop is in `references/spanner.md` § Working rules under the revised Q1 answer. | Step 2a cites `references/spanner.md` § Working rules and says what Role 1 stops on. |
| 20261027 | Caliper | 3: Step 3 and Step 4b contradict each other. Step 3 changes `docs/dev/specs/_TEMPLATE_SPEC.md:56` to say that a case no design rule decides "is not [covered], and the implementer stops on it". That sentence has no condition. The template's next line (`:61`) points only to `SKILL.md` § Role 3. Step 4b tells Role 1, while implementing a direct-path spec, to make a wording or mechanical change within the approved meaning without stopping and to record it as `within approved meaning`. The direct-path spec is written from the same template (`docs/DEVELOPMENT_STANDARDS.md` §1.1, "Spec"). So a Role 1 implementer who meets a wording-level case no design rule decides is told to stop by the spec template and told not to by `references/spanner.md`, and it has to guess which governs. Step 3's text needs to name both homes, as Step 1's `none` bullet already does: § Role 3 for Anvil, `references/spanner.md` § Working rules for Role 1 on the direct path. | Accepted. Step 3's text names both: Anvil stops on it under § Role 3, and Role 1 on the direct path handles it under `references/spanner.md` § Working rules. |
| 20261027 | Caliper | 3: Step 1 defines `within approved meaning` as a `Step stopped at` value, but nothing says what goes in `Resolution` and `Resolved by` on such a row. Under Step 4b no one besides Role 1 decides the change. The same gap exists for a `none` row, where no resolution may exist yet because #243's review comes later. This spec's own results artifact needs these values first: DR1 sends this implementation's within-meaning changes to it (Step 5b, "Its §4 uses Step 1's table"). The implementer would have to invent the values, and #243 reads them (§7 Risks, second bullet). | Accepted. Step 1 states `Resolution` and `Resolved by` for each value: a stop is resolved by `Ray, <date>`; a `within approved meaning` row records the change made, resolved by `Role 1, <date>`; a `none` row records what was done, with `Awaiting Ray` until Ray rules and `Ray, <date>` after, matching the `Awaiting Ray` form `docs/DEVELOPMENT_STANDARDS.md` §1.2 uses for a check Ray has not made. AC1.1 covers it. |
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
- `.claude/skills/session-start/SKILL.md` § Role 3. It binds Anvil on every departure and is unchanged.
- A direct-path spec that states what each passage must say rather than its exact new text. Deferred by Ray to #245, decided from the direct-path cycles #243 reviews.
- #243's check of each `within approved meaning` row for a change of meaning. Step 1 defines the value; the check is #243's, and its body says so.

## 2. Verified current state

Direct path: each step below quotes the text it replaces. Each quoted block was confirmed to occur exactly once in its file on 20261027.

## 3. Design rules

- **DR1 — Exact text.** Each edit is made as quoted. A wording or mechanical change within the meaning, scope and file set approved here is recorded in the results artifact's §4 as `within approved meaning`. A quote that does not match the file stops the step: what the edit would then change is unknown, and an ambiguity about the kind of change counts as a change of meaning (Step 4b, binding Role 1 here as it implements this spec).
- **DR2 — One home.** Results §4 is the only record of a departure. No other document is told to record one.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Results §4 records the stop | `docs/dev/results/_TEMPLATE_RESULTS.md` |
| 2 | Standards passages adjudicated | `docs/DEVELOPMENT_STANDARDS.md` |
| 3 | Design rules no longer stand in for a stop | `docs/dev/specs/_TEMPLATE_SPEC.md` |
| 4 | Role 1 stops on a change of meaning, scope or file set | `.claude/skills/session-start/references/spanner.md` |
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
A departure is any difference between the approved spec and what was delivered, including an ambiguity the spec did not settle. Every departure is listed here with how it was handled, how it was resolved, and who resolved it. `Step stopped at` holds one of three values:

- **the step** the implementer stopped at, before making the change. `Resolution` is what Ray decided, and `Resolved by` is `Ray, <date>`;
- **`within approved meaning`** — a wording or mechanical change Role 1 made without stopping while implementing its own direct-path spec, within the meaning, scope and file set Ray approved (`.claude/skills/session-start/references/spanner.md` § Working rules). Anvil never uses it. `Resolution` is the change made, and `Resolved by` is `Role 1, <date>`;
- **`none`** — the change was made without the stop it required. A `none` row breaks the stop rule: `.claude/skills/session-start/SKILL.md` § Role 3 for Anvil, `references/spanner.md` § Working rules for Role 1. It is still listed, because a record that leaves it out hides it. `Resolution` is what was done, and `Resolved by` is `Awaiting Ray` until Ray rules on it, then `Ray, <date>`.

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
and scope that no acceptance criterion named is found only *during* implementation, when Role 1 stops on a change to the scope Ray approved (`.claude/skills/session-start/references/spanner.md` § Working rules), rather than *before* it by recon and review.
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
Numbered invariants the implementation must hold to. A case a design rule decides is covered by this spec. A case none decides is not: Anvil stops on it (`.claude/skills/session-start/SKILL.md` § Role 3), and Role 1, implementing a direct-path spec, stops on it when it changes meaning, scope or file set (`.claude/skills/session-start/references/spanner.md` § Working rules).
```

### Step 4 — `.claude/skills/session-start/references/spanner.md`

**4a.** Replace:

```text
These hold for the whole Spanner session. The run neither reads nor emits them, and no other role's session loads them.
```

with:

```text
These hold for the whole Spanner session, except where "Implementing a direct-path spec" limits two of them. The run neither reads nor emits them, and no other role's session loads them.
```

**4b.** After the last bullet of § Working rules, which begins `- **Keep the open items visible.**`, append:

```markdown
- **Implementing a direct-path spec.** On the direct path Role 1 implements its own spec (`docs/DEVELOPMENT_STANDARDS.md` §1.1). It holds design authority, and Ray's approval of the spec is the only review between the spec and the edit, so it keeps its judgment over wording and mechanics within the meaning, scope and file set Ray approved. Such a change is made and recorded in the results artifact's §4 as `within approved meaning`. A change to the meaning, the scope or the file set stops at the current step and goes to Ray, who decides it. An ambiguity about which kind a change is counts as a change of meaning, and stops. During that implementation, "Apply a rule; do not ask" and "A case no standard yet covers does not block the work" do not decide a change of meaning, scope or file set. Anvil holds no design authority, and `SKILL.md` § Role 3 stops it on every departure.
```

### Step 5 — Study disposition and results artifact

**5a.** In the design study's §6, replace `- Promoted to:` with ``- Promoted to: `../specs/DEVIATION_RECORD_SPEC.md` ``.

**5b.** Write `docs/dev/results/DEVIATION_RECORD_RESULTS.md` from `docs/dev/results/_TEMPLATE_RESULTS.md` as Step 1 leaves it, with `**Released as:** n/a — chore/*`. Its §4 uses Step 1's table. Its §5 cites the design study's §2 for the search and §3–§4 for each hit's adjudication, and states for each hit the step that delivered it, or that it was read and left unchanged (design study §3.2).

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The results template's §4 defines a departure once, as any difference from the approved spec including an unsettled ambiguity, and requires each to be listed with how it was handled — the step stopped at, `within approved meaning` (Role 1 on the direct path only, never Anvil), or `none` — its resolution and who resolved it, with what `Resolution` and `Resolved by` hold for each value, and says that `none` breaks the stop rule. | Stated reading by Ray of §4 of `docs/dev/results/_TEMPLATE_RESULTS.md`, for the instruction issue #242 states and the three values |
| AC1.2 | The template's §4 table records the stop, and has no column for approving a departure after it was made. | `grep -c 'Departure or ambiguity . Step stopped at . Resolution . Resolved by' docs/dev/results/_TEMPLATE_RESULTS.md` prints `1`, and `grep -c 'Approved by' docs/dev/results/_TEMPLATE_RESULTS.md` prints `0` |
| AC2.1 | Each of the three passages issue #242 names has a recorded adjudication, and the standards text matches it: §1.1 rewritten to stop, §2.2 rewritten to the feature spec's Decision Log, §6.4 removed. | Stated reading by Ray of this spec's Decision Log against `docs/DEVELOPMENT_STANDARDS.md` §1.1, §2.2 and §6 |
| AC3.1 | No passage is kept as an exception to the stop rule, so none needs to be marked as one. | Stated reading by Ray of this spec's Decision Log: every adjudication is a rewrite or a removal |
| AC4.1 | The search for further self-resolution passages and every hit's adjudication are recorded, and the results artifact cites that record and states what was delivered for each hit. | Stated reading by Ray of the design study's §2–§4 and the results artifact's §5 |
| AC4.2 | No live document tells anyone to record a departure from a spec in place of stopping, or to resolve an uncovered case from the spec's design rules. | `grep -rni -e 'document the deviation' -e 'note any deviations' -e 'falls back on' CLAUDE.md docs/DEVELOPMENT_STANDARDS.md docs/AI_SETTINGS_GUIDE.md .claude/ docs/dev/*/_TEMPLATE_*.md` returns nothing |
| AC4.3 | Role 1, implementing a direct-path spec, stops on a change of meaning, scope or file set, treats an ambiguity about the kind of change as a change of meaning, and records a wording or mechanical change within them as `within approved meaning`; only "Apply a rule; do not ask" and "A case no standard yet covers does not block the work" are limited during that implementation, and only for a change of meaning, scope or file set. | Stated reading by Ray of `.claude/skills/session-start/references/spanner.md` § Working rules |
| AC5.1 | Both test suites pass. | `pytest` and `pytest automation/` each run as written and exit `0` |

## 6. Test plan

Omitted: no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes.

## 7. Risks and rollback

- **A quote does not match.** DR1 stops the step. Rollback: none needed.
- **The new §4 wording conflicts with #243's review.** #243 checks for a §4 entry with no recorded stop and, per Ray, each `within approved meaning` row for a change of meaning; the `Step stopped at` values are what it reads. Rollback: revert Step 1's commit.
- **Removing §6.4 leaves a case uncovered.** A spec-named file that does not exist is emitted as a discrepancy by `.claude/skills/session-start/references/anvil.md` before step 1, and on the direct path a file the spec names that does not exist is a change to the file set, which Step 4b stops. Rollback: revert Step 2's commit.
