WorkmAIn
SESSION_HANDOFF_PHASE8_READY v1.0
20260310

# Session Handoff — Phase 8 Ready for Implementation

**Date:** 20260310
**Status:** ✅ PHASE 8 SPEC COMPLETE — Ready for Claude Code
**App Version:** v1.4.0 (current) → v1.5.0 (Phase 8 target)
**Spec:** PHASE8_SLACK_SPEC_v1_5.md

---

## WHAT WAS ACCOMPLISHED THIS SESSION

Phase 8 (Slack Integration) spec written and reviewed across 5 revision cycles.
All design decisions confirmed by user. Spec is approved and ready for Claude Code.

### Key Decisions Made

1. **Auth model** — Bot Token only (no programmatic OAuth). Manual browser setup
   guided by `workmain slack setup` interactive checklist command. `--reauth` flag
   on `workmain slack auth` for token replacement workflow.

2. **Single workspace, multiple channels** — `config.json` is temporary Phase 8
   scaffolding. Phase 11 wires `post-weekly` to `system_state.active_client` →
   `clients.slack_channel`. Fallback to `config.json` preserved post-Phase 11.

3. **`slack post` command dropped** — no standalone manual post command. The
   `reports` table cannot accommodate manual posts (no report row to attach to),
   and the command was low-value. May be revisited in a future version.

4. **Schema alignment** — `slack_posts` table dropped entirely. Migration 006 is
   `ALTER TABLE reports ADD COLUMN` only, adding `slack_channel` and
   `slack_workspace_name`. `reports.slack_message_ts` already existed in the
   initial schema. No new tables in Phase 8.

5. **`post-weekly` is standalone** — NOT wired into `workmain eod`. The Thursday
   Slack draft + Friday final email EOD integration is Phase 10 work (day-aware
   EOD pipeline). Phase 8 spec §Phase 10 Pre-requisites documents the exact wiring.

6. **`--channel` override on `post-weekly`** — added. No short form (standard
   convention). Normalises with/without `#` prefix consistently.

7. **Two flag errors self-caught during standard review:**
   - `--dry-run` had been incorrectly assigned `-n` — corrected to no short form
   - `--force` had been incorrectly assigned `-f` — corrected to no short form

8. **Report generation integrated into `post-weekly`** — Option C (stale check):
   - No staged report → auto-generate
   - Same-day staged report → use silently
   - Prior-day staged report → warn + prompt regenerate/use-existing
   - `--regenerate` flag → force regeneration unconditionally

9. **Thursday/Friday workflow documented** — Thursday = Mon–Thu draft to Slack
   with `[DRAFT — For Review]` label. Friday = Mon–Fri final to email. Separate
   commands, no shared state.

---

## PHASE 8 SPEC SUMMARY

**Spec file:** PHASE8_SLACK_SPEC_v1_5.md
**Branch:** `feature/phase-8-slack` from `dev`
**Target version:** v1.5.0

### Commands Delivered (5 total)

| Command | Purpose |
|---------|---------|
| `workmain slack setup` | Interactive setup checklist — guides Slack app creation, token config, channel setup |
| `workmain slack auth [--reauth]` | Validates token via auth.test, caches workspace name |
| `workmain slack status` | Auth state + last 5 Slack-posted reports from DB |
| `workmain slack channel set <channel>` | Sets default channel in config.json |
| `workmain slack post-weekly` | Thu draft workflow: generate → preview → edit → post |

### `post-weekly` Flags

| Flag | Short | Notes |
|------|-------|-------|
| `--date` | `-d` | Anchor date override (YYYYMMDD) |
| `--channel` | none | Per-post channel override |
| `--dry-run` | none | No short form per standard |
| `--force` | none | Override duplicate check |
| `--regenerate` | none | Skip stale prompt, force regeneration |

### Gates

| Gate | Description |
|------|-------------|
| Gate 0 | Branch setup + .env.example update + directory creation |
| Gate 1 | Migration 006 (ALTER TABLE reports) + model column verification |
| Gate 2 | slack_sdk install + integrations/slack module (auth, client, __init__) |
| Gate 3 | CLI command group (5 commands) + interface.py registration |
| Gate 4 | post-weekly full implementation |
| Gate 5 | Integration tests (18 test cases, all API mocked) |
| Gate 6 | Version bump v1.5.0 + CHANGELOG + merge feature→dev→main + tag |

### New Files

```
workmain/integrations/slack/__init__.py    v1.0
workmain/integrations/slack/auth.py        v1.0
workmain/integrations/slack/client.py      v1.0
workmain/database/migrations/006_add_slack_columns.sql
workmain/cli/commands/slack.py             v1.0
tests/test_slack.py                        v1.0
~/.workmain/integrations/slack/config.json (created on first auth)
```

### Modified Files

```
workmain/database/models.py        v1.7  (add slack_channel, slack_workspace_name mappings)
workmain/cli/interface.py          v2.1.0 (register slack group)
tests/conftest.py                  v1.3  (slack test cleanup)
workmain/__version__.py            v1.5.0
requirements.txt                   (add slack_sdk>=3.26.0)
.env.example                       (add SLACK_BOT_TOKEN, SLACK_DEFAULT_CHANNEL)
```

---

## OUTSTANDING FROM PHASE 7 (unchanged, non-blocking)

- `datetime.utcnow()` deprecation in `gdrive_repository.py` — deferred cleanup
- `test_templates.py` import error — pre-existing, unrelated
- `test_database.py` errors — pre-existing, unrelated

---

## FEATURE_BACKLOG.md UPDATE REQUIRED

The FEATURE_BACKLOG.md file needs the following entry added manually.
It is read-only in project files — paste this into the file after the
current Phase 4 section, before the Summary Statistics section.

Increment the version to v3.2 and update summary statistics (+1 item,
+~8 hours effort, Phase 10 workload +1).

---

### 11. `workmain eod` Day-Aware Thursday/Friday Steps

**Status:** Deferred to Phase 10
**Priority:** High (core daily workflow)
**Effort:** ~3 hours
**Added:** 20260310

**Description:**
`workmain eod` currently runs the same 7 steps every day regardless of the
day of the week. Thursday and Friday require additional weekly steps that
are not currently included.

**Current State:**
- `workmain eod` runs 7 fixed steps (condense, sync, review, report,
  email, clockify, gdocs)
- No Thursday Slack draft step
- No Friday weekly report/email steps

**Required Behaviour:**
EOD should be day-aware — automatically include Thursday and Friday steps
based on `date.today().weekday()`:

| Day | Additional steps |
|-----|-----------------|
| Thursday | Step 8: `workmain slack post-weekly` (Mon–Thu draft → Slack) |
| Friday | Step 8: `workmain report save weekly_client` (Mon–Fri final) |
|  | Step 9: `workmain email save weekly_client` |

**Flags:**
- `--skip weekly` — skip all day-specific steps on that run
- `--dry-run` — shows full day-appropriate step sequence including weekly steps
- Non-Thu/Fri days run standard 7 steps only; weekly steps do not appear

**Why Deferred to Phase 10:**
Phase 10 (Complete Pipeline) is explicitly designed for the Thu/Fri workflow.
Phase 8 delivers `workmain slack post-weekly` which is the Thursday EOD step.
Phase 10 will have all dependencies available.

**Phase 8 deliverables consumed by Phase 10:**
- `workmain slack post-weekly` → EOD Thursday Step 8 (subprocess call)
- `reports.slack_message_ts` → duplicate post check before running Step 8
- `workmain integrations.slack` → already importable, no additional wiring

**Acceptance Criteria:**
- [ ] `workmain eod` detects Thursday and adds Slack post step
- [ ] `workmain eod` detects Friday and adds weekly report + email steps
- [ ] `--skip weekly` flag skips all day-specific steps
- [ ] `--dry-run` shows correct step count for the current day
- [ ] Monday–Wednesday run is unchanged (7 steps)
- [ ] `eod.py` version bumped, CHANGELOG updated

**Decision:** Defer to Phase 10 (Complete Pipeline — Thu/Fri workflow)

---

## PHASE 10 PRE-REQUISITES NOTE

When Phase 10 spec is written, reference:
- `PHASE8_SLACK_SPEC_v1_5.md` §Phase 10 Pre-requisites for the full EOD
  day-aware design spec
- `workmain slack post-weekly` subprocess pattern matches existing EOD step
  pattern in `eod.py` — no new infrastructure needed

---

## ENVIRONMENT VERIFICATION COMMANDS

Before Claude Code starts Gate 0:

```bash
# Confirm current version
workmain version   # expect 1.4.0

# Confirm on main (clean)
git status
git branch         # expect main

# Confirm Phase 7 tests still passing
pytest tests/test_gdrive.py -v

# Confirm reports table exists (migration 005 applied)
psql -U workmain_user -d workmain -c "\d reports" | grep slack
# Expected: slack_message_ts column present
# slack_channel and slack_workspace_name should NOT yet exist
```

---

## INSTRUCTIONS FOR CLAUDE CODE

1. Read `GIT_WORKFLOW_STANDARDS.md` before touching any code
2. Read `DEVELOPMENT_STANDARDS_REVIEW.md` for file headers and naming patterns
3. Read `PHASE8_SLACK_SPEC_v1_5.md` in full before writing any code
4. Follow the `gdrive` integration module as the structural template
5. Execute gates strictly: Gate 0 → 1 → 2 → 3 → 4 → 5 → 6
6. Stop after each gate, present verification output, wait for confirmation
7. Gate 0 Step 0.2: present Slack app setup instructions, wait for explicit
   confirmation that SLACK_BOT_TOKEN is in .env before proceeding to Gate 1
8. All Slack API calls in tests must be mocked — no real API calls
9. Do not combine gates
10. `config.json` is temporary scaffolding — this is documented and intentional.
    Do not attempt to replace it with DB lookups in Phase 8.

---

END OF HANDOFF
WorkmAIn SESSION_HANDOFF_PHASE8_READY v1.0 — 20260310
