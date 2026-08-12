WorkmAIn
INTENT_ACTION_EXECUTOR_FIXES_TRACK1_ITEMS4-5 v1.2
20260623

Version History:
- v1.0: Initial spec — Gates 1-4 (confirm_report fix, correct_report fix,
  tests, close-out). No service module, no migration, no schema changes.
- v1.1: Five corrections from Claude Code pre-implementation review:
  (1) version target 1.22.2 → 1.22.3 (v1.22.2 already published today
      by items-33-34 hotfix); Gate 4 Step 1 also notes latent
      __version__.py docstring bug from that hotfix to fix in the same
      step.
  (2) Block Kit modal backlog item number 46 → 47 (46 already taken by
      "build_weekly_prompt() Edge Cases" added in items-33-34 session).
  (3) Backlog version in Gate 4 Step 3: v5.24 → v5.26 (backlog already
      at v5.25 after items-33-34 session).
  (4) Test baseline in Gate 3: 624 → 629 (5 tests added in
      items-33-34 hotfix).
  (5) Gate 4 Step 11 handoff: Items 33 and 34 are COMPLETE (v1.22.2);
      only Item 32 is reopened.
- v1.2: Version target 1.22.3 → 1.22.4. v1.22.3 was already published
  as the Ollama keep-alive timeout hotfix (project docs updated at
  session start). This spec targets the next available patch version.

---

# Purpose & Scope

Track 1 audit for Items 4 & 5 (`confirm_report` / `correct_report`) is
complete. Recon document `ACTION_AUDIT_TRACK1_ITEMS4-5.md` (in
`docs/dev/design/intent-parser-audit/`) identified three behavioral gaps
in `_execute_confirm_report` and one significant semantic error in
`_execute_correct_report`. This spec corrects both handlers directly in
`action_executor.py`. No service module, no migration, no schema changes.

## `_execute_confirm_report` — three gaps

1. `updated_at` not explicitly set. CLI and eod_workflow both set it
   explicitly (`report.updated_at = datetime.now()`). The action_executor
   relies on the ORM `onupdate` trigger, which may not fire depending on
   how SQLAlchemy generates the UPDATE statement. Fix: set explicitly.

2. No idempotency guard. Will stamp `status = 'confirmed'` over an
   already-corrected report, which is a state regression. The CLI returns
   early if `report.status in ('confirmed', 'corrected')`. Fix: add the
   same guard.

3. Today-only scope via `_get_latest_report(date.today())`. The CLI
   resolver accepts any ID or date. **No fix needed** — the intent schema
   has no `report_date` field and the Slack path was never designed to
   confirm past reports. Acceptable as-is.

## `_execute_correct_report` — one significant semantic error

Phase 12 Decision 21 (locked per Claude Code rundown): `correction_note`
was added as a Phase 13 placeholder specifically for the Slack/intent
parser correction description. The spec explicitly deferred that write
path to Phase 13.

Sprint 2's implementation wrote the correction description string to
`corrected_content` instead. This is wrong because `corrected_content` is
reserved for full edited report text written via `$EDITOR` (CLI /
eod_workflow path). The consequence: if the Slack action fires first,
`corrected_content` holds a one-line description string. When the user
subsequently runs `workmain reports correct today`, the CLI pre-populates
`$EDITOR` with `corrected_content` (since it is not NULL), and the user
sees the description string rather than the report they intended to edit.

Fix: route the correction description to `correction_note` per Phase 12
design intent. Leave `corrected_content` untouched. Set
`status = 'corrected'` to prevent EOD regeneration and signal that the
report requires a CLI edit before it is considered clean.

## In scope

- Fix `_execute_confirm_report` (gaps 1 & 2 above)
- Fix `_execute_correct_report` (route to `correction_note`, not
  `corrected_content`)
- Tests for both corrected handlers
- CLAUDE.md note on the `corrected_content` / `correction_note`
  distinction (Gate 4)

## Explicitly deferred

- Block Kit modal for full report correction from Slack — requires
  Cloudflare Tunnel interactivity endpoint infrastructure; see
  Backlog Item 47
- Today-only scope on `_get_latest_report` — acceptable given current
  schema; revisit if `report_date` is added to the intent schema
- Prompt builder integration using `corrected_content` as few-shot
  examples for AI generation — future sprint; requires correction data
  to accumulate and upstream tag filtering to stabilise first
- Data cleanup for any existing rows where `corrected_content` holds an
  incorrect description string from Sprint 2 behavior — low volume;
  user handles via `workmain reports correct today` at the terminal

---

# Git Workflow

This spec touches only `workmain/orchestration/action_executor.py` and
`tests/test_action_executor.py` — within the 3-file cap for `hotfix/*`
per `GIT_WORKFLOW_STANDARDS.md`.

```bash
git checkout main
git pull
git checkout -b hotfix/intent-action-executor-fixes-items4-5
```

One commit per gate:
- Gate 1: `fix(action-executor): correct confirm_report handler — idempotency guard and updated_at`
- Gate 2: `fix(action-executor): correct correct_report handler — route correction to correction_note`
- Gate 3: `test(action-executor): add confirm_report and correct_report fix tests`
- Gate 4: `chore: bump version to 1.22.4, update changelog and backlog`

Co-Authored-By line on each commit per established practice.

---

# Gate 1 — Fix `_execute_confirm_report`

File: `workmain/orchestration/action_executor.py`

Replace the existing `_execute_confirm_report` method (lines ~214-229
per recon) with the implementation below. Do not change any other method.

```python
def _execute_confirm_report(self, action: dict) -> ActionResult:
    """Confirm today's most recent report of the given type.

    Matches CLI behaviour (report_confirm in reports.py):
    - Idempotency guard: no-op if already confirmed or corrected.
    - Explicit updated_at stamp (does not rely on ORM onupdate trigger).

    Does not accept a report_date — the intent schema has no such field
    and the Slack path is designed for today's report only.
    """
    report_type = action.get("report_type", "daily_internal")
    report = self._get_latest_report(report_type)
    if report is None:
        return ActionResult(
            success=False,
            message=f"No {report_type.replace('_', ' ')} found for today.",
            error="no_report",
        )
    if report.status in ("confirmed", "corrected"):
        return ActionResult(
            success=True,
            message=(
                f"{report_type.replace('_', ' ').title()} is already "
                f"{report.status} — no change made."
            ),
            entity_id=report.id,
        )
    report.status = "confirmed"
    report.updated_at = datetime.now()
    self.session.commit()
    return ActionResult(
        success=True,
        message=f"✓ {report_type.replace('_', ' ').title()} confirmed.",
        entity_id=report.id,
    )
```

**Before committing:**
Verify `datetime` is already imported at the top of `action_executor.py`
(it is used elsewhere — do not add a duplicate import).

**Commit:**
```bash
git add workmain/orchestration/action_executor.py
git commit -m "fix(action-executor): correct confirm_report handler — idempotency guard and updated_at

- Add idempotency guard: return early (success=True, no DB write) if
  report.status is already 'confirmed' or 'corrected'. Matches CLI
  report_confirm behaviour (reports.py).
- Set report.updated_at = datetime.now() explicitly rather than
  relying on ORM onupdate trigger, which may not fire on partial
  UPDATE statements. Matches CLI and eod_workflow behaviour.
- No change to _get_latest_report scope (today-only is intentional
  given current intent schema has no report_date field).

Co-Authored-By: Claude Sonnet 4.6"
```

---

# Gate 2 — Fix `_execute_correct_report`

File: `workmain/orchestration/action_executor.py`

Replace the existing `_execute_correct_report` method (lines ~231-247
per recon) with the implementation below. Do not change any other method.

```python
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

**corrected_content note for existing Sprint 2 data:**
Any report row where Sprint 2's incorrect behaviour already wrote a
correction description string to `corrected_content` will retain that
string. When the user runs `workmain reports correct today`, the CLI
will pre-populate `$EDITOR` with the description string (since
`corrected_content` is not NULL). The user clears it, pastes the actual
corrected report, and saves. No migration is needed and no automated
cleanup should be attempted — low volume, user handles at the terminal.

**Commit:**
```bash
git add workmain/orchestration/action_executor.py
git commit -m "fix(action-executor): correct correct_report handler — route correction to correction_note

Phase 12 Decision 21 (locked): correction_note is the designated field
for Slack/intent parser correction descriptions. corrected_content is
reserved for full edited report text from \$EDITOR (CLI/eod_workflow).

Sprint 2 implementation wrote the correction description string to
corrected_content, corrupting the CLI pre-populate flow.

Changes:
- correction string now written to report.correction_note
- corrected_content is never touched by this method
- status set to 'corrected' if not already (prevents EOD regeneration)
- report.updated_at explicitly set
- Empty correction string now returns error='missing_correction'
  rather than writing an empty string to correction_note
- Return message directs user to complete full edit via CLI

Co-Authored-By: Claude Sonnet 4.6"
```

---

# Gate 3 — Tests

File: `tests/test_action_executor.py`

Add test cases within the existing `_execute_confirm_report` and
`_execute_correct_report` test groups. Do not create a separate file.

## `_execute_confirm_report` test cases

**`test_confirm_report_sets_status_confirmed`**
Unconfirmed report exists for today. Fire action with
`{"action": "confirm_report", "report_type": "daily_internal"}`.
Assert: `report.status == "confirmed"`, `success=True`,
`entity_id == report.id`.

**`test_confirm_report_sets_updated_at`**
Unconfirmed report exists. Capture `report.updated_at` before the call.
Fire action. Assert `report.updated_at` has changed (is greater than
the captured value). Do not assert a specific timestamp.

**`test_confirm_report_idempotent_when_already_confirmed`**
Report exists with `status = 'confirmed'`. Fire action. Assert: no
additional DB write (mock or inspect `session.commit` call count — should
not be called), `success=True`, returned message contains "already
confirmed".

**`test_confirm_report_no_change_when_corrected`**
Report exists with `status = 'corrected'`. Fire action. Assert:
`report.status` still `'corrected'` after the call, `success=True`,
returned message contains "already corrected".

**`test_confirm_report_no_report_today`**
No report exists for today. Fire action. Assert: `success=False`,
`error="no_report"`.

## `_execute_correct_report` test cases

**`test_correct_report_writes_correction_note`**
Unconfirmed report exists. Fire action with
`{"correction": "XSOAR time should be 120 min not 90"}`.
Assert: `report.correction_note == "XSOAR time should be 120 min not 90"`,
`report.corrected_content is None`, `report.status == "corrected"`,
`report.updated_at` was set, `success=True`.

**`test_correct_report_corrected_content_not_touched`**
Report exists with `corrected_content` already set to a full report
string (simulate a prior CLI edit). Fire action with a correction
description. Assert: `report.corrected_content` is unchanged (still
holds the full report string from before the call).

**`test_correct_report_from_unconfirmed`**
Report with `status = 'unconfirmed'`. Fire action.
Assert: `report.status == "corrected"`.

**`test_correct_report_overrides_confirmed_status`**
Report with `status = 'confirmed'`. Fire action.
Assert: `report.status == "corrected"`. Correction takes precedence
over prior confirmation.

**`test_correct_report_status_unchanged_if_already_corrected`**
Report already `status = 'corrected'`. Fire action with a new
correction description. Assert: `report.status` stays `'corrected'`,
`report.correction_note` is overwritten with the new description.

**`test_correct_report_empty_correction_string`**
Fire action with `{"correction": ""}` or without the correction field.
Assert: `success=False`, `error="missing_correction"`, no DB write
(`session.commit` not called).

**`test_correct_report_no_report_today`**
No report exists for today. Fire action with a valid correction string.
Assert: `success=False`, `error="no_report"`.

**Before committing:** Run the full suite and record the actual passing
count. Use that number in the commit message below in place of 629.
The baseline is 629 (624 original + 5 from items-33-34 hotfix).

**Commit:**
```bash
git add tests/test_action_executor.py
git commit -m "test(action-executor): add confirm_report and correct_report fix tests

Covers: idempotency guard, updated_at stamp, corrected_content
isolation, status transition table, empty correction guard, and
no-report-today for both handlers. Baseline 629 + new tests.

Co-Authored-By: Claude Sonnet 4.6"
```

---

# Gate 4 — Version bump, changelog, backlog, CLAUDE.md, merge, tag, release

## Step 1 — Version bump

`workmain/__version__.py`: bump `__version__` to `"1.22.4"`.

Also verify and align the module docstring header with the new
`__version__` value. Prior hotfixes left these out of sync; confirm
both read `1.22.4` after this edit.

Patch bump — behavioral correction in existing handlers, no new features,
no migration.

## Step 2 — CHANGELOG.md

Add `[1.22.4]` entry:

```
## [1.22.4] - 2026-06-23

### Fixed
- `action_executor._execute_confirm_report`: now sets `updated_at`
  explicitly and returns early (no-op) if report is already confirmed
  or corrected. Matches CLI and eod_workflow behaviour.
- `action_executor._execute_correct_report`: correction description is
  now written to `correction_note` (Phase 12 Decision 21 design intent)
  rather than `corrected_content`. `corrected_content` is no longer
  overwritten by Slack corrections and remains reserved for full edited
  report text from $EDITOR. `status` is set to 'corrected' to prevent
  EOD regeneration.
- `_execute_correct_report` now returns `error="missing_correction"` if
  the correction field is absent or empty, rather than writing an empty
  string to `correction_note`.
- Fixed latent `__version__.py` docstring header mismatch introduced in
  v1.22.2 (header string was not updated alongside `__version__`).
```

## Step 3 — docs/FEATURE_BACKLOG.md

Add Item 47 (Block Kit report correction modal). See the separately
provided Item 47 draft for the full entry text. Bump backlog version
header to v5.26 and add a v5.26 line to the Version History block:

```
- v5.26 (20260623): Item 47 added — Block Kit modal for full report
  correction from Slack (Phase 14; requires Cloudflare Tunnel).
```

Also add a row to the Quick Reference Register:
```
| 47 | Block Kit modal — report correction from Slack | Ph 14 | Medium | ~6h | |
```

## Step 4 — CLAUDE.md

Add the following entry under the architectural decisions / key
constraints section. This distinction must survive future sessions and
must not be inferred from code alone:

```
**corrected_content vs correction_note (reports table)**
- `corrected_content` (TEXT): full edited report text, written only by
  the $EDITOR path (CLI `workmain reports correct` and eod_workflow
  `[e]dit` branch). Never written by action_executor.
- `correction_note` (TEXT): correction description or intent, written by
  action_executor._execute_correct_report (Slack/intent parser path) and
  optionally by the user at the eod_workflow correction-note prompt.
  Phase 12 Decision 21 (locked): this field was designed as a Phase 13
  placeholder for exactly this purpose.
These fields serve different purposes and must never be conflated.
```

## Step 5 — Final test run

```bash
python -m pytest tests/ -v --tb=short 2>&1 | tail -10
```

Must be 0 failures. Record total count.

## Step 6 — Commit

```bash
git add workmain/__version__.py CHANGELOG.md docs/FEATURE_BACKLOG.md CLAUDE.md
git commit -m "chore: bump version to 1.22.4, update changelog, backlog, and CLAUDE.md

Co-Authored-By: Claude Sonnet 4.6"
```

## Step 7 — Merge to main (no-ff)

```bash
git checkout main
git merge --no-ff hotfix/intent-action-executor-fixes-items4-5 \
  -m "fix: merge intent action executor fixes — items 4 & 5 (v1.22.4)"
```

Full test run on main:
```bash
python -m pytest tests/ -v --tb=short 2>&1 | tail -5
```
Must be 0 failures.

## Step 8 — Sync hotfix to dev

```bash
git checkout dev
git merge --no-ff hotfix/intent-action-executor-fixes-items4-5 \
  -m "fix: merge hotfix intent-action-executor-fixes to dev"
git checkout main
```

## Step 9 — Tag and push

```bash
git tag v1.22.4
git push --tags
```

## Step 10 — GitHub release

```bash
gh release create v1.22.4 \
  --title "v1.22.4 — Intent action executor fixes (items 4 & 5)" \
  --notes "Corrects confirm_report and correct_report handlers in action_executor.py. confirm_report gains idempotency guard and explicit updated_at. correct_report now routes correction description to correction_note per Phase 12 Decision 21, preserving corrected_content for the CLI/eod_workflow edit path. Also fixes latent __version__.py docstring mismatch from v1.22.2. See CHANGELOG.md."
```

## Step 11 — Session handoff

Create `docs/dev/handoffs/SESSION_HANDOFF_INTENT_ACTION_AUDIT_ITEMS4-5_COMPLETE_<YYYYMMDD>.md`.

Required sections (use `SESSION_HANDOFF_PHASE13_SPRINT1_COMPLETE_20260605.md`
as format reference):
- Sprint summary (one paragraph): note this completes Track 1 of the
  Phase 13 Sprint 3 pre-work audit (items 1-5 fully audited and fixed);
  Track 2 (Block Kit UX, session persistence) is the remaining Sprint 3
  scope
- Version: v1.22.4, branch, tag, PR if applicable, test suite count
- Gate log table (gate → deliverable → commit hash → notes)
- File versions table for modified files
  (`action_executor.py`, `test_action_executor.py`, `CHANGELOG.md`,
  `__version__.py`, `FEATURE_BACKLOG.md`, `CLAUDE.md`)
- Infrastructure reference — unchanged (Ollama host, model
  `workmain-intent:latest`, config_version 1.6)
- Item 47 added (Block Kit modal — Phase 14 pending Cloudflare Tunnel)
- Items status note: Items 33 and 34 are COMPLETE (v1.22.2); Item 32
  is reopened and under separate investigation
- Next: Sprint 3 Track 2 planning — Block Kit UX, session persistence;
  Item 45 (`tags` for `create_time_entry`) timing TBD pending Item 44
  schema work
- Note on `docs/dev/design/` folder rename:
  `intent-parser-audit-20260612` → `intent-parser-audit` (performed with
  regular `mv`; folder is gitignored / untracked)

## Step 12 — Delete hotfix branch

```bash
git branch -d hotfix/intent-action-executor-fixes-items4-5
git push origin --delete hotfix/intent-action-executor-fixes-items4-5
```

---

# Summary of what is NOT in this spec

- Block Kit modal for full report correction from Slack (Item 47)
- Today-only scope on `_get_latest_report` — deferred
- Prompt builder integration using corrected reports as few-shot context
- Data cleanup for existing Sprint 2 rows with description strings in
  `corrected_content` — user handles via CLI
- Item 32 (CF task deduplication) — separate investigation
