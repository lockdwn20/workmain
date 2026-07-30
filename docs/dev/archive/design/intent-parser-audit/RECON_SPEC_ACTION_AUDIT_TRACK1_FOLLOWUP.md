WorkmAIn
RECON_SPEC_ACTION_AUDIT_TRACK1_FOLLOWUP v1.0
20260612

# Purpose

Follow-up recon for Phase 13 Sprint 3 action audit, Items 1 & 2
(`create_note` / `create_time_entry`). This is recon only — no code
changes, no migrations, no fixes, no architectural recommendations.

This pass answers five open questions from the prior audit
(`ACTION_AUDIT_TRACK1_ITEMS1-2.md`) needed to scope the Option A
service-layer design.

Do not modify any files. Do not run migrations. Read-only DB queries
(SELECT only) are fine for the data-existence checks below.

---

# Output

Produce a single new file:
`docs/dev/design/intent-parser-audit-20260612/ACTION_AUDIT_TRACK1_FOLLOWUP.md`

Do not edit any other files.

---

# A. `entry_time` NOT NULL feasibility

1. Find every call site of `TimeEntriesRepository.create()` across the
   entire codebase (not just `time.py` / `notes.py` / `action_executor.py`
   already covered). For each call site, report:
   - File and line number
   - The value passed for `entry_time` (literal, variable, or omitted
     entirely → defaults to `None`)
   - One-line context of what triggers this call (e.g. "Clockify sync
     pull", "meeting condensation", "EOD step N")

2. Run a read-only query against the database:
   ```sql
   SELECT COUNT(*) FROM time_entries WHERE entry_time IS NULL;
   ```
   Report the count. If non-zero, also report:
   ```sql
   SELECT id, entry_date, note_id, created_at
   FROM time_entries WHERE entry_time IS NULL
   ORDER BY entry_date DESC LIMIT 20;
   ```

3. Confirm the current `entry_time` column definition in
   `workmain/database/models.py` (type, nullable) and in the relevant
   migration file, verbatim.

---

# B. Tag vocabulary enforcement

1. Report the full contents of `config/tags.json` verbatim.

2. Find every location in the codebase that reads `config/tags.json`
   or calls `get_tag_system()`. For each, report file, line, and a
   one-line description of how the result is used.

3. Locate `interactive_correction()` (referenced in the prior audit as
   called from `notes.py` when invalid tags are detected). Report its
   full source. Specifically answer: does it ever allow an invalid tag
   to proceed unchanged (e.g. user dismisses/skips the picker), or does
   it always block/replace invalid tags before the repo call?

4. Locate where `parse_tags()` validates a tag against the configured
   vocabulary (if it does). Report the relevant source. Does
   `NotesRepository.create()` itself perform any vocabulary check, or
   only the dedup/sort already documented in the prior audit?

5. Run a read-only query to check for any existing tag values outside
   the `config/tags.json` vocabulary:
   ```sql
   SELECT DISTINCT unnest(tags) AS tag FROM notes ORDER BY tag;
   ```
   Report the full distinct list.

---

# C. Meeting resolution

For `create_time_entry` and `create_note`, `--meeting` resolution
currently uses `MeetingsRepository.get_by_id()`,
`MeetingsRepository.get_by_title()`, and `MeetingsRepository.fuzzy_match()`,
plus helper functions `fuzzy_match_meeting()` and
`interactive_meeting_picker()`.

1. Report full method signatures for `get_by_id()`, `get_by_title()`,
   and `fuzzy_match()` on `MeetingsRepository`, including return types
   and any threshold/parameters.

2. Report the full source of `fuzzy_match_meeting()` (called from
   `notes.py`).

3. Report the full source of `interactive_meeting_picker()` (called
   from `notes.py`). Specifically note: does it ONLY prompt
   interactively, or does it have any non-interactive/programmatic path
   (e.g. accepting a pre-selected index, or a "no match → return None
   without prompting" branch)?

4. Report the full source of `TimeEntriesRepository.parse_duration()`
   and `TimeEntriesRepository.parse_time()` (referenced in `time.py`
   as `repo.parse_duration()` / `repo.parse_time()`).

---

# D. Project field implementation status

1. Does a `ProjectsRepository` (or equivalent) exist? If so, report its
   full list of public method signatures.

2. Find every usage of `--project`/`-p` / `project_id` across all CLI
   command files (`notes.py`, `time.py`, any others). For each, report
   file, line, and what happens with the value (passed through as-is,
   validated, looked up by name, etc.)

3. Is there anywhere in the codebase that resolves a project by NAME
   (string) to a `project_id` (integer)? If yes, report the method. If
   no, state that explicitly.

4. Report the `Project` model definition from `workmain/database/models.py`
   (columns and constraints only).

---

# Format Notes

- Use the WorkmAIn document header convention (title, doc name + version,
  date) at the top of the output file.
- Quote source code and query results verbatim in fenced code blocks
  with file path / query comments.
- If something cannot be located, state that explicitly rather than
  omitting the section.
- Enumeration and verbatim reporting only — no recommendations, no
  severity judgments, no proposed fixes.
