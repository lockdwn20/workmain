# A process rule has one home — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20260904
**Branch:** `feature/issue-134-process-rule-home` (from `dev`)
**Target release:** v1.34.0
**Originating item:** Issue #134
**Design study:** `../design/DESIGN_PROCESS_RULE_HOME.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260904 | Spanner | Three successive attempts to define what a docstring may say — an audience test, the issue's literal wording, a decision-ownership test — were all attempts to draw a boundary §3.1 had already drawn. | Withdrawn. §3.1 states that a module header is a one-line summary and a conceptual description; commands, flags, invocations, triggers and inventories were never permitted there. The design study records the withdrawn options so they are not proposed again. |
| 20260904 | Ray | §3.5's title reads as licence to put function-level docstring content in a module header, and §5.6's docstring bullet can be read as reaching one too. Both misreadings were load-bearing. | Both sections are rescoped in this spec — §3.5 to function and class level, §5.6 to the Click command function. |
| 20260904 | Ray | Scope is the full union of non-conforming files, not the subset with a direct line to the failure. | Steps 3-6, one per set, so any set can be split to its own issue at a step boundary if Ray decides. |
| 20260904 | Ray | The §1.5 rule is stated by class, not as a list of file kinds or directories. | DR1. Covers every file that exists and every file that will exist; no register to maintain. |
| 20260904 | Ray | `templates/` is out of scope — JSON consumed by the template engine for AI provider calls, no module headers. | Recorded in §1 Out of scope. |
| 20260904 | Spanner | 243 tests are `unittest.TestCase` subclasses and structurally cannot take the `db_session` fixture; eighteen classes commit to the live database and clean up by hand. Eight state in their header that they use `db_session` and do not. | Out of scope. Opened as **#136**, blocked by this issue. Step 4 makes those eight headers describe what the files actually do; #136 fixes the structure. |
| 20260908 | Spanner | The spec's first draft stated a 996-passed baseline and an AC of "996 passed, 0 failed". No run had produced either; both came from `pytest --collect-only`, which reports what is *collected*, not what passes. | Corrected against a real run. Recorded because it is the failure this issue exists to close, committed inside the spec that closes it: a count written down without the command behind it. |
| 20260908 | Ray | The four pre-existing `tests/test_ai_clients.py` failures are known, are already covered by open issues (#130 root cause, #131 file and reporting), and are handled at close-out. No finding is to be raised against them. | §6 records them as the branch-point baseline and §7 records the ruling. AC5.1 passes on the count matching that baseline, not on a green suite. |
| 20260908 | Spanner | 18 tests across four files contain **zero assertions** and signal pass/fail by returning a boolean, which pytest discards. They pass unconditionally regardless of what the code does. | Out of scope — no test body is touched here (DR7). Opened as **#137**, blocked by this issue. Step 6 deletes the `main()` runners these were written for, which does not change their behaviour under pytest. |
| 20260904 | Spanner | High primary keys (`notes_id_seq` 83,431 against 2,281 rows) were suspected to be test leakage. | Not leakage. PostgreSQL sequences are non-transactional, so a correctly isolated `db_session` test burns an id permanently too. Recorded so it is not re-investigated. |

---

## 1. Scope

**In scope.** Five sections of `docs/DEVELOPMENT_STANDARDS.md` — §1.5, §3.1, §3.4, §3.5, §5.6. Four sets of files, measured by census at authoring time and re-measurable by the same script:

| Set | What | Count |
| --- | --- | --- |
| A | Module headers containing a terminal command, an environment variable assignment, a command-line flag, an invocation, or a trigger for when to run something | 26 |
| B | Module headers whose shape is an inventory — a bullet or numbered list, or a `Commands:` / `Covers:` / `Features:` / `Steps:` label — rather than a description | 47 (33 not already in A) |
| C | `__init__.py` files not conforming to §3.4 | 16 of 26 |
| D | Test modules carrying a `__main__` block, and the four in-module runner functions behind them | 12 of 60 |

Sets A and B are measured across `tests/`, `workmain/`, `automation/` and `scripts/` — 194 module headers. Deletion of `CONTRIBUTING.md`, an empty file at the repository root.

**Out of scope.**

- **The 243 `unittest.TestCase` tests** and the eighteen classes that commit to the live database — issue #136. This spec changes those files' *headers* (Step 4) and deletes their `__main__` blocks (Step 6); it does not touch a test body or an isolation mechanism.
- **`tests/test_ai_clients.py`'s file split, its `SKIP_API_TESTS` gate, and §6's invocation and skip-reporting rules** — issue #131. This spec removes three lines from that file's header and its `__main__` block. It does not alter the gate, split the file, or amend §6.
- **`templates/`** — JSON read by the template engine for AI provider calls. No module headers.
- **`scripts-deprecated/`** — excluded from collection.
- **`docs/archive/**`** — archived artifacts are never authoritative (§1.5) and are not edited.

## 2. Verified current state

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| §3.1 requires a PEP 257 module docstring, "description only", and prohibits version, date and version-history blocks. It names no other exclusion. | `docs/DEVELOPMENT_STANDARDS.md` §3.1 |
| §3.4 is one sentence: "Descriptive docstring, import classes *and* singleton getters, declare `__all__`. No `__version__` constant." It does not say what a package with no public API does. | §3.4 |
| §3.5 is titled "Type hints and docstrings" and its worked example is a function docstring with `Args:` and `Returns:`. Nothing in it names a module header. | §3.5 |
| §5.6's closing bullet is "Every command needs a docstring serving as `--help`, with a one-line summary and at least one `Examples:` block." It sits in a section titled Output. | §5.6, last bullet |
| §1.5's every bullet is scoped to `docs/dev/` artifacts — filenames, `Status:` fields, archive moves, citation form, Decision Logs, hard wrapping, version headers, templates. No bullet reaches code, config or a `README`. | §1.5 |
| §6 states pytest is the exclusive runner and `testpaths` resolves a bare `pytest` to the application suite. | §6, first two bullets |
| `tests/test_ai_clients.py:9-12` states that the tests make real API calls and consume tokens, gives `SKIP_API_TESTS=1` to skip them, and gives `Run with: python3 test_ai_clients.py`. | `tests/test_ai_clients.py:9-12` |
| `run_all_tests()` calls nine test functions. The module defines 33. | `tests/test_ai_clients.py:706-762`; `ast` census |
| `main()` in `tests/test_config_system.py` iterates a list naming one of the module's three test functions. | `tests/test_config_system.py`, `main()` |
| Seven of the twelve `__main__` blocks delegate to `pytest.main([__file__, "-v"])` or `unittest.main()`. | `tests/test_action_executor.py`, `test_eod_pipeline.py`, `test_eod_workflow.py`, `test_orchestration.py`, `test_report_history.py`, `test_self_invoke.py`, `test_db_connection.py` |
| Under `pytest`, 996 test functions are defined across `tests/` and 996 are collected. | `pytest --collect-only -q`; `ast` census |
| Fourteen `__init__.py` files are zero bytes, including `workmain/__init__.py`. Two more carry inventory-shaped docstrings. Ten of the 26 already conform. | `ast` census of `**/__init__.py` |
| `workmain/ai/providers/claude.py:5` and `gemini.py:5` state `Do not instantiate directly — use get_provider_manager()...`. No command, no flag, no trigger. | those files |
| `.github/ISSUE_TEMPLATE/issue.schema.json` and `issue.template.json` contain field definitions only, no prose. | those files |
| `CONTRIBUTING.md` exists at the repository root and is 0 bytes. Nothing references it. | `CONTRIBUTING.md`; `grep -rn CONTRIBUTING` |
| Eight test modules state in their header that they use the `db_session` fixture; no test in any of the eight takes it, and each opens a real session through `get_db()`. | `tests/test_task_lifecycle.py`, `test_notes_add.py`, `test_notes_edit.py`, `test_notes_log.py`, `test_meetings_condense.py`, `test_meetings_track.py`, `test_time_add.py`, `test_reports_corrections.py` |

## 3. Design rules

- **DR1 — The rule is stated by class, never as a list.** A process rule has exactly one home, `CLAUDE.md` or `docs/DEVELOPMENT_STANDARDS.md`. No other file in the repository may state or imply one. Do not enumerate file kinds, directories, or exempt paths anywhere in the rule's text.
- **DR2 — A module header describes; it never instructs.** One-line summary, then a conceptual description of what the module does and why. No terminal command, no environment variable assignment, no command-line flag, no invocation, no trigger for when to run something, no inventory of the code tools the module contains.
- **DR3 — Removed text is not relocated by default.** A command or flag that documented a program's interface is already carried by that program's `argparse` definition and its `--help`; nothing replaces it. A genuine ordering constraint is a property of the code and survives as prose. Where neither applies, the text is deleted.
- **DR4 — Set C conforms to §3.4 as amended, not to an example.** A package with a public API gets the docstring, the imports and `__all__`. A package marker with nothing to export gets a §3.1 header and no invented exports. Never add an export to make a file look conforming.
- **DR5 — Set D deletes; it does not repair.** Do not fix a drifted runner to cover the tests it misses. A maintained parallel runner is a manual register and is worse than none.
- **DR6 — A rewritten header states what the file actually does.** Where the existing header's claim is false — the eight files naming a `db_session` fixture they do not use — the replacement describes the mechanism in the file, not the one the header claimed. Do not fix the mechanism; that is #136.
- **DR7 — No test body, assertion, fixture or isolation mechanism is altered by this spec.** If a step appears to require one, stop: `CLAUDE.md` Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Standards edits, part 1 — the rule. §1.5's preamble widened from `docs/dev/` artifacts to all text in the repository, and the one-home rule added per DR1, stating the failure it exists for: a process rule written into a test module's docstring was read as project policy by two roles in two sessions, and four real failures reached `main` and the running daemon. | `docs/DEVELOPMENT_STANDARDS.md` |
| 2 | Standards edits, part 2 — the four sections the rule needs to be applicable. §3.1 gains the explicit exclusion (DR2) and a summary-plus-description example. §3.4 gains the two shapes a package takes and which gets imports and `__all__` (DR4). §3.5 is rescoped so it cannot be read as governing a module header — function and class level, `Args` / `Returns` / `Raises` / `Attributes`, with type hints. §5.6's closing bullet is scoped to the Click command function, whose docstring is the `--help` the user sees, and is the correct home for an `Examples:` block. | `docs/DEVELOPMENT_STANDARDS.md` |
| 3 | **Set A** — 26 module headers rewritten to DR2. Removes `SKIP_API_TESTS=1`, `Run with: python3 ...`, the `Usage:` blocks in `automation/` and `scripts/`, the eight migration triggers, the flags quoted in four CLI modules, and the retired version header in `tests/google_drive/gdrive_probe.py`. Ordering constraints survive as prose per DR3. | 26 files across `tests/`, `workmain/`, `automation/`, `scripts/` |
| 4 | **Set B** — the 33 remaining inventory-shaped headers rewritten to DR2. Includes the eight false `db_session` claims, which state the file's actual mechanism per DR6. `workmain/cli/commands/eod.py` and `reports.py` need their conceptual description written, since the inventory is currently doing that work. | 33 files |
| 5 | **Set C** — 16 `__init__.py` files conformed to §3.4 as amended. Fourteen are empty; two carry inventory docstrings. Run `pytest` at the end of this step alone, before Sets A, B and D are judged — this is the only step that changes the import graph. | 16 `__init__.py` files |
| 6 | **Set D** — 12 `__main__` blocks deleted, and the four in-module runners with them (`run_all_tests` in `tests/test_ai_clients.py` and `tests/test_ai_foundation.py`; `main` in `tests/test_config_system.py`, `tests/test_tag_system.py`, `tests/test_templates.py`). Delete the now-unused `sys` / `unittest` / `pytest` imports each leaves behind, where nothing else uses them. | 12 files under `tests/` |
| 7 | Delete `CONTRIBUTING.md`. Re-run the census script from Step 3 across all four sets and record its output, the search performed, and every hit adjudicated in the results artifact — issue #134's second acceptance criterion requires that record. | `CONTRIBUTING.md`, `docs/dev/results/PROCESS_RULE_HOME_RESULTS.md` |

### Authorization points

**This spec contains none.** No migration, no GitHub object deleted, no merge to `main`, no force-push, no change to a live service's run state. The `dev → main` PR, the version bump, the tag and the service restart belong to `/closeout` and are not steps here.

Note for the implementer: issue #136's last acceptance criterion deletes three leaked rows from the live `reports` table. That is #136's, not this spec's. Do not delete a database row in this branch.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No module header under `tests/`, `workmain/`, `automation/` or `scripts/` contains a terminal command, an environment variable assignment, a command-line flag, an invocation, or a trigger | The census script reports 0 hits in all four Set A classes; script and output recorded in the results artifact |
| AC2.1 | §1.5 states that a process rule has exactly one home, `CLAUDE.md` or `docs/DEVELOPMENT_STANDARDS.md`, and that no other file in the repository may state or imply one — stated by class, with no directory or file-kind list | Stated reading by Ray |
| AC2.2 | §1.5's preamble scopes the section to all text in the repository, not to `docs/dev/` artifacts | Stated reading by Ray |
| AC3.1 | The rule records the failure it exists for, so a later reader can tell it from style advice | Stated reading by Ray |
| AC5.1 | `pytest` reports 992 passed and 4 failed, and `pytest automation/` reports 51 passed — the same counts as the branch point, since this spec changes no behaviour. The four failures are `tests/test_ai_clients.py::{test_claude_generation, test_gemini_generation, test_provider_status, test_cost_tracking_integration}`, pre-existing and owned by #130 | Both run and compared against the counts recorded in §6, which were produced by a run on this branch at `83ff5f9` |
| AC6.1 | §3.1 states the one-line-summary-plus-conceptual-description shape and excludes commands, flags, invocations, triggers and inventories of code tools by name | Stated reading by Ray |
| AC7.1 | Every module header under the four trees opens with a one-line summary and continues as description | The census script reports 0 inventory-shaped headers |
| AC7.2 | The Set B rewrites say what each file does | Stated reading by Ray of the Step 4 diff |
| AC8.1 | §3.4 states which `__init__.py` gets imports and `__all__` and which is a package marker that gets a header only, so the rule is decidable without asking | Stated reading by Ray |
| AC9.1 | Every `__init__.py` conforms to §3.4 as amended | The census script reports 0 nonconforming; `pytest` passes, which is what fails if the new imports introduce a cycle |
| AC10.1 | §3.5 cannot be read as governing a module header — its title and opening sentence scope it to function-level and class-level docstrings | Stated reading by Ray |
| AC10.2 | §5.6's docstring bullet is scoped to the Click command function whose docstring is its `--help` | Stated reading by Ray |
| AC11.1 | No test module can be run as a script | `grep -rn "__main__" tests/` returns no matches |
| AC11.2 | No in-module test runner remains | `grep -rn "def run_all_tests\|def main" tests/` returns no matches |
| AC11.3 | No file exists whose name reserves a home for process text it does not hold | `CONTRIBUTING.md` is absent |

Issue #134's AC1 and AC2 are replaced by AC1.1 and AC2.1 above, and AC6 through AC11 are added; the issue is edited to match at close-out, per `CLAUDE.md` — a spec is designed on the merits and the issue's criteria are reconciled to it, never the reverse.

## 6. Test plan

- **Baseline before this work**, measured on `feature/issue-134-process-rule-home` at `83ff5f9` on 20260908: `pytest` → **992 passed, 4 failed, 26 warnings**; `pytest automation/` → **51 passed**.
- **The suite is not green at the branch point**, and this spec cannot make it green. The four failures are `tests/test_ai_clients.py::{test_claude_generation, test_gemini_generation, test_provider_status, test_cost_tracking_integration}` — the same four recorded in `docs/archive/results/VENDOR_SDK_PINNING_RESULTS.md` AC9.1, pre-existing, root cause **#130**, carried to **#131**. See §7 for what this does to close-out.
- **Expected after:** unchanged — 992 passed, 4 failed. This spec adds no test and removes none.
- **No new test file.** Every change is prose except Step 5's imports and Step 6's deletions, and neither adds behaviour to cover. The census script is verification tooling, not a test: it lives with the results artifact and is quoted there in full, not added to `tests/` or `automation/`.
- **Step 5 runs `pytest` on its own** before Steps 3, 4 and 6 are judged (DR-adjacent, see §7).

## 7. Risks and rollback

| Risk | Blast radius | Rollback |
| --- | --- | --- |
| **Step 5 introduces a circular import.** Adding imports and `__all__` to `workmain/__init__.py` and the top-level packages creates an import surface that does not exist today. This is the only step that can turn the suite red. | The whole application — a cycle at package import breaks every entry point, not one command. | Revert the step's commit. Step 5 is committed alone and runs `pytest` before anything else is judged, so the failure is attributable to one commit. |
| **A Set B rewrite loses information.** `workmain/cli/commands/eod.py`'s numbered step sequence and `reports.py`'s subcommand list are currently the only prose description of what those modules do. | Two files; a reader is left with less than they had. | The replacement describes the same behaviour conceptually. Ray reads the Step 4 diff (AC7.2) before it is accepted. |
| **A migration script's ordering constraint is deleted as a trigger.** `Run AFTER applying migration 017_ai_costs.sql` is a real precondition wearing an imperative. | One script, re-run out of order at some future date. | DR3 requires the constraint to survive as prose. Ray reads the Step 3 diff. |
| **Step 6 deletes an import another part of the file uses.** `sys`, `unittest` or `pytest` may be referenced outside the deleted block. | One test file fails to import; caught immediately. | `pytest` at the end of the step. |
| **`/closeout` P8 meets a red suite.** P8 requires `pytest` to pass. Four tests fail at the branch point for reasons this issue does not own. | None. Ruled on by Ray, 20260908: the four failures are known, issues are already open against them, and they are handled at close-out. P8 is satisfied by the run matching the §6 branch-point baseline — 992 passed, 4 failed, those four and no others. Do not raise them as findings, and do not treat a fifth failure as covered by this ruling. |
| **Scope creep into #136.** Sixteen files in Step 4 are `unittest.TestCase` modules whose headers are false because their structure is wrong. Fixing the structure is tempting and is not this spec's. | The branch grows a 243-test refactor with no spec behind it. | DR6 and DR7. The header describes the mechanism that is there. |
