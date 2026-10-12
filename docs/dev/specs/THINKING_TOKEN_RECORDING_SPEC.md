# Thinking Token Recording — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261011
**Branch:** `feature/issue-149-gemini-thinking-tokens` (from `dev`)
**Target release:** v1.44.0 (set by `/closeout`)
**Originating item:** Issue #149
**Design study:** `../design/DESIGN_THINKING_TOKEN_RECORDING.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261009 | Ray | #182 study Q3: a separate thinking count, priced at the completion rate, stored in a new nullable `ai_costs.thinking_tokens` column and in `reports.metadata`, with `total_tokens` taken from the provider. | Taken — DR1, DR5–DR8, Steps 1–3. |
| 20261009 | Ray | #182 study Q5: no backfill of historical rows. | Taken — existing rows keep `thinking_tokens` `NULL`. |
| 20261011 | Ray | Study Q1 (D1): `completion_tokens` is all billed output on every provider; `thinking_tokens` is the part of it that was thinking, `None` where the provider reports no count. `estimate_cost` is unchanged. | Taken — DR1–DR4. |
| 20261011 | Ray | Study Q2 (D2, F3): Claude rows record the vendor's thinking count (`0` while the policy disables thinking). | Taken — DR3. |
| 20261011 | Ray | Study Q3 (D3): no display change in this work; thinking is stored and counted in every total. The per-row breakdown in the cost displays belongs with #191. | Taken — out of scope. Added to #191, which is now blocked by #149. |
| 20261011 | Ray | Study Q4 (F15): test rows leaking into the live `ai_costs` table belong to #136. | #136 updated. Out of scope here; this spec's new tests use `db_session` (DR12). |
| 20261011 | Ray | Study Q5 (D4): token counts are read in code, pricing stays in the two existing config rates, and #149 adds no config key. | Taken — no config change. |
| 20261011 | Ray | The provider settings files can carry only the keys their code names, contrary to #79's promise, so Claude's effort level cannot be set (study F16). | Opened as #194, blocked by #155. Out of scope here. |

---

## 1. Scope

**In scope:**

- `GenerationResponse` gains `thinking_tokens`, and `completion_tokens` and `tokens_used` get one meaning on every provider (DR1).
- Each provider maps its vendor's usage into those fields: Gemini prices thinking for the first time (DR2), and Claude reads its thinking count (DR3). Ollama reports none (DR4).
- Migration `024` adds `ai_costs.thinking_tokens` (DR6). Executing it is the spec's one authorization point.
- `AiCostRepository.create` stores the thinking count and the provider's total instead of recomputing one (DR5). `ReportsRepository.create` stores the thinking count in `reports.metadata` (DR8). The three `ai_costs` write sites pass both values (DR7).
- `scripts/compare_providers.py` reads the response's thinking count (DR9).
- `docs/AI_SETTINGS_GUIDE.md`'s completion-rate row (DR10).
- Test construction sites and fixtures that the new required field and the vendor usage shapes reach (DR11).

**Out of scope:**

- Cost display breakdown in `providers costs`, `reports costs`, `meetings costs` and `notes costs` — #191 (Decision Log). Their totals include thinking once this ships, with no display change (study F10).
- The token lines printed by `reports save` and `providers test`. They print `completion_tokens`, which on Gemini now includes thinking (DR1). No change.
- Where and when `ai_costs` rows are written, including narration, task match, note dedup and refused replies — #191.
- Test rows already in, or still leaking into, the live `ai_costs` table — #136.
- Rate keys, their in-code defaults and their validation — #155.
- Which settings keys a provider sends, and Claude's effort level — #194. Gemini's thinking level — #186.
- `CostTracker`. Its total is `prompt_tokens + completion_tokens` (`cost_tracker.py:198`), which equals the provider's total on every provider once DR1 holds (study F9). No change.
- Backfill of existing rows (Decision Log, 20261009).

## 2. Verified current state

Verified 20261011 on `feature/issue-149-gemini-thinking-tokens` at `a8256aa`. The study's §3 carries the full evidence.

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| `GenerationResponse` fields: `content, provider, model, tokens_used, prompt_tokens, completion_tokens, cost, finish, finish_reason`, then `metadata` defaulting to `None`. Every construction passes keywords. | `workmain/ai/base_provider.py:64-90` |
| `GenerationResponse` construction sites, found by `git grep -n 'GenerationResponse(' -- workmain scripts automation tests` | `workmain/ai/providers/claude.py:151`, `gemini.py:177`, `ollama.py:104`; `tests/mocks/stub_providers.py:32`, `tests/test_ai_foundation.py:89`, `tests/test_compare_providers.py:39`, `tests/test_intent_parser.py:27`, `tests/test_meetings_condense.py:41`, `tests/test_note_condenser.py:78`, `tests/test_notes_log.py:106`, `tests/test_provider_foundation.py:1016`, `:1027`, `:1094`, `:1214` |
| Gemini: `completion_tokens = usage.candidates_token_count or 0`; `total_tokens = usage.total_token_count or (prompt_tokens + completion_tokens)`; `cost = self.estimate_cost(prompt_tokens, completion_tokens)`. `thoughts_token_count` is not read. | `gemini.py:153-160` |
| Gemini `total_token_count` is prompt + candidates + `tool_use_prompt_token_count` + `thoughts_token_count`. No request passes tools. Live 20261011: prompt 9, candidates 6, thoughts 196, total 211. | `google-genai` 2.22.0 field doc; `config/providers/gemini/settings.json`; study F1, F2 |
| Claude: `prompt_tokens = usage.input_tokens`, `completion_tokens = usage.output_tokens`, `total_tokens = prompt_tokens + completion_tokens`. `output_tokens` is the inclusive billing count; `usage.output_tokens_details.thinking_tokens` is its thinking part (`Optional`, `None` when absent). Live 20261011, thinking disabled: `OutputTokensDetails(thinking_tokens=0)`. | `claude.py:135-139`; `anthropic` 1.3.0 `types/usage.py:30-40`, `output_tokens_details.py`; study F3 |
| Ollama: prompt from `prompt_eval_count`, completion from `eval_count`, `tokens_used` their sum, `cost=0.0`. No thinking count. | `ollama.py:92-93`, `:104-114` |
| `estimate_cost(prompt_tokens, completion_tokens)` is identical in Claude and Gemini; Ollama returns `0.0`. | `claude.py:207-220`; `gemini.py:246-259`; `ollama.py:128-130` |
| `AiCostRepository.create(interaction_type, provider, model, prompt_tokens, completion_tokens, cost_usd, generation_time_s=None, report_id=None, meeting_id=None, context_label=None)` stores `total_tokens=prompt_tokens + completion_tokens`. | `workmain/database/repositories/ai_costs_repo.py:21-68` |
| `AiCostRepository.create` call sites, found by `git grep -n 'AiCostRepository\|get_ai_cost_repository' -- workmain scripts automation tests`. All pass keywords. `tests/test_ai_arguments.py:177` and `tests/test_provider_foundation.py:501` patch the getter and call no `create`. `tests/test_ai_costs.py` `_insert_cost` builds `AiCost` directly. | `workmain/ai/report_generator.py:215`; `workmain/ai/note_condenser.py:196`; `workmain/ai/intent_parser.py:112`; `tests/test_ai_costs.py:59`, `:81`, `:97` |
| `AiCost` columns: `id, interaction_type, provider, model, prompt_tokens, completion_tokens, total_tokens, cost_usd, generation_time_s, report_id, meeting_id, context_label, created_at`. No JSON column. | `workmain/database/models.py:430-443`; `workmain/database/migrations/017_ai_costs.sql` |
| Latest migration is `023`. Migrations are SQL files run with `psql -U workmain_user -d workmain -f <file>`. | `workmain/database/migrations/`; `docs/archive/specs/FEATURE_SPEC_COST_TRACKING_PERSISTENCE_v1_4_20260528.md:1063` |
| `ReportsRepository.create` builds `metadata` from `ai_provider, ai_model, prompt_tokens, completion_tokens, total_tokens, cost, generation_time` (+ `file_path`, `fallback_reason`). One caller, found by `git grep -n 'ai_provider=' -- workmain tests scripts automation`. | `workmain/database/repositories/reports_repo.py:34-96`; `workmain/ai/report_generator.py:194` |
| `report_generator` passes `total_tokens=response.tokens_used` to `reports_repo.create`, and `prompt_tokens`, `completion_tokens`, `cost_usd` (no total) to `AiCostRepository.create`. | `report_generator.py:194-225` |
| `compare_providers.py` derives thinking as `tokens_used - prompt_tokens - completion_tokens` and prints it as "Thinking tokens". No test asserts that line. | `scripts/compare_providers.py:184-185`, `:231`; `git grep -n 'Thinking tokens\|_thinking_tokens' -- tests` no match |
| Test fixtures for vendor usage: Claude `_fake_message` sets `usage.input_tokens` and `usage.output_tokens` on a `MagicMock`. Gemini fixtures set prompt, candidates and total on a `MagicMock` `usage_metadata`; an unset attribute is a truthy `MagicMock`. | `tests/test_ai_providers_offline.py:75-86`; `:297-303`, `:524-526`, `:545-547`, `:608-610`, `:622-624`, `:634-636` |
| `StubProvider.generate` returns `tokens_used=10, prompt_tokens=5, completion_tokens=5, cost=0.0`. `stubbed_manager` builds a real `ProviderManager` with stubs injected. | `tests/mocks/stub_providers.py:15-35`, `:46-68` |
| Existing tests build `ReportGenerator(db_session, provider_manager=pm)` and `NoteCondenser(db_session)` against `db_session`. A test reaching code that calls `get_db()` itself points it at `db_session` with `mock_get_db.return_value.get_session.return_value = db_session`. | `tests/test_report_generator.py:64`; `tests/test_note_condenser.py:113-134`; `tests/test_eod_workflow.py:301` |
| `docs/AI_SETTINGS_GUIDE.md` rate row: "`cost_per_1k_completion_tokens` | USD cost per 1,000 completion tokens". | `docs/AI_SETTINGS_GUIDE.md:53` |

**Not verified:** whether Gemini omits `thoughts_token_count` or sends `0` when a reply uses no thinking. DR2 maps both to `0`.

## 3. Design rules

- **DR1 — One meaning per token field, on every provider.** `GenerationResponse` gains `thinking_tokens: Optional[int]`, declared after `completion_tokens`, required with no default (the #148 precedent for `finish`). Docstrings state:
  - `completion_tokens`: every output token the vendor billed, thinking included.
  - `thinking_tokens`: how many of `completion_tokens` were thinking; `None` when the provider reports no count.
  - `tokens_used`: the total the provider reported, or the sum of its own counts where it reports no total.
- **DR2 — Gemini.** `thinking_tokens = usage.thoughts_token_count or 0`. Gemini reports thinking wherever it happens, so an absent count means none was used. `completion_tokens = (usage.candidates_token_count or 0) + thinking_tokens`. `tokens_used` stays `usage.total_token_count`, falling back to `prompt_tokens + completion_tokens`. `cost = self.estimate_cost(prompt_tokens, completion_tokens)`, unchanged in form, now pricing thinking at the completion rate.
- **DR3 — Claude.** `completion_tokens` stays `usage.output_tokens`. `thinking_tokens = usage.output_tokens_details.thinking_tokens` when `output_tokens_details` is not `None`, else `None`. `tokens_used` stays `input_tokens + output_tokens`: Anthropic reports no total, and these two counts are its whole bill. Cost is unchanged.
- **DR4 — Ollama.** `thinking_tokens=None`. Nothing else changes.
- **DR5 — `AiCostRepository.create` stores what the provider reported.** It gains `thinking_tokens: Optional[int]` and `total_tokens: int`, both required keyword arguments with no default, placed after `completion_tokens`. It stores both as passed. Nothing in the repository computes a total. The docstring states that `thinking_tokens` is `None` when the provider reports no count.
- **DR6 — Migration `024`.** `workmain/database/migrations/024_ai_costs_thinking_tokens.sql`, with a header in `017`'s form, contains `ALTER TABLE ai_costs ADD COLUMN IF NOT EXISTS thinking_tokens INTEGER;` and nothing else: nullable, no default, no backfill. `AiCost` gains `thinking_tokens = Column(Integer, nullable=True)`. The model change lands only after the migration has been executed (§4, authorization point), because an ORM insert names every mapped column.
- **DR7 — The three write sites pass the response's values.** `report_generator.py`, `note_condenser.py` and `intent_parser.py` each pass `thinking_tokens=response.thinking_tokens` and `total_tokens=response.tokens_used` to `AiCostRepository.create`. Nothing else at these sites changes. #191 later moves these writes into one site and keeps the signature.
- **DR8 — `reports.metadata` carries the thinking count.** `ReportsRepository.create` gains a required `thinking_tokens: Optional[int]` and writes it as the metadata key `thinking_tokens` (JSON `null` for `None`). `report_generator.py:194` passes `response.thinking_tokens`. `total_tokens` already carries `response.tokens_used`.
- **DR9 — One definition of thinking.** `compare_providers.py` deletes `_thinking_tokens` and prints `response.thinking_tokens`, or `not reported` when it is `None`.
- **DR10 — The guide's completion-rate row** reads: "USD cost per 1,000 completion tokens: every output token the provider bills, thinking included". No other guide change.
- **DR11 — Tests model the vendor's shape, not a `MagicMock` default.** Every Gemini `usage_metadata` fixture in §2 sets `thoughts_token_count` to an `int` or `None`. Claude's `_fake_message` sets `usage.output_tokens_details` to `None` or to an object with an `int` `thinking_tokens`. Each test `GenerationResponse` construction in §2 passes `thinking_tokens`: `None` for Ollama-shaped and stub replies, otherwise the value its fixture models. `StubProvider` gains `thinking_tokens: Optional[int] = None` and `tokens_used: int = 10` constructor arguments, passed through to its response, so a test can script both.
- **DR12 — New database tests take `db_session`.** A test that reaches `IntentParser.parse` points its `get_db()` at `db_session` with the `tests/test_eod_workflow.py:301` pattern, so it leaves no row behind (study F15).

Anything this spec doesn't cover stops work under `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps; the authorization point below sits inside Step 1.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | **The column exists.** DR6's migration file, committed. Then the authorization point below. After execution, the AC2.1 test, committed. | `workmain/database/migrations/024_ai_costs_thinking_tokens.sql`, `tests/test_ai_costs.py` |
| 2 | **Providers report thinking.** DR1–DR4 in the base class and the three providers. DR11's fixture and construction-site changes, and `StubProvider`'s new arguments. DR9 and DR10 in the same commit, so the field, its one reader outside the write path, and the doc that prices it land together. New tests §6 (a). | `workmain/ai/base_provider.py`, `workmain/ai/providers/{claude,gemini,ollama}.py`, `scripts/compare_providers.py`, `docs/AI_SETTINGS_GUIDE.md`, `tests/mocks/stub_providers.py`, tests |
| 3 | **Rows store it.** DR5, DR6's model column, DR7 and DR8, with the `tests/test_ai_costs.py` `create` calls updated to pass both new arguments. New tests §6 (b). | `workmain/database/models.py`, `workmain/database/repositories/ai_costs_repo.py`, `workmain/database/repositories/reports_repo.py`, `workmain/ai/{report_generator,note_condenser,intent_parser}.py`, tests |

### Authorization points

**One: executing migration `024` against the live `workmain` database**, in Step 1, after the migration file is committed and before the model changes. State that it adds one nullable `INTEGER` column, `thinking_tokens`, to `ai_costs`; changes no row; and is reversed by `ALTER TABLE ai_costs DROP COLUMN thinking_tokens;`. Then stop and wait for Ray's explicit approval (`docs/DEVELOPMENT_STANDARDS.md` §1.4, §4.5). The command is `psql -U workmain_user -d workmain -f workmain/database/migrations/024_ai_costs_thinking_tokens.sql`. Ray runs it, or approves its being run. Code already running on `dev`, including the daemon, inserts without the column and is unaffected.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A Gemini reply that thinks is priced with its thinking at the completion rate: `completion_tokens` is answer plus thinking, `thinking_tokens` is the vendor's count, and `cost` is prompt × prompt rate + (answer + thinking) × completion rate. Entry path: `GeminiProvider.generate`, the only place a Gemini cost is computed. | `pytest tests/test_ai_providers_offline.py` — a test whose `usage_metadata` has prompt 9, candidates 6, thoughts 196, total 211, and configured rates, asserting `completion_tokens == 202`, `thinking_tokens == 196`, `tokens_used == 211` and the cost by formula |
| AC1.2 | A Gemini reply with no thinking count records `thinking_tokens` `0`, and `completion_tokens` equals the answer count. | `pytest tests/test_ai_providers_offline.py` — `thoughts_token_count = None` |
| AC1.3 | A Claude reply records the vendor's thinking count and leaves `completion_tokens` and cost unchanged; with no `output_tokens_details` it records `None`. Entry path: `ClaudeProvider.generate`. | `pytest tests/test_ai_providers_offline.py` — one test with `thinking_tokens=40` inside `output_tokens=100`, asserting `completion_tokens == 100` and the cost from 100; one with `output_tokens_details = None` |
| AC1.4 | An Ollama reply records `thinking_tokens` `None`. | `pytest tests/test_ollama_provider.py` |
| AC1.5 | `docs/AI_SETTINGS_GUIDE.md` states that the completion rate prices every output token the provider bills, thinking included. | A stated reading by Ray of the `cost_per_1k_completion_tokens` row |
| AC2.1 | `ai_costs` has a nullable integer `thinking_tokens` column in the live database. | `pytest tests/test_ai_costs.py` — a `db_session` test reading `information_schema.columns` for `ai_costs.thinking_tokens`, asserting `data_type = 'integer'` and `is_nullable = 'YES'` |
| AC2.2 | `AiCostRepository.create` stores the thinking count it is given, and `NULL` for `None`. | `pytest tests/test_ai_costs.py` — two `db_session` tests reading the stored row back |
| AC2.3 | A generated report's `ai_costs` row and its `reports.metadata` both carry the reply's thinking count. Entry path: `ReportGenerator.generate_report` through a real `ProviderManager`. | `pytest tests/test_report_generator.py` — `stubbed_manager` with a stub scripting `thinking_tokens=196`, `save_to_file=False`, `db_session`; asserts the `ai_costs` row's `thinking_tokens == 196` and `report.report_metadata['thinking_tokens'] == 196` |
| AC2.4 | A condensation's `ai_costs` row carries the reply's thinking count. Entry path: `NoteCondenser.condense_meeting` through a real `ProviderManager`. | `pytest tests/test_note_condenser.py` — `NoteCondenser(db_session)` with its `provider_manager` replaced by a `stubbed_manager` whose stub scripts `thinking_tokens=50`; asserts the row's `thinking_tokens == 50` |
| AC2.5 | An intent parse's `ai_costs` row records `thinking_tokens` `NULL`, since Ollama reports none. Entry path: `IntentParser.parse`. | `pytest tests/test_intent_parser.py` — `workmain.ai.intent_parser.get_provider_manager` patched to a `stubbed_manager` with an Ollama-typed stub, `get_db()` pointed at `db_session` (DR12); asserts one row with `thinking_tokens IS NULL` |
| AC2.6 | The provider comparison report prints the response's own thinking count, and "not reported" when there is none. | `pytest tests/test_compare_providers.py` — `render()` over one run whose response has `thinking_tokens=196` and one with `None`, asserting each "Thinking tokens" line |
| AC3.1 | `AiCostRepository.create` stores the total it is given, even where it differs from prompt + completion. | `pytest tests/test_ai_costs.py` — `prompt_tokens=10, completion_tokens=5, total_tokens=20`, stored row reads `20` |
| AC3.2 | Each write path stores the reply's `tokens_used` as `total_tokens`. Entry paths: report generation, condensation and intent parse. | The AC2.3, AC2.4 and AC2.5 tests each script `tokens_used` to differ from prompt + completion and assert the row's `total_tokens` equals it |
| AC3.3 | No code under `workmain/` computes an `ai_costs` total; every row's total comes from the provider. | `git grep -n 'total_tokens=prompt_tokens + completion_tokens' -- workmain/database` returns no match, and the required `total_tokens` argument makes a call site that omits it fail with `TypeError` in the AC3.2 tests |
| AC4.1 | Full suite passes with no net test loss from the baseline. | `pytest`, counts recorded in the form §6 states |

## 6. Test plan

- **Baseline before this work:** the `Suite:` line of the latest `CHANGELOG.md` entry, confirmed by running `pytest` at the start of Step 1.
- **Expected after:** the baseline's passed count plus the new tests, 0 failed, 0 skipped, in the form `docs/DEVELOPMENT_STANDARDS.md` §6 states. Anvil records the actual counts.
- **Fixture rule:** a test of a write path uses a real `ProviderManager` from `stubbed_manager`, as the #148 tests do. Mocking `ProviderManager.generate` would bypass the response the provider builds.

Tests go in existing files:

- **Step 1:** AC2.1 in `tests/test_ai_costs.py`.
- **(a) Step 2:** AC1.1–AC1.3 in `tests/test_ai_providers_offline.py`; AC1.4 in `tests/test_ollama_provider.py`; AC2.6 in `tests/test_compare_providers.py`.
- **(b) Step 3:** AC2.2, AC3.1 in `tests/test_ai_costs.py`; AC2.3 (with AC3.2) in `tests/test_report_generator.py`; AC2.4 (with AC3.2) in `tests/test_note_condenser.py`; AC2.5 (with AC3.2) in `tests/test_intent_parser.py`.

## 7. Risks and rollback

- **The suite fails between the migration file and its execution** if the model column lands first. DR6 orders them: the model changes in Step 3, after the authorization point. If the migration is not approved, Steps 2 and 3 don't proceed past the model change.
- **Gemini totals and costs rise from the day this ships.** Every Gemini cost and `completion_tokens` figure now includes thinking, so `reports costs`, `providers costs` and the rest jump against earlier rows. That is the correction #149 asks for. Earlier Gemini rows carry `thinking_tokens` `NULL`, which marks them as recorded before the change.
- **A `GenerationResponse` or `AiCostRepository.create` call outside §2's enumeration** fails with `TypeError` at construction or call, which is loud. The searches cover `workmain`, `scripts`, `automation` and `tests`.
- **A vendor changes its usage shape.** A Gemini fixture or Claude fixture that no longer matches would pass while live replies differ. DR11's fixtures are built from the installed SDK fields named in §2.
- **Rollback:** each step reverts on its own, in reverse order. The column is removed with `ALTER TABLE ai_costs DROP COLUMN thinking_tokens;`, which is itself an authorization point, and only after Step 3 is reverted.
