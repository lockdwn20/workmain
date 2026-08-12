WorkmAIn
PHASE8_SLACK_SPEC v1.5
20260310

# Phase 8: Slack Integration — Implementation Spec

**Branch:** `feature/phase-8-slack`
**Branch from:** `dev`
**Target version:** v1.5.0
**Spec version:** v1.5
**Date:** 20260310

---

## Overview

Phase 8 adds Slack posting capability to WorkmAIn. The primary deliverable is
`workmain slack post-weekly` — a standalone command that generates (or locates)
the weekly draft report, shows a Rich preview, allows editing, and posts to the
configured Slack channel on confirmation.

### Thursday / Friday Workflow

`post-weekly` is designed around a two-stage weekly reporting cycle:

| Day | Command | Purpose |
|-----|---------|---------|
| Thursday | `workmain slack post-weekly` | Generates Mon–Thu draft, posts to Slack for stakeholder review |
| Friday | `workmain report save weekly_client` + `workmain email save weekly_client` | Generates Mon–Fri final, emails to recipients |

The Thursday Slack post is explicitly labelled `[DRAFT — For Review]` so
recipients understand it is not the final report. The Friday email is the
authoritative deliverable. These are two separate commands with no shared state
— running `post-weekly` on Friday does not affect the email workflow.

**Supporting commands** cover auth validation, guided setup, status display,
config management, and raw message posting.

**Scope constraints (per planning session):**
- Single default workspace + channel — no per-client routing (deferred to Phase 11)
- `post-weekly` is standalone — NOT wired into `workmain eod`
- Slack app setup requires manual browser steps — `workmain slack setup` guides the
  user through them interactively, checking state at each step
- Bot Token auth only — no programmatic OAuth flow

---

## Architecture

### New Files

```
workmain/integrations/slack/
├── __init__.py          — public exports
├── auth.py              — token loading, is_authenticated(), SlackAuthError,
│                          config.json helpers (load/save/get_default_channel)
└── client.py            — SlackClient, SlackClientError, format_for_slack()

workmain/cli/commands/
└── slack.py             — CLI command group

tests/
└── test_slack.py        — 10+ test cases, all Slack API mocked

~/.workmain/integrations/slack/
└── config.json          — Phase 8 temporary scaffolding (see §Auth Model) — chmod 600
```

### Modified Files

```
workmain/database/models.py     — no changes needed (reports model already has
                                   slack_message_ts; migration adds two columns)
workmain/database/migrations/   — 006_add_slack_columns.sql (ALTER TABLE only)
workmain/cli/interface.py       — register slack command group
requirements.txt                — add slack_sdk
.env / .env.example             — add SLACK_BOT_TOKEN
```

### Schema Alignment

The initial schema (`001_initial_schema.sql`) already anticipated Slack
integration in two places:

**`reports.slack_message_ts VARCHAR(255)`**
Stores the Slack message timestamp when a report is posted. Phase 8 uses this
as the primary posted/not-posted indicator. `already_posted()` is a query on
`reports` — no separate tracking table needed.

**`clients.slack_workspace` and `clients.slack_channel`**
Per-client Slack config columns already exist. Phase 8 does not use them
(no clients in DB yet), but Phase 11 will populate them via
`workmain clients add/edit`. See §Phase 11 Upgrade Path.

Migration 006 adds two columns to `reports` to complete the Phase 8 record:
- `slack_channel TEXT` — channel the report was posted to
- `slack_workspace_name TEXT` — human-readable workspace name (from auth.test cache)

No new tables are created in Phase 8.

### Auth Model

`SLACK_BOT_TOKEN` is a secret — stored in `.env` (chmod 600), never in
`config.json`.

`~/.workmain/integrations/slack/config.json` is **Phase 8 temporary scaffolding**.
It stores the default channel and cached workspace name for the single-workspace
case. In Phase 11, when clients are configured in the DB and `system_state.active_client`
is set, `post-weekly` will look up `clients.slack_channel` and
`clients.slack_workspace` instead of reading `config.json`. See §Phase 11
Upgrade Path for the exact wiring change required.

`config.json` structure:
```json
{
    "default_channel": "#general",
    "workspace_name":  "My Workspace"
}
```

---

## Gate 0 — Pre-Phase Setup

### 0.1 Branch Creation

Claude Code must complete this before writing any code:

```bash
git checkout dev
git pull
git checkout -b feature/phase-8-slack
git status   # must be clean
workmain version   # expect 1.4.0
```

### 0.2 Slack App Setup

The Slack app setup requires manual browser steps that cannot be automated.
These are surfaced through `workmain slack setup` (implemented in Gate 3) rather
than documented as a raw instruction wall here. Gate 0 only establishes the
prerequisite environment; the user runs `workmain slack setup` after Gate 3 is
complete to complete configuration.

**What setup requires (reference for spec purposes):**
1. Create a Slack App at https://api.slack.com/apps
2. Add Bot Token Scopes: `chat:write`, `auth:read`
3. Install App to Workspace → copy Bot User OAuth Token (`xoxb-...`)
4. Add `SLACK_BOT_TOKEN=xoxb-...` to `.env`
5. Set default channel: `workmain slack channel set <channel>`
6. Invite the bot in Slack: `/invite @WorkmAIn`
7. Validate: `workmain slack auth`

`workmain slack setup` checks which steps are satisfied and prints only what
remains. Full behaviour specified in Gate 3 §3.1.

### 0.3 Directory Creation

```bash
mkdir -p ~/.workmain/integrations/slack
chmod 700 ~/.workmain/integrations/slack
```

### 0.4 .env.example Update

Add the following lines to `.env.example`:
```
# Slack Integration (Phase 8)
SLACK_BOT_TOKEN=
SLACK_DEFAULT_CHANNEL=
```

### 0.5 Gate 0 Verification

```bash
# Branch correct
git branch   # must show feature/phase-8-slack

# Directory exists with correct permissions
ls -la ~/.workmain/integrations/ | grep slack

# Token present in .env (do not print value)
grep SLACK_BOT_TOKEN .env | grep -v "^#"
```

**Stop here and present Gate 0 results. Do not proceed to Gate 1 without confirmation.**

---

## Gate 1 — Database Migration

### 1.1 Migration: `006_add_slack_columns.sql`

The `reports` table already has `slack_message_ts`. This migration adds the
two additional columns needed to record where a report was posted.

```sql
-- WorkmAIn
-- Migration 006 — Add Slack posting columns to reports
-- 20260310

ALTER TABLE reports
    ADD COLUMN IF NOT EXISTS slack_channel        TEXT,
    ADD COLUMN IF NOT EXISTS slack_workspace_name TEXT;

COMMENT ON COLUMN reports.slack_message_ts      IS 'Slack message timestamp (ts). Non-null = report was posted to Slack.';
COMMENT ON COLUMN reports.slack_channel         IS 'Slack channel the report was posted to (e.g. #weekly-reports).';
COMMENT ON COLUMN reports.slack_workspace_name  IS 'Human-readable Slack workspace name cached from auth.test at time of post.';
```

**Apply migration:**
```bash
psql -U workmain_user -d workmain \
    -f workmain/database/migrations/006_add_slack_columns.sql
```

**No model changes required.** The existing `Report` SQLAlchemy model will be
updated to expose the two new columns. `slack_message_ts` is already mapped if
it was included in the original model — Claude Code must verify and add any
missing column mappings.

**`already_posted()` implementation** — used by `post-weekly` duplicate check:
```python
def already_posted(session, report_date: date) -> bool:
    """Returns True if a weekly_client report for this date has been posted to Slack."""
    from workmain.database.models import Report
    result = session.query(Report).filter(
        Report.report_type == 'weekly_client',
        Report.report_date == report_date,
        Report.slack_message_ts.isnot(None)
    ).first()
    return result is not None
```

This function lives in `workmain/integrations/slack/client.py` alongside the
other Slack helpers — not in a repository class.

### 1.2 Gate 1 Verification

```bash
# Migration applied — confirm new columns present
psql -U workmain_user -d workmain -c "\d reports" | grep slack

# Expected output (3 slack columns):
#  slack_message_ts      | character varying(255) |
#  slack_channel         | text                   |
#  slack_workspace_name  | text                   |

# Model importable with new columns
python -c "
from workmain.database.models import Report
cols = [c.key for c in Report.__table__.columns]
assert 'slack_channel' in cols, 'slack_channel missing'
assert 'slack_workspace_name' in cols, 'slack_workspace_name missing'
assert 'slack_message_ts' in cols, 'slack_message_ts missing'
print('Report model OK — all 3 Slack columns present')
"
```

**Stop here and present Gate 1 results. Do not proceed to Gate 2 without confirmation.**

---

## Gate 2 — Slack Integration Module

### 2.1 `requirements.txt` Update

Add:
```
slack_sdk>=3.26.0
```

Install:
```bash
pip install slack_sdk --break-system-packages
```

### 2.2 `workmain/integrations/slack/auth.py` v1.0

**Public surface:**
- `SlackAuthError(Exception)` — raised when `SLACK_BOT_TOKEN` is missing or empty
- `get_token() → str` — reads `SLACK_BOT_TOKEN` from env; raises `SlackAuthError` if not set
- `is_authenticated() → bool` — returns True if token is present (does NOT call API)

**Implementation notes:**
- `get_token()` uses `os.environ.get('SLACK_BOT_TOKEN', '').strip()`
- If result is empty string, raise `SlackAuthError("SLACK_BOT_TOKEN not set in .env")`
- `is_authenticated()` calls `get_token()` in a try/except — returns False on exception

### 2.3 `workmain/integrations/slack/client.py` v1.0

**Classes and functions:**

`SlackClientError(Exception)` — raised on Slack API failures

`SlackClient`:
```
__init__(token: str)
    — instantiates slack_sdk.WebClient(token=token)

test_connection() → dict
    — calls auth_test() on the WebClient
    — returns {"ok": True, "team": str, "user": str, "user_id": str}
    — raises SlackClientError on API error

post_message(channel: str, text: str) → str
    — calls chat_postMessage(channel=channel, text=text)
    — returns message_ts (the ts field from the response)
    — raises SlackClientError on API error

format_for_slack(markdown_text: str) → str
    — converts markdown to Slack mrkdwn
    — see conversion rules in §2.4
```

`get_slack_client() → SlackClient`
— singleton factory: loads token via `get_token()`, instantiates and returns `SlackClient`

### 2.4 Markdown → Slack mrkdwn Conversion Rules

`format_for_slack()` applies these transformations in order:

| Input (Markdown)        | Output (Slack mrkdwn)   |
|-------------------------|-------------------------|
| `# Heading`             | `*Heading*`             |
| `## Subheading`         | `*Subheading*`          |
| `### Sub-subheading`    | `*Sub-subheading*`      |
| `**bold**`              | `*bold*`                |
| `*italic*`              | `_italic_`              |
| `- list item`           | `• list item`           |
| `---` (hr)              | (remove)                |
| `` `code` ``            | `` `code` `` (unchanged)|
| Triple backtick blocks  | unchanged               |

Implementation: use `re.sub()` for each rule. Apply heading rules before bold
(headings contain `#` which could interfere). Apply bold before italic (both use `*`).

### 2.5 `workmain/integrations/slack/__init__.py` v1.0

Follow the `gdrive/__init__.py` pattern exactly:
- Docstring with version history
- Import all public classes and functions from auth.py and client.py
- `__all__` list
- `__version__ = '1.0'`

**Public exports:**
`get_token`, `is_authenticated`, `SlackAuthError`,
`SlackClient`, `SlackClientError`, `get_slack_client`, `format_for_slack`

### 2.6 Config File Helpers

Add these functions to `auth.py` (they manage the config file, not the token):

```
load_slack_config() → dict
    — reads ~/.workmain/integrations/slack/config.json
    — returns {} if file does not exist (not an error)

save_slack_config(config: dict) → None
    — writes ~/.workmain/integrations/slack/config.json (chmod 600)
    — creates file if it does not exist

get_default_channel() → Optional[str]
    — checks config.json first, then SLACK_DEFAULT_CHANNEL env var
    — returns None if neither is set
```

Config file structure:
```json
{
    "default_channel": "#general",
    "workspace_name": "My Workspace"
}
```

### 2.7 Gate 2 Verification

```bash
# SDK installed
python -c "import slack_sdk; print('slack_sdk OK')"

# Module importable
python -c "from workmain.integrations.slack import SlackClient, get_token, is_authenticated; print('Slack module OK')"

# Auth check (token must be in .env)
python -c "from workmain.integrations.slack import is_authenticated; print('Authenticated:', is_authenticated())"
# Expected: Authenticated: True
```

**Stop here and present Gate 2 results. Do not proceed to Gate 3 without confirmation.**

---

## Gate 3 — CLI Command Group

### 3.1 `workmain/cli/commands/slack.py` v1.0

**Command group:** `slack`

#### `slack auth`

```
workmain slack auth [--reauth]
```

Validates the bot token currently in `.env` against the Slack API using
`auth.test`. On success, caches the workspace name in `config.json` and
prints confirmation. On failure, prints a clear error with a pointer to
`workmain slack setup`.

**`--reauth`** — forces re-validation even if config.json already has a cached
workspace name. Use after replacing `SLACK_BOT_TOKEN` in `.env` to pick up the
new workspace details. Without `--reauth`, `auth` is a no-op if the workspace
name is already cached (prevents accidental double-auth noise in normal use).

**Output (success — first auth or --reauth):**
```
✓ Slack authenticated
  Workspace: My Workspace
  Bot user:  WorkmAIn
  Default channel: #general
  Config saved to ~/.workmain/integrations/slack/config.json
```

**Output (already authenticated, no --reauth):**
```
✓ Already authenticated — My Workspace
  Run with --reauth to re-validate after a token change.
```

**Output (failure — token missing):**
```
✗ SLACK_BOT_TOKEN not set in .env
  Run: workmain slack setup
```

**Output (failure — token present but invalid):**
```
✗ Token validation failed: [Slack API error message]
  Your token may be revoked or incorrect.
  Edit .env and replace SLACK_BOT_TOKEN, then run: workmain slack auth --reauth
```

#### `slack status`

```
workmain slack status
```

Displays:
- Auth state (token present: yes/no, workspace name if cached)
- Default channel from `config.json`
- Last 5 weekly reports posted to Slack, queried from `reports` where
  `slack_message_ts IS NOT NULL`, ordered by `report_date DESC`

Each row shows: `report_date | channel | workspace | message_ts (truncated)`

If no posts yet: "No reports have been posted to Slack."
If not configured: "Not configured. Run: workmain slack setup"

#### `slack channel set <channel>`

```
workmain slack channel set <channel>
```

Writes `default_channel` to `~/.workmain/integrations/slack/config.json`.
Normalizes input: prepend `#` if not already present.

```
workmain slack channel set general      → stores "#general"
workmain slack channel set "#general"   → stores "#general"
```

**Output:**
```
Default channel set to #general
Config: ~/.workmain/integrations/slack/config.json
```

#### `slack setup`

```
workmain slack setup
```

Interactive setup checklist. Checks each configuration step in sequence,
displays `[✓]`, `[✗]`, or `[?]` for each, and prints actionable instructions
only for steps that are incomplete or unverifiable.

Designed to be run repeatedly — re-running after completing a step advances the
checklist automatically. Safe to run at any point including when fully configured.

**Steps checked (in order):**

| Step | Check | How verified |
|------|-------|--------------|
| 1. Slack app created | `[?]` always | Cannot verify remotely — instructions printed on first run only |
| 2. Bot scopes configured | `[?]` always | Cannot verify remotely — instructions printed on first run only |
| 3. App installed to workspace | `[?]` always | Cannot verify remotely — instructions printed on first run only |
| 4. Token in `.env` | `[✓]`/`[✗]` | `SLACK_BOT_TOKEN` present and non-empty |
| 5. Token valid | `[✓]`/`[✗]` | `auth.test` API call (only if Step 4 passes) |
| 6. Default channel set | `[✓]`/`[✗]` | `config.json` or `SLACK_DEFAULT_CHANNEL` env var |
| 7. Bot invited to channel | `[?]` always | Cannot verify remotely — reminder printed if Step 6 passes |

Steps 1–3 are `[?]` because they require browser actions WorkmAIn cannot
verify. They are printed as instructions on the first run, then collapsed to a
one-line reminder on subsequent runs once Step 4 passes (token present implies
the app was created and installed).

**Output — nothing configured yet (first run):**
```
WorkmAIn — Slack Setup
──────────────────────────────────────────────
[?] Step 1: Create Slack app
[?] Step 2: Configure bot scopes
[?] Step 3: Install to workspace
[✗] Step 4: Add token to .env
[ ] Step 5: Validate token          (waiting on Step 4)
[ ] Step 6: Set default channel     (waiting on Step 4)
[ ] Step 7: Invite bot to channel   (waiting on Step 6)

To complete Steps 1–4:
  1. Go to https://api.slack.com/apps
  2. Create New App → From scratch → name it WorkmAIn
  3. OAuth & Permissions → Bot Token Scopes → add:
       chat:write    (post messages)
       auth:read     (token validation)
  4. Click Install to Workspace → Allow
  5. Copy Bot User OAuth Token (starts with xoxb-)
  6. Add to .env:
       SLACK_BOT_TOKEN=xoxb-your-token-here

Run `workmain slack setup` again after adding the token.
```

**Output — token present, channel not set:**
```
WorkmAIn — Slack Setup
──────────────────────────────────────────────
[✓] Steps 1–3: Slack app created and installed
[✓] Step 4: Token found
[✓] Step 5: Token valid — My Workspace (bot: WorkmAIn)
[✗] Step 6: Default channel not configured
[ ] Step 7: Invite bot to channel   (waiting on Step 6)

To complete Step 6:
  workmain slack channel set <channel>

Then invite the bot in Slack:
  /invite @WorkmAIn
  (must be done in each channel you want to post to)

Run `workmain slack setup` again to verify.
```

**Output — token present but invalid:**
```
WorkmAIn — Slack Setup
──────────────────────────────────────────────
[✓] Steps 1–3: Slack app created and installed
[✓] Step 4: Token found
[✗] Step 5: Token validation failed: invalid_auth

  Your token may be revoked, expired, or incorrectly copied.
  To replace it:
    1. Go to https://api.slack.com/apps → your app → OAuth & Permissions
    2. Reinstall app or copy the existing Bot User OAuth Token
    3. Edit .env and update SLACK_BOT_TOKEN
    4. Run: workmain slack auth --reauth

Run `workmain slack setup` again after updating the token.
```

**Output — fully configured:**
```
WorkmAIn — Slack Setup
──────────────────────────────────────────────
[✓] Steps 1–3: Slack app created and installed
[✓] Step 4: Token found
[✓] Step 5: Token valid — My Workspace (bot: WorkmAIn)
[✓] Step 6: Default channel: #general
[?] Step 7: Bot invited to #general?
  If not yet done: /invite @WorkmAIn  (in Slack, in #general)

Setup complete. Run `workmain slack status` to see integration state.
```

**Token replacement reminder** — shown at the bottom whenever fully configured:
```
To replace your token: edit .env → update SLACK_BOT_TOKEN → run: workmain slack auth --reauth
```

**Output (success):**
```
✓ Posted to #channel
  Message: [first 80 chars]...
  Timestamp: 1678900000.123456
```

#### `slack post-weekly`

```
workmain slack post-weekly [--date YYYYMMDD] [--channel CHANNEL] [--dry-run] [--force] [--regenerate]
```

Full spec in Gate 4.

### 3.2 Flag Summary

| Flag            | Short    | Commands        | Notes                                             |
|-----------------|----------|-----------------|---------------------------------------------------|
| `--date`        | `-d`     | `post-weekly`   | Standard flag — always `-d` per flag standard     |
| `--channel`     | *(none)* | `post-weekly`   | Infrequent override — no short form per standard  |
| `--dry-run`     | *(none)* | `post-weekly`   | No short form — per CLI flag standard (§1.1)      |
| `--force`       | *(none)* | `post-weekly`   | Safety/override flag — no short form              |
| `--reauth`      | *(none)* | `auth`          | Forces re-validation after token replacement      |
| `--regenerate`  | *(none)* | `post-weekly`   | Skips stale prompt — forces report regeneration   |

**Flag standard compliance:**
- `--date/-d` is the canonical date flag across all commands — ✓ no conflict
- All remaining flags have no short form, consistent with `CLI_STANDARDIZATION_SPRINT_SPEC_v1_2.md`
  §1.1 convention for safety/override/infrequent flags.
- `--channel` short form candidates: `-c` taken (`--content`), `-C` taken (`--category`).
  No short form is correct.

### 3.3 Session Pattern

All commands that touch the DB use the standard session pattern:
```python
db = get_db()
session = db.get_session()
repo = SlackRepository(session)
try:
    # operations
finally:
    session.close()
```

### 3.4 `interface.py` Registration (bump to v2.1.0)

```python
from workmain.cli.commands.slack import slack
```

Register under a `# Phase 8 — Slack Integration` comment, consistent with
how `gdocs` was registered in Phase 7.

### 3.5 Gate 3 Verification

```bash
# Command group registered — 5 commands: setup, auth, status, channel, post-weekly
workmain --help   # must list 'slack'
workmain slack --help

# Help text correct for each command
workmain slack setup --help
workmain slack auth --help
workmain slack status --help
workmain slack channel set --help
workmain slack post-weekly --help

# Setup checklist (token not yet in .env — shows Step 4 as [✗])
workmain slack setup

# Live auth test (token must be in .env)
workmain slack auth
workmain slack auth --reauth   # must re-validate and refresh config.json
workmain slack status          # shows no Slack posts yet (reports table empty)

# Setup fully configured output
workmain slack setup   # must show [✓] for Steps 4, 5, 6
```

**Stop here and present Gate 3 results. Do not proceed to Gate 4 without confirmation.**

---

## Gate 4 — `post-weekly` Command

### 4.0 Workflow Context

`post-weekly` is the Thursday draft command. It covers Mon–Thu of the current
ISO week. The Friday final report (Mon–Fri) is a separate workflow handled by
`workmain report save weekly_client` + `workmain email save weekly_client` and
is not touched by this command.

### 4.1 Date Range Calculation

The Mon–Thu range is calculated automatically from today's date. No user input
required for the common case.

```python
from datetime import date, timedelta

def get_draft_date_range(anchor: date) -> tuple[date, date]:
    """
    Returns (monday, anchor) for the ISO week containing anchor.
    anchor is typically today (Thursday), but accepts any date.
    """
    monday = anchor - timedelta(days=anchor.weekday())  # weekday() Mon=0
    return monday, anchor
```

**With `--date YYYYMMDD`:** use that date as the anchor instead of today.
The range is always Mon of that date's ISO week → that date.

**Example (run on Thursday 2026-03-12):**
- anchor = 2026-03-12
- monday = 2026-03-09
- range passed to report generation: `--start 2026-03-09 --end 2026-03-12`
- staged filename: `staging/reports/weekly_client_2026-03-12.md`

### 4.2 Step 0 — Report Generation / Stale Check

This is the first thing `post-weekly` does before any duplicate check or preview.

**Decision logic (in order):**

**Case 1 — `--regenerate` flag set:**
Skip all checks. Generate unconditionally:
```
Generating weekly draft (Mon 09 Mar – Thu 12 Mar)...
  workmain report save weekly_client --start 2026-03-09 --end 2026-03-12
✓ Report generated: staging/reports/weekly_client_2026-03-12.md
```

**Case 2 — No staged report found:**
```
No staged report found for week ending 2026-03-12.
Generating weekly draft (Mon 09 Mar – Thu 12 Mar)...
  workmain report save weekly_client --start 2026-03-09 --end 2026-03-12
✓ Report generated: staging/reports/weekly_client_2026-03-12.md
```

**Case 3 — Staged report found, file date matches today (same-day):**
Use the existing file silently. No prompt, no message about the file age.
Proceed directly to §4.3 (duplicate check).

**Case 4 — Staged report found, file date is prior day or older (stale):**
```
⚠ Staged report is from a prior day (staged: 2026-03-11, today: 2026-03-12).
  It may not reflect today's notes and time entries.
  Regenerate? [y]es / [n]o (use existing):
```
- `y` → generate fresh report, overwrite staged file, proceed
- `n` → use existing file as-is, proceed

**`--dry-run` interaction:** In dry-run mode, generation is skipped regardless.
If no staged report exists, dry-run prints:
```
[DRY RUN] No staged report found — would generate weekly_client --start ... --end ...
[DRY RUN] Cannot preview content without a staged report.
```
and exits cleanly. If a staged report exists, dry-run proceeds to show the
preview with `[DRY RUN]` output but no post or DB record.

**Generation implementation:**
`post-weekly` invokes the report generation via subprocess, identical to how
`eod.py` calls other steps:
```python
import subprocess
result = subprocess.run(
    ["workmain", "report", "save", "weekly_client",
     "--start", start_str, "--end", end_str],
    capture_output=True, text=True
)
```
On non-zero exit code: print stderr and prompt `Retry or skip? [r/s]`.
`s` exits cleanly (no post). `r` retries generation once; if it fails again,
exit with error.

### 4.3 Duplicate Check

After generation/discovery, check `already_posted(report_date, 'weekly_draft')`
where `report_date` = the anchor date (end of range).

If already posted AND `--force` not set:
```
⚠ Weekly draft for 2026-03-12 was already posted to #channel.
  Use --force to post again.
```
Exit cleanly (not an error).

If already posted AND `--force` set: proceed, but add a `[REPOST]` note to the
preview header (see §4.4).

### 4.4 Preview Display

Use Rich to display report content before prompting.

**Standard preview header:**
```
┌──────────────────────────────────────────────────────────────────┐
│  WEEKLY DRAFT PREVIEW — FOR REVIEW                               │
│  Period:  Mon 09 Mar – Thu 12 Mar 2026                           │
│  File:    staging/reports/weekly_client_2026-03-12.md            │
│  Target:  #channel-name (My Workspace)                           │
└──────────────────────────────────────────────────────────────────┘
```

**If `--force` repost, replace first header line with:**
```
│  WEEKLY DRAFT PREVIEW — REPOST (already posted 2026-03-12)       │
```

Content display: if report exceeds 50 lines, show first 40 lines then:
```
... [N more lines — full content will be posted] ...
```

### 4.5 DRAFT Label

Before calling `format_for_slack()`, prepend the DRAFT header to the content:

```python
draft_header = f"*[DRAFT — For Review]* Week of {monday_str}–{anchor_str}\n\n"
slack_content = draft_header + format_for_slack(report_content)
```

Where:
- `monday_str` = `"Mon 09 Mar 2026"` format
- `anchor_str` = `"Thu 12 Mar 2026"` format

This label appears in Slack exactly as posted — recipients see it as the first
line of the message. It is NOT stored in `content_preview` (the preview stores
the raw report markdown without the prepended label, so the DB remains clean).

### 4.6 Approval Prompt

After preview:
```
Post to #channel? [y]es / [n]o / [e]dit:
```

**`y` — Post:**
1. Prepend DRAFT label and call `format_for_slack()` (§4.5)
2. Call `client.post_message(channel, slack_content)`
3. Update the `reports` row via upsert:
   - If a `reports` row exists for `report_type='weekly_client'` and
     `report_date=anchor_date`: update `slack_message_ts`, `slack_channel`,
     `slack_workspace_name`
   - If no row exists (report was generated but not yet in DB, or was generated
     externally): insert a new `reports` row with those fields populated plus
     `content` set to the raw report markdown
   - Use the standard session pattern with `try/finally`
4. Print confirmation:
   ```
   ✓ Posted to #channel
     Workspace:  My Workspace
     Period:     Mon 09 Mar – Thu 12 Mar 2026
     Timestamp:  1678900000.123456
     Report record updated (reports table)
   ```

**`n` — Cancel:**
```
Cancelled. No message posted.
```
Exit cleanly.

**`e` — Edit:**
1. Check `$EDITOR` env var. If not set:
   ```
   $EDITOR not set. Set it with: export EDITOR=nano
   Cannot open editor. Post as-is? [y/n]:
   ```
2. If `$EDITOR` set: write raw report content (without DRAFT label) to a temp
   file, open `$EDITOR`, wait for exit, read updated content, delete temp file.
3. Show updated preview with DRAFT label prepended.
4. Final prompt: `Post edited content to #channel? [y]es / [n]o:`
   (one edit pass only — no loop)

### 4.7 `--dry-run` Behavior

Show the full preview (including DRAFT label as it would appear) but skip the
approval prompt entirely. Print:
```
[DRY RUN] Would post to #channel (My Workspace)
[DRY RUN] Period:         Mon 09 Mar – Thu 12 Mar 2026
[DRY RUN] Content length: N characters (including DRAFT label)
[DRY RUN] No message sent. No database record created.
```

### 4.8 Channel Resolution

`post-weekly` resolves the target channel in this priority order:
1. `--channel` option (explicit per-post override)
2. `config.json` `default_channel`
3. `SLACK_DEFAULT_CHANNEL` env var
4. Error: `"No default channel configured. Run: workmain slack channel set <channel>"`

The `--channel` option accepts with or without `#` prefix and normalizes to
include `#` (consistent with `channel set` and `post` normalization).

### 4.9 Slack Data Storage on `reports`

After a successful post, three fields are written to the `reports` row:

| Column | Value stored |
|--------|-------------|
| `slack_message_ts` | Slack message timestamp string e.g. `"1678900000.123456"` |
| `slack_channel` | Normalised channel name e.g. `"#weekly-reports"` |
| `slack_workspace_name` | Workspace display name from `config.json` cache |

`slack_message_ts` being non-null is the canonical "was this posted?" indicator.
`already_posted()` checks this field only — channel and workspace name are
metadata for display in `slack status`.

### 4.10 Gate 4 Verification

```bash
# No staged report — dry-run shows would-generate message
workmain slack post-weekly --dry-run

# Force regenerate
workmain slack post-weekly --regenerate --dry-run

# With a staged same-day report — dry-run shows preview with DRAFT label
workmain slack post-weekly --dry-run

# Duplicate check — run live post-weekly, then run again without --force
# Second run must warn and exit cleanly
# Run with --force — must proceed with REPOST header
workmain slack post-weekly --force --dry-run

# Status shows recent post with period info
workmain slack status
```

**Stop here and present Gate 4 results. Do not proceed to Gate 5 without confirmation.**

---

## Gate 5 — Integration Tests

### 5.1 `tests/test_slack.py` v1.0

Minimum 10 test cases. All Slack API calls mocked via `unittest.mock.patch`.
No real API calls in tests.

**Test classes and cases:**

`TestSlackReportsIntegration` (uses real DB — `reports` table):
- `test_01_already_posted_false` — no report row for date → returns False
- `test_02_already_posted_true` — insert report row with `slack_message_ts` set → True
- `test_03_already_posted_ignores_null_ts` — report row exists but `slack_message_ts`
  is NULL → returns False (report generated but not yet posted)
- `test_04_upsert_updates_existing_row` — existing report row gets slack fields
  populated after post

`TestSlackAuth`:
- `test_05_get_token_success` — env var set → returns token
- `test_06_get_token_missing` — env var not set → raises SlackAuthError
- `test_07_is_authenticated_true` — token present → True
- `test_08_is_authenticated_false` — token absent → False

`TestFormatForSlack`:
- `test_09_heading_conversion` — `# Title` → `*Title*`
- `test_10_bold_conversion` — `**word**` → `*word*`
- `test_11_italic_conversion` — `*word*` → `_word_` (no conflict with bold rule)

`TestDraftDateRange`:
- `test_12_thursday_range` — anchor=Thursday → returns (Monday, Thursday)
- `test_13_monday_anchor` — anchor=Monday → returns (Monday, Monday)
- `test_14_custom_date` — arbitrary mid-week date returns correct Monday

`TestSlackClient` (mocked API):
- `test_15_post_message_success` — mock `chat_postMessage`, verify message_ts returned
- `test_16_post_message_failure` — mock raises SlackApiError → SlackClientError raised

`TestDraftLabel`:
- `test_17_draft_label_prepended` — DRAFT header is first line of formatted slack content
- `test_18_draft_label_not_in_reports_ts` — `slack_message_ts` stored on reports row
  does not contain the DRAFT label text

### 5.2 `tests/conftest.py` Update (bump to v1.3)

No new model import needed — `Report` is already imported. Add cleanup of any
test report rows that had slack fields set during tests:

```python
# Clean up any slack-tagged test report rows
session.query(Report).filter(
    Report.slack_message_ts.like("test-ts-%")
).update(
    {"slack_message_ts": None, "slack_channel": None, "slack_workspace_name": None},
    synchronize_session=False
)
```

Use `slack_message_ts` values prefixed with `test-ts-` in all test fixtures.

### 5.3 Gate 5 Verification

```bash
pytest tests/test_slack.py -v
# All tests must pass

# Full suite — no new failures introduced
pytest tests/ -v --tb=short 2>&1 | tail -30
```

**Stop here and present Gate 5 results. Do not proceed to Gate 6 without confirmation.**

---

## Gate 6 — Version Bump + Merge

### 6.1 `workmain/__version__.py` — bump to v1.5.0

```python
"""
WorkmAIn Package Version
Version v1.5.0
20260309

Version History:
- v1.5.0: Phase 8 complete — Slack integration, post-weekly with review flow
- v1.4.0: Phase 7 complete — Google Drive archival, gdocs command group, eod Step 6
"""

__version__ = "1.5.0"
```

### 6.2 `CHANGELOG.md` Entry

```markdown
## v1.5.0 — 20260309

### Added
- `workmain slack` command group (5 commands)
- `workmain slack auth` — validates Bot Token against Slack API, caches workspace name
- `workmain slack status` — shows auth state and recent post history
- `workmain slack channel set` — sets default posting channel
- `workmain slack post` — raw message post to any channel
- `workmain slack post-weekly` — weekly report preview → approve → post pipeline
- `SlackPost` model and `slack_posts` table (migration 006)
- `SlackRepository` with `record_post`, `already_posted`, `get_recent_posts`
- `workmain/integrations/slack` module (auth, client, config helpers)
- Markdown → Slack mrkdwn format conversion
- Duplicate post detection with `--force` override
```

### 6.3 Merge Sequence

```bash
# Merge feature → dev
git checkout dev
git merge --no-ff feature/phase-8-slack -m "feat(slack): Phase 8 — Slack integration complete (v1.5.0)"
git branch -d feature/phase-8-slack

# Merge dev → main
git checkout main
git merge --no-ff dev -m "release: v1.5.0 — Phase 8 Slack integration"
git tag v1.5.0
git push origin main dev --tags
```

### 6.4 Gate 6 Verification

```bash
workmain version               # must show 1.5.0
workmain slack --help          # all commands present
workmain slack auth            # validates token
workmain slack status          # shows config + post history
git log --oneline -5           # clean merge history
git tag | grep v1.5.0          # tag present
```

---

## File Version Summary

| File | Version | Change |
|------|---------|--------|
| `workmain/integrations/slack/__init__.py` | v1.0 | New |
| `workmain/integrations/slack/auth.py` | v1.0 | New — includes config.json helpers |
| `workmain/integrations/slack/client.py` | v1.0 | New — includes `already_posted()` |
| `workmain/database/migrations/006_add_slack_columns.sql` | — | New — ALTER TABLE only |
| `workmain/cli/commands/slack.py` | v1.0 | New — 5 commands |
| `tests/test_slack.py` | v1.0 | New |
| `workmain/database/models.py` | v1.7 | Add `slack_channel`, `slack_workspace_name` column mappings; verify `slack_message_ts` present |
| `workmain/cli/interface.py` | v2.1.0 | Register slack command group |
| `tests/conftest.py` | v1.3 | Add slack test cleanup |
| `workmain/__version__.py` | v1.5.0 | Version bump |
| `requirements.txt` | bump | Add slack_sdk |
| `.env.example` | — | Add SLACK_BOT_TOKEN, SLACK_DEFAULT_CHANNEL |

---

## Known Scope Exclusions (Deferred)

| Item | Deferred To |
|------|-------------|
| Per-client workspace/channel routing | Phase 11 — see §Phase 11 Upgrade Path |
| `workmain slack post` manual command | Deferred indefinitely — dropped from Phase 8 |
| `workmain eod` Thursday/Friday day-aware steps | Phase 10 — see §Phase 10 Pre-requisites |
| Thread replies | Phase 10 or 11 |
| DMs | Phase 10 or 11 |
| Multiple workspace support | Phase 11 |

---

## Phase 10 Pre-requisites

Phase 10 (Complete Pipeline) will make `workmain eod` day-aware — automatically
including Thursday and Friday weekly steps based on the current date. Phase 8
delivers everything Phase 10 needs for the Thursday Slack path.

### Day-aware EOD design (to be fully specced in Phase 10)

| Day | Additional steps beyond the standard 7 |
|-----|-----------------------------------------|
| Thursday | Step 8: `workmain slack post-weekly` — generate Mon–Thu draft, post to Slack |
| Friday | Step 8: `workmain report save weekly_client` (Mon–Fri final) |
| | Step 9: `workmain email save weekly_client` |

Behaviour:
- Thursday and Friday steps are included automatically based on `date.today().weekday()`
- `--skip weekly` skips all day-specific steps on that run
- `--dry-run` shows the full day-appropriate step sequence including weekly steps
- On non-Thursday/Friday days, EOD runs the standard 7 steps only — no
  weekly steps appear even in dry-run output

### Phase 8 deliverables consumed by Phase 10

| Phase 8 deliverable | Phase 10 usage |
|--------------------|----------------|
| `workmain slack post-weekly` | EOD Thursday Step 8 — called via subprocess, same as other EOD steps |
| `reports.slack_message_ts` | EOD can check if Thursday draft was already posted before re-running |
| `workmain integrations.slack` module | Already importable — no additional wiring needed |

---

## Phase 11 Upgrade Path

This section documents the exact changes required in Phase 11 to replace Phase 8's
temporary `config.json` scaffolding with data-driven client configuration.

### Context

Phase 8 reads the default Slack channel and workspace name from
`~/.workmain/integrations/slack/config.json`. This is intentional temporary
scaffolding — the schema already supports per-client Slack configuration via
`clients.slack_workspace` and `clients.slack_channel`, but no clients are
configured in the DB during Phase 8.

### Phase 11 Commands That Enable This

```bash
workmain clients add <name> --slack-workspace X --slack-channel Y
workmain clients list
workmain clients set-active <name>
workmain clients show <name>
workmain clients edit <name>
workmain clients remove <name>
```

`clients set-active <name>` writes to `system_state.active_client` (already
exists in schema from `001_initial_schema.sql`).

### Required Change in `post-weekly` (Phase 11)

Replace the `config.json` channel lookup in `slack.py` with a DB lookup:

**Phase 8 (current):**
```python
# workmain/integrations/slack/auth.py
channel = get_default_channel()  # reads config.json → SLACK_DEFAULT_CHANNEL env var
workspace = load_slack_config().get("workspace_name")
```

**Phase 11 replacement:**
```python
# Resolve active client from system_state
active_client_name = session.query(SystemState).filter_by(
    key="active_client"
).first()

if active_client_name and active_client_name.value:
    client = session.query(Client).filter_by(
        name=active_client_name.value
    ).first()
    channel = client.slack_channel
    workspace = client.slack_workspace
else:
    # Fall back to config.json for single-workspace / no active client
    channel = get_default_channel()
    workspace = load_slack_config().get("workspace_name")
```

This fallback means `config.json` continues to work after Phase 11 for any
workspace where no active client is set — no breaking change.

### No Migration Required in Phase 11

`clients.slack_workspace` and `clients.slack_channel` already exist in
`001_initial_schema.sql`. Phase 11 only needs to populate them via the
`clients add/edit` CLI — no new migration needed for Slack support.

### `reports.client_id` (Phase 11 consideration)

The `reports` table currently has no `client_id` FK. For multi-client reporting
in Phase 11, adding `client_id` to `reports` allows each report row to be
associated with its client without relying on `system_state.active_client`.
This is a Phase 11 migration decision — not required for Phase 8.

---

## Instructions for Claude Code

1. Read `GIT_WORKFLOW_STANDARDS.md` before touching any code
2. Execute gates strictly in order: Gate 0 → 1 → 2 → 3 → 4 → 5 → 6
3. Stop after each gate, present verification output, wait for confirmation
4. Gate 0 includes manual user steps — present the Slack app setup instructions
   and explicitly wait for confirmation that `SLACK_BOT_TOKEN` is in `.env`
   before proceeding to Gate 1
5. All Slack API calls in tests must be mocked — no real API calls in the test suite
6. Follow `DEVELOPMENT_STANDARDS_REVIEW.md` for all file headers, version history,
   singleton naming, and import organization
7. Follow the `gdrive` module as the structural template for the `slack` integration module
8. Do not combine gates

---

END OF PHASE 8 SPEC
WorkmAIn PHASE8_SLACK_SPEC v1.0 — 20260309
WorkmAIn PHASE8_SLACK_SPEC v1.1 — 20260309
WorkmAIn PHASE8_SLACK_SPEC v1.2 — 20260309
WorkmAIn PHASE8_SLACK_SPEC v1.3 — 20260309
WorkmAIn PHASE8_SLACK_SPEC v1.4 — 20260310
WorkmAIn PHASE8_SLACK_SPEC v1.5 — 20260310