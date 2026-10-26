# Auto-Memory Retirement — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261026
**Branch:** `chore/issue-241-disable-auto-memory` (from `origin/main`)
**Target release:** n/a — `chore/*`
**Originating item:** Issue #241
**Design study:** `../design/DESIGN_AUTO_MEMORY_RETIREMENT.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261026 | Ray | Branch type `chore/*`, direct path. | Applied. |
| 20261026 | Ray | Design study Q1: `scripts/baseline/` gets a one-line pointer to #188 in `CLAUDE.md` § Common Pitfalls, and #188 notes that the line is removed once it is no longer needed. | Steps 2 and 6. |
| 20261026 | Spanner | The issue's third criterion sends role-specific rules to `references/<role>.md`. Those files hold only the session-open run's reads and emits; `SKILL.md` § THREE-ROLE MODEL is the only statement of what each role does (design study F4). Restated as AC3.1 with `SKILL.md` § Role N. | The issue body is edited at close-out. |
| 20261026 | Spanner | The issue's second criterion records dispositions in the results artifact. They are decided before the spec, so their one home is the design study's §3.2, and the results artifact cites it (design study F5). Restated as AC2.1. | The issue body is edited at close-out. |

## 1. Scope

**In scope:**

- A tracked `.claude/settings.json` that turns auto-memory off.
- The text each `Moved` row of the design study's §3.2 names, written at its destination: `CLAUDE.md`; `docs/DEVELOPMENT_STANDARDS.md` §1.1–§1.5, §2.4, §2.6, §2.7 and §6.2; `.claude/skills/session-start/SKILL.md`; `docs/dev/results/_TEMPLATE_RESULTS.md` §3; `docs/AI_SETTINGS_GUIDE.md`.
- One addition to #188's body (Q1).
- The design study's §6 Disposition and this spec's results artifact.

**Out of scope:**

- Deleting the memory directory. It is outside the working tree, the setting stops it loading, and Ray checks AC2.1 against it (design study §3.4).
- The three standards passages and the results template §4 deviations table that #240 names. They are #242's.
- The Outlook duplicate-series defect in the design study's §3.3. Ray decides whether it becomes an issue.
- The spec template's `<passed> passed` line, which Ray is fixing separately.

## 2. Verified current state

Direct path: each step below quotes the text it replaces or anchors on.

## 3. Design rules

- **DR1 — Exact text.** Each edit is made exactly as quoted. A quote that does not match the file stops the step (`.claude/skills/session-start/SKILL.md` § Role 3).
- **DR2 — No unwrapping beyond the edit.** `CLAUDE.md`'s opening paragraph is hard-wrapped. The new paragraph after it is one line, and the wrapped paragraph is left as it is.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Auto-memory off | `.claude/settings.json` |
| 2 | `CLAUDE.md` additions | `CLAUDE.md` |
| 3 | Standards additions | `docs/DEVELOPMENT_STANDARDS.md` |
| 4 | Role rules and rationale | `.claude/skills/session-start/SKILL.md` |
| 5 | Results template and AI settings guide | `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/AI_SETTINGS_GUIDE.md` |
| 6 | #188 notes the pointer | GitHub issue #188 body |
| 7 | Study disposition and results artifact | `docs/dev/design/DESIGN_AUTO_MEMORY_RETIREMENT.md`, `docs/dev/results/AUTO_MEMORY_RETIREMENT_RESULTS.md` |

Close-out is not in this table. It is `/closeout`.

### Step 1 — `.claude/settings.json`

Create the file with exactly this content:

```json
{
  "autoMemoryEnabled": false
}
```

### Step 2 — `CLAUDE.md`

**2a.** After the opening paragraph, which ends:

```text
read: not the artifact in chat, not a section in another section, not a design rule in a
decision log.
```

insert a blank line and this paragraph:

```markdown
A wording artifact in a document — an awkward phrase, an overloaded term — is not a finding. Fix it in one line or leave it; never report it as a defect.
```

**2b.** After the § THREE-ROLE MODEL paragraph and its rule:

```text
A session opens in its declared role with `/session-start <role>`. What each role is, does and hands to the others is `.claude/skills/session-start/SKILL.md` § THREE-ROLE MODEL, and is stated nowhere else.

---
```

insert:

```markdown

## Auto-memory

Claude Code auto-memory is off for this repository: `.claude/settings.json` sets `autoMemoryEnabled` to `false`. No instruction is carried by memory. A rule lives in this file, in `docs/DEVELOPMENT_STANDARDS.md`, or in the skill that governs its role, and a correction Ray gives in a session is made there, through a spec like any other change.

---
```

**2c.** After the last § Common Pitfalls bullet, which ends `never accept an elided "unchanged" block without checking it against the recon's own quote.`, append:

```markdown
- **A destructive write is checked before it runs.** Run `gh` from the repository root: outside a repository it fails, and an empty file passed to `gh issue edit --body-file` blanks the issue, which GitHub cannot restore. Before overwriting anything you did not author, check that the source is non-empty and holds what you expect, and read stderr in the same block. Before changing a value, read the whole file and search it for every occurrence of the value, not only the one you came for.
- **Deleting a meeting unlinks its notes.** `notes.meeting_id` is `ON DELETE SET NULL`, and the "Notes: N captured" line counts only the current occurrence. Before deleting a meeting, count its notes by query, and for a recurring meeting count the series too (`MeetingsRepository.get_series_note_count()`).
- **`scripts/baseline/` is restricted until #188 ships.** Read #188 before running, editing or citing anything under it.
```

### Step 3 — `docs/DEVELOPMENT_STANDARDS.md`

**3a. §1.1.** Replace:

```text
Run one where that is true; it produces a design artifact in `docs/dev/design/` exactly as on the full path.
```

with:

```markdown
Run one where that is true; it produces a design artifact in `docs/dev/design/` exactly as on the full path. It is required, not only permitted, wherever the work turns up options or questions whose answers change it: they are answered in the design artifact's open questions, never in the spec's Decision Log or in chat.
```

**3b. §1.2.** Replace:

```text
- Defects found during verification become their own hotfix, not sprint scope — on an open issue that already covers them where one exists, §1.3.
```

with:

```markdown
- **A finding outside the spec's scope is not fixed in it.** Whoever finds it states what an issue for it needs — the defect or gap, and its acceptance criteria — and names any open issue it could join, found by §1.3's search. Ray decides whether it becomes its own issue, joins that one, or is bundled with others.
- **An issue's acceptance criteria validate the work; they do not design it.** They are written before the design exists. Design on the merits. Where the design makes a criterion wrong, the spec restates it in its §5, says the issue body needs the edit, and the edit is made at close-out. A conflict between the design and an issue's criterion is not an open question.
- **A fix that establishes a method writes it into this document in the same spec**, with an acceptance criterion of its own, so the next author follows it. The spec measures the defect's full extent itself — every site, every condition — and never takes the issue's list as the census.
- **An expected failure a spec quotes is observed, never reasoned.** Its author runs each mutation in the working tree and quotes what happened. Each run uses a fresh `PYTHONPYCACHEPREFIX`, because restoring and re-mutating a file within one second at the same size reuses the previous mutation's `.pyc`. Each mutation's old text is a literal that occurs once in its file. The test seeds its own rows, so the mutation cannot pass on whatever the database holds.
- **A rule that refuses authored text is run over the live set it will judge before it is specified** — every open issue, every spec row, whatever the rule reads — and the result is recorded in the spec. A rule tried only on its own example can refuse correct text it was never shown.
```

**3c. §1.3.** Replace:

```text
- Work is tracked in GitHub Issues. State is GitHub's own — open or closed. There is no status vocabulary to maintain in prose, and no register or statistics table to keep in step.
```

with:

```markdown
- Work is tracked in GitHub Issues. State is GitHub's own — open or closed. There is no status vocabulary to maintain in prose, and no register or statistics table to keep in step. Work is called an issue and cited by its number; "backlog" and "item" are retired terms.
```

**3d. §1.3.** Insert after the bullet that begins `- **An issue is opened only for what no open issue already covers.**`:

```markdown
- **An issue is opened when it is on the board and its dependencies are linked.** It is added to the `WorkmAIn Queue` project at creation — `gh project item-add 3 --owner lockdwn20 --url <issue-url>` — and each issue it waits on is linked as a GitHub dependency — `gh api --method POST repos/lockdwn20/workmain/issues/<N>/dependencies/blocked_by -F issue_id=<the blocking issue's id>`. "Depends on #N" in prose is not a dependency: nothing reads it, and the board shows the issue as ready.
```

**3e. §1.4.** Replace:

```text
- **Steps.** Ordered work inside a spec. Committed individually, reviewable and revertible individually. No approval stop. A step ends with a commit, not with a request to continue.
```

with:

```markdown
- **Steps.** Ordered work inside a spec. Committed individually, reviewable and revertible individually. No approval stop. A step ends with a commit, not with a request to continue. A step that changes a signature, a required input or an invariant updates every caller in that step, so each step's commit leaves the suite green.
```

**3f. §1.5.** Insert after the bullet that begins `- **Markdown is never hard-wrapped.**`:

```markdown
- **A document never asserts a live count or holds a hand-maintained list.** A test count, queue size, version or status written as currently true is stale on the next commit, and the next reader spends a turn reconciling it. The document states the rule, and the set is derived from its live source: `pytest --collect-only -q`, `gh issue list`, `gh label list`, `workmain/__version__.py`. A dated measurement with its evidence, such as a recon's suite count at recon time, is a record and stays.
- **A document is written for a reader who has read nothing else.** An ID — a finding, a question, a design rule — is used only inside the file that defines it; anywhere else the thing is stated or cited in full. A bare `§` is a section of this document; a section of any other document is cited with that document's name. A reason is stated in terms the reader can check. An issue number may follow it as the record, but never stands in as the reason.
```

**3g. §2.4.** Insert after the bullet ``- `git commit --no-verify` is **prohibited**. It bypasses commit validation.``:

```markdown
- **Stage only the files you wrote** — `git add <path>`, never `git commit -a`. Ray edits live `config/` in the working tree mid-session, and `-a` commits his edit under your message. Check `git status --short` first; a file you did not touch stays unstaged and is mentioned.
```

**3h. §2.6.** Insert after the line ``Confirm the new `ActiveEnterTimestamp` postdates the merge commit before calling anything deployed.``:

```markdown

**The CLI does not wait for the restart.** `workmain` is an editable install from the repository, so every `workmain` command runs whatever branch is checked out, in its own process. A live check made through the CLI passes on the working branch before close-out. Only what the daemon runs — scheduled triggers and Slack Socket Mode — waits for the restart.
```

**3i. §2.7.** Replace:

```text
4. Create the branch **before** writing anything.
```

with:

```markdown
4. Create the branch **before** writing anything, from its base's `origin` ref after `git fetch` — `git checkout -b <branch> origin/main`. Pull requests merge on GitHub, so a local `main` falls behind.
```

**3j. §6.2.** Insert after rule 8, which ends `takes the routing as a required argument and makes every unstubbed provider raise.`:

```markdown
9. **A test pins behaviour meant to stay.** It never exercises a path an open issue is about to remove or narrow; it proves the same property with inputs that issue leaves valid. Opening an issue that narrows behaviour includes rewriting the open criteria and tests that exercise the narrowed path.
```

### Step 4 — `.claude/skills/session-start/SKILL.md`

**4a.** Append to the bullet `- The same arguments against the same repository and GitHub state produce the same output.`:

```markdown
 That is what the skill is for: before it, every session opened with a different set of commands and closed with a different summary.
```

**4b.** Insert after `**Model changes happen between chats, not during chats.**`:

```markdown

Each role is its own Claude Code session — never a subagent, which runs inside its parent's session, and never a second agent runtime, which chooses its model its own way. Either collapses the boundary between roles that this model exists to keep.
```

**4c.** Insert after `- Do not consider a parallel design path because it is easier than planning against the existing one.`:

```markdown

**Role 1 working rules.** These govern how Spanner settles questions. They do not apply to Role 2 or Role 3; Role 3 stops on anything the spec does not settle.

- **Apply a rule; do not ask.** Where a documented rule, or a precedent in the same document, decides a question, state the answer in one line and carry on. Options are for questions no rule decides. A recommendation that is obvious while it is being written was decided by a rule.
- **No filler options.** Drop every option the findings or a standing rule defeat. When one survives, say it is the only valid option and why.
- **Decide; do not defer.** What the issue in hand should settle is settled there — never parked as "the spec's call" or as a future issue. Dead code found in scope is removed in scope.
- **A reviewer's claim about who owns a decision is checked against this model, not adopted.** A decision is withdrawn on the merits of the finding, and the authority claim is recorded as not taken.
- **Build only what the issue asks for.** A mechanism the issue did not name goes to Ray as an open question before it is specified. Every invented surface draws review findings of its own.
- **A repeated pattern is not a precedent if an open issue calls it a defect.** Before citing what other call sites do, search the open issues for that family of defect.
- **A design holds for every provider a call type can be routed to.** Which provider serves a call is switchable configuration, often set to work around the defect in hand. Read the commit message that set a value before calling the value a finding.
- **A position Ray brings from an outside review is his decision** once he confirms it, and is recorded as his, never cited to the review. Its claims are verified against code first.
```

**4d.** Replace:

```text
Findings go BACK to Role 1, never forward. You do not implement.
```

with:

```markdown
Findings go BACK to Role 1, never forward. You do not implement.

A case no standard yet covers is not a finding. It is a one-line amendment with suggested wording, listed apart from the findings, for Role 1 to write into the standards; the spec is not held against the old text.
```

### Step 5 — results template and AI settings guide

**5a. `docs/dev/results/_TEMPLATE_RESULTS.md`.** Insert after the row ``| AC1.1 | Met / **Not met** / Carried | `pytest ...` output, file:line, or command result |``:

```markdown

This section holds only the AC table. Close-out reads every three-column table under `## 3.` as AC rows (`automation/closeout_acs.py`), so a supporting table goes under `## 5. Verification` and the AC row cites it.
```

**5b. `docs/AI_SETTINGS_GUIDE.md`.** Insert before `### Claude-Specific Fields`:

```markdown
**Cost values are Ray's.** `cost_structure` and every `cost_per_1k_*` field are set by Ray whenever a model changes. A spec that changes a model states the expected values, citing the vendor's live pricing page and the date it was read, never a cached table, and leaves the edit to him.

```

### Step 6 — #188

From the repository root, read #188's body to a scratchpad file and check it is non-empty. Make the two edits below, check that each anchor matched exactly once, and write the body back with `gh issue edit 188 --body-file`. Then read it back.

- After the line ``- Run data under `staging/baseline/` (gitignored, local to Ray's machine) may be used and cited.``, insert ``- `CLAUDE.md` § Common Pitfalls carries one line sending a session here before anything under `scripts/baseline/` is run, edited or cited. This issue removes that line once the restrictions are lifted.``
- After the last AC, `- Full suite passes with no net test loss from the current baseline.`, append:

```markdown
- `CLAUDE.md` no longer sends sessions to this issue
  - Checked by: grep -n '#188' CLAUDE.md returns nothing
```

No commit; the deliverable is on GitHub.

### Step 7 — study disposition and results artifact

In the design study, replace `- Promoted to: *(the spec, once written)*` with ``- Promoted to: `../specs/AUTO_MEMORY_RETIREMENT_SPEC.md` ``. Write `docs/dev/results/AUTO_MEMORY_RETIREMENT_RESULTS.md` from the template, with one §3 row per AC below.

### Authorization points

None in these steps. The one authorization point on this path, the merge to `main`, belongs to `/closeout`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Auto-memory is turned off by a tracked project setting, so it holds in every session opened on this repository. | `git ls-files .claude/settings.json` prints the path, and `python3 -c "import json; print(json.load(open('.claude/settings.json'))['autoMemoryEnabled'])"` prints `False` |
| AC2.1 | Every file in the memory directory as it stood on 20261026 has a disposition — moved, with destination, or dropped, with reason — in the design study's §3.2. | Stated reading by Ray of the design study's §3.2 against the memory directory |
| AC2.2 | Each `Moved` row's rule is stated at its destination, and nowhere else. | Stated reading by Ray of each destination §3.2 names, against Steps 2–5 |
| AC2.3 | #188 records that it removes the `CLAUDE.md` pointer. | `gh issue view 188 --json body --jq .body \| grep -c 'removes that line'` prints `1` |
| AC3.1 | No role-specific rule moved out of memory lands in `CLAUDE.md`; each lands in `.claude/skills/session-start/SKILL.md` § Role N for the role it governs. | Stated reading by Ray of Step 2's additions and `SKILL.md` § Role 1 and § Role 2 |
| AC4.1 | `CLAUDE.md` states that auto-memory is off for this repository and that no instruction is carried by memory. | `grep -n autoMemoryEnabled CLAUDE.md` returns one line, in § Auto-memory |
| AC5.1 | A session opened after the change loads no auto-memory. | Ray runs `/memory` in a fresh session on this branch and reports auto-memory shown as off |

## 6. Test plan

Omitted: no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes.

## 7. Risks and rollback

- **Auto-memory stays on.** The project setting overrides the user setting for this repository, per the Claude Code docs (design study F1); AC5.1 observes it. Rollback: `git revert` the Step 1 commit.
- **A moved rule contradicts its new neighbours.** Each insertion was read against the section it joins. Rollback: revert that step's commit.
- **#188's body is damaged.** Step 6 checks the body is non-empty and that each anchor matched once, and reads it back. Recovery is the scratchpad copy read at the start of the step.
