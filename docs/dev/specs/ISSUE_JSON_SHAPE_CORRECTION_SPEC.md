# Issue JSON Shape Correction — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20260831
**Branch:** `chore/issue-105-88-issue-json-shape` (from `main`)
**Target release:** n/a — `chore/*` carries no release (`docs/DEVELOPMENT_STANDARDS.md` §2.2)
**Originating item:** Issues #105 and #88
**Design study:** `n/a` — direct path, no recon was run

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260831 | Ray | Both issues complete on one branch — each issue's own body says so, and both rewrite the same four files | One spec, one branch. AC ids are prefixed by originating issue (`AC105.n`, `AC88.n`) so close-out's `^\| AC[0-9]+\.[0-9]+ \|` parse still reads them |
| 20260831 | Ray | **The `type` key does not get renamed, it gets deleted.** A separate key that exists only to be emitted as `--label` is unneeded machinery | §4 Step 2. The rule reads off `labels` |
| 20260831 | Ray | **Milestone plus a pair label is not an error.** An unscheduled issue gets one of `gap`/`defect`; when it is later pulled into a milestone the label stays. All validation runs at creation, and the pair exists for Ray's own searching | `validate_type_rule`'s second half is deleted outright, not relocated. DR2 |
| 20260831 | Spanner | §1.3's current *"A discriminator appearing inside a milestone means that work was pulled in from the unscheduled pool later"* reads as permission at creation, while the shipped validator rejects that state. `docs/archive/specs/ISSUE_CREATION_VALIDATION_SPEC.md` C6 recorded the clause as meaning "not an error" and shipped a validator that errors anyway | Resolved by Ray's decision above. §1.3 restates it as what it is — an observation about issues already on the board. Wording approved by Ray, 20260831 |
| 20260831 | Spanner | `parse_type_labels` locates the pair by matching the literal phrase `discriminator pair` in §1.3, so the approved §1.3 rewording changes the string the parser looks for. `docs/archive/results/CLOSEOUT_STANDARDIZATION_RESULTS.md` deviation 8 records a §1.3 reflow that took `pytest automation/` red at import time by exactly this route | The standards line and the parser constant are one atomic change and ship as Step 1 together, not as two steps either of which leaves the suite red |
| 20260831 | Spanner | Proposed an added predicate requiring at least one non-pair label in `labels`, since merging the pair into `labels` lets `["defect"]` satisfy `min_items: 1` with no area label | **Not taken** — Ray, 20260831. The labels are for his own searching and the guarantee is not worth the rule |
| 20260831 | Ray | #88's single-line refusal extends beyond `acs` | Every string-typed value is single-line; `context` is the sole exception, being the issue body's prose. One schema flag covers `title`, `milestone`, `labels[]` and `acs[]`. DR4 |
| 20260831 | Spanner | #105's third AC still ends *"and an issue with a milestone carries neither"*, which is the rule Ray struck in the same session | The approved §1.3 wording governs the standards text; the residual clause is superseded by Ray's 20260831 direction and is not implemented. Recorded here so it is not re-raised. `AC105.3` is written to the approved wording |
| 20260831 | Spanner | #105's tenth AC reads *"neither `gap` or `defect` labels fails validation, naming both"*, duplicating the ninth. *"naming both"* is unambiguous about intent | Read as the both-labels-present case. `AC105.10` states it that way |
| 20260831 | Spanner | #105's twelfth AC says *"each of the four cases above"* where three bullets now stand | Four cases are tested: none, both, exactly one, and milestone-with-a-pair-label validating — the fourth being what Ray's §1.3 wording newly permits and the only case with no test today |

---

## 1. Scope

**In scope:**

- `docs/DEVELOPMENT_STANDARDS.md` §1.3 — the two bullets carrying the label pair and the GitHub Type field, reworded to the text Ray approved on 20260831.
- `.github/ISSUE_TEMPLATE/issue.schema.json` — the top-level `type` key removed; a `single_line` constraint added.
- `.github/ISSUE_TEMPLATE/issue.template.json` — the `type` key removed.
- `automation/issue_validator.py` — the label pair read from `labels`; every `type`-named symbol removed; single-line enforcement added to `validate_schema`.
- `automation/fixtures/**` — the `type` key removed from all seventeen JSON fixtures, five filenames retired, three fixtures added, two standards fixtures updated.
- `automation/issue_validator_test.py` — tests updated to the new signatures and four label-pair case tests plus single-line tests added.
- `../results/ISSUE_JSON_SHAPE_CORRECTION_RESULTS.md` — written at Step 5.

**Out of scope:**

- Anything under `workmain/**`, `tests/**`, `scripts/**`, `config/**` or `templates/**`. This branch touches none of them, which is what keeps it `chore/*` under §2.2 with no proof-method clause needed.
- `automation/closeout_acs.py` and `.claude/skills/closeout/**`. Neither reads the issue schema or the validator — verified by `grep -rln 'issue_validator\|issue.schema' .claude/ docs/` returning zero hits outside `docs/archive/`.
- Renaming any label on GitHub. `defect` and `gap` are live and stay live.
- Requiring an area label alongside the pair — declined by Ray, see the Decision Log.
- `docs/archive/**`. `docs/archive/specs/ISSUE_CREATION_VALIDATION_SPEC.md` AC2.6 is superseded by this spec, not edited; §1.5 forbids updating an archived artifact.

## 3. Design rules

- **DR1 — The pair is parsed from §1.3, never hardcoded.** `docs/archive/specs/ISSUE_CREATION_VALIDATION_SPEC.md` AC2.6 established this so the names cannot go stale, and that reason is unchanged. No string literal `"defect"` or `"gap"` appears in `automation/issue_validator.py`.
- **DR2 — One rule governs the pair: an issue with no milestone carries exactly one of it.** An issue with a milestone is not checked against the pair at all — carrying one is the normal record of work pulled in from the unscheduled pool. There is no second rule and no rule about where the pair may appear, because it appears in `labels` like every other label.
- **DR3 — The parse anchor and §1.3 are one contract.** The phrase `parse_label_pair` matches must exist in §1.3 on a line whose only backticked tokens are the pair itself. Changing either side without the other breaks `pytest automation/` at import, since the pair is computed at module scope in the test file.
- **DR4 — Every string a key contributes is a single line; `context` is the sole exception.** Declared per key in the schema, enforced in `validate_schema`, so it is inside total reporting by construction.
- **DR5 — Total reporting (`docs/archive/specs/ISSUE_CREATION_VALIDATION_SPEC.md` DR4) is preserved.** Every check appends to one error list and the run reports all of them. The one exception stays the §1.3 parse itself, which raises `ValidationAbort` before any other check.
- **DR6 — Refusal, not repair.** A malformed value is rejected at validation. `render_body()` is not changed, and nothing normalizes, joins or strips a newline into shape.

When something is not covered here, `CLAUDE.md` Role 3 escalation applies: stop at the step, document it, bring it to Ray.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps. Every step leaves `pytest automation/` green; the step boundaries were chosen for that reason (DR3).

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | §1.3 reworded and the parse anchor moved with it, atomically | `docs/DEVELOPMENT_STANDARDS.md`, `automation/issue_validator.py`, `automation/fixtures/standards_alpha_beta.md`, `automation/fixtures/standards_missing_label_pair.md`, `automation/issue_validator_test.py` |
| 2 | The `type` key deleted end to end | `.github/ISSUE_TEMPLATE/issue.schema.json`, `.github/ISSUE_TEMPLATE/issue.template.json`, `automation/issue_validator.py`, all `automation/fixtures/*.json`, `automation/issue_validator_test.py` |
| 3 | The four label-pair cases, each with its own named test | `automation/fixtures/shape_invalid_unscheduled_both_pair_labels.json`, `automation/issue_validator_test.py` |
| 4 | Single-line enforcement across every string-typed key | `.github/ISSUE_TEMPLATE/issue.schema.json`, `automation/issue_validator.py`, two new fixtures, `automation/issue_validator_test.py` |
| 5 | Results artifact | `../results/ISSUE_JSON_SHAPE_CORRECTION_RESULTS.md` |

### Step 1 — §1.3 and the parse anchor

In `docs/DEVELOPMENT_STANDARDS.md` §1.3, replace these three lines:

```text
- Labels carry area. `defect`/`gap` is the discriminator pair, applied only to issues with no milestone.
  - A **defect** is work the project asserted already worked — a spec acceptance criterion, a CHANGELOG entry, a man page — and does not. A **gap** is work never planned, documented, or designed.
  - A discriminator appearing inside a milestone means that work was pulled in from the unscheduled pool later, not planned as part of it.
```

with:

```text
- Labels carry area, and `defect`/`gap` is the label pair that says what an unscheduled issue is. An issue with no milestone carries exactly one of them.
  - A **defect** is work the project asserted already worked — a spec acceptance criterion, a CHANGELOG entry, a man page — and does not. A **gap** is work never planned, documented, or designed.
  - The pair is not removed when an issue is later pulled into a milestone. A milestone carrying one means that work came from the unscheduled pool rather than being planned as part of it.
```

and replace this line:

```text
- The Github type field is not utilized.
```

with:

```text
- GitHub's native issue Type field is not used, and cannot be: Types are an organisation-level feature, so `Repository.issueTypes` is null for this repository and `gh issue create --type` is inert. `defect` and `gap` are ordinary labels and travel as `--label`.
```

The first replacement bullet is the parse anchor. Its only backticked tokens are `defect` and `gap`; the Type-field bullet backticks other tokens but is never reached, because the parse takes the first matching line in the section.

In `automation/issue_validator.py`:

- `DISCRIMINATOR_PHRASE = "discriminator pair"` becomes `LABEL_PAIR_PHRASE = "label pair"`.
- `parse_type_labels` is renamed `parse_label_pair`, with its three uses of the old constant and both `ValidationAbort` messages carrying the new one.
- The module docstring's *"the §1.3 discriminator-pair rule"* and *"so the discriminator pair lives only in `docs/DEVELOPMENT_STANDARDS.md` §1.3"* are reworded to say label pair. The docstring's statement of why — `Repository.issueTypes` is null — stays, and is now the same fact §1.3 states.
- `ValidationAbort`'s docstring *"Raised when the §1.3 discriminator parse itself fails"* becomes *"Raised when the §1.3 label-pair parse itself fails"*.

In `automation/fixtures/standards_alpha_beta.md`, the line reading ``- Labels carry area. `alpha`/`beta` is the discriminator pair, applied only to`` becomes ``- Labels carry area, and `alpha`/`beta` is the label pair that says what an unscheduled issue is. An issue with no``. `automation/fixtures/standards_missing_discriminator.md` is renamed `standards_missing_label_pair.md`; its content is already free of the phrase and does not change.

In `automation/issue_validator_test.py`, `TYPE_LABELS` becomes `LABEL_PAIR`, the two module-level and in-test `parse_type_labels` calls become `parse_label_pair`, and `test_ac2_8_missing_discriminator_line_aborts_before_other_checks` is renamed to name the label pair and asserts on the new filename and the phrase `label pair`.

### Step 2 — delete the `type` key

`issue.schema.json`: the top-level `type` block is deleted. The per-key `"type"` datatype declarations on the other eight keys are untouched — they are the datatype, not the deleted key.

`issue.template.json`: the `"type": null` line is deleted.

`automation/issue_validator.py`:

- `validate_type_rule(data)` becomes `validate_label_pair_rule(data, label_pair)`. It returns no errors when `milestone` is not `None`. Otherwise it counts the members of `label_pair` present in `data["labels"]`: none reports that the issue carries none of them, naming the pair; more than one reports that it carries more than one, naming each present label.
- `validate_labels_not_type` is deleted. Its rule is not relocated — with the pair inside `labels` there is nothing left to check.
- `validate_live_state` loses its `type_labels` parameter and the whole `type_value` block. The existing `labels` loop already checks pair-label existence against live GitHub state, because the pair now travels in `labels`.
- `build_command` loses the `if data.get("type") is not None:` branch. The pair leaves through the existing `--label` loop.
- `validate_issue`'s third parameter is renamed `label_pair` and is passed to `validate_label_pair_rule`, no longer to `validate_live_state`.
- `main` renames its local `type_labels` to `label_pair`.

All seventeen `automation/fixtures/*.json`: the `"type"` line is deleted from each, and where its value was not `null` that value is appended to the `labels` array. Then:

- `ac2_4_type_label_in_labels.json` is **deleted**, not renamed. It exists to prove a pair label inside `labels` is an error, and that is now the correct form. Its filename is one of the five #105 names, and this is the reason the rename count reads four rather than five.
- `shape_invalid_scheduled_with_type_child.json` → `shape_scheduled_with_pair_child.json` and `shape_invalid_scheduled_with_type_standalone.json` → `shape_scheduled_with_pair_standalone.json`. Both stop being invalid: they are the milestone-plus-pair case Ray's §1.3 wording describes.
- `shape_invalid_unscheduled_no_type_child.json` → `shape_invalid_unscheduled_no_pair_child.json` and `shape_invalid_unscheduled_no_type_standalone.json` → `shape_invalid_unscheduled_no_pair_standalone.json`. These stay invalid.
- `ac2_7_three_errors.json` needs no new content. Its three errors survive the transform intact: the unknown key `extra_bogus_key`, the label `not-a-real-label` that is not live, and — with `"type": null` gone and no pair member in `labels` — an unscheduled issue carrying none of the pair.

`automation/issue_validator_test.py`: `test_ac2_4_type_label_inside_labels_fails` is deleted with its fixture. `TestAC1`'s two loops move the two renamed scheduled fixtures into the passing set. `TestAC2`'s `test_ac2_3` assertions are rewritten to the new messages. Both `test_ac2_9_*` tests drop the now-absent positional argument from their `validate_live_state` calls. `test_ac2_7` drops its `"type label"` assertion and asserts the missing-pair error instead. `test_ac3_2` still expects three `--label` occurrences, since `valid_full.json`'s two labels plus its former type value are now three labels.

### Step 3 — the four cases

Add `automation/fixtures/shape_invalid_unscheduled_both_pair_labels.json`: no milestone, `labels` carrying an area label and both pair members.

Add four tests to `automation/issue_validator_test.py`, each named for its case and each asserting the specific message, not merely that errors exist:

- no milestone and neither pair label fails, naming what is missing
- no milestone and both pair labels fails, naming both
- no milestone and exactly one pair label validates, and `build_command`'s output carries that label among its `--label` flags
- a milestone with a pair label validates, carrying no pair error

### Step 4 — single line

`issue.schema.json`: `"single_line": true` is added to `title`, `milestone`, `labels` and `acs`. `context` does not carry it. On a string-typed key the flag constrains the value; on an array-of-string key it constrains every item. That is one flag with one meaning — every string the key contributes is a single line.

`automation/issue_validator.py`, in `validate_schema`:

- The `expected == "string"` branch gains a check appending `key '<key>' must be a single line` when the flag is set and the value contains `\n` or `\r`.
- The per-item loop in the `expected == "array"` branch gains a further `elif` appending `key '<key>[<i>]' must be a single line` on the same condition. The index is in the message, which is what #88 asks for.

Both live inside `validate_schema`, which is already the first call in `validate_issue`'s error accumulation, so the refusal participates in total reporting with nothing further to wire (DR4, DR5).

`render_body()` is not touched (DR6).

Add `automation/fixtures/single_line_newline_in_ac.json` and `automation/fixtures/single_line_newline_in_title.json`, each otherwise valid.

Add tests: the AC fixture fails with an error naming `acs[1]`; the title fixture fails naming `title`; `valid_minimal.json` and `valid_full.json` still validate clean; and one test asserting a file carrying both a newline AC and a second unrelated error reports both, which is DR5 at this new check.

### Authorization points

**This spec contains none.** Nothing here executes a migration, deletes a GitHub object, force-pushes, or changes a live service's run state. The merge to `main` is an authorization point, but it belongs to `/closeout`, which stops at it — not to a step in this spec.

## 5. Acceptance criteria

`AC105.n` and `AC88.n` map to the nth acceptance criterion on issues #105 and #88 respectively. Commands are run from the repository root.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC105.1 | The schema declares no key named `type` | `python3 -c "import json;print('type' in json.load(open('.github/ISSUE_TEMPLATE/issue.schema.json')))"` prints `False` |
| AC105.2 | The template carries no `type` key, and the skeleton's keys match the schema's | `python3 -c "import json;print('type' in json.load(open('.github/ISSUE_TEMPLATE/issue.template.json')))"` prints `False`; `pytest automation/issue_validator_test.py::TestSchema::test_new_skeleton_matches_schema_keys` passes |
| AC105.3 | §1.3 states the rule against labels — an issue with no milestone carries exactly one of `defect`/`gap` in its labels — using neither the word `type` nor the word `discriminator` | Ray reads the Step 1 replacement text; mechanically, `sed -n '/^### 1.3/,/^### 1.4/p' docs/DEVELOPMENT_STANDARDS.md \| grep -ci 'discriminator'` prints `0` |
| AC105.4 | §1.3's Type-field line states why the field is unavailable — an organisation-level feature, `Repository.issueTypes` null — so the fact lives outside a recon | `sed -n '/^### 1.3/,/^### 1.4/p' docs/DEVELOPMENT_STANDARDS.md \| grep -c 'Repository.issueTypes'` prints `1` |
| AC105.5 | The pair is parsed from §1.3, not hardcoded (DR1) | `grep -nE "['\"](defect\|gap)['\"]" automation/issue_validator.py` returns zero hits, and `pytest automation/issue_validator_test.py -k live_standards_file` passes, asserting the live parse returns exactly `['defect', 'gap']` |
| AC105.6 | No `type`-named symbol survives | `grep -rn "parse_type_labels\|validate_type_rule\|validate_labels_not_type\|type_labels\|type_value\|TYPE_LABELS" automation/ .github/` returns zero hits |
| AC105.7 | `validate_labels_not_type` no longer exists in any form and its rule is not relocated | `grep -rn "labels must not contain" automation/` returns zero hits; covered by AC105.6's grep for the symbol itself |
| AC105.8 | `build_command` emits the pair through the same `--label` loop as area labels, and no path passes `--type` | `grep -n 'data\["type"\]' automation/issue_validator.py` returns zero hits; `pytest automation/issue_validator_test.py::TestAC3::test_ac3_4_type_flag_is_never_passed` passes |
| AC105.9 | No milestone and neither pair label fails validation, naming what is missing | The Step 3 test for that case passes, asserting the message names the pair |
| AC105.10 | No milestone and both pair labels fails validation, naming both | The Step 3 test for that case passes, asserting both label names appear in the message |
| AC105.11 | No milestone and exactly one pair label validates, and the printed command carries that label among its `--label` flags | The Step 3 test for that case passes, asserting `errors == []` and the label's presence in `build_command`'s output |
| AC105.12 | Each of the four cases has its own test, named for the case it covers | `pytest automation/issue_validator_test.py -k TestLabelPairCases -v` lists four tests, all passing — the three above plus the milestone-with-a-pair-label case |
| AC105.13 | No fixture declares a `type` key, and every fixture that carried a non-null one now carries that value in `labels` | `grep -rn '^  "type"' automation/fixtures/` returns zero hits; the Step 2 fixture set is the evidence for the second half, recorded per file in the results artifact |
| AC105.14 | No fixture filename contains `type` | `ls automation/fixtures/ \| grep -c type` prints `0`. Four of the five are renamed; `ac2_4_type_label_in_labels.json` is deleted, its case having become the correct form — see the Decision Log |
| AC105.15 | `pytest automation/` passes, with the count recorded against the baseline | `pytest automation/ -q`; baseline 41 passed, recorded in the results artifact §5 |
| AC105.16 | `pytest` passes at or above the CHANGELOG baseline, and nothing under `workmain/**` or `tests/**` is touched | `pytest -q` reports 934 or more passed; `git diff --name-only main...HEAD \| grep -E '^(workmain\|tests)/'` returns zero hits |
| AC88.1 | A newline inside an `acs` item is rejected, naming the offending item's index | The Step 4 test passes, asserting an error containing `acs[1]` |
| AC88.2 | The rejection participates in total reporting — it does not stop the run before other errors are collected | The Step 4 total-reporting test passes, asserting both the newline error and a second unrelated error are present in one run |
| AC88.3 | A fixture with a newline inside an AC exits non-zero; the existing valid fixtures still exit zero | The Step 4 tests over `single_line_newline_in_ac.json`, `valid_minimal.json` and `valid_full.json` pass |
| AC88.4 | Both are covered in `automation/issue_validator_test.py`, with the test name carrying what it covers | `pytest automation/issue_validator_test.py -k single_line -v` lists the Step 4 tests by name, all passing |
| AC88.5 | `render_body()` is unchanged — the fix is refusal at validation, not repair at render (DR6) | `git diff main...HEAD -- automation/issue_validator.py \| grep -c '^[-+].*render_body'` prints `0`, and the function body is absent from the diff |

Ray verifies AC105.3 and AC105.4 semantically, per `docs/DEVELOPMENT_STANDARDS.md` §1.2. The greps beside them check the mechanical half only.

## 6. Test plan

- **Baseline before this work:** `pytest` 934 passed, 0 failed — last CHANGELOG.md entry, per `docs/DEVELOPMENT_STANDARDS.md` §6. `pytest automation/` 41 passed, measured on `main` at authoring time.
- **Expected after:** `pytest` flat at 934 — no file under `workmain/**` or `tests/**` is touched. `pytest automation/` at 41 − 1 + 9 = 49: one test deleted with its fixture at Step 2, four label-pair case tests added at Step 3, five single-line tests added at Step 4.
- All additions land in `automation/issue_validator_test.py`, the established file for this module. `automation/closeout_acs_test.py` is not touched.
- Coverage added: the four label-pair cases at the `validate_issue` boundary and, for the passing case, through `build_command`; the single-line refusal on an `acs` item and on `title`; its participation in total reporting; and the two valid fixtures as the negative control.

## 7. Risks and rollback

- **A §1.3 reflow breaks every issue creation.** This is the branch's only real hazard and it has fired before — `docs/archive/results/CLOSEOUT_STANDARDIZATION_RESULTS.md` deviation 8. Mitigated by DR3's atomic Step 1 and by the existing regression test over the live standards file, which fails loudly rather than silently. Rollback is `git revert` of Step 1's single commit; the phrase and the parser move back together.
- **A fixture rename that misses a reference** leaves a test loading a path that no longer exists. It fails immediately and visibly at collection, not silently. Rollback is the Step 2 commit.
- **Widening single-line beyond `acs` could reject an existing valid fixture** — for example a `context` value spanning lines, which is why `context` is exempt. The two valid fixtures are asserted clean as the negative control (AC88.3). Rollback is the Step 4 commit.
- **Blast radius is bounded to issue creation.** Nothing on this branch is imported by the application, the daemon or the CLI; the only consumer is a developer running `python3 automation/issue_validator.py`. A defect here cannot reach runtime behaviour, which is what makes `chore/*` correct under §2.2 with no proof-method clause required.
- Every step is one commit and each is independently revertible. The branch has not been pushed, so a full abandon is a local branch delete, which §2.3 states is not a GitHub object deletion and not an authorization point.
