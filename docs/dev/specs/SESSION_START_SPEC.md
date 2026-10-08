# Session-Start Skill — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261007
**Branch:** `chore/issue-85-session-start`
**Target release:** n/a — `chore/*`, `docs/DEVELOPMENT_STANDARDS.md` §2.2
**Originating item:** Issue #85, child of #80
**Design study:** n/a — direct path, no recon was run

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261007 | Spanner | The issue's premise that an unsupplied declared argument expands to an empty string, and so cannot fail on its own, was checked against the Claude Code skills reference (`https://code.claude.com/docs/en/skills`, § "When Arguments Are Not Supplied"): a named placeholder from `arguments` with no matching argument expands to an empty string; an indexed `$N` with no argument stays as literal text. | Holds. The skill declares `arguments: [role, target]` and refuses on an empty `role` as its own first step. |
| 20261007 | Spanner | The issue's AC7 reads the `--limit` from "the command in the reference". `docs/DEVELOPMENT_STANDARDS.md` §1.6 already owns the board-read command, `--limit` included, and `CLAUDE.md`'s opening gives every rule one home. A copy in the reference is a second home that drifts the first time §1.6 changes. | The Spanner reference runs §1.6's command by citation. AC7.1 checks the limit in the command the reference cites. The issue's AC7 is reworded at close-out to match. |
| 20261007 | Spanner | `disable-model-invocation: true`, as `closeout` carries. A role is declared by the person in the session; a skill the model can load on its own would let it declare one. | Applied. The verification runs in AC4.1–AC6.1 are therefore Ray's invocations; Spanner records their output. |
| 20261007 | Ray | Board order puts #80 above its own child #85, so a no-target Spanner run that reports the first open item reports a parent, which is not workable. | Option A: a no-target run skips every item whose sub-issues are not all closed and reports the first that remains, naming each parent it passed over. A blocked item is not skipped; its blockers are reported, so board position still decides. |
| 20261008 | Ray | With the skill in place, the role definitions belong in it rather than in `CLAUDE.md` § THREE-ROLE MODEL: one home, so a change to one role or to all of them is one edit, and each role carries its next steps with it. This reverses the issue's premise that the skill cites `CLAUDE.md` for the roles. | Applied as Steps 3 and 4. The issue's ACs 8, 9 and 10 are reworded at close-out to match AC8.1–AC10.1. |
| 20261008 | Spanner | Where the moved text can live. Per the Claude Code skills reference (`https://code.claude.com/docs/en/skills`, § "Skill content lifecycle"), an invoked `SKILL.md` stays in context and is re-attached after auto-compaction (first 5,000 tokens); a reference file is loaded by a read and can be summarised away. Rules that hold for the whole session must therefore be in `SKILL.md`. Inlining only the declared role's reference through `!`-command injection was considered: untested argument substitution order, and a failing command aborts the whole invocation. | Ray chose all three role definitions in `SKILL.md`, references holding only the session-open run. Carrying the other two roles is required, not a cost: a role has to know the others to hand a spec to Caliper or a handoff to Anvil. |

| 20261008 | Caliper | 4: `e5727c5` changes `config/ai_settings.json` on this branch, outside §1's scope; `docs/DEVELOPMENT_STANDARDS.md` §2.8 keeps `config/*` off `chore/*`, so close-out would ship a config change to `main` with no release. | Accepted as a deviation on Ray's direction, 20261008: the commit is an operational provider switch made through the CLI during live use, not development. The missing rule for operational changes is carried to the correction issue opened at the end of this work. |
| 20261008 | Caliper | 3: the results step names "the §5 AC table"; `docs/dev/results/_TEMPLATE_RESULTS.md` carries the AC table in §3, which `/closeout` reads. | Accepted. Step 5 names the spec's §5 ACs as the results artifact's §3 table. |
| 20261008 | Caliper | 1/7: AC4.1 and AC6.1 record outputs but state no pass condition, so any recorded output passes. The Anvil run also ended with a recommendation its reference does not allow. | Accepted. Both criteria carry a pass condition. `SKILL.md`'s run rules end every run at its reference's last emitted item (Step 3a). |
| 20261008 | Caliper | 7/3: `SKILL.md` lists the role names, and AC10.1's grep cannot see them. | Resolved by the role move: `SKILL.md` is the home of the role set, so naming the roles there restates nothing. |

| 20261008 | Caliper | 2/5: Spanner read 4 matches `Issue #<N>`, but both templates show the `**Originating item:**` placeholder as `Backlog Item #N`. | `Backlog Item` is the retired markdown-backlog term; every live artifact outside the templates uses `Issue #N`. The search stays. The template placeholders are carried to the correction issue, on Ray's direction 20261008. |
| 20261008 | Caliper | 3: Spanner's "Next stage" cannot be derived from read 4, which finds only design studies and specs. | Ray's direction 20261008: cite `docs/DEVELOPMENT_STANDARDS.md` rather than write per-role definitions of done into the skill. Read 4 also finds the results artifact, and Next stage cites §1.1 and §1.5 for the stages and spec status. The standards state no done condition for Implementation, so that one condition cites `docs/dev/results/_TEMPLATE_RESULTS.md` §3. The missing §1.1 done conditions, and the undefined Spanner-to-Anvil handoff, are carried to the correction issue (Step 3d). |
| 20261008 | Caliper | 7: AC1.1 requires `.claude/skills/` to hold `closeout` and `session-start` only, so an unrelated skill added later fails it without breaking its intent. | Accepted, on Ray's direction 20261008: AC1.1 checks that `session-start` exists with its files and makes no claim about other skills. |

| 20261008 | Caliper | 2/5: §6 says no file under `config/` changes, but `e5727c5` changes `config/ai_settings.json`, which six tests read directly (`tests/test_report_generator.py:36`, `tests/test_ai_providers_offline.py:25`, `tests/test_narration.py:27`, `tests/test_intent_parser.py:297`, `tests/test_note_condenser.py:158`, `tests/test_provider_foundation.py:978`); the baseline predates it. | Accepted. §6 names the commit and the reads, and records the suite at `a415051`, after the swap, matching the baseline. |
| 20261008 | Caliper | 3/5: §7's rollback says every step touches only new files; Steps 3 and 4 edit existing files, and reverting Step 3 alone leaves the Step 4 citations pointing at a section that no longer exists. | Accepted. §7 states the revert order. |

---

## 1. Scope

**In scope:** four new files — `.claude/skills/session-start/SKILL.md` and `references/spanner.md`, `references/caliper.md`, `references/anvil.md` — plus this spec and its results artifact. The move of `CLAUDE.md` § THREE-ROLE MODEL into `SKILL.md`, and the three citations that point at it: `CLAUDE.md` § Critical Rules ("Stop and surface"), the `docs/DEVELOPMENT_STANDARDS.md` preamble, and `docs/dev/specs/_TEMPLATE_SPEC.md` §3.

**Out of scope:**

- Enforcing that a session is in a role — the issue's own exclusion.
- Any other edit to `CLAUDE.md` or `docs/DEVELOPMENT_STANDARDS.md` (including §2.7), and any edit to the `closeout` skill.
- `Role 1`, `Role 2` and `Role 3` used as names in `docs/DEVELOPMENT_STANDARDS.md` §1.1–§1.5 and in the template `**Author:**` fields. They name a role and cite no section, so they resolve against wherever the definitions live.
- Session close. `/closeout` covers an issue's close; a per-session close summary is not in #85.
- Any write by the skill. Every source it names is read-only; it creates no branch, file, commit or GitHub object.

## 3. Design rules

- **DR1 — Refuse before reading.** The first thing a run does is validate its arguments. No tool call precedes it.
- **DR2 — Named sources only.** A run reads the sources its reference names, in the order named, and emits only what they carry. A source that cannot be read is reported unreadable; nothing is reconstructed in its place.
- **DR3 — One home for the roles; cite everything else.** `SKILL.md` § THREE-ROLE MODEL is the only statement of what each role is, does and hands to the others; nothing else states it. Every other rule and command another document owns is cited by its section, never copied.
- **DR4 — Common once.** What holds for all three roles lives in `SKILL.md`; a reference carries only its role's target, reads and emits.
- **DR5 — Same inputs, same run.** Identical arguments against identical repository and GitHub state produce identical output. No editorial commentary and no closing summary.

Anything not covered: `.claude/skills/session-start/SKILL.md` § Role 3 — stop and surface to Ray.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Write `SKILL.md` with the exact text below. Commit `chore(skills): add the session-start skill entry point`. | `.claude/skills/session-start/SKILL.md` |
| 2 | Write the three references with the exact text below. Commit `chore(skills): add the session-start role references`. | `.claude/skills/session-start/references/{spanner,caliper,anvil}.md` |
| 3 | Move the role definitions into `SKILL.md`, repoint the references to them, and widen Spanner's artifact read, with the exact text in § Step 3 below. Commit `chore(skills): make session-start the home of the role definitions`. | `.claude/skills/session-start/SKILL.md`, `.claude/skills/session-start/references/{spanner,caliper,anvil}.md` |
| 4 | Replace `CLAUDE.md` § THREE-ROLE MODEL with its pointer and repoint the three citations, with the exact text in § Step 4 below. Commit `docs(standards): point role citations at the session-start skill`. | `CLAUDE.md`, `docs/DEVELOPMENT_STANDARDS.md`, `docs/dev/specs/_TEMPLATE_SPEC.md` |
| 5 | Write the results artifact from `docs/dev/results/_TEMPLATE_RESULTS.md`: this spec's §5 ACs as the results artifact's §3 table, the output of each Ray-invoked run named in AC4.1–AC6.1, the AC7.1 count comparison, and the suite counts. Commit `docs(results): record the session-start skill results for issue #85`. | `docs/dev/results/SESSION_START_RESULTS.md` |

### Step 1 — `.claude/skills/session-start/SKILL.md`

````markdown
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
````

### Step 2 — `.claude/skills/session-start/references/spanner.md`

````markdown
# Spanner session open

**Role:** `CLAUDE.md` § Role 1. **Target:** an issue number, optional.

## Reads, in order

1. **The item.** With a target, the item is that issue; skip to read 2. Without one, run the board read in `docs/DEVELOPMENT_STANDARDS.md` §1.6 exactly as written there. Walk the result in board order: for each item, read `gh issue view <N> --json subIssuesSummary`; the item is the first whose `subIssuesSummary.total` equals `subIssuesSummary.completed`. Every item passed over is a parent with open children. When no item qualifies, the item is `none` and reads 2–5 are skipped.
2. `gh issue view <N> --json number,title,state,body,labels,milestone,parent,subIssuesSummary`
3. `gh api repos/{owner}/{repo}/issues/<N>/dependencies/blocked_by --jq '.[] | "#\(.number) \(.state) \(.title)"'`
4. `grep -lE '^\*\*Originating item:\*\* .*Issue #<N>([^0-9]|$)' docs/dev/design/*.md docs/dev/specs/*.md`, and the `**Status:**` and `**Branch:**` lines of each file found.
5. `git branch --list '*/issue-<N>-*'`

## Emits

- **Item** — number, title, state, milestone, labels, parent, or `none`. Without a target, also each parent passed over in read 1.
- **Blocked by** — each blocker with its state, or `none`.
- **Artifacts** — each design study and spec found, with its `Status:`, or `none`.
- **Next stage** — the first stage of the `docs/DEVELOPMENT_STANDARDS.md` §1.1 path whose artifact read 4 did not find. The path is the branch type a found spec's `**Branch:**` field or the issue body states; where neither states one, say so and name the first stage of each path.
- **Branch** — the branch read 5 found, or `none exists`.
````

### Step 2 — `.claude/skills/session-start/references/caliper.md`

````markdown
# Caliper session open

**Role:** `CLAUDE.md` § Role 2. **Target:** a spec path, required.

## Reads, in order

1. The spec at the target path, end to end.
2. The originating issue named by the spec's `**Originating item:**` field: `gh issue view <N> --json number,title,body,labels,milestone,parent`
3. The design study named by the spec's `**Design study:**` field, resolved relative to the spec. Skipped when the field reads `n/a`.
4. Every source the spec cites — file, symbol, line, section or command — at the cited location.

## Emits

Findings against the review criteria `CLAUDE.md` § Role 2 carries, as a table with the spec's Decision Log header and one row per finding. Resolution is left empty — it is filled when the finding is resolved:

```markdown
| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| <YYYYMMDD> | Caliper | <criterion number>: <finding, with the evidence that grounds it> | |
```

With no finding, the run emits `No findings.` and nothing else. No other commentary.
````

### Step 2 — `.claude/skills/session-start/references/anvil.md`

````markdown
# Anvil session open

**Role:** `CLAUDE.md` § Role 3. **Target:** a spec path, required.

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

Every read runs and every discrepancy is reported; the run does not stop at the first. What happens next is `CLAUDE.md` § Role 3.
````

### Step 3 — the role definitions move into `SKILL.md`

**3a — `SKILL.md`, the paragraph under the title and one run rule.** Replace:

> This skill **reads**. It writes no file, creates no branch or commit, and makes no GitHub change. It assembles the state a role needs before it acts, from the sources that role's reference names, in the order named. What each role is and does is `CLAUDE.md` § THREE-ROLE MODEL; this skill restates none of it.

with:

````markdown
The session-open run **reads**. It writes no file, creates no branch or commit, and makes no GitHub change. It assembles the state a role needs before it acts, from the sources that role's reference names, in the order named.

§ THREE-ROLE MODEL below is the only statement of what each role is, does and hands to the others. It holds for the whole session, not only for the run.
````

and, in `## Rules every run holds`, replace the second bullet:

> Emit only what those sources carry, in the shape the reference states. No commentary, no recommendation the reference does not name, no closing summary.

with:

> Emit only what those sources carry, in the shape the reference states, and end at the last item its Emits list names. No commentary, no recommendation the reference does not name, no closing summary.

**3b — `SKILL.md`, appended after `## Anything not covered here` and its line.** A `---` rule, then `CLAUDE.md` lines 30–75 moved word for word, with one sentence changed. The section's second line reads `Each chat session begins with the role clearly stated.` today; it becomes `` Each chat session begins with `/session-start <role>`. `` — invoking the skill is now how the role is stated. The full appended text:

````markdown
---

## THREE-ROLE MODEL ⭐

Operating outside this model causes architecture drift. Each chat session begins with `/session-start <role>`.

**Model changes happen between chats, not during chats.**

### Role 1 - Claude Code (VS Code UI) / Opus - Codename: Spanner - Spec Planner & Keeper

All design authority lives here:

- Writes all specs; makes all architecture decisions.
- Maintains the implementation plan and workflow.
- Identifies any workflow, phasing or sprint issues immediately to Ray.
- Resolves conflicts in design and project documentation during planning, so they never reach implementation. Ray is the final authority on all documentation changes.

**Role 1 Critical Rule.** The easiest way is not always the correct way:

- All designs follow the established application services, orchestration and workflows.
- Do not consider a parallel design path because it is easier than planning against the existing one.

### Role 2 - Claude Code (CLI) / Opus - Codename: Caliper - Spec Reviewer

Reviews every spec before implementation begins, against these criteria:

1. Which acceptance criteria are not mechanically testable?
2. Which claims about existing behavior were asserted rather than verified against code?
3. Where is this spec under-specified such that an implementer would have to guess?
4. What here is scope that wasn't in the originating item?
5. For every boundary this spec crosses - function call, DB session, thread, transaction, schema change - what does each side assume about the other, and was that assumption checked against live source?
6. Does this spec introduce a new path where an existing service, orchestrator, or workflow already covers the case?
7. Which acceptance criteria could be satisfied by a change that does not achieve what the criterion is for? — how a criterion is worded so that difference is visible: `docs/DEVELOPMENT_STANDARDS.md` §1.2.

Findings go BACK to Role 1, never forward. You do not implement.

### Role 3 - Claude Code / Sonnet - Codename: Anvil - Implementer

Works from approved specs only. Read the full spec end to end, cross-check and validate all references, and report discrepancies before touching step 1.

If you encounter anything the spec doesn't cover, or that requires a design decision:

1. **STOP at the current step** - do not proceed
2. **Document the issue clearly** in chat
3. **Tell Ray** - he will bring it to Spanner
4. **Do NOT self-resolve** - no scope adjustments, no in-flow architecture calls

**Choosing the cheapest way to turn an acceptance criterion green is a design decision.** Where the least-effort way to satisfy a criterion and the way that achieves what it is for come apart, that is not an implementer's call — it is the case above, and it stops at 1 through 4. How a criterion is worded so the two are distinguishable: `docs/DEVELOPMENT_STANDARDS.md` §1.2.
````

**3c — the references.** `CLAUDE.md` becomes `SKILL.md` in each role citation, and nothing else on the line changes:

| File | Line | Before | After |
| --- | --- | --- | --- |
| `references/spanner.md` | 3 | `` **Role:** `CLAUDE.md` § Role 1. `` | `` **Role:** `SKILL.md` § Role 1. `` |
| `references/caliper.md` | 3 | `` **Role:** `CLAUDE.md` § Role 2. `` | `` **Role:** `SKILL.md` § Role 2. `` |
| `references/caliper.md` | 14 | `` the review criteria `CLAUDE.md` § Role 2 carries `` | `` the review criteria `SKILL.md` § Role 2 carries `` |
| `references/anvil.md` | 3 | `` **Role:** `CLAUDE.md` § Role 3. `` | `` **Role:** `SKILL.md` § Role 3. `` |
| `references/anvil.md` | 22 | `` What happens next is `CLAUDE.md` § Role 3. `` | `` What happens next is `SKILL.md` § Role 3. `` |

**3d — `references/spanner.md`, read 4 and Next stage.** Replace read 4:

> 4. `grep -lE '^\*\*Originating item:\*\* .*Issue #<N>([^0-9]|$)' docs/dev/design/*.md docs/dev/specs/*.md`, and the `**Status:**` and `**Branch:**` lines of each file found.

with:

> 4. `grep -lE '^\*\*Originating item:\*\* .*Issue #<N>([^0-9]|$)' docs/dev/design/*.md docs/dev/specs/*.md`, and the `**Status:**` and `**Branch:**` lines of each file found. For each spec found, `grep -l '^\*\*Spec:\*\* .*<spec file name>' docs/dev/results/*.md` and the `**Status:**` line of each file found.

Replace the Artifacts and Next stage bullets:

> - **Artifacts** — each design study and spec found, with its `Status:`, or `none`.
> - **Next stage** — the first stage of the `docs/DEVELOPMENT_STANDARDS.md` §1.1 path whose artifact read 4 did not find. The path is the branch type a found spec's `**Branch:**` field or the issue body states; where neither states one, say so and name the first stage of each path.

with:

> - **Artifacts** — each design study, spec and results artifact found, with its `Status:`, or `none`.
> - **Next stage** — the first stage on the item's `docs/DEVELOPMENT_STANDARDS.md` §1.1 path that the artifacts found do not show done, judged by §1.1 for which artifact each stage produces, §1.2 for review before approval, §1.5 for the spec's `Status:`, and `docs/dev/results/_TEMPLATE_RESULTS.md` §3 for the results artifact as the last implementation step. The path is the branch type a found spec's `**Branch:**` field or the issue body states; where neither states one, say so and name the first stage of each path.

### Step 4 — `CLAUDE.md` and the citations that point at the roles

**4a — `CLAUDE.md` § THREE-ROLE MODEL.** Lines 30–75, quoted in full at 3b, are replaced by:

````markdown
## THREE-ROLE MODEL ⭐

A session opens in its declared role with `/session-start <role>`. What each role is, does and hands to the others is `.claude/skills/session-start/SKILL.md` § THREE-ROLE MODEL, and is stated nowhere else.
````

**4b — `CLAUDE.md` § Critical Rules, "Stop and surface", its last sub-bullet.** Ray-approved reword, 20261008. Replace:

> This entry is the full statement of the global rule; Role 3 below holds the implementation-specific form.

with:

> This entry is the full statement of the global rule; `.claude/skills/session-start/SKILL.md` § Role 3 holds the implementation-specific form.

**4c — `docs/DEVELOPMENT_STANDARDS.md`, preamble, line 3.** Replace:

> How work gets built. `CLAUDE.md` owns who does what (the three-role model), what this project is (stack, architecture), and domain decisions (tag system, time format, trigger terminology, write-path map). This document owns everything else — process, git workflow, code patterns, database, CLI structure, and testing.

with:

> How work gets built. `.claude/skills/session-start/SKILL.md` owns who does what (the three-role model). `CLAUDE.md` owns what this project is (stack, architecture) and domain decisions (tag system, time format, trigger terminology, write-path map). This document owns everything else — process, git workflow, code patterns, database, CLI structure, and testing.

**4d — `docs/dev/specs/_TEMPLATE_SPEC.md` §3, last line.** Replace:

> State explicitly what an implementer should do when they hit something not covered: see `CLAUDE.md` Role 3 for the escalation  procedure.

with:

> State explicitly what an implementer should do when they hit something not covered: see `.claude/skills/session-start/SKILL.md` § Role 3 for the escalation procedure.

### Authorization points

None. The merge to `main` belongs to `/closeout`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The `session-start` skill exists with its entry point and exactly one reference per role | `ls .claude/skills/session-start/ .claude/skills/session-start/references/` shows `SKILL.md` and `references/`, and exactly `anvil.md caliper.md spanner.md` |
| AC2.1 | The requirements common to all three roles — the read-only property, Step 0's refusal, the four run rules and the reference dispatch — are stated in `SKILL.md` and in no reference | Stated reading by Ray of `SKILL.md` and the three references, for any common rule appearing in a reference |
| AC3.1 | Each reference names its target, the sources it reads in numbered order, and what the run emits | Stated reading by Ray of the three references, for whether each run's reads and output can be told without running it |
| AC4.1 | A run emits state assembled only from its reference's named sources, with nothing a source carries reconstructed and nothing beyond its Emits list | Ray invokes `/session-start Spanner`, `/session-start Caliper docs/dev/specs/SESSION_START_SPEC.md` and `/session-start Anvil docs/dev/specs/SESSION_START_SPEC.md` against the live repository. The results artifact records each output beside the source reads it made. Passes when every fact in each output matches the source read it came from, and no output carries an item its reference's Emits list does not name |
| AC5.1 | The skill stops before reading any source when the role is absent or unknown, or when Caliper or Anvil has no spec path | Ray invokes `/session-start`, `/session-start Hammer` and `/session-start Caliper`; the results artifact records for each that the output is the usage line and that no tool call preceded it |
| AC6.1 | `Spanner` with no target reports the next open item from the board; with an issue number it opens on that item | Ray invokes `/session-start Spanner` and `/session-start Spanner 85`. Passes when the first run's item equals the item derived independently — the `docs/DEVELOPMENT_STANDARDS.md` §1.6 read, skipping each item whose sub-issues are not all closed, recorded in the results artifact — and the second run's item is #85 |
| AC7.1 | The queue read the Spanner reference cites passes an explicit `--limit` above the current open-issue count, so the default of 30 cannot truncate the board | Read the `--limit` in the `docs/DEVELOPMENT_STANDARDS.md` §1.6 command that `references/spanner.md` cites, and compare it against `gh issue list --state open --limit 300 --json number --jq length`; both values are recorded in the results artifact |
| AC8.1 | Each reference cites its own role's section of `SKILL.md` — Role 1 from Spanner, Role 2 from Caliper, Role 3 from Anvil — so a reader of any one is sent to the role definition rather than given a copy | `grep -n 'SKILL.md. § Role' .claude/skills/session-start/references/*.md` shows `Role 1` in `spanner.md`, `Role 2` in `caliper.md` and `Role 3` in `anvil.md`, and no reference line cites `CLAUDE.md` for a role |
| AC9.1 | The role definitions have one home, `SKILL.md` § THREE-ROLE MODEL: no live document outside the skill states a role's duties, the review criteria or the stop procedure, and `CLAUDE.md` § THREE-ROLE MODEL is the Step 4a pointer | `grep -rnE 'Codename:\|Reviews every spec\|STOP at the current step\|Role 1 Critical Rule' --include='*.md' .`, excluding `docs/archive/` and this spec, hits only `.claude/skills/session-start/SKILL.md`; and a stated reading by Ray of `CLAUDE.md` § THREE-ROLE MODEL against Step 4a |
| AC10.1 | No live document sends a reader to `CLAUDE.md` for a role, so every role citation resolves to the one home | `grep -rnE 'CLAUDE\.md`?( §)? Role [123]\|Role [123] below\|CLAUDE\.md` owns who does what' --include='*.md' .`, excluding `docs/archive/` and this spec, returns zero hits |
| AC11.1 | `pytest` and `pytest automation/` report the same passed, failed and skipped counts as at the start of the branch, since no application code changes | Both suites run at close-out and compared against the baseline in §6 |

## 6. Test plan

- **Baseline before this work**, recorded at `6a2781b` when the branch was cut: `pytest` 1155 passed, 0 failed, 0 skipped; `pytest automation/` 58 passed, 0 failed, 0 skipped.
- **Expected after:** identical, and no test is added. No file under `tests/`, `automation/`, `workmain/` or `templates/` changes. `e5727c5` changes `config/ai_settings.json`, which six tests read directly (Decision Log, 20261008); the suites at `a415051`, after that commit, report the baseline counts, so the provider switch moves no count.

## 7. Risks and rollback

- **Every board item is a parent with open children.** Read 1 then finds no item. The run emits `none` for the item and lists the parents it passed over; it does not fall back to the first parent.
- **Live `config/` edits fail Anvil's clean-tree read.** Ray's working-tree edits to `config/ai_settings.json` are listed as a discrepancy. The discrepancy is reported, not resolved; Role 3 decides from there.
- **Rollback:** one commit per step, reverted newest first. Revert Step 4 before Step 3: Step 4's citations point at `SKILL.md` § THREE-ROLE MODEL, which Step 3 created, so reverting Step 3 first leaves them pointing at nothing. Steps 1 and 2 add new files only and revert last.
