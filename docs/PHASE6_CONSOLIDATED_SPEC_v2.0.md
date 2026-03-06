WorkmAIn
PHASE6_CONSOLIDATED_SPEC v2.0
20260304

---

# Phase 6 — Outlook Integration
## Consolidated Specification for Claude Code Implementation

---

## Session Context

**Application Version:** v1.2.0
**Target Version:** v1.3.0
**Branch:** main (post-standardization sprint)
**Date:** 20260304
**Spec Version:** v2.0 — adds Gate 0 (report restructure + output directory),
updated email command structure, draft path correction.

---

## Problem Statement

Due to corporate restrictions on OAuth/Azure AD access, a direct Microsoft Graph API
connection is not currently possible. Phase 6 implements Outlook calendar and email
integration via ICS file import as a fully functional offline path, while building
the complete OAuth framework as stubs so that future OAuth implementation requires
no architectural changes — only credential provisioning.

---

## Scope Overview

| Area | Works Now | Stubbed (OAuth Required) |
|------|-----------|--------------------------|
| Report command restructure | ✓ | — |
| Output directory restructure | ✓ | — |
| ICS import pipeline | ✓ | — |
| Calendar local view | ✓ | — |
| Email draft generation | ✓ | — |
| Email local save | ✓ | — |
| Recipient management | ✓ | — |
| Report send (chains to email send) | — | ✓ |
| Calendar sync from Outlook | — | ✓ |
| Email send to Outlook drafts | — | ✓ |

---

## Gate 0 — Pre-Phase 6 Housekeeping

**Complete Gate 0 fully before writing any Phase 6 code.**
Gate 0 touches existing production commands used daily.
Verify each checkpoint before advancing.

---

### Gate 0.1 — Output Directory Restructure

**Current state:**
```
~/Projects/workmain/
└── reports/          # generated report markdown files (gitignored)
```

**Target state:**
```
~/Projects/workmain/
└── output/           # gitignored at this level
    ├── reports/      # relocated from reports/
    └── email/        # new — email drafts (Phase 6)
```

**Steps:**

1. Create new directory structure:
```bash
mkdir -p output/reports
mkdir -p output/email
```

2. Move existing report files:
```bash
mv reports/*.md output/reports/ 2>/dev/null || true
```

3. Update `.gitignore` — replace existing `reports/` entry with:
```
# Generated output (reports, email drafts)
output/
```

4. Update all path references in `report.py` from `reports/` to `output/reports/`

5. Verify `workmain report list` still shows all existing reports
6. Verify `workmain report show <filename>` still works
7. Verify `workmain report costs` still shows correct totals
8. Remove old `reports/` directory if empty

**Files affected:**
- `cli/commands/report.py` — path references only, increment version
- `.gitignore` — update entry

---

### Gate 0.2 — Report Command Restructure

**Current command structure:**
```
workmain report <template> --preview    # preview prompts, no AI cost
workmain report <template> --send       # generate with AI, save to output/reports/
workmain report list
workmain report costs
workmain report show <filename>
```

**Target command structure:**
```
workmain report preview <template>      # preview prompts, no AI cost
workmain report save <template>         # generate with AI, save to output/reports/
workmain report send <template>         # stub — chains to email send (OAuth required)
workmain report list                    # no change
workmain report costs                   # no change
workmain report show <filename>         # no change
```

**Implementation notes:**

`preview`, `save`, `send` are static Click subcommands taking `<template>`
as a required argument. The `AliasedReportGroup` dynamic routing is removed
and replaced with standard Click group structure. Adding new templates remains
a configuration task — template name is passed as an argument, not hardcoded.

`report send` stub:
```python
@report.command()
@click.argument('template')
def send(template):
    """
    Generate report and send to Outlook via email pipeline.
    Requires OAuth authentication — see docs/OAUTH_SETUP.md
    Use 'workmain report save <template>' to generate and save locally,
    then 'workmain email save <template>' to create an email draft.
    """
    raise NotImplementedError(
        "report send requires workmain email send, which requires OAuth.\n"
        "See docs/OAUTH_SETUP.md\n"
        "Use: workmain report save <template>"
    )
```

**Files affected:**
- `cli/commands/report.py` — full restructure, increment version

**Verification after Gate 0.2:**
```bash
workmain report preview daily_internal
workmain report save daily_internal
workmain report list
workmain report costs
workmain report show <most-recent-filename>
workmain report send daily_internal    # should show NotImplementedError stub message
```

Confirm all existing reports still appear in `workmain report list`.
Confirm `workmain report costs` totals unchanged.
Confirm newly generated report appears in `output/reports/`.

---

### Gate 0 — Version Updates

| File | Current | Action |
|------|---------|--------|
| `cli/commands/report.py` | v1.8 | Increment — restructure + path update |
| `.gitignore` | (current) | Update reports/ → output/ |

**Do not increment `__version__.py` for Gate 0.**
Gate 0 is preparatory work — version bump happens at end of Phase 6.

---

## Part 1 — Architecture

### 1.1 Outlook Client (Single Auth Layer)

**Path:** `workmain/integrations/outlook_client.py`
**Version:** v1.0

This is the single integration point for all Microsoft Graph API interactions.
Both `workmain calendar` and `workmain email` import from this module.
All methods are stubbed with `NotImplementedError` except token file management.

**OAuth Scopes (declared now, used when OAuth becomes available):**
```python
REQUIRED_SCOPES = [
    "Calendars.Read",       # read calendar events
    "Mail.ReadWrite",       # create and read email drafts
    "Mail.Send",            # send email
]
```

**Token storage:**
- Path: `~/.workmain/outlook_tokens.json`
- Permissions: chmod 600 (set on creation)
- Structure:
```json
{
  "access_token": "",
  "refresh_token": "",
  "expires_at": "",
  "scopes": []
}
```

**Client credentials (static secrets — stored in `.env`, not token file):**
```
OUTLOOK_CLIENT_ID=
OUTLOOK_CLIENT_SECRET=
OUTLOOK_TENANT_ID=
```

These are added to `.env` (chmod 600) when OAuth becomes available.
They are the Azure AD app registration credentials, distinct from
the user tokens which rotate automatically.

**`docs/OAUTH_SETUP.md` must contain:**
1. What Azure AD app registration requires (admin access to org tenant)
2. The three `.env` variables above with descriptions
3. Required OAuth scopes: `Calendars.Read`, `Mail.ReadWrite`, `Mail.Send`
4. Token file location (`~/.workmain/outlook_tokens.json`)
5. Which commands become functional once OAuth is configured:
   - `workmain calendar today/week/month sync`
   - `workmain calendar today/week/month` (live, no --offline needed)
   - `workmain email <template> send`

**Method signatures (all stubbed with NotImplementedError):**
```python
class OutlookClient:
    def authenticate(self) -> None:
        """
        Initiate OAuth 2.0 flow against Azure AD.
        Requires app registration in organization's Azure AD tenant.
        Stores access_token and refresh_token to ~/.workmain/outlook_tokens.json (chmod 600).
        NotImplemented until Azure AD app registration is available.
        """
        raise NotImplementedError("OAuth requires Azure AD app registration. See docs/OAUTH_SETUP.md")

    def refresh_token(self) -> None:
        """
        Use stored refresh_token to obtain new access_token silently.
        Updates outlook_tokens.json with new token and expiry.
        NotImplemented until Azure AD app registration is available.
        """
        raise NotImplementedError("OAuth requires Azure AD app registration. See docs/OAUTH_SETUP.md")

    def is_authenticated(self) -> bool:
        """Check if valid tokens exist and are not expired."""
        raise NotImplementedError("OAuth requires Azure AD app registration. See docs/OAUTH_SETUP.md")

    def get_calendar_events(self, start: datetime, end: datetime) -> list[dict]:
        """
        Fetch calendar events from Microsoft Graph API.
        Endpoint: GET /me/calendarView?startDateTime=<start>&endDateTime=<end>
        Returns list of event dicts with: id, subject, start, end, isRecurring, seriesMasterId
        NotImplemented until Azure AD app registration is available.
        """
        raise NotImplementedError("OAuth requires Azure AD app registration. See docs/OAUTH_SETUP.md")

    def create_draft(self, subject: str, body: str, to: list[str], cc: list[str]) -> str:
        """
        Create email draft in Outlook via Graph API.
        Endpoint: POST /me/messages
        Returns draft message ID.
        NotImplemented until Azure AD app registration is available.
        """
        raise NotImplementedError("OAuth requires Azure AD app registration. See docs/OAUTH_SETUP.md")

    def send_email(self, message_id: str) -> None:
        """
        Send a previously created draft.
        Endpoint: POST /me/messages/{id}/send
        NotImplemented until Azure AD app registration is available.
        """
        raise NotImplementedError("OAuth requires Azure AD app registration. See docs/OAUTH_SETUP.md")
```

Create `docs/OAUTH_SETUP.md` as a placeholder documenting what Azure AD app
registration requires so a future implementer has a clear starting point.

---

### 1.2 Integrations Directory

`workmain/integrations/` already exists from Clockify setup.
Verify `workmain/integrations/__init__.py` is present.

---

## Part 2 — Database Changes

### 2.1 No Calendar Migration Required

`outlook_id` column already exists on meetings table.
All 49 existing values are NULL — no collision risk.
`outlook_recurring_id` already exists.

**Do not create a calendar migration file.**

### 2.2 Email Recipients Migration

Create `workmain/database/migrations/004_add_recipients.sql`

Adds a thin `recipients` identity table and `recipient_id` foreign key on
`report_recipients` — consistent with how `notes.meeting_id` references
`meetings.id` throughout the schema.

**Requires `report_recipients` to be empty. Confirmed empty (COUNT = 0).**

```sql
-- WorkmAIn
-- 004_add_recipients.sql v1.0
-- 20260304
-- Add recipients identity table for stable per-person IDs
-- Consistent with meetings/notes foreign key pattern

-- Safety check: verify report_recipients is empty
DO $$
BEGIN
    IF (SELECT COUNT(*) FROM report_recipients) > 0 THEN
        RAISE EXCEPTION 'Migration requires report_recipients to be empty. '
            'Remove existing rows before applying this migration.';
    END IF;
END $$;

-- Recipients identity table (one row per person)
CREATE TABLE IF NOT EXISTS recipients (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) NOT NULL UNIQUE,
    created_at  TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);

-- Add recipient_id foreign key to report_recipients
ALTER TABLE report_recipients
ADD COLUMN recipient_id INTEGER REFERENCES recipients(id) ON DELETE CASCADE;

-- Add index for join performance
CREATE INDEX IF NOT EXISTS idx_report_recipients_recipient_id
ON report_recipients (recipient_id);

-- Verification
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'recipients'
    ) THEN
        RAISE EXCEPTION 'Migration failed: recipients table not created';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'report_recipients'
        AND column_name = 'recipient_id'
    ) THEN
        RAISE EXCEPTION 'Migration failed: recipient_id column not added';
    END IF;

    RAISE NOTICE 'Migration 004 applied successfully';
END $$;
```

### 2.3 Model Updates

Add `Recipient` SQLAlchemy model to `workmain/database/models.py` (v1.4).
Add `recipient_id` foreign key and `recipient` relationship to existing
`ReportRecipient` model. Increment models version.

```python
class Recipient(Base):
    __tablename__ = 'recipients'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now)
    assignments = relationship('ReportRecipient', back_populates='recipient',
                               cascade='all, delete-orphan')

# Add to existing ReportRecipient model:
recipient_id = Column(Integer, ForeignKey('recipients.id', ondelete='CASCADE'))
recipient = relationship('Recipient', back_populates='assignments')
```

### 2.4 Repository

Create `workmain/database/repositories/email_repository.py` v1.0.

Methods required:
```python
def get_all_recipients(self) -> list[Recipient]
def get_recipient_by_id(self, id: int) -> Recipient | None
def get_recipient_by_email(self, email: str) -> Recipient | None
def add_recipient(self, email: str) -> Recipient
def remove_recipient(self, id: int) -> None  # cascades to report_recipients
def get_assignments_for_template(self, report_type: str) -> list[ReportRecipient]
def assign_recipient(self, recipient_id: int, report_type: str, role: str) -> ReportRecipient
def unassign_recipient(self, recipient_id: int, report_type: str) -> None
```

---

## Part 3 — ICS Import Pipeline

### 3.1 Parser Utility

**Path:** `workmain/utils/ics_parser.py`
**Version:** v1.0

**Pipeline order (every run, automatic):**
```
Read ICS → Validate file → Filter FREE events → Strip sensitive fields → Return ICSEvent list
```

**Fields kept:**

| ICS Field | Maps To | Notes |
|-----------|---------|-------|
| `UID` | `outlook_id` | Deduplication key |
| `SUMMARY` | `title` | As-is, no sanitization |
| `DTSTART` | `start_time` | Convert to PST/PDT naive |
| `DTEND` | `end_time` | Convert to PST/PDT naive |
| `RRULE` | `is_recurring` | True if present, False if not |
| `X-MICROSOFT-CDO-BUSYSTATUS` | (filter only) | Not stored |

**Fields stripped automatically:**
`DESCRIPTION`, `ORGANIZER`, `ATTENDEE`, `CLASS`, `TRANSP`,
`SEQUENCE`, `DTSTAMP`, all `X-*` extension fields

**Event filtering:**
- `BUSYSTATUS = FREE` → exclude silently
- `BUSYSTATUS = BUSY` → include
- `BUSYSTATUS = TENTATIVE` → include
- Missing BUSYSTATUS → include (treat as BUSY)

**Dataclass:**
```python
@dataclass
class ICSEvent:
    uid: str
    title: str
    start_time: datetime    # PST/PDT naive
    end_time: datetime      # PST/PDT naive
    is_recurring: bool
    is_cancelled: bool
```

**Validation:**
- First line must be `BEGIN:VCALENDAR`
- Required fields per event: `UID`, `SUMMARY`, `DTSTART`, `DTEND`
- Date window: current date forward, no hard 30-day ceiling
  (month sync is current date → end of current month)
- Missing required field → `ICSParseError` (event index + field name)
- `STATUS:CANCELLED` → sets `is_cancelled = True`

**Timezone conversion:**
```python
from zoneinfo import ZoneInfo
LOCAL_TZ = ZoneInfo("America/Los_Angeles")

def to_local_naive(dt) -> datetime:
    if dt.tzinfo is not None:
        dt = dt.astimezone(LOCAL_TZ)
    return dt.replace(tzinfo=None)
```

---

## Part 4 — Calendar Command Group

**Path:** `workmain/cli/commands/calendar.py`
**Version:** v1.0

Register in `workmain/cli/interface.py` alongside existing command groups.

### 4.1 Command Structure

```
workmain calendar                        # help + count of local Outlook events
workmain calendar today                  # local DB, outlook_id IS NOT NULL, today
workmain calendar week                   # local DB, this week
workmain calendar month                  # local DB, current date → end of month
workmain calendar today sync             # OAuth stub
workmain calendar week sync              # OAuth stub
workmain calendar month sync             # OAuth stub
workmain calendar import <file>          # ICS pipeline
```

### 4.2 Calendar Group Header

```
workmain calendar
```
Displays help and:
```
Local Outlook events: 42 (last import: 2026-03-04)
Calendar sync: not available (OAuth required)
```

### 4.3 Calendar Today/Week/Month (Local)

Queries meetings table where `outlook_id IS NOT NULL`.

**Today:** `start_time::date = current_date`
**Week:** `start_time >= date_trunc('week', now()) AND start_time < date_trunc('week', now()) + interval '7 days'`
**Month:** `start_time >= current_date AND start_time < date_trunc('month', now()) + interval '1 month'`

Output format:
```
Outlook Calendar — Week of 09 Mar 2026

  [61] Mon 09 Mar  09:00–09:30  Team Standup
  [62] Mon 09 Mar  14:00–15:00  DE Weekly Standup
  [52] Thu 12 Mar  15:00–15:30  Weekly IPS Review  ↻
  [48] Fri 13 Mar  10:00–10:30  CSIRT Policy Violation

4 meetings  (↻ = recurring)
```

### 4.4 Sync Commands (Stubs)

```python
@calendar.command()
@click.argument('period', type=click.Choice(['today', 'week', 'month']))
def sync(period):
    """
    Pull calendar events from Outlook via Microsoft Graph API.
    Requires OAuth authentication — see docs/OAUTH_SETUP.md
    """
    raise NotImplementedError(
        "Calendar sync requires OAuth. See docs/OAUTH_SETUP.md\n"
        "Use 'workmain calendar import <file>' to import via ICS export."
    )
```

Note: `today sync`, `week sync`, `month sync` are implemented as
`calendar <period>` with an optional `sync` flag argument, not as
separate subcommands. This keeps Click structure clean.

### 4.5 Import Command

```
workmain calendar import <file>
```

**Options:**

| Flag | Long | Description |
|------|------|-------------|
| (none) | `--dry-run` | Parse and report, no DB writes |
| `-q` | `--silent` | Summary line only |

**Full pipeline:**

1. Validate file (`BEGIN:VCALENDAR`, readable, non-empty)
2. Parse all VEVENT blocks via `ics_parser.py`
3. Filter FREE events (silent)
4. Strip sensitive fields (automatic)
5. Build preview table
6. Display batch confirmation
7. On confirm: upsert all events in single transaction
8. Display post-import summary with assigned IDs

**Batch confirmation display:**
```
Importing: ~/exports/week.ics  (13 events found, 1 filtered as FREE)

  [  ] Mon 09 Mar  09:00–09:30  Team Standup              (new)
  [  ] Mon 09 Mar  14:00–15:00  DE Weekly Standup          (new)
  [52] Thu 12 Mar  15:00→15:30  Weekly IPS Review          (time changed)
  [48] Tue 10 Mar  09:00–09:30  CSIRT Touchpoint           (unchanged)

2 new, 1 updated, 1 unchanged. Import? (Y/n):
```

**Post-import summary:**
```
Import complete: 2 new, 1 updated, 1 unchanged

  [61] Mon 09 Mar  09:00–09:30  Team Standup
  [62] Mon 09 Mar  14:00–15:00  DE Weekly Standup
  [52] Thu 12 Mar  15:00–15:30  Weekly IPS Review
```

**Cancelled event handling:**
- `STATUS:CANCELLED` + matching UID in DB → delete record
- `STATUS:CANCELLED` + no match → skip silently
- Include deletion count in summary

**Malformed event handling:**
- Stop immediately
- Report event name (or index if SUMMARY missing) and missing field
- Roll back all writes
- Print: `"Fix the ICS file or re-export from Outlook and try again."`

**Dry run:** Full parse and preview, no DB writes, no confirmation prompt.
Summary line reads: `Dry run complete (no changes written): 2 new, 1 updated, 1 unchanged`

---

## Part 5 — Email Command Group

**Path:** `workmain/cli/commands/email.py`
**Version:** v1.0

Register in `workmain/cli/interface.py`.

### 5.1 Command Structure

```
workmain email <template> preview        # terminal output of draft
workmain email <template> save           # generate and save to local file
workmain email <template> send           # OAuth stub → push to Outlook drafts
workmain email list                      # show saved local drafts
workmain email show <id>                 # view a saved draft
workmain email recipients list           # all recipients with IDs + template assignments
workmain email recipients add <email>    # add recipient, returns ID
workmain email recipients remove <id>    # remove completely (with verification)
workmain email assign <id> <template> <to|cc>   # assign recipient to template role
workmain email unassign <id> <template>          # remove from template only
```

### 5.2 Draft Generation

`workmain email <template> preview/save/send` assumes the report has already
been generated. It looks up the most recent report output for the given template,
builds the email, and acts on it.

**Subject line format:**
```
Daily Report — 04 Mar 2026
Weekly Report — Week of 02 Mar 2026
```
(Derive format from template name — daily/weekly/monthly handled automatically)

**Recipients:** pulled automatically from `report_recipients` table filtered by
`report_type = <template>`.

**Body:** formatted report content, plain text.

### 5.3 Local Draft Storage

**Path:** `output/email/`
**Permissions:** directory already covered by `output/` gitignore
**Filename format:** `<template>_<YYYYMMDD_HHMMSS>.txt`

Draft file format:
```
To: peter@example.com, rikin@example.com
CC: ryan@example.com
Subject: Daily Report — 04 Mar 2026
Date: 2026-03-04 09:15:00

---

[report body here]
```

### 5.4 Send Command (Stub)

```python
@email_group.command()
@click.argument('template')
def send(template):
    """
    Send email draft to Outlook via Microsoft Graph API.
    Requires OAuth authentication — see docs/OAUTH_SETUP.md
    Use 'workmain email <template> save' to save draft locally.
    """
    raise NotImplementedError(
        "Email send requires OAuth. See docs/OAUTH_SETUP.md\n"
        "Use 'workmain email <template> save' to save draft locally."
    )
```

### 5.5 Recipients List Display

```
workmain email recipients list

ID  Email                    Daily    Weekly   Monthly
1   peter@example.com        to       cc       --
2   rikin@example.com        to       --       --
3   ryan@example.com         --       to       to
4   ronnie@example.com       cc       cc       --

4 recipients
```

### 5.6 Recipients Add

```
workmain email recipients add peter@example.com

Added: peter@example.com  [ID: 1]
Assign to a template: workmain email assign 1 daily to
```

If email already exists: `peter@example.com already exists [ID: 1]` — no duplicate created.

### 5.7 Recipients Remove Verification

```
workmain email recipients remove 1

peter@example.com is assigned to: daily (to), weekly (cc)
Remove completely? This cannot be undone. (Y/n):
```

### 5.8 Assign / Unassign

```
workmain email assign 1 daily to
→ Assigned: peter@example.com → daily (to)

workmain email unassign 1 daily
→ Unassigned: peter@example.com from daily
```

---

## Part 6 — Flag Standard Compliance

All new commands follow `CLI_STANDARDIZATION_SPRINT_SPEC_v1.2.md`.

| Short | Long | Used By | Compliant? |
|-------|------|---------|------------|
| `-q` | `--silent` | `calendar import` | ✓ |
| (none) | `--dry-run` | `calendar import` | ✓ |

No new flags introduced that conflict with existing standard.

---

## Part 7 — Dependencies

Add to `requirements.txt`:
```
icalendar>=7.0.0
```

`zoneinfo` is stdlib (Python 3.9+) — no install needed.

---

## Part 8 — Testing

### 8.1 ICS Parser Tests

**Path:** `tests/test_ics_import.py` v1.0

1. New events — 3 new UIDs, verify 3 inserted, `outlook_id` populated
2. Unchanged — re-import same file, verify 0 changes
3. Updated event — same UID, changed DTSTART, verify update
4. FREE event filtered — verify excluded from import
5. TENTATIVE event included — verify imported
6. Cancelled — known UID, verify deletion
7. Cancelled — unknown UID, verify no error
8. Malformed — missing DTEND, verify ICSParseError with event name
9. Dry run — verify zero DB writes
10. Timezone — CST event stored as PST equivalent (1hr back)
11. Manual meetings untouched — existing meetings with `outlook_id = NULL` unaffected
12. Sensitive fields stripped — verify DESCRIPTION/ORGANIZER not stored

### 8.2 Email Tests

**Path:** `tests/test_email.py` v1.0

1. Add recipient — verify ID returned, no duplicate on re-add
2. Assign recipient — verify assignment in DB
3. Unassign — verify removed from template, recipient record intact
4. Remove recipient — verify cascade deletes assignments
5. Recipients list — verify correct to/cc display per template
6. Draft generation — verify subject, recipients pulled from assignments
7. Draft save — verify file created at correct path with correct permissions
8. Send stub — verify NotImplementedError raised with correct message

### 8.3 Test Fixtures

**Path:** `tests/fixtures/`

- `week_normal.ics` — 3 BUSY events, 1 TENTATIVE, mix of recurring/single
- `week_with_free.ics` — includes FREE event that should be filtered
- `week_with_cancelled.ics` — includes STATUS:CANCELLED
- `week_malformed.ics` — one event missing DTEND
- `week_cst.ics` — all events in CST timezone for conversion testing

---

## Part 9 — Version Updates Required

### Gate 0 (pre-Phase 6)

| File | Current | Action |
|------|---------|--------|
| `cli/commands/report.py` | v1.8 | Increment — restructure + path update |
| `.gitignore` | (current) | Update reports/ → output/ |

### Phase 6

| File | Current | Action |
|------|---------|--------|
| `cli/interface.py` | v1.6.0 | Increment — register calendar + email groups |
| `cli/commands/calendar.py` | N/A | Create v1.0 |
| `cli/commands/email.py` | N/A | Create v1.0 |
| `integrations/outlook_client.py` | N/A | Create v1.0 |
| `utils/ics_parser.py` | N/A | Create v1.0 |
| `database/models.py` | v1.4 | Increment — add Recipient model, update ReportRecipient |
| `database/repositories/email_repository.py` | N/A | Create v1.0 |
| `database/migrations/004_add_recipients.sql` | N/A | Create v1.0 |
| `tests/test_ics_import.py` | N/A | Create v1.0 |
| `tests/test_email.py` | N/A | Create v1.0 |
| `docs/OAUTH_SETUP.md` | N/A | Create v1.0 |
| `requirements.txt` | (current) | Add icalendar>=7.0.0 |
| `workmain/__version__.py` | v1.2.0 | → v1.3.0 |
| `CHANGELOG.md` | (current) | Add Phase 6 entry |

---

## Part 10 — Implementation Gates

Execute in order. Do not advance until current gate passes.

### Gate 0 — Report Restructure and Output Directory
See Gate 0 section above for full checklist.
- [ ] `output/reports/` created, existing reports relocated
- [ ] `output/email/` created
- [ ] `.gitignore` updated to `output/`
- [ ] `report.py` restructured — `preview/save/send <template>` working
- [ ] `report send` stub verified with correct message
- [ ] `workmain report list`, `costs`, `show` verified unaffected
- [ ] Old `reports/` directory removed

### Gate 1 — Database
- [ ] Migration 004 applied successfully
- [ ] `recipients` table created, `recipient_id` column added to `report_recipients`
- [ ] Verify with `information_schema` queries
- [ ] `Recipient` model added, `ReportRecipient` model updated in `models.py`
- [ ] `email_repository.py` created and methods verified
- [ ] `outlook_id` confirmed NULL for all 49 existing meetings

### Gate 2 — Outlook Client Stub
- [ ] `workmain/integrations/` directory confirmed present (from Clockify)
- [ ] `outlook_client.py` created with all method signatures
- [ ] Token file structure documented
- [ ] `docs/OAUTH_SETUP.md` placeholder created with required content (see Part 1)
- [ ] All stub methods raise `NotImplementedError` with correct message

### Gate 3 — ICS Parser
- [ ] `ics_parser.py` created
- [ ] All fixture files created
- [ ] Test cases 1–12 pass
- [ ] FREE events confirmed filtered
- [ ] Sensitive fields confirmed stripped
- [ ] CST → PST conversion verified

### Gate 4 — Calendar Command Group
- [ ] `calendar.py` registered in `interface.py`
- [ ] `workmain calendar` shows help + local event count
- [ ] `today/week/month` query correct rows (outlook_id IS NOT NULL)
- [ ] `import` command runs full pipeline
- [ ] Batch confirmation displays correctly with IDs
- [ ] Post-import summary shows assigned IDs for new records
- [ ] `sync` commands raise NotImplementedError with correct message
- [ ] `workmain calendar --help` shows all subcommands

### Gate 5 — Email Command Group
- [ ] `email.py` registered in `interface.py`
- [ ] Recipients add/remove/list working with ID display
- [ ] Assign/unassign working with ID
- [ ] Draft generation pulls correct recipients from DB
- [ ] `save` writes file to `output/email/` 
- [ ] `send` raises NotImplementedError with correct message
- [ ] All test cases in `test_email.py` pass

### Gate 6 — Integration
- [ ] `workmain calendar import tests/fixtures/week_normal.ics --dry-run`
- [ ] `workmain calendar import tests/fixtures/week_normal.ics`
- [ ] `workmain calendar today` shows imported events
- [ ] `workmain meetings list` shows ALL meetings (manual + imported)
- [ ] `workmain email recipients add test@example.com` → `workmain email assign 1 daily to` → `workmain email daily --save`
- [ ] Draft file appears in `output/email/`
- [ ] Existing 49 manual meetings untouched

### Gate 7 — Version and Docs
- [ ] All file versions incremented per Part 9
- [ ] `requirements.txt` updated
- [ ] `__version__.py` at v1.3.0
- [ ] `CHANGELOG.md` updated noting original OAuth scope, ICS path rationale,
      and report restructure
- [ ] Session handoff document created

---

## Part 11 — Deviations from Original implementation-checklist.md

The original Phase 6 scope is fully represented here with the following adaptations:

| Original Item | Adaptation | Reason |
|---------------|------------|--------|
| OAuth 2.0 flow | Stubbed in `outlook_client.py` | Corporate Azure AD access blocked |
| Calendar fetch via Graph API | Replaced by `calendar import <file>` | ICS export achieves same result without OAuth |
| Meeting reminder system | Deferred to Phase 9 | Dependent on notification system not yet built |
| `workmain calendar today/week` | Implemented against local DB | Works now; `sync` variant stubbed for OAuth |
| `workmain email draft daily` | Expanded to `workmain email <template> save/send` | Template-driven, not hardcoded to daily |

All original deliverables are addressed:
- ✓ Calendar visibility in CLI (`workmain calendar today/week/month`)
- ✓ Recurring meeting detection (`is_recurring` flag via RRULE)
- ✓ Email draft creation (`workmain email <template> save`)
- ⏳ Meeting reminders (Phase 9 — notification system dependency)
- ⏳ Send to Outlook (OAuth stub — infrastructure ready)

---

## Part 12 — Handoff Document Requirements

Produce `SESSION_HANDOFF_PHASE6_COMPLETE.md` containing:

1. Gate completion status (all 7 gates)
2. All file versions (current state)
3. Any deviations from this spec and rationale
4. Known issues or loose ends
5. Verification commands:
```bash
# Gate 0 verification
workmain report preview daily_internal
workmain report save daily_internal
workmain report list
workmain report costs
workmain report send daily_internal    # should show stub message

# Phase 6 verification
workmain calendar import tests/fixtures/week_normal.ics --dry-run
workmain calendar import tests/fixtures/week_normal.ics
workmain calendar today
workmain meetings list
workmain email recipients add test@example.com
workmain email assign 1 daily to
workmain email preview daily_internal
workmain email save daily_internal     # draft appears in output/email/
workmain email send daily_internal     # should show stub message
```

---

*Phase 6 Consolidated Spec v2.0 — Planning complete. Ready for Claude Code.*
*Gate 0 must be completed and verified before any Phase 6 code is written.*
