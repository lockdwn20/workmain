# Hotfix — wsl-notify-send Invocation Bug
20260505

## Summary

Windows toast notifications were not appearing despite `notifications set os` being configured.
The `wsl-notify-send.exe` binary was being called with two positional arguments (title, body)
but v0.1 of the binary only accepts one positional argument. Passing two args causes the binary
to print its usage to stdout and exit 0 without sending a toast.

## Root Cause

`workmain/daemon/delivery.py` `_deliver_os()` called:

```python
subprocess.run([NOTIFY_CMD, title, body], ...)
```

`wsl-notify-send` v0.1 interface:
- `--category <string>` — notification title / app label in Windows Action Center
- One positional arg — the message body text

Passing two positional args triggers the binary's usage output and exits 0.
`check=True` never raised because exit code was 0. The terminal output the user
saw was the always-echo `_deliver_terminal()` call at line 113, not a fallback.

## Fix

Change the subprocess invocation to use `--category` for the title:

```python
subprocess.run([NOTIFY_CMD, "--category", title, body], ...)
```

Confirmed working invocation (tested 2026-05-05):
```
wsl-notify-send.exe --category "WorkmAIn" "Test message body"
```

## Files Changed

| File | Version | Change |
|------|---------|--------|
| `workmain/daemon/delivery.py` | v1.0 → v1.1 | Fix subprocess invocation |
| `workmain/__version__.py` | v1.11.0 → v1.11.1 | Patch version bump |
| `CHANGELOG.md` | — | v1.11.1 entry |

## Version

v1.11.0 → v1.11.1 (patch)

## Verification

```bash
workmain notifications set os
workmain notifications test os   # Windows toast should appear
python -m pytest tests/          # 221 passed expected
workmain --version               # 1.11.1
```
