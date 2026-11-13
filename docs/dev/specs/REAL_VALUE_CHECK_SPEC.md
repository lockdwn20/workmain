# Real-Value Check in the Style Check — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261112
**Branch:** `chore/issue-275-real-value-check` (from `main`, merges to `main` and `dev`)
**Target release:** none — `chore/*` carries no version bump, no `CHANGELOG.md` entry, no tag, no Release
**Originating item:** Issue #275
**Design study:** `../design/DESIGN_REAL_VALUE_CHECK.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261112 | Ray | With no value to check against, the style check passes and prints a notice (design study Q1) | DR6 |
| 20261112 | Ray | `DEV_REAL_VALUES` is one comma-separated line, as `.env` holds it; no value contains a comma (design study Q2) | DR1 |
| 20261112 | Ray | A value is matched case-insensitively and bounded only by letters and digits (design study Q3) | DR2 |
| 20261112 | Ray | `SKIPPED` applies to the real-value check; once #276's one-time removal has run, a value in a skipped path means the check missed it upstream (design study Q4) | DR3 |
| 20261112 | Ray | Branch names are not checked; the slug comes from the issue title, which the rule governs (design study Q5) | §1 Out of scope |
| 20261112 | Spanner | `.env` is read from the main working tree, not from `ROOT`, because Caliper's I6 runs the check in a detached worktree, which has no `.env` (design study F4). Under DR6 a `ROOT` read would pass there with a notice on every review | DR1 |
| 20261112 | Spanner | `.env` is parsed with `dotenv.dotenv_values`. The standard library has no `.env` parser, so `docs/standards/3-code.md` §3.8 names none; `python-dotenv` is already a dependency (`requirements.txt`) and is how the application reads the same file (design study F8) | DR1 |
| 20261112 | Spanner | The report names a hit by the value's position in `DEV_REAL_VALUES`, which tells Ray which entry it is without printing it | DR5 |
| 20261112 | Caliper | 5, Design gap, blocking: a renamed-and-edited file is never read. `changed_lines` diffs with `--diff-filter=AM` and lists new files with `--diff-filter=A` (`automation/style_check.py` `changed_lines`); git's default rename detection reports such a file as `R`, which both filters drop, so a value added to it never reaches `check`. The same holds for an uncommitted `git mv`. Options: `R` in the filter (only the edited lines are read), `--no-renames` (the moved file counts as wholly new, for the style checks too), or out of scope and carried to an issue | Awaiting Ray |
| 20261112 | Caliper | 7, Spec defect, non-blocking: AC2.1 passes on a check that reads only the newest commit's subject, which does not meet DR4 | Accepted: AC2.1's test puts the value in the body of a commit that is not the newest, with a clean newest commit |
| 20261112 | Caliper | 7, Spec defect, non-blocking: AC1.2 covers a value joined by `_` or `-`, but its test name names only `_` | Accepted: the test is `test_a_value_is_matched_in_any_case_and_joined_by_underscore_or_hyphen`, and AC1.2 states it asserts both |
| 20261112 | Caliper | 3, Spec defect, non-blocking: DR5's position is ambiguous where DR1 drops an empty entry | Accepted: DR5 counts the non-empty entries left to right |
| 20261112 | Caliper | 3, Spec defect, non-blocking: Step 2 gives no form for the commit count in the summary line, nor for the case where DR6 found no values | Accepted: Step 2 states the summary line's form; the commit count is printed whether or not there are values |
| 20261112 | Caliper | 3, Spec defect, non-blocking: DR3 does not say how lines are numbered; `str.splitlines()` splits on characters git does not, so a hit can get a line number `check`'s filter drops | Accepted: DR3 numbers lines by `\n` |
| 20261112 | Caliper | 1, Spec defect, non-blocking: AC1.7's check requires exit 0, which depends on the branch's content, not on whether the values were read | Accepted: AC1.7's check is the absence of the notice only |
| 20261112 | Caliper | 4, Standards gap, non-blocking: no standard says how a direct-path spec that adds new code at contract level, which cannot quote replacement text, is implemented | Proposed for Ray: joins #245, which asks whether a direct-path spec should state what each passage must say instead of quoting it |
| 20261112 | Caliper | Pass at f678abd, full: 29 items checked, 1 blocking, 7 non-blocking | n/a |

---

## 1. Scope

**In scope:** `automation/style_check.py` reads the values listed in `DEV_REAL_VALUES` and fails a branch where a changed line, or one of the branch's own commit messages, holds one. `automation/style_check_test.py` covers it.

**Out of scope:**

- Issue and pull request text, and branch names: the rule alone covers them (issue #275; design study Q5).
- Values already published in `docs/archive/` and in commit history: #276.
- `tests/test_slack_channel_config.py:186`, which holds the real workspace name: #214 (design study F7).
- Commits `/closeout` makes after preflight P7 (design study F10).
- Any change to `CLAUDE.md` § Client Reference or `docs/standards/`. The issue asks for the check only.

## 2. Verified current state

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| `changed_lines(base)` returns changed line numbers by path against `git merge-base HEAD <base>`, a new or untracked file mapping to `None`, with `SKIPPED` paths dropped. Its filters (`--diff-filter=AM`, `--diff-filter=A`) drop a file git reports as renamed (`R`), edited or not | `automation/style_check.py` `changed_lines`, `SKIPPED` |
| `check(changes)` keeps a violation only where its span touches a changed line; `main` prints `<path>:<line> — <message>` per violation, then `PASS` or `FAIL`, and returns 1 on any | `automation/style_check.py` `check`, `main` |
| `ROOT` is `Path(__file__).resolve().parent.parent`; in a linked worktree that is the worktree | `automation/style_check.py` `ROOT` |
| Nothing in the module reads a commit message or `.env` | `automation/style_check.py`, read end to end |
| `.env` is ignored, so a linked worktree has none | `.gitignore:37` |
| Callers of `check`, `changed_lines` and `main`, found by `grep -rn 'sc\.check\|sc\.main\|sc\.changed_lines\|style_check\.check\|from style_check\|import style_check' --include=*.py .`: `automation/style_check_test.py:106`, `:177`, `:191`, `:199`, `:206`, `:247`, `:249`. No other Python file imports the module. The command line runs it at `.claude/skills/closeout/SKILL.md:35` (P7), `.claude/skills/session-start/references/anvil.md:46` (check 5) and `.claude/skills/session-start/references/caliper.md:52` (I6, with `--base`, in a detached worktree) | the search shown; `grep -rn style_check` over the repository, `docs/archive/` excluded |
| `dotenv.dotenv_values(path)` returns an empty mapping for a missing file and does not change `os.environ` | `python-dotenv==1.0.0` (`requirements.txt:4`), run 20261112 |
| `pytest automation/`: 101 passed, 0 failed, 0 skipped | run 20261112 on this branch |

## 3. Design rules

- **DR1 — Where the values come from.** `DEV_REAL_VALUES` is read with `dotenv.dotenv_values` from `.env` at the root of the main working tree, which is the parent of `git rev-parse --path-format=absolute --git-common-dir` run in `ROOT`. It is never read from `ROOT / ".env"` or from `os.environ`. The value is split on `,`; whitespace around each entry is dropped, and so is an empty entry.
- **DR2 — How a value is matched.** Case-insensitively, as a literal (`re.escape`), where the character before it and the character after it are each absent or not an ASCII letter or digit. `_`, `-`, `#`, `.` and whitespace all bound a value.
- **DR3 — Which changed text is read.** Every path `changed_lines` returns, whatever its extension, read as UTF-8 with undecodable bytes replaced. `SKIPPED` applies, unchanged. Lines are numbered by splitting on `\n` alone, as git numbers them. A hit is reported only where its line is a changed line, by `check`'s existing filter.
- **DR4 — Which commit messages are read.** The full message, subject and body, of every commit in `git log <merge-base>..HEAD`, where `<merge-base>` is `git merge-base HEAD <base>` for the `<base>` `main` already resolves. Merge commits are included. A commit reachable from the base is never read.
- **DR5 — The report never holds a value.** A changed-line hit is reported in the existing form, `<path>:<line> — holds value <n> of DEV_REAL_VALUES`, and a commit hit as `commit <short hash> — holds value <n> of DEV_REAL_VALUES`, where `<n>` is the value's 1-based position among the non-empty entries of `DEV_REAL_VALUES`, counted left to right. No other text of a hit is printed.
- **DR6 — With no values the check passes with a notice.** Where `.env` is missing, the key is missing, or the list is empty, neither real-value check runs, `main` prints `real-value check not run: DEV_REAL_VALUES is not set in .env in the main working tree`, and the exit code is decided by the other checks alone.
- **DR7 — Tests hold invented values only.** No test reads the repository's `.env`, per `CLAUDE.md` § Client Reference. A test that runs `main` writes its own `.env` with invented values into its temporary repository, ignored there as `.env` is here.
- **DR8 — The key is not application configuration.** `DEV_REAL_VALUES` is named nowhere under `workmain/`, `config/` or `templates/`, nor in `.env.example`.

## 4. Steps

| Step | Deliverable | Files | ACs |
| --- | --- | --- | --- |
| 1 | The values and the changed-line check: DR1, DR2, DR3, DR5 for lines, DR6, with tests | `automation/style_check.py`, `automation/style_check_test.py` | AC1.1–AC1.6 |
| 2 | The commit-message check: DR4, DR5 for commits, with tests | `automation/style_check.py`, `automation/style_check_test.py` | AC2.1, AC2.2 |
| 3 | The results artifact | `docs/dev/results/REAL_VALUE_CHECK_RESULTS.md` | AC1.7, AC3.1 |

**Step 1.** `automation/style_check.py` gains:

- `real_values(env: Path) -> List[str]` — the values DR1 lists from the `.env` file at `env`; an empty list for a missing file, key or value.
- `real_value_violations(path: str, text: str, values: Sequence[str]) -> List[Violation]` — one `(path, line, line, message)` entry per line and listed value that DR2 matches, with DR5's message.
- `check(changes, values: Sequence[str] = ())` — also runs `real_value_violations` over every path in `changes` that exists, per DR3, when `values` is not empty. The default keeps every caller in §2 working unchanged.
- `main` reads the values per DR1, passes them to `check`, and prints DR6's notice when there are none, before the `PASS` or `FAIL` line.

The module docstring states that changed lines are checked for the values `DEV_REAL_VALUES` lists, where they are read from, and that python-dotenv is required.

**Step 2.** `automation/style_check.py` gains `commit_violations(base: str, values: Sequence[str]) -> List[Tuple[str, int]]`, one `(short hash, position)` per commit and listed value that DR2 matches in a DR4 message. `main` runs it when there are values, prints each per DR5 after the line violations, counts them in the summary line's violation total and in the exit code, and prints the summary line as `<branch> against <base>: <f> changed file(s), <c> commit(s), <v> violation(s)`, where `<c>` is the number of commits in DR4's range, printed whether or not there are values. The module docstring adds the branch's own commit messages to what is checked.

**Step 3.** The results artifact, per `docs/standards/1-workflow.md` §1.1.

Each step's new public function lives in `automation/style_check.py`, the module issue #275 names; `docs/standards/7-file-placement.md` §7 places dev tooling in `automation/`, which `docs/ARCHITECTURE.md` does not map.

### Authorization points

None.

## 5. Acceptance criteria

Each test named below is in `automation/style_check_test.py`.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A branch whose changed line holds a listed value fails the style check, and the output names the file and line without the value | `pytest automation/style_check_test.py` passes, including `test_a_listed_value_on_a_changed_line_fails_without_printing_it`, which runs `main` and asserts exit 1, `<path>:<line>` in the output, and the value absent from it in any case |
| AC1.2 | A listed value is found in any letter case and when joined into a word by `_` or `-`, and not when it is part of a longer run of letters and digits | `test_a_value_is_matched_in_any_case_and_joined_by_underscore_or_hyphen`, which asserts a hit for each of `_` and `-`, and `test_a_value_inside_a_longer_word_is_not_matched` pass |
| AC1.3 | A listed value on a line the branch did not change is not reported, so the values already published (#276) do not fail every branch | `test_a_listed_value_on_an_untouched_line_is_not_reported` passes |
| AC1.4 | `DEV_REAL_VALUES` is split on commas, with surrounding whitespace and empty entries dropped, and a missing file yields no values | `test_values_are_split_on_commas_with_whitespace_and_empty_entries_dropped` and `test_a_missing_env_file_lists_no_values` pass |
| AC1.5 | With no values the check passes with DR6's notice, its exit code set by the other checks | `test_without_listed_values_the_check_passes_with_a_notice` passes, running `main` on a branch with no other violation and asserting exit 0 and the notice in the output |
| AC1.6 | Run in a linked worktree, as Caliper's I6 runs it, the check reads `.env` from the main working tree | `test_values_are_read_from_the_main_working_tree_in_a_linked_worktree` passes, running `main` with `--base` from a linked worktree whose own folder has no `.env`, and asserting a hit and no notice |
| AC1.7 | On this repository the check reads the live `DEV_REAL_VALUES` | `python3 automation/style_check.py` run on this branch prints no `real-value check not run` line |
| AC2.1 | A branch whose own commit message holds a listed value fails the style check, and the output names the commit without the value | `test_a_listed_value_in_a_branch_commit_message_fails_without_printing_it` passes, with the value in the body of a branch commit that is not the newest and a newest commit that holds none, asserting exit 1, that commit's short hash in the output, and the value absent from it in any case |
| AC2.2 | A commit made before the branch left its base is not read, so the commit messages already published (#276) do not fail every branch | `test_a_value_in_a_commit_before_the_branch_is_not_reported` passes, with the value in the base commit's message only |
| AC3.1 | `DEV_REAL_VALUES` is read only by development tooling and is not part of the application's configuration | `grep -rn DEV_REAL_VALUES workmain/ config/ templates/ .env.example` returns zero hits |

The command line is the only entry path to the check (§2 callers). AC1.1, AC1.5, AC1.6 and AC2.1 run it through `main`, with and without `--base`.

## 6. Test plan

- **Baseline before this work:** `tests/`: 1635 passed, 0 failed, 0 skipped (`CHANGELOG.md` 1.58.1). `automation/`: 101 passed, 0 failed, 0 skipped (§2).
- **Expected after:** `tests/` unchanged. `automation/`: 111 passed, 0 failed, 0 skipped, with ruff installed: step 1 adds eight tests and step 2 two, each named in §5.
- The tests build their repository with the existing `repo` fixture, adding an ignored `.env` with invented values where DR7 needs one.

## 7. Risks and rollback

- **A 3-character value refuses new text that contains it as a word.** That is the rule working; the text is reworded. A value inside a longer word is not refused (DR2).
- **A lost or emptied key passes every branch with only a notice** (DR6, Ray's ruling). The notice is the only signal, and P7 reads the exit code.
- **The check's own tests would trip it** if a test value were real, which DR7 rules out, and the invented values are checked against `DEV_REAL_VALUES` before they are written.
- **Rollback:** revert the step commits. Nothing outside `automation/` changes, and no caller's command line changes.
