# Documentation Direct Path — Spec

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20260828
**Branch:** `chore/issue-113-documentation-direct-path` (from `main`)
**Target release:** n/a — `chore/*` carries no version bump, tag or Release (§2.2)
**Originating item:** Issue #113, child of #80
**Design study:** n/a — direct path, no recon was run

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260828 | Spanner | Issue AC9 as first written claimed no close-out change was needed, but `P5a` fails on a missing `**Design study:**` field with `n/a when: never`, and `references/chore.md` step 1 sets a design artifact unconditionally. AC9 and AC3 could not both stand | Ray took option A: the direct path carries no design artifact, and `P5a` gains one stated `n/a` condition. AC9 replaced with two ACs; AC3 and AC8 extended. Step 4 |
| 20260828 | Spanner | Which sections a direct-path spec may omit — AC8 says "sections", plural, and only §2 is named by AC5 | §2 and §6. §6 is omittable only where the change touches no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` — `P8` and `P9` still run at close-out regardless. Every other section is required. Step 3 |
| 20260828 | Spanner | Issue AC11's command is `grep -n "Recon before spec" … .claude/`, which errors on a directory without `-r` | The spec's AC checks the same thing with `grep -rn`. The intent is unchanged; the quoted form could not have run |
| 20260828 | Spanner | §2.7 step 3 could back-cite §1.1 so the reader is pointed at the path from the branch decision | Not taken. §1.1 cites §2.2 and §2.7; a back-citation would make §2.7 a second place stating the discriminator. §1.1 owns it |
| 20260828 | Ray | Handing a direct-path spec to Role 3 is needless overhead and a fresh chance to get it wrong — the steps already quote the exact replacement text, so Anvil would transcribe, not implement | The direct path's implementer is Role 1, in the session that wrote the spec. §1.1 says so and states the cost: with no recon, no Caliper pass and no separate implementer, Ray's approval is the path's only review. **No AC on #113 covers this** — it is carried as a deviation in the results artifact §4 at Ray's direction, and checked by AC4.1. Step 1 |
| 20260828 | Ray | Today's §1.2 requires a Role 2 pass before approval, and step 2 is what makes that optional on the direct path — so this spec is owed a Caliper round under the rule it is replacing | Waived, at Ray's direction, as the first exercise of the rule. Recorded here rather than left as a silent omission. Carried as a deviation in the results artifact §4 |
| 20260828 | Ray | Step 5 surfaced that `_TEMPLATE_RESULTS.md` §3 names Anvil as the only possible author of the AC table, which deviation 1 makes false on the direct path. Offered as a follow-up for the next `chore/*` | Fix it on this branch. Added as step 6 after steps 1–5 had shipped. No AC on #113 covers it — carried as a deviation in the results artifact §4 and evidenced there, not given an `ACn.m` id it could not honestly map to |
| 20260828 | Spanner | This spec is written in the form it defines — no recon, `**Design study:** n/a`, no §2 table — before the rule permitting that form has shipped | Deliberate, and required by AC12. The standards are being written by this issue; the spec is its own first use |

---

## 1. Scope

**In scope:**

- `docs/DEVELOPMENT_STANDARDS.md` §1.1 — heading and body, rewritten to define two paths.
- `docs/DEVELOPMENT_STANDARDS.md` §1.2 — the verification-form rule and the Role 2 review rule, each scoped to a path.
- `docs/dev/specs/_TEMPLATE_SPEC.md` — the `**Design study:**` header line and a direct-path note naming the omittable sections.
- `.claude/skills/closeout/SKILL.md` — the `P5a` row only.
- `.claude/skills/closeout/references/chore.md` — step 1 only.
- `docs/dev/results/DOCUMENTATION_DIRECT_PATH_RESULTS.md` — new.

**Out of scope, and why:**

- **`automation/**`.** `closeout_acs.py` reads the spec's `**Branch:**` field, derives the results path from the spec filename, and compares AC ids. None of that reads the `**Design study:**` field or the §2 table. A direct-path spec is the same shape to it. AC10 asserts this; no edit delivers it.
- **`CLAUDE.md`.** Its one §1.1 citation is "No implementation without an approved spec" (`CLAUDE.md:19`), which stays true on both paths. Editing it would put the discriminator in a second place.
- **`P4`, `P5`, `P6`, `P7` and every other preflight row.** Verified against `.claude/skills/closeout/SKILL.md:30-41`: none of them reads the design artifact. Only `P5a` does.
- **§1.5's artifact rules, §2.2's branch definitions, §2.7's checklist.** This issue keys the path off rules those sections already own. Restating any of them here would break the single-owner rule.
- **The word "gate", `docs/archive/**`, and shipped specs that quote the old §1.1.** Archived and shipped artifacts are the record of what was true when written (§1.5) and are not retrofitted.

## 2. Verified current state

Omitted — direct path, per §1.2 as this spec amends it. The text being replaced is quoted inline in the step that replaces it, at the line numbers it holds on `main` at this branch's point.

## 3. Design rules

- **DR1 — The discriminator is the branch type and nothing else.** `chore/*` → direct path; `feature/*` and `hotfix/*` → full path. No file-path test, no size test, no judgement call. Where a reader would have to weigh anything, the wording is wrong.
- **DR2 — The discriminator is stated in exactly one place: §1.1.** §1.1 cites §2.2 for what `chore/*` covers and §2.7 for when the branch type is chosen. Neither of those sections gains a restatement.
- **DR3 — Nothing on the direct path is optional except the recon and the Role 2 pass.** Spec, Ray's explicit approval, results artifact and close-out are all required, and §1.1 says so in those words.
- **DR4 — The verification principle does not change; only its form does.** No claim about existing state is asserted unverified on either path. The full path carries the §2 table; the direct path quotes the text being replaced inside the step that replaces it.
- **DR5 — `**Design study:** n/a` is a stated form, not an absence.** `P5a` accepts it only on a `chore/*` spec and only as that exact string; every other missing or broken citation fails exactly as it does today.
- **DR6 — Existing text is edited surgically.** Bullets that are still correct on both paths keep their present wording; only what the two paths differ on is restructured.

Anything this spec does not cover: stop at the step and escalate per `CLAUDE.md` Role 3. Do not self-resolve.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | §1.1 rewritten — heading, two paths, discriminator, direct-path recon rule | `docs/DEVELOPMENT_STANDARDS.md` |
| 2 | §1.2 — verification form and Role 2 review each scoped to a path | `docs/DEVELOPMENT_STANDARDS.md` |
| 3 | Spec template — `**Design study:**` form and the direct-path note | `docs/dev/specs/_TEMPLATE_SPEC.md` |
| 4 | `P5a` gains its one `n/a` condition; `chore.md` step 1 made conditional | `.claude/skills/closeout/SKILL.md`, `.claude/skills/closeout/references/chore.md` |
| 5 | Results artifact written and §3 filled against delivered text | `docs/dev/results/DOCUMENTATION_DIRECT_PATH_RESULTS.md` |
| 6 | Results template §3 no longer names Anvil as the only possible author of the AC table | `docs/dev/results/_TEMPLATE_RESULTS.md` |

### Step 1 — §1.1

**Replace this, in full** (`docs/DEVELOPMENT_STANDARDS.md:11-26` on `main` at branch point):

````markdown
### 1.1 Recon before spec

No spec is written without a read-only audit first. Recon produces a findings document in `docs/dev/design/`; decisions are made from it; only then is a spec written.

```text
RECON  →  ANALYSIS  →  SPEC  →  REVIEW  →  APPROVAL  →  IMPLEMENTATION  →  CLOSE-OUT
```

- **Recon** — read-only pass, verbatim findings, no fixes and no inline suggestions.
- **Analysis** — Ray plus Role 1 decide; decisions are logged.
- **Spec** — written to `docs/dev/specs/`.
- **Review** — Role 2 findings go back to Role 1, never forward to the implementer.
- **Approval** — Ray approves explicitly. No implementation without an approved spec.
- **Implementation** — Role 3, step by step, from the approved spec only.
- **Close-out** — Ray runs the `/closeout` skill against the branch being closed out, or `--branch <name>` for one already merged. It performs the merges, artifact completion, and whatever version bump, tag, Release and service restart its branch type requires, stopping at each authorization point it crosses. It composes the issue's closing comment and prints the command that would post it; posting the comment and closing the issue are Ray's, on the same principle as merging the `dev → main` PR.
````

**With this:**

````markdown
### 1.1 Two paths through the cycle

There are two paths, and **the branch type is which one applies**. §2.7 step 3 already makes that the first decision of any session, so by the time work starts the path is settled and no further judgement is needed.

- **`feature/*` and `hotfix/*` → the full path.** The change alters application behaviour.
- **`chore/*` → the direct path.** §2.2 defines what `chore/*` covers: `docs/**`, standards documents, `.claude/`, and dev tooling that changes no application behaviour.

**Full path**

No spec is written without a read-only audit first. Recon produces a findings document in `docs/dev/design/`; decisions are made from it; only then is a spec written.

```text
RECON  →  ANALYSIS  →  SPEC  →  REVIEW  →  APPROVAL  →  IMPLEMENTATION  →  CLOSE-OUT
```

- **Recon** — read-only pass, verbatim findings, no fixes and no inline suggestions.
- **Analysis** — Ray plus Role 1 decide; decisions are logged.
- **Spec** — written to `docs/dev/specs/`.
- **Review** — Role 2 findings go back to Role 1, never forward to the implementer.
- **Approval** — Ray approves explicitly. No implementation without an approved spec.
- **Implementation** — Role 3, step by step, from the approved spec only.
- **Close-out** — Ray runs the `/closeout` skill against the branch being closed out, or `--branch <name>` for one already merged. It performs the merges, artifact completion, and whatever version bump, tag, Release and service restart its branch type requires, stopping at each authorization point it crosses. It composes the issue's closing comment and prints the command that would post it; posting the comment and closing the issue are Ray's, on the same principle as merging the `dev → main` PR.

**Direct path**

```text
SPEC  →  APPROVAL  →  IMPLEMENTATION  →  CLOSE-OUT
```

**All four are required.** Nothing on this path is optional except the two things named below as optional.

- **Spec** — written to `docs/dev/specs/`, from the same template. §1.2 states which sections it may omit and how it verifies existing state instead.
- **Approval** — Ray approves explicitly. No implementation without an approved spec.
- **Implementation** — Role 1, in the session that wrote the spec. A direct-path step quotes the exact replacement text, so there is nothing to hand off: a separate implementer would transcribe rather than implement, and a transcription is a new chance to get it wrong, not a second pair of eyes.
- **Close-out** — the same `/closeout` run, unchanged. A direct-path spec meets its preconditions as a full-path spec does.

**A recon is permitted on this path**, and earns its place when the change spans documents that may contradict each other — where a rule is stated in one place and cited or restated in others, and the change has to find every site before it can be specified. Run one where that is true; it produces a design artifact in `docs/dev/design/` exactly as on the full path.

**Where no recon is run, no design artifact exists** and the spec's `**Design study:**` field reads `n/a`. That is the stated form of a direct-path spec, not a requirement quietly skipped: `/closeout`'s `P5a` accepts `n/a` only on a `chore/*` spec, and fails every other missing or broken design-study citation exactly as before.

**What the direct path trades.** With no recon, no Role 2 pass and no separate implementer, **Ray's approval is the only review between the spec and the edit**, and scope that no acceptance criterion named is caught *after* implementation, by the results artifact's deviations table, rather than *before* it by recon and review. On a document that is recoverable — the text is there to read and the fix is another edit. On application code it is not, which is why the path is keyed on the branch type and not on how small the change looks.
````

### Step 2 — §1.2

**Replace these two bullets** (`docs/DEVELOPMENT_STANDARDS.md:30` and `:35` on `main` at branch point):

```markdown
- Every claim about existing behaviour is verified against source at authoring time — cite file and symbol. Asertions that were not verified are the most common spec defect.
```

```markdown
- At least one Role 2 review pass before a spec is approved.
```

**With, in their existing positions:**

```markdown
- Every claim about existing behaviour is verified against source at authoring time — cite file and symbol. Assertions that were not verified are the most common spec defect. This principle is the same on both paths; only its form differs.
  - **Full path:** the §2 verified-current-state table carries the citations.
  - **Direct path:** the §2 table is not required. The text being replaced is quoted inline in the step that replaces it, which *is* the verification — the claim and its evidence are the same lines, and a quote that no longer matches the file is caught the moment the edit is applied.
```

```markdown
- At least one Role 2 review pass before a spec is approved — on the full path. On the direct path a Caliper pass is optional and at Ray's discretion.
```

The corrected spelling of "Assertions" rides this edit; it is the same line.

### Step 3 — `_TEMPLATE_SPEC.md`

**Replace the header line:**

```markdown
**Design study:** `docs/dev/design/<file>.md`
```

**With:**

```markdown
**Design study:** `docs/dev/design/<file>.md` | `n/a` — direct path, no recon was run
```

**And add to the delete-before-use block, after the `Filename:` paragraph:**

```markdown
> **Direct path** (`chore/*` — `docs/DEVELOPMENT_STANDARDS.md` §1.1): §2 Verified current state is omitted; quote the text being replaced inline in the step that replaces it. §6 Test plan may be omitted where the change touches no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` — close-out still runs the suites regardless. Every other section is required, and this stays one template.
```

### Step 4 — the close-out skill

**Replace the `P5a` row** (`.claude/skills/closeout/SKILL.md:33`):

```markdown
| P5a | The design artifact named by the spec's `**Design study:**` field exists, and its `**Status:**` is one `docs/DEVELOPMENT_STANDARDS.md` §1.5 defines | never | No field: §1.1 permits no spec without a recon or design study first. Missing file: the citation is broken and the spec cannot be verified against what it was built from |
```

**With:**

```markdown
| P5a | The design artifact named by the spec's `**Design study:**` field exists, and its `**Status:**` is one `docs/DEVELOPMENT_STANDARDS.md` §1.5 defines | the branch prefix is `chore` and the spec's `**Design study:**` field reads `n/a` — the direct path with no recon, §1.1 | No field at all, or `n/a` on a `feature/*` or `hotfix/*` branch: §1.1 requires a recon on the full path and permits `n/a` only in the direct path's stated form. Missing file: the citation is broken and the spec cannot be verified against what it was built from |
```

**Replace `references/chore.md` step 1's Step and Done-when cells** (`.claude/skills/closeout/references/chore.md:7`):

```markdown
| 1 | Set the spec, the design artifact and the results artifact to `**Status:** Shipped`. Complete the results artifact: `**Released as:** n/a`, §5 suite results, live verification, and the restart's `n/a` reason. Commit on the branch, before any merge — §2.2 | The branch tip carries all three at `Shipped` and the results artifact's §5 is complete |
```

**With:**

```markdown
| 1 | Set the spec, the design artifact **where the spec names one**, and the results artifact to `**Status:** Shipped`. Complete the results artifact: `**Released as:** n/a`, §5 suite results, live verification, and the restart's `n/a` reason. Commit on the branch, before any merge — §2.2 | The branch tip carries the spec, the results artifact, and any design artifact the spec names, each at `Shipped`, and the results artifact's §5 is complete |
```

### Step 5 — results artifact

Write `docs/dev/results/DOCUMENTATION_DIRECT_PATH_RESULTS.md` from `_TEMPLATE_RESULTS.md`. §1 records that this issue is the first use of the direct path (AC12.1). §3 carries a row for every AC id in §5 below, each run against the delivered text. `**Released as:** n/a`.

### Step 6 — results template

**Replace this phrase** in `docs/dev/results/_TEMPLATE_RESULTS.md` §3:

```markdown
This table is written by Anvil as the last implementation step — he ran the ACs, so he is the only one who can fill it.
```

**With:**

```markdown
This table is written by whoever implemented the spec, as the last implementation step — Anvil on the full path, Role 1 on the direct path (`docs/DEVELOPMENT_STANDARDS.md` §1.1). They ran the ACs, so they are the only one who can fill it.
```

The header's `**Author:**` line already offers `Anvil (Role 3) | Spanner (Role 1)` and needs no change. Nothing else in the template names a role.

### Authorization points

Steps 1–5 contain **none**. Every edit is to a tracked file on a local branch that is never pushed (§2.3).

The one authorization point in this issue is at close-out: **merging to `main`** (§1.4). `/closeout`'s `chore` variant stops there and waits.

## 5. Acceptance criteria

Sub-ACs map to issue #113's ACs in order — `ACn.m` where `n` is the issue AC's position in its list.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | §1.1 defines two paths and names the branch type as the discriminator, citing §2.2 for what `chore/*` covers and §2.7 for when the type is chosen | Within `awk '/^### 1.1/,/^### 1.2/' docs/DEVELOPMENT_STANDARDS.md`: `grep -c 'the branch type is which one applies'` prints `1`, `grep -c '§2.2'` is ≥ `1`, `grep -c '§2.7 step 3'` is ≥ `1` |
| AC2.1 | §1.1 no longer opens with the unconditional recon sentence; it appears only under the full-path subheading | In the same range, the line `**Full path**` precedes the line containing `No spec is written without a read-only audit first`, and that sentence occurs exactly once |
| AC3.1 | §1.1 states that a recon is permitted on the direct path and when it earns its place | In the same range: `grep -c 'A recon is permitted on this path'` prints `1` and `grep -c 'may contradict each other'` prints `1` |
| AC3.2 | §1.1 states that where no recon is run, no design artifact exists and `**Design study:**` reads `n/a` | In the same range: `grep -c 'Where no recon is run'` prints `1` and `grep -c 'not a requirement quietly skipped'` prints `1` |
| AC4.1 | §1.1's direct path names all four of spec, approval, results artifact and close-out and states that they are required, names Role 1 as the implementer with the reason, and states that Ray's approval is the path's only review | In the same range: `grep -c '\*\*All four are required'` prints `1`, the direct-path block contains `**Spec**`, `**Approval**`, `**Implementation**` and `**Close-out**`, `grep -c 'Role 1, in the session that wrote the spec'` prints `1`, and `grep -c "only review between the spec and the edit"` prints `1` |
| AC5.1 | §1.2 states the §2 table is not required on the direct path and that the replaced text is quoted inline instead, with the principle unchanged | Within `awk '/^### 1.2/,/^### 1.3/' docs/DEVELOPMENT_STANDARDS.md`: `grep -c 'the §2 table is not required'` prints `1`, `grep -c 'quoted inline in the step that replaces it'` prints `1`, `grep -c 'only its form differs'` prints `1` |
| AC6.1 | §1.2 scopes the Role 2 pass to the full path and states it is optional and at Ray's discretion on the direct path | In the same range: `grep -c "on the full path"` is ≥ `1` and `grep -c "optional and at Ray's discretion"` prints `1` |
| AC7.1 | The §1.1 heading no longer names the rule it now conditions | `grep -c '^### 1.1 Recon before spec' docs/DEVELOPMENT_STANDARDS.md` prints `0` |
| AC8.1 | `_TEMPLATE_SPEC.md` names the omittable sections and gives the `**Design study:** n/a` form, and remains one template | Against `docs/dev/specs/_TEMPLATE_SPEC.md`: `grep -c 'direct path, no recon was run'` prints `1`, `grep -c '§2 Verified current state is omitted'` prints `1`, `grep -c '§6 Test plan may be omitted'` prints `1`; `ls docs/dev/specs/_TEMPLATE_*.md` returns exactly one file |
| AC9.1 | `P5a` names exactly one `n/a` condition — `chore/*` branch, `**Design study:**` reads `n/a` — and its remedy no longer states the recon requirement as unconditional | Against `.claude/skills/closeout/SKILL.md`: `grep -c 'P5a.*the branch prefix is'` prints `1`, `grep -c 'P5a.*permits no spec without a recon'` prints `0`, and `grep -c 'P5a.*never'` prints `0` |
| AC9.2 | `references/chore.md` step 1 sets the design artifact to `Shipped` only where the spec names one | `grep -c 'where the spec names one' .claude/skills/closeout/references/chore.md` prints `1` |
| AC10.1 | Nothing under `automation/**` changed, and no preflight row other than `P5a` changed | `git diff --name-only $(git merge-base main HEAD) HEAD -- automation/` returns empty; `git diff $(git merge-base main HEAD) HEAD -- .claude/skills/closeout/SKILL.md` touches only the `P5a` line |
| AC10.2 | A direct-path spec satisfies `P4`, `P5`, `P6` and `closeout_acs.py` unchanged — demonstrated by this issue's own close-out | `python3 automation/closeout_acs.py --branch chore/issue-113-documentation-direct-path` exits `0`; `pytest automation/` passes; the `/closeout` run reports `P4`, `P5`, `P6` as `pass` |
| AC11.1 | No live document describes the recon requirement as unconditional under that heading | `grep -rn "Recon before spec" docs/DEVELOPMENT_STANDARDS.md CLAUDE.md .claude/` returns no hits |
| AC12.1 | This issue ran on the direct path, and the results artifact records it as the first use | This spec's `**Design study:**` reads `n/a`, it has no §2 table, and no file was added under `docs/dev/design/` on this branch (`git diff --name-only $(git merge-base main HEAD) HEAD -- docs/dev/design/` returns empty); `docs/dev/results/DOCUMENTATION_DIRECT_PATH_RESULTS.md` §1 names it as the first use |

## 6. Test plan

No file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` is touched, so the suite is unchanged by this work.

- **Baseline:** whatever `pytest tests/` reports on `main` at this branch's point.
- **Expected after:** identical — same count, zero failures. A change in either is a defect in this spec, not a new baseline.
- `pytest automation/` must also pass. `closeout_acs.py` is untouched, so its suite is a regression check that AC10.1 held.
- Close-out's `P8` and `P9` run both suites regardless of what this section says.

## 7. Risks and rollback

| Risk | Blast radius | Mitigation |
| --- | --- | --- |
| The `P5a` `n/a` condition is too loose and a full-path spec ships with no design artifact | One issue closes out unverified against its recon | The condition tests the branch prefix as well as the field. A `feature/*` or `hotfix/*` spec writing `n/a` still fails, and AC9.1 checks that the remedy says so |
| The direct path is used for a change that turns out to touch application behaviour | A behaviour change ships with no recon and no review | §2.2 already forbids `chore/*` for application code, and §2.7 step 3 is where that is caught. This spec adds no new way to reach the direct path — it only names what `chore/*` already meant |
| §1.1's rewrite strands a citation elsewhere | A document points at a rule that no longer reads that way | Every live citation of §1.1 was checked: `CLAUDE.md:19` and `SKILL.md:31` state "no implementation without an approved spec", true on both paths; `SKILL.md:33` is step 4's own edit. Archived and shipped artifacts are the record of what was true when written (§1.5) and are not retrofitted |

**Rollback.** Five commits, each to markdown only, on a branch that is never pushed until it merges. `git revert` of any step's commit removes it with no migration, no schema change, no application code and no released version to unwind. Reverting step 4 alone restores `P5a`'s current behaviour, at which point a direct-path spec fails close-out again — steps 1–3 and step 4 revert together or not at all.
