# Five Non-Command TestCase Files to Plain pytest — Implementation Results

**Status:** Active
**Author:** Anvil (Role 3)
**Date:** 20261012
**Spec:** `../specs/TESTCASE_CONVERSION_SPEC.md`
**Released as:** v1.45.2 (tag v1.45.2)

---

## 1. Summary

Complete. The five files hold no `unittest.TestCase` class. All 258 tests keep their node IDs, pass, and keep every assertion. The four sessions the tests opened themselves, and their hand cleanup, are gone. Every temporary directory in the five files, and the eight outside them that the spec named, comes from `tmp_path` or is removed by the test. A bare `pytest` run leaves nothing in the system temp directory (32 entries on the unchanged suite, 0 now). §6.2 carries rules 6 and 7.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | 6 classes converted; `test_self_invoke.py`'s two `TemporaryDirectory` blocks take `tmp_path` | `tests/test_self_invoke.py`, `tests/test_eod_pipeline.py` | +0 |
| 2 | 4 classes converted; the three ConfirmationGate classes build their gate in the test | `tests/test_action_executor.py` | +0 |
| 3 | 18 classes converted; `_make_store(tmp_path)` and `_make_daemon(store, dm_channel)` have no fallback; two `assertLogs` become `caplog` scoped to the scheduler logger | `tests/test_orchestration.py` | +0 |
| 4 | 10 classes converted; four classes take `db_session` and lose their sessions, `load_dotenv()`, `tearDown` and id lists; five temp directories come from `tmp_path` | `tests/test_eod_workflow.py` | +0 |
| 5 | `self.addCleanup(shutil.rmtree, tmp_dir)` after the leaking `mkdtemp()` | `tests/test_report_correction.py` | +0 |
| 6 | The seven `TemporaryDirectory` test functions take `tmp_path` | `tests/test_provider_foundation.py` | +0 |
| 7 | §6.2 rules 6 and 7, as the spec's Step 7 gives them; restated positively by Spanner after Ray's review (spec Decision Log) | `docs/DEVELOPMENT_STANDARDS.md` | n/a |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | the AC1.1 command prints nothing |
| AC2.1 | Met | `diff nodeids_before.txt nodeids_after.txt` prints nothing; 258 node IDs on each side |
| AC2.2 | Met | `pytest <five files>`: 258 passed, 0 failed, 0 skipped; `nodeids_before.txt` has 258 lines |
| AC3.1 | Met | `python3 assert_count.py a4071ea` ends `tests whose count fell or that are missing: 0`; output in §5 |
| AC4.1 | Met | the AC4.1 command prints nothing |
| AC4.2 | Met | the AC4.2 command prints nothing (6 lines on `a4071ea`) |
| AC5.1 | Met | the AC5.1 command prints `0` (32 before Step 1) |
| AC5.2 | Met | the first AC5.2 command prints nothing; the second prints exactly `tests/test_meetings_condense.py:187` and `tests/test_report_correction.py:687` (the spec's :686 moved one line when `import shutil` was added above it) |
| AC5.3 | Met | `git diff -w a4071ea -- tests/test_provider_foundation.py` shows 35 changed lines: 7 functions × 5 (signature before and after, the `with` line, the `settings_path` line before and after). No other line differs |
| AC6.1 | Met | Ray read `docs/DEVELOPMENT_STANDARDS.md` §6.2 rules 6 and 7. The text is the spec's Step 7 text, verbatim, as restated after Ray's review |
| AC7.1 | Met | bare `pytest`: 1274 passed, 0 failed, 0 skipped |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | `from pathlib import Path` removed from `tests/test_self_invoke.py` (committed in Step 4) and from `tests/test_eod_workflow.py` | The conversion removed their last use. The self_invoke removal was found after Step 1's commit | not asked; DR5 reads it as required by the conversion |
| 2 | `import pytest` added to `test_self_invoke.py` and `test_orchestration.py`; the spec's table lists this. `import logging` added to `test_orchestration.py`. `from workmain.database.models import Report` added at module level to `test_eod_workflow.py` | Conversion table rows for `import` and for `self._Report` | not asked; the spec's table |
| 3 | The two converted log assertions bind `messages = [...]` on one line and assert on it on the next, instead of inlining the list in the `assert` | One `assert` per original `assertTrue`, with the list comprehension the spec gives; the inline form read as one 130-column line | not asked |
| 4 | `TestConfirmationGateBlocks` repeats the local `from ... import ConfirmationGate` in each test, beside `gate = ConfirmationGate()` | Its `setUp` held both lines; the table's row names the `gate = ...` line only, and DR5 keeps imports where they were | not asked |
| 5 | `test_orchestration.py`'s `TestT5SessionPersistence` and `TestEodStateThroughStore` keep their `_store` helpers, now taking `tmp_path`; tests that read the file path bind `store_path = tmp_path / 'daemon' / 'conversation_state.json'` | The spec's table says a helper that used the directory takes the path as a parameter; it names no form for a test that reads `self._path` directly | not asked |

## 5. Verification

- **Test suite:** 1274 passed, 0 failed, 0 skipped (baseline: 1274 passed, 0 failed, 0 skipped) — form per `docs/DEVELOPMENT_STANDARDS.md` §6.
- **Leak count (AC5.1):** baseline 32 entries in an empty `TMPDIR` besides `pytest-of-*`; after Step 7, 0.
- **AC3.1 output:**

```text
tests/test_orchestration.py: 100 tests, 121 before, 121 after
tests/test_eod_workflow.py: 78 tests, 170 before, 170 after
tests/test_action_executor.py: 58 tests, 98 before, 98 after
tests/test_eod_pipeline.py: 12 tests, 27 before, 27 after
tests/test_self_invoke.py: 10 tests, 25 before, 25 after
tests whose count fell or that are missing: 0
```

- **Live verification:** none. No file under `workmain/` changed.
- **Daemon restart:** none by this work. Close-out owns it.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| `tests/test_meetings_condense.py:187`, `tests/test_report_correction.py:687` | Two `tempfile` sites that remain until their TestCase files convert | Out of scope in the spec; #199's command-group issues convert those files |
