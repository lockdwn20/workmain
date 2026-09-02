# Provider Model Capability — Making a Model Swap Safe — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20260902
**Originating item:** Ray request, 20260902 — raised out of issue #79

---

## 1. Purpose

Issue #79 is being treated as a payload defect. Ray's reframing is the more important question: *why did editing one string in `config/ai_settings.json` break a provider at all?* A model swap is presented by this project as configuration, and it is not — it is an unversioned contract change with a vendor, and the provider classes hardcode one side of that contract.

This study answers: **what can we actually know about a model before we point config at it, where does that knowledge come from, and what shape of solution does that make possible?** It is written against live data pulled from both vendor APIs on 20260902, not against documentation.

## 2. Scope of the read

**Read:** the Anthropic Models API (`client.models.list`, 11 models) and the Google Generative Language models endpoint (`v1beta/models`, 54 models / 40 supporting `generateContent`), both queried live with the project's own keys. Three empirical probes against `claude-sonnet-5` to test parameters the metadata does not describe. `workmain/ai/providers/{claude,gemini,ollama}.py` for what each currently hardcodes.

**Deliberately not read:** Ollama capability discovery. Per `CLAUDE.md`, generation parameters for `workmain-intent` are baked into the Modelfile and rebuilt outside this repository; it has no model-swap problem of this kind. Prompt quality under any model. Cost/benefit of any specific model choice — this study is about *knowing*, not about *choosing*.

## 3. Findings

### 3a. What the vendors expose

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | The Anthropic Models API returns a structured `capabilities` object per model, including `thinking.supported`, `thinking.types.{enabled,adaptive}.supported`, and `effort.{low,medium,high,xhigh,max}.supported`, plus `max_input_tokens` and `max_tokens`. | `client.models.list()`, 11 models, live 20260902 | High |
| F2 | **The Anthropic capability object says nothing about sampling parameters.** The full key set is `batch, citations, code_execution, context_management, effort, image_input, pdf_input, structured_outputs, thinking`. There is no `temperature`, `top_p`, `top_k`, or `sampling` key. The single fact that broke #79 is not discoverable from the metadata. | same call; key set enumerated | Critical |
| F3 | **It also says nothing about whether `thinking: {"type": "disabled"}` is accepted.** `thinking.types` enumerates only `enabled` and `adaptive`. The second fact the #79 fix depends on is likewise undiscoverable. | same call | Critical |
| F4 | The Google models endpoint *does* expose sampling: every `generateContent` model carries `temperature` (default), `maxTemperature`, `topP`, `topK`, plus `inputTokenLimit`, `outputTokenLimit`, `thinking`, and `supportedGenerationMethods`. Exactly one of 40 lacks `maxTemperature` (`antigravity-preview-05-2026`). | `v1beta/models`, live 20260902 | High |
| F5 | The two vendors expose *disjoint* capability sets. Anthropic describes thinking and effort but not sampling; Google describes sampling but not thinking modes. Neither exposes everything the other does, and no common schema exists. | F1, F2, F4 | High |

### 3b. What the live data proves about drift

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F6 | `claude-fable-5-1` exists, created **2026-08-28** — five days before this study, and newer than any documentation available to this project. Models land continuously and without notice. | `models.list()` | High |
| F7 | On the Anthropic side, thinking mode and sampling acceptance correlate perfectly across all 11 models: every `enabled=Y, adaptive=n` model is prior-generation and accepts `temperature`; every `enabled=n, adaptive=Y` model is current-generation and rejects it. `claude-opus-4-6` and `claude-sonnet-4-6` support both modes and sit on the boundary. **This is a correlation observed in one snapshot, not a documented contract** — it is exactly the kind of inference that breaks on the next model drop, and it must not be turned into code. | matrix below | Medium |
| F8 | `claude-sonnet-4-5-20250929` — the model `config/ai_settings.json` names **today** — now reports `max_input_tokens: 1000000`. It shipped as a 200K-context model. **A pinned, dated model snapshot had its advertised capability change underneath us.** Pinning a version does not freeze the contract. | `models.list()` | High |
| F9 | `config/ai_settings.json` names `gemini-3.5-flash-lite`. Live listing shows `gemini-3.6-flash`, `gemini-3.7-flash` and `gemini-3.8-flash` also available. The config is several generations behind on that line and nothing in the system says so. | `v1beta/models`; `config/ai_settings.json` | Medium |

**Anthropic thinking/effort matrix, live 20260902:**

| Model | in / out | thinking `enabled` | thinking `adaptive` | effort |
| --- | --- | --- | --- | --- |
| `claude-fable-5` | 1M / 128K | no | yes | low…max |
| `claude-fable-5-1` | 1M / 128K | no | yes | low…max |
| `claude-opus-5` | 1M / 128K | no | yes | low…max |
| `claude-opus-4-8` | 1M / 128K | no | yes | low…max |
| `claude-opus-4-7` | 1M / 128K | no | yes | low…max |
| `claude-sonnet-5` | 1M / 128K | no | yes | low…max |
| `claude-opus-4-6` | 1M / 128K | yes | yes | low,medium,high,max |
| `claude-sonnet-4-6` | 1M / 128K | yes | yes | low,medium,high,max |
| `claude-opus-4-5-20251101` | 200K / 64K | yes | no | low,medium,high |
| `claude-sonnet-4-5-20250929` | 1M / 64K | yes | no | — |
| `claude-haiku-4-5-20251001` | 200K / 64K | yes | no | — |

### 3c. What a probe proves that metadata cannot

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F10 | Three throwaway requests against `claude-sonnet-5` (`max_tokens=16`, prompt `"hi"`, SDK retries disabled) settled both undiscoverable facts in under a second: `temperature=0.0` → **HTTP 400 `invalid_request_error`**; `thinking={"type":"disabled"}` → **accepted**; no thinking key and no sampling → accepted. Total spend: a fraction of one cent. | live probe, 20260902 | Critical |
| F11 | F10 converts the two central assumptions of `CLAUDE_PROVIDER_CURRENT_MODEL_SPEC.md` (DR1, DR2) from documentation-derived claims into facts verified against this project's own account and key. | F10; that spec §2, last row | High |

### 3d. What the providers hardcode today

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F12 | `ClaudeProvider` hardcodes a literal `api_params` dict — the payload shape is fixed at author time and cannot vary by model. | `workmain/ai/providers/claude.py:92-101` | High |
| F13 | `GeminiProvider` hardcodes `temperature` into its generation config the same way, with no reference to the `maxTemperature` the vendor publishes per model. | `workmain/ai/providers/gemini.py:100` | Medium |
| F14 | Nothing anywhere validates that the `model` string in `config/ai_settings.json` names a model that exists, let alone one whose contract matches what the provider sends. The first signal is a 400 at generation time — and per #79 finding 3, that 400 is then retried three times before it surfaces. | `config/ai_settings.json`; `workmain/ai/providers/claude.py:136-151` | Critical |

### 3e. Is the option *set* stable within a vendor?

Raised by Ray, 20260902: *the available options stay the same within a provider; only defaults change without warning.* Checked against the live pull — **it holds for Google and fails for Anthropic**, and the failure is on the side that broke us.

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F15 | **Google — option set stable, values vary.** 39 of 40 `generateContent` models carry all four of `temperature`, `maxTemperature`, `topP`, `topK`; only `antigravity-preview-05-2026` lacks them. What varies is values: `maxTemperature` is 2 on 32 models and 1 on 7 (the image models); `topK` is 64 on all 39. `thinking` is absent on 6 (TTS, image and audio models). So for Google the premise is correct — the knobs are constant, the ranges and defaults move. | `v1beta/models`, live 20260902 | High |
| F16 | **Anthropic — the option set itself changes across generations.** `temperature` / `top_p` / `top_k` are not re-defaulted on current models, they are *removed*: the probe returns `400 invalid_request_error`, not a clamped value (F10). `thinking.types.enabled` is likewise gone on 6 of 11 models, `effort` is absent entirely on 3, and `xhigh` was added to the effort set partway through the family. Six of eleven models — every current-generation one — accept a strictly different parameter set from the other five. | `models.list()` matrix in §3b; F10 | Critical |
| F17 | The consequence for design: a check built on "validate the defaults" detects F15 and is **blind to F16**. Issue #79 is an F16 event — a parameter that stopped existing, not one whose default moved. A checker that only compares values against published ranges would have passed `claude-sonnet-5` and let the same 400 through. | F10, F15, F16 | Critical |
| F18 | Compounding it: Anthropic publishes no sampling metadata at all (F2), so for the one vendor whose option set *does* change, there is no published option set to diff against. Detecting F16 requires the probe; there is no metadata-only route to it. | F2, F16 | Critical |

### 3f. How much of each catalogue is even addressable

Raised by Ray, 20260902: models for media, imaging and similar are of no use to WorkmAIn and the design should not carry weight for them. Checked against the live pull — **the filtering problem is entirely one-sided.**

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F19 | **Anthropic returns 11 models and every one is general-purpose text.** No image, TTS, audio, video or embedding models appear in the listing at all. There is nothing to filter. | `models.list()`, live 20260902 | Medium |
| F20 | **Google returns 54 models, of which 17 are general-purpose text.** The rest: 6 image, 7 audio/music, 3 video, 3 TTS, 3 embedding, 15 live/robotics/research/other. Drop previews and floating aliases from the 17 and **nine** remain as realistic candidates — `gemini-3.8/3.7/3.6/3.5-flash`, `gemini-3.5-flash-lite` (configured), `gemini-3.1-flash-lite`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.5-pro`. | `v1beta/models`, live 20260902 | Medium |
| F21 | All nine Google candidates are configuration-identical: 1,048,576 in / 65,536 out, `maxTemperature` 2, `topP` 0.95, `topK` 64, `thinking` true. Within the addressable set, a Gemini model swap changes nothing about the request contract. | same | Medium |
| F22 | Google publishes four `-latest` floating aliases (`gemini-flash-latest`, `gemini-flash-lite-latest`, `gemini-pro-latest`, `gemini-flash-latest-high-res-exp`). These move underneath a caller with no version change at all — F8's problem in a worse form. `config/ai_settings.json` pins an explicit name today and should continue to. | same | Medium |
| F23 | `gemini-3.8-flash` reports its `version` field as `"3.0"`. Published vendor metadata is not automatically self-consistent, which bounds how much any derived design should trust a single field. | same | Low |
| F24 | Consequence for design: **candidate filtering is a per-provider adapter concern, not a shared one.** Anthropic needs no filter; Google needs one that drops two-thirds of its catalogue. This is a second reason the adapter shape is right — vendors differ not only in what they publish (F5) but in what fraction of their catalogue is addressable at all. | F19, F20 | High |
| F25 | The Anthropic sampling boundary lands precisely at `claude-opus-4-7` and `claude-sonnet-5`. `claude-opus-4-6` and `claude-sonnet-4-6` straddle it — both thinking modes, sampling still accepted — and every model from 4-7 / sonnet-5 forward is adaptive-only with sampling removed. | §3b matrix; F10 | Medium |

## 4. Options

The constraint that decides this is **F2 + F3**: the two facts that actually broke us are the two Anthropic does not publish. Any design resting purely on vendor metadata has a hole exactly where the wound is.

### Option A — a maintained capability matrix in the repo

- **Approach:** a checked-in table of model → supported options, updated by hand when a model is added or proposed.
- **Pros:** covers what metadata omits, because a human writes it. No network dependency. Readable in a diff.
- **Cons:** it is a hand-maintained copy of someone else's state, which is the failure mode #79 already *is* — `_FALLBACK_MODEL` is a one-row capability matrix, and it went stale. The live data shows it would already be wrong: it would not contain `claude-fable-5-1` (F6), and it would still assert 200K for `claude-sonnet-4-5` (F8). It goes stale silently and is trusted precisely when nobody has checked it. Rejected in-provider by issue #79 on the same grounds, and by `docs/DEVELOPMENT_STANDARDS.md` §3.6.

### Option B — derive everything from the vendor metadata APIs

- **Approach:** query `models.list` / `v1beta/models` and drive behaviour from the published `capabilities`.
- **Pros:** always current, zero maintenance, single source of truth per vendor. Genuinely strong for what it does cover — limits, thinking modes, effort levels, Gemini sampling ranges, and "does this model even exist" (F14).
- **Cons:** **does not cover the two facts that matter** (F2, F3). Building only this and declaring the problem solved would leave us confident and still exposed. The tempting patch — inferring sampling support from thinking mode (F7) — is a one-snapshot correlation and would be a register in disguise, worse than Option A because it *looks* derived.

### Option C — derive what is published, probe what is not

- **Approach:** one command, `workmain providers check [--model X]`, that for a candidate model (a) pulls the vendor's own model object and reports limits, thinking modes, effort and — for Gemini — sampling ranges; (b) fires a small set of single-parameter throwaway requests to *measure* the facts metadata omits, reading accept/reject off the real API; (c) compares the result against what the configured provider actually sends and prints a verdict. Run it before editing config, and on demand.
- **Pros:** derivation where derivation works, measurement where it does not — nothing hand-maintained anywhere. F10 shows the probe half already works and costs a fraction of a cent. It answers the question a person actually has ("can I point config at this?") rather than publishing a table they must interpret. It closes F14 as a side effect: a model that does not exist fails the check. It degrades honestly — a probe that cannot run reports that, rather than reporting a guess. And the probe set is small and stable, because it tests *our* payload contract, not the vendor's whole surface.
- **Cons:** spends real tokens, in cents. Requires live network and valid keys to run. New CLI surface and its own tests. Does not make the providers dynamic — the payload contract stays fixed and conservative; this tells you whether a model fits it.

### Option D — providers negotiate their payload per model at runtime

- **Approach:** provider resolves a capability descriptor at construction and builds its payload from it.
- **Pros:** the only option where "providers are hardcoded" stops being literally true.
- **Cons:** puts a vendor API call and a network failure mode into provider construction — on every CLI invocation and every daemon trigger — for a value that changes a few times a year. Caching it moves the problem to invalidation. Worse, it cannot work: the descriptor would be built from metadata that omits F2 and F3, so the provider would negotiate confidently around the two things it must get right. This is Option B's hole with a runtime cost attached.

**Recommendation: Option C, with Option B as its first half.** The finding that decides it is F2/F3 — sampling acceptance and disabled-thinking acceptance are not published by Anthropic, so a metadata-only design (B or D) is structurally blind to the exact defect that started this. A probe is not a workaround for that; it is the only instrument that reads those facts, and F10 proves it takes three requests and a fraction of a cent.

Option C is also the one that matches how this project already works. It adds no state anyone must remember to update — the standing rule is to state the rule and derive the set from the live system, and a probe *is* derivation, just against behaviour instead of a document. And it puts the answer where the decision is made: the person changing `model` runs one command and gets a verdict, instead of reading a matrix and interpreting it correctly.

Two requirements land on Option C from the discussion of 20260902, and both change its shape:

**One capability shape, filled in by each existing provider class (Ray, 20260902).** The vendors describe themselves in disjoint, incompatible vocabularies (F5), so the check must not be written against Anthropic's schema with Google bolted on. It needs one internal shape — *what our payload contract needs to know* — which each provider class fills in for itself, reporting "cannot answer" where it cannot rather than defaulting to "supported". This is **not a new component**: it is a method on the provider classes that already exist, alongside the payload policy file below. `OllamaProvider` is the honest test — it answers almost nothing, and the shape has to tolerate that.

**The check must detect option *removal*, not only value drift (F16, F17).** This is where I'd correct the premise the requirement came in on. The stability observation is right for Google and wrong for Anthropic, and Anthropic is the vendor that broke us: `temperature` on `claude-sonnet-5` is not a moved default, it is a 400 (F10). A check that validates defaults against published ranges would have passed the model that caused #79. So "set the defaults and validate them" is the right goal for Google and only half the job for Anthropic — the other half is confirming each parameter we send is still *accepted at all*, which F18 shows only the probe can establish.

**What the check reports (Ray, 20260902).** Two things about one named model, from a single live reading — no stored history, no snapshot file:

- **Validate what we set.** Every knob the provider's policy file declares is confirmed still *accepted* by that model, and any value it carries is confirmed still in range. This is the half that requires the probe (F16–F18): acceptance is not published by Anthropic, so it must be measured. A policy value that has fallen out of a published range — `maxTemperature` moving 2 → 1 — is caught here too, which is what makes drift in defaults detectable without keeping a copy of yesterday's reading.
- **Report what we are not using.** Options the model publishes that the policy does not set — effort levels, thinking modes, context and output limits, structured outputs. Informative only (Q4): it tells you what became available, it does not change anything.

The asymmetry is worth stating plainly: options being *removed* is what breaks us and is only visible by probing; options being *added* is visible from the published metadata. The check needs both halves for that reason.

**Where the payload policy lives (Ray, 20260902).** Option C needs something concrete to check *against*, and today there is nothing: what we send is a hardcoded dict inside each provider (F12, F13). The resolution is to split the configuration the way `intent_parse_prompt.json` and `intent_parse_system_prompt.txt` are already split, with the same never-duplicate boundary:

- `config/ai_settings.json` — *which provider, and how it is orchestrated*: `enabled`, `model`, `api_key_env`, costs, rate limits, retry, `report_types` routing, fallback settings, cost tracking.
- `config/providers/<name>_settings.json` — *how we talk to that provider*: the request payload policy. Which knobs we send and with what values, thinking mode, and anything else about request shaping.

This is consistent with the existing extension path — `workmain/ai/providers/__init__.py:6` already defines adding a provider as "add to `PROVIDER_REGISTRY` and `config/ai_settings.json`"; this makes it a third step of the same shape.

**The line that decides whether it works: the policy file declares what we _send_, never what the model _supports_.** `"thinking": "disabled"` is a decision we made and is legitimate configuration. `"supports_temperature": false` is a fact about a vendor's model — that is Option A's hand-maintained matrix in a config file, and it goes stale exactly the way `_FALLBACK_MODEL` did. Stated correctly, the split gives the check a clean three-way comparison: the policy file (what we send) against live metadata plus probe (what the model accepts) against `ai_settings.json` (which model we named).

**One policy per provider, not per model (Ray, 20260902).** A row per model is a register with a drift problem. One policy per provider fits the fixed conservative contract from #79 and lets the check answer the real question: does the model `ai_settings.json` names honour the policy? `claude_settings.json` declares "thinking disabled, no sampling"; point `model` at `claude-fable-5` and the check fails before production does. This also makes that spec's DR3 enforceable without a capability table — the constraint stops being prose in a `notes` field and becomes a policy something can test. And when a vendor shifts again, the change is one value in one file per affected provider.

What Option C deliberately does **not** do is make the payload dynamic. The fixed conservative contract from `CLAUDE_PROVIDER_CURRENT_MODEL_SPEC.md` is what makes `max_tokens` mean one thing everywhere; Option C's job is to tell you, before you commit, whether a candidate model honours that contract — turning a model swap from "edit config and find out in production" into "run one command and read the verdict."

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Confirm the split between #79 and this work. | **Answered 20260902 (Ray).** Superseded in part by Q11: the two stay separate items, but **#79 grows to carry the config restructure** rather than shipping as originally specced. |
| Q2 | Option C as the shape? Specifically: derive from vendor metadata, probe what metadata omits, one CLI command, no checked-in matrix anywhere. | **Answered 20260902 (Ray): yes**, with the added requirement that the capability model be provider-agnostic so future providers fold into it — see §4 recommendation. |
| Q3 | Ollama — probe scope. | **Answered 20260902 (Ray): no probe needed**, but Ollama is brought inline with the same per-provider config structure (`config/providers/ollama*`), including a possible filename and location change. **Its own issue.** |
| Q4 | Enforcing or advisory? | **Answered 20260902 (Ray): informative only.** It is a tool you run to check validity *before* making a model change. Nothing fails closed. |
| Q5 | Gemini config several generations behind. | **Answered 20260902 (Ray): dropped.** Not a concern; a newer Gemini model may be used as a test subject for the check if useful. |
| Q6 | F8 — a pinned dated snapshot changed advertised capability. Is that discoverable *by* the check, or required *for* it? | **Answered 20260902: discoverable by it, and not required for it.** Nothing in the check assumes capability is stable — it reads live every run and stores nothing it trusts. F8-style drift is exactly what the Q7 diff surfaces. |
| Q7 | Should the check validate existing settings and surface new ones? | **Answered 20260902 (Ray): yes, both** — validate every knob the policy declares is still accepted and in range, and report published options the policy does not use. One live reading of one named model; **no stored snapshot or history** — that was Spanner's addition and is withdrawn as unnecessary. See §4. |
| Q8 | ~~`GenerationRequest.temperature` re-examined once a capability model exists?~~ | **Withdrawn 20260902.** Subsumed by the per-provider payload policy files — the policy declares what each provider sends, so the field is honoured by Gemini and ignored by Claude by declaration rather than by assumption. The question predated that decision. |
| Q9 | ~~Does candidate filtering belong in the adapter?~~ | **Withdrawn 20260902.** "Adapter" was my term for something that is not a new component. Filtering is a responsibility of the existing provider class (F24) — Anthropic's filter is empty, Google's drops two-thirds. |
| Q10 | What does `--model` take, and does the check enumerate models? | **Answered 20260902 (Ray): one named model, never a catalogue** — `workmain providers check --model claude-sonnet-5`. Checking one model you intend to configure is also what keeps the modality noise of F20 entirely out of scope. |
| Q11 | Scope split. | **Answered 20260902 (Ray): two issues.** **#79 grows to include the config restructure and goes first**; a new issue carries the capability check, the live reading, and the change diff. |

## 6. Disposition

Split three ways, per Q3 and Q11 (Ray, 20260902):

- **Issue #79 — first.** Grows beyond the payload fix to carry the provider config restructure: `config/providers/<name>_settings.json` holding each provider's request payload policy, with `ClaudeProvider` and `GeminiProvider` building their payloads from it instead of from hardcoded dicts. Spec: `../specs/CLAUDE_PROVIDER_CURRENT_MODEL_SPEC.md`. F10/F11 verify that spec's DR1 and DR2 against the live API.
- **Issue #121 — the capability check.** `workmain providers check --model <model-name>`: one named model, live reading from the vendor, probe for what the vendor does not publish, validate the policy against it, report unused published options, informative verdict. Depends on #79 — until the payload policy is declared somewhere, the check has nothing to compare against.
- **Issue #122 — Ollama alignment.** Bring Ollama's configuration inline with the same per-provider structure, including any filename and location change. No probe.
