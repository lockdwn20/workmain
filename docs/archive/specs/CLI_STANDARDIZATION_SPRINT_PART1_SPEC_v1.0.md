WorkmAIn
CLI Standardization Sprint Part 1 - Implementation Specification
v1.1 - 20260401

**STATUS: SPRINT COMPLETE** — All 9 Work Units committed to `feature/cli-standardization-sprint`.
Version bumped to v1.7.0. 148 tests pass. Ready to merge to `dev`.

---

v1.0 - 20260331

---

## Purpose

This document is the authoritative implementation spec for CLI Standardization Sprint Part 1. It supersedes `CLI_STANDARDIZATION_SPRINT_SPEC_v1.2.md` for all Part 1 violations. The compiled plan at `/home/lockdwn20/.claude/plans/compiled-soaring-fox.md` is the source-of-record for the full work unit sequence; this spec captures it in the project doc tree before execution begins.

---

## Branch

`feature/cli-standardization-sprint` — branched from `dev` on 20260331.

One commit per work unit. Merge to `dev` as one PR after all tests pass.

---

## Pre-Sprint Corrections

**Violation 10 count correction:** The violation register originally listed `meetings upcoming --days/-d` as a conflict. Live code uses `--days/-n` — already compliant. Count corrects from 8 to 7 actual short-form conflicts. `CLI_STANDARDS.md` updated to v1.5 accordingly.

**Test baseline:** 148 collected (CLAUDE.md note of 142 was stale — corrected in WU-0).

---

## Work Units

### WU-0: Pre-sprint documentation (no code)

Files changed:
- `docs/dev/specs/CLI_STANDARDIZATION_SPRINT_PART1_SPEC_v1.0.md` — this file (new)
- `docs/CLI_STANDARDS.md` — v1.4 → v1.5: remove meetings upcoming false conflict, count 8 → 7; annotate WU-4 short form assignments in §5.3
- `CLAUDE.md` — test baseline 142 → 148
- `docs/FEATURE_BACKLOG.md` — add Items 20–24 for deferred violations 6, 7, 8, 9, 18

Commit: `chore: pre-sprint doc corrections (CLI standards v1.5, backlog violations, Part 1 spec)`

---

### WU-1: Items 1 + 2 + 3 + 5 — Create `time.py`, move sync to `clockify.py`

Root dependency of the sprint. Done first and atomically.

**New file: `workmain/cli/commands/time.py`** (v1.0 → v1.1 after WU-4)

- Single `time` group replacing both `track` and `time` from old `track.py`
- Copy `format_time_entry_display()` and `format_time_summary()` verbatim
- Commands under `time`: `add`, `edit`, `delete`, `today`, `week`, `date`
- Item 5: On `time add`, make `DESCRIPTION` optional (`required=False, default=None`). Add at top of function body: `if not description: description = click.prompt('Description')`
- Update all docstring examples: `workmain track add` → `workmain time add`
- `__all__ = ['time']`

**Modified: `workmain/cli/commands/clockify.py`** (v1.3 → v1.4)

- Add `sync` subgroup to `clockify` with `push`, `pull`, `both` commands — copied verbatim from `track.py` sync section
- Decorator: `@track.group('sync')` → `@clockify.group('sync')`
- Update `status()` hint text: `'workmain track sync push'` → `'workmain clockify sync push'`

**Delete: `workmain/cli/commands/track.py`**

Clean break — no alias, no deprecation wrapper.

**Modified: `workmain/cli/interface.py`** (v2.3.0 → v2.4.0)

- Import: `from workmain.cli.commands.track import track, time` → `from workmain.cli.commands.time import time`
- Registration: remove `cli.add_command(track)`, keep `cli.add_command(time)`
- Update `today()` and `status()` help text: `track add` → `time add`, `track edit` → `time edit`, `track sync push` → `clockify sync push`

**Tests:** Grep `tests/` for any import from `workmain.cli.commands.track` — update to `.time`. Run `pytest tests/ -q`.

**Verify:** `workmain time --help` shows `add/edit/delete/today/week/date`. `workmain clockify sync --help` shows `push/pull/both`. `workmain track` returns "No such command" error.

Commit: `feat(sprint): WU-1 — create time.py, move clockify sync, delete track.py`

---

### WU-2: Item 4 — `slack post PERIOD`

**Modified: `workmain/cli/commands/slack.py`** (v1.2 → v1.3)

- `@slack.command("post-weekly")` → `@slack.command("post")`
- Add before existing options: `@click.argument('period', type=click.Choice(['weekly', 'daily', 'monthly']))`
- Rename function `slack_post_weekly` → `slack_post`; add `period` to signature
- Guard at top of body:
  ```python
  if period != 'weekly':
      raise NotImplementedError(f"slack post {period} is not yet implemented.")
  ```
- Update docstring examples

Note: `eod.py` subprocess call to `post-weekly` breaks after this. WU-2 and WU-3 must be committed before running `pytest`.

**Verify:** `workmain slack post weekly --help` works. `workmain slack post-weekly` returns error.

Commit: `feat(sprint): WU-2 — slack post PERIOD argument`

---

### WU-3: Update `eod.py` subprocess calls (depends on WU-1 + WU-2)

**Modified: `workmain/cli/commands/eod.py`** (v1.9 → v2.0)

1. `_run_sync_step`: `['workmain', 'track', 'sync', 'push']` → `['workmain', 'clockify', 'sync', 'push']`. Update dry-run print string to match.
2. `_run_slack_weekly_step`: `['workmain', 'slack', 'post-weekly']` → `['workmain', 'slack', 'post', 'weekly']`. Update dry-run print string to match.
3. Step description: `'Post weekly draft to Slack (slack post-weekly)'` → `'Post weekly draft to Slack (slack post weekly)'`

**Modified: `tests/test_eod_pipeline.py`** (version bump)
- Update any assertion on `'slack post-weekly'` → `'slack post weekly'`

Run `pytest tests/ -q` — must pass.

**Verify:** `workmain eod --dry-run` shows `clockify sync push` and `slack post weekly` in the plan table.

Commit: `fix(sprint): WU-3 — update eod.py subprocess calls for WU-1/WU-2 renames`

---

### WU-4: Item 10 — Short form flag conflicts (7 actual)

| Conflict | File | Resolution |
|---|---|---|
| `clockify sync pull --start/-s` | `clockify.py` | Assign `-b` (expand scope) |
| `clockify sync push --all/-a` | `clockify.py` | Remove `-a` entirely |
| `eod --skip/-s` | `eod.py` | Assign `-S` (uppercase) |
| `time edit --category/-c` | `time.py` | Change to `-C` (uppercase) |
| `providers costs --provider/-p` | `providers.py` | Assign `-P` (uppercase) |
| `providers costs --month/-m` | `providers.py` | Assign `-M` (uppercase) |
| `reports list --type/-t` | `reports.py` | Assign `-R` (uppercase) |

`CLI_STANDARDS.md` bumped to v1.6 with §5.3 updates for each change.

**Version bumps:** `clockify.py` v1.4 → v1.5, `eod.py` v2.0 → v2.1, `time.py` v1.0 → v1.1, `providers.py` +1, `reports.py` +1

**Tests:** Grep all test files for short form invocations of affected commands and update. Run `pytest tests/ -q`.

Commit: `fix(sprint): WU-4 — resolve 7 short form flag conflicts`

---

### WU-5: Item 11 — `email recipients delete`

**Modified: `workmain/cli/commands/email.py`** (v1.3 → v1.4)

- `@email_recipients.command('remove')` → `@email_recipients.command('delete')`
- Function name `recipients_remove` → `recipients_delete`
- Update docstring example

**Verify:** `workmain email recipients delete 1` works. `workmain email recipients remove` returns error.

Commit: `fix(sprint): WU-5 — email recipients remove → delete`

---

### WU-6: Item 12 — Consolidate `reports show` + `reports view`

**Modified: `workmain/cli/commands/reports.py`** (version from WU-4 +1)

Single `show` command accepting either ID or filename:

```python
@click.argument('target', type=str)
# Body:
try:
    report_id = int(target)
    # ID path — current view() logic
except ValueError:
    # Filename path — current show() logic
```

Remove `view` command entirely. Update docstring with both usage examples.

**Tests:** Update any `test_report_history.py` invocations of `['reports', 'view', ...]` → `['reports', 'show', ...]`.

**Verify:** `workmain reports show 42` resolves by ID. `workmain reports show daily_internal_20260305.md` resolves by filename. `workmain reports view` returns error.

Commit: `fix(sprint): WU-6 — consolidate reports view into reports show`

---

### WU-7: Item 13 — `gdocs upload <ARTIFACT>`

**Modified: `workmain/cli/commands/gdocs.py`** (v1.3 → v1.4)

Replace four `@gdocs.command('upload-*')` with a `@gdocs.group('upload')` subgroup:

```python
@gdocs.group('upload')
def gdocs_upload():
    """Upload work artifacts to Google Drive."""
    pass

@gdocs_upload.command('notes')    # was upload-notes
@gdocs_upload.command('report')   # was upload-report
@gdocs_upload.command('clockify') # was upload-clockify
@gdocs_upload.command('all')      # was upload-all
```

Python function names unchanged — `ctx.invoke()` calls in `upload all` reference function objects directly.

**Modified: `workmain/cli/commands/eod.py`** (v2.1 → v2.2)

- `['workmain', 'gdocs', 'upload-all', '--date', date_str]` → `['workmain', 'gdocs', 'upload', 'all', '--date', date_str]`
- Dry-run print and step description updated to match.

**Tests:** Update `test_gdrive.py` CLI invocations: `upload-all` → `upload all`, `upload-notes` → `upload notes`, etc.

**Verify:** `workmain gdocs upload notes` works. `workmain gdocs upload all` works. `workmain gdocs upload-notes` returns error.

Commit: `feat(sprint): WU-7 — gdocs upload <ARTIFACT> subgroup`

---

### WU-8: Item 14 — `calendar sync` subcommand

**Modified: `workmain/cli/commands/calendar.py`** (v1.3 → v1.4)

For `today`, `week`, `month` commands:
- Remove `@click.argument('action', required=False, type=click.Choice(['sync']))` and `action` parameter
- Remove `if action == 'sync': raise NotImplementedError(...)` guard

Add new subcommand:
```python
@calendar.command('sync')
def calendar_sync():
    """Sync calendar from Outlook (requires OAuth setup).

    Note: OAuth is currently stubbed (corporate policy).
    Use 'workmain calendar import <file>' to import via ICS export.
    """
    raise NotImplementedError(
        "Calendar sync requires OAuth. Use 'workmain calendar import <file>' instead."
    )
```

No `test_calendar.py` exists — no test changes needed.

**Verify:** `workmain calendar today` works without argument. `workmain calendar sync` shows the not-implemented message. `workmain calendar today sync` returns error.

Commit: `fix(sprint): WU-8 — calendar sync as proper subcommand`

---

### WU-9: Final cleanup

**Modified: `workmain/cli/interface.py`** (v2.4.0 → v2.5.0)

Final sweep of `status()` and `today()` help text for stale references:
- `gdocs upload-all` → `gdocs upload all`
- `calendar today sync` etc. → `calendar sync`
- Any residual `track` or `post-weekly` references

**Modified: `CHANGELOG.md`**

Add sprint section documenting all breaking changes:
- `workmain track` → `workmain time` (add/edit/delete)
- `workmain track sync push/pull/both` → `workmain clockify sync push/pull/both`
- `workmain slack post-weekly` → `workmain slack post weekly`
- `workmain gdocs upload-{notes,report,clockify,all}` → `workmain gdocs upload {notes,report,clockify,all}`
- `workmain reports view <id>` → `workmain reports show <id>`
- `workmain email recipients remove` → `workmain email recipients delete`
- `workmain calendar today/week/month sync` → `workmain calendar sync`
- Short form changes: `-b` expanded to `clockify sync pull`; `-S` = `--skip`; `-C` expanded to `time edit`; `-P` = `--provider`; `-M` = `--month`; `-R` = `--type`; `clockify sync push --all` loses short form

**Update spec:** This file → bump to v1.1 noting sprint complete.

**Final run:** `pytest tests/ -q` — confirm 148+ pass, 0 failed.

Commit: `feat(sprint): CLI standardization sprint Part 1 complete`

---

## Version Header Checklist

| File | Before | After |
|------|--------|-------|
| `time.py` (new) | — | v1.1 (v1.0 at WU-1, bumped at WU-4) |
| `track.py` | v2.1 | **Deleted** |
| `clockify.py` | v1.3 | v1.5 (WU-1 + WU-4) |
| `slack.py` | v1.2 | v1.3 |
| `eod.py` | v1.9 | v2.2 (WU-3 + WU-7) |
| `email.py` | v1.3 | v1.4 |
| `reports.py` | v2.3 | v2.4 (WU-4 + WU-6) |
| `gdocs.py` | v1.3 | v1.4 |
| `calendar.py` | v1.3 | v1.4 |
| `interface.py` | v2.3.0 | v2.5.0 |
| `providers.py` | (check live) | +1 |
| `test_eod_pipeline.py` | (check live) | +1 |
| `test_gdrive.py` | (check live) | +1 |
| `CLI_STANDARDS.md` | v1.4 | v1.6 (WU-0 correction + WU-4 short form updates) |

---

## Sprint Part 2 (separate plan after Part 1 merges)

`feature/cli-standardization-sprint-part2` branch:

- Violation 15: `meetings track` verb — research whether to retire (superseded by `time add --meeting`) or rename
- Violation 16: `templates list-aliases` → `templates list --aliases`; `templates add-section` → restructure
- Violation 17: `providers set-default` → `providers set default` with positional; currently stubbed

## Deferred to Feature Backlog

| Violation | Backlog Item | Phase |
|---|---|---|
| 6 (`tasks carryover` single-command group) | Item 20 | Phase 11 |
| 7 (`reports costs` + `providers costs` audit) | Item 21 | Phase 12 |
| 8 (`add-holiday` top-level placement) | Item 22 | Phase 10 |
| 9 (`add-timeoff` top-level placement) | Item 23 | Phase 10 |
| 18 (name-or-ID rule on edit/delete commands) | Item 24 | Phase 12 |
