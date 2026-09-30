# Ollama Provider Alignment — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20260929
**Branch:** `feature/issue-122-ollama-provider-alignment` (from `dev`)
**Target release:** v1.35.0
**Originating item:** Issue #122
**Design study:** `../design/DESIGN_OLLAMA_PROVIDER_ALIGNMENT.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260928 | Ray | D1–D3: a directory per provider under `config/providers/`, `settings.json` as the payload policy, an optional `models/<model>/` for a model we define, a `_template/` provider directory; the layout is interim and #147 owns the wider `config/` organisation. | Taken — DR1, DR2, DR9, Step 1. |
| 20260928 | Ray | Q5: per-call `max_tokens` moves under #127, which blocks #122. | Shipped by #127 (v1.34.2). This spec only removes the build-input copy. |
| 20260929 | Ray | Q2: the build source is the literal Modelfile. | Taken — DR3, Step 2. |
| 20260929 | Ray | Q3: delete the daemon warm-up; the guide states that pre-loading a model is the model server's concern. | Taken — DR7, Steps 4 and 5. |
| 20260929 | Ray | Q4: daemon start loads the provider manager in line, not in a separate thread or process, so a configuration fault fails the start. | Taken — DR7, Step 4. |
| 20260929 | Spanner | The issue's AC3 names a two-file boundary (version metadata in one file, runtime generation parameters in another) that Q2 replaces with one build source and no runtime generation parameters at all. Its purpose — no value lives in two places, and version state lives in one — is kept. | Restated as AC3.1–AC3.3. The issue's AC3 text is edited at close-out. |
| 20260930 | Ray | The model was rebuilt as `v1.7` with `PARAMETER num_predict 512` and `PARAMETER num_thread 4`. `num_thread 4` restores usable speed: without it the LXC sizes its thread pool from the Proxmox host's threads rather than the four the LXC is allotted, and generation runs at 1–2 tokens/s. The thread-detection cause is outside this issue. | Taken — DR3 carries both, at `# version: 1.7`. `num_predict 512` governs only a request that sends no `num_predict`; every workmain call sends its per-call cap (#127), so it duplicates no workmain value (DR8). Supersedes Spanner's 20260929 entry that dropped `num_predict`. |
| 20260929 | Spanner | The Modelfile carries `# version:` only. `config_updated` and `model_built` do not carry over: the date is in git, and the built tag is derived from the version by the build. | Taken — DR3. |
| 20260929 | Ray | C1: `keep_alive` keeps a loaded model resident but never loads one, so after an Ollama or LXC restart the first request loads the model inside the 30 s timeout. Measured: ~112 s from a warm disk, ~243 s after a reboot. Ray takes C1-A: the IaC side warms the model after a restart and checks it regularly; the post-reboot window is accepted. | Taken — §7 lists the IaC warm-up as a requirement; the guide paragraph in Step 5 no longer says the first request waits. |
| 20260929 | Ray | C2: Ollama still differs from Claude and Gemini at request time — no retries, an availability probe before every generation, and a `timeout` key where they have `timeout_seconds`. Kept out of #122. | Opened #152 (blocked by #122); §1 Out of scope cites it. Step 5 documents `timeout` as it is today; the key name is #152's. |
| 20260929 | Ray | C4: DR7 makes a configuration fault fail daemon start, and the daemon runs EOD steps in its own process (`slack_eod.py` `run_step`) against its cached manager, so AC5.3's path is reached from a CLI `workmain eod` run. Its only trace is the printed line. | Taken — stated in DR6 and §7. |
| 20260929 | Ray | S1: AC5.4 patches `get_provider_manager` in `workmain.daemon.daemon`, which works only with a module-level import; `daemon.py` has none. | Taken — Step 4 adds the import at module level. |
| 20260929 | Ray | S3: `check_availability()` compares only the name before the colon, so a server holding only `workmain-intent:v1.6` reads as available for `workmain-intent:latest` and the request then fails. | Fixed here, not deferred — it sits on the `is_available()` path this issue creates. DR10, Step 3, AC5.5. |
| 20260929 | Ray | S4: `ProviderManager._load_config` turns any provider constructor exception into a disabled provider, so `get_provider('ollama')` raises `ProviderUnavailableError` and `is_available()` returns `False` — DR6 overstated what propagates. | Taken — DR6 reworded. `OllamaProvider.__init__` only reads dict keys, so the case is theoretical for Ollama. |
| 20260929 | Ray | G1: how the IaC side receives the Modelfile. Ray runs the IaC script manually after the PR merges and the repo is back on `main`; it reads the Modelfile from the workmain working tree (a sibling checkout), copies it to the LXC, and runs the build script there. It reads whatever branch is checked out. | Taken — §7 states the trigger and the source. The reworked script is needed before the next Modelfile change, not before merge. |

---

## 1. Scope

**In scope:**

- `config/providers/` — per-provider directories; `ollama/models/workmain-intent/Modelfile`; `_template/`.
- `config/intent_parse_prompt.json`, `config/intent_parse_system_prompt.txt` — deleted.
- `workmain/ai/provider_manager.py` — policy path.
- `workmain/ai/intent_parser.py` — stops loading build sources; gains `is_available()`.
- `workmain/ai/providers/ollama.py` — `check_availability()` matches the configured model exactly.
- `workmain/workflows/eod_workflow.py` — both Ollama probes.
- `workmain/daemon/daemon.py` — `_warmup_ollama` deleted; `start()` loads the provider manager.
- Comments and docstrings naming a moved path or `workmain-intent:latest`: `workmain/ai/base_provider.py`, `workmain/ai/providers/claude.py`, `workmain/ai/providers/gemini.py`, `workmain/ai/providers/ollama.py`, `workmain/ai/intent_parser.py`.
- `CLAUDE.md` § Intent Parser Config - Source of Truth; `docs/AI_SETTINGS_GUIDE.md`.
- Tests named in §6.

**Out of scope:**

- The IaC repo. `sync_modelfile.sh` reads both deleted files, so it stops working when this merges. §7 states what the workmain side guarantees so Ray can change the script to match. Nothing in workmain depends on it.
- The wider `config/` organisation, including whether `config/providers/` stays where it is — #147.
- How Ollama behaves at request time compared with Claude and Gemini: retries, the availability probe inside `generate()`, and the `timeout` / `timeout_seconds` key name — #152. The EOD probes move from 15 s to the configured 30 s; nothing else about timeouts changes.
- The `raw` / `format` generation options `parse_task_match()` and `parse_note_duplicate()` send. They are the response shape the parser depends on, not tunables (study F4).
- `OllamaProvider`'s per-request `keep_alive: -1` — `CLAUDE.md` § OLLAMA_KEEP_ALIVE.

## 2. Verified current state

Verified on this branch at `e0f8b8c`, which includes the #127 merge.

| Claim | Evidence |
| --- | --- |
| Policy files are flat: `claude_settings.json`, `gemini_settings.json`, `ollama_settings.json`. | `ls config/providers/` |
| `ProviderManager` loads a policy as `ConfigLoader().load(f"providers/{name}_settings")` and names `config/providers/{name}_settings.json` in its errors. | `provider_manager.py:339-340` `_load_provider_policy` |
| `ConfigLoader.load(name)` reads `<config_dir>/<name>.json`, so a name with a subdirectory resolves. | `config_manager/loader.py:49` |
| `ProviderManager` instantiates only providers named in `ai_settings.json` `providers`. | `provider_manager.py` `_load_config` |
| A test asserts the Claude policy error names `claude_settings.json`. | `tests/test_provider_foundation.py:272` |
| `IntentParser.__init__` loads `config/intent_parse_prompt.json` (CWD-relative) and the system prompt file it names, only to fail fast; neither is sent. All three calls take `max_tokens` from `get_max_tokens()`. | `intent_parser.py:19`, `:39-66`, `:89`, `:189`, `:236` |
| Three tests cover those loads. | `tests/test_intent_parser.py` `TestIntentParserConfig` (`:161-195`) |
| `config/intent_parse_prompt.json` `max_tokens` is Modelfile build input only since #127. | its `_doc.description` |
| The system prompt body follows the header's last `# ===` line (line 33) and contains no `"""`. | `config/intent_parse_system_prompt.txt` |
| The live model is `workmain-intent:v1.7` (also `:latest`). Its SYSTEM block equals that body, and it bakes `temperature 0.4`, `top_p 0.9`, `top_k 40`, `repeat_penalty 1.1`, `num_predict 512`, `num_thread 4`. The repo's system prompt header still records `config_version 1.6`. | `POST /api/show`, `GET /api/tags`, 20260930 |
| `sync_modelfile.sh` v1.0 builds `FROM mistral:latest`, `SYSTEM """<body>"""` and those five `PARAMETER` lines from the two files. | Ray-supplied script |
| Both EOD probes build `OllamaProvider` from a literal dict with `OLLAMA_HOST` / `OLLAMA_PORT` fallbacks, then construct `IntentParser()`, all inside `except Exception: pass`. | `eod_workflow.py:464-481`, `:706-723` |
| Each step's outer handler prints `⚠ <step> failed (<e>) — continuing` and returns `COMPLETED`. | `eod_workflow.py` `_run_task_match_step`, `_run_note_dedup_step` |
| EOD tests drive the probe by patching `workmain.ai.providers.ollama.OllamaProvider.check_availability`; some also patch `workmain.ai.intent_parser.IntentParser` with a `MagicMock`. | `tests/test_eod_workflow.py` |
| `_warmup_ollama` builds `OllamaProvider` from literals with a 120 s timeout and `max_tokens=1`; `start()` calls it after the auth token reads and before `_resolve_dm_channel`. No test references it. | `daemon.py:245-270`, `:345`; `git grep _warmup -- tests` |
| The unit restarts on failure every 30 s. | `workmain-notify.service` `Restart=on-failure`, `RestartSec=30` |
| `ConfigurationError` subclasses `ProviderError`; `ProviderUnavailableError` is what `get_provider()` raises for a disabled or unregistered provider. | `base_provider.py`; `provider_manager.py` `get_provider` |
| `OLLAMA_HOST` / `OLLAMA_PORT` are set nowhere. | `.env`; unit `EnvironmentFile` |

## 3. Design rules

- **DR1 — One directory per provider.** `config/providers/<name>/settings.json` is that provider's request payload policy, with exactly the meaning `<name>_settings.json` has today. No other file in the provider directory is read by workmain.
- **DR2 — `models/<model>/` is a build source, never runtime input.** It holds the definition of a model this project builds, in the provider's own format. Nothing under `workmain/` reads anything under `config/providers/*/models/`.
- **DR3 — The intent model's only source is `config/providers/ollama/models/workmain-intent/Modelfile`.** It is exactly the file below, where `<body>` is the current system prompt body — everything after the last `# ===` header line, with leading and trailing blank lines removed, the transformation `sync_modelfile.sh` applies:

  ```text
  # workmain-intent: the WorkmAIn intent parsing model.
  # version: 1.7

  FROM mistral:latest

  SYSTEM """
  <body>
  """

  PARAMETER temperature 0.4
  PARAMETER top_p 0.9
  PARAMETER top_k 40
  PARAMETER repeat_penalty 1.1
  PARAMETER num_predict 512
  PARAMETER num_thread 4
  ```

  The `# version: <v>` line is Ray's build record and the only version state in the repository. `num_predict` is the default for a request that sends none; every workmain request sends its own from `application_functions` (#127), which overrides it. `num_thread` is sized to the LXC's allotted cores.
- **DR4 — The application names the model once.** `workmain-intent:latest` appears only in `config/ai_settings.json` `providers.ollama.model`. The Modelfile does not name the model; the build does.
- **DR5 — Ollama comes from `ProviderManager`.** No module outside `workmain/ai/providers/` constructs `OllamaProvider`, and nothing reads `OLLAMA_HOST` or `OLLAMA_PORT`.
- **DR6 — A configuration fault is not an availability result.** `IntentParser.is_available()` returns `False` only for `ProviderUnavailableError`. That covers a provider disabled in `ai_settings.json`, and one `ProviderManager._load_config` marked disabled because its constructor raised; `OllamaProvider.__init__` only reads dict keys, so the second is theoretical for Ollama. Every other exception — including `ConfigurationError` from `get_provider_manager()` and anything from `IntentParser()` — reaches the caller. No new code catches `ProviderError` or `Exception` around the probe. Because DR7 fails daemon start on a configuration fault and the daemon runs EOD steps against its cached manager, the step-level fault path is reached from a CLI `workmain eod` run, where its only trace is the printed line.
- **DR7 — workmain never pre-loads a model.** `start()` calls `get_provider_manager()` in line where `_warmup_ollama()` is called today — same thread, no retry, no handler — so a configuration fault fails the start.
- **DR8 — No duplicated values.** Nothing in `ai_settings.json` or `config/providers/ollama/settings.json` repeats a value from the Modelfile, and the Modelfile repeats nothing from them.
- **DR9 — `_template/` is never loaded.** It is not named in `ai_settings.json`, and DR1's loader reads only named providers.
- **DR10 — Availability means the configured model, exactly.** `OllamaProvider.check_availability()` returns `AVAILABLE` only when `/api/tags` lists the configured model name exactly. A configured name with no tag is compared as `<name>:latest`, which is how Ollama resolves it. A different tag of the same model does not count.

Anything this spec does not cover: stop, per `CLAUDE.md` Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | **Provider directories.** `git mv` each `config/providers/<name>_settings.json` to `config/providers/<name>/settings.json`, contents unchanged. `_load_provider_policy` loads `providers/{name}/settings` and names `config/providers/{name}/settings.json` in every error. Update the path in the `base_provider.py`, `claude.py` and `gemini.py` docstrings, in `provider_manager.py`'s `_load_provider_policy` docstring, in the Claude `notes` string in `config/ai_settings.json`, and in the assertion at `test_provider_foundation.py:272`. Add `config/providers/_template/settings.json`: `{"description": "Request payload policy: the parameters every request to this provider carries. Holds every key the provider class declares in REQUIRED_POLICY_KEYS, and only those."}`. Add `config/providers/_template/models/README.md` stating what a model directory is (DR2) in two sentences, and that a hosted provider has none. | `config/providers/**`, `config/ai_settings.json`, `provider_manager.py`, `base_provider.py`, `claude.py`, `gemini.py`, `tests/test_provider_foundation.py` |
| 2 | **The Modelfile.** Create `config/providers/ollama/models/workmain-intent/Modelfile` per DR3. `git rm` both intent parser config files. In `intent_parser.py` delete `PROMPT_CONFIG_PATH`, `_load_prompt_config`, `_load_system_prompt` and the two attributes they set; `__init__` only obtains the manager. Reword every comment and docstring in `intent_parser.py`, `base_provider.py` and `ollama.py` that names `workmain-intent:latest` or a deleted file to say "the Ollama model's Modelfile" (DR4). Delete `TestIntentParserConfig` and its now-unused imports. Update the path in the `test_action_executor.py:350` docstring. | `config/**`, `intent_parser.py`, `base_provider.py`, `ollama.py`, `tests/test_intent_parser.py`, `tests/test_action_executor.py` |
| 3 | **Probe.** Change `OllamaProvider.check_availability()` per DR10. Add `IntentParser.is_available() -> bool` per DR6. In both EOD steps replace the probe block with `intent_parser = IntentParser()` then `ollama_available = intent_parser.is_available()`, outside any new handler. Every EOD test that patches `IntentParser` with a mock sets `is_available.return_value` to match the `check_availability` patch beside it. Add the §6 tests. | `ollama.py`, `intent_parser.py`, `eod_workflow.py`, `tests/test_ollama_provider.py`, `tests/test_intent_parser.py`, `tests/test_eod_workflow.py` |
| 4 | **Daemon start.** Delete `_warmup_ollama`. Add `from workmain.ai.provider_manager import get_provider_manager` to `daemon.py`'s module-level imports, and replace the `_warmup_ollama()` call in `start()` with `get_provider_manager()` per DR7. Add the §6 test. | `daemon.py`, `tests/test_orchestration.py` |
| 5 | **Documentation.** Replace `CLAUDE.md` § Intent Parser Config - Source of Truth with the text below. In `docs/AI_SETTINGS_GUIDE.md`: the Overview's policy line and § The request payload policy use `config/providers/<name>/settings.json`, and the shipped-files table lists the three directories; describe `models/<model>/` and `_template/` there, citing DR2's README rather than restating it; § Ollama Fields gains `model` and `timeout`; add the paragraph below to § Ollama Fields; § How to add a new provider step 4 says to copy `_template/`; delete § Phase 13-1 Ollama Activation Checklist. Every paragraph this step writes is one line (`DEVELOPMENT_STANDARDS.md` §1.5). | `CLAUDE.md`, `docs/AI_SETTINGS_GUIDE.md` |

`CLAUDE.md` replacement section:

```markdown
### Local Model Definitions - Source of Truth

- `config/providers/<provider>/models/<model>/` holds the build source for a model this project defines, in that provider's own format. workmain never reads it; the build runs from the IaC repo.
- `config/providers/ollama/models/workmain-intent/Modelfile` is the intent model's only source: its SYSTEM prompt, its PARAMETER values, and a `# version:` line that is Ray's build record.
- The application references the model only as `workmain-intent:latest`, in `config/ai_settings.json` `providers.ollama.model`. A version tag is never application configuration.

**Model change workflow:** edit the Modelfile and its `# version:` line → Ray runs the IaC build, which creates `workmain-intent:latest` and tags the version. Nothing else in workmain changes.
```

`docs/AI_SETTINGS_GUIDE.md` § Ollama Fields paragraph:

```markdown
workmain never pre-loads a model. Keep-alive (`CLAUDE.md` § OLLAMA_KEEP_ALIVE) keeps a loaded model resident but does not load one, so after the model server restarts, the first request loads the model from disk inside that request's `timeout` and can fail. Loading the model after a restart is the model server's job, not workmain's.
```

### Authorization points

None. Every step edits the working tree. The live-model checks in §5 are read-only requests; AC4.1's parse call also writes one `ai_costs` row, as every intent parse does.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Every provider is configured through the same structure, so a reader finds any provider's policy at the same relative path. | `ls config/providers/*/settings.json` lists `_template`, `claude`, `gemini`, `ollama`, and `ls config/providers/` lists nothing else |
| AC1.2 | The policies still load from their new paths, and a policy fault still names its file. | `pytest tests/test_provider_foundation.py` passes, including the updated `:272` assertion |
| AC2.1 | No reference to a moved or deleted file points at its old path. | `git grep -nE "intent_parse_prompt|intent_parse_system_prompt|providers/[a-z<>]+_settings|(claude|gemini|ollama)_settings\.json" -- '*.py' '*.md' '*.json' ':!docs/archive' ':!CHANGELOG.md' ':!docs/dev/*/*OLLAMA_PROVIDER_ALIGNMENT*'` returns zero hits. The excluded set is this issue's own record of the old paths |
| AC3.1 | The Modelfile is the same model that is deployed, so moving the source changed nothing workmain receives. | The live model's `system` from `POST /api/show` equals the Modelfile's SYSTEM block, and each `PARAMETER` the Modelfile carries equals the live `parameters` value of the same name |
| AC3.2 | Version state lives in one place. | `grep -rn "config_version\|model_built\|# version:" config/ workmain/` returns only the Modelfile's `# version:` line |
| AC3.3 | No Modelfile value is also held in runtime configuration, and the application reads nothing from a model directory. Property of documents — Ray's stated reading of the Modelfile, `config/providers/ollama/settings.json`, `ai_settings.json` `providers.ollama` and `application_functions`, and `CLAUDE.md` § Local Model Definitions, for any value in two places. | Stated reading by Ray; and `grep -rn "models/" workmain/ --include='*.py'` returns zero hits |
| AC4.1 | Intent parsing works end to end against the live model after the move. | `python -c "from workmain.ai.intent_parser import IntentParser; p=IntentParser(); assert p.is_available(); print(p.parse('note: alignment check'))"` prints a dict whose `action` is `create_note` |
| AC5.1 | No module builds an Ollama provider from literal configuration, and the model is named only in configuration. | `grep -rnE "OllamaProvider\(\{|workmain-intent:latest|workmain-ollama|OLLAMA_(HOST|PORT)|_warmup_ollama" workmain/` returns zero hits |
| AC5.2 | `is_available()` reports availability of the configured model and nothing else. | Tests: `True` when `check_availability` returns `AVAILABLE`; `False` when it returns `UNAVAILABLE`; `False` when `get_provider('ollama')` raises `ProviderUnavailableError`; `ConfigurationError` from `get_provider` propagates |
| AC5.3 | A configuration fault in either EOD step is reported with its reason, not replaced by keyword matching. | One test per step: `get_provider_manager` raises `ConfigurationError("sentinel")`; the step returns `COMPLETED`, stdout contains `failed (sentinel)`, and `_keyword_score_match` (task match) or `_keyword_note_dedup_match` (note dedup) is never called |
| AC5.4 | A configuration fault fails daemon start. | Test: with the calls before it patched, `start()` raises the `ConfigurationError` that `get_provider_manager` raises, and `_resolve_dm_channel` is never called |
| AC5.5 | A server holding a different tag of the configured model is not reported available, and an untagged configured name still matches its `:latest`. | Tests in `tests/test_ollama_provider.py`: configured `workmain-intent:latest` with `/api/tags` listing only `workmain-intent:v1.6` → `UNAVAILABLE`; listing `workmain-intent:latest` → `AVAILABLE`; the existing `test_model_prefix_matching` (`mistral` against `mistral:latest`) still passes |
| AC6.1 | The full suite passes with no net test loss. | `pytest` passes; count is at least the baseline in §6 |
| AC6.2 | The template provider and the documentation describe the layout as built. Property of documents — Ray's stated reading of `config/providers/_template/`, `CLAUDE.md` § Local Model Definitions, and `docs/AI_SETTINGS_GUIDE.md`'s Overview, § Ollama Fields, § The request payload policy and § How to add a new provider. | Stated reading by Ray |

## 6. Test plan

- **Baseline:** the suite count in `CHANGELOG.md`'s `[1.34.2]` entry.
- **Expected after:** baseline, minus the three `TestIntentParserConfig` tests Step 2 deletes, plus the tests below.
- `tests/test_ollama_provider.py` — AC5.5's two new cases, using the existing `_tags_response` helper.
- `tests/test_intent_parser.py` — AC5.2's four cases. The manager is a `MagicMock` whose `get_provider` returns an object with a patched `check_availability`, or raises; no network.
- `tests/test_eod_workflow.py` — AC5.3, one test per step, patching `workmain.ai.intent_parser.get_provider_manager` to raise. Uses the existing `db_session` and sentinel-date fixtures. `_keyword_score_match` / `_keyword_note_dedup_match` are spied with a patch so "never called" is asserted, not inferred.
- `tests/test_orchestration.py`, which holds the daemon tests — AC5.4. Patch `build_scheduler`, `_check_not_root`, `_ensure_daemon_dirs`, `_configure_logging` and the three `auth` reads; patch `get_provider_manager` in `workmain.daemon.daemon` to raise; assert `pytest.raises` and that `_resolve_dm_channel` was not called.
- Existing EOD tests keep patching `OllamaProvider.check_availability`; with `IntentParser` real, the probe now reaches that method through the manager's instance.

## 7. Risks and rollback

- **IaC sync breaks on merge.** `sync_modelfile.sh` reads both deleted files. The live model is unaffected (AC3.1 proves the new source matches it), so nothing breaks at runtime; only the next rebuild waits for the script. What the workmain side guarantees the script: the Modelfile at `config/providers/ollama/models/workmain-intent/Modelfile` is complete as written and needs no generation; its version is the value on its `^# version: (\S+)$` line; the build name is `workmain-intent:latest`, tagged `workmain-intent:v<version>`.
- **IaC handoff.** Ray runs the IaC script manually, after the PR merges and the workmain checkout is back on `main`. It reads the Modelfile from the workmain working tree, copies it to the LXC and runs the build there. It reads whatever branch is checked out, so running it from `main` after merge is the only guard.
- **IaC warm-up is required.** workmain no longer pre-loads the model (DR7), and `keep_alive` does not load one. After an Ollama or LXC restart the first request loads the model from disk — measured at ~112 s from a warm disk and ~243 s after a reboot — which exceeds the 30 s timeout, so that request fails. The IaC side warms the model after a restart and checks it regularly; the window before that completes is accepted.
- **The EOD config-fault path is CLI-only in practice** (DR6). A fault the daemon would hit fails its start instead.
- **Restart loop on a config fault.** With `Restart=on-failure`, a broken provider policy makes the daemon restart every 30 s until fixed, each attempt logged with the `ConfigurationError`. That is the intended visibility (Q4); today the same fault surfaces only at the first Slack DM.
- **Slower EOD when Ollama is unreachable.** Each probe now waits the configured 30 s instead of 15 s.
- **Rollback.** Each step is one commit and reverts cleanly in reverse order. Reverting Step 2 restores the two deleted files from git.
