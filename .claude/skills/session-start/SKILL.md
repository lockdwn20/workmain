---
name: session-start
description: Open a session in a declared role — Spanner, Caliper or Anvil — by reading a fixed set of sources in a fixed order and emitting the state that role needs before it acts. Read-only.
argument-hint: <Spanner|Caliper|Anvil> [issue-number | spec-path]
arguments: [role, target]
disable-model-invocation: true
user-invocable: true
---

# `/session-start`

User-initiated only. Invoked with role `$role` and target `$target`.

This skill **reads**. It writes no file, creates no branch or commit, and makes no GitHub change. It assembles the state a role needs before it acts, from the sources that role's reference names, in the order named. What each role is and does is `CLAUDE.md` § THREE-ROLE MODEL; this skill restates none of it.

## Step 0 — refuse before reading

Run this before any tool call. A declared argument that was not supplied expands to an empty string rather than failing, so nothing upstream of this step catches a missing role.

Stop, print the line below, and read nothing when any of these holds:

- the role is empty, or is not exactly `Spanner`, `Caliper` or `Anvil`
- the role is `Caliper` or `Anvil` and the target is empty
- the role is `Spanner` and the target is present but is not an issue number

`Usage: /session-start <Spanner|Caliper|Anvil> [target] — Spanner takes an optional issue number; Caliper and Anvil require a spec path.`

## Rules every run holds

- Read only the sources the role's reference names, in the order it names them. A source that cannot be read is reported as unreadable with its error; nothing is reconstructed in its place.
- Emit only what those sources carry, in the shape the reference states. No commentary, no recommendation the reference does not name, no closing summary.
- Every rule, role definition and command another document owns is cited by its section of `CLAUDE.md` or `docs/DEVELOPMENT_STANDARDS.md`, never copied.
- The same arguments against the same repository and GitHub state produce the same output.

## Choosing the reference

Reached only when Step 0 passed. Load exactly one:

- `Spanner` → `references/spanner.md`
- `Caliper` → `references/caliper.md`
- `Anvil` → `references/anvil.md`

## Anything not covered here

Stop and surface to Ray.
