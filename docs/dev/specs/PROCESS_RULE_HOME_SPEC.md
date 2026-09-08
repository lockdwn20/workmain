# A process rule has one home — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20260908
**Branch:** `feature/issue-134-process-rule-home` (from `dev`)
**Target release:** v1.34.0
**Originating item:** Issue #134
**Design study:** `../design/DESIGN_PROCESS_RULE_HOME.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260904 | Spanner | Three successive attempts to define what a docstring may say — an audience test, the issue's literal wording, a decision-ownership test — were all attempts to draw a boundary §3.1 had already drawn. | Withdrawn. §3.1 states that a module header is a one-line summary and a conceptual description; commands, flags, invocations, triggers and inventories were never permitted there. The design study records the withdrawn options so they are not proposed again. |
| 20260904 | Ray | §3.5's title reads as licence to put function-level docstring content in a module header, and §5.6's docstring bullet can be read as reaching one too. | Both rescoped — §3.5 to function and class level, §5.6 to the Click command function. |
| 20260904 | Ray | Scope is the full union of non-conforming files, not the subset with a direct line to the failure. | One step per set, so any set can be split to its own issue at a step boundary. |
| 20260904 | Ray | The rule is stated by class, not as a list of file kinds or directories. | DR1. |
| 20260904 | Ray | `templates/` is out of scope — JSON consumed by the template engine for AI provider calls. | §1 Out of scope. |
| 20260904 | Spanner | High primary keys (`notes_id_seq` 83,431 against 2,281 rows) were suspected to be test leakage. | Not leakage. PostgreSQL sequences are non-transactional, so a correctly isolated `db_session` test burns an id permanently too. Recorded so it is not re-investigated. |
| 20260908 | Spanner | The first draft stated a 996-passed baseline and an AC of "996 passed, 0 failed". No run produced either; both came from `pytest --collect-only`, which reports what is collected, not what passes. | Corrected against a real run. Recorded because it is this issue's own failure mode committed inside the spec that closes it. |
| 20260908 | Ray | The four pre-existing `tests/test_ai_clients.py` failures are known, are covered by open issues (#130 root cause, #131 file and reporting), and are handled at close-out. No finding is to be raised against them. | §6 records them as the branch-point baseline; §7 records the ruling. |
| 20260908 | Spanner | 18 tests across four files contain zero assertions and signal pass/fail by returning a boolean, which pytest discards. | Out of scope (DR7). Opened as **#137**, blocked by this issue. |
| 20260908 | Caliper F1 | **Blocking.** §2 claimed eight test modules state they use the `db_session` fixture and do not. False. `tests/test_task_lifecycle.py` says it uses the fixture **and does** — 22 tests take it. The other seven say the **opposite**, in terms: *"Uses a real committed session (get_db().get_session()), **not** the db_session fixture — CliRunner.invoke() drives the command through its own session…"* Those seven headers are accurate and document §6.1's constraint. | Accepted in full. The detection matched the substring `db_session` and inverted the meaning of every hit. §2's claim is replaced by the verified one, DR6 is rewritten, Step 5 no longer rewrites those headers, and **issue #136's body and its fifth AC are corrected on GitHub**, since they propagated the same error. |
| 20260908 | Caliper F2 | **Blocking.** AC1.1, AC7.1 and AC9.1 all check "the census script reports 0 hits", and no step delivers a script or states its classifier — the implementer would write the instrument that judges their own work. Caliper's own heuristic over the same 194 files returned 41/45/29 against the spec's 26/47/33. | Accepted in full. §3 DR8 states the classifier; Step 1 delivers `automation/header_census.py` with its own `automation/header_census_test.py`. The sets are defined by the classifier, not by the numbers — §1's counts are the authoring-time reading and are re-measured by the delivered script. |
| 20260908 | Caliper F3 | Set D is 13 files, not 12. The thirteenth is `tests/google_drive/gdrive_probe.py`, whose `__main__` is an argparse entry point — deleting it destroys the program. AC11.1's grep cannot pass on the delivered state. | Accepted. Step 7 edits 12 of 13; AC11.1 carves out the probe by name and checks that it is the only match. |
| 20260908 | Caliper F4 | "Four in-module runners" — there are five: `run_all_tests` in `test_ai_clients.py` and `test_ai_foundation.py`, `main` in `test_tag_system.py`, `test_config_system.py`, `test_templates.py`. | Accepted. Five throughout, and AC11.2 greps for both names. |
| 20260908 | Caliper F5 | **§1.5 has no preamble**, and giving it a repo-wide one falsifies five of its bullets. Separately, `CLAUDE.md`'s opening already states *"Every fact, decision, and rule has exactly one home. State it there; everywhere else cites it."* — so restating the general rule in §1.5 creates two homes for the one-home rule. | Accepted. No preamble is added. §1.5 gains one repo-wide bullet stating the **specific prohibition** — that near-code text may not carry a process rule — and cites `CLAUDE.md` for the general rule rather than repeating it. Precedent for a repo-wide bullet in §1.5 is F7's two. This departs from issue #134's AC3 wording, which asks for the general rule to be restated; designed on the merits per `CLAUDE.md`, and the issue is reconciled at close-out. |
| 20260908 | Caliper F6 | Issue #134's AC2 names `config/` and `.github/` and covers comments and non-module docstrings. The spec silently dropped `config/`, comments and non-module docstrings while DR1 is stated far wider than any step enforces. A live survivor exists: `config/intent_parse_system_prompt.txt:11-32` states a VERSION AUTHORITY rule and a five-step tuning workflow that **contradicts** `CLAUDE.md`'s version-bump workflow. | Accepted. `config/` is back in scope as Step 6. Comments and non-module docstrings were censused in response to this finding and are clean — the seven candidate hits are all descriptions of code behaviour; the census and its adjudication go in the results artifact, which is what issue #134's AC2 asks for. |
| 20260908 | Caliper F7 | §2's claim that no §1.5 bullet reaches code, config or a README is overstated: *"Markdown is never hard-wrapped"* and *"No version headers … in any document"* are already repo-wide. | Accepted. §2 corrected, and the version-header bullet is cited in Step 2 as the precedent for the new bullet's form. |
| 20260908 | Caliper F8 | "194 module headers" is a file count; 179 carry a header. Fourteen of the 15 without one are the empty `__init__.py` files. The fifteenth is `scripts/sanitize_ics.py` — real code, no header, a §3.1 violation in no set, no step and no AC. AC7.1 passes vacuously on a file with no header. | Accepted. **Set E** is modules with no header at all. AC7.1 is reworded to require a header before judging its shape. |
| 20260908 | Caliper F9 | Step 5's per-file outcome is not determined: under DR4 all 14 empty inits may be markers and the step changes no import, making §7's top risk moot; under §7's reading it is the riskiest step in the spec. | Accepted, and resolved empirically rather than by preference: `from <pkg> import` at package level returns **zero** hits for all 14 packages (the single `workmain.cli.commands` hit imports a module, not an export). All 14 are markers under DR4. Step 5 adds no import and no `__all__`, §7's circular-import risk is withdrawn, and the shape of each of the 16 files is named in Step 5. |
| 20260908 | Caliper F10 | AC5.1 hardcodes 992/4 and requires a run that makes billed API calls whose failures are vendor-dependent, so a differing count is not attributable to this work. | Accepted. AC5.1 is worded as no new failure and no reduction in passed count. |

---

## 1. Scope

**In scope.** Five sections of `docs/DEVELOPMENT_STANDARDS.md` — §1.5, §3.1, §3.4, §3.5, §5.6 — and five sets of files, defined by the classifier in DR8 and measured by the script Step 1 delivers.

| Set | What | At authoring |
| --- | --- | --- |
| A | Module headers containing a terminal command, an environment variable assignment, a command-line flag, an invocation, or a trigger | 26 |
| B | Module headers whose shape is an inventory rather than a description | 33 not already in A |
| C | `__init__.py` files not conforming to §3.4 | 16 of 26 |
| D | Test modules carrying a `__main__` block, and the five in-module runner functions behind them | 13 files, 12 edited |
| E | Modules with no header at all, once Set C has covered the empty `__init__.py` files | 1 — `scripts/sanitize_ics.py` |

Also in scope: `config/intent_parse_system_prompt.txt`'s VERSION AUTHORITY and tuning-workflow block; deletion of `CONTRIBUTING.md`; and the census of comments and non-module docstrings, whose result is recorded whether or not it produces an edit.

**The counts above are the authoring-time reading and are not acceptance criteria.** A set is what DR8's classifier selects. If the delivered script returns different numbers, the script is right and this table is stale — say so in the results artifact and proceed.

**Out of scope.**

- **The 243 `unittest.TestCase` tests** and the eighteen classes that commit to the live database — issue #136. This spec changes some of those files' headers and deletes their `__main__` blocks; it touches no test body and no isolation mechanism.
- **The 18 assertion-less tests** — issue #137.
- **`tests/test_ai_clients.py`'s file split, its `SKIP_API_TESTS` gate, and §6's invocation and skip-reporting rules** — issue #131. This spec removes three lines from that file's header and its `__main__` block and runner.
- **`templates/`** — JSON read by the template engine for AI provider calls.
- **`scripts-deprecated/`**, excluded from collection; **`docs/archive/**`**, never authoritative (§1.5).
- **The Ollama version-bump contradiction itself.** Step 6 removes the duplicate rule from `config/intent_parse_system_prompt.txt`. Which of the two conflicting workflows is correct is Ray's, not this spec's — see §4 Step 6.

## 2. Verified current state

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| §3.1 requires a PEP 257 module docstring, "description only", and prohibits version, date and version-history blocks. It names no other exclusion. | §3.1 |
| §3.4 is one sentence and does not say what a package with no public API does. | §3.4 |
| §3.5 is titled "Type hints and docstrings"; its worked example is a function docstring with `Args:` and `Returns:`. Nothing in it names a module header. | §3.5 |
| §5.6's closing bullet requires every command to have a docstring serving as `--help` with an `Examples:` block. It sits in a section titled Output. | §5.6, last bullet |
| §1.5 has **no preamble** — the heading is followed directly by bullets. Most bullets are scoped to `docs/dev/` artifacts, but two are already repo-wide: "Markdown is never hard-wrapped" and "No version headers or version-history blocks in any document". | §1.5 |
| `CLAUDE.md`'s opening paragraph already states the general rule: "Every fact, decision, and rule has exactly one home. State it there; everywhere else cites it." | `CLAUDE.md`, opening |
| §6 states pytest is the exclusive runner and `testpaths` resolves a bare `pytest` to the application suite. | §6, first two bullets |
| `tests/test_ai_clients.py:9-12` states the tests make real API calls and consume tokens, gives `SKIP_API_TESTS=1`, and gives `Run with: python3 test_ai_clients.py`. | `tests/test_ai_clients.py:9-12` |
| `run_all_tests()` calls nine test functions; the module defines 33. `main()` in `tests/test_config_system.py` iterates a list naming one of that module's three. | `tests/test_ai_clients.py:706`; `tests/test_config_system.py:198` |
| Thirteen files under `tests/` contain a `__main__` block. Five in-module runners exist: `run_all_tests` at `test_ai_clients.py:706` and `test_ai_foundation.py:371`; `main` at `test_tag_system.py:317`, `test_config_system.py:198`, `test_templates.py:234`. | `grep -rln "__main__" tests/`; `grep -rn "^def main\|^def run_all_tests" tests/` |
| `tests/google_drive/gdrive_probe.py:129`'s `__main__` block is an argparse entry point for a standalone probe, not a test runner. | that file |
| 194 `.py` files sit in the four trees; **179 carry a module docstring**. Of the 15 without one, 14 are the empty `__init__.py` files and the fifteenth is `scripts/sanitize_ics.py`. | `ast` census |
| No code imports from any of the 14 empty packages at package level. `from workmain.cli.commands import slack as slack_module` imports a module, not an export. | `grep -rn "from <pkg> import"`; `tests/test_slack.py:409` |
| `tests/test_task_lifecycle.py` states it uses the `db_session` fixture and does — 22 of its tests take it; one of its seven classes is a `TestCase`. | `tests/test_task_lifecycle.py:16`, `:322` |
| Seven test modules state explicitly that they use a real committed session **and not** the `db_session` fixture, and give §6.1's `CliRunner` reason. These headers are accurate. | `tests/test_notes_add.py:15`, `test_notes_edit.py`, `test_notes_log.py`, `test_meetings_condense.py`, `test_meetings_track.py`, `test_time_add.py`, `test_reports_corrections.py` |
| `config/intent_parse_system_prompt.txt:11-32` states a VERSION AUTHORITY rule, a versioning rule and a five-step tuning workflow. Its versioning rule says to increment an `ollama_model` suffix (`workmain-intent-1`, `-2`); `CLAUDE.md` says the model is always referenced as `workmain-intent:latest`. The file's own `model_built` follows neither. | that file; `CLAUDE.md` § Intent Parser Config |
| `workmain/ai/providers/claude.py:5` and `gemini.py:5` state a construction constraint with no command, flag or trigger. Compliant. | those files |
| `.github/ISSUE_TEMPLATE/*.json` contain field definitions only, no prose. | those files |
| `CONTRIBUTING.md` is 0 bytes with no references. | `CONTRIBUTING.md`; `grep -rn CONTRIBUTING` |

## 3. Design rules

- **DR1 — The rule is stated by class, never as a list.** No enumeration of file kinds, directories, or exempt paths in the rule's text.
- **DR2 — A module header describes; it never instructs.** One-line summary, then a conceptual description of what the module does and why. No terminal command, environment variable assignment, command-line flag, invocation, trigger, or inventory of the code tools the module contains.
- **DR3 — Removed text is not relocated by default.** A command or flag that documented a program's interface is already carried by its `argparse` definition and `--help`; nothing replaces it. A genuine ordering constraint is a property of the code and survives as prose. Otherwise the text is deleted.
- **DR4 — Set C conforms to §3.4 as amended, not to an example.** A package with a public API gets the docstring, the imports and `__all__`. A package marker with nothing to export gets a §3.1 header and nothing else. **Never add an export to make a file look conforming** — §2 records that no package-level import exists for any of the 14.
- **DR5 — Set D deletes; it does not repair.** Do not fix a drifted runner to cover the tests it misses. A maintained parallel runner is a manual register and is worse than none.
- **DR6 — A header is rewritten only where it is wrong or shapeless.** A header that accurately describes a non-obvious mechanism and its reason — the seven files documenting why they use a committed session rather than the `db_session` fixture — is what §3.1 asks for. Preserve that content; reshape only if the classifier flags it, and never drop the *why*.
- **DR7 — No test body, assertion, fixture or isolation mechanism is altered by this spec.** If a step appears to require one, stop: `CLAUDE.md` Role 3.
- **DR8 — The census classifier.** The script parses every `.py` under `tests/`, `workmain/`, `automation/`, `scripts/` with `ast`, takes the module docstring, and reports per file: `NO_HEADER` (docstring is `None`); `COMMAND` (a `python`/`python3` invocation naming a `.py` path, a bare `pytest` or `gh` invocation, or a `Usage:` label line); `FLAG` (`--word`, or an uppercase identifier of three or more characters followed by `=`); `TRIGGER` (a line beginning `Run`, `Increment` or `Update`, or containing "before deploying", "run once", or "as part of … Gate"); `VERSION` (a `<name>.py v<digits>` line or a bare eight-digit date); `INVENTORY` (a line beginning `-`, `*`, `•`, `N.` or `N)`, or a label line `Commands:` / `Covers:` / `Features:` / `Steps:` / `Usage:` / `Tests:`). Set A is `COMMAND|FLAG|TRIGGER|VERSION`, Set B is `INVENTORY`, Set E is `NO_HEADER`. **The script prints the matching line for every hit**, so each is adjudicable, and it is exercised by its own test file with fixtures for each class.

An implementer who hits something these do not cover stops at the step — `CLAUDE.md` Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `automation/header_census.py` implementing DR8, with `automation/header_census_test.py` covering one fixture per class and one file per set boundary. Record its output for the untouched tree as the branch-point census. | `automation/header_census.py`, `automation/header_census_test.py` |
| 2 | Standards edits. §1.5 gains **one repo-wide bullet** applying `CLAUDE.md`'s one-home rule to near-code text: a docstring, comment, template or README may say what a thing does and never carry a process rule; the two homes are named; the general rule is cited, not restated (F5). Its form follows §1.5's existing "No version headers … in any document" bullet (F7). It records the failure it exists for. No preamble is added. §3.1 gains the explicit exclusion (DR2) and a summary-plus-description example. §3.4 gains the two package shapes (DR4). §3.5 is rescoped to function and class level. §5.6's closing bullet is scoped to the Click command function. | `docs/DEVELOPMENT_STANDARDS.md` |
| 3 | **Set A** — every header the classifier flags `COMMAND`, `FLAG`, `TRIGGER` or `VERSION`, rewritten to DR2. Ordering constraints survive as prose (DR3). | as reported by Step 1 |
| 4 | **Set B** — every header flagged `INVENTORY`, rewritten to DR2 under DR6. `workmain/cli/commands/eod.py` and `reports.py` need their conceptual description written, since the inventory currently does that work. | as reported by Step 1 |
| 5 | **Set C** — 16 `__init__.py` files. The 14 empty ones are package markers under DR4 and receive a §3.1 header and nothing else: `workmain/`, `workmain/cli/`, `workmain/cli/commands/`, `workmain/config_manager/`, `workmain/core/`, `workmain/database/`, `workmain/database/migrations/`, `workmain/integrations/`, `workmain/notifications/`, `workmain/utils/`, `workmain/web/`, `tests/`, `tests/fixtures/`, `tests/mocks/`. `workmain/ai/__init__.py` and `workmain/ai/providers/__init__.py` already carry imports and `__all__` and need their inventory docstrings reshaped only. **No import and no `__all__` is added or removed in this step.** | 16 `__init__.py` files |
| 6 | **Set E and `config/`.** Write a §3.1 header for `scripts/sanitize_ics.py`. Remove the VERSION AUTHORITY, versioning and tuning-workflow block from `config/intent_parse_system_prompt.txt`, leaving the version metadata fields themselves — `CLAUDE.md` § Intent Parser Config already owns both the source-of-truth statement and the version-bump workflow. **Stop and report** the contradiction between that file's `workmain-intent-1/-2` versioning and `CLAUDE.md`'s `workmain-intent:latest`: this step removes the duplicate, it does not adjudicate which is right. | `scripts/sanitize_ics.py`, `config/intent_parse_system_prompt.txt` |
| 7 | **Set D** — delete the `__main__` block from the 12 test modules that have one, and the five in-module runners (`run_all_tests` in `tests/test_ai_clients.py` and `tests/test_ai_foundation.py`; `main` in `tests/test_config_system.py`, `tests/test_tag_system.py`, `tests/test_templates.py`). Delete imports left unused by the removal. **`tests/google_drive/gdrive_probe.py` keeps its `__main__` block** — it is a standalone program's argparse entry point, not a test runner (F3). | 12 files under `tests/` |
| 8 | Delete `CONTRIBUTING.md`. Census comments and non-module docstrings across the five trees and record every hit with its adjudication. Re-run `automation/header_census.py` and record its output against the branch-point census from Step 1. Write the results artifact — issue #134's second acceptance criterion requires the search performed and every hit adjudicated. | `CONTRIBUTING.md`, `docs/dev/results/PROCESS_RULE_HOME_RESULTS.md` |

### Authorization points

**None.** No migration, no GitHub object deleted, no merge to `main`, no force-push, no change to a live service's run state. The `dev → main` PR, version bump, tag and restart belong to `/closeout`.

Issue #136's final acceptance criterion deletes three leaked rows from the live `reports` table. That is #136's. **Do not delete a database row in this branch.**

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No module header under the four trees is flagged `COMMAND`, `FLAG`, `TRIGGER` or `VERSION` | `python3 automation/header_census.py` reports zero in those four classes; its own test file passes |
| AC1.2 | The instrument that judges the work is itself judged | `pytest automation/header_census_test.py` passes, covering one fixture per DR8 class |
| AC2.1 | §1.5 states that a docstring, comment, template or README may say what a thing does and may not carry a process rule, and names the two homes | Stated reading by Ray |
| AC2.2 | §1.5 cites `CLAUDE.md` for the general one-home rule rather than restating it, and no preamble is added | Stated reading by Ray |
| AC3.1 | The new bullet records the failure it exists for | Stated reading by Ray |
| AC5.1 | `pytest` produces no failure other than the four at the branch point, and no reduction in passed count; `pytest automation/` passes with the count raised only by Step 1's new tests | Both run and compared against §6 |
| AC6.1 | §3.1 states the summary-plus-description shape and excludes commands, flags, invocations, triggers and inventories by name | Stated reading by Ray |
| AC7.1 | Every `.py` file under the four trees has a module header, and none is flagged `INVENTORY` | `header_census.py` reports zero `NO_HEADER` and zero `INVENTORY` |
| AC7.2 | The rewrites say what each file does, and no header that documented a non-obvious mechanism lost its reason | Stated reading by Ray of the Step 3, 4 and 6 diffs |
| AC8.1 | §3.4 states which `__init__.py` gets imports and `__all__` and which is a package marker, so the rule is decidable without asking | Stated reading by Ray |
| AC9.1 | Every `__init__.py` conforms to §3.4 as amended, and Step 5 changed no import | `header_census.py` reports zero; `git diff --stat` for Step 5 shows no change to an import or `__all__` line |
| AC10.1 | §3.5 cannot be read as governing a module header | Stated reading by Ray |
| AC10.2 | §5.6's docstring bullet is scoped to the Click command function | Stated reading by Ray |
| AC11.1 | No test module can be run as a script | `grep -rln "__main__" tests/` returns `tests/google_drive/gdrive_probe.py` and nothing else |
| AC11.2 | No in-module test runner remains | `grep -rn "^def run_all_tests\|^def main" tests/` returns no matches |
| AC11.3 | No file exists whose name reserves a home for process text it does not hold | `CONTRIBUTING.md` is absent |
| AC12.1 | No process rule survives in `config/` | `config/intent_parse_system_prompt.txt` carries version metadata fields and no VERSION AUTHORITY, versioning or tuning-workflow block; stated reading by Ray |
| AC12.2 | The comment and non-module-docstring census was performed and every hit adjudicated | The census, its command, and the adjudication of each hit appear in the results artifact; stated reading by Ray |

Issue #134's AC1 and AC2 are replaced by AC1.1 and AC2.1; AC6 through AC12 are added; and AC3 is met by a bullet that cites rather than restates the general rule (F5). The issue is edited to match at close-out — a spec is designed on the merits and the issue's criteria are reconciled to it, never the reverse.

## 6. Test plan

- **Baseline**, measured on `feature/issue-134-process-rule-home` at `83ff5f9` on 20260908: `pytest` → **992 passed, 4 failed, 26 warnings**; `pytest automation/` → **51 passed**.
- **The suite is not green at the branch point and this spec cannot make it green.** The four are `tests/test_ai_clients.py::{test_claude_generation, test_gemini_generation, test_provider_status, test_cost_tracking_integration}` — the same four in `docs/archive/results/VENDOR_SDK_PINNING_RESULTS.md` AC9.1, root cause **#130**, carried to **#131**. Ruled by Ray on 20260908 as known and handled at close-out.
- **Expected after:** `pytest` unchanged. `pytest automation/` rises by the tests Step 1 adds — the only new tests in this spec.
- **New test file:** `automation/header_census_test.py`. It covers one fixture per DR8 class, a file with no header, and a file that is clean, so the classifier cannot report zero by construction.
- No test is added under `tests/`; no behaviour is added to cover.

## 7. Risks and rollback

| Risk | Blast radius | Rollback |
| --- | --- | --- |
| **The classifier is wrong in a way that reports zero.** Three ACs rest on it. A missed class is a silent pass. | Every set. The work looks complete and is not. | `automation/header_census_test.py` (AC1.2) asserts a positive hit per class, so a classifier that never matches fails its own tests. Ray reads the Step 3/4/6 diffs (AC7.2), which is a second, independent check on the same property. |
| **A Set B rewrite loses information.** `workmain/cli/commands/eod.py`'s step sequence and `reports.py`'s subcommand list are currently the only description of what those modules do. Seven test headers carry a non-obvious mechanism and its reason. | A reader is left with less than they had — and in the seven, less than the standard wants. | DR6. Ray reads the Step 4 diff before it is accepted. |
| **A migration script's ordering constraint is deleted as a trigger.** `Run AFTER applying migration 017_ai_costs.sql` is a real precondition wearing an imperative. | One script, re-run out of order at some future date. | DR3 requires it to survive as prose. Ray reads the Step 3 diff. |
| **Step 6 removes text from a file the Ollama model build depends on.** The block is a header comment, not prompt content, but the file's SYSTEM block is synced to a Modelfile outside this repository. | The intent parser, if the sync copies the wrong region. | The version metadata fields stay. Step 6 stops and reports rather than adjudicating the `workmain-intent-1` vs `:latest` contradiction, so no build behaviour is decided here. |
| **Step 7 deletes an import another part of the file uses.** | One test file fails to import; caught immediately. | `pytest` at the end of the step. |
| **Scope creep into #136 or #137.** Sixteen files in Step 4 are `TestCase` modules; four are the assertion-less ones. Fixing either is tempting and is neither this spec's. | The branch grows a refactor with no spec behind it. | DR6 and DR7. |

**Withdrawn risk.** The first draft named Step 5's circular-import exposure as the top risk. §2 records that no package-level import exists for any of the 14 packages, so DR4 makes them all markers and Step 5 adds no import. AC9.1 checks that directly.
