# Cycle Process Corrections — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261008
**Branch:** `chore/issue-180-cycle-process-corrections`
**Target release:** n/a — `chore/*`
**Originating item:** Issue #180
**Design study:** `../design/DESIGN_CYCLE_PROCESS_CORRECTIONS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261008 | Ray | Q1: a change the CLI writes to tracked files during live use is committed as one commit on the next branch to be completed, of any type. Neither a `chore/*` branch nor a commit to `dev` handles a change made while another branch is checked out. | DR1; Step 1. |
| 20261008 | Ray | Q2: accept the stage done-condition table, including the `No findings.` Caliper row and `Active` in the results template header. | DR2; Steps 3–4. |
| 20261008 | Ray | Q3: the handoff is the spec path and nothing more; the spec speaks for itself. | DR3; Step 5. |
| 20261008 | Ray | Spec approved; no Role 2 pass, which the direct path leaves to Ray's discretion (`docs/DEVELOPMENT_STANDARDS.md` §1.2). | Status `Approved`. |
| 20261008 | Ray | When no branch type is stated, the Spanner run recommends one rather than stopping blank, so Ray isn't argued from a hotfix into a feature. The recommendation follows §2.2's test: `chore/*` for `chore/*`-only scope, otherwise `hotfix/*` unless the issue shows a §2.2 escalation trigger. Amends the approved spec. | Step 4 Next stage text; AC3.6. AC3.2 narrowed to stage judgement, since the branch-type recommendation now cites §2.2. |
| 20261008 | Spanner | Role 3 has to cite a rule that an AC whose check names Ray is Ray's sign-off, and no live document states one. It was the cause of the #179 close-out stop. It is added to §1.2, next to the stated-reading rule it completes, so Role 3 has something to cite. | DR3; Step 3. |

---

## 1. Scope

**In scope:**

- `docs/DEVELOPMENT_STANDARDS.md`:
  - §1.1: done conditions.
  - §1.2: Ray-owned checks.
  - §2.2: operational changes.
  - §2.8: cite the operational-change exception.
- `docs/dev/specs/_TEMPLATE_SPEC.md` and `docs/dev/design/_TEMPLATE_DESIGN.md`: the `**Originating item:**` placeholder.
- `docs/dev/results/_TEMPLATE_RESULTS.md`: the `**Status:**` placeholder.
- `.claude/skills/session-start/references/spanner.md`: read 4, and the Next stage line under Emits.
- `.claude/skills/session-start/references/caliper.md`: how a clean pass is emitted.
- `.claude/skills/session-start/SKILL.md`: the handoff subsection, and the Role 1 and Role 3 citations of it.

**Out of scope:**

- Moving CLI-written state out of git (design study, Item 1 Option C). That's application work, and Ray chose the exception instead.
- `/closeout` preflight. P5 already accepts any §1.5 status on a results artifact, and P11 checks only version, changelog and tag, so neither needs a change.
- `CLAUDE.md`. Its § THREE-ROLE MODEL is already a pointer, and the operational-change rule's home is `docs/DEVELOPMENT_STANDARDS.md` §2.2.
- Handoffs other than Spanner→Anvil, which #180 does not ask for.

## 3. Design rules

- **DR1 — One home for the operational-change rule.** It is stated in §2.2. §2.8 cites it; nothing else restates it.
- **DR2 — §1.1 owns what shows each stage done.** `spanner.md` judges its Next stage by §1.1 alone and cites no template.
- **DR3 — The handoff carries no instruction.** `SKILL.md` § Spanner → Anvil handoff defines it, and Role 1 and Role 3 cite it. What every implementation owes regardless of spec is cited from Role 3 to its home section, never restated.

Anything this spec doesn't cover stops and goes to Ray.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Operational-change exception | `docs/DEVELOPMENT_STANDARDS.md` |
| 2 | Template `Originating item` placeholders | `docs/dev/specs/_TEMPLATE_SPEC.md`, `docs/dev/design/_TEMPLATE_DESIGN.md` |
| 3 | Done conditions, Ray-owned checks, results template status | `docs/DEVELOPMENT_STANDARDS.md`, `docs/dev/results/_TEMPLATE_RESULTS.md` |
| 4 | Spanner and Caliper references | `.claude/skills/session-start/references/spanner.md`, `.claude/skills/session-start/references/caliper.md` |
| 5 | Spanner → Anvil handoff | `.claude/skills/session-start/SKILL.md` |
| 6 | Results artifact | `docs/dev/results/CYCLE_PROCESS_CORRECTIONS_RESULTS.md` |

### Step 1 — Operational-change exception

In `docs/DEVELOPMENT_STANDARDS.md` §2.2, insert after the line `- Scope: One tightly-related set of files edited for a single reason.` and before `**hotfix/* → feature/* exception.**`:

```markdown
**Operational changes from live use.**

- WorkmAIn is in daily use while it is developed, and some `workmain` commands write tracked files as part of normal operation — `workmain providers set default`, for example, writes `config/ai_settings.json`. The change appears uncommitted on whichever branch is checked out, and is not part of that branch's work.
- It is committed on the next branch to be completed, of any type, before `/closeout` runs: one commit, separate from the branch's own work, typed `chore(config)` or `chore(templates)`, whose body states that it is an operational change made through the CLI.
- It needs no spec and no acceptance criterion, is not scope of the issue the branch serves, and does not count toward the `hotfix/*` file limit.
- It does not change whether the merge is a release: a `chore/*` merge carrying it is still not one, and a `feature/*` or `hotfix/*` merge is released as it would be without it.
- It covers only a file a `workmain` command wrote. A hand edit to `config/` or `templates/` is development, and takes the branch its change requires.
```

In §2.8, replace:

```markdown
- Use `chore/*` for application code, `config/*`, `templates/*`, `tests/**`, or `CHANGELOG.md` — except under the `chore/*` exception in §2.2.
```

with:

```markdown
- Use `chore/*` for application code, `config/*`, `templates/*`, `tests/**`, or `CHANGELOG.md` — except under the `chore/*` exception or the operational-change exception in §2.2.
```

### Step 2 — Template placeholders

In both `docs/dev/specs/_TEMPLATE_SPEC.md` and `docs/dev/design/_TEMPLATE_DESIGN.md`, replace:

```markdown
**Originating item:** Backlog Item #N | Ray request, YYYYMMDD
```

with:

```markdown
**Originating item:** Issue #N | Ray request, YYYYMMDD
```

### Step 3 — Done conditions, Ray-owned checks, results status

In `docs/DEVELOPMENT_STANDARDS.md` §1.1, insert after the paragraph that begins `**What the direct path trades.**` and before `### 1.2 Spec authoring rules`:

```markdown
**What shows each stage done.** Each stage is done when its artifact or field shows it, and not before. A stage on both paths has the same condition on each.

| Stage | Done when |
| --- | --- |
| Recon | A `docs/dev/design/` artifact names the issue in its `**Originating item:**` field. |
| Analysis | Every row of that artifact's §5 Open questions carries an answer. |
| Spec | A `docs/dev/specs/` artifact names the issue in its `**Originating item:**` field. |
| Review | The spec's Decision Log carries at least one `Caliper` row, and every `Caliper` row has a resolution. A clean pass is the `No findings.` row `/session-start Caliper` emits for one. |
| Approval | The spec's `**Status:**` is `Approved`. |
| Implementation | A results artifact in the `results/` directory beside the spec names it in its `**Spec:**` field. The implementing role writes it as its last implementation step. |
| Close-out | The spec's `**Status:**` is `Shipped`, and the artifact set is in `docs/archive/`. |
```

In §1.2, replace:

```markdown
- **Where a criterion is a property of a document rather than of running code, the check may be a stated reading by Ray.** It is still a check, and it still names what is being read: the section, and what the reader is reading it for. `docs/dev/specs/_TEMPLATE_SPEC.md` §5 states the same and cites here.
```

with:

```markdown
- **Where a criterion is a property of a document rather than of running code, the check may be a stated reading by Ray.** It is still a check, and it still names what is being read: the section, and what the reader is reading it for. `docs/dev/specs/_TEMPLATE_SPEC.md` §5 states the same and cites here.
  - **A check that names Ray is Ray's sign-off.** The implementer records its results row as `Not met`, with `Awaiting Ray` as its evidence, never `Met` on its own reading or run. Ray changes the row once he has checked it.
```

In `docs/dev/results/_TEMPLATE_RESULTS.md`, replace:

```markdown
**Status:** Shipped | Superseded
```

with:

```markdown
**Status:** Active | Shipped | Superseded
```

### Step 4 — Spanner and Caliper references

In `.claude/skills/session-start/references/spanner.md`, replace read 4:

```markdown
4. `grep -lE '^\*\*Originating item:\*\* .*Issue #<N>([^0-9]|$)' docs/dev/design/*.md docs/dev/specs/*.md`, and the `**Status:**` and `**Branch:**` lines of each file found. For each spec found, `grep -l '^\*\*Spec:\*\* .*<spec file name>' docs/dev/results/*.md` and the `**Status:**` line of each file found.
```

with:

```markdown
4. `grep -lE '^\*\*Originating item:\*\* .*Issue #<N>([^0-9]|$)' docs/dev/design/*.md docs/dev/specs/*.md docs/archive/design/*.md docs/archive/specs/*.md`, and the `**Status:**` and `**Branch:**` lines of each file found. For each design study found, its §5 Open questions table. For each spec found, its Decision Log rows whose Source is `Caliper`, and `grep -l '^\*\*Spec:\*\* .*<spec file name>'` over the `results/` directory beside it, with the `**Status:**` line of each file found.
```

Replace the Next stage line under Emits:

```markdown
- **Next stage** — the first stage on the item's `docs/DEVELOPMENT_STANDARDS.md` §1.1 path that the artifacts found do not show done, judged by §1.1 for which artifact each stage produces, §1.2 for review before approval, §1.5 for the spec's `Status:`, and `docs/dev/results/_TEMPLATE_RESULTS.md` §3 for the results artifact as the last implementation step. The path is the branch type a found spec's `**Branch:**` field or the issue body states; where neither states one, say so and name the first stage of each path.
```

with:

```markdown
- **Next stage** — the first stage on the item's `docs/DEVELOPMENT_STANDARDS.md` §1.1 path that §1.1's done conditions, applied to the artifacts found, do not show done. The path is the branch type a found spec's `**Branch:**` field or the issue body states. Where neither states one, name the recommended branch type by `docs/DEVELOPMENT_STANDARDS.md` §2.2 — `chore/*` where the issue names only what §2.2's `chore/*` block covers; otherwise `hotfix/*` over `feature/*` unless the issue shows an escalation trigger §2.2 names, and which one — and the first stage of that path. The recommendation is Ray's to confirm before any branch is cut.
```

In `.claude/skills/session-start/references/caliper.md`, replace:

```markdown
With no finding, the run emits `No findings.` and nothing else. No other commentary.
```

with:

```markdown
With no finding, the run emits the same table with one row, `| <YYYYMMDD> | Caliper | No findings. | n/a |`, and nothing else. No other commentary.
```

### Step 5 — Spanner → Anvil handoff

In `.claude/skills/session-start/SKILL.md` § Role 1, after the bullet `- Resolves conflicts in design and project documentation during planning, so they never reach implementation. Ray is the final authority on all documentation changes.`, insert:

```markdown
- Hands each approved full-path spec to Anvil as § Spanner → Anvil handoff states.
```

In § Role 3, after the paragraph `Works from approved specs only. Read the full spec end to end, cross-check and validate all references, and report discrepancies before touching step 1.`, insert:

```markdown
Receives work as § Spanner → Anvil handoff states. Every implementation owes the following, whether or not the spec repeats it:

- a commit at the end of each step — `docs/DEVELOPMENT_STANDARDS.md` §1.4
- the results artifact as the last implementation step, with test counts in the form §6 states and every check that names Ray left to him — §1.1 § What shows each stage done, §1.2
- no merge, version bump or restart; those are close-out's — §1.1
```

After § Role 3's last paragraph, which begins `**Choosing the cheapest way to turn an acceptance criterion green is a design decision.**`, append:

```markdown
### Spanner → Anvil handoff

On the full path, Spanner hands an approved spec to Anvil as `/session-start Anvil <spec path>`, and nothing else. The spec is the whole instruction. Anything Anvil needs that the spec doesn't say is a defect in the spec, and it is fixed there, never carried in the prompt. A prompt that restates the spec is a second statement of it, and the two can disagree. The direct path has no handoff — `docs/DEVELOPMENT_STANDARDS.md` §1.1.
```

### Step 6 — Results artifact

Write `docs/dev/results/CYCLE_PROCESS_CORRECTIONS_RESULTS.md` from `_TEMPLATE_RESULTS.md`, `**Status:** Active`. Every AC whose check names Ray is recorded `Not met` with `Awaiting Ray`, per the Step 3 §1.2 rule.

### Authorization points

None. The merge to `main` belongs to `/closeout`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | An operational change the CLI makes during live use has one stated rule, giving the branch it is committed on and whether that merge is a release. | A stated reading by Ray of `docs/DEVELOPMENT_STANDARDS.md` §2.2 § Operational changes from live use, for the branch it names and its release statement |
| AC1.2 | The rule is stated only in §2.2. Every other process document cites it rather than restating it. | `grep -rn 'Operational changes from live use\|operational-change exception' CLAUDE.md docs/DEVELOPMENT_STANDARDS.md .claude docs/dev/*/_TEMPLATE_*.md` returns the §2.2 heading and the §2.8 citation, and nothing else |
| AC2.1 | An artifact filled in from either template names its issue in the form the `/session-start Spanner` artifact read matches. | `grep -n 'Originating item' docs/dev/specs/_TEMPLATE_SPEC.md docs/dev/design/_TEMPLATE_DESIGN.md` shows `Issue #N` in both and `Backlog Item` in neither |
| AC3.1 | §1.1 states, for every stage of both paths, the artifact or field that shows the stage done. | A stated reading by Ray of `docs/DEVELOPMENT_STANDARDS.md` §1.1 § What shows each stage done, for a condition on every stage named in the full-path and direct-path diagrams |
| AC3.2 | The Spanner reference judges which stage is next by §1.1 alone, citing no artifact template, §1.2 or §1.5. | `grep -nE '_TEMPLATE_RESULTS\|§1\.[25]' .claude/skills/session-start/references/spanner.md` returns zero hits |
| AC3.3 | Each artifact the done conditions inspect is readable through a Spanner read: design study §5, spec Decision Log `Caliper` rows, and results artifacts, in both live and archive roots. | A stated reading by Ray of `.claude/skills/session-start/references/spanner.md` read 4 against the §1.1 done-condition table |
| AC3.6 | With no branch type stated, the Spanner run recommends one by §2.2's test, preferring `hotfix/*` to `feature/*` unless the issue shows a named escalation trigger. | A stated reading by Ray of `.claude/skills/session-start/references/spanner.md` § Emits, Next stage |
| AC3.4 | A clean Caliper pass leaves a Decision Log row, so a reviewed spec is distinguishable from an unreviewed one. | `grep -n 'No findings' .claude/skills/session-start/references/caliper.md` shows the one-row table form |
| AC3.5 | The results template offers the status an implementer writes at implementation time. | `grep -n '^\*\*Status:\*\*' docs/dev/results/_TEMPLATE_RESULTS.md` shows `Active` |
| AC4.1 | What a Spanner→Anvil handoff contains is stated in one place, and the Spanner and Anvil role definitions cite it rather than restate it. | A stated reading by Ray of `.claude/skills/session-start/SKILL.md` § Spanner → Anvil handoff, § Role 1 and § Role 3 |
| AC4.2 | Role 3 cites every obligation an implementation owes regardless of spec — the per-step commit, the results artifact, test-count form, Ray-owned checks, and close-out's ownership of merge and restart — from its home section. | A stated reading by Ray of `.claude/skills/session-start/SKILL.md` § Role 3, for a citation of each, with `docs/DEVELOPMENT_STANDARDS.md` §1.2 stating the Ray-owned rule |

## 7. Risks and rollback

Documents and skill references only. Each step is its own commit and reverts on its own. The risk is a new contradiction with text this spec didn't find. Step 1's rule and Step 3's table are new statements, and the AC1.2 grep covers only the first.
