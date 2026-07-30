# Phase 11 — Gate 0 Assessment Report
20260512

---

## Checklist

- [x] `git branch` shows `feature/phase11-clients`
- [x] `python -m pytest tests/` — **239 passed, 0 failed**
- [x] `ls migrations/` — highest number confirmed as `009_add_is_cancelled.sql`
- [x] `notification_config` impact table complete (5 files + grep output)
- [x] Return type of `NotificationConfigRepository` methods documented
- [x] Daemon config read pattern documented
- [x] `~/.workmain/integrations/slack/config.json` — contents recorded
- [x] All five data table model names and `__tablename__` values confirmed
- [x] Sections A, B, C complete
- [ ] **STOPPED — awaiting approval**

---

## Section A — `notification_config` Consolidation

### Impact Table

| File | Line(s) | Read or Write | Field(s) accessed |
|------|---------|---------------|-------------------|
| `database/migrations/008_notification_config.sql` | n/a | Schema definition | `id`, `method` VARCHAR(20), `enabled` BOOLEAN, `updated_at` TIMESTAMPTZ |
| `database/repositories/notification_repository.py` | 32–79 | Read + Write | `get_config()` → `.method`, `.enabled`, `.updated_at`; `set_method()` writes `method`; `set_enabled()` writes `enabled` |
| `cli/commands/notifications.py` | 76, 118, 185, 191 | Read | `config.method`, `config.enabled`, `config.updated_at` |
| `daemon/daemon.py` | 176–186, 202–210 | Read | `config.enabled` (bool guard), `config.method` (delivery routing) |
| `daemon/scheduler.py` | — | None | No direct reference — delegates to `daemon.py` |
| `tests/test_notifications_commands.py` | — | Mocked | Tests the CLI commands (not the repo directly) |

### Return Type of `NotificationConfigRepository` Methods

- `get_config()` → returns the `NotificationConfig` **SQLAlchemy model object** with attributes `.method` (str), `.enabled` (bool), `.updated_at` (datetime with tz)
- `set_method()` → returns updated `NotificationConfig` model object
- `set_enabled()` → returns updated `NotificationConfig` model object
- All callers access only `.method`, `.enabled`, `.updated_at` as plain attributes

### Daemon Config Read Pattern

**Per-job invocation.** Each notification trigger (`_enriched_notify`, `_pre_meeting_reminder`) opens a new DB session and calls `NotificationConfigRepository(session).get_config()` independently. Changes via `workmain notifications set` take effect on the next job — no daemon restart required.

### Type Cast Strategy

`enabled` is stored as BOOLEAN in `notification_config`. In `system_state`, it will be `'true'`/`'false'` TEXT. The rewritten `NotificationConfigRepository.get_config()` must cast this back to bool before returning.

**Proposed approach:** Define a `NotificationConfigData` **dataclass** with `.method: str`, `.enabled: bool`, `.updated_at: datetime` attributes and return it from `get_config()`. All call sites access only these three attributes — zero call-site changes required.

### Proposed `system_state` Key Names

| Key | Replaces | Type stored |
|-----|----------|-------------|
| `notify_method` | `notification_config.method` | TEXT |
| `notify_enabled` | `notification_config.enabled` | `'true'` / `'false'` TEXT |

`updated_at` is implicit — `system_state.updated_at` column on whichever key was written most recently serves this role.

### Risks

1. `notifications.py` line 190: `config.updated_at.strftime(...)` — the returned dataclass must have a valid `updated_at` datetime attribute. Return the more recent of the two `system_state` row `updated_at` values.
2. The `NotificationConfig` SQLAlchemy class in `models.py` must be **removed** after Migration 010 drops the table — otherwise SQLAlchemy will attempt to reflect it at startup. Clean removal: delete the class, update `get_all_models()` and the module docstring.

### Go / No-Go

**GO.** Consolidation is straightforward. All callers access exactly 3 attributes. Dataclass return type preserves the interface with zero call-site changes.

---

## Section B — Slack `config.json`

**Full file contents:**

```json
{
    "workspace_name": "slower-midwest",
    "default_channel": "#int-gmf-csirt"
}
```

No migration action in Phase 11. Recorded for Phase 11.5 planning only.

---

## Section C — Data Table Confirmation

| Python Class | `__tablename__` | Notes |
|---|---|---|
| `Note` | `notes` | ✓ |
| `Meeting` | `meetings` | ✓ |
| `TimeEntry` | `time_entries` | ✓ |
| `Report` | `reports` | Written via `ReportsRepository.create()` inside `report_generator.py` → same session as `reports.py` |
| ~~ClockifyEntry~~ | **Does not exist** | See critical finding below |

---

## Critical Finding — No `clockify_entries` Table

The spec's Migration 012 references a `clockify_entries` table and an associated index `idx_clockify_entries_client_id`. **This table does not exist.**

All Clockify data is stored in `time_entries` via `clockify_id` and `synced_at` columns. The Clockify sync engine (`integrations/clockify/sync.py`) uses `TimeEntriesRepository` and the `TimeEntry` model directly — there is no separate clockify entry model or table anywhere in the codebase.

**Required spec amendment:** Migration 012 should drop the `clockify_entries` ALTER TABLE and the `idx_clockify_entries_client_id` index creation. The `client_id` FK on `time_entries` (already present in the spec) is sufficient — it covers both manually-entered and Clockify-imported time entries.

---

## Open Questions — Answered

| # | Question | Answer |
|---|---------|--------|
| 1 | Return type of `NotificationConfigRepository`? | `NotificationConfig` SQLAlchemy model object. Rewrite returns a `NotificationConfigData` dataclass with `.method`, `.enabled`, `.updated_at` — zero call-site changes. |
| 2 | Daemon reads config once at startup or per-job? | **Per-job.** Fresh session + `get_config()` on every notification trigger. Changes take effect immediately on next delivery. |
| 3 | Exact `__tablename__` for clockify entries? | **No separate table.** Clockify data is in `time_entries`. Migration 012 clockify section must be removed. |
| 4 | Creation commands beyond `note add`, `time add`, `meetings add`? | Yes — two additional paths: (1) `workmain reports save` creates a `Report` row via `ReportsRepository.create()` inside `report_generator.py`; (2) `slack.py` line 656 creates `Report` rows directly for Slack-posted weekly reports. Both need `client_id` stamped at Gate 5. |
| 5 | Does `workmain reports save` write a `reports` row? | Yes. `reports.py` calls `generator.generate_report(session)` → `report_generator.py` calls `self.reports_repo.create(...)`. Session is owned by `reports.py`; `client_id` must be threaded: `reports.py` → `generate_report()` → `ReportsRepository.create()`. |
| 6 | Subprocess architecture confirmed? | Confirmed. `eod.py` spawns `workmain reports save` via `subprocess.run()`. `reports.py` creates its own DB session and can read `system_state` independently. Gate 6 architecture is valid as written. |

---

## Additional Findings

- **`slack.py` Report creation (line 656):** Creates `Report` rows directly (not via `ReportsRepository`) for Slack-posted weekly reports. This is a 5th creation path to update at Gate 5 — needs `client_id=active_client_id` stamped at write time.
- **`ReportsRepository.create()` signature:** Does not currently accept `client_id`. Parameter must be added at Gate 5.
- **`report_generator.py` call chain:** The Report DB write is inside `generate_report()` — `client_id` must be passed from `reports.py` → `generate_report()` → `ReportsRepository.create()`. The call chain threading is a Gate 5/6 concern.

---

## Spec Amendment Required Before Gate 1

**Migration 012 — remove clockify_entries section:**

The following lines must be removed from the spec's Migration 012 before execution:

```sql
-- REMOVE THESE (no clockify_entries table exists):
ALTER TABLE clockify_entries
    ADD COLUMN IF NOT EXISTS client_id INTEGER
        REFERENCES clients(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_clockify_entries_client_id
    ON clockify_entries (client_id);

COMMENT ON COLUMN clockify_entries.client_id IS
    'NULL = internal/company work. Non-NULL = attributed client.';
```

Also remove from the spec's Modified Files table:
- `workmain/database/repositories/clockify_repository.py` — this repository does not exist. Clockify uses `time_entries_repo.py`.

---

*Awaiting approval to proceed to Gate 1.*
