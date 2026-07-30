WorkmAIn
ACTION_AUDIT_TRACK1_ITEMS4-5 v1.0
20260623

Recon output for Phase 13 Sprint 3 intent parser audit.
Track 1, Items 4 & 5: `confirm_report` ↔ `workmain reports confirm` and
`correct_report` ↔ `workmain reports correct`.

No code was modified. No recommendations are made. This is a factual
enumeration for use in a separate planning session.

> **Note on spec's Preliminary Step:** The spec instructed `git mv` to rename
> `intent-parser-audit-20260612` → `intent-parser-audit`. `docs/dev/` is
> gitignored (local-only, untracked). The rename was performed with a
> regular `mv`. No commit was made — there are no git-tracked changes.

---

# A. CLI Command Discovery

## A.1. `workmain reports --help`

```
Usage: workmain reports [OPTIONS] COMMAND [ARGS]...

  Generate and manage reports.

Options:
  --help  Show this message and exit.

Commands:
  confirm  Mark a report as confirmed (attest accuracy).
  correct  Open editor to correct a report's content.
  costs    Show per-report cost breakdown with provider and token details.
  history  List past generated reports (alias for 'list').
  list     List generated reports (DB-backed).
  preview  Preview report prompts without generating (no AI cost).
  resend   Recreate an email draft from a previously stored report.
  save     Generate report with AI and save to staging/reports/.
  send     Generate report and send to Outlook via email pipeline.
  show     Display a report by database ID or filename.
```

## A.2. All Subcommand Help Outputs

```
# workmain reports confirm --help
Usage: workmain reports confirm [OPTIONS] IDENTIFIER

  Mark a report as confirmed (attest accuracy).

  IDENTIFIER is a report ID or date string (YYYY-MM-DD, today, yesterday).
  Looks up the most recent daily_internal for the given date.

  Examples:
    workmain reports confirm 42
    workmain reports confirm today
    workmain reports confirm 2026-05-27

Options:
  --help  Show this message and exit.
```

```
# workmain reports correct --help
Usage: workmain reports correct [OPTIONS] IDENTIFIER

  Open editor to correct a report's content. Original content is preserved;
  correction stored in corrected_content field.

  IDENTIFIER is a report ID or date string (YYYY-MM-DD, today, yesterday).

  Examples:
    workmain reports correct 42
    workmain reports correct today
    workmain reports correct 2026-05-27

Options:
  --help  Show this message and exit.
```

```
# workmain reports list --help
Usage: workmain reports list [OPTIONS]

  List generated reports (DB-backed).

  Examples:
    workmain reports list
    workmain reports list -n 20
    workmain reports list --type daily_internal
    workmain reports list --status unconfirmed
    workmain reports list --status confirmed --type daily_internal

Options:
  -n, --limit INTEGER  Number of reports to show
  -R, --type TEXT      Filter by report type (daily_internal, weekly_client)
  --status TEXT        Filter by status: unconfirmed, confirmed, corrected,
                       all [default: all]
  --help               Show this message and exit.
```

```
# workmain reports history --help
Usage: workmain reports history [OPTIONS]

  List past generated reports (alias for 'list').

  Examples:
    workmain reports history
    workmain reports history --limit 3
    workmain reports history --type daily_internal
    workmain reports history --status confirmed

Options:
  -n, --limit INTEGER  Number of rows to show
  -R, --type TEXT      Filter by report type (daily_internal, weekly_client)
  --status TEXT        Filter by status: unconfirmed, confirmed, corrected,
                       all [default: all]
  --help               Show this message and exit.
```

```
# workmain reports show --help
Usage: workmain reports show [OPTIONS] TARGET

  Display a report by database ID or filename.

  TARGET can be an integer database ID or a report filename.

  Examples:
    workmain reports show 42
    workmain reports show daily_internal_2026-03-05.md

Options:
  --help  Show this message and exit.
```

```
# workmain reports save --help
Usage: workmain reports save [OPTIONS] TEMPLATE

  Generate report with AI and save to staging/reports/.

  Examples:
    workmain reports save daily_internal
    workmain reports save weekly_client --provider gemini
    workmain reports save daily_internal --date 2026-03-30

Options:
  --provider [claude|gemini]  Override AI provider
  -d, --date YYYY-MM-DD       Generate report for this date instead of today
  --help                      Show this message and exit.
```

```
# workmain reports send --help
Usage: workmain reports send [OPTIONS] TEMPLATE

  Generate report and send to Outlook via email pipeline.

  Requires OAuth authentication — see docs/OAUTH_SETUP.md Use 'workmain
  reports save <template>' to generate and save locally, then 'workmain email
  save <template>' to create an email draft.

Options:
  --help  Show this message and exit.
```

```
# workmain reports preview --help
Usage: workmain reports preview [OPTIONS] TEMPLATE

  Preview report prompts without generating (no AI cost).

  Examples:
    workmain reports preview daily_internal
    workmain reports preview weekly_client --provider claude

Options:
  --provider [claude|gemini]  Override AI provider
  --help                      Show this message and exit.
```

```
# workmain reports resend --help
Usage: workmain reports resend [OPTIONS] ID

  Recreate an email draft from a previously stored report.

  Stages report content to staging/reports/ then invokes the email pipeline.

  Example:
    workmain reports resend 42

Options:
  --help  Show this message and exit.
```

```
# workmain reports costs --help
Usage: workmain reports costs [OPTIONS]

  Show per-report cost breakdown with provider and token details.

  Shows each individual report's cost. Defaults to the current calendar month.
  For aggregate totals grouped by provider and type, use 'workmain providers
  costs'.

  Examples:
    workmain reports costs
    workmain reports costs -P claude
    workmain reports costs -R daily_internal
    workmain reports costs -M 2026-05
    workmain reports costs -b 2026-05-01 -e 2026-05-15
    workmain reports costs --all -n 50

Options:
  -P, --provider [claude|gemini]  Filter by AI provider
  -R, --type [daily_internal|weekly_client]
                                  Filter by report type
  -n, --limit INTEGER             Max rows to display
  -d, --date YYYY-MM-DD           Show costs for a single day
  -b, --start YYYY-MM-DD          Range start date (inclusive)
  -e, --end YYYY-MM-DD            Range end date (requires --start)
  -M, --month YYYY-MM             Filter by calendar month
  --all                           Show all history (no date filter)
  --help                          Show this message and exit.
```

## A.3. Source-Level Command Inventory

File: `workmain/cli/commands/reports.py`

```python
# workmain/cli/commands/reports.py (decorator → function name)
@reports.command('preview')   → def report_preview
@reports.command('save')      → def report_save
@reports.command('send')      → def report_send
@reports.command('list')      → def report_list
@reports.command('history')   → def report_history
@reports.command('confirm')   → def report_confirm
@reports.command('correct')   → def report_correct
@reports.command('show')      → def report_show
@reports.command('resend')    → def report_resend
@reports.command('costs')     → def report_costs
```

Standalone CLI commands exist for both `confirm` and `correct`.

---

# B. CLI Command Implementation

## B.1. Click Command Signatures

### `report_confirm` — `workmain/cli/commands/reports.py:511`

```python
@reports.command('confirm')
@click.argument('identifier')
def report_confirm(identifier: str):
```

One positional argument: `identifier` (string, required). No options.

### `report_correct` — `workmain/cli/commands/reports.py:545`

```python
@reports.command('correct')
@click.argument('identifier')
def report_correct(identifier: str):
```

One positional argument: `identifier` (string, required). No options.

## B.2. Command Body Logic

### `report_confirm` — `workmain/cli/commands/reports.py:513`

Full function body:

```python
# workmain/cli/commands/reports.py:513-542
def report_confirm(identifier: str):
    """
    Mark a report as confirmed (attest accuracy).

    IDENTIFIER is a report ID or date string (YYYY-MM-DD, today, yesterday).
    Looks up the most recent daily_internal for the given date.

    \b
    Examples:
      workmain reports confirm 42
      workmain reports confirm today
      workmain reports confirm 2026-05-27
    """
    db = get_db()
    session = db.get_session()
    try:
        report = _resolve_report(session, identifier)
        if report.status in ('confirmed', 'corrected'):
            console.print(
                f"[yellow]Report is already {report.status} — no change made.[/yellow]"
            )
            return
        report.status = 'confirmed'
        report.updated_at = datetime.now()
        session.commit()
        console.print(
            f"[green]✓ Report confirmed:[/green] {report.report_type} {report.report_date}"
        )
    finally:
        session.close()
```

**`_resolve_report` helper — `workmain/cli/commands/reports.py:88`:**

```python
# workmain/cli/commands/reports.py:88-136
def _resolve_report(session, identifier: str):
    if identifier.isdigit():
        report = session.query(Report).filter(Report.id == int(identifier)).first()
        if not report:
            console.print(f"[red]✗ No report found with ID {identifier}[/red]")
            raise SystemExit(1)
        return report

    if identifier == 'today':
        target_date = datetime.now().date()
    elif identifier == 'yesterday':
        target_date = datetime.now().date() - timedelta(days=1)
    else:
        try:
            target_date = datetime.strptime(identifier, '%Y-%m-%d').date()
        except ValueError:
            console.print(
                f"[red]✗ Invalid identifier '{identifier}'. "
                "Use a report ID or date (YYYY-MM-DD, today, yesterday).[/red]"
            )
            raise SystemExit(1)

    report = (
        session.query(Report)
        .filter(Report.report_date == target_date)
        .filter(Report.report_type == 'daily_internal')
        .order_by(Report.id.desc())
        .first()
    )
    if not report:
        report = (
            session.query(Report)
            .filter(Report.report_date == target_date)
            .order_by(Report.id.desc())
            .first()
        )
    if not report:
        console.print(f"[red]✗ No report found for {target_date}[/red]")
        raise SystemExit(1)
    return report
```

**`report_confirm` body breakdown:**

- Derived/computed values: none.
- Defaults applied in function body: none.
- Interactive prompts: none.
- Validation: checks `report.status in ('confirmed', 'corrected')` → prints warning and returns with no write.
- DB writes:
  - `report.status = 'confirmed'`
  - `report.updated_at = datetime.now()`
  - `session.commit()`
- Tables modified: `reports` only.
- Calls to eod_workflow functions: none.
- Calls to functions outside local module: `get_db()` (connection), `_resolve_report()` (local helper).

---

### `report_correct` — `workmain/cli/commands/reports.py:547`

Full function body:

```python
# workmain/cli/commands/reports.py:547-585
def report_correct(identifier: str):
    """
    Open editor to correct a report's content.
    Original content is preserved; correction stored in corrected_content field.

    IDENTIFIER is a report ID or date string (YYYY-MM-DD, today, yesterday).

    \b
    Examples:
      workmain reports correct 42
      workmain reports correct today
      workmain reports correct 2026-05-27
    """
    db = get_db()
    session = db.get_session()
    try:
        report = _resolve_report(session, identifier)
        current = report.corrected_content if report.corrected_content else report.content
        edited = _edit_in_editor(current or '')
        if edited is None:
            return
        if edited == current:
            console.print("[yellow]No changes detected — report status unchanged.[/yellow]")
            return
        report.corrected_content = edited
        report.status = 'corrected'
        report.updated_at = datetime.now()
        session.commit()
        fp = (report.report_metadata or {}).get('file_path')
        if fp:
            try:
                Path(fp).write_text(edited, encoding='utf-8')
            except Exception as stage_err:
                console.print(f"[yellow]⚠ DB saved; staging file update failed: {stage_err}[/yellow]")
        console.print(
            f"[green]✓ Report correction saved:[/green] {report.report_type} {report.report_date}"
        )
    finally:
        session.close()
```

**`_edit_in_editor` helper — `workmain/cli/commands/reports.py:139`:**

```python
# workmain/cli/commands/reports.py:139-168
def _edit_in_editor(content: str) -> Optional[str]:
    editor = os.environ.get('EDITOR')
    if not editor:
        console.print(
            "[red]✗ $EDITOR is not set. "
            "Export EDITOR=vim (or nano, etc.) and retry.[/red]"
        )
        return None

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            tmp_path = f.name
            f.write(content)
        subprocess.run([editor, tmp_path], check=True)
        return Path(tmp_path).read_text()
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Editor failed: {e}[/red]")
        return None
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
```

**`report_correct` body breakdown:**

- Derived/computed values:
  - `current = report.corrected_content if report.corrected_content else report.content`
    (pre-populates editor with prior corrected content if one exists, otherwise original content)
- Defaults applied in function body: none.
- Interactive prompts: `_edit_in_editor(current or '')` opens `$EDITOR` via subprocess. This is the sole mechanism for capturing the corrected content — there is no `click.prompt` or `click.confirm`.
- Validation / early exits:
  - `edited is None` → `$EDITOR` unset or editor subprocess failed; function returns with no write.
  - `edited == current` → no change detected; prints warning and returns with no write.
- DB writes:
  - `report.corrected_content = edited`
  - `report.status = 'corrected'`
  - `report.updated_at = datetime.now()`
  - `session.commit()`
- Non-DB write (best-effort): `Path(fp).write_text(edited, encoding='utf-8')` to staging file
  path from `report.report_metadata.get('file_path')`. Exception is caught and printed; DB
  state is already committed before this attempt.
- Tables modified: `reports` only. No write to `notes` or `time_entries`.
- `correction_note` field: NOT set by this command.
- Calls to eod_workflow functions: none.
- Calls to functions outside local module: `get_db()`, `_resolve_report()` (local), `_edit_in_editor()` (local).

---

# C. Action Executor Handlers

File: `workmain/orchestration/action_executor.py`

## C.1. `_execute_confirm_report`

```python
# workmain/orchestration/action_executor.py:214-229
def _execute_confirm_report(self, action: dict) -> ActionResult:
    report_type = action.get("report_type", "daily_internal")
    report = self._get_latest_report(report_type)
    if report is None:
        return ActionResult(
            success=False,
            message=f"No {report_type.replace('_', ' ')} found for today.",
            error="no_report",
        )
    report.status = "confirmed"
    self.session.commit()
    return ActionResult(
        success=True,
        message=f"✓ {report_type.replace('_', ' ').title()} confirmed.",
        entity_id=report.id,
    )
```

**`_get_latest_report` helper — `workmain/orchestration/action_executor.py:313`:**

```python
# workmain/orchestration/action_executor.py:313-321
def _get_latest_report(self, report_type: str):
    """Return today's most recent report of the given type, or None."""
    from workmain.database.models import Report
    return (
        self.session.query(Report)
        .filter(Report.report_type == report_type, Report.report_date == date.today())
        .order_by(Report.id.desc())
        .first()
    )
```

**Field reads:**
- `action.get("report_type", "daily_internal")` — defaults to `"daily_internal"` if absent.

**Repository methods called:**
- `self._get_latest_report(report_type)` — direct ORM query on `Report` model:
  `WHERE report_type = <report_type> AND report_date = date.today() ORDER BY id DESC LIMIT 1`

**DB writes:**
- `report.status = "confirmed"`
- `self.session.commit()`
- `report.updated_at` is NOT set explicitly. (Model has `onupdate=datetime.now`; whether
  the ORM triggers this depends on whether the column is included in the UPDATE statement.)

**EOD workflow calls:** None.

**Other tables modified:** None. Only `reports`.

---

## C.2. `_execute_correct_report`

```python
# workmain/orchestration/action_executor.py:231-247
def _execute_correct_report(self, action: dict) -> ActionResult:
    report_type = action.get("report_type", "daily_internal")
    report = self._get_latest_report(report_type)
    if report is None:
        return ActionResult(
            success=False,
            message=f"No {report_type.replace('_', ' ')} found for today.",
            error="no_report",
        )
    report.corrected_content = action.get("correction", "")
    report.status = "corrected"
    self.session.commit()
    return ActionResult(
        success=True,
        message=f"✓ Correction applied to {report_type.replace('_', ' ')}.",
        entity_id=report.id,
    )
```

**Field reads:**
- `action.get("report_type", "daily_internal")` — defaults to `"daily_internal"` if absent.
- `action.get("correction", "")` — the correction string from the action dict; defaults to `""`.

**Repository methods called:**
- `self._get_latest_report(report_type)` — same ORM query as `_execute_confirm_report`.

**DB writes:**
- `report.corrected_content = action.get("correction", "")` — stores the raw correction
  description string from the intent parser output.
- `report.status = "corrected"`
- `self.session.commit()`
- `report.updated_at` is NOT set explicitly.
- `report.correction_note` is NOT set.

**Non-DB writes:** None. No staging file write.

**EOD workflow calls:** None.

**Other tables modified:** None. Only `reports`.

---

# D. EOD Workflow Step Runners

File: `workmain/workflows/eod_workflow.py`

Two step runner functions contain report confirmation/correction logic.

## D.1. `_run_report_step` (Step 4a — daily_internal)

Full source of the relevant interactive review section. The full function spans
lines 598–753; only the DB-writing branches are quoted in full below.

```python
# workmain/workflows/eod_workflow.py:598-753
def _run_report_step(dry_run: bool, target_date: date) -> EodStepResult:
    """Step 4a: Generate daily report with pre-check and interactive review menu."""
    date_str = target_date.isoformat()
    cmd = [_WORKMAIN_BIN, 'reports', 'save', 'daily_internal', '--date', date_str]

    if dry_run:
        print(f"  Would run: workmain reports save daily_internal --date {date_str}")
        print("  Would present: [v]iew / [e]dit / [c]onfirm / [s]kip menu")
        return EodStepResult(status=EodStepStatus.COMPLETED)

    # Pre-check: skip generation if confirmed/corrected report already exists
    db = get_db()
    session = db.get_session()
    try:
        from workmain.database.repositories.reports_repo import get_reports_repository
        repo = get_reports_repository(session)
        existing = repo.list_reports(
            report_type='daily_internal',
            start_date=target_date,
            end_date=target_date,
        )
        for r in existing:
            if r.status in ('confirmed', 'corrected'):
                print(
                    f"  Daily report already confirmed for {date_str} — "
                    f"skipping generation"
                )
                return EodStepResult(status=EodStepStatus.COMPLETED)
    finally:
        session.close()

    # Generate report
    try:
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print()
            print(f"  ⚠ Report generation returned exit code {result.returncode}")
            if not _is_interactive():
                return EodStepResult(
                    status=EodStepStatus.FAILED,
                    error=f"Report generation failed (exit code {result.returncode})",
                )
            action = _prompt_choice("  Continue? [r]etry / [s]kip", default='s')
            if action == 'r':
                result = subprocess.run(cmd)
                if result.returncode != 0:
                    print("  ✗ Retry failed")
                    return EodStepResult(
                        status=EodStepStatus.FAILED,
                        error="Report generation retry failed"
                    )
    except Exception as e:
        print(f"  ✗ Report step error: {e}")
        return EodStepResult(status=EodStepStatus.FAILED, error=str(e))

    # Non-interactive: report generated, skip the interactive review loop
    if not _is_interactive():
        return EodStepResult(
            status=EodStepStatus.COMPLETED,
            message="Daily report generated — review with: workmain reports history",
        )

    # Load the new report for review
    db = get_db()
    session = db.get_session()
    try:
        from workmain.database.repositories.reports_repo import get_reports_repository
        repo = get_reports_repository(session)
        reports = repo.list_reports(
            report_type='daily_internal',
            start_date=target_date,
            end_date=target_date,
            limit=1,
        )

        if not reports:
            print(
                "  ⚠ Could not load report for review — "
                "report saved as unconfirmed"
            )
            return EodStepResult(status=EodStepStatus.COMPLETED)

        report = reports[0]
        content = report.content or ''
        preview = content[:200] + '…' if len(content) > 200 else content

        print()
        print("─── Daily Report Preview ───")
        print(preview)
        print("────────────────────────────")
        print()

        while True:
            choice = _prompt_choice(
                "  Review: [v]iew / [e]dit / [c]onfirm / [s]kip",
                default='s',
            )

            if choice == 'v':
                print()
                print("─── Daily Report — Full View ───")
                print(content)
                print("────────────────────────────────")
                print()
                continue

            elif choice == 'e':
                source = report.corrected_content if report.corrected_content else content
                edited = _eod_edit_in_editor(source)
                if edited is not None and edited != source:
                    report.corrected_content = edited
                    report.status = 'corrected'
                    report.updated_at = datetime.now()
                    session.commit()
                    fp = (report.report_metadata or {}).get('file_path')
                    if fp:
                        try:
                            Path(fp).write_text(edited, encoding='utf-8')
                        except Exception as stage_err:
                            print(f"  ⚠ DB saved; staging file update failed: {stage_err}")
                    correction_note_text = _prompt_raw(
                        "  Add a correction note (optional, Enter to skip): "
                    ).strip()
                    if correction_note_text:
                        repo.set_correction_note(report.id, correction_note_text)
                        print("  Correction note saved.")
                    print("  ✓ Daily report saved with corrections.")
                else:
                    print("  No changes detected.")
                break

            elif choice == 'c':
                report.status = 'confirmed'
                report.updated_at = datetime.now()
                session.commit()
                print("  ✓ Daily report confirmed.")
                break

            else:  # s or any other input
                print()
                print(
                    "  ⚠ Daily report left unconfirmed — it will not appear "
                    "in the weekly draft until confirmed."
                )
                break

        return EodStepResult(status=EodStepStatus.COMPLETED)

    except Exception as e:
        print(
            f"  ⚠ Report review failed ({e}) — report saved but review skipped"
        )
        return EodStepResult(status=EodStepStatus.COMPLETED)

    finally:
        session.close()
```

**`_eod_edit_in_editor` helper — `workmain/workflows/eod_workflow.py:135`:**

```python
# workmain/workflows/eod_workflow.py:135-156
def _eod_edit_in_editor(content: str) -> Optional[str]:
    """Open $EDITOR with content. Returns edited text, or None if EDITOR not set."""
    editor = os.environ.get('EDITOR', '').strip()
    if not editor:
        print(
            '  ⚠ $EDITOR not set — cannot open editor. '
            'Set EDITOR in your shell profile.'
        )
        return None
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        subprocess.run([editor, tmp_path], check=True)
        return Path(tmp_path).read_text()
    except Exception as e:
        print(f'  ⚠ Editor error: {e}')
        return None
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
```

**Parameters:** `dry_run: bool`, `target_date: date`

**DB writes — `[c]onfirm` branch:**
- `report.status = 'confirmed'`
- `report.updated_at = datetime.now()`
- `session.commit()`
- Tables modified: `reports` only.

**DB writes — `[e]dit` (correction) branch:**
- `report.corrected_content = edited` (full corrected report text from `$EDITOR`)
- `report.status = 'corrected'`
- `report.updated_at = datetime.now()`
- `session.commit()`
- Non-DB (best-effort): staging file write via `Path(fp).write_text(edited)`
- `repo.set_correction_note(report.id, correction_note_text)` — conditional; only if user
  enters a non-empty correction note at the prompt. Sets `reports.correction_note`.
- Tables modified: `reports` only.

---

## D.2. `_run_weekly_report_step` (Friday step A — weekly_client)

Full source of the confirmation/correction section:

```python
# workmain/workflows/eod_workflow.py:907-1077
def _run_weekly_report_step(dry_run: bool, target_date: date) -> EodStepResult:
    """Friday step A: Generate weekly client report with pre-check and review menu."""
    # ... [generation and pre-check logic omitted — no DB writes before the review loop] ...

        while True:
            choice = _prompt_choice(
                "  Review: [v]iew / [e]dit / [c]onfirm / [s]kip",
                default='s',
            )

            if choice == 'v':
                # display only — no writes
                continue

            elif choice == 'e':
                source = report.corrected_content if report.corrected_content else content
                edited = _eod_edit_in_editor(source)
                if edited is not None and edited != source:
                    report.corrected_content = edited
                    report.status = 'corrected'
                    report.updated_at = datetime.now()
                    session.commit()
                    fp = (report.report_metadata or {}).get('file_path')
                    if fp:
                        try:
                            Path(fp).write_text(edited, encoding='utf-8')
                        except Exception as stage_err:
                            print(f"  ⚠ DB saved; staging file update failed: {stage_err}")
                    correction_note_text = _prompt_raw(
                        "  Add a correction note (optional, Enter to skip): "
                    ).strip()
                    if correction_note_text:
                        repo.set_correction_note(report.id, correction_note_text)
                        print("  Correction note saved.")
                    print("  ✓ Weekly report saved with corrections.")
                else:
                    print("  No changes detected.")
                break

            elif choice == 'c':
                report.status = 'confirmed'
                report.updated_at = datetime.now()
                session.commit()
                print("  ✓ Weekly report confirmed.")
                break

            else:  # s or any other input
                print()
                print("  ⚠ Weekly report left unconfirmed.")
                break
```

**Parameters:** `dry_run: bool`, `target_date: date`

**DB writes — `[c]onfirm` branch:**
- `report.status = 'confirmed'`
- `report.updated_at = datetime.now()`
- `session.commit()`
- Tables modified: `reports` only.

**DB writes — `[e]dit` (correction) branch:**
- Identical to `_run_report_step` correction branch.
- Tables modified: `reports` only.

---

# E. Cross-Reference: action_executor vs eod_workflow

## E.1. `confirm_report`

Does action_executor call any eod_workflow function? **No.**

action_executor writes (enumerated):
1. `report.status = "confirmed"`
2. `session.commit()`
(`report.updated_at` is NOT explicitly set)

eod_workflow writes (enumerated):
1. `report.status = 'confirmed'`
2. `report.updated_at = datetime.now()`
3. `session.commit()`

## E.2. `correct_report`

Does action_executor call any eod_workflow function? **No.**

action_executor writes (enumerated):
1. `report.corrected_content = action.get("correction", "")` — raw correction description
   string from intent parser
2. `report.status = "corrected"`
3. `session.commit()`
(`report.updated_at` NOT set, `report.correction_note` NOT set, no staging file write)

eod_workflow writes (enumerated):
1. `report.corrected_content = edited` — full corrected report text from `$EDITOR`
2. `report.status = 'corrected'`
3. `report.updated_at = datetime.now()`
4. `session.commit()`
5. (best-effort) staging file: `Path(fp).write_text(edited, encoding='utf-8')`
6. (conditional) `report.correction_note` via `repo.set_correction_note(report.id,
   correction_note_text)` — only if user enters a non-empty note at the prompt

---

# F. Report Model and Status Fields

## F.1. `Report` Model

```python
# workmain/database/models.py:381-428
class Report(Base):
    """
    Report model - represents AI-generated reports.

    Stores generated report metadata including AI costs, tokens, and provider info.
    Links to file system for actual report content.
    """
    __tablename__ = 'reports'

    # Primary key
    id = Column(Integer, primary_key=True)

    # Fields
    report_type = Column(String(50), nullable=False)  # 'daily_internal', 'weekly_client', etc.
    report_date = Column(Date, nullable=False)
    content = Column(Text, nullable=False)

    # Metadata (JSONB for AI costs, tokens, provider info)
    # Note: Using 'report_metadata' in Python, mapped to 'metadata' in database
    # to avoid conflict with SQLAlchemy's reserved 'metadata' attribute
    report_metadata = Column('metadata', JSON, nullable=True)

    # Validation & sending
    validation_passed = Column(Boolean, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    # Integration fields
    outlook_draft_id = Column(String(255), nullable=True)
    slack_message_ts = Column(String(255), nullable=True)
    slack_channel = Column(Text, nullable=True)
    slack_workspace_name = Column(Text, nullable=True)

    # Client attribution (Phase 11)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='SET NULL'),
                       nullable=True, index=True)
    client    = relationship('Client', lazy='select')

    # Status tracking and correction (Phase 12)
    status            = Column(String(20), nullable=False, default='unconfirmed')
    corrected_content = Column(Text, nullable=True)
    correction_note   = Column(Text, nullable=True)  # Phase 13 placeholder — Ollama intent parser

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Report(id={self.id}, type='{self.report_type}', date={self.report_date})>"
```

## F.2. Migration Files

### Migration 016 — adds status/correction fields

```sql
-- workmain/database/migrations/016_reports_status_columns.sql
-- WorkmAIn Phase 12 — PC-3 Report Correction Propagation
-- Adds status tracking and correction fields to reports table

ALTER TABLE reports
    ADD COLUMN status            VARCHAR(20) NOT NULL DEFAULT 'unconfirmed'
                                     CHECK (status IN ('unconfirmed',
                                                       'confirmed',
                                                       'corrected')),
    ADD COLUMN corrected_content TEXT NULL,
    ADD COLUMN correction_note   TEXT NULL,
    ADD COLUMN updated_at        TIMESTAMP NULL DEFAULT NOW();

-- Grandfather existing records as confirmed
-- (preserves existing weekly aggregation behavior)
-- Note: ALTER TABLE fills existing rows with DEFAULT 'unconfirmed',
-- so WHERE status = 'unconfirmed' correctly targets all pre-existing records.
UPDATE reports SET status = 'confirmed'
WHERE  status = 'unconfirmed';
```

No other migration file was found that adds or modifies fields related to report
confirmation or correction status.

## F.3. Live Schema Query

Query:
```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'reports'
ORDER BY ordinal_position;
```

Results:
```
column_name          | data_type                   | is_nullable | column_default
---------------------+-----------------------------+-------------+--------------------------------
id                   | integer                     | NO          | nextval('reports_id_seq'::regclass)
report_type          | character varying           | NO          | None
report_date          | date                        | NO          | None
content              | text                        | NO          | None
metadata             | jsonb                       | YES         | None
validation_passed    | boolean                     | YES         | None
sent_at              | timestamp without time zone | YES         | None
outlook_draft_id     | character varying           | YES         | None
slack_message_ts     | character varying           | YES         | None
created_at           | timestamp without time zone | YES         | now()
slack_channel        | text                        | YES         | None
slack_workspace_name | text                        | YES         | None
client_id            | integer                     | YES         | None
status               | character varying           | NO          | 'unconfirmed'::character varying
corrected_content    | text                        | YES         | None
correction_note      | text                        | YES         | None
updated_at           | timestamp without time zone | YES         | now()
```

---

# G. Underlying Data Mutation Check

Search scope: `action_executor.py`, `eod_workflow.py`, `reports.py` (CLI).

No code path was found that modifies `notes` or `time_entries` records as part
of a report confirmation or correction flow.

- `_execute_confirm_report`: writes only to `reports.status`. No `NotesRepository`
  or `TimeEntriesRepository` call.
- `_execute_correct_report`: writes only to `reports.corrected_content` and
  `reports.status`. No `NotesRepository` or `TimeEntriesRepository` call.
- `_run_report_step` (`[c]onfirm` branch): writes only to `reports.status` and
  `reports.updated_at`.
- `_run_report_step` (`[e]dit` branch): writes only to `reports.corrected_content`,
  `reports.status`, `reports.updated_at`, and (conditionally) `reports.correction_note`.
  No `NotesRepository` or `TimeEntriesRepository` call.
- `_run_weekly_report_step`: same as `_run_report_step` — `reports` table only.
- `report_confirm` (CLI): writes only to `reports.status` and `reports.updated_at`.
- `report_correct` (CLI): writes only to `reports.corrected_content`, `reports.status`,
  and `reports.updated_at`. No `correction_note` written from this path.

`correct_report` in all paths only modifies the `reports` table. The `corrected_content`
field is used to store either a correction description string (action_executor path) or
the full corrected report text (CLI/eod_workflow path). In neither path are the
underlying `notes` or `time_entries` records that contributed to the report modified.

---

# H. Schema Cross-Reference

Source: `config/intent_parse_system_prompt.txt` (config_version 1.6)

## H.1. `confirm_report` Schema

```
# config/intent_parse_system_prompt.txt:81-84
4. confirm_report
   Required: report_type (one of: daily_internal, weekly_client)
   Example input: "daily report looks good, confirm it"
   Example output: {"action": "confirm_report", "report_type": "daily_internal"}
```

**Field cross-reference:**

| Schema Field | Type     | Required | action_executor reads it?                         | CLI parameter exists? |
|--------------|----------|----------|---------------------------------------------------|-----------------------|
| `report_type`| string   | Yes      | Yes — `action.get("report_type", "daily_internal")` | No — CLI uses `identifier` (ID or date); `_resolve_report` defaults to `daily_internal` on date-based lookup with any-type fallback |

## H.2. `correct_report` Schema

```
# config/intent_parse_system_prompt.txt:86-89
5. correct_report
   Required: report_type (one of: daily_internal, weekly_client), correction (string)
   Example input: "fix the daily — I spent 2 hours on XSOAR not 90 minutes"
   Example output: {"action": "correct_report", "report_type": "daily_internal", "correction": "XSOAR time should be 120 minutes not 90"}
```

**Field cross-reference:**

| Schema Field | Type   | Required | action_executor reads it?                                          | CLI parameter exists?                                                     |
|--------------|--------|----------|--------------------------------------------------------------------|---------------------------------------------------------------------------|
| `report_type`| string | Yes      | Yes — `action.get("report_type", "daily_internal")`               | No — CLI uses `identifier`; no `report_type` parameter                   |
| `correction` | string | Yes      | Yes — `action.get("correction", "")` → written to `corrected_content` | No — CLI opens `$EDITOR` to capture a full replacement of report content |
