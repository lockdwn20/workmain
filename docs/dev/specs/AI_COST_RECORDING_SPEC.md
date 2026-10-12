# AI Cost Recording — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261011
**Branch:** `feature/issue-191-ai-cost-recording` (from `dev`)
**Target release:** v1.45.0 (set by `/closeout`)
**Originating item:** Issue #191
**Design study:** `../design/DESIGN_AI_COST_RECORDING.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261011 | Ray | Study Q1: the status check on Claude and Gemini is a paid generation request. Make it free, a simple ping, rather than recording it. | Taken — DR14, Step 5. |
| 20261011 | Ray | Study Q2: all costs belong in one central table that other modules reference and add to. `ai_costs` becomes the only record of cost, and report metadata stops carrying cost. | Taken — DR11, DR12, Steps 1, 4, 6, 7. |
| 20261011 | Ray | The Gemini re-send (a paid reply discarded and the request sent again when reading the reply raises) belongs with provider retry behaviour. | Added to #125 as an acceptance criterion. Out of scope here. |
| 20261011 | Spanner | Study design item 3 placed the test recorder on the `ProviderManager` instance. Three test files construct managers directly (`ProviderManager(`), so each would have to remember to set it, and one that forgot would write to the live database. | Changed: an autouse fixture in `tests/conftest.py` blocks the recording service's database access for every test, and a test that checks recording opts in with `session_for_command` (DR6). |
| 20261011 | Spanner | `reports save` and `providers test` each print one reply's tokens as "prompt / completion", where completion includes thinking. The study's item 10 covered only the `meetings condense` line. | Same reason as item 10, so they are in scope: every line that prints one call's tokens shows prompt, answer and thinking (DR16). |
| 20261011 | Spanner | Migration in two parts. A rename of the stored type, or removing cost from report metadata, while code that still writes the old shape is running would leave rows that need fixing again. | `025` is additive and runs in Step 1. `026` renames and strips, runs in Step 7, and is safe to run again (DR10, DR12). |

---

## 1. Scope

**In scope:**

- A recording service, `workmain/services/ai_cost_service.py`, the only code outside the repository that writes `ai_costs` (DR1–DR4).
- `ProviderManager.generate` records every reply a provider returns, including a rejected primary reply and a fallback reply, and hands the row ids back to the caller (DR5).
- The three caller-side writes in `report_generator.py`, `note_condenser.py` and `intent_parser.py` are removed. Report generation links its rows to the saved report, and condensation passes its meeting (DR8, DR9).
- `workmain providers test` records its reply (DR15).
- `ai_costs` gains `refused` and `finish_reason`, stores the call type as its type, and drops its CHECK constraint. Migrations `025` and `026` (DR7, DR10).
- `ai_costs` becomes the only record of cost. Migrations copy across what only the reports hold, then remove cost from report metadata. `ReportsRepository.create` stops writing cost (DR11, DR12).
- `CostTracker` is removed (DR13).
- `check_availability` on Claude and Gemini becomes a model lookup that generates nothing (DR14).
- The four cost commands, and the per-call token lines printed by `meetings condense`, `reports save` and `providers test`, show prompt, answer and thinking separately (DR16–DR18).
- Dead code that reads report cost (DR19).
- Tests that the above changes reach (§2 enumerations, §6).

**Out of scope:**

- The Gemini re-send on a post-reply error — #125.
- Test rows already in the live `ai_costs` table, and test isolation generally — #136. This spec removes one leak path (intent parse's own session) and adds none (DR6).
- Ollama's availability check, and Ollama checking availability before every request — #152. Ollama's check is already a free model listing.
- Who owns retry in each provider, and the configured timeout — #125, #114.
- Back-filling thinking counts on old rows. Rows written before migration 024 keep `thinking_tokens` `NULL` (#149's decision).
- Removing `meetings costs` or `notes costs`. They are the same command, and they share a renderer here (DR17). Removing either one is a CLI change the issue doesn't ask for.
- The report's provider, fallback reason, run time and file path. These stay in report metadata, because they are facts about the report, read by EOD and the reports commands (DR11).

## 2. Verified current state

Verified 20261011 on `feature/issue-191-ai-cost-recording` at `0667206`. The study's §3 carries the full evidence. Line numbers are at that commit.

### The write path

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| `ProviderManager.generate(request, report_type=None, provider_override=None)` returns `(GenerationResponse, Optional[FallbackNotice])`. It calls `provider.generate(request)` then `require_complete(...)` for the primary. On `ProviderError` or `RateLimitError`, which includes `IncompleteResponseError`, it calls the fallback the same way when the mode is auto. | `workmain/ai/provider_manager.py:178-261` |
| `IncompleteResponseError(GenerationError)` carries `call_type, max_tokens, provider, finish_reason`, not the reply. `require_complete` raises it for `FinishStatus.CUT_OFF`, `FinishStatus.STOPPED`, or empty `content`. | `workmain/ai/base_provider.py:279-296`, `:298-330` |
| `GenerationResponse` fields: `content, provider, model, tokens_used, prompt_tokens, completion_tokens, thinking_tokens, cost, finish, finish_reason`, then `metadata: Optional[Dict] = None`. A dataclass. | `base_provider.py:64-95` |
| Callers of `ProviderManager.generate`, found by `git grep -n '\.generate(' -- workmain scripts` excluding provider-level calls. | `workmain/ai/report_generator.py:155`; `workmain/ai/note_condenser.py:175`; `workmain/ai/intent_parser.py:80`, `:183`, `:229`; `workmain/daemon/narration.py:83`; `scripts/compare_providers.py:117` |
| Provider-level `generate` calls that bypass the manager. | `workmain/cli/commands/providers.py:152` (`providers test`) |
| `AiCostRepository.create(interaction_type, provider, model, prompt_tokens, completion_tokens, thinking_tokens, total_tokens, cost_usd, generation_time_s=None, report_id=None, meeting_id=None, context_label=None)` adds the row, commits the session it was given, and refreshes the row. | `workmain/database/repositories/ai_costs_repo.py:21-75` |
| `AiCostRepository` and its getter, found by `git grep -n 'AiCostRepository\|get_ai_cost_repository' -- workmain scripts automation tests`. Writers: report generator, condenser, intent parser. Readers: `meetings costs`, `notes costs`, `providers costs`. Tests: `test_ai_costs.py` throughout; `test_ai_arguments.py:177` and `test_provider_foundation.py:501` patch the getter in a command module. | `report_generator.py:215-216`; `note_condenser.py:17`, `:196`; `intent_parser.py:109-112`; `cli/commands/meetings.py:20`, `:1765`; `cli/commands/notes.py:22`, `:1053`; `cli/commands/providers.py:23`, `:228` |
| Report generation calls `generate`, saves the report with `reports_repo.create(...)` (which commits), then writes `ai_costs` in `self.session` with `report_id=db_report.id, context_label=template_name, generation_time_s=generation_time`. | `report_generator.py:155-227`; `reports_repo.py:102-106` |
| Condensation calls `generate`, commits the summary, then writes `ai_costs` in `self.session` with `meeting_id, context_label=db_meeting.title`. `condense_meeting` returns `(summary, resolved_tags, notice)` on both paths. | `note_condenser.py:131-212` |
| `condense_meeting` callers, found by `git grep -n 'condense_meeting(' -- workmain scripts tests`. | `cli/commands/meetings.py:872`; `cli/commands/notes.py:668`; `tests/test_note_condenser.py:115`, `:140`, `:202`, `:229`, `:289`, `:330`, `:346`, `:368` |
| Intent parse opens its own session through `get_db()` imported inside the function, writes `ai_costs` only after `json.loads` succeeds and `action` is present, inside `try/except Exception` that logs a warning. `parse_task_match` and `parse_note_duplicate` write nothing. Narration writes nothing. | `intent_parser.py:80-126`, `:183`, `:229`; `daemon/narration.py:64-87` |
| `providers test` calls `client.check_availability()`, then `client.generate(request)` with `max_tokens=512`, then `require_complete(response, "providers test", 512, None)`, and prints `Tokens: {tokens_used} (prompt: …, completion: …)`. | `cli/commands/providers.py:105-177` |
| `get_db().get_session()` returns a new session each call over an engine with `poolclass=NullPool`. | `workmain/database/connection.py:48-62` |

### The table

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| `AiCost` declares `CheckConstraint("interaction_type IN ('report', 'condensation', 'intent_parse')", name='ai_costs_interaction_type_check')`. Columns: `id, interaction_type, provider, model, prompt_tokens, completion_tokens, total_tokens, thinking_tokens, cost_usd, generation_time_s, report_id, meeting_id, context_label, created_at`. Live, the constraint exists, with FKs `report_id → reports(id)` and `meeting_id → meetings(id)`, both `ON DELETE SET NULL`. | `workmain/database/models.py:414-445`; live `pg_constraint` 20261011 |
| Latest migration is `024`. Migrations are SQL files run with `psql -U workmain_user -d workmain -f <file>`. | `workmain/database/migrations/024_ai_costs_thinking_tokens.sql`; #149 spec §3 |
| Live 20261011: report rows carry `context_label` `daily_internal` (171) or `weekly_client` (78), and on every row with a report link it equals `reports.report_type`. One report row (id 2549) has no report link. | live query |
| Call types configured: `daily_internal, weekly_client, monthly_executive, note_condensation, daemon_narration, intent_parse, task_match, note_dedup`. | `config/ai_settings.json` `report_types`, `application_functions` |
| Live 20261011: `reports.metadata` is `jsonb`. Of 248 reports with a cost row, provider, prompt, completion and cost match. Model is `NULL` on the cost row for the 102 back-filled reports. Total differs on 9, and in all 9 the report's total is the larger one: Gemini's own total, which includes thinking. 3 reports have no cost row: #136's test reports. | live query; study F14, F15 |

### Report cost metadata

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| `ReportsRepository.create(report_type, report_date, content, ai_provider, ai_model, prompt_tokens, completion_tokens, thinking_tokens, total_tokens, cost, generation_time, file_path=None, client_id=None, fallback_reason=None)` builds metadata from all of these. One caller. | `reports_repo.py:30-106`; `report_generator.py:194` |
| Readers of report metadata, found by `git grep -n 'report_metadata' -- workmain`: file path (`reports.py:482`, `report_generator.py:493-495`, `eod_workflow.py:1054`); provider and fallback reason (`eod_workflow.py:980-997`); cost, total tokens and provider (`reports costs`, `reports.py:814-856`); `Report.ai_provider`, `.cost`, `.total_tokens` (`models.py:393-411`); `ReportsRepository.get_cost_summary` (`:333-404`) and `.get_costs_by_date` (`:413-450`). | as listed |
| No caller exists for `ReportGenerator.get_cost_summary`, `ReportsRepository.get_cost_summary`, `ReportsRepository.get_costs_by_date`, or the three `Report` properties, found by `git grep -n 'get_cost_summary\|get_costs_by_date\|\.ai_provider\b\|\.cost\b\|\.total_tokens\b' -- workmain scripts`. | the definitions only; `report_generator.py:513` is the one call of the repository method, inside the dead method |
| Tests that assert report cost metadata or `ai_costs` writes: `test_report_generator.py:305-328` (`TestReportThinkingTokens`), `test_note_condenser.py:355-372` (`TestCondensationThinkingTokens`), `test_intent_parser.py:460-486` (`TestIntentParseThinkingTokens`, using `session_for_command('workmain.database.connection')`). | as listed |

### `CostTracker`

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| Users, found by `git grep -n 'CostTracker\|cost_tracker\|get_cost_tracker\|SectionCost\|ReportCost\|CostCategory' -- workmain scripts tests automation`: the module itself; `workmain/ai/__init__.py:30-35`, `:76-80`; `report_generator.py:27`, `:30`, `:59`, `:71`, `:79`, `:127`, `:162`, `:212`, `:249`; `note_condenser.py:15`, `:83`, `:171`, `:181`, `:212`; `meetings.py:876-877` (its one reader, through `_last_completed`); `tests/test_ai_foundation.py:23-26`, `:149` (`test_cost_tracker`); `tests/test_ai_providers_live.py:21`, `:149` (`test_cost_tracking_integration`); `cost_tracker=MagicMock()` at `tests/test_ai_arguments.py:205`, `tests/test_prompt_builder_data_sources.py:140`, `tests/test_report_generator.py:198`. | as listed |
| `ReportGenerator(session, …, cost_tracker=None, …)` and `NoteCondenser(session)` construction sites in `workmain` and `scripts`: `report_generator.py:550`, `note_condenser.py:325`, `scripts/compare_providers.py:91`, `:156`. None passes `cost_tracker`. | as listed |

### Availability check

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| Claude `check_availability` sends `messages.create(**self._base_api_params(1), messages=[{"role": "user", "content": "test"}])`. It maps `AnthropicRateLimitError` to `RATE_LIMITED`, `APIError` to `ERROR`, and any other exception to `UNAVAILABLE`. | `workmain/ai/providers/claude.py:263-288` |
| Gemini `check_availability` sends `models.generate_content(model, ["test"], GenerateContentConfig(**self._generation_config(100)))`. It maps a rate-limit `APIError` to `RATE_LIMITED`, other `APIError`s to `UNAVAILABLE`, and any other exception to `UNAVAILABLE`. | `workmain/ai/providers/gemini.py:307-333` |
| `anthropic` 1.3.0 has `client.models.retrieve(model_id)`. `google-genai` 2.22.0 has `client.models.get(model=...)`. | installed SDK signatures, 20261011 |
| Callers of `check_availability` / `test_connection` on Claude or Gemini: `providers status` (`providers.py:86`), `providers test` (`:137`), `BaseProvider.test_connection` (`base_provider.py:222-226`). `IntentParser.is_available` routes only to Ollama in the shipped config. | as listed; `intent_parser.py:39-56` |
| Tests calling Claude or Gemini `check_availability`, found by `git grep -n 'check_availability()' -- tests`: in `test_ai_providers_offline.py`, `test_claude_payload_check_availability_identical_contract` (`:138`), `test_claude_check_availability_carries_thinking_policy` (`:160`), `test_gemini_policy_sampling_key_not_sent` (`:309`), `test_gemini_check_availability_carries_policy` (`:365`), `test_gemini_check_availability_carries_afc` (`:389`), `test_check_availability_429_and_500` (`:501`), `test_gemini_shipped_policy_sends_no_sampling` (`:520`), `test_gemini_shipped_policy_takes_sdk_direct_path` (`:566`); `test_ai_foundation.py::test_provider_status` (`:311`); `test_ai_providers_live.py::test_provider_available` (`:91`). | as listed |
| `docs/AI_SETTINGS_GUIDE.md` says a provider declares `REQUIRED_POLICY_KEYS` "If `generate()` or `check_availability()` reads any policy key". | `docs/AI_SETTINGS_GUIDE.md:201` |

### Displays

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| `AiCostRepository.get_summary` returns `total_cost, total_tokens, total_calls, by_provider{calls,cost,tokens}, by_type{calls,cost,tokens}`, summing `total_tokens` only. `get_filtered` returns rows by `created_at` descending. | `ai_costs_repo.py:77-178` |
| `providers costs` prints the summary and two aggregate tables (provider, type) with one Tokens column. `meetings costs` and `notes costs` filter `interaction_type='condensation'` and print a summary, a by-provider table and a per-row table; they differ only in title, detail heading and help text. `reports costs` lists up to 500 reports, filters in Python on `report_date`, provider and type, and reads `cost` and `total_tokens` from metadata. | `providers.py:179-305`; `meetings.py:1716-1850`; `notes.py:1004-1140`; `reports.py:741-870` |
| `meetings condense` prints `Cost: ${total_cost:.6f} ({total_tokens} tokens)` from `CostTracker._last_completed`. `reports save` prints `Tokens: {tokens_used} (prompt: …, completion: …)` from the `generate_report` result dict. | `meetings.py:872-888`; `reports.py:206-207`; `report_generator.py:230-244` |
| Each command opens its session through its own module's `get_db`, so `session_for_command('<module>')` reaches it. | `meetings.py:1762-1763`; `notes.py:1050-1051`; `providers.py:225-226`; `reports.py:791-792`; `tests/conftest.py:45-65` |
| Tests that patch a command module's cost repository with a fixed summary dict: `test_ai_arguments.py:122-125`, `:170-180`; `test_provider_foundation.py:495-507`. | as listed |

### Tests that run the real `generate`

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| Files constructing `ProviderManager(` and calling `.generate(` on it: `test_ai_foundation.py`, `test_ai_providers_offline.py`, `test_provider_foundation.py`, `test_ai_providers_live.py`; plus every user of `tests/mocks/stub_providers.py` `stubbed_manager`. | `git grep -c 'ProviderManager(\|\.generate(' -- tests` |
| `session_for_command(module)` patches `<module>.get_db` to return `db_session` and makes its `close()` a no-op. | `tests/conftest.py:45-65` |

**Not verified:** that `models.retrieve` and `models.get` are unbilled. They are metadata reads that generate no tokens, and both vendors bill tokens. No invoice was checked.

## 3. Design rules

### Recording

- **DR1 — One recording service.** New module `workmain/services/ai_cost_service.py`, with `from workmain.database.connection import get_db` at module level. It has two public functions. No other module outside `ai_costs_repo.py` constructs `AiCostRepository` or calls a write method on it.
- **DR2 — `record_reply(response, call_type, *, refused, generation_time_s, meeting_id=None, context_label=None) -> Optional[int]`.** Opens a session with the `docs/DEVELOPMENT_STANDARDS.md` §4.1 pattern (`get_db()`, `db.get_session()`, `try/finally: session.close()`). Calls `AiCostRepository.create` with `interaction_type=call_type`, `provider=response.provider.value`, `model=response.model`, the reply's `prompt_tokens`, `completion_tokens`, `thinking_tokens`, `total_tokens=response.tokens_used`, `cost_usd=response.cost`, `generation_time_s`, `refused`, `finish_reason=response.finish_reason`, `meeting_id`, `context_label`. Returns the new row's id.
- **DR3 — `link_report(cost_record_ids, report_id) -> None`.** Opens its own session the same way and calls `AiCostRepository.link_report(cost_record_ids, report_id)`, which sets `report_id` on those rows and commits. An empty list does nothing and opens no session.
- **DR4 — Recording never fails the call.** Both functions catch `Exception`, log `logger.warning` naming the call type (or report id) and the error, and return `None`. The session is closed in `finally` whether or not it was opened successfully.
- **DR5 — `ProviderManager.generate` records every reply.**
  - Signature: `generate(request, report_type=None, provider_override=None, meeting_id=None, context_label=None)`. Return type unchanged.
  - `GenerationResponse` gains `cost_record_ids: List[int] = field(default_factory=list)`, declared after `metadata`. Providers do not set it. Its docstring says it holds the `ai_costs` ids `generate` recorded during the call that returned this reply.
  - For each provider tried, `generate` times `provider.generate(request)` with `time.monotonic()`. Once it returns, `generate` calls `require_complete`. If that raises `IncompleteResponseError`, it records the reply with `refused=True` and re-raises. Otherwise it records with `refused=False`. Both call `ai_cost_service.record_reply` with the call type `report_type`, the elapsed seconds, and the `meeting_id` and `context_label` it was given. The service is referenced as a module attribute, so a test can patch it.
  - Each non-`None` id returned is appended to one list local to the call. The reply that `generate` returns carries that whole list, so a fallback reply's list holds the refused primary's id first, then its own.
  - A provider call that raises before returning a reply records nothing.
  - The existing fallback control flow, messages and `FallbackNotice` are unchanged.
- **DR6 — Tests never record to the live database.** `tests/conftest.py` gains an autouse fixture that monkeypatches `workmain.services.ai_cost_service.get_db` with a function raising `RuntimeError("tests do not record AI costs to the live database")`. Every test that reaches the service then takes DR4's warning path. A test that checks a recorded row calls `session_for_command('workmain.services.ai_cost_service')`, which replaces that patch for the test, so the row lands in `db_session` and is rolled back.

### The table

- **DR7 — `AiCost` model.** Remove the `CheckConstraint` and its `__table_args__`. Add `refused = Column(Boolean, nullable=False, default=False, server_default=text('false'))` and `finish_reason = Column(String(50), nullable=True)`. The docstring's list of `interaction_type` values becomes: "the call type, as named in config/ai_settings.json, or `providers_test`". `AiCostRepository.create` gains required keyword arguments `refused: bool` and `finish_reason: Optional[str]` after `cost_usd`, and its `interaction_type` docstring says the same. It gains `link_report(ids: List[int], report_id: int) -> None`, `get_by_ids(ids: List[int]) -> List[AiCost]` and `get_report_costs(provider, report_type, start_date, end_date) -> List[Tuple[AiCost, Report]]` (DR18). The model changes land only after migration `025` has been executed (§4 authorization point), because an ORM insert names every mapped column.
- **DR8 — Callers pass what only they know, and write no cost row.**
  - `report_generator.py`: remove the `AiCostRepository` write. After `reports_repo.create` returns, call `ai_cost_service.link_report(response.cost_record_ids, db_report.id)`.
  - `note_condenser.py`: remove the write and its import. Pass `meeting_id=db_meeting.id, context_label=db_meeting.title` to `generate`. `condense_meeting` returns `(summary, resolved_tags, notice, cost_record_ids)`: the reply's `cost_record_ids` on the AI path, `[]` on the "Attended …" path. Its docstring states the fourth element.
  - `intent_parser.py`: remove the write block (`:106-124`).
  - `narration.py`, `parse_task_match` and `parse_note_duplicate` change nothing. `generate` records for them.
- **DR9 — The callers of `condense_meeting`** unpack four values: `meetings.py:872` (DR16 reads the ids), and `notes.py:668`, which ignores them as `_`.
- **DR10 — Migration `025_ai_costs_recording.sql`** (Step 1), with a header in `024`'s form, in one transaction:
  1. `ALTER TABLE ai_costs DROP CONSTRAINT IF EXISTS ai_costs_interaction_type_check;`
  2. `ALTER TABLE ai_costs ADD COLUMN IF NOT EXISTS refused BOOLEAN NOT NULL DEFAULT FALSE;`
  3. `ALTER TABLE ai_costs ADD COLUMN IF NOT EXISTS finish_reason VARCHAR(50);`
  4. Copy the model from the report where the cost row has none: `UPDATE ai_costs a SET model = r.metadata->>'ai_model' FROM reports r WHERE a.report_id = r.id AND a.model IS NULL AND r.metadata ? 'ai_model';`
  5. Copy the report's total where it is larger: `UPDATE ai_costs a SET total_tokens = (r.metadata->>'total_tokens')::int FROM reports r WHERE a.report_id = r.id AND r.metadata ? 'total_tokens' AND (r.metadata->>'total_tokens')::int > a.total_tokens;`

  Code still running from `dev`, including the daemon, keeps working: it writes the old type values, which are still valid, and omits the new columns, which have defaults. The statements are safe to run again.

### One record of cost

- **DR11 — Report metadata carries no cost.** `ReportsRepository.create` drops the parameters `ai_model, prompt_tokens, completion_tokens, thinking_tokens, total_tokens, cost`. Its metadata keeps `ai_provider` and `generation_time`, plus `file_path` and `fallback_reason` when given. `report_generator.py:194` passes only those. The `generate_report` result dict is unchanged, apart from DR16's added `thinking_tokens` key: it reports the reply, not stored metadata.
- **DR12 — Migration `026_ai_costs_single_record.sql`** (Step 7), with a header in `024`'s form, in one transaction:
  1. `UPDATE ai_costs SET interaction_type = context_label WHERE interaction_type = 'report' AND context_label IS NOT NULL;`
  2. `UPDATE ai_costs SET interaction_type = 'note_condensation' WHERE interaction_type = 'condensation';`
  3. Strip cost from reports that have a cost row: `UPDATE reports r SET metadata = r.metadata - 'ai_model' - 'prompt_tokens' - 'completion_tokens' - 'thinking_tokens' - 'total_tokens' - 'cost' WHERE EXISTS (SELECT 1 FROM ai_costs a WHERE a.report_id = r.id);`

  It is safe to run again, and running it again corrects any row an older process wrote between its first run and the post-merge restart. Reports with no cost row (#136's three test reports) keep their metadata.
- **DR13 — `CostTracker` is removed.** Delete `workmain/ai/cost_tracker.py` and its five exports from `workmain/ai/__init__.py`. Remove every use listed in §2, including the `cost_tracker` constructor parameter of `ReportGenerator`. Delete `test_cost_tracker` and `test_cost_tracking_integration`, and their imports. Remove the `cost_tracker=MagicMock()` keyword at the three test sites.

### Availability check

- **DR14 — The status check generates nothing.** Claude: `check_availability` calls `self.client.models.retrieve(self.model)`. Gemini: it calls `self.client.models.get(model=self.model)`. Each keeps its existing exception-to-status mapping (§2) and its `_set_status` calls. `_base_api_params` and `_generation_config` remain, used by `generate` only. Their docstrings drop "and check_availability()". `docs/AI_SETTINGS_GUIDE.md:201` reads "If `generate()` reads any policy key". The eight offline tests in §2 are handled as follows:
  - Each one that asserts the availability request's payload (`…identical_contract`, `…carries_thinking_policy`, `…carries_policy`, `…carries_afc`) is deleted. The payload it pinned is no longer sent, and each has a `generate` counterpart that stays.
  - Each one that counts `generate_content` calls including the availability call (`test_gemini_policy_sampling_key_not_sent`, `test_gemini_shipped_policy_sends_no_sampling`, `test_gemini_shipped_policy_takes_sdk_direct_path`) drops its `check_availability()` call and asserts against the `generate` call alone.
  - `test_check_availability_429_and_500` raises its errors from `models.get` instead of `generate_content`.

  `test_provider_status` and `test_provider_available` stay as they are.
- **DR15 — `providers test` records its reply.** After `client.generate(request)` returns, it times the call. It calls `require_complete` in a `try`, then `ai_cost_service.record_reply(response, "providers_test", refused=<whether require_complete raised>, generation_time_s=<elapsed>)` in both branches, before printing or exiting.

### Displays

- **DR16 — A call's token line shows three counts.** The answer is `completion_tokens − thinking_tokens`, or `completion_tokens` when thinking is `None`. Thinking prints `—` when `None`. The format is `Tokens: {prompt} prompt, {answer} answer, {thinking} thinking`. It is used by:
  - `meetings condense`, which reads its rows with `AiCostRepository(session).get_by_ids(cost_record_ids)` and prints `Cost: ${sum of cost_usd:.6f}` followed by the token line summed over those rows (thinking `—` only when every row's is `NULL`);
  - `reports save`, from the `generate_report` result dict, which gains `thinking_tokens`;
  - `providers test`, from the reply.
- **DR17 — One rendering module for cost.** New `workmain/utils/cost_display.py` holds:
  - the answer and thinking rules in DR16;
  - `render_cost_summary(console, summary, label)`;
  - `render_cost_rows(console, rows, heading, label_column)`;
  - `render_cost_breakdown(console, title, breakdown)`.

  The four cost commands and the three token lines use it. `meetings costs` and `notes costs` call one shared function from it, with their own title and detail heading. Columns everywhere: `Prompt`, `Answer`, `Thinking`, `Total`, `Cost`, plus the existing identifying columns (date, label, provider, calls, average). A row with `refused` true shows its provider as `<provider> (refused)`. Summary lines: `Prompt Tokens`, `Answer Tokens`, `Thinking Tokens`, `Total Tokens`, `Total Cost`. A summary's or bucket's thinking total is the sum over rows that report a count, and `—` when none does. Its answer total is the sum of its rows' answers.
- **DR18 — The cost commands read `ai_costs` only.**
  - `get_summary` adds `prompt_tokens`, `answer_tokens` and `thinking_tokens` (`None` when no row reports one) at the top level and in each `by_provider` and `by_type` bucket. The existing keys stay. Its row aggregation moves into a module-level `summarize(rows)` that `reports costs` also uses.
  - `meetings costs` and `notes costs` filter `interaction_type='note_condensation'`.
  - `providers costs` labels its second table "By Call Type" and prints each call type as stored, not `.title()`d.
  - `reports costs` calls `get_report_costs`. That method joins `Report` on `report_id`, filters provider on `AiCost.provider`, type on `Report.report_type`, and dates on `Report.report_date` (inclusive), and orders by `Report.report_date` descending, then `AiCost.id` descending. Its summary is `summarize` over every row returned, and its detail table is the first `--limit` rows: one row per cost row, with `Date` (report date) and `Type` (report type).

### Dead code

- **DR19 — Removed:** `ReportGenerator.get_cost_summary`, `ReportsRepository.get_cost_summary`, `ReportsRepository.get_costs_by_date`, and the `Report` properties `ai_provider`, `cost`, `total_tokens`.

Anything this spec doesn't cover stops work under `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps. The two authorization points sit inside Steps 1 and 7.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | **The columns exist.** DR10's migration file, committed. Then the first authorization point. After execution, the AC8.1 test, committed. | `workmain/database/migrations/025_ai_costs_recording.sql`, `tests/test_ai_costs.py` |
| 2 | **The service records.** DR7 (model, repository methods and `create` arguments), DR1–DR4, and DR6's conftest fixture. `tests/test_ai_costs.py` `create` calls pass the two new arguments. New tests §6 (a). | `workmain/database/models.py`, `workmain/database/repositories/ai_costs_repo.py`, `workmain/services/ai_cost_service.py`, `tests/conftest.py`, tests |
| 3 | **`generate` records every reply.** DR5. The three caller writes are removed and the callers pass their context (DR8, DR9). The three existing cost-row tests in §2 move to `session_for_command('workmain.services.ai_cost_service')` and the new type names. New tests §6 (b). | `workmain/ai/base_provider.py`, `workmain/ai/provider_manager.py`, `workmain/ai/{report_generator,note_condenser,intent_parser}.py`, `workmain/cli/commands/{meetings,notes}.py`, tests |
| 4 | **One record of cost.** DR11 and DR19. `TestReportThinkingTokens` asserts the cost row and that the report's metadata carries no cost key. New tests §6 (c). | `workmain/database/repositories/reports_repo.py`, `workmain/database/models.py`, `workmain/ai/report_generator.py`, tests |
| 5 | **A free status check, and `providers test` recorded.** DR14 and DR15, and the guide line. New tests §6 (d). | `workmain/ai/providers/{claude,gemini}.py`, `workmain/cli/commands/providers.py`, `docs/AI_SETTINGS_GUIDE.md`, tests |
| 6 | **The screens.** DR16–DR18, and DR13 in the same commit, because `CostTracker`'s one reader is the `meetings condense` line DR16 replaces. New tests §6 (e). | `workmain/utils/cost_display.py`, `workmain/database/repositories/ai_costs_repo.py`, `workmain/cli/commands/{providers,meetings,notes,reports}.py`, `workmain/ai/{report_generator,note_condenser,cost_tracker,__init__}.py`, tests |
| 7 | **The old shape is gone.** DR12's migration file, committed. Then the second authorization point. After execution, the AC8.4 and AC8.5 tests, committed. | `workmain/database/migrations/026_ai_costs_single_record.sql`, `tests/test_ai_costs.py` |

### Authorization points

**1. Executing migration `025` against the live `workmain` database**, in Step 1, after its file is committed. State what it does:
- drops the `interaction_type` CHECK constraint;
- adds `refused` (boolean, default false) and `finish_reason` (nullable text) to `ai_costs`;
- copies the model from `reports.metadata` onto the cost rows that have none (102 rows on 20261011);
- copies the report's larger total onto the cost rows where it differs (9 rows).

Code running from `dev` is unaffected. To reverse it: `ALTER TABLE ai_costs DROP COLUMN refused, DROP COLUMN finish_reason;` and re-add the constraint as `017` declares it. The two copies are not reversed: they replace a missing or understated value with the report's own. Stop and wait for Ray's explicit approval (`docs/DEVELOPMENT_STANDARDS.md` §1.4, §4.5). Command: `psql -U workmain_user -d workmain -f workmain/database/migrations/025_ai_costs_recording.sql`.

**2. Executing migration `026` against the live `workmain` database**, in Step 7, after its file is committed. State what it does:
- renames the stored type on existing rows: `report` becomes the report type in `context_label`, and `condensation` becomes `note_condensation`;
- removes the six cost keys from `reports.metadata` on every report that has a cost row.

The metadata removal is a destructive change to data. It runs only after `025` has copied what only the reports held, and the values it removes are present on the cost rows. Before running it, Anvil runs and reports `select count(*) from ai_costs a join reports r on r.id = a.report_id where a.model is null or a.total_tokens < (r.metadata->>'total_tokens')::int` and confirms it is 0. If a report or condensation runs on older code between this migration and the post-merge restart, its row is written in the old shape. Running `026` again corrects it. Stop and wait for Ray's explicit approval. Command: `psql -U workmain_user -d workmain -f workmain/database/migrations/026_ai_costs_single_record.sql`.

## 5. Acceptance criteria

Issue #191's ACs map to AC1–AC6. AC7 and AC8 cover Ray's two decisions (Decision Log). They are added to the issue at close-out.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A report records exactly one cost row for its reply, typed with the report's call type and linked to the saved report, carrying the reply's provider, model, token counts and cost. Entry path: `ReportGenerator.generate_report` through a real `ProviderManager`. | `pytest tests/test_report_generator.py` — `stubbed_manager` with a Gemini stub scripting `thinking_tokens=196, tokens_used=999`; `session_for_command('workmain.services.ai_cost_service')`; asserts one row with `report_id` equal to the report, `interaction_type == 'daily_internal'`, `refused` false, and the stub's values |
| AC1.2 | A condensation records exactly one cost row, typed `note_condensation`, carrying the meeting and its title. Entry path: `NoteCondenser.condense_meeting`. | `pytest tests/test_note_condenser.py` — as above, asserting `meeting_id`, `context_label` and the stub's values, and that `condense_meeting`'s fourth return value is `[row.id]` |
| AC1.3 | Daemon narration records exactly one cost row, typed `daemon_narration`. Entry path: `narration.narrate`. | `pytest tests/test_narration.py` — `get_provider_manager` patched to a `stubbed_manager`; one observation; asserts one row with the stub's values |
| AC1.4 | An intent parse records exactly one cost row, typed `intent_parse`. Entry path: `IntentParser.parse`. | `pytest tests/test_intent_parser.py` — the existing thinking-tokens test, moved to the service's `session_for_command` |
| AC1.5 | Task match records exactly one cost row, typed `task_match`. Entry path: `IntentParser.parse_task_match`. | `pytest tests/test_intent_parser.py` — an Ollama stub replying with a match JSON; a task with note content and one note; asserts one row |
| AC1.6 | Note dedup records exactly one cost row, typed `note_dedup`. Entry path: `IntentParser.parse_note_duplicate`. | `pytest tests/test_intent_parser.py` — an Ollama stub replying with a duplicate JSON; asserts one row |
| AC1.7 | `workmain providers test` records exactly one cost row for its reply, typed `providers_test`. Entry path: the CLI command. | `pytest tests/test_provider_foundation.py` — `CliRunner` invokes `providers test claude` with the manager patched to return a stub; asserts one row with `interaction_type == 'providers_test'` |
| AC1.8 | A primary provider that fails without returning a reply records nothing, and the fallback reply that answers records one row. Entry path: `ProviderManager.generate`. | `pytest tests/test_provider_foundation.py` — primary stub raises `GenerationError`, fallback stub completes; asserts exactly one row (the fallback's) and that the returned reply's `cost_record_ids` is `[that id]` |
| AC1.9 | A recording failure does not fail the call: the reply is returned and a warning is logged. Entry path: `ProviderManager.generate`. | `pytest tests/test_provider_foundation.py` — no `session_for_command`, so DR6's fixture makes the service's `get_db` raise; asserts the reply is returned, `cost_record_ids == []`, and a warning in `caplog` |
| AC2.1 | A reply cut off at its cap, with no fallback, is recorded with its tokens and cost and marked refused, and the call still raises. Entry path: `ProviderManager.generate`. | `pytest tests/test_provider_foundation.py` — `stubbed_manager` with `drop_fallback`, primary `cut_off(...)`; asserts `IncompleteResponseError` and one row with `refused` true, `finish_reason == 'MAX_TOKENS'` and the stub's tokens and cost |
| AC2.2 | A refused primary reply followed by a fallback reply records both, the first refused, and the returned reply carries both ids, refused first. | `pytest tests/test_provider_foundation.py` — primary `cut_off`, fallback `complete`; asserts two rows and the order of `cost_record_ids` |
| AC2.3 | An empty reply is recorded as refused. | `pytest tests/test_provider_foundation.py` — stub with `content=""` and `finish=COMPLETE`, no fallback; asserts one row with `refused` true |
| AC3.1 | An intent reply that is not JSON is still recorded. | `pytest tests/test_intent_parser.py` — stub replies `"not json"`; asserts `IntentParseError` and one row with `refused` false |
| AC3.2 | A report whose save fails after the reply returned is still recorded. Entry path: `ReportGenerator.generate_report`. | `pytest tests/test_report_generator.py` — `reports_repo.create` patched to raise; asserts the exception propagates and one row exists, unlinked |
| AC3.3 | A condensation whose commit fails after the reply returned is still recorded. Entry path: `NoteCondenser.condense_meeting`. | `pytest tests/test_note_condenser.py` — the condenser's `session.commit` patched to raise on the summary commit; asserts the exception propagates and one row exists with the meeting id |
| AC4.1 | Only the recording service writes `ai_costs`. Outside the repository module, `AiCostRepository` and `AiCost(` appear only in the service, and the repository's getter appears only in the commands that read. | `git grep -nE 'AiCostRepository|AiCost\(' -- workmain` returns hits only in `workmain/database/repositories/ai_costs_repo.py`, `workmain/database/models.py` and `workmain/services/ai_cost_service.py`; `git grep -n 'get_ai_cost_repository' -- workmain` returns hits only in the repository module and `workmain/cli/commands/{providers,meetings,notes,reports}.py` |
| AC4.2 | The cost commands only read the cost table: none of them writes a row or a link. Entry path: each command through `CliRunner`. | The AC5.1–AC5.3 tests run with `AiCostRepository.create` and `AiCostRepository.link_report` monkeypatched to raise, and each command exits 0 |
| AC5.1 | `workmain providers costs` shows prompt, answer and thinking separately in its summary and in both tables, with `—` where no row reports thinking. Entry path: the CLI command. | `pytest tests/test_cost_display.py` — `CliRunner`, `session_for_command('workmain.cli.commands.providers')`, seeded rows in a sentinel date range: one Gemini row (prompt 10, completion 202, thinking 196) and one Ollama row (thinking `NULL`); asserts each figure, the answer `6`, and `—` on the Ollama bucket's thinking |
| AC5.2 | `workmain meetings costs` and `workmain notes costs` show the three counts per row and in their summaries, and print the same figures for the same rows. | `pytest tests/test_cost_display.py` — seeded `note_condensation` rows as above; both commands; asserts figures, `—`, and that the two outputs differ only in title and detail heading |
| AC5.3 | `workmain reports costs` reads the cost table: per cost row and in its summary, it shows the three counts, the report's date and type, and `(refused)` on a refused row. | `pytest tests/test_cost_display.py` — a seeded report with two cost rows (one refused, one accepted) and no cost keys in its metadata; asserts both rows, the summary sums, and the `(refused)` marker |
| AC5.4 | The per-call token lines (`meetings condense`, `reports save`, `providers test`) show prompt, answer and thinking, and `meetings condense` reads its figures from the rows recorded for that call. | `pytest tests/test_cost_display.py` — the shared formatter for a Gemini-shaped and an Ollama-shaped reply; and `CliRunner` invoking `meetings condense <title>` on a seeded sentinel meeting with one note, `session_for_command` on `workmain.cli.commands.meetings` and `workmain.services.ai_cost_service`, `get_note_condenser`'s manager patched to a `stubbed_manager` scripting thinking 196; asserts the printed cost and token line |
| AC6.1 | Full suite passes with no net test loss from the baseline at branch creation. Tests deleted by DR13 and DR14 are listed in the results artifact with the reason. | `pytest`, counts in the form `docs/DEVELOPMENT_STANDARDS.md` §6 states |
| AC7.1 | The Claude and Gemini status checks make no generation request, and look up the configured model instead. Entry path: `check_availability`, which `providers status`, `providers test` and `test_connection` call. | `pytest tests/test_ai_providers_offline.py` — for each provider, asserts `messages.create` / `generate_content` is not called, and `models.retrieve(model)` / `models.get(model=model)` is called once |
| AC7.2 | The status mapping is unchanged: a rate limit reads `rate_limited`, and other failures read as before. | `pytest tests/test_ai_providers_offline.py` — `test_check_availability_429_and_500` against `models.get`, and a Claude counterpart raising `AnthropicRateLimitError` and `APIError` from `models.retrieve` |
| AC7.3 | `docs/AI_SETTINGS_GUIDE.md` no longer says the status check reads policy keys. | A stated reading by Ray of the `REQUIRED_POLICY_KEYS` sentence in "Adding a provider" |
| AC8.1 | Migration `025` is applied: `ai_costs` has `refused` (boolean, not null, default false) and `finish_reason` (nullable), and no `interaction_type` CHECK constraint. | `pytest tests/test_ai_costs.py` — a `db_session` test reading `information_schema.columns` and `pg_constraint` |
| AC8.2 | A new report's metadata carries no cost: no model, token count or cost key. | `pytest tests/test_report_generator.py` — the AC1.1 test asserts the absence of all six keys and the presence of `ai_provider` and `generation_time` |
| AC8.3 | Nothing outside `ai_costs` holds a copy of cost. `CostTracker` is gone, and nothing reads cost from report metadata. | `git grep -nE 'CostTracker|cost_tracker' -- workmain scripts tests` returns nothing; `git grep -nE "report_metadata.*'(cost|total_tokens|prompt_tokens|completion_tokens|thinking_tokens|ai_model)'" -- workmain` returns nothing |
| AC8.4 | Migration `026` is applied: no live cost row carries the type `report` or `condensation`. | `pytest tests/test_ai_costs.py` — a `db_session` test counting those values, asserting 0 |
| AC8.5 | No live report that has a cost row carries a cost key in its metadata. | `pytest tests/test_ai_costs.py` — a `db_session` test counting reports with a cost row and any of the six keys, asserting 0. Anvil's pre-`026` check (§4) and its result are recorded in the results artifact |

## 6. Test plan

- **Baseline before this work:** the `Suite:` line of the latest `CHANGELOG.md` entry, confirmed by running `pytest` at the start of Step 1.
- **Expected after:** the baseline's passed count, plus the new tests, minus the tests DR13 and DR14 delete. 0 failed, 0 skipped, in the form `docs/DEVELOPMENT_STANDARDS.md` §6 states. Anvil records the actual counts and lists each deleted test.
- **Fixture rules:** a test of a recording path uses a real `ProviderManager` from `stubbed_manager` and `session_for_command('workmain.services.ai_cost_service')`. A CLI test seeds rows in `db_session`, uses sentinel dates (`2099-…`) and calls `session_for_command` on the command module. No test opens its own session.

Tests go in existing files, except the new `tests/test_cost_display.py`, which has no existing home: no current file tests a cost command's output.

- **(a) Step 2:** in `tests/test_ai_costs.py`, beside the repository tests: `create` stores `refused` and `finish_reason`; `link_report`, `get_by_ids` and `summarize` each do what DR7 and DR18 state; `record_reply` stores every field DR2 lists from a reply; `link_report` with `[]` opens no session; both service functions return `None` and log a warning on failure.
- **(b) Step 3:** AC1.1–AC1.9, AC2.1–AC2.3, AC3.1–AC3.3 in the files the ACs name.
- **(c) Step 4:** AC8.2, and AC8.3's metadata grep.
- **(d) Step 5:** AC1.7, AC7.1, AC7.2 in the files named. DR14's test changes.
- **(e) Step 6:** AC4.2, AC5.1–AC5.4, and AC8.3's `CostTracker` grep.
- **Steps 1 and 7:** AC8.1, AC8.4, AC8.5.

## 7. Risks and rollback

- **The suite fails between migration `025`'s file and its execution** if the model changes first. Step 2 holds the model change, after the authorization point. If `025` is not approved, Step 2 does not proceed.
- **A process on older code runs between `026` and the post-merge restart.** It writes the old type, or puts cost into a new report's metadata. `026` is safe to run again and corrects both. The daemon itself writes only narration, which old code does not record, and intent parse, whose type does not change. Reports and condensations run as CLI subprocesses on the checked-out branch.
- **`scripts/compare_providers.py` runs are now recorded** under their real call types, because they are paid replies. That is intended. They show in `providers costs` alongside production calls.
- **A test that reaches the service without opting in** takes the warning path silently. Its assertions are unaffected, and DR6 prevents any live write. A recording test that forgets `session_for_command` finds no row and fails, which is loud.
- **The cost commands' numbers shift for old rows.** Report rows move from `report` to their report type, condensation rows to `note_condensation`, and 9 Gemini report totals rise to the provider's own figure.
- **A recording failure is only a warning.** A row can go missing without failing the call. That is DR4's choice. The warning names the call type.
- **Rollback:** each step reverts on its own, in reverse order. After Step 7, reverting the code needs the report cost metadata back. It is reconstructed from the cost rows (`UPDATE reports SET metadata = metadata || jsonb_build_object(...)` from the accepted cost row). That is itself a data change, an authorization point, and is written only if needed. Migration `025`'s columns are dropped only after Step 2 is reverted.
