# Anvil session open

**Role:** `SKILL.md` § Role 3. **Target:** a spec path, required.

## Reads, in order

1. The spec at the target path, end to end.
2. The spec's `**Status:**` field.
3. `git status --porcelain`
4. `git branch --show-current`, against the spec's `**Branch:**` field.
5. Every reference the spec makes, at the cited location. A reference resolves when the location holds what the spec says it holds:
   - **Path** — exists on the current branch.
   - **Symbol** — defined in the file the spec names, as a `def`, a `class` or an assignment, with the signature the spec gives where it gives one.
   - **Line or line range** — holds the text or symbol the spec says it holds.
   - **Quoted text a step replaces or edits** — occurs verbatim in the file named, as many times as the step says, and once where it does not say.
   - **Section** — the file named has the heading, and the section says what the spec says it says.
   - **Reference to another part of the spec** — a step's citation of another section of the same spec, or of an item that section gives an ID: the section exists, and each item cited is there and is what the step says it is.
   - **Claim about existing behaviour** — a §2 row, or a statement of what code does: the evidence it cites is read and shows the claim.
   - **Test node** — `pytest --collect-only -q <node>` collects it.
   - **Issue** — `gh issue view <N>` returns it, in the state the spec gives where it gives one.
   - **Command** — run only if it only reads, such as `grep`, `git grep`, `git show` or `gh issue view`, and resolved when it exits 0, or 1 from `grep` or `git grep`, which means no match. Any other exit status is a discrepancy. Its output is compared with the spec only where the spec says what it prints before the work; output a criterion states for after the work is not checked at open. Any other command is not run: each path, symbol and test node it names is resolved under this list.

   A path, symbol or test node that a step creates resolves against that step's deliverable instead, and is a discrepancy if it already exists.
6. `docs/standards/README.md`, `docs/standards/1-workflow.md`, `docs/standards/2-git.md` and `docs/standards/6-testing.md`, end to end.

## Emits

- **Steps** — the spec's §4 step table, as written.
- **Discrepancies** — each of these that holds, or `none`:
  - `Status:` is not `Approved`
  - the working tree is not clean, with each path `git status --porcelain` lists
  - the current branch is not the spec's `**Branch:**`
  - a reference that does not resolve, or resolves to something other than what the spec says is there
  - an item with a name of its own given an ID anywhere in the spec, such as a test named other than by its node ID (`docs/standards/1-workflow.md` §1.2)

Every read runs and every discrepancy is reported; the run does not stop at the first. What happens next — waiting for Ray's go-ahead, and what it authorizes — is `SKILL.md` § Role 3.

## Working rules

These hold for the whole Anvil session. The run neither reads nor emits them, and no other role's session loads them.

- **Each step runs in this order.** A difference any check finds is a departure, and stops the step under `SKILL.md` § Role 3.
  1. Before the step's first change, re-read the step's row and text in the spec, and every design rule and acceptance criterion that governs it.
  2. Make the change.
  3. Stage only the files written for the step (`docs/standards/2-git.md` §2.4), and compare `git diff --cached --name-only` with the step's entry in the Files column. A staged file the entry does not name, or a named file that is not staged, is a difference.
  4. Read `git diff --cached` against the step's text. A change the text does not cover, or anything the text says that the diff does not deliver, is a difference.
  5. Commit only when checks 3 and 4 find no difference.
