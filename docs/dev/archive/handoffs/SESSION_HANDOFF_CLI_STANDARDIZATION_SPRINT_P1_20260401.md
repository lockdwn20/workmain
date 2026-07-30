WorkmAIn
Session Handoff — CLI Standardization Sprint Part 1
v1.0
20260401

# Session Handoff: CLI Standardization Sprint Part 1

**Application Version:** v1.7.0 (was v1.6.10)
**Sprint Completed:** 20260401
**Branch:** `feature/cli-standardization-sprint` → merged to `dev` → PR to `main` open
**Spec:** `docs/dev/specs/CLI_STANDARDIZATION_SPRINT_PART1_SPEC_v1.0.md` → updated to v1.1 (sprint complete)
**Test Baseline:** 148 passed, 0 failed, 0 errors (unchanged from start of sprint)

---

## What Was Done

CLI Standardization Sprint Part 1 addressed all **High and Medium severity violations** (violations 1–5, 10–14)
from the full 18-violation audit in `docs/CLI_STANDARDS.md`. Executed in 9 Work Units on
`feature/cli-standardization-sprint`, merged to `dev` via no-ff merge, tagged `v1.7.0`.

PR from `dev` → `main` was opened manually (gh CLI not installed). Version bump of v1.7.0 is already
in the feature branch — merge to `main` does NOT need another version bump (the minor bump already happened).

---

## Breaking CLI Changes (Before → After)

| Old Command | New Command | WU |
|-------------|-------------|-----|
| `workmain track add/edit/delete/today/week/date` | `workmain time add/edit/delete/today/week/date` | WU-1 |
| `workmain track sync push` | `workmain clockify sync push` | WU-1 |
| `workmain track sync pull` | `workmain clockify sync pull` | WU-1 |
| `workmain track sync both` | `workmain clockify sync both` | WU-1 |
| `workmain slack post-weekly` | `workmain slack post weekly` | WU-2 |
| `workmain gdocs upload-notes` | `workmain gdocs upload notes` | WU-7 |
| `workmain gdocs upload-report` | `workmain gdocs upload report` | WU-7 |
| `workmain gdocs upload-clockify` | `workmain gdocs upload clockify` | WU-7 |
| `workmain gdocs upload-all` | `workmain gdocs upload all` | WU-7 |
| `workmain calendar today sync` | `workmain calendar sync` | WU-8 |
| `workmain calendar week sync` | `workmain calendar sync` | WU-8 |
| `workmain calendar month sync` | `workmain calendar sync` | WU-8 |
| `workmain reports view <id>` | `workmain reports show <id-or-filename>` | WU-6 |
| `workmain email recipients remove <id>` | `workmain email recipients delete <id>` | WU-5 |
| `workmain eod --skip/-s` | `workmain eod --skip/-S` | WU-4 |
| `providers costs --provider/-p` | `--provider/-P` | WU-4 |
| `providers costs --month/-m` | `--month/-M` | WU-4 |
| `reports history --type/-t` | `--type/-R` | WU-4 |
| `clockify sync pull --start/-s` | `--start/-b` | WU-4 |
| `clockify sync push --all/-a` | `--all` (no short form) | WU-4 |

### New Behaviors

- **`workmain time add <description>`** — description is now optional; prompts interactively if omitted (§4.4 interactive fallback)
- **`workmain reports show <target>`** — unified command accepting int ID (DB lookup) or filename (staging dir lookup); `view` command removed
- **`workmain slack post <period>`** — extensible; `weekly` is the only implemented value; other periods raise NotImplementedError
- **`workmain calendar sync`** — dedicated OAuth stub subcommand; `today`/`week`/`month` no longer accept `sync` as a positional argument

---

## Work Unit Commit Log

```
07354d3  feat(sprint): WU-9 CLI standardization sprint Part 1 complete — v1.7.0
bf4ceb0  feat(sprint): WU-8 calendar sync subcommand — remove action positional
3ee7ae7  feat(sprint): WU-7 gdocs upload subgroup — upload-all → upload all
18961e4  fix(sprint): WU-6 — consolidate reports view into reports show
d0eda7b  fix(sprint): WU-5 — email recipients remove → delete
88d7e12  fix(sprint): WU-4 — resolve 7 short form flag conflicts
b9da80a  fix(sprint): WU-3 — update eod.py subprocess calls for WU-1/WU-2 renames
bd248d3  feat(sprint): WU-2 — slack post PERIOD argument
18ea85d  feat(sprint): WU-1 — create time.py, move clockify sync, delete track.py
1f2ab8c  chore: pre-sprint doc corrections (CLI standards v1.5, backlog violations, Part 1 spec)
```

---

## File Version Table (End of Sprint)

| File | Version at Start | Version at End | Notes |
|------|-----------------|----------------|-------|
| `workmain/cli/commands/time.py` | — (new) | v1.1 | Replaces track.py |
| `workmain/cli/commands/track.py` | v2.1 | **Deleted** | Clean break |
| `workmain/cli/commands/clockify.py` | v1.3 | v1.5 | `sync` subgroup added (WU-1); short forms (WU-4) |
| `workmain/cli/commands/slack.py` | v1.2 | v1.3 | `post <period>` argument |
| `workmain/cli/commands/eod.py` | v1.9 | v2.3 | subprocess calls (WU-3), `-S` flag (WU-4), gdocs (WU-7), track hints (WU-9) |
| `workmain/cli/commands/email.py` | v1.3 | v1.4 | `recipients delete` |
| `workmain/cli/commands/reports.py` | v2.3 | v2.5 | `-R` flag (WU-4); unified `show` (WU-6) |
| `workmain/cli/commands/gdocs.py` | v1.3 | v1.4 | `upload` subgroup |
| `workmain/cli/commands/calendar.py` | v1.3 | v1.4 | `sync` subcommand; action positional removed |
| `workmain/cli/commands/providers.py` | v1.7 | v1.8 | `-P/-M` short forms |
| `workmain/cli/interface.py` | v2.3.0 | v2.5.0 | Import `time`; remove `track`; residual sweep |
| `workmain/__version__.py` | v1.6.10 | v1.7.0 | Minor bump (breaking changes) |
| `CHANGELOG.md` | — | [1.7.0] entry | Breaking changes documented |
| `docs/CLI_STANDARDS.md` | v1.4 | v1.6 | New file; violation register; §5.3 reserved table |
| `docs/FEATURE_BACKLOG.md` | v3.9 | v4.0 | Items 20–24 added (deferred violations) |
| `CLAUDE.md` | test baseline 142 | test baseline 148 | Corrected stale count |
| `tests/test_eod_pipeline.py` | v1.0 | v1.1 | `post-weekly` → `post weekly` assertion |
| `tests/test_report_history.py` | v1.0 | v1.1 | `reports view` → `reports show` invocations |
| `tests/test_gdrive.py` | v1.0 | v1.1 | `upload-all` → `upload all` invocation |

---

## Pre-Sprint Corrections Applied

- **Violation 10 false positive:** `meetings upcoming --days/-d` was listed as a conflict. Live code uses `--days/-n` — already compliant. Count corrected from 8 to 7 actual short-form conflicts.
- **Test baseline:** CLAUDE.md had stale `142`; actual baseline was 148. Corrected in WU-0.

---

## Implementation Gotchas — Learned This Sprint

1. **`ctx.invoke()` references Python function objects, not CLI names.** In `gdocs.py`, `gdocs_upload_all` calls `ctx.invoke(gdocs_upload_notes, ...)`. When the CLI decorator changed from `@gdocs.command('upload-notes')` to `@gdocs_upload.command('notes')`, the Python function name did NOT need to change — `ctx.invoke` targets the function object. Only the decorator changed.

2. **`clockify sync pull --start/-b` — not `-s`.** `-s/--search` is globally reserved (§5.3). The `sync pull` `--start` flag must use `-b` ("begin"), consistent with `time add --start/-b` and `meetings create --begin/-b`.

3. **`clockify sync push --all` — no short form is intentional.** Deliberate friction for bulk destructive operations. This is a documented decision in CLI_STANDARDS.md §5.3.

4. **WU-2 and WU-3 must be committed before running pytest.** After WU-2 renames `post-weekly`, `eod.py` subprocess still calls the old name — tests fail until WU-3 fixes it. Plan explicitly requires committing WU-2 before pytest.

5. **`reports show` unified command uses `int()` to branch.** If `int(target)` succeeds → ID path (DB lookup). `ValueError` → filename path (staging directory lookup). The staging dir is resolved from `generator.output_dir` via `get_report_generator(session)`.

6. **`email recipients delete` function renamed.** Changed from `recipients_remove` to `recipients_delete` along with the decorator. No test invokes the CLI name string directly (email tests target the repository layer), so no test update was needed.

---

## Deferred Violations (Feature Backlog)

The following violations were out of scope for Part 1 and logged in `docs/FEATURE_BACKLOG.md`:

| Backlog Item | Violation | Description | Target Phase |
|---|---|---|---|
| Item 20 | Violation 6 | `tasks carryover` single-command group — barely qualifies; expand when Phase 11 adds more task commands | Phase 11 |
| Item 21 | Violation 7 | `reports costs` + `providers costs` potential duplicate surface — audit and remove redundant one | Phase 12 |
| Item 22 | Violation 8 | `add-holiday` must be built under `schedule` group in Phase 10, not as a top-level command | Phase 10 (pre-emptive) |
| Item 23 | Violation 9 | `add-timeoff` must be built under `schedule` group in Phase 10, not as a top-level command | Phase 10 (pre-emptive) |
| Item 24 | Violation 18 | Name-or-ID rule missing on `notes edit/delete`, `time edit/delete`, `meetings delete/rename`, `email recipients delete` | Phase 12 |

---

## Remaining Work — Sprint Part 2

**Violations 15, 16, 17** were explicitly scoped out of Part 1 and flagged for a follow-on
`feature/cli-standardization-sprint-part2` branch. No code was written for these in this sprint.

### Violation 15 — `meetings track` Verb

**Severity:** Medium
**Current state:** `workmain meetings track 'Meeting Title'` creates a time entry from a meeting.
**Issue:** `track` is a verb that no longer exists as a command group (renamed to `time` in WU-1).
Using `track` as a subcommand verb inside `meetings` is now a naming inconsistency.

**Options to evaluate before starting:**
1. **Rename to `meetings log-time`** — §3.2 permits `log` as a standard verb; descriptive
2. **Rename to `meetings time`** — parallel to `workmain time add`; very concise but potentially confusing since `time` is now a top-level group
3. **Retire the command** — `meetings condense` already prompts to track time at the end; `meetings track` may be redundant. Check actual usage before deciding.
4. **Keep as-is** — `track` as a subcommand verb (not a group name) may be acceptable per §3.3 domain-specific verbs

**Recommendation:** Research whether the command is used before deciding. If rarely used and `meetings condense` covers the flow, retire it and add a deprecation note. If retained, prefer `meetings log-time`.

**Files to change:** `workmain/cli/commands/meetings.py` (rename decorator + function), `workmain/cli/interface.py` `today()` references.

---

### Violation 16 — `templates` Subcommand Structure

**Severity:** Medium
**Current issues (two distinct problems):**

**16a. `templates list-aliases` → `templates list --aliases`**

`list-aliases` is a hyphenated command name rather than an option on `list`. Per §3.2, `list` is the standard verb for listing; variant views should be flags.

- `@templates.command('list-aliases')` → remove; add `--aliases/-A` flag to `templates list`
- If `--aliases` is set: show only aliases; otherwise: show full template list (current behavior)
- Files: `workmain/cli/commands/templates.py`

**16b. `templates add-section` → needs design**

`add-section` is hyphenated and imperative-first. The correct form depends on the domain model:
- If sections belong to templates: `templates sections add <template> <section>` (noun-verb, subgroup pattern)
- If it's truly a one-off operation: `templates section add` (still noun-verb without subgroup)
- §3.2 permits `add` as a verb, but the noun must come first in the group hierarchy

**Recommendation:** Evaluate whether a `templates sections` subgroup makes sense (would it have `list`, `add`, `remove`?). If yes, build the full subgroup. If `add-section` is the only operation, just rename to `templates section add` without a subgroup.

**Files to change:** `workmain/cli/commands/templates.py`, `workmain/cli/interface.py` references.

---

### Violation 17 — `providers set-default` Naming

**Severity:** Medium
**Current state:** `workmain providers set-default <provider>` — hyphenated command name.
**Issue:** Hyphenated verbs violate §3.2. This is currently a stub (raises NotImplementedError), so the rename is low-risk.

**Fix:** `@providers.command('set-default')` → `@providers.command('set')` with `@click.argument('target', type=click.Choice(['default']))` positional, making it `workmain providers set default <provider>`.

Alternatively if `set` will have multiple subcommands in the future (e.g. `providers set model`, `providers set key`), use a `@providers.group('set')` subgroup pattern instead of a positional argument. This is the cleaner long-term design.

**Recommendation:** Use `@providers.group('set')` from the start — `providers set default <provider>` and `providers set model <provider>` can both live under it. Phase 12 (Setup Wizard) will likely add more provider config commands.

**Files to change:** `workmain/cli/commands/providers.py`; no tests for this command (it's a stub).

---

## Part 2 Branch Strategy

```bash
git checkout dev
git checkout -b feature/cli-standardization-sprint-part2
```

One commit per violation. Merge to `dev` as one PR. No version bump needed within `dev` —
bump only on merge to `main` (patch or minor depending on scope of changes).

**Suggested commit structure:**
```
fix(sprint2): WU-P2-1 — meetings track verb rename/retire
fix(sprint2): WU-P2-2 — templates list --aliases flag; add-section restructure
fix(sprint2): WU-P2-3 — providers set-default → providers set group
chore(sprint2): CLI Standardization Sprint Part 2 complete
```

---

## Open PR

The `dev` → `main` PR was created manually (gh CLI not installed on this machine).
PR URL: https://github.com/lockdwn20/workmain/compare/main...dev

**Merge checklist before merging to main:**
- [ ] PR approved
- [ ] 148 tests still passing on `dev` (run `python -m pytest tests/ -q` on latest `dev`)
- [ ] `__version__.py` is already at `v1.7.0` — no additional bump needed
- [ ] `CHANGELOG.md` [1.7.0] entry already present
- [ ] Tag `v1.7.0` already pushed to remote
- [ ] After merge: confirm `workmain --version` returns `1.7.0` on `main`

---

## Current State Summary

| Item | State |
|------|-------|
| Project version | v1.7.0 on `dev`; v1.6.10 on `main` (pending PR merge) |
| Active branch | `dev` (clean) |
| Test suite | 148 passed, 0 failed |
| CLI Standards | `docs/CLI_STANDARDS.md` v1.6 — 18-violation register, §5.3 reserved table complete |
| Sprint Part 1 | ✅ Complete — merged, tagged |
| Sprint Part 2 | ⏳ Not started — violations 15, 16, 17 scoped and ready |
| Phase 10 | ⏳ Unblocked — CLI Standards gate satisfied; ready to begin |
