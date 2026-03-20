# WorkmAIn Testing Standards
TESTING_STANDARDS v1.0
20260320

## Overview

WorkmAIn uses **pytest** as its exclusive test runner. All tests live in
`tests/` and run against the production database with full transaction
isolation — nothing a test creates ever persists after the test ends.

---

## Running the Suite

```bash
# From the project root (with .venv active):
python -m pytest tests/

# Verbose output:
python -m pytest tests/ -v

# Single file:
python -m pytest tests/test_recurring_meetings.py

# Single test:
python -m pytest tests/test_recurring_meetings.py::TestRecurringMeetings::test_daily_workdays_only_default
```

Expected baseline: **142 passed, 0 failed, 0 errors** (as of v1.6.4).

---

## Database Isolation — The `db_session` Fixture

Every test that touches the database **must** accept `db_session` as a
parameter. This fixture is defined in `tests/conftest.py` and provides
complete transaction isolation:

```python
# conftest.py — how it works
@pytest.fixture
def db_session():
    session = get_db().get_session()
    session.commit = session.flush   # redirects commits → flushes
    try:
        yield session
    finally:
        session.rollback()           # undoes everything the test did
        session.close()
```

**What this means for test authors:**

| Action | Effect |
|--------|--------|
| `repo.create(...)` | Data is written and visible **within** the test session |
| `session.commit()` (inside a repo) | Redirected to `flush()` — data stays in the transaction |
| Test ends | `session.rollback()` removes every INSERT/UPDATE/DELETE |
| Production DB | **Unaffected** — always |

You do **not** need to delete anything you create in a test. The rollback
handles all cleanup automatically.

---

## Writing a New Test

### Template

```python
"""
WorkmAIn <Feature> Tests
test_<feature> v1.0
20YYMMDD

<One-line description>.

Uses db_session fixture from conftest.py for full transaction isolation.

Version History:
- v1.0: Initial implementation
"""

import pytest
from workmain.database.repositories.<repo> import <Repo>


class Test<Feature>:
    """<What this class tests>."""

    def test_<scenario>(self, db_session):
        repo = <Repo>(db_session)
        # arrange, act, assert
        # No cleanup needed — rollback handles it
```

### Rules

1. **Always use `db_session`** — never call `get_db()` or `get_session()`
   directly inside a test file.

2. **Sentinel dates for aggregation tests** — if a test checks exact totals
   (hours, counts), use a far-future sentinel date (e.g. `date(2099, 1, 1)`)
   so production data cannot skew the result.

3. **One assertion focus per test** — each `test_*` method should verify one
   behaviour. Prefer multiple small tests over one large test that creates
   many objects.

4. **No manual cleanup** — do not call `repo.delete()` or `session.rollback()`
   at the end of a test. The fixture handles it. The only exception is if you
   are explicitly testing a delete operation.

5. **File header required** — all test files follow the project versioning
   standard (module name, version, date, version history).

6. **Class grouping** — group related tests in a `class Test<Topic>`. Keeps
   the output readable and allows running a group with `-k TestTopic`.

---

## `scripts-deprecated/` — Legacy Validation Scripts

The following files in `scripts-deprecated/` are **not** part of the pytest
suite. They are standalone scripts from the early development phase (Claude
Desktop era) when the application was not yet operational and tests were run
manually.

| File | Original Purpose |
|------|-----------------|
| `test_time_tracking.py` | Manual time tracking validation script |
| `test_database.py` | Manual DB connection and schema check |
| `test_phase_4_feature_3_4.py` | Manual Phase 4 feature validation (note condensation) |
| `test_style_system.py` | Manual writing style system validation |
| `test_prompt_builder.py` | Manual AI prompt builder inspection |

These scripts can still be run directly (`python3 scripts-deprecated/<file>.py`)
for manual diagnostics, but they are **not** maintained as part of the test
suite and should not be imported or discovered by pytest.

**Do not add new files to `scripts-deprecated/`.** If you need a diagnostic
script, add it to `scripts/` instead. If you need new tests, add them to
`tests/` following the standards above.

---

## Test File Inventory

| File | Type | DB? | Notes |
|------|------|-----|-------|
| `test_recurring_meetings.py` | pytest classes | Yes (db_session) | |
| `test_ics_import.py` | pytest classes | Yes (db_session) | |
| `test_email.py` | pytest classes | Yes (db_session) | |
| `test_slack.py` | pytest classes | Yes (db_session) | |
| `test_gdrive.py` | pytest classes | Yes (db_session) | |
| `test_report_history.py` | unittest.TestCase | Yes (own session + tearDown) | Uses far-future dates (2099) |
| `test_time_tracking.py` | pytest classes | Yes (db_session) | Sentinel date: 2099-01-01 |
| `test_eod_pipeline.py` | unittest.TestCase | No (all mocked) | |
| `test_ai_clients.py` | pytest functions | No (live API) | Skips if no API key |
| `test_ai_foundation.py` | pytest functions | No | |
| `test_prompt_builder.py` | pytest functions | Yes (db_session) | Reads only |
| `test_config_system.py` | pytest functions | No | |
| `test_tag_system.py` | pytest functions | No | |
| `test_templates.py` | pytest functions | No | |
| `test_style_system.py` | pytest functions | No | |
| `test_db_connection.py` | pytest functions | Yes (connection only) | No writes |

---

## Adding a Test for a New Phase

When a new phase introduces commands that touch the database:

1. Create `tests/test_<feature>.py` using the template above.
2. Import `db_session` via the fixture parameter — never import directly.
3. Use sentinel dates if testing queries with totals or counts.
4. Run `python -m pytest tests/test_<feature>.py -v` to verify isolation
   before running the full suite.
5. Reference this file and `docs/DEVELOPMENT_STANDARDS_REVIEW.md` for any
   patterns or conventions questions.
