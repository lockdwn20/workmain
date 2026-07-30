WorkmAIn
SESSION_HANDOFF_PHASE13_DB_SCHEMA_SPRINT_COMPLETE_20260610
Phase 13 DB Schema Refactorization Sprint

---

## Sprint Summary

This sprint eliminated the denormalization that caused the weekly report tag-leak
bugs (hotfixes v1.19.1 and v1.19.2). The root cause was that `time_entries`
carried its own `description` and `tags` columns — duplicating the note it was
created from. The AI prompt builder then pulled time entry descriptions directly
into client-facing sections regardless of tags. The fix is structural: every
time entry now requires a `note_id` FK to its source note. Content and tags come
from the note. The DB enforces this at the schema level (NOT NULL, ON DELETE
RESTRICT).

Secondary deliverables: `projects.client_id` FK materialized (migration 019),
`report_recipients.email` dead column dropped (migration 020), client/project
consistency guard in both repos, `preview_report()` client filter parity,
clockify sync signature fix, and 13 new tests.

**Version:** v1.20.0 (tagged on main; post-merge header fix on dev: 8083231)
**Branch:** `feature/phase13-db-schema-refactor` → merged to `dev` → PR #19 (dev → main)
**Suite:** 514 passed, 0 failed

---

## Gate Log

| Gate | Deliverable | Commit | Notes |
|------|-------------|--------|-------|
| 0 | Environment verify; feature branch cut from dev | *(branch creation)* | confirmed prod DB has 0 NULL note_id rows after migration |
| 1 | Migrations 019 + 020; H-4 clockify sig fix; H-5 CLAUDE.md | `190f22c` | projects FK, report_recipients.email drop, async guard |
| 2 | H-3 client/project consistency guard (notes + time_entries repos) | `ac89d50` | ValueError on mismatch; no-op when project_id=None |
| 3 | Diagnostic report — orphan + ambiguity audit | `e7c1255` | 8 orphaned rows; 242 NULL rows from stub notes; AD #15 design decision preserved |
| 4 | Migration 021 — note_id FK; backfill; drop description + tags | `3334ab9` | two-phase: Gate 3 orphan fix + Gate 4 resume script for 242 stub rows |
| 5 | Application layer — all creation paths updated to note-first | `26c6538`, `11744bb` | Gate 5 proper + missed-sites fix commit |
| 6 | New tests: test_time_entries_refactor (8) + test_prompt_builder_data_sources (5) | `d96185a` | 501+13=514 passing |
| 7 | v1.20.0 bump; CHANGELOG; backlog v5.17 (Item 23 → High); merge + PR + tag | `a5f66ba`, merge, tag | header fix for meetings.py/reports.py post-merge: `8083231` |

---

## File Versions at v1.20.0

| File | Version |
|------|---------|
| `workmain/__version__.py` | v1.20.0 |
| `workmain/database/models.py` | v2.8 |
| `workmain/database/repositories/notes_repo.py` | v2.0 |
| `workmain/database/repositories/time_entries_repo.py` | v1.9 |
| `workmain/database/repositories/email_repository.py` | v1.2 |
| `workmain/ai/prompt_builder.py` | v2.0 |
| `workmain/ai/report_generator.py` | v1.13 |
| `workmain/cli/commands/time.py` | v1.6 |
| `workmain/cli/commands/notes.py` | v4.1 |
| `workmain/cli/commands/meetings.py` | v4.5 |
| `workmain/cli/commands/eod.py` | v2.12 |
| `workmain/cli/commands/reports.py` | v2.11 |
| `workmain/integrations/clockify/sync.py` | v1.3 |
| `workmain/templates_engine/field_manager.py` | v1.1 |
| `workmain/database/migrations/019_projects_client_id_fk.sql` | new |
| `workmain/database/migrations/020_drop_report_recipients_email.sql` | new |
| `workmain/database/migrations/021_time_entries_note_id.sql` | new |
| `tests/test_time_entries_refactor.py` | v1.0 (8 tests) |
| `tests/test_prompt_builder_data_sources.py` | v1.0 (5 tests) |
| `tests/test_time_tracking.py` | v2.1 |
| `tests/test_name_or_id_resolution.py` | v1.1 |
| `tests/test_notification_engine.py` | v1.1 |
| `tests/test_recurring_meetings.py` | v1.3 |
| `tests/test_email.py` | v1.1 |
| `tests/test_email_recipients_client.py` | v1.1 |
| `CHANGELOG.md` | [1.20.0] entry added |
| `docs/FEATURE_BACKLOG.md` | v5.17 |

---

## Key Design Decisions

### AD #15 — Stub notes for 242 NULL rows (preserved in spec)
Gate 4 created 242 stub notes (`source='task'`, `tags=['internal-only']`,
`created_at = midnight of entry_date`) for the NULL-note time entries that
existed before the sprint. These stubs are correct scaffolding but need a
re-tag audit. Item 39 in FEATURE_BACKLOG.md tracks this with a query for
identification: `source = 'task'` + `tags = ['internal-only']` +
`created_at::time = '00:00:00'`.

### note-first pattern (all creation paths)
Every `TimeEntriesRepository.create()` call site now:
1. Calls `NotesRepository.create(content=..., tags=..., source=..., ...)`
2. Passes `note_id=note.id` to `time_repo.create()`
Description edits route to `notes_repo.update(note_id=entry.note_id, content=...)`.

### Client filter via note_id join (permanent fix for Issues A+B)
Hotfixes v1.19.1/v1.19.2 patched the symptom (AI instruction + data_sources
gating). This sprint fixes the root cause: `get_for_date_client(filter_client=True)`
now excludes time entries whose linked notes have `client_id=NULL` at the DB level.
Internal-only entries never reach the prompt builder for client reports.

---

## Migration Scripts (for reference)

All three migrations were applied to production during the sprint. The scripts
remain in `scripts/` for documentation and rollback reference.

| Script | Purpose |
|--------|---------|
| `scripts/migrate_019_projects_client_fk.py` | Add FK constraint to projects.client_id |
| `scripts/migrate_020_drop_report_recipients_email.py` | Drop report_recipients.email |
| `scripts/migrate_021_time_entries_note_id.py` | Phase 1: backfill 8 orphaned rows |
| `scripts/migrate_021_gate4_resume.py` | Phase 2: create 242 stub notes + backfill + NOT NULL + drop columns |

---

## Known Issues / Follow-up

| Item | Backlog | Notes |
|------|---------|-------|
| 242 stub note re-tag audit | Item 39 (Open, High) | Identify via `source='task'`, `tags=['internal-only']`, `created_at::time='00:00:00'` |
| Meeting visibility / tag gap | Item 23 (Open, **elevated to High**) | Same structural gap: meetings have no tag equivalent; internal meeting titles can surface in client report prompts. Phase 15 target, scheduling review pending. |
| Task deduplication via Ollama | Item 32 | Phase 13 Sprint 2 |
| correction_note field population | Item 33 | Phase 13 Sprint 2 |
| Weekly report from confirmed dailies | Item 34 | Phase 13 Sprint 2 |

---

## Next Sprint

**Phase 13 Sprint 2 — Slack Inbound Polling, Action Executor, Confirmation UX**

Gate 0 prerequisite: Item 38 — Ollama warm-up ping on bot startup (cold start
55–72s must not block the first DM response).

Spec location: `docs/dev/specs/` (check for most recent Phase 13 Sprint 2 spec).
