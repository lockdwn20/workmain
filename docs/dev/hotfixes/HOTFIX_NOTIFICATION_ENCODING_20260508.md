# Hotfix — Notification Em Dash Encoding + Delivery Logging
20260508

## Summary

Two issues with OS notification delivery:

1. **Em dash garbling** — Notification titles and narration body text contain em dash characters (`—`, U+2014). Windows does not default to UTF-8 (codepage 65001), so `wsl-notify-send.exe` receives the bytes but Windows renders them as garbage characters. Affects all hardcoded scheduler job titles and any AI-narrated body text that includes em dashes.

2. **Silent delivery failures** — `_deliver_os()` calls `subprocess.run(..., capture_output=True)`, so any output from `wsl-notify-send.exe` is silently discarded. Combined with the binary exiting 0 on soft failures, the daemon logs "Delivered enriched notification" regardless of whether Windows actually showed the toast. The journal gives no diagnostic signal when delivery fails.

## Root Cause

### Em dash encoding

`workmain/daemon/scheduler.py` hardcodes titles with em dashes:
```python
_enriched_notify("WorkmAIn — Good Morning")
_enriched_notify("WorkmAIn — Daily Closeout")
...
```

`_deliver_os()` in `delivery.py` passes `title` and `body` directly to the subprocess. The `body` comes from Claude narration and may also contain em dashes. Windows resolves command-line args using the active system codepage (typically CP1252 on English Windows), not UTF-8, so `—` (0xE2 0x80 0x94 in UTF-8) is not correctly decoded.

### Silent delivery failures

`_deliver_os()`:
```python
subprocess.run([NOTIFY_CMD, "--category", title, body],
               timeout=5, check=True, capture_output=True)
```

`capture_output=True` suppresses all stdout/stderr from `wsl-notify-send.exe`. The success log in `daemon.py` fires unconditionally after `deliver()` returns, so the journal never distinguishes between OS delivery and terminal fallback.

## Fix

### 1. Em dash sanitization in `delivery.py`

Add `_sanitize_for_windows()` helper that replaces em dash and en dash with ` - ` before passing strings to the subprocess:

```python
def _sanitize_for_windows(text: str) -> str:
    return text.replace('—', ' - ').replace('–', ' - ')
```

Apply to both `title` and `body` in `_deliver_os()`.

### 2. Subprocess output logging in `delivery.py`

Log captured stdout/stderr at WARNING level when non-empty so failures are visible in the journal. Also log the resolved `NOTIFY_CMD` path at INFO on first delivery for diagnostics.

### 3. Em dash replacement in `scheduler.py` job titles

Replace `—` with ` - ` in all five hardcoded `_enriched_notify()` title strings. Belt-and-suspenders alongside the sanitization step.

## Files Changed

| File | Version | Change |
|------|---------|--------|
| `workmain/daemon/delivery.py` | v1.1 → v1.2 | Add `_sanitize_for_windows()`, apply to title/body, log subprocess output |
| `workmain/daemon/scheduler.py` | v1.1 → v1.2 | Replace em dashes in hardcoded job titles |
| `workmain/__version__.py` | — | v1.12.0 → v1.12.1 patch bump |
| `CHANGELOG.md` | — | v1.12.1 entry |

## Version

v1.12.0 → v1.12.1 (patch)

## Verification

```bash
workmain notifications test os     # Windows toast should appear with clean title
journalctl --user -u workmain-notify.service -f   # confirm NOTIFY_CMD path logged
python -m pytest tests/            # 232 passed expected
workmain --version                 # 1.12.1
```
