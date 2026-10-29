# Standards Split — Implementation Results

**Status:** Active
**Author:** Spanner (Role 1)
**Date:** 20261029
**Spec:** `../specs/STANDARDS_SPLIT_SPEC.md`
**Released as:** n/a — `chore/*`

---

## 1. Summary

Complete. `docs/DEVELOPMENT_STANDARDS.md` is now `docs/standards/`: a README that holds the header and index, and one file for each of §1–§7, with the text unchanged. Every live citation names the new file, apart from the two lines the spec keeps on purpose. The issue validator reads §1.3 from `1-workflow.md`, and each role's session-open run reads its standards files.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | Split into `docs/standards/`, README written, validator and its test repointed (`25d5900`) | `docs/DEVELOPMENT_STANDARDS.md` (removed), `docs/standards/` (8 files), `automation/issue_validator.py`, `automation/issue_validator_test.py` | +0 |
| 2 | Citations outside `workmain/` and `tests/` repointed (`71a2245`) | the 14 files in the spec's Step 2 row | +0 |
| 3 | Comment and docstring citations in `workmain/` and `tests/` repointed (`bf9754a`) | the 11 files in the spec's Step 3 row | +0 |
| 4 | Role references read their standards files (`8560ab3`) | `.claude/skills/session-start/references/spanner.md`, `caliper.md`, `anvil.md` | +0 |
| 5 | This artifact | `docs/dev/results/STANDARDS_SPLIT_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `ls docs/standards` lists `1-workflow.md` … `7-file-placement.md` and `README.md` only. The loop prints a count of `1` for each file, and its first line is `## <N>. ` matching the file's prefix (`## 1. Development Workflow` … `## 7. File Placement`). `git ls-files docs/DEVELOPMENT_STANDARDS.md` prints nothing. |
| AC1.2 | Met | Ray, 20261029: reviewed docs/standards/README.md |
| AC2.1 | Met | The spec's `diff` command, with `<base>` = `3a585d5`, prints nothing. It was run at Step 1 and again on the final tree. |
| AC3.1 | Met | The `git grep` prints exactly two lines: `automation/check_release_integrity.py:44` ("only entered DEVELOPMENT_STANDARDS §2.2 at v1.26.0") and `docs/standards/README.md:11` ("It was a single file, `docs/DEVELOPMENT_STANDARDS.md`, …"). |
| AC3.2 | Met | The §6 check over 24 distinct citations on the final tree prints nothing. |
| AC3.3 | Met | Ray, 20261029: reviewed CLAUDE.md, .claude/skills/session-start/SKILL.md |
| AC4.1 | Met | `pytest automation/`: 58 passed, 0 failed, 0 skipped, `test_the_live_standards_file_yields_exactly_the_label_pair` among them `PASSED`. `grep -n 'DEVELOPMENT_STANDARDS\|"docs"' automation/issue_validator_test.py` prints nothing. |
| AC5.1 | Met | Ray, 20261029: reviewed .claude/skills/session-start/references/spanner.md, .claude/skills/session-start/references/caliper.md, .claude/skills/session-start/references/anvil.md |
| AC6.1 | Met | `pytest`: 1598 passed, 0 failed, 0 skipped, after Step 1 and again before Step 3's commit. |
| AC6.2 | Met | The DR6 script, run on Step 3's edits before the commit and again on the final tree, prints `11 files checked` and exits `0`. The spec's §6 quotes its observed failures under mutation. |

## 4. Deviations from spec

None.

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |

## 5. Verification

- **Test suite:** 1598 passed, 0 failed, 0 skipped (baseline: 1598 passed, 0 failed, 0 skipped). `pytest automation/`: 58 passed, 0 failed, 0 skipped (baseline: 58 passed, 0 failed, 0 skipped).
- **Live verification:** the Step 1 section files were compared byte for byte with the scratch dry run the spec's §2 describes, and they were identical. `issue_validator.parse_label_pair` is exercised on the live `1-workflow.md` by AC4.1's test.
- **Daemon restart:** n/a — `chore/*` changes no application behaviour (`docs/standards/2-git.md` §2.6).

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| Issue #244 body | The spec restates AC2 and AC3 (Decision Log, 20261029), so the issue body needs the matching edit at close-out (`docs/standards/1-workflow.md` §1.2). | Close-out edits it. |
