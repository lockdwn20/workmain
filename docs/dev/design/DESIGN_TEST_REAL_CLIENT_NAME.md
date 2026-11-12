# Real client name in the test suite — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261112
**Originating item:** Issue #271

---

## 1. Purpose

Issue #271 reports that two test files write the real client's name, which `CLAUDE.md` § Client Reference forbids. It also reports that one comment in `tests/test_client_repository.py` describes collisions with production clients, a hazard the test database removed: since #257 the suite runs on `workmain_test`, which is rebuilt empty at the start of every run. This study measures how far both problems actually reach, rather than taking the issue's list as the full set. It also asks Ray about two adjacent findings that change how much work the spec covers.

This document does not quote the client's name or the real Slack workspace name. It cites each by file and line.

## 2. Scope of the read

Read at `b8551c4` (`origin/main`), on `hotfix/issue-271-real-client-name-in-tests`, 20261112. The suite collects 1635 tests (`pytest --collect-only -q`).

- **Searched for the client name**, case-insensitive, with `.env` loaded: `tests/` (every file, not only `*.py`), and the whole repository excluding `.git/`, `.env` and `scripts/baseline/` (`CLAUDE.md` § Common Pitfalls restricts the harness until #188 ships).
- **Read in full:** `tests/test_client_repository.py:1–60`, `tests/test_slack.py:105–145` and `:355–395`, and the `db_session` fixture at `tests/conftest.py:167–180`.
- **Read for precedent:** the archived #257 spec, `docs/archive/specs/TEST_DATABASE_SPEC.md`, and `tests/test_slack_channel_config.py`.
- **Searched for comments that describe production or live data:** `tests/**/*.py`.
- **Not read:** `docs/archive/`, beyond confirming which files hit. It is never edited (`docs/standards/1-workflow.md` §1.5).

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | The client name appears in `tests/` at exactly the four lines the issue names, and nowhere else. It is in no non-Python file under `tests/`. The same four hits appear with and without a word-boundary match, so none is a substring false positive inside a longer word. | `grep -rni "$WORKMAIN_DEFAULT_CLIENT" tests/` and `grep -rniw …` each return `tests/test_client_repository.py:23` and `tests/test_slack.py:127`, `:137`, `:372`. | Medium |
| F2 | Outside `tests/`, the client name appears only in `docs/archive/` (8 files). It is not in `workmain/`, `config/`, `templates/`, `automation/`, `scripts/` (excluding `scripts/baseline/`) or `CHANGELOG.md`. | `grep -rlic "$WORKMAIN_DEFAULT_CLIENT" --exclude-dir=.git --exclude-dir=baseline --exclude=.env .` | Low — out of scope |
| F3 | `tests/test_client_repository.py:23` is the comment `# Unique names avoid collisions with production clients (<client>, etc.)`, which sits above `_NAME_A = "_TestClient_G8_A"` and `_NAME_B = "_TestClient_G8_B"`. No production client can collide with these names any more: `workmain_test` starts empty, no migration seeds a `clients` row, and `db_session` rolls back every test. What the names still have to avoid is the reserved name `internal`, which `test_create_reserved_name` exercises, and duplicating each other, which `test_create_duplicate_name` relies on. | `tests/test_client_repository.py:23–25`, `:40–51`; `grep -niE "insert into (public\.)?clients\|COPY (public\.)?clients" workmain/database/migrations/versions/0001_baseline.sql` → none; `tests/conftest.py:167–180`. | Medium |
| F4 | `tests/test_slack.py:127`, `:137` and `:372` use the channel literal `#int-<client>-csirt` as data for `Report.slack_channel`. `:127` writes it in `test_04_upsert_updates_existing_row`, and `:137` asserts that the same value comes back. `:372` writes it in `test_18_draft_label_not_in_reports_ts`, and nothing asserts on it. No application code parses the channel's form: the only other `#int-` string in `workmain/` is the help-text example `"#int-ACME"` at `workmain/cli/commands/slack.py:304`. | `tests/test_slack.py:108–143`, `:362–388`; `grep -rn 'csirt\|"#int-' workmain/ tests/ config/`. | Medium |
| F5 | The precedent for a replacement value is set. #257 replaced the same kind of literal in `tests/test_slack_channel_config.py` with `#test-client-channel`. | `tests/test_slack_channel_config.py:63`, `:71`; `docs/archive/specs/TEST_DATABASE_SPEC.md:126`, `:201`. | — |
| F6 | **Adjacent, and not in the issue.** `tests/test_slack.py:128`, `:138` and `:373`, the lines next to F4's, use a `slack_workspace_name` literal that is the real Slack workspace name: it matches the value in the live `~/.workmain/integrations/slack/config.json`. `CLAUDE.md` § Client Reference governs only the client name, so no rule forbids this. The same literal appears at `tests/test_slack_channel_config.py:186`, where `TestSlackSetWorkspace` asserts it in the output of a command that reads that live config file. #257 left that test out of scope because it does not touch the database (`docs/archive/specs/TEST_DATABASE_SPEC.md:64`). | `grep -c <literal> ~/.workmain/integrations/slack/config.json` → 1; `grep -rn <literal>` over the repository → `tests/test_slack.py` (3), `tests/test_slack_channel_config.py` (1), `docs/archive/` (2 files). | Low |
| F7 | **Adjacent, and not in the issue.** Since #257, comments that describe isolating tests from production data, such as sentinel dates or unique keys "to avoid collisions with production data", appear in 19 test files. `tests/test_client_repository.py` is one of them. The issue's second criterion reaches only that one file. No open issue covers the rest. | `grep -rniE 'production (data\|db\|database\|rows\|keys\|clients\|system_state\|active\|corrected)\|prod collisions\|real production' tests/ --include=*.py`, 20261112. Open issues searched: `production data`, `sentinel`, `collision`, `test_client_repository`, `test_slack`, `WORKMAIN_DEFAULT_CLIENT`, `workmain_test`. | Low |

Every finding above was checked against source. The 19-file count in F7 is a dated measurement of comment text. This study does not judge whether each sentinel in those files is still needed.

## 4. Options

The change the issue asks for has one valid form, so it gets no options. F5 sets the precedent, and under `docs/standards/2-git.md` §2.2 one root cause belongs on one hotfix. The spec will deliver:

- `tests/test_client_repository.py:23`: the comment is replaced with one stating what the names are for: the tests' own clients, kept distinct from each other and from the reserved name `internal`. The comment does not name a client and does not mention live data.
- `tests/test_slack.py:127`, `:137`, `:372`: the literal becomes `#test-client-channel`, following F5. `:127` and `:137` still write and assert the same value.

Q1 and Q2 decide whether the hotfix also takes in F6 and F7.

### Q1 — the real workspace name (F6)

- **Option A: leave it out of #271, and Spanner drafts a proposed issue.**
  - **Pros:**
    - The hotfix stays one root cause, the rule `CLAUDE.md` § Client Reference states.
    - The real decision lives in the proposed issue: whether that rule should also cover the workspace name, and what `TestSlackSetWorkspace` should read instead of the live config.
  - **Cons:**
    - The workspace literal next to each fixed channel literal stays real for now.
- **Option B: fold the three `tests/test_slack.py` lines into #271.**
  - **Pros:**
    - It is the same three tests, and the fix is one more literal each.
  - **Cons:**
    - It applies a rule nobody has written down: § Client Reference does not cover workspace names.
    - It leaves `tests/test_slack_channel_config.py:186` real, because that line depends on the live config file. One file would be fixed and one would not.

**Recommendation: A.** Option B carries out a rule before Ray has decided to have it, and still leaves one occurrence behind. Option A puts that decision in front of him, as an issue.

### Q2 — production-data comments in 18 other files (F7)

- **Option A: leave it out of #271, and Spanner drafts a proposed issue.**
  - **Pros:**
    - #271 stays the change the issue named.
    - Each of those comments sits beside a sentinel date or unique key, and whether that sentinel is still needed is a judgement per test. A hotfix should not make that judgement in passing.
  - **Cons:**
    - The stale comments stay until that issue is worked.
- **Option B: fold the comment rewording into #271.**
  - **Cons:**
    - 18 more files.
    - A second concern, comments that went stale when #257 landed, sits on a branch whose concern is the client name. `docs/standards/2-git.md` §2.2 escalates bundled unrelated concerns to `feature/*`.

**Recommendation: A.** Option B moves this off the hotfix path.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | The real Slack workspace name is used as test data at `tests/test_slack.py:128`, `:138` and `:373`, and asserted at `tests/test_slack_channel_config.py:186` (F6). `CLAUDE.md` § Client Reference does not cover it. Should #271 leave it out, with a proposed issue drafted (A), or fix the three `tests/test_slack.py` lines here (B)? | |
| Q2 | 18 test files besides `tests/test_client_repository.py` carry comments about isolating tests from production data, which `workmain_test` has made stale (F7). Should #271 leave them out, with a proposed issue drafted (A), or reword them here (B)? | |

## 6. Disposition

- Promoted to:
- Superseded by:
