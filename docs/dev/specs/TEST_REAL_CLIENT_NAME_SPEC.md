# Real client name in the test suite — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261112
**Branch:** `hotfix/issue-271-real-client-name-in-tests` (from `main`)
**Target release:** v1.58.1
**Originating item:** Issue #271
**Design study:** `../design/DESIGN_TEST_REAL_CLIENT_NAME.md`

This spec does not quote the real client name or the real Slack workspace name. Every check reads them from where they live: the client name from `WORKMAIN_DEFAULT_CLIENT` in `.env`, and the workspace name from `workspace_name` in `~/.workmain/integrations/slack/config.json`.

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261112 | Ray | The branch is `hotfix/*`. The change touches only `tests/`, and changing a literal changes the code, so it cannot use the `chore/*` exception in `docs/standards/2-git.md` §2.2. | — |
| 20261112 | Ray | The real Slack workspace literal in `tests/test_slack.py` joins this issue (design study Q1). | Step 2, AC4.1 |
| 20261112 | Ray | The stale production-data comments in 18 other test files stay out of scope (design study Q2). | #273 |
| 20261112 | Ray | Widening `CLAUDE.md` § Client Reference goes to its own `chore/*` issue (design study Q3). | #274 |
| 20261112 | Ray | The real workspace name asserted at `tests/test_slack_channel_config.py:186` goes to #214 (design study Q4). | #214's context and criteria, edited 20261112 |
| 20261112 | Caliper | Spec defect, non-blocking. AC1.1's `grep -rci` reads the working tree, and its result depends on which `grep` runs it. Under GNU `grep`, the stale, gitignored `tests/__pycache__/test_slack.cpython-312.pyc` still matches after a correct change. Under ugrep, binary files are skipped, so the §5 preamble's "every file under `tests/`" does not hold. | Accepted. AC1.1 is now `git grep -ci … -- tests/` printing nothing, so it checks tracked files whichever `grep` is installed, and the §5 preamble says "every tracked file". |
| 20261112 | Caliper | Spec defect, non-blocking. AC2.1's raw check `grep -niE 'production\|live'` matches a literal pipe under `-E`, so it returns nothing on the unchanged file. | Accepted. The check is now `grep -ni -e production -e live`, which contains no pipe and so is the same text in the raw file and in the rendered table. |
| 20261112 | Caliper | Spec defect, non-blocking. AC4.1's check is case-sensitive, but DR1 says "in any case". | Accepted. AC4.1 is now `git grep -ci`, and its criterion says "in any case". |
| 20261112 | Caliper | Spec defect, non-blocking. DR1 covers all test text, but `tests/test_slack_channel_config.py:186` stays out of scope (#214), so DR1 is false when the work is delivered. DR1 also says "a real client", but only `WORKMAIN_DEFAULT_CLIENT` is searched. | Accepted. DR1 is narrowed to the files §1 puts in scope, and to the two values the checks read. |
| 20261112 | Caliper | Spec defect, non-blocking. The §2 row cites `tests/test_client_repository.py:40–51`, but the two tests run `:39–57`. The design study's F3 has the same range. | Accepted. Both now cite `:39–57`. |
| 20261112 | Caliper | Pass at dd35338, full: 19 items checked, 0 blocking, 5 non-blocking. | n/a |
| 20261112 | Caliper | Pass at 21e5ba7, changes since dd35338: 12 items checked, 0 blocking, 0 non-blocking. | n/a |
| 20261112 | Anvil | The §2 precedent row says #257 set `#test-client-channel`. The value was added by `b4d2013`, and #257 never touched it. | Accepted. The row cites `b4d2013`. The design study's F5 is corrected to match. Step 2 is unchanged. |
| 20261112 | Anvil | §1 Out of scope cites `docs/standards/1-workflow.md` §1.5 for the archive being "never edited". §1.5 does not say that. | Accepted. The entry now states its actual reason: #271 covers only `tests/`. The design study's §2 is corrected to match. |
| 20261112 | Caliper | Pass at b258cdd, changes since 21e5ba7: 13 items checked, 0 blocking, 0 non-blocking. | n/a |
| 20261112 | Ray | `docs/archive/` keeps its occurrences of the real client and workspace names. No issue is opened for them, and #274 is not widened to cover them. | — |

---

## 1. Scope

**In scope:**

- `tests/test_client_repository.py`: the comment above `_NAME_A` and `_NAME_B`.
- `tests/test_slack.py`: the channel literal and the workspace literal in `TestSlackReportsIntegration::test_04_upsert_updates_existing_row` and `TestDraftLabel::test_18_draft_label_not_in_reports_ts`.

**Out of scope:**

- **Comments in 18 other test files that describe guarding against production data:** #273.
- **Widening `CLAUDE.md` § Client Reference:** #274.
- **`tests/test_slack_channel_config.py`.** Its real workspace name is asserted against the live Slack config file, so removing it means changing what the test reads, not only a literal: #214.
- **`docs/archive/`.** It names the client in 8 files and the workspace in 2. #271 covers only `tests/`.
- **Whether `_NAME_A` and `_NAME_B` keep their values.** Nothing about them is wrong; only the comment is.

## 2. Verified current state

Verified at `b8551c4`, 20261112. The design study's §3 holds the full census. The rows below are the claims the steps act on.

| Claim | Evidence |
| --- | --- |
| The client name appears in `tests/` on exactly four lines, and in no non-Python file. | `grep -rni "$WORKMAIN_DEFAULT_CLIENT" tests/` → `tests/test_client_repository.py:23`, `tests/test_slack.py:127`, `:137`, `:372` |
| `tests/test_client_repository.py:23` reads `# Unique names avoid collisions with production clients (<client>, etc.)` and sits above `_NAME_A = "_TestClient_G8_A"` and `_NAME_B = "_TestClient_G8_B"` (`:24–25`). | `tests/test_client_repository.py:23–25` |
| What the names still have to avoid: the reserved name `internal`, and each other. `test_create_reserved_name` and `test_create_duplicate_name` depend on these. No client is seeded in the test database, and every test is rolled back. | `tests/test_client_repository.py:39–57`; `workmain/database/migrations/versions/0001_baseline.sql` has no `INSERT` or `COPY` into `clients`; `docs/standards/6-testing.md` §6.1 |
| In `test_04_upsert_updates_existing_row`, `:127` writes `existing.slack_channel = "#int-<client>-csirt"` and `:128` writes `existing.slack_workspace_name = "<workspace>"`. `:137` and `:138` assert the same two values come back. | `tests/test_slack.py:108–143` |
| In `test_18_draft_label_not_in_reports_ts`, `:372` and `:373` pass the same two literals to `Report(...)`. No assertion reads them. | `tests/test_slack.py:362–388` |
| The workspace literal at `:128`, `:138` and `:373` equals `workspace_name` in the live Slack config. | `grep -c "$(jq -r .workspace_name ~/.workmain/integrations/slack/config.json)" tests/test_slack.py` → 3 |
| No application code reads the form of a channel or workspace value, so any string works as test data. | `grep -rn 'csirt\|"#int-' workmain/` → only the help-text example at `workmain/cli/commands/slack.py:304`; `Report.slack_channel` and `Report.slack_workspace_name` are `Text` (`workmain/database/models.py:386–387`) |
| Precedent for the replacement channel value. | `tests/test_slack_channel_config.py:63`, `:71`: `#test-client-channel`, a neutral channel value in that file since `b4d2013` (`git log -S'#test-client-channel'`) |

No signature, required input or invariant changes, so there is no call-sites row.

## 3. Design rules

- **DR1 — No line of the files §1 puts in scope names the real client or the real Slack workspace, in any case.** That means code, comments and docstrings alike. The real client is the value of `WORKMAIN_DEFAULT_CLIENT` in `.env`, and the real workspace is `workspace_name` in `~/.workmain/integrations/slack/config.json`.
- **DR2 — A test that wrote a value and asserted it still writes and asserts the same value.** It may be a different string, but the value written and the value asserted stay the same.
- **DR3 — A comment states what the code it describes needs today.** It does not describe a hazard that `docs/standards/6-testing.md` §6.1 rules out.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | The client-name comment is replaced | `tests/test_client_repository.py` |
| 2 | The Slack test literals are replaced | `tests/test_slack.py` |
| 3 | Results artifact | `docs/dev/results/TEST_REAL_CLIENT_NAME_RESULTS.md` |

### Step 1 — `tests/test_client_repository.py`

Replace the comment at `:23`. The new comment states that `_NAME_A` and `_NAME_B` are the clients these tests seed, and that they differ from each other and from the reserved name `internal`. It names no client and does not mention production or live data (DR1, DR3). `_NAME_A` and `_NAME_B` are unchanged. The wording is the implementer's.

### Step 2 — `tests/test_slack.py`

- `:127`, `:137` and `:372`: `"#int-<client>-csirt"` becomes `"#test-client-channel"`.
- `:128`, `:138` and `:373`: the workspace literal becomes `"test-workspace"`.

Every occurrence in the file is replaced, not only the cited lines (DR1). In `test_04_upsert_updates_existing_row`, the asserts at `:137–138` compare against the same new values that `:127–128` write (DR2).

### Step 3 — Results artifact

The last implementation step, following `docs/dev/results/_TEMPLATE_RESULTS.md`.

### Authorization points

None.

## 5. Acceptance criteria

The issue's first AC uses `--include=*.py`. AC1.1 searches every tracked file under `tests/`, so a fixture or data file is counted too. AC4.1 comes from Ray's Q1 ruling, and the issue body needs it added at close-out.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No tracked file under `tests/` names the real client, in any case | With `.env` loaded, `git grep -ci "$WORKMAIN_DEFAULT_CLIENT" -- tests/` printing nothing |
| AC1.2 | `test_04_upsert_updates_existing_row` asserts the same channel and workspace values it writes | `git diff main -- tests/test_slack.py` shows each new literal on both the write lines and the assert lines of that test, and `pytest tests/test_slack.py::TestSlackReportsIntegration::test_04_upsert_updates_existing_row` passes |
| AC2.1 | No comment in `tests/test_client_repository.py` describes collisions with production or live clients, and the comment above `_NAME_A` and `_NAME_B` states what the names avoid | `grep -ni -e production -e live tests/test_client_repository.py` returning no comment line, and a stated reading by Ray of `tests/test_client_repository.py`'s comment above `_NAME_A`, read for whether it states what the names must differ from |
| AC3.1 | The full suite passes | A bare `pytest` reporting 0 failed |
| AC4.1 | `tests/test_slack.py` does not name the real Slack workspace, in any case | `git grep -ci "$(jq -r .workspace_name ~/.workmain/integrations/slack/config.json)" -- tests/test_slack.py` printing nothing |

## 6. Test plan

- **Baseline before this work:** 1635 passed, 0 failed, 0 skipped (`CHANGELOG.md`, v1.58.0).
- **Expected after:** 1635 passed, 0 failed, 0 skipped. No test is added or removed.
- No new test. Step 2 changes data in two existing tests, and AC1.2 checks that one of them still asserts what it writes.

## 7. Risks and rollback

- **Risk:** a replaced literal on a write line does not match its assert, and `test_04_upsert_updates_existing_row` fails. AC1.2 and the suite run catch this.
- **Overlap:** #214 later replaces `test_04_upsert_updates_existing_row`. Because this spec only changes its data, #214's work is not affected.
- **Rollback:** each step is one commit touching one test file. `git revert` that commit.
