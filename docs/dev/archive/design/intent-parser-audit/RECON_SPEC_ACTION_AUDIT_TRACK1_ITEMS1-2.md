WorkmAIn
RECON_SPEC_ACTION_AUDIT_TRACK1_ITEMS1-2 v1.0
20260612

# Purpose

Phase 13 Sprint 3 is blocked pending a full audit of how IntentParser action
types map to existing CLI commands. This is recon only — no code changes,
no fixes, no architectural decisions. The output is a single reference
document that will be used in a separate planning session to design the
fix.

This spec covers Track 1, Items 1 & 2 only:
- `create_note` ↔ `workmain notes add`
- `create_time_entry` ↔ `workmain time add`

Do not modify any files. Do not propose solutions. This is a fact-finding
pass — report what exists, as it exists today.

---

# Output

Produce a single new file: `docs/dev/design/intent-parser-audit-20260612/ACTION_AUDIT_TRACK1_ITEMS1-2.md`

Do not edit any other files.

---

# For EACH of the two commands (`notes add`, `time add`), include the following sections:

## 1. CLI Help Output
Full `--help` output for the command, verbatim.

## 2. Click Command Signature
The full Click command function signature including the decorator stack
(`@click.option`, `@click.argument`, etc.) — every option/argument with its
flags, type, default, required/optional status, and help text, exactly as
declared in source. Quote the actual decorator code, not a paraphrase.

## 3. Command Body Logic
List everything the command function body does beyond a direct
pass-through to a repository `.create()` call. Specifically call out:
- Any derived/computed values (e.g., values calculated from other inputs)
- Any defaults applied in the function body (vs. defaults declared in the
  decorator)
- Any interactive prompts (`click.prompt`, `click.confirm`, custom pickers)
- Any validation/error-raising before the repo call
- Any tag normalization or transformation (short name → full name, etc.)
- Any AI provider calls
- Any multi-step writes (e.g., creates more than one record)
- Any calls to other commands/functions

## 4. Repository Method(s) Called
For each repository method invoked (e.g.
`NotesRepository.create()`, `TimeEntriesRepository.create()`):
- Full method signature (parameter names, types, defaults)
- What validation or defaults exist INSIDE the repository method itself
  (as distinct from what the CLI command already validated)
- Any constraints enforced at the DB/model level relevant to these
  parameters (e.g., NOT NULL, FK, CHECK constraints) — reference the
  relevant migration file(s) if known

---

# Additional section: Action Executor Cross-Reference

For each of the two action types, using
`workmain/orchestration/action_executor.py` (`_execute_create_note`,
`_execute_create_time_entry`):

- List every field the action_executor handler currently reads from the
  action dict
- List every parameter the repository method accepts that the
  action_executor does NOT pass (or passes a hardcoded/default value for)
- List every CLI option/argument (from section 2 above) that has NO
  corresponding field anywhere in the action_executor handler

This section should be a factual enumeration/diff — do not characterize
severity, do not propose fixes, do not recommend which gaps matter.

---

# Additional section: Schema Cross-Reference

Using `config/intent_parse_system_prompt.txt` (config_version 1.6),
for the `create_note` and `create_time_entry` action definitions:

- List every field defined in the schema for each action type
- For each schema field, confirm whether action_executor reads it
  (cross-reference with the section above)
- List any field present in the Click command (section 2) that has no
  equivalent field anywhere in the schema

Again, enumeration only — no recommendations.

---

# Format Notes

- Use the WorkmAIn document header convention (title, doc name + version,
  date) at the top of the output file.
- Quote source code verbatim in fenced code blocks with file path comments
  — do not paraphrase signatures or option lists.
- If a referenced file/method cannot be located, state that explicitly
  rather than omitting the section.
- Keep this self-contained — the reviewing session will not have live
  access to the repo, only this document.
