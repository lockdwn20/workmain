# Gemini Model Selection — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261009
**Branch:** `hotfix/issue-181-gemini-model-selection` (from `main`)
**Target release:** v1.42.2
**Originating item:** Issue #181
**Design study:** `../design/DESIGN_GEMINI_MODEL_SELECTION.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261009 | Ray | Design §4: how the side-by-side is produced. | Option B: one read-only comparison script that sends each provider the production prompts and writes nothing to the database. |
| 20261009 | Ray | Design Q1–Q7. | All accepted as recommended. Answers are recorded in the design study §5. |
| 20261009 | Spanner | Branch type. | `hotfix/*`: one root cause, Gemini output not comparable to Claude. Three application files: `gemini.py`, `note_condenser.py`, `config/ai_settings.json` (`docs/DEVELOPMENT_STANDARDS.md` §2.2). `scripts/`, tests and docs do not count. |
| 20261009 | Spanner | The comparison script needs the condenser's note selection, which is inline in `condense_meeting`. Copying the query into the script would create a second definition of "the notes a condensation reads". | The selection and the request build become two public `NoteCondenser` methods that `condense_meeting` itself calls. |
| 20261009 | Spanner | Which call types the script compares. | Derived from `report_types`: every entry whose `primary_provider` is the candidate provider. A fixed list in the script would be a register that goes stale at the next routing change. |
| 20261009 | Spanner | `docs/AI_SETTINGS_GUIDE.md` § Gemini-Specific Fields quotes Gemini 2.5 Flash prices, a stale copy of values `config/ai_settings.json` owns. | Deleted in Step 5. The guide states the fields, not their values. |
| 20261009 | Spanner | `GeminiProvider.__init__` defaults `cost_per_1k_*` to the same stale 2.5 Flash prices when config omits them (`gemini.py:70-71`). | Not fixed here. It joins design F9 and F11 in the one correction issue opened at close-out: all three are Gemini cost and check accuracy, and none changes the verdict. |
| 20261009 | Caliper | F1: The spec doesn't say how the script hands its `provider_manager` to the production builders. `NoteCondenser` takes the singleton (`note_condenser.py:85`), `ReportGenerator` takes it as an argument (`report_generator.py:39`), and `preview_report` calls `get_provider_for_report` and `estimate_cost`, which the §6 fake doesn't delegate. | Accepted. Step 3 states `ReportGenerator(session, provider_manager=provider_manager)` and `condenser.provider_manager = provider_manager`. The fake is replaced by a real `ProviderManager` with only `generate` replaced (F3), so there is no delegation list to keep complete. |
| 20261009 | Caliper | F2: "Read through the `ProviderManager`" names no method for listing the default call types. | Accepted. Step 3 names `get_report_type_names()` and `get_report_config(name).primary_provider` (`provider_manager.py:261`, `:277`). |
| 20261009 | Caliper | F3: `test_default_types_follow_routing` hands `compare` a real `ProviderManager`, whose `generate()` calls the live providers. With keys present, the suite would make paid API calls. | Accepted. Every `tests/test_compare_providers.py` test runs under `offline_provider_env` with a `ProviderManager` built from a temporary config copy and `generate` replaced by a recorder, as in `_stubbed_manager` (`test_note_condenser.py:157-173`). No test reaches a vendor. |
| 20261009 | Caliper | F4: DR6 lets a run that returns empty content, or stops on SAFETY or RECITATION, count as a success, so AC1.3 can read met over missing output. | Accepted. DR6 passes a run only when its content is non-empty and its reason is in the success set, `FinishReason.STOP` (Gemini) or `end_turn` (Claude). Any other reason fails, an absent one included. The test covers each case. |
| 20261009 | Caliper | F5: AC1.6's equality test passes with `condense_meeting` unchanged, so it doesn't prove production calls the two new methods. | Accepted. The test patches both methods to return sentinels and asserts that `condense_meeting` sends the sentinel request built from the sentinel notes. |
| 20261009 | Caliper | F6: AC1.2's test only checks that candidate equals baseline for `daily_internal`, so a script with its own prompt text passes. | Accepted. The test also asserts that the `daily_internal` request equals `preview_report`'s prompts and `get_max_tokens('daily_internal')` for the sentinel date. |
| 20261009 | Caliper | F7: `needs_condensation` has no callers. §2 and DR2 assumed it did without checking. | Accepted. Step 2 deletes it. |
| 20261009 | Caliper | Second pass: no test scores a skipped call type, so a `compare`/`exit_status` pair that records a skip as a pass meets every §6 test, and Step 6 could exit `0` with `weekly_client` missing. | Accepted. `test_run_outcome_sets_exit_status` adds a skip produced by `compare` itself: `types=['weekly_client']` with `SystemStateRepository.get_int` patched to return `None`. It asserts the run is recorded as skipped and `exit_status` returns `1`. |
| 20261009 | Ray | Caliper's review resolved. | Approved for implementation. |

---

## 1. Scope

**In scope:**

- `workmain/ai/providers/gemini.py`: `generate()` sends the system prompt as `system_instruction`.
- `workmain/ai/note_condenser.py`: `select_condensation_notes` and `build_condensation_request`, called by `condense_meeting`; `needs_condensation` deleted.
- `scripts/compare_providers.py`: new.
- `config/ai_settings.json` `providers.gemini`: `model`, plus Ray's four pricing fields.
- `docs/AI_SETTINGS_GUIDE.md` § Gemini-Specific Fields.
- Tests: `tests/test_ai_providers_offline.py`, `tests/test_note_condenser.py`, `tests/test_compare_providers.py` (new).
- The comparison run on 2026-10-08's data and its record in the results artifact.

**Out of scope:**

- **Gemini cost accounting** (design F9) and the stale `cost_per_1k_*` defaults in `__init__`, which go to the correction issue (Decision Log).
- **What `providers test` proves** (design F11). It checks that the request is accepted, which is all the issue's third criterion asks.
- **Any code that reads `finish_reason`** (design F10). The script reports truncation for this comparison. Making the application act on it is a separate change.
- **`max_tokens` caps.** The measured runs fit with margin (design Q4).
- **`monthly_executive` and `daemon_narration`.** They reach the new model only as fallback (design Q5).
- **Prompt and template content.**
- **The routing.** It changes only on the Q1 path in Step 6, and only through the CLI.

## 2. Verified current state

The design study's findings F1–F12 are the verified record. This spec relies on these entries, re-checked 20261009.

| Claim | Evidence |
| --- | --- |
| `generate()` prepends the system prompt to the user message and sends one-element `contents`. `_generation_config` builds the config for both request paths from the policy only. | `workmain/ai/providers/gemini.py:124-131`, `:88-101` |
| The installed `google-genai` 2.22.0 accepts `system_instruction` on `GenerateContentConfig`. A live call to `gemini-3.1-pro-preview` carrying it plus the shipped policy returned `STOP`. | Design F8, Q4 |
| `GeminiProvider` is constructed by `ProviderManager` and by tests only. These are its two entry paths. | `grep -rn "GeminiProvider(" --include=*.py .` → `tests/test_provider_foundation.py:195`, `:205`, `:239`; `tests/test_ai_providers_offline.py:284`, `:413`; the manager builds from `PROVIDER_REGISTRY` |
| No test asserts on the prepended `contents`. | `grep -n "contents" tests/test_ai_providers_offline.py tests/test_provider_foundation.py` returns no hit on a Gemini call |
| `condense_meeting` selects notes with an inline query (meeting id, the occurrence's own date, not `info-only`, not `source='condensed'`, ordered by `created_at`) and builds its `GenerationRequest` inline. | `workmain/ai/note_condenser.py:116-141` |
| `needs_condensation` repeats that filter and has no callers. | `grep -rn needs_condensation --include=*.py .` → only its definition, `note_condenser.py:278` |
| `NoteCondenser` takes the `get_provider_manager()` singleton and exposes it as `self.provider_manager`, which tests replace. `ReportGenerator` takes a `provider_manager` argument, and `preview_report` calls `get_provider_for_report`, `get_max_tokens` and `estimate_cost` on it. | `workmain/ai/note_condenser.py:85`; `tests/test_note_condenser.py:194`; `workmain/ai/report_generator.py:54-58`, `:247`, `:287-305` |
| `ProviderManager.get_report_type_names()` lists the `report_types` keys, and `get_report_config(name)` returns their routing. | `workmain/ai/provider_manager.py:261`, `:277`, `:554` |
| `_build_condensation_prompt` and `_get_system_prompt` are called only from `condense_meeting`. | `grep -rn "_build_condensation_prompt\|_get_system_prompt" --include=*.py .` → `note_condenser.py:134`, `:140` |
| Report prompts for generation and preview come from the same `prompt_builder.build_prompt` call. The client filter comes from the template's `recipient_type` through `get_client_filter`, with the client id from `SystemStateRepository.get_int('active_client_id')`. | `workmain/ai/report_generator.py:138`, `:277`; `workmain/cli/commands/reports.py:79-96`, `:117-128` |
| `ProviderManager.generate(..., provider_override=p)` sets fallback to `None`, so an override that fails raises instead of returning another provider's output. | `workmain/ai/provider_manager.py:184-192` |
| The truncation signal: `GeminiProvider` sets `metadata['finish_reason']` (`FinishReason.MAX_TOKENS` on truncation), and `ClaudeProvider` sets `metadata['stop_reason']` (`max_tokens`). Gemini's `tokens_used` includes thinking; `completion_tokens` does not. | `workmain/ai/providers/gemini.py:141-154`; `workmain/ai/providers/claude.py:151`; design F9 |
| `MeetingsRepository.get_by_date(d)` returns every meeting on `d`, cancelled included. | `workmain/database/repositories/meetings_repo.py:235` |
| `staging/reports/*` is gitignored. `email` reads only `staging/reports/{template}_*.md`. | `.gitignore:57`; `workmain/cli/commands/email.py:50` |
| `workmain` is importable from `scripts/` through the editable install. | `pip show workmain` → `Editable project location: /home/lockdwn20/Projects/workmain` |

## 3. Design rules

- **DR1:** Gemini receives a request's system prompt as `system_instruction` and its prompt as the only `contents` element, unaltered. A request with no system prompt sends no `system_instruction`. `_generation_config` stays policy-only, and `generate()` adds the system instruction to its result. `check_availability()` is unchanged.
- **DR2:** `NoteCondenser.select_condensation_notes(meeting)` is the one definition of the notes a condensation reads. `NoteCondenser.build_condensation_request(meeting, notes)` is the one builder of its `GenerationRequest`. `condense_meeting` calls both. Neither method writes. `needs_condensation`, which has no callers, is deleted.
- **DR3:** The comparison script builds every request through production code: `prompt_builder.build_prompt` (via `ReportGenerator.preview_report`) for report types, and DR2's two methods for `note_condensation`. It contains no prompt text and no note query of its own.
- **DR4:** The comparison script writes nothing to the database. It never calls `ReportGenerator.generate_report`, `condense_meeting` or any repository write, never commits, and closes its session after a rollback.
- **DR5:** Each provider gets the same `GenerationRequest` through `ProviderManager.generate(request, report_type=<type>, provider_override=<provider>)`, so no fallback can stand in for the provider named.
- **DR6:** A run passes only when it returns content that is non-empty after stripping and its finish or stop reason is in the success set: `FinishReason.STOP` (Gemini `metadata['finish_reason']`) or `end_turn` (Claude `metadata['stop_reason']`). Every other run fails, including one that raises, one with any other reason or no reason, and one whose call type was skipped. The script exits `1` when any run fails, `0` otherwise, and records every failure in its output.
- **DR7:** Comparison output contains real work content and can name the client. It is written only to the path given in `--out`, under `staging/reports/` in this spec, and is never committed or quoted in a document.
- **DR8:** `cost_per_1k_prompt_tokens`, `cost_per_1k_completion_tokens`, `cost_structure` and `notes` in `providers.gemini` are Ray's edit. The implementer sets `model` only.

For anything this spec does not cover, follow `.claude/skills/session-start/SKILL.md` § Role 3: stop, document, tell Ray.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Gemini receives the system prompt as a system instruction (DR1). In `generate()`, replace the prepend block and its comment with: `config_dict = self._generation_config(request.max_tokens)`; when `request.system_prompt` is truthy, `config_dict['system_instruction'] = request.system_prompt`; `contents = [request.prompt]`. Add the §6 Gemini tests. Commit: `fix(ai): send the system prompt to Gemini as a system instruction` | `workmain/ai/providers/gemini.py`, `tests/test_ai_providers_offline.py` |
| 2 | Condensation note selection and request build are public `NoteCondenser` methods (DR2). `select_condensation_notes(self, meeting) -> List[Note]` holds `condense_meeting`'s query verbatim, `order_by` included. `build_condensation_request(self, meeting, notes) -> GenerationRequest` returns the request `condense_meeting` builds today. `condense_meeting` replaces its inline query and request with calls to these; the rest of the method, cost tracking included, is unchanged. Delete `needs_condensation`. Add the §6 condenser tests. Commit: `refactor(ai): expose condensation note selection and request build` | `workmain/ai/note_condenser.py`, `tests/test_note_condenser.py` |
| 3 | The read-only comparison script, as specified below. Add `tests/test_compare_providers.py`. Commit: `feat(scripts): add read-only provider comparison for one date` | `scripts/compare_providers.py`, `tests/test_compare_providers.py` |
| 4 | The Gemini provider runs `gemini-3.1-pro-preview`. Set `providers.gemini.model` to `gemini-3.1-pro-preview` and nothing else. **Stop: Ray enters the four pricing fields** (DR8; expected values below). After Ray says they are entered, commit the file as one commit: `fix(config): run Gemini on gemini-3.1-pro-preview`, body stating that the pricing fields are Ray's edit. | `config/ai_settings.json` |
| 5 | The guide states Gemini's fields and no prices. In § Gemini-Specific Fields, replace the paragraph and two bullets that begin `Same fields as Claude. Gemini 2.5 Flash paid-tier pricing:` with the single line `Same fields as Claude.` Commit: `docs(ai): drop stale Gemini prices from the settings guide` | `docs/AI_SETTINGS_GUIDE.md` |
| 6 | The comparison run. Run `python scripts/compare_providers.py --date 2026-10-08 --out staging/reports/provider_comparison_20261008.md` from the repository root and record its exit status and summary table. Give Ray the output path. Ray reads the output and states his verdict and its reason. **If Ray judges it not comparable** (design Q1): Ray routes each of the three types with `workmain providers set default <type> claude --fallback gemini`, and the CLI-written `config/ai_settings.json` is committed as `chore(config)` (`docs/DEVELOPMENT_STANDARDS.md` §2.2 § Operational changes). No commit otherwise; the output is never committed (DR7). | — |
| 7 | The results artifact, `docs/dev/results/GEMINI_MODEL_SELECTION_RESULTS.md`. §5 holds one row per model tested: model id, date of data, script exit status, and verdict with reason. The verdict cell reads `Awaiting Ray` until Ray fills it. | `docs/dev/results/GEMINI_MODEL_SELECTION_RESULTS.md` |

**Step 3: `scripts/compare_providers.py`.**

- **Arguments:** `--date YYYY-MM-DD` (required); `--out PATH` (required); `--candidate` (default `gemini`); `--baseline` (default `claude`); `--types` (comma-separated, optional).
- **Call types:** `--types` when given. Otherwise every name from `provider_manager.get_report_type_names()` whose `provider_manager.get_report_config(name).primary_provider.value` is `--candidate`. With today's config that is `daily_internal`, `weekly_client` and `note_condensation`.
- **One manager:** the `provider_manager` given to `compare` is the one every builder and every send uses. Build the report generator as `ReportGenerator(session, provider_manager=provider_manager)` and the condenser as `NoteCondenser(session)` followed by `condenser.provider_manager = provider_manager`. `main()` passes `get_provider_manager()`.
- **Requests:**
  - A report type: load its template's `recipient_type` and derive `(filter_client, client_id)` with `workmain.cli.commands.reports.get_client_filter` and the active client id. If a client is required and none is active, the type is skipped (DR6). Otherwise take `system_prompt` and `user_prompt` from `ReportGenerator.preview_report(template_name=<type>, report_date=<date>, filter_client=..., client_id=...)` and build `GenerationRequest(prompt=user_prompt, system_prompt=system_prompt, max_tokens=provider_manager.get_max_tokens(<type>))`, the same three fields `generate_report` sends.
  - `note_condensation`: one request per meeting from `MeetingsRepository.get_by_date(<date>)` for which `select_condensation_notes` returns at least one note, built by `build_condensation_request`. A meeting with no qualifying notes takes the condenser's no-AI path in production and is not compared.
- **Sending:** for each request, the candidate first and then the baseline, each per DR5. An exception is recorded against that run and the script continues.
- **Output:** a Markdown file with one section per request (call type, plus meeting title for condensation). Under each section, one subsection per provider giving response model, prompt tokens, completion tokens, thinking tokens (`tokens_used − prompt_tokens − completion_tokens`), finish or stop reason, and the content in a fenced block, or the error. The file ends with a summary table, one row per run, which is also printed to stdout.
- **Structure:** testable functions `compare(session, report_date, candidate, baseline, types, provider_manager) -> list` and `exit_status(runs) -> int` (DR6), and a `main()` that opens a session with `get_db().get_session()`, calls them, and rolls back and closes the session in `finally` (DR4). PEP 257 module docstring stating that the script is read-only, plus Google-style docstrings and type hints (`docs/DEVELOPMENT_STANDARDS.md` §3).

**Step 4 expected pricing values for Ray** (Google, ai.google.dev/gemini-api/docs/pricing, fetched 20261009; ≤ 200k-token tier, design Q7):

- `cost_per_1k_prompt_tokens`: `0.002`
- `cost_per_1k_completion_tokens`: `0.012`
- `cost_structure`: `$2.00/MTok prompt, $12.00/MTok completion (prompts ≤ 200k tokens)`
- `notes`: `Gemini 3.1 Pro Preview - $2.00/MTok input, $12.00/MTok output at ≤ 200k-token prompts; $4.00/$18.00 above, not modelled`

### Authorization points

None. No migration, no GitHub object deletion, no force-push, no service run-state change. Step 4's pricing stop and Step 6's verdict are Ray's inputs, not authorization points. The merge to `main` and the post-merge restart belong to `/closeout`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Every report type routed to the Gemini provider produces output comparable to `claude-sonnet-5`'s for the same inputs. | Ray reads `staging/reports/provider_comparison_20261008.md` from Step 6, comparing the `gemini-3.1-pro-preview` and `claude-sonnet-5` output for `daily_internal`, `weekly_client` and each `note_condensation` meeting, and states his verdict |
| AC1.2 | The side-by-side compares like with like: both providers got the same request, built by production code, for every compared call type, and no output came from a fallback. | `pytest tests/test_compare_providers.py::TestCompareProviders::test_each_provider_receives_identical_request` |
| AC1.3 | No compared output was truncated, blocked or missing: every run returned non-empty content and finished on its provider's normal stop reason. | Step 6's run exits `0`, recorded in the results artifact with its summary table |
| AC1.4 | Gemini receives the system prompt as a system instruction and the prompt unaltered, through both entry paths that build the provider. | `pytest tests/test_ai_providers_offline.py::TestGeminiPolicyPayload::test_gemini_system_prompt_sent_as_system_instruction tests/test_ai_providers_offline.py::TestProviderManagerBuildsFromConfig::test_gemini_shipped_provider_sends_system_instruction` |
| AC1.5 | The comparison leaves live data untouched: no write, no commit. | `pytest tests/test_compare_providers.py::TestCompareProviders::test_comparison_writes_nothing` |
| AC1.6 | Production condensation sends the request the comparison builds, so the condensation comparison reflects what production sends. | `pytest tests/test_note_condenser.py::TestCondensationRequest::test_condense_meeting_sends_built_request` |
| AC1.7 | The application suite passes with no net test loss. | Bare `pytest` from the repository root, keys present |
| AC2.1 | The Gemini provider's configured model is the selected, non-Flash model. | `jq -r .providers.gemini.model config/ai_settings.json` prints `gemini-3.1-pro-preview` |
| AC3.1 | The selected model accepts every setting the Gemini request policy sends. | Ray runs `workmain providers test gemini` on the branch and it reports success |
| AC4.1 | Every Gemini model tested is recorded with its verdict and why, so a rejected model is not tested again. | Ray reads §5 of `docs/dev/results/GEMINI_MODEL_SELECTION_RESULTS.md` for each tested model's verdict and reason |

If Ray's AC1.1 verdict is "not comparable", AC2.1 cannot be met as worded. Close-out restates it per design Q1, and AC1.1 records the verdict.

## 6. Test plan

- **Baseline before this work:** 1155 passed, 0 failed, 0 skipped, keys present — v1.42.1 `CHANGELOG.md`; re-observe on this branch before Step 1.
- **Expected after:** 1164 passed, 0 failed, 0 skipped, keys present. Nine tests added, none removed.

**`tests/test_ai_providers_offline.py`:**

- `TestGeminiPolicyPayload::test_gemini_system_prompt_sent_as_system_instruction`: built with `_build_gemini` and `_fake_gemini_response`. `generate(GenerationRequest(prompt="USER", system_prompt="SYS", max_tokens=20))`, then assert the call's `config.system_instruction == "SYS"` and `contents == ["USER"]`.
- `TestGeminiPolicyPayload::test_gemini_no_system_prompt_sends_no_system_instruction`: the same with no system prompt. Assert `config.system_instruction is None` and `contents == ["USER"]`.
- `TestProviderManagerBuildsFromConfig::test_gemini_shipped_provider_sends_system_instruction`: `ProviderManager().get_provider('gemini')` under `offline_provider_env`, mock response set up as in `test_gemini_shipped_policy_sends_no_sampling`. Assert the same as the first test.

**`tests/test_note_condenser.py`**, new class `TestCondensationRequest`, `db_session`, sentinel meeting at `_MEETING_START`:

- `test_select_condensation_notes_filters`: seed one qualifying note, one `info-only` note, one `source='condensed'` note, and one note on the same meeting dated a different day. Assert the method returns only the qualifying note.
- `test_condense_meeting_sends_built_request`: use `_stubbed_manager`. Patch `select_condensation_notes` to return a sentinel list (one stand-in with `tags=['client-report']`) and `build_condensation_request` to return a sentinel `GenerationRequest`. Assert that `build_condensation_request` was called with the meeting and the sentinel list, and that the request `condense_meeting` sends is the sentinel.

**`tests/test_compare_providers.py`**, new. Load the script with `importlib.util.spec_from_file_location`. Every test runs under `offline_provider_env` with `db_session`, a sentinel date (`date(2099, 6, 5)`) and a seeded meeting with one qualifying note. The manager is a real `ProviderManager(config_path=<temporary copy of config/ai_settings.json>)` with only `generate` replaced, as in `_stubbed_manager`, by a recorder that stores `(request, report_type, provider_override)` and returns a `GenerationResponse` the test sets. No test reaches a vendor. Class `TestCompareProviders`:

- `test_each_provider_receives_identical_request`: `types=['daily_internal', 'note_condensation']`. For each request, the candidate's call and the baseline's call carry equal `prompt`, `system_prompt` and `max_tokens`, and `provider_override` names candidate then baseline. The `daily_internal` request's `system_prompt` and `prompt` equal `ReportGenerator(db_session, provider_manager=pm).preview_report('daily_internal', <sentinel date>)`'s `system_prompt` and `user_prompt`, and its `max_tokens` equals `pm.get_max_tokens('daily_internal')`. The `note_condensation` request equals `build_condensation_request` for the seeded meeting.
- `test_comparison_writes_nothing`: patch `db_session.commit` with a mock. After `compare`, assert the mock was not called and that `db_session.new`, `.dirty` and `.deleted` are empty.
- `test_run_outcome_sets_exit_status`: `exit_status(runs)` is `0` when every response has content and `FinishReason.STOP` or `end_turn`. It is `1` for each of these: `FinishReason.MAX_TOKENS` with content, `FinishReason.SAFETY` with empty content, `FinishReason.STOP` with empty content, no reason in `metadata`, a recorder that raises, and a skipped call type. The skip comes from `compare(..., types=['weekly_client'])` with `SystemStateRepository.get_int` patched to return `None`, so the recorder is never called and the run is recorded as skipped.
- `test_default_types_follow_routing`: with `types=None`, the call types in the returned runs, skipped ones included, are exactly the `report_types` entries whose `primary_provider` is the candidate. Changing one entry's primary in the copy changes the set.

## 7. Risks and rollback

- **A preview model can be withdrawn at short notice** (design F1, `gemini-2.5-pro`'s 404). A withdrawal makes Gemini calls fail, and `fallback_mode: auto` sends the three types to Claude. Recovery is a config edit of `model`.
- **System-instruction delivery changes Gemini output on every routed call type**, which is the point. It applies equally to the fallback paths for `monthly_executive` and `daemon_narration`.
- **Cost rises about 2.7× per token** against Flash (design F12), and recorded cost stays understated until the correction issue is fixed (design F9).
- **Rollback:** revert Steps 5, 4, 3, 2, 1 in that order. None touches the database. The daemon picks up reverted code and config at its next restart. A Step 6 routing change is reverted with `providers set default`.
