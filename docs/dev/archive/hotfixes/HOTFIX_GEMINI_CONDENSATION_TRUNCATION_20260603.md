# Hotfix: Gemini Note Condensation Truncation

**Date:** 20260603
**Branch:** hotfix/gemini-condensation-truncation
**Version:** v1.18.0 → v1.18.1

---

## Problem

After Gemini became the primary provider, `workmain notes log` produces truncated condensed summaries. Example:

```
Sending to Gemini...
✓ Condensed: "Splunk Normalization Sync: Reviewed app"
```

Expected (as produced by Claude previously):
```
✓ Condensed: "DE Standup: Discussed TIE team's XSOAR migration concerns due to lack of dev environment and source control, troubleshot PR automation 404 error."
```

The truncated summary is saved to `meetings.condensed_summary` and used as the Clockify time entry description — breaking the time tracking workflow.

## Root Cause

`gemini-2.5-flash` enables internal "thinking" by default. Thinking tokens count against the same `max_output_tokens` budget as the visible response text. With `max_tokens=200` in `note_condenser.py`, Gemini exhausts the budget on reasoning and has almost no tokens left for the actual summary, producing mid-phrase cutoffs.

Claude did not exhibit this because Claude's `max_tokens` parameter controls completion tokens only — it has no built-in thinking phase.

The fix cannot disable Gemini thinking via `ThinkingConfig` because the installed SDK (`google-genai==0.3.0`) does not expose that class.

## Fix Applied

**File:** `workmain/ai/note_condenser.py`
**Change:** Line 141 — `max_tokens=200` → `max_tokens=1024`

1024 tokens gives Gemini sufficient budget for its thinking phase (~200–500 tokens) plus the actual one-liner response (~20–40 tokens), while remaining well below Gemini's 8,192-token default. Cost impact per condensation is negligible (~$0.0006 at $0.60/MTok output pricing).

## Files Changed

| File | Version Change | Description |
|------|---------------|-------------|
| `workmain/ai/note_condenser.py` | v1.9 → v2.0 | Raise max_tokens 200→1024 |
| `workmain/__version__.py` | v1.18.0 → v1.18.1 | Patch bump |
| `CHANGELOG.md` | — | Entry added |

## Verification

1. `python -m pytest tests/` → 479 passed, 0 failed
2. `workmain notes log -m <id>` → enter notes → confirm condensed output is a complete sentence
