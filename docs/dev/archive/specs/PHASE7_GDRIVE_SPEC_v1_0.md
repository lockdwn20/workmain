WorkmAIn
PHASE7_GDRIVE_SPEC v1.0
20260306

# Phase 7 — Google Drive Integration
## Implementation Specification for Claude Code

---

## Session Context

**Application Version:** v1.3.1
**Target Version:** v1.4.0
**Branch:** `feature/phase-7-gdocs` (from `dev`)
**Date:** 20260306
**Spec Version:** v1.0

---

## Problem Statement

Daily work artifacts (notes, reports, Clockify PDFs) are generated and staged
locally but have no persistent archive. Phase 7 implements Google Drive archival
so that all daily artifacts land in a structured, date-organized Drive folder
automatically as part of the end-of-day workflow.

---

## Scope Overview

| Area | Delivered This Phase |
|------|---------------------|
| `~/.workmain/` directory restructure | ✓ Gate 0 |
| `outlook_client.py` → `outlook/client.py` | ✓ Gate 0 |
| `GDRIVE_TIMECARDS_ROOT` env var | ✓ Gate 0 |
| `gdrive_uploads` DB table | ✓ Gate 1 |
| Google Drive integration module | ✓ Gate 2 |
| `workmain gdocs` command group | ✓ Gate 3 |
| `workmain eod` Step 6 (Drive upload) | ✓ Gate 4 |
| Integration testing — all gates verified | ✓ Gate 5 |
| Version bump + CHANGELOG + handoff | ✓ Gate 6 |

---

## Architecture Decisions

### Auth Method
OAuth2 user flow via WSL-compatible console flow (copy-paste URL + auth code).
No browser spawn required. Reuses the probe token created during pre-spec
discovery (`~/.workmain/gdrive_probe_token.json` → moved to canonical path
in Gate 0).

Scope: `https://www.googleapis.com/auth/drive.file`
This scope only allows the app to see files it creates — least privilege.

### Folder ID Persistence
`~/.workmain/integrations/gdrive/cache.json` (chmod 600)
Caches Drive folder IDs to avoid re-querying Drive on every command.
Cache is keyed by `YYYYMM` period — one entry per month folder.

### Drive Folder Structure
Controlled by `GDRIVE_TIMECARDS_ROOT` env var in `.env`.
```
{GDRIVE_TIMECARDS_ROOT}/
└── YYYYMM/
    ├── Raw_Notes/
    ├── Reports/
    └── Clockify/
```

### Local Staging (already in place from v1.3.1 hotfix)
```
staging/
├── notes/       → Drive: YYYYMM/Raw_Notes/
├── reports/     → Drive: YYYYMM/Reports/
└── clockify/    → Drive: YYYYMM/Clockify/
```

### Module Location
`workmain/integrations/gdrive/` — mirrors the clockify integration pattern.

### DB Upload Tracking
`gdrive_uploads` table tracks every file uploaded to Drive.
Enables `gdocs status` to show history and prevents duplicate uploads.

---

## Gate 0 — Pre-Phase Housekeeping

**Complete Gate 0 fully before writing any Phase 7 code.**
Gate 0 touches existing production paths and integrations.
Verify each checkpoint before advancing.

---

### Gate 0.1 — `~/.workmain/` Directory Restructure

**Before:**
```
~/.workmain/
├── credentials.json          # Google OAuth client secret (probe artifact)
├── gdrive_probe_token.json   # OAuth token (probe artifact)
└── encryption.key            # Fernet encryption key (existing)
```

**After:**
```
~/.workmain/
├── encryption.key            # unchanged
└── integrations/
    ├── clockify/             # placeholder for future clockify auth migration
    ├── outlook/              # placeholder for future outlook auth migration
    └── gdrive/
        ├── credentials.json  # moved from ~/.workmain/credentials.json
        ├── token.json        # moved from ~/.workmain/gdrive_probe_token.json
        └── cache.json        # NEW — folder ID cache (created by gdocs auth)
```

**Migration steps:**
```bash
mkdir -p ~/.workmain/integrations/clockify
mkdir -p ~/.workmain/integrations/outlook
mkdir -p ~/.workmain/integrations/gdrive

# Move probe artifacts to canonical locations
mv ~/.workmain/credentials.json ~/.workmain/integrations/gdrive/credentials.json
mv ~/.workmain/gdrive_probe_token.json ~/.workmain/integrations/gdrive/token.json

# Set permissions
chmod 700 ~/.workmain/integrations/
chmod 700 ~/.workmain/integrations/clockify/
chmod 700 ~/.workmain/integrations/outlook/
chmod 700 ~/.workmain/integrations/gdrive/
chmod 600 ~/.workmain/integrations/gdrive/credentials.json
chmod 600 ~/.workmain/integrations/gdrive/token.json
```

**Verify:**
```bash
ls -la ~/.workmain/integrations/gdrive/
# Must show credentials.json and token.json with 600 permissions
```

---

### Gate 0.2 — `outlook_client.py` → `outlook/client.py`

Move the existing outlook integration file into a proper subdirectory
to match the clockify pattern.

```bash
mkdir -p workmain/integrations/outlook
mv workmain/integrations/outlook_client.py workmain/integrations/outlook/client.py
touch workmain/integrations/outlook/__init__.py
```

**Update all imports that reference `outlook_client`:**
```bash
grep -r "outlook_client" workmain/ --include="*.py" -l
```

Update each import from:
```python
from workmain.integrations.outlook_client import OutlookClient
```
To:
```python
from workmain.integrations.outlook.client import OutlookClient
```

**Verify:**
```bash
# Import resolves correctly
python -c "from workmain.integrations.outlook.client import OutlookClient; print('OK')"

# Calendar commands still work
workmain calendar today
workmain calendar import tests/fixtures/week_normal.ics --dry-run
```

---

### Gate 0.3 — `GDRIVE_TIMECARDS_ROOT` Environment Variable

Add to `.env`:
```bash
# Google Drive Integration (Phase 7)
GDRIVE_TIMECARDS_ROOT=Timecards
```

Add to `.env.example` (if it exists) with same key, empty value:
```bash
GDRIVE_TIMECARDS_ROOT=
```

**Verify:**
```bash
grep GDRIVE_TIMECARDS_ROOT .env
# Must return the entry
```

---

### Gate 0 Verification

```bash
# Directory structure
ls -la ~/.workmain/integrations/gdrive/

# Outlook import
python -c "from workmain.integrations.outlook.client import OutlookClient; print('OK')"

# Calendar still works
workmain calendar today

# Env var present
grep GDRIVE_TIMECARDS_ROOT .env

# No remaining outlook_client references
grep -r "outlook_client" workmain/ --include="*.py"
# Must return nothing
```

**Stop here. Present Gate 0 results. Do not proceed to Gate 1 without confirmation.**

---

## Gate 1 — Database Migration

### 1.1 Migration File

**File:** `workmain/database/migrations/005_add_gdrive_uploads.sql`

```sql
-- WorkmAIn Migration 005
-- Add gdrive_uploads table for tracking Drive archival
-- 20260306

CREATE TABLE gdrive_uploads (
    id          SERIAL PRIMARY KEY,
    local_path  TEXT        NOT NULL,
    drive_file_id TEXT      NOT NULL,
    drive_folder_id TEXT    NOT NULL,
    filename    TEXT        NOT NULL,
    upload_type TEXT        NOT NULL,  -- 'notes', 'report', 'clockify'
    upload_date DATE        NOT NULL,
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_gdrive_uploads_date ON gdrive_uploads(upload_date);
CREATE INDEX idx_gdrive_uploads_type ON gdrive_uploads(upload_type);
```

**Run migration:**
```bash
psql -U workmain_user -d workmain \
  -f workmain/database/migrations/005_add_gdrive_uploads.sql
```

### 1.2 SQLAlchemy Model

**File:** `workmain/database/models.py` (increment version)

Add `GDriveUpload` model:

```python
class GDriveUpload(Base):
    __tablename__ = "gdrive_uploads"

    id             = Column(Integer, primary_key=True)
    local_path     = Column(Text, nullable=False)
    drive_file_id  = Column(Text, nullable=False)
    drive_folder_id = Column(Text, nullable=False)
    filename       = Column(Text, nullable=False)
    upload_type    = Column(Text, nullable=False)  # 'notes', 'report', 'clockify'
    upload_date    = Column(Date, nullable=False)
    created_at     = Column(DateTime, default=datetime.utcnow, nullable=False)
```

### 1.3 Repository

**File:** `workmain/database/repositories/gdrive_repository.py` v1.0

```python
class GDriveRepository:
    def __init__(self, session: Session): ...

    def record_upload(
        self,
        local_path: str,
        drive_file_id: str,
        drive_folder_id: str,
        filename: str,
        upload_type: str,
        upload_date: date
    ) -> GDriveUpload: ...

    def get_uploads_for_date(self, upload_date: date) -> list[GDriveUpload]: ...

    def get_uploads_by_type(
        self, upload_type: str, limit: int = 10
    ) -> list[GDriveUpload]: ...

    def already_uploaded(
        self, filename: str, upload_date: date, upload_type: str
    ) -> bool: ...
```

Update `workmain/database/repositories/__init__.py` to export `gdrive_repository`.

### 1.4 Gate 1 Verification

```bash
# Migration applied
psql -U workmain_user -d workmain \
  -c "\d gdrive_uploads"

# Model imports correctly
python -c "from workmain.database.models import GDriveUpload; print('OK')"

# Repository imports correctly
python -c "from workmain.database.repositories.gdrive_repository import GDriveRepository; print('OK')"
```

**Stop here. Present Gate 1 results. Do not proceed to Gate 2 without confirmation.**

---

## Gate 2 — Google Drive Integration Module

### 2.1 Module Structure

```
workmain/integrations/gdrive/
├── __init__.py
├── auth.py      # OAuth2 flow, token management, WSL console flow
├── client.py    # Drive API operations
└── cache.py     # Folder ID cache management
```

---

### 2.2 `auth.py` v1.0

Responsibilities:
- Load credentials from `~/.workmain/integrations/gdrive/credentials.json`
- Load/save token from `~/.workmain/integrations/gdrive/token.json`
- Handle token refresh automatically
- WSL-safe auth flow using `run_console` (copy-paste URL + code — no browser spawn)
- Raise `GDriveAuthError` with clear message if credentials file missing

```python
CREDENTIALS_PATH = Path.home() / ".workmain" / "integrations" / "gdrive" / "credentials.json"
TOKEN_PATH       = Path.home() / ".workmain" / "integrations" / "gdrive" / "token.json"
SCOPES           = ["https://www.googleapis.com/auth/drive.file"]

class GDriveAuthError(Exception): ...

def get_credentials() -> Credentials:
    """
    Load credentials, refresh if expired, run console flow if no token.
    WSL-safe: uses run_console() not run_local_server().
    Saves token to TOKEN_PATH (chmod 600) after auth.
    Raises GDriveAuthError if credentials.json missing.
    """
    ...

def get_service():
    """
    Build and return authenticated Drive v3 service.
    """
    ...

def is_authenticated() -> bool:
    """
    Return True if a valid token exists. Does not attempt refresh.
    Used by `gdocs status` for quick check.
    """
    ...
```

**WSL console flow pattern (from probe):**
```python
flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
creds = flow.run_console()   # prints URL, waits for pasted code
```

---

### 2.3 `cache.py` v1.0

Responsibilities:
- Load/save folder ID cache from `~/.workmain/integrations/gdrive/cache.json`
- Cache structure: `{ "YYYYMM": { "root": id, "Raw_Notes": id, "Reports": id, "Clockify": id } }`
- chmod 600 on write

```python
CACHE_PATH = Path.home() / ".workmain" / "integrations" / "gdrive" / "cache.json"

def load_cache() -> dict: ...
def save_cache(cache: dict) -> None: ...  # chmod 600 after write

def get_folder_id(period: str, subfolder: str | None = None) -> str | None:
    """
    Return cached folder ID for period (YYYYMM) and optional subfolder
    (Raw_Notes, Reports, Clockify). Returns None if not cached.
    """
    ...

def set_folder_id(period: str, subfolder: str | None, folder_id: str) -> None:
    """
    Store folder ID in cache and persist.
    """
    ...
```

---

### 2.4 `client.py` v1.0

Responsibilities:
- Folder operations: get-or-create folder by name under parent
- File upload: upload local file to Drive folder
- Uses `GDRIVE_TIMECARDS_ROOT` from environment
- Raises `GDriveClientError` on API failures

```python
class GDriveClientError(Exception): ...

class GDriveClient:
    def __init__(self, service):
        self.service = service

    def get_or_create_folder(
        self, name: str, parent_id: str | None = None
    ) -> str:
        """
        Find folder by name under parent_id (or Drive root if None).
        Creates if not found. Returns folder ID.
        Uses cache via cache.py before querying Drive.
        """
        ...

    def ensure_period_structure(self, period: str) -> dict[str, str]:
        """
        Ensure YYYYMM/Raw_Notes, YYYYMM/Reports, YYYYMM/Clockify folders exist.
        Uses GDRIVE_TIMECARDS_ROOT as the root folder name.
        Returns dict: { 'root': id, 'Raw_Notes': id, 'Reports': id, 'Clockify': id }
        Caches all folder IDs via cache.py.
        """
        ...

    def upload_file(
        self,
        local_path: Path,
        folder_id: str,
        filename: str | None = None,
        mime_type: str = "application/octet-stream"
    ) -> str:
        """
        Upload local file to Drive folder.
        Returns Drive file ID.
        filename defaults to local_path.name if not provided.
        """
        ...

    def get_root_folder_id(self) -> str:
        """
        Get or create the GDRIVE_TIMECARDS_ROOT folder in Drive root.
        Raises GDriveClientError if GDRIVE_TIMECARDS_ROOT not set in env.
        """
        ...
```

### 2.5 `__init__.py`

Export public surface:
```python
from workmain.integrations.gdrive.auth import get_service, is_authenticated, GDriveAuthError
from workmain.integrations.gdrive.client import GDriveClient, GDriveClientError
from workmain.integrations.gdrive.cache import get_folder_id, set_folder_id
```

### 2.6 Gate 2 Verification

```bash
# Module imports correctly
python -c "from workmain.integrations.gdrive import GDriveClient, get_service; print('OK')"

# Auth resolves (uses existing token from probe)
python -c "
from workmain.integrations.gdrive.auth import is_authenticated
print('Authenticated:', is_authenticated())
"
# Must print: Authenticated: True

# Client can reach Drive
python -c "
from workmain.integrations.gdrive.auth import get_service
from workmain.integrations.gdrive.client import GDriveClient
svc = get_service()
client = GDriveClient(svc)
print('Service OK')
"
```

**Stop here. Present Gate 2 results. Do not proceed to Gate 3 without confirmation.**

---

## Gate 3 — `workmain gdocs` Command Group

### 3.1 File

**New file:** `workmain/cli/commands/gdocs.py` v1.0

### 3.2 Command Tree

```
workmain gdocs
├── auth                 # Authenticate / re-authenticate
├── status               # Auth state, cache contents, recent uploads
├── upload-notes         # Today's notes DB → markdown → staging/notes/ → Drive
├── upload-report        # Latest report from staging/reports/ → Drive
├── upload-clockify      # Latest PDF from staging/clockify/ → Drive
└── upload-all           # Runs upload-notes, upload-report, upload-clockify in sequence
```

---

### 3.3 `gdocs auth`

```
workmain gdocs auth [--reauth]
```

- If valid token exists and `--reauth` not passed: print "Already authenticated. Use --reauth to refresh."
- Otherwise: run WSL console flow, save token, print success
- After auth: run `ensure_period_structure` for current month and cache folder IDs
- Print confirmation: "Authentication complete. Drive folder structure verified."

| Flag | Short | Notes |
|------|-------|-------|
| `--reauth` | (none) | Force re-authentication even if token valid |

---

### 3.4 `gdocs status`

```
workmain gdocs status
```

Output format:
```
Google Drive Integration
─────────────────────────────────────────
Auth          ✓ Authenticated
Token path    ~/.workmain/integrations/gdrive/token.json
Root folder   Timecards (GDRIVE_TIMECARDS_ROOT)

Cached Folders
  202603  root        → <id>
  202603  Raw_Notes   → <id>
  202603  Reports     → <id>
  202603  Clockify    → <id>

Recent Uploads (last 5)
  2026-03-06  notes      Daily_Notes_20260306.md
  2026-03-06  report     daily_internal_20260306.md
  2026-03-06  clockify   Clockify_20260306.pdf
```

If not authenticated:
```
Google Drive Integration
─────────────────────────────────────────
Auth          ✗ Not authenticated
Run: workmain gdocs auth
```

---

### 3.5 `gdocs upload-notes`

```
workmain gdocs upload-notes [--date YYYYMMDD] [--dry-run]
```

**Sequence:**
1. Query DB for all notes for target date (default: today)
2. Format as markdown (see §3.8 Notes Markdown Format)
3. Write to `staging/notes/Daily_Notes_YYYYMMDD.md`
4. Ensure period folder structure exists in Drive (uses cache)
5. Upload to Drive: `YYYYMM/Raw_Notes/Daily_Notes_YYYYMMDD.md`
6. Record upload in `gdrive_uploads` table
7. Print: "Uploaded: Daily_Notes_YYYYMMDD.md → Timecards/202603/Raw_Notes/"

If already uploaded today (checked via `GDriveRepository.already_uploaded()`):
- Print warning: "Notes for YYYY-MM-DD already uploaded. Use --force to overwrite."
- Do not re-upload unless `--force` passed

| Flag | Short | Notes |
|------|-------|-------|
| `--date` | `-d` | Target date YYYYMMDD. Default: today |
| `--dry-run` | (none) | Show what would be uploaded, no Drive writes |
| `--force` | (none) | Re-upload even if already uploaded |

---

### 3.6 `gdocs upload-report`

```
workmain gdocs upload-report [--date YYYYMMDD] [--dry-run] [--force]
```

**Sequence:**
1. Find most recent `daily_internal_YYYYMMDD.md` in `staging/reports/` matching target date
2. If not found: print error "No report found for YYYY-MM-DD. Run: workmain report save daily_internal"
3. Ensure period folder structure exists
4. Upload to Drive: `YYYYMM/Reports/daily_internal_YYYYMMDD.md`
5. Record upload in `gdrive_uploads` table
6. Print: "Uploaded: daily_internal_YYYYMMDD.md → Timecards/202603/Reports/"

Same `--date`, `--dry-run`, `--force` flags as `upload-notes`.

---

### 3.7 `gdocs upload-clockify`

```
workmain gdocs upload-clockify [--date YYYYMMDD] [--dry-run] [--force]
```

**Sequence:**
1. Find most recent `Clockify_YYYYMMDD.pdf` in `staging/clockify/` matching target date
2. If not found: print error "No Clockify PDF found for YYYY-MM-DD. Run: workmain clockify report save daily"
3. Ensure period folder structure exists
4. Upload to Drive: `YYYYMM/Clockify/Clockify_YYYYMMDD.pdf`
   - MIME type: `application/pdf`
5. Record upload in `gdrive_uploads` table
6. Print: "Uploaded: Clockify_YYYYMMDD.pdf → Timecards/202603/Clockify/"

Same `--date`, `--dry-run`, `--force` flags as `upload-notes`.

---

### 3.8 Notes Markdown Format

**File name:** `Daily_Notes_YYYYMMDD.md`

**Format:**
```markdown
# Daily Notes — YYYY-MM-DD

## [tag] HH:MM
Note content here.

## [tag] HH:MM
Another note.

---
*Generated by WorkmAIn on YYYY-MM-DD HH:MM*
```

Rules:
- Notes ordered by created_at ascending
- Tag shown as full display name (e.g. `[internal-only]` not `ilo`)
- Time shown in 24-hour format (HH:MM)
- If note has multiple tags: `[internal-only] [carry-forward] HH:MM`
- Empty note body: still included with empty line (preserve record)

---

### 3.9 `gdocs upload-all`

```
workmain gdocs upload-all [--date YYYYMMDD] [--dry-run] [--force]
```

Runs `upload-notes`, `upload-report`, `upload-clockify` in sequence.
On failure of any step: prompt "Continue with remaining uploads? [Y/n]"
Prints summary on completion:

```
Upload Summary — 2026-03-06
  ✓ Notes      → Timecards/202603/Raw_Notes/Daily_Notes_20260306.md
  ✓ Report     → Timecards/202603/Reports/daily_internal_20260306.md
  ✓ Clockify   → Timecards/202603/Clockify/Clockify_20260306.pdf
```

---

### 3.10 Error Handling

All `gdocs` commands must handle these failure modes gracefully:

| Error | User-facing message |
|-------|---------------------|
| Not authenticated | "Not authenticated. Run: workmain gdocs auth" |
| `GDRIVE_TIMECARDS_ROOT` not set | "GDRIVE_TIMECARDS_ROOT is not set. Add it to your .env file." |
| Drive API error | "Drive API error: <message>. Check your connection and retry." |
| Local file missing | "File not found: <path>. Run: <suggested command>" |
| Token expired | Auto-refresh attempted. If fails: "Token expired. Run: workmain gdocs auth --reauth" |

---

### 3.11 Gate 3 Verification

```bash
# Command group registered
workmain gdocs --help

# Auth command (reuses existing probe token — no browser flow needed)
workmain gdocs auth
# Must print: "Already authenticated. Use --reauth to refresh."

# Status shows auth + cached folders
workmain gdocs status

# Dry runs (no Drive writes)
workmain gdocs upload-notes --dry-run
workmain gdocs upload-report --dry-run
workmain gdocs upload-clockify --dry-run
workmain gdocs upload-all --dry-run

# Live uploads (requires staging files to exist)
# Generate required staging files first:
workmain notes today   # confirm notes exist
workmain report save daily_internal
workmain clockify report save daily

# Then upload
workmain gdocs upload-notes
workmain gdocs upload-report
workmain gdocs upload-clockify

# Verify in Drive (manual check in browser)
# Should see: Timecards/202603/Raw_Notes/, Reports/, Clockify/

# Status shows upload history
workmain gdocs status

# Duplicate protection
workmain gdocs upload-notes
# Must print: "Notes for 2026-03-06 already uploaded. Use --force to overwrite."
```

**Stop here. Present Gate 3 results. Do not proceed to Gate 4 without confirmation.**

---

## Gate 4 — interface.py Registration + eod Step 6

### 4.1 interface.py Registration

**File:** `workmain/cli/interface.py` (increment version)

Add under Phase 7 section:
```python
from workmain.cli.commands.gdocs import gdocs
# ...
workmain_cli.add_command(gdocs)
```

### 4.2 eod Step 6 — Upload to Google Drive

**File:** `workmain/cli/commands/eod.py` (increment version)

Insert new Step 6 before the existing Complete step.
Complete becomes Step 7.

```
Step 6: UPLOAD TO GOOGLE DRIVE
  Command: workmain gdocs upload-all
  - On success: display upload summary (notes, report, clockify)
  - On Drive auth failure: prompt "Not authenticated. Skip Drive upload? [Y/n]"
    If Y: skip and note in summary
    If N: "Run 'workmain gdocs auth' then retry eod"
  - On individual file failure: prompt "Continue with remaining uploads? [Y/n]"
  - On success: "✓ All files uploaded to Google Drive"
```

**Updated `--skip` flag values:**

| Value | Skips |
|-------|-------|
| `condense` | Step 1 |
| `sync` | Step 2 |
| `review` | Step 3 |
| `report` | Steps 4a + 4b |
| `email` | Step 4b only |
| `clockify` | Step 5 |
| `gdocs` | Step 6 (Drive upload) |

**Updated `--dry-run` output:**
```
[DRY RUN] Step 1/7 — Condense pending meetings
[DRY RUN] Step 2/7 — Sync time entries (track sync push)
[DRY RUN] Step 3/7 — Review time entries (time today)
[DRY RUN] Step 4a/7 — Generate report (report save daily_internal)
[DRY RUN] Step 4b/7 — Create email draft (email save daily_internal)
[DRY RUN] Step 5/7 — Pull Clockify PDF (clockify report save daily)
[DRY RUN] Step 6/7 — Upload to Google Drive (gdocs upload-all)
[DRY RUN] Step 7/7 — Complete
```

### 4.3 Gate 4 Verification

```bash
# interface.py loads cleanly
workmain --help   # gdocs must appear in command list
workmain gdocs --help

# eod dry run shows 7-step sequence
workmain eod --dry-run

# skip gdocs works
workmain eod --skip gdocs --dry-run

# Full eod run (skip time-consuming steps for verification)
workmain eod --skip condense,sync,review
# Steps 4a, 4b, 5, 6 should execute in sequence
```

**Stop here. Present Gate 4 results. Do not proceed to Gate 5 without confirmation.**

---

## Gate 5 — Integration Testing

### 5.1 Test File

**New file:** `tests/test_gdrive.py` v1.0

**Test cases (minimum 10):**

| # | Test | Description |
|---|------|-------------|
| 1 | `test_record_upload` | GDriveRepository.record_upload() stores record correctly |
| 2 | `test_already_uploaded_true` | Returns True when matching record exists |
| 3 | `test_already_uploaded_false` | Returns False when no matching record |
| 4 | `test_get_uploads_for_date` | Returns correct records for date |
| 5 | `test_cache_set_get` | cache.py set/get round-trip |
| 6 | `test_cache_missing_key` | Returns None for missing cache key |
| 7 | `test_notes_markdown_format` | Notes render correctly in markdown format |
| 8 | `test_notes_markdown_empty` | Empty note list produces valid markdown |
| 9 | `test_notes_markdown_multi_tag` | Multiple tags rendered correctly |
| 10 | `test_upload_all_dry_run` | CLI dry-run produces correct output, no DB writes |

Tests must use mocked Drive API — no real Drive calls in test suite.
Use `unittest.mock.patch` to mock `get_service()` and Drive API responses.

### 5.2 Full CLI Verification

```bash
# Run test suite
pytest tests/test_gdrive.py -v

# Full suite still passes
pytest tests/ -v

# Complete eod flow
workmain eod --dry-run   # 7-step sequence correct

# gdocs commands all functional
workmain gdocs auth
workmain gdocs status
workmain gdocs upload-all --dry-run
workmain gdocs upload-notes
workmain gdocs upload-report
workmain gdocs upload-clockify
workmain gdocs status   # shows 3 uploads in history

# Verify in Google Drive (manual)
# Timecards/202603/ must contain Raw_Notes/, Reports/, Clockify/
# Each subfolder must contain today's file
```

**Stop here. Present Gate 5 results. Do not proceed to Gate 6 without confirmation.**

---

## Gate 6 — Version Bump + CHANGELOG + Handoff

### 6.1 `workmain/__version__.py` → v1.4.0

```python
"""
WorkmAIn Package Version
Version v1.4.0
20260306

Version History:
- v1.4.0: Phase 7 complete — Google Drive integration, gdocs command group,
          eod Step 6, ~/.workmain/integrations/ restructure
- v1.3.1: Hotfix — staging/ restructure, eod corrections, clockify report redesign
- v1.3.0: Phase 6 complete — ICS import, calendar commands, email draft pipeline
"""

__version__ = "1.4.0"
```

### 6.2 CHANGELOG.md Entry

```markdown
## v1.4.0 — 20260306

### Added
- Google Drive integration (`workmain/integrations/gdrive/`) with OAuth2,
  WSL-compatible console auth flow, folder ID caching
- `workmain gdocs` command group: `auth`, `status`, `upload-notes`,
  `upload-report`, `upload-clockify`, `upload-all`
- `gdrive_uploads` database table for upload history tracking
- `workmain eod` Step 6: automated Drive upload via `gdocs upload-all`
- `GDRIVE_TIMECARDS_ROOT` environment variable for configurable Drive path
- Daily notes markdown export to `staging/notes/Daily_Notes_YYYYMMDD.md`

### Changed
- `~/.workmain/` restructured to `~/.workmain/integrations/<name>/` pattern
- `outlook_client.py` moved to `outlook/client.py` (mirrors clockify pattern)
- `workmain eod` expanded from 6 to 7 steps; `--skip gdocs` added
```

### 6.3 Merge Sequence

```bash
# Merge feature branch to dev
git checkout dev
git merge --no-ff feature/phase-7-gdocs \
  -m "feat(gdrive): Phase 7 complete — Google Drive integration (v1.4.0)"

# Merge dev to main (phase complete)
git checkout main
git merge --no-ff dev \
  -m "release: v1.4.0 — Phase 7 Google Drive integration"
git tag v1.4.0

# Clean up
git branch -d feature/phase-7-gdocs

# Verify
git log --oneline -5
git tag | grep v1.4
```

### 6.4 Gate 6 Verification

```bash
workmain version         # must show 1.4.0
workmain gdocs --help    # command group present
workmain eod --dry-run   # 7-step sequence
pytest tests/ -v         # all tests pass
git log --oneline -3     # clean merge history
git tag                  # v1.4.0 present
```

---

## Summary of All Files

### New Files

| File | Version | Description |
|------|---------|-------------|
| `workmain/integrations/gdrive/__init__.py` | v1.0 | Module exports |
| `workmain/integrations/gdrive/auth.py` | v1.0 | OAuth2 + WSL console flow |
| `workmain/integrations/gdrive/client.py` | v1.0 | Drive API operations |
| `workmain/integrations/gdrive/cache.py` | v1.0 | Folder ID cache |
| `workmain/integrations/outlook/__init__.py` | v1.0 | Empty init (Gate 0 move) |
| `workmain/cli/commands/gdocs.py` | v1.0 | gdocs command group |
| `workmain/database/repositories/gdrive_repository.py` | v1.0 | Upload tracking |
| `workmain/database/migrations/005_add_gdrive_uploads.sql` | v1.0 | DB migration |
| `tests/test_gdrive.py` | v1.0 | Integration tests (10+ cases) |

### Modified Files

| File | Change |
|------|--------|
| `workmain/integrations/outlook/client.py` | Moved from `outlook_client.py` |
| `workmain/database/models.py` | Add GDriveUpload model |
| `workmain/database/repositories/__init__.py` | Export gdrive_repository |
| `workmain/cli/interface.py` | Register gdocs group |
| `workmain/cli/commands/eod.py` | Add Step 6, --skip gdocs, 6→7 steps |
| `workmain/__version__.py` | v1.3.1 → v1.4.0 |
| `CHANGELOG.md` | v1.4.0 entry |
| `.env` | Add GDRIVE_TIMECARDS_ROOT |

---

## Instructions for Claude Code

1. Read `GIT_WORKFLOW_STANDARDS.md` before starting
2. Branch from `dev`: `git checkout dev && git checkout -b feature/phase-7-gdocs`
3. Execute gates strictly in order: Gate 0 → 1 → 2 → 3 → 4 → 5 → 6
4. Stop after each gate, present verification output, wait for user confirmation
5. Gate 0 touches production integrations — verify imports after every move
6. The probe token at `~/.workmain/integrations/gdrive/token.json` is valid
   and should be reused — `gdocs auth` should detect it and skip the browser flow
7. All Drive API calls in tests must be mocked — no real Drive calls in test suite
8. `GDRIVE_TIMECARDS_ROOT` must never be hardcoded — always read from environment
9. If `GDRIVE_TIMECARDS_ROOT` is not set, all gdocs commands must fail with a
   clear actionable message — no silent defaults
10. The notes markdown format in §3.8 is the canonical format — do not deviate
11. `already_uploaded()` check must run before every upload — duplicate protection
    is required, not optional
12. Any ambiguity not covered by this spec must be raised with the user before
    implementation

---

END OF SPECIFICATION
WorkmAIn PHASE7_GDRIVE_SPEC v1.0 — 20260306
