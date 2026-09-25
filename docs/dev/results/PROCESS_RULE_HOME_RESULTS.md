# A process rule has one home — Implementation Results

**Status:** Shipped — pending Ray's stated-reading confirmation on the criteria the spec assigns to him
**Author:** Anvil (Role 3)
**Date:** 20260925
**Spec:** `../specs/PROCESS_RULE_HOME_SPEC.md`
**Released as:** TBD

---

## 1. Summary

All seven steps are complete. Ray adjudicated every row of the census report at Step 4 (420 leave as is, 265 edit, 14 remove — no row left without a determination). Step 5 applied every edit and remove determination across 65 files; every leave-as-is row was left untouched. Step 6 deleted the `__main__` block from all 12 tracked test modules that carried one, and the five named in-module runners. Step 7 deleted the empty `CONTRIBUTING.md` and this artifact is complete. The suite is unchanged from the branch-point baseline: 992 passed, the same four named failures, `pytest automation/` unchanged at 51 passed.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | Branch-point baseline recorded below | `docs/dev/results/PROCESS_RULE_HOME_RESULTS.md` | n/a |
| 2 | The six standards edits (§4.1), verified to match exactly once each | `docs/DEVELOPMENT_STANDARDS.md` | unchanged |
| 3 | `scripts/rule_census.py` per DR8, run once; census report appended below. Explicit §1 pre-adjudications (claude.py:5, gemini.py:5, issue_validator.py:5-7, the three tracked shell scripts, fixtures/mocks/migrations directories, `intent_parse_system_prompt.txt`) transcribed into the Determination/Reason columns so Ray is not asked to re-decide a settled row | `scripts/rule_census.py`, census report in this file | n/a (no test added — §6, DR8's "nothing to test it for") |
| 4 | Ray adjudicated every census row: remove / edit / leave as is, with a reason recorded for every leave as is | census report below (Determination/Reason columns) | n/a |
| 5 | Every remove and edit determination applied. §4.2's three changes to `automation/issue_validator.py` (invocations moved to the argparse epilog); §4.3's two changes to the provider headers; the 14 empty `__init__.py` markers given a §3.1 header per DR4; `scripts/sanitize_ics.py` given a header it had none of; every flagged inventory/trigger/flag line reshaped to prose or removed per DR3/DR6 | 65 files (see `git diff` for the full list) | unchanged |
| 6 | Deleted the `__main__` block from all 12 tracked test modules carrying one, and the five named in-module runners (`run_all_tests` in `test_ai_clients.py`/`test_ai_foundation.py`; `main` in `test_config_system.py`/`test_tag_system.py`/`test_templates.py`). Removed the `sys` import from three files where it became unused | 12 test files | unchanged |
| 7 | Deleted the empty `CONTRIBUTING.md`. Completed this artifact | `CONTRIBUTING.md` | n/a |

## 2.1 Step 1 — branch-point baseline

`pytest`, run before any edit:

```
FAILED tests/test_ai_clients.py::test_claude_generation
FAILED tests/test_ai_clients.py::test_gemini_generation
FAILED tests/test_ai_clients.py::test_provider_status
FAILED tests/test_ai_clients.py::test_cost_tracking_integration
4 failed, 992 passed, 26 warnings
```

The four failures match the known, open-issue-covered set named in the spec's Decision Log (20260908, Ray) and §6: `test_claude_generation`, `test_gemini_generation`, `test_provider_status`, `test_cost_tracking_integration` — root cause #130, file/reporting #131. No finding raised against them per Ray's ruling.

`pytest automation/`, run before any edit:

```
automation/closeout_acs_test.py .....................
automation/issue_validator_test.py ..............................
51 passed
```

## 3. Acceptance criteria

Nine of these criteria are checked by Ray's stated reading, per the spec's own §5 check method — Anvil cannot self-certify them. Evidence is given for each; status reflects what Anvil verified mechanically, and those nine are marked accordingly rather than "Met."

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Awaiting Ray's stated reading | All 259 tracked files across the five trees (excluding `scripts/rule_census.py` itself, DR8.5) appear in the census report below with candidate rows or an explicit no-hit row stating what was read |
| AC1.2 | Met | Every one of the 699 census rows carries a determination (0 blank, verified programmatically); every one of the 420 leave-as-is rows carries a non-empty reason |
| AC1.3 | Awaiting Ray's stated reading | Verified: every edit/remove-flagged text string is gone from its file except the three `issue_validator.py` invocation lines, which now appear only in the argparse epilog (§4.2's edit, not a removal) |
| AC2.1 | Met | `docs/DEVELOPMENT_STANDARDS.md` §1.5's new bullet states the class-worded prohibition and names `CLAUDE.md` and this document as the two homes; no file kind, directory or exempt path is enumerated |
| AC3.1 | Met | The bullet's closing two sentences record the `tests/test_ai_clients.py` failure it exists for |
| AC5.1 | Met | `pytest`: 4 failed (the same four named tests), 992 passed — unchanged from the branch-point baseline in §2.1; `pytest automation/`: 51 passed, unchanged |
| AC6.1 | Met | §3.1's replacement text states the summary-plus-description shape, excludes commands/flags/invocations/triggers/inventories by name, and permits naming an environment variable read or the API call that yields an instance |
| AC8.1 | Met | §3.4's replacement states which `__init__.py` gets imports/`__all__` (exposes an API) and which gets only the docstring (exposes nothing), keyed to whether any caller writes `from <package> import <name>` |
| AC9.1 | Met | The AC9.1 filter from spec §5 (G5's `command grep`, piped from `git diff` on `**/__init__.py`) returns nothing |
| AC10.1 | Met | §3.5's heading and opening sentence scope it to functions and classes; §5.6's replacement scopes its docstring bullet to the Click command function |
| AC11.1 | Met | `git ls-files tests/ \| xargs grep -ln "__main__"` returns nothing |
| AC11.2 | Met | `git ls-files tests/ \| xargs grep -n "^def run_all_tests"` and `... "^def main"` both return nothing |
| AC11.3 | Met | `CONTRIBUTING.md` is absent (`git rm`, this branch) |
| AC12.1 | Awaiting Ray's stated reading | Every named location appears in the census report with a determination: `tests/test_ai_clients.py`'s SKIP_API_TESTS/Run-with lines (10, 12) — remove (applied); the `:361-363` gate comment — leave as is, read on its own per the spec's instruction, reason recorded; all four `config/intent_parse_prompt.json` prose fields and all three `config/providers/*_settings.json` descriptions — present with determinations (edit/remove/leave as is) |
| AC12.4 | Met | `git diff` shows both `claude.py:5` and `gemini.py:5` changed; `grep -rn "Do not instantiate" workmain/ai/providers/` returns nothing |
| AC12.3 | Met | `python3 automation/issue_validator.py --help` shows the three invocations under an `examples:` epilog, on separate lines; the module docstring carries none |
| AC12.2 | Met | `git diff $(git merge-base main HEAD) -- config/intent_parse_system_prompt.txt` is empty; every census row for that file cites #122 in its determination reason |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | `automation/closeout_acs.py`'s `--tree` flag loses its only documentation (the removed docstring paragraph was its sole explanation; the `add_argument` call carries no `help=` text) | Census row determination was "remove," not "edit" — DR3 was followed literally. Adding a `help=` string was not part of the determination and would be scope Anvil was not asked to add | Not yet — flagged in §6 below rather than acted on unilaterally |

## 5. Verification

- **Test suite:** 992 passed, 0 unexpected failures (4 known, named, unchanged) — baseline was identical (§2.1). `pytest automation/`: 51 passed, unchanged.
- **Live verification:** None performed — this branch changes only module/package docstrings, comments, one JSON config file's prose fields, test-file headers and `__main__` blocks, and deletes an empty file. No runtime behavior changes (confirmed by the unchanged test counts and by `ast`-parsing every edited `.py` file after each edit).
- **Daemon restart:** Not applicable — no code path executed by the daemon or CLI changed; docstrings and comments are not evaluated at runtime except `automation/issue_validator.py`'s `--help` (verified directly) and the `_doc`/`_comment` JSON fields (verified unread by any code, Decision Log 20260909 row citing `workmain/ai/intent_parser.py:19`).

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| — | `automation/closeout_acs.py`'s `--tree <ref>` flag has no `help=` text after its docstring explanation was removed (Deviation 1 above) | Outside this spec's determination; a one-line `add_argument(..., help=...)` fix, left for whoever next touches that file or a future issue |
| #122 | Realign Ollama configuration with the per-provider structure; already owns the ownership boundary between `config/intent_parse_prompt.json` and `config/intent_parse_system_prompt.txt`, and the third/fifth ACs inherit the field-name and file-ownership findings recorded in this spec's Decision Log (20260909, Spanner) | Pre-existing, not opened by this work — carried forward per the spec's §1 exclusion |
| #130 / #131 | The four `tests/test_ai_clients.py` API-integration failures (root cause / file-and-reporting split) | Pre-existing, named and excluded from this spec's scope per Ray's 20260908 ruling |
| #136 | The `unittest.TestCase` tests and the classes that commit to the live database | Out of scope per spec §1 — this branch only edited some of those files' headers and deleted their `__main__` blocks, touching no test body or isolation mechanism |
| #137 | The assertion-less tests (including `tests/test_db_connection.py`'s `test_database()`, left untouched except for its now-deleted `__main__` block) | Out of scope per spec §1 |

## Census report (Step 3)

`scripts/rule_census.py` excludes itself by name (DR8.5) — its own source is the literal text of the categories it defines.

| File | Line | Category | Text | Determination | Reason |
| --- | --- | --- | --- | --- | --- |
| `automation/check_release_integrity.py` | 6 | INVENTORY | `1.`CHANGELOG.md` has a matching `## [N.N.N]`section` | edit | |
| `automation/check_release_integrity.py` | 7 | INVENTORY | `2. that section is non-empty (a heading with no body is a silent loss)` | edit | |
| `automation/check_release_integrity.py` | 8 | INVENTORY | `3. a GitHub Release object exists for the tag` | edit | |
| `automation/check_release_integrity.py` | 12 | INVENTORY | `4.`**version**` and `**version_info**`agree with each other` | edit | |
| `automation/check_release_integrity.py` | 13 | INVENTORY | `5.`**version**`is not behind the newest tag (a stale version file)` | edit | |
| `automation/check_release_integrity.py` | 14 | INVENTORY | `6. if`**version**`is ahead of every tag — a release in flight — CHANGELOG.md` | edit | |
| `automation/check_release_integrity.py` | 20 | COMMAND | `python3 automation/check_release_integrity.py             # full check` | remove | |
| `automation/check_release_integrity.py` | 21 | COMMAND,FLAG | `python3 automation/check_release_integrity.py --no-remote # skip the gh Release check` | remove | |
| `automation/check_release_integrity.py` | 22 | COMMAND,FLAG | `python3 automation/check_release_integrity.py --show-historical` | remove | |
| `automation/closeout_acs.py` | 8 | COMMAND,FLAG | `python3 automation/closeout_acs.py --branch <name> [--tree <ref>]` | remove | |
| `automation/closeout_acs.py` | 10 | FLAG | ``--tree <ref>`reads the spec and the artifact from that git ref instead of the` | remove | |
| `automation/closeout_acs_test.py` | | NO_HIT | `no match in 254 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `automation/fixtures/ac2_1_missing_milestone.json` | 2 | PROSE | `title = 'Missing the milestone key entirely'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/ac2_1_missing_milestone.json` | 3 | PROSE | `context = 'A required key is absent, not just null.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/ac2_2_unknown_key.json` | 2 | PROSE | `title = "Typo'd key name"` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/ac2_2_unknown_key.json` | 3 | PROSE | `context = 'The milestone key is misspelled, so it reads as both unknown and missing.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/ac2_5_bad_label.json` | 2 | PROSE | `title = 'Label that does not exist on GitHub'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/ac2_5_bad_label.json` | 3 | PROSE | `context = "labels[] names a label that isn't live."` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/ac2_5_bad_milestone.json` | 2 | PROSE | `title = 'Milestone that does not exist on GitHub'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/ac2_5_bad_milestone.json` | 3 | PROSE | `context = "milestone names a title that isn't live."` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/ac2_5_bad_milestone.json` | 5 | PROSE | `milestone = 'Not A Real Milestone'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/ac2_5_bad_parent.json` | 2 | PROSE | `title = 'Parent that does not exist'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/ac2_5_bad_parent.json` | 3 | PROSE | `context = 'parent names an issue number nothing resolves to.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/ac2_7_three_errors.json` | 2 | PROSE | `title = 'Three independent errors in one file'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/ac2_7_three_errors.json` | 3 | PROSE | `context = 'Unknown key, a label that is not live, and an unscheduled issue carrying neither pair label.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/closeout_results_carried_uncited.md` | | NO_HIT | `no match in 14 lines` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/closeout_results_clean.md` | 10 | COMMAND | `\| AC1.1 \| Met \|`pytest automation/closeout_acs_test.py`passes \|` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/closeout_results_clean.md` | 11 | COMMAND | `\| AC1.2 \| Met \|`pytest automation/closeout_acs_test.py`passes \|` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/closeout_results_clean.md` | 12 | COMMAND | `\| AC2.1 \| Met \|`pytest automation/closeout_acs_test.py`passes \|` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/closeout_results_escaped_pipe.md` | | NO_HIT | `no match in 14 lines` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/closeout_results_extra_row.md` | | NO_HIT | `no match in 15 lines` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/closeout_results_missing_row.md` | | NO_HIT | `no match in 15 lines` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/closeout_results_not_met.md` | 10 | COMMAND | `\| AC1.1 \| Not met \|`pytest`fails against delivered code \|` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/closeout_results_unevidenced_met.md` | | NO_HIT | `no match in 14 lines` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/closeout_spec_bare_acn.md` | | NO_HIT | `no match in 15 lines` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/closeout_spec_clean.md` | | NO_HIT | `no match in 16 lines` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/closeout_specs_bad_filename/WEIRD_NAME.md` | | NO_HIT | `no match in 10 lines` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/closeout_specs_no_match/OTHER_SUBJECT_SPEC.md` | | NO_HIT | `no match in 10 lines` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/closeout_specs_one_match/ONLY_SUBJECT_SPEC.md` | | NO_HIT | `no match in 10 lines` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/closeout_specs_two_match/A_SUBJECT_SPEC.md` | | NO_HIT | `no match in 10 lines` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/closeout_specs_two_match/B_SUBJECT_SPEC.md` | | NO_HIT | `no match in 10 lines` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_invalid_scheduled_both_pair_labels.json` | 2 | PROSE | `title = 'Invalid: scheduled standalone carrying both pair labels'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_invalid_scheduled_both_pair_labels.json` | 3 | PROSE | `context = 'Milestone set and labels carrying defect and gap at once, which no scheduling explains.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_invalid_scheduled_both_pair_labels.json` | 5 | PROSE | `milestone = 'Phase 14 — Setup Wizard & Configuration'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_invalid_unscheduled_both_pair_labels.json` | 2 | PROSE | `title = 'Invalid: unscheduled standalone carrying both pair labels'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_invalid_unscheduled_both_pair_labels.json` | 3 | PROSE | `context = 'Milestone null and labels carrying defect and gap at once.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_invalid_unscheduled_no_pair_child.json` | 2 | PROSE | `title = 'Invalid: unscheduled child carrying neither pair label'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_invalid_unscheduled_no_pair_child.json` | 3 | PROSE | `context = 'Milestone null, parent set, and labels carrying neither defect nor gap.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_invalid_unscheduled_no_pair_standalone.json` | 2 | PROSE | `title = 'Invalid: unscheduled standalone carrying neither pair label'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_invalid_unscheduled_no_pair_standalone.json` | 3 | PROSE | `context = 'Milestone null and labels carrying neither defect nor gap.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_scheduled_child.json` | 2 | PROSE | `title = 'Scheduled child issue'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_scheduled_child.json` | 3 | PROSE | `context = 'Context for a scheduled child issue.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_scheduled_child.json` | 5 | PROSE | `milestone = 'Phase 14 — Setup Wizard & Configuration'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_scheduled_standalone.json` | 2 | PROSE | `title = 'Scheduled standalone issue'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_scheduled_standalone.json` | 3 | PROSE | `context = 'Context for a scheduled standalone issue.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_scheduled_standalone.json` | 5 | PROSE | `milestone = 'Phase 14 — Setup Wizard & Configuration'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_scheduled_with_pair_child.json` | 2 | PROSE | `title = 'Scheduled child carrying a pair label'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_scheduled_with_pair_child.json` | 3 | PROSE | `context = 'Milestone set, parent set, and a pair label kept from before it was scheduled.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_scheduled_with_pair_child.json` | 5 | PROSE | `milestone = 'Phase 14 — Setup Wizard & Configuration'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_scheduled_with_pair_standalone.json` | 2 | PROSE | `title = 'Scheduled standalone carrying a pair label'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_scheduled_with_pair_standalone.json` | 3 | PROSE | `context = 'Milestone set and a pair label kept from before it was scheduled.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_scheduled_with_pair_standalone.json` | 5 | PROSE | `milestone = 'Phase 14 — Setup Wizard & Configuration'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_unscheduled_child.json` | 2 | PROSE | `title = 'Unscheduled child issue'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_unscheduled_child.json` | 3 | PROSE | `context = 'Context for an unscheduled child issue, carrying exactly one pair label.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_unscheduled_standalone.json` | 2 | PROSE | `title = 'Unscheduled standalone issue'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/shape_unscheduled_standalone.json` | 3 | PROSE | `context = 'Context for an unscheduled standalone issue, carrying exactly one pair label.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/single_line_newline_in_ac.json` | 2 | PROSE | `title = 'Newline inside an AC'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/single_line_newline_in_ac.json` | 3 | PROSE | `context = 'Otherwise valid; acs[1] carries an embedded newline.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/single_line_newline_in_title.json` | 2 | PROSE | `title = 'Newline inside\\nthe title'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/single_line_newline_in_title.json` | 3 | PROSE | `context = 'Otherwise valid; the title carries an embedded newline.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/standards_alpha_beta.md` | 5 | INVENTORY | `- Labels carry area, and`alpha`/`beta`is the label pair that says what an unscheduled issue is. An issue with no milestone carries exactly one of them.` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/standards_alpha_beta.md` | 6 | INVENTORY | `- A milestone carries the exit condition that closes it.` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/standards_missing_label_pair.md` | 5 | INVENTORY | `- Labels carry area. What each label means beyond that is its description on` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/standards_missing_label_pair.md` | 7 | INVENTORY | `- A milestone carries the exit condition that closes it.` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/valid_full.json` | 2 | PROSE | `title = 'Fully populated valid issue'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/valid_full.json` | 3 | PROSE | `context = 'Two area labels, one pair label, and two blocked_by entries.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/valid_minimal.json` | 2 | PROSE | `title = 'Minimal valid issue'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/fixtures/valid_minimal.json` | 3 | PROSE | `context = 'No milestone, no parent, no blockers.'` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `automation/issue_validator.py` | 3 | COMMAND | `GitHub state, then create the issue through`gh issue create`.` | leave as is | Descriptive summary of what the module does; `gh issue create` names the mechanism it drives, not an invocation (§3.1 / DR2 permit naming the call that does the work). |
| `automation/issue_validator.py` | 5 | COMMAND,FLAG | `python3 automation/issue_validator.py --new              # print the skeleton` | edit | Pre-adjudicated (§1, §4.2) — invocation lines move to argparse epilog. |
| `automation/issue_validator.py` | 6 | COMMAND | `python3 automation/issue_validator.py issue.json         # validate, print command` | edit | Pre-adjudicated (§1, §4.2) — invocation lines move to argparse epilog. |
| `automation/issue_validator.py` | 7 | COMMAND,FLAG | `python3 automation/issue_validator.py issue.json --create  # validate, then create` | edit | Pre-adjudicated (§1, §4.2) — invocation lines move to argparse epilog. |
| `automation/issue_validator.py` | 238 | COMMAND | `"""Map validated issue data to a`gh issue create`argv, per §4.3."""` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `automation/issue_validator.py` | 262 | COMMAND | `"""Live`gh issue view`lookup. Returns the issue's state, or None if it does not exist."""` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `automation/issue_validator_test.py` | | NO_HIT | `no match in 284 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `config/ai_settings.json` | 2 | PROSE | `version = '1.3'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 3 | PROSE | `description = 'WorkmAIn AI Provider Configuration'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 4 | VERSION | `last_updated = '20260903'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 8 | PROSE | `providers.claude.model = 'claude-sonnet-5'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 9 | PROSE | `providers.claude.api_key_env = 'ANTHROPIC_API_KEY'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 12 | PROSE | `providers.claude.cost_structure = '$2/MTok prompt, $10/MTok completion'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 17 | PROSE | `providers.claude.notes = 'Claude Sonnet 5 - fallback provider for all report types and note condensation. Request payload policy (thinking disabled, no sampling) lives in config/providers/claude_settings.json.'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 21 | PROSE | `providers.gemini.model = 'gemini-3.5-flash-lite'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 22 | PROSE | `providers.gemini.api_key_env = 'GOOGLE_API_KEY'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 25 | PROSE | `providers.gemini.cost_structure = '$.30/MTok prompt, $2.5/MTok completion'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 30 | PROSE | `providers.gemini.notes = 'Gemini 3.5 Flash Lite - $0.30/MTok input, $2.5/MTok output'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 34 | PROSE | `providers.ollama.model = 'workmain-intent:latest'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 35 | PROSE | `providers.ollama.host = 'workmain-ollama.lab.haloschaos.com'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 38 | PROSE | `providers.ollama.cost_structure = 'Local \\u2014 no API cost'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 43 | PROSE | `report_types.daily_internal.primary_provider = 'claude'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 44 | PROSE | `report_types.daily_internal.fallback_provider = 'gemini'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 45 | PROSE | `report_types.daily_internal.fallback_mode = 'auto'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 47 | PROSE | `report_types.daily_internal.description = 'Daily internal status report'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 49 | PROSE | `report_types.daily_internal.tags_include[0] = 'internal-only'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 50 | PROSE | `report_types.daily_internal.tags_include[1] = 'both'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 51 | PROSE | `report_types.daily_internal.tags_include[2] = 'carry-forward'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 52 | PROSE | `report_types.daily_internal.tags_include[3] = 'blocker'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 55 | PROSE | `report_types.daily_internal.tags_exclude[0] = 'client-report'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 56 | PROSE | `report_types.daily_internal.tags_exclude[1] = 'info-only'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 60 | PROSE | `report_types.weekly_client.primary_provider = 'claude'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 61 | PROSE | `report_types.weekly_client.fallback_provider = 'gemini'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 62 | PROSE | `report_types.weekly_client.fallback_mode = 'auto'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 64 | PROSE | `report_types.weekly_client.description = 'Weekly client status report'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 66 | PROSE | `report_types.weekly_client.tags_include[0] = 'client-report'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 67 | PROSE | `report_types.weekly_client.tags_include[1] = 'both'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 68 | PROSE | `report_types.weekly_client.tags_include[2] = 'carry-forward'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 71 | PROSE | `report_types.weekly_client.tags_exclude[0] = 'internal-only'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 72 | PROSE | `report_types.weekly_client.tags_exclude[1] = 'info-only'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 76 | PROSE | `report_types.note_condensation.primary_provider = 'gemini'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 77 | PROSE | `report_types.note_condensation.fallback_provider = 'claude'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 78 | PROSE | `report_types.note_condensation.fallback_mode = 'auto'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 80 | PROSE | `report_types.note_condensation.description = 'Condense meeting notes for Clockify'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 86 | PROSE | `fallback_settings.default_mode = 'auto'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 89 | PROSE | `fallback_settings.notification_channels[0] = 'cli'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 96 | PROSE | `cost_tracking.storage_path = '~/.workmain/cost_history.json'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/ai_settings.json` | 107 | PROSE | `advanced.context_window_management.truncation_strategy = 'oldest_first'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/intent_parse_prompt.json` | 3 | PROSE | `_doc.name = 'WorkmAIn Intent Parse — Generation Config'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/intent_parse_prompt.json` | 4 | PROSE | `_doc.description = 'Generation parameters for Mistral 7B intent parsing via Ollama. Controls max_tokens only at runtime — temperature/top_p/top_k/repeat_penalty are baked into the Modelfile and listed here as the editable reference for rebuilds.'` | edit | |
| `config/intent_parse_prompt.json` | 5 | PROSE | `_doc.system_prompt_source = 'config/intent_parse_system_prompt.txt'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/intent_parse_prompt.json` | 6 | PROSE | `_doc.ollama_model = 'workmain-intent:latest'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/intent_parse_prompt.json` | 7 | PROSE | `_doc.ollama_host = 'workmain-ollama.lab.haloschaos.com:11434'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/intent_parse_prompt.json` | 8 | PROSE | `_doc.version_authority = 'Version metadata (config_version, config_updated, model_built) is maintained exclusively in config/intent_parse_system_prompt.txt header. Do not add version fields here — read the .txt header for current version state.'` | edit | |
| `config/intent_parse_prompt.json` | 9 | PROSE | `_doc.notes = 'To update generation parameters: edit generation_options below, sync PARAMETER blocks in the Modelfile (IaC repo), rebuild model via build_workmain_intent.sh, then update config_version/config_updated/model_built in intent_parse_system_prompt.txt only.'` | remove | |
| `config/intent_parse_prompt.json` | 11 | PROSE | `system_prompt_file = 'config/intent_parse_system_prompt.txt'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/intent_parse_prompt.json` | 14 | PROSE | `generation_options._comment = 'Reference only — runtime source of truth is Modelfile PARAMETER blocks. Edit here first, then sync to Modelfile and rebuild.'` | edit | |
| `config/intent_parse_system_prompt.txt` | 5 | VERSION | `# config_updated:    20260611` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 45 | INVENTORY | `1. create_note` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 56 | INVENTORY | `2. create_time_entry` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 76 | INVENTORY | `3. update_task` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 81 | INVENTORY | `4. confirm_report` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 86 | INVENTORY | `5. correct_report` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 91 | INVENTORY | `6. defer_task` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 96 | INVENTORY | `7. deduplicate_task` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 97 | TRIGGER | `Use when the user says two carry-forward tasks are the same thing.` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 105 | INVENTORY | `8. start_eod` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 106 | TRIGGER | `Use when the user wants to begin the end-of-day workflow review.` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 119 | INVENTORY | `9. unknown` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 120 | TRIGGER | `Use when the input does not match any action or is too ambiguous to parse.` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 126 | INVENTORY | `- Return ONLY the JSON object. No other text.` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 127 | INVENTORY | `- If the input begins with "note:" or "Note:", always use create_note.` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 128 | INVENTORY | `- If duration is given in hours, convert to minutes. duration_minutes is already` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 130 | INVENTORY | `- If the input mentions being blocked or waiting on something external, infer` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 132 | INVENTORY | `- If the input mentions "still waiting", "ongoing", "need to follow up", or an` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 134 | INVENTORY | `- If the input mentions multiple actions, focus on the most specific actionable` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 136 | INVENTORY | `- When in doubt between two actions, return unknown with a clarifying question.` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 137 | INVENTORY | `- If the user says "start eod", "begin eod", "run eod", "end of day", "eod",` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/intent_parse_system_prompt.txt` | 139 | INVENTORY | `- Never invent fields not listed in the schema above.` | leave as is | Pre-adjudicated (§1, §5, Decision Log 20260909) — deferred to #122. |
| `config/meeting_templates.json` | | NO_HIT | `no match in 1 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `config/providers/claude_settings.json` | 2 | PROSE | `description = "Claude (Anthropic) request payload policy. Declares what we SEND, never what a model SUPPORTS. Required keys read by ClaudeProvider: thinking, sampling. Values are the vendor's own parameter shapes, passed through verbatim."` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/providers/gemini_settings.json` | 2 | PROSE | `description = 'Gemini (Google AI) request payload policy. Declares what we SEND, never what a model SUPPORTS. Required key read by GeminiProvider: sampling. A sampling value of \\"from_request\\" means read that parameter off the GenerationRequest.'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/providers/ollama_settings.json` | 2 | PROSE | `description = 'Ollama request payload policy. Declares what we SEND, never what a model SUPPORTS. OllamaProvider requires no policy keys: its generation parameters (temperature, top_p, top_k, repeat_penalty) are Modelfile-baked and set outside this repository; only num_predict is sent per request.'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 2 | PROSE | `version = '1.0'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 3 | PROSE | `description = 'WorkmAIn Tag System Configuration'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 4 | PROSE | `last_updated = '2025-12-22'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 5 | PROSE | `default_tag = 'ilo'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 8 | PROSE | `tag_mappings.ilo.full_name = 'internal-only'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 9 | PROSE | `tag_mappings.ilo.display = '[internal-only]'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 10 | PROSE | `tag_mappings.ilo.description = 'Internal reports only, excluded from client reports'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 17 | PROSE | `tag_mappings.cr.full_name = 'client-report'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 18 | PROSE | `tag_mappings.cr.display = '[client-report]'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 19 | PROSE | `tag_mappings.cr.description = 'Client reports only, excluded from internal reports'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 26 | PROSE | `tag_mappings.ifo.full_name = 'info-only'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 27 | PROSE | `tag_mappings.ifo.display = '[info-only]'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 28 | PROSE | `tag_mappings.ifo.description = 'Reference only, excluded from all reports'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 35 | PROSE | `tag_mappings.both.full_name = 'both'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 36 | PROSE | `tag_mappings.both.display = '[both]'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 37 | PROSE | `tag_mappings.both.description = 'Include in both internal and client reports'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 44 | PROSE | `tag_mappings.cf.full_name = 'carry-forward'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 45 | PROSE | `tag_mappings.cf.display = '[carry-forward]'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 46 | PROSE | `tag_mappings.cf.description = 'Tasks in progress, carry to next period'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 53 | PROSE | `tag_mappings.blk.full_name = 'blocker'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 54 | PROSE | `tag_mappings.blk.display = '[blocker]'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 55 | PROSE | `tag_mappings.blk.description = 'Blockers and issues requiring attention'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/tags.json` | 70 | PROSE | `display_options.separator = ' '` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/template_aliases.json` | 2 | PROSE | `version = '1.0'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/template_aliases.json` | 4 | PROSE | `aliases.daily = 'daily_internal'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/template_aliases.json` | 5 | PROSE | `aliases.weekly = 'weekly_client'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/template_aliases.json` | 8 | PROSE | `metadata.created_at = '2025-12-30'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `config/template_aliases.json` | 9 | PROSE | `metadata.description = 'Template alias registry for WorkmAIn report templates'` | leave as is | Configuration data read by the application, not documentation — the value states what the setting is, and no process rule. |
| `scripts/database/reset_database.sh` | | NO_HIT | `no match in 1 lines` | leave as is | Pre-adjudicated (§1) — tracked shell file; no standard in this project governs a shell file. |
| `scripts/database/reset_database_fixed.sql` | | NO_HIT | `no match in 54 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `scripts/preview_templates.py` | | NO_HIT | `no match in 135 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `scripts/sanitize_ics.py` | 1 | NO_HEADER | `(no module docstring)` | edit | |
| `scripts/setup/ai_dependencies.sh` | 33 | FLAG | `pip install "httpx==0.27.0" --break-system-packages` | leave as is | Pre-adjudicated (§1) — tracked shell file; no standard in this project governs a shell file. |
| `scripts/setup/ai_dependencies.sh` | 37 | FLAG | `pip install "anthropic>=0.40.0" --break-system-packages` | leave as is | Pre-adjudicated (§1) — tracked shell file; no standard in this project governs a shell file. |
| `scripts/setup/ai_dependencies.sh` | 41 | FLAG | `pip install "google-genai>=0.1.0" --break-system-packages` | leave as is | Pre-adjudicated (§1) — tracked shell file; no standard in this project governs a shell file. |
| `scripts/setup/ai_dependencies.sh` | 91 | COMMAND | `echo "  1. Run: python3 tests/test_ai_clients.py"` | leave as is | Pre-adjudicated (§1) — tracked shell file; no standard in this project governs a shell file. |
| `scripts/setup/db-setup.sh` | | NO_HIT | `no match in 29 lines` | leave as is | Pre-adjudicated (§1) — tracked shell file; no standard in this project governs a shell file. |
| `tests/__init__.py` | 1 | NO_HEADER | `(no module docstring)` | edit | |
| `tests/conftest.py` | | NO_HIT | `no match in 38 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/fixtures/__init__.py` | 1 | NO_HEADER | `(no module docstring)` | edit | |
| `tests/fixtures/recurrence_id_override.ics` | 8 | VERSION | `DTSTART:16011104T020000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/recurrence_id_override.ics` | 9 | FLAG | `RRULE:FREQ=YEARLY;BYDAY=1SU;BYMONTH=11` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/recurrence_id_override.ics` | 14 | VERSION | `DTSTART:16010311T020000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/recurrence_id_override.ics` | 15 | FLAG | `RRULE:FREQ=YEARLY;BYDAY=2SU;BYMONTH=3` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/recurrence_id_override.ics` | 22 | FLAG,VERSION | `DTSTART;TZID="Pacific Standard Time":20990511T090000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/recurrence_id_override.ics` | 23 | FLAG,VERSION | `DTEND;TZID="Pacific Standard Time":20990511T100000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/recurrence_id_override.ics` | 24 | FLAG | `RRULE:FREQ=WEEKLY;COUNT=3;BYDAY=MO` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/recurrence_id_override.ics` | 30 | FLAG,VERSION | `RECURRENCE-ID;TZID="Pacific Standard Time":20990511T090000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/recurrence_id_override.ics` | 31 | FLAG,VERSION | `DTSTART;TZID="Pacific Standard Time":20990513T140000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/recurrence_id_override.ics` | 32 | FLAG,VERSION | `DTEND;TZID="Pacific Standard Time":20990513T150000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_cst.ics` | 7 | FLAG,VERSION | `DTSTART;TZID=America/Denver:20260309T100000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_cst.ics` | 8 | FLAG,VERSION | `DTEND;TZID=America/Denver:20260309T110000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_malformed.ics` | 7 | FLAG,VERSION | `DTSTART;TZID=America/Los_Angeles:20260309T090000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_malformed.ics` | 8 | FLAG,VERSION | `DTEND;TZID=America/Los_Angeles:20260309T093000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_malformed.ics` | 14 | FLAG,VERSION | `DTSTART;TZID=America/Los_Angeles:20260310T100000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_normal.ics` | 7 | FLAG,VERSION | `DTSTART;TZID=America/Los_Angeles:20260309T090000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_normal.ics` | 8 | FLAG,VERSION | `DTEND;TZID=America/Los_Angeles:20260309T093000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_normal.ics` | 10 | FLAG,VERSION | `RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;UNTIL=20260309T235959Z` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_normal.ics` | 18 | FLAG,VERSION | `DTSTART;TZID=America/Los_Angeles:20260309T140000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_normal.ics` | 19 | FLAG,VERSION | `DTEND;TZID=America/Los_Angeles:20260309T150000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_normal.ics` | 25 | FLAG,VERSION | `DTSTART;TZID=America/Los_Angeles:20260313T100000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_normal.ics` | 26 | FLAG,VERSION | `DTEND;TZID=America/Los_Angeles:20260313T103000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_with_cancelled.ics` | 7 | FLAG,VERSION | `DTSTART;TZID=America/Los_Angeles:20260309T090000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_with_cancelled.ics` | 8 | FLAG,VERSION | `DTEND;TZID=America/Los_Angeles:20260309T093000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_with_cancelled.ics` | 15 | FLAG,VERSION | `DTSTART;TZID=America/Los_Angeles:20260310T100000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_with_cancelled.ics` | 16 | FLAG,VERSION | `DTEND;TZID=America/Los_Angeles:20260310T110000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_with_free.ics` | 7 | FLAG,VERSION | `DTSTART;TZID=America/Los_Angeles:20260309T090000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_with_free.ics` | 8 | FLAG,VERSION | `DTEND;TZID=America/Los_Angeles:20260309T093000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_with_free.ics` | 14 | FLAG,VERSION | `DTSTART;TZID=America/Los_Angeles:20260312T150000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_with_free.ics` | 15 | FLAG,VERSION | `DTEND;TZID=America/Los_Angeles:20260312T160000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_with_free.ics` | 21 | FLAG,VERSION | `DTSTART;TZID=America/Los_Angeles:20260311T120000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/fixtures/week_with_free.ics` | 22 | FLAG,VERSION | `DTEND;TZID=America/Los_Angeles:20260311T130000` | leave as is | Pre-adjudicated (§1) — fixtures/mocks directory: test data, not text a session reads as guidance. |
| `tests/mocks/__init__.py` | 1 | NO_HEADER | `(no module docstring)` | edit | |
| `tests/test_action_executor.py` | | NO_HIT | `no match in 649 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_ai_clients.py` | 3 | INVENTORY | `- ClaudeProvider (Anthropic)` | edit | |
| `tests/test_ai_clients.py` | 4 | INVENTORY | `- GeminiProvider (Google AI)` | edit | |
| `tests/test_ai_clients.py` | 5 | INVENTORY | `- Real API generation` | edit | |
| `tests/test_ai_clients.py` | 6 | INVENTORY | `- Token counting` | edit | |
| `tests/test_ai_clients.py` | 7 | INVENTORY | `- Cost estimation` | edit | |
| `tests/test_ai_clients.py` | 8 | INVENTORY | `- Error handling` | edit | |
| `tests/test_ai_clients.py` | 10 | FLAG | `Set SKIP_API_TESTS=1 to skip real API tests.` | remove | |
| `tests/test_ai_clients.py` | 12 | COMMAND,TRIGGER | `Run with: python3 test_ai_clients.py` | remove | |
| `tests/test_ai_clients.py` | 361 | FLAG | `# under SKIP_API_TESTS=1 and without any API key. They are unit tests of the` | leave as is | Explains why these payload-contract tests sit outside the SKIP_API_TESTS gate — a property of the code, not a process rule; the gate itself is #131's. |
| `tests/test_ai_clients.py` | 362 | TRIGGER | `# request payload contract, not API tests — they must not sit behind the` | leave as is | Explains why these payload-contract tests sit outside the SKIP_API_TESTS gate — a property of the code, not a process rule; the gate itself is #131's. |
| `tests/test_ai_costs.py` | 3 | INVENTORY | `- AiCostRepository (create, get_filtered, get_summary with provider filter)` | edit | |
| `tests/test_ai_costs.py` | 4 | INVENTORY | `- resolve_date_window and format_date_window_label (date_utils)` | edit | |
| `tests/test_ai_costs.py` | 5 | INVENTORY | `- ProviderManager config loading from ai_settings.json` | edit | |
| `tests/test_ai_costs.py` | 148 | TRIGGER | `# Query a completely different year — must not include the 2099 row` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `tests/test_ai_foundation.py` | 3 | INVENTORY | `- Base provider abstract class` | edit | |
| `tests/test_ai_foundation.py` | 4 | INVENTORY | `- Cost tracking system` | edit | |
| `tests/test_ai_foundation.py` | 5 | INVENTORY | `- Provider manager with fallback` | edit | |
| `tests/test_ai_foundation.py` | 6 | INVENTORY | `- Configuration structures` | edit | |
| `tests/test_ai_foundation.py` | 7 | COMMAND,TRIGGER | `Run with: python3 test_ai_foundation.py` | remove | |
| `tests/test_client_repository.py` | | NO_HIT | `no match in 161 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_clients_commands.py` | | NO_HIT | `no match in 240 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_clockify.py` | | NO_HIT | `no match in 52 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_clockify_sync.py` | | NO_HIT | `no match in 122 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_config_system.py` | | NO_HIT | `no match in 239 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_db_connection.py` | | NO_HIT | `no match in 100 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_delivery.py` | 95 | TRIGGER | `# must not raise` | leave as is | Trailing comment on a code line, describing local behaviour; states no process rule. |
| `tests/test_delivery.py` | 128 | TRIGGER | `# must not raise` | leave as is | Trailing comment on a code line, describing local behaviour; states no process rule. |
| `tests/test_delivery.py` | 145 | TRIGGER | `# must not raise` | leave as is | Trailing comment on a code line, describing local behaviour; states no process rule. |
| `tests/test_email.py` | | NO_HIT | `no match in 251 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_email_recipients_client.py` | 3 | INVENTORY | `- assign_recipient() client_id scoping` | edit | |
| `tests/test_email_recipients_client.py` | 4 | INVENTORY | `- unassign_recipient() client_id filtering` | edit | |
| `tests/test_email_recipients_client.py` | 5 | INVENTORY | `- list_for_client() global + client-scoped merge` | edit | |
| `tests/test_email_recipients_client.py` | 6 | INVENTORY | `- _get_draft_recipients() client-aware resolution and deduplication` | edit | |
| `tests/test_eod_pipeline.py` | | NO_HIT | `no match in 146 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_eod_task_matching.py` | 4 | INVENTORY | `Covers:` | edit | |
| `tests/test_eod_task_matching.py` | 5 | INVENTORY | `- _tokenize(): lowercases, strips punctuation, removes stop words, returns set` | edit | |
| `tests/test_eod_task_matching.py` | 6 | INVENTORY | `- _score_match(): ratio of overlap to task token count; 0.0 for empty task_tokens` | edit | |
| `tests/test_eod_task_matching.py` | 7 | INVENTORY | `- Confidence thresholds: High ≥ 0.5, Medium 0.2–0.49, Low < 0.2 (not surfaced)` | edit | |
| `tests/test_eod_task_matching.py` | 8 | INVENTORY | `- _run_task_match_step(): returns COMPLETED immediately when no CF observations` | edit | |
| `tests/test_eod_task_matching.py` | 9 | INVENTORY | `- _run_task_match_step(): returns COMPLETED immediately when no active tasks` | edit | |
| `tests/test_eod_task_matching.py` | 10 | INVENTORY | `- _run_task_match_step(): exception handling returns COMPLETED (non-blocking)` | edit | |
| `tests/test_eod_workflow.py` | 5 | INVENTORY | `Covers: EodStepResult/EodStepStatus, get_step_sequence, run_step, dry-run` | edit | |
| `tests/test_eod_workflow.py` | 166 | TRIGGER | `Canonical location after extraction from eod.py — mirrors TestReviewStepDispatch` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `tests/test_eod_workflow.py` | 282 | TRIGGER | `must not see itself in its candidate list, in both LLM and` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `tests/test_eod_workflow.py` | 1015 | TRIGGER | `different date must not suppress generation for target_date."""` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `tests/test_gdrive.py` | 3 | INVENTORY | `- GDriveRepository (DB layer)` | edit | |
| `tests/test_gdrive.py` | 4 | INVENTORY | `- cache.py (folder ID cache)` | edit | |
| `tests/test_gdrive.py` | 5 | INVENTORY | `- _format_notes_markdown (§3.8 notes formatter)` | edit | |
| `tests/test_gdrive.py` | 6 | FLAG,INVENTORY | `- gdocs upload all --dry-run (CLI)` | edit | |
| `tests/test_gdrive.py` | 225 | FLAG | `# Test 10 — upload-all --dry-run (CLI, all Drive API mocked)` | leave as is | Test-section banner naming the CLI surface under test; §3.1 governs module headers, not comments, and this states no process rule. |
| `tests/test_ics_import.py` | 740 | TRIGGER | `The original Mon 2099-05-11 09:00 occurrence must NOT appear.` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `tests/test_ics_import.py` | 753 | TRIGGER | `# Original Monday occurrence must NOT be present` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `tests/test_ics_import.py` | 822 | TRIGGER | `# Condensed note — must NOT be counted` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `tests/test_ics_import.py` | 826 | TRIGGER | `# Info-only note — must NOT be counted` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `tests/test_intent_parser.py` | | NO_HIT | `no match in 266 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_meetings_condense.py` | 102 | VERSION | `# -> conservative collapse to ['internal-only'] (Ray, 20260728), never` | leave as is | Decision attribution recording the why (`CLAUDE.md`); §1.5's bar is a version header or version-history block, and a dated decision note is neither. |
| `tests/test_meetings_edit.py` | | NO_HIT | `no match in 127 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_meetings_repository.py` | | NO_HIT | `no match in 88 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_meetings_track.py` | | NO_HIT | `no match in 110 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_name_or_id_resolution.py` | 5 | INVENTORY | `Covers:` | edit | |
| `tests/test_name_or_id_resolution.py` | 6 | INVENTORY | `- NotesRepository.find_by_content_like()` | edit | |
| `tests/test_name_or_id_resolution.py` | 7 | INVENTORY | `- TimeEntriesRepository.find_by_description_like()` | edit | |
| `tests/test_name_or_id_resolution.py` | 8 | INVENTORY | `- Both ID-path and name-path resolution logic` | edit | |
| `tests/test_note_condenser.py` | 3 | INVENTORY | `- _compute_condensed_tags(): the condensed-summary tag classifier (Design` | edit | |
| `tests/test_note_condenser.py` | 5 | INVENTORY | `- condense_meeting()'s two return paths (the early "Attended <Meeting>"` | edit | |
| `tests/test_note_condenser.py` | 49 | VERSION | `# Ray's conservative rule, 20260728.` | leave as is | Decision attribution recording the why (`CLAUDE.md`); §1.5's bar is a version header or version-history block, and a dated decision note is neither. |
| `tests/test_notes_add.py` | | NO_HIT | `no match in 103 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_notes_edit.py` | | NO_HIT | `no match in 83 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_notes_list.py` | 5 | INVENTORY | `Covers:` | edit | |
| `tests/test_notes_list.py` | 6 | INVENTORY | `- get_filtered() exact date filter` | edit | |
| `tests/test_notes_list.py` | 7 | INVENTORY | `- get_filtered() date range (start/end, boundary inclusion)` | edit | |
| `tests/test_notes_list.py` | 8 | INVENTORY | `- get_filtered() meeting_ids filter` | edit | |
| `tests/test_notes_list.py` | 9 | INVENTORY | `- get_filtered() FTS search keyword` | edit | |
| `tests/test_notes_list.py` | 10 | INVENTORY | `- get_filtered() include_tags OR logic` | edit | |
| `tests/test_notes_list.py` | 11 | INVENTORY | `- get_filtered() limit cap and ordering` | edit | |
| `tests/test_notes_list.py` | 12 | INVENTORY | `- get_filtered() combined AND filters` | edit | |
| `tests/test_notes_list.py` | 13 | FLAG,INVENTORY | `- CLI: error paths, --history warning, invalid date, deprecated aliases` | edit | |
| `tests/test_notes_list.py` | 14 | FLAG,INVENTORY | `- CLI: notes today --search flag acceptance` | edit | |
| `tests/test_notes_list.py` | 411 | FLAG | `# CLI — 'notes today --search' flag` | leave as is | Test-section banner naming the CLI surface under test; §3.1 governs module headers, not comments, and this states no process rule. |
| `tests/test_notes_log.py` | 161 | VERSION | `# ['internal-only'] (Ray, 20260728), never the old hard-coded ['both'].` | leave as is | Decision attribution recording the why (`CLAUDE.md`); §1.5's bar is a version header or version-history block, and a dated decision note is neither. |
| `tests/test_notes_repo.py` | | NO_HIT | `no match in 110 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_notes_service.py` | | NO_HIT | `no match in 229 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_notes_show.py` | 5 | INVENTORY | `Covers:` | edit | |
| `tests/test_notes_show.py` | 6 | INVENTORY | `- CLI: 'notes show <id>' not-found error path` | edit | |
| `tests/test_notes_show.py` | 7 | INVENTORY | `- CLI: 'notes show <keyword>' not-found error path` | edit | |
| `tests/test_notes_show.py` | 8 | INVENTORY | `- Repo: get_by_id() for valid and invalid IDs` | edit | |
| `tests/test_notes_show.py` | 9 | INVENTORY | `- Repo: find_by_content_like() substring match (backs the name-path)` | edit | |
| `tests/test_notification_engine.py` | | NO_HIT | `no match in 303 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_notifications_commands.py` | | NO_HIT | `no match in 189 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_ollama_provider.py` | | NO_HIT | `no match in 224 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_orchestration.py` | 1155 | TRIGGER | `schedule_exceptions) must not crash job_workday_start(); it falls back` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `tests/test_orchestration.py` | 759 | TRIGGER | `# must not raise` | leave as is | Trailing comment on a code line, describing local behaviour; states no process rule. |
| `tests/test_prompt_builder_data_sources.py` | 3 | INVENTORY | `- data_sources gating: time_entries omitted from prompt when absent from section config` | edit | |
| `tests/test_prompt_builder_data_sources.py` | 4 | INVENTORY | `- client filter forwarding: filter_client=True propagated to repo calls` | edit | |
| `tests/test_prompt_builder_data_sources.py` | 5 | INVENTORY | `- preview_report filter parity: same client filter applied as full report generation` | edit | |
| `tests/test_provider_foundation.py` | 3 | INVENTORY | `- PROVIDER_REGISTRY structure and subclass contract` | edit | |
| `tests/test_provider_foundation.py` | 4 | INVENTORY | `- base_provider.py additions (ProviderUnavailableError, OLLAMA, test_connection)` | edit | |
| `tests/test_provider_foundation.py` | 5 | INVENTORY | `- OllamaProvider ABC-compliant stub` | edit | |
| `tests/test_provider_foundation.py` | 6 | INVENTORY | `- Config-driven model selection (ClaudeProvider, GeminiProvider)` | edit | |
| `tests/test_provider_foundation.py` | 7 | INVENTORY | `- ProviderManager N-provider: disabled tracking, get_provider, registry methods` | edit | |
| `tests/test_provider_foundation.py` | 8 | INVENTORY | `- Dynamic CLI validation (providers test, providers costs)` | edit | |
| `tests/test_provider_foundation.py` | 9 | INVENTORY | `- providers set default read-modify-write` | edit | |
| `tests/test_recurring_edits.py` | | NO_HIT | `no match in 299 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_recurring_meetings.py` | | NO_HIT | `no match in 378 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_report_correction.py` | 3 | FLAG | `--status filter on reports list, and weekly aggregation filter.` | edit | |
| `tests/test_report_correction.py` | 5 | INVENTORY | `Covers:` | edit | |
| `tests/test_report_correction.py` | 6 | INVENTORY | `- Report model: new report defaults to status='unconfirmed'` | edit | |
| `tests/test_report_correction.py` | 7 | INVENTORY | `- reports confirm: sets status='confirmed'; idempotent on already-confirmed` | edit | |
| `tests/test_report_correction.py` | 8 | INVENTORY | `- reports correct: saves corrected_content, sets status='corrected',` | edit | |
| `tests/test_report_correction.py` | 10 | FLAG,INVENTORY | `- reports list --status: filters by unconfirmed/confirmed/corrected/all` | edit | |
| `tests/test_report_correction.py` | 11 | INVENTORY | `- reports list (no flag): existing behavior preserved (shows all)` | edit | |
| `tests/test_report_correction.py` | 12 | FLAG,INVENTORY | `- reports list --status invalid: validation error` | edit | |
| `tests/test_report_correction.py` | 13 | INVENTORY | `- EOD Step 4a pre-check: skips generation if confirmed/corrected report exists` | edit | |
| `tests/test_report_correction.py` | 14 | INVENTORY | `- EOD Step 4a: report starts as unconfirmed after generation` | edit | |
| `tests/test_report_correction.py` | 15 | INVENTORY | `- weekly_client generation via build_prompt(): always template-formatted` | edit | |
| `tests/test_report_correction.py` | 19 | INVENTORY | `- ReportsRepository.get_filtered(): status/type/date/updated_after floor/` | edit | |
| `tests/test_report_correction.py` | 21 | INVENTORY | `- ReportsRepository.apply_correction(): corrected_content/status write,` | edit | |
| `tests/test_report_correction.py` | 23 | INVENTORY | `- reports correct (CLI): now routed through edit_in_editor() +` | edit | |
| `tests/test_report_correction.py` | 143 | FLAG | `# Reports repo — list_reports --status filter` | leave as is | Test-section banner naming the CLI surface under test; §3.1 governs module headers, not comments, and this states no process rule. |
| `tests/test_report_correction.py` | 329 | FLAG | `# CLI — reports list --status (error path validation)` | leave as is | Test-section banner naming the CLI surface under test; §3.1 governs module headers, not comments, and this states no process rule. |
| `tests/test_report_correction.py` | 542 | TRIGGER | `# must not raise` | leave as is | Trailing comment on a code line, describing local behaviour; states no process rule. |
| `tests/test_report_history.py` | | NO_HIT | `no match in 339 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_reports_corrections.py` | 3 | FLAG | `updated_at), --search/--limit/--type/--all, sort order, and display` | edit | |
| `tests/test_reports_corrections.py` | 8 | COMMAND | `pytest db_session fixture. CliRunner invokes the command via its own` | leave as is | DR6 / F9 — accurate description of this module's own session mechanism and its reason; "pytest db_session fixture" names the fixture, not an invocation. |
| `tests/test_reports_corrections.py` | 18 | FLAG | `unique correction_note marker term (--search) or a sentinel far-future` | edit | |
| `tests/test_reports_corrections.py` | 19 | FLAG | `report_date (--date) — never by exact result count against an unfiltered` | edit | |
| `tests/test_schedule_commands.py` | | NO_HIT | `no match in 173 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_schedule_service.py` | | NO_HIT | `no match in 221 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_self_invoke.py` | | NO_HIT | `no match in 107 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_slack.py` | 5 | INVENTORY | `- TestSlackReportsIntegration      — real DB, reports table` | edit | |
| `tests/test_slack.py` | 6 | INVENTORY | `- TestSlackAuth                    — token loading` | edit | |
| `tests/test_slack.py` | 7 | INVENTORY | `- TestFormatForSlack                — markdown conversion` | edit | |
| `tests/test_slack.py` | 8 | INVENTORY | `- TestDraftDateRange                — date range calculation` | edit | |
| `tests/test_slack.py` | 9 | INVENTORY | `- TestSlackClient                   — mocked Slack API` | edit | |
| `tests/test_slack.py` | 10 | INVENTORY | `- TestDraftLabel                    — DRAFT label prepend behaviour` | edit | |
| `tests/test_slack.py` | 11 | INVENTORY | `- TestSlackPostWeeklySharedRunner   — slack_post() driving the shared` | edit | |
| `tests/test_slack.py` | 196 | TRIGGER | `"""# Heading must become *Heading*, not _Heading_ (italic must not re-match)."""` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `tests/test_slack.py` | 190 | TRIGGER | `# Bold and italic on same line — must not interfere` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `tests/test_slack_channel_config.py` | 3 | INVENTORY | `- slack set channel: writes clients.slack_channel for active client` | edit | |
| `tests/test_slack_channel_config.py` | 4 | INVENTORY | `- slack set workspace: informational, no writes` | edit | |
| `tests/test_slack_channel_config.py` | 5 | INVENTORY | `- slack channel set: retired (command not found)` | edit | |
| `tests/test_slack_channel_config.py` | 6 | INVENTORY | `- post-weekly channel resolution: clients.slack_channel first, config fallback` | edit | |
| `tests/test_slack_channel_config.py` | 7 | INVENTORY | `- slack status: displays clients.slack_channel as primary channel value` | edit | |
| `tests/test_state_io.py` | | NO_HIT | `no match in 77 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_system_state_repository.py` | | NO_HIT | `no match in 88 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_tag_system.py` | | NO_HIT | `no match in 353 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_task_lifecycle.py` | 5 | INVENTORY | `Covers:` | edit | |
| `tests/test_task_lifecycle.py` | 6 | INVENTORY | `- TaskStatusRepository: create_active, ensure_active, set_completed,` | edit | |
| `tests/test_task_lifecycle.py` | 9 | FLAG,INVENTORY | `- CLI error paths: tasks list --status invalid, tasks show/complete nonexistent` | edit | |
| `tests/test_task_lifecycle.py` | 10 | FLAG,INVENTORY | `- CLI: tasks list --all removes the row cap independent of --status; --status` | edit | |
| `tests/test_task_lifecycle.py` | 13 | INVENTORY | `- Notes carry-forward hook: ensure_active and set_dismissed_by_tag_removal` | edit | |
| `tests/test_task_lifecycle.py` | 318 | FLAG | `# CLI — tasks list --all/--status decoupling, truncation-honest header,` | leave as is | Test-section banner naming the CLI surface under test; §3.1 governs module headers, not comments, and this states no process rule. |
| `tests/test_templates.py` | | NO_HIT | `no match in 267 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_time_add.py` | | NO_HIT | `no match in 194 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_time_entries_refactor.py` | 3 | INVENTORY | `- note_id FK enforcement (NOT NULL, ON DELETE RESTRICT)` | edit | |
| `tests/test_time_entries_refactor.py` | 4 | INVENTORY | `- get_by_note_id() return values` | edit | |
| `tests/test_time_entries_refactor.py` | 5 | INVENTORY | `- notes delete pre-check guard data source` | edit | |
| `tests/test_time_entries_refactor.py` | 6 | INVENTORY | `- client/project consistency guard in both NotesRepository and TimeEntriesRepository` | edit | |
| `tests/test_time_entries_repo.py` | | NO_HIT | `no match in 112 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_time_entry_service.py` | | NO_HIT | `no match in 315 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_time_parser.py` | | NO_HIT | `no match in 121 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_time_tracking.py` | | NO_HIT | `no match in 245 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `tests/test_utils_date_format.py` | | NO_HIT | `no match in 27 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/__init__.py` | 1 | NO_HEADER | `(no module docstring)` | edit | |
| `workmain/__version__.py` | | NO_HIT | `no match in 8 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/ai/__init__.py` | 5 | INVENTORY | `- Abstract base provider class` | edit | |
| `workmain/ai/__init__.py` | 6 | INVENTORY | `- Provider registry (claude, gemini, ollama)` | edit | |
| `workmain/ai/__init__.py` | 7 | INVENTORY | `- Provider manager with fallback` | edit | |
| `workmain/ai/__init__.py` | 8 | INVENTORY | `- Cost tracking system` | edit | |
| `workmain/ai/__init__.py` | 9 | INVENTORY | `- Prompt builder for report generation` | edit | |
| `workmain/ai/__init__.py` | 10 | INVENTORY | `- Report generator orchestrator` | edit | |
| `workmain/ai/base_provider.py` | 6 | INVENTORY | `- generate() for text generation` | edit | |
| `workmain/ai/base_provider.py` | 7 | INVENTORY | `- estimate_cost() for cost calculation` | edit | |
| `workmain/ai/base_provider.py` | 8 | INVENTORY | `- validate_config() for configuration validation` | edit | |
| `workmain/ai/base_provider.py` | 9 | INVENTORY | `- count_tokens() for token estimation` | edit | |
| `workmain/ai/base_provider.py` | 10 | INVENTORY | `- check_availability() for connectivity` | edit | |
| `workmain/ai/cost_tracker.py` | 5 | INVENTORY | `Features:` | edit | |
| `workmain/ai/cost_tracker.py` | 6 | INVENTORY | `- Per-section cost tracking (detailed)` | edit | |
| `workmain/ai/cost_tracker.py` | 7 | INVENTORY | `- Per-report cost aggregation` | edit | |
| `workmain/ai/cost_tracker.py` | 8 | INVENTORY | `- Provider-specific tracking` | edit | |
| `workmain/ai/cost_tracker.py` | 9 | INVENTORY | `- Cost history and analytics` | edit | |
| `workmain/ai/cost_tracker.py` | 10 | INVENTORY | `- Budget alerts` | edit | |
| `workmain/ai/intent_parser.py` | | NO_HIT | `no match in 259 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/ai/note_condenser.py` | 43 | VERSION | `# (Ray, 20260728). Expected to be rare in practice.` | leave as is | Decision attribution recording the why (`CLAUDE.md`); §1.5's bar is a version header or version-history block, and a dated decision note is neither. |
| `workmain/ai/prompt_builder.py` | 4 | INVENTORY | `Features:` | edit | |
| `workmain/ai/prompt_builder.py` | 5 | INVENTORY | `- Integrates template structure with database data` | edit | |
| `workmain/ai/prompt_builder.py` | 6 | INVENTORY | `- Applies user's writing style` | edit | |
| `workmain/ai/prompt_builder.py` | 7 | INVENTORY | `- Includes Master Log examples for context` | edit | |
| `workmain/ai/prompt_builder.py` | 8 | INVENTORY | `- Manages context window limits` | edit | |
| `workmain/ai/prompt_builder.py` | 9 | INVENTORY | `- Builds system and user prompts` | edit | |
| `workmain/ai/prompt_builder.py` | 10 | INVENTORY | `- Supports both Claude and Gemini formats` | edit | |
| `workmain/ai/prompt_builder.py` | 12 | INVENTORY | `1. Load template structure` | edit | |
| `workmain/ai/prompt_builder.py` | 13 | INVENTORY | `2. Get relevant data from database (filtered by tags)` | edit | |
| `workmain/ai/prompt_builder.py` | 14 | INVENTORY | `3. Load user's writing style preferences` | edit | |
| `workmain/ai/prompt_builder.py` | 15 | INVENTORY | `4. Select relevant Master Log examples` | edit | |
| `workmain/ai/prompt_builder.py` | 16 | INVENTORY | `5. Build comprehensive prompt` | edit | |
| `workmain/ai/prompt_builder.py` | 17 | INVENTORY | `6. Manage token limits` | edit | |
| `workmain/ai/prompt_builder.py` | 397 | TRIGGER | `tags_exclude: Tags that must not be present` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/ai/provider_manager.py` | 4 | INVENTORY | `Features:` | edit | |
| `workmain/ai/provider_manager.py` | 5 | INVENTORY | `- N-provider extensible registry (claude, gemini, ollama, ...)` | edit | |
| `workmain/ai/provider_manager.py` | 6 | INVENTORY | `- Per-report-type provider selection from ai_settings.json` | edit | |
| `workmain/ai/provider_manager.py` | 7 | INVENTORY | `- Configurable fallback (manual/automatic)` | edit | |
| `workmain/ai/provider_manager.py` | 8 | INVENTORY | `- Provider health monitoring` | edit | |
| `workmain/ai/provider_manager.py` | 9 | INVENTORY | `- Notification on fallback` | edit | |
| `workmain/ai/provider_manager.py` | 10 | INVENTORY | `- Disabled provider tracking (no connectivity check for disabled providers)` | edit | |
| `workmain/ai/provider_manager.py` | 246 | TRIGGER | `Update fallback mode for a report type.` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/ai/providers/__init__.py` | 4 | INVENTORY | `1. Create workmain/ai/providers/<name>.py implementing BaseProvider` | remove | |
| `workmain/ai/providers/__init__.py` | 5 | INVENTORY | `2. Import and add one line to PROVIDER_REGISTRY below` | remove | |
| `workmain/ai/providers/__init__.py` | 6 | INVENTORY | `3. Add a section to config/ai_settings.json` | remove | |
| `workmain/ai/providers/claude.py` | 5 | TRIGGER | `Do not instantiate directly — use get_provider_manager().get_provider('claude').` | edit | Pre-adjudicated (§1, §4.3) — imperative addressed to a reader; restated descriptively. |
| `workmain/ai/providers/claude.py` | 7 | INVENTORY | `Features:` | edit | |
| `workmain/ai/providers/claude.py` | 8 | INVENTORY | `- Anthropic SDK integration` | edit | |
| `workmain/ai/providers/claude.py` | 9 | INVENTORY | `- Config-driven model selection (reads model from ai_settings.json)` | edit | |
| `workmain/ai/providers/claude.py` | 10 | INVENTORY | `- Token counting with Anthropic client` | edit | |
| `workmain/ai/providers/claude.py` | 11 | INVENTORY | `- Retry logic with exponential backoff` | edit | |
| `workmain/ai/providers/claude.py` | 12 | INVENTORY | `- Cost tracking` | edit | |
| `workmain/ai/providers/gemini.py` | 5 | TRIGGER | `Do not instantiate directly — use get_provider_manager().get_provider('gemini').` | edit | Pre-adjudicated (§1, §4.3) — imperative addressed to a reader; restated descriptively. |
| `workmain/ai/providers/gemini.py` | 7 | INVENTORY | `Features:` | edit | |
| `workmain/ai/providers/gemini.py` | 8 | INVENTORY | `- Google GenAI SDK integration (google-genai package)` | edit | |
| `workmain/ai/providers/gemini.py` | 9 | INVENTORY | `- Config-driven model selection (reads model from ai_settings.json)` | edit | |
| `workmain/ai/providers/gemini.py` | 10 | INVENTORY | `- Native token counting` | edit | |
| `workmain/ai/providers/gemini.py` | 11 | INVENTORY | `- Retry logic with exponential backoff` | edit | |
| `workmain/ai/providers/gemini.py` | 12 | INVENTORY | `- Cost tracking` | edit | |
| `workmain/ai/providers/ollama.py` | | NO_HIT | `no match in 129 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/ai/report_generator.py` | 4 | INVENTORY | `Features:` | edit | |
| `workmain/ai/report_generator.py` | 5 | INVENTORY | `- Orchestrates full report generation pipeline` | edit | |
| `workmain/ai/report_generator.py` | 6 | INVENTORY | `- Combines prompt_builder + AI clients + templates` | edit | |
| `workmain/ai/report_generator.py` | 7 | INVENTORY | `- Handles section-by-section generation (optional)` | edit | |
| `workmain/ai/report_generator.py` | 8 | INVENTORY | `- Saves reports to files (markdown, text)` | edit | |
| `workmain/ai/report_generator.py` | 9 | INVENTORY | `- Saves report metadata to database for analytics` | edit | |
| `workmain/ai/report_generator.py` | 10 | INVENTORY | `- Provides generation status and logging` | edit | |
| `workmain/ai/report_generator.py` | 11 | INVENTORY | `- Manages errors and retries` | edit | |
| `workmain/ai/report_generator.py` | 12 | INVENTORY | `- Tracks costs in database (not JSON file)` | edit | |
| `workmain/ai/report_generator.py` | 14 | INVENTORY | `1. Load template and validate` | edit | |
| `workmain/ai/report_generator.py` | 15 | INVENTORY | `2. Build prompts with prompt_builder` | edit | |
| `workmain/ai/report_generator.py` | 16 | INVENTORY | `3. Start cost tracking (start_report)` | edit | |
| `workmain/ai/report_generator.py` | 17 | INVENTORY | `4. Generate content with AI client` | edit | |
| `workmain/ai/report_generator.py` | 18 | INVENTORY | `5. Track costs (track_section)` | edit | |
| `workmain/ai/report_generator.py` | 19 | INVENTORY | `6. Format output` | edit | |
| `workmain/ai/report_generator.py` | 20 | INVENTORY | `7. Save to file` | edit | |
| `workmain/ai/report_generator.py` | 21 | INVENTORY | `8. Save to database with report_metadata (costs, tokens, provider)` | edit | |
| `workmain/ai/report_generator.py` | 22 | INVENTORY | `9. End cost tracking (end_report with timing)` | edit | |
| `workmain/ai/report_generator.py` | 147 | FLAG | `# provider stays None unless --provider flag was passed by caller;` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/ai/report_generator.py` | 294 | FLAG | `# provider stays None unless --provider flag was passed by caller;` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/cli/__init__.py` | 1 | NO_HEADER | `(no module docstring)` | edit | |
| `workmain/cli/commands/__init__.py` | 1 | NO_HEADER | `(no module docstring)` | edit | |
| `workmain/cli/commands/calendar.py` | 4 | INVENTORY | `Commands:` | edit | |
| `workmain/cli/commands/calendar.py` | 382 | TRIGGER | `Use 'workmain calendar import <file.ics>' to import via ICS export instead.` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/clients.py` | 5 | INVENTORY | `Commands:` | edit | |
| `workmain/cli/commands/clients.py` | 150 | TRIGGER | `Use --force if the client is currently active.` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/clockify.py` | 4 | INVENTORY | `Commands:` | edit | |
| `workmain/cli/commands/clockify.py` | 5 | INVENTORY | `- clockify report save [period]      # Download PDF report (daily/weekly/monthly)` | edit | |
| `workmain/cli/commands/clockify.py` | 6 | INVENTORY | `- clockify status                    # Show connection and sync status` | edit | |
| `workmain/cli/commands/clockify.py` | 7 | INVENTORY | `- clockify sync push/pull/both       # Sync time entries with Clockify` | edit | |
| `workmain/cli/commands/clockify.py` | 160 | TRIGGER | `Use --start/-b and --end/-e to override the date range for any period.` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/clockify.py` | 344 | TRIGGER | `Use this after creating entries directly in Clockify (e.g., mobile app` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/clockify.py` | 283 | FLAG | `# Filter to unsynced unless --all` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/cli/commands/email.py` | 6 | INVENTORY | `Commands:` | edit | |
| `workmain/cli/commands/email.py` | 250 | TRIGGER | `Use 'workmain clients status' to confirm current context.` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/email.py` | 337 | TRIGGER | `Use 'workmain email save <template>' to save draft locally.` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/email.py` | 631 | TRIGGER | `Use 'workmain clients status' to confirm current context before assigning.` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/eod.py` | 7 | INVENTORY | `1.  Condense pending meeting notes (meetings with notes, no condensed_summary)` | edit | |
| `workmain/cli/commands/eod.py` | 8 | INVENTORY | `2.  Sync time entries to Clockify (clockify sync push)` | edit | |
| `workmain/cli/commands/eod.py` | 9 | FLAG,INVENTORY | `3.  Review time entries (loop until confirmed; uses target date when --date is set)` | edit | |
| `workmain/cli/commands/eod.py` | 14 | INVENTORY | `5.  Pull Clockify PDF (clockify report save daily → staging/clockify/)` | edit | |
| `workmain/cli/commands/eod.py` | 15 | INVENTORY | `6.  Upload to Google Drive (gdocs upload all)` | edit | |
| `workmain/cli/commands/eod.py` | 16 | INVENTORY | `7.  Complete — step summary and sign-off` | edit | |
| `workmain/cli/commands/eod.py` | 19 | INVENTORY | `7. Post weekly draft to Slack (slack post weekly)` | edit | |
| `workmain/cli/commands/eod.py` | 20 | INVENTORY | `8. Complete` | edit | |
| `workmain/cli/commands/eod.py` | 23 | INVENTORY | `7. Generate weekly report (reports save weekly_client)` | edit | |
| `workmain/cli/commands/eod.py` | 24 | INVENTORY | `8. Create weekly email draft (email save weekly_client)` | edit | |
| `workmain/cli/commands/eod.py` | 25 | INVENTORY | `9. Complete` | edit | |
| `workmain/cli/commands/eod.py` | 106 | TRIGGER | `Use '--skip email' to skip only the draft (4b), keeping report generation.` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/eod.py` | 107 | TRIGGER | `Use '--skip weekly' to skip Thursday/Friday weekly steps only.` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/gdocs.py` | 4 | INVENTORY | `Commands:` | edit | |
| `workmain/cli/commands/gdocs.py` | 5 | FLAG,INVENTORY | `- gdocs auth [--reauth]          # Authenticate / re-authenticate` | edit | |
| `workmain/cli/commands/gdocs.py` | 6 | INVENTORY | `- gdocs status                   # Auth state, cached folders, recent uploads` | edit | |
| `workmain/cli/commands/gdocs.py` | 7 | INVENTORY | `- gdocs upload notes             # DB notes → markdown → staging/notes/ → Drive` | edit | |
| `workmain/cli/commands/gdocs.py` | 8 | INVENTORY | `- gdocs upload report            # staging/reports/daily_internal_YYYY-MM-DD.md → Drive` | edit | |
| `workmain/cli/commands/gdocs.py` | 9 | INVENTORY | `- gdocs upload clockify          # staging/clockify/Clockify_YYYYMMDD.pdf → Drive` | edit | |
| `workmain/cli/commands/gdocs.py` | 10 | INVENTORY | `- gdocs upload all               # Runs all three in sequence` | edit | |
| `workmain/cli/commands/gdocs.py` | 582 | TRIGGER | `Runs upload notes, report, and clockify in order.` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/meetings.py` | 1298 | TRIGGER | `Update the wall-clock time for all future occurrences in a recurring series.` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/meetings.py` | 1500 | TRIGGER | `Use 'meetings template use <name>' to create meetings from a template.` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/meetings.py` | 184 | FLAG | `# Validate recurring parameters and set default --until` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/cli/commands/meetings.py` | 272 | FLAG | `# Skip weekends unless --include-weekends specified` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/cli/commands/meetings.py` | 369 | FLAG | `# Parse --date if provided` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/cli/commands/meetings.py` | 1069 | FLAG | `# Resolve the date to shift onto (explicit --date or keep existing)` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/cli/commands/meetings.py` | 1097 | FLAG | `# --date only: shift existing start wall-clock time onto new date` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/cli/commands/meetings.py` | 1112 | FLAG | `# --date only: shift existing end wall-clock time onto new date` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/cli/commands/meetings.py` | 1199 | FLAG | `# Resolve new date (explicit --date or keep existing)` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/cli/commands/meetings.py` | 1428 | FLAG | `# If --date was given, try to find the specific occurrence on that date` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/cli/commands/notes.py` | 950 | TRIGGER | `Use 'workmain notes list --date <date>' instead.` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/notes.py` | 970 | TRIGGER | `Use 'workmain notes list --search <keyword>' instead.` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/notes.py` | 989 | TRIGGER | `Use 'workmain notes list --meeting <title>' instead.` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/notes.py` | 261 | FLAG | `# --meeting with no value = interactive` | leave as is | Trailing comment on a code line, describing local behaviour; states no process rule. |
| `workmain/cli/commands/notes.py` | 266 | FLAG | `# --meeting "Title"` | leave as is | Trailing comment on a code line, describing local behaviour; states no process rule. |
| `workmain/cli/commands/notes.py` | 279 | FLAG | `# Parse --tags flag if provided` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/cli/commands/notifications.py` | 5 | INVENTORY | `Commands:` | edit | |
| `workmain/cli/commands/providers.py` | 4 | INVENTORY | `Commands:` | edit | |
| `workmain/cli/commands/providers.py` | 5 | INVENTORY | `- providers list: Show all providers, status, model, cost structure` | edit | |
| `workmain/cli/commands/providers.py` | 6 | INVENTORY | `- providers test <provider>: Test provider API connection` | edit | |
| `workmain/cli/commands/providers.py` | 7 | INVENTORY | `- providers costs: Show aggregate cost totals` | edit | |
| `workmain/cli/commands/providers.py` | 8 | INVENTORY | `- providers set default <REPORT_TYPE> <PROVIDER>: Update provider assignment` | edit | |
| `workmain/cli/commands/providers.py` | 9 | INVENTORY | `- providers config show: Display full ai_settings.json detail view` | edit | |
| `workmain/cli/commands/reports.py` | 4 | INVENTORY | `Commands:` | edit | |
| `workmain/cli/commands/reports.py` | 5 | INVENTORY | `- reports preview <template>   # preview prompts, no AI cost` | edit | |
| `workmain/cli/commands/reports.py` | 6 | INVENTORY | `- reports save <template>      # generate with AI, save to staging/reports/` | edit | |
| `workmain/cli/commands/reports.py` | 7 | INVENTORY | `- reports send <template>      # stub — chains to email send (OAuth required)` | edit | |
| `workmain/cli/commands/reports.py` | 8 | INVENTORY | `- reports list / history       # list reports from DB (history is alias)` | edit | |
| `workmain/cli/commands/reports.py` | 9 | INVENTORY | `- reports show <id\|file>       # show by DB id (int) or filename (str)` | edit | |
| `workmain/cli/commands/reports.py` | 10 | INVENTORY | `- reports resend <id>          # recreate email draft from stored report` | edit | |
| `workmain/cli/commands/reports.py` | 11 | FLAG,INVENTORY | `- reports corrections [-d DATE] [-s SEARCH] [-n LIMIT] [-R TYPE] [--all]` | edit | |
| `workmain/cli/commands/reports.py` | 13 | INVENTORY | `- reports costs` | edit | |
| `workmain/cli/commands/reports.py` | 290 | TRIGGER | `Use 'workmain reports save <template>' to generate and save locally,` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/schedule.py` | | NO_HIT | `no match in 578 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/cli/commands/slack.py` | 4 | INVENTORY | `Commands:` | edit | |
| `workmain/cli/commands/slack.py` | 5 | INVENTORY | `- slack setup                           # Interactive setup checklist` | edit | |
| `workmain/cli/commands/slack.py` | 6 | FLAG,INVENTORY | `- slack auth [--reauth]                 # Validate Bot Token, cache workspace name` | edit | |
| `workmain/cli/commands/slack.py` | 7 | INVENTORY | `- slack status                          # Auth state + recent Slack posts` | edit | |
| `workmain/cli/commands/slack.py` | 8 | INVENTORY | `- slack set channel <channel>           # Set Slack channel for the active client` | edit | |
| `workmain/cli/commands/slack.py` | 9 | INVENTORY | `- slack set workspace                   # Show workspace config file path (informational)` | edit | |
| `workmain/cli/commands/slack.py` | 10 | FLAG,INVENTORY | `- slack post PERIOD [flags]             # Generate/review (shared runner) → post; PERIOD=weekly\|daily\|monthly` | edit | |
| `workmain/cli/commands/slack.py` | 281 | TRIGGER | `Use 'workmain clients set active' to switch clients.` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/cli/commands/tasks.py` | 177 | FLAG | `# --all is a pure row-cap override, independent of --status (Design Rule 1)` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/cli/commands/templates.py` | | NO_HIT | `no match in 551 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/cli/commands/time.py` | 191 | FLAG | `# Validate --notes requires --meeting` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/cli/interface.py` | 3 | TRIGGER | `Updated for CLI Standardization Sprint Part 1` | remove | |
| `workmain/cli/interface.py` | 96 | TRIGGER | `Use 'workmain COMMAND --help' for more information on a specific command.` | leave as is | Click command docstring — this text *is* the `--help` output, which §5.6 (Edit 5) makes the one home for invocations and flags. DR8.2 applies below module level for recall only. |
| `workmain/config_manager/__init__.py` | 1 | NO_HEADER | `(no module docstring)` | edit | |
| `workmain/config_manager/alias_manager.py` | 4 | INVENTORY | `Features:` | edit | |
| `workmain/config_manager/alias_manager.py` | 5 | INVENTORY | `- Load aliases from config/template_aliases.json` | edit | |
| `workmain/config_manager/alias_manager.py` | 6 | INVENTORY | `- Register new aliases` | edit | |
| `workmain/config_manager/alias_manager.py` | 7 | INVENTORY | `- Unregister aliases` | edit | |
| `workmain/config_manager/alias_manager.py` | 8 | INVENTORY | `- Resolve alias to template name` | edit | |
| `workmain/config_manager/alias_manager.py` | 9 | INVENTORY | `- List all aliases` | edit | |
| `workmain/config_manager/loader.py` | | NO_HIT | `no match in 292 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/config_manager/validator.py` | | NO_HIT | `no match in 256 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/core/__init__.py` | 1 | NO_HEADER | `(no module docstring)` | edit | |
| `workmain/daemon/__init__.py` | 2 | TRIGGER | `Always-on background notification daemon. Manages the APScheduler` | leave as is | False positive — the `Always` opener is the header's one-line summary, which is exactly what §3.1 asks for. |
| `workmain/daemon/acknowledgment.py` | | NO_HIT | `no match in 104 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/daemon/conversation_state.py` | 91 | FLAG | `# original --skip` | leave as is | Trailing comment on a code line, describing local behaviour; states no process rule. |
| `workmain/daemon/daemon.py` | 7 | TRIGGER | `Run via systemd user service (workmain-notify.service).` | edit | |
| `workmain/daemon/daemon.py` | 8 | TRIGGER | `Do not run as root — enforced by _check_not_root().` | edit | |
| `workmain/daemon/daemon.py` | 250 | TRIGGER | `warm-up is best-effort; daemon startup must not block on Ollama.` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/daemon/delivery.py` | 3 | INVENTORY | `- 'wsl-notify' → wsl-notify-send (WSL) or notify-send (native Linux)` | edit | |
| `workmain/daemon/delivery.py` | 4 | INVENTORY | `- 'slack'      → Slack DM via daemon.post_message()` | edit | |
| `workmain/daemon/delivery.py` | 5 | INVENTORY | `- 'both'       → wsl-notify + slack` | edit | |
| `workmain/daemon/inspection_engine.py` | 8 | INVENTORY | `1. Time gap       — meeting exists with no linked time entry` | edit | |
| `workmain/daemon/inspection_engine.py` | 9 | INVENTORY | `2. Coverage       — total logged time vs. expected workday hours` | edit | |
| `workmain/daemon/inspection_engine.py` | 10 | INVENTORY | `3. Tag anomaly    — notes with no tags (all notes should have at least` | edit | |
| `workmain/daemon/inspection_engine.py` | 12 | INVENTORY | `4. Missing notes  — meeting occurred with no notes at all` | edit | |
| `workmain/daemon/inspection_engine.py` | 13 | INVENTORY | `5. Carry-forward  — open cf-tagged tasks from previous business day` | edit | |
| `workmain/daemon/models.py` | | NO_HIT | `no match in 24 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/daemon/narration.py` | | NO_HIT | `no match in 103 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/daemon/scheduler.py` | 304 | TRIGGER | `"T4 must not fire after hours" guarantee).` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/daemon/state_io.py` | | NO_HIT | `no match in 66 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/database/__init__.py` | 1 | NO_HEADER | `(no module docstring)` | edit | |
| `workmain/database/connection.py` | 69 | COMMAND | `Usage:` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/database/migrations/001_initial_schema.sql` | | NO_HIT | `no match in 225 lines` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/002_add_condensation_fields.sql` | 4 | VERSION | `-- Date: 20251231` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/003_add_trigram_index.sql` | | NO_HIT | `no match in 33 lines` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/004_add_recipients.sql` | 3 | VERSION | `-- 20260305` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/005_add_gdrive_uploads.sql` | 3 | VERSION | `-- 20260309` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/006_add_slack_columns.sql` | 3 | VERSION | `-- 20260310` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/007_schedule_exceptions.sql` | | NO_HIT | `no match in 22 lines` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/008_notification_config.sql` | | NO_HIT | `no match in 23 lines` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/009_add_is_cancelled.sql` | | NO_HIT | `no match in 13 lines` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/010_system_state.sql` | | NO_HIT | `no match in 34 lines` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/011_clients.sql` | | NO_HIT | `no match in 35 lines` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/012_client_attribution.sql` | | NO_HIT | `no match in 49 lines` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/013_clients_slack_channel.sql` | | NO_HIT | `no match in 13 lines` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/014_report_recipients_client.sql` | | NO_HIT | `no match in 38 lines` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/015_task_status.sql` | | NO_HIT | `no match in 24 lines` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/016_reports_status_columns.sql` | | NO_HIT | `no match in 18 lines` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/017_ai_costs.sql` | 3 | VERSION | `-- 20260528` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/018_extend_ai_costs_interaction_type.sql` | 3 | VERSION | `-- 20260605` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/019_projects_client_id_fk.sql` | | NO_HIT | `no match in 10 lines` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/020_drop_report_recipients_email.sql` | | NO_HIT | `no match in 7 lines` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/021_time_entries_note_id.sql` | 5 | TRIGGER | `--         before this SQL runs (migrate_021_time_entries_note_id.py)` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/022_intent_action_constraints.sql` | 14 | TRIGGER | `-- Verification (run manually after applying):` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/023_task_status_orphan_backfill.sql` | | NO_HIT | `no match in 10 lines` | leave as is | Pre-adjudicated (§1) — one-time migration; comments record what was done (v1.29.0 precedent). |
| `workmain/database/migrations/__init__.py` | 1 | NO_HEADER | `(no module docstring)` | edit | |
| `workmain/database/models.py` | | NO_HIT | `no match in 568 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/database/repositories/__init__.py` | | NO_HIT | `no match in 17 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/database/repositories/ai_costs_repo.py` | | NO_HIT | `no match in 189 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/database/repositories/client_repository.py` | 43 | TRIGGER | `name: Client name. Must not be 'internal' (case-insensitive).` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/database/repositories/email_repository.py` | | NO_HIT | `no match in 222 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/database/repositories/gdrive_repository.py` | | NO_HIT | `no match in 142 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/database/repositories/meetings_repo.py` | 452 | TRIGGER | `Update a meeting.` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/database/repositories/meetings_repo.py` | 464 | TRIGGER | `Updated Meeting object or None if not found` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/database/repositories/meetings_repo.py` | 524 | TRIGGER | `Update wall-clock start/end times for all series occurrences from a date forward.` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/database/repositories/meetings_repo.py` | 570 | TRIGGER | `Updated Meeting object or None if not found` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/database/repositories/notes_repo.py` | 238 | TRIGGER | `exclude_tags: Tags that must not be present` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/database/repositories/notes_repo.py` | 317 | TRIGGER | `Update an existing note.` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/database/repositories/notes_repo.py` | 328 | TRIGGER | `Updated Note object or None if not found` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/database/repositories/notes_repo.py` | 150 | TRIGGER | `# Note must NOT have any of the exclude tags (PostgreSQL @> operator)` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/database/repositories/notification_repository.py` | 72 | TRIGGER | `Updated NotificationConfigData.` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/database/repositories/notification_repository.py` | 84 | TRIGGER | `Updated NotificationConfigData.` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/database/repositories/reports_repo.py` | 5 | INVENTORY | `- Create report records with metadata` | edit | |
| `workmain/database/repositories/reports_repo.py` | 6 | INVENTORY | `- Query reports by type, date, or status` | edit | |
| `workmain/database/repositories/reports_repo.py` | 7 | INVENTORY | `- Get cost summaries and analytics` | edit | |
| `workmain/database/repositories/reports_repo.py` | 8 | INVENTORY | `- Link reports to files on disk` | edit | |
| `workmain/database/repositories/schedule_repository.py` | | NO_HIT | `no match in 135 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/database/repositories/system_state_repository.py` | | NO_HIT | `no match in 75 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/database/repositories/task_status_repo.py` | 94 | TRIGGER | `Updated TaskStatus object.` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/database/repositories/task_status_repo.py` | 114 | TRIGGER | `Updated TaskStatus object.` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/database/repositories/task_status_repo.py` | 160 | TRIGGER | `Updated TaskStatus, or None if no record existed.` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/database/repositories/time_entries_repo.py` | 299 | TRIGGER | `Update an existing time entry.` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/database/repositories/time_entries_repo.py` | 312 | TRIGGER | `Updated TimeEntry object or None if not found` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/database/repositories/time_entries_repo.py` | 504 | TRIGGER | `Updated TimeEntry object or None if not found` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/integrations/__init__.py` | 1 | NO_HEADER | `(no module docstring)` | edit | |
| `workmain/integrations/clockify/__init__.py` | | NO_HIT | `no match in 9 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/integrations/clockify/auth.py` | | NO_HIT | `no match in 83 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/integrations/clockify/client.py` | | NO_HIT | `no match in 262 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/integrations/clockify/sync.py` | | NO_HIT | `no match in 366 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/integrations/gdrive/__init__.py` | | NO_HIT | `no match in 26 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/integrations/gdrive/auth.py` | | NO_HIT | `no match in 106 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/integrations/gdrive/cache.py` | | NO_HIT | `no match in 86 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/integrations/gdrive/client.py` | | NO_HIT | `no match in 207 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/integrations/outlook/__init__.py` | | NO_HIT | `no match in 8 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/integrations/outlook/client.py` | 103 | TRIGGER | `Use stored refresh_token to obtain new access_token silently.` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/integrations/outlook/client.py` | 105 | TRIGGER | `Updates outlook_tokens.json with new token and expiry.` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/integrations/slack/__init__.py` | | NO_HIT | `no match in 54 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/integrations/slack/auth.py` | 7 | FLAG | `Token:       .env SLACK_BOT_TOKEN=xoxb-...` | remove | |
| `workmain/integrations/slack/client.py` | | NO_HIT | `no match in 210 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/integrations/slack/slack_eod.py` | 357 | TRIGGER | `Once cancel_event is set, this thread must not mutate session state` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/integrations/slack/slack_eod.py` | 94 | TRIGGER | `# DR10 — an offer made before the session must not survive it.` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/integrations/slack/socket_client.py` | | NO_HIT | `no match in 166 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/notifications/__init__.py` | 1 | NO_HEADER | `(no module docstring)` | edit | |
| `workmain/orchestration/__init__.py` | | NO_HIT | `no match in 18 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/orchestration/action_executor.py` | | NO_HIT | `no match in 363 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/orchestration/confirmation_gate.py` | | NO_HIT | `no match in 152 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/services/__init__.py` | | NO_HIT | `no match in 12 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/services/exceptions.py` | | NO_HIT | `no match in 26 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/services/notes_service.py` | | NO_HIT | `no match in 146 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/services/schedule_service.py` | | NO_HIT | `no match in 116 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/services/time_entry_service.py` | | NO_HIT | `no match in 124 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/templates_engine/__init__.py` | | NO_HIT | `no match in 27 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/templates_engine/field_manager.py` | | NO_HIT | `no match in 409 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/templates_engine/loader.py` | | NO_HIT | `no match in 325 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/templates_engine/renderer.py` | | NO_HIT | `no match in 420 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/templates_engine/style_adapter.py` | | NO_HIT | `no match in 272 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/templates_engine/validator.py` | | NO_HIT | `no match in 406 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/utils/__init__.py` | 1 | NO_HEADER | `(no module docstring)` | edit | |
| `workmain/utils/date_format.py` | | NO_HIT | `no match in 16 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/utils/date_utils.py` | | NO_HIT | `no match in 100 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/utils/duration_parser.py` | | NO_HIT | `no match in 62 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/utils/editor.py` | | NO_HIT | `no match in 50 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/utils/encryption.py` | | NO_HIT | `no match in 199 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/utils/ics_parser.py` | 37 | INVENTORY | `- Exception found, not cancelled → emit exception's DTSTART/DTEND with` | edit | |
| `workmain/utils/ics_parser.py` | 39 | INVENTORY | `- Exception found, cancelled → skip the occurrence entirely` | edit | |
| `workmain/utils/ics_parser.py` | 40 | INVENTORY | `- No exception → emit normal occurrence` | edit | |
| `workmain/utils/ics_parser.py` | 183 | FLAG | `# UNTIL=...Z values are UTC — convert to local naive so rrulestr(ignoretz=True) works` | leave as is | Inline comment describing the behaviour at this line; §3.1 governs module headers, not comments, and this states no process rule. |
| `workmain/utils/meeting_templates.py` | | NO_HIT | `no match in 118 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/utils/self_invoke.py` | | NO_HIT | `no match in 133 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/utils/tag_utils.py` | | NO_HIT | `no match in 413 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/utils/time_parser.py` | | NO_HIT | `no match in 125 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/web/__init__.py` | 1 | NO_HEADER | `(no module docstring)` | edit | |
| `workmain/workflows/__init__.py` | | NO_HIT | `no match in 13 lines` | leave as is | No candidate text — the census reports no match in this file. |
| `workmain/workflows/eod_workflow.py` | 370 | TRIGGER | `Never blocks EOD — always returns COMPLETED.` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/workflows/eod_workflow.py` | 411 | TRIGGER | `Never blocks EOD — always returns COMPLETED.` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/workflows/eod_workflow.py` | 651 | TRIGGER | `Incremental pairing scope, not full all-pairs: candidates are drawn from` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
| `workmain/workflows/eod_workflow.py` | 661 | TRIGGER | `Never blocks EOD — always returns COMPLETED (matching` | leave as is | Function or class docstring under §3.5, describing behaviour; the matched opener is not a process rule. DR8.2 flags these for recall only. |
