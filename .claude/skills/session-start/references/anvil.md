# Anvil session open

**Role:** `SKILL.md` § Role 3. **Target:** a spec path, required.

## Reads, in order

1. The spec at the target path, end to end.
2. The spec's `**Status:**` field.
3. `git status --porcelain`
4. `git branch --show-current`, against the spec's `**Branch:**` field.
5. Every reference the spec makes — file, symbol, line, section or command — at the cited location.

## Emits

- **Steps** — the spec's §4 step table, as written.
- **Discrepancies** — each of these that holds, or `none`:
  - `Status:` is not `Approved`
  - the working tree is not clean, with each path `git status --porcelain` lists
  - the current branch is not the spec's `**Branch:**`
  - a reference that does not resolve, or resolves to something other than what the spec says is there

Every read runs and every discrepancy is reported; the run does not stop at the first. What happens next is `SKILL.md` § Role 3.
