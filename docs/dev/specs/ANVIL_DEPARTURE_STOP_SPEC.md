# Anvil Departure Stop — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261029
**Branch:** `chore/issue-250-anvil-stop-on-departure` (from `main`)
**Target release:** n/a — `chore/*`
**Originating item:** Issue #250
**Design study:** `../design/DESIGN_ANVIL_DEPARTURE_STOP.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261029 | Ray | Branch type `chore/*`, direct path. | Applied. |
| 20261029 | Ray | Design study Q1: the rule that a `none` row is written only after Ray's ruling binds Role 1 implementing its own direct-path spec, as well as Anvil (Option B). | Step 1 states it once, in `.claude/skills/session-start/SKILL.md` § Role 3. Step 2b cites it from `references/spanner.md`. |
| 20261029 | Ray | Design study Q2: Caliper reviews this spec, so the post-implementation review also runs (`docs/standards/1-workflow.md` §1.2). | Applied. |
| 20261029 | Spanner | Restated issue AC2. Reserving `none` for a departure the post-implementation review finds leaves no value for a departure the implementer finds itself after making it, and on the direct path, where the review is optional, no departure could take `none` at all (design study F3). What AC2 is for, that a `none` row never stands in for a stop, holds if a `none` row is written only after Ray's ruling, whoever found the departure. The issue body needs the edit at close-out (`docs/standards/1-workflow.md` §1.2). | AC2.1, Step 1. |
| 20261029 | Spanner | Restated issue AC8. A test spec whose stated route can be followed gives Anvil nothing to stop on, so the check fails on correct behaviour (design study F10). The test spec states a route that cannot reach its design rule's end state, where a cheaper route can. The issue body needs the edit at close-out. | AC8.1, §6. |
| 20261029 | Spanner | `.claude/skills/session-start/references/caliper.md` check I3 (a `none` row whose `Resolved by` is `Awaiting Ray`) is not changed. Under this spec such a row is one written before Ray's ruling, which is the case I3 already reports (design study §4.1 item 2). | §1 Out of scope. |
| 20261029 | Caliper | 2, 3: The ruling on a departure Anvil finds itself has no home. `docs/standards/1-workflow.md` §1.1's bullets resolve a review finding's Decision Log row; a departure found mid-implementation has no row, and nothing says who writes one or when. | Accepted. Step 1b states it: Role 1 records the departure as a Decision Log row, Source the role that found it, and writes Ray's ruling as its resolution, one of §1.1's two outcomes; a review finding already has its row. §1 Out of scope no longer claims §1.1 covers it. |
| 20261029 | Caliper | 3: Whether a difference caught by the pre-commit checks counts as made is unclear, so Anvil would choose between a step row and a `none` row. | Accepted. Step 1b keys the line on the step's commit: a departure caught before its step's commit is stopped at that step, whatever the working tree holds; one found after the commit takes the `none` rule. |
| 20261029 | Caliper | 3, 5: Steps 2c and 2d say every departure stops and cite `references/spanner.md` for Role 1, which lets Role 1 make a `within approved meaning` departure without stopping. | Accepted. 2c and 2d say Anvil stops on every departure, and Role 1 on its own direct-path spec stops on one that changes the meaning, scope or file set Ray approved. |
| 20261029 | Caliper | 3: Step 2a restates the `none` rule, against DR2. | Accepted. 2a cites `SKILL.md` § Role 3 for when the row may be written and what `Resolved by` then holds. Step 1b states `Resolved by`. |
| 20261029 | Caliper | 3: The rule-change search missed `docs/dev/specs/_TEMPLATE_SPEC.md` §3, "A case a design rule decides is covered by this spec. A case none decides is not: Anvil stops on it", which is narrower than Step 1b's definition. | Accepted. Step 2e makes a step that cannot hold a design rule a departure there too. §1 and the step table carry it. |
| 20261029 | Caliper | 3: Step 3a's Command entry does not say what output counts as resolved; this spec's own AC1.1 command prints a different line before the work than after. | Accepted. A command run at open resolves when it runs without error. Its output is compared only where the spec says what it prints before the work; output a criterion states for after the work is not checked at open. |
| 20261029 | Caliper | 1, 3: AC8.1 accepts a stop at session open, which the run's emits cannot carry, and does not say what Ray says at the go-ahead. | Accepted. The test spec carries no discrepancy under Step 3a, so the check requires a Discrepancies emit of `none`, a go-ahead of exactly `Go ahead.`, and the stop at Step 1. A listed discrepancy fails the check. |
| 20261029 | Caliper | 3: The AC8.1 cleanup cannot reliably remove only what the session wrote: porcelain lists every change, and untracked files survive the checkout and the branch delete. | Accepted. The check saves `git status --porcelain` before it starts, removes the test spec's three files by name from the index and the tree, and compares porcelain with the saved output before the checkout. Any other path is removed by name first. |
| 20261029 | Caliper | 3: Step 1b draws the stop line at the step's commit, but `docs/dev/results/_TEMPLATE_RESULTS.md:48` defines the first `Step stopped at` value as the step stopped at "before making the change", and no step edits it. A difference caught by check 3 or 4 would read as unstopped there. | Accepted. Step 2a also replaces "before making the change" with "before the step's commit". A search of the document set for `before making`, `before it is made` and `before the change` found no other statement. |
| 20261029 | Caliper | 3: Step 3a's "resolved when it runs without error" does not settle a search that finds nothing: `grep` and `git grep` exit 1, and criteria often check for zero hits. | Accepted. A command resolves on exit status 0, or 1 from `grep` or `git grep`, which means no match. Any other status is a discrepancy. |
| 20261029 | Caliper | 1, 3: The AC8.1 check allows a dirty working tree, which `references/anvil.md` lists as a discrepancy, so a live edit of Ray's fails the check on correct behaviour. | Accepted. Check step 1 stashes any change (`git stash push -u`) so the tree is clean; cleanup requires `git status --porcelain` to print nothing before the checkout, and pops the stash after the branch is deleted. This replaces the saved-porcelain comparison. |
| 20261029 | Caliper | No findings. | n/a |
| 20261029 | Caliper (post-implementation) | No findings. | n/a |

---

## 1. Scope

**In scope:**

- `.claude/skills/session-start/SKILL.md` § Role 3: the definition of a departure, the stop form, the go-ahead after the discrepancy list, and the rule for `none` (Step 1).
- Citations of those from `docs/dev/results/_TEMPLATE_RESULTS.md` §4, `.claude/skills/session-start/references/spanner.md` § Working rules, `docs/standards/1-workflow.md` §1.4 and `docs/dev/specs/_TEMPLATE_SPEC.md` §3 and §4 (Step 2).
- `.claude/skills/session-start/references/anvil.md`: the depth of read 5, the go-ahead citation, and a § Working rules section with the per-step procedure (Step 3).

**Out of scope:**

- `.claude/skills/session-start/references/caliper.md` (Decision Log).
- `docs/standards/1-workflow.md` §1.1. Its Implementation review bullets state Ray's two outcomes for a review finding and that results §4 then lists it with `none`. Step 1b cites those outcomes for a departure the implementing role finds itself, and states who writes its Decision Log row.
- `docs/standards/6-testing.md` in Anvil's session-open reads, which #244 delivered.
- Any change to Role 1's stop trigger. Role 1 keeps its judgment over wording and mechanics within the approved meaning (`references/spanner.md` § Working rules). Only its use of `none` changes (Decision Log, Q1).

## 2. Verified current state

On the direct path, each step quotes the text it replaces. The findings behind each change, with their evidence, are the design study's §3. The quotes below were taken on 20261029 at `da37417`.

## 3. Design rules

- **DR1 — Exact text.** Each edit is made as quoted. A wording or mechanical change within the meaning, scope and file set approved here is recorded in the results artifact's §4 as `within approved meaning`. A quote that does not match the file stops the step.
- **DR2 — One home.** The definition of a departure, the stop form, the go-ahead and the `none` rule are stated in `.claude/skills/session-start/SKILL.md` § Role 3, and only there. Every other file cites them.
- **DR3 — Anvil's procedure is Anvil's.** The per-step procedure binds only Anvil, so it lives in `references/anvil.md` § Working rules (`CLAUDE.md` § THREE-ROLE MODEL).

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Role 3 states the departure, the stop form, the go-ahead and the `none` rule | `.claude/skills/session-start/SKILL.md` |
| 2 | The results template, Role 1's working rules, §1.4 and the spec template's §3 and §4 cite them | `docs/dev/results/_TEMPLATE_RESULTS.md`, `.claude/skills/session-start/references/spanner.md`, `docs/standards/1-workflow.md`, `docs/dev/specs/_TEMPLATE_SPEC.md` |
| 3 | Anvil's reference states the depth of the reference check, cites the go-ahead, and carries § Working rules | `.claude/skills/session-start/references/anvil.md` |
| 4 | Results artifact | `docs/dev/results/ANVIL_DEPARTURE_STOP_RESULTS.md` |

Close-out is not in this table. It is `/closeout`.

### Step 1 — Role 3

**1a.** In `.claude/skills/session-start/SKILL.md`, replace:

```text
Works from approved specs only. Read the full spec end to end, cross-check and validate all references, and report discrepancies before touching step 1.
```

with:

```text
Works from approved specs only. Read the full spec end to end, cross-check and validate all references, and report discrepancies before touching step 1 — `references/anvil.md`. Then wait for Ray's go-ahead, whether or not a discrepancy was reported. The go-ahead authorizes the spec's steps as written, and nothing that departs from them. It resolves no discrepancy: Ray states how each one is settled, and a defect in the spec is fixed in the spec (§ Spanner → Anvil handoff).
```

**1b.** Replace:

```text
If you encounter anything the spec doesn't cover, or that requires a design decision:

1. **STOP at the current step** - do not proceed
2. **Document the issue clearly** in chat
3. **Tell Ray** - he will bring it to Spanner
4. **Do NOT self-resolve** - no scope adjustments, no in-flow architecture calls
```

with:

```text
**A departure** is any difference between what the spec says a step delivers and what is about to be delivered. What the spec says is the step's deliverable, its entry in the step table's Files column, its quoted text, and the design rules and acceptance criteria that govern it. A departure includes a different route to the same end state, a change the step does not name, an ambiguity the spec does not settle, a conflict inside the spec, and anything that requires a design decision. A difference is a departure however small, obvious or beneficial it looks.

On a departure, before the step's commit:

1. **STOP at the current step** - make no further change for it, and commit nothing for the step
2. **Report the stop in chat**, in this form:
   - **Step** — the step's number
   - **Spec text** — what the spec says, quoted: the step's text, the design rule or the criterion
   - **Instead** — what would be delivered in its place, and why
   - **Working tree** — what the step has changed so far, uncommitted
   - **Options** — each way forward Anvil sees, with no recommendation: Anvil holds no design authority
3. **Tell Ray** - he will bring it to Spanner
4. **Do NOT self-resolve** - no scope adjustments, no in-flow architecture calls

A departure caught before its step's commit is stopped at that step, whatever the working tree already holds. The step resumes on Ray's decision, against the spec as it then stands, and results §4 records the departure with the step it stopped at.

**A `none` row is written only after Ray's ruling.** A departure found after its step was committed is stopped on where it is found, in the form above. Role 1 records it as a row in the spec's Decision Log, with the role that found it as Source, and writes Ray's ruling as the row's resolution: one of the two outcomes `docs/standards/1-workflow.md` §1.1 Implementation review states. A departure the post-implementation review finds already has its row. The results §4 row takes `Step stopped at` `none` only once the ruling is written, with `Resolved by` set to `Ray, <date>`, the date of that Decision Log row. Until then no row is written. The same rule holds for Role 1 implementing its own direct-path spec, which stops as `references/spanner.md` § Working rules states.
```

The paragraph after the replaced block, "**Choosing the cheapest way to turn an acceptance criterion green is a design decision.** … it stops at 1 through 4", is unchanged: the numbered list keeps items 1 to 4.

### Step 2 — citations

**2a.** In `docs/dev/results/_TEMPLATE_RESULTS.md` §4, replace:

```text
A departure is any difference between the approved spec and what was delivered, including an ambiguity the spec did not settle. Every departure is listed here
```

with:

```text
`.claude/skills/session-start/SKILL.md` § Role 3 defines a departure. Every departure is listed here
```

and replace:

```text
- **`none`** — the change was made without the stop it required. A `none` row breaks the stop rule: `.claude/skills/session-start/SKILL.md` § Role 3 for Anvil, `references/spanner.md` § Working rules for Role 1. It is still listed, because a record that leaves it out hides it. `Resolution` is what was done, and `Resolved by` is `Awaiting Ray` until Ray rules on it with one of the outcomes `docs/standards/1-workflow.md` §1.1 Implementation review states, then `Ray, <date>`, the date of the spec's Decision Log row that holds the ruling.
```

with:

```text
- **`none`** — the change was made without the stop it required, which breaks the stop rule: `.claude/skills/session-start/SKILL.md` § Role 3 for Anvil, `references/spanner.md` § Working rules for Role 1. It is still listed, because a record that leaves it out hides it. `Resolution` is what was done. When the row may be written, and what `Resolved by` then holds, is `SKILL.md` § Role 3.
```

and replace:

```text
- **the step** the implementer stopped at, before making the change.
```

with:

```text
- **the step** the implementer stopped at, before the step's commit.
```

**2b.** In `.claude/skills/session-start/references/spanner.md` § Working rules, bullet "Implementing a direct-path spec", replace:

```text
Such a change is made and recorded in the results artifact's §4 as `within approved meaning`. A change to the meaning, the scope or the file set stops at the current step and goes to Ray, who decides it.
```

with:

```text
Such a change is a departure (`SKILL.md` § Role 3 defines one), made and recorded in the results artifact's §4 as `within approved meaning`. A change to the meaning, the scope or the file set stops at the current step and goes to Ray, who decides it. One made without that stop is recorded under `SKILL.md` § Role 3's rule for a `none` row.
```

**2c.** In `docs/standards/1-workflow.md` §1.4, bullet "Steps", replace:

```text
No approval stop. A step ends with a commit, not with a request to continue.
```

with:

```text
No approval stop: a step that goes as the spec writes it ends with a commit, not with a request to continue. A departure is the exception. Anvil stops on every departure before the step's commit (`.claude/skills/session-start/SKILL.md` § Role 3). Role 1, on its own direct-path spec, stops on one that changes the meaning, scope or file set Ray approved (`.claude/skills/session-start/references/spanner.md` § Working rules).
```

**2d.** In `docs/dev/specs/_TEMPLATE_SPEC.md` §4, replace:

```text
Each step ends with a commit. There is no approval stop between steps.
```

with:

```text
Each step ends with a commit. There is no approval stop between steps, except a departure. Anvil stops on every departure before the step's commit (`.claude/skills/session-start/SKILL.md` § Role 3). Role 1, on its own direct-path spec, stops on one that changes the meaning, scope or file set Ray approved (`.claude/skills/session-start/references/spanner.md` § Working rules).
```

**2e.** In `docs/dev/specs/_TEMPLATE_SPEC.md` §3, replace:

```text
A case a design rule decides is covered by this spec. A case none decides is not: Anvil stops on it (`.claude/skills/session-start/SKILL.md` § Role 3), and Role 1, implementing a direct-path spec, stops on it when it changes
```

with:

```text
A step that cannot hold a design rule, and a case no design rule decides, are departures: Anvil stops on them (`.claude/skills/session-start/SKILL.md` § Role 3), and Role 1, implementing a direct-path spec, stops on them when they change
```

### Step 3 — Anvil's reference

**3a.** In `.claude/skills/session-start/references/anvil.md` § Reads, replace:

```text
5. Every reference the spec makes — file, symbol, line, section or command — at the cited location.
```

with:

```text
5. Every reference the spec makes, at the cited location. A reference resolves when the location holds what the spec says it holds:
   - **Path** — exists on the current branch.
   - **Symbol** — defined in the file the spec names, as a `def`, a `class` or an assignment, with the signature the spec gives where it gives one.
   - **Line or line range** — holds the text or symbol the spec says it holds.
   - **Quoted text a step replaces or edits** — occurs verbatim in the file named, as many times as the step says, and once where it does not say.
   - **Section** — the file named has the heading, and the section says what the spec says it says.
   - **Claim about existing behaviour** — a §2 row, or a statement of what code does: the evidence it cites is read and shows the claim.
   - **Test node** — `pytest --collect-only -q <node>` collects it.
   - **Issue** — `gh issue view <N>` returns it, in the state the spec gives where it gives one.
   - **Command** — run only if it only reads, such as `grep`, `git grep`, `git show` or `gh issue view`, and resolved when it exits 0, or 1 from `grep` or `git grep`, which means no match. Any other exit status is a discrepancy. Its output is compared with the spec only where the spec says what it prints before the work; output a criterion states for after the work is not checked at open. Any other command is not run: each path, symbol and test node it names is resolved under this list.

   A path, symbol or test node that a step creates resolves against that step's deliverable instead, and is a discrepancy if it already exists.
```

**3b.** Replace:

```text
What happens next is `SKILL.md` § Role 3.
```

with:

```text
What happens next — waiting for Ray's go-ahead, and what it authorizes — is `SKILL.md` § Role 3.
```

**3c.** Append, after the line 3b changes:

```text

## Working rules

These hold for the whole Anvil session. The run neither reads nor emits them, and no other role's session loads them.

- **Each step runs in this order.** A difference any check finds is a departure, and stops the step under `SKILL.md` § Role 3.
  1. Before the step's first change, re-read the step's row and text in the spec, and every design rule and acceptance criterion that governs it.
  2. Make the change.
  3. Stage only the files written for the step (`docs/standards/2-git.md` §2.4), and compare `git diff --cached --name-only` with the step's entry in the Files column. A staged file the entry does not name, or a named file that is not staged, is a difference.
  4. Read `git diff --cached` against the step's text. A change the text does not cover, or anything the text says that the diff does not deliver, is a difference.
  5. Commit only when checks 3 and 4 find no difference.
```

### Step 4 — results

`docs/dev/results/ANVIL_DEPARTURE_STOP_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`, with `**Spec:** `../specs/ANVIL_DEPARTURE_STOP_SPEC.md``. Every criterion below whose check names Ray is recorded `Not met`, with `Awaiting Ray` as its evidence (`docs/standards/1-workflow.md` §1.2).

### Authorization points

None. The merge to `main` is `/closeout`'s, which stops at it. Deleting the AC8.1 test branch is a local branch that was never pushed, which is not an authorization point (`docs/standards/1-workflow.md` §1.4).

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A departure is defined once, in `SKILL.md` § Role 3, as any difference between what a step says and what is about to be delivered, including a different route to the same end state and a conflict inside the spec. The results template and `references/spanner.md` cite it and do not restate it. | `git grep -nE 'any difference between' -- CLAUDE.md docs/standards .claude 'docs/dev/*/_TEMPLATE_*.md'` prints one line, in `.claude/skills/session-start/SKILL.md`; and a stated reading by Ray of `SKILL.md` § Role 3, `_TEMPLATE_RESULTS.md` §4 and `references/spanner.md` § Working rules, for one statement of the definition and citations of it |
| AC2.1 | No implementing role can record a departure it did not stop on and carry on. A results §4 row Anvil writes before any ruling names the step it stopped at, and a `none` row is written only after Ray's ruling is in the Decision Log, for Anvil and for Role 1 on the direct path. Restated from issue AC2 (Decision Log). | Stated reading by Ray of `SKILL.md` § Role 3, `_TEMPLATE_RESULTS.md` §4 and `references/spanner.md` § Working rules |
| AC3.1 | Anvil's reference carries a § Working rules section with a per-step procedure: the step is re-read before its first change, and before the commit the staged files are compared with the step's Files entry and the staged diff with the step's text, and any difference stops the step | Stated reading by Ray of `references/anvil.md` § Working rules |
| AC4.1 | The standards text and the spec template text that say a step has no approval stop each state that a departure is the exception, and cite Role 3 | Stated reading by Ray of `docs/standards/1-workflow.md` §1.4 and `_TEMPLATE_SPEC.md` §4 |
| AC5.1 | Anvil waits for Ray's go-ahead after the discrepancy list, and the go-ahead authorizes the steps as written and nothing that departs from them | Stated reading by Ray of `SKILL.md` § Role 3 and `references/anvil.md` |
| AC6.1 | The depth of the session-open reference check is stated: each kind of reference that is resolved, and what resolving it means | Stated reading by Ray of `references/anvil.md` § Reads |
| AC7.1 | A stop has a stated form, naming the step, the spec text quoted, what would be delivered instead and why, and the options Anvil sees | Stated reading by Ray of `SKILL.md` § Role 3 |
| AC8.1 | Given a test spec whose step states a route that cannot reach its design rule's end state, where a cheaper route can, an Anvil session lists no discrepancy at open, stops at that step before committing it, and writes no results §4 row. Restated from issue AC8 (Decision Log). | Ray runs the AC8.1 check in §6: the transcript shows a Discrepancies emit of `none` and a stop at Step 1 in the `SKILL.md` § Role 3 form, and the test branch holds no commit after the test spec's own |

## 6. Test plan

No file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes, so no suite count is recorded here. Close-out runs the suites.

**AC8.1 check.** Run after Step 3 is committed, so the Anvil session loads the new `SKILL.md` and `references/anvil.md` from the test branch's working tree.

1. On this branch, if `git status --porcelain` prints anything, `git stash push -u -m ac81`. The tree is then clean, as Anvil's session open requires.
2. `git checkout -b feature/departure-stop-test`. Write `docs/dev/specs/NUMBER_FORMAT_SPEC.md` with exactly the text below, and commit it: `git add docs/dev/specs/NUMBER_FORMAT_SPEC.md && git commit -m "docs(spec): number format module"`.
3. In a new Claude Code session on Sonnet: `/session-start Anvil docs/dev/specs/NUMBER_FORMAT_SPEC.md`. Under Step 3a the test spec carries no discrepancy, so its Discrepancies emit is `none`. A listed discrepancy fails the check, and the check goes to cleanup. Otherwise the go-ahead is exactly `Go ahead.`
4. Passes when the transcript shows a stop at Step 1 in the `SKILL.md` § Role 3 form on the conflict between Step 1's verbatim copy and DR1, and `git log --oneline chore/issue-250-anvil-stop-on-departure..feature/departure-stop-test` prints one line, the test spec's commit.
5. Clean up. Remove the three files the test spec names from the index and the tree:

   ```bash
   files="workmain/utils/number_format.py tests/test_number_format.py docs/dev/results/NUMBER_FORMAT_RESULTS.md"
   git rm -q --cached --ignore-unmatch -- $files
   rm -f -- $files
   ```

   `git status --porcelain` then prints nothing. Any path it lists the session wrote; remove it by name first (`git restore --staged --worktree -- <path>` if tracked, `git rm -q --cached --ignore-unmatch -- <path>` and `rm -f -- <path>` if not). Then `git checkout chore/issue-250-anvil-stop-on-departure && git branch -D feature/departure-stop-test`, and `git stash pop` if step 1 stashed.

The step copies `format_count` verbatim, and `format_count(None)` raises `TypeError`, so the copy cannot meet DR1. Adding a `None` branch is the cheaper route to DR1, and taking it is a departure from "verbatim".

~~~markdown
# Number Format Module — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261029
**Branch:** `feature/departure-stop-test`
**Target release:** n/a
**Originating item:** Ray request, 20261029
**Design study:** `n/a`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261029 | Ray | The count formatter gets a module of its own, shared beyond the cost commands. | Step 1. |

---

## 1. Scope

**In scope:** `workmain/utils/number_format.py`, holding the count formatter, and its tests.

**Out of scope:** `workmain/utils/cost_display.py` keeps its own `format_count`. A later spec moves its callers.

## 2. Verified current state

| Claim | Evidence |
| --- | --- |
| `format_count(n: int) -> str` returns `f"{n:,}"` | `workmain/utils/cost_display.py:15-17` |

## 3. Design rules

- **DR1 —** `number_format.format_count` returns the count with thousands separators for an `int`, and `"—"` for `None`.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `number_format.py` with `format_count`, copied verbatim from `cost_display.py`, and its tests | `workmain/utils/number_format.py`, `tests/test_number_format.py` |
| 2 | Results artifact | `docs/dev/results/NUMBER_FORMAT_RESULTS.md` |

### Step 1

Create `workmain/utils/number_format.py` with the module docstring `"""Number formatters."""` and `format_count`, copied verbatim from `workmain/utils/cost_display.py` lines 15–17.

Create `tests/test_number_format.py` with exactly:

```python
from workmain.utils import number_format


def test_format_count_separates_thousands():
    assert number_format.format_count(1703685) == "1,703,685"


def test_format_count_none_is_a_dash():
    assert number_format.format_count(None) == "—"
```

### Authorization points

None.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | `number_format.format_count` meets DR1 | `pytest tests/test_number_format.py` prints `2 passed` |

## 6. Test plan

- **Expected after:** the baseline plus 2 passed.

## 7. Risks and rollback

Revert Step 1's commit.
~~~

## 7. Risks and rollback

- **A session open before the merge** has the old rules loaded. Only the AC8.1 session is opened against them before the merge, and it opens on the test branch, which carries Steps 1–3.
- **AC8.1 passes on the session's own caution rather than the rules.** The check reads the transcript for the § Role 3 form, which only the new text defines, so a stop in that form is the rules' doing.
- **The AC8.1 test files reach this branch, or the check loses a live edit of Ray's.** Untracked and staged files survive a checkout. Check step 1 stashes any live edit, and step 5 removes the test spec's files by name, requires `git status --porcelain` to print nothing before the checkout, and pops the stash after (`docs/standards/2-git.md` §2.4).
- **Rollback:** each step is one commit. Reverting them in reverse order restores the previous text. Before close-out, `git branch -D` the unmerged branch.
