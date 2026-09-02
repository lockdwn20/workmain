# ClaudeProvider — Current-Generation Model Compatibility — Design Study

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20260902
**Originating item:** Issue #79

---

## 1. Purpose

Issue #79 reports that `ClaudeProvider` cannot run a current-generation Claude model: it sends `temperature` on every request, and current models reject the sampling parameters with a 400. The issue also proposes a direction — strip the sampling parameters and send `thinking: {"type": "disabled"}` — and rejects one alternative.

This study answers a question the issue could not: **what does committing to disabled thinking actually cost us, and is it still the right call once the full model matrix is known?** The recon behind it also surfaced a second payload site, a verified-false acceptance criterion, and three adjacent defects, each of which needs a scope decision before a spec can be written. The options in §4 are the substance; the findings in §3 are what forced them.

## 2. Scope of the read

**Read:**

- `workmain/ai/providers/claude.py` in full — every `messages.create` call site, the exception handling, the constants, `count_tokens`, `check_availability`.
- `workmain/ai/base_provider.py` — `GenerationRequest` only.
- `workmain/ai/providers/gemini.py` and `ollama.py` — `temperature` handling only, to confirm #79's claim that they are unaffected.
- Every `max_tokens` in `workmain/` (`grep -rn "max_tokens" --include=*.py workmain/`), to find which call sites a change in `max_tokens` semantics would truncate.
- `tests/test_ai_clients.py` in full, plus a tree-wide search for any other `ClaudeProvider` coverage.
- `config/ai_settings.json` — the `providers.claude` block and the `report_types` routing that decides when Claude is reached at all.
- The installed `anthropic` SDK (0.75.0) — exception class hierarchy and `ThinkingConfigDisabledParam` — verified by execution, not by recall.
- Anthropic's current per-model rules for `thinking`, sampling parameters, and `max_tokens` semantics, via the bundled `claude-api` skill.

**Deliberately not read:**

- Prompt content — `prompt_builder.py`, the report templates, the condensation and narration system prompts. Output *quality* under a new model is a separate question from whether the request is accepted, and this study answers only the second. Q5 records the one place the two touch.
- Gemini and Ollama beyond the `temperature` confirmation above.
- Cost history and the cost tracker. Repricing is arithmetic in a config file, not a design question.
- `requirements.txt` pinning policy.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | `generate()` sends `temperature` unconditionally, in a literal `api_params` dict holding `model`, `max_tokens`, `temperature`, `messages`. No `thinking` key, so the model's default thinking behaviour applies — which on a current model means adaptive, and means `max_tokens` caps thinking *plus* response. | `workmain/ai/providers/claude.py:92-101`, `ClaudeProvider.generate` | Critical |
| F2 | **`check_availability()` builds a second, independent `messages.create` payload** — `max_tokens=1`, no `temperature`, no `thinking`. Issue #79 does not mention it. Fixing only `generate()` leaves the availability probe running a different contract from the request it is meant to vouch for, and `providers test` calls `check_availability()` before it calls `generate()`. | `workmain/ai/providers/claude.py:222-226`, `ClaudeProvider.check_availability`; `workmain/cli/commands/providers.py:143` | High |
| F3 | The `APIError` handler retries every `APIError` with exponential backoff. `BadRequestError` (400) is a subclass of `APIStatusError`, itself a subclass of `APIError` — so a permanently invalid request is retried `retry_attempts` times. This is the "failed after 3 attempts" in #79. `AnthropicRateLimitError` is already caught ahead of it and correctly not retried. | `workmain/ai/providers/claude.py:132-151`; `anthropic.BadRequestError.__mro__` → `BadRequestError → APIStatusError → APIError → AnthropicError`, verified by execution against the installed 0.75.0 | High |
| F4 | `_FALLBACK_MODEL = "claude-sonnet-4-5-20250929"` is a hardcoded copy of a config value, used whenever `model` is absent. `validate_config()` — already called from `__init__` — raises `ConfigurationError` when `self.model` is falsy, so the constant is the *only* thing standing between a missing config key and a loud failure. | `workmain/ai/providers/claude.py:34`, `:55`, `:70-71`, `:181-182` | Medium |
| F5 | **Issue #79's test AC is false as written.** It names `tests/test_ai_clients.py` lines 124, 161, 286, 298, 328 as "assertions on `temperature`". All five are `GenerationRequest(...)` *constructions* inside tests gated on `SKIP_API_TESTS`, and all five stay valid — `temperature` remains a live field that `GeminiProvider` reads. The AC as worded is satisfied by changing nothing. | `tests/test_ai_clients.py:124, 161, 286, 298, 328`; gate at `:36`; `workmain/ai/providers/gemini.py:100` | High |
| F6 | **No test anywhere asserts what `ClaudeProvider` sends.** `tests/test_ai_clients.py` contains no `patch`, no `MagicMock`, and no reference to `messages.create`; every Claude test in it is a live-API test. The payload contract #79 is about is entirely unguarded. | `grep -rn "messages.create\|MagicMock\|patch" tests/test_ai_clients.py` returns zero hits | High |
| F7 | The smallest Claude-reachable budget in the tree is `max_tokens=20` (`providers test`). `narration.py` uses 200. `note_condenser.py` already uses 1024 — it was raised from 200 for exactly this class of problem, and the inline comment says so: "Gemini 2.5 Flash thinking tokens count against this budget; 200 caused truncation". `daemon.py:266`'s `max_tokens=1` is an Ollama warm-up and never reaches Claude. #79's finding 2 cites `note_condenser.py:142` at 200; that is stale. | `workmain/cli/commands/providers.py:155`; `workmain/daemon/narration.py:57`; `workmain/ai/note_condenser.py:141`; `workmain/daemon/daemon.py:250-266` | High |
| F8 | Claude is the **fallback** provider for all three report types, never the primary — Gemini is primary for `daily_internal`, `weekly_client` and `note_condensation`. A Claude regression degrades the fallback path, not the primary one. | `config/ai_settings.json` → `report_types.*.primary_provider` / `.fallback_provider` | Medium |
| F9 | `count_tokens()` calls `self.client.count_tokens(text)`. That method does not exist on the `anthropic` 0.75.0 client — the current binding is `client.messages.count_tokens(model=..., messages=...)`. The call raises on every invocation and the bare `except Exception` silently returns `len(text) // 4`. Token counts from this provider have always been an estimate mislabelled as a count. | `workmain/ai/providers/claude.py:110-113` | Medium |
| F10 | The provider's own retry loop (`retry_attempts: 3`) sits on top of the SDK client's own retry default of 2, and `Anthropic(api_key=...)` is constructed without overriding it. A 429 or 5xx can therefore be attempted up to nine times with two independent backoff schedules. | `workmain/ai/providers/claude.py:68`; `config/ai_settings.json` → `providers.claude.retry_attempts`; SDK `max_retries` default 2 | Low |
| F11 | `default_max_tokens` and `default_temperature` in the `providers.claude` and `providers.gemini` config blocks are read by no code. | `grep -rn "default_temperature\|default_max_tokens" --include=*.py workmain/ tests/` returns zero hits | Low |
| F12 | `timeout_seconds: 60` in the claude config block is read by no code either — already tracked as issue **#114**, open and awaiting placement. | `config/ai_settings.json` → `providers.claude.timeout_seconds`; issue #114 | Low |
| F13 | The installed SDK carries the parameter type the proposed direction needs: `anthropic.types.ThinkingConfigDisabledParam` → `{'type': Required[Literal['disabled']]}`. No dependency change is required to implement Option A below. | `anthropic` 0.75.0, verified by execution | Low |
| F14 | Current per-model rules, from the bundled `claude-api` skill. `temperature` / `top_p` / `top_k` are **removed and return 400** on Fable 5, Opus 5, Opus 4.8, Opus 4.7 and Sonnet 5 — so #79's defect is not specific to Sonnet 5. `thinking: {"type": "disabled"}` is **accepted** on Sonnet 5, Opus 4.8 and Opus 4.7; accepted on Opus 5 only at effort `high` or below; and **rejected with a 400 on Fable 5 and Mythos 5**, where thinking is always on. Omitting `thinking` runs adaptive on Sonnet 5 and Opus 5, but runs *without* thinking on Opus 4.8 and 4.7. | `claude-api` skill, Thinking & Effort matrix | Critical |

**Asserted, not verified:** F14 is documentation, not something this tree can execute. Step 6 of the resulting spec — a live `workmain providers test claude` — is what converts the Sonnet 5 row of it into a verified fact for this project. Nothing else in this table is unverified.

## 4. Options

The decision is F14. `max_tokens` has one meaning when thinking is off and a different meaning when it is on, and the model named in `config/ai_settings.json` decides which — so the provider either pins that meaning or every call site inherits it. Three ways to pin it, and they differ in what they foreclose.

### Option A — send `thinking: {"type": "disabled"}` on every request

- **Approach:** the provider always declares thinking off. `max_tokens` means response tokens, on every model, at every call site, permanently. Issue #79's proposed direction.
- **Pros:** No call-site budget audit — F7's twenty-token `providers test` and two-hundred-token narration keep working untouched. No caller has to know which model config names. Repointing the model becomes a one-line config edit again, which is the property #79 is really asking for. Cheapest per request: no thinking tokens billed on a fallback path that exists to be cheap and fast (F8).
- **Cons:** Forecloses `claude-fable-5` and `claude-mythos-5` outright — they 400 on it (F14). Constrains Opus 5 to effort `high` or below. Gives up any quality gain adaptive thinking might bring to report generation. Carries a known behaviour where a thinking-off model can write reasoning into visible response text — see Q5.

### Option B — omit `thinking` entirely

- **Approach:** send no thinking key; whatever the model does by default is what happens.
- **Pros:** Every model works, Fable included. Report generation gets adaptive thinking on Sonnet 5 for free, which may improve output.
- **Cons:** `max_tokens` silently changes meaning with the model named in config — the exact failure mode F7 records `note_condenser` already having been bitten by once, on Gemini. Requires auditing and raising every Claude-reachable budget, and re-auditing on every model change, because a budget that is generous under one model truncates under the next. Behaviour is also *non-uniform*: adaptive on Sonnet 5 and Opus 5, off on Opus 4.8 and 4.7 (F14), so "omit" does not even mean one thing. Costs thinking tokens on every call, including a twenty-token connectivity check.

### Option C — a `thinking` key in `config/ai_settings.json`

- **Approach:** `providers.claude.thinking: "disabled" | "adaptive"`, read at construction, passed through.
- **Pros:** Fable 5 becomes reachable by editing config. The switch sits next to `model`, where the person changing the model already is.
- **Cons:** It is a switch that cannot be safely flipped. Flipping it to `adaptive` silently changes what every call site's `max_tokens` means, with no code able to compensate — it converts a 400 you see immediately into truncated report output you may not notice. The value that makes Fable work is the value that breaks `providers test` and narration. Shipping a configuration option whose documentation has to say "do not use this without first auditing six call sites" is worse than not shipping it: it is Option B's cost with an extra surface, and it invites the failure at a moment when nobody is looking at this code.

**Recommendation: Option A.** It is what #79 proposed, and the model matrix in F14 — which #79 did not have — strengthens rather than weakens it. The property the project needs is that `max_tokens` means one thing; A is the only option that delivers it. What A forecloses costs us nothing real: Claude is a *fallback* provider for plain text generation under cost tracking (F8), and Fable-tier pricing has no place on that path. The constraint belongs in the config `notes` field, next to `model`, where the next person to change the model will read it — not in a model-capability table inside the provider, which is the parallel path #79 already rejected and which `docs/DEVELOPMENT_STANDARDS.md` §3.6 rules out anyway.

Two consequences follow from A and are not separate choices. First, F2: if the provider pins a payload contract, it pins it once — `generate()` and `check_availability()` build from a single helper, or the next contract change lands in one and misses the other. Second, F13: no dependency change is needed.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Accept Option A's foreclosure of `claude-fable-5` / `claude-mythos-5`, and Opus 5 at effort ≤ high (F14)? | |
| Q2 | F4 — issue #79's AC asks that `_FALLBACK_MODEL` be kept in sync with `config/ai_settings.json`. That is a hand-maintained copy of config state, and #79 exists *because* nobody kept it in sync. Delete the constant instead and let the existing `validate_config()` raise on a missing `model`? Same defect closed, nothing left to drift. Departs from the AC as worded; restated at close-out. | |
| Q3 | F3 — #79's AC names HTTP 400 specifically. The same handler retries 401, 403, 404, 413 and 422 just as pointlessly. Fix the class (non-retryable 4xx, excluding 408/409/429, every 5xx untouched) rather than the instance? | |
| Q4 | F9, F10, F11 — three adjacent defects found during this read. Recommendation: all three out of scope, F9 as its own issue at close-out, F10 and F11 recorded here only. Confirm, or pull any of them in? | |
| Q5 | A thinking-off current model can write reasoning into visible response text, and the documented mitigation is a line of system-prompt wording. Every affected caller's output passes through review or an `$EDITOR` step before it goes anywhere, and prompt content was deliberately outside this read (§2). Recommendation: no prompt change now; if it appears in practice it is a new issue against the prompt builder. Confirm? | |
| Q6 | F5/F6 — #79's test AC is false as written and goes green by doing nothing. Replace it with an offline payload-contract test (the coverage F6 shows is entirely missing), and restate the issue AC at close-out? | |

## 6. Disposition

- Promoted to: `../specs/CLAUDE_PROVIDER_CURRENT_MODEL_SPEC.md` — drafted 20260901, pending answers to Q1–Q6.
