WorkmAIn
HOTFIX_ITEM56_REPORTS_CORRECTIONS_SPEC v1.2
20260717

---

## Status

Approved by Ray on 20260717. Ready for Role 3 implementation.
Recon basis:
- `RECON_SPEC_ITEM56_REPORTS_CORRECTIONS_20260717.md` (`docs/dev/design/`)
- `RECON_SPEC_REPORT_CORRECTION_DATA_INTEGRITY_20260717.md` (`docs/dev/design/`)

Both referenced, not reproduced.

## Scope

**In scope:**
- Rewrite `workmain reports corrections` display from a truncated Rich
  Table to a plain-text block format
- Default 7-day window on `updated_at` (correction date), mirroring
  `notes_list`'s default window mechanism exactly — substituting
  `updated_at` for `note.created_date`, and `--search` (no `--meeting`
  equivalent exists for corrections) as the lift condition
- Add `-s/--search` (matches `correction_note` only; lifts the window)
- Add `-n/--limit` (default 20, secondary cap — mirrors `notes_list`)
- Add `-R/--type` (report type filter, validated; does NOT lift the
  window, mirrors `--tags` on `notes_list`)
- Extract a shared `_validate_report_type()` helper in `reports.py`,
  refactoring `_report_list_impl` to use it alongside the new command —
  touches existing, working code, not just new code (Design Rule 10)
- Add `--all` (bypasses both the window and the limit)
- Fix sort order to `updated_at DESC` (correction recency), not
  `report_date`
- New `ReportsRepository.get_filtered()` method; `reports_corrections`
  calls it instead of querying the ORM directly
- Extend `reports show <id>` (ID path only) to render `corrected_content`
  alongside `content` when present

**Out of scope:**
- Date-range filtering as a *user-facing flag* beyond the existing
  single-date `--date` (stays single-date only — Ray's own call; the
  window is a default-scoping mechanism, not a new user-facing range
  filter, so this doesn't reopen that decision)
- Dedicated `corrected_at` column. `updated_at` carries an
  `onupdate=datetime.now` staleness risk in principle (any later write
  to a corrected row would bump it), but not in practice for this
  workflow: daily reports are never edited after sending, and a weekly
  report not posted Thursday is never posted at all — there is no later
  day for a post-time write to land on. No later-day write ever touches
  an already-corrected row. Revisit only if that workflow changes.
- A note prompt on standalone `workmain reports correct <id>` (currently
  absent, unlike the EOD `[e]dit` branch, which does prompt) — real,
  known gap, deferred to a separate future item, not part of this
  hotfix.
- Any other change to `correction_note` write paths (EOD `[e]dit` or
  `action_executor`) — this spec is display/read-only
- `reports show`'s filename path (non-integer target) — untouched, no
  `corrected_content` concept applies there
- `CLAUDE.md`'s inaccurate claim that `correction_note` is written only
  by `action_executor` — real drift, but a docs fix, not part of this
  hotfix
- `report_resend` writing original `content` back over a corrected
  staging file — reported as fact by recon, not evaluated or fixed here

## Design Rules

1. `reports_corrections` sorts by `Report.updated_at.desc(), Report.id.desc()`
   — never `report_date`. See Scope/Out-of-scope for why a dedicated
   `corrected_at` column was considered and not added.
2. Default window: when `--date` and `--search` are both absent, results
   are scoped to `updated_at >= (today - 7 days)`. Mirrors
   `notes_list`'s `date_filter is None and meeting_ids is None and not
   search` condition, with `updated_at` standing in for
   `note.created_date` and no `--meeting`-equivalent flag (corrections
   has none).
3. `--type` alone does NOT lift the window — same as `--tags` not lifting
   `notes_list`'s window. Only `--search` or an explicit `--date` lifts
   it.
4. `--search` lifts the window (searches full history, not just the last
   7 days) — matching `notes_list`'s `--search` behavior exactly.
5. `--limit` (default 20) is always applied as a secondary cap on top of
   whatever the window/search/type filters produce — mirrors
   `notes_list`'s always-on `--limit` (default 20). It is NOT itself
   lifted by anything.
6. `--all` bypasses both the window and the limit — the only way to see
   truly everything. Takes precedence if combined with `--limit`.
7. `--search` matches `correction_note` only. Corrections made via
   standalone `reports correct <id>` (no note prompt on that path)
   display `(no note)` and are not findable by `--search` — accepted,
   not a defect to fix here.
8. Display is plain-text (`click.echo`), not a Rich `Table` — no
   truncation of `correction_note` under any circumstance.
9. `report_corrections()` must call `ReportsRepository.get_filtered()` —
   no direct `session.query(Report)` calls in the CLI function.
10. `--type` validation is centralized in one new module-level helper in
    `reports.py`, `_validate_report_type(report_type)` — extracted from
    `_report_list_impl`'s existing inline `VALID_REPORT_TYPES` check
    (same error message and exit behavior, just moved, not rewritten).
    `_report_list_impl` is refactored to call this helper instead of its
    inline block; `report_corrections` calls the same helper. No second
    copy of the validation logic or its error string anywhere. Because
    this touches existing, working code (`_report_list_impl`), the
    existing `reports list --type <bogus>` error behavior must be
    regression-tested after the refactor, not just re-verified on the
    new command.
11. `--date` filters `report_date` (the report's subject date); sort and
    the default window use `updated_at` (correction recency). Deliberate
    — these answer two different questions ("corrections on this subject
    date" vs. "corrections I made recently") — not an oversight.
12. `--full`/diff functionality does not exist on `reports corrections` in
    any form. It lives only on `reports show <id>` (ID path), gated on
    `report.corrected_content is not None`.
13. `reports show`'s filename path is unchanged in this hotfix.
14. A report with `correction_note is None` displays as `(no note)` in
    the corrections listing — never a blank line or a dash.
15. Zero results in an unfiltered (windowed) call print "No corrected
    reports found." — the same generic message as any other empty
    result, no special-cased "empty week" wording, and no `--all` hint.
16. **Test-fixture trap:** `Report.updated_at` has `onupdate=datetime.now`
    on the model. Any fixture that constructs a `Report`, commits, and
    then mutates/re-commits that same row will silently overwrite
    `updated_at` to the current time, invalidating any test asserting a
    specific, scrambled `updated_at` ordering. Fixtures for
    `test_get_filtered_orders_by_updated_at_desc` (Gate 1) and
    `test_default_window_applied`, `test_type_alone_does_not_lift_window`,
    `test_sort_order_is_updated_at_not_report_date` (Gate 2) must set
    `updated_at` at construction (INSERT) and must not perform any
    further commit-triggering write on that row.

## Branch & Git Workflow

Per `GIT_WORKFLOW_STANDARDS.md` v1.6 (confirm current version before
starting — Sonnet reads this doc every session).

- **Branch type:** `hotfix/*`
- **Branch name:** `hotfix/item-56-reports-corrections`
- **Branches from:** `main`
- **Merges to:** `main` **and** `dev`
- **Commit strategy:** one descriptive commit per gate (body: files
  changed, decisions applied, test count)
- **Deployment:** touches `workmain/**` (both `reports.py` and
  `reports_repo.py`) — **the restart-and-verify step is mandatory** after
  merging to `dev`:
  ```bash
  systemctl --user restart workmain-notify.service
  systemctl --user show workmain-notify.service --property=ActiveEnterTimestamp
  ```
  Confirm the new `ActiveEnterTimestamp` postdates the merge commit before
  reporting the change as deployed.
- **Version bump:** `__version__.py` `1.25.0` → `1.25.1` (patch, per
  Version Bump Rules table — hotfix merge to `main`). Bump at the final
  gate, alongside the `CHANGELOG.md` entry.

## Gates

### Gate 1 — Repository Layer: `ReportsRepository.get_filtered()`

- **Files:** `workmain/database/repositories/reports_repo.py`
- **Changes:** Add a new method:
  ```python
  def get_filtered(
      self,
      status: Optional[str] = None,
      report_type: Optional[str] = None,
      report_date: Optional[date] = None,
      updated_after: Optional[date] = None,
      search: Optional[str] = None,
      limit: Optional[int] = None,
  ) -> List[Report]:
      """
      Filtered report query for corrections listing.

      Ordered by updated_at DESC, id DESC (correction recency, not
      report_date). updated_after applies a >= floor on updated_at
      (used for the default 7-day window; None = no floor). search
      matches correction_note only (ILIKE). limit=None returns
      unbounded results.
      """
      q = self.session.query(Report)
      if status:
          q = q.filter(Report.status == status)
      if report_type:
          q = q.filter(Report.report_type == report_type)
      if report_date:
          q = q.filter(Report.report_date == report_date)
      if updated_after:
          q = q.filter(Report.updated_at >= updated_after)
      if search:
          q = q.filter(Report.correction_note.ilike(f'%{search}%'))
      q = q.order_by(Report.updated_at.desc(), Report.id.desc())
      if limit is not None:
          q = q.limit(limit)
      return q.all()
  ```
  Do not modify `list_reports()` or any other existing method — this is
  additive only.
- **Tests:** `tests/test_report_correction.py` — new tests appended to
  this file (existing home for repo/model-level correction behavior; see
  `test_original_content_preserved_after_correction` for the file's
  existing style/session pattern). **Read Design Rule 16 before writing
  any of these** — the `onupdate` trap will silently break the sort test
  if fixtures are built the wrong way:
  - `test_get_filtered_by_status`
  - `test_get_filtered_by_report_type`
  - `test_get_filtered_by_report_date`
  - `test_get_filtered_updated_after_floor` — assert rows with
    `updated_at` before the floor are excluded, rows on/after included
  - `test_get_filtered_search_matches_correction_note_only` — assert a
    report whose `content`/`corrected_content` contains the search term
    but whose `correction_note` does not is excluded
  - `test_get_filtered_search_case_insensitive`
  - `test_get_filtered_limit_caps_results`
  - `test_get_filtered_limit_none_returns_unbounded`
  - `test_get_filtered_orders_by_updated_at_desc` — assert against
    explicit `updated_at` values, not creation order, to prove the sort
    key (report_date order and updated_at order must be deliberately
    scrambled in the fixture, set at construction per Design Rule 16, so
    the test would fail if the old `report_date` sort were still in
    effect)
- **Version bump:** `reports_repo.py` v1.4 → v1.5
- **Human approval checkpoint:** Ray confirms `get_filtered()` behavior
  and test results before Gate 2 begins.

### Gate 2 — `reports_corrections` Command Rewrite

- **Files:** `workmain/cli/commands/reports.py`
- **Changes:**
  1. Replace the existing `-d/--date`-only Click signature with:
     ```python
     @reports.command('corrections')
     @click.option('-d', '--date', 'date_str', default=None, metavar='YYYY-MM-DD',
                   help='Filter by report date')
     @click.option('-s', '--search', default=None, help='Search correction notes')
     @click.option('-n', '--limit', 'limit_opt', type=int, default=None,
                   help='Maximum results [default: 20]')
     @click.option('-R', '--type', 'report_type', default=None,
                   help='Filter by report type')
     @click.option('--all', 'show_all', is_flag=True, default=False,
                   help='Show all results, no window, no limit')
     def report_corrections(date_str, search, limit_opt, report_type, show_all):
     ```
     Mirror `reports_list`'s exact `-R/--type` decorator verbatim from the
     same file — do not invent a `click.Choice` if `reports_list` doesn't
     use one.
  2. Extract `_report_list_impl`'s existing inline `VALID_REPORT_TYPES`
     check into a new module-level helper, `_validate_report_type
     (report_type)` (Design Rule 10) — same logic, same error message,
     same exit behavior, moved rather than rewritten. Refactor
     `_report_list_impl` to call this helper in place of its inline
     block. Call the same helper from `report_corrections` before the
     repository call. Locate `_report_list_impl`'s current test coverage
     for `--type` validation (likely alongside `reports list`/`reports
     history` tests — not enumerated by the Item #56 recon, which
     scoped to `reports_corrections`) and confirm it still passes after
     the refactor; if no such test exists today, add one as a
     regression guard before making this change.
  3. Window and limit logic (Design Rules 2-6):
     ```python
     window_start = None
     if not show_all and not date_str and not search:
         window_start = datetime.now().date() - timedelta(days=7)

     effective_limit = None if show_all else (limit_opt if limit_opt is not None else 20)
     ```
  4. Replace the `session.query(Report)...` block with a call to
     `get_reports_repository(session).get_filtered(status='corrected',
     report_type=report_type, report_date=filter_date,
     updated_after=window_start, search=search, limit=effective_limit)`.
     Keep the existing `date.fromisoformat()` parsing and its
     `SystemExit(1)` error handling for invalid `--date` values
     unchanged.
  5. Replace the Rich `Table` display with a plain-text block format,
     mirroring `notes_list`'s shape (`docs/dev/design/
     RECON_SPEC_ITEM56_REPORTS_CORRECTIONS_20260717.md` Section 2 for
     the exact reference code):
     - Header line selection (first match wins): `search` set ->
       `f"Corrections matching '{search}'"`; `filter_date` set (no
       search) -> `f"Corrections — {filter_date}"`; `show_all` set (no
       search, no date) -> `"Report Corrections — all"`; `report_type`
       set (no search, no date, not all) -> `f"Corrections — type
       {report_type}"`; else (default windowed case) ->
       `"Report Corrections — last 7 days"` (direct mirror of
       `notes_list`'s `"Notes — last 7 days"` default header).
     - `click.echo(f"\n{header} ({len(rows)}):\n")` then `"=" * 60`.
     - Group rows by `updated_at.date()` (the correction date, not
       `report_date`) with `[YYYY-MM-DD]` sub-headers and `"-" * 60`
       separators, exactly matching `notes_list`'s grouping loop shape
       (same recon section) — substitute `updated_at.date()` for
       `note.created_date` as the grouping key.
     - Per-row block, new helper function `format_correction_display`
       (module-level, alongside `format_note_display`'s pattern in
       `notes.py` — place this one in `reports.py`):
       ```python
       def format_correction_display(report) -> str:
           corrected_str = report.updated_at.strftime('%Y-%m-%d %H:%M') if report.updated_at else '—'
           lines = [f"[#{report.id}] {report.report_type} — {report.report_date} (corrected {corrected_str})"]
           lines.append(f"  {report.correction_note or '(no note)'}")
           return "\n".join(lines)
       ```
     - Empty-results message (Design Rule 15) unchanged and generic
       regardless of window: `"[yellow]No corrected reports
       found.[/yellow]"` (keep as `console.print`, not `click.echo` —
       this is the one line that stays Rich-styled since it's not part
       of the block display).
  6. Update the command docstring/`--help` examples to include the four
     new flags and the default-window behavior, following the existing
     docstring's `\b` example-block convention — mirror `notes_list`'s
     docstring phrasing ("Default behavior (no flags): ... When --search
     is provided without --date, no window is applied...").
- **Tests:** new file `tests/test_reports_corrections.py`, pytest-style
  with the `db_session` fixture (mirrors `test_notes_list.py`'s pattern
  per recon Section 5 Q2). **Read Design Rule 16 before writing any test
  that depends on `updated_at` ordering:**
  - `test_default_window_applied` — create corrections inside and outside
    the last 7 days (by `updated_at`), assert only the in-window ones
    return by default
  - `test_search_lifts_window` — create a match older than 7 days, assert
    `--search` alone still returns it
  - `test_type_alone_does_not_lift_window` — create a `--type`-matching
    correction older than 7 days, assert `--type` alone excludes it
  - `test_type_invalid_value_errors` — assert an unrecognized `--type`
    value errors clearly (per Design Rule 10 / Gate 2 step 2), not a
    silent empty result
  - Regression, wherever `reports_list`'s existing `--type` test lives
    (Gate 2 step 2) — confirm `reports list --type <bogus>` still errors
    identically after `_report_list_impl` is refactored onto
    `_validate_report_type()`
  - `test_date_lifts_window` — explicit `--date` on an old date still
    returns that report regardless of the 7-day floor
  - `test_default_limit_applied` — create 25 in-window corrected reports,
    assert exactly 20 returned by default
  - `test_limit_override`
  - `test_all_flag_bypasses_window_and_limit` — create corrections both
    outside the 7-day window and beyond the 20-row limit, assert `--all`
    returns everything
  - `test_search_with_explicit_limit`
  - `test_no_note_displays_placeholder` — assert `(no note)` appears for
    a `correction_note IS NULL` row
  - `test_sort_order_is_updated_at_not_report_date` — CLI-level version
    of the Gate 1 sort test; scramble `report_date` vs `updated_at`
    ordering in the fixture, per Design Rule 16
  - `test_no_results_message` — empty window returns the generic message,
    not a special "empty week" variant
  - `test_help_output` — snapshot the four new flags and the default-
    window description appear in `--help`
- **Version bump:** `reports.py` v2.13 -> v2.14
- **Human approval checkpoint:** Ray runs `workmain reports corrections`
  live (with real corrected-report data) and confirms display shape,
  default window, and search/type/limit behavior before Gate 3 begins.

### Gate 3 — `reports show <id>` Diff Extension

- **Files:** `workmain/cli/commands/reports.py`
- **Changes:** In `report_show()`, ID path only (inside the `try:
  report_id = int(target)` block), after the existing `content` `Panel`
  and before the existing `correction_note` line, insert:
  ```python
  if report.corrected_content:
      console.print(Panel(
          report.corrected_content,
          title="[bold]Corrected Version[/bold]",
          border_style="yellow"
      ))
  ```
  No change to the `correction_note` line, the filename path, or any
  other part of the function.
- **Tests:** `tests/test_report_history.py`, `TestReportView` class —
  new tests alongside `test_show_displays_correction_note_when_set`:
  - `test_show_displays_corrected_content_when_present`
  - `test_show_omits_corrected_panel_when_corrected_content_is_null` —
    confirms today's behavior (content + note only) is unchanged for
    reports with no `corrected_content`
  - `test_show_displays_both_panels_and_note_together` — a report with
    all three fields populated, asserting panel order (content, then
    corrected, then note line)
- **Version bump:** `reports.py` v2.14 -> v2.15. `__version__.py`
  `1.25.0` -> `1.25.1`. `CHANGELOG.md` entry added for this hotfix
  (files touched, decisions applied, final test count — baseline is 815
  passing per `__version__.py` v1.25.0).
- **Human approval checkpoint:** Ray runs `workmain reports show <id>`
  live against a known corrected report and confirms both panels render
  correctly before the branch is merged.

## Acceptance Criteria

Live verification required for all — passing tests alone do not close
these, per standing project rule.

- [ ] AC1 — `workmain reports corrections` with no flags shows only
      corrections from the last 7 days (by `updated_at`), sorted by
      correction recency, in the new block display format — no Rich
      Table, no truncated notes
- [ ] AC2 — `workmain reports corrections --search <term>` returns
      matching reports regardless of age (window lifted), still capped
      at the default/explicit limit
- [ ] AC3 — `workmain reports corrections --type <report_type>` alone
      (no search, no date) still respects the 7-day window
- [ ] AC4 — `workmain reports corrections --limit N` returns at most N
      results within whatever window/search scope is active
- [ ] AC5 — `workmain reports corrections --all` returns every corrected
      report, unbounded by window or limit
- [ ] AC6 — `workmain reports corrections --date DATE` (single date)
      still works exactly as before this hotfix, and lifts the window
- [ ] AC7 — a corrected report with no `correction_note` displays
      `(no note)`, never blank
- [ ] AC8 — `workmain reports show <id>` for a report with non-null
      `corrected_content` displays both the original content panel and a
      labeled "Corrected Version" panel
- [ ] AC9 — `workmain reports show <id>` for a corrected report with
      `corrected_content IS NULL` displays exactly as it did before this
      hotfix (content + note only, no empty second panel)
- [ ] AC10 — `reports_corrections` contains no direct
      `session.query(Report)` call — verified by reading the merged
      source, not just by tests passing
- [ ] AC11 — `workmain reports corrections --type <bogus value>` errors
      clearly, matching `reports_list`'s validation behavior — never a
      silent empty result

## Test Plan

- `tests/test_report_correction.py` — `test_get_filtered_search_matches_correction_note_only` — proves search never matches `content`/`corrected_content` — fixture must set a search term present in `content` but absent from `correction_note`, and assert zero results
- `tests/test_report_correction.py` — `test_get_filtered_orders_by_updated_at_desc` — fixture must set `report_date` and `updated_at` in deliberately opposite order across rows (set at construction, per Design Rule 16), so the test fails if sort reverts to `report_date`
- `tests/test_reports_corrections.py` — `test_default_window_applied` — proves the core new behavior; fixture must include at least one correction just inside and one just outside the 7-day boundary
- `tests/test_reports_corrections.py` — `test_type_alone_does_not_lift_window` — proves Design Rule 3; an old, type-matching row must be excluded
- `tests/test_reports_corrections.py` — `test_type_invalid_value_errors` — proves Design Rule 10; assert an error, not zero rows
- `tests/test_reports_corrections.py` — `test_all_flag_bypasses_window_and_limit` — create corrections both outside the window and beyond the limit, assert `--all` returns all of them
- `tests/test_report_history.py` — `test_show_omits_corrected_panel_when_corrected_content_is_null` — regression guard for existing `reports show` behavior on non-diff reports

## Backlog Item Update (for `FEATURE_BACKLOG.md`, verbatim on approval)

```
#### Item 56 — workmain reports corrections Listing Command
**Status:** Complete
**Priority:** Low
**Effort:** ~1-2 hours (original) + this hotfix
**Added:** 20260626
**Target Phase:** Between-Phase Integration Sprint (pre-Phase 14)
**Description:** Extends the v1.24.0 single-date `reports corrections`
listing with a default 7-day window (by updated_at), search
(correction_note only, lifts the window), validated type filter (does
not lift the window), configurable limit, and an unbounded --all bypass
— mirroring notes_list's window/limit/lift mechanics directly. Fixes
sort order to correction recency (updated_at) instead of report_date;
moves display off a truncated Rich Table onto a full-text block format
matching notes list. Adds ReportsRepository.get_filtered(). Separately
extends `reports show <id>` to render corrected_content alongside
content when present, closing the diff/comparison gap identified during
this item's recon (see RECON_SPEC_REPORT_CORRECTION_DATA_INTEGRITY_20260717.md
— original content was never at risk; the gap was display-only).
**Acceptance Criteria:** See spec `HOTFIX_ITEM56_REPORTS_CORRECTIONS_SPEC_v1_2.md`.
**Files Affected:**
- `workmain/cli/commands/reports.py`
- `workmain/database/repositories/reports_repo.py`
```

---

*Ready for Role 3 (Claude Code / Sonnet) implementation. Paste this
document — not the planning-chat review history — as the opening message
of a fresh Claude Code / Sonnet session.*
