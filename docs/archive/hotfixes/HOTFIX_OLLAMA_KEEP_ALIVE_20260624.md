# Hotfix: Ollama keep_alive + timeout hardening
**Branch:** `hotfix/ollama-keep-alive`
**Version:** v1.22.2 → v1.22.3
**Date:** 20260624

---

## Problem

`workmain eod` freezes on step 3c (carry-forward task match) when Ollama is
reachable but the model is cold (not loaded in GPU/RAM). The 15-second probe
in `_run_task_match_step` passes because `/api/tags` responds immediately, but
the subsequent `/api/generate` call blocks for the full 120-second timeout
before timing out. With multiple carry-forward tasks, the step can hang for
several minutes, emitting repeated:

```
WARNING:workmain.ai.intent_parser:parse_task_match error: timed out
```

**Root cause:** The Ollama server's default `keep_alive` (5 minutes) evicts the
model from VRAM between EOD runs. The next `/api/generate` must reload the model
into GPU RAM before responding — easily exceeding the 120s timeout. The 120s
`timeout` in `ai_settings.json` compounds this by making each failed call block
for 2 minutes before the exception fires.

---

## Fix

### 1. `workmain/ai/providers/ollama.py` → v1.3

Add `"keep_alive": -1` to the `/api/generate` payload. The Ollama API honours
this field per-request, keeping the model resident in VRAM indefinitely after
each call. This supplements the `OLLAMA_KEEP_ALIVE=-1` systemd environment
variable applied on the LXC host (server-level default), providing belt-and-
suspenders coverage in case the server default is ever changed.

Also reduce the hard-coded fallback default timeout from 120 → 30 seconds.

### 2. `config/ai_settings.json`

Reduce Ollama `"timeout"` from `120` to `30`. Generating 64 tokens from a loaded
model completes in well under 30 seconds. A tighter timeout allows the keyword
fallback in `_run_task_match_step` to engage sooner if Ollama is genuinely
unresponsive.

---

## Files Changed

| File | Change | Version |
|------|--------|---------|
| `workmain/ai/providers/ollama.py` | Add `keep_alive: -1` to payload; default timeout 120→30 | v1.2 → v1.3 |
| `config/ai_settings.json` | `timeout` 120 → 30 | n/a |
| `workmain/__version__.py` | Patch bump v1.22.2 → v1.22.3 (also correct stale 1.22.1 variable) | — |
| `CHANGELOG.md` | Add [1.22.3] entry | — |

---

## Verification

1. `python -m pytest tests/ -x -q` — baseline 624 passed
2. Run `workmain eod --skip condense,sync,pre_flight_inspection,review,report,email,clockify,gdocs`
   with Ollama cold — step 3c should fall back to keyword scoring within 30s
   (not 120s) if model is not loaded
3. After model warms up, `parse_task_match` calls should complete in 1–5s
