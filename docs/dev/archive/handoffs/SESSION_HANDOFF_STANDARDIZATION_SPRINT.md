WorkmAIn
Session Handoff — CLI Standardization Sprint
v1.0
20260303

# Session Handoff: CLI Standardization Sprint

**Application Version:** v1.2.0 (was v1.1.0)
**Sprint completed:** 20260303
**Branch:** feature/standardization (merged to dev, then main)
**Spec:** CLI_STANDARDIZATION_SPRINT_SPEC_v1.2.md (excluded from git)

---

## Summary

6-gate sprint standardizing all CLI flags, consolidating duplicate command groups,
adding new workflow commands, and rewriting `workmain today`. Executed without user
intervention across all gates. All gate verification checks passed.

---

## Before / After Command Tree

### Notes

| Before | After |
|---|---|
| `workmain note add` | `workmain notes add` |
| `workmain note edit` | `workmain notes edit` |
| `workmain note delete` | `workmain notes delete` |
| `workmain note meeting -m X` | `workmain notes log -m X` (**renamed**) |
| `workmain notes today` | `workmain notes today` (unchanged) |
| `workmain notes date` | `workmain notes date` (unchanged) |
| `workmain notes search` | `workmain notes search` (unchanged) |
| `workmain notes meeting X` | `workmain notes meeting X` (unchanged) |

### Meetings

| Before | After |
|---|---|
| `workmain meetings create` | `workmain meetings create` (unchanged) |
| `workmain meetings list --today` | `workmain meetings today` (**new subcommand**) |
| `workmain meetings list --upcoming` | `workmain meetings upcoming -n 7d` (**new subcommand**) |
| `workmain meeting condense X` | `workmain meetings condense X` |
| `workmain meeting rename ID X` | `workmain meetings rename ID X` |
| `workmain meeting merge FROM TO` | `workmain meetings merge FROM TO` |

### New Commands

| Command | Description |
|---|---|
| `workmain meetings today` | Today's meetings, optional `--search/-s` |
| `workmain meetings upcoming` | Upcoming meetings, `--days/-n` (e.g. 7d, 2w, 1m) |
| `workmain eod` | Guided 6-step end-of-day workflow |

### Removed Commands

| Command | Reason |
|---|---|
| `workmain note` (group) | Merged into `workmain notes` |
| `workmain meeting` (group) | Merged into `workmain meetings` |

---

## Complete Flag Standard Reference

### `track add`

| Flag | Long | Short | Notes |
|---|---|---|---|
| Time | `--time` | `-T` | REQUIRED. Wall-clock start time. Was `-t`. |
| Tags | `--tags` | `-t` | New short form. |
| Notes | `--notes` | `-N` | Was `-n`. |
| Category | `--category` | `-C` | Was `-c`. |
| Meeting | `--meeting` | `-m` | Unchanged. |
| Date | `--date` | `-d` | Unchanged. |
| Start override | `--start` | `-b` | New flag. Clockify clock-in override. |
| End override | `--end` | `-e` | New flag. Clockify clock-out override. |

### `track edit`

| Flag | Long | Short | Notes |
|---|---|---|---|
| Description | `--description` | `-D` | Was `-d`. |

### `track sync push`

| Flag | Long | Short | Notes |
|---|---|---|---|
| Silent | `--silent` | `-q` | Was `-s`. |

### `time` group

| Flag | Long | Short | Notes |
|---|---|---|---|
| Show IDs | `--show-ids` | `-i` | No-op; IDs always shown. |

### `report list`

| Flag | Long | Short | Notes |
|---|---|---|---|
| Limit | `--limit` | `-n` | Was `-l`. |

### `providers costs`

| Flag | Long | Short | Notes |
|---|---|---|---|
| Limit | `--limit` | `-n` | Was `-l`. |

### `meetings create`

| Flag | Long | Short | Notes |
|---|---|---|---|
| Start | `--start` | `-b` | REQUIRED. Wall-clock start. |
| End | `--end` | `-e` | REQUIRED. Wall-clock end. |

### `notes add`

| Flag | Long | Short | Notes |
|---|---|---|---|
| Source | `--source` | `-f` | New short form. |

### `notes meeting`

| Flag | Long | Short | Notes |
|---|---|---|---|
| History | `--history` | `-H` | New short form. |

### `meetings upcoming`

| Flag | Long | Short | Default |
|---|---|---|---|
| Days | `--days` | `-n` | `7d` |

### `eod`

| Flag | Long | Short | Notes |
|---|---|---|---|
| Skip | `--skip` | `-s` | Comma-separated step names. |
| Dry run | `--dry-run` | (none) | Show plan without executing. |

---

## Modified Files with Version Numbers

| File | Before | After | Gate(s) |
|---|---|---|---|
| `cli/commands/track.py` | v1.8 | v1.9 | 1 |
| `cli/commands/report.py` | v1.7 | v1.8 | 1 |
| `cli/commands/providers.py` | v1.4 | v1.6 | 1, 6 |
| `cli/commands/meetings.py` | v2.9 | v3.0 | 1, 3 |
| `cli/commands/note.py` | v2.8 | v2.9 | 1 — then **deleted** in Gate 6 |
| NEW: `cli/commands/notes.py` | — | v3.0 | 2 |
| NEW: `cli/commands/eod.py` | — | v1.0 | 4 |
| NEW: `utils/duration_parser.py` | — | v1.0 | 3 |
| `cli/interface.py` | v1.0.0 | v1.5.0 | 1–6 |
| `workmain/__version__.py` | v1.1.0 | v1.2.0 | 6 |
| `docs/FEATURE_BACKLOG.md` | v3.1 | v3.2 | 6 |

---

## Notes for Next Session

- **Next Phase: 6 — Outlook Integration** (OAuth, calendar sync, email drafts)
- AI feedback loop planning: no spec yet
- `providers set-default` is marked [NOT IMPLEMENTED]; will require Phase 12 config system
- `meeting` group code remains in `meetings.py` as dead code (not registered in CLI);
  can be fully removed in a future cleanup pass
- IDs always show for notes, meetings, and time entries — `--show-ids/-i` on `time` is a no-op
  retained for muscle memory

---

*Sprint complete. WorkmAIn v1.2.0.*
