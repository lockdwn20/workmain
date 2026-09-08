# Where a process rule may live — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20260904
**Originating item:** Issue #134

---

## 1. Purpose

Issue #134 asks for a rule stating that a process rule has exactly one home, and for the removal of the instance that defeated three controls. Two earlier drafts of this study treated the question as an open one and spent their length constructing a boundary for what a docstring may say. That was wrong, and Ray identified why: `docs/DEVELOPMENT_STANDARDS.md` §3.1 already answers it. A module header is a one-line summary and a conceptual description of what the module does and why. A terminal command, an environment flag, an invocation, a trigger, and an inventory of code tools are none of those things and have never been permitted there.

So the boundary is not this study's to draw. Every hit the census found is already a §3.1 violation. The options that argued over which violations to keep are withdrawn. Scope was the only open question and Ray has settled it: the full union, implemented as separable steps. This study now records the decisions, the three sets, and the acceptance criteria the issue needs to cover them.

## 2. Scope of the read

Read: every module docstring in `tests/`, `workmain/`, `automation/`, `scripts/` — 194 modules, extracted with `ast.get_docstring` and matched against four violation classes and one shape class; `config/`, `.github/` and `deploy/` hold no Python modules with headers. `.github/ISSUE_TEMPLATE/issue.schema.json` and `issue.template.json` in full. `README.md` and `CONTRIBUTING.md` at the repository root. `docs/DEVELOPMENT_STANDARDS.md` §1.5, §3.1, §3.4, §3.5, §5.6, §6. `.claude/skills/closeout/SKILL.md` rows P8 and P9. Issues #131 and #135.

Not read, deliberately: `docs/archive/**` beyond locating the #79 / #126 evidence — archived artifacts are never authoritative (§1.5); `scripts-deprecated/`, excluded from collection; `templates/` (`fields`, `reports`, `style`), which holds report output templates read by the template engine, not module headers.

## 3. Findings

Two distinct sets, measured separately because they carry different risk and different cost.

**Set A — headers containing a command, flag, trigger or version header. 26 files.** `scripts/` 9, `tests/` 8, `workmain/` 6, `automation/` 3.

**Set B — headers whose shape is an inventory rather than a description: a bullet or numbered list, or a `Commands:` / `Covers:` / `Features:` / `Steps:` label. 47 files.** `workmain/` 24, `tests/` 18, `scripts/` 4, `automation/` 1.

**Set C — `__init__.py` files not conforming to §3.4. 16 of 26.** Fourteen are entirely empty; two carry inventory-shaped docstrings (`workmain/ai/__init__.py`, `workmain/ai/providers/__init__.py`). Set C is disjoint from A and B, which cover module headers with content.

**Set D — test modules carrying a `__main__` block. 12 of 60.** Under `pytest` the block is dead: the module is imported, so `__name__` is never `"__main__"`. It fires only when a file is executed directly, which §6 does not recognise as an invocation. Four of the twelve back it with an in-module runner. Set D overlaps A and B only incidentally.

Sets A and B overlap in 14 files. Their union is **59 of 194 module headers**; 12 are Set A only, 33 are Set B only. With Set C the total in scope is **75 files**, plus Set D's 12, which overlap the others in part.

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | The instance, and it is three lines. `:9` states that the tests make real API calls and consume tokens, `:10` gives the flag that skips them, `:12` gives a second invocation. All three are Set A. Under §3.1 none of the three belongs in a module header — including `:9`, whose subject is a cost incurred by running the file, not what the module does. | `tests/test_ai_clients.py:9-12` | Critical |
| F2 | Two test modules carry `Run with: python3 test_X.py`, each backed by a live `__main__` block, against §6's "pytest is the exclusive runner". The docstring line is a §3.1 violation; the `__main__` block is the second invocation §6 says does not exist. | `tests/test_ai_clients.py:12` + `:759`; `tests/test_ai_foundation.py:7` + `:403` | High |
| F3 | A retired version header (`gdrive_probe.py v1.0` / `20260306`), a stale process step naming a shipped phase, and a `Usage:` block — the only file in the census hitting all four Set A classes. | `tests/google_drive/gdrive_probe.py:2-11` | Medium |
| F4 | Eight one-shot migration scripts open with a trigger — `Run once as part of Phase 13 DB Schema Sprint Gate 1`, `Run before deploying Item 27 CLI changes`, `Run AFTER applying migration 017_ai_costs.sql` — plus the invocation line. Executing a DB migration is an authorization point under `CLAUDE.md` § Critical Rules, so these supply a trigger for the one decision class the project treats as irreversible. | `scripts/migrate_*.py` (8 files) | High |
| F5 | Three `automation/` tools carry multi-line `Usage:` blocks listing every invocation with flags. These are the project's own dev tooling, run by a session, and the blocks are Set A. `argparse` in each already defines the same interface. | `automation/issue_validator.py:5-7`, `check_release_integrity.py:20-22`, `closeout_acs.py:8` | Medium |
| F6 | Four CLI command modules and several test modules open with a command or coverage inventory rather than a description — `reports.py` lists nine subcommands with their flags, `eod.py` lists a numbered step sequence naming the commands each step shells to. Set B, and `reports.py` and `eod.py` are Set A as well through the flags they quote. | `workmain/cli/commands/reports.py`, `eod.py`, `gdocs.py`, `slack.py`; `tests/test_notes_list.py` and 17 others | Medium |
| F7 | `workmain/daemon/daemon.py` states `Run via systemd user service (workmain-notify.service).` and `Do not run as root — enforced by _check_not_root().` The first is a trigger. The second is a real constraint with its enforcement cited, and says the same thing as prose: the daemon refuses to start as root. | `workmain/daemon/daemon.py:7-8` | Low |
| F8 | Both provider modules state `Do not instantiate directly — use get_provider_manager().get_provider('claude')`. No command, no flag, no trigger — a conceptual statement of how the module is constructed, which is what §3.1 asks for. #130 exists because the constraint is real and unenforced. Compliant as written. | `workmain/ai/providers/claude.py:5`, `gemini.py:5` | — |
| F9 | Roughly fifteen test modules state `Uses db_session fixture from conftest.py for full transaction isolation` — prose, describing what the module does, and prescribed verbatim by §6.2's worked example. Compliant. | `tests/test_notes_service.py` and ~14 others; §6.2 | — |
| F10 | `CONTRIBUTING.md` exists at the repository root and is zero bytes. A file with that name is the conventional home for exactly this class of text, and an empty one is a standing invitation with no owner. | `CONTRIBUTING.md`, 0 lines | Medium |
| F11 | No standards section states where a *process rule* lives. §3.1 governs the shape of a module header and would have caught F1 through F6 had it been applied, but it does not say that a process rule has one home and that no docstring may carry one — which is the rule that closes the class rather than the file. §1.5 is scoped to `docs/dev/` artifacts throughout. | §1.5, §3.1 | High |
| F15 | `tests/test_ai_clients.py`'s `run_all_tests()` is a hand-written list of nine calls in a file defining **33** tests. Executing the file directly runs 9, prints `✓ ALL TESTS PASSED`, and silently omits all 24 offline payload-contract tests added by #79 and #126 — the entire body of work proving the provider payload is correct. It also wraps all nine in one `try`, so the first failure aborts the rest. `tests/test_config_system.py`'s `main()` has drifted the same way, iterating a list that names one of its three tests. | `tests/test_ai_clients.py:706-762`; `tests/test_config_system.py` `main()` | High |
| F16 | Seven of the twelve delegate to a real runner — `pytest.main([__file__, "-v"])` or `unittest.main()` — and cannot drift. They are still a second invocation: `unittest.main()` runs unittest's own runner, which bypasses `conftest.py`, fixtures, plugins and `testpaths`, so the file behaves differently under it than under `pytest`. | `tests/test_action_executor.py`, `test_eod_pipeline.py`, `test_eod_workflow.py`, `test_orchestration.py`, `test_report_history.py`, `test_self_invoke.py`, `test_db_connection.py` | Medium |
| F13 | Fourteen `__init__.py` files are zero bytes, including `workmain/__init__.py` and every top-level package under it. §3.4 asks for a descriptive docstring, imports and `__all__`. Four of the fourteen — `tests/`, `tests/fixtures/`, `tests/mocks/`, `workmain/database/migrations/` — are package markers with no public API to export. | `workmain/__init__.py`, `workmain/cli/__init__.py`, `workmain/core/__init__.py` and 11 others; §3.4 | Medium |
| F14 | §5.6's closing bullet — "Every command needs a docstring serving as `--help`, with a one-line summary and at least one `Examples:` block" — governs the Click command function, whose docstring *is* the `--help` text. Read as reaching the module header it becomes a second, contradictory rule about headers, and an `Examples:` block is exactly the shape §3.1 excludes. This is the correct home for invocation text: the command function's docstring, which the user sees. | §5.6 last bullet; §3.1 | Medium |
| F12 | `.github/ISSUE_TEMPLATE/issue.schema.json` and `issue.template.json` carry no prose at all — pure field definitions. The template class named in the issue's second AC is clean. | `.github/ISSUE_TEMPLATE/*` | — |

## 4. Decisions

Scope is the full union — Sets A, B, C and D — implemented as **separable steps**, one per set, so that if Ray later decides Set B or Set C should be its own issue the split is a step boundary rather than a rewrite. Recorded with the reasoning, since the alternative was live for two drafts:

| | Decision | Why |
| --- | --- | --- |
| D1 | Full union in one issue, Sets A / B / C / D as separate steps | Set A is the class that caused the failure and cannot wait; B and C are conformance work whose cost is real but whose risk is not. Separate steps keep the reviewable boundary without deferring anything. |
| D2 | The §1.5 rule is stated by class, not by directory list | *A process rule has exactly one home, `CLAUDE.md` or `docs/DEVELOPMENT_STANDARDS.md`; no other file in the repository may state or imply one.* Covers every file that exists and every file that will exist, and needs no maintained list. The census still walks the directories the issue's AC names — that is evidence, not the rule. |
| D3 | `templates/` is out of scope | JSON only, consumed by the template engine for AI provider calls. No module headers, nothing a session reads as instruction. |
| D4 | Set C conforms to §3.4 as written, not to an illustrative example | A package with a public API gets the docstring, the imports and `__all__`. A package marker with nothing to export — `tests/`, `tests/fixtures/`, `tests/mocks/`, `workmain/database/migrations/` — gets a §3.1 header and no invented exports. §3.4's text is amended to say which of the two a given `__init__.py` is. |
| D6 | Set D deletes the blocks, it does not fix the runners | A runner that discovers tests correctly is still a second invocation `docs/DEVELOPMENT_STANDARDS.md` §6 does not recognise. Repairing `run_all_tests()` to cover all 33 tests would produce a maintained parallel runner — a manual register — which is worse than none. |
| D7 | The 243 `unittest.TestCase` tests are **not** in scope | A `TestCase` method cannot receive a pytest fixture, so §6.1's mandatory `db_session` is unsatisfiable for them and eighteen classes commit to the live database instead. That is issue **#136**, opened 20260904 and blocked by this one. This issue makes the Set B headers describe what those files actually do; #136 makes the structure right. |
| D5 | Set C carries the only real implementation risk here | Adding imports and `__all__` to `workmain/__init__.py` and the top-level packages creates a new import surface and can produce circular imports. Everything else in this issue is prose. Set C's step runs the suite on its own, before Set A and Set B are judged. |

### What replaces the removed text

Not an option, an answer, recorded so the spec does not have to re-derive it per file.

- **A command or flag in a header** is removed. Where it documented a script's interface, `argparse` already carries it — every file in F4 and F5 defines its flags there, and `--help` is that interface. Nothing is written to replace it.
- **A trigger** is removed. Where it stated a real ordering constraint (`Run AFTER applying migration 017_ai_costs.sql`), the constraint is a property of the migration and survives as prose: *this migration assumes 017 has been applied.*
- **An inventory** becomes the conceptual description §3.1 asks for: what the module does and why, not what it contains.
- **F7's first line** becomes prose — the daemon runs as a systemd user service and refuses to start as root, enforced by `_check_not_root()`.
- **F1's `:9`** is removed with the rest. That those tests bill money is real, and #131 is where it is expressed — as a pytest skip that reports honestly, which is a mechanism rather than a sentence a reader has to act on.

### The standards edits

Given by Ray; listed so the spec has the set in one place.

- **§1.5** — preamble widened from `docs/dev/` artifacts to all text in the repository, plus the new rule: a process rule has exactly one home, `CLAUDE.md` or `docs/DEVELOPMENT_STANDARDS.md`, and no docstring, comment, template or README may state or imply one. It records the failure it exists for, per the issue's fourth AC.
- **§3.1** — the explicit exclusion (no terminal commands, no flags, no invocation, no triggers, no inventories of code tools) and Ray's summary-plus-description example.
- **§3.4** — an `__init__.py` example: module header, grouped imports, explicit `__all__`. Every `__init__.py` in the tree is then conformed to it.
- **§3.5** — retitled and rescoped so it cannot be read as governing module headers. It is function-level and class-level: `Args`, `Returns`, `Raises`, `Attributes`, with type hints.
- **§5.6** — its closing docstring bullet scoped explicitly to the Click command function, whose docstring *is* the `--help` text the user sees. That is the correct and only home for an `Examples:` block containing invocations; §3.1 excludes the same text from a module header, and the two stop contradicting each other (F14).

### Set D — the `__main__` blocks

Delete all twelve, and the four in-module runners with them: once the guard is gone, `run_all_tests()` and `main()` have no caller. The industry-standard shape for a pytest module is no `__main__` block at all — a test module is a library the runner imports, and running a subset is a command-line concern §6 already states (`pytest tests/test_x.py`, `pytest tests/test_x.py::TestClass::test_name`). Even `pytest.main([__file__])` is caveated by pytest itself, since the module is already imported and plugin state does not reset.

Safe by construction: under `pytest` the blocks never execute, so removing them changes no collected test and no result. Two of the four runners have already drifted (F15). The block is the second invocation §6 says does not exist, and leaving it keeps a live counter-example to the standard this issue is writing. `tests/test_ai_foundation.py` is owned by no other issue. The deletion in `tests/test_ai_clients.py` survives #131's split unchanged, whichever half each function lands in.

### F10 — `CONTRIBUTING.md`

Delete it. Nothing links to it, it has never held a byte, and its name is the standing invitation. `CLAUDE.md` and `docs/DEVELOPMENT_STANDARDS.md` are the two homes; a third named home with no content is the gap the rule closes.

## 5. Acceptance criteria this issue needs

The issue carries five ACs. Two need replacing and six need adding, because the work has grown from removing one docstring line to conforming 75 files and amending five standards sections. Written in the §1.2 form — a property of the delivered system, with the evidence for it named.

Replacing the issue's existing AC1 and AC2:

| | Criterion |
| --- | --- |
| AC1 | No module header under `tests/`, `workmain/`, `automation/` or `scripts/` contains a terminal command, an environment variable assignment, a command-line flag, an invocation, or a trigger for when to run something — *property of the repository*, checked by re-running the census script this study used and getting zero hits in all four classes, with the script and its output recorded in the results artifact. |
| AC2 | `docs/DEVELOPMENT_STANDARDS.md` §1.5 states that a process rule has exactly one home, `CLAUDE.md` or `docs/DEVELOPMENT_STANDARDS.md`, and that no other file in the repository may state or imply one — *property of a document*; check is a stated reading by Ray. Stated by class, not as a list of file kinds or directories (D2). |

Added:

| | Criterion |
| --- | --- |
| AC6 | §3.1 states that a module header is a one-line summary and a conceptual description of what the module does and why, and excludes terminal commands, flags, invocations, triggers and inventories of code tools by name — *property of a document*; check is a stated reading by Ray. |
| AC7 | Every module header under the four trees opens with a one-line summary and continues as description — no bullet inventory, no `Commands:` / `Covers:` / `Features:` / `Steps:` block — *property of the repository*, checked by the census script reporting zero inventory-shaped headers, and by a stated reading by Ray of the Set B diff. |
| AC8 | §3.4 states which `__init__.py` gets imports and `__all__` and which is a package marker that gets a header only, so the rule is decidable without asking — *property of a document*; check is a stated reading by Ray. |
| AC9 | Every `__init__.py` conforms to §3.4 as amended — *property of the repository*, checked by the census script reporting zero nonconforming files, and by `pytest` passing, which is what fails if the new imports introduce a cycle. |
| AC10 | §3.5 cannot be read as governing a module header — its title and opening sentence scope it to function-level and class-level docstrings — and §5.6's docstring bullet cannot be read as governing one either, being scoped to the Click command function whose docstring is its `--help` — *property of two documents*; check is a stated reading by Ray. |
| AC11 | No test module can be run as a script, and no file exists whose name reserves a home for process text it does not hold — *property of the repository*, checked by `grep -rn "__main__" tests/` returning nothing, `grep -rn "def run_all_tests\|def main" tests/` returning nothing, and `CONTRIBUTING.md` being absent. |

The issue's existing AC3, AC4 and AC5 stand as written: the one-home rule records the failure it exists for; the standards state it; and `pytest` and `pytest automation/` report the counts they reported at the start of the branch.

**Still to confirm:** the eight new and replacement criteria above. Everything else in this study is decided.

## 6. Consequences

The rule §1.5 gains is the one thing here §3.1 could not have caught. §3.1 governs the shape of a module header; it does not say that a process rule has one home, so a rule written into a comment, a template or a `README` would still have no section to violate. Both are needed: §3.1 keeps commands and flags out of headers, §1.5 keeps rules out of everywhere that is not the two homes.

Neither reaches the reason the flag was attractive. That is #131's: a gate that reports a skipped test as passed, and a suite whose recorded evidence never had to say what was skipped. This issue removes the sentence; #131 removes the mechanism. The order on the board is correct — the sentence is what two roles read.

Behaviour is unchanged everywhere except Set C. Sets A and B are prose; the two `__main__` deletions remove no collected test and the `CONTRIBUTING.md` deletion removes an empty file. Set C adds imports and `__all__` to packages that currently export nothing, which is a real change to the import graph and the one place in this issue where the suite can go red. Its step runs `pytest` on its own before anything else is judged (D5).
