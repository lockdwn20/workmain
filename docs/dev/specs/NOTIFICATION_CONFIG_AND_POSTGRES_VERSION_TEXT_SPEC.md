# Notification Config and PostgreSQL Version Text — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261113
**Branch:** `chore/issue-268-false-statements` (from `main`, merges to `main` and `dev`)
**Target release:** none — `chore/*` carries no version bump, no `CHANGELOG.md` entry, no tag, no Release
**Originating item:** Issue #268
**Design study:** `n/a` — direct path, no recon was run

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261110 | Ray | One `chore/*` issue covers both statements, since each is text that states something false (issue #268 body) | **Branch:** |
| 20261113 | Spanner | `tests/test_notifications_commands.py` takes `chore/*` under the `docs/standards/2-git.md` §2.2 `chore/*` exception for `tests/**`. The proof of behaviour-neutrality is DR2: the file's AST, with the module docstring removed, is equal before and after | DR2, AC1.2 |
| 20261113 | Spanner | The docstring keeps its true claim, that there is no `notification_config` table, and drops only the false parenthetical. Neither live nor the test database has the table: no file under `workmain/database/migrations/` names it, and Alembic builds the test database | Superseded by Ray's ruling of 20261113 below: Step 1 rewrites the whole module docstring |
| 20261113 | Spanner | `CLAUDE.md` names only the major version and adds no pointer to `SHOW server_version`. The issue names that command as the source of the exact version, but does not ask for `CLAUDE.md` to state it | Step 2 |
| 20261113 | Spanner | The census covers the whole tree except `docs/archive/` and `scripts/baseline/`. `docs/archive/` is a record that is never updated (`docs/standards/1-workflow.md` §1.5). `scripts/baseline/` is restricted until #188 ships (`CLAUDE.md` § Common Pitfalls). This issue's own spec and results artifact are excluded too, because they quote the false text. The census finds only the two sites the issue names | AC1.1, AC2.1 |
| 20261113 | Ray | Approved. #268 runs the direct path without Role 2 review: no Caliper pass on the spec and no post-implementation review (`docs/standards/1-workflow.md` §1.2) | **Status:** |
| 20261113 | Spanner | `/closeout` preflight P7 failed. `automation/style_check.py` checks the changed lines, and Step 1 changed a line inside the module docstring, which lacks the blank line after its summary (`tests/test_notifications_commands.py:1 — D205`). DR1 allowed no other line to change | Ray's ruling below |
| 20261113 | Ray | Step 1 brings the module docstring up to `docs/standards/3-code.md` §3.1 | DR1, Step 1, AC1.3. **Status:** back to `Draft` |
| 20261113 | Spanner | The rewritten docstring drops two more claims that were false, verified against the file: no test exercises `notifications test`, and no test mocks delivery. The process citation in `test_status_corrupt_inspection_file`'s docstring is outside the module docstring, and open issue #264 covers it | Step 1 |

---

## 1. Scope

**In scope:**

- `tests/test_notifications_commands.py`, the module docstring only.
- `CLAUDE.md` § Tech Stack, the PostgreSQL version on its first bullet.

**Out of scope:**

- `workmain/database/repositories/notification_repository.py:31` says "the former notification_config table". That is true: the table existed and live no longer has it.
- `docs/archive/` and `CHANGELOG.md`. They are records of what was true when written, and neither holds a match for the census below.
- Any statement of which database version is live. The issue's own reason is that a minor version written as current goes stale (`docs/standards/1-workflow.md` §1.5). No other document gets one in its place.

## 3. Design rules

- **DR1 —** Step 1 replaces the module docstring of `tests/test_notifications_commands.py` and nothing else in that file. Step 2 replaces only the false text in `CLAUDE.md`. No other line in either file changes.
- **DR2 —** `tests/test_notifications_commands.py` is behaviour-neutral. That is proved by parsing the file at `main` and at the branch tip with `ast.parse`, removing the module docstring node from each tree, and comparing `ast.dump` of the two trees. They must be equal. The script is a throwaway kept in the session scratchpad, not in the repository. Its command and output are recorded in the results artifact.

Anything not covered here stops at the current step under `.claude/skills/session-start/references/spanner.md` § Working rules, "Implementing a direct-path spec".

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | The test module docstring is a `docs/standards/3-code.md` §3.1 module header and no longer says a migration dropped `notification_config` | `tests/test_notifications_commands.py` |
| 2 | `CLAUDE.md` names PostgreSQL's major version only | `CLAUDE.md` |
| 3 | Results artifact | `docs/dev/results/NOTIFICATION_CONFIG_AND_POSTGRES_VERSION_TEXT_RESULTS.md` |

### Step 1 — test docstring

The module docstring of `tests/test_notifications_commands.py` at `main`, lines 1–9, reads:

```text
"""
Tests for NotificationConfigRepository and the notifications CLI command group.
CLI-level tests (notifications test, notifications status) use CliRunner with
mocked delivery and filesystem — no actual notification dispatch occurs.

Uses db_session fixture for full transaction isolation.
Repository now reads/writes system_state KV rows (keys: notify_method,
notify_enabled) — no notification_config table (dropped in migration 010).
"""
```

Replace it with:

```text
"""
Tests for NotificationConfigRepository and the notifications command group.

The repository keeps the notification method and the enabled flag in
system_state rows, notify_method and notify_enabled; there is no
notification_config table. The repository tests run in db_session. The
notifications status tests point WORKMAIN_STATE_DIR at tmp_path, so the
command reads the inspection file each test writes, never the daemon's own.
"""
```

Commit `414c149` removed only the parenthetical. The commit that completes this step replaces the docstring that commit left.

Commit: `test(notifications): drop a false migration claim from a docstring`.

### Step 2 — CLAUDE.md PostgreSQL version

`CLAUDE.md` line 74, § Tech Stack, reads:

```text
- **Python 3.12** on WSL Ubuntu 24.04 · **PostgreSQL 16.11** (workmain / workmain_user)
```

Replace it with:

```text
- **Python 3.12** on WSL Ubuntu 24.04 · **PostgreSQL 16** (workmain / workmain_user)
```

Commit: `docs(claude): name PostgreSQL's major version only`.

### Step 3 — results artifact

Written from `docs/dev/results/_TEMPLATE_RESULTS.md`. It records each criterion's evidence, DR2's script and output, and the suite counts.

### Authorization points

None.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No live text in the repository says a migration dropped or removed `notification_config` | `git grep -n -i -E 'notification_config.*(drop\|remov)\|(drop\|remov).*notification_config' -- . ':!docs/archive' ':!scripts/baseline' ':!docs/dev/*/NOTIFICATION_CONFIG_AND_POSTGRES_VERSION_TEXT_*'` prints nothing. This covers the issue's check over `tests`. `git grep -n -i 'notification_config' -- tests` prints only the module docstring's line, so no wording the pattern misses is left |
| AC1.2 | The edit to `tests/test_notifications_commands.py` changes no behaviour | The DR2 comparison reports the two trees equal, and `pytest` reports the counts in §6 |
| AC1.3 | The module docstring of `tests/test_notifications_commands.py` is a `docs/standards/3-code.md` §3.1 module header: a one-line summary, a blank line, then a paragraph on what the tests cover, and every claim in it is true of the file | `ruff check --output-format concise tests/test_notifications_commands.py` reports nothing on lines 1–9, `python3 automation/style_check.py` exits 0, and Ray reads the docstring against §3.1 and the file's tests |
| AC2.1 | No live text in the repository states a PostgreSQL minor version, and `CLAUDE.md` § Tech Stack names the major version | `git grep -n -i -E 'postgres(ql)? ?[0-9]+\.[0-9]' -- . ':!docs/archive' ':!scripts/baseline' ':!docs/dev/*/NOTIFICATION_CONFIG_AND_POSTGRES_VERSION_TEXT_*'` prints nothing, and `grep -n 'PostgreSQL 16' CLAUDE.md` prints the § Tech Stack line |

## 6. Test plan

- **Baseline before this work:** 1635 passed, 0 failed, 0 skipped (`CHANGELOG.md` [1.58.2]).
- **Expected after:** 1635 passed, 0 failed, 0 skipped. No test is added, removed or changed. Only a module docstring changes.
- No test file is added.

## 7. Risks and rollback

- **Risk:** an edit outside the docstring changes a test. DR2 catches it before Step 1's commit.
- **Rollback:** each step is one commit, and `git revert <sha>` undoes it.
