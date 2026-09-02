# Provider Payload Policy and Current-Generation Model Compatibility — Spec

**Status:** Draft — Caliper pass 1 resolved 20260902, awaiting Ray
**Author:** Spanner (Role 1)
**Date:** 20260902
**Branch:** `feature/issue-79-provider-payload-policy` (from `dev`)
**Target release:** v1.32.0
**Originating item:** Issue #79
**Design study:** `../design/DESIGN_CLAUDE_PROVIDER_CURRENT_MODEL.md` (the payload defect) and `../design/DESIGN_PROVIDER_MODEL_CAPABILITY.md` (the config restructure)

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260901 | Issue #79 | Strip the sampling parameters; send `thinking: {"type": "disabled"}`. | Taken — DR1, DR2. Options in `DESIGN_CLAUDE_PROVIDER_CURRENT_MODEL.md` §4; Option A. |
| 20260901 | Issue #79 | Rejected: model-capability gating inside the provider. | Still rejected. A policy file declares what we *send*; it never records what a model *supports* — DR8. |
| 20260902 | Spanner | Verified live on Ray's key: `claude-sonnet-5` returns 400 on `temperature`, accepts `thinking={"type":"disabled"}`. | DR1 and DR2 rest on measurement, not documentation. `DESIGN_PROVIDER_MODEL_CAPABILITY.md` F10. |
| 20260902 | Ray | Scope grows: this issue carries the **provider config restructure** and goes first; the capability check is a separate, dependent issue. | Taken — §1, Steps 1–3. Study Q11. |
| 20260902 | Ray | Payload policy is **one per provider**, not one per model. | Taken — DR7. A row per model is a register with a drift problem. |
| 20260902 | Ray | Branch type `feature/*` from `dev`, not `hotfix/*`. Conceded on scope, **not** on the premise — the provider was proven broken by a live 400 against `claude-sonnet-5`; the old model in config is a workaround, not evidence of health. | Taken. Branch `feature/issue-79-provider-payload-policy`, target v1.32.0. |
| 20260902 | Spanner | Design study Q1 — Option A forecloses `claude-fable-5` / `claude-mythos-5` and caps Opus 5 at effort ≤ high. | Resolved by the restructure: the constraint is now a policy value in `claude_settings.json`, changeable without code, not prose in a `notes` field. DR3. |
| 20260902 | Spanner | Design study Q2 — delete `_FALLBACK_MODEL` rather than sync it. | Resolved by the restructure: with `model` required from config there is no place for a hardcoded default. DR5. |
| 20260902 | Ray | Fail fast on the whole non-retryable 4xx class — "for the 400, to me that means 4XX". | Taken — DR4, Step 5, AC9.1. |
| 20260902 | Ray | #79's test AC was false as written and satisfiable by changing nothing; replace it. | Taken. Issue #79's acceptance criteria rewritten in place 20260902 — 14 criteria, each a property with its evidence per `docs/DEVELOPMENT_STANDARDS.md` §1.2. §5 below maps to them. |
| 20260902 | Spanner | Design study Q4 — `count_tokens` calls a method the SDK does not have; retry multiplication. | Out of scope. `count_tokens` becomes its own issue at close-out. |
| 20260902 | Caliper | **B1** — a sibling `except APIStatusError` ahead of `except APIError` catches every status error including 5xx; Python does not fall through, so Step 5 as written could not both fail fast on 4xx and keep 5xx backoff. | **Accepted.** Step 5 restated as a status check inside the existing `APIError` handler — one handler, one retry policy. DR4 reworded. |
| 20260902 | Caliper | **B2** — DR10 plus Step 2 would silently disable `OllamaProvider`: it is enabled in config, has no policy file, and `_load_config` swallows construction failures into `_disabled`. AC4.1 would still pass because it tests the provider class directly. | **Accepted.** Step 1 ships `ollama_settings.json`; Step 2 loads the policy *before* provider construction so the failure is not caught by the existing blanket `except`. AC4.1 gains the manager-level case. |
| 20260902 | Caliper | **B3a** — Step 8's `0.002` / `0.010` are the expired introductory rate; list price is `0.003` / `0.015`. | **Not taken.** Verified against the live pricing page 20260902, which states: "The $2/$10 per million input/output token pricing for Claude Sonnet 5, announced at launch as introductory pricing through August 31, 2026, is now the standard price. The previously scheduled increase to $3/$15 per million input/output tokens on September 1, 2026 will not occur." Caliper was right that the introductory window existed and right to ask for verification; the increase was cancelled. Step 8 unchanged. |
| 20260902 | Caliper | **B3b** — AC12.1's check prints back what Step 8 wrote, so it is evidence the file was edited, not that the price is correct. | **Accepted.** AC12.1 reworded so the numeric fields, the `cost_structure` string and the vendor's published rate must agree, checked by Ray's reading. |
| 20260902 | Ray | **Pricing values are Ray's to set, whenever a model is updated** — not the implementer's. | Taken. Step 8 splits: Anvil changes `model`, `notes` and `last_updated`; the two `cost_per_1k_*` fields and `cost_structure` are Ray's edit. This is why AC12.1's check is Ray's reading and not a command — no command can tell whether a price is the one Ray intends to be billed at. |
| 20260902 | Caliper | **S4** — the policy file has no grammar; DR3 and AC1.1 both go green on a loader that hardcodes `if policy['thinking'] == 'disabled'`, which is DR8's register moved into an `if`. | **Accepted, and it improves the design.** New DR11: policy values are the vendor's own shapes, passed through verbatim and untranslated. This removes the translation layer rather than specifying it. |
| 20260902 | Caliper | **S5** — DR10 guards absence and syntax but not a missing or misspelled key, so a policy file with `thinking` dropped reproduces the exact #79 payload. | **Accepted.** DR10 extended to required keys; AC4.1's test set gains the present-but-incomplete case. |
| 20260902 | Caliper | **S6** — AC2.1's intersection is empty even with `default_max_tokens` / `default_temperature` still in `ai_settings.json`, so the criterion passes over a live DR9 violation. | **Accepted.** Those two dead keys move *into* scope and are deleted; AC2.1 gains a runnable command. |
| 20260902 | Caliper | **S7** — Step 2 adds a third hand-rolled config read without addressing `ConfigLoader`; §3.6 makes that a decision to state, not inherit. | **Accepted.** New DR12: the policy read goes through `ConfigLoader.load()`. Verified it handles the nested name — `ConfigLoader().config_dir / 'providers/claude_settings.json'` resolves correctly, so no new pattern is needed. |
| 20260902 | Caliper | Offline tests need a patched environment with a well-formed fake key, since `__init__` reads the key from the environment and `validate_config()` rejects anything not prefixed `sk-ant-`. | **Accepted.** Stated in Step 7. |

---

## 1. Scope

**In scope:**

- **New:** `config/providers/claude_settings.json` and `config/providers/gemini_settings.json` — each provider's request payload policy.
- **New:** policy loading, in `workmain/ai/provider_manager.py`, passed to providers at construction.
- `workmain/ai/providers/claude.py` — payload built from policy in both `generate()` and `check_availability()`; the `APIError` handler; `_FALLBACK_MODEL`.
- `workmain/ai/providers/gemini.py` — sampling read from policy rather than hardcoded.
- `workmain/ai/base_provider.py` — the `GenerationRequest.temperature` docstring only.
- `config/ai_settings.json` — the `providers.claude` block: `model`, both `cost_per_1k_*`, `cost_structure`, `notes`, `last_updated`; and deletion of the unread `default_max_tokens` / `default_temperature` keys from the `claude` and `gemini` blocks (DR9 — they are payload values sitting in the orchestration file).
- `tests/` — offline payload-contract tests and policy-loading tests.

**Out of scope:**

- `OllamaProvider`. Brought inline under its own issue (study Q3); its generation parameters are Modelfile-baked and rebuilt outside this repo.
- `workmain providers check` and everything capability-related — the dependent issue.
- Every `max_tokens` value at every call site. DR2 exists so no call-site budget audit is needed.
- Adaptive thinking for `reports generate`. Named out of scope by issue #79.
- `ClaudeProvider.count_tokens()` (broken against `anthropic` 0.75.0) and the provider-plus-SDK retry multiplication. Recorded in `DESIGN_CLAUDE_PROVIDER_CURRENT_MODEL.md` F9, F10.
- Converting `ProviderManager`'s existing hand-rolled `ai_settings.json` read to `ConfigLoader`. It works, and changing it is not this issue's business — DR12 covers only the new read.
- `timeout_seconds` — issue #114, already open.
- Choosing a newer Gemini model. Study Q5, dropped.

## 2. Verified current state

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| `generate()` sends `temperature` unconditionally from a literal `api_params` dict; no `thinking` key. | `workmain/ai/providers/claude.py:92-101` |
| `check_availability()` builds a second, independent payload — `max_tokens=1`, no `temperature`, no `thinking`. | `workmain/ai/providers/claude.py:222-226` |
| `GeminiProvider` hardcodes `temperature` into its generation config. | `workmain/ai/providers/gemini.py:100` |
| The `APIError` handler retries every `APIError`; `BadRequestError` (400) is a subclass of it via `APIStatusError`. | `workmain/ai/providers/claude.py:136-151`; `anthropic.BadRequestError.__mro__`, verified by execution on 0.75.0 |
| `AnthropicRateLimitError` is already caught ahead of `APIError` and re-raised without retry. | `workmain/ai/providers/claude.py:132-134` |
| `_FALLBACK_MODEL = "claude-sonnet-4-5-20250929"` supplies `model` when config omits it. | `workmain/ai/providers/claude.py:34`, `:55` |
| `validate_config()` already raises `ConfigurationError` on a falsy `self.model`, and is called from `__init__`. | `workmain/ai/providers/claude.py:70-71`, `:181-182` |
| `ProviderManager` loads `config/ai_settings.json` and instantiates providers from `PROVIDER_REGISTRY`, passing each its config section. | `workmain/ai/provider_manager.py:286-296`, `:60`, `:98-103` |
| The documented way to add a provider is `PROVIDER_REGISTRY` + a section in `config/ai_settings.json`. This spec adds a third step. | `workmain/ai/providers/__init__.py:6` |
| `config/` holds flat per-concern JSON today; `intent_parse_prompt.json` / `intent_parse_system_prompt.txt` is the existing precedent for splitting one concern across two files with a stated ownership boundary. | `ls config/`; `CLAUDE.md` § Intent Parser Config |
| `GenerationRequest.temperature` is documented with no provider qualification. | `workmain/ai/base_provider.py:42`, `:48` |
| `config/ai_settings.json` names `claude-sonnet-4-5-20250929` at $3/$15. | `config/ai_settings.json` → `providers.claude` |
| **Live, 20260902:** `claude-sonnet-5` rejects `temperature=0.0` with HTTP 400 `invalid_request_error`; accepts `thinking={"type": "disabled"}`. | `DESIGN_PROVIDER_MODEL_CAPABILITY.md` F10 |
| Anthropic publishes no sampling capability and no `disabled` thinking type, so neither DR1 nor DR2 was derivable from vendor metadata. | `DESIGN_PROVIDER_MODEL_CAPABILITY.md` F2, F3 |
| The five `temperature` lines named in #79's test AC are `GenerationRequest(...)` constructions in tests gated on `SKIP_API_TESTS`, not payload assertions. No test anywhere asserts what `ClaudeProvider` sends. | `tests/test_ai_clients.py:124, 161, 286, 298, 328`; gate at `:36`; `grep -rn "messages.create\|MagicMock\|patch" tests/test_ai_clients.py` returns zero hits |
| The smallest Claude-reachable budget is `max_tokens=20` (`providers test`); `narration.py` uses 200; `note_condenser.py` already uses 1024. | `workmain/cli/commands/providers.py:155`; `workmain/daemon/narration.py:57`; `workmain/ai/note_condenser.py:141` |
| The installed SDK carries `anthropic.types.ThinkingConfigDisabledParam`. | `anthropic` 0.75.0, verified by execution |

## 3. Design rules

- **DR1 — `ClaudeProvider` sends no sampling parameter.** No `temperature`, `top_p` or `top_k` reaches the Anthropic SDK. `GenerationRequest.temperature` stays on the dataclass because Gemini reads it; the docstring says which providers honour it.
- **DR2 — `ClaudeProvider` sends `thinking={"type": "disabled"}` on every request.** This is what keeps `max_tokens` meaning response tokens at every call site on every model, so no caller has to know which model config names.
- **DR3 — the models `ClaudeProvider` supports are those that accept its policy.** `claude-fable-5` and `claude-mythos-5` reject disabled thinking and cannot be named in `config/ai_settings.json` while the policy says `disabled`. This is a consequence of a policy value, not a rule in code — no model-capability table exists anywhere.
- **DR4 — a request the API will never accept is not retried.** A 4xx other than 408, 409 and 429 is a permanent property of the request: fail on the first attempt, surfacing the API's own message. 408/409/429 and every 5xx keep the existing backoff, as do connection errors. This is a **status check at the top of the existing `APIError` handler**, not a second `except` clause — `RateLimitError`, `APIStatusError` and `APIConnectionError` all descend from `APIError`, and a sibling clause would swallow 5xx and network errors along with the 4xx. One handler, one retry policy.
- **DR5 — the provider carries no copy of a config value.** `model` comes from config or the provider refuses to construct.
- **DR6 — one payload, one builder.** `generate()` and `check_availability()` build from a single private helper, so a contract change cannot land in one and miss the other. `docs/DEVELOPMENT_STANDARDS.md` §3.6.
- **DR7 — one payload policy per provider, not per model.** A policy row per model is a register that drifts. The policy states what this provider sends; whether the configured model accepts it is a question for the capability check, in its own issue.
- **DR8 — the policy file declares what we _send_, never what a model _supports_.** `"thinking": "disabled"` is a decision and belongs there. `"supports_temperature": false` is a fact about a vendor's model and must not appear in any file in this repository — that is the maintained capability matrix issue #79 rejected, and `_FALLBACK_MODEL` is what it looks like when it goes stale.
- **DR9 — file ownership.** `config/ai_settings.json` owns *which provider and how it is orchestrated*: `enabled`, `model`, `api_key_env`, costs, rate limits, retry, `report_types` routing, fallback, cost tracking. `config/providers/<name>_settings.json` owns *how we talk to that provider*: the request payload policy. No key appears in both.
- **DR10 — an unusable policy is a configuration error, not a default.** Absent, unparseable, **or missing a key the provider requires** — all three raise `ConfigurationError`, and the failure must reach the caller rather than being absorbed into `ProviderManager._disabled`. A file that parses but has `thinking` dropped or misspelled produces exactly the payload that returns 400 on `claude-sonnet-5`, which is the defect this issue exists to fix; guarding only absence and syntax lets it back in silently.
- **DR11 — policy values are the vendor's own shapes, passed through verbatim.** `claude_settings.json` holds `"thinking": {"type": "disabled"}` — the literal Anthropic parameter object — and the provider passes it into the request untranslated. No `"disabled"` string that a loader maps to an object: a translation layer would only understand the values someone thought to write, which is DR8's register moved from a file into an `if`. `sampling` is an object mapping API parameter name to either a literal value or the single sentinel `"from_request"`, meaning read it off the `GenerationRequest`; `{}` sends nothing. What makes "changeable without code" true is that a value the vendor accepts can be typed into the file and works.
- **DR12 — the policy read goes through `ConfigLoader`.** `workmain/config_manager/loader.py` already owns JSON config loading, and `ConfigLoader.load('providers/claude_settings')` resolves correctly — the nested name joins onto `config_dir` without changing its pattern. `docs/DEVELOPMENT_STANDARDS.md` §3.6. `ProviderManager`'s pre-existing hand-rolled `ai_settings.json` read is left alone; that inconsistency is deliberate and bounded to one method.

Anything this spec does not cover: stop at the current step and escalate per `CLAUDE.md` Role 3. In particular, if a call site's `max_tokens` looks too small, that is a design decision — do not raise it.

## 4. Steps

Each step ends with a commit.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `config/providers/claude_settings.json`, `gemini_settings.json` and `ollama_settings.json`. Claude: `{"thinking": {"type": "disabled"}, "sampling": {}}`. Gemini: `{"sampling": {"temperature": "from_request"}}`. Ollama: empty policy, with a `description` recording that its generation parameters are Modelfile-baked and set outside this repository. Each file carries a `description` naming DR8's boundary. (DR7, DR8, DR11) | `config/providers/*.json` |
| 2 | Policy loading via `ConfigLoader.load('providers/<name>_settings')`, **before** the provider is constructed and therefore outside the existing `try/except Exception` that absorbs construction failures into `_disabled` — so an unusable policy surfaces instead of silently disabling a provider. Absent, unparseable, or missing a required key raises `ConfigurationError`. The loaded policy is passed to the provider at construction. (DR10, DR12) | `workmain/ai/provider_manager.py` |
| 3 | `ClaudeProvider` builds its payload from policy. Add `_base_api_params(max_tokens)` returning `model`, `max_tokens` and the policy's `thinking`, and nothing else; `generate()` adds `messages` plus the conditional `system`, `check_availability()` uses it with `max_tokens=1`. The literal `temperature` key is deleted. (DR1, DR2, DR6) | `workmain/ai/providers/claude.py` |
| 4 | `GeminiProvider` reads its sampling from policy rather than hardcoding `temperature`. Behaviour is unchanged — this step exists so both providers answer to the same mechanism. (DR9) | `workmain/ai/providers/gemini.py` |
| 5 | Fail fast on permanent failures. **Inside** the existing `except APIError` handler, as its first statement: if the error is an `APIStatusError` whose `status_code` is below 500 and not 408, 409 or 429, set `ProviderStatus.ERROR` and raise `GenerationError` from it with the API's message — no sleep, no further attempt. The backoff below is untouched, so 5xx, 408/409/429 and `APIConnectionError` retry exactly as they do today. Do **not** add a sibling `except` clause. (DR4) | `workmain/ai/providers/claude.py` |
| 6 | Delete `_FALLBACK_MODEL`; `self.model = config.get('model')`. Update the `GenerationRequest.temperature` docstring. (DR5, DR1) | `workmain/ai/providers/claude.py`, `workmain/ai/base_provider.py` |
| 7 | Offline tests, vendor clients patched, no network. `ClaudeProvider.__init__` reads its key from the environment and `validate_config()` rejects anything not prefixed `sk-ant-`, so these tests patch the environment with a well-formed fake key as well as the client. Cover: no sampling key and `thinking == {"type":"disabled"}` in the `generate()` payload; the same for `check_availability()`; a 400 raises after exactly one call; a 500 still retries `retry_attempts` times; a 401 fails fast; missing `model` raises `ConfigurationError`; a policy file that is absent, unparseable, or present-but-missing `thinking` each raises `ConfigurationError`; an unusable policy propagates out of `ProviderManager` rather than landing in `_disabled`; Gemini's sampling comes from its policy file. | `tests/test_ai_clients.py` |
| 8 | Point config at a current model: `model: "claude-sonnet-5"`, `notes` rewritten, `last_updated` bumped. Delete the unread `default_max_tokens` and `default_temperature` keys from the `claude` and `gemini` blocks. (DR9) **Do not set the price fields** — `cost_per_1k_prompt_tokens`, `cost_per_1k_completion_tokens` and `cost_structure` are Ray's, set whenever a model is updated. Stop here and tell him the model changed; the expected values as of 20260902 are `0.002` / `0.010`, "$2/MTok prompt, $10/MTok completion". | `config/ai_settings.json` |
| 9 | Live verification: `workmain providers test claude`. Record content and `stop_reason` in the results artifact. | none |
| 10 | Version bump to v1.32.0, CHANGELOG entry, PR `dev` → `main`. | `workmain/__version__.py`, `CHANGELOG.md` |

### Authorization points

**None** as defined by `docs/DEVELOPMENT_STANDARDS.md` §1.4 — no migration, no GitHub object deletion, no force-push, no service run-state change. Step 10 opens the PR and stops; Ray merges. A post-merge restart applies — `feature/*` branch.

## 5. Acceptance criteria

Numbered to issue #79's fourteen criteria, in the order they appear there.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Each provider's request payload policy is declared in configuration, so changing what Claude sends for thinking, or what Gemini sends for sampling, requires no code edit. (DR7, DR9) | `grep -n "temperature" workmain/ai/providers/claude.py workmain/ai/providers/gemini.py` showing no literal sampling value in either payload construction; `pytest tests/test_ai_clients.py -k policy` |
| AC2.1 | Nothing about a provider's request payload is left in the orchestration file: `ai_settings.json` carries no sampling or payload key for any provider, and no key name appears in both files. (DR9) | `python -c "import json,glob,pathlib;a=json.load(open('config/ai_settings.json'))['providers'];[print(n, set(c) & set(json.load(open(f'config/providers/{n}_settings.json'))), {'default_temperature','default_max_tokens'} & set(c)) for n,c in a.items()]"` printing two empty sets per provider |
| AC3.1 | No file in the repository records what a vendor's model *supports*; the policy files declare only what we *send*. (DR8) Property of a document; **check is a stated reading by Ray** of both files under `config/providers/`, read for whether any key asserts a model capability rather than a choice. | Ray's reading |
| AC4.1 | An unusable policy — absent, unparseable, or missing a key the provider requires — fails loudly rather than falling back to a built-in default or silently disabling the provider, so the #79 payload cannot return through a typo. (DR10) | `pytest tests/test_ai_clients.py -k policy_error`, covering all three cases at the provider *and* at `ProviderManager`, asserting the error propagates rather than landing in `_disabled` |
| AC5.1 | The payload `generate()` hands to the SDK carries no sampling parameter — the provider never asks a model to sample at a temperature it may reject. (DR1) | `pytest tests/test_ai_clients.py -k claude_payload`, asserting `temperature`, `top_p`, `top_k` all absent from captured kwargs |
| AC6.1 | `generate()` declares thinking off, so `max_tokens` bounds response text alone at every call site regardless of the configured model. (DR2) | same test, asserting `thinking == {"type": "disabled"}` |
| AC7.1 | `check_availability()` sends the identical contract, so the availability probe cannot pass on a payload shape the real request would fail on. (DR6) | `pytest tests/test_ai_clients.py -k claude_payload`; `grep -n "_base_api_params" workmain/ai/providers/claude.py` returning both call sites |
| AC8.1 | A reader of `GenerationRequest` can tell which providers honour `temperature` without opening a provider. (DR1) Property of a document; **check is a stated reading by Ray** of the docstring, read for whether it names both the provider that ignores the field and the one that reads it. | Ray's reading |
| AC9.1 | A request the API has permanently rejected costs one attempt rather than `retry_attempts`, and surfaces the API's own message — for any 4xx other than 408, 409 and 429. (DR4) | `pytest tests/test_ai_clients.py -k claude_no_retry_on_4xx`, asserting the error propagates and `messages.create` was called exactly once |
| AC10.1 | Transient failures still retry — a 500 is attempted `retry_attempts` times before failing. (DR4) | `pytest tests/test_ai_clients.py -k claude_retries_on_500` |
| AC11.1 | The provider holds no copy of the configured model: a config without `model` fails at construction rather than silently running a stale hardcoded one. (DR5) | `grep -rn "_FALLBACK_MODEL" workmain/` returning zero hits; `pytest tests/test_ai_clients.py -k claude_requires_model` |
| AC12.1 | The deployed configuration names a current-generation model, and its two numeric cost fields, its `cost_structure` string, and the vendor's published rate for that model all agree — so cost tracking is not silently wrong in either direction. Reading the fields back proves only that the file was edited; **the check is Ray's reading** of the `providers.claude` block alongside the live pricing page at close-out. | Ray's reading, against `python -c "import json;c=json.load(open('config/ai_settings.json'))['providers']['claude'];print(c['model'],c['cost_per_1k_prompt_tokens'],c['cost_per_1k_completion_tokens'],c['cost_structure'])"` |
| AC13.1 | The provider works end to end against a current model — non-empty content with `stop_reason` of `end_turn`, not `max_tokens`, proving the twenty-token budget went to response text and not to thinking. | `workmain providers test claude` |
| AC14.1 | No existing behaviour regressed — full suite green with a net gain over the v1.31.0 baseline of 972. | `pytest` reporting at least 972 passed, 0 failed |

## 6. Test plan

- **Baseline before this work:** 972 passed, 0 failed (CHANGELOG v1.31.0). `pytest automation/` 51 passed, separately.
- **Expected after:** 984–990 passed. Roughly a dozen new tests in Step 7; no existing test deleted.
- `tests/test_ai_clients.py` is the established home for provider coverage and gains its first offline section. These tests patch the vendor clients so they run under `SKIP_API_TESTS=1` and without keys — they are unit tests of the payload contract, not API tests, and must not sit behind the `SKIP_API_TESTS` gate. Per `docs/DEVELOPMENT_STANDARDS.md` §6.

## 7. Risks and rollback

- **`claude-sonnet-5` behaves differently from Sonnet 4.5 for report generation.** Blast radius is bounded: Claude is the *fallback* provider for all three report types, never primary (`config/ai_settings.json` → `report_types`), so a regression degrades the fallback path. Rollback: revert Step 8 alone; Steps 1–7 are correct for Sonnet 4.5 too.
- **Thinking disabled can let a model write reasoning into visible response text.** Not mitigated here — every affected caller passes through review or an `$EDITOR` step before anything is sent. If it appears in practice it is a new issue against the prompt builder.
- **The config restructure touches provider construction, which every AI path depends on.** A policy-loading defect fails every provider at once rather than degrading. Mitigated by DR10 making the failure loud and immediate at construction, and by Step 7's policy tests; Step 4 deliberately leaves Gemini's behaviour unchanged so the mechanism is exercised by two providers before anything else depends on it.
- **Rollback overall:** ten commits on a `feature/*` branch, no migration and no schema change. Step 8 should not outlive Step 3 — a current model in config without the payload fix is exactly the 400 in issue #79.
