WorkmAIn
RECON_SPEC_REPORT_CORRECTION_DATA_INTEGRITY v1.0
20260717

# Purpose

Standalone Gate 0 recon, run alongside (or just ahead of) the Item #56
recon. This is recon only — no code changes, no fixes, no scope decisions.
Report what exists today, as it exists today. Do not propose solutions.

# Why this exists (for context only — verify, don't assume)

Documentation (`CLAUDE.md`, `SESSION_HANDOFF_PHASE12_COMPLETE.md`, migration
016) states `content` (original) and `corrected_content` (edited) are
separate, independently-preserved columns, with `corrected_content` written
only by the `$EDITOR` path (`workmain reports correct` / EOD `[e]dit`
branch), never by `action_executor`. Ray's direct experience using the CLI
is that corrections appear to overwrite the original with no way to
compare versions. This recon exists to resolve that discrepancy against
actual current source and actual current data — not against either party's
memory of it.

Do not resolve the discrepancy by picking a side. Report what the code
does and what the data shows.

---

# Output

Save this document, verbatim as pasted into this session, to
`docs/dev/design/RECON_SPEC_REPORT_CORRECTION_DATA_INTEGRITY_20260717.md`
if it is not already present at that path. Then append your findings
directly to the end of this same file, below the `## Findings` heading at
the bottom — do not create a separate output file, do not use a different
name or location. Do not edit any other files.

---

# Section 1 — `report_correct()` (CLI $EDITOR path)

**File:** `workmain/cli/commands/reports.py`

1. Full current function body, verbatim, complete (definition through
   final line — confirm nothing is elided).
2. Exactly which field(s) does it write, and with what values? Quote the
   exact assignment lines (e.g. `report.corrected_content = ...`,
   `report.content = ...` if present, `report.correction_note = ...` if
   present).
3. Does this function, as it exists today, ever write to `correction_note`?
   (Documentation says only `action_executor` does — confirm or
   contradict against live source.)
4. Does this function ever write to `content` (the original field)? If so,
   quote the exact line and describe the condition under which it fires.
5. Confirm current header version.

---

# Section 2 — EOD `[e]dit` Branch

**File:** `workmain/workflows/eod_workflow.py` (or wherever the EOD Step
4a edit choice currently lives — confirm actual file/function name, it
may have moved since the `hotfix_eod-edit-staging-sync_spec.md` era).

Same five questions as Section 1, applied to this code path.

---

# Section 3 — `action_executor._execute_correct_report()` (Slack/intent path)

**File:** `workmain/orchestration/action_executor.py`

1. Full current function body, verbatim, complete.
2. Exactly which field(s) does it write? Quote the exact assignment
   lines.
3. Confirm whether it writes `corrected_content` under any condition
   today (documentation says never — confirm or contradict).
4. Confirm current header version and confirm this matches or has drifted
   from the fix described in
   `SESSION_HANDOFF_INTENT_ACTION_AUDIT_ITEMS4-5_COMPLETE_20260624.md`
   Gate 2 ("route to correction_note").

---

# Section 4 — Repository Write Methods

**File:** likely `workmain/database/repositories/reports_repo.py` —
confirm actual filename/class name.

For every method that writes to any of `content`, `corrected_content`,
`correction_note`, or `status` on the `reports` table:
1. Full method signature and full body, verbatim.
2. Which of the three callers above (Sections 1–3) invoke it, and with
   what arguments?
3. Does any single method write more than one of these three fields in
   the same call? If so, quote it exactly.

---

# Section 5 — `reports_show()` / `report_show()` Rendering

**File:** `workmain/cli/commands/reports.py`

1. Full current function body, verbatim, complete.
2. Confirm: does it render `report.content`, `report.corrected_content`,
   or both? Under what condition, if any?
3. Confirm current behavior for `correction_note` display (added per
   hotfix v1.22.2) — is it still present and unconditional-when-populated,
   or has it changed?
4. Confirm current header version.

---

# Section 6 — Staging File Behavior

**File:** wherever `report_correct()` and the EOD `[e]dit` branch write to
`staging/reports/`.

1. Confirm whether the staging-file overwrite behavior described in
   `hotfix_eod-edit-staging-sync_spec.md` (v1.18.2) is still present in
   current source — quote the current write call verbatim.
2. Confirm: does anything ever write a *second* staging file preserving
   the pre-correction version, or is the single staging file always
   overwritten in place?

---

# Section 7 — Live Data Check (Read-Only)

Run a read-only query against the actual `workmain` database (no writes)
against the 10 most recently corrected reports (`status = 'corrected'`,
ordered by whatever the actual "corrected at" timestamp column is,
descending). For each of the 10 rows, report:

- `id`, `report_type`, `report_date`
- `content` — present/length (do not reproduce full text, just confirm
  non-null and approximate length)
- `corrected_content` — NULL, or present/length
- `correction_note` — NULL, or present/length
- Whether `content` and `corrected_content` are byte-identical when both
  are non-null (this would indicate an overwrite-in-place rather than
  independent preservation)

State the exact SQL or ORM query used.

---

# Format Notes

- Use the WorkmAIn document header convention (title, doc name + version,
  date) at the top of the output file.
- Quote source code verbatim in fenced code blocks with file path
  comments — do not paraphrase signatures or logic.
- If a referenced file/method cannot be located, state that explicitly
  rather than omitting the section.
- Mark each finding CONFIRMS or CONTRADICTS against the "Why this exists"
  framing above.
- This is a factual enumeration — do not characterize severity, do not
  propose fixes, do not recommend a remediation path. That happens in a
  separate Role 1 planning session after this recon returns.
- Keep this self-contained — the reviewing session will not have live
  access to the repo, only this document.

---

## Findings

WorkmAIn
RECON_SPEC_REPORT_CORRECTION_DATA_INTEGRITY — Findings
20260717
Appended by Claude Code / Opus (Role 2), read-only recon execution.

Factual enumeration only. No severity, no remediation, no scope decisions.
Each section marked CONFIRMS or CONTRADICTS against the "Why this exists"
framing (documentation: `content` and `corrected_content` are separate,
independently-preserved columns, `corrected_content` written only by the
`$EDITOR` path; Ray's experience: corrections appear to overwrite the
original with no way to compare versions).

---

### Section 1 — `report_correct()` (CLI $EDITOR path)

**File:** `workmain/cli/commands/reports.py` — header **v2.13, 20260708** (Q5).

**Q1 — full current function body, verbatim (definition through final line, nothing elided):**

```python
# workmain/cli/commands/reports.py  (lines 550–590)
@reports.command('correct')
@click.argument('identifier')
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

**Q2 — which field(s) does it write, and with what values? Exact assignment lines:**

```python
report.corrected_content = edited            # edited text returned from $EDITOR
report.status = 'corrected'
report.updated_at = datetime.now()
```

Plus a staging-file write (not a DB field): `Path(fp).write_text(edited, ...)`.

**Q3 — does it ever write `correction_note`?** No. There is no assignment to
`report.correction_note` anywhere in this function. **CONFIRMS** the
documentation's claim that `report_correct()` does not write `correction_note`.

**Q4 — does it ever write `content` (the original field)?** No. There is no
`report.content = ...` assignment anywhere in this function. The original
`report.content` is left untouched. **CONFIRMS** independent preservation of
the original column; **CONTRADICTS** the "overwrites the original" experience
at the DB level (see Section 7 for corroborating data).

Note (factual, not a fix): the pre-populate line reads
`report.corrected_content if report.corrected_content else report.content` —
so a second `correct` on an already-corrected report edits the prior
correction, not the original.

---

### Section 2 — EOD `[e]dit` Branch

**File:** `workmain/workflows/eod_workflow.py` — header **v1.8, 20260716**
(Q5). The EOD edit choice did move since the `hotfix_eod-edit-staging-sync`
era: it now lives in this surface-agnostic workflow module (extracted from
`cli/commands/eod.py` v2.13 per the v1.0 history entry), **not** in
`cli/commands/eod.py`. There are **two** near-identical `[e]dit` branches —
one in the daily-report review step (lines ~990–1013) and one in the
weekly-report review step (lines ~1317–1340). Both are quoted.

**Q1 — full current branch bodies, verbatim:**

```python
# workmain/workflows/eod_workflow.py  (daily report review, lines 990–1013)
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
```

```python
# workmain/workflows/eod_workflow.py  (weekly report review, lines 1317–1340)
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
```

**Q2 — which field(s), with what values (both branches, identical):**

```python
report.corrected_content = edited            # edited text from $EDITOR
report.status = 'corrected'
report.updated_at = datetime.now()
# then, optionally, via repo.set_correction_note(report.id, correction_note_text):
report.correction_note = <stripped prompt text>   # only if user types a note
```

**Q3 — does this path write `correction_note`?** YES — but only via the
optional interactive prompt, routed through `repo.set_correction_note()`
(which itself no-ops on empty input, see Section 4). This is a difference
from the CLI `reports correct` path (Section 1), which has no such prompt.
This is a **CONTRADICTION of the documentation's blanket statement** that
`correction_note` is written only by `action_executor` (CLAUDE.md, "Report
Correction Fields": *"`correction_note` ... Written by
`action_executor._execute_correct_report`"*) — the EOD `[e]dit` branch also
writes it, via the repository method.

**Q4 — does this path write `content` (the original)?** No. No
`report.content = ...` assignment exists in either branch. Original preserved.
**CONFIRMS** independent preservation.

---

### Section 3 — `action_executor._execute_correct_report()` (Slack/intent path)

**File:** `workmain/orchestration/action_executor.py` — header **v1.4,
20260624** (Q4).

**Q1 — full current function body, verbatim:**

```python
# workmain/orchestration/action_executor.py  (lines 254–307)
    def _execute_correct_report(self, action: dict) -> ActionResult:
        """Flag a correction for today's most recent report.

        Phase 12 Decision 21 (locked): correction_note was added as the
        Phase 13 placeholder for Slack/intent parser correction descriptions.
        This method writes the correction description to correction_note.

        corrected_content is reserved for full edited report text written
        via $EDITOR (CLI / eod_workflow path only). This method must never
        write to corrected_content — doing so would corrupt the pre-populate
        behaviour of 'workmain reports correct today'.

        Sets status = 'corrected' to:
        - Prevent EOD from regenerating the report on a subsequent run
          (eod_workflow pre-check skips reports where status IN
          ('confirmed', 'corrected')).
        - Exclude this daily from weekly aggregation until the CLI edit
          is applied and the report is re-confirmed.

        Status transition table:
          unconfirmed → corrected  : normal flagging path
          confirmed   → corrected  : correction overrides prior confirmation
          corrected   → corrected  : already flagged; correction_note
                                     overwritten with most recent description
        """
        report_type = action.get("report_type", "daily_internal")
        correction = action.get("correction", "").strip()
        if not correction:
            return ActionResult(
                success=False,
                message="Cannot flag correction: no correction description provided.",
                error="missing_correction",
            )
        report = self._get_latest_report(report_type)
        if report is None:
            return ActionResult(
                success=False,
                message=f"No {report_type.replace('_', ' ')} found for today.",
                error="no_report",
            )
        report.correction_note = correction
        if report.status != "corrected":
            report.status = "corrected"
        report.updated_at = datetime.now()
        self.session.commit()
        report_label = report_type.replace("_", " ")
        return ActionResult(
            success=True,
            message=(
                f"Correction noted for {report_label}: '{correction}'. "
                f"Apply the full edit with: workmain reports correct today"
            ),
            entity_id=report.id,
        )
```

**Q2 — which field(s) does it write? Exact assignment lines:**

```python
report.correction_note = correction          # stripped 'correction' string from action dict
report.status = 'corrected'                   # only when status != 'corrected'
report.updated_at = datetime.now()
```

**Q3 — does it write `corrected_content` under any condition today?** No.
There is no `report.corrected_content = ...` assignment anywhere in this
method. **CONFIRMS** the documentation's claim that `action_executor` never
writes `corrected_content`.

**Q4 — header version vs. the Gate 2 fix ("route to correction_note"):**
**Matches, no drift.** Header v1.4 history entry reads: *"Fix
`_execute_correct_report` — route correction description to `correction_note`
(Phase 12 Decision 21) not `corrected_content`; add empty-correction guard;
explicit updated_at stamp."* The live code implements exactly that: writes
`correction_note` (not `corrected_content`), guards on empty `correction`,
and sets `updated_at` explicitly. Header date 20260624 aligns with the
`..._INTENT_ACTION_AUDIT_ITEMS4-5_COMPLETE_20260624.md` handoff date. (The
handoff file itself lives under gitignored `docs/dev/handoffs/` and was not
opened for this recon — the match is confirmed against code + header only.)

---

### Section 4 — Repository Write Methods

**File:** `workmain/database/repositories/reports_repo.py` — class
`ReportsRepository`, header **v1.4, 20260611**.

Methods that write to any of `content`, `corrected_content`,
`correction_note`, or `status` on the `reports` table:

**(a) `create(...)` — writes `content` (at row creation only):**

```python
# reports_repo.py  (lines 48–111, signature + relevant body)
    def create(
        self,
        report_type: str,
        report_date: date,
        content: str,
        ai_provider: str,
        ai_model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        cost: float,
        generation_time: float,
        file_path: Optional[str] = None,
        client_id: Optional[int] = None,
    ) -> Report:
        ...
        report = Report(
            report_type=report_type,
            report_date=report_date,
            content=content,
            report_metadata=metadata,
            created_at=datetime.now(),
            client_id=client_id,
        )
        self.session.add(report)
        self.session.commit()
        self.session.refresh(report)
        return report
```

Writes `content` (original) at creation. Does not set `status` (relies on the
model default `'unconfirmed'`), and never sets `corrected_content` or
`correction_note`. Callers: the report generator (not in Sections 1–3 scope).

**(b) `set_correction_note(report_id, note)` — writes `correction_note`:**

```python
# reports_repo.py  (lines 193–209)
    def set_correction_note(self, report_id: int, note: str) -> None:
        """Populate reports.correction_note for a corrected report.

        Strips whitespace. Silently no-ops if note is empty after strip.

        Args:
            report_id: ID of the report to annotate.
            note: Human-readable correction note describing what changed.
        """
        note = note.strip()
        if not note:
            return
        report = self.get_by_id(report_id)
        if report is None:
            return
        report.correction_note = note
        self.session.commit()
```

Writes only `correction_note`. Caller among Sections 1–3: the **EOD `[e]dit`
branch** (Section 2), via `repo.set_correction_note(report.id,
correction_note_text)`. (Also called by
`action_executor._execute_write_correction_note`, a *separate* handler from
`_execute_correct_report` — see action_executor lines 331–343 — which is not
one of the three correction paths under recon but does invoke this method.)

**No repository method writes `corrected_content` or `status`.** Those two
fields are written only inline against the ORM object in the CLI
`report_correct()` path (Section 1) and the EOD `[e]dit` branches (Section 2)
— i.e. `report.corrected_content = ...` / `report.status = ...` followed by
`session.commit()`, bypassing any repository method. `_execute_correct_report`
(Section 3) likewise sets `status` inline, not via a repo method.

**Q3 — does any single method write more than one of the four fields in the
same call?** No repository method does. `create()` writes only `content`;
`set_correction_note()` writes only `correction_note`. The multi-field writes
(`corrected_content` + `status` + `updated_at`) occur inline in the CLI/EOD
call sites, not inside a repository method.

---

### Section 5 — `report_show()` Rendering

**File:** `workmain/cli/commands/reports.py` — header **v2.13, 20260708**
(Q4). Function name is `report_show` (command `reports show`).

**Q1 — full current function body, verbatim:**

```python
# workmain/cli/commands/reports.py  (lines 670–735)
@reports.command('show')
@click.argument('target', type=str)
def report_show(target: str):
    """
    Display a report by database ID or filename.

    TARGET can be an integer database ID or a report filename.

    \b
    Examples:
      workmain reports show 42
      workmain reports show daily_internal_2026-03-05.md
    """
    db = get_db()
    session = db.get_session()

    try:
        try:
            report_id = int(target)
            # ID path — fetch from database
            report = session.query(Report).filter(Report.id == report_id).first()

            if not report:
                console.print(f"[red]Error: No report found with ID {report_id}.[/red]")
                raise SystemExit(1)

            title = f"Report #{report.id} — {report.report_type} — {report.report_date}"

            console.print()
            console.print(Panel(
                report.content or "(no content)",
                title=f"[bold]{title}[/bold]",
                border_style="green"
            ))
            if report.correction_note:
                console.print(f"  [yellow]Correction note:[/yellow] {report.correction_note}")
            console.print()

        except ValueError:
            # Filename path — read from staging directory
            generator = get_report_generator(session)
            file_path = generator.output_dir / target

            if not file_path.exists():
                console.print(f"[red]✗ Report not found: {target}[/red]")
                console.print("\n[dim]Use 'workmain reports list' to see available reports[/dim]\n")
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            console.print()
            console.print(Panel(
                content,
                title=f"[bold]{target}[/bold]",
                border_style="green"
            ))
            console.print()

    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]✗ Failed to show report: {e}[/red]")

    finally:
        session.close()
```

**Q2 — renders `content`, `corrected_content`, or both?** The **ID path**
renders **`report.content` only** (`report.content or "(no content)"`). It
does **not** reference `report.corrected_content` at all — there is no
condition under which `reports show <id>` displays the corrected text. The
**filename path** reads and renders the staging file on disk (`generator.
output_dir / target`), which — per Sections 1/2/6 — is overwritten with the
corrected text at correction time; so the filename path shows corrected text
only insofar as the file was overwritten, not by reading `corrected_content`.

This is the **factual mechanism behind the "no way to compare versions"
experience** (**CONTRADICTS** the assumption of overwrite, but explains the
symptom): `corrected_content` is stored in the DB (Section 7 confirms it is
non-null and differs from `content`), yet **no CLI surface renders
`corrected_content`**. `reports show <id>` always shows the *original*
`content`; the corrected text is only reachable via the overwritten staging
file (filename path) or by re-running `reports correct` (which pre-populates
from `corrected_content`). Reported as fact; no remediation proposed.

**Q3 — `correction_note` display (hotfix v1.22.2 / Item 33):** Still present
and unconditional-when-populated on the **ID path only**:
`if report.correction_note: console.print(f"  [yellow]Correction
note:[/yellow] {report.correction_note}")`. Unchanged in behavior. (Header
history attributes this to v2.12, "Hotfix items-33-34-incomplete-impl".) The
filename path does not display `correction_note`.

---

### Section 6 — Staging File Behavior

**Files:** `workmain/cli/commands/reports.py` (`report_correct`, Section 1)
and `workmain/workflows/eod_workflow.py` (both `[e]dit` branches, Section 2).

**Q1 — is the staging-file overwrite from `hotfix_eod-edit-staging-sync_spec.md`
(v1.18.2) still present? Verbatim current write call:**

Yes, present in all three correction sites. Identical write pattern:

```python
# reports.py report_correct (lines 580–585)
        fp = (report.report_metadata or {}).get('file_path')
        if fp:
            try:
                Path(fp).write_text(edited, encoding='utf-8')
            except Exception as stage_err:
                console.print(f"[yellow]⚠ DB saved; staging file update failed: {stage_err}[/yellow]")
```

```python
# eod_workflow.py both [e]dit branches (lines 998–1003 and 1325–1330)
                    fp = (report.report_metadata or {}).get('file_path')
                    if fp:
                        try:
                            Path(fp).write_text(edited, encoding='utf-8')
                        except Exception as stage_err:
                            print(f"  ⚠ DB saved; staging file update failed: {stage_err}")
```

The reports.py history corroborates: v2.10 — *"reports correct: after
committing corrected_content to DB, also overwrite the staging file so email
and gdocs steps use the edited content."*

**Q2 — is a second (pre-correction) staging file ever written, or is the
single file overwritten in place?** Overwritten in place. All three sites
write `edited` to the same `file_path` pulled from
`report.report_metadata['file_path']` — the exact path the original was
written to at generation time (`create()` stored `metadata["file_path"]`,
Section 4). No code writes a second, versioned, or `.orig`/backup staging
file preserving the pre-correction text. `report_resend` (reports.py lines
738–796) writes `report.content` (the *original* DB field) to
`staging/reports/{type}_{date}.md`, which can re-overwrite the corrected
staging file with the original — reported as fact, not evaluated.

---

### Section 7 — Live Data Check (Read-Only)

**Query used** (ORM, read-only, no writes; run via the Python app connection
per project DB pattern). There is no dedicated "corrected at" column on
`reports`; the de-facto correction timestamp is `updated_at` (set explicitly
by every correction path — Sections 1–3 — and also `onupdate=datetime.now` on
the model). Ordered by `updated_at DESC`:

```python
from workmain.database.connection import get_db
from workmain.database.models import Report

db = get_db()
session = db.get_session()
try:
    rows = (session.query(Report)
            .filter(Report.status == 'corrected')
            .order_by(Report.updated_at.desc(), Report.id.desc())
            .limit(10).all())
    # per row: id, report_type, report_date, updated_at,
    #          len(content), len(corrected_content) or NULL,
    #          len(correction_note) or NULL, (content == corrected_content)
finally:
    session.close()
```

**Result — 10 rows returned, all `status = 'corrected'`:**

| id | report_type | report_date | updated_at | content | corrected_content | correction_note | content == corrected_content |
|----|-------------|-------------|------------|---------|-------------------|-----------------|------------------------------|
| 9122 | daily_internal | 2026-07-16 | 2026-07-16 14:05:06 | len 1622 | len 1131 | len 24 | **False** |
| 9121 | daily_internal | 2026-07-15 | 2026-07-16 10:57:32 | len 1364 | len 1157 | NULL | **False** |
| 9120 | daily_internal | 2026-07-14 | 2026-07-16 10:14:17 | len 1106 | len 1001 | NULL | **False** |
| 9119 | daily_internal | 2026-07-13 | 2026-07-16 08:41:03 | len 1546 | len 1243 | NULL | **False** |
| 8896 | weekly_client | 2026-07-10 | 2026-07-10 14:37:04 | len 1886 | len 1640 | NULL | **False** |
| 8895 | daily_internal | 2026-07-10 | 2026-07-10 14:32:38 | len 1683 | len 1699 | NULL | **False** |
| 8894 | daily_internal | 2026-07-09 | 2026-07-09 14:43:41 | len 1272 | len 1294 | len 17 | **False** |
| 8595 | daily_internal | 2026-07-08 | 2026-07-08 19:49:09 | len 1859 | len 1771 | len 50 | **False** |
| 7705 | daily_internal | 2026-07-07 | 2026-07-07 14:10:19 | len 1596 | len 1248 | len 30 | **False** |
| 7704 | daily_internal | 2026-07-06 | 2026-07-07 10:53:23 | len 1112 | len 1182 | NULL | **False** |

Raw per-row facts as observed:
- `content`: **non-null in all 10 rows** (lengths 1106–1886).
- `corrected_content`: **non-null in all 10 rows** (lengths 1001–1771).
- `correction_note`: non-null in **4 of 10** (rows 9122, 8894, 8595, 7705);
  NULL in the other 6 (9121, 9120, 9119, 8896, 8895, 7704).
- `content == corrected_content` (byte-identical): **False in all 10 rows.**
  In no observed corrected report is the corrected column a byte-copy of the
  original — the two columns hold genuinely different text in every case.

**Interpretation against the framing (facts only):** The data **CONFIRMS the
documentation's model** — `content` (original) and `corrected_content`
(edited) are separately populated and independently preserved; the original
`content` is never overwritten by the correction (it remains non-null and
differs from `corrected_content` in 10/10 rows). This **CONTRADICTS** the
literal reading of Ray's experience that corrections *overwrite the original*
at the storage layer. The gap between the data and the experience is fully
accounted for by Section 5: `reports show <id>` renders only `content`
(never `corrected_content`), and no CLI surface displays the two side by side,
so the stored correction is effectively invisible through the ID-based show
command. Root-cause characterization and any remediation are explicitly out
of scope for this recon and deferred to the Role 1 planning session.

---

### Header Version Summary

| File | Header version | Date |
|------|----------------|------|
| `workmain/cli/commands/reports.py` | v2.13 | 20260708 |
| `workmain/workflows/eod_workflow.py` | v1.8 | 20260716 |
| `workmain/orchestration/action_executor.py` | v1.4 | 20260624 |
| `workmain/database/repositories/reports_repo.py` | v1.4 | 20260611 |
| `workmain/database/models.py` (Report model) | v2.x (columns confirmed: `content`, `corrected_content`, `correction_note`, `status`) | — |

### CONFIRMS / CONTRADICTS Roll-up

- **CONFIRMS** (documentation accurate): `report_correct()` writes
  `corrected_content` + `status`, never `content`, never `correction_note`
  (S1). `action_executor._execute_correct_report()` writes `correction_note`,
  never `corrected_content` (S3), matching the v1.4 Gate 2 fix with no drift.
  DB holds `content` and `corrected_content` as distinct, both-non-null,
  never-byte-identical columns in 10/10 corrected rows (S7) — original is
  preserved, not overwritten.
- **CONTRADICTS / QUALIFIES documentation:** the EOD `[e]dit` branch **also**
  writes `correction_note` (via `repo.set_correction_note`, optional prompt),
  so the CLAUDE.md statement that `correction_note` is written *only* by
  `action_executor` is not accurate as written (S2, S4).
- **EXPLAINS the reported experience** (no overwrite, but symptom real):
  `reports show <id>` renders `report.content` only and never
  `corrected_content` (S5); the single staging file is overwritten in place
  with no pre-correction copy retained (S6). The correction is stored but has
  no read surface that shows it against the original.

_End of findings._
