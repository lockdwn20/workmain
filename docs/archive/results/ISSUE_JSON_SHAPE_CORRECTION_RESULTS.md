# Issue JSON Shape Correction — Implementation Results

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20260831
**Spec:** `../specs/ISSUE_JSON_SHAPE_CORRECTION_SPEC.md`
**Released as:** n/a — `chore/*` carries no release (`docs/DEVELOPMENT_STANDARDS.md` §2.2)

---

## 1. Summary

Complete. Both issues shipped on one branch, in five commits.

The `type` key is gone from the issue JSON. `defect` and `gap` are read off `labels` like every other label, and one rule governs them: an issue with no milestone carries exactly one of the pair. An issue *with* a milestone is no longer checked against the pair at all — a label kept after the work was scheduled is the normal record of something pulled in from the unscheduled pool, not an error to resolve. `validate_labels_not_type` is deleted rather than relocated, and `build_command` no longer has a second path to `--label`.

Separately, every string-typed value is now refused if it carries a line break, `context` excepted. The defect #88 describes is real and was reproduced against the shipped code before the fix: an AC authored with an embedded newline rendered as a bullet followed by a loose line belonging to no AC, so a created issue silently misrepresented its own AC list. `render_body()` is byte-identical to `main` — the fix is refusal at validation.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | §1.3's pair rule reworded off *discriminator*, and the phrase the parser matches moved with it in the same commit. The Type-field line now states why the field is unavailable. `parse_type_labels` → `parse_label_pair`, `DISCRIMINATOR_PHRASE` → `LABEL_PAIR_PHRASE` | `docs/DEVELOPMENT_STANDARDS.md`, `automation/issue_validator.py`, `automation/issue_validator_test.py`, 2 standards fixtures | 41, flat |
| 2 | The `type` key deleted from the schema, the template, all seventeen JSON fixtures and `build_command`. `validate_type_rule` → `validate_label_pair_rule` reading `labels`; `validate_labels_not_type` deleted; `validate_live_state` loses its pair parameter | `.github/ISSUE_TEMPLATE/*.json`, `automation/issue_validator.py`, `automation/issue_validator_test.py`, 17 fixtures | 40 (−1 deleted) |
| 3 | `TestLabelPairCases` — one named test per case: neither label, both labels, exactly one traced through to `build_command`'s `--label` flags, and a milestone carrying a pair label | `automation/issue_validator_test.py` | 44 (+4) |
| 4 | `single_line` declared on `title`, `milestone`, `labels`, `acs`; enforced in `validate_schema` via `_has_line_break`. `context` exempt | `.github/ISSUE_TEMPLATE/issue.schema.json`, `automation/issue_validator.py`, `automation/issue_validator_test.py`, 2 new fixtures | 50 (+6) |
| 5 | This artifact | `docs/dev/results/ISSUE_JSON_SHAPE_CORRECTION_RESULTS.md` | 50, flat |
| 6 | The at-most-one half of the pair rule ungated from the milestone, closing a scheduled issue carrying both labels | `automation/issue_validator.py`, `automation/issue_validator_test.py`, 1 new fixture | 51 (+1) |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC105.1 | Met | `python3 -c "import json;print('type' in json.load(open('.github/ISSUE_TEMPLATE/issue.schema.json')))"` prints `False` |
| AC105.2 | Met | The same probe over `issue.template.json` prints `False`; `TestSchema::test_new_skeleton_matches_schema_keys` passes, and a live `--new` emits the eight-key skeleton |
| AC105.3 | Met | §1.3 now reads *"Labels carry area, and `defect`/`gap` is the label pair that says what an unscheduled issue is. An issue with no milestone carries exactly one of them."* `sed -n '/^### 1.3/,/^### 1.4/p' docs/DEVELOPMENT_STANDARDS.md \| grep -ci 'discriminator'` prints `0`. Ray's semantic check outstanding at close-out |
| AC105.4 | Met | The Type-field bullet states the organisation-level cause and the null `Repository.issueTypes`; the same `sed` range greps `Repository.issueTypes` exactly once |
| AC105.5 | Met | `grep -nE "['\"](defect\|gap)['\"]" automation/issue_validator.py` returns zero hits; `test_the_live_standards_file_yields_exactly_the_label_pair` asserts `['defect', 'gap']` off the live file |
| AC105.6 | Met | `grep -rn "parse_type_labels\|validate_type_rule\|validate_labels_not_type\|type_labels\|type_value\|TYPE_LABELS" automation/ .github/` exits 1 with no output |
| AC105.7 | Met | The symbol is absent per AC105.6, and `grep -rn "labels must not contain" automation/` returns zero hits — the rule is deleted, not relocated |
| AC105.8 | Met | `grep -n 'data\["type"\]' automation/issue_validator.py` returns zero hits; `test_ac3_4_the_type_flag_is_never_passed` passes. Live run prints `--label process --label defect` through one loop |
| AC105.9 | Met | `test_label_pair_unscheduled_with_neither_label_fails_naming_what_is_missing`. Live: `unscheduled issue carries none of defect/gap`, exit 1 |
| AC105.10 | Met | `test_label_pair_unscheduled_with_both_labels_fails_naming_both`. Live: `unscheduled issue carries more than one of defect/gap: defect, gap`, exit 1 |
| AC105.11 | Met | `test_label_pair_unscheduled_with_exactly_one_label_validates_and_reaches_the_label_flags`. Live run exits 0 and prints the pair among the `--label` flags |
| AC105.12 | Met | `pytest automation/issue_validator_test.py -k TestLabelPairCases -v` → 5 passed, each named for its case: the four #105 names plus AC105.17's |
| AC105.13 | Met | `grep -rn '^  "type"' automation/fixtures/` returns zero hits. Eleven fixtures carried a non-null value; each now carries it in `labels` |
| AC105.14 | Met | `ls automation/fixtures/ \| grep -c type` prints `0`. Four renamed, one deleted — see deviation 2 |
| AC105.15 | Met | `pytest automation/ -q` → 51 passed, against a baseline of 41 measured on `main` |
| AC105.16 | Met | `pytest -q` → 934 passed, 0 failed, flat against the CHANGELOG baseline. `git diff --name-only main...HEAD \| grep -cE '^(workmain\|tests)/'` prints `0` |
| AC105.17 | Met | `test_label_pair_a_milestone_carrying_both_labels_still_fails` and `test_label_pair_unscheduled_with_both_labels_fails_naming_both` pass. Matrix re-run: milestone + `['defect','gap']` now fails with `issue carries more than one of defect/gap: defect, gap`, and every other row is unchanged |
| AC88.1 | Met | `test_single_line_newline_in_an_ac_is_refused_naming_the_index` asserts `key 'acs[1]' must be a single line` |
| AC88.2 | Met | `test_single_line_refusal_participates_in_total_reporting`. Live run reported the `title` and `acs[1]` refusals together in one invocation |
| AC88.3 | Met | `single_line_newline_in_ac.json` and `single_line_newline_in_title.json` fail; `test_single_line_the_valid_fixtures_are_unaffected` holds `valid_minimal.json` and `valid_full.json` clean |
| AC88.4 | Met | `pytest automation/issue_validator_test.py -k TestSingleLine -v` → 6 passed, each named for what it covers |
| AC88.5 | Met | `git diff main...HEAD -- automation/issue_validator.py \| grep -cE '^[-+].*def render_body'` prints `0`, and the function extracted from `git show main:` and `git show HEAD:` is byte-identical — see deviation 5 |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | `shape_invalid_unscheduled_both_pair_labels.json` was created at Step 2, not Step 3 as §4 states. `validate_issue`'s parameter rename likewise landed at Step 1, not Step 2 | Step 2's rewrite of `test_ac2_3` needs the fixture, and Step 1's call site in `main()` needs the parameter name. DR3's requirement that every step leave the suite green outranks the step a file is listed under | Spanner, 20260831 |
| 2 | Four fixture filenames renamed, one deleted — #105's AC reads *"the five that do are renamed"* | `ac2_4_type_label_in_labels.json` existed to prove a pair label inside `labels` was an error, which is now the correct form. It had no case left to test. Anticipated in the spec's Decision Log and stated at AC105.14 | Ray, 20260831 (Decision Log) |
| 3 | Renamed fixtures also had their `title` and `context` values rewritten, beyond the filename | Both narrated the deleted key — *"Invalid: scheduled standalone with a type label"* on a fixture that is now valid. A fixture whose own description contradicts what it tests is the defect #105 is about, one level down | Spanner, 20260831 |
| 4 | Six single-line tests, not the five §6 projected; final count 50, not 49 | The sixth asserts `context` is still accepted multi-line. Without it the exemption is undeclared in the tests, and a later tightening would pass | Spanner, 20260831 |
| 5 | Two AC check commands were corrected in the spec during implementation. AC105.12's `-k label_pair` matched 11 tests once the Step 1 renames landed, and was tightened to `-k TestLabelPairCases`. AC88.5's `grep -c '^[-+].*render_body'` returned 1 on a docstring *mention* in the new `_has_line_break` helper, and was replaced with a `def render_body` grep plus a byte-identity extraction | Both were loose checks that would have passed or failed for the wrong reason. The criteria themselves are unchanged; only how they are checked | Spanner, 20260831 |
| 6 | The spec said "fourteen JSON fixtures" in §1 and §4; there are seventeen | Miscounted at authoring time. Corrected in the spec at Step 2 | Spanner, 20260831 |
| 7 | **Step 6 and `AC105.17` were added after the first five steps shipped**, ungating the at-most-one half of the pair rule from the milestone. The error text drops the word *unscheduled*, since it now fires on scheduled issues too | Ray verified the shipped matrix and found a milestoned issue carrying both `defect` and `gap` passed. Gating that half on the milestone was a misreading of his direction: one kept label is the record of work pulled in from the unscheduled pool, two is incoherent regardless. `AC105.17` has no counterpart bullet on #105 yet — see §6 | Ray, 20260831 |

## 5. Verification

- **Test suite:** 934 passed, 0 failed (baseline was 934). `pytest automation/` 51 passed (baseline 41): one test deleted with its fixture, four label-pair cases added, six single-line tests added, one scheduled-both-labels case added at Step 6.
- **Live verification:** `automation/issue_validator.py` run against live GitHub label and milestone state, 20260831. `--new` emits the eight-key skeleton. A valid unscheduled issue exits 0 and prints `--label process --label defect` through one loop, with no `--type` anywhere. The three failure shapes exit 1 with the expected messages, and the newline probe reported its `title` and `acs[1]` refusals in a single run. **No issue was created** — `--create` was never passed.
- The #88 defect was reproduced against the shipped `render_body()` before the fix, returning `'...\n- single line AC\n- wrapped AC\nsecond physical line\n- third AC\n'` — the orphan line the issue describes.
- **Daemon restart:** not applicable. `chore/*` carries none (`docs/DEVELOPMENT_STANDARDS.md` §2.6), and nothing on this branch is imported by the application, the daemon or the CLI.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #105 | `AC105.17` is a criterion this branch meets that #105 does not yet state. The matching bullet to add: *"An issue carrying both `defect` and `gap` fails validation whatever its milestone, naming both."* | The criterion arose from Ray's verification after the spec was approved. Editing the issue body is Ray's, as merging and closing are |
