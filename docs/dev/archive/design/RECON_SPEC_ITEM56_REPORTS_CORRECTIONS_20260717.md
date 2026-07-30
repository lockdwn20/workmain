WorkmAIn
RECON_SPEC_ITEM56_REPORTS_CORRECTIONS v1.0
20260717

# Purpose

Gate 0 recon for Backlog Item #56 (`workmain reports corrections`). This is
recon only — no code changes, no fixes, no architectural decisions, no
proposed implementations. Report what exists today, as it exists today.
The output will be used in a separate Role 1 (Claude Desktop) planning
session to write the implementation spec.

Do not modify any files. Do not propose solutions.

---

# Output

Save this document, verbatim as pasted into this session, to
`docs/dev/design/RECON_SPEC_ITEM56_REPORTS_CORRECTIONS_20260717.md` if it
is not already present at that path. Then append your findings directly
to the end of this same file, below the `## Findings` heading at the
bottom — do not create a separate output file, do not use a different
name or location. Do not edit any other files.

---

# Background (for context only — verify, don't assume)

`workmain reports corrections` currently supports only `-d/--date`. This
recon covers what's needed to add `-s/--search`, `-n/--limit`, `--type`,
`--all`, and a display change from a truncated Rich Table to a
`notes list`-style scannable block format. Date-range filtering is
explicitly OUT of scope for this round — do not investigate it.

---

# Section 1 — `reports_corrections` Command (current state)

**File:** `workmain/cli/commands/reports.py`

1. Full `--help` output, verbatim.
2. Full Click command signature including the decorator stack — every
   option/argument with flags, type, default, required/optional status,
   help text, exactly as declared in source.
3. Complete function body, verbatim, in a fenced code block. Confirm this
   is the complete function (definition through final line) — do not
   truncate or elide any block.
4. Current display logic: is it a Rich Table (as documented) or something
   else? Quote the exact table/column construction code.
5. Confirm current sort order (reverse chronological — by what field
   exactly? `corrected_at`? `updated_at`? Quote the actual query/sort
   line).

---

# Section 2 — `notes list` Display Function (Reference Pattern)

Since the new `reports corrections` display is intended to mirror
`notes list`'s output shape, quote the exact function(s) responsible for
that rendering.

**File:** `workmain/cli/commands/notes.py`

1. Full `--help` output for `notes list`, verbatim (confirm it still
   matches: default last 7 days, limit 20, most recent first, with
   `--meeting`/`--search` lifting the date constraint when `--date` is
   absent).
2. The exact function(s) that build the sectioned/block display (date
   headers, separators, full-text body) — full body verbatim, not a
   paraphrase.
3. The exact logic that lifts the default date-window bound when
   `--meeting` or `--search` is supplied without `--date` — quote the
   conditional verbatim, not a description of it.
4. Full Click command signature for `notes list` (all options, in
   decorator form) for short-form/long-form cross-reference.

---

# Section 3 — Repository Layer

**File:** likely `workmain/database/repositories/reports_repo.py` — confirm
actual filename/class name.

1. Full public API of the reports repository class (method signatures
   only, with a one-line description of what each does).
2. For any method currently used by `reports_corrections` — full body,
   verbatim.
3. Does any existing method support: text search (ILIKE or full-text) on
   `correction_note`? Filtering by `report_type`? A configurable row
   limit? For each: state whether it exists today or would need to be
   added. Do not design the addition — just confirm presence/absence.
4. Confirm the `Report` model's relevant columns (`workmain/database/models.py`):
   exact column names, types, nullability for `correction_note`, `status`,
   `report_type`, `report_date`, `corrected_at` (or whatever the actual
   "when corrected" timestamp column is named — do not assume it's
   `corrected_at`), `created_at`.

---

# Section 4 — CLI Standards Cross-Reference

Using `CLI_STANDARDS.md`'s short-form table (§5.3):

1. Confirm current short-form assignments for `-s` (`--search`), `-n`
   (`--limit`) elsewhere in the codebase — list every command currently
   using each, to confirm no conflict when added to `reports corrections`.
2. Is there an existing short form used anywhere for a report-type filter
   (`reports list` uses `-R` for `--type` per its own `--help`)? Confirm
   this is still accurate, and confirm no other command has claimed `-R`
   for something else.

---

# Section 5 — Test Coverage (current)

1. Which test file(s) currently exercise `reports_corrections`? List file
   path(s) and test function names.
2. Which test file(s) currently exercise `notes list`'s display/default
   -lifting behavior? List file path(s) and test function names — these
   are the fixtures/pattern the new corrections tests should extend.

---

# Format Notes

- Use the WorkmAIn document header convention (title, doc name + version,
  date) at the top of the output file.
- Quote source code verbatim in fenced code blocks with file path
  comments — do not paraphrase signatures, option lists, or conditionals.
- If a referenced file/method cannot be located, state that explicitly
  rather than omitting the section.
- Mark each finding CONFIRMS or CONTRADICTS against anything stated as
  "current state" in this document's Background section.
- Keep this self-contained — the reviewing session will not have live
  access to the repo, only this document.

---

## Findings

WorkmAIn
RECON_SPEC_ITEM56_REPORTS_CORRECTIONS — Findings
20260717
Appended by Claude Code / Opus (Role 2), read-only recon execution.

Factual enumeration only. No code changes, no proposed implementation, no
architectural decisions. Each finding marked CONFIRMS / CONTRADICTS against
the "current state" claims in this document's Background section.

---

### Section 1 — `reports_corrections` Command (current state)

**File:** `workmain/cli/commands/reports.py` — header **v2.13, 20260708**.
Command registered as `reports corrections` (function `report_corrections`,
decorator `@reports.command('corrections')`).

**Q1 — full `--help` output, verbatim (captured live):**

```text
Usage: workmain reports corrections [OPTIONS]

  List reports with status 'corrected'.

  Shows the correction note for each corrected report, optionally filtered to
  a single report date.

  Examples:
    workmain reports corrections
    workmain reports corrections --date 2026-05-27

Options:
  -d, --date YYYY-MM-DD  Filter by report date
  --help                 Show this message and exit.
```

**Q2 — full Click signature / decorator stack, verbatim:**

```python
# workmain/cli/commands/reports.py  (lines 593–596)
@reports.command('corrections')
@click.option('-d', '--date', 'date_str', default=None, metavar='YYYY-MM-DD',
              help='Filter by report date')
def report_corrections(date_str: Optional[str]):
```

Only one option today: `-d/--date` → dest `date_str`, `str`/optional,
`default=None`, `metavar='YYYY-MM-DD'`. No `--search`, `--limit`, `--type`,
or `--all`. **CONFIRMS** Background ("currently supports only `-d/--date`").

**Q3 — complete function body, verbatim (definition through final line, nothing elided):**

```python
# workmain/cli/commands/reports.py  (lines 593–667)
@reports.command('corrections')
@click.option('-d', '--date', 'date_str', default=None, metavar='YYYY-MM-DD',
              help='Filter by report date')
def report_corrections(date_str: Optional[str]):
    """
    List reports with status 'corrected'.

    Shows the correction note for each corrected report, optionally
    filtered to a single report date.

    \b
    Examples:
      workmain reports corrections
      workmain reports corrections --date 2026-05-27
    """
    db = get_db()
    session = db.get_session()

    try:
        filter_date = None
        if date_str:
            try:
                filter_date = date.fromisoformat(date_str)
            except ValueError:
                console.print(f"[red]✗ Invalid date: '{date_str}' — expected YYYY-MM-DD[/red]")
                raise SystemExit(1)

        q = session.query(Report).filter(Report.status == 'corrected')
        if filter_date:
            q = q.filter(Report.report_date == filter_date)

        rows = q.order_by(Report.report_date.desc(), Report.id.desc()).all()

        if not rows:
            console.print("\n[yellow]No corrected reports found.[/yellow]\n")
            return

        title = f"Report Corrections ({len(rows)})"
        if filter_date:
            title += f" — {filter_date}"

        table = Table(
            title=f"\n{title}",
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED
        )
        table.add_column("ID", style="dim", justify="right")
        table.add_column("Type", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Corrected", style="dim")
        table.add_column("Note", style="yellow")

        for r in rows:
            corrected_str = r.updated_at.strftime('%Y-%m-%d %H:%M') if r.updated_at else "—"
            note_preview = (r.correction_note or "")[:60]

            table.add_row(
                str(r.id),
                r.report_type or "—",
                str(r.report_date) if r.report_date else "—",
                corrected_str,
                note_preview or "—"
            )

        console.print(table)
        console.print()

    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]✗ Failed to list corrections: {e}[/red]")

    finally:
        session.close()
```

**Q4 — current display logic (Rich Table or otherwise):** It is a **Rich
`Table`** (`box.ROUNDED`), five columns: `ID`, `Type`, `Date`, `Corrected`,
`Note`. **CONFIRMS** Background ("truncated Rich Table"). The `Note` column
truncates `correction_note` to 60 chars: `note_preview = (r.correction_note
or "")[:60]`. Exact column construction quoted above.

Note (factual): the query filters `status == 'corrected'` but the `Note`
column shows `correction_note`, which — per the companion recon
(`RECON_SPEC_REPORT_CORRECTION_DATA_INTEGRITY`) — is populated only by the
Slack/intent path and the EOD `[e]dit` optional prompt, **not** by the CLI
`reports correct` `$EDITOR` path. So corrected rows created via `reports
correct` show `—` in the Note column despite being genuine corrections.
Reported as fact, not evaluated.

**Q5 — current sort order, exact line:**

```python
rows = q.order_by(Report.report_date.desc(), Report.id.desc()).all()
```

Sorts by **`report_date` DESC, then `id` DESC** — i.e. by the report's
subject date, not by when it was corrected. **CONTRADICTS** the implicit
"reverse chronological by correction time" reading in the Section 1 Q5
prompt: there is **no `corrected_at` column**, and the sort does **not** use
`updated_at` (the de-facto correction timestamp, which the `Corrected` column
*displays* but does not sort by). There is also **no `.limit()`** — the query
returns all corrected rows unbounded.

---

### Section 2 — `notes list` Display Function (Reference Pattern)

**File:** `workmain/cli/commands/notes.py` — header **v4.2, 20260612**.

**Q1 — full `notes list --help`, verbatim (captured live):**

```text
Usage: workmain notes list [OPTIONS]

  List notes with optional filters.

  Default behavior (no flags): last 7 days, limit 20, most recent first. When
  --meeting or --search is provided without --date, no date constraint is
  applied so the full history is searchable.

  Examples:
    workmain notes list
    workmain notes list --date today
    workmain notes list --date 2026-05-01
    workmain notes list --meeting "Team Standup"
    workmain notes list --meeting "Standup" --history
    workmain notes list --search "security review"
    workmain notes list --tags cf
    workmain notes list --tags ilo,cf
    workmain notes list --date today --tags ilo
    workmain notes list --limit 50

Options:
  -d, --date TEXT      Date filter (YYYY-MM-DD, 'today', 'yesterday')
  -m, --meeting TEXT   Filter by meeting title or ID (fuzzy match)
  -s, --search TEXT    Full-text search keyword
  -t, --tags TEXT      Filter by tags (comma-separated: ilo,cf)
  -n, --limit INTEGER  Maximum results [default: 20]
  -H, --history        Show all instances of recurring meeting (only
                       meaningful with --meeting)
  --show-ids           Show note IDs
  --help               Show this message and exit.
```

**CONFIRMS** Background ("default last 7 days, limit 20, most recent first,
with `--meeting`/`--search` lifting the date constraint when `--date` is
absent") — with one nuance made explicit under Q3 below (`--tags` does **not**
lift the window; only `--meeting` and `--search` do).

**Q2 — exact function building the sectioned/block display, verbatim.** The
display is built inline in `notes_list` (there is no separate render helper;
per-note formatting delegates to the module-level `format_note_display`).
Both are quoted.

```python
# workmain/cli/commands/notes.py  (notes_list display block, lines 882–912)
        if not note_list:
            click.echo("No notes found.")
            return

        # Build header
        if meeting_str and resolved_meeting:
            header = f"Notes for '{resolved_meeting.title}'"
            if history:
                header += " (all instances)"
        elif date_filter is not None:
            header = f"Notes for {date_filter}"
        elif search:
            header = f"Notes matching '{search}'"
        elif tags:
            header = f"Notes with tags [{tags}]"
        else:
            header = f"Notes — last 7 days"

        click.echo(f"\n{header} ({len(note_list)}):\n")
        click.echo("=" * 60)

        current_date = None
        for note in note_list:
            if note.created_date != current_date:
                if current_date is not None:
                    click.echo("=" * 60)
                click.echo(f"\n[{note.created_date}]")
                click.echo("-" * 60)
                current_date = note.created_date
            click.echo(format_note_display(note, show_id=show_ids))
            click.echo("-" * 60)
```

```python
# workmain/cli/commands/notes.py  (format_note_display, lines 82–118)
def format_note_display(note, show_id: bool = True) -> str:
    """
    Format note for display.

    Args:
        note: Note object
        show_id: Whether to show note ID (default: True — consistent with
                 meetings and time entries)

    Returns:
        Formatted string
    """
    lines = []

    # ID and timestamp
    time_str = note.created_at.strftime('%H:%M')
    if show_id:
        lines.append(f"[#{note.id}] {time_str}")
    else:
        lines.append(f"{time_str}")

    # Content
    lines.append(f"  {note.content}")

    # Tags
    if note.tags:
        lines.append(f"  Tags: {note.display_tags}")

    # Meeting
    if note.meeting:
        lines.append(f"  Meeting: {note.meeting.title} (ID: {note.meeting.id})")

    # Project
    if note.project:
        lines.append(f"  Project: {note.project.name}")

    return "\n".join(lines)
```

Display shape: header line + `===` rule; then per calendar date a `[YYYY-MM-DD]`
section header with `---` separators; each note rendered full-text (no
truncation) via `format_note_display`, followed by a `---` rule. `click.echo`
output (plain text), not a Rich Table. This is the "`notes list`-style
scannable block format" the Background references.

**Q3 — exact conditional that lifts the default date-window bound, verbatim:**

```python
# workmain/cli/commands/notes.py  (lines 865–870)
        # Default 7-day window when no meeting/search filter and no explicit date
        date_range_start = None
        date_range_end = None
        if date_filter is None and meeting_ids is None and not search:
            date_range_end = datetime.now().date()
            date_range_start = date_range_end - timedelta(days=7)
```

The 7-day window is applied **only** when `date_filter is None AND meeting_ids
is None AND not search`. So supplying `--meeting` (→ non-None `meeting_ids`)
or `--search` lifts the window; supplying **`--tags` alone does NOT lift it**
(the condition does not test `include_tags`) — a `--tags`-only query still
gets the 7-day bound. This matches the help text (which names only `--meeting`
/`--search`). **CONFIRMS**, with the `--tags` nuance surfaced as fact.

**Q4 — full Click signature for `notes list`, verbatim:**

```python
# workmain/cli/commands/notes.py  (lines 789–799)
@notes.command('list')
@click.option('--date', '-d', 'date_str', help="Date filter (YYYY-MM-DD, 'today', 'yesterday')")
@click.option('--meeting', '-m', 'meeting_str', help='Filter by meeting title or ID (fuzzy match)')
@click.option('--search', '-s', help='Full-text search keyword')
@click.option('--tags', '-t', help='Filter by tags (comma-separated: ilo,cf)')
@click.option('--limit', '-n', type=int, default=20, help='Maximum results [default: 20]')
@click.option('--history', '-H', is_flag=True, default=False,
              help='Show all instances of recurring meeting (only meaningful with --meeting)')
@click.option('--show-ids', is_flag=True, default=False, help='Show note IDs')
def notes_list(date_str: Optional[str], meeting_str: Optional[str], search: Optional[str],
               tags: Optional[str], limit: int, history: bool, show_ids: bool):
```

Cross-reference: `-d/--date`, `-m/--meeting`, `-s/--search`, `-t/--tags`,
`-n/--limit`, `-H/--history`, `--show-ids` (no short form). The actual DB
filtering is delegated to `notes_repo.get_filtered(...)` (lines 872–880).

---

### Section 3 — Repository Layer

**File:** `workmain/database/repositories/reports_repo.py` — class
**`ReportsRepository`**, header **v1.4, 20260611**. Module singleton accessor:
`get_reports_repository(session)`.

**Q1 — full public API (signatures + one-line description):**

```python
# workmain/database/repositories/reports_repo.py
def __init__(self, session: Session)
    # Store session on the repo instance.

def create(self, report_type, report_date, content, ai_provider, ai_model,
           prompt_tokens, completion_tokens, total_tokens, cost,
           generation_time, file_path=None, client_id=None) -> Report
    # Insert a new report row (writes content + report_metadata); commits.

def get_by_id(self, report_id: int) -> Optional[Report]
    # Fetch one report by primary key.

def list_reports(self, report_type=None, start_date=None, end_date=None,
                 limit=10, status=None) -> List[Report]
    # List reports filtered by type / date range / status; ordered by
    # created_at DESC; capped by limit.

def get_confirmed_dailies(self, start_date, end_date) -> List[Report]
    # daily_internal reports with status in ('confirmed','corrected') for a
    # date range; ordered report_date ASC (weekly aggregation source).

def set_correction_note(self, report_id: int, note: str) -> None
    # Strip + write correction_note for one report; no-op on empty/missing.

def get_cost_summary(self, start_date=None, end_date=None) -> Dict[str, Any]
    # Aggregate cost/token totals grouped by type and provider.

def get_costs_by_date(self, start_date=None, end_date=None) -> Dict[str, float]
    # Map report_date → summed cost.

def delete(self, report_id: int) -> bool
    # Delete one report by id; True if found/deleted.
```

**Q2 — full body of any method currently used by `reports_corrections`:**
**None.** `report_corrections` (Section 1) does **not** call any
`ReportsRepository` method — it queries the ORM directly
(`session.query(Report).filter(Report.status == 'corrected')...`). There is
no repository method to quote for this command. (**CONTRADICTS** the Section 3
prompt's implicit assumption that a repository method backs the command.)

**Q3 — support for the three needs (presence/absence only):**

- **Text search (ILIKE / full-text) on `correction_note`:** **ABSENT.** No
  method in `ReportsRepository` performs any text/`ILIKE` search on
  `correction_note` (or on `content`). Would need to be added.
- **Filtering by `report_type`:** **PRESENT** — `list_reports(report_type=...)`
  applies `query.filter(Report.report_type == report_type)`. (Not currently
  wired to `reports corrections`, which does its own ORM query without a type
  filter.)
- **Configurable row limit:** **PRESENT** — `list_reports(limit=...)` applies
  `.limit(limit)` (default 10). (Also not wired to `reports corrections`,
  which is unbounded.)

Reference point (not part of reports repo): the analogous scannable-list
command `notes list` uses **`NotesRepository.get_filtered(...)`**, which does
support `search=` and `limit=` and date-range params (notes.py lines 872–880).
That is the repository shape the corrections feature would parallel; the
reports repo has no equivalent combined-filter method today. Stated as fact.

**Q4 — `Report` model relevant columns, verbatim (`workmain/database/models.py`, Report model, header notes columns added in models v2.x):**

```python
# workmain/database/models.py  (class Report, lines 388–425, relevant columns)
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)

    report_type = Column(String(50), nullable=False)   # 'daily_internal', 'weekly_client', etc.
    report_date = Column(Date, nullable=False)
    content = Column(Text, nullable=False)

    report_metadata = Column('metadata', JSON, nullable=True)

    # Status tracking and correction (Phase 12)
    status            = Column(String(20), nullable=False, default='unconfirmed')
    corrected_content = Column(Text, nullable=True)
    correction_note   = Column(Text, nullable=True)  # Phase 13 placeholder — Ollama intent parser

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

Column facts:
- `correction_note` — `Text`, **nullable** (no default).
- `status` — `String(20)`, **NOT NULL**, default `'unconfirmed'`.
- `report_type` — `String(50)`, **NOT NULL**.
- `report_date` — `Date`, **NOT NULL**.
- **`corrected_at`** — **does not exist.** There is no dedicated
  "when corrected" column. The de-facto correction timestamp is `updated_at`
  (`DateTime`, `default=datetime.now`, `onupdate=datetime.now`) — set
  explicitly by every correction path and also auto-touched on any update.
  **CONTRADICTS** the Section 3 Q4 candidate name `corrected_at`.
- `created_at` — `DateTime`, `default=datetime.now`.

---

### Section 4 — CLI Standards Cross-Reference

Source: `docs/CLI_STANDARDS.md` §5.3 (header **v2.5, 20260529** era; reserved
short-form table). Verified against live `@click.option` declarations in
`workmain/cli/commands/`.

**Q1 — current short-form assignments for `-s` and `-n`:**

`-s` → `--search` — reserved "Filter commands" (§5.3 table). Live in-code
users (all `--search`, no conflict):
```text
tasks.py:166   tasks ... --search/-s   (Filter by keyword — note content)
tasks.py:265   tasks ... --search/-s   (Filter by keyword)
notes.py:792   notes list  --search/-s (Full-text search keyword)
notes.py:963   notes today --search/-s (Filter today's notes by keyword)
meetings.py:403 meetings ... --search/-s (Search meetings by title)
meetings.py:778 meetings ... --search/-s (Search meetings by title)
```
Every `-s` in the codebase maps to `--search`. **No conflict** for adding
`-s/--search` to `reports corrections`. (Historical note, §5.3 line 360:
`eod --skip` was reassigned off `-s` to `-S` precisely to keep `-s` = search.)

`-n` → `--limit` — reserved "List commands" (§5.3 table). Live in-code users:
```text
tasks.py:169    --limit/-n   (default 20)
tasks.py:419    --limit/-n   (default None)
reports.py:476  reports list    --limit/-n (default 10)
reports.py:497  reports history --limit/-n (default 10)
reports.py:805  reports costs   --limit/-n (default 20)
notes.py:794    notes list   --limit/-n (default 20)
notes.py:1031   notes search --limit/-n (default 10)
notes.py:1071   notes costs  --limit/-n (default 20)
meetings.py:404  --limit/-n  (default 20)
meetings.py:1764 --limit/-n  (default 20)
```
All map to `--limit` **except one documented exception:**
`meetings.py:819  meetings upcoming --days/-n` uses `-n` for `--days` (per
§5.3 history v1.5: "live code uses `--days/-n`, already compliant"). That is
a different command group and does not affect `reports corrections`. **No
conflict** for adding `-n/--limit` to `reports corrections`.

**Q2 — report-type filter short form (`-R`):**

`-R` → `--type`, reserved specifically for `reports list` (§5.3 table line
364: "Uppercase; `-T` already taken by `--time`; less-common filter").
Live in-code users — **all in reports.py, all `--type`/`report_type`:**
```text
reports.py:477  reports list    --type/-R
reports.py:498  reports history --type/-R
reports.py:802  reports costs   --type/-R
```
`-R` is used **only** for `--type` and nowhere else in the codebase — no
other command has claimed it. **CONFIRMS** Background/prompt (`reports list`
uses `-R` for `--type`). No conflict for reusing `-R/--type` on `reports
corrections`. (Per §5.3, `--type`'s valid values would still be the report
types — factual, not a design call.)

---

### Section 5 — Test Coverage (current)

**Q1 — test file(s) exercising `reports_corrections`:** **None.** No test in
`tests/` invokes the `reports corrections` command (no `CliRunner` call with
`['reports','corrections']` or `report_corrections`, and no assertion against
its output). Grep for the command across `tests/` returns zero hits.
`reports corrections` (added v2.13, Item #56 Gate 6 partial) has **zero
direct test coverage today.** Tests that mention "correction" exercise
*different* surfaces:
- `tests/test_action_executor.py::test_correct_report_writes_correction_note`
  (and `_empty_correction_string`, `_missing_correction_field`) — the
  `action_executor` write path, not the listing command.
- `tests/test_report_history.py::TestReportView::test_show_displays_correction_note_when_set`
  — `reports show` rendering of `correction_note`, not `reports corrections`.
- `tests/test_report_correction.py::test_original_content_preserved_after_correction`
  and the `TestListReportsStatusFilter` class — repo/model behavior, not the
  listing command.
- `tests/test_orchestration.py::test_t6_summary_posted_after_write_correction_note`
  — T6 Slack summary, unrelated to the command.

**Q2 — test file(s) exercising `notes list` display / default-lifting:**
**`tests/test_notes_list.py`** is the pattern to extend. Relevant tests:
```text
tests/test_notes_list.py:
  test_exact_date_match / test_exact_date_no_results / test_date_filter_overrides_range
  test_range_includes_boundary_dates / test_range_start_only_excludes_before
  test_meeting_filter_returns_linked_notes / test_meeting_filter_empty_meeting_returns_empty
  test_multiple_meeting_ids
  test_search_returns_matching_note
  test_search_applies_no_date_constraint      ← the default-window-lift test
  test_single_tag_match / test_multi_tag_uses_or_logic
  test_limit_caps_results
  test_results_ordered_most_recent_first
  test_date_and_tag_and_logic / test_meeting_and_date_combined
  test_history_without_meeting_shows_warning
  test_invalid_date_format_prints_error
  test_sentinel_date_returns_no_notes
  test_deprecated_date_alias_prints_warning / _search_alias_ / _meeting_alias_
  test_search_flag_accepted_no_error / test_search_short_form_accepted
```
`test_search_applies_no_date_constraint` (line 214) is the direct analogue of
the window-lift behavior (Section 2 Q3). The repo-level `get_filtered` search
pattern is also exercised in `tests/test_task_lifecycle.py`
(`test_get_filtered_search`, `test_get_filtered_limit`, etc.), using the
`db_session` fixture — the same fixture pattern new corrections tests would
use.

---

### Header Version Summary

| File | Header version | Date |
|------|----------------|------|
| `workmain/cli/commands/reports.py` | v2.13 | 20260708 |
| `workmain/cli/commands/notes.py` | v4.2 | 20260612 |
| `workmain/database/repositories/reports_repo.py` | v1.4 | 20260611 |
| `workmain/database/models.py` (Report model) | columns confirmed (see S3 Q4) | — |
| `docs/CLI_STANDARDS.md` | v2.5+ (§5.3 reserved table) | — |

### CONFIRMS / CONTRADICTS Roll-up

- **CONFIRMS:** `reports corrections` supports only `-d/--date` today (S1 Q2);
  display is a truncated Rich Table, 5 cols, Note truncated to 60 chars
  (S1 Q4); `notes list` help/default-lift behavior as described, with block
  display + `format_note_display` (S2); `-s/--search`, `-n/--limit`,
  `-R/--type` are cleanly reserved with no conflicts for reuse on `reports
  corrections` (S4).
- **CONTRADICTS / QUALIFIES:** `reports corrections` sorts by `report_date`
  DESC + `id` DESC — **not** by a correction timestamp; there is **no
  `corrected_at` column** and the sort does not use `updated_at` (S1 Q5,
  S3 Q4). `reports corrections` uses a **direct ORM query, not a repository
  method** (S3 Q2). The reports repo has **no text-search method** on
  `correction_note` (S3 Q3). `reports corrections` has **zero test coverage**
  (S5 Q1). Nuance on the lift condition: `--tags` alone does **not** lift the
  `notes list` 7-day window — only `--meeting`/`--search` do (S2 Q3).

_End of findings._
