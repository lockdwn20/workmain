# Test Database Built by Alembic — Implementation Results

**Status:** Active
**Author:** Anvil (Role 3)
**Date:** 20261112
**Spec:** `../specs/TEST_DATABASE_SPEC.md`
**Released as:** v1.58.0

---

## 1. Summary

Complete. A bare `pytest` now runs on `workmain_test`. Before the first test it drops everything the application's user owns there and builds the schema with `alembic upgrade head` in a child process. A run whose `DB_NAME` names another database stops before any test. The Slack channel tests seed their own active client and no longer touch the real one. `docs/standards/6-testing.md` §6.1 and §6.2 now describe the test database and no longer carry the live-data rules, and every live citation of a renumbered §6.2 rule is repointed. Every criterion is met.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | The Slack channel tests seed their own active client (`24ea2a2`) | `tests/test_slack_channel_config.py` | +0 (5 changed) |
| 2 | The guard and the build (`06c9098`) | `tests/conftest.py`, `tests/test_database_isolation.py` | +5 |
| 3 | The standards, and every citation of a renumbered rule (`1721a22`) | `docs/standards/6-testing.md`, `.claude/skills/session-start/references/anvil.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`; #256's body | +0 |
| 4 | Evidence, and this artifact | `docs/dev/results/TEST_DATABASE_RESULTS.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | §5 AC1.1: after a full `pytest`, the two schema dumps compared by `diff` printed nothing |
| AC2.1 | Met | §5 AC2.1: the live counts before and after a bare `pytest` compared by `diff` printed nothing |
| AC3.1 | Met | `tests/test_database_isolation.py::TestTestDatabaseGuard::test_a_run_naming_another_database_stops_before_any_test` PASSED |
| AC3.2 | Met | `tests/test_database_isolation.py::TestTestDatabaseGuard::test_the_suite_is_connected_to_the_test_database` PASSED |
| AC3.3 | Met | `tests/test_database_isolation.py::TestTestDatabaseGuard::test_a_url_naming_another_database_is_refused` PASSED |
| AC4.1 | Met | `tests/test_database_isolation.py::TestTestDatabaseBuild::test_the_build_empties_the_schema_and_upgrades_to_head` PASSED |
| AC4.2 | Met | `tests/test_database_isolation.py::TestTestDatabaseBuild::test_a_run_builds_the_database_before_its_first_test` PASSED |
| AC5.1 | Met | Ray, 20261112: reviewed `docs/standards/6-testing.md` and found no issues. The search half is done: `grep -nE 'sentinel\|Committed rows are visible\|row lock' docs/standards/6-testing.md` printed nothing (exit 1) |
| AC5.2 | Met | §5 AC5.2: every hit is listed there with the rule its number now names, or as historical |
| AC6.1 | Met | `pytest`: 1635 passed, 0 failed, 0 skipped |
| AC6.2 | Met | With `.env` loaded, `grep -ci "$WORKMAIN_DEFAULT_CLIENT" tests/test_slack_channel_config.py` printed `0` |

## 4. Deviations and decisions

| # | Departure or ambiguity | Step stopped at | Resolution | Resolved by |
| --- | --- | --- | --- | --- |

None.

**Decisions below the contract.**

| # | Step | Decision | Considered instead | Why |
| --- | --- | --- | --- | --- |
| 1 | 1 | `test_slack_status_fallback_when_no_client_channel` reads the seeded client's channel through `db_session` (`expire_all()`, then asserts `None`) instead of setting it | Setting `slack_channel = None` and committing | The fixture seeds the client with no channel, so setting it would change nothing. The read states the precondition the test relies on, through `db_session` as step 1 requires |
| 2 | 1 | `test_slack_status_shows_client_channel` sets the channel by assigning the fixture client's attribute and committing `db_session` | `ClientRepository(db_session).update(...)` | Both use the same session. Assigning the attribute is the most direct way to set the channel on that client |
| 3 | 1 | The hash-normalising literal becomes `int-test-channel` | Any other literal without `#` | The old literal held the real client's name. The new one keeps the no-`#` shape the test pins |
| 4 | 1 | The module docstring becomes a one-line summary followed by a description, and drops its process citation. The fixture and the four changed tests get `Session` / `Client` type hints, and `Client` is imported at module level | Leaving the docstring's first sentence as it was | `automation/style_check.py` flags changed lines: D205 on the docstring step 1 edits, and ANN on the changed signatures. The old summary line also cited a phase, which `docs/standards/3-code.md` §3.1 forbids |
| 5 | 2 | DR3's refusal text is `Tests run only on workmain_test; the connection names '<name>'.` | Reusing DR2's text | DR3 states no text. DR2's text names `DB_NAME`, which is not what DR3 found wrong |
| 6 | 2 | DR5's messages are built by a private helper, `_stop_build(url, detail)`. A missing database is recognised by psycopg2's `database "workmain_test" does not exist`. The owner it names comes from the URL's username | Hard-coding `workmain_user` | The connecting user is the one that must own the database, and under `.env` that user is `workmain_user`. Checked with `DB_PORT=1`: the run stops with return code 4 and the connection error |
| 7 | 2 | A private `_REPO_ROOT` constant in `tests/conftest.py` and in the test file. The AC3.1 test reads `_REPO_ROOT / ".env"` | `dotenv_values(".env")` relative to the working directory | It is the same file when run from the root, and it stays correct from any other directory |
| 8 | 2 | `_isolated_database`'s changed signature gets type hints (`pytest.MonkeyPatch`, `None`, `Iterator[None]`) | Leaving it unannotated | `automation/style_check.py` flags the changed line |
| 9 | 2 | The build test checks the probe with `to_regclass('public.rebuild_probe')`. The AC4.2 test's return-code assertion carries the child's output as its message | Querying `information_schema` | One scalar, which is NULL when the table is absent. On failure, the output shows why the child failed |
| 10 | 2 | The tests import `build_test_database` and `require_test_database` from `tests.conftest` | `from conftest import ...` | `tests/` is a package, so pytest loads the file as `tests.conftest`. Importing it by that name reaches the same module, not a second copy |

## 5. Verification

- **Test suite:** 1635 passed, 0 failed, 0 skipped (baseline: 1630 passed, 0 failed, 0 skipped). Step 1's commit left the suite on live at 1630 passed, 0 failed, 0 skipped.
- **Defect shown before the fix:** n/a. No step fixes a defect in application code.

**AC2.1.** Run 20261112 06:17:03–06:17:48 PST (Thursday), after T1's 05:30 run. The service `workmain-notify` was active and was not stopped. `ac21.sql` is the spec's §5 query, verbatim.

```bash
psql -AtX -d workmain -f ac21.sql > before.txt   # 26 lines
pytest                                           # DB_NAME unset in the environment
psql -AtX -d workmain -f ac21.sql > after.txt
diff before.txt after.txt                        # printed nothing, exit 0
```

`pytest` printed `1635 passed, 9 warnings in 43.50s`.

**AC1.1.** Run right after that `pytest`.

```bash
pg_dump --schema-only --no-owner --no-privileges -d workmain_test | grep -vE '^\\(restrict|unrestrict) ' > test.sql   # 1300 lines
pg_dump --schema-only --no-owner --no-privileges -d workmain      | grep -vE '^\\(restrict|unrestrict) ' > live.sql   # 1300 lines
diff test.sql live.sql                                                                                                 # printed nothing, exit 0
```

`pg_dump` 16.15. Both runs exited 0.

**AC5.2.** These are the hits after step 3. A hit in one of this issue's own records is historical and stays as written (`docs/standards/1-workflow.md` §1.5).

| Search | Hit | Rule its number now names |
| --- | --- | --- |
| `grep -nE '\brules? [0-9]+' docs/standards/6-testing.md` | `:62` "(rule 1)" | Rule 1, take `db_session` |
| same | `:62` "(rule 6)" | Rule 6, a test's directory is `tmp_path` |
| `grep -rnE '6\.2[^\|]{0,40}\brules? [0-9]+' .claude docs/standards docs/dev CLAUDE.md automation .github` | `.claude/skills/session-start/references/anvil.md:43` rule 9 | Rule 9, a defect fix's test is seen to fail first |
| same | `docs/dev/results/_TEMPLATE_RESULTS.md:63` rule 9 | Rule 9, a defect fix's test is seen to fail first |
| same | `docs/dev/specs/TEST_DATABASE_SPEC.md:21, :171, :172` | Historical: this spec |
| same | `docs/dev/design/DESIGN_TEST_DATABASE.md:63` (F17) | Historical: this issue's design study |
| same | this file | Historical: this results artifact |
| The second pattern over every open issue's body | #256 rule 8 | Rule 8, a test pins behaviour meant to stay |
| same | #257 rule 2 | Historical: #257's body, which states the problem as filed |

Before #256's body was edited, it was saved to a file and checked to be non-empty and to contain `§6.2 rule 9` exactly once. The edit was made with `gh issue edit 256 --body-file`, run from the repository root, and the body read back with `§6.2 rule 8` as its only citation of a §6.2 rule.

- **Live verification:** AC1.1 and AC2.1 above.
- **Daemon restart:** close-out's.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| Proposed issue for Ray | The comment at `tests/test_client_repository.py:23` names the real client, and describes collisions with live clients that can no longer happen. Fix: reword the comment. AC: `grep -ci "$WORKMAIN_DEFAULT_CLIENT" tests/test_client_repository.py` prints 0 | Out of scope (spec §1, §7). Ray decides whether it becomes an issue |
| #257's body | Restate its first and fourth criteria, and replace the line "#66's migration-integrity half is delivered here" with a pointer to #266 and #66 | Close-out's (spec §5) |
