# Ollama Provider Alignment — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20260928
**Originating item:** Issue #122

---

## 1. Purpose

Issue #122 asks that Ollama be configured the way Claude and Gemini are, and that the three sites building an `OllamaProvider` from literals obtain it the way the rest of the application obtains a provider. Recon shows the file move is not a rename: the two intent parser files hold four different kinds of thing, and one of the per-provider files already means something specific. This study sorts those, settles the construction sites, and puts three questions to Ray.

It also inherits the findings `docs/archive/specs/PROCESS_RULE_HOME_SPEC.md` deferred to #122 (its Decision Log, 20260909): the `config/intent_parse_system_prompt.txt` header and the `CLAUDE.md` § Intent Parser Config lines describing it.

## 2. Scope of the read

Read: `config/ai_settings.json`, `config/providers/*_settings.json`, `config/intent_parse_prompt.json`, `config/intent_parse_system_prompt.txt`; `workmain/ai/intent_parser.py`, `provider_manager.py`, `base_provider.py`, `providers/ollama.py`; `workmain/daemon/daemon.py` (`_warmup_ollama`, `start`); `workmain/workflows/eod_workflow.py` (`_run_task_match_step`, `_run_note_dedup_step`); `docs/AI_SETTINGS_GUIDE.md`; `CLAUDE.md` § Intent Parser Config; `.env` and the `workmain-notify` user unit for `OLLAMA_*`; tests that patch the probe or construct `IntentParser`; the live model via `GET /api/tags` and `POST /api/show` (read-only).

Not read: the Modelfile and `build_workmain_intent.sh` in the IaC repo. What the live model reports stands in for the Modelfile.

## 3. Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F1 | AC1's check already passes on `dev`. `config/providers/ollama_settings.json` exists, shipped by #130 with a `description` only. The property AC1 is for — a reader finds any provider's configuration in one place — does not hold: Ollama's prompt and generation parameters are still in `config/` root. | `ls config/providers/` |
| F2 | `config/providers/<name>_settings.json` has one meaning: the request payload policy, "what we SEND, never what a model SUPPORTS". Every key in it is sent on every request. | `docs/AI_SETTINGS_GUIDE.md` § The request payload policy; each file's `description` |
| F3 | Of `intent_parse_prompt.json`, `IntentParser` reads only `max_tokens` and `system_prompt_file`. `_doc` (including `ollama_model`, `ollama_host`, `system_prompt_source`) and `generation_options` are read by nothing. | `intent_parser.py` `_load_prompt_config`, `_load_system_prompt`, `parse` |
| F4 | `max_tokens` (256) governs `parse()` only. `parse_task_match()` and `parse_note_duplicate()` send `max_tokens=64` and `generation_options={"raw": True, "format": "json"}` as literals. Runtime generation parameters are therefore already split between the JSON and the code. | `intent_parser.py` `parse_task_match`, `parse_note_duplicate` |
| F5 | The system prompt text is loaded only to fail fast if missing; it is never sent. The live model's SYSTEM block is identical to the file body (comment lines stripped). | `intent_parser.py` `_load_system_prompt` docstring; `/api/show` compared 20260928 |
| F6 | The live model bakes `temperature 0.4`, `top_p 0.9`, `top_k 40`, `repeat_penalty 1.1` — matching `generation_options` — plus `num_predict 256` and `stop "[INST]"`, `"[/INST]"`, which the repo copy omits. | `/api/show` 20260928 |
| F7 | `workmain-intent:latest` and the host appear in four places: `ai_settings.json` `providers.ollama` (the one that governs — `ProviderManager` reads it), the JSON `_doc`, the `.txt` header, and the literals at the three construction sites. | `provider_manager.py` `_load_config`; grep |
| F8 | The `.txt` header carries `ollama_model` and `ollama_host` (duplicates of F7), `model_built: workmain-intent:v1.6` (what was built), and two prose blocks — "Versioning" and "Tuning workflow" — that tell a person what to do. The Versioning block says to increment the model name suffix and update `ai_settings.json` to match, contradicting `CLAUDE.md`'s rule that the model is always referenced as `:latest`. | `config/intent_parse_system_prompt.txt:1-33` |
| F9 | `CLAUDE.md:174` attaches `model_built` to the `:latest` rule, but `model_built` records the built tag (`v1.6`). `CLAUDE.md:175` lists `ollama_model` and `ollama_host` as JSON-owned runtime parameters; nothing reads them there. | `CLAUDE.md` § Intent Parser Config; F3 |
| F10 | `IntentParser` resolves both files relative to the working directory; `ProviderManager` and `ConfigLoader` anchor to the project root. The daemon works only because its unit sets `WorkingDirectory`. | `intent_parser.py:19`; `loader.py` `__init__`; `workmain-notify.service` |
| F11 | `OLLAMA_HOST` / `OLLAMA_PORT` are set nowhere — not in `.env`, not in the unit. The parse path (`ProviderManager`) never read them, so setting one would redirect the probes and warm-up but not the parse. | `grep -c OLLAMA .env` = 0; unit `EnvironmentFile` |
| F12 | Timeouts differ by site: warm-up 120 s, both EOD probes 15 s, `ai_settings.json` 30 s (what `parse` uses). `OllamaProvider` has one timeout, used for both `check_availability` and `generate`. | `daemon.py` `_warmup_ollama`; `eod_workflow.py` probe blocks; `ollama.py` `__init__` |
| F13 | Each EOD probe wraps provider construction **and** `IntentParser()` in `except Exception: pass`. Today that absorbs an unreachable host, a missing prompt file (`FileNotFoundError`), and — through `get_provider_manager()` — any provider's `ConfigurationError`. Each step already has an outer handler that prints `⚠ <step> failed (<reason>) — continuing` and returns `COMPLETED`. | `eod_workflow.py:466-481`, `:708-723`, `:635`, `:862` |
| F14 | `ConfigurationError` is a subclass of `ProviderError`, so any handler catching `ProviderError` also catches a configuration fault. | `base_provider.py` exception classes |
| F15 | `_warmup_ollama` catches `Exception` and logs a warning; a configuration fault at daemon start is a warning today. | `daemon.py` `_warmup_ollama` |
| F16 | `docs/AI_SETTINGS_GUIDE.md` § Phase 13-1 Ollama Activation Checklist describes Ollama as "a disabled stub" with `generate()` unimplemented and points at a docstring checklist that does not exist. § Ollama Fields omits `model` and `timeout`. | `docs/AI_SETTINGS_GUIDE.md:64-71`, `:188-200` |
| F17 | Tests in `tests/test_eod_workflow.py` patch `workmain.ai.providers.ollama.OllamaProvider.check_availability` to drive the probe; the patch target survives a conversion that still calls that method on the manager's instance. | grep |

## 4. What each piece is

The layout question answers itself once the contents are sorted by kind:

| Kind | Today | Governs |
| --- | --- | --- |
| Connection and selection — `enabled`, `model`, `host`, `port`, `timeout` | `ai_settings.json` `providers.ollama` | Runtime, via `ProviderManager` |
| Request payload policy — keys sent on every request | `config/providers/ollama_settings.json` (none) | Runtime |
| Per-call request parameters — `max_tokens` per call, `raw`/`format` | JSON (`parse`) and code literals (the other two) | Runtime, per call |
| Modelfile inputs — SYSTEM text, PARAMETER values, version metadata | `.txt` (SYSTEM, version) and JSON `generation_options` (PARAMETERs, incomplete) | Build, outside this repo |

The first two already follow the per-provider structure. The last two are what the two intent parser files hold, and neither is payload policy (F2): a per-call `max_tokens` is not sent on every request, and the Modelfile values are not sent at all.

## 5. Options — file layout

### Option A — fold into the policy file

- **Approach:** `max_tokens` and `generation_options` move into `ollama_settings.json`; the `.txt` moves to `config/providers/ollama_system_prompt.txt`.
- **Pros:** fewest files; every Ollama file sits under `config/providers/`.
- **Cons:** breaks F2 — the policy file would hold values that are never sent and one that is sent on one call of three. `_load_provider_policy` would validate keys the provider never reads.

### Option B — one file per kind, under `config/providers/`

- **Approach:**
  - `config/intent_parse_system_prompt.txt` → `config/providers/ollama_system_prompt.txt`. Body unchanged. Header keeps `config_version`, `config_updated`, `model_built` only; `ollama_model`, `ollama_host` and the Versioning / Tuning workflow prose are removed (F7, F8). The procedure already has its home in `CLAUDE.md` § Intent Parser Config, version bump workflow (`DEVELOPMENT_STANDARDS.md` §1.5, a process rule never travels with the code).
  - `config/intent_parse_prompt.json` → `config/providers/ollama_generation.json`: `max_tokens` per call (`parse`, `task_match`, `note_dedup`) and the Modelfile PARAMETER values, completed to what the live model bakes (F6). `_doc` and `system_prompt_file` removed; the prompt path becomes a code constant beside the config path, both anchored to the project root (F10).
  - `ollama_settings.json` stays the payload policy, unchanged.
  - `CLAUDE.md` § Intent Parser Config rewritten for the new paths, with F9's two errors fixed.
- **Pros:** each file has one meaning, and the boundary AC3 protects holds by construction — version metadata in the `.txt`, generation parameters in the JSON, no key in both. Runtime generation parameters end in one file (F4). Every Ollama file sits under `config/providers/`.
- **Cons:** Ollama has three files where the others have one; that reflects that Ollama alone has a purpose-built model.

### Option C — leave the files, fix contents and construction sites only

- **Approach:** no move; strip duplicates and fix the construction sites.
- **Pros:** smallest change.
- **Cons:** AC1's command is already green (F1), so this passes the check without the property — the §1.2 case the criterion's wording exists to catch.

**Recommendation: Option B.** It is the only option where AC1 and AC3 both hold as properties rather than as grep results, and it keeps `config/providers/<name>_settings.json` meaning what #79 and #130 made it mean.

## 6. Construction sites

These follow from the issue and from existing rules; they are not open.

- **Configuration comes from `ProviderManager`.** All three sites stop building an `OllamaProvider`. The `OLLAMA_HOST` / `OLLAMA_PORT` reads are removed, not moved: nothing sets them and the parse path never honoured them (F11).
- **The probe belongs to `IntentParser`,** which already holds the manager. It gains `is_available()`: `get_provider('ollama').check_availability() == AVAILABLE`, returning `False` on `ProviderUnavailableError` (Ollama disabled). Both EOD steps become: construct `IntentParser()` outside any availability handler, then ask `is_available()`. The duplicated probe block goes.
- **A configuration fault is not an availability result.** `ConfigurationError` from the manager and `FileNotFoundError` from `IntentParser` propagate out of the probe to the step's existing outer handler (F13), which prints the reason and continues EOD. The step no longer falls back to keyword matching over a broken config without saying why. No handler in the new code catches `ProviderError` broadly (F14).
- **Warm-up** calls `get_provider_manager().generate(..., provider_override=ProviderType.OLLAMA)`.
- **Tests** keep the existing `check_availability` patch target (F17); new tests cover `is_available()` and that a `ConfigurationError` reaches the step's outer handler instead of the keyword path.
- **`docs/AI_SETTINGS_GUIDE.md`**: § Phase 13-1 Ollama Activation Checklist is deleted (F16); § Ollama Fields gains `model` and `timeout`; the new files are described beside § The request payload policy.

## 7. Open questions

| Q | Question | Recommendation | Answer |
| --- | --- | --- | --- |
| Q1 | Layout — Option A, B or C (§5)? | **B.** | |
| Q2 | Timeouts (F12). Reading from configuration "in one place" means one value per provider today. Warm-up used 120 s for a cold model load; the probes used 15 s. **(a)** One `timeout` (30 s) everywhere: an unreachable host costs each EOD step 30 s instead of 15, and warm-up after an Ollama service restart may time out if a cold load exceeds 30 s. **(b)** Add named timeouts to `providers.ollama` and a per-call timeout path through the provider — new surface that overlaps #114 and #117. | **(a).** `keep_alive -1` keeps the model resident, so warm-up is cold only after the Ollama service restarts, and warm-up is best-effort by design. Not verified: whether Ollama finishes a load after the client disconnects — measuring it means unloading the live model, a run-state change outside this issue. | |
| Q3 | Should a configuration fault at daemon start fail the start, rather than log a warning (F15)? A `ConfigurationError` from `get_provider_manager()` means some provider's policy is broken, which also breaks report generation. | **Yes.** Warm-up re-raises `ConfigurationError` and stays best-effort for everything else, so the unit fails visibly — the same rule as the EOD probes. | |

## 8. Disposition

- Promoted to: —
