WorkmAIn
ACTION_AUDIT_TRACK1_FOLLOWUP v1.0
20260612

Follow-up recon for Phase 13 Sprint 3 action audit, Items 1 & 2.
Answers five open questions from ACTION_AUDIT_TRACK1_ITEMS1-2.md
needed to scope the Option A service-layer design.

No code was modified. No recommendations are made. DB queries were
SELECT-only.

---

# A. `entry_time` NOT NULL Feasibility

---

## A.1 All `TimeEntriesRepository.create()` Call Sites

The following are every call site of `TimeEntriesRepository.create()`
across the codebase, excluding test files.

---

### Call site 1 — `workmain/cli/commands/notes.py:406`

Context: `notes add` — meeting time entry sub-prompt (fires only if user confirms
"Create time entry for this meeting?" after adding a note linked to a meeting).

```python
# notes.py lines 406-414
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

`entry_time` value: `note.meeting.start_time.time()` — derived from the meeting's
`start_time` DateTime field. Always set (meeting.start_time is NOT NULL per model).

---

### Call site 2 — `workmain/cli/commands/notes.py:759`

Context: `notes log` — meeting condensation sub-flow (fires only if user confirms
"Condense notes and create time entry?" and no existing time entry for the meeting
date is found).

```python
# notes.py lines 759-768
entry = time_repo.create(
    note_id=condensed_note.id,
    duration_hours=duration_hours,
    entry_date=meeting_obj.start_time.date(),
    entry_time=meeting_obj.start_time.time(),
    category='meeting',
    meeting_id=meeting_obj.id,
    client_id=active_client_id,
)
```

`entry_time` value: `meeting_obj.start_time.time()` — derived from meeting start.
Always set.

---

### Call site 3 — `workmain/cli/commands/time.py:330`

Context: `time add` command — primary creation path.

```python
# time.py lines 330-339
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

`entry_time` value: result of `repo.parse_time(time)` where `time` is the value
of the `-T`/`--time` option, which is declared `required=True`. Always set (required
option; parse failure causes early return before this line).

---

### Call site 4 — `workmain/cli/commands/meetings.py:758`

Context: `meetings track` command — manually creates a time entry for a meeting
(command name not confirmed, but context is the meeting time-entry creation flow).

```python
# meetings.py lines 758-765
entry = time_repo.create(
    note_id=note.id,
    duration_hours=duration_hours,
    entry_date=meeting.start_time.date(),
    entry_time=meeting.start_time.time(),
    category='meeting',
    meeting_id=meeting.id,
)
```

`entry_time` value: `meeting.start_time.time()` — derived from meeting start.
Always set. Note: `client_id` is not passed here.

---

### Call site 5 — `workmain/cli/commands/meetings.py:968`

Context: `meetings condense` command — creates a new time entry when no existing
entry for the meeting date is found.

```python
# meetings.py lines 968-975
entry = time_repo.create(
    note_id=condensed_note.id,
    duration_hours=duration_hours,
    entry_date=meeting.start_time.date(),
    entry_time=meeting.start_time.time(),
    category='meeting',
    meeting_id=meeting.id,
)
```

`entry_time` value: `meeting.start_time.time()` — derived from meeting start.
Always set. Note: `client_id` is not passed here.

---

### Call site 6 — `workmain/orchestration/action_executor.py:122`

Context: `create_time_entry` action handler — IntentParser path.

```python
# action_executor.py lines 122-127
entry = time_repo.create(
    note_id=note.id,
    duration_hours=duration_hours,
    entry_date=date.today(),
    entry_time=entry_time,
)
```

`entry_time` value: `entry_time` — set to a `datetime.time` object parsed from
`action.get("start_time")`, or `None` if `start_time` is absent from the action
dict or fails to parse. This is the only call site where `entry_time` may be `None`.

---

### Call site 7 — `workmain/integrations/clockify/sync.py:336`

Context: Clockify pull import — creates a local time entry from a Clockify entry.

```python
# sync.py lines 336-343
entry = self.repo.create(
    note_id=note.id,
    duration_hours=duration_hours,
    entry_date=start_dt.date(),
    entry_time=start_dt.time().replace(tzinfo=None),
    clockify_id=clockify_entry['id'],
    synced_at=datetime.now(),
)
```

`entry_time` value: `start_dt.time().replace(tzinfo=None)` — derived from the
Clockify entry's `timeInterval.start` timestamp. Always set (Clockify API always
returns a start time).

---

## A.2 Database Query Results

```sql
SELECT COUNT(*) FROM time_entries WHERE entry_time IS NULL;
```

Result: **0**

No follow-up query needed.

---

## A.3 `entry_time` Column Definition — Verbatim

**`workmain/database/models.py` line 315:**

```python
entry_time = Column(Time, nullable=True)  # 24-hour format: 14:30, 09:00
```

**`workmain/database/migrations/001_initial_schema.sql` line 89:**

```sql
entry_time TIME,  -- Time of day (24-hour format)
```

(No `NOT NULL` constraint in either the original schema or any subsequent migration.
Migration 021 did not touch the `entry_time` column.)

---

---

# B. Tag Vocabulary Enforcement

---

## B.1 `config/tags.json` — Full Contents

```json
{
    "version": "1.0",
    "description": "WorkmAIn Tag System Configuration",
    "last_updated": "2025-12-22",
    "default_tag": "ilo",
    "tag_mappings": {
        "ilo": {
            "full_name": "internal-only",
            "display": "[internal-only]",
            "description": "Internal reports only, excluded from client reports",
            "report_inclusion": {
                "daily_internal": true,
                "weekly_client": false
            }
        },
        "cr": {
            "full_name": "client-report",
            "display": "[client-report]",
            "description": "Client reports only, excluded from internal reports",
            "report_inclusion": {
                "daily_internal": false,
                "weekly_client": true
            }
        },
        "ifo": {
            "full_name": "info-only",
            "display": "[info-only]",
            "description": "Reference only, excluded from all reports",
            "report_inclusion": {
                "daily_internal": false,
                "weekly_client": false
            }
        },
        "both": {
            "full_name": "both",
            "display": "[both]",
            "description": "Include in both internal and client reports",
            "report_inclusion": {
                "daily_internal": true,
                "weekly_client": true
            }
        },
        "cf": {
            "full_name": "carry-forward",
            "display": "[carry-forward]",
            "description": "Tasks in progress, carry to next period",
            "report_inclusion": {
                "daily_internal": true,
                "weekly_client": true
            }
        },
        "blk": {
            "full_name": "blocker",
            "display": "[blocker]",
            "description": "Blockers and issues requiring attention",
            "report_inclusion": {
                "daily_internal": true,
                "weekly_client": false
            }
        }
    },
    "validation": {
        "case_sensitive": false,
        "allow_unknown_tags": false,
        "normalize_order": true,
        "remove_duplicates": true
    },
    "display_options": {
        "show_brackets": true,
        "separator": " ",
        "sort_alphabetically": true
    }
}
```

Valid short names: `ilo`, `cr`, `ifo`, `both`, `cf`, `blk`.
Valid full names: `internal-only`, `client-report`, `info-only`, `both`,
`carry-forward`, `blocker`.

---

## B.2 All Locations Reading `config/tags.json` or Calling `get_tag_system()`

| File | Line | Usage |
|------|------|-------|
| `workmain/utils/tag_utils.py` | 37–42 | `TagSystem.__init__()` — loads `config/tags.json` via `Path(__file__).parent.parent.parent / "config" / "tags.json"`; this is the only file that reads the JSON directly |
| `workmain/utils/tag_utils.py` | 352–357 | `get_tag_system()` — creates/returns singleton `TagSystem` instance |
| `workmain/utils/tag_utils.py` | 368 | `parse_tags()` convenience function — calls `get_tag_system().process_tags()` |
| `workmain/utils/tag_utils.py` | 382 | `format_tags()` convenience function — calls `get_tag_system().format_display()` |
| `workmain/utils/tag_utils.py` | 388 | `format_tags_short()` convenience function — calls `get_tag_system().format_short()` |
| `workmain/utils/tag_utils.py` | 396 | `get_valid_tags()` convenience function — calls `get_tag_system().get_valid_tags_list()` |
| `workmain/cli/commands/notes.py` | 73 | `from workmain.utils.tag_utils import parse_tags, get_tag_system` — `parse_tags` used throughout; `get_tag_system()` called directly at line 348 only (inside the invalid-tag correction branch) |
| `workmain/cli/commands/time.py` | 295 | `from workmain.utils.tag_utils import parse_tags` — `parse_tags` called at line 302 to process the `--tags` option value |
| `workmain/database/models.py` | 255 | `from workmain.utils.tag_utils import format_tags` — used inside `Note.display_tags` property to format the stored full-name array for display |
| `workmain/cli/commands/tasks.py` | 33 | `from workmain.utils.tag_utils import format_tags_short` — used in task display formatting |

---

## B.3 `interactive_correction()` — Full Source

Source: `workmain/utils/tag_utils.py` lines 278–327

```python
def interactive_correction(
    self, 
    text: str, 
    invalid_tags: List[str],
    valid_tags: List[str]
) -> Optional[List[str]]:
    """
    Prompt user to correct invalid tags interactively.
    
    Args:
        text: Original text (for context)
        invalid_tags: List of invalid tag shortcuts
        valid_tags: List of valid tag shortcuts that were found
        
    Returns:
        List of corrected tag shortcuts, or None if user cancels
    """
    print(f"\n⚠️  Warning: Unknown tag(s): {', '.join(f'#{t}' for t in invalid_tags)}")
    print(f"Valid tags: {', '.join(f'#{t}' for t in self.get_valid_tags_list())}")
    
    # Show current valid tags
    if valid_tags:
        converted = self.convert_to_full_names(valid_tags)
        print(f"\nCurrent valid tags: {self.format_display(converted)}")
    
    print("\nOptions:")
    print("  1. Save note with valid tags only")
    print("  2. Correct the tags")
    print("  3. Cancel")
    
    choice = input("\nChoice (1-3): ").strip()
    
    if choice == "1":
        return valid_tags
    elif choice == "2":
        current_tags_str = " ".join(f"#{t}" for t in valid_tags) if valid_tags else ""
        prompt = f"Enter corrected tags (or press Enter to keep {current_tags_str or 'no tags'}): "
        corrected = input(prompt).strip()
        
        if not corrected:
            return valid_tags
        
        # Extract tags from corrected input
        _, new_tags = self.extract_tags(corrected)
        return new_tags
    elif choice == "3":
        return None
    else:
        print("Invalid choice. Cancelling.")
        return None
```

**Question: Can an invalid tag proceed unchanged?**

`interactive_correction()` itself returns shortcut strings (not full names), not
validated. Via option 2, `self.extract_tags(corrected)` extracts any `#word`
tokens from user input but does NOT validate them against the vocabulary. So
`interactive_correction()` CAN return invalid shortcuts.

However, the caller in `notes.py` (lines 358–360) re-processes the returned list
through `parse_tags()` before passing to the repo:

```python
# notes.py lines 358-360
tag_str = " ".join(f"#{t}" for t in corrected)
_, all_tags, _ = parse_tags(tag_str, apply_default=True)
```

`parse_tags()` calls `validate_tags()`, which drops any tag not in
`self.tag_mappings`. The discarded-invalid result (`_`) is ignored by the caller.
The `all_tags` list passed to `notes_repo.create()` will therefore contain only
valid full names.

There is no non-interactive path through `interactive_correction()`. Every branch
either returns a list (possibly empty) or `None`. A `None` return is treated as
cancel in the caller.

---

## B.4 `parse_tags()` Vocabulary Validation

Source: `workmain/utils/tag_utils.py` lines 361–369 (`parse_tags` convenience
function), which delegates to `TagSystem.process_tags()` lines 241–276.

The validation step inside `process_tags()`:

```python
# tag_utils.py lines 268-274
# Validate tags
valid_tags, invalid_tags = self.validate_tags(raw_tags)

# Convert to full names
full_tags = self.convert_to_full_names(valid_tags)

# Normalize (remove duplicates, sort)
normalized_tags = self.normalize_tags(full_tags)
```

`validate_tags()` (lines 101–120):

```python
def validate_tags(self, tags: List[str]) -> Tuple[List[str], List[str]]:
    valid = []
    invalid = []
    
    for tag in tags:
        if tag.lower() in self.tag_mappings:
            valid.append(tag.lower())
        else:
            invalid.append(tag)
    
    return valid, invalid
```

Validation is by membership in `self.tag_mappings` (the `tag_mappings` dict from
`config/tags.json`). Accepts short names only (e.g., `ilo`, `cf`); full names
(e.g., `internal-only`) are NOT in `tag_mappings` and would be returned as invalid.

`NotesRepository.create()` performs **no** vocabulary validation. The only
transformations inside the repo are dedup and alphabetical sort
(`sorted(set(tags)) if tags else []`). The repo accepts whatever list is passed.

---

## B.5 Distinct Tag Values in `notes` Table

```sql
SELECT DISTINCT unnest(tags) AS tag FROM notes ORDER BY tag;
```

Results:

```
both
carry-forward
info-only
internal-only
(empty string)
```

Five distinct values. The empty string value indicates at least one row in the
`notes` table has an array containing an empty string element (`''`).

The four named values — `both`, `carry-forward`, `info-only`, `internal-only` —
are all within the `config/tags.json` vocabulary (full names). `client-report` and
`blocker` have no rows. The empty string is outside the vocabulary.

---

---

# C. Meeting Resolution

---

## C.1 `MeetingsRepository` Method Signatures

Source: `workmain/database/repositories/meetings_repo.py`

### `get_by_id()`

```python
# meetings_repo.py line 151
def get_by_id(self, meeting_id: int) -> Optional[Meeting]:
```

Queries `Meeting.id == meeting_id`. Returns first match or `None`.

### `get_by_title()`

```python
# meetings_repo.py line 163
def get_by_title(self, title: str, exact: bool = True) -> Optional[Meeting]:
```

- `exact=True` (default): `Meeting.title == title` (exact string equality)
- `exact=False`: `func.lower(Meeting.title) == func.lower(title)` (case-insensitive)

Both branches use `.order_by(Meeting.start_time.desc()).first()` — returns the
most recent meeting with that title, or `None`.

### `fuzzy_match()`

```python
# meetings_repo.py line 199
def fuzzy_match(self, title: str, threshold: float = 0.6) -> List[Tuple[Meeting, float]]:
```

Primary path: PostgreSQL `pg_trgm` `similarity()` function with a GIN index.
Filters `similarity(Meeting.title, title) >= threshold`. Orders by similarity
descending, then by proximity to `now()` ascending (so today's recurring instance
ranks highest on ties).

Fallback path (if `pg_trgm` unavailable): Python `difflib.SequenceMatcher` ratio
against all meetings. Same threshold. Same sort order.

Returns `List[Tuple[Meeting, float]]` — list of `(meeting_object, score)` pairs.
Empty list if no matches above threshold.

---

## C.2 `fuzzy_match_meeting()` — Full Source

Source: `workmain/cli/commands/notes.py` lines 170–231

```python
def fuzzy_match_meeting(meetings_repo: MeetingsRepository, title: str) -> Optional[int]:
    """
    Try to match meeting by ID or fuzzy title match.

    Args:
        meetings_repo: Meetings repository
        title: Meeting title or numeric ID string

    Returns:
        Meeting ID or None if cancelled
    """
    # Try ID first (Item 26 Direction B fix)
    if title.isdigit():
        meeting = meetings_repo.get_by_id(int(title))
        if meeting:
            return meeting.id
        click.echo(f"✗ No meeting found with ID {title}")
        return None

    exact = meetings_repo.get_by_title(title, exact=False)
    if exact:
        return exact.id

    matches = meetings_repo.fuzzy_match(title, threshold=0.6)

    if not matches:
        create = click.confirm(f"No meeting found matching '{title}'. Create new?", default=True)
        if create:
            meeting = meetings_repo.find_or_create(title)
            return meeting.id
        return None

    click.echo(f"\n⚠️  No exact match for '{title}'")
    click.echo("Did you mean:")

    today = datetime.now().date()

    for i, (meeting, score) in enumerate(matches[:5], 1):
        note_count = meetings_repo.get_note_count(meeting.id)
        meeting_date = meeting.start_time.strftime('%Y-%m-%d %H:%M')
        is_today = meeting.start_time.date() == today
        today_marker = " ← Today" if is_today else ""
        click.echo(f"  {i}. [#{meeting.id}] {meeting.title} ({meeting_date}, {note_count} notes, {score*100:.0f}% match){today_marker}")

    click.echo(f"  N. Create new meeting '{title}'")

    choice = click.prompt("\nSelect", type=str, default='1')

    if choice.lower() == 'n':
        meeting = meetings_repo.find_or_create(title)
        return meeting.id

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(matches):
            return matches[idx][0].id
        else:
            click.echo("Invalid selection.")
            return None
    except ValueError:
        click.echo("Invalid input.")
        return None
```

---

## C.3 `interactive_meeting_picker()` — Full Source

Source: `workmain/cli/commands/notes.py` lines 118–167

```python
def interactive_meeting_picker(meetings_repo: MeetingsRepository) -> Optional[int]:
    """
    Show interactive meeting picker.

    Args:
        meetings_repo: Meetings repository

    Returns:
        Meeting ID or None if cancelled
    """
    recent = meetings_repo.get_recent(limit=10)

    if not recent:
        click.echo("No recent meetings found.")
        create = click.confirm("Create new meeting?", default=True)
        if create:
            title = click.prompt("Meeting title")
            meeting = meetings_repo.find_or_create(title)
            return meeting.id
        return None

    click.echo("\nRecent meetings:")
    today = datetime.now().date()

    for i, meeting in enumerate(recent, 1):
        note_count = meetings_repo.get_note_count(meeting.id)
        meeting_date = meeting.start_time.strftime('%Y-%m-%d %H:%M')
        is_today = meeting.start_time.date() == today
        today_marker = " ← Today" if is_today else ""
        click.echo(f"  {i}. [#{meeting.id}] {meeting.title} ({meeting_date}, {note_count} notes){today_marker}")

    click.echo(f"  N. New meeting")

    choice = click.prompt("\nSelect meeting", type=str)

    if choice.lower() == 'n':
        title = click.prompt("Meeting title")
        meeting = meetings_repo.find_or_create(title)
        return meeting.id

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(recent):
            return recent[idx].id
        else:
            click.echo("Invalid selection.")
            return None
    except ValueError:
        click.echo("Invalid input.")
        return None
```

**Question: Does it have any non-interactive / programmatic path?**

No. Every code path in `interactive_meeting_picker()` requires terminal input via
`click.confirm()` or `click.prompt()`. There is no path that returns a meeting ID
without blocking on user input. The only non-blocking return is `None` from the
`if not recent` → `click.confirm` → user declines path — but that still requires
a terminal interaction (the confirm prompt).

`interactive_meeting_picker()` is called from `notes_add` only when `--meeting`
is passed with an empty string value (i.e., the flag is present but no value
follows it on the command line).

---

## C.4 `parse_duration()` and `parse_time()` — Full Source

Source: `workmain/database/repositories/time_entries_repo.py`

### `parse_duration()`

Lines 593–645:

```python
def parse_duration(self, duration_str: str) -> float:
    """
    Parse duration string to hours.
    
    Args:
        duration_str: Duration string (e.g., "1.5h", "2h", "30m", "1h30m")
        
    Returns:
        Duration in hours as float
        
    Raises:
        ValueError: If duration string is invalid
    """
    duration_str = duration_str.lower().strip()
    
    hours = 0.0
    minutes = 0.0
    
    # Check for hours
    if 'h' in duration_str:
        parts = duration_str.split('h')
        try:
            hours = float(parts[0])
            # Check if there are minutes after hours
            if len(parts) > 1 and parts[1]:
                remainder = parts[1].replace('m', '').strip()
                if remainder:
                    minutes = float(remainder)
        except ValueError:
            raise ValueError(f"Invalid duration format: {duration_str}")
    
    # Check for minutes only
    elif 'm' in duration_str:
        try:
            minutes = float(duration_str.replace('m', '').strip())
        except ValueError:
            raise ValueError(f"Invalid duration format: {duration_str}")
    
    # Try parsing as plain number (assume hours)
    else:
        try:
            hours = float(duration_str)
        except ValueError:
            raise ValueError(
                f"Invalid duration format: {duration_str}. "
                "Expected format: 1.5h, 2h, 30m, or 1h30m"
            )
    
    total_hours = hours + (minutes / 60.0)
    
    return total_hours
```

Accepted formats: `1.5h`, `2h`, `30m`, `1h30m`, plain float (treated as hours).

### `parse_time()`

Lines 647–719:

```python
def parse_time(self, time_str: str) -> time:
    """
    Parse time string to time object (24-hour format).
    
    Supports multiple formats:
    - 24-hour with colon: "14:30", "09:00"
    - 24-hour without colon: "1430", "0900", "930"
    - 12-hour with colon: "2:30pm", "9:00am"
    - 12-hour without colon: "230pm", "900am"
    
    Args:
        time_str: Time string
        
    Returns:
        time object in 24-hour format
        
    Raises:
        ValueError: If time string is invalid
    """
    time_str = time_str.lower().strip()
    
    # Check for AM/PM
    is_pm = 'pm' in time_str
    is_am = 'am' in time_str
    
    # Remove am/pm markers
    time_str = time_str.replace('am', '').replace('pm', '').strip()
    
    # Try parsing with colon first
    if ':' in time_str:
        try:
            parsed = datetime.strptime(time_str, '%H:%M').time()
            
            # Convert 12-hour to 24-hour if needed
            if is_pm and parsed.hour != 12:
                parsed = parsed.replace(hour=parsed.hour + 12)
            elif is_am and parsed.hour == 12:
                parsed = parsed.replace(hour=0)
            
            return parsed
        except ValueError:
            pass
    
    # Try parsing without colon (military time or 12-hour without colon)
    try:
        # Pad to 4 digits if needed
        if len(time_str) == 3:
            time_str = '0' + time_str
        elif len(time_str) == 1 or len(time_str) == 2:
            time_str = time_str.zfill(2) + '00'
        
        if len(time_str) == 4:
            hours = int(time_str[:2])
            minutes = int(time_str[2:])
            
            # Validate
            if hours > 23 or minutes > 59:
                raise ValueError("Invalid hours or minutes")
            
            # Convert 12-hour to 24-hour if needed
            if is_pm and hours != 12:
                hours += 12
            elif is_am and hours == 12:
                hours = 0
            
            return time(hours, minutes)
    except (ValueError, IndexError):
        pass
    
    raise ValueError(
        f"Invalid time format: {time_str}. "
        "Expected format: HH:MM (24hr) or H:MMam/pm (12hr)"
    )
```

Note: `parse_time()` always returns a `time` object or raises `ValueError`. It has
no path that returns `None`. This is distinct from the `action_executor.py` start_time
handling which has its own inline parse logic and returns `None` on failure.

---

---

# D. Project Field Implementation Status

---

## D.1 `ProjectsRepository` Existence

No `ProjectsRepository` class exists anywhere in
`workmain/database/repositories/` or elsewhere in the codebase. There is no
Python file in the project that defines a repository for the `projects` table.

---

## D.2 `--project` / `project_id` Usage Across CLI Command Files

All usages are in two files: `notes.py` and `time.py`. In every case the value is
passed through as-is (integer) directly to the repository create/update call with
no validation, lookup, or name resolution.

| File | Decorator line | Call site line | Command | What happens with value |
|------|----------------|----------------|---------|-------------------------|
| `notes.py` | 289 | 367 | `notes add` | Passed as `project_id=project` to `notes_repo.create()` |
| `notes.py` | 427 | 490 | `notes edit` | Passed as `project_id=project` to `notes_repo.update()` |
| `time.py` | 187 | 336 | `time add` | Passed as `project_id=project` to `time_repo.create()` |
| `time.py` | 391 | 442 | `time edit` | Passed as `project_id=project` to `time_repo.update()` |

The Click option is declared `type=int` in all four cases, so Click itself enforces
that the supplied value is an integer. No existence check against the `projects`
table is performed in any of these call sites before the repo call.

The only enforcement of project validity is inside `_validate_client_project_consistency()`
in both repositories — which raises `ValueError` if `project_id` is set but the
project does not exist.

---

## D.3 Project-by-Name Resolution

There is no method anywhere in the local-DB layer of the codebase that resolves a
project name (string) to a `project_id` (integer).

One method exists in the Clockify integration layer only:

```python
# workmain/integrations/clockify/client.py line 249
def find_project_by_name(self, project_name: str) -> Optional[Dict[str, Any]]:
    """
    Find a Clockify project by name.
    
    Args:
        project_name: Name of project to find
        
    Returns:
        dict: Project data if found, None otherwise
    """
    workspace_id = self.get_workspace_id()
    url = f"{self.BASE_URL}/workspaces/{workspace_id}/projects"
    headers = self.auth.get_auth_headers()
    
    params = {"name": project_name}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    projects = response.json()
    return projects[0] if projects else None
```

This queries the Clockify API (not the local PostgreSQL database) and returns
a Clockify project dict, not a local `project_id` integer.

---

## D.4 `Project` Model Definition

Source: `workmain/database/models.py` lines 92–121

```python
class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    
    client_id = Column(
        Integer,
        ForeignKey('clients.id', ondelete='SET NULL'),
        nullable=True
    )

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default='active')
    clockify_project_id = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

| Column               | Type         | Constraint                                        |
|----------------------|--------------|---------------------------------------------------|
| `id`                 | Integer      | PRIMARY KEY                                       |
| `client_id`          | Integer      | FK → `clients.id` ON DELETE SET NULL, nullable    |
| `name`               | String(255)  | NOT NULL                                          |
| `description`        | Text         | nullable                                          |
| `status`             | String(50)   | nullable, default `'active'`                      |
| `clockify_project_id`| String(255)  | nullable                                          |
| `start_date`         | Date         | nullable                                          |
| `end_date`           | Date         | nullable                                          |
| `created_at`         | DateTime     | default `datetime.now`                            |
| `updated_at`         | DateTime     | default `datetime.now`, `onupdate=datetime.now`   |

No UNIQUE constraint on `name`. No index on `name` declared in the model.
