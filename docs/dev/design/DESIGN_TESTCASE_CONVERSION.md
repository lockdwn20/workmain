# Converting Five Non-Command TestCase Files to Plain pytest — Design Study

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261012
**Originating item:** Issue #200

---

## 1. Purpose

Issue #200 converts five `unittest.TestCase` test files to plain pytest classes so their tests can request fixtures. This study measures the five files on the commit the work starts from, checks the issue's claims against them, settles how each `unittest` construct converts, and names the one scope question the census raised.

## 2. Scope of the read

Read on `origin/main` `a4071ea` (v1.45.1, #136 shipped), 20261012:

- The five files in full for structure: `tests/test_orchestration.py`, `tests/test_eod_workflow.py`, `tests/test_action_executor.py`, `tests/test_eod_pipeline.py`, `tests/test_self_invoke.py`.
- `tests/conftest.py`, `docs/DEVELOPMENT_STANDARDS.md` §6–§6.3.
- `docs/archive/design/DESIGN_TEST_DATABASE_ISOLATION.md` (#136's study, which split this issue out), and issues #199 and #198.
- `workmain/` for logger `propagate` and logging config, which decide whether `caplog` sees what `assertLogs` saw.

Not read: the twelve CLI-driving TestCase files #199 carries, and application code beyond the logging check.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | The issue's census holds on `a4071ea`. Collected: 100, 78, 58, 12, 10. Lines: 1,566, 1,522, 645, 142, 103 (3,978). `self.assert*` calls: 115, 115, 33, 27, 25 (315). | `pytest --collect-only -q <file>`; `wc -l`; `grep -oE 'self\.assert[A-Za-z]*'` | Low |
| F2 | 38 TestCase classes across the five files (18, 10, 4, 4, 2). Eleven have `setUp`/`tearDown`; none has `setUpClass`, `setUpModule`, `subTest`, `skipTest`, `addCleanup`, `self.fail` or method-level `@patch` decorators. | `grep -c '(unittest.TestCase)'` per file; AST walk for `setUp`/`tearDown` | Low |
| F3 | Four `setUp`s open their own session and `tearDown` deletes the seeded rows by hand: `test_eod_workflow.py` `TestReportReviewStepCollapse` (:1009), `TestReportReviewStepEditBranch` (:1142), `TestReportStepOutcome` (:1315), `TestCondenseStepOutcome` (:1426). Each also calls `load_dotenv()`, which `_isolated_database` in `tests/conftest.py` already does. Under #136 these sessions come from the same patched factory `db_session` uses, so changing to `db_session` keeps their transaction behaviour, and §6.1's rollback makes the hand deletion dead code. | `tests/test_eod_workflow.py:1009-1023, 1142-1156, 1315-1330, 1426-1448`; `tests/conftest.py` `db_session`, `_isolated_database` | Medium |
| F4 | Five `setUp`s create a `tempfile.TemporaryDirectory()` that `tmp_path` replaces: `test_orchestration.py` `TestT5SessionPersistence` (:745), `TestWriteJsonAtomic` (:1218), `TestEodStateThroughStore` (:1375); `test_eod_workflow.py` `TestReportStepOutcome` and `TestCondenseStepOutcome` (also in F3). `test_self_invoke.py` :23 and :30 open one inside the test. | `grep -n tempfile` | Low |
| F5 | Four `setUp`s only construct `ConfirmationGate()`: `test_orchestration.py` `TestConfirmationGateBlocks` (:257) and `test_action_executor.py` `TestConfirmationGateIsConfirmation`, `TestConfirmationGateIsRejection`, `TestConfirmationGateFormatPrompt` (:52, :82, :106). | Read | Low |
| F6 | **`_make_store()` in `test_orchestration.py` falls back to `tempfile.mkdtemp()` because TestCase tests could not pass `tmp_path`, and the directory is never removed.** `_make_daemon()` calls `_make_store()` when it is given no store, and 13 of its call sites give none; `TestConversationStorePending._store` (:1249) and `TestProviderFailureReplies` (:1500) call `_make_store()` directly. Each call leaves a directory in `/tmp`. Once every caller can take `tmp_path`, the fallback is dead code. | `tests/test_orchestration.py:29-33, 45, 1249, 1500`; `grep -n '_make_daemon(' \| grep -vc 'store='` → 13 | Medium |
| F7 | **The same leak exists in two plain pytest classes outside the issue's TestCase scope:** `test_eod_workflow.py` `TestControlResumeRetries` (:908) and `TestHandleReplyMidFlightGuard` (:955) build a store on `tempfile.mkdtemp()`. These tests can already take `tmp_path`. | `tests/test_eod_workflow.py:908, 955` | Low |
| F8 | **The issue says the `get_db` patches in `test_orchestration.py` and `test_eod_workflow.py` "are not database sessions". That holds for `test_orchestration.py`, which returns `MagicMock`s. In `test_eod_workflow.py`, 21 of the 23 patches are in plain pytest classes (:300–:884) and return the test's real `db_session`** (`mock_get_db.return_value.get_session.return_value = db_session`). None is in a TestCase class and none breaks a rule in §6.1, so the issue's conclusion still holds: they stay. | `grep -n 'get_db' tests/test_eod_workflow.py` | Low |
| F9 | **Two files drive CLI commands through `CliRunner`, though the issue calls all five "files that test no CLI command."** `test_eod_pipeline.py` `TestEodDryRun` (4 tests) asserts on `eod --dry-run` output. `test_eod_workflow.py` `TestReportStepOutcome._reports_save_run` and `TestCondenseStepOutcome._condense_run` run `reports save` and `meetings condense` only to produce the result a workflow step consumes. #136's study recorded this as "drive no command, or drive one only incidentally" (its F14), and Ray answered its Q2 with all five files in #200. #199's command census will find `TestEodDryRun` as an `eod` command test. It may rewrite those four tests later; converting them now costs little. | `tests/test_eod_pipeline.py:82-121`; `tests/test_eod_workflow.py:1342-1358, 1450-1473`; `DESIGN_TEST_DATABASE_ISOLATION.md` F14, Q2 | Low |
| F10 | **No helper method in the five files holds a `self.assert*` call, and every TestCase test holds at least one assertion.** A per-test count of assertions, which the issue's third criterion asks for, can therefore be taken from each test function's own body. | AST walk over the five files | Low |
| F11 | The issue's third criterion counts `assert` statements and `pytest.raises` blocks after the conversion. It does not count the replacement for `self.assertLogs`. Its two uses (`test_orchestration.py` :587, :613) become `caplog`. The check `assertLogs` makes on its own — that at least one record was logged — is covered by the `any(...)` assertion after it, which fails on an empty list. As the criterion is worded, both tests show a count that fell from 2 to 1, which is a false report. | `tests/test_orchestration.py:580-620` | Medium |
| F12 | `caplog` sees the same records `assertLogs` did: nothing in `workmain/` sets `propagate` or calls `dictConfig`/`fileConfig`. | `grep -rn 'propagate\|dictConfig\|fileConfig' workmain/` (only docstring hits) | Low |
| F13 | `self.assertAlmostEqual` is used three times (`test_eod_workflow.py` :219, :223, :227), with its default `places=7`, which means `round(a - b, 7) == 0`. `pytest.approx(0.0)` uses only its absolute tolerance of `1e-12`, which is stricter, so a literal conversion can turn a passing test red. | `tests/test_eod_workflow.py:219-227` | Low |
| F14 | All `assertRaises` uses (3) are context managers, so each maps one-to-one to `pytest.raises`. | `test_orchestration.py:246`; `test_self_invoke.py:37, 94` | Low |
| F15 | **Standards gap.** §6.2's template shows a plain class, but no rule says a test is never a `unittest.TestCase`. The 12 TestCase files #199 carries will remain after #200 ships, so nothing stops a new test from copying one of them. | `docs/DEVELOPMENT_STANDARDS.md` §6.2 | Medium |

## 4. Design

### The conversion form

Only one form is valid. A test that needs a fixture (`db_session`, `tmp_path`, `caplog`) takes it as an argument and passes it to any helper that needs it. An object that needs no fixture is built in the test body. Two things rule out the others:

- `setup_method` and an autouse class fixture that sets `self.*` both hide the fixture from the test's signature. §6.1 says a test that seeds or reads *takes* `db_session`. `setup_method` also cannot take a fixture at all, so it fails F3's four classes and F4's five.
- The repository already does this: `tests/test_action_executor.py` `TestActionExecutorTaskResolutionUncapped._seed_filler_tasks(self, db_session, ...)` (:396) and `tests/test_eod_workflow.py` `TestCandidatePathTag._second_note(self, db_session, ...)` (:748).

| `unittest` construct | Becomes |
| --- | --- |
| `class X(unittest.TestCase):` | `class X:`, with the class name and every test name unchanged |
| `setUp` that builds a session (F3) | the test takes `db_session`; helpers such as `_seed` take it as a parameter; `self._Report` becomes a module-level import |
| `tearDown` that deletes seeded rows (F3) | deleted (§6.1 rollback, §6.2 rule 4) |
| `setUp`/`tearDown` around a temp directory (F4) | the test takes `tmp_path`; helpers such as `_store` take the path |
| `setUp` that only constructs `ConfirmationGate()` (F5) | `gate = ConfirmationGate()` in the test body |
| `load_dotenv()` in `setUp` (F3) | deleted (already done by `_isolated_database`) |
| `self.assertEqual(a, b[, msg])`, `assertIn`, `assertTrue`, … | `assert a == b[, msg]`, `assert a in b`, `assert a`, … — with the message kept |
| `self.assertRaises(E)` (F14) | `pytest.raises(E)` |
| `self.assertLogs(logger, level=L) as ctx` (F11, F12) | the test takes `caplog` and calls `caplog.set_level(L, logger=logger)`; `ctx.output` becomes `caplog.messages` |
| `self.assertAlmostEqual(a, b)` (F13) | `assert a == pytest.approx(b, abs=5e-8)`, the tolerance `places=7` gives |
| `import unittest` | deleted once no use is left; `from unittest.mock import …` stays |

### Restating the issue's criteria

These follow from the findings. The spec states them, and the issue's text is updated at close-out:

- **Criterion 2 (every test still collected):** compare node IDs before and after, not counts per file. A count can match after a test was renamed or dropped. A node-ID match cannot, and the table's "names unchanged" row makes it achievable.
- **Criterion 3 (no assertion lost):** the counting script reads `origin/main` `a4071ea` for the before side and matches tests by node ID. It counts `self.assertLogs` before against `caplog.set_level` after (F11), and needs no helper attribution (F10).
- **Criterion 4 (no own session):** F3's four sites are the whole set, and the grep stands as written.

### Standard shipped with the fix (F15)

The conversion sets the rule, so it writes the rule into §6.2 in the same spec: tests are plain classes, and a test file never subclasses `unittest.TestCase`, because a TestCase test cannot take a fixture as an argument (§6.1). The rule states the principle and no list of files. The 12 files #199 carries break it until their command-group issues convert them, the same way #136 wrote §6.1 while 14 files still broke it. #198's pilot rewrites §6.2 later and builds on this rule, not against it.

### Branch

`hotfix/*`, as Ray confirmed 20261012. No application file changes.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | The five files create temporary directories that are never removed. Every call to `_make_store()` in `tests/test_orchestration.py` without a path argument calls `tempfile.mkdtemp()`, which happens at 15 call sites (13 through `_make_daemon()`). That fallback exists only because TestCase tests could not take `tmp_path`, so the conversion makes it removable. Two plain pytest classes in `tests/test_eod_workflow.py` (lines 908 and 955) also call `tempfile.mkdtemp()` directly, though those are not TestCase tests. Should #200 remove the fallback and have every caller pass `tmp_path`, including those two plain classes? Or should the leak go to its own issue? **Recommendation: fold it into #200.** The fallback is dead once the conversion lands, and §6 already treats `tmp_path` as the only temp directory. The two plain-class sites sit in a file this branch rewrites, and they share the defect and the fix. A separate issue would edit the same lines twice. | Answered 20261012 (Ray): fold it into #200. |

## 6. Disposition

- Promoted to: `../specs/TESTCASE_CONVERSION_SPEC.md`
- Superseded by:
