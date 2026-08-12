WorkmAIn
RECON_SPEC_ACTION_AUDIT_TRACK1_ITEMS4-5 v1.0
20260623

# Purpose

Phase 13 Sprint 3 pre-work. This is recon only — no code changes,
no fixes, no migrations, no architectural decisions. The output is a
single reference document used in a separate planning session to design
any fixes.

This spec covers Track 1, Items 4 & 5:
- `confirm_report` ↔ report confirmation
- `correct_report` ↔ report correction

Do not modify any files. Do not run migrations. Read-only SELECT queries
are permitted for data-existence checks. Report what exists, as it
exists today.

---

# Preliminary Step — Rename Audit Folder

Before producing any output, rename the audit folder so it is no longer
date-scoped (the audit has grown beyond a single-day effort):

```bash
git mv docs/dev/design/intent-parser-audit-20260612 \
        docs/dev/design/intent-parser-audit
```

Use `git mv` to preserve history. All existing files in the folder move
with it. Do not commit this rename separately — it will be committed as
part of the same commit that adds the recon output file.

---

# Output

Produce a single new file:
`docs/dev/design/intent-parser-audit/ACTION_AUDIT_TRACK1_ITEMS4-5.md`

Do not edit any other files.

---

# A. CLI Command Discovery

The CLI command names for confirm/correct are not assumed — discover them
from the source before reporting anything else.

1. Report the full output of `workmain reports --help`. Quote verbatim.

2. For every subcommand listed under `workmain reports`, run
   `workmain reports <subcommand> --help` and report the output verbatim.

3. In the source file that defines the `reports` command group, list
   every `@reports.command()` decorator with its decorated function name.
   This is the authoritative command list, independent of `--help`.

If no standalone CLI command exists for one or both of confirm/correct,
state that explicitly and note how the operation is currently exposed to
the user (e.g., only through EOD interactive steps).

---

# B. CLI Command Implementation (for each confirm/correct command found)

If a standalone reports subcommand exists for confirm or correct, report
the following for each. If no such command exists, skip this section and
state that in the output.

## B.1. Click Command Signature

Full Click decorator stack (`@click.option`, `@click.argument`, etc.) —
every option/argument with its flags, type, default, required/optional
status, and help text, exactly as declared in source. Quote the actual
decorator code, not a paraphrase.

## B.2. Command Body Logic

List everything the command function body does beyond a direct repo call.
Specifically call out:
- Any derived/computed values
- Any defaults applied in the function body (vs. in decorators)
- Any interactive prompts (`click.prompt`, `click.confirm`, etc.)
- Any validation or error-raising before the main operation
- What DB write(s) occur — which repository method(s) are called,
  with the field(s) modified
- Whether the command modifies any table OTHER than `reports`
  (e.g., `notes`, `time_entries`)
- Any calls to eod_workflow functions or step runners
- Any calls to other commands or functions outside the local module

---

# C. Action Executor Handlers

In `workmain/orchestration/action_executor.py`:

1. Report the full source of `_execute_confirm_report` verbatim.
2. Report the full source of `_execute_correct_report` verbatim.

For each handler:
- List every field it reads from the incoming action dict.
- List every repository method it calls, with the exact parameters passed.
- State whether it calls any function from `eod_workflow.py` or any
  EOD-related helper. If yes, name the function. If no, state that
  explicitly.
- State whether it modifies any table OTHER than `reports`
  (e.g., `notes`, `time_entries`). If yes, report the write. If no,
  state that explicitly.

---

# D. EOD Workflow Step Runners

In `workmain/orchestration/eod_workflow.py`:

1. Find every method, function, or branch that handles report confirmation
   or correction — step runner methods, helper methods, and anything
   called during the confirmation or correction flow. Report the full
   source of each, verbatim.

2. For each method found:
   - What does it write to the database? Which tables, which fields?
   - Does it modify any table OTHER than `reports` (e.g., `notes`,
     `time_entries`)? State yes or no explicitly.
   - What parameters does it accept?

---

# E. Cross-Reference: action_executor vs eod_workflow

For each of `confirm_report` and `correct_report`:

1. Does the action_executor handler call any function from
   `eod_workflow.py`? Answer yes or no, name the function if yes.

2. If action_executor does NOT delegate to eod_workflow: list every
   DB write that action_executor performs for this action type, and
   separately list every DB write that the eod_workflow step runner
   performs. Present as two enumerated lists. Do not characterize
   which is correct — enumerate only.

3. If action_executor DOES delegate to eod_workflow: state which
   function it calls and what parameters it passes.

---

# F. Report Model and Status Fields

1. Report the full `Report` (or `Reports`) model definition from
   `workmain/database/models.py` — all columns, types, constraints,
   and relationships — verbatim.

2. Report any migration file(s) that added or modified fields related
   to report confirmation or correction status (e.g., `confirmed`,
   `corrected`, `status`, `confirmed_at`, `corrected_at`, or similar).
   Include the migration SQL verbatim.

3. Run the following read-only query and report the full results:

   ```sql
   SELECT column_name, data_type, is_nullable, column_default
   FROM information_schema.columns
   WHERE table_name = 'reports'
   ORDER BY ordinal_position;
   ```

---

# G. Underlying Data Mutation Check

The key architectural question for `correct_report` is whether it
closes the loop on underlying data or only stamps a status field
on the report record.

1. Search the entire codebase for any code path that modifies `notes`
   or `time_entries` records as part of a report correction flow.
   Include:
   - Any call to `NotesRepository` write methods (create, update,
     delete) originating from action_executor, eod_workflow, or any
     reports CLI command during a correction flow
   - Any call to `TimeEntriesRepository` write methods from the same
     locations
   - Any other data modification described as part of "correcting"
     a report

2. For each such code path found, report the file, function name,
   and relevant source lines verbatim.

3. If no such code path exists — if `correct_report` only modifies
   the `reports` table — state that explicitly.

---

# H. Schema Cross-Reference

Using `config/intent_parse_system_prompt.txt` (current config_version):

1. Report the full schema definition for the `confirm_report` action
   type verbatim.

2. Report the full schema definition for the `correct_report` action
   type verbatim.

For each schema field defined in either action type:
- State whether the corresponding action_executor handler reads it.
- State whether there is a corresponding parameter in the relevant
  CLI command (if one was found in section A/B).

Enumeration only — no recommendations.

---

# Format Notes

- Use the WorkmAIn document header convention (title, doc name +
  version, date) at the top of the output file.
- Quote source code and query results verbatim in fenced code blocks
  with file path / line number comments.
- If a referenced file, method, or command cannot be located, state
  that explicitly rather than omitting the section.
- Keep the output self-contained — the reviewing session will not have
  live access to the repo, only this document.
- Enumeration and verbatim reporting only — no recommendations, no
  severity judgments, no proposed fixes.
