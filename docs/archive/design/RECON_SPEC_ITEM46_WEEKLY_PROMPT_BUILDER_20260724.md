WorkmAIn
RECON_SPEC_ITEM46_WEEKLY_PROMPT_BUILDER v1.0
20260724

# Purpose

Standalone Gate 0 recon. Read-only. No code changes, no fixes, no scope
decisions. Report what exists today, as it exists today. Do not propose
solutions or characterize severity.

# Why this exists (context only — verify, don't assume)

This recon exists to unblock **Gate 4** of
`HOTFIX_ITEM61_REPORT_REVIEW_UNIFICATION_SPEC_v1.0.md`, which unifies the
Thursday Slack draft-weekly path (`slack post weekly`) with the Friday EOD
weekly review into one shared review runner. Gate 4 needs to know: once
Thursday's draft becomes a real `confirmed`/`corrected` row (instead of an
unconfirmed, unstatused row as it is today), what should Friday's EOD do
with it — reuse it as-is, or regenerate incorporating it? That question
turns out to depend entirely on **Backlog Item #46**
(`build_weekly_prompt()` Edge Cases: Short Weeks, Thursday Draft, Internal
Content Pollution — `FEATURE_BACKLOG.md`), which is open, not yet
implemented, and describes exactly this seam:

> "On Thursday EOD the pipeline posts a Slack draft weekly report. At that
> point only Mon–Thu confirmed dailies exist... the confirmed path is
> unreachable. The Thursday draft always uses raw data even if Mon–Thu are
> fully confirmed."

Ray independently observed a live symptom consistent with this: a
Thursday-generated draft that matched the `weekly_client` template
correctly (scoped Mon–Thu) versus a separately-generated report scoped
Mon–Fri that abandoned the template's five-question structure entirely.
This recon does not assume Item #46's "Why Deferred" reasoning or gap
descriptions are still accurate against current source — verify each
against live code.

A second, narrower question is bundled in here because it blocks the same
Gate 4 and touches the same subsystem: `slack.py:slack_post`'s exact
anchor-date computation, needed so Gate 4's lookup (does a
`confirmed`/`corrected` `weekly_client` row already exist for Friday's
`target_date`?) actually matches the row Thursday's post created. The
original recon (`RECON_REPORT_REVIEW_FLOWS_20260724.md`) cited this code
by line number only, not verbatim.

---

# Output

Save this document, verbatim as pasted into this session, to
`docs/dev/design/RECON_SPEC_ITEM46_WEEKLY_PROMPT_BUILDER_20260724.md` if
not already present at that path. Append findings directly to the end of
this same file, below the `## Findings` heading at the bottom — do not
create a separate output file, do not use a different name or location.
Do not edit any other files.

---

# Section 1 — Weekday-Mode Dispatch

**Files:** `workmain/cli/commands/eod.py`, `workmain/workflows/eod_workflow.py`,
`workmain/ai/report_generator.py` (confirm actual dispatch location — it
may live in more than one of these).

1. Trace, end to end, how the system decides "this is a Thursday draft
   generation" vs. "this is a Friday final generation" — quote the exact
   conditional/weekday check verbatim, with file and line numbers.
2. What parameters does that dispatch pass down to `generate_report_impl`
   and ultimately to `prompt_builder.build_weekly_prompt()`? Is there any
   explicit `draft=True`/`mode=` flag, or is Thursday-vs-Friday behavior
   entirely implicit in which dailies happen to be confirmed at call time?
3. Confirm current header versions of all files touched.

---

# Section 2 — `build_weekly_prompt()` Confirmed-Path / Raw-Fallback Logic

**File:** `workmain/ai/prompt_builder.py`.

1. Full current body of `build_weekly_prompt()`, verbatim, complete.
2. Quote the exact `weekdays_covered` computation and the exact confirmed-path
   condition (Item #46 describes it as `weekdays_covered == {0, 1, 2, 3, 4}`
   — confirm or contradict against live source, verbatim).
3. Quote the exact raw-data fallback branch — what does it query directly,
   and how does its output differ in structure/detail from the
   confirmed-daily-summary path?
4. Does anything in this function today accept prior report content
   (e.g. a previously `corrected_content`) as seed/context input for
   generation? If nothing exists, state that explicitly rather than
   omitting the question.
5. Confirm current header version, and confirm/contradict against
   `hotfix_weekly-report-prompt-builder_spec.md`'s recorded version
   (`v1.7 → v1.9`, 20260605) — has it moved since, and if so quote the
   version history entries added after that date.

---

# Section 3 — Internal Content Filtering, Current State

**File:** `workmain/ai/prompt_builder.py`, `workmain/database/repositories/reports_repo.py`.

Item #46's Gap 3 (internal content pollution via `get_confirmed_dailies()`)
was described 20260623 — after `hotfix_weekly-report-prompt-builder_spec.md`
(20260605) already added `data_sources` gating and `ai_instruction`
injection for the *raw* generation path. Confirm whether that same
protection applies to the **confirmed-daily-summary injection path**
Gap 3 describes, or whether Gap 3 is a genuinely separate, still-open
hole:

1. Quote the exact code path that injects `get_confirmed_dailies()` output
   into the `weekly_client` prompt.
2. Does any tag-aware filtering happen to that injected content, or is it
   injected verbatim from each daily's `content`/`corrected_content`?
3. State plainly: CONFIRMS Gap 3 still open, or CONTRADICTS (already
   mitigated by the June hotfix), with the verbatim code as evidence
   either way.

---

# Section 4 — `get_confirmed_dailies()`

**File:** `workmain/database/repositories/reports_repo.py`.

1. Full current method body, verbatim.
2. Exact filter conditions (date range, `status` values included,
   `report_type`).
3. Confirm current header version.

---

# Section 5 — `slack.py:slack_post` Weekly Anchor Date + Upsert

**File:** `workmain/cli/commands/slack.py`.

1. Full body of the weekly anchor-date computation, verbatim (the logic
   that decides what `report_date` a Thursday `slack post weekly` run
   targets).
2. Full body of the upsert block (recon-cited at lines 820–841), verbatim
   — confirm the exact `report_date` value used to key the upsert, and
   confirm it is computed by the same logic as (1) or a different one.
3. Does this anchor-date value match what Friday's EOD `target_date` would
   be for the same week (i.e., would a lookup keyed on
   `(report_type='weekly_client', report_date=<Friday's target_date>)`
   find the row Thursday's post created)? State the comparison explicitly,
   don't just show both values.
4. Confirm current header version.

---

# Section 6 — Live Data Check (Read-Only)

Run a read-only query against the `workmain` database (no writes) for the
5 most recent `weekly_client` rows, ordered `created_at DESC`. For each,
report: `id`, `report_date`, `status`, `created_at`, length of `content`,
whether `corrected_content` is null, and — if `report_metadata` records
anything about which generation path was used (confirmed vs. raw,
draft vs. final) — quote that field's relevant keys verbatim. State the
exact query used.

---

# Format Notes

- Use the WorkmAIn document header convention (title, doc name + version,
  date) at the top of the output file.
- Quote source code verbatim in fenced code blocks with file path
  comments — do not paraphrase signatures or logic.
- Per `CLAUDE.md`'s recon-discipline lenses: where this recon references
  a prior document's claim (Item #46's gap descriptions, the June hotfix's
  fix descriptions) as a reference to diff against, diff the live code
  against that claim verbatim — don't confirm at the shape level only.
  Where a prior fix's code block is quoted here as "still current," verify
  that against live source rather than trusting the citation.
- If a referenced file/method cannot be located, state that explicitly
  rather than omitting the section.
- Mark each finding CONFIRMS or CONTRADICTS against the specific claim it
  addresses (Item #46's three gaps; the anchor-date match question).
- This is a factual enumeration — do not characterize severity, do not
  propose fixes, do not recommend a remediation path or a Gate 4 design.
  That happens in a separate Role 1 planning session after this recon
  returns.
- Keep this self-contained — the reviewing session will not have live
  access to the repo, only this document.

---

## Findings

_Appended 20260724 by Claude Code / Opus (Role 2), read-only Gate 0 recon.
Factual enumeration only — no severity, no fixes, no Gate 4 design._

### Header versions of all files touched (verbatim)

| File | Version | Date |
|------|---------|------|
| `workmain/ai/prompt_builder.py` | Prompt Builder v2.2 | 20260623 |
| `workmain/database/repositories/reports_repo.py` | Reports Repository v1.5 | 20260717 |
| `workmain/ai/report_generator.py` | Report Generator v1.14 | 20260610 |
| `workmain/workflows/eod_workflow.py` | v1.8 | 20260716 |
| `workmain/cli/commands/eod.py` | EOD v2.14 | 20260611 |
| `workmain/cli/commands/slack.py` | slack.py v1.7 | 20260713 |

---

### Section 1 — Weekday-Mode Dispatch

**1.1 — How the system decides "Thursday draft" vs. "Friday final."**

The weekday branch lives in `eod_workflow.py:_build_step_sequence()`, keyed on
`date.today().weekday()` passed down from `eod.py` (`today_weekday = today.weekday()`
at `eod.py:191`, handed to `get_step_sequence(today_weekday, skip_steps)` at
`eod.py:211`). Verbatim:

```python
# workmain/workflows/eod_workflow.py:1426-1443
    if 'weekly' not in skip:
        if weekday == THURSDAY:
            raw.append(
                ('weekly', '7',
                 'Post weekly draft to Slack (slack post weekly)',
                 _run_slack_weekly_step)
            )
        elif weekday == FRIDAY:
            raw.append(
                ('weekly_report', '7',
                 'Generate weekly report (reports save weekly_client)',
                 _run_weekly_report_step)
            )
            raw.append(
                ('weekly_email', '8',
                 'Create weekly email draft (email save weekly_client)',
                 _run_weekly_email_step)
            )
```

So "Thursday draft" and "Friday final" are **two different step runners selected by
weekday**, not one runner with a mode flag:

- Thursday → `_run_slack_weekly_step` → shells `workmain slack post weekly`
- Friday → `_run_weekly_report_step` → shells `workmain reports save weekly_client --date <target_date>`

The daemon-side cron equivalents corroborate the same weekday split
(`daemon/scheduler.py:531` `day_of_week='thu'` weekly draft;
`daemon/scheduler.py:537` `day_of_week='fri'` end-of-week).

**1.2 — Parameters passed down; is there a `draft=`/`mode=` flag?**

**No explicit draft/mode flag exists anywhere in the chain.** The two paths differ only
in *which subprocess is invoked* and *what `report_date` reaches
`build_weekly_prompt()`*, then Thursday-vs-Friday behavior is **entirely implicit in
which dailies happen to be confirmed at call time** (see Section 2).

- Thursday's `_run_slack_weekly_step` shells `['slack', 'post', 'weekly']` **with no
  `--date`** (`eod_workflow.py:1171`). Inside `slack.py`, `anchor = _parse_date_arg(None)`
  → `date.today()` (the actual calendar Thursday). `slack.py:_run_generation(anchor)`
  calls `generator.generate_report(template_name="weekly_client", report_date=anchor)`.
- Friday's `_run_weekly_report_step` shells `['reports','save','weekly_client','--date',
  target_date.isoformat()]` (`eod_workflow.py:1196`), i.e. `report_date = Friday`.

Dispatch into the prompt builder is in `report_generator.generate_report()`, verbatim:

```python
# workmain/ai/report_generator.py:187-200
            if template_name == 'weekly_client':
                system_prompt, user_prompt = self.prompt_builder.build_weekly_prompt(
                    template_name=template_name,
                    report_date=report_date,
                    filter_client=filter_client,
                    client_id=client_id_filter,
                )
            else:
                system_prompt, user_prompt = self.prompt_builder.build_prompt(
                    template_name=template_name,
                    report_date=report_date,
                    filter_client=filter_client,
                    client_id=client_id_filter,
                )
```

`generate_report()` passes only `report_date` (+ `filter_client`/`client_id_filter`) into
`build_weekly_prompt()` — no draft/final signal. **CONFIRMS Item #46's framing that
Thursday-vs-Friday is implicit in confirmed-daily coverage, not an explicit mode.**

---

### Section 2 — `build_weekly_prompt()` Confirmed-Path / Raw-Fallback Logic

**2.1 — Full current body, verbatim:**

```python
# workmain/ai/prompt_builder.py:159-226
    def build_weekly_prompt(
        self,
        template_name: str,
        report_date: date,
        section_name: Optional[str] = None,
        filter_client: bool = False,
        client_id: Optional[int] = None,
    ) -> Tuple[str, str]:
        """Build the weekly client report prompt with confirmed daily context.
        ...docstring elided for length; unchanged from source...
        """
        week_start = report_date - timedelta(days=report_date.weekday())
        week_end = week_start + timedelta(days=4)  # Mon–Fri

        db = get_db()
        session = db.get_session()
        try:
            reports_repo = ReportsRepository(session)
            confirmed = reports_repo.get_confirmed_dailies(week_start, week_end)
        finally:
            session.close()

        system_prompt, raw_user_prompt = self.build_prompt(
            template_name=template_name,
            report_date=report_date,
            section_name=section_name,
            filter_client=filter_client,
            client_id=client_id,
        )

        weekdays_covered = {r.report_date.weekday() for r in confirmed}
        if weekdays_covered != {0, 1, 2, 3, 4}:
            return system_prompt, raw_user_prompt

        lines = [
            "## Confirmed Daily Summaries",
            "Use the following confirmed daily reports as the source of truth for this week.",
            "Do not infer additional work beyond what is stated here.",
            "",
        ]
        for report in confirmed:
            day_label = report.report_date.strftime("%A %Y-%m-%d")
            content = report.corrected_content if report.corrected_content else report.content
            lines.append(f"### {day_label}")
            lines.append(content or "")
            lines.append("")

        return system_prompt, "\n".join(lines)
```

**2.2 — `weekdays_covered` computation and confirmed-path condition, verbatim:**

```python
# workmain/ai/prompt_builder.py:209-211
        weekdays_covered = {r.report_date.weekday() for r in confirmed}
        if weekdays_covered != {0, 1, 2, 3, 4}:
            return system_prompt, raw_user_prompt
```

**CONFIRMS Item #46's claim** that the confirmed path is gated on
`weekdays_covered == {0, 1, 2, 3, 4}` — verbatim in source (expressed as the negated
early-return `!= {0, 1, 2, 3, 4}`). The confirmed-substitutive block executes only when
all five Mon–Fri weekdays are present in confirmed/corrected `daily_internal` reports.

Because Thursday's draft runs before Friday's daily exists, `weekdays_covered` can be at
most `{0,1,2,3}` on Thursday → the `!=` guard is always true → **the Thursday draft
always takes the raw-fallback branch.** **CONFIRMS** the quoted Item #46 text ("the
confirmed path is unreachable [on Thursday]… The Thursday draft always uses raw data even
if Mon–Thu are fully confirmed"). Note the confirmed-substitutive path **is** reachable on
Friday once all five days are confirmed — the "unreachable" claim is Thursday-scoped, and
the live DB (Section 6) shows Friday rows do exist.

**2.3 — Raw-data fallback branch: what it queries, and how its output structure differs.**

The raw fallback is simply the tuple returned by `self.build_prompt(...)` (line 201–207,
computed unconditionally *before* the coverage check and returned verbatim at line 211).
That is the full template-driven path through `_build_user_prompt` → `_get_section_data`,
which queries **live notes / time_entries / meetings** via `get_for_date_client()` and
renders the template's section titles, per-section `ai_instruction`, and
`data_sources`-gated data (`prompt_builder.py:284-453`).

Structural difference between the two paths (Section 2.3 asks explicitly):

- **Raw-fallback path** (`weekdays_covered != {0,1,2,3,4}`, i.e. Thursday): emits the full
  template scaffold — `## <section title>`, `**Instruction:** <ai_instruction>`, and the
  section's data. The `weekly_client` template's five-question section structure is
  present.
- **Confirmed-substitutive path** (all five days confirmed, i.e. a fully-confirmed
  Friday): the returned `user_prompt` is **only** the hand-built
  `## Confirmed Daily Summaries` block — a flat concatenation of each day's
  `corrected_content`/`content` under `### <Weekday date>` headers. **It contains none of
  the template's section titles, `ai_instruction` fields, or five-question structure**;
  `raw_user_prompt` is computed but discarded. (`system_prompt` is identical across both
  paths — both come from the same `build_prompt()` call, and the template's five-question
  scaffold lives in the *user* prompt, not the system prompt.)

This structural inversion is directly consistent with the live symptom recorded in the
recon preamble (Thursday/Mon–Thu draft matched the template; separately-generated Mon–Fri
report "abandoned the template's five-question structure entirely"): the Mon–Thu draft
hits the template-bearing raw path, the fully-confirmed Mon–Fri report hits the
template-free substitutive path. Stated as fact, not severity.

**2.4 — Does the function accept prior report content as seed/context?**

Partially — **but only for daily reports, never for a prior weekly report.**
`build_weekly_prompt()` reads confirmed/corrected **`daily_internal`** reports via
`get_confirmed_dailies()` and, per day, prefers `corrected_content` over `content`
(`prompt_builder.py:221`). **Nothing in this function (or in `report_generator` /
`slack.py`) feeds a prior `weekly_client` report's `content`/`corrected_content` — e.g.
Thursday's draft row — back in as seed/context for the Friday generation.** There is no
weekly-report-self-seeding path. Stated explicitly per the recon's instruction not to omit
the question.

**2.5 — Version movement vs. `hotfix_weekly-report-prompt-builder_spec.md` (`v1.7 → v1.9`, 20260605).**

**It has moved.** Current header is **Prompt Builder v2.2, 20260623**. Version-history
entries added *after* v1.9, verbatim from the live file header:

```text
# workmain/ai/prompt_builder.py:39-49
- v2.0: Phase 13 DB Schema Sprint Gate 5 — _get_time_entries reads entry.note.content
        instead of the now-dropped entry.description column
- v2.1: Phase 13 Sprint 2 Gate 1a — add build_weekly_prompt(); prepends confirmed
        daily summaries block when calling build_prompt() for weekly_client reports;
        build_prompt() unmodified
- v2.2: Hotfix items-33-34-incomplete-impl — rewrite build_weekly_prompt() (Item 34):
        (1) prefer corrected_content over content for each confirmed daily;
        (2) substitutive path — when all 5 Mon–Fri weekdays are confirmed, lean
        user_prompt replaces raw DB data entirely (token reduction);
        (3) fallback to raw build_prompt() when any weekday lacks a confirmed daily
```

Note the v2.1 history line describes a "prepends confirmed daily summaries block" design
that the **v2.2 rewrite superseded** — the current code (2.1 above) does not prepend to
`build_prompt()` output; in the all-confirmed case it *replaces* it. The current v2.2 body
is authoritative; the v2.1 description is stale narrative history only.

---

### Section 3 — Internal Content Filtering, Current State

**3.1 — Exact code path injecting `get_confirmed_dailies()` output into the prompt:**

```python
# workmain/ai/prompt_builder.py:213-226
        lines = [
            "## Confirmed Daily Summaries",
            "Use the following confirmed daily reports as the source of truth for this week.",
            "Do not infer additional work beyond what is stated here.",
            "",
        ]
        for report in confirmed:
            day_label = report.report_date.strftime("%A %Y-%m-%d")
            content = report.corrected_content if report.corrected_content else report.content
            lines.append(f"### {day_label}")
            lines.append(content or "")
            lines.append("")

        return system_prompt, "\n".join(lines)
```

**3.2 — Any tag-aware filtering on the injected content?**

**No.** Each confirmed daily's `corrected_content` (or `content`) is appended
**verbatim, whole-report**, to the prompt. There is no tag inspection, no
`data_sources` gating, no `ai_instruction`, and no `filter_client` involvement on this
block. The `data_sources`/`ai_instruction` protections added by the June hotfix live
exclusively in `_get_section_data()` (`prompt_builder.py:354-453`), which is on the
**`build_prompt()` raw path** — a path that is *not executed for output* when the
substitutive block runs (its result `raw_user_prompt` is discarded at line 210–211 when
all five days are confirmed). Additionally, the injected units are entire
`daily_internal` reports — the `daily_internal` report type is itself the internal-audience
artifact, so no client-report tag filtering was applied to that text when it was generated
either.

**3.3 — Verdict on Gap 3.**

**CONFIRMS Gap 3 is a genuinely separate, still-open hole** on the confirmed-daily-summary
injection path. The June 20260605 hotfix (`data_sources` gating + `ai_instruction`
injection) mitigated internal-content leakage on the **raw** `build_prompt()` path only;
it does **not** reach the substitutive confirmed-summary path introduced later (v2.1/v2.2,
20260623), which injects whole `daily_internal` report bodies with no tag-aware filtering.
Evidence: the verbatim block in 3.1 performs zero filtering, and the gated code
(`_get_section_data`) is not on this branch.

---

### Section 4 — `get_confirmed_dailies()`

**4.1 — Full current method body, verbatim:**

```python
# workmain/database/repositories/reports_repo.py:167-193
    def get_confirmed_dailies(
        self,
        start_date: date,
        end_date: date,
    ) -> List[Report]:
        """Return confirmed or corrected daily_internal reports for a date range.
        ...docstring elided for length; unchanged from source...
        """
        return (
            self.session.query(Report)
            .filter(Report.report_type == 'daily_internal')
            .filter(Report.status.in_(['confirmed', 'corrected']))
            .filter(Report.report_date >= start_date)
            .filter(Report.report_date <= end_date)
            .order_by(Report.report_date.asc())
            .all()
        )
```

**4.2 — Exact filter conditions:**

- `report_type == 'daily_internal'`
- `status IN ('confirmed', 'corrected')`
- `report_date >= start_date` AND `report_date <= end_date` (inclusive both ends)
- ordered `report_date ASC`
- **no `client_id` filter, no tag filter, no de-duplication** — if two confirmed rows share
  a `report_date`, both are returned, and `weekdays_covered` (a set) would still collapse
  them to one weekday. (Enumeration only.)

**4.3 — Header version:** Reports Repository **v1.5**, 20260717.

---

### Section 5 — `slack.py:slack_post` Weekly Anchor Date + Upsert

**5.1 — Weekly anchor-date computation, verbatim.**

```python
# workmain/cli/commands/slack.py:89-98  (anchor default)
def _parse_date_arg(date_str: Optional[str]) -> date:
    """Parse YYYYMMDD string to date, defaulting to today."""
    if date_str is None:
        return date.today()
    try:
        return datetime.strptime(date_str, "%Y%m%d").date()
    except ValueError:
        raise click.BadParameter(
            f"Invalid date '{date_str}'. Expected format: YYYYMMDD (e.g. 20260312)."
        )
```

```python
# workmain/cli/commands/slack.py:101-112  (range derivation)
def get_draft_date_range(anchor: date) -> tuple:
    """Return (monday, anchor) for the ISO week containing anchor. ..."""
    monday = anchor - timedelta(days=anchor.weekday())  # weekday() Mon=0
    return monday, anchor
```

```python
# workmain/cli/commands/slack.py:619  (in slack_post)
    anchor = _parse_date_arg(date_str)
```

So `report_date` for the post is **`anchor`**, which is the `-d/--date` value or, when
absent, **`date.today()`**. Under EOD Thursday dispatch the subprocess is invoked with **no
`--date`** (Section 1.2), so `anchor = date.today()` = the calendar day the Thursday step
runs. `monday` is derived from `anchor` but is used only for display/range, not as the
upsert key.

**5.2 — Upsert block, verbatim (recon-cited 820–841):**

```python
# workmain/cli/commands/slack.py:814-841
    db = get_db()
    session = db.get_session()
    try:
        from workmain.database.repositories.system_state_repository import SystemStateRepository
        active_client_id = SystemStateRepository(session).get_int('active_client_id')

        existing = session.query(Report).filter(
            Report.report_type == "weekly_client",
            Report.report_date == anchor,
        ).first()

        if existing:
            existing.slack_message_ts = message_ts
            existing.slack_channel = target_channel
            existing.slack_workspace_name = workspace_name
        else:
            new_row = Report(
                report_type="weekly_client",
                report_date=anchor,
                content=report_content,
                slack_message_ts=message_ts,
                slack_channel=target_channel,
                slack_workspace_name=workspace_name,
                client_id=active_client_id,
            )
            session.add(new_row)

        session.commit()
```

The upsert is keyed on `(report_type == "weekly_client", report_date == anchor)`.
`anchor` here is the **same** `anchor` variable from 5.1 (line 619) — the identical
computation, not a different one. The INSERT branch sets `report_date=anchor` as well.
Note the new row is created **without `status`** (defaults to the column default — the live
DB shows Thursday drafts land as `unconfirmed`, Section 6) and **without
`corrected_content`**.

**5.3 — Does Thursday's anchor match Friday's EOD `target_date`? Explicit comparison.**

**No — they do not match.**

- **Thursday post** keys its row on `report_date = anchor = date.today()` at Thursday's
  run = **the Thursday date**.
- **Friday EOD** (`_run_weekly_report_step`, `eod_workflow.py:1196`) generates with
  `--date target_date` and its pre-check/lookup queries
  `report_type='weekly_client', start_date=target_date, end_date=target_date`
  (`eod_workflow.py:1225-1229`) where `target_date` = **the Friday date**.

A Friday lookup keyed on `(report_type='weekly_client', report_date=<Friday's target_date>)`
would query `report_date == Friday`, whereas Thursday's post created a row with
`report_date == Thursday`. **The two dates differ by one day, so Friday's lookup does not
find Thursday's row.** This is confirmed by live data (Section 6): the Thursday draft row
is `report_date=2026-07-23` (Thursday) while Friday's generated rows are
`report_date=2026-07-24` (Friday).

Caveat, stated as fact: this holds under the current EOD wiring where the Thursday step
shells `slack post weekly` with no `--date`. If `slack post weekly` were invoked manually
with `-d <Friday>`, the anchors would coincide — but no code path does that today. **The
answer to the recon's Section 5.3 question, as the system runs today, is: they do NOT
match.**

**5.4 — Header version:** slack.py **v1.7**, 20260713.

---

### Section 6 — Live Data Check (Read-Only)

Query used (Python app connection, read-only, no writes):

```python
from workmain.database.connection import get_db
from workmain.database.models import Report
from sqlalchemy import desc
db = get_db(); s = db.get_session()
rows = (s.query(Report)
          .filter(Report.report_type == 'weekly_client')
          .order_by(desc(Report.created_at))
          .limit(5).all())
# per row: id, report_date, status, created_at, len(content),
#          corrected_content IS NULL, report_metadata keys
```

Result (5 most recent `weekly_client` rows, `created_at DESC`):

| id | report_date | weekday | status | created_at | len(content) | corrected_content NULL? |
|----|-------------|---------|--------|------------|--------------|--------------------------|
| 10984 | 2026-07-24 | Fri | corrected | 2026-07-24 14:36:41 | 2868 | No |
| 10983 | 2026-07-24 | Fri | corrected | 2026-07-24 14:30:14 | 1775 | No |
| 10981 | 2026-07-23 | Thu | unconfirmed | 2026-07-23 14:57:17 | 1753 | Yes |
| 9717  | 2026-07-17 | Fri | confirmed | 2026-07-17 14:57:17 | 1848 | Yes |
| 9123  | 2026-07-16 | Thu | unconfirmed | 2026-07-16 14:05:22 | 1792 | Yes |

**`report_metadata` records nothing about generation path.** For every row the keys are
exactly: `['cost', 'ai_model', 'file_path', 'ai_provider', 'total_tokens',
'prompt_tokens', 'generation_time', 'completion_tokens']` — there is **no** field recording
confirmed-vs-raw or draft-vs-final. There is no way, from a stored row alone, to tell which
`build_weekly_prompt()` branch produced it.

Observations relevant to the recon's questions (facts, not severity):

- **CONFIRMS the Section 5.3 anchor mismatch empirically.** Thursday drafts land on the
  Thursday date (id=10981 `2026-07-23`, id=9123 `2026-07-16`, both `unconfirmed`); Friday
  reports land on the Friday date (id=10983/10984 `2026-07-24`, id=9717 `2026-07-17`). A
  Friday `target_date` lookup would never match the Thursday draft row.
- **CONFIRMS the Thursday draft is "unconfirmed, unstatused"** per the recon preamble:
  both Thursday rows (10981, 9123) are `status=unconfirmed` with `corrected_content` NULL —
  consistent with the `slack_post` INSERT (5.2) omitting `status` and `corrected_content`.
- Two Friday rows for the same `report_date=2026-07-24` (10983, 10984) both `corrected` —
  a separate observation; `get_confirmed_dailies()`-style de-dup does not apply to
  `weekly_client` rows (that method targets `daily_internal` only).

---

### Summary of CONFIRMS / CONTRADICTS

| Claim under test | Verdict | Evidence |
|------------------|---------|----------|
| Item #46 Gap 1 — confirmed path gated on `weekdays_covered == {0,1,2,3,4}` | **CONFIRMS** | `prompt_builder.py:209-211` verbatim |
| Item #46 — Thursday draft always uses raw data (confirmed path unreachable Thursday) | **CONFIRMS** | Thursday can reach at most `{0,1,2,3}`; guard always true; live rows 10981/9123 |
| Item #46 Gap 3 — internal content pollution via `get_confirmed_dailies()` injection | **CONFIRMS still open** | `prompt_builder.py:213-226` injects whole daily bodies, zero tag filtering; June hotfix gating is on the discarded raw path only |
| June hotfix (`data_sources`/`ai_instruction`) protects the confirmed-summary path | **CONTRADICTS** | Gating lives in `_get_section_data` (raw path), not on the substitutive block |
| Anchor-date match: Friday `target_date` lookup finds Thursday's posted row | **CONTRADICTS (they do NOT match)** | Thursday keys `report_date=today()=Thu`; Friday queries `report_date=Fri`; live rows 10981(Thu) vs 10983/10984(Fri) |
| No explicit draft/mode flag in the dispatch chain | **CONFIRMS (implicit only)** | `report_generator.py:187-200`, `eod_workflow.py:1426-1443` |
| `build_weekly_prompt()` seeds from a prior weekly report's content | **CONTRADICTS (no such path)** | reads `daily_internal` only; no weekly self-seed anywhere |
| `report_metadata` records the generation path used | **CONTRADICTS (not recorded)** | Section 6 — keys are cost/token/provider only |

_End of recon findings. No fixes, severities, or Gate 4 design proposed — that is a
separate Role 1 planning session._

---

## Follow-up Findings — Weekly Report Note-Tag Sourcing

_Appended 20260724 by Claude Code / Opus (Role 2), read-only. Answers three follow-up
questions from Claude Desktop (Role 1) verifying how the raw-fallback path
(`build_weekly_prompt()` → `build_prompt()` → `_get_section_data()`) sources and filters
notes/meetings/time-entries. Factual enumeration only._

Files referenced (header versions, verbatim): `workmain/ai/prompt_builder.py` Prompt
Builder v2.2 20260623; `workmain/database/repositories/notes_repo.py`; `templates/reports/
weekly_client.json` version 1.2; `workmain/templates_engine/loader.py`.

### FQ1 — Does `_get_section_data()` scope to the single `report_date` or expand to a week range?

**Expands to the full Mon–Fri week range — it does NOT use `report_date` as a one-day
window.** `build_weekly_prompt()` passes only a single `report_date` into `build_prompt()`,
but `_get_section_data()` delegates all scoping to `_get_date_range()`, which branches on
the template's `metadata.frequency`:

```python
# workmain/ai/prompt_builder.py:386-387  (_get_section_data)
        # Get date range for the section
        date_range = self._get_date_range(template, report_date)
        start_date, end_date = date_range
```

```python
# workmain/ai/prompt_builder.py:470-480  (_get_date_range)
        metadata = template.get("metadata", {})
        frequency = metadata.get("frequency", "daily")

        if frequency == "daily":
            return report_date, report_date
        elif frequency == "weekly":
            # Get Monday to Friday of the week containing report_date
            days_since_monday = report_date.weekday()
            start_date = report_date - timedelta(days=days_since_monday)
            end_date = start_date + timedelta(days=4)  # Friday
            return start_date, end_date
```

`weekly_client.json` declares `"frequency": "weekly"` (line 139), and the loader returns
the raw JSON dict unchanged (`loader.py:84` `template = json.load(f)` → `loader.py:104`
`return template`), so the `weekly` branch always fires. The single `report_date` is used
only as the anchor from which Mon–Fri is derived; every note / time-entry / meeting query
for every section runs against `[Monday … Friday]`.

Note: this is the **same** Mon–Fri window `build_weekly_prompt()` independently computes for
`get_confirmed_dailies()` (`prompt_builder.py:190-191` — `week_start = report_date -
timedelta(days=report_date.weekday())`, `week_end = week_start + timedelta(days=4)`).
Separate code, identical dates — the raw-fallback live-data window and the confirmed-dailies
window converge.

### FQ2 — Exact per-section `tag_filter`, and the code that reads and applies it.

All five `weekly_client.json` sections declare a `tag_filter`. Verbatim values:

| # | Section | `include` | `exclude` | `data_sources` |
|---|---------|-----------|-----------|----------------|
| 1 | what_working_on | `client-report`, `both` | `internal-only`, `info-only` | `notes`, `time_entries` |
| 2 | completion_timeline | `carry-forward`, `client-report`, `both` | `internal-only`, `info-only` | `notes` |
| 3 | risks_blockers | `blocker`, `client-report`, `both` | `internal-only`, `info-only` | `notes` |
| 4 | unclear_requests | `client-report`, `both` | `internal-only`, `info-only` | `notes` |
| 5 | artifacts_location | `client-report`, `both` | `internal-only`, `info-only` | `notes` |

Read and passed through, verbatim:

```python
# workmain/ai/prompt_builder.py:371-374  (_get_section_data)
        tag_filter = section.get("tag_filter", {})
        tags_include = tag_filter.get("include", [])
        tags_exclude = tag_filter.get("exclude", [])
```

```python
# workmain/ai/prompt_builder.py:391-396  (_get_section_data → _get_filtered_notes)
        notes = self._get_filtered_notes(
            start_date=start_date,
            end_date=end_date,
            tags_include=tags_include,
            tags_exclude=tags_exclude
        )
```

```python
# workmain/ai/prompt_builder.py:513-520  (_get_filtered_notes)
        notes = self.notes_repo.get_for_date_client(
            start_date=start_date,
            end_date=end_date,
            include_tags=tags_include if tags_include else None,
            exclude_tags=tags_exclude if tags_exclude else None,
            client_id=self._client_id,
            filter_client=self._filter_client,
        )
```

The SQL semantics that decide which tags actually pass through, verbatim:

```python
# workmain/database/repositories/notes_repo.py:276-281  (get_for_date_client)
        if include_tags:
            query = query.filter(Note.tags.op('&&')(include_tags))

        if exclude_tags:
            for tag in exclude_tags:
                query = query.filter(~Note.tags.op('@>')([tag]))
```

Confirmed semantics as the system runs today:

- **Include = OR (array overlap `&&`).** A note is admitted if it carries **at least one**
  of the section's include tags (e.g. §1 admits any note tagged `client-report` OR `both`).
- **Exclude = drop-on-any-match.** Each exclude tag adds a `~ Note.tags @> [tag]` clause, so
  a note is dropped if it carries **any** of `internal-only` / `info-only`.
- Net for the raw-fallback (Thursday) path: only `client-report` / `both` (plus
  `carry-forward` in §2, `blocker` in §3) tagged notes reach the client prompt;
  `internal-only` / `info-only` are hard-excluded at the DB layer. **This is exactly the
  per-section filtering the confirmed-summary substitutive path bypasses** (main-recon §3),
  making the contrast precise: raw path = five per-section include/exclude filters applied;
  substitutive path = whole `daily_internal` bodies, no tag filter.

### FQ3 — Do meetings feed `weekly_client` generation today? Are they tag-filtered?

**No — meetings do not feed `weekly_client` on the raw path today.** Meeting fetch is gated
on each section declaring `"meetings"` in `data_sources`:

```python
# workmain/ai/prompt_builder.py:380-382  (_get_section_data)
        data_sources = section.get("data_sources", [])
        include_time_entries = ("time_entries" in data_sources) if data_sources else True
        include_meetings = ("meetings" in data_sources) if data_sources else True
```

```python
# workmain/ai/prompt_builder.py:443-451  (_get_section_data)
        if include_meetings:
            meetings = self._get_meetings(start_date, end_date)
            if meetings:
                parts.append("\n### Meetings:")
                for meeting in meetings:
                    time_str = meeting.get("start_time", "")
                    title = meeting.get("title", "Untitled")
                    attendees = meeting.get("attendees", 0)
                    parts.append(f"- {time_str} - {title} ({attendees} attendees)")
```

Every `weekly_client.json` section declares a **non-empty** `data_sources` that **omits**
`"meetings"` (§1 `["notes","time_entries"]`; §2–§5 `["notes"]`). Because `data_sources` is
non-empty for all five, the `else True` fallback never applies, so
`include_meetings = ("meetings" in data_sources)` = **False for every section**.
`_get_meetings()` is therefore never called during `weekly_client` generation.

Were a section to opt in, the fetch carries **no tag parameters** — meetings would bypass
tag filtering entirely (only date + client scoping):

```python
# workmain/ai/prompt_builder.py:573-585  (_get_meetings)
        meetings = self.meetings_repo.get_for_date_client(
            start_date=start_date,
            end_date=end_date,
            client_id=self._client_id,
            filter_client=self._filter_client,
        )
```

So: meetings do not reach `weekly_client` today, and the meeting-fetch path is not subject
to the per-section tag filtering that notes receive (it has no `include_tags`/`exclude_tags`
arguments) — only `filter_client`/`client_id` would apply if a section ever declared
`"meetings"`.

### Follow-up Summary

| Question | Finding | Evidence |
|----------|---------|----------|
| FQ1 — note/meeting/time-entry scope on the raw path | Expands to Mon–Fri week (via `metadata.frequency == "weekly"`), not single `report_date` | `prompt_builder.py:386-387`, `470-480`; `weekly_client.json:139`; `loader.py:84,104` |
| FQ2 — which tags pass through | Include = OR (`&&` overlap); exclude = drop-on-any (`~ @>`); only `client-report`/`both` (+`carry-forward` §2, `blocker` §3) admitted, `internal-only`/`info-only` excluded | `prompt_builder.py:371-374,391-396,513-520`; `notes_repo.py:276-281`; template §1–§5 |
| FQ3 — meetings in `weekly_client` | Not fed today (no section declares `"meetings"` in `data_sources`); if they were, they bypass tag filtering (no tag args on `_get_meetings`) | `prompt_builder.py:380-382,443-451,573-585`; `weekly_client.json` data_sources |

_End of follow-up findings. No fixes, severities, or Gate 4 design proposed._

