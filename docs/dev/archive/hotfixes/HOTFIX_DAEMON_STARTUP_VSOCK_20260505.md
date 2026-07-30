# Hotfix — Daemon Startup Ordering + AF_VSOCK + AssertUser
20260505

## Summary

Three bugs fixed in this hotfix, all affecting the workmain-notify systemd service.

---

## Bug 1 — Daemon Startup Ordering (Critical)

### Root Cause

`daemon.py` `main()` called `_schedule_meeting_reminders()` and logged "daemon running"
AFTER `scheduler.start()`, which is a blocking call that never returns until SIGTERM.
These two lines only executed during shutdown, not startup.

### Impact

Pre-meeting reminders were never scheduled. The 15-minute pre-meeting reminder feature
was completely non-functional since Gate 8.

### Fix

Move `_schedule_meeting_reminders()` and the "daemon running" log to before
`scheduler.start()`. APScheduler accepts jobs added before `start()` — they fire
correctly once the scheduler is running.

---

## Bug 2 — AF_VSOCK Missing from RestrictAddressFamilies

### Root Cause

`workmain-notify.service` had:
```
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
```

WSL2 interop (the mechanism that allows running Windows `.exe` files from Linux) uses
`AF_VSOCK` sockets to communicate between the Linux process and the Windows NT kernel
side. Without `AF_VSOCK` in the allowed set, every call to `wsl-notify-send.exe`
from within the daemon failed with `EAFNOSUPPORT` (errno 97) and exit code 1.

WSL error in journal: `WSL (...) ERROR: UtilBindVsockAnyPort:307: socket failed 97`

### Impact

`wsl-notify-send.exe` always returned exit code 1 from the daemon, so Windows toast
notifications were never delivered. Only the terminal fallback appeared.

### Fix

```
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX AF_VSOCK
```

Confirmed fix with `systemd-run --user` before applying.

### Note for Future Portability

`AF_VSOCK` is required for WSL2 interop. On native Linux (Phase 18 service promotion),
this entry can be removed if the deployment does not use any WSL-specific tools.
Document in FEATURE_BACKLOG Item 30.

---

## Bug 3 — AssertUser=!root Unknown Directive

### Root Cause

`AssertUser=!root` is not a recognized systemd directive in the installed version.
Systemd ignores it and logs a warning on every service load/reload/restart.

### Impact

Warning spam in the journal. The Python-level `_check_not_root()` in `daemon.py` is
the authoritative enforcement mechanism (noted in the service file comments).

### Fix

Remove `AssertUser=!root` from the service file.

---

## Files Changed

| File | Version | Change |
|------|---------|--------|
| `workmain/daemon/daemon.py` | v1.0 → v1.1 | Fix startup ordering |
| `deploy/workmain-notify.service` | v1.0 → v1.1 | Add AF_VSOCK, remove AssertUser |
| `workmain/__version__.py` | v1.11.1 → v1.11.2 | Patch version bump |
| `CHANGELOG.md` | — | v1.11.2 entry |

## Post-Fix Steps

```bash
cp deploy/workmain-notify.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user restart workmain-notify
journalctl --user -u workmain-notify -f
```

Expected log order on startup:
1. "workmain-notify daemon starting."
2. "Pre-meeting reminders scheduled: N"
3. "workmain-notify daemon running."
4. Scheduler jobs added

## Verification

```bash
# Confirm clean startup log order
journalctl --user -u workmain-notify --since "1 min ago"

# Confirm no AssertUser warnings
journalctl --user -u workmain-notify | grep -c AssertUser

# Wait for or trigger a scheduled job and confirm Windows toast appears
workmain notifications test os   # Should produce terminal + Windows toast
```
