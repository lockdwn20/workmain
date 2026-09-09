# A process rule has one home — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20260909
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
| 20260908 | Caliper F6 | Issue #134's AC2 names `config/` and `.github/` and covers comments and non-module docstrings. The spec silently dropped `config/`, comments and non-module docstrings while DR1 is stated far wider than any step enforces. A live survivor exists: `config/intent_parse_system_prompt.txt:11-32` states a VERSION AUTHORITY rule and a five-step tuning workflow that **contradicts** `CLAUDE.md`'s version-bump workflow. | Accepted. `config/` is back in scope. The comment census this finding prompted was `.py`-only and its "clean" conclusion was withdrawn in round 2 — see G2 and G3. |
| 20260908 | Caliper F7 | §2's claim that no §1.5 bullet reaches code, config or a README is overstated: *"Markdown is never hard-wrapped"* and *"No version headers … in any document"* are already repo-wide. | Accepted. §2 corrected, and the version-header bullet is cited in Step 2 as the precedent for the new bullet's form. |
| 20260908 | Caliper F8 | "194 module headers" is a file count; 179 carry a header. Fourteen of the 15 without one are the empty `__init__.py` files. The fifteenth is `scripts/sanitize_ics.py` — real code, no header, a §3.1 violation in no set, no step and no AC. AC7.1 passes vacuously on a file with no header. | Accepted. **Set E** is modules with no header at all. AC7.1 is reworded to require a header before judging its shape. |
| 20260908 | Caliper F9 | Step 5's per-file outcome is not determined: under DR4 all 14 empty inits may be markers and the step changes no import, making §7's top risk moot; under §7's reading it is the riskiest step in the spec. | Accepted, and resolved empirically rather than by preference: `from <pkg> import` at package level returns **zero** hits for all 14 packages (the single `workmain.cli.commands` hit imports a module, not an export). All 14 are markers under DR4. Step 5 adds no import and no `__all__`, §7's circular-import risk is withdrawn, and the shape of each of the 16 files is named in Step 5. |
| 20260908 | Caliper F10 | AC5.1 hardcodes 992/4 and requires a run that makes billed API calls whose failures are vendor-dependent, so a differing count is not attributable to this work. | Accepted. AC5.1 is worded as no new failure and no reduction in passed count. |
| 20260909 | Caliper G1 | **Blocking.** DR8 censuses every `.py` under `automation/`, and the repo's fixture convention is on-disk files in `automation/fixtures/`. Step 1's fixtures would therefore be committed `.py` files with deliberately non-conforming headers, and AC1.1 and AC7.1 could never report zero. | Accepted. DR10: the census test writes each fixture as an inline source string into pytest's `tmp_path`. Nothing non-conforming is committed, so no census exclusion is needed and none is added — an exclusion is a hole the next reader cannot see. |
| 20260909 | Caliper G2 | **Blocking.** Step 8's second census — comments and non-module docstrings — had no classifier and no file-type scope, while DR8 specified the other half to the character. The trees hold 24 `.sql`, 28 `.json`, 16 `.md`, 1 `.sh` and 1 `.txt` besides the 194 `.py`, with real candidates in them: `022_intent_action_constraints.sql:14` (`-- Verification (run manually after applying):`), `021_time_entries_note_id.sql:5` (an ordering constraint), and `tests/test_ai_clients.py:361-363`, a comment naming the `SKIP_API_TESTS` gate and stating which tests must not sit behind it. | Accepted in full. DR9 states the second classifier and its file types; it is delivered in the same module as DR8's and is tuned for **recall, not precision** — it proposes candidates, a human adjudicates every one, and the adjudication is the deliverable. Step 9 does that work. The `.sql` hits are DR3 adjudications of exactly the kind Step 3 makes for the migration script headers. |
| 20260909 | Caliper G3 | The "comments are clean" conclusion was load-bearing, lived only in the Decision Log, carried no command and no hit list, and let §1 say the census is "recorded whether or not it produces an edit" — i.e. that no edit was expected. G2 found candidates that reading missed. | Accepted. The conclusion is withdrawn, not relocated: it was a `.py`-only regex pass reported as though it covered the trees. Step 9 returns the answer; §1 no longer predicts it. This is the same over-claim shape as F1 and is recorded rather than quietly fixed. |
| 20260909 | Caliper G4 | DR1 forbids enumerating file kinds in the rule's text; AC2.1 required the rule to say "docstring, comment, template or README" — an enumeration, checked by an AC. Unsatisfiable together, and a rule listing four kinds does not reach a `.sql` comment or a `.sh` header. | Accepted. The bullet is worded by class — text that travels with the code — and AC2.1 checks the class. DR1 stands unchanged. This reaches `.sql` and `.sh` for free, which is G2 answered from the other end. |
| 20260909 | Caliper G5 | AC9.1's check was `git diff --stat`, which emits per-file counts and no line content, so it cannot tell a docstring line from an import line. | Accepted. Replaced with `git diff <range> -- '**/__init__.py' \| grep -E '^[+-](from \|import \|__all__)'` returning nothing. |
| 20260909 | Caliper G6 | Step 6 hardcoded `scripts/sanitize_ics.py` as Set E's only member while Steps 3 and 4 defer to the classifier. If the delivered script reports a second `NO_HEADER`, AC7.1 fails with no step owning it. | Accepted. Set E's step is worded "as reported by Step 1", as Steps 3 and 4 are. |
| 20260909 | Caliper G7 | Step 6 bundled Set E with the `config/` removal, against the one-step-per-set property, and the `config/` half is the only one carrying a stop-and-report. | Accepted. Split into two steps. |
| 20260909 | Ray | Step 2 described five standards changes through six cross-references. An implementer had to resolve all six to find the text, and no reviewer could see the result without writing it. | Replaced by §4.1 — six edits, current text quoted in full, replacement verbatim, matched on text not line number. |
| 20260909 | Ray | **The census does not judge; Ray judges.** A classifier has recall, not precision — `Run AFTER applying migration 017` and `Run once as part of Phase 13 Gate 1` match the same pattern and have opposite correct outcomes. An AC reading "the script reports zero" is satisfiable by rewording to evade the regex while leaving the instruction in place. | Accepted; this was the spec's own Role 2 Q7 defect. The script is a one-time gathering tool in `scripts/`, and issue #134's original AC form is restored: the search performed, every hit adjudicated, and the check is Ray's stated reading of that record. `automation/`, the test file, the close-out row and the `pre-push` hook are all withdrawn — see the next three rows. |
| 20260909 | Ray | No `P12` close-out row, no `pre-push` wiring, no change to `.claude/skills/closeout/`. | Accepted, and `pre-push` was independently unworkable: §2.3 means a working branch is never pushed, so the hook first fires on the `dev` push at close-out step 3 — after the merge, when the branch that introduced the violation is gone. Former §8 deleted. |
| 20260909 | Ray | The census is one-time. Once every file has been reviewed, the standards govern new files. | Accepted. `scripts/rule_census.py`, run once. §6.3 places it: `scripts/` is utilities, never tests, and there is nothing to test for once the script stops deciding anything. |
| 20260909 | Ray | Files may be left as they are where they are one-time and carry historical information — the precedent set by the v1.29.0 file-header work. | Accepted. **"Leave as is" is a first-class adjudication outcome.** v1.29.0 enumerated its exceptions in its own artifacts and added no carve-out to §3.1; this work does the same, so Edit 2's §3.1 text needs no exception clause. |
| 20260909 | Ray | The census must list **every file**, including those producing no hit, so a no-result row can be hand-checked and a miss caught rather than skipped. | Accepted, and it replaces a weaker mitigation. Nothing checks a classifier's recall except a human reading the files it cleared; an absent file cannot be checked, a "no hits" row can. `.json` files appear with the reason they yield nothing rather than being silently excluded. |
| 20260909 | Ray | The A/B/C/D/E/F set vocabulary produced multiple passes and multiple outputs where one belongs. | Accepted. One run, one report, one adjudication pass. The categories survive as a column in the report, which is where they help; they are no longer step boundaries. Ten steps become six. |

**Reading the rows above.** The Caliper F and G rows record findings and the resolutions taken *at the time*. Several of those resolutions — the `automation/` placement, the census test file, DR10's `tmp_path` fixtures, DR11, the A-to-F set vocabulary and the step numbering they imply — were superseded by Ray's 20260909 decisions in the rows that follow. The findings still stand and are still answered; the mechanism changed. §1 through §7 are the current spec, and where a row above disagrees with them, they win.

---

## 1. Scope

**In scope.** Five sections of `docs/DEVELOPMENT_STANDARDS.md` — §1.5, §3.1, §3.4, §3.5, §5.6, replaced verbatim per §4.1.

Every file under `tests/`, `workmain/`, `automation/`, `scripts/` and `config/` — 194 `.py`, 28 `.json`, 24 `.sql`, 16 `.md`, 1 `.sh`, 1 `.txt` at authoring — surveyed once by `scripts/rule_census.py` and adjudicated by Ray, row by row. The census reports module headers, non-module docstrings, comments, and the text of non-`.py` files. **Its output is evidence, not a verdict**: what it reports is a candidate, and what happens to a candidate is Ray's determination, which may be remove, edit, or leave as is.

Also in scope, and needing no adjudication because they are already decided: the 12 `__main__` blocks and 5 in-module runners under `tests/`, and the deletion of the empty `CONTRIBUTING.md`.

**The counts above are the authoring-time reading and are not acceptance criteria.** The census reports what is there when it runs.

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
| The five trees hold 24 `.sql`, 28 `.json`, 16 `.md`, 1 `.sh` and 1 `.txt` file besides the 194 `.py`. | `find tests workmain automation scripts config -name "*.<ext>"` |
| `workmain/database/migrations/022_intent_action_constraints.sql:14` states `-- Verification (run manually after applying):` followed by two `SELECT`s and `-- Both should return 0.` | that file |
| `workmain/database/migrations/021_time_entries_note_id.sql:5` states that stub notes are created by `migrate_021_time_entries_note_id.py` **before this SQL runs** — an ordering constraint between two files. | that file |
| `tests/test_ai_clients.py:361-363` is a comment stating that the offline tests run under `SKIP_API_TESTS=1` without a key and **must not sit behind the `SKIP_API_TESTS` gate**. | that file |
| `automation/fixtures/` holds 35 on-disk fixture files for the existing `automation/*_test.py` suites. | `ls automation/fixtures/` |

## 3. Design rules

- **DR1 — The rule is stated by class, never as a list.** No enumeration of file kinds, directories, or exempt paths in the rule's text.
- **DR2 — A module header describes; it never instructs.** One-line summary, then a conceptual description of what the module does and why. No terminal command, environment variable assignment, command-line flag, invocation, trigger, or inventory of the code tools the module contains.
- **DR3 — Removed text is not relocated by default.** A command or flag that documented a program's interface is already carried by its `argparse` definition and `--help`; nothing replaces it. A genuine ordering constraint is a property of the code and survives as prose. Otherwise the text is deleted.
- **DR4 — An `__init__.py` conforms to §3.4 as amended, not to an example.** A package with a public API gets the docstring, the imports and `__all__`. A package marker with nothing to export gets a §3.1 header and nothing else. **Never add an export to make a file look conforming** — §2 records that no package-level import exists for any of the 14.
- **DR5 — Step 5 deletes; it does not repair.** Do not fix a drifted runner to cover the tests it misses. A maintained parallel runner is a manual register and is worse than none.
- **DR6 — A header is rewritten only where it is wrong or shapeless.** A header that accurately describes a non-obvious mechanism and its reason — the seven files documenting why they use a committed session rather than the `db_session` fixture — is what §3.1 asks for. Preserve that content; reshape only if the classifier flags it, and never drop the *why*.
- **DR7 — No test body, assertion, fixture or isolation mechanism is altered by this spec.** If a step appears to require one, stop: `CLAUDE.md` Role 3.
- **DR8 — The census gathers; it never decides.** `scripts/rule_census.py` runs once and writes one report. It parses every `.py` under the five trees with `ast` and reads the module docstring, every non-module docstring, and every `#` comment line; for `.sql`, `.sh`, `.md` and `.txt` it reads every line; for `.json` it reads nothing, because JSON has no comment syntax. **Every file appears in the report** — those with candidates and those without, the latter as an explicit no-hit row carrying the reason nothing matched. A file's absence from the report is a defect in the script, not a clean file. Each candidate row carries file, line, the matched text verbatim, and the category that flagged it: `COMMAND` (a `python`/`python3` invocation naming a `.py` path, a bare `pytest` or `gh` invocation, or a `Usage:` label), `FLAG` (`--word`, or an uppercase identifier of three or more characters followed by `=`), `TRIGGER` (a line beginning `Run`, `Increment` or `Update`, or containing "before deploying", "run once", "run manually", "must not", "as part of … Gate", or an ordering phrase naming another file), `VERSION` (a `<name>.py v<digits>` line or a bare eight-digit date), `INVENTORY` (a line beginning `-`, `*`, `•`, `N.` or `N)`, or a label line `Commands:` / `Covers:` / `Features:` / `Steps:` / `Usage:` / `Tests:`), `NO_HEADER` (a `.py` file whose module docstring is `None`). **The categories are tuned for recall.** A false positive costs one line of adjudication; a false negative costs a missed violation, which is why the no-hit rows exist.
- **DR9 — Every row gets a determination, and "leave as is" is one of them.** Ray adjudicates each row: remove, edit, or leave as is. A file that is one-time and carries historical information may stand unchanged — the precedent is v1.29.0, which enumerated its exceptions in its own artifacts and added no carve-out to §3.1. Every determination, including every "leave as is" and its reason, is recorded in the results artifact. **No row is acted on before its determination exists, and no row is left without one.**

An implementer who hits something these do not cover stops at the step — `CLAUDE.md` Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | The five standards edits, stated verbatim in §4.1 below. Nothing else in `docs/DEVELOPMENT_STANDARDS.md` changes. They land first so the census is adjudicated against the amended §3.1, not the one it replaces. | `docs/DEVELOPMENT_STANDARDS.md` |
| 2 | Write `scripts/rule_census.py` per DR8 and run it once. It writes one report covering every file under the five trees — every candidate row with its file, line, verbatim text and category, and every no-hit row with the reason nothing matched. **Nothing in this step edits a surveyed file.** | `scripts/rule_census.py`, and the report into `docs/dev/results/PROCESS_RULE_HOME_RESULTS.md` |
| 3 | **Stop. Ray adjudicates the report** — every row, remove / edit / leave as is. Record each determination and the reason for every "leave as is" (DR9). Nothing is edited until the determinations exist. | `docs/dev/results/PROCESS_RULE_HOME_RESULTS.md` |
| 4 | Apply the determinations. A header rewritten to §3.1 keeps whatever it accurately described (DR6); an ordering constraint kept as prose (DR3); a file marked "leave as is" is not touched and stays enumerated in the artifact. `config/intent_parse_system_prompt.txt` is adjudicated with everything else — and where its `workmain-intent-1/-2` versioning contradicts `CLAUDE.md`'s `workmain-intent:latest`, **stop and report**: removing a duplicate is this spec's, deciding which of two conflicting rules is right is not. | as determined in Step 3 |
| 5 | Delete the `__main__` block from the 12 test modules that carry one, and the 5 in-module runners (`run_all_tests` in `tests/test_ai_clients.py` and `tests/test_ai_foundation.py`; `main` in `tests/test_config_system.py`, `tests/test_tag_system.py`, `tests/test_templates.py`). Delete imports left unused. **`tests/google_drive/gdrive_probe.py` keeps its `__main__`** — a standalone program's argparse entry point, not a test runner. No adjudication: this is decided. | 12 files under `tests/` |
| 6 | Delete `CONTRIBUTING.md`. Re-run the census and record the second report beside the first. Complete the results artifact. | `CONTRIBUTING.md`, `docs/dev/results/PROCESS_RULE_HOME_RESULTS.md` |

### 4.1 Step 1 — the five edits, stated literally

Line numbers are as of `83ff5f9`. Match on the quoted text, not the number.

**Edit 1 — §1.5, insert after line 121** (`- **No version headers or version-history blocks in any document.** …`), as the next bullet:

```markdown
- **A process rule never travels with the code.** Text that ships alongside what it describes — a docstring, an inline comment, a template, a file whose name invites it — says what the thing does and what it requires. It never says what a person should do about that. `CLAUDE.md` and this document are the two homes for a process rule; per `CLAUDE.md`'s opening, everywhere else cites them. This bullet exists because `tests/test_ai_clients.py` stated that an environment variable would skip its live API tests. Two roles, in two sessions, read a statement of what the flag did as an instruction to set it, ran a modified command in place of the suite, and shipped four real failures to `main` and to the running daemon.
```

**Edit 2 — §3.1, replace line 294** in full:

- Current: `- PEP 257 module docstring, description only. **No version, no date, no version-history block.** Git tags, `CHANGELOG.md`, and `workmain/__version__.py` are the version record.`
- Replacement:

```markdown
- PEP 257 module docstring: a one-line summary, then a paragraph describing what the module does and why. **No version, no date, no version-history block** — git tags, `CHANGELOG.md`, and `workmain/__version__.py` are the version record. **No terminal command, no environment variable, no command-line flag, no invocation, no trigger for when to run something, and no inventory of the module's own contents.** A command belongs to `argparse` or to a Click command's own docstring (§5.6), which is where a reader looking for it will be.
```

**Edit 2b — §3.1, replace the example at lines 296-301** so it shows the shape Edit 2 describes:

```python
"""
Parses, validates, converts and formats tags for display.

Tags are case-insensitive, are normalized on entry, and are validated
against config/tags.json. Callers receive full names; short forms are an
input convenience and are never stored.
"""
```

**Edit 3 — §3.4, replace line 344** in full:

- Current: `- Descriptive docstring, import classes *and* singleton getters, declare `__all__`. No `__version__` constant.`
- Replacement:

```markdown
- A package that exposes an API gets a §3.1 docstring, imports of its classes *and* singleton getters, and an `__all__` declaring them. A package that exposes nothing — a namespace holding modules that callers import directly — gets the §3.1 docstring and nothing else. Which one a package is, is a fact about it: if no caller writes `from <package> import <name>`, it exposes nothing, and inventing exports to satisfy this section is not conformance. No `__version__` constant in either.
```

**Edit 4 — §3.5, replace lines 346 and 348.**

- Current heading: `### 3.5 Type hints and docstrings`
- Replacement heading: `### 3.5 Function and class docstrings`
- Current line 348: `- Type hints on every parameter and return. Google-style docstrings on every public function and class.`
- Replacement:

```markdown
- **This section governs functions and classes. It does not govern module headers, which are §3.1's.** Type hints on every parameter and return. Google-style docstrings on every public function and class — `Args:`, `Returns:`, `Raises:`, `Attributes:`. Those blocks belong to a function or a class and never appear in a module header.
```

**Edit 5 — §5.6, replace line 613** in full:

- Current: `- Every command needs a docstring serving as `--help`, with a one-line summary and at least one `Examples:` block.`
- Replacement:

```markdown
- Every Click command function needs a docstring, with a one-line summary and at least one `Examples:` block. That docstring *is* the `--help` output, so it is written for the person running the command and is the one place invocations and flags belong. It is not a module header — §3.1 governs those and excludes exactly this content.
```

Any cross-reference this spec makes elsewhere to §1.5, §3.1, §3.4, §3.5 or §5.6 means the text above once Step 1 is committed.

### Authorization points

**None.** No migration, no GitHub object deleted, no merge to `main`, no force-push, no change to a live service's run state. The `dev → main` PR, version bump, tag and restart belong to `/closeout`.

Issue #136's final acceptance criterion deletes three leaked rows from the live `reports` table. That is #136's. **Do not delete a database row in this branch.**

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Every file under the five trees was surveyed, and each appears in the report either with its candidates or with an explicit no-hit row — so a file the classifier cleared can be hand-checked rather than silently skipped | Ray's stated reading of the report: the file list is complete, and the no-hit rows are what he expects them to be |
| AC1.2 | Every candidate row carries a determination, and every "leave as is" carries its reason | Zero rows without a determination; Ray's stated reading |
| AC1.3 | The repository matches the determinations — every row marked remove or edit was acted on, and every row marked leave as is was not touched | Ray's stated reading of the Step 4 diff against the adjudicated report |
| AC2.1 | §1.5 states by class — text that travels with the code — that such text may say what a thing does and may not carry a process rule, and names the two homes. It enumerates no file kind, directory or exempt path (DR1) | Stated reading by Ray |
| AC3.1 | The new bullet records the failure it exists for | Stated reading by Ray |
| AC5.1 | `pytest` produces no failure other than the four at the branch point, and no reduction in passed count; `pytest automation/` reports 51 passed | Both run and compared against §6 |
| AC6.1 | §3.1 states the summary-plus-description shape and excludes commands, flags, invocations, triggers and inventories by name | Stated reading by Ray |
| AC8.1 | §3.4 states which `__init__.py` gets imports and `__all__` and which is a package marker, so the rule is decidable without asking | Stated reading by Ray |
| AC9.1 | No `__init__.py` gained or lost an import or an `__all__` entry — the determinations are about headers, not exports | `git diff <step-4-range> -- '**/__init__.py' \| grep -E '^[+-](from \|import \|__all__)'` returns nothing |
| AC10.1 | §3.5 cannot be read as governing a module header, and §5.6's docstring bullet is scoped to the Click command function | Stated reading by Ray |
| AC11.1 | No test module can be run as a script | `grep -rln "__main__" tests/` returns `tests/google_drive/gdrive_probe.py` and nothing else |
| AC11.2 | No in-module test runner remains | `grep -rn "^def run_all_tests\|^def main" tests/` returns no matches |
| AC11.3 | No file exists whose name reserves a home for process text it does not hold | `CONTRIBUTING.md` is absent |
| AC12.1 | The three candidates verified in §2 each appear in the report with a determination — the two `.sql` ordering constraints in `workmain/database/migrations/`, and the `SKIP_API_TESTS` gate comment at `tests/test_ai_clients.py:361-363` | `grep` for the three locations in the results artifact; stated reading by Ray |

Issue #134's AC1 and AC2 are replaced by AC1.1 and AC2.1; AC6 through AC12 are added; and AC3 is met by a bullet that cites rather than restates the general rule (F5). The issue is edited to match at close-out — a spec is designed on the merits and the issue's criteria are reconciled to it, never the reverse.

## 6. Test plan

- **Baseline**, measured on `feature/issue-134-process-rule-home` at `83ff5f9` on 20260908: `pytest` → **992 passed, 4 failed, 26 warnings**; `pytest automation/` → **51 passed**.
- **The suite is not green at the branch point and this spec cannot make it green.** The four are `tests/test_ai_clients.py::{test_claude_generation, test_gemini_generation, test_provider_status, test_cost_tracking_integration}` — the same four in `docs/archive/results/VENDOR_SDK_PINNING_RESULTS.md` AC9.1, root cause **#130**, carried to **#131**. Ruled by Ray on 20260908 as known and handled at close-out.
- **Expected after:** both unchanged. This spec adds no test and removes none.
- **No new test file.** `scripts/rule_census.py` is a one-time gathering tool, and `docs/DEVELOPMENT_STANDARDS.md` §6.3 places `scripts/` as utilities and demos, never tests. It decides nothing, so there is nothing to test it *for* — its recall is checked by Ray reading the no-hit rows (AC1.1), which is a stronger check than a fixture suite, because it is performed against the real tree rather than against examples the author chose.
- No test is added under `tests/`; no behaviour is added to cover.

## 7. Risks and rollback

| Risk | Blast radius | Rollback |
| --- | --- | --- |
| **The classifier misses a category, so a violation is never proposed.** Nothing tests the script, and it decides nothing, so a silent miss is the one failure it can still cause. | One or more violations survive the work that exists to remove them. | Every file appears in the report, so a miss shows as a no-hit row on a file Ray can open (AC1.1). This is why the no-hit rows exist, and it is the reason a fixture suite was not a substitute — a suite tests the examples its author thought of. |
| **Adjudication under volume.** Roughly 264 rows, most of them legitimate. A reviewer can start clearing rows without reading them. | The half of issue #134's second acceptance criterion this spec exists to satisfy. | AC1.2 requires a determination per row and a reason per "leave as is", not a verdict. AC12.1 names three rows verified in §2 that must each carry a determination, so a blanket clearance is visible: two are ordering constraints DR3 preserves as prose, one is a comment about the very flag this issue removes. |
| **A header rewrite loses information.** `workmain/cli/commands/eod.py`'s step sequence and `reports.py`'s subcommand list are currently the only description of what those modules do. Seven test headers carry a non-obvious mechanism and its reason. | A reader is left with less than they had — and in the seven, less than the standard wants. | DR6, and AC1.3 — Ray reads the Step 4 diff against his own determinations. |
| **A migration script's ordering constraint is deleted as a trigger.** `Run AFTER applying migration 017_ai_costs.sql` is a real precondition wearing an imperative. | One script, re-run out of order at some future date. | DR3 requires it to survive as prose. Ray reads the Step 3 diff. |
| **Step 6 removes text from a file the Ollama model build depends on.** The block is a header comment, not prompt content, but the file's SYSTEM block is synced to a Modelfile outside this repository. | The intent parser, if the sync copies the wrong region. | The version metadata fields stay. Step 6 stops and reports rather than adjudicating the `workmain-intent-1` vs `:latest` contradiction, so no build behaviour is decided here. |
| **Step 7 deletes an import another part of the file uses.** | One test file fails to import; caught immediately. | `pytest` at the end of the step. |
| **Scope creep into #136 or #137.** Sixteen files in Step 4 are `TestCase` modules; four are the assertion-less ones. Fixing either is tempting and is neither this spec's. | The branch grows a refactor with no spec behind it. | DR6 and DR7. |

**Withdrawn risk.** The first draft named Step 5's circular-import exposure as the top risk. §2 records that no package-level import exists for any of the 14 packages, so DR4 makes them all markers and Step 5 adds no import. AC9.1 checks that directly.
