# Real-Value Check in the Style Check — Implementation Results

**Status:** Active
**Author:** Spanner (Role 1)
**Date:** 20261113
**Spec:** `../specs/REAL_VALUE_CHECK_SPEC.md`
**Released as:** n/a

---

## 1. Summary

Complete. `automation/style_check.py` reads `DEV_REAL_VALUES` from `.env` in the main working tree and fails a branch where a changed line, or one of the branch's own commit messages, holds a listed value. It reports the file and line or the commit's short hash, with the value's position in the list, never the value. With no values listed it fails with a message saying the check could not run. A file the branch renamed and edited is not read, a known limitation the spec records and #277 carries.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `real_values`, `real_value_violations`, `check(changes, values=())`, and `main` reading the values per DR1 and failing per DR6; the `repo` fixture writes an ignored `.env` listing an invented value (`57ea5a1`) | `automation/style_check.py`, `automation/style_check_test.py` | +10 |
| 2 | `commit_violations`, run by `main`, its hits printed after the line violations and counted in the violation total and the exit code (`7e3f7e0`) | `automation/style_check.py`, `automation/style_check_test.py` | +2 |
| 3 | This artifact | `docs/dev/results/REAL_VALUE_CHECK_RESULTS.md` | — |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `automation/style_check_test.py::test_a_listed_value_on_a_changed_line_fails_without_printing_it` passed |
| AC1.2 | Met | `automation/style_check_test.py::test_a_value_is_matched_in_any_case_and_joined_by_underscore_or_hyphen` and `automation/style_check_test.py::test_a_value_inside_a_longer_word_is_not_matched` passed |
| AC1.3 | Met | `automation/style_check_test.py::test_a_listed_value_on_an_untouched_line_is_not_reported` passed |
| AC1.4 | Met | `automation/style_check_test.py::test_values_are_split_on_commas_with_whitespace_and_empty_entries_dropped` and `automation/style_check_test.py::test_a_missing_env_file_lists_no_values` passed |
| AC1.5 | Met | `automation/style_check_test.py::test_without_listed_values_the_check_fails_with_a_message` passed for `[no-env-file]`, `[no-key]` and `[empty-value]` |
| AC1.6 | Met | `automation/style_check_test.py::test_values_are_read_from_the_main_working_tree_in_a_linked_worktree` passed |
| AC1.7 | Met | `python3 automation/style_check.py` on this branch at `7e3f7e0`: `grep -c 'real-value check not run'` over its output gives 0 |
| AC2.1 | Met | `automation/style_check_test.py::test_a_listed_value_in_a_branch_commit_message_fails_without_printing_it` passed |
| AC2.2 | Met | `automation/style_check_test.py::test_a_value_in_a_commit_before_the_branch_is_not_reported` passed |
| AC3.1 | Met | `grep -rn DEV_REAL_VALUES workmain/ config/ templates/ .env.example` returned zero hits (exit 1) at `7e3f7e0` |

## 4. Deviations and decisions

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |

None.

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |
| 1 | 1 | The main working tree is found by a private `_main_worktree()` beside `_git` | Inlining the `git rev-parse` call in `main` | `main` stays a sequence of named steps, as it was |
| 2 | 1 | A changed file is read as bytes and decoded as UTF-8 with replacement, and only where `is_file()` holds | `read_text`, as the other checks do | DR3 reads files of any type; `read_text` raises on undecodable bytes, and a changed path can be a directory such as a submodule |
| 3 | 1 | The fixture's invented value is `Qzx`, a 3-character value like the real client name, held in the test module's `VALUE` | A longer invented value | A 3-character value exercises DR2's boundary the way the real short value does. It and `quillbrook-hollow` were checked against `DEV_REAL_VALUES` before they were written |
| 4 | 1 | `BASE` gains a `.gitignore` holding `.env`, so the fixture's `.env` is ignored as it is in this repository | Writing `.git/info/exclude` | A tracked `.gitignore` is how this repository ignores `.env` |
| 5 | 1 | AC1.5's test also asserts `0 violation(s)`, so the exit 1 can come only from DR6 | Asserting the exit code and message alone | Shows the branch had no other violation, as AC1.5 states |
| 6 | 2 | Value patterns are compiled by a private `_value_patterns`, shared by `real_value_violations` and `commit_violations` | Compiling in each | One statement of DR2's match |
| 7 | 2 | The commit log is read with `%h%x00%B%x1e` and split on the separators | One `git log` call per commit | One call. git does not allow NUL in a commit message, and a record separator in one would only split it into two parts that are each still searched |

## 5. Verification

- **Test suite:** `tests/`: 1635 passed, 0 failed, 0 skipped (baseline: 1635 passed, 0 failed, 0 skipped). `automation/`: 113 passed, 0 failed, 0 skipped (baseline: 101 passed, 0 failed, 0 skipped).
- **Checks:** `python3 automation/style_check.py` exit 0, 0 violations, with the live values read (AC1.7); `python3 automation/architecture_check.py` PASS.
- **Live verification:** the style check run on this branch against the live `.env` at `7e3f7e0` read its 7 values and checked the branch's changed lines and its commit messages.
- **Daemon restart:** n/a. `chore/*` changes no application code (`docs/standards/2-git.md` §2.6).

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #277 | `automation/style_check.py` does not read a file the branch renamed and edited | Ray ruled it out of scope (spec Decision Log, Caliper 5): the gap predates #275 and affects every style check |
| #276 | Values already published in `docs/archive/` and in commit history | Out of scope per issue #275; its search was amended to the letters-and-digits boundary |
| #245 | How a direct-path spec that adds new code is written and implemented | Caliper's standards gap, added to #245 as a comment |
