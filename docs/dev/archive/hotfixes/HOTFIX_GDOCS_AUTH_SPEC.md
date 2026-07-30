WorkmAIn
HOTFIX_GDOCS_AUTH_SPEC v1.0
20260310

# Hotfix Spec: GDocs Auth Token Refresh Fix

**Branch:** `hotfix/gdocs-auth-refresh`
**Branch from:** `main` (currently v1.5.1)
**Merge to:** `main` then `dev`
**Target version:** v1.5.2
**Spec version:** v1.0

---

## Problem

`workmain gdocs upload-all` (and all `gdocs` upload commands) fail with
"Not authenticated. Run: workmain gdocs auth" when the Google access token
has expired — even when a valid refresh token exists and no user interaction
is required.

**Root cause:** `_require_auth()` in `workmain/integrations/gdrive/auth.py`
calls `is_authenticated()`, which checks `creds.valid`. Google access tokens
expire after ~1 hour. When expired, `creds.valid` returns `False` even if
`creds.refresh_token` is present and the token can be silently refreshed.
The function returns `False` and the upload is blocked before `get_credentials()`
is ever reached.

**Why Option A (check for refresh_token) was rejected:** Answering "do you have
a refresh token?" is not the same as answering "can you actually authenticate?"
A token may be expired, revoked, or fail to refresh due to network or Google-side
issues. Option A moves the failure surface into the upload operation itself where
the error message is less clear. The spec (PHASE7_GDRIVE_SPEC_v1_0.md §3.10)
explicitly documents: "Token expired → Auto-refresh attempted. If fails:
'Token expired. Run: workmain gdocs auth --reauth'" — which requires the
attempt to actually be made.

**Fix:** Replace the `is_authenticated()` check in `_require_auth()` with a
`get_credentials()` call that silently refreshes the token if expired. If
`get_credentials()` raises `GDriveAuthError` (requires interactive login),
print the not-authenticated message and exit.

---

## Pre-Hotfix Checklist

Claude Code must complete these before writing any code:

```bash
git checkout main
git pull
git checkout -b hotfix/gdocs-auth-refresh
git status   # must be clean
```

Confirm current application version:
```bash
workmain version   # expect 1.5.1
```

---

## Gate 1 — Fix `_require_auth()` in `auth.py`

### 1.1 File

**`workmain/integrations/gdrive/auth.py`** — bump version (check current header)

### 1.2 Current Code (locate and verify before editing)

```python
def _require_auth() -> None:
    if not is_authenticated():
        console.print("Not authenticated. Run: workmain gdocs auth")
        sys.exit(1)
```

### 1.3 Replacement

```python
def _require_auth() -> None:
    try:
        get_credentials()
    except GDriveAuthError:
        console.print("Not authenticated. Run: workmain gdocs auth")
        sys.exit(1)
```

**That is the complete change.** No other logic in this file should be touched.

### 1.4 What this does

- If the token is valid: `get_credentials()` returns immediately, no network call.
- If the token is expired but has a refresh token: `get_credentials()` silently
  refreshes via the Google OAuth library and returns. The upload proceeds.
- If refresh fails (revoked, network error, etc.): `get_credentials()` raises
  `GDriveAuthError`, the user sees the correct message and is directed to
  re-authenticate.

`is_authenticated()` is not removed or changed — it is still used by
`workmain gdocs status` and `workmain gdocs auth` to display auth state.
Only `_require_auth()` is changed.

### 1.5 Version bump

Increment the file-level version number in the `auth.py` header and add a
version history entry:

```
- vX.Y: Fix _require_auth() to call get_credentials() instead of is_authenticated(),
        enabling silent token refresh on expiry
```

### 1.6 Gate 1 Verification

**Step 1 — Confirm the change is correct:**
```bash
grep -A 5 "_require_auth" workmain/integrations/gdrive/auth.py
```
Must show `get_credentials()` inside the try block, not `is_authenticated()`.

**Step 2 — Simulate an expired token:**

The simplest way to verify without waiting an hour is to temporarily corrupt
the `expiry` field in `~/.workmain/integrations/gdrive/token.json` to a past
timestamp (e.g. `"2020-01-01T00:00:00Z"`), then run an upload command.

```bash
# Backup token
cp ~/.workmain/integrations/gdrive/token.json /tmp/token_backup.json

# Edit expiry to force expiration (set to a past date)
# Open token.json and change "expiry" to "2020-01-01T00:00:00.000000Z"
# (do not change access_token or refresh_token)

# Run upload — must succeed (silent refresh), NOT produce auth error
workmain gdocs upload-notes --dry-run

# Restore token backup
cp /tmp/token_backup.json ~/.workmain/integrations/gdrive/token.json
```

Expected result: command succeeds (or dry-run completes without auth error).
If the fix is working, the token will be silently refreshed and a new `expiry`
value will be written to `token.json`.

**Step 3 — Confirm existing auth flow is unaffected:**
```bash
workmain gdocs status        # must show Authenticated
workmain gdocs auth          # must show "Already authenticated. Use --reauth to refresh."
```

**Stop here and present Gate 1 results. Do not proceed to Gate 2 without confirmation.**

---

## Gate 2 — Version Bump + Merge

### 2.1 File Updates

**`workmain/__version__.py`** — bump to v1.5.2

```python
"""
WorkmAIn Package Version
Version v1.5.2
20260310

Version History:
- v1.5.2: Hotfix — gdocs _require_auth() now calls get_credentials() for silent
          token refresh on expiry instead of checking is_authenticated()
- v1.5.1: Hotfix — post-weekly report generation subprocess → Python API fix
- v1.5.0: Phase 8 complete — Slack integration
"""

__version__ = "1.5.2"
```

**`CHANGELOG.md`** — add entry at top:

```markdown
## v1.5.2 — 20260310

### Fixed
- `workmain gdocs upload-all` (and all gdocs upload commands) now silently
  refresh expired Google access tokens instead of incorrectly reporting
  "Not authenticated". Root cause: `_require_auth()` checked `creds.valid`
  which is False on expiry even when a valid refresh token exists.
  Fix: `_require_auth()` now calls `get_credentials()` which handles refresh
  transparently. Only surfaces an auth error when interactive login is
  genuinely required.
```

### 2.2 Merge Sequence

```bash
# Merge to main
git checkout main
git merge --no-ff hotfix/gdocs-auth-refresh -m "fix(gdocs): silent token refresh in _require_auth() (v1.5.2)"
git tag v1.5.2

# Carry fix forward to dev
git checkout dev
git merge --no-ff hotfix/gdocs-auth-refresh -m "chore: merge hotfix/gdocs-auth-refresh into dev"

# Clean up branch
git branch -d hotfix/gdocs-auth-refresh

# Verify
git log --oneline -5
```

### 2.3 Gate 2 Verification

```bash
workmain version          # must show 1.5.2
git log --oneline -3      # confirm clean merge history
git tag                   # confirm v1.5.2 tag present

# Full EOD gdocs step still works end-to-end
workmain eod --skip condense,sync,review,report,email,clockify   # gdocs only
```

**Stop here and present Gate 2 results.**

---

## Summary of Files Modified

| File | Change | Version |
|------|--------|---------|
| `workmain/integrations/gdrive/auth.py` | `_require_auth()` calls `get_credentials()` instead of `is_authenticated()` | bump |
| `workmain/__version__.py` | v1.5.1 → v1.5.2 | v1.5.2 |
| `CHANGELOG.md` | v1.5.2 entry | — |

**Total: 3 files. No database changes. No migration required.**

---

## Instructions for Claude Code

1. Read `GIT_WORKFLOW_STANDARDS.md` before starting
2. Branch from `main`: `git checkout -b hotfix/gdocs-auth-refresh`
3. Execute Gate 1 first — make the single targeted change to `_require_auth()` only
4. Run Gate 1 verification including the expired token simulation
5. Stop after Gate 1 and present results — wait for confirmation before Gate 2
6. Do not modify `is_authenticated()` — it is used by other commands and is correct for its purpose
7. Do not touch any other files in `auth.py` beyond the version bump and `_require_auth()`
8. Do not combine gates

---

END OF HOTFIX SPEC
WorkmAIn HOTFIX_GDOCS_AUTH_SPEC v1.0 — 20260310
