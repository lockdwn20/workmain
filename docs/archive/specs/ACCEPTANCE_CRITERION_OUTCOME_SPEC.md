# An acceptance criterion names an outcome, not the command that checks it — Spec

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20260901
**Branch:** `chore/issue-118-acceptance-criterion-outcome`
**Target release:** n/a — `chore/*` carries no version bump, no tag and no Release (`docs/DEVELOPMENT_STANDARDS.md` §2.2)
**Originating item:** Issue #118
**Design study:** n/a — direct path, no recon was run

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260901 | Spanner | The worked pair in §1.2 needs a concrete example. Issue #118's own illustration is #101's AC1, whose command returns hits today (`workmain/daemon/daemon.py:427`) because the state moved to `workmain/daemon/conversation_state.py` and the call sites kept the word — a reader who ran it would read the example as broken | Use the retired file-version-header rule instead: currently true, runnable, and its gaming path is self-evident |
| 20260901 | Spanner | Issue #118 states that splitting `acs` into structured objects "is recorded as a follow-up". No such issue exists — `gh issue list --state all` returns nothing for it | Out of scope here. Raised to Ray; if he wants it tracked it is opened at close-out and placed on the board by him |
| 20260902 | Third-party review | This spec's first draft claimed in this log that grep had found every live site stating or citing the acceptance-criteria rule. It had not: it missed `CLAUDE.md`'s opening single-home rule, which DR1 and AC5.1 both depend on, and `docs/dev/specs/_TEMPLATE_SPEC.md:82`. §1.1 names this exact case — a rule stated in one place and cited in others — as where a recon earns its place on the direct path | Claim withdrawn, not repaired. The census the review produced is recorded in § 1 Out of scope. No recon artifact is written after the fact; `**Design study:**` stays `n/a`, and the sweep's provenance is this row |
| 20260902 | Third-party review | Five of this spec's ACs are checked by a stated reading by Ray. §1.2 as it stands requires every criterion to be mechanically testable with no carve-out, so Caliper's question 1 has five correct answers on this spec. The permission exists only in `docs/dev/specs/_TEMPLATE_SPEC.md` §5, which is advisory and explicitly not a Caliper criterion — and §5 cites §1.2 for a rule §1.2 does not contain (`_TEMPLATE_SPEC.md:75`, `:82`) | Taken as scope, in the section already being edited. Step 1 gains a fourth bullet giving §1.2 the carve-out it is already credited with. **This is scope no acceptance criterion on issue #118 named** — it is here because without it the spec cannot state its own criteria, and the alternative is a second issue this one would have to wait on. AC9.1 covers it; Ray strikes it at approval if he wants it split out |
| 20260902 | Third-party review | Question 7 as first drafted cited nothing, which DR1 requires of it. Separately the review suggested restoring a second sentence — "Name the cheaper wrong implementation for each" — said to be in the issue's version | Citation added. The second sentence is **not taken**: issue #118 carries no such sentence (its AC3 is one sentence plus its check), and Role 2's other six criteria are each a single question. Naming the cheaper implementation is what the answer to question 7 *is*, not a second instruction |
| 20260902 | Third-party review | AC3.1's check, `grep -c '^[0-9].' CLAUDE.md` returns 11, is anchored to nothing — it counts Role 2's six questions and Role 3's four escalation steps together, so a fifth escalation step satisfies it equally. It is the defect this issue exists to fix, in the spec that introduces the rule | Replaced with a check scoped to the Role 2 block plus an additions-only diff. The hardcoded line range 54–59 is dropped with it: a positional citation goes stale the first time anything above it moves |

---

## 1. Scope

**In scope:**

- `docs/DEVELOPMENT_STANDARDS.md` §1.2 — the wording rule, one worked pair, the statement that it is not retrospective, and the document-criteria carve-out (Decision Log, 20260902).
- `CLAUDE.md` Role 2 — one added review question, appended as item 7.
- `CLAUDE.md` Role 3 — one added clause naming the cheapest-way-versus-purpose choice as a design decision, and therefore a stop under the escalation procedure already stated there.

**Out of scope.** The sites that state or cite the acceptance-criteria rule, and what happens to each:

- `CLAUDE.md` opening preamble, lines 3–7 — the single-home rule DR1 rests on. Cited, not edited.
- `docs/dev/specs/_TEMPLATE_SPEC.md` §5, `:75` and `:82` — the `Criterion` / `How it is checked` columns, and two sentences carving out document criteria and citing §1.2 for them. Both citations resolve once Step 1 lands. The template is not edited.
- `.claude/skills/closeout/SKILL.md` P7, which cites §1.2 for the sub-AC mapping only. The mapping rule is untouched, so the citation stays correct.
- `docs/DEVELOPMENT_STANDARDS.md:42`, which cites §1.2 for what a direct-path spec may omit. Untouched by Step 1, which appends.
- `automation/issue_validator.py`, which parses §1.3, not §1.2. No line it reads is edited. `automation/closeout_acs.py` reads a spec's `**Branch:**` field and AC ids, neither of which changes shape.
- `.github/ISSUE_TEMPLATE/issue.schema.json`. `acs` stays `array of string`; the distinction is carried inside the string. Structured AC objects are the follow-up recorded in the Decision Log.
- Acceptance criteria on issues already open or closed. They are not rewritten, and no issue is reopened to reword them.
- Any file under `workmain/`, `tests/`, `automation/`, `config/` or `templates/`.

## 2. Verified current state

Omitted — direct path (`docs/DEVELOPMENT_STANDARDS.md` §1.2). Each step below quotes the text it replaces, which is the verification.

## 3. Design rules

- **DR1 — One home each.** §1.2 owns how a criterion is worded. The Role 2 question owns the review-time check. The Role 3 clause owns the implementation-time stop. None restates another in full, and each cites the one it depends on. The single-home rule itself lives in `CLAUDE.md`'s opening preamble.
- **DR2 — Additions only.** Step 1 appends after the existing §1.2 bullet; that bullet is not reworded. No existing Role 2 question is reworded, renumbered or reordered, and Role 3's four escalation steps are not reworded or renumbered — the new clause routes into them. AC3.1 depends on this.
- **DR3 — The rule is prospective.** §1.2 says so in its own text. Nothing in this spec touches an existing acceptance criterion anywhere.
- **DR4 — The worked pair must be runnable, and its property must be true, not merely its command green.** An example a reader runs and sees fail teaches the opposite of the rule; an example whose command passes over a property that is false teaches the opposite while passing. The property and the check are narrowed together to the set the check actually covers.
- Anything this spec does not cover: `CLAUDE.md` Role 3 escalation procedure.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | §1.2 wording rule, worked pair, prospective-scope statement, document-criteria carve-out | `docs/DEVELOPMENT_STANDARDS.md` |
| 2 | Role 2 question 7 and the Role 3 clause | `CLAUDE.md` |
| 3 | Results artifact, `**Status:** Active`, §3 filled from the run | `docs/dev/results/ACCEPTANCE_CRITERION_OUTCOME_RESULTS.md` |

### Step 1 — `docs/DEVELOPMENT_STANDARDS.md` §1.2

Text as it stands today, one bullet, unchanged by this step:

```markdown
- Acceptance criteria must be mechanically testable. If an AC cannot be checked by running something, rewrite it until it can.
```

Three bullets are inserted directly after it:

```markdown
- **A criterion names a property of the delivered system. The command is evidence for that property, not the criterion itself.** Write it as "*<property>*, checked by `<command>`" — not as "`<command>` returns zero hits" standing alone. A command is a proxy, and a proxy has many ways to read green, only one of which is the change that was wanted. Naming the property is what tells a reviewer, and an implementer, which of those ways is the work.
  - The same criterion, written both ways:
    - **Check as the criterion:** `grep -rn '^Version:' workmain/ --include='*.py'` returns zero hits.
    - **Property, with the check as evidence:** no Python module under `workmain/` carries a version header in its docstring — git is the version record (§3.1) — checked by `grep -rn '^Version:' workmain/ --include='*.py'` returning zero hits.
    - The first is satisfied by renaming the header to `Ver:`. The second is not, and the difference is readable at review time, before any code exists.
  - `docs/dev/specs/_TEMPLATE_SPEC.md` §5 carries the two as separate columns, `Criterion` and `How it is checked`. On an issue, where `.github/ISSUE_TEMPLATE/issue.schema.json` types an acceptance criterion as one string, the wording is what carries that separation instead.
- **Where a criterion is a property of a document rather than of running code, the check may be a stated reading by Ray.** It is still a check, and it still names what is being read: the section, and what the reader is reading it for. `docs/dev/specs/_TEMPLATE_SPEC.md` §5 states the same and cites here.
- **The wording rule applies to criteria authored from here forward.** Criteria already written are not rewritten and no issue is reopened to reword one; there is no retrospective sweep of the queue.
```

### Step 2 — `CLAUDE.md`

Role 2, appended below existing question 6. Questions 1 to 6 are unchanged in wording and order:

```markdown
7. Which acceptance criteria could be satisfied by a change that does not achieve what the criterion is for? — how a criterion is worded so that difference is visible: `docs/DEVELOPMENT_STANDARDS.md` §1.2.
```

Role 3, appended below the existing numbered escalation list, as a new paragraph. The four steps are not reworded or renumbered:

```markdown
**Choosing the cheapest way to turn an acceptance criterion green is a design decision.** Where the least-effort way to satisfy a criterion and the way that achieves what it is for come apart, that is not an implementer's call — it is the case above, and it stops at 1 through 4. How a criterion is worded so the two are distinguishable: `docs/DEVELOPMENT_STANDARDS.md` §1.2.
```

### Authorization points

This spec contains none. `chore/*` carries no migration, no GitHub object deletion, no force-push and no service restart. Close-out's merge to `main` is its own authorization point, taken there and not here (`docs/DEVELOPMENT_STANDARDS.md` §1.4).

## 5. Acceptance criteria

Five criteria below are checked by a stated reading rather than by a command, because what they assert is a property of a document. That form is permitted by the bullet Step 1 adds to §1.2 — this spec is the first artifact to rely on it, as it is the first to be written under the wording rule.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | §1.2 states that a criterion names a property of the delivered system and that the command is evidence for it, giving the form to write and the form not to write | Ray reads §1.2 for that statement |
| AC2.1 | §1.2 carries one worked pair — one criterion in both forms — whose property is true of the tree as it stands and whose command runs green over it | Ray reads §1.2 for both forms; `grep -rn '^Version:' workmain/ --include='*.py'` returns zero hits |
| AC3.1 | Role 2's review criteria include a question asking which criteria could be satisfied without achieving what they are for, and the existing six are unchanged in wording and order | `sed -n '/^### Role 2/,/^### Role 3/p' CLAUDE.md \| grep -c '^[0-9]\.'` returns 7, was 6; `git diff main...HEAD -- CLAUDE.md` shows added lines only, no line removed |
| AC4.1 | Role 3 states that choosing the cheapest way to satisfy a criterion over the way that achieves its purpose is a design decision and therefore a stop under the escalation procedure already stated there | Ray reads Role 3 for that clause |
| AC5.1 | The three additions cite rather than restate each other — §1.2 owns the wording, Role 2 owns the review check, Role 3 owns the implementation stop — and each cites the one it depends on | Ray reads all three against DR1 and `CLAUDE.md`'s opening single-home rule |
| AC6.1 | No acceptance criterion on an existing issue is rewritten and no issue is opened or closed by this work, and §1.2 states the rule is prospective | `gh issue list --state open --limit 300 --json number \| jq length` returns the same count before and after; Ray reads §1.2 for the statement |
| AC7.1 | Every acceptance criterion in this table is written in the form §1.2 now requires — a property, with its check as evidence | Recorded in the results artifact, §3 |
| AC8.1 | No file outside the two documents and this spec's own artifact set is edited | Run before the close-out archive commit, `git diff --name-only main...HEAD` lists exactly four paths: `CLAUDE.md`, `docs/DEVELOPMENT_STANDARDS.md`, `docs/dev/specs/ACCEPTANCE_CRITERION_OUTCOME_SPEC.md` and `docs/dev/results/ACCEPTANCE_CRITERION_OUTCOME_RESULTS.md`. After it, the spec and results paths are their `docs/archive/` equivalents |
| AC8.2 | Both suites pass unchanged at their baselines, since no code is touched | `pytest` returns 972 passed; `pytest automation/` returns 51 passed |
| AC9.1 | §1.2 states that a criterion asserting a property of a document may be checked by a stated reading, naming what is read and what it is read for, and `docs/dev/specs/_TEMPLATE_SPEC.md` §5's two citations to §1.2 resolve to text that is there | Ray reads §1.2 for the statement, then `_TEMPLATE_SPEC.md:75` and `:82` against it |

Issue AC mapping: AC1.1→AC1, AC2.1→AC2, AC3.1→AC3, AC4.1→AC4, AC5.1→AC5, AC6.1→AC6, AC7.1→AC7, AC8.1 and AC8.2→AC8. **AC9.1 maps to no issue AC** — it is the scope addition recorded in the Decision Log, 20260902, and is named here rather than left for Caliper's question 4 to find.

## 6. Test plan

- **Baseline before this work:** 972 passed (`CHANGELOG.md`, v1.31.0) for `pytest`; 51 passed for `pytest automation/`, run at authoring time.
- **Expected after:** unchanged — 972 and 51. No test file is added or edited. Any movement in either number means a file outside § 1 In scope was touched.

## 7. Risks and rollback

- **Blast radius:** two documents. No application behaviour, no schema, no tooling.
- **The rule is advice a reviewer must apply, not a gate.** Issue #118 states the limit: this makes the reviewer's job targeted, it does not remove the incentive to optimise what is measured. If criteria keep arriving in check-only form after this ships, the answer is the structured-`acs` follow-up, not more prose here.
- **A worked pair can go stale.** The pair is true because version headers were retired at v1.29.0 and §3.1 forbids them in a module docstring; if §3.1 changes, the example changes with it. Its `--include='*.py'` narrowing is load-bearing — three files under `workmain/database/migrations/` carry `-- Version:` headers, so the unnarrowed property is false while the unnarrowed command is still green. DR4 is why.
- **Rollback:** `git revert` the step's commit. Each step is one commit against one file.
