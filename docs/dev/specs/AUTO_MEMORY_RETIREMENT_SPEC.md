# Auto-Memory Retirement — Spec

**Status:** Approved
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
| 20261026 | Ray | Design study Q1: `scripts/baseline/` gets a one-line pointer to #188 in `CLAUDE.md` § Common Pitfalls, and #188 notes that the line is removed once it is no longer needed. | Steps 2c and 6. |
| 20261026 | Spanner | The issue's second criterion records dispositions in the results artifact. They are decided before the spec, so their one home is the design study's §3.2, and the results artifact cites it (design study F5). Restated as AC2.1. | The issue body is edited at close-out. |
| 20261026 | Ray | **The Role 1 working rules land where every role loads them.** Step 4c puts eight Spanner rules, including "Apply a rule; do not ask" and "Decide; do not defer", into `.claude/skills/session-start/SKILL.md` § Role 1. That file carries all three roles and is loaded by Anvil and Caliper. The rules stay in Anvil's context, separated from it only by "They do not apply to Role 2 or Role 3". That is the same mechanism #240 records as a contributor: directives for one role sitting in another role's context. The carve-out was already tried in memory. `feedback_anvil_stop_on_any_gap.md` states "The Spanner-side rules ([[feedback-decide-dont-defer]], [[feedback-apply-rules-dont-ask]]) do not apply to Anvil." Design study F4 is right that `references/<role>.md` today holds only session-open reads and emits. But the issue's criterion asks for a home only that role loads, not for the current shape of those files. Required: a location read only by a Spanner session (for example an expanded `references/spanner.md`, or a Spanner-only rules file the Spanner session-open reads). AC3.1 is restated to require it. | Accepted. Spanner's rules go to a new § Working rules in `references/spanner.md`, and the Caliper rule goes to the same section in `references/caliper.md` (Steps 4d, 4e). `SKILL.md` and `CLAUDE.md` each gain a sentence naming that home as the one exception to "the role model is stated only in `SKILL.md`" (Steps 2b, 4c). Design study F4 is corrected. AC3.1 now carries the issue's own criterion: the role's reference file. |
| 20261026 | Ray | **Step 4d drops both qualifiers of its source entry.** `feedback_dont_block_on_unwritten_standards.md` limits the rule to "reviewing or authoring work that is *building* the process (issue #80's cycle mechanics, and anything like it)". It also states "Mechanism defects (a wrong `gh` default, an unverifiable AC) are unaffected — those still block." Step 4d writes it unqualified into § Role 2: "A case no standard yet covers is not a finding." As written, it narrows Caliper's criterion 3 (under-specification) for every spec, not only process-building ones. Required: carry both qualifiers into the destination text, or withdraw 4d and give Ray an open question. | Accepted. Both qualifiers are carried (Step 4e), with the entry's "a point argued once and reaffirmed by Ray is decided". The amendment is an `Amendment:` row of Caliper's findings table, because `references/caliper.md`'s Emits allow nothing outside that table. |
| 20261026 | Ray | **The moved text has not been checked against its sources.** Every `Moved` row in design study §3.2 is rewritten at its destination rather than quoted. A check of eight source entries against Steps 2–5 found one with scope lost (4d, above). AC2.2 checks that each rule is stated at its destination, not that it says what the entry said. Required: a criterion that each `Moved` row's destination text is checked against its source entry for scope, conditions and exceptions, with every difference recorded and either justified or corrected. Proposed check: a Caliper pass over the `Moved` rows only, with its findings table in the design study. | Accepted. Spanner re-checked every Moved row first (design study §3.5): about twenty had lost a condition, exception or qualifier, and each is corrected below or kept out with its reason. Caliper's pass is recorded in design study §3.6. AC2.4 covers both. |
| 20261026 | Caliper | Source-check pass over the Moved rows: four findings — §1.6 says nothing writes to the board; two `--limit 200` literals break Step 3f's rule; Step 3a leaves §1.1's recon permission and `n/a` rule contradicting it; the `Amendment:` row's form is unspecified. | Each resolved in design study §3.6: Steps 2d, 3a, 3d, 3k and 4e. |
| 20261026 | Ray | Fidelity pass (design study §3.6), wording noise: `CLAUDE.md`'s wording-artifact line is removed, and `feedback_no_wording_noise.md` becomes Dropped. "Fix it in one line" reads as permission to edit for every role, including Anvil, and the line adds nothing the findings rules don't already cover. | Applied: Step 2a withdrawn, the line removed, design study §3.2 changed. |
| 20261026 | Ray | Fidelity pass, unwritten standards: the rule applies to authoring as well as review. Whichever role meets a case no standard covers identifies it with suggested wording and does not block on it; Ray approves it, and Spanner then writes it into the spec. It goes into `references/spanner.md` § Working rules as well as `caliper.md`, with "and anything like it" restored in place of the closed list. | Applied (Steps 4d, 4e). |
| 20261026 | Ray | Fidelity pass, fix ships its standard: applies to every issue; the general wording stands. Second agent runtime: the general form is correct; Copilot was context, not a standard. | Recorded in design study §3.5 as Ray's decisions; no text change. |
| 20261026 | Ray | Fidelity pass, the remaining findings (issue opening, meeting deletes, writing for a stranger, hand-kept state, stale documents, the editable CLI, "item number"): restore the source's scope, conditions and exceptions as Caliper states them. | Applied (Steps 2c, 3c, 3d, 3f, 3h). |
| 20261026 | Ray | **Two points routed to #242 are recorded only in this design study.** (1) `feedback_anvil_stop_on_any_gap.md`: "A results Deviations row is for something Ray already decided, not a substitute for stopping." (2) `feedback_spec_test_file_drift.md` is the origin of `docs/DEVELOPMENT_STANDARDS.md` §6.4's "use the established file … document the deviation". The entry says outright "This is a 'proceed with the obviously-correct interpretation and note it' situation, not a 'stop the gate and wait for Ray' situation." The study drops both as "#242's subject". Once this set is archived, nothing carries them forward. Required: a step that adds both points, with their source text, to #242's body (same read-check-write procedure as Step 6), and a criterion that checks it. | Accepted. Step 7, AC2.5. Design study §3.2 now records both as moved to #242. |

## 1. Scope

**In scope:**

- A tracked `.claude/settings.json` that turns auto-memory off.
- The text each `Moved` row of the design study's §3.2 names, written at its destination: `CLAUDE.md`; `docs/DEVELOPMENT_STANDARDS.md` §1.1–§1.6, §2.4, §2.6, §2.7 and §6.2; `.claude/skills/session-start/SKILL.md`; a new § Working rules in `references/spanner.md` and `references/caliper.md`; `docs/dev/results/_TEMPLATE_RESULTS.md` §3; `docs/AI_SETTINGS_GUIDE.md`.
- One addition each to #188's and #242's bodies.
- The design study's §6 Disposition and this spec's results artifact.

**Out of scope:**

- Deleting the memory directory. It is outside the working tree, the setting stops it loading, and Ray checks AC2.1 against it (design study §3.4).
- The standards passages and the results template §4 deviations table that #240 names. They are #242's; Step 7 only carries memory's two points to it.
- The Outlook duplicate-series defect in the design study's §3.3. Ray decides whether it becomes an issue.
- The spec template's `<passed> passed` line, which Ray is fixing separately.

## 2. Verified current state

Direct path: each step below quotes the text it replaces or anchors on. Each anchor was confirmed to occur exactly once in its file on 20261026.

## 3. Design rules

- **DR1 — Exact text.** Each edit is made exactly as quoted. A quote that does not match the file stops the step (`.claude/skills/session-start/SKILL.md` § Role 3).
- **DR2 — No unwrapping beyond the edit.** `CLAUDE.md`'s opening paragraph is hard-wrapped. The new paragraph after it is one line, and the wrapped paragraph is left as it is.
- **DR3 — A role's working rules load only in that role's session.** Nothing in Steps 2–5 that governs how a single role works is written into `CLAUDE.md` or `SKILL.md`.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Auto-memory off | `.claude/settings.json` |
| 2 | `CLAUDE.md` additions and the derived issue-list bound | `CLAUDE.md` |
| 3 | Standards additions | `docs/DEVELOPMENT_STANDARDS.md` |
| 4 | Role rules and rationale | `.claude/skills/session-start/SKILL.md`, `references/spanner.md`, `references/caliper.md` |
| 5 | Results template and AI settings guide | `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/AI_SETTINGS_GUIDE.md` |
| 6 | #188 notes the pointer | GitHub issue #188 body |
| 7 | #242 carries memory's two points | GitHub issue #242 body |
| 8 | Study disposition and results artifact | `docs/dev/design/DESIGN_AUTO_MEMORY_RETIREMENT.md`, `docs/dev/results/AUTO_MEMORY_RETIREMENT_RESULTS.md` |

Close-out is not in this table. It is `/closeout`.

### Step 1 — `.claude/settings.json`

Create the file with exactly this content:

```json
{
  "autoMemoryEnabled": false
}
```

### Step 2 — `CLAUDE.md`

**2a.** Withdrawn 20261026 by Ray (Decision Log). Shipped in `1894ec2` and removed by the fidelity amendment.

**2b.** Replace:

```text
A session opens in its declared role with `/session-start <role>`. What each role is, does and hands to the others is `.claude/skills/session-start/SKILL.md` § THREE-ROLE MODEL, and is stated nowhere else.

---
```

with:

```markdown
A session opens in its declared role with `/session-start <role>`. What each role is, does and hands to the others is `.claude/skills/session-start/SKILL.md` § THREE-ROLE MODEL, and is stated nowhere else. The one exception is a rule for how a single role works: it sits in that role's `.claude/skills/session-start/references/<role>.md` § Working rules, which no other role's session loads.

---

## Auto-memory

Claude Code auto-memory is off for this repository: `.claude/settings.json` sets `autoMemoryEnabled` to `false`. No instruction is carried by memory. A rule lives in this file, in `docs/DEVELOPMENT_STANDARDS.md`, or in the skill that governs its role, and a correction Ray gives in a session is made there, through a spec like any other change.

---
```

**2c.** After the last § Common Pitfalls bullet, which ends `never accept an elided "unchanged" block without checking it against the recon's own quote.`, append:

```markdown
- **A destructive write is checked before it runs.** Run `gh` from the repository root: outside a repository it fails, and an empty file passed to `gh issue edit --body-file` blanks the issue, which GitHub cannot restore. Before overwriting anything you did not author, check that the source is non-empty and holds what you expect, and read stderr in the same block. Before changing a value, read the whole file and search it for every occurrence of the value, not only the one you came for. Where a written standard and the practice recorded in an earlier artifact disagree, surface the disagreement before running either.
- **A meeting deleted by a cleanup script or an ad-hoc fix unlinks its notes.** `notes.meeting_id` is `ON DELETE SET NULL`, and the "Notes: N captured" line counts only the current occurrence. Before such a delete, count the meeting's notes by query, and for a recurring meeting count the series too (`MeetingsRepository.get_series_note_count()`). Delete only when the count is 0: any other count means the delete orphans those notes.
- **`scripts/baseline/` is restricted until #188 ships.** Read #188 before running, editing or citing anything under it, and scope any search a check runs to the file it is about, never to a directory that holds the harness.
```

**2d.** In § Project Status, replace:

```text
gh issue list --state open --limit 200 \
  --json number,title,state,milestone,labels,parent,subIssuesSummary
```

with:

```bash
gh issue list --state open --limit "$(gh repo view --json issues --jq .issues.totalCount)" \
  --json number,title,state,milestone,labels,parent,subIssuesSummary
```

`gh repo view --json issues` reports the repository's open-issue count (123 on 20261026, equal to `gh issue list --state open --limit 1000 --json number --jq length`), so the list is never cut short.

### Step 3 — `docs/DEVELOPMENT_STANDARDS.md`

**3a. §1.1.** Three edits.

Replace:

```text
- **Recon** — read-only pass, verbatim findings, no fixes and no inline suggestions.
```

with:

```markdown
- **Recon** — read-only pass, verbatim findings, no fixes and no inline suggestions. Where the findings turn up options, a trade-off, or questions whose answers change the work, the artifact is a design study instead: it adds the options with a recommendation and the open questions (`docs/dev/design/_TEMPLATE_DESIGN.md`), and it is written before the spec. Findings and options never go in the spec's Decision Log or only in chat, and each Decision Log decision cites the question it answers.
```

Replace:

```text
**A recon is permitted on this path**, and earns its place when the change spans documents that may contradict each other
```

with:

```markdown
**A design artifact is permitted on this path, and required where the work turns up options or questions whose answers change it** — the full path's Recon stage states what it then holds. A recon earns its place when the change spans documents that may contradict each other
```

Replace:

```text
**Where no recon is run, no design artifact exists** and the spec's `**Design study:**` field reads `n/a`.
```

with:

```markdown
**Where no design artifact is written**, the spec's `**Design study:**` field reads `n/a`.
```

**3b. §1.2.** Replace:

```text
- Defects found during verification become their own hotfix, not sprint scope — on an open issue that already covers them where one exists, §1.3.
```

with:

```markdown
- **A finding outside the spec's scope is not fixed in it.** Whoever finds it states what an issue for it needs — the defect or gap, and its acceptance criteria — and names any open issue it could join, found by §1.3's search. Ray decides whether it becomes its own issue, joins that one, or is bundled with others.
- **An issue's acceptance criteria validate the work; they do not design it.** They are written before the design exists. Design on the merits. Where the design makes a criterion wrong, the spec restates it in its §5, says the issue body needs the edit, and the edit is made at close-out. A conflict between the design and an issue's criterion is not an open question. A criterion's check must be able to produce the answer the criterion states: a search that cannot see every form of what it counts proves nothing.
- **A fix that establishes a method writes it into this document in the same spec**, with an acceptance criterion of its own, so the next author follows it. This holds where the issue itself calls a missing rule a gap to raise elsewhere. The spec measures the defect's full extent itself — every site, every condition — and never takes the issue's list as the census.
- **An expected failure a spec quotes is observed, never reasoned.** Its author runs each mutation in the working tree, reverts it with `git checkout -- <file>`, and quotes what happened. Each run uses a fresh `PYTHONPYCACHEPREFIX`, because restoring and re-mutating a file within one second at the same size reuses the previous mutation's `.pyc`. Each mutation's old text is a literal that occurs once in its file. The test seeds its own rows, so the mutation cannot pass on whatever the database holds.
- **A rule that refuses authored text is run over the live set it will judge before it is specified** — every open issue, every spec row, whatever the rule reads — and the result is recorded in the spec before its options go to Ray. A rule tried only on its own example can refuse correct text it was never shown. A rule that must tell a property's subject from the evidence for it is a reading, not a pattern.
```

**3c. §1.3.** Replace:

```text
- Work is tracked in GitHub Issues. State is GitHub's own — open or closed. There is no status vocabulary to maintain in prose, and no register or statistics table to keep in step.
```

with:

```markdown
- Work is tracked in GitHub Issues. State is GitHub's own — open or closed. There is no status vocabulary to maintain in prose, and no register or statistics table to keep in step. Work is called an issue and cited by its number. "Backlog", "backlog item" and "item number" are retired terms and are not written into new text; a quote of existing text, and the filename `docs/archive/FEATURE_BACKLOG.md`, stay as they are.
```

**3d. §1.3.** Insert after the bullet that begins `- **An issue is opened only for what no open issue already covers.**`:

```markdown
- **An issue is opened when its body is written, it is on the board, and its dependencies are linked.** It is added to the `WorkmAIn Queue` project at creation — `gh project item-add 3 --owner lockdwn20 --url <issue-url>` — and every real dependency is linked as a GitHub dependency, whichever way it runs: the new issue may wait on an open one, or an open one may wait on it. The link is made on the issue that waits — `gh api --method POST repos/lockdwn20/workmain/issues/<blocked>/dependencies/blocked_by -F issue_id=<the blocking issue's id>`. "Depends on #N" in prose is not a dependency: nothing reads it, and the board shows the issue as ready. Each is verified by reading it back, in both directions — the board read in §1.6, `gh api repos/lockdwn20/workmain/issues/<blocked>/dependencies/blocked_by` and `gh api repos/lockdwn20/workmain/issues/<blocker>/dependencies/blocking` — because `item-add` prints nothing on success.
```

**3e. §1.4.** Replace:

```text
- **Steps.** Ordered work inside a spec. Committed individually, reviewable and revertible individually. No approval stop. A step ends with a commit, not with a request to continue.
```

with:

```markdown
- **Steps.** Ordered work inside a spec. Committed individually, reviewable and revertible individually. No approval stop. A step ends with a commit, not with a request to continue. A step that changes a signature, a required input or an invariant updates every caller in that step, or keeps the old call working, so each step's commit leaves the suite green.
```

**3f. §1.5.** Insert after the bullet that begins `- **Markdown is never hard-wrapped.**`:

```markdown
- **Nothing is proposed that has to be kept up by hand.** No list, register, count, status table or copy of state that lives somewhere authoritative goes into a document, a spec step, a criterion or a script. A test count, queue size, version or status written as currently true is stale on the next commit, and the next reader spends a turn reconciling it. The rule is stated, and the set is derived from its live source: `pytest --collect-only -q`, `gh issue list`, `gh label list`, `workmain/__version__.py`. An operational bound, such as a `--limit`, is an instruction to derive it, never a remembered number. A list found already in a document is deleted, not updated: needing an update is the sign it should not exist. A criterion that would need such a list checks instead that the rule is stated. A document that cannot be trusted is deleted, not annotated. A dated measurement with its evidence, such as a recon's suite count at recon time, is a record and stays.
- **A change to a rule searches the whole document set** — `CLAUDE.md`, this document, the skills and the templates — for every other statement of it, and corrects each one. A historical citation stays as written; only a live, forward-looking reference is repointed.
- **A document is written for a reader who has read nothing else.** An issue, a criterion and a design study's open question each stand alone. The facts they depend on are stated in them. A rule is stated in a sentence, and another document is cited as its checklist, never as its definition. What breaks, and who notices, is spelled out. A design study's question says whether the problem it asks about is real before framing it, and a finding that cites two files says which one has the problem and which is there for contrast. An ID — a finding, a question, a design rule — is used only inside the file that defines it; anywhere else the thing is stated or cited in full. A bare `§` is only ever a section of this document, wherever it is written; a section of any other document is cited with that document's name, and on its first reference in a document with what the section is. A reason is stated in terms the reader can check. An issue number may follow it as the record, but never stands in as the reason. An example is set out as an example, not woven into the rule, and is checked against the rest of this document before it goes in.
```

**3g. §2.4.** Insert after the bullet ``- `git commit --no-verify` is **prohibited**. It bypasses commit validation.``:

```markdown
- **Stage only the files you wrote** — `git add <path>`, never `git commit -a`. Ray edits live `config/` in the working tree mid-session, and `-a` commits his edit under your message. Check `git status --short` first; a file you did not touch stays unstaged and is mentioned.
```

**3h. §2.6.** Insert after the line ``Confirm the new `ActiveEnterTimestamp` postdates the merge commit before calling anything deployed.``:

```markdown

**The CLI does not wait for the restart.** `workmain` is an editable install from the repository, so every `workmain` command runs whatever branch is checked out, in its own process. A live check made through the CLI passes on the working branch: where a spec has one that Ray runs, he runs it there, before `/closeout`. Only what the daemon runs — the T1–T6 triggers (`CLAUDE.md` § Trigger Terminology) and Slack Socket Mode — waits for the restart.
```

**3i. §2.7.** Replace:

```text
4. Create the branch **before** writing anything.
```

with:

```markdown
4. Create the branch **before** writing anything. A `hotfix/*` or `chore/*` branch is cut from `origin/main` after `git fetch` — `git checkout -b <branch> origin/main` — because pull requests merge on GitHub and a local `main` falls behind.
```

**3j. §6.2.** Insert after rule 8, which ends `takes the routing as a required argument and makes every unstubbed provider raise.`:

```markdown
9. **A test pins behaviour meant to stay.** It never exercises a path an open issue is about to remove or narrow; it proves the same property with inputs that issue leaves valid. Opening an issue that narrows behaviour includes rewriting the open criteria and tests that exercise the narrowed path, and both issues say why.
```

**3k. §1.6.** Replace:

```text
gh project item-list 3 --owner lockdwn20 --format json --limit 200 --query "is:open" \
```

with:

```bash
gh project item-list 3 --owner lockdwn20 --format json --query "is:open" \
  --limit "$(gh project view 3 --owner lockdwn20 --format json --jq .items.totalCount)" \
```

and replace:

```text
Ordering is Ray's. Position is set in the Web UI, and nothing in this repository writes to the board.
```

with:

```markdown
Ordering is Ray's. Position is set in the Web UI, and nothing in this repository changes it. Adding a new issue to the board (§1.3) is the one write, and it orders nothing. The limit is the board's own item count, because `item-list` cuts its output at `--limit` without saying so.
```

### Step 4 — session-start skill

**4a. `SKILL.md`.** Append to the bullet `- The same arguments against the same repository and GitHub state produce the same output.`:

```markdown
 That is what the skill is for: before it, every session opened with a different set of commands and closed with a different summary.
```

**4b. `SKILL.md`.** Insert after `**Model changes happen between chats, not during chats.**`:

```markdown

Each role is its own Claude Code session — never a subagent, which runs inside its parent's session, and never a second agent runtime, which chooses its model its own way. Either collapses the boundary between roles that this model exists to keep.
```

**4c. `SKILL.md`.** Replace:

```text
§ THREE-ROLE MODEL below is the only statement of what each role is, does and hands to the others. It holds for the whole session, not only for the run.
```

with:

```markdown
§ THREE-ROLE MODEL below is the only statement of what each role is, does and hands to the others. It holds for the whole session, not only for the run. The one exception is a rule for how a single role works: it sits in that role's reference file, § Working rules, so that no other role's session loads it.
```

**4d. `references/spanner.md`.** Append after the last line, `` - **Branch** — the branch read 5 found, or `none exists`. ``:

```markdown

## Working rules

These hold for the whole Spanner session. The run neither reads nor emits them, and no other role's session loads them.

- **Apply a rule; do not ask.** Where a documented rule, or a precedent in the same document, decides a question, state the answer in one line and carry on. Ask only when rules conflict, when no rule covers the case, or when the answer changes scope Ray owns. Stating the applied rule is not skipping approval: Ray can still reverse it. A recommendation that is obvious while it is being written was decided by a rule.
- **No filler options.** Drop every option the findings or a standing rule defeat, even one the issue names. When one survives, say it is the only valid option and why.
- **Decide; do not defer.** What the issue in hand should settle is settled there — never parked as "the spec's call" or as a future issue. Dead code found in scope is removed in scope, with its blast radius inventoried and acceptance criteria of its own.
- **A reviewer's claim about who owns a decision is checked against the role model, not adopted.** A decision is withdrawn on the merits of the finding, and the authority claim is recorded as not taken.
- **Build only what the issue asks for.** A mechanism the issue did not name goes to Ray as an open question, saying what it is for, before it is specified. A rule that needs tooling to enforce it is two issues. When a review round lands, check whether each finding is about the work or about surface added since the last round; if the latter, the fix is usually deletion.
- **A repeated pattern is not a precedent if an open issue calls it a defect.** Before citing what other call sites do, search the open issues for that family of defect. A value a request sends to a provider is declared in configuration, never inherited from a Python default or a literal at the call site.
- **A design holds for every provider a call type can be routed to.** Which provider serves a call is switchable configuration, often set to work around the defect in hand. Read the commit message that set a value before calling the value a finding.
- **A position Ray brings from an outside review is his decision** once he confirms it — pasted text is not his words until he says so — and is recorded as his, never cited to the review. Its claims are verified against code first.
- **A case no standard yet covers does not block the work.** When authoring work that builds the process — the standards, the skills, the implementation cycle, and anything like it — a case no standard yet covers is identified with suggested wording, and the work carries on. Ray approves the wording, and Spanner then writes it into the spec. A mechanism defect — a wrong command default, a criterion that cannot be checked — still blocks.
- **Keep the open items visible.** When Ray's input moves between several open items, keep a checklist of them in the reply and show it each time it changes.
```

**4e. `references/caliper.md`.** Replace the last line:

```text
With no finding, the run emits the same table with one row, `| <YYYYMMDD> | Caliper | No findings. | n/a |`, and nothing else. No other commentary.
```

with:

```markdown
An amendment (§ Working rules) is a row of the same table: `| <YYYYMMDD> | Caliper | Amendment: <criterion number>: <the case no standard yet covers, and the suggested wording> | |`. With no finding and no amendment, the run emits the same table with one row, `| <YYYYMMDD> | Caliper | No findings. | n/a |`, and nothing else. A run with amendments and no finding emits the amendment rows alone. No other commentary.

## Working rules

These hold for the whole Caliper session. The run neither reads nor emits them, and no other role's session loads them.

- **A spec that builds the process can outrun the standards.** Where the spec under review builds the process — the standards, the skills, the implementation cycle, and anything like it — a case no standard yet covers is not a finding against it. It is an amendment row (§ Emits) with suggested wording, and it does not hold the spec. Ray approves the wording, and Spanner then writes it into the spec. A mechanism defect — a wrong command default, a criterion that cannot be checked — is still a finding, in every spec. A point argued once and reaffirmed by Ray is decided.
```

### Step 5 — results template and AI settings guide

**5a. `docs/dev/results/_TEMPLATE_RESULTS.md`.** Insert after the row ``| AC1.1 | Met / **Not met** / Carried | `pytest ...` output, file:line, or command result |``:

```markdown

This section holds only the AC table. Close-out reads every three-column table under `## 3.` as AC rows (`automation/closeout_acs.py`), so a supporting table goes under `## 5. Verification` and the AC row cites it.
```

**5b. `docs/AI_SETTINGS_GUIDE.md`.** Insert before `### Claude-Specific Fields`:

```markdown
**Cost values are Ray's.** `cost_structure` and every `cost_per_1k_*` field are set by Ray whenever a model changes. A spec step that changes a model changes `model`, `notes` and `last_updated`, then stops and reports the expected cost values, citing the vendor's live pricing page and the date it was read, never a cached table. Ray makes the cost edit.

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

### Step 7 — #242

Same procedure as Step 6, for #242. After the bullet that begins ``- line 780, §6.4: a spec-named test file that doesn't exist``, insert:

```markdown

Two corrections Ray gave earlier bear on this adjudication. Both were held only in Claude Code auto-memory, which #241 retired:

- On #202's implementation (20261026): "A results Deviations row is for something Ray already decided, not a substitute for stopping."
- The note §6.4's passage was written from (Item #61, 20260725), which says outright: "This is a 'proceed with the obviously-correct interpretation and note it' situation, not a 'stop the gate and wait for Ray' situation — the latter is reserved for actual design ambiguity (scope, architecture, behavior), not filename bookkeeping."
```

No commit; the deliverable is on GitHub.

### Step 8 — study disposition and results artifact

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
| AC2.4 | Each `Moved` row's destination text says what its source entry said — the same scope, conditions and exceptions — and every difference is recorded with its correction or the reason it stands. | Stated reading by Ray of the design study's §3.5 (Spanner's check) and §3.6 (Caliper's pass), every row resolved |
| AC2.5 | #242 carries memory's two points on deviations, in their source wording. | `gh issue view 242 --json body --jq .body` piped to `grep -c 'substitute for stopping'` and to `grep -c 'filename bookkeeping'` each prints `1` |
| AC2.6 | No live document reads issues or the board with a fixed `--limit`; each bound is derived from the live count, so neither read can be cut short as the queue grows. | `grep -rn -- '--limit [0-9]' CLAUDE.md docs/DEVELOPMENT_STANDARDS.md .claude/` returns nothing, and the §1.6 board read and the § Project Status issue read each return as many open items as `gh repo view --json issues --jq .issues.totalCount` |
| AC3.1 | No role-specific rule moved out of memory lands in a file every role loads (`CLAUDE.md`, `SKILL.md`). Each lands in the § Working rules of `.claude/skills/session-start/references/<role>.md` for the role it governs. | Stated reading by Ray of Step 2's and Step 4a–4c's additions, and of § Working rules in `references/spanner.md` and `references/caliper.md` |
| AC4.1 | `CLAUDE.md` states that auto-memory is off for this repository and that no instruction is carried by memory. | `grep -n autoMemoryEnabled CLAUDE.md` returns one line, in § Auto-memory |
| AC5.1 | A session opened after the change loads no auto-memory. | Ray runs `/memory` in a fresh session on this branch and reports auto-memory shown as off |

## 6. Test plan

Omitted: no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes.

## 7. Risks and rollback

- **Auto-memory stays on.** The project setting overrides the user setting for this repository, per the Claude Code docs (design study F1); AC5.1 observes it. Rollback: `git revert` the Step 1 commit.
- **A moved rule contradicts its new neighbours.** Each insertion was read against the section it joins. Rollback: revert that step's commit.
- **#188's or #242's body is damaged.** Steps 6 and 7 check the body is non-empty and that each anchor matched once, and read it back. Recovery is the scratchpad copy read at the start of the step.
