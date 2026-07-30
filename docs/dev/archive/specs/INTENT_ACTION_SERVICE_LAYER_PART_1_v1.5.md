WorkmAIn
INTENT_ACTION_SERVICE_LAYER_PART_1 v1.5
20260612

Version History:
- v1.0: Initial spec — Gates 0-5 (recon, migration, service layer,
  CLI/action_executor refactor, tests)
- v1.1: Added Git Workflow section (feature/* branch, per-gate commits)
  and Gate 6 (version bump, changelog, backlog, merge to main, tag,
  release, session handoff). Fixed time_entry_service client_id
  double-resolution bug, tags passthrough gap in
  _execute_create_time_entry, get_valid_full_names() pattern,
  services/__init__.py requirement, empty-array CHECK note, orphaned
  trailing section, git add -A → explicit paths, and
  InvalidTagsError message to surface full tag vocabulary instead of
  the valid-subset-of-submitted-tags.
- v1.2: Fixed Gate 3 time.py underspecification — time.py's direct
  NotesRepository.create() call (separate from TimeEntriesRepository
  .create()) was not addressed, and the service didn't support
  source='meeting', meeting-notes content, or backdated note
  created_at. Resolved by branching Gate 3 on --meeting presence:
  non-meeting path delegates to time_entry_service (which gains a new
  note_created_at parameter for backdating consistency); meeting path
  is unchanged, deferred alongside meeting_id linkage (Part 2/3).
  Added Gate 0 #4 (time.py source + NotesRepository.create() signature
  recon). Fixed stale v1.0 cross-references in Gate 6.
- v1.3: Corrected v1.2's framing of the backdating fix. It is NOT new
  design work — NotesRepository.create() already has a
  created_at: Optional[datetime] parameter, and time.py already
  computes note_created_at with the exact one-liner this spec now
  reuses, both from the Phase 13 DB Schema Hygiene sprint
  (DESIGN_TIME_ENTRIES_REFACTOR_20260608.md, v1.20.0). Removed the
  note_created_at parameter from create_time_entry()'s signature
  (computed internally instead, matching the existing pattern) and
  narrowed Gate 0 #4 from open-ended time.py recon to a one-line
  confirmation of source/tags defaults on the non-meeting path.
- v1.4: Fixed a real data-loss bug in v1.1-v1.3's Gate 3 non-meeting
  time add example — the "intentionally omitted" comment incorrectly
  grouped project_id with meeting_id as meeting-dependent. project_id
  is an independent top-level --project flag (time.py:187, already a
  validated int) and was being silently dropped for any non-meeting
  time add with --project. Added project_id=project to the call and
  rewrote the comment to distinguish it from the deferred Slack
  schema `project` field. Also clarified the "Explicitly deferred"
  section: the project_id deferral is Slack/schema-specific (no
  name-resolution path exists); the CLI's --project is unaffected and
  was never deferred.
- v1.5: Gate 0 complete — all four items confirmed matching spec
  expectations (migration number 022; empty-string tag search returned
  zero rows; parse_time()/parse_duration() call convention confirmed;
  time.py non-meeting path source/tags confirmed). Removed Gate 1's
  data-cleanup step (no rows to clean) — migration is now two
  statements, not three. Marked Gate 0 items as resolved. Clarified
  Gate 1's approval gate: writing the migration file may proceed;
  running it against the DB requires separate explicit approval after
  SQL review. Fixed remaining 0{N} migration-number placeholder in
  Gate 6.

# Purpose & Scope

Phase 13 Sprint 3 is blocked on validating IntentParser action types 1
(`create_note`) and 2 (`create_time_entry`) against their CLI equivalents.
Two recon passes (`ACTION_AUDIT_TRACK1_ITEMS1-2.md`,
`ACTION_AUDIT_TRACK1_FOLLOWUP.md`) identified a set of gaps. This spec
extracts the shared application logic for these two operations into a new
service layer, following the same pattern established by
`eod_workflow.py` in Phase 13 Sprint 1/2: a shared, no-I/O layer that both
the CLI and `action_executor.py` call, with CLI and action_executor
shrinking to thin adapters (the same role `eod.py` / `slack_eod.py` play
relative to `eod_workflow.py`).

## In scope for v1

- `client_id` stamping on both `create_note` and `create_time_entry`
  (system-derived from active-client state — no schema change)
- `time_entries.entry_time` becomes NOT NULL at the DB level; service
  layer enforces this with a friendly pre-check
- `notes.tags` gets a CHECK constraint restricting to the 6 full-name
  values in `config/tags.json` (after a 1-row data cleanup)
- `entry_date` defaulting (today if not specified) — service accepts the
  parameter; not yet schema-exposed (see Deferred)
- `category` passthrough — service accepts the parameter; not yet
  schema-exposed (see Deferred)
- Replace `action_executor`'s inline ad-hoc `start_time` parsing with
  `TimeEntriesRepository.parse_time()`

## Explicitly deferred (separate future items, not this spec)

- **`project_id` via the IntentParser schema (Slack)** — no
  `ProjectsRepository` exists, no project-by-name resolution exists
  anywhere in the local DB layer. The `project` field (a string, with
  nothing to resolve it to an integer) should be removed from
  `create_time_entry`'s schema entirely (its own hotfix to
  `intent_parse_system_prompt.txt`, requires model rebuild). This
  deferral is Slack-specific: the CLI's `--project` (`time.py:187`,
  `type=int`) is already a valid, Click-validated integer with nothing to
  resolve, and is NOT deferred — it's passed through to
  `time_entry_service.create_time_entry()` in Gate 3 below. Service
  signatures accept `project_id: Optional[int] = None` to serve both: the
  CLI's real value now, and `None` from Slack until the schema field
  exists.
- **`meeting_id`** linkage for either action type — `fuzzy_match_meeting()`
  and `interactive_meeting_picker()` are built entirely around
  `click.confirm`/`click.prompt`; there is no non-interactive resolution
  path today. This needs new logic (likely tied to Sprint 3's T6
  conversational pattern) and is its own item. Service signatures accept
  `meeting_id` as forward-compatible (always `None` for now).
- **`entry_date` / `category` as model-extractable schema fields** — the
  service supports both starting in this spec. Wiring them into
  `intent_parse_system_prompt.txt` (new examples, `config_version` bump,
  model rebuild) is Phase 2, deliberately separated from this spec.

## Decided: missing `start_time` policy

When `create_time_entry` arrives via Slack with no stated start time, the
service raises `MissingStartTimeError`. `action_executor` returns an
`ActionResult` requesting clarification ("what time did you start?")
rather than defaulting to "now" or writing a null timestamp. The retry
loop that takes the user's answer and re-invokes the action with
`start_time` filled in is Sprint 3 T6 machinery — this spec produces the
interface point (`MissingStartTimeError` → clarification `ActionResult`);
wiring the actual conversational retry is T6's responsibility.

---

# Git Workflow

This change touches `workmain/database/migrations/`,
`workmain/services/__init__.py` (new), `workmain/services/exceptions.py`
(new), `workmain/services/notes_service.py` (new),
`workmain/services/time_entry_service.py` (new),
`workmain/utils/tag_utils.py`, `workmain/cli/commands/notes.py`,
`workmain/cli/commands/time.py`,
`workmain/orchestration/action_executor.py`, plus test files — more than
the 3-file cap for `hotfix/*` per `GIT_WORKFLOW_STANDARDS.md`. The git
branch is `feature/*`, not `hotfix/*`:

```bash
git checkout dev
git pull
git checkout -b feature/intent-action-service-layer
```

Merges to `dev` (no-ff), then `dev` → `main` via PR, per the established
practice of merging every verified feature branch to `main` promptly
rather than phase-gating. Version bump, `CHANGELOG.md`, tag, release, and
session handoff are all part of Gate 6 below.

Commit messages follow the standard `<type>(<scope>): <description>`
format, **one commit per gate** (matching prior sprint handoffs), not one
combined commit at the end:
- Gate 1: `fix(db): add intent action constraints`
- Gate 2: `feat(services): add notes_service and time_entry_service`
- Gate 3: `refactor(notes): use notes_service for notes add`,
  `refactor(time): use time_entry_service for time add`
- Gate 4: `refactor(action-executor): delegate create_note/create_time_entry to services`
- Gate 5: `test(services): add notes_service and time_entry_service tests`
- Gate 6: see Gate 6 step 5 (separate, final commit for close-out changes)

---

# Gate 0 — Recon prerequisites (before writing any code)

**#1 is already resolved** — Claude Code's review confirmed
active-client resolution is `SystemStateRepository(session).get_int('active_client_id')`,
called at `notes.py:307` and `time.py:222`. No dedicated
`get_active_client_id()` method exists. Both services call this directly.

**All items below are now resolved** (Gate 0 complete — results recorded
for the session handoff):

1. **Current migration number.** ✅ `021_time_entries_note_id.sql` is
   highest; this spec's migration is `022_intent_action_constraints.sql`.

2. **The empty-string tag row.** ✅
   ```sql
   SELECT id, content, tags, source FROM notes WHERE '' = ANY(tags);
   ```
   returned zero rows. No data cleanup needed — see revised Gate 1.

3. **`parse_time()` / `parse_duration()` call convention.** ✅ Both are
   instance methods on `TimeEntriesRepository` (lines 647 and 593).
   `action_executor.py` calls via
   `TimeEntriesRepository(self.session).parse_time(str(start_time_str))`.

4. **`time.py` `time add` non-`--meeting` path — exact current
   `NotesRepository.create()` call.** ✅ Confirmed `source = 'task'`
   (line 318) and default `tags = ['internal-only']` (line 298) — matches
   `time_entry_service` exactly.

Proceeding to Gate 1 (revised below to remove the now-unnecessary
data-cleanup step).

---

# Decided: Gate 3 `time.py` scope (`--meeting` vs non-`--meeting` paths)

Claude Code's third review identified that `time.py`'s `time add` makes
its own direct `NotesRepository.create()` call (in addition to
`TimeEntriesRepository.create()`), and that this call uses three things
the v1.1 service didn't support: `source='meeting'` when `--meeting` is
set, separate meeting-notes content via `-N/--notes`, and a backdated
`note.created_at` derived from `-d/--date`.

**Resolution — split by whether `--meeting` is present:**

- **`--meeting` is set:** `time.py` keeps its current direct
  `NotesRepository.create()` / `TimeEntriesRepository.create()` calls,
  unchanged. This path is already covered by this spec's `meeting_id`
  deferral (Part 2/3) — `source='meeting'` and `-N/--notes` content are
  both meeting-specific, so they stay with the rest of meeting linkage.

- **`--meeting` is NOT set:** `time.py` delegates to
  `time_entry_service.create_time_entry()` per Gate 3 below. This is also
  the path Slack/`action_executor` uses (which never has `meeting_id` in
  v1), so it's the one that actually needs to be shared.

**The backdating piece is NOT new design work** — it's reuse of an
existing, already-implemented pattern from the Phase 13 DB Schema Hygiene
sprint (`DESIGN_TIME_ENTRIES_REFACTOR_20260608.md`, v1.20.0).
`NotesRepository.create()` already accepts
`created_at: Optional[datetime] = None`, added specifically so
`note.created_date` can match a backdated `entry_date`. `time.py` already
computes this value with:

```python
note_created_at = (
    datetime.combine(entry_date, datetime.now().time())
    if entry_date != datetime.today().date() else None
)
```

`time_entry_service.create_time_entry()` (Gate 2) simply replicates this
exact one-liner and passes the result as `created_at` to
`NotesRepository.create()` — no new signature, no new mechanism, no open
question. The `--meeting` path already does this too (it's the same
`note_created_at` computation, shared by both branches in current
`time.py`), so no adjustment is needed there either.

---

# Gate 1 — Migration

**Gate 0 complete** — findings confirmed all spec expectations:
migration number is 022; `parse_time()`/`parse_duration()` call
convention confirmed; `time.py` non-`--meeting` path confirmed
`source="task"`, `tags=["internal-only"]` matching the service. **The
empty-string tag row search returned zero rows** — no data exists outside
the 6-value vocabulary, so the data-cleanup step is removed entirely.
Migration is now two steps, not three.

**STOP: human approval required before running this migration**, per
standard gate discipline. Writing the migration file itself
(`022_intent_action_constraints.sql`) is non-destructive and may proceed;
running it against the database requires a separate explicit go-ahead
after the exact SQL is reviewed.

File: `workmain/database/migrations/022_intent_action_constraints.sql`

1. **`entry_time` NOT NULL.** Confirmed zero existing NULL rows (Gate 0 of
   the prior recon pass) — no backfill needed.
   ```sql
   ALTER TABLE time_entries ALTER COLUMN entry_time SET NOT NULL;
   ```

2. **`tags` CHECK constraint.** Restrict to the 6 full-name values from
   `config/tags.json` (`tag_mappings[*].full_name`). No existing rows
   violate this (confirmed via Gate 0's empty-string search returning
   zero rows — the only known out-of-vocabulary case), so this can be
   added directly with no pre-migration cleanup:
   ```sql
   ALTER TABLE notes ADD CONSTRAINT notes_tags_valid_vocabulary
     CHECK (tags <@ ARRAY['internal-only','client-report','info-only','both','carry-forward','blocker']::text[]);
   ```
   Note: `{} <@ ARRAY[...]` is true in PostgreSQL, so this constraint
   permits an empty `tags` array. That's acceptable — the service layer
   (Gate 2) always applies the `["internal-only"]` default before an
   empty list would reach the repository, so an empty array should never
   actually occur from these write paths. The constraint's job is to
   reject *invalid* values, not to enforce non-emptiness.

Verify post-migration:
```sql
SELECT COUNT(*) FROM notes WHERE NOT (tags <@ ARRAY['internal-only','client-report','info-only','both','carry-forward','blocker']::text[]);
-- expect 0
SELECT COUNT(*) FROM time_entries WHERE entry_time IS NULL;
-- expect 0
```

---

# Gate 2 — Service layer modules

## `workmain/services/__init__.py` (new)

Required per `CLAUDE.md` §4 package-structure rules: module docstring,
version history block, imports re-exporting `create_note` and
`create_time_entry` for convenient access (`from workmain.services import
notes_service, time_entry_service`), `__all__`, `__version__`.

## `workmain/services/exceptions.py` (new)

```python
class ServiceValidationError(Exception):
    """Base class for service-layer validation failures."""

class MissingStartTimeError(ServiceValidationError):
    """Raised by time_entry_service when entry_time cannot be determined
    and no default may be applied. Caller must obtain a start time from
    the user and retry."""

class InvalidTagsError(ServiceValidationError):
    """Raised when one or more supplied tags are outside the configured
    vocabulary."""
    def __init__(self, invalid_tags: list[str], valid_tags: list[str]):
        self.invalid_tags = invalid_tags
        self.valid_tags = valid_tags
        super().__init__(f"Invalid tags: {invalid_tags}")
```

## `workmain/utils/tag_utils.py` (addition)

Add to `TagSystem`, mirroring the existing short-name `validate_tags()`
(instance method) but checking against `full_name` values instead of
`tag_mappings` keys:

```python
def validate_full_names(self, tags: list[str]) -> tuple[list[str], list[str]]:
    """Validate a list of full-name tags against the configured
    vocabulary. Returns (valid, invalid)."""
    full_names = {m["full_name"] for m in self.tag_mappings.values()}
    valid, invalid = [], []
    for tag in tags:
        if tag in full_names:
            valid.append(tag)
        else:
            invalid.append(tag)
    return valid, invalid

def get_valid_full_names(self) -> list[str]:
    """Return all valid full-name tag values."""
    return sorted(m["full_name"] for m in self.tag_mappings.values())
```

Both are instance methods on `TagSystem`, matching `validate_tags()` /
`get_valid_tags_list()` (tag_utils.py:203). Also add a module-level
convenience function `get_valid_full_names()` calling
`get_tag_system().get_valid_full_names()`, mirroring the existing
`get_valid_tags()` convenience wrapper. `validate_full_names()` does not
need a convenience wrapper — both services already hold a
`get_tag_system()` instance for default/validation logic and call
`.validate_full_names()` on it directly.

## `workmain/services/notes_service.py` (new)

```python
def create_note(
    session,
    content: str,
    tags: Optional[list[str]] = None,
    source: str = "ad-hoc",
    meeting_id: Optional[int] = None,   # forward-compatible, always None in v1
    project_id: Optional[int] = None,   # forward-compatible, always None in v1
) -> Note:
    """
    - Resolves active_client_id via
      SystemStateRepository(session).get_int('active_client_id') and
      passes it to the repository.
    - tags: if None or empty, defaults to ["internal-only"]. Otherwise
      validated via TagSystem.validate_full_names(); raises
      InvalidTagsError if any tag is outside the vocabulary.
    - meeting_id / project_id passed through as-is (None in v1).
    - Calls NotesRepository.create(content=content, tags=tags,
      source=source, client_id=active_client_id, meeting_id=meeting_id,
      project_id=project_id) and returns the created Note.
    """
```

## `workmain/services/time_entry_service.py` (new)

```python
def create_time_entry(
    session,
    description: str,
    duration_hours: float,
    entry_time: Optional[time] = None,
    entry_date: Optional[date] = None,
    category: Optional[str] = None,
    tags: Optional[list[str]] = None,
    meeting_id: Optional[int] = None,   # forward-compatible, always None in v1
    project_id: Optional[int] = None,   # forward-compatible, always None in v1
) -> TimeEntry:
    """
    - If entry_time is None: raise MissingStartTimeError(). Caller must
      obtain a start time and retry — no default is applied.
    - entry_date: defaults to date.today() if None.
    - Computes note_created_at using the existing v1.20.0 pattern
      (DESIGN_TIME_ENTRIES_REFACTOR_20260608.md), reusing the same
      one-liner already in time.py verbatim:
        note_created_at = (
            datetime.combine(entry_date, datetime.now().time())
            if entry_date != date.today() else None
        )
      This is "now" for the common (today) case — no behavior change —
      and aligns the linked note's created_date with a backdated
      entry_date otherwise.
    - Resolves active_client_id ONCE via
      SystemStateRepository(session).get_int('active_client_id').
    - tags: if None or empty, defaults to ["internal-only"]. Otherwise
      validated via TagSystem.validate_full_names(); raises
      InvalidTagsError if any tag is outside the vocabulary.
    - category: passthrough string, no validation (no validation exists
      anywhere in the current codebase for this field).
    - DECISION (resolves spec ambiguity #3): creates the linked note via
      NotesRepository.create(content=description, tags=tags,
      source="task", client_id=active_client_id,
      created_at=note_created_at) directly — NOT via
      notes_service.create_note(). This avoids a second
      active_client_id resolution and avoids inter-service coupling.
      notes_service.create_note() has no client_id parameter (it
      resolves internally for its own callers); calling it from here
      with client_id would be a TypeError, which is why this needed to
      be decided rather than left as written. (`created_at` is a
      confirmed existing parameter on NotesRepository.create() —
      see Decided: Gate 3 section above.)
    - Creates the entry via TimeEntriesRepository.create(note_id=note.id,
      duration_hours=duration_hours, entry_date=entry_date,
      entry_time=entry_time, category=category, client_id=active_client_id,
      meeting_id=meeting_id, project_id=project_id)
    - Returns the created TimeEntry (with .note accessible).
    """
```

Note: `time_entry_service` and `notes_service` independently call
`get_tag_system()` for tag default/validation — this is calling a shared
utility, not duplicating logic. The vocabulary itself still lives in one
place (`config/tags.json` via `TagSystem`).

---

# Gate 3 — CLI refactor

## `notes.py` — `notes add`

CLI retains ALL interactive resolution as-is (meeting picker, tag
parsing/correction via `parse_tags()`/`interactive_correction()`, project
option). Once content/tags/meeting_id/project_id are resolved, replace the
direct `NotesRepository.create(...)` call (and its `active_client_id`
lookup) with:

```python
note = notes_service.create_note(
    session,
    content=content,
    tags=resolved_tags,       # already full names from parse_tags()
    source=resolved_source,
    meeting_id=resolved_meeting_id,
    project_id=resolved_project_id,
)
```

Since CLI tags are already validated via `parse_tags()`/
`interactive_correction()` before this point, `InvalidTagsError` should
not fire from this path — the service's validation is defense-in-depth,
not the primary check for CLI.

## `time.py` — `time add`

**See "Decided: Gate 3 `time.py` scope" above** — this command branches
on whether `--meeting` is set.

`DURATION` → `repo.parse_duration()` → `duration_hours`; `-T/--time` →
`repo.parse_time()` → `entry_time` (still required by Click, so
`MissingStartTimeError` never fires from this path); `-d/--date` →
`entry_date` — all unchanged regardless of branch.

**If `--meeting` is NOT set:** replace both the direct
`NotesRepository.create(...)` call (line ~322 per prior audit) and the
`TimeEntriesRepository.create(...)` call with a single call to
`time_entry_service.create_time_entry()`:

```python
entry = time_entry_service.create_time_entry(
    session,
    description=description,
    duration_hours=duration_hours,
    entry_time=entry_time,
    entry_date=entry_date,
    category=category,
    tags=resolved_tags,
    project_id=project,
    # meeting_id intentionally omitted — always None on this branch by
    # construction (it's the non-meeting branch). project_id is NOT
    # meeting-dependent — it's a separate top-level --project flag
    # (time.py:187, type=int, already validated by Click) and must be
    # passed through here. The service accepts it as-is; this is the
    # CLI's already-valid integer, not the deferred Slack `project`
    # field (which has no name-resolution path and remains deferred).
)
```

The `note_created_at` backdating logic (existing v1.20.0 pattern,
reused per the Decision above) is computed internally by the service from
`entry_date` — no separate parameter or caller-side handling needed.

**If `--meeting` IS set:** no change. `time.py` keeps its existing direct
`NotesRepository.create(...)` (with `source='meeting'`, `-N/--notes`
content, and its existing backdating handling) and
`TimeEntriesRepository.create(...)` calls exactly as they are today. This
branch is part of the `meeting_id` deferral (Part 2/3), not this spec.

---

# Gate 4 — `action_executor.py` refactor

File: `workmain/orchestration/action_executor.py`

## `_execute_create_note`

```python
def _execute_create_note(self, action: dict) -> ActionResult:
    from workmain.services import notes_service
    from workmain.services.exceptions import InvalidTagsError
    from workmain.utils.tag_utils import get_valid_full_names

    content = action.get("content", "")
    tags = action.get("tags")  # full names per schema, or None

    try:
        note = notes_service.create_note(self.session, content=content, tags=tags)
    except InvalidTagsError as e:
        # Note: e.valid_tags is the valid SUBSET of what was submitted
        # (often empty if every submitted tag was bad) — not the full
        # vocabulary. Always surface get_valid_full_names() here so the
        # message tells the user what tags DO exist, not just that none
        # of their submitted ones were valid.
        return ActionResult(
            success=False,
            message=f"Unrecognized tag(s): {', '.join(e.invalid_tags)}. "
                    f"Valid tags: {', '.join(get_valid_full_names())}.",
            error="invalid_tags",
        )

    return ActionResult(success=True, message="✓ Note saved.", entity_id=note.id)
```

## `_execute_create_time_entry`

```python
def _execute_create_time_entry(self, action: dict) -> ActionResult:
    from workmain.services import time_entry_service
    from workmain.services.exceptions import MissingStartTimeError, InvalidTagsError
    from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
    from workmain.utils.tag_utils import get_valid_full_names

    description = action.get("description", "")
    duration_minutes = int(action.get("duration_minutes", 0))
    duration_hours = duration_minutes / 60.0

    entry_time = None
    start_time_str = action.get("start_time")
    if start_time_str:
        try:
            entry_time = TimeEntriesRepository(self.session).parse_time(str(start_time_str))
        except ValueError:
            logger.warning("Invalid start_time format '%s', treating as not provided", start_time_str)
            entry_time = None

    # NOTE (resolves spec gap #2): create_time_entry has no `tags` field
    # in intent_parse_system_prompt.txt v1.6 — action.get("tags") will
    # always be None today. We extract and pass it anyway, for parity
    # with _execute_create_note and so that no further action_executor
    # change is needed if/when a tags field is added to this action type
    # in a future schema revision. With tags=None, time_entry_service
    # applies the existing default of ["internal-only"] — matching
    # current behavior exactly.
    tags = action.get("tags")

    try:
        entry = time_entry_service.create_time_entry(
            self.session,
            description=description,
            duration_hours=duration_hours,
            entry_time=entry_time,
            tags=tags,
        )
    except MissingStartTimeError:
        return ActionResult(
            success=False,
            message="What time did you start this?",
            error="needs_clarification",
        )
    except InvalidTagsError as e:
        return ActionResult(
            success=False,
            message=f"Unrecognized tag(s): {', '.join(e.invalid_tags)}. "
                    f"Valid tags: {', '.join(get_valid_full_names())}.",
            error="invalid_tags",
        )

    hrs = duration_minutes // 60
    mins = duration_minutes % 60
    hrs_str = f"{hrs}h {mins}m" if hrs and mins else (f"{hrs}h" if hrs else f"{mins}m")
    return ActionResult(
        success=True,
        message=f"✓ Logged {hrs_str} for '{description}' at {entry_time.strftime('%H:%M')}.",
        entity_id=entry.id,
    )
```

Note: `error="needs_clarification"` is a new `ActionResult.error` value.
The conversational retry (ask the question, take the reply, re-invoke
with `start_time` populated) is Sprint 3 T6 scope — out of scope for this
spec, but this is the interface point T6 should consume.

---

# Gate 5 — Tests

- `tests/test_notes_service.py`, `tests/test_time_entry_service.py`:
  success paths; `InvalidTagsError` on bad tags; default tag application;
  `client_id` stamping; `MissingStartTimeError` when `entry_time=None`;
  `entry_date` defaulting to today.
- Update existing `notes add` / `time add` CLI tests for the refactored
  call path — behavior should be unchanged from the user's perspective.
- Update `action_executor` tests:
  - `create_time_entry` without `start_time` returns
    `error="needs_clarification"` and does NOT write a row (current
    behavior writes a null-timestamp row — this is the bug being fixed).
  - `create_note` / `create_time_entry` via Slack now stamp `client_id`
    matching the active client.
  - `create_note` with an out-of-vocabulary tag returns
    `error="invalid_tags"` and does not write a row.
- Full suite must pass (590 baseline + new tests).

---

# Gate 6 — Version bump, changelog, backlog, merge, tag, release

**Objective:** Close out this feature branch with version bump, changelog
entry, backlog updates for the deferred items, and a clean merge to
`dev` → `main`.

**Steps:**

1. Version bump `workmain/__version__.py`: `1.21.0` → `1.22.0` (minor
   bump — feature/phase → dev → main, per
   `GIT_WORKFLOW_STANDARDS.md`'s version bump table).

2. `CHANGELOG.md` — add `[1.22.0]` entry. Include:
   - New `workmain/services/` package: `notes_service.create_note()`,
     `time_entry_service.create_time_entry()` — shared logic for note
     and time entry creation, used by both CLI and `action_executor`
   - Migration 022_intent_action_constraints.sql: `time_entries.entry_time`
     now NOT NULL; `notes.tags` CHECK constraint on the 6-value vocabulary
   - Fix: Slack-originated notes and time entries now stamp `client_id`
     from active-client state (previously unattributed)
   - Fix: `create_time_entry` via Slack with no stated start time now
     returns a clarification request instead of writing a null-timestamp
     row
   - `action_executor.py`'s `_execute_create_note` /
     `_execute_create_time_entry` refactored to thin adapters over the
     new service layer

3. `docs/FEATURE_BACKLOG.md` — add three entries for items deferred from
   this spec (cross-reference `INTENT_ACTION_SERVICE_LAYER_PART_1`):
   - `project_id` resolution: no `ProjectsRepository` exists, no
     project-by-name lookup anywhere in the local DB layer; needed before
     `create_time_entry`'s `project` field can be restored
   - `meeting_id` linkage for `create_note`/`create_time_entry`: needs
     non-interactive meeting resolution (current resolution is entirely
     `click.confirm`/`click.prompt`-based); likely intersects Sprint 3 T6
   - `entry_date`/`category` as IntentParser schema fields (Phase 2):
     service already accepts both parameters; needs
     `intent_parse_system_prompt.txt` `config_version` bump + new
     examples + model rebuild

4. Final test run:
   ```bash
   python -m pytest tests/ -v --tb=short 2>&1 | tail -10
   ```
   Must be 0 failures. Record total passing count (baseline 590 + new
   service/action_executor tests from Gate 5).

5. Commit (Gate 6's changes only — version bump, changelog, backlog;
   Gates 1–5 are already committed individually per the Git Workflow
   section above):
   ```bash
   git add workmain/__version__.py CHANGELOG.md docs/FEATURE_BACKLOG.md
   git commit -m "chore: bump version to 1.22.0, update changelog and backlog"
   ```

6. Merge to dev (no-ff):
   ```bash
   git checkout dev
   git merge --no-ff feature/intent-action-service-layer \
     -m "feat: merge intent action service layer (items 1 & 2)"
   ```

7. Full test run on dev:
   ```bash
   python -m pytest tests/ -v --tb=short 2>&1 | tail -5
   ```
   Must be 0 failures.

8. Create PR (dev → main) via `gh`:
   ```bash
   gh pr create \
     --title "v1.22.0: Intent action service layer (Part 1 — create_note / create_time_entry)" \
     --body "Extracts shared create_note/create_time_entry logic into workmain/services/. Adds client_id stamping, entry_time NOT NULL + tags CHECK constraints, and missing-start-time clarification flow for Slack. Resolves Sprint 3 Gate 0 prerequisite. See INTENT_ACTION_SERVICE_LAYER_PART_1." \
     --base main \
     --head dev
   ```

9. After Ray merges PR: pull main, tag, and push tag:
   ```bash
   git checkout main
   git pull origin main
   git tag v1.22.0
   git push --tags
   ```

10. Create GitHub release:
    ```bash
    gh release create v1.22.0 \
      --title "v1.22.0 — Intent action service layer (Part 1)" \
      --notes "Shared service layer for create_note/create_time_entry, used by both CLI and Slack action_executor. Fixes client_id attribution and null-timestamp time entries from Slack. See CHANGELOG.md."
    ```

11. Create session handoff document at
    `docs/dev/handoffs/SESSION_HANDOFF_INTENT_ACTION_SERVICE_LAYER_PART1_<YYYYMMDD>.md`.

    The handoff must follow the established format from prior sprint
    handoffs and include:
    - Sprint summary (one paragraph) — note this resolves the Sprint 3
      Gate 0 prerequisite identified during Sprint 3 planning; Sprint 3
      itself has not yet started
    - Version, branch, tag, PR number, GitHub release URL, test suite
      count
    - Gate log table (gate → deliverable → commit hash → notes),
      including Gate 0 findings (active_client_id mechanism, migration
      number, empty-string tag row resolution)
    - File versions table for all new and modified files
    - Infrastructure reference (Ollama host, model `workmain-intent:v1.6`,
      `config_version 1.6` — unchanged by this spec)
    - Known issues / follow-up items with the three `FEATURE_BACKLOG.md`
      item numbers added in step 3
    - Next preview: Sprint 3 planning resumes; `confirm_report`/
      `correct_report` (items 4 & 5) are the next Track 1 audit target

    Use `SESSION_HANDOFF_PHASE13_SPRINT1_COMPLETE_20260605.md` as the
    format reference.

12. Delete feature branch:
    ```bash
    git branch -d feature/intent-action-service-layer
    git push origin --delete feature/intent-action-service-layer
    ```

---

# Summary of what is NOT in this spec

- `project_id` resolution (no `ProjectsRepository` exists) — separate item
- `meeting_id` linkage for these two action types — separate item, likely
  intersects with T6
- `entry_date`/`category` as IntentParser schema fields — Phase 2,
  schema-only wiring on top of the service support added here
