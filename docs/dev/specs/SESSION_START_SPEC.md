# Session-Start Skill — Spec

**Status:** Draft
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

---

## 1. Scope

**In scope:** four new files — `.claude/skills/session-start/SKILL.md` and `references/spanner.md`, `references/caliper.md`, `references/anvil.md` — plus this spec and its results artifact.

**Out of scope:**

- Enforcing that a session is in a role — the issue's own exclusion.
- Any edit to `CLAUDE.md`, `docs/DEVELOPMENT_STANDARDS.md` (including §2.7) or the `closeout` skill. The skill cites them; it changes none of them.
- Session close. `/closeout` covers an issue's close; a per-session close summary is not in #85.
- Any write by the skill. Every source it names is read-only; it creates no branch, file, commit or GitHub object.

## 3. Design rules

- **DR1 — Refuse before reading.** The first thing a run does is validate its arguments. No tool call precedes it.
- **DR2 — Named sources only.** A run reads the sources its reference names, in the order named, and emits only what they carry. A source that cannot be read is reported unreadable; nothing is reconstructed in its place.
- **DR3 — Cite, never copy.** Every role definition, rule and command another document owns is cited by its section. No file in the skill enumerates or counts a set `CLAUDE.md` or `docs/DEVELOPMENT_STANDARDS.md` owns.
- **DR4 — Common once.** What holds for all three roles lives in `SKILL.md`; a reference carries only its role's target, reads and emits.
- **DR5 — Same inputs, same run.** Identical arguments against identical repository and GitHub state produce identical output. No editorial commentary and no closing summary.

Anything not covered: `CLAUDE.md` § Role 3 — stop and surface to Ray.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Write `SKILL.md` with the exact text below. Commit `chore(skills): add the session-start skill entry point`. | `.claude/skills/session-start/SKILL.md` |
| 2 | Write the three references with the exact text below. Commit `chore(skills): add the session-start role references`. | `.claude/skills/session-start/references/{spanner,caliper,anvil}.md` |
| 3 | Write the results artifact from `docs/dev/results/_TEMPLATE_RESULTS.md`: the §5 AC table, the output of each Ray-invoked run named in AC4.1–AC6.1, the AC7.1 count comparison, and the suite counts. Commit `docs(results): record the session-start skill results for issue #85`. | `docs/dev/results/SESSION_START_RESULTS.md` |

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

1. **The item.** With a target, the item is that issue; skip to read 2. Without one, run the board read in `docs/DEVELOPMENT_STANDARDS.md` §1.6 exactly as written there. Walk the result in board order: for each item, read `gh issue view <N> --json subIssuesSummary`; the item is the first whose `subIssuesSummary.total` equals `subIssuesSummary.completed`. Every item passed over is a parent with open children.
2. `gh issue view <N> --json number,title,state,body,labels,milestone,parent,subIssuesSummary`
3. `gh api repos/{owner}/{repo}/issues/<N>/dependencies/blocked_by --jq '.[] | "#\(.number) \(.state) \(.title)"'`
4. `grep -lE '^\*\*Originating item:\*\* .*Issue #<N>([^0-9]|$)' docs/dev/design/*.md docs/dev/specs/*.md`, and the `**Status:**` and `**Branch:**` lines of each file found.
5. `git branch --list '*/issue-<N>-*'`

## Emits

- **Item** — number, title, state, milestone, labels, parent. Without a target, also each parent passed over in read 1.
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

Findings against the review criteria `CLAUDE.md` § Role 2 carries, one row per finding, shaped as a row of the spec's Decision Log:

`| <YYYYMMDD> | Caliper | <criterion number>: <finding, with the evidence that grounds it> | |`

The Resolution column is left empty. With no finding, the run emits `No findings.` and nothing else. No other commentary.
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

### Authorization points

None. The merge to `main` belongs to `/closeout`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | One skill exists, with exactly one reference per role and no separate per-role skill | `ls .claude/skills/ .claude/skills/session-start/ .claude/skills/session-start/references/` shows `closeout` and `session-start` only, `SKILL.md` and `references/`, and exactly `anvil.md caliper.md spanner.md` |
| AC2.1 | The requirements common to all three roles — the read-only property, Step 0's refusal, the four run rules and the reference dispatch — are stated in `SKILL.md` and in no reference | Stated reading by Ray of `SKILL.md` and the three references, for any common rule appearing in a reference |
| AC3.1 | Each reference names its target, the sources it reads in numbered order, and what the run emits | Stated reading by Ray of the three references, for whether each run's reads and output can be told without running it |
| AC4.1 | A run emits state assembled only from its reference's named sources, with nothing a source carries reconstructed | Ray invokes `/session-start Spanner`, `/session-start Caliper docs/dev/specs/SESSION_START_SPEC.md` and `/session-start Anvil docs/dev/specs/SESSION_START_SPEC.md` against the live repository; each output is recorded in the results artifact with the reads the run made |
| AC5.1 | The skill stops before reading any source when the role is absent or unknown, or when Caliper or Anvil has no spec path | Ray invokes `/session-start`, `/session-start Hammer` and `/session-start Caliper`; the results artifact records for each that the output is the usage line and that no tool call preceded it |
| AC6.1 | `Spanner` with no target reports the next open item from the board; with an issue number it opens on that item | Ray invokes `/session-start Spanner` and `/session-start Spanner 85`; both outputs are recorded in the results artifact |
| AC7.1 | The queue read the Spanner reference cites passes an explicit `--limit` above the current open-issue count, so the default of 30 cannot truncate the board | Read the `--limit` in the `docs/DEVELOPMENT_STANDARDS.md` §1.6 command that `references/spanner.md` cites, and compare it against `gh issue list --state open --limit 300 --json number --jq length`; both values are recorded in the results artifact |
| AC8.1 | Each reference cites its own role's section of `CLAUDE.md` — Role 1 from Spanner, Role 2 from Caliper, Role 3 from Anvil | `grep -n 'CLAUDE.md. § Role' .claude/skills/session-start/references/*.md` shows `Role 1` in `spanner.md`, `Role 2` in `caliper.md` and `Role 3` in `anvil.md` |
| AC9.1 | No file in the skill restates the three-role model, a role's duties, the review criteria, or any rule `CLAUDE.md` or `docs/DEVELOPMENT_STANDARDS.md` owns; each is cited by section | Stated reading by Ray of the four files against `CLAUDE.md`'s opening single-home rule |
| AC10.1 | No file in the skill enumerates or counts a set `CLAUDE.md` owns | `grep -rniE 'criteri\|role model\|Role [123]\|duties' .claude/skills/session-start/` and a stated reading by Ray that every hit is a citation, not a list or a count |
| AC11.1 | `pytest` and `pytest automation/` report the same passed, failed and skipped counts as at the start of the branch, since no application code changes | Both suites run at close-out and compared against the baseline in §6 |

## 6. Test plan

- **Baseline before this work**, recorded at `6a2781b` when the branch was cut: `pytest` 1155 passed, 0 failed, 0 skipped; `pytest automation/` 58 passed, 0 failed, 0 skipped.
- **Expected after:** identical. No file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes, so no test is added.

## 7. Risks and rollback

- **The board's top item is a parent.** Board order puts #80 above its own children today. Read 1's skip-parents rule is what keeps a no-target run from reporting a parent as the next work. If that rule is rejected, a no-target run reports #80.
- **Live `config/` edits fail Anvil's clean-tree read.** Ray's working-tree edits to `config/ai_settings.json` are listed as a discrepancy. The discrepancy is reported, not resolved; Role 3 decides from there.
- **Rollback:** each step is one commit touching only new files; `git revert` of either removes it with no other effect.
