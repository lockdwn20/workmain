# Framework Mechanism First — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261014
**Branch:** `chore/issue-221-framework-mechanism-first` (from `main`, merges to `main` and `dev`)
**Target release:** none — `chore/*` carries no version bump, no `CHANGELOG.md` entry, no tag, no Release
**Originating item:** Issue #221
**Design study:** `n/a` — direct path, no recon was run

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261014 | Ray | #221 is a `chore/*` on the direct path, landing before #58 so the pilot and #201–#216 are written and reviewed under the rule. Ray approves the `SKILL.md` wording | Accepted. Branch and path as in the header; the `SKILL.md` wording is quoted in full in §4 step 2 for that approval |
| 20261014 | Spanner | §3.8 names its scope as the Python standard library and the packages `requirements.txt` declares, not the four libraries the issue names (Python, Click, Rich, SQLAlchemy) | A fixed list of four is a hand-maintained copy of the dependency set, and it would leave out APScheduler, slack-sdk, python-dotenv and pytest, which the project already depends on. `requirements.txt` is the declared set, so the rule reads it rather than copying it. The issue's four are all inside that set, so AC1 and AC2 are met as their property reads; the issue's wording is edited to match at close-out |
| 20261014 | Spanner | Caliper's criterion 6 cites §3.8 for what counts as a library mechanism instead of naming the libraries itself | §3.8 is the rule's one home (AC3). A criterion that listed the libraries would be a second statement of the rule's scope. This follows criterion 7, which asks its question and cites §1.2 for the rule behind it |
| 20261014 | Spanner | A spec that writes its own version records the mechanism it set aside in its Decision Log | Choosing not to use the mechanism is a design decision, and the Decision Log is where a spec records one (§1.5). It is the one place Caliper is already reading, so no new template field is created |
| 20261014 | Ray | The first §3.8 draft did not read clearly, its examples did not read as examples, and its reason cited an issue number and a design study no reader outside this session will know | Accepted. §3.8 now gives its reason in plain terms with no issue or study reference, and its examples are a table: the job, the hand-written version, the mechanism to use |
| 20261014 | Spanner | §3.8 does not use `click.ClickException` as an example | `docs/DEVELOPMENT_STANDARDS.md` §5.6's Error row still prescribes `err_console.print(...)` then `sys.exit()`, so that example would contradict a standing rule. Changing §5.6 is #58's work, not #221's |

---

## 1. Scope

**In scope:**

- `docs/DEVELOPMENT_STANDARDS.md` — a new **§3.8 Framework mechanisms first**, appended after §3.7. Every bare `§3.8` in this spec means that new section, which does not exist until step 1 writes it.
- `.claude/skills/session-start/SKILL.md` § Role 2, criterion 6 — extended to ask about a library mechanism and cite §3.8.

**Out of scope:**

- **`SKILL.md` § Role 1 Critical Rule.** It governs choosing a design path against existing services. §3.8 already governs a spec author directly ("a spec that writes its own…"), so a citation there adds no rule and is not something #221 asks for.
- **`CLAUDE.md` § Critical Rules.** Ray approves membership; adding §3.8 there is not part of #221.
- **`docs/dev/specs/_TEMPLATE_SPEC.md`.** No new field. The Decision Log already holds the record (Decision Log row 4).
- **Converting any existing hand-written code.** The seven sites the #58 study found (F3, F5, F19, F23–F26) are #58's and #201–#216's work.
- **`workmain/**`, `tests/**`, `automation/**`, `config/**`.** Untouched, which is what keeps this on `chore/*` under §2.2.

## 3. Design rules

- **DR1 —** The rule is stated once, in §3.8. Every other document that refers to it cites §3.8 and does not restate its scope or its requirement.
- **DR2 —** The rule's scope is derived from `requirements.txt` and the standard library, never listed.
- **DR3 —** Text is applied exactly as quoted in §4. Anything not covered here stops and goes to Ray, per `.claude/skills/session-start/SKILL.md` § Role 3.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps. Implementation is Spanner's, in this session (`docs/DEVELOPMENT_STANDARDS.md` §1.1, direct path).

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | §3.8 Framework mechanisms first | `docs/DEVELOPMENT_STANDARDS.md` |
| 2 | Caliper criterion 6 extended | `.claude/skills/session-start/SKILL.md` |
| 3 | Results artifact | `docs/dev/results/FRAMEWORK_MECHANISM_FIRST_RESULTS.md` |

### Step 1 — §3.8

Insert after §3.7's last bullet (`- Nothing encrypts secrets at rest; `.env` must be `chmod 600`.`) and before the `---` that closes §3:

```markdown

### 3.8 Framework mechanisms first

- Before writing code of your own, check whether Python's standard library or one of the packages in `requirements.txt` already does the job. If one does, use it.
- When a spec writes its own code for a job one of those packages already does, its Decision Log names the package's mechanism and says why it was not used.
- Why: the library's version is already tested and behaves the same way in every command that uses it. Code that does the same job by hand has to get every edge case right by itself, and it often misses some. A number prompt that checks its own bounds can accept `-1`, and Python then reads `-1` as the last item in the list.

Examples:

| Job | Written by hand | Use instead |
| --- | --- | --- |
| Ask for a number between 1 and `n` | A loop that reads the input, converts it and checks the bounds itself | `click.prompt("Select", type=click.IntRange(1, n))` |
| Accept an option from a fixed set of values | An `if value not in (...)` check in the command body | `type=click.Choice([...])` on the option |
| Accept a date | Splitting the string and building a `date` from its parts | `type=click.DateTime(formats=["%Y-%m-%d"])` on the option |
| Print text that may contain `[` | Passing it straight to `console.print`, where Rich reads `[...]` as markup and drops it | `console.print(rich.markup.escape(text))` |
```

### Step 2 — Caliper criterion 6

Replace, in § Role 2:

```markdown
6. Does this spec introduce a new path where an existing service, orchestrator, or workflow already covers the case?
```

with:

```markdown
6. Does this spec introduce a new path where an existing service, orchestrator, or workflow already covers the case, or write its own version of a mechanism `docs/DEVELOPMENT_STANDARDS.md` §3.8 says to use?
```

### Step 3 — Results artifact

`docs/dev/results/FRAMEWORK_MECHANISM_FIRST_RESULTS.md` from `_TEMPLATE_RESULTS.md`, recording each AC in §5 below. All three are Ray's checks and are recorded `Not met` / `Awaiting Ray` (§1.2).

### Authorization points

None. No migration, no GitHub object deleted, no merge to `main`, no force-push, no service run-state change. The merges are `/closeout`'s.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | §3.8 tells an author to use the mechanism the standard library or a package `requirements.txt` declares provides before writing their own, and requires a spec that writes its own to name, in its Decision Log, the mechanism it set aside and why | A stated reading by Ray of `docs/DEVELOPMENT_STANDARDS.md` §3.8, for both requirements |
| AC2.1 | Caliper's criterion 6 asks whether a spec writes its own version of a mechanism §3.8 governs, as well as whether it bypasses an existing service, orchestrator or workflow | A stated reading by Ray of `.claude/skills/session-start/SKILL.md` § Role 2 criterion 6 |
| AC3.1 | The rule is stated only in §3.8; every other mention in the standards, the skills and `CLAUDE.md` is a citation of §3.8 | `git grep -n -iE 'framework\|mechanism\|§3\.8' -- docs/DEVELOPMENT_STANDARDS.md .claude CLAUDE.md`, which returned nothing on `main` at authoring, now returns only lines inside §3.8 and `SKILL.md` criterion 6, read by Ray |

## 6. Test plan

Omitted: no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes (`_TEMPLATE_SPEC.md`, direct path). Close-out runs the suites regardless.

## 7. Risks and rollback

| Risk | Mitigation |
| --- | --- |
| §3.8 is read as forbidding any helper | Its requirement is conditional on a provided mechanism, and the remedy is a Decision Log row, not a ban |
| A dependency is removed from `requirements.txt` | §3.8 reads the file, so the rule's scope follows it with no edit |

Rollback: revert the step commits. Both edits are additive text in two documents.
