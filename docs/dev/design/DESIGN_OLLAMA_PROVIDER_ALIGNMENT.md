# Ollama Provider Alignment — Design Study

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20260928
**Originating item:** Issue #122

---

## 1. Purpose

Issue #122 asks that Ollama be configured the way Claude and Gemini are, and that the three sites building an `OllamaProvider` from literals obtain it the way the rest of the application obtains a provider. Ray's requirements, stated 20260928:

- **R1** — Ollama operates at runtime exactly as the other providers do.
- **R2** — Ray can easily adjust the Modelfile.
- **R3** — Modelfile changes reach the Ollama LXC through automation that lives outside workmain, because a future user may run different models or providers.

This study also inherits the findings `docs/archive/specs/PROCESS_RULE_HOME_SPEC.md` deferred to #122 (its Decision Log, 20260909): the `config/intent_parse_system_prompt.txt` header and the `CLAUDE.md` § Intent Parser Config lines describing it.

## 2. Scope of the read

Read: `config/ai_settings.json`, `config/providers/*_settings.json`, `config/intent_parse_prompt.json`, `config/intent_parse_system_prompt.txt`, the rest of `config/` and its loaders; `workmain/ai/intent_parser.py`, `provider_manager.py`, `base_provider.py`, `providers/ollama.py`; `workmain/daemon/daemon.py` (`_warmup_ollama`, `start`); `workmain/workflows/eod_workflow.py` (`_run_task_match_step`, `_run_note_dedup_step`); every `max_tokens` call site; `docs/AI_SETTINGS_GUIDE.md`; `CLAUDE.md` § Intent Parser Config; `.env` and the `workmain-notify` unit for `OLLAMA_*`; tests that patch the probe or construct `IntentParser`; the live model via `GET /api/tags` and `POST /api/show` (read-only); `sync_modelfile.sh` v1.0 from the IaC repo, supplied by Ray.

Not read: the Modelfile and `update_workmain_intent.sh` in the IaC repo.

## 3. Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F1 | AC1's check already passes on `dev`. `config/providers/ollama_settings.json` exists, shipped by #130 with a `description` only. The property AC1 is for — a reader finds any provider's configuration in one place — does not hold: Ollama's model build sources are still in `config/` root. | `ls config/providers/` |
| F2 | `config/providers/<name>_settings.json` has one meaning: the request payload policy, "what we SEND, never what a model SUPPORTS". | `docs/AI_SETTINGS_GUIDE.md` § The request payload policy |
| F3 | The two intent parser files are the **input to Modelfile generation**. `sync_modelfile.sh` in the IaC repo reads both at fixed paths: from the `.txt`, the `# config_version:` line and the body after the last `# ===` line (→ `SYSTEM`); from the JSON, `generation_options` (→ `PARAMETER` lines) and `max_tokens` (→ `PARAMETER num_predict`). A move or format change in workmain breaks that script. | `sync_modelfile.sh` v1.0 |
| F4 | Since #127, `max_tokens` in the JSON is Modelfile build input only (the IaC script bakes it as `num_predict`); nothing in workmain reads it. All three `IntentParser` calls take their runtime cap from `ProviderManager.get_max_tokens()` — `application_functions.intent_parse`, `.task_match`, `.note_dedup` in `ai_settings.json`. `parse_task_match()` and `parse_note_duplicate()` still send `generation_options={"raw": True, "format": "json"}` as literals; those are the response shape the parser depends on, not tunables. | `intent_parser.py` `parse`, `parse_task_match`, `parse_note_duplicate`; `provider_manager.py` `get_max_tokens`; `sync_modelfile.sh` |
| F5 | After #127 the only `max_tokens` literals left in `workmain/` are the `providers test` probe and the daemon warm-up (`daemon.py` `_warmup_ollama`, `max_tokens=1`), which #127 left to this issue. | `git grep max_tokens` |
| F6 | Of the JSON, `IntentParser` now reads only `system_prompt_file`. The system prompt is loaded only to fail fast if missing; it is never sent. `_doc` (including `ollama_model`, `ollama_host`) is read by nothing, in either repo. | `intent_parser.py` `_load_prompt_config`, `_load_system_prompt`; `sync_modelfile.sh` |
| F7 | The live model matches the sources: its SYSTEM block equals the `.txt` body, and it bakes `temperature 0.4`, `top_p 0.9`, `top_k 40`, `repeat_penalty 1.1`, `num_predict 256`. Its `stop` tokens are inherited from `FROM mistral:latest`, not emitted by the script. | `/api/show` 20260928; `sync_modelfile.sh` |
| F8 | The `.txt` header carries `ollama_model` and `ollama_host` (duplicates of `ai_settings.json`, which is the one `ProviderManager` reads) and two prose blocks — "Versioning" and "Tuning workflow" — telling a person what to do. The Versioning block says to increment the model name suffix and update `ai_settings.json` to match. That contradicts the rule that the application only ever uses `workmain-intent:latest`; `config_version` and `model_built` are Ray's build record for the IaC side. | `config/intent_parse_system_prompt.txt:1-33` |
| F9 | `CLAUDE.md:174` attaches `model_built` to the `:latest` rule, but `model_built` is the build record (`v1.6`). `CLAUDE.md:175` lists `ollama_model` and `ollama_host` as JSON-owned runtime parameters; nothing reads them. | `CLAUDE.md` § Intent Parser Config; F6 |
| F10 | `IntentParser` resolves both files relative to the working directory; `ProviderManager` and `ConfigLoader` anchor to the project root. | `intent_parser.py:19`; `loader.py` `__init__` |
| F11 | `OLLAMA_HOST` / `OLLAMA_PORT` are set nowhere. The parse path (`ProviderManager`) never read them, so setting one would redirect the probes and warm-up but not the parse. | `.env`; unit `EnvironmentFile` |
| F12 | Timeouts differ by site: warm-up 120 s, both EOD probes 15 s, `ai_settings.json` 30 s. `OllamaProvider` has one timeout for `check_availability` and `generate`. | `daemon.py` `_warmup_ollama`; `eod_workflow.py`; `ollama.py` |
| F13 | `OLLAMA_KEEP_ALIVE=-1` is set on the LXC, so the model stays resident; a cold load follows only an Ollama service or LXC restart, which daemon restarts are not tied to. `OllamaProvider` also sends `keep_alive: -1`. | `CLAUDE.md` § OLLAMA_KEEP_ALIVE; `ollama.py` `generate` |
| F14 | Each EOD probe wraps provider construction **and** `IntentParser()` in `except Exception: pass`, absorbing an unreachable host, a missing prompt file, and any `ConfigurationError` from `get_provider_manager()` — which since #127 also covers a malformed or duplicated `application_functions` / `report_types` `max_tokens` entry. Each step's outer handler prints `⚠ <step> failed (<reason>) — continuing` and returns `COMPLETED`. | `eod_workflow.py:466-481`, `:708-723`, `:635`, `:862` |
| F15 | `ConfigurationError` subclasses `ProviderError`, so a handler catching `ProviderError` also catches a configuration fault. | `base_provider.py` |
| F16 | `_warmup_ollama` catches `Exception` and logs a warning; a configuration fault at daemon start is a warning today. | `daemon.py` |
| F17 | `docs/AI_SETTINGS_GUIDE.md` § Phase 13-1 Ollama Activation Checklist describes Ollama as "a disabled stub" and points at a docstring checklist that does not exist. § Ollama Fields omits `model` and `timeout`. | `docs/AI_SETTINGS_GUIDE.md:64-71`, `:188-200` |
| F18 | Tests in `tests/test_eod_workflow.py` patch `workmain.ai.providers.ollama.OllamaProvider.check_availability`; that target survives a conversion that calls the method on the manager's instance. | grep |
| F19 | `ProviderManager` instantiates only the providers named in `ai_settings.json` `providers`, so a directory under `config/providers/` that no entry names is never loaded. | `provider_manager.py` `_load_config` |

## 4. Decisions

| # | Decision | By |
| --- | --- | --- |
| D1 | `config/providers/` becomes a directory per provider. `settings.json` in it is the request payload policy, with the meaning `<name>_settings.json` has today (F2). An optional `models/<model>/` holds the build source for a model we define, in that provider's own format. Claude and Gemini have no `models/`. `ai_settings.json` keeps owning which provider and model are used. | Ray, 20260928 |
| D2 | A template provider directory, `config/providers/_template/`, shows the shape: a `settings.json`, a `models/` example, and a short statement of what each part is and requires. The leading underscore follows the `docs/dev/<type>/_TEMPLATE_*.md` precedent; F19 means it is never loaded. | Ray, 20260928 |
| D3 | The `config/providers/` layout is interim. The wider `config/` organisation — including `config/providers/` — is #147, blocked by #122. | Ray, 20260928 |
| D4 | Withdrawn 20260928. F5 is not a precedent: a request value hardcoded at the call site is the defect #127 describes for temperature, and `max_tokens` sits beside it in the same plumbing. Where per-call `max_tokens` values live is Q5. | Ray, 20260928 |
| D5 | `OLLAMA_HOST` / `OLLAMA_PORT` reads are removed, not moved (F11). | Follows from F11 |
| D6 | The `.txt` header's `ollama_model`, `ollama_host` and Versioning / Tuning workflow prose are removed (F8). The procedure's home is `CLAUDE.md` § Intent Parser Config, rewritten for the new paths with F9's errors fixed. | `DEVELOPMENT_STANDARDS.md` §1.5, a process rule never travels with the code |

## 5. Options — the model build source format

The only open design question D1 leaves: what goes in `config/providers/ollama/models/workmain-intent/`.

### Option A — keep the generator input pair

- **Approach:** `system_prompt.txt` (version header + SYSTEM body) and `parameters.json` (`generation_options` and `num_predict`, renamed from `max_tokens` now that #127 left it build input only). `sync_modelfile.sh` changes its two read paths and the `num_predict` key.
- **Pros:** Ray's authoring workflow stays as it is.
- **Cons:** the IaC automation has to know this model's source format (the `# ===` delimiter, `config_version:` line, JSON keys), so a second model, or a different user's model, needs its own generator. That works against R3.

### Option B — the literal Modelfile

- **Approach:** `Modelfile` — `FROM`, `SYSTEM`, `PARAMETER` lines, and a `# version:` comment as Ray's build record. The automation reads the directory, builds the Modelfile as `<model>:latest`, and tags `<model>:v<version>`.
- **Pros:** Ray edits the artifact Ollama actually builds (R2). The automation needs only a directory and a name, so it works for any Ollama model and any user (R3). Nothing is translated, so there is no generator to drift from its inputs.
- **Cons:** `sync_modelfile.sh` is rewritten; it gets simpler, but the change is in the IaC repo.

**Recommendation: Option B.** R3 is the requirement that decides it: generic automation outside workmain cannot depend on a workmain-specific source format. Under either option the application stops loading the build source at runtime (F6): it never sent it, and a missing build input should not stop the daemon.

## 6. Construction sites

These follow from the issue and existing rules.

- **Configuration comes from `ProviderManager`.** No site builds an `OllamaProvider`.
- **The probe belongs to `IntentParser`,** which already holds the manager. It gains `is_available()`: `get_provider('ollama').check_availability() == AVAILABLE`, returning `False` on `ProviderUnavailableError` (Ollama disabled). Both EOD steps construct `IntentParser()` outside any availability handler, then ask `is_available()`. The duplicated probe block goes.
- **A configuration fault is not an availability result.** `ConfigurationError` from the manager propagates out of the probe to the step's outer handler (F14), which prints the reason and continues EOD. No new handler catches `ProviderError` broadly (F15).
- **Tests** keep the existing patch target (F18); new tests cover `is_available()` and that a `ConfigurationError` reaches the step's outer handler rather than the keyword path.
- **`docs/AI_SETTINGS_GUIDE.md`**: § Phase 13-1 Ollama Activation Checklist is deleted (F17); § Ollama Fields gains `model` and `timeout`; the new layout replaces the flat file list in § The request payload policy.

## 7. Open questions

| Q | Question | Recommendation | Answer |
| --- | --- | --- | --- |
| Q1 | Where Ollama's build source lives. | — | 20260928, Ray: D1, D2, D3. |
| Q2 | Model build source format — Option A or B (§5)? | **B.** | 20260929, Ray: **B**, the literal Modelfile. workmain reads the build source only in `IntentParser.__init__`, to fail fast if it is missing (F6), so nothing in workmain depends on its format. The IaC script reduces to building a directory. |
| Q3 | Delete `_warmup_ollama`? With the model resident on the LXC (F13), a daemon-start warm-up almost never meets a cold model, and deleting it removes one construction site and the 120 s timeout (F12). The EOD probes then use the single configured 30 s timeout: an unreachable host costs each step 30 s instead of 15. | **Delete.** | 20260929, Ray: **delete.** `docs/AI_SETTINGS_GUIDE.md` states that workmain never pre-loads a model: a model that must be resident before its first request is loaded where the model server is run, not by workmain. |
| Q4 | Should daemon start call `get_provider_manager()` once, so a broken provider policy fails the start rather than the first Slack DM (F16)? It is the same rule as the EOD probes. | **Yes.** | 20260929, Ray: **yes**, performed in line in `start()` where the warm-up call is today, not in a separate thread or process. |
| Q5 | Where per-call `max_tokens` values live, and which issue moves them (D4). | — | 20260928, Ray: #127 is widened to cover `max_tokens`, one value per call type, declared in configuration. #122 is blocked by #127 and resumes after it ships; the intent parser's runtime `max_tokens` leaves `config/intent_parse_prompt.json` there, not here. |

## 8. Disposition

- Promoted to: `../specs/OLLAMA_PROVIDER_ALIGNMENT_SPEC.md`
