# Provider Tests State Their Routing — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261023
**Originating item:** Issue #236

---

## 1. Purpose

Tests that drive refusal, fallback and cost recording build a real `ProviderManager` from a copy of the live `config/ai_settings.json`, so their result depends on which provider the operator routes each call type to. This study finds every site whose result depends on that routing, records what each one does today under both orientations of the routing, and sets out how the tests state the routing they need instead. It is written now because #201's baseline is a full `pytest` run against the routing in use, and that run is red.

## 2. Scope of the read

- **Census:** every hit of `git grep -n 'ai_settings.json\|stubbed_manager\|ProviderManager()' -- tests`, each read in full. Plus every test that reaches `get_provider_manager()` through the module singleton, since `ProviderManager()` with no `config_path` resolves the file relative to the package (`workmain/ai/provider_manager.py:438-440`), not the working directory.
- **Application reads of the routing:** `workmain/ai/provider_manager.py` (`_load_config`, `generate`), `workmain/cli/commands/providers.py` (`set_default_provider`), `scripts/compare_providers.py` (`_default_types`).
- **Runs**, all on `hotfix/issue-236-provider-test-routing` cut from `origin/main` at `b39d432`:
  - **Claude-primary:** the working tree as Ray left it on 20261023 — `daily_internal`, `weekly_client`, `note_condensation` Claude primary, Gemini fallback; `monthly_executive` and `daemon_narration` were already Claude primary.
  - **Swapped:** an isolated copy of the tree in the session scratchpad, with every `report_types` and `application_functions` entry that has a `fallback_provider` swapped (all five Gemini primary), run with `PYTHONPATH` pointing at the copy so both relative and package-relative config reads hit the swapped file. Ray's live file was never modified.
  - **Real-call trap:** both runs repeated with a pytest plugin that replaces `ClaudeProvider.generate` and `GeminiProvider.generate` with a recorder that raises, to find which tests reach a real vendor class. `tests/test_ai_providers_offline.py` (which tests `generate()` itself against a mocked SDK client) and `tests/test_ai_providers_live.py` (billed by design, per its docstring) are excluded from that list.
- **Not examined:** Ollama provider tests other than those using `stubbed_manager`; the daemon process's own loaded routing.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | `stubbed_manager` copies the live file and says the routing is "the shipped ones unless `edit` changes the settings dict". No caller passes an edit that sets routing; the only edit offered is `drop_fallback`. | `tests/mocks/stub_providers.py:61-82`, `:85-91` | High |
| F2 | `stubbed_manager` replaces only the providers a test names. Every other enabled provider stays the real one, built from `.env` keys, and no `stubbed_manager` caller uses the `offline_provider_env` fixture (`tests/conftest.py:78-87`) that patches the vendor clients. A test whose stub is not on the routed path therefore calls the real vendor. | `tests/mocks/stub_providers.py:79-81` | Critical |
| F3 | Under the Claude-primary run these tests failed: `test_compare_providers::test_default_types_follow_routing`; `test_cost_display::TestMeetingsCondenseTokenLine::test_line_is_read_from_the_recorded_rows`; `test_eod_workflow::TestReportStepOutcome::test_non_interactive_failure_carries_cli_refusal_on_one_line`, `TestCondenseStepOutcome::test_recovered_fallback_is_reported_in_the_step_message`; `test_meetings_condense::TestMeetingsCondenseRefusal::test_fallback_condensation_warns_on_stderr`; `test_note_condenser::TestCondensationRefusal` (both), `TestCondensationRecording::test_condensation_records_one_row_for_its_reply`; `test_provider_foundation::TestManagerRecording` (all five); `test_report_generator::TestReportRefusal` (both), `TestReportRecording` (both). The set matches the one #236 records on `feature/issue-201-ai-cost-service`. | run output, Claude-primary | High |
| F4 | Under the Claude-primary run, the trap recorded a real `ClaudeProvider.generate` call from eleven tests: every F3 test whose stub is Gemini-only, plus `test_note_condenser::TestCondensationRecording::test_commit_failure_after_reply_still_leaves_the_row`, which **passed** while calling the real Claude API. The untrapped Claude-primary run made those calls for real and was billed for them. | trap output, Claude-primary | Critical |
| F5 | Under the swapped run, `test_narration::TestNarrationRefusal::test_cut_off_narration_returns_fallback_text` and `TestNarrationRecording::test_narration_records_one_row` failed and the trap recorded real `GeminiProvider.generate` calls from both. Without the trap, the first returned a real Gemini narration ("I have completed the pre-flight check of your workday data…"). These tests stub only Claude and inherit `daemon_narration`'s routing, which no CLI command writes. | `tests/test_narration.py:128-168`, trap output, swapped | High |
| F6 | `test_default_types_follow_routing` asserts its premise against the live routing: `expected >= {"daily_internal", "weekly_client", "note_condensation"}`, where `expected` is the call types the live file routes to Gemini. What `compare_providers._default_types` does — select the candidate's call types from the routing it is given — is routing-independent; only the premise is not. The local `_manager` already takes a `routing` argument, but it sets the primary only. | `tests/test_compare_providers.py:47-61`, `:167-186`; `scripts/compare_providers.py:73-78` | High |
| F7 | Sites that copy or read the live file but whose result does not depend on routing, confirmed by passing under both runs with no trap hit: the cap-sentinel helpers, which replace `pm.generate` before any routing is read (`test_report_generator.py:35-56`, `test_note_condenser.py:161-177`, `test_intent_parser.py:300-315`, `test_narration.py:47-66`); `test_narration.py:72-84` (entry deleted); `test_report_generator.py:101-134` (sets its own routing); schema/shape checks `test_provider_foundation.py:1015-1019`, `test_ai_foundation.py:285-300`, `test_report_generator.py:92-99`; provider-block reads in `test_ai_providers_offline.py`; `test_ai_foundation.py:263-280` (replaces both providers). `test_ai_costs.py:429-436` checks the live configuration and #236 assigns it to #132. | listed | Low |
| F8 | The suite already contains the precedent #236 cites and two more: tests that write their own settings dict and set routing themselves — `test_ai_foundation.py` `_manager_with_route`, `test_provider_foundation.py:297-334` `_make_temp_settings`/`_manager_from_dict`, `test_intent_parser.py:366-398` `_routed_manager`, `test_narration.py:90-114`. | listed | Low |
| F9 | The working-tree change to `config/ai_settings.json` carries the marks of `workmain providers set default`, not a hand edit: `last_updated` moved to `20261023`, and both `≤` characters were rewritten as `≤`, which `json.dump(data, f, indent=2)` with its default `ensure_ascii=True` produces (`providers.py:349-350`). Only `report_types` primary/fallback changed. #236's body calls it a hand edit and makes committing it an AC; `docs/DEVELOPMENT_STANDARDS.md` §2.2 § Operational changes from live use makes a CLI-written change a separate `chore(config)` commit that needs no AC and is not the issue's scope. | `git diff config/ai_settings.json`; `workmain/cli/commands/providers.py:340-350` | Medium |
| F10 | `providers.claude.notes` in the working tree reads "fallback provider for all report types and note condensation", which no longer matches the routing. | `config/ai_settings.json:20` | Low |
| F11 | #236's first AC check swaps the live `config/ai_settings.json` "for the run and restored after". During that window any `workmain` command, or a daemon restart, reads the swapped routing. The swapped run in §2 shows the same check can be made against an isolated copy of the tree without touching the live file. | `workmain/ai/provider_manager.py:438-440`; §2 Runs | Medium |
| F12 | Out of scope: `test_report_history::TestReportResend::test_resend_prompts_on_existing_file` fails when the repository path is long enough that Rich wraps "already exists" onto a new line — the terminal-width class #198 names. Seen only in the scratchpad copy. | `tests/test_report_history.py:300` | Low |

## 4. Options

The decision is how a test that uses a real `ProviderManager` states its routing. Two things have to hold for any option: the routing a test runs under comes from the test, and a misrouted call cannot reach a vendor (F2, F4, F5).

### Option A — `stubbed_manager` takes the routing as a required argument and refuses unstubbed providers

- **Approach:** `stubbed_manager(tmp_path, stubs, routing, edit=None)`. `routing` maps each call type the test exercises to its primary and fallback, and is written over the copied file's entries for those types. The helper also replaces every provider the test did not stub with one that raises on `generate()`, so a call that reaches a provider the test did not anticipate fails loudly and never reaches a vendor. The file is still the source of caps, `accepts` and the provider set, which are hand-edit-only and change on a branch with their tests. `drop_fallback` stays: it expresses "no fallback", which a routing argument can express too, so the spec chooses one form and removes the other. `test_compare_providers._manager` sets primary and fallback for every report type it relies on, and `test_default_types_follow_routing` asserts against the routing it set.
- **Pros:** Each test reads as the routing it is about. No default to fall back on, so the hidden premise cannot return through omission. Keeps the shipped caps that several assertions are about (`"16000"`, `"4000"`, `"256"` in refusal messages). Closes the real-call path for every caller at once.
- **Cons:** Every `stubbed_manager` call site changes. A test that wants a cap other than the shipped one still uses `edit`.

### Option B — keep the helper's signature; tests that care pass routing through `edit`

- **Approach:** add a `route(call_type, primary, fallback)` edit factory beside `drop_fallback`, and change only the call sites that failed in F3/F5.
- **Pros:** Fewer lines change.
- **Cons:** The helper still defaults to the live routing, so the next test written without `edit` repeats the defect — the AC "stubbed_manager no longer inherits routing from the live file" is not met. Leaves F2 open for every caller that is not changed. Fixes the failures observed under two orientations, not the dependency.

### Option C — `stubbed_manager` builds its settings from a fixed dict, not the file

- **Approach:** as F8's helpers do, write a complete settings dict in the helper.
- **Pros:** No test reads the live file at all.
- **Cons:** Changes what the refusal and recording tests are about: their assertions name the shipped caps, and those would become values the helper invents. Wider than #236, which names routing; caps are not written by any command and change only through development on a branch.

**Recommendation:** Option A. It removes the dependency rather than the failures it produced, and it closes the vendor-call path (F2) that turns a routing change into billed API calls and a passing test that called a real provider (F4). Option B leaves the default that caused the defect. Option C solves a problem the project does not have and moves assertions off the values they are about.

The standard #236's fourth AC asks for, as suggested wording for `docs/DEVELOPMENT_STANDARDS.md` §6.2 Rules: "**A test that builds a real `ProviderManager` states the routing it needs.** It passes the primary and fallback of every call type it exercises to the helper, and never relies on the routing in `config/ai_settings.json`, which the operator changes in ordinary use. A provider the test does not stub must not be reachable."

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Option A, B or C? | |
| Q2 | Should `stubbed_manager` make every provider the test does not stub raise on `generate()`, so a test can never call a real vendor through it? Recommended: yes — without it a misrouted test bills the vendor and can pass (F4). | |
| Q3 | Ray's routing change was written by `workmain providers set default` (F9). Is it committed as a §2.2 operational `chore(config)` commit, with #236's third AC removed from the issue, or committed as this issue's scope with the AC kept? Recommended: the §2.2 commit and remove the AC, because §2.2 states that a CLI-written change needs no AC and is not the issue's scope. | |
| Q4 | Is the stale `providers.claude.notes` text (F10) corrected on this branch? It is a hand edit to `config/`, so under §2.2 it is development and would be this issue's scope. | |
| Q5 | #236's first AC check swaps the live `config/ai_settings.json` during a run (F11). Should the spec run that check against an isolated copy of the tree with `PYTHONPATH` set to it, as §2 did, and the issue's check wording be changed to match? Recommended: yes — the live file is read by every `workmain` command run in that window. | |
| Q6 | The terminal-width failure in F12 needs an issue under #198 unless one of #198's children already covers `test_report_history`. Own issue, add to an existing child, or leave it to #198's conversions? | |

## 6. Disposition

- Promoted to:
- Superseded by:
