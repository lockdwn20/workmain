WorkmAIn
SESSION_HANDOFF_PHASE13_SPRINT1_COMPLETE_20260605
Phase 13 Sprint 1 — Ollama Provider Activation

---

## Sprint Summary

Phase 13 Sprint 1 activated the OllamaProvider stub, built the intent parsing
pipeline against Mistral 7B on Proxmox, and validated prompt quality through a
live benchmark. The key architectural decision was pulling the Modelfile approach
forward from the backlog: the system prompt and generation parameters are baked
into `workmain-intent:latest` rather than injected per-request, keeping the
context window clean for every Slack DM parse.

**Version:** v1.19.0 (tagged after PR merge to main)
**Branch:** `feature/phase-13-sprint1-ollama-provider` → merged to `dev` → PR #18 (dev → main)
**Suite:** 501 passed, 0 failed

---

## Gate Log

| Gate | Deliverable | Commit | Notes |
|------|-------------|--------|-------|
| 0 | note_condenser writing style fix; feature branch cut | `4ce3c59` | v2.1 — StyleAdapter replaces broken _format_writing_style_context |
| 1 | OllamaProvider v1.1/v1.2; Migration 018; Item 36; tests | `13817f8`, `a36587a` | two commits — Gate 1 impl + v1.8 arch update |
| 2 | IntentParser v1.0; config files; benchmark approved 9/10 | `a36587a` | same commit as Gate 1 v1.8 update |
| 3 | IntentParser v1.1 cost tracking; test_intent_parser.py | `f677067` | 12 tests |
| 4 | v1.19.0 bump; CHANGELOG; backlog; test_ai_clients fix | `116ac22`, `3eb0dcb` | system prompt header update committed separately |
| merge | feature → dev (no-ff); PR #18 created | `d748188` | branch deleted |

---

## File Versions at v1.19.0

| File | Version |
|------|---------|
| `workmain/__version__.py` | v1.19.0 |
| `workmain/ai/base_provider.py` | v1.2 |
| `workmain/ai/__init__.py` | v1.5 |
| `workmain/ai/providers/ollama.py` | v1.2 |
| `workmain/ai/intent_parser.py` | v1.1 |
| `workmain/ai/note_condenser.py` | v2.1 |
| `workmain/database/models.py` | v2.6 |
| `config/ai_settings.json` | v1.2 |
| `config/intent_parse_prompt.json` | v1.1 |
| `config/intent_parse_system_prompt.txt` | config_version 1.1 |
| `tests/test_ollama_provider.py` | v1.0 (10 tests) |
| `tests/test_intent_parser.py` | v1.0 (12 tests) |
| `tests/test_ai_clients.py` | v1.4 |
| `tests/test_ai_foundation.py` | v1.4 |
| `tests/test_provider_foundation.py` | v1.1 |
| `CHANGELOG.md` | [1.19.0] entry added |
| `docs/FEATURE_BACKLOG.md` | v5.15 |

---

## Infrastructure

- **Ollama host:** `workmain-ollama.lab.haloschaos.com:11434`
- **Base model:** `mistral:latest` (Q4_K_M, 7.2B parameters, 32K context)
- **Intent model:** `workmain-intent:latest` (alias → `workmain-intent:v1.1`)
- **Modelfile:** `ollama-lxc/models/workmain-intent/Modelfile` (IaC repo)
- **System prompt source:** `config/intent_parse_system_prompt.txt` (config_version 1.1)
- **ai_settings.json ollama:** model `workmain-intent:latest`, timeout 120s

---

## Gate 2 Benchmark Report (preserved for Sprint 2 reference)

**Model:** `workmain-intent:latest` (v1.1 Modelfile, 20260605)
**Result:** 9/10 pass, 0 fail, 1 partial

| # | Input | Action | Pass/Fail | Latency |
|---|-------|--------|-----------|---------|
| 1 | "spent 90 minutes on the TIE team XSOAR migration" | create_time_entry (90 min) | PASS | 72.1s (cold) |
| 2 | "finished the Splunk normalization doc review" | update_task (completed) | PASS | 7.7s |
| 3 | "note: PR automation pipeline throwing 404 on merge trigger" | create_note | PASS | 7.3s |
| 4 | "still waiting on dev environment access from the TIE team, blocking XSOAR work" | create_note (blocker) | PARTIAL — carry-forward missing | 10.8s |
| 5 | "need to follow up with Matt on the normalization schema tomorrow" | defer_task | PASS | 2.7s |
| 6 | "daily report looks good, confirm it" | confirm_report (daily_internal) | PASS | 5.4s |
| 7 | "fix the daily — I spent 2 hours on XSOAR not 90 minutes" | correct_report (120 min) | PASS | 10.9s |
| 8 | "done with standup, also logged 30 min for email triage" | create_time_entry (30 min) | PASS | 8.2s |
| 9 | "working on the Splunk alert fidelity metrics for Emily" | create_note | PASS | 7.2s |
| 10 | "hey what's the weather like" | unknown + follow_up | PASS | 7.3s |

**Sample 4 note:** carry-forward tag consistently absent despite "still waiting" rule.
Known Mistral 7B limitation — multi-tag inference unreliable at 7B model size.
Accepted as-is; not a prompt issue.

**Cold start:** Sample 1 took 72.1s (model loading from storage). Subsequent requests
7–11s. 120s timeout provides headroom. Sprint 2 warm-up ping will eliminate this.

---

## Key Architectural Decisions

1. **Modelfile owns system prompt and generation params at runtime** — `intent_parser.py`
   passes `system_prompt=None`; the Modelfile SYSTEM block is the runtime authority.
   `config/intent_parse_system_prompt.txt` is the human-readable source of truth synced
   to the IaC Modelfile — it is NOT a runtime artifact.

2. **Only `num_predict` (max_tokens) sent per-request** — temperature, top_p, top_k,
   repeat_penalty are baked into the Modelfile PARAMETER blocks. `generation_options`
   in the JSON is an editable reference for rebuilds, not a per-request override.

3. **Versioned Modelfile approach** — build `workmain-intent:v1.N`, tag as `latest`.
   `ai_settings.json` always points to `workmain-intent:latest`. Roll back by retagging.

4. **`config/intent_parse_prompt.json` `_doc` block** — metadata for rebuild workflow:
   `ollama_model`, `ollama_host`, `model_built` date. Update after each Modelfile rebuild.

---

## Known Issues / Deferred

| Issue | Status | Target |
|-------|--------|--------|
| carry-forward tag inference (Sample 4) | Accepted — 7B model limit | Sprint 2/3 fine-tuning if data available |
| Cold-start latency 55–72s | Item 38 — warm-up ping on bot startup | Sprint 2 Gate 0 prerequisite |
| Modelfile tuning workflow as schema grows | Item 37 — ongoing maintenance | Sprint 2/3 |
| GPU offloading (RTX 4070) | Item 19 — CPU path sufficient | Phase 14+ |

---

## Sprint 2 Prerequisites and First Tasks

### Must complete before Sprint 2 Gate 0
- [ ] **Item 38 — Ollama warm-up ping** on Slack bot startup; eliminates cold-start for
  first real user message. Budget ~30 min. Wire into bot startup sequence before poll loop.
- [ ] Confirm `workmain-intent:latest` is reachable from Sprint 2 bot environment
  (same LAN; same host/port in ai_settings.json)
- [ ] Review Sprint 2 spec for action vocabulary additions — rebuild Modelfile after
  any schema change using the workflow in `config/intent_parse_system_prompt.txt` header

### Sprint 2 first tasks
- Inbound Slack polling (T1–T6 trigger types)
- Action executor / orchestration layer
- Confirmation UX (Block Kit)
- Wire `IntentParser.parse()` into the Slack DM handler

### Modelfile rebuild workflow (per Sprint 2/3 schema changes)
1. Edit `config/intent_parse_system_prompt.txt`
2. Sync SYSTEM block to `ollama-lxc/models/workmain-intent/Modelfile`
3. Run `build_workmain_intent.sh` on Proxmox LXC
4. Increment `config_version` in txt header; update `model_built` date
5. If new ollama_model suffix (e.g. `v1.2`): update `ai_settings.json` model field
6. Update `_doc.model_built` in `config/intent_parse_prompt.json`

---

END OF HANDOFF
WorkmAIn Phase 13 Sprint 1 — 20260605
