WorkmAIn
ACTION_AUDIT_TRACK1_ITEMS1-2 v1.0
20260612

Recon output for Phase 13 Sprint 3 intent parser audit.
Track 1, Items 1 & 2: `create_note` ↔ `workmain notes add` and
`create_time_entry` ↔ `workmain time add`.

No code was modified. No recommendations are made. This is a factual
enumeration for use in a separate planning session.

---

# Part 1: `workmain notes add`

---

## 1. CLI Help Output

```
Usage: workmain notes add [OPTIONS] [TEXT]

  Add a new note with tags.

  Examples:
    workmain notes add "Fixed login bug" -t ilo,blk
    workmain notes add "Fixed login bug #ilo #blk"
    workmain notes add "Discussed goals" -m "Team Standup"
    workmain notes add -m  (interactive picker)

Options:
  -t, --tags TEXT        Tags (comma-separated short names: ilo,cf,blk)
  -m, --meeting TEXT     Meeting title (fuzzy match supported)
  -p, --project INTEGER  Project ID
  -f, --source TEXT      Note source (ad-hoc, meeting, task)
  --help                 Show this message and exit.
```

---

## 2. Click Command Signature

Source: `workmain/cli/commands/notes.py` lines 285–291

```python
@notes.command('add')
@click.argument('text', required=False)
@click.option('--tags', '-t', help='Tags (comma-separated short names: ilo,cf,blk)')
@click.option('--meeting', '-m', help='Meeting title (fuzzy match supported)')
@click.option('--project', '-p', type=int, help='Project ID')
@click.option('--source', '-f', default='ad-hoc', help='Note source (ad-hoc, meeting, task)')
def notes_add(text: Optional[str], tags: Optional[str], meeting: Optional[str],
               project: Optional[int], source: str):
```

Parameter summary:

| Name      | Kind     | Type           | Required | Default    | Flags         |
|-----------|----------|----------------|----------|------------|---------------|
| `text`    | ARGUMENT | str            | No       | None       | positional    |
| `tags`    | OPTION   | str            | No       | None       | `-t`/`--tags` |
| `meeting` | OPTION   | str            | No       | None       | `-m`/`--meeting` |
| `project` | OPTION   | int            | No       | None       | `-p`/`--project` |
| `source`  | OPTION   | str            | No       | `'ad-hoc'` | `-f`/`--source` |

---

## 3. Command Body Logic

Source: `workmain/cli/commands/notes.py` lines 303–419

**Session setup:**
- `get_db()` + `db.get_session()` pattern.
- `NotesRepository`, `MeetingsRepository`, `SystemStateRepository` constructed on the session.
- `active_client_id` read from `SystemStateRepository(session).get_int('active_client_id')`.

**Meeting resolution (before text prompt):**
- If `meeting == ''` (flag passed with no value): `interactive_meeting_picker(meetings_repo)` is called.
  - Shows list of up to 10 recent meetings; prompts selection or new meeting creation.
  - Interactive — requires terminal input.
- If `meeting` is a non-empty string: `fuzzy_match_meeting(meetings_repo, meeting)` is called.
  - If `meeting.isdigit()`: looked up directly by `meetings_repo.get_by_id(int(meeting))`.
  - Otherwise: `meetings_repo.get_by_title(title, exact=False)` first; then `meetings_repo.fuzzy_match(threshold=0.6)`.
  - If multiple fuzzy matches: interactive numbered picker shown.
  - If no match: `click.confirm()` to create a new meeting.
- Either path returns `None` on cancel, which causes an early return.

**Text prompt (if text not supplied):**
- `click.prompt("Note")` — interactive prompt.

**Tag parsing:**
- `parse_tags(text, apply_default=False)` — extracts inline `#tag` tokens from `text`; returns `(clean_text, inline_tags, inline_invalid)`.
- If `--tags` supplied: each comma-separated short name converted to `#short` format, then run through `parse_tags(tag_string, apply_default=False)` → `flag_tags`, `flag_invalid`.
- `all_tags = inline_tags + flag_tags` (merged).
- If `all_tags` is empty after merge: `all_tags = ['internal-only']` (default applied in function body, not in decorator).
- If invalid tags present: `get_tag_system().interactive_correction()` interactive picker; may modify tags or cancel.

**Repository call (primary note):**
```python
# notes.py line 363
note = notes_repo.create(
    content=clean_text,
    tags=all_tags,
    meeting_id=meeting_id,
    project_id=project,
    source=source,
    client_id=active_client_id,
)
```

**Post-create carry-forward hook:**
- If `'carry-forward' in (note.tags or [])`: `TaskStatusRepository(session).ensure_active(note.id)` + `session.commit()`.

**Conditional time entry creation (meeting path only):**
- If `note.meeting` is set: `click.confirm()` prompts whether to create a time entry for the meeting.
- If confirmed:
  - `duration_hours` derived: `(note.meeting.end_time - note.meeting.start_time).total_seconds() / 3600`.
  - `click.prompt("Description", default=f"Meeting: {note.meeting.title}")` — interactive.
  - **Second** `notes_repo.create()` call:
    ```python
    # notes.py line 399
    te_note = notes_repo.create(
        content=time_description,
        tags=['both'],
        source='meeting',
        meeting_id=note.meeting.id,
        client_id=active_client_id,
    )
    ```
  - `TimeEntriesRepository(session).create()` call:
    ```python
    # notes.py line 406
    time_repo.create(
        note_id=te_note.id,
        duration_hours=meeting_duration,
        entry_date=note.meeting.start_time.date(),
        entry_time=note.meeting.start_time.time(),
        category='meeting',
        meeting_id=note.meeting.id,
        client_id=active_client_id,
    )
    ```

**AI provider calls:** None.

**Derived/computed values:**
- `active_client_id` — derived from system state, not user input.
- `clean_text` — derived from `text` by stripping inline `#tag` tokens.
- `all_tags` — merged and potentially defaulted; not a direct pass-through of any single input.
- In the meeting time entry path: `meeting_duration`, `entry_date`, `entry_time` all derived from the meeting object (not from user input).

---

## 4. Repository Method(s) Called

### `NotesRepository.create()`

Source: `workmain/database/repositories/notes_repo.py` lines 82–133

```python
def create(
    self,
    content: str,
    tags: List[str],
    project_id: Optional[int] = None,
    meeting_id: Optional[int] = None,
    source: str = 'ad-hoc',
    created_at: Optional[datetime] = None,
    client_id: Optional[int] = None,
) -> Note:
```

**Validation inside the method:**
- `_validate_client_project_consistency(client_id, project_id)`:
  - No-op if either is `None`.
  - If both set: queries `Project` by `project_id`; raises `ValueError` if project not found, or if `project.client_id != client_id`.

**Defaults applied inside the method (not in caller):**
- `tags` → `sorted(set(tags)) if tags else []` — deduplicated and sorted alphabetically.
- `created_at` → `datetime.now()` if `None`.

**DB / model constraints on `Note`** (source: `workmain/database/models.py`):

| Column          | Type         | Constraint                                    |
|-----------------|--------------|-----------------------------------------------|
| `id`            | Integer      | PRIMARY KEY                                   |
| `content`       | Text         | NOT NULL                                      |
| `tags`          | ARRAY(Text)  | NOT NULL, default=list                        |
| `source`        | String(50)   | nullable                                      |
| `project_id`    | Integer      | FK → `projects.id` ON DELETE SET NULL, nullable |
| `meeting_id`    | Integer      | FK → `meetings.id` ON DELETE SET NULL, nullable |
| `client_id`     | Integer      | FK → `clients.id` ON DELETE SET NULL, nullable, indexed |
| `created_at`    | DateTime     | (set by repo, not a DB default)               |
| `created_date`  | Date         | Computed column `(created_at::DATE)`, nullable (DB-generated, never written by app) |
| `searchable`    | TSVECTOR     | nullable                                      |

### `TimeEntriesRepository.create()` (called in the meeting time entry sub-path)

See Part 2, Section 4 below — same method signature applies.

---

---

# Part 2: `workmain time add`

---

## 1. CLI Help Output

```
Usage: workmain time add [OPTIONS] [DESCRIPTION] DURATION

  Log a time entry with optional meeting linkage.

  A note is automatically created for each time entry. When using --meeting,
  the note is linked to that meeting. For detailed meeting notes, use
  'workmain notes log' instead.

  Examples:
    workmain time add "Fixed login bug" 2h -T 14:30
    workmain time add "Team meeting" 1.5h -T 1430 -m "Daily Standup" -t ilo
    workmain time add "Meeting time" 1h -T 09:00 -m 42 -N "Discussed features"
    workmain time add 2h -T 14:30                   # prompts for description

Options:
  -T, --time TEXT        Start time in 24hr format (14:30 or 1430) or AM/PM
                         (2:30pm or 230pm)  [required]
  -d, --date TEXT        Date (YYYY-MM-DD, default: today)
  -C, --category TEXT    Category (e.g., development, meeting)
  -p, --project INTEGER  Project ID
  -m, --meeting TEXT     Link to meeting (title or ID)
  -N, --notes TEXT       Create note for meeting (requires --meeting)
  -t, --tags TEXT        Tags for note (comma-separated, e.g., ilo,cf).
                         Replaces default tag (ilo).
  -b, --start TEXT       Clock-in time for Clockify (HH:MM or HHMM, optional
                         override)
  -e, --end TEXT         Clock-out time for Clockify (HH:MM or HHMM, optional
                         override)
  --help                 Show this message and exit.
```

---

## 2. Click Command Signature

Source: `workmain/cli/commands/time.py` lines 181–196

```python
@time.command('add')
@click.argument('description', required=False, default=None)
@click.argument('duration')
@click.option('--time', '-T', required=True, help='Start time in 24hr format (14:30 or 1430) or AM/PM (2:30pm or 230pm)')
@click.option('--date', '-d', help='Date (YYYY-MM-DD, default: today)')
@click.option('--category', '-C', help='Category (e.g., development, meeting)')
@click.option('--project', '-p', type=int, help='Project ID')
@click.option('--meeting', '-m', help='Link to meeting (title or ID)')
@click.option('--notes', '-N', help='Create note for meeting (requires --meeting)')
@click.option('--tags', '-t', help='Tags for note (comma-separated, e.g., ilo,cf). Replaces default tag (ilo).')
@click.option('--start', '-b', help='Clock-in time for Clockify (HH:MM or HHMM, optional override)')
@click.option('--end', '-e', help='Clock-out time for Clockify (HH:MM or HHMM, optional override)')
def time_add(description: Optional[str], duration: str, time: str,
             date: Optional[str], category: Optional[str], project: Optional[int],
             meeting: Optional[str], notes: Optional[str], tags: Optional[str],
             start: Optional[str], end: Optional[str]):
```

Parameter summary:

| Name          | Kind     | Type  | Required | Default | Flags              |
|---------------|----------|-------|----------|---------|--------------------|
| `description` | ARGUMENT | str   | No       | None    | positional         |
| `duration`    | ARGUMENT | str   | Yes      | —       | positional         |
| `time`        | OPTION   | str   | Yes      | —       | `-T`/`--time`      |
| `date`        | OPTION   | str   | No       | None    | `-d`/`--date`      |
| `category`    | OPTION   | str   | No       | None    | `-C`/`--category`  |
| `project`     | OPTION   | int   | No       | None    | `-p`/`--project`   |
| `meeting`     | OPTION   | str   | No       | None    | `-m`/`--meeting`   |
| `notes`       | OPTION   | str   | No       | None    | `-N`/`--notes`     |
| `tags`        | OPTION   | str   | No       | None    | `-t`/`--tags`      |
| `start`       | OPTION   | str   | No       | None    | `-b`/`--start`     |
| `end`         | OPTION   | str   | No       | None    | `-e`/`--end`       |

---

## 3. Command Body Logic

Source: `workmain/cli/commands/time.py` lines 211–382

**Description prompt:**
- If `description` is falsy: `click.prompt('Description')` — interactive.

**Validation:**
- If `notes` is set and `meeting` is not set: prints error and returns early.

**Session setup:**
- `get_db()` + `db.get_session()` pattern.
- `TimeEntriesRepository` and `SystemStateRepository` constructed on the session.
- `active_client_id` read from `SystemStateRepository(session).get_int('active_client_id')`.

**Duration parsing:**
- `repo.parse_duration(duration)` → `duration_hours` (float). Raises `ValueError` on bad format; error printed and early return.

**Time parsing:**
- `repo.parse_time(time)` → `entry_time` (datetime.time). Raises `ValueError` on bad format; error printed and early return.

**Date parsing:**
- Default: `entry_date = datetime.today().date()`.
- If `--date` provided: `datetime.strptime(date, '%Y-%m-%d').date()`. Error on bad format → early return.

**Backdate note timestamp (derived value):**
- If `entry_date != datetime.today().date()`: `note_created_at = datetime.combine(entry_date, datetime.now().time())`.
- Otherwise: `note_created_at = None`.
- Passed to `notes_repo.create(created_at=note_created_at)` so `note.created_date` matches the intended entry date.

**Meeting resolution:**
- If `--meeting` provided:
  - `meeting.isdigit()`: look up by `meetings_repo.get_by_id(int(meeting))` first.
  - If not found or not digit: `meetings_repo.fuzzy_match(meeting, threshold=0.6)`.
  - If no fuzzy match: error + early return.
  - If multiple matches: interactive numbered picker.
  - `meeting_obj` is the resolved `Meeting` ORM object or `None`.

**Tag parsing:**
- Default: `note_tags = ['internal-only']`.
- If `--tags` provided: comma-separated short names converted to `#name` format, run through `parse_tags(tag_string, apply_default=False)`. Invalid tags warned but not blocking. If `parsed_tags` is non-empty, replaces the default (full replacement, not merge).

**Content/source/meeting_id routing (derived values):**
```python
# time.py lines 308–319
if notes and meeting_obj:
    primary_content = notes           # --notes value used as content
    primary_source = 'meeting'
    primary_meeting_id = meeting_obj.id
elif meeting_obj:
    primary_content = description     # description used as content
    primary_source = 'meeting'
    primary_meeting_id = meeting_obj.id
else:
    primary_content = description
    primary_source = 'task'
    primary_meeting_id = None
```

**Repository call — note created first (note-first pattern):**
```python
# time.py lines 322–328
note = notes_repo.create(
    content=primary_content,
    tags=note_tags,
    source=primary_source,
    meeting_id=primary_meeting_id,
    created_at=note_created_at,
)
```
Note: `client_id` and `project_id` are **not** passed to `notes_repo.create()` here.

**Repository call — time entry:**
```python
# time.py lines 330–339
entry = repo.create(
    note_id=note.id,
    duration_hours=duration_hours,
    entry_date=entry_date,
    entry_time=entry_time,
    category=category,
    project_id=project,
    meeting_id=meeting_obj.id if meeting_obj else None,
    client_id=active_client_id,
)
```

**Additional note prompt (meeting path without `--notes`):**
- If `meeting_obj` is set and `notes` was not provided: `click.confirm("Add additional notes to this meeting?", default=False)`.
- If confirmed: `click.prompt("Enter note content")` + third `notes_repo.create()` call:
  ```python
  # time.py lines 357–362
  extra_note = notes_repo.create(
      content=note_content,
      tags=note_tags,
      meeting_id=meeting_obj.id,
      created_at=note_created_at,
  )
  ```

**Clockify sync prompt:**
- `click.confirm("Sync to Clockify now?", default=False)`.
- If confirmed: `ClockifySync(session).push_entries(entries=[entry], interactive=True)`.

**`--start` and `--end` parameters:**
- Both are declared in the decorator (lines 191–192) and function signature (line 196).
- Neither `start` nor `end` is referenced anywhere in the function body.
- They are not passed to `ClockifySync.push_entries()` or to any other call.

**AI provider calls:** None.

**Derived/computed values:**
- `duration_hours` — parsed from `duration` string by `repo.parse_duration()`.
- `entry_time` — parsed from `time` string by `repo.parse_time()`.
- `entry_date` — defaults to today; overridden by `--date`.
- `note_created_at` — computed from `entry_date` for backdating; `None` if today.
- `note_tags` — defaults to `['internal-only']`; replaced (not merged) if `--tags` supplied.
- `primary_content`, `primary_source`, `primary_meeting_id` — all derived from combination of `notes`, `meeting_obj`, and `description`.
- `active_client_id` — from system state, not user input.

---

## 4. Repository Method(s) Called

### `NotesRepository.create()`

See Part 1, Section 4 above — same signature and constraints.

Differences in how `time add` calls it compared to `notes add`:
- `client_id` is **not** passed (not in any of the three `notes_repo.create()` call sites in `time_add`).
- `project_id` is not passed (not in any call site in `time_add`).
- `created_at` is passed as `note_created_at` (which is `None` for today, or `datetime.combine(entry_date, now().time())` when backdating).

### `TimeEntriesRepository.create()`

Source: `workmain/database/repositories/time_entries_repo.py` lines 84–134

```python
def create(
    self,
    note_id: int,
    duration_hours: float,
    entry_date: date,
    entry_time: Optional[time] = None,
    category: Optional[str] = None,
    project_id: Optional[int] = None,
    meeting_id: Optional[int] = None,
    client_id: Optional[int] = None,
    clockify_id: Optional[str] = None,
    synced_at: Optional[datetime] = None,
) -> TimeEntry:
```

**Validation inside the method:**
- `_validate_client_project_consistency(client_id, project_id)`: same logic as notes repo — raises `ValueError` on client/project mismatch.

**Defaults applied inside the method:**
- `duration_hours` stored as `Decimal(str(duration_hours))` — conversion from float to Decimal is applied internally.

**DB / model constraints on `TimeEntry`** (source: `workmain/database/models.py`):

| Column           | Type          | Constraint                                         |
|------------------|---------------|----------------------------------------------------|
| `id`             | Integer       | PRIMARY KEY                                        |
| `note_id`        | Integer       | FK → `notes.id` ON DELETE RESTRICT, NOT NULL       |
| `duration_hours` | DECIMAL(5,2)  | NOT NULL                                           |
| `entry_date`     | Date          | NOT NULL                                           |
| `entry_time`     | Time          | nullable                                           |
| `category`       | String(100)   | nullable                                           |
| `project_id`     | Integer       | FK → `projects.id` ON DELETE SET NULL, nullable    |
| `meeting_id`     | Integer       | FK → `meetings.id` ON DELETE SET NULL, nullable    |
| `client_id`      | Integer       | FK → `clients.id` ON DELETE SET NULL, nullable, indexed |
| `clockify_id`    | String(255)   | UNIQUE, nullable                                   |
| `synced_at`      | DateTime      | nullable                                           |

Migration reference for `note_id` column addition: `workmain/database/migrations/021_time_entries_note_id.sql`.

---

---

# Additional Section: Action Executor Cross-Reference

Source: `workmain/orchestration/action_executor.py` lines 92–145

---

## `create_note` — `_execute_create_note` (lines 138–145)

```python
def _execute_create_note(self, action: dict) -> ActionResult:
    from workmain.database.repositories.notes_repo import NotesRepository

    content = action.get("content", "")
    tags = action.get("tags") or ["internal-only"]
    note_repo = NotesRepository(self.session)
    note = note_repo.create(content=content, tags=tags, source="ad-hoc")
    return ActionResult(success=True, message="✓ Note saved.", entity_id=note.id)
```

**Fields the handler reads from the action dict:**
- `content` (string)
- `tags` (array, or `["internal-only"]` as fallback if absent/falsy)

**Parameters `NotesRepository.create()` accepts that the handler does NOT pass (or passes a hardcoded value):**

| Parameter    | Passed?      | Value used                    |
|--------------|--------------|-------------------------------|
| `source`     | Hardcoded    | `"ad-hoc"`                    |
| `project_id` | Not passed   | `None` (repo default)         |
| `meeting_id` | Not passed   | `None` (repo default)         |
| `created_at` | Not passed   | `None` → `datetime.now()` in repo |
| `client_id`  | Not passed   | `None` (repo default)         |

**CLI options from Section 2 (`notes add`) that have no corresponding field in the handler:**

| CLI option        | Flags  | No action dict field, not read by handler |
|-------------------|--------|-------------------------------------------|
| `--meeting`       | `-m`   | Not present in handler                    |
| `--project`       | `-p`   | Not present in handler                    |
| `--source`        | `-f`   | Hardcoded `"ad-hoc"` in handler           |

---

## `create_time_entry` — `_execute_create_time_entry` (lines 92–136)

```python
def _execute_create_time_entry(self, action: dict) -> ActionResult:
    from workmain.database.repositories.notes_repo import NotesRepository
    from workmain.database.repositories.time_entries_repo import TimeEntriesRepository

    description = action.get("description", "")
    duration_minutes = int(action.get("duration_minutes", 0))
    duration_hours = duration_minutes / 60.0

    entry_time = None
    start_time_str = action.get("start_time")
    if start_time_str:
        try:
            s = str(start_time_str).strip()
            if ":" in s:
                parts = s.split(":")
                entry_time = time_type(int(parts[0]), int(parts[1]))
            elif len(s) == 4 and s.isdigit():
                entry_time = time_type(int(s[:2]), int(s[2:]))
            else:
                raise ValueError(f"unrecognised format: {s!r}")
        except (ValueError, IndexError, AttributeError):
            logger.warning("Invalid start_time format '%s', ignoring", start_time_str)

    note_repo = NotesRepository(self.session)
    note = note_repo.create(
        content=description,
        tags=["internal-only"],
        source="task",
    )
    time_repo = TimeEntriesRepository(self.session)
    entry = time_repo.create(
        note_id=note.id,
        duration_hours=duration_hours,
        entry_date=date.today(),
        entry_time=entry_time,
    )
    ...
```

**Fields the handler reads from the action dict:**
- `description` (string)
- `duration_minutes` (integer, converted to `duration_hours`)
- `start_time` (string, optional; parsed to `datetime.time` or silently ignored on parse error)

**Parameters `NotesRepository.create()` accepts that the handler does NOT pass (or passes a hardcoded value) — first call in handler:**

| Parameter    | Passed?      | Value used                        |
|--------------|--------------|-----------------------------------|
| `tags`       | Hardcoded    | `["internal-only"]`               |
| `source`     | Hardcoded    | `"task"`                          |
| `project_id` | Not passed   | `None` (repo default)             |
| `meeting_id` | Not passed   | `None` (repo default)             |
| `created_at` | Not passed   | `None` → `datetime.now()` in repo |
| `client_id`  | Not passed   | `None` (repo default)             |

**Parameters `TimeEntriesRepository.create()` accepts that the handler does NOT pass (or passes a hardcoded value):**

| Parameter    | Passed?      | Value used                  |
|--------------|--------------|-----------------------------|
| `entry_date` | Hardcoded    | `date.today()`              |
| `category`   | Not passed   | `None` (repo default)       |
| `project_id` | Not passed   | `None` (repo default)       |
| `meeting_id` | Not passed   | `None` (repo default)       |
| `client_id`  | Not passed   | `None` (repo default)       |
| `clockify_id`| Not passed   | `None` (repo default)       |
| `synced_at`  | Not passed   | `None` (repo default)       |

**CLI options from Section 2 (`time add`) that have no corresponding field in the handler:**

| CLI option    | Flags  | No action dict field, not read by handler          |
|---------------|--------|----------------------------------------------------|
| `--date`      | `-d`   | Not present; `entry_date` hardcoded to `date.today()` |
| `--category`  | `-C`   | Not present in handler                             |
| `--project`   | `-p`   | Not present in handler                             |
| `--meeting`   | `-m`   | Not present in handler                             |
| `--notes`     | `-N`   | Not present in handler                             |
| `--tags`      | `-t`   | Hardcoded `["internal-only"]` for note             |
| `--start`     | `-b`   | Not present (also unused in CLI command body)      |
| `--end`       | `-e`   | Not present (also unused in CLI command body)      |

---

---

# Additional Section: Schema Cross-Reference

Source: `config/intent_parse_system_prompt.txt` config_version 1.6

---

## `create_note` schema definition

```
1. create_note
   Required: content (string)
   Optional: tags (array of strings from: internal-only, client-report,
             info-only, carry-forward, blocker)
```

**Field-by-field cross-reference with action_executor:**

| Schema field | Handler reads it?                                               |
|--------------|-----------------------------------------------------------------|
| `content`    | Yes — `action.get("content", "")`                              |
| `tags`       | Yes — `action.get("tags") or ["internal-only"]`                |

**CLI options from `notes add` Section 2 with no equivalent schema field:**

| CLI option | Flags | Present in schema? |
|------------|-------|--------------------|
| `--meeting`| `-m`  | No                 |
| `--project`| `-p`  | No                 |
| `--source` | `-f`  | No                 |

---

## `create_time_entry` schema definition

```
2. create_time_entry
   Required: duration_minutes (integer), description (string)
   Optional: start_time (string — 24-hour HH:MM or HHMM, only if explicitly stated),
             project (string)
```

**Field-by-field cross-reference with action_executor:**

| Schema field       | Handler reads it?                                              |
|--------------------|----------------------------------------------------------------|
| `duration_minutes` | Yes — `action.get("duration_minutes", 0)`, converted to hours |
| `description`      | Yes — `action.get("description", "")`                         |
| `start_time`       | Yes — `action.get("start_time")`, parsed to `datetime.time`   |
| `project`          | No — schema defines it as optional; handler does not read it  |

**CLI options from `time add` Section 2 with no equivalent schema field:**

| CLI option    | Flags  | Present in schema? |
|---------------|--------|--------------------|
| `--date`      | `-d`   | No                 |
| `--category`  | `-C`   | No                 |
| `--meeting`   | `-m`   | No                 |
| `--notes`     | `-N`   | No                 |
| `--tags`      | `-t`   | No                 |
| `--start`     | `-b`   | No                 |
| `--end`       | `-e`   | No                 |

Note: The schema `project` field (string type) has no equivalent in the action_executor handler and no direct equivalent in the CLI `--project` option (which accepts an integer project ID, not a project name string).
