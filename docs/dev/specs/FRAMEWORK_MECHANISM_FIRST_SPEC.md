# Framework Mechanism First — Spec

**Status:** Shipped
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
| 20261014 | Spanner | §3.8 names its scope as the Python standard library and the packages `requirements.txt` declares, not the four libraries the issue names (Python, Click, Rich, SQLAlchemy) | A fixed list of four is a hand-maintained copy of the dependency set, and it would leave out APScheduler, slack-sdk, python-dotenv and pytest, which the project already depends on. `requirements.txt` is the declared set, so the rule reads it rather than copying it. **Withdrawn** after Caliper's review. The wider set also brought in packages that conflict with §5.6 (`tabulate` against `rich.Table`) or with each other (`requests` and `httpx`), and dev tooling and deferred-phase packages that no command uses. §3.8 names the four; the issue's wording stands |
| 20261014 | Spanner | Caliper's criterion 6 cites §3.8 for what counts as a library mechanism instead of naming the libraries itself | §3.8 is the rule's one home (AC3). A criterion that listed the libraries would be a second statement of the rule's scope. This follows criterion 7, which asks its question and cites §1.2 for the rule behind it |
| 20261014 | Spanner | A spec that writes its own version records the mechanism it set aside in its Decision Log | Choosing not to use the mechanism is a design decision, and the Decision Log is where a spec records one (§1.5). It is the one place Caliper is already reading, so no new template field is created |
| 20261014 | Ray | The first §3.8 draft did not read clearly, its examples did not read as examples, and its reason cited an issue number and a design study no reader outside this session will know | Accepted. §3.8 now gives its reason in plain terms with no issue or study reference, and its examples are a table: the job, the hand-written version, the mechanism to use |
| 20261014 | Spanner | §3.8 does not use `click.ClickException` as an example | `docs/DEVELOPMENT_STANDARDS.md` §5.6's Error row still prescribes `err_console.print(...)` then `sys.exit()`, so that example would contradict a standing rule. Changing §5.6 is #58's work, not #221's |
| 20261014 | Caliper | 3: §3.8 does not say what to do when two in-scope mechanisms both do the job — `tabulate` against §5.6's `rich.Table`, `requests` against `httpx`, `datetime.strptime` (27 command sites) against the table's `click.DateTime` | Accepted. The scope goes back to the four (row 2), which removes `tabulate`, `requests` and `httpx`. §3.8 now says any of their mechanisms meets the rule unless another section names one, so `strptime` meets it and §5.6's `rich.Table` still governs. The date example is now `date.fromisoformat` |
| 20261014 | Caliper | 4: row 2 widens the scope Ray decided, with no Ray row approving it, and plans to edit the issue's AC wording | Withdrawal accepted, on finding 3's grounds; the issue is not edited. **The authority claim is not taken** — scoping the rule was Spanner's call to make (Ray, 20261014) |
| 20261014 | Caliper | 1/7: AC3.1's `\|` is a literal pipe in the raw file, so the grep matches nothing whatever the files hold; and a word search cannot see the rule restated in other words | Accepted. The grep uses `-e` per term, with no pipe. The check adds the branch diff, which is what shows this change put the rule nowhere but §3.8 and criterion 6 |
| 20261014 | Caliper | 2: the Why bullet says `-1` selects the last item; the code it describes indexes `matches[choice - 1]`, so `-1` selects the second-to-last | Accepted. The Why bullet now says a negative number counts from the end of the list, which holds for any index arithmetic |
| 20261014 | Caliper | 2: `click.DateTime` returns `datetime.datetime`, not `date`, so it is not a drop-in replacement for code that builds a `date` | Accepted. The row now uses `date.fromisoformat(value)`, which returns a `date` |
| 20261014 | Caliper | 2: the out-of-scope bullet calls seven findings "seven sites", and cites a study that exists only on the #58 branch | Accepted. The bullet no longer counts or cites the study |
| 20261014 | Ray | §3.8 wording supplied by Ray: the four libraries, bold rule statements, the reason stated without a label, the `-1` case moved into the prompt example's row, and the markup-escape row replaced by a `pathlib` row | Accepted. Step 1 quotes it verbatim |
| 20261014 | Ray | **Approved**, including the `SKILL.md` criterion 6 wording in step 2 | Status Draft → Approved. Implementation may begin at step 1 |

---

## 1. Scope

**In scope:**

- `docs/DEVELOPMENT_STANDARDS.md` — a new **§3.8 Framework mechanisms first**, appended after §3.7. Every bare `§3.8` in this spec means that new section, which does not exist until step 1 writes it.
- `.claude/skills/session-start/SKILL.md` § Role 2, criterion 6 — extended to ask about a library mechanism and cite §3.8.

**Out of scope:**

- **`SKILL.md` § Role 1 Critical Rule.** It governs choosing a design path against existing services. §3.8 already governs a spec author directly ("a spec that writes its own…"), so a citation there adds no rule and is not something #221 asks for.
- **`CLAUDE.md` § Critical Rules.** Ray approves membership; adding §3.8 there is not part of #221.
- **`docs/dev/specs/_TEMPLATE_SPEC.md`.** No new field. The Decision Log already holds the record (Decision Log row 4).
- **Converting existing code that writes its own version of a mechanism.** That is #58's and #201–#216's work.
- **`workmain/**`, `tests/**`, `automation/**`, `config/**`.** Untouched, which is what keeps this on `chore/*` under §2.2.

## 3. Design rules

- **DR1 —** The rule is stated once, in §3.8. Every other document that refers to it cites §3.8 and does not restate its scope or its requirement.
- **DR2 —** The rule's scope is Python's standard library, Click, Rich and SQLAlchemy, as Ray decided on the issue.
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

- **Use the mechanism Python's standard library, Click, Rich or SQLAlchemy provides before writing your own.** Where two of them do the job, either meets this rule, unless another section names one.
- **A spec that writes its own records why.** Its Decision Log names the mechanism it set aside and the reason it does not fit.
- The library's version is tested and behaves the same in every caller. A hand-written version has to get every edge case right on its own, and each copy can get a different one wrong.

| Job | Written by hand | Use instead |
| --- | --- | --- |
| Ask for a number from 1 to `n` | A loop that converts and bounds-checks the input. One that rejects only `0` and values above `n` accepts `-1`, which Python reads as an index from the end of the list. | `click.prompt(..., type=click.IntRange(1, n))` |
| Restrict an option to fixed values | An `if value not in (...)` check in the command body | `type=click.Choice([...])` on the option |
| Parse a `YYYY-MM-DD` date | Splitting on `-` and building a `date` from the parts | `date.fromisoformat(value)` |
| Build a file path | Joining strings with `/` | `pathlib.Path(base) / name` |
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
| AC1.1 | §3.8 tells an author to use the mechanism Python's standard library, Click, Rich or SQLAlchemy provides before writing their own, and requires a spec that writes its own to name, in its Decision Log, the mechanism it set aside and why | A stated reading by Ray of `docs/DEVELOPMENT_STANDARDS.md` §3.8, for both requirements |
| AC2.1 | Caliper's criterion 6 asks whether a spec writes its own version of a mechanism §3.8 governs, as well as whether it bypasses an existing service, orchestrator or workflow | A stated reading by Ray of `.claude/skills/session-start/SKILL.md` § Role 2 criterion 6 |
| AC3.1 | The rule is stated only in §3.8; every other mention in the standards, the skills and `CLAUDE.md` is a citation of §3.8 | `git grep -n -i -e framework -e mechanism -e '§3\.8' -- docs/DEVELOPMENT_STANDARDS.md .claude CLAUDE.md`, which returned nothing on `main` at authoring, now returns only lines inside §3.8 and `SKILL.md` criterion 6; and `git diff main...HEAD -- docs/DEVELOPMENT_STANDARDS.md .claude CLAUDE.md` adds text only in §3.8 and criterion 6, both read by Ray |

## 6. Test plan

Omitted: no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changes (`_TEMPLATE_SPEC.md`, direct path). Close-out runs the suites regardless.

## 7. Risks and rollback

| Risk | Mitigation |
| --- | --- |
| §3.8 is read as forbidding any helper | Its requirement is conditional on a provided mechanism, and the remedy is a Decision Log row, not a ban |

Rollback: revert the step commits. Both edits are additive text in two documents.
