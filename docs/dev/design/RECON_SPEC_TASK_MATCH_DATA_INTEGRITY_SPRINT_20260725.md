# Task Match Data Integrity Sprint — Recon

**Status:** Shipped
**Kind:** Recon
**Author:** Spanner (Role 1)
**Date:** 20260725
**Originating item:** Backlog Items #71, #67, #70, #66
**Disposition:** Promoted to `docs/dev/specs/TASK_MATCH_DATA_INTEGRITY_SPRINT_SPEC_v1_3.md`; shipped v1.28.0

---

## Critical Instructions — Read Before Acting

**This is a read-only pass. No code changes, no fixes, no refactors, no
suggestions inline with findings.** Verbatim source quotations and
observations only. Read-only shell commands (grep, psql/app-connection
SELECT, git log) are permitted where explicitly requested below. No writes
of any kind outside the Findings section of this document.

**Pitfall #12 applies throughout (component-verified ≠ integration-verified).**
Section H is a census: its value is completeness. Do not stop at the
surfaces named as verification targets — enumerate from the constructors
and service entry points outward so unnamed surfaces are found, not
assumed absent. For every surface: trace provenance (what invokes it,
under what conditions, in whose daily flow), not just existence.

**Prior recon dependency:** This recon extends
`RECON_SPEC_ITEM66_TASK_MATCH_QUALITY_20260725.md` (sections E/F/G,
findings complete). Cite its findings by section letter rather than
re-verifying, EXCEPT where a question below explicitly asks you to
re-examine or extend one. Sections here are lettered H/I/J to continue
that sequence.

**Version anchors:** codebase v1.26.1, `main`==`dev`. Verify against file
headers on disk and quote line ranges as found NOW.

**Output:** Append all findings to the END of this same file, below the
`## Findings` placeholder. Do not create a separate output file. Complete
and document each section in full before proceeding to the next. Work
sequentially; no parallel agents or sub-tasks.

---

## Purpose

Gate 0 recon for the Task_Match_Data_Integrity Sprint (pre-sprint feature
effort ahead of the Slack_LLM_Completion_Sprint). Produces the source
facts needed to spec:

- Gate 1 — canonical CF→TaskStatus hook placement in the service-layer
  write path (Section H: which surfaces write notes, through what path,
  with what tag capability, with what hook coverage today)
- Gate 2 — `workmain tasks` command block correction (Section J: what the
  command block can and cannot do today at real data volumes)
- Gate 3 — data repair: orphan backfill scope and stale-pool housekeeping
  (Section I: the true orphan population, all dates, and whether the
  existing 148 task rows are PC-2 backfill artifacts or live hook output)

Sprint context: #66 recon Section F established that TaskStatus creation
exists ONLY on the `notes add`/`notes edit` CLI branches, and that Ray's
actual note entry runs through `notes log -m <meeting>` and `time add`
(plus Slack since 2026-06-25) — surfaces whose hook coverage F never
examined because F's grep found no `ensure_active` callers there. The
working hypothesis to test (not assume): the hook may never have covered
Ray's real capture surfaces at all, making the Feb–May task rows a PC-2
backfill artifact rather than evidence of a formerly working live hook —
and making the orphan population much larger than the 16 post-cutover
notes counted in F4.

---

## Section H — Complete Note Write-Surface Census (HIGHEST PRIORITY)

Goal: a complete map of every code path that creates a Note row, so the
Gate 1 spec can place the CF→TaskStatus hook at the point ALL of them
traverse — integrating every surface, none parallel, no back channels.

H1. Enumerate EVERY code path that constructs/persists a Note. Work from
    the inside out: (a) grep all `Note(` constructor calls; (b) all
    creation methods on the notes repository and their callers; (c) all
    callers of `notes_service.create_note` (and any other note-writing
    service function). Quote each call site verbatim with file, version
    header, line range.

H2. For EACH surface found in H1, state:
    - What invokes it (CLI command, EOD step, daemon trigger, Slack
      action, sync/import job, script)
    - Whether it routes through `notes_service.create_note` or bypasses
      it (direct repo / direct model construction)
    - Whether tags can be supplied at creation, and specifically whether
      a `carry-forward` tag can arrive on that surface (user-supplied,
      hashtag-parsed, defaulted, or impossible)
    - Whether the CF→TaskStatus hook fires today (per F1, expected: only
      `notes add`/`notes edit`)
    - Whether it is part of Ray's daily flow

    Verification targets that MUST each appear in the map with explicit
    findings (do not limit the census to these — H1's grep defines the
    boundary): `notes add`, `notes edit`, `notes log` (including the
    `-m <meeting>` editor flow — does the multi-line editor create one
    note per line, and how are tags attached per line?), `time add`
    (does it create a Note row per notes-as-source-of-truth, or reference
    an existing one?), meeting workflows/commands that write notes, EOD
    workflow steps that create notes (corrections, condensation
    artifacts, forwarding?), Slack `action_executor` paths —
    `_execute_create_note` AND `_execute_create_time_entry` (does a Slack
    time entry create a Note?), report correction `apply_correction`,
    Clockify sync, Outlook ICS import, and any scripts/ backfills still
    invocable.

H3. Deliverable: a single mapping table — surface → invoker → write path
    (service / direct repo / direct model) → tags possible? → CF possible?
    → hook fires? → in daily flow? One row per surface. This table is the
    Gate 1 spec's foundation; completeness over brevity.

H4. Identify the convergence point(s): if the hook were placed in
    `notes_service.create_note`, which H3 rows would be covered and which
    would still bypass it? If any surface bypasses the service layer
    entirely, quote the bypass verbatim — those are the seams Gate 1 must
    either converge or explicitly except.

H5. Tag-transition coverage: beyond creation, which surfaces can MODIFY
    a note's tags (adding or removing `carry-forward` after creation)?
    Per F1, `notes edit` handles both transition directions. List every
    other tag-mutating surface (CLI, Slack, EOD correction paths) and
    whether it handles the CF transition today.

## Section I — Orphan Census and Task-Row Provenance

Goal: the true repair scope for Gate 3, and a correct read of history.

I1. Full orphan census (read-only DB): count of ALL notes with
    `tags @> ARRAY['carry-forward']` that have no task_status row — all
    dates, not just post-2026-06-24. Break down by month and by
    `Note.source` value (`meeting`/`task`/`ad-hoc` per models.py:221).
    Also quote the inverse: CF-tagged notes that DO have task rows, by
    month — the overlay of the two distributions against F4's task
    timeline is the evidence for I2.

I2. Backfill vs live-hook determination for the existing 148 task rows:
    - Quote the task_status table schema (does it carry its own
      `created_at`/timestamp independent of the note's?).
    - If yes: group task_status rows by their OWN creation timestamp
      (day granularity). A concentration on one or few days ≈ backfill;
      a spread tracking note dates ≈ live hook firing. Quote the
      distribution.
    - Search git history and `scripts/`/`scripts-deprecated/` for any
      PC-2-era backfill mechanism (migration, one-time script, test
      fixture run against live DB) that could have produced the Feb–May
      rows. F3 found no such path exists NOW; check whether one EXISTED
      and was removed (`git log --diff-filter=D`, and `-S "ensure_active"`
      / `-S "task_status"` across the repo history, not just notes.py).
    - Conclude explicitly: were the Feb–May rows created live at
      note-entry time, or in bulk after the fact? If indeterminate,
      say so and state what evidence is missing.

I3. task_status id-sequence gap: `MAX(task_status.id) = 2538` with only
    148 rows (F5) — ~2,390 consumed ids with no surviving rows. Explain:
    quote any delete call sites on the tasks repo; check for test suites
    that touch the live DB vs fixtures; check sequence `last_value` and
    any ON CONFLICT / rollback patterns that consume ids. If the
    explanation is historical churn with no current-code cause, state
    that; if deletes are reachable from live surfaces, quote them.

I4. Housekeeping facts for Gate 3's dismissal pass: of the 143 active
    tasks, quote the age distribution (by note created_date month) and
    the status-transition surfaces available today (per J) — enough for
    Role 1 to design the S4 stale-dismissal flow without guessing.

## Section J — `workmain tasks` Command Block Access Audit

Goal: facts for the Gate 2 spec — what the corrected command block must
support so tasks are fully manageable OUTSIDE the EOD flow. (Design
decisions remain Role 1's; this section documents current capability and
gaps only.)

J1. Full inventory of the `tasks` group at v1.26.1: `list`, `show`,
    `today`, `complete`, `dismiss`, `carryover`. For each: quote the
    signature (arguments, options, defaults), the repo calls it makes,
    and its limit/filter behavior. Incorporate G1–G3 by reference; do not
    re-quote what G already established.

J2. Capability gaps at real data volume (143 active): state, per
    operation, whether it is practically usable —
    - Can a user page or scope beyond the 20-row cap other than `-n 0`?
    - Can `complete`/`dismiss` act on more than one task per invocation
      (bulk, ranges, filters)? Quote signatures.
    - Can a dismissal/completion carry a reason/note? (Compare EOD Step
      3c's `[c]/[d]/[s]` semantics — quote what those write vs what the
      CLI commands write; are they equivalent state transitions?)
    - Is there any date-range or source or tag filter on `list` beyond
      what G1 quoted?

J3. Deprecation state: `carryover` is deprecated pointing at `list`, but
    per G it is currently the ONLY uncapped active view. State what
    functionality would be lost if `carryover` were removed today with
    `list` unchanged. Also `today`: quote its scope (created today only?)
    and note whether any command answers "what should I be working on"
    (active tasks, all ages) without the cap.

J4. CLI_STANDARDS conformance sweep for the group beyond G4's `--all`
    finding: option naming/short-forms vs §5.3, help-text accuracy
    (G1 already flagged the `list` docstring; check the others), output
    format vs standards. List each deviation with the standard's wording
    quoted.

---

## Findings

<!-- Opus: append all findings below this line, section by section
     (H, then I, then J). Verbatim quotes with file/version/line ranges.
     Do not edit anything above this line. -->

**Recon performed:** 2026-07-25, Opus (Role 2). Read-only. Codebase v1.26.1, `dev` ==
`main` (verified in #66 recon same session). Extends
`RECON_SPEC_ITEM66_TASK_MATCH_QUALITY_20260725.md` (E/F/G). File versions cited (header
line): `notes.py` v4.2, `time.py` v1.7, `meetings.py` v4.5, `tasks.py` v2.2,
`clockify/sync.py` v1.4, `time_entry_service.py` v1.0, `notes_service.py` v1.0,
`action_executor.py` v1.4, `notes_repo.py` v2.1, `task_status_repo.py` v1.1.

> **⚠ This recon materially corrects #66 Section F.** #66 F1 stated TaskStatus creation
> "exists ONLY on the `notes add`/`notes edit` CLI branches" and F3 concluded the hook
> "was byte-stable and firing live Feb–May, then the 2026-06-25 Slack cutover stopped it."
> The DB evidence below (I2) shows the 147 Feb–May task rows are a **one-time PC-2
> migration-015 backfill**, not live-hook output, and that the live hook has fired
> **exactly once ever** (2026-06-24). The hook never meaningfully covered Ray's real
> capture surfaces. Details in Section I.

---

### Section H — Complete Note Write-Surface Census

**H1 — The single Note construction point.** `Note(` is constructed in exactly one place
in `workmain/` (excluding the `__repr__` at models.py:247): `NotesRepository.create()`,
`notes_repo.py` **v2.1**, line 121. Every note that exists was made by a caller of
`NotesRepository.create()`. That method accepts `tags: List[str]` and
`source: str = 'ad-hoc'` (notes_repo.py:84-92), so **any** caller can pass a
`carry-forward` tag. Grepping all `.create(` note callers + all `create_note` service
callers yields **twelve** live call sites (two through a service, ten direct-to-repo).

**H2/H3 — Surface census.** One row per surface. "Write path": service = through
`notes_service.create_note`/`time_entry_service.create_time_entry`; direct = calls
`NotesRepository.create()` itself. "Hook" = does the CF→TaskStatus `ensure_active` fire
(per F1, only the `notes.py` add/edit branches carry it).

| # | Surface | Invoked by | Write path | Tags at create | CF reachable? | Hook fires? | Ray daily flow? |
|---|---------|-----------|-----------|----------------|---------------|-------------|-----------------|
| 1 | `notes add` (primary note) | CLI `workmain notes add` | **service** (`create_note`, notes.py:366) | user `--tags` (parsed) | **yes** | **YES** (notes.py:375-377) | yes |
| 2 | `notes add` → meeting time-entry follow-on | CLI, after #1 when note has a meeting | direct (notes.py:402) | hard-coded `['both']` | no | no | occasional |
| 3 | `notes log -m <meeting>` (per-line editor) | CLI `workmain notes log` | direct, **one note per line** (notes.py:701) | **per-line inline `#cf`** (parse_tags, notes.py:694; prompt advertises `#cf` at :669) | **yes** | **no** | **yes (primary)** |
| 4 | `notes log` condensed summary | CLI, after #3 | direct (notes.py:737) | hard-coded `['both']` | no | no | yes |
| 5 | `time add` meeting path | CLI `workmain time add -m` | direct (time.py:313) | user `--tags` (time.py:300-308) | **yes** | no | **yes** |
| 6 | `time add` non-meeting path | CLI `workmain time add` | **service** (`create_time_entry`, time.py:333 → time_entry_service.py:84) | user `--tags` | **yes** | no | **yes (primary)** |
| 7 | `time add` extra note | CLI, after #5 (confirm prompt) | direct (time.py:361) | inherits `note_tags` | **yes** | no | occasional |
| 8 | `meetings <flow>` time-entry note | CLI meetings path (meetings.py:752) | direct | hard-coded `['both']` | no | no | occasional |
| 9 | `meetings condense` note | CLI `workmain meetings condense` (meetings.py:940) | direct | hard-coded `['both']`, source `condensed` | no | no | yes |
| 10 | Slack create-note | `action_executor._execute_create_note` (action_executor.py:164) | **service** (`create_note`) | intent `tags` (pass-through) | **yes** | no | yes (Slack) |
| 11 | Slack create-time-entry | `action_executor._execute_create_time_entry` (action_executor.py:125) | **service** (`create_time_entry`) | schema has **no** tags field (v1.6); always `None` (action_executor.py:119-122) | **no (today)** | no | yes (Slack) |
| 12 | Clockify import | `clockify/sync.py:330` | direct | hard-coded `['internal-only']`, source `clockify` | no | no | yes (sync) |

EOD workflow steps create **no** notes (grep of `eod_workflow.py` for `.create(` finds
none; its report corrections write `reports.corrected_content` via
`reports_repo.apply_correction`, not notes — reports_repo.py:176). `note_condenser.py` only
writes `ai_costs`. `gdocs.py`/`field_manager.py` instantiate `NotesRepository` for reads
only. So the census is complete at twelve.

**Surfaces where a `carry-forward` tag can actually land** (CF reachable = yes): #1
`notes add`, #3 `notes log`, #5/#6/#7 `time add`, #10 Slack note. Of these, **only #1
fires the hook.** #3, #5, #6, #7, #10 all admit CF and produce **no** TaskStatus row.

**H4 — Convergence point.** The only point all twelve traverse is **`NotesRepository.create()`**
(notes_repo.py:121). Placing the hook in `notes_service.create_note` would cover **only
rows #1 and #10** (the two `create_note` callers) — it would still miss every direct-repo
surface (#2,#3,#4,#5,#7,#8,#9,#12) **and** the entire `time_entry_service` path (#6, #11),
because `time_entry_service.create_time_entry` calls `NotesRepository.create()` directly,
not `notes_service.create_note`:
```python
# time_entry_service.py v1.0:84-90
    note = NotesRepository(session).create(
        content=description,
        tags=resolved_tags,
        source="task",
        client_id=active_client_id,
        created_at=note_created_at,
    )
```
The two services are **siblings** that both bottom out at the repo; neither calls the
other. So the service layer is **not** a true convergence seam for this hook. The only
seams that cover 100% of surfaces are (a) `NotesRepository.create()` itself, or (b) both
`notes_service.create_note` **and** `time_entry_service` **and** each of the eight
direct-repo call sites individually. Which of these to use — and whether a cross-entity
side-effect (creating a `task_status` row) belongs in the data-access repo — is a Gate 1
design decision for Role 1; this recon only maps the seams. The verbatim direct-repo
bypasses Gate 1 must converge or explicitly except are rows #2 (notes.py:402), #3
(notes.py:701), #4 (notes.py:737), #5 (time.py:313), #7 (time.py:361), #8 (meetings.py:752),
#9 (meetings.py:940), #12 (sync.py:330).

**H5 — Tag-transition (post-creation CF add/remove) coverage.** `NotesRepository.update()`
(notes_repo.py:331) can change tags. Its callers:
- **`notes edit`** (notes.py:488) — the **only** surface that handles the CF transition,
  both directions: `ensure_active` on add, `set_dismissed_by_tag_removal` on remove
  (notes.py:500-507, per F1). This is also the only route by which a note *not* created
  through `notes add` can ever acquire a task row (see I2).
- **`time edit`** (time.py:439) — `NotesRepository(session).update(note_id=entry.note_id,
  content=description)` — passes **content only**, `tags` omitted (defaults to None = keep
  existing). Cannot add/remove CF; no transition handling.
- `meetings_repo.py:625,651` — bulk `.update({Note.meeting_id: …})` reassignments; never
  touch tags.
- **Slack / `action_executor`** — has no note-tag-edit action at all (action types are
  create_note, create_time_entry, update_task, defer_task, deduplicate_task, confirm/correct
  report, write_correction_note; `update_task` transitions task *status*, not note tags).
  No CF transition path from Slack.

So: **exactly one surface (`notes edit`) can transition a CF tag on an existing note**, and
it is a manual CLI command. No time-edit, no Slack, no EOD path can.

---

### Section I — Orphan Census and Task-Row Provenance

**I1 — Full orphan census (all dates).** CF-tagged notes with **no** task_status row:

| Month | Orphans |
|---|---|
| 2026-05 | 3 |
| 2026-06 | 11 |
| 2026-07 | 16 |
| **Total** | **30** |

By `Note.source`: **`task` = 16, `meeting` = 14, `ad-hoc` = 0, `condensed`/`clockify` = 0.**
Every orphan originates from a `time add` (source `task`) or a `notes log`/meeting-flow
(source `meeting`) surface — i.e. exactly the surfaces H showed admit CF but never fire the
hook. **Zero `ad-hoc` orphans** (every `notes add` CF note has a task row). The 16
post-2026-06-24 figure from #66 F4 was a floor; the true all-dates orphan population is
**30** and climbing (16 in July alone).

CF notes that **do** have task rows, by note month (I1c): 2026-02→31, 03→44, 04→50, 05→22,
06→1. (This is the same distribution #66 F4 read as a "creation timeline" — I2 shows why
that reading was wrong.)

Full CF-note population by month × source (context for the crossover):
Feb {meeting 17, task 13, condensed 1}; Mar {meeting 22, task 22}; Apr {meeting 26,
task 24}; May {meeting 13, task 11, ad-hoc 1}; Jun {task 9, meeting 3}; Jul {meeting 10,
task 6}. CF notes have **always** been overwhelmingly `meeting`/`task` source; `ad-hoc`
(the one hooked surface) accounts for **1 CF note in the entire DB**.

**I2 — Backfill vs live-hook: the 147 Feb–May rows are a migration backfill, confirmed.**
- `task_status` carries its **own** `created_at` (models.py:368,
  `created_at = Column(DateTime, nullable=False, default=datetime.now)`), independent of
  the note's.
- **Migration `015_task_status.sql` (Phase 12 / PC-2) contains an explicit backfill** that
  copies each note's `created_at` into the task row:
  ```sql
  -- 015_task_status.sql:19-24
  -- Backfill: create active records for all existing carry-forward notes
  INSERT INTO task_status (note_id, status, created_at, updated_at)
  SELECT id, 'active', created_at, NOW()
  FROM   notes
  WHERE  'carry-forward' = ANY(tags)
  ON CONFLICT (note_id) DO NOTHING;
  ```
  Because the backfill sets `task_status.created_at = notes.created_at`, grouping task rows
  by their own `created_at` reproduces the *notes'* date spread — it does **not** indicate
  live firing. (#66 F never examined migration 015; my prior "no other creation path
  exists" grep was on `notes.py` history only. This is the removed/pre-existing mechanism
  I2 asked to find — it was never removed; it ran once and its rows persist.)
- Partitioning task rows at the migration date makes it unambiguous:
  - **`created_at ≤ 2026-05-28`: 147 rows**, task_status ids **1–147 contiguous**, max such
    `created_at` = **2026-05-27 14:27** (the last CF note existing when the migration ran).
  - **`created_at > 2026-05-28`: exactly 1 row** — `task_status.id = 2538`, `note_id = 15053`,
    `created_at = 2026-06-24`, `source = task`, `status = active`.
- **Conclusion (explicit):** the 147 Feb–May task rows were created **in bulk by migration
  015**, not live at note-entry time. The live `ensure_active` hook has produced **exactly
  one** task row in the entire history of the system (2026-06-24, id 2538) — and that note
  is `source='task'` (a `time add` note), so it got its row via a **`notes edit`
  re-tagging** (the only post-hoc route, H5), not via any creation surface. The recon's
  working hypothesis (lines 59-63) is **confirmed**: Feb–May rows are a PC-2 backfill
  artifact; the hook never covered Ray's real capture surfaces (`time add`, `notes log`,
  meetings) — those have produced CF notes continuously (Feb→July) and essentially none
  ever received a task row except via the one-time backfill snapshot and one manual edit.

**I3 — The id-sequence gap is test-fixture sequence churn, not deletes.** Facts:
`MIN/MAX/COUNT(task_status.id) = 1 / 2538 / 148`; `task_status_id_seq.last_value = 5158`.
Distribution: **147 rows in ids 1–147** (the contiguous backfill), **1 row at id 2538**, and
nothing else — yet the sequence has advanced to 5158. So ~2,390 ids (148→2537) and ~2,620
ids (2539→5158) were consumed with zero surviving rows. The only delete path on tasks is
the FK `ON DELETE CASCADE` from `notes` (models.py:365) triggered by
`NotesRepository.delete()` (notes_repo.py:382-397, reachable via `workmain notes delete`),
but a cascade removes the note **and** its task together and cannot explain surviving-row
gaps between contiguous backfill ids and the single live id. The signature — one live
`INSERT` (committed, id 2538) surrounded by thousands of unused ids — is the classic
Postgres pattern of **rolled-back test transactions consuming `nextval` without
committing** (sequences are non-transactional). The test suite creates `task_status` rows
under the `db_session` fixture (rolled back per test), advancing the sequence each run.
**There is no current-code, live-surface delete that explains the gap; it is historical
test churn.** (Consequence for any Gate 3 repair: `task_status.id` is meaningless as a
volume/timeline signal — use `created_at` and `note_id`, as I2 does.)

**I4 — Housekeeping facts for a Gate 3 stale-dismissal pass.** The 143 active tasks by note
`created_date` month: **2026-02 → 31, 03 → 44, 04 → 50, 05 → 16, 06 → 1.** (The 5
`completed` rows are all backfill-era May notes plus the ad-hoc PC-2 test note id 147; no
live completions.) So **142 of 143 active tasks are ≥ 2 months stale** (note dates Feb–May,
all pre-backfill), and the pool has had **one** genuine addition since. The available
status-transition surfaces for a dismissal pass are (per J): CLI `tasks complete` / `tasks
dismiss` (one task per invocation, no bulk), EOD Step 3c `[c]/[d]/[s]`, and Slack
`update_task`/`defer_task`/`deduplicate_task`. None supports bulk or filtered dismissal
today — a mass stale-dismissal of 142 rows would require 142 individual invocations or a
new bulk capability (Gate 2/Gate 3 design input for Role 1).

---

### Section J — `workmain tasks` Command Block Access Audit

**J1 — Inventory at v1.26.1** (`tasks.py` v2.2). Six commands:

| Command | Signature | Repo call | Limit/filter behavior |
|---|---|---|---|
| `list` | `--status`(def `active`), `--all`(flag), `--search/-s`, `--date/-d`, `--limit/-n`(def **20**) | `get_filtered(status, search, date_filter, limit)` | **caps at 20** unless `-n 0`; `--all`→status only; `--date` = single-day equality (G1) |
| `show` | `<identifier>` (ID or content substring) | `_resolve_task` → `get_by_note_id` | read-only detail; renders status, timestamps, forwarding_note_id, meeting, tags |
| `today` | `--search/-s` | `get_filtered(status='active', date_filter=today, limit=0)` | **uncapped** but scoped to notes `created_date == today` only |
| `complete` | `<identifier>` | `set_completed(note_id)` | **single** task; writes status/completed_at/updated_at only |
| `dismiss` | `<identifier>` | `set_dismissed(note_id)` | **single** task; writes status/completed_at/updated_at only |
| `carryover` (deprecated) | `--all`(redundant), `--limit/-n`(def **None→0**) | delegates to `list` with `limit=0` | **uncapped** active view (G3) |

`show`/`complete`/`dismiss` resolve their target via `_resolve_task` (tasks.py:47-106):
digit → `get_by_id`; else `find_by_content_like` with an interactive picker on multiple
matches; exits with a hint if the note exists but has no task row (tasks.py:97-104 —
"Note N exists but is not tracked as a task. Use 'workmain notes edit' to add the
carry-forward tag first").

**J2 — Capability gaps at 143 active.**
- **Paging/scope beyond 20:** the only ways to see past the cap are `list -n 0` (the magic
  "0 = no limit" value, undocumented in the command help — the docstring instead claims "no
  age limit"), `list -n <N>` with a hand-picked N, or the **deprecated** `carryover`. There
  is **no** `--offset`/page option and no date-**range** filter (`--date` is single-day
  equality). At 143 active, the default `list` shows only the newest 20 by `note.created_at
  DESC` — and because completed/dismissed rows are interleavable under `--all`, active rows
  can be displaced (Ray's observed "20 found … completed rows displace active ones", #66
  Context table).
- **Bulk complete/dismiss:** **not supported.** Both `task_complete` and `task_dismiss`
  take a single `@click.argument('identifier')` (tasks.py:353, 385) and act on one task.
  No multiple IDs, no ranges, no filter-driven bulk. Clearing 142 stale tasks = 142
  invocations.
- **Reason/note on completion/dismissal:** **not supported, and no column exists for it.**
  `set_completed`/`set_dismissed` (task_status_repo.py:95-133) write only
  `status`/`completed_at`/`updated_at`; the `task_status` schema has no reason/note field
  (models.py:362-372: id, note_id, status, created_at, updated_at, completed_at,
  forwarding_note_id). Comparison to EOD Step 3c `[c]/[d]/[s]` (eod_workflow.py:644-660):
  `[c]` → `set_completed(ts.note_id)` **plus** `set_forwarding_note(ts.id, note.id)` when a
  match note exists; `[d]` → `set_dismissed(ts.note_id)`; `[s]` → no write. So EOD and CLI
  write the **same** state transitions — they are equivalent — **except** EOD's `[c]`
  additionally records `forwarding_note_id` (the matched note linkage), which the CLI
  `complete` never sets. Neither surface writes a free-text reason anywhere.
- **Other `list` filters:** only `--status`, `--search` (note content `ILIKE`), `--date`
  (single day). **No source filter, no tag filter, no date range** — `get_filtered`'s
  signature (task_status_repo.py:199-205) exposes nothing more.

**J3 — Deprecation state.** `carryover` prints "⚠ Deprecated … use: workmain tasks list"
(tasks.py:432-433) but, per G, it is the **only** command that shows all active tasks with
no cap and no date scope. If `carryover` were removed today with `list` unchanged, the
lost functionality is: **the only discoverable, single-command, uncapped "all active tasks,
all ages" view.** `list` alone can reproduce it only via `-n 0`, whose "0 = no limit"
semantics are documented only in the repository docstring (task_status_repo.py:213), not in
the `list --help` text — so a user reading the CLI help has no signposted way to see beyond
20. `today` does **not** fill this gap: its scope is active tasks whose note
`created_date == today` (tasks.py:279-284), i.e. "what I flagged today," not "what should I
be working on across all ages." **No non-deprecated command answers "show me all my open
tasks" without the 20-row cap.**

**J4 — CLI_STANDARDS conformance sweep (beyond G4's `--all`).**
- **`list` docstring is inaccurate** (also flagged G1): tasks.py:175 states *"Default (no
  options): all active tasks, no age limit."* There is no age filter, but there **is** a
  hard 20-**row** cap, so "all active tasks" is false whenever >20 active tasks exist (143
  today). §6.5 ("Help text requirements") requires help to describe actual behavior; this
  misdescribes it. **The other five commands' docstrings are accurate** (verified: `show`,
  `complete`, `dismiss` describe single-target behavior truthfully; `today` correctly says
  "created today"; `carryover` correctly says deprecated).
- **Short forms** conform to §5.3: `-s`=`--search`, `-d`=`--date`, `-n`=`--limit` match the
  reserved assignments used elsewhere (e.g. `reports corrections -n/--limit`); `--status`
  and `--all` correctly have **no** short form (§5.3 no-short-form table). No new conflicts.
- **Resource targeting** (`show`/`complete`/`dismiss` positional `identifier` = ID or
  content substring) conforms to §4.3 (name-or-ID targeting of DB resources).
- **Output**: `list` uses a Rich `Table` (§6.1 satisfied); the other commands use plain
  `console.print`, acceptable for single-record/action output.
- No §5.3 short-form violations found in this group; the sole standards deviation is the
  `list` docstring (§6.5). The larger issues (20-cap usability, no bulk, deprecated-yet-only
  uncapped view) are capability gaps for the Gate 2 spec, not §5.3 naming violations.

---

*End of Opus findings — Sections H, I, J complete. Read-only pass; no source modified
outside this Findings block. Note the Section-I correction to #66 F flagged at the top.*

---

### Addendum K (20260727) — Write-path parameter surface for Item 69 service convergence (micro-recon, requested by Role 1)

**Critical instructions (carried forward from the parent recon):**
- Read-only pass. No code changes, no fixes, no refactors, no design
  suggestions inline with findings — verbatim quotes and observations
  only.
- **Pitfall #12 applies:** component-verified ≠ integration-verified.
  Confirming a service function *could* accept a parameter is not the
  same as confirming a given H3 call site actually supplies it — quote
  each call site verbatim to prove it, don't infer from the shape of the
  call.
- **Version-drift caution:** Section H/I/J were run at codebase v1.26.1
  (`main`==`dev`) against file headers `notes.py` v4.2, `time.py` v1.7,
  `meetings.py` v4.5, `clockify/sync.py` v1.4, `time_entry_service.py`
  v1.0, `notes_service.py` v1.0, `action_executor.py` v1.4,
  `notes_repo.py` v2.1. Re-check each header now; if any file has moved
  since 20260725, note the new version and re-verify the relevant H3 row
  rather than assuming it's unchanged.
- **Output:** append findings below this addendum's own
  `#### Addendum K — Findings` placeholder, in the same file. Do not
  create a separate output file.

**Purpose.** Item 69 (Note Write-Path Convergence) will converge all
twelve H3 note-write surfaces onto a single service-layer contract. H4
already established that `notes_service.create_note` and
`time_entry_service.create_time_entry` are siblings — each sees only its
own 1–2 callers today, not the full twelve-surface contract. Before Role
1 can design the converged API shape, it needs:

1. The complete current signature and body of both services, verbatim.
2. The complete, per-parameter call pattern of every one of the twelve
   H3 surfaces — not just whether a surface *can* pass tags/CF (H3
   already answered that), but literally every argument it passes today,
   including any that neither service currently declares.

Without this, a converged signature designed against only the two
current callers risks silently dropping a parameter one of the other ten
surfaces depends on (a hard-coded tag list, a `source` value, a
`created_at` backdate, a `client_id` passthrough) — exactly the
integration gap Pitfall #12 exists to catch.

**Questions:**

**K1.** Quote `notes_service.create_note()` in full — signature and
body, file path, version header, line range
(`workmain/services/notes_service.py`, last known v1.0).

**K2.** Quote `time_entry_service.create_time_entry()` in full —
signature and body, file path, version header, line range
(`workmain/services/time_entry_service.py`, last known v1.0). H4 already
quoted lines 84–90 (the `NotesRepository.create()` call inside it) —
quote the FULL method: parameter list, anything before/after that call
(including any TimeEntry-side construction), return value.

**K3.** For EACH of the twelve H3 surfaces (use the same #1–#12
numbering as the H3 table), quote the exact call site verbatim — full
argument list as written in source, not paraphrased — showing every
parameter passed to whichever write path that surface uses (service
call, or direct `NotesRepository.create()` / model construction). At
minimum, capture per surface whether each of the following is present,
and its literal value or source, or explicitly state it is absent:
- `content`
- `tags` (literal list, user-supplied, or parsed)
- `source` (literal value)
- `client_id`
- `meeting_id` — confirm from `models.py` whether `meeting_id` is an
  actual `Note` column or lives elsewhere (e.g. a `meeting` relationship
  joined separately); H3 didn't surface this explicitly and it must not
  be assumed
- `created_at` (any override/backdate — H already flagged #6's
  `note_created_at`; confirm whether #12 Clockify's import backdates too,
  and check the remaining surfaces)
- surface-specific extras: #2/#4/#8/#9's hard-coded `['both']` tag list
  (quote it literally per surface — confirm it's the same list object or
  four independent literals), #9's `source='condensed'`, #12's
  `source='clockify'` and whether any external Clockify reference id is
  stored on the `Note` or a related row, #10/#11 Slack's intent-derived
  values, #11's H3 note that the create-time-entry schema "has no tags
  field (v1.6)" — confirm that's still current at whatever version
  `action_executor.py` is at now.

**K4.** For the surfaces that pair a Note write with a TimeEntry write
(#5, #6, #7 — the `time add` paths — and #11, Slack create-time-entry),
quote the TimeEntry-side creation call(s) alongside the Note-side call,
with the same per-parameter treatment as K3 (`entry_date`, `client_id`,
duration/hours, `meeting_id`, `category` if it exists as a column).
Item 69 needs to know whether the converged hook point has to account
for a paired TimeEntry write, not just the Note write, on these
surfaces.

**K5. (Primary deliverable) Superset parameter table.** One table:
rows = the union of every parameter name observed across K1/K2
(declared by the services) and K3/K4 (actually passed at any call
site); columns = the twelve H3 surfaces (#1–#12) plus the two service
signatures. Cell contents = the value/source passed on that surface, or
`—` if omitted/left to default, or `N/A` if the parameter doesn't apply
to that surface's write path (e.g. TimeEntry-only fields on a pure-Note
surface). This table is the direct input to Item 69's spec — it must
show the FULL contract the converged API needs to support, not the
two-caller subset either service currently sees.

**K6.** Explicitly flag any parameter found in K3/K4 that is NOT in
either service's current declared signature (K1/K2) — these are gaps
the converged API must *add*, not just relocate. For each gap, name
which of the ten non-service surfaces (#2, #3, #4, #5, #7, #8, #9, #12,
plus the TimeEntry side of #6/#11) depends on it, so Role 1 can size the
spec's parameter-addition scope accurately.

**Output:** Append all findings below this line, under a
`#### Addendum K — Findings` heading, at the END of
`RECON_SPEC_TASK_MATCH_DATA_INTEGRITY_SPRINT_20260725.md` (after the
existing H/I/J closing line). Verbatim quotes with file/version/line
ranges throughout. Do not edit anything above this line in the live
file. Do not create a separate output file.

#### Addendum K — Findings

**Recon performed:** 2026-07-27, Opus (Role 2). Read-only. Codebase v1.26.1, `dev` == `main`.
Extends Sections H/I/J of this file (20260725). No source modified outside this Findings block.

**Version-drift re-check (per this addendum's instruction).** All eight anchored headers are
UNCHANGED since 20260725: `notes.py` v4.2, `time.py` v1.7, `meetings.py` v4.5,
`clockify/sync.py` v1.4, `time_entry_service.py` v1.0, `notes_service.py` v1.0,
`action_executor.py` v1.4, `notes_repo.py` v2.1. No H3 row required re-verification for drift.
Two path/version notes: (a) `action_executor.py` lives at
`workmain/orchestration/action_executor.py` (the parent recon cited it without a path); (b) one
file relevant to K4 is NOT in the anchor list — `time_entries_repo.py` **v1.11**
(`workmain/database/repositories/time_entries_repo.py`), whose `create()` signature is quoted
under K4.

**Two corrections to the addendum's own framing, surfaced first (Pitfall #12 — do not infer the
paired-write set from K4's list; it was checked against source):**

1. **K4's paired-write set is both over- and under-inclusive.** K4 assumes {#5, #6, #7} + #11
   pair a Note write with a TimeEntry write. In source: **#7 pairs NO TimeEntry** — it is a
   standalone "additional note" (`notes_repo.create` at time.py:361 with no `time_repo.create`
   following it), so #7 is a **pure-Note** surface. And **five surfaces K4 did not name DO pair a
   TimeEntry**: #2 (notes.py:409), #4 (notes.py:762), #8 (meetings.py:758), #9 (meetings.py:968),
   #12 (sync.py:336). The complete Note+TimeEntry **paired set is {#2, #4, #5, #6, #8, #9, #11,
   #12}**; the **pure-Note set is {#1, #3, #7, #10}**. K4 below quotes the TimeEntry side of every
   surface that actually has one.

2. **`meeting_id` IS a real `Note` column**, not a relationship-only join. `models.py:216`:
   `meeting_id = Column(Integer, ForeignKey('meetings.id', ondelete='SET NULL'), nullable=True)`.
   It can be set at create on any surface. (The `Note.meeting` relationship at models.py:238 is a
   separate read-side convenience over the same FK.) The `Note` row carries **no** `entry_date`,
   `category`, or Clockify-reference column — those live only on `TimeEntry` (see K4).

---

**K1 — `notes_service.create_note()` in full.** `workmain/services/notes_service.py` **v1.0**,
lines 23–68:

```python
def create_note(
    session,
    content: str,
    tags: Optional[List[str]] = None,
    source: str = "ad-hoc",
    meeting_id: Optional[int] = None,
    project_id: Optional[int] = None,
) -> Note:
    ...
    tag_system = get_tag_system()

    if not tags:
        resolved_tags = ["internal-only"]
    else:
        _, invalid = tag_system.validate_full_names(tags)
        if invalid:
            valid_vocab = tag_system.get_valid_full_names()
            raise InvalidTagsError(invalid_tags=invalid, valid_tags=valid_vocab)
        resolved_tags = tags

    active_client_id = SystemStateRepository(session).get_int("active_client_id")

    return NotesRepository(session).create(
        content=content,
        tags=resolved_tags,
        source=source,
        client_id=active_client_id,
        meeting_id=meeting_id,
        project_id=project_id,
    )
```

Declared params: `content`, `tags` (None/empty → `["internal-only"]`), `source` (default
`"ad-hoc"`), `meeting_id`, `project_id`. `client_id` is **resolved internally** (line 59), NOT a
caller param. **`created_at` is NOT exposed** — every note this service makes defaults to
`datetime.now()` in the repo (notes_repo.py:127). No backdating path.

**K2 — `time_entry_service.create_time_entry()` in full.** `workmain/services/time_entry_service.py`
**v1.0**, lines 26–101:

```python
def create_time_entry(
    session,
    description: str,
    duration_hours: float,
    entry_time: Optional[time_type] = None,
    entry_date: Optional[date] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    meeting_id: Optional[int] = None,
    project_id: Optional[int] = None,
) -> TimeEntry:
    ...
    if entry_time is None:
        raise MissingStartTimeError()

    if entry_date is None:
        entry_date = date.today()

    tag_system = get_tag_system()

    if not tags:
        resolved_tags = ["internal-only"]
    else:
        _, invalid = tag_system.validate_full_names(tags)
        if invalid:
            valid_vocab = tag_system.get_valid_full_names()
            raise InvalidTagsError(invalid_tags=invalid, valid_tags=valid_vocab)
        resolved_tags = tags

    active_client_id = SystemStateRepository(session).get_int("active_client_id")

    # Backdate note's created_at to match entry_date when not today
    note_created_at = (
        datetime.combine(entry_date, datetime.now().time())
        if entry_date != date.today() else None
    )

    note = NotesRepository(session).create(
        content=description,
        tags=resolved_tags,
        source="task",
        client_id=active_client_id,
        created_at=note_created_at,
    )

    return TimeEntriesRepository(session).create(
        note_id=note.id,
        duration_hours=duration_hours,
        entry_date=entry_date,
        entry_time=entry_time,
        category=category,
        client_id=active_client_id,
        meeting_id=meeting_id,
        project_id=project_id,
    )
```

Two structural facts Item 69 must not miss:
- **`source` is HARD-CODED `"task"`** on the note (line 87) — not exposed. A converged API driven
  through this service cannot produce a non-`task` note source (relevant to #11).
- **`meeting_id` and `project_id` are accepted but routed ONLY to the TimeEntry** (lines 99–100),
  **never to the Note** (the Note create at 84–90 omits both). So a meeting-linked time entry made
  via this service yields a Note with `meeting_id = NULL`. `created_at` backdate is computed
  internally (79–82) and applied only to the Note; the TimeEntry create does NOT pass `created_at`
  (defaults to now).

---

**K3 — Per-surface Note-write call sites (verbatim).** "→" = omitted param and its resulting
default. `client_id`/`created_at` omissions are flagged because they diverge across surfaces.

- **#1 `notes add`** — service, notes.py:366–373. `content=clean_text`,
  `tags=all_tags` (user `--tags/-t`, parsed), `source=source` (CLI `--source/-f`, **default
  `'ad-hoc'`**, notes.py:293), `meeting_id=meeting_id` (from `--meeting/-m` fuzzy),
  `project_id=project` (`--project/-p`). `client_id` svc-resolved. `created_at` N/A (not exposed).

- **#2 `notes add` → meeting time-entry follow-on** — direct, notes.py:402–408.
  `content=time_description` (prompt), `tags=['both']` (**hard-coded literal**), `source='meeting'`,
  `meeting_id=note.meeting.id`, `client_id=active_client_id`. `created_at` → now. `project_id` → None.
  **Paired TimeEntry** (K4).

- **#3 `notes log -m` (per line)** — direct, notes.py:701–707. `content=clean_text`,
  `tags=note_tags if note_tags else ['internal-only']` (**per-line inline `#cf` parse**, else
  internal-only default), `meeting_id=meeting_obj.id`, `source='meeting'`,
  `client_id=active_client_id`. `created_at` → now. `project_id` → None. Pure-Note.

- **#4 `notes log` condensed summary** — direct, notes.py:737–743. `content=summary`,
  `tags=['both']` (**hard-coded literal**), `meeting_id=meeting_obj.id`, `source='condensed'`,
  `client_id=active_client_id`. `created_at` → now. `project_id` → None. **Paired TimeEntry** (K4,
  create-or-relink).

- **#5 `time add -m` meeting path** — direct, time.py:313–319. `content=primary_content`
  (`notes` if given else `description`), `tags=note_tags` (user `--tags`, else `['internal-only']`,
  time.py:300–308), `source='meeting'`, `meeting_id=meeting_obj.id`,
  `created_at=note_created_at` (**backdate when `entry_date != today`**, time.py:251–254).
  **`client_id` OMITTED → NULL** ⚠. `project_id` → None. **Paired TimeEntry** (K4).

- **#6 `time add` non-meeting path** — service, time.py:333–342 → time_entry_service.
  `description=description`, `duration_hours`, `entry_time`, `entry_date`, `category`,
  `tags=note_tags`, `project_id=project`. `meeting_id` NOT passed → None. Note-side: `source='task'`,
  `client_id` svc-resolved, `created_at` svc-internal backdate. **Paired TimeEntry** (K4).

- **#7 `time add` extra note** — direct, time.py:361–366. `content=note_content` (prompt),
  `tags=note_tags` (inherited from #5's parse), `meeting_id=meeting_obj.id`,
  `created_at=note_created_at` (**backdate**). **`source` OMITTED → `'ad-hoc'`** ⚠ (all other
  meeting-note surfaces use `'meeting'`). **`client_id` OMITTED → NULL** ⚠. `project_id` → None.
  **Pure-Note — no TimeEntry** (corrects K4).

- **#8 `meetings <flow>` time-entry note** — direct, meetings.py:752–757. `content=description`
  (prompt), `tags=['both']` (**hard-coded literal**), `source='meeting'`, `meeting_id=meeting.id`.
  **`client_id` OMITTED → NULL** ⚠. `created_at` → now. `project_id` → None. **Paired TimeEntry** (K4).

- **#9 `meetings condense` note** — direct, meetings.py:940–945. `content=summary`,
  `tags=['both']` (**hard-coded literal**), `meeting_id=meeting.id`, `source='condensed'`.
  **`client_id` OMITTED → NULL** ⚠. `created_at` → now. `project_id` → None. **Paired TimeEntry** (K4,
  create-or-relink).

- **#10 Slack create-note** — service, action_executor.py:164. `content=content` (intent),
  `tags=tags` (intent pass-through, `action.get("tags")` — may be None). `source` → svc default
  `'ad-hoc'`. `meeting_id`/`project_id` → None. `client_id` svc-resolved. Pure-Note.

- **#11 Slack create-time-entry** — service, action_executor.py:125–131. `description=description`
  (intent), `duration_hours` (from `duration_minutes/60`), `entry_time`, `tags=tags`.
  **`tags = action.get("tags")` is always `None` today** — confirmed still current: the comment at
  action_executor.py:119–122 still reads *"create_time_entry has no `tags` field in the schema
  (v1.6) — always None today"*, unchanged at action_executor v1.4. `entry_date`/`category`/
  `meeting_id`/`project_id` → svc defaults. Note-side `source='task'`, `client_id` svc-resolved,
  `created_at` svc-internal (entry_date=today → None → now). **Paired TimeEntry** (K4).

- **#12 Clockify import** — direct, sync.py:330–334. `content=` clockify description or
  `'Imported from Clockify'`, `tags=['internal-only']` (**hard-coded literal**), `source='clockify'`.
  **`client_id` OMITTED → NULL** ⚠. **`created_at` OMITTED → now (import time), NOT backdated** —
  the note's `created_at`/`created_date` reflects **import time, not the work date**; the paired
  TimeEntry's `entry_date = start_dt.date()` still carries the real work date. **Confirmed
  intentional by Ray (2026-07-27):** imports can legitimately run after the fact (e.g. while
  traveling), so import-time `created_at` on the note is the desired behavior — NOT a defect, no
  repair in scope. (Contrast the `time add` paths #5–#7, which backdate; the divergence is by
  design, not an oversight.) **No external Clockify reference id is stored on the Note**;
  `clockify_id` lives on the paired TimeEntry (sync.py:341, models.py:310). **Paired TimeEntry** (K4).

**The four `['both']` literals are four INDEPENDENT inline list literals**, not one shared
constant: notes.py:404 (#2), notes.py:739 (#4), meetings.py:754 (#8), meetings.py:942 (#9). Each is
a bare `tags=['both']` written at the call site. Likewise `source='meeting'`, `source='condensed'`,
`source='clockify'`, `source='task'` are inline literals at each site (the services hard-code
`'ad-hoc'`/`'task'`; no shared source constant exists).

---

**K4 — Paired TimeEntry-side writes** (`TimeEntriesRepository.create()` **v1.11**, sig at
time_entries_repo.py:93–106: `note_id`, `duration_hours`, `entry_date`, `entry_time`, `category`,
`project_id`, `meeting_id`, `client_id`, `clockify_id`, `synced_at`, `created_at`). Paired set is
{#2, #4, #5, #6, #8, #9, #11, #12}; **#7 has none**.

- **#2** notes.py:409–417: `note_id=te_note.id`, `duration_hours=meeting_duration`,
  `entry_date=note.meeting.start_time.date()`, `entry_time=note.meeting.start_time.time()`,
  `category='meeting'`, `meeting_id=note.meeting.id`, `client_id=active_client_id`. (`project_id` →
  None; `created_at` → now.)
- **#4** notes.py:762–770 (else branch; the `existing_today` branch at 754 only re-points
  `entry.note_id`, no create): `note_id=condensed_note.id`, `duration_hours`,
  `entry_date=meeting_obj.start_time.date()`, `entry_time=…time()`, `category='meeting'`,
  `meeting_id=meeting_obj.id`, `client_id=active_client_id`.
- **#5** time.py:320–329: `note_id=note.id`, `duration_hours`, `entry_date=entry_date`,
  `entry_time=entry_time`, `category=category`, `project_id=project`, `meeting_id=meeting_obj.id`,
  `client_id=active_client_id`. (Note the TimeEntry **does** get `client_id` here even though #5's
  Note does not — the omission is Note-side only.)
- **#6** via service (K2, time_entry_service.py:92–101): `note_id`, `duration_hours`, `entry_date`,
  `entry_time`, `category`, `client_id` (svc-resolved), `meeting_id` (None on this path),
  `project_id`.
- **#8** meetings.py:758–765: `note_id=note.id`, `duration_hours`,
  `entry_date=meeting.start_time.date()`, `entry_time=…time()`, `category='meeting'`,
  `meeting_id=meeting.id`. **`client_id` OMITTED → NULL** ⚠ (both Note and TimeEntry). `project_id` →
  None.
- **#9** meetings.py:968–974 (else branch; `existing_today` at 956 re-points `entry.note_id` only):
  `note_id=condensed_note.id`, `duration_hours`, `entry_date=meeting.start_time.date()`,
  `entry_time=…time()`, `category='meeting'`, `meeting_id=meeting.id`. **`client_id` OMITTED → NULL**
  ⚠. `project_id` → None.
- **#11** via service (K2): defaults throughout — `entry_date` today, `category`/`meeting_id`/
  `project_id` None, `client_id` svc-resolved.
- **#12** sync.py:336–343: `note_id=note.id`, `duration_hours`, `entry_date=start_dt.date()`,
  `entry_time=start_dt.time().replace(tzinfo=None)`, **`clockify_id=clockify_entry['id']`**,
  **`synced_at=datetime.now()`**. **`client_id` OMITTED → NULL** ⚠; `category`/`meeting_id`/
  `project_id` → None.

---

**K5 — Superset parameter table.** Rows = union of every parameter observed across K1/K2 (declared)
and K3/K4 (passed). Columns = the twelve surfaces + the two services (`svc:note` = create_note,
`svc:te` = create_time_entry). Cell = value/source; `—` = omitted (default applies, noted); `N/A` =
param doesn't apply to that surface's write path; `⚠` marks a NULL-producing omission that diverges
from sibling surfaces. First block = Note-write params; second block = paired-TimeEntry-write params.

| Param | #1 | #2 | #3 | #4 | #5 | #6 | #7 | #8 | #9 | #10 | #11 | #12 | svc:note | svc:te |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **content** (Note) | clean_text | prompt | clean_text | summary | notes\|desc | desc | prompt | prompt | summary | intent | intent | descr\|"Imported…" | `content` | `description` |
| **tags** (Note) | user `-t` | `['both']` | `#cf`\|`['internal-only']` | `['both']` | user `-t`\|`['internal-only']` | user `-t` | inherit #5 | `['both']` | `['both']` | intent | intent (→None) | `['internal-only']` | param→`['internal-only']` | param→`['internal-only']` |
| **source** (Note) | `-f` (`'ad-hoc'`) | `'meeting'` | `'meeting'` | `'condensed'` | `'meeting'` | `'task'` | — →`'ad-hoc'` ⚠ | `'meeting'` | `'condensed'` | — →`'ad-hoc'` | `'task'` | `'clockify'` | param (`'ad-hoc'`) | `'task'` (hard-coded) |
| **meeting_id** (Note) | from `-m` | note.meeting.id | meeting_obj.id | meeting_obj.id | meeting_obj.id | — →None | meeting_obj.id | meeting.id | meeting.id | — | — | — | param | — (not→note) |
| **project_id** (Note) | `-p` | — | — | — | — | — | — | — | — | — | — | — | param | — (not→note) |
| **client_id** (Note) | svc-resolved | active_client_id | active_client_id | active_client_id | — NULL ⚠ | svc-resolved | — NULL ⚠ | — NULL ⚠ | — NULL ⚠ | svc-resolved | svc-resolved | — NULL ⚠ | internal | internal |
| **created_at** (Note) | — now | — now | — now | — now | **backdate** | svc backdate | **backdate** | — now | — now | — now | svc(now) | — now (by design) | **not exposed** | internal backdate |
| — *TimeEntry-write params* — | | | | | | | | | | | | | | |
| **note_id** | N/A | note.id | N/A | note.id | note.id | note.id | N/A | note.id | note.id | N/A | note.id | note.id | N/A | note.id |
| **duration_hours** | N/A | meeting_dur | N/A | calc | `-d` | `-d` | N/A | calc | calc | N/A | min/60 | interval | N/A | param |
| **entry_date** | N/A | meeting date | N/A | meeting date | `--date`\|today | today | N/A | meeting date | meeting date | N/A | — today | start_dt.date | N/A | param→today |
| **entry_time** | N/A | meeting time | N/A | meeting time | `--time` | param | N/A | meeting time | meeting time | N/A | parsed | start_dt.time | N/A | param (req) |
| **category** | N/A | `'meeting'` | N/A | `'meeting'` | `-C` | `-C` | N/A | `'meeting'` | `'meeting'` | N/A | — None | — None | N/A | param |
| **meeting_id** (TE) | N/A | meeting.id | N/A | meeting_obj.id | meeting_obj.id | — None | N/A | meeting.id | meeting.id | N/A | — None | — None | N/A | param |
| **project_id** (TE) | N/A | — | N/A | — | `-p` | `-p` | N/A | — | — | N/A | — | — | N/A | param |
| **client_id** (TE) | N/A | active_client_id | N/A | active_client_id | active_client_id | svc-resolved | N/A | — NULL ⚠ | — NULL ⚠ | N/A | svc-resolved | — NULL ⚠ | N/A | internal |
| **clockify_id** | N/A | — | N/A | — | — | — | N/A | — | — | N/A | — | `entry['id']` | N/A | — (not exposed) |
| **synced_at** | N/A | — | N/A | — | — | — | N/A | — | — | N/A | — | `datetime.now()` | N/A | — (not exposed) |
| **created_at** (TE) | N/A | — now | N/A | — now | — now | — now | N/A | — now | — now | N/A | — now | — now | N/A | — (not passed) |

---

**K6 — Parameters used at call sites that are NOT in either service's declared signature** (the
converged API must ADD these, not merely relocate them):

1. **`created_at` on the Note write (caller-supplied backdate)** — `notes_service.create_note` does
   NOT expose `created_at`; `create_time_entry` computes it internally and does not accept it from
   the caller. **Direct surfaces #5 (time.py:318) and #7 (time.py:365)** pass `created_at=note_created_at`
   straight to the Note create to backdate it. If either converges onto `create_note` as it stands,
   **backdating is silently lost** — the exact Pitfall #12 hazard. → **The converged note-write API
   must add a caller-supplied `created_at`/backdate parameter.** (The repo already supports it —
   notes_repo.py:91; the gap is purely at the service layer.)

2. **`clockify_id` + `synced_at` on the paired TimeEntry (#12 only)** — neither service exposes
   these; only the direct Clockify path sets them (sync.py:341–342). If Item 69's converged hook
   wraps #12's paired Note+TimeEntry write, the converged TimeEntry path **must add** `clockify_id`
   + `synced_at`, or #12 must be **explicitly excepted** from convergence.

**Behavioral deltas convergence would introduce (not "add" gaps, but Role-1 decisions, not
accidents):**

3. **`client_id` is currently NULL on five surfaces.** Both services resolve `client_id` internally,
   so it is not a param to add — but **#5, #7, #8, #9, #12 write `client_id = NULL` on the Note
   today** (and #8, #9, #12 also on the TimeEntry). Converging them through a service that
   auto-resolves `active_client_id` would **start stamping** these surfaces — a data-integrity change
   Role 1 should make deliberately. #12 (Clockify import) is the sharpest case: today an import
   inherits no client; convergence would attach the active client to every imported row.

4. **`source` cannot be caller-set through `create_time_entry`** (hard-coded `"task"`, K2). Any
   converged paired-write API that is meant to carry a non-`task` source (e.g. if #2/#8's
   `'meeting'` time-entry notes are ever service-routed) must expose `source`.

5. **`meeting_id`/`project_id` never reach the Note through `create_time_entry`** (K2 — routed only
   to the TimeEntry). Today no service-routed surface (#6, #11) passes a meeting, so no live note is
   affected; but if convergence is meant to link the paired note to its meeting, the service must
   route `meeting_id` to the Note create as well.

*End of Addendum K findings — Opus (Role 2), 2026-07-27. Read-only pass; no source modified outside
this Findings block. Two framing corrections to K4's paired-write set and the `meeting_id`-column
assumption are flagged at the top.*

---

### Addendum L (20260728) — Pre-sprint anchor check for the Task_Match_Data_Integrity Sprint (micro-recon, requested by Role 1)

**Critical instructions (carried forward):** Read-only pass. Verbatim quotes and observations only;
no code changes, no fixes, no design suggestions. Pitfall #12 applies — do not infer a file "owns"
a behavior from one grep hit; trace the full chain. Output appended below this addendum's own
`#### Addendum L — Findings` heading, in this same file. Do not create a separate output file.

**Purpose.** Codebase has advanced to **v1.27.0 post-Item-69** (`dev` HEAD) since Sections H/I/J
(v1.26.1) and Addendum K (v1.26.1). Before the Task_Match_Data_Integrity Sprint spec is drafted,
Role 1 needs current-HEAD anchors for four facts:

**L1.** Quote verbatim the `get_filtered()` call inside `eod_workflow.py`'s Step 3c candidate/
attempt-set construction: file/line, full arguments, current limit value (explicit or defaulted).
**L2.** Highest existing migration number in `workmain/database/migrations/`. Confirm
`022_intent_action_constraints.sql` is still the latest.
**L3.** Exact filename(s) of the existing test file(s) covering `tasks.py`'s CLI commands and
`eod_workflow.py`'s Step 3c.
**L4.** Current version header (docstring) for `workmain/ai/intent_parser.py`,
`workmain/workflows/eod_workflow.py`, and whichever file currently owns Ollama `generation_options`
threading for `parse_task_match`/note_dedup.

#### Addendum L — Findings

**Recon performed:** 2026-07-28, Opus (Role 2). Read-only. Codebase **v1.27.0** (`workmain/__version__.py`
line 554, `__version__ = "1.27.0"`), branch `dev`, HEAD `0f05214` (*Merge chore/task-match-sprint-prep-corrections
into dev*). No source modified outside this Findings block.

---

**L1 — Step 3c candidate/attempt-set `get_filtered()` call.** File
`workmain/workflows/eod_workflow.py` **v1.11** (20260725), inside `_run_task_match_step()` — the
Step 3c runner (`def` at line 445; docstring line 448: *"Step 3c: Match active carry-forward tasks
against today's notes."*). The candidate/attempt-set is built at **line 488**:

```python
# eod_workflow.py v1.11:488
        active_tasks = task_repo.get_filtered(status='active')
```

- **Full arguments:** only `status='active'` is passed. `search`, `date_filter`, and `limit` are
  **all omitted → defaulted.**
- **Current limit value: DEFAULTED to 20.** `TaskStatusRepository.get_filtered` signature
  (`task_status_repo.py` lines 199–205) is `get_filtered(self, status='active', search=None,
  date_filter=None, limit: int = 20)`; docstring line 213: *"limit: Maximum number of results. 0
  means no limit."* Because Step 3c omits `limit`, **the CF-task candidate pool it matches against
  today's notes is silently capped at the newest 20 active tasks** (ordered by note `created_at
  DESC`, per the repo docstring). At the 143-active volume documented in Section I/I4, this cap
  excludes ~123 active tasks from the Step 3c match entirely.
- **Contrast within the same file (for Role 1's context, not asked but material to the cap
  question):** the post-review "remaining" count at **line 665** — `remaining =
  task_repo.get_filtered(status='active')` — is **also** defaulted (capped at 20), so the
  "N active tasks remaining" summary Step 3c prints is likewise a ≤20 figure. Step **3d**
  (`_run_note_dedup_step`, note dedup) at **line 712** passes `limit=0` explicitly
  (`task_repo.get_filtered(status='active', limit=0)`) — **uncapped**. So of the two substeps, only
  Step 3d sees the full active pool today; Step 3c and its summary do not.

---

**L2 — Highest migration number.** `workmain/database/migrations/` top file (numeric):
**`022_intent_action_constraints.sql`**. **Confirmed still the latest** — no `023_*` (or higher)
exists. Full ordered list on disk: `001_initial_schema` … `021_time_entries_note_id`,
`022_intent_action_constraints`, plus `__init__.py`. Item #69 (v1.27.0, Write-Path Convergence)
added **no** migration; the highest migration is unchanged since migration 022 (v1.22.0).

---

**L3 — Existing test files.**

- **`tasks.py` CLI commands →** `tests/test_task_lifecycle.py` **v1.0** (header line 3). Docstring
  names it explicitly: *"…and tasks CLI command group"*; *"CLI error paths: tasks list --status
  invalid, tasks show/complete nonexistent"*; *"CLI deprecation: tasks carryover warning and flag
  mapping"*. Uses `click.testing.CliRunner`. This is the file that exercises the `workmain tasks`
  group (list/show/complete/dismiss/carryover). (It also covers `TaskStatusRepository` methods.)

- **`eod_workflow.py` Step 3c →** coverage lives in **two** files, not one:
  - `tests/test_eod_task_matching.py` **v1.1** — docstring: *"Tests for PC-1 — EOD Step 3c task
    matching algorithm"*; tests `_run_task_match_step()`'s early-return/exception paths.
  - `tests/test_eod_workflow.py` — imports `_run_task_match_step` (line 73), invokes it (lines
    338/366/392), asserts the `task_match` step is in the sequence (line 126), and tests the keyword
    match helpers used by Step 3c (class docstring line 237). Its header (line 43) records the
    *"ProviderError demotion restructure in `_run_task_match_step()`"* work.
  - (`tests/test_eod_pipeline.py` also exists but is the broader end-to-end EOD sequence, not
    Step-3c-specific — noted for completeness, not as Step 3c coverage.)

---

**L4 — Current version headers.**

- `workmain/ai/intent_parser.py` — **v1.4, 20260725.** (Header: *"workmain/ai/intent_parser.py /
  v1.4 / 20260725"*; latest history entry v1.4 = "Hotfix Item #62 Gate 2 —
  parse_task_match()/parse_note_duplicate() set generation_options={'raw': True} …".)
- `workmain/workflows/eod_workflow.py` — **v1.11, 20260725.** (Header: *"WorkmAIn EOD Workflow
  Service Layer / workmain/workflows/eod_workflow.py / v1.11 / 20260725"*.)
- **Ollama `generation_options` threading for `parse_task_match`/note_dedup** — Pitfall #12: this is
  **not owned by a single file; it is a three-file chain.** Naming only one would misrepresent the
  seam. Two anchor notes first: (a) the note-dedup method is named **`parse_note_duplicate`**, not
  `parse_note_dedup`; (b) both match calls set the same `generation_options={"raw": True}`.
  - **Set at the call sites** in `workmain/ai/intent_parser.py` **v1.4, 20260725**:
    `parse_task_match()` (`def` line 164) passes `generation_options={"raw": True}` at **line 216**;
    `parse_note_duplicate()` (`def` line 241) passes `generation_options={"raw": True}` at
    **line 263**.
  - **Field declared** on `GenerationRequest` in `workmain/ai/base_provider.py` **v1.2, 20260605**
    (`generation_options: Optional[Dict[str, Any]] = None`, line 65).
  - **Threaded into the Ollama `/api/generate` payload** in `workmain/ai/providers/ollama.py`
    **v1.4, 20260725** — lines 71–72: `if request.generation_options: options.update(request.generation_options)`;
    v1.4 (Item #62 Gate 1) additionally pops `generation_options["raw"]` to a top-level payload key.
    If Role 1 means the single file that performs the actual threading (as opposed to the call sites
    that set the value), that is **`ollama.py` v1.4** — but the value originates in `intent_parser.py`
    v1.4 and is typed in `base_provider.py` v1.2, and all three must move together for any change.

---

*End of Addendum L findings — Opus (Role 2), 2026-07-28. Read-only pass; no source modified outside
this Findings block. Codebase v1.27.0, `dev` HEAD 0f05214. The Step 3c 20-row cap (L1) and the
`parse_note_duplicate` naming / three-file threading chain (L4) are flagged for Role 1's attention.*

---

### Addendum M (20260728) — Item #69 regression surface: Step 3d note-dedup blocks daily EOD (field finding, surfaced by Ray)

**Origin.** Unlike K/L (Role-1-issued question sets), this addendum documents a **live EOD blocker
Ray hit on `dev` HEAD immediately after Item #69 shipped**, run down by Opus (Role 2) at Ray's
request. Read-only pass — verbatim quotes and observations only; no fix applied, no `VALID_STEPS`
edit made. The remediation is a Role-1 design call (it is squarely this sprint's Gate 2/Gate 3
subject); this section only establishes the mechanism and the seams so the spec can size it.

**Symptom (Ray, 2026-07-28).** After #69, `workmain eod` now stalls in Step 3d (note dedup) printing
`Comparing 1/574…`, `2/574…` at ~30s per item, and Step 3d is **not** an accepted `--skip` target, so
EOD cannot be completed or bypassed.

**Version anchors (this addendum).** `workmain/workflows/eod_workflow.py` **v1.11** (20260725);
`workmain/cli/commands/eod.py` **v2.14** (20260611); `workmain/ai/intent_parser.py` **v1.4**
(`parse_note_duplicate`, per Addendum L). Codebase v1.27.0, `dev` HEAD `0f05214`.

---

**M1 — The `574` is a candidate-PAIR count, and every pair is one Ollama round-trip.** Step 3d
(`_run_note_dedup_step`) builds candidate pairs at **eod_workflow.py:734–737**:

```python
# eod_workflow.py v1.11:732-737
        # Candidate pairs: new x existing, plus new x new (C(new, 2)).
        # existing x existing is excluded — already evaluated in a prior run.
        pairs = [(a, b) for a in today_tasks for b in existing_tasks]
        for i in range(len(today_tasks)):
            for j in range(i + 1, len(today_tasks)):
                pairs.append((today_tasks[i], today_tasks[j]))
```

`total = len(pairs)` (line 768) — so the `i/574` counter (loop at line 780) is `len(today_tasks) ×
len(existing_tasks) + C(len(today_tasks), 2)`, **not** a note or task count. For each pair, when
Ollama is available, one inference call is made at **eod_workflow.py:796**:

```python
# eod_workflow.py v1.11:796
                    result = intent_parser.parse_note_duplicate(note_a.content, note_b.content)
```

The ~30s/item is that call's model latency (one `/api/generate` per pair). `parse_note_duplicate`
is **not** independently slow — Addendum L / Item #62 Gate 2 (`raw=True`) *reduced* its prompt
(~2,400→~600 tokens). The cost is structural: **574 sequential LLM calls**, ≈ a few of today's CF
notes × the full ~143-row active pool (e.g. 4 × 143 = 572, + a couple today×today).

**M2 — Why #69 flipped this from dormant to blocking.** Step 3d draws its pool **uncapped** —
`active_tasks = task_repo.get_filtered(status='active', limit=0)` (eod_workflow.py:712; contrast
Step 3c's *defaulted-to-20* call at line 488, Addendum L1) — then partitions it (line 723):

```python
# eod_workflow.py v1.11:720-726
        for ts in active_tasks:
            if not ts.note or not ts.note.content:
                continue
            if ts.note.created_date == target_date:
                today_tasks.append(ts)
            else:
                existing_tasks.append(ts)
```

with an early-out when nothing is new today (line 728–730):

```python
# eod_workflow.py v1.11:728-730
        if not today_tasks:
            print("  No new carry-forward notes today — skipping note dedup")
            return EodStepResult(status=EodStepStatus.COMPLETED)
```

Pre-#69, Sections H/I established the CF→TaskStatus hook fired only on `notes add`/`notes edit`
(live hook fired **exactly once ever**; the 143 active rows are a migration-015 backfill). Ray's real
capture surfaces — `time add` (#6), `notes log` (#3), meeting flows — produced CF notes with **no**
task row, so those notes never entered `active_tasks` at all → `today_tasks` was empty essentially
every day → Step 3d hit the line-728 early-out and did nothing. **Item #69 converged the write path
so the hook now fires on all note-write surfaces** (H4's convergence, now shipped). Consequence: (a)
today's CF notes from `time add`/`notes log` now get task rows → `today_tasks` is non-empty daily;
(b) they are paired against **the entire uncapped stale pool** — the ~142 Feb–May backfill artifacts
that Section I4 already flagged as ≥2-months stale and never dismissed. The 574-pair blowup is the
direct product of (correctly) fixing the hook while the stale pool remains unpruned and Step 3d
remains uncapped. This is the intersection of the two things this sprint already scopes: **Gate 3
(stale-pool dismissal / orphan housekeeping)** and the **Step 3d scope/cap** question — but the #69
ship has escalated it from "cleanup" to "daily EOD is blocked."

**M3 — Step 3d is unskippable: a `VALID_STEPS` wiring gap.** `note_dedup` is a first-class step in
the sequence (eod_workflow.py:1330):

```python
# eod_workflow.py v1.11:1330
        ('note_dedup',            '3d', 'Detect duplicate carry-forward notes',              _run_note_dedup_step),
```

but it is **absent from the CLI `--skip` allowlist** (eod.py:110–111):

```python
# eod.py v2.14:110-111
VALID_STEPS = ['condense', 'sync', 'review', 'pre_flight_inspection',
               'task_match', 'report', 'email', 'clockify', 'gdocs', 'weekly']
```

so `workmain eod --skip note_dedup` is rejected (eod.py:200–203):

```python
# eod.py v2.14:200-203
            if s not in VALID_STEPS:
                console.print(f"[red]✗ Unknown step: '{s}'[/red]")
                console.print(f"[dim]Valid steps: {', '.join(VALID_STEPS)}[/dim]")
                return
```

`note_dedup` is the **only** non-weekly step in `_build_step_sequence` missing from `VALID_STEPS`
(cross-check: `condense`, `sync`, `review`, `pre_flight_inspection`, `task_match`, `report`, `email`,
`clockify`, `gdocs` all present; `note_dedup` is not). It was added to the sequence in
Operations_Config_Correction_Sprint Gate 5 (Item #32) but never added to the skip allowlist. This is
a plain omission, not a design choice — no code comment or guard indicates `note_dedup` was
intentionally made mandatory.

**M4 — No clean mid-run escape either.** The in-loop cancellation check is **daemon-only**
(eod_workflow.py:781: `if cancel_event is not None and cancel_event.is_set()`), so an interactive CLI
run has no cancel path into the compare loop. A Ctrl-C during the loop raises `KeyboardInterrupt`,
which is **not** a subclass of `Exception` and so is **not** caught by the step's guard
(eod_workflow.py:900, `except Exception as e: … continuing`) — it propagates and aborts the entire
`eod` run rather than skipping just Step 3d. (The only `KeyboardInterrupt` handler in this step is at
line 861, inside the *merge-review* prompt, which the run never reaches while stuck in the compare
loop.) Net: on CLI today there is no way to skip, cancel, or survive Step 3d once it starts against a
large pool.

**M5 — Remediation seams (for Role 1; no fix applied here).** Two independent levers, different
sizes — this section maps them, it does not choose:
- **Immediate unblock (one line):** add `'note_dedup'` to `VALID_STEPS` (eod.py:110–111). Low blast
  radius; restores `--skip note_dedup`. Pure wiring correction. Could stand as a `hotfix/` ahead of
  the sprint if Role 1 wants EOD unblocked now. (Not done in this read-only pass.)
- **Structural (this sprint):** the 574-pair cost is the Gate 3 stale-pool problem (dismiss the ~142
  backfill artifacts so `existing_tasks` collapses to the genuinely-active few) intersecting the
  Step 3d scope question (uncapped `limit=0` at line 712 vs Step 3c's cap of 20 at line 488; and
  whether note-dedup should pair against the whole historical pool at all, or only a bounded recent
  window). Both are already in scope; M2 is the evidence that they now gate daily operation, not just
  data hygiene. Role-1 design decisions — flagged, not resolved.

*End of Addendum M findings — Opus (Role 2), 2026-07-28. Read-only pass; no source modified outside
this Findings block, no `VALID_STEPS` edit made. Codebase v1.27.0, `dev` HEAD 0f05214. Surfaced from
Ray's live EOD blocker; remediation deferred to Role 1 per the three-role model.*
