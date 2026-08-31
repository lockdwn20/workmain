# Issue Creation and Validation — Spec

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20260817
**Branch:** `chore/issue-82-issue-creation` (from `main`, merges to `main` and `dev`)
**Target release:** none — `chore/*` carries no version bump, no `CHANGELOG.md` entry, no tag, no Release
**Originating item:** Issue #82, child of #80
**Design study:** `docs/dev/design/RECON_CYCLE_MECHANICS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260814 | Ray | Recon Q3 — issue content is authored as JSON, validated client-side, and streamed into `gh issue create` parameters | Accepted. This is the mechanism of the spec |
| 20260817 | Ray | One template, not one per issue shape, provided it covers all issue conditions | Accepted. DR1 |
| 20260817 | Ray | The script validates and then invokes `gh issue create` itself | Accepted. DR5 |
| 20260817 | Ray | Every issue created in this repo joins the WorkmAIn Queue project | Accepted. DR6. Membership only — #84 owns rank |
| 20260817 | Ray | Allowances are needed while the process is still being built | Accepted. DR7 |
| 20260817 | Spanner | `gh issue create --type` is inert — `Repository.issueTypes` is `null` (recon F26) | The type discriminator is applied as a label. See C11 |
| 20260817 | Caliper | F4 — the type-label derivation was never specified, and GitHub carries no type marking | The validator parses §1.3, which owns the rule. §4.1 |
| 20260817 | Caliper | F6 — C6 quoted §1.3 one clause short; the clause makes milestone + type label legitimate | C6 quotes it whole. The rule is scoped to creation, where the state cannot arise |
| 20260817 | Caliper | F7 — `grep -c` prints `0` but exits `1` | AC2.6 and AC3.4 restated as stdout comparisons |
| 20260817 | Caliper | F8 — C3 cited an ownership query for a linkage claim | Re-cited to `repository.projectsV2` |
| 20260817 | Caliper | F9 — `--blocked-by` takes comma-joined numbers; `--label` repeats | Both forms stated in §4.3 and checked by AC3.2 |
| 20260817 | Caliper | F10 — §7 credited AC1.1 with an exclusivity check it did not make | AC1.1 is now a directory-listing equality |
| 20260817 | Ray | F5 — §2.2 has no category for new dev tooling in `scripts/` | `chore/*` and `scripts/`, per the standards as they stand. Any missing category is #86's |
| 20260818 | Ray | The template governs new issues only. Existing issues predate it and are revised when they come up for planning | The spec validates nothing against the existing population. AC1.4 proves shape coverage from the schema's own fields |
| 20260818 | Ray | #82's first AC reworded to describe one template with shape expressed by field population | The spec matches the new wording. See §5 |
| 20260818 | Ray | The body format is stated as the standard, not derived from what issues look like today | §4.2 |
| 20260818 | Caliper | R3 — C12 said `gh label list --json` returns three fields; it returns eight | Corrected. The conclusion holds: `isDefault` is `true` for `documentation`, `question` and others, so no field separates type from area |
| 20260818 | Caliper | R4 — `type`'s value was never checked against live GitHub, though it is passed to `--label` | Closed in §4.1. `type` is checked against the live label set exactly as `labels[]` is |
| 20260818 | Ray | What happens with all existing issues that don't match the template? | Existing issues will be updated to match the template prior to their implementation planning |
| 20260818 | Ray | F11 — repository layout. Non-application tooling and its tests live in `automation/`; `tests/` holds application tests only; the JSON template goes in `.github/ISSUE_TEMPLATE/`, which GitHub ignores because it reads only `.md` and `.yml` | Adopted. DR3 and DR9. `automation/` is named in none of §2.2's exception paths, so `chore/*` applies with no deviation |
| 20260818 | Caliper | F12 — the spec never said whether the schema file or the script owns the rules | The script owns them; the schema file is data the script loads. DR9 |
| 20260818 | Caliper | F13 — `gh issue list` returns open issues only, and the spec never said which states are queried | Finding accepted, **fix reversed by Ray**. A parent closes when its children are done, so a closed parent, blocker, or blocked issue is a mistake to catch, not a case to allow. All three must exist **and** be open. The lookup still resolves any state so it can tell "closed" apart from "does not exist" and say which — see R5 for the form it takes. §4.1, AC2.9 |
| 20260818 | Caliper | F14 — `CLAUDE.md` was in scope with no step or AC | #82 gained a fourth AC covering the plain-speech line, so it is in scope. Step 5 and AC5.1 carry it |
| 20260818 | Caliper | F15 — AC4.x cited §1.2 for a test obligation §1.2 does not contain | Corrected to §6 |
| 20260818 | Caliper | F16 — DR4 says never stop at the first error; AC2.8 exits immediately | DR4 gains the ordering exception: the §1.3 parse runs first and aborts, because no type rule can be evaluated without it |
| 20260818 | Caliper | F17 — the standards-file location and section bounds were specified for tests only | §4.1 states both |
| 20260818 | Caliper | F18 — Step 2's ACs needed fixtures assigned to a later step | Fixtures move to Step 2 |
| 20260818 | Caliper | R5 — the issue lookup had no stated shape, and the natural bulk form is defective: `gh issue list` caps at 30 by default, so valid older numbers report as non-existent | §4.1 states a per-number `gh issue view`. No list, no limit to keep correct |
| 20260818 | Caliper | R7 — "at least one test per AC2.x row" needs a human to confirm | Test names carry their AC id, so the check is a grep |
| 20260818 | Caliper | R8 — AC5.2's grep passes with both hits in one section | Anchored per section: one `automation/` row in §6.3's table, one in §7's |
| 20260818 | Caliper | R9 — Step 4 claimed the shape fixtures that §6 assigns to Step 2 | Step 2 is correct; the Step 4 row no longer claims them |
| 20260818 | Caliper | R10 — AC1.2's `issueTemplates` query reads the default branch and cannot run at Step 1 | Split. AC1.2 is the local check; the query is Ray's post-merge confirmation, stated outside the AC table |
| 20260818 | Caliper | §2.2's `chore/*` clause says "non-behavioural dev tooling" and lists no `.github/` or `automation/` | Amendment folded into Step 5 and AC5.3. It is proposed, not applied — the standard changes only if Ray approves this spec |
| 20260818 | Caliper | R11 — C15 and §4.1 wrote the live open-issue count into the spec | Corrected. Both now say the count exceeds the cap; the evidence commands derive it |
| 20260818 | Caliper | R12 — AC2.9(c) could not be a test, because §6's seam replaces the very fetch it was meant to catch, yet AC4.1 required it to be one | Real contradiction. Split into AC2.10, a live check run once at Step 2 with its issue number derived at run time |
| 20260818 | Caliper | R13 — AC5.3 asserted the reworded phrase with no command behind it | Four greps, including a negative one for `non-behavioural` |
| 20260818 | Caliper | R14 — the AC2.9 split left three stale cross-references | Step 2 claims AC2.1 – AC2.10; AC4.1 scoped to AC2.1 – AC2.9; the §7 row cites AC2.10 |
| 20260818 | Caliper | Fourth pass: no remaining findings. C1 – C16 verified against live source. Verdict — sound, approval is Ray's | Recorded |
| 20260818 | Ray | §5.1's §2.2 amendment approved | Step 5 applies it |
| 20260818 | Ray | **Spec approved for implementation** | Status → Approved. Anvil works from this document only |
| 20260818 | Caliper | `--label` accepts comma-joined values as well as repetition, so §4.3's stated rationale was wrong | Rationale corrected. Repetition is still used: a comma inside a label name would break the joined form |
| 20260818 | Spanner | Bare `pytest` collects `scripts-deprecated/`, so CLAUDE.md's "excluded from test collection" is not enforced by anything. Adding `automation/` would put a second test tree in the same sweep | `pyproject.toml` gains `testpaths = ["tests"]`. Bare `pytest` runs the application suite only; `pytest automation/` still works, since `testpaths` applies only when no path is given |

---

## 1. Scope

**In scope:**

- One JSON schema and one skeleton template describing a WorkmAIn issue, in
  `.github/ISSUE_TEMPLATE/`.
- `automation/issue_validator.py` — a stdlib-only client-side validator that checks a JSON
  issue file against the schema and against live GitHub state, then creates the issue
  through `gh issue create`.
- `automation/issue_validator_test.py` — its tests.
- `pyproject.toml` — `testpaths`, so the application suite and `automation/` stay separate.
- `docs/DEVELOPMENT_STANDARDS.md` §6.3 and §7 — the `automation/` placement rows.
- `CLAUDE.md` — the plain-speech directive, per #82's first AC.

**Out of scope:**

- **Rank and ordering.** Items land in Project #3 as members; where they sit in the queue
  is #84's mechanism and this spec must not acquire it. See DR6.
- **Existing issues.** They predate this template. Nothing here reads, validates, or
  reconciles them; they are revised when they come up for planning.
- **Issue editing.** `gh issue edit`. This spec covers creation.
- **Milestone and label administration.** The validator checks names against live GitHub
  and fails on a name that does not exist; it never creates one.
- **Server-side GitHub templates.** No `.md` or `.yml` template is created. Recon F24/F25
  rule them out; the `.json` file shares the directory but is not one. See DR3.
- **`automation/check_release_integrity.py`.** Same category as `automation/`, but moving it is
  an unrelated change with its own blast radius. It becomes its own issue.
- **`CLAUDE.md` line 52** (`gate` → `step`). Committed on this branch, covered by no AC
  here; the subject belongs to #86.
- Any change to `workmain/**`, `config/**`, or `templates/**`. Nothing in the application
  imports this script, and the script imports nothing from the application.

## 2. Verified current state

| # | Claim | Evidence |
| --- | --- | --- |
| C1 | `gh` is **2.97.0**, and `gh issue create` carries `--title`, `--body`, `--body-file`, `--label`, `--milestone`, `--parent`, `--blocked-by`, `--blocking`, `--project`, `--type` | `gh --version`; `gh issue create --help`, read at authoring time. Confirms recon F23 |
| C2 | The token holds the `project` scope alongside `repo`, so `--project` works | `gh auth status` — scopes list. Confirms recon F28 |
| C3 | Project **#3 "WorkmAIn Queue"** is linked to this repository and is the only open one; a closed untitled #2 is also linked | `gh api graphql` on `repository(owner:"lockdwn20",name:"workmain"){projectsV2}` — #3 `closed=false`, #2 `closed=true`. `--project` resolves against linkage, so an ownership query is not sufficient evidence |
| C4 | `.github/` **does not exist** in the working tree | Filesystem read at repo root. Confirms recon F14 |
| C5 | `automation/check_release_integrity.py` is the precedent for standards-enforcing dev tooling: stdlib only, module docstring stating why it exists, non-zero exit on failure. It has no tests | The file's imports and docstring; `grep -rl check_release_integrity tests/` returns nothing |
| C6 | §1.3, quoted whole: *"Labels carry area. `bug`/`enhancement` is the type discriminator, applied only to issues with no milestone — so a type label appearing inside a milestone means that work was pulled in later, not planned as part of it."* The trailing clause matters: milestone + type label is a legitimate state, not an error. §1.3 also states that what a label means *"is its description on GitHub … not enumerated here"* | `docs/DEVELOPMENT_STANDARDS.md:45-49`, as it stands after #81 |
| C7 | §1.3 also states *"A milestone carries the exit condition that closes it"* and *"An issue must be independently verifiable on its own"* | `docs/DEVELOPMENT_STANDARDS.md:50-53` |
| C8 | The live label set and milestone set are each readable in one call — `gh label list --json name` and `gh api repos/:owner/:repo/milestones --jq '.[].title'`. Neither is transcribed into this spec | Both commands run at authoring time |
| C9 | The `docs` label no longer exists; `documentation` carries the four issues that had it | `gh label list --limit 100` — confirms #81 shipped |
| C10 | Python is **3.12.3** and no JSON-schema library is a project dependency | `python3 --version`; `requirements.txt` |
| C11 | The `type` discriminator cannot be set through `gh issue create --type`: `Repository.issueTypes` is `null` for this repository | Recon F26, re-checked at authoring time |
| C12 | GitHub cannot distinguish a type label from an area label. `gh label list --json` offers eight fields — `color`, `createdAt`, `description`, `id`, `isDefault`, `name`, `updatedAt`, `url` — and none marks type. `isDefault` is `true` for `documentation`, `question` and `wontfix` as well as `bug` and `enhancement`, so it does not separate them. With `issueTypes` null (C11), the discriminator is knowable only from §1.3 | `gh label list --json` field list; `gh label list --limit 100 --json name,isDefault`; C11 |
| C13 | No pytest configuration exists. `pyproject.toml` is tracked and **empty**; there is no `pytest.ini`, `setup.cfg`, or `tox.ini`. Defaults therefore apply, including the `test_*.py` / `*_test.py` collection patterns | `ls`/`cat` at repo root; `grep` for `[tool.pytest`, `testpaths`, `python_files` across `*.toml`, `*.ini`, `*.cfg` |
| C14 | Bare `pytest` collects `scripts-deprecated/` — three files' worth of tests outside `tests/`. CLAUDE.md's *"`scripts-deprecated/` is excluded from test collection"* is not enforced by anything; the suite looks clean only because it is always invoked as `pytest tests/` | `pytest --collect-only -q` at repo root versus `pytest --collect-only -q tests/`; the difference is entirely `scripts-deprecated/` |
| C15 | `gh issue list` returns **open** issues only unless `--state all` is passed, and caps at **30** unless `--limit` is raised. The open-issue count already exceeds that cap, so the default silently truncates | `gh issue list --help`; `gh issue list --json number -q 'length'` versus the same with `--limit 300` — the two differ |
| C16 | `gh issue view <N> --json number,state` resolves a single issue in any state — it returned `{"number":81,"state":"CLOSED"}` for a closed issue — and exits **1** with *"Could not resolve to an issue or pull request"* for a number that does not exist. State and existence are therefore separable without any list | Both commands run at authoring time |

## 3. Design rules

- **DR1 — One schema, rules not shapes.** There is a single template. Issue shape (parent,
  child, scheduled, unscheduled) follows from which fields are populated, and the validator
  enforces the cross-field rules §1.3 already states. A per-shape template set would be a
  register, and any shape missing from it would go unprompted. A parent issue is created
  through this template like any other: it leaves `parent` null and becomes a parent when a
  child names it with `--parent`. Parent and standalone are therefore the same shape at
  creation, which is the plainest case for one template — a per-shape set would carry two
  identical files.
- **DR2 — Nothing is enumerated that can be derived.** Label names, milestone titles, and
  whether a parent issue exists are read live from GitHub at validation time. The type
  discriminator is not a GitHub facet (C12), so it is read from §1.3, which owns the rule.
  Neither this spec nor the schema contains a list of labels, milestones, or issue numbers.
- **DR3 — The template lives in `.github/ISSUE_TEMPLATE/` and is not a GitHub template.**
  GitHub reads only `.md` and `.yml` from that directory, so a `.json` file sits there
  without being offered as an issue template (Ray, 20260818). The directory is the
  discoverable home for issue structure; the file format is what keeps GitHub out of it.
  No `.md` or `.yml` template is created — recon F24/F25 rule that mechanism out.
- **DR4 — Validation is total, with one ordering exception.** All checks run before the
  script exits; it never stops at the first error. Each failure names the offending key and
  what was wrong with it. The script never repairs, defaults, or rewrites a field. **The
  exception is the §1.3 discriminator parse**, which runs first and aborts on failure: no
  type rule can be evaluated without the token list, so continuing would report guesses.
- **DR5 — Creation is opt-in.** The default run validates and prints the exact
  `gh issue create` command, creating nothing. `--create` runs it. The stop on an
  outward-facing action is carried by the tool, not by a step in a process document.
- **DR6 — Every created issue joins the Queue, and nothing more.**
  `--project "WorkmAIn Queue"` is passed on every creation (Ray, 20260817).
  Membership only: no field is set and no position is chosen — #84 owns rank. GitHub
  auto-populates `Status` to `Todo` (recon F32); the script does not write it and ignores it.
- **DR7 — The validator checks mechanical properties, not judgement.** §1.3's
  "independently verifiable" and "the exit condition covers every issue" are judgements. A
  validator that guesses at them blocks correct work, so it does not try.
- **DR8 — The application suite and `automation/` never mix.** `tests/` holds application
  tests; `automation/` holds non-application tooling and the tests for it. `pyproject.toml`
  sets `testpaths = ["tests"]` so a bare `pytest` runs the application suite only. Without
  it nothing enforces the separation — C14 shows the existing claim about
  `scripts-deprecated/` is already untrue.
- **DR9 — The script owns the rules; the schema file is data.** `issue.schema.json` declares
  the key set and each key's type and required-ness, and `issue_validator.py` loads it at
  runtime and enforces what it finds. Cross-field rules that need live GitHub or §1.3 — the
  type rule, label and milestone existence — live in the script, because a JSON file cannot
  express them. Nothing is stated in both places, so the two cannot drift.
- **Anything not covered here: STOP and surface to Ray.** No self-resolution, no scope
  adjustment. Unconditional, and independent of step boundaries.

## 4. Steps

Ordered, each committed on completion. **No step is an approval stop** — every step is a
new file on a branch, undone by `git revert`.

| Step | Deliverable | Files | Verification |
| --- | --- | --- | --- |
| 1 | The JSON schema and the skeleton template | `.github/ISSUE_TEMPLATE/` | AC1.1, AC1.2, AC1.3 |
| 2 | The validator — the §1.3 parse, schema checks, then live-state checks, per DR4 — **and every fixture this spec uses**, including the eight shape fixtures AC1.4 needs | `automation/issue_validator.py`, `automation/fixtures/` | AC2.1 – AC2.10 |
| 3 | `gh issue create` invocation: parameter mapping per §4.3, `--create` opt-in | `automation/issue_validator.py` | AC3.1 – AC3.5 |
| 4 | Tests over the fixtures Step 2 created; `pyproject.toml` `testpaths`, per DR8 | `automation/issue_validator_test.py`, `pyproject.toml` | AC1.4, AC4.1 – AC4.3 |
| 5 | `CLAUDE.md` plain-speech directive; the `automation/` placement rows and the §2.2 wording amendment | `CLAUDE.md`, `docs/DEVELOPMENT_STANDARDS.md` | AC5.1 – AC5.3 |

### 4.1 The schema

`.github/ISSUE_TEMPLATE/issue.schema.json` — a hand-rolled schema, since no JSON-schema
library is a dependency (C10) and adding one for a dev script is not warranted. Per DR9 the
script loads this file and enforces what it declares. Field set:

| Key | Type | Required | Rule |
| --- | --- | --- | --- |
| `title` | string | yes | non-empty after strip; ≤ 256 characters |
| `context` | string | yes | non-empty after strip. Becomes the body's prose |
| `acs` | array of string | yes | ≥ 1 entry, each non-empty after strip |
| `milestone` | string or `null` | yes — key must be present | if non-`null`, must match a live milestone title exactly |
| `parent` | integer or `null` | yes — key must be present | if non-`null`, must be an **open** issue in this repository |
| `labels` | array of string | yes | ≥ 1 entry; every entry must be a live label; **no entry may be a type label** (see below) |
| `type` | string or `null` | yes — key must be present | if non-`null`, must be one of the §1.3 type labels **and** must exist as a live label — the same check `labels[]` gets, since both are passed to `--label` |
| `blocked_by` | array of integer | no — defaults `[]` | every entry an **open** issue |
| `blocking` | array of integer | no — defaults `[]` | every entry an **open** issue |

Every key must be present even when its value is `null`. A missing `milestone` key is an
omission; `"milestone": null` is a decision.

Any key not in this table fails, naming the key. That is what catches a typo.

**Referenced issues must be open, and the check reads all states to say why.** A parent
closes when its children are done, so naming a closed parent means the work is finished and
the child does not belong to it. The same holds in both directions for dependencies: a
closed blocker is a stale dependency, and an issue that is already closed cannot be blocked.
All three of `parent`, `blocked_by` and `blocking` must name an **open** issue.

**The lookup is per number, not a list.** For each number the JSON file names, the validator
runs `gh issue view <N> --json number,state` (C16). That call resolves an issue in any state,
so the two failures stay distinct:

- non-zero exit → *no such issue*
- exit `0` with `state` of `CLOSED` → *issue #N is closed*

A repository-wide list is not used. `gh issue list` returns open issues only and caps at 30
unless told otherwise (C15), and the open-issue count already exceeds that cap, so the
default silently drops the older numbers — a valid low-numbered parent reports as
non-existent. That failure is
invisible in testing with recent issue numbers and appears the first time someone references
an early one. The per-number form has no limit to keep correct and no state default to
remember.

**The type rule (C6, §1.3).** `type` is non-`null` **if and only if** `milestone` is
`null`. Both violations are reported distinctly:

- `milestone` is `null` and `type` is `null` → *unscheduled issue carries no type label*.
- `milestone` is set and `type` is non-`null` → *a scheduled issue must not carry a type
  label*.

**This rule applies to creation only.** Per C6, a milestone plus a type label marks work
pulled into a milestone after planning. That state is legitimate, and it is reached by
editing an existing issue, not by creating one. If the validator is ever used to gate
`gh issue edit`, this rule must be revisited first.

`type` is a separate key from `labels`, and a type label inside `labels` fails, so the
discriminator has exactly one path and the cross-field rule cannot be bypassed.

**Deriving the type-label names.** GitHub carries no type marking (C12), so the validator
reads §1.3, which owns the rule. Mechanism, in full:

- **Locating the file.** Resolved relative to the repository root, which is found by walking
  up from the script's own path to the first directory containing `.git`. Not the working
  directory — the script must behave the same run from anywhere.
- **Delimiting the section.** From the line matching `### 1.3` to the next line beginning
  `###` or `---`, whichever comes first.
- **Extracting the tokens.** Within that section, the single line containing the phrase
  `type discriminator`; from it, every backtick-delimited token. Against the current text
  this yields `bug` and `enhancement`, verified at authoring time.
- **On failure.** If the repository root, the section, the line, or the tokens cannot be
  found, exit non-zero naming the file and the phrase. There is no fallback list, and per
  DR4 this check runs first and aborts.

The parse depends on the tokens and the phrase sharing one physical line of a wrapped
paragraph. That holds today, and a rewrap fails loudly rather than silently.

`.github/ISSUE_TEMPLATE/issue.template.json` is the skeleton — every key present, values
empty or `null`, ready to copy. `automation/issue_validator.py --new` writes a copy to
stdout so the path never has to be remembered.

### 4.2 Body rendering

The body format for issues the script creates:

```markdown
<context, verbatim>

**ACs**

- <acs[0]>
- <acs[1]>
```

Written to a temporary file and passed as `--body-file`, not `--body`: a body containing
backticks, quotes, or newlines is otherwise at the mercy of shell quoting.

### 4.3 Parameter mapping

| JSON | `gh issue create` |
| --- | --- |
| `title` | `--title` |
| `context` + `acs` | `--body-file <tmp>` |
| `milestone` (non-`null`) | `--milestone` |
| `parent` (non-`null`) | `--parent` |
| `labels` + `type` (non-`null`) | `--label` **repeated once per name** |
| `blocked_by` (non-empty) | `--blocked-by` **once, values comma-joined** |
| `blocking` (non-empty) | `--blocking` **once, values comma-joined** |
| — | `--project "WorkmAIn Queue"`, always (DR6) |

`--label` accepts either form; repetition is used because a comma inside a label name —
`help wanted` is one space away from such a name — would break the joined form.
`--blocked-by` is documented as taking comma-joined numbers, where the values are integers
and no such ambiguity exists (C1). An empty `blocked_by` or `blocking` omits the flag
rather than passing an empty value.

`--type` is never passed. It is inert on this repository (C11) and the discriminator travels
as a label.

### 4.4 Authorization point

Creating a GitHub issue is outward-facing. Per DR5 the stop is the tool's default: no
`--create`, no issue. Ray runs the script, reads the printed command and the validation
report, then re-runs with `--create`. No separate approval step is needed, because the tool
cannot create anything without the flag.

No DB migration appears in this spec.

## 5. Acceptance criteria

Mapped to #82's four ACs: AC5.x carries its first (the CLAUDE.md directive), AC1.x its
second, AC2.x its third, AC3.x its fourth. AC4.x is the test obligation §6 imposes. Each row
is a single assertion.

#82's template AC — one template, with shape expressed by which fields are populated — is
met by AC1.1 (one schema on disk) and AC1.4 (every shape validates through it). The shape
set is the cross product of the schema's own fields, so it is complete by construction
rather than by anyone having listed the shapes correctly.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | `.github/ISSUE_TEMPLATE/` holds exactly the schema and the skeleton, per DR1 | `ls .github/ISSUE_TEMPLATE/ \| sort` prints exactly two lines: `issue.schema.json`, `issue.template.json`. An equality, so a third file fails |
| AC1.2 | No server-side GitHub template is created, per DR3 | `ls .github/ISSUE_TEMPLATE/*.md .github/ISSUE_TEMPLATE/*.yml .github/ISSUE_TEMPLATE/*.yaml` matches nothing. Local check only — see the post-merge confirmation below the table |
| AC1.3 | The skeleton carries every schema key and no other | `python3 automation/issue_validator.py --new \| python3 -c "import json,sys; print(sorted(json.load(sys.stdin)))"` equals the sorted key list from `issue.schema.json` |
| AC1.4 | Every issue shape validates through the one schema, per DR1 | Eight fixtures covering the cross product of `milestone` set/null × `parent` set/null × `type` set/null. The four satisfying the type rule validate and exit `0`: scheduled standalone, scheduled child, unscheduled standalone, unscheduled child. The parent case is covered by the standalone fixtures, since a parent leaves `parent` null at creation (DR1). The other four violate it and fail with the AC2.3 messages. Shape is therefore carried by field population, and no fixture needs a template of its own |
| AC2.1 | A missing required key fails, naming the key | Fixture with `milestone` deleted → exit non-zero, stderr contains `milestone` |
| AC2.2 | An unknown key fails, naming the key | Fixture with `mileston` (typo) → exit non-zero, stderr contains `mileston` |
| AC2.3 | Both halves of the type rule fail, and are distinguishable | Fixture A (`milestone: null`, `type: null`) and fixture B (`milestone` set, `type` set) each exit non-zero with different messages |
| AC2.4 | A type label inside `labels` fails | Fixture with a live type-label name in `labels` → exit non-zero |
| AC2.5 | A non-existent label, milestone, or parent fails against live state | Three fixtures, each exiting non-zero and naming the offending value |
| AC2.6 | The type-label names are parsed from §1.3, not hardcoded — DR2, §4.1 | Both required. **(a)** `grep -cE "['\"](bug\|enhancement)['\"]" automation/issue_validator.py` prints `0`. Compare stdout, not exit status — `grep -c` exits `1` when it prints `0`. **(b)** Against a fixture standards file whose discriminator line reads ``` `alpha`/`beta` is the type discriminator ```, the validator treats `alpha` and `beta` as type labels and `bug` as an area label |
| AC2.7 | Validation is total, per DR4 | Fixture with three independent errors → stderr names all three in one run |
| AC2.8 | A missing §1.3 discriminator line aborts before any other check, per DR4 | Fixture standards file with the `type discriminator` line deleted, given a JSON file that also has two schema errors → exit non-zero, stderr names `DEVELOPMENT_STANDARDS.md` and `type discriminator` and **does not** report the two schema errors. This is the one place DR4's total reporting does not apply |
| AC2.9 | A closed issue is rejected as a parent or blocker and reported as closed, not as missing, per §4.1 | Two fixtures, both unit tests over the §6 seam, since message distinctness is pure logic. **(a)** a closed issue in `parent` → exit non-zero, stderr says **closed**, not that it does not exist. **(b)** a number existing in no state → exit non-zero, stderr says it does not exist. The two messages must differ |
| AC2.10 | The real lookup is not built on a truncating list — **a live check, not a test**, per §4.1 | Run once at Step 2 against real GitHub, result recorded in the Step 2 commit message. Take the oldest open issue number from `gh issue list --state open --limit 300 --json number`, name it as `parent` in a JSON file, and run the validator: it must validate. An implementation built on a default `gh issue list` reports that number as non-existent and fails. This cannot be a unit test — §6's seam replaces the fetch, which is the very code under examination — and the number is derived at run time, since a hardcoded one closes eventually and breaks the check for reasons unrelated to the validator |
| AC3.1 | The default run creates nothing | On a valid fixture, `python3 automation/issue_validator.py <file>` exits `0`, prints the `gh issue create` command, and `gh issue list --limit 300 --json number \| jq length` is unchanged before and after |
| AC3.2 | The printed command carries every populated field in the form `gh` expects, per §4.3 | For a fixture with two labels, a type, and two `blocked_by` entries: the command contains `--title`, `--body-file`, `--milestone`, `--parent`, `--project`; exactly three `--label` occurrences; and exactly one `--blocked-by` with the numbers comma-joined. Presence alone would pass a wrong form |
| AC3.3 | `--project "WorkmAIn Queue"` is present unconditionally, per DR6 | Printed command for a *minimal* fixture (no milestone, no parent, no blockers) still contains `--project` |
| AC3.4 | `--type` is never passed, per C11 | `grep -c '\-\-type' automation/issue_validator.py` prints `0`. Compare stdout, not exit status, as in AC2.6(a) |
| AC3.5 | Empty `blocked_by` / `blocking` omit the flag rather than passing an empty value | Printed command for the minimal fixture contains neither `--blocked-by` nor `--blocking` |
| AC4.1 | Every rule in AC2.1 – AC2.9 is covered by a test, checkable without reading them. AC2.10 is excluded by design — it is a live check, not a test | `python -m pytest automation/ -q` passes, and each test function name carries the AC it covers (`test_ac2_1_…` through `test_ac2_9_…`). `python -m pytest automation/ --collect-only -q \| grep -oE 'ac2_[1-9]' \| sort -u \| wc -l` prints `9`. Naming the id in the test is what makes the coverage claim mechanical instead of a human count |
| AC4.2 | The application suite is unchanged | `python -m pytest tests/` — zero failures, and the pass count equals the baseline recorded at Step 1. No test is added to `tests/`, so the count moves by zero |
| AC4.3 | Bare `pytest` runs the application suite only, per DR8 | `python -m pytest --collect-only -q` and `python -m pytest --collect-only -q tests/` report the same count. Before this step they differ, because bare collection sweeps in `scripts-deprecated/` (C14) |
| AC5.1 | `CLAUDE.md` carries the plain-speech directive, per #82's first AC | `sed -n '3p' CLAUDE.md \| grep -c 'direct, concise and plainly spoken'` prints `1` |
| AC5.2 | Both placement tables know about `automation/`, per DR8 | Anchored per section, since a repo-wide grep passes with both hits in one place. `awk '/^### 6.3/,/^---/' docs/DEVELOPMENT_STANDARDS.md \| grep -c 'automation/'` prints at least `1`, and `awk '/^## 7\./,/^---/' docs/DEVELOPMENT_STANDARDS.md \| grep -c 'automation/'` prints at least `1` |
| AC5.3 | §2.2's `chore/*` clause names the directories this branch creates and carries the reworded phrase, per §5.1 | Within `awk '/^### 2.2/,/^### 2.3/' docs/DEVELOPMENT_STANDARDS.md`, three greps: `-c 'automation/'` prints `1`, `-c '\.github/'` prints `1`, and `-c 'changes no application behaviour'` prints `1`. A fourth, `-c 'non-behavioural'`, prints `0` |

**Post-merge confirmation — Ray's, not an AC.** `Repository.issueTemplates` reads the
**default branch**, so it returns nothing about a file sitting on a `chore/*` branch and
cannot be run at Step 1. Once this reaches `main`:

```bash
gh api graphql -f query='{repository(owner:"lockdwn20",name:"workmain"){issueTemplates{filename}}}'
```

It must still return `[]`. That is the only observation that confirms GitHub ignores the
`.json`, and it is why AC1.2 asserts only what is checkable locally.

### 5.1 §2.2 amendment — verbatim

Step 5 replaces the `chore/*` positive clause with exactly this:

```markdown
- For `docs/**`, standards documents, and dev tooling that changes no application behaviour
  (`.gitignore`, `.githooks/`, `.github/`, `automation/`, editor/CI config).
```

Two changes: *"non-behavioural dev tooling"* becomes *"dev tooling that changes no
application behaviour"*, and `.github/` and `automation/` join the examples. The exception
clause beneath it is untouched and reads correctly afterwards — `workmain/**`, `tests/**`
and `scripts/**` are carved out precisely because they are application-facing, which is what
the reworded positive clause now says plainly.

**This is proposed, not applied.** The standard changes only if Ray approves this spec.

## 6. Test plan

- **New file:** `automation/issue_validator_test.py`, beside the script it tests, per Ray's
  layout. The name matches pytest's default `*_test.py` pattern, so `pytest automation/`
  collects it with no configuration (C13). Test functions are named for the AC they cover,
  per AC4.1. `automation/` has no `__init__.py`, so the script
  is loaded by path with `importlib.util.spec_from_file_location`.
- **Two suites, never mixed.** `pytest tests/` is the application suite; `pytest automation/`
  is this tool's. `testpaths` keeps a bare `pytest` on the first (DR8). Every invocation in
  this spec names its path, because the two are different populations and a count from one
  means nothing against the other.
- **No `db_session`.** Nothing here touches the database, so §6.1's fixture does not apply.
- **No live network in tests.** The live-state checks (labels, milestones, parent existence)
  are behind a seam that tests substitute — the validator takes the live sets as arguments
  rather than fetching them internally, so the pure rules are testable offline and the
  fetch happens once at the top of the run.
- **Second seam:** the §1.3 parse (§4.1) takes the path to `DEVELOPMENT_STANDARDS.md` as
  an argument. AC2.6(b) and AC2.8 substitute a fixture standards file and need it.
- **Fixtures:** `automation/fixtures/` — the eight shape fixtures AC1.4 needs, the invalid
  fixtures AC2.x needs, and two Markdown standards fixtures, one with a substituted
  discriminator line and one with it removed. Every fixture is created at **Step 2**,
  including the eight shape fixtures, because AC2.6(b), AC2.8 and AC2.9 need fixtures at
  that step and splitting the directory across two steps buys nothing.
- **Baseline:** derive at Step 1 with `python -m pytest tests/` and record it in the Step 1
  commit message, never in this spec.
- **Deviation from C5:** this is the first tested tooling script. #82's validator AC is
  about behaviour, which tests are the only way to assert. §6.3's *"`scripts/` — utilities
  and demos, never tests"* is about the application suite, and Step 5 adds the
  `automation/` rows so the placement is documented rather than assumed.

## 7. Risks and rollback

| Risk | Blast radius | Rollback |
| --- | --- | --- |
| The validator rejects a correctly-authored issue and creation stalls behind the tool | Work stoppage | AC1.4's eight fixtures cover every shape the schema can express, so a rule stricter than reality fails at Step 2 or 4 rather than in use. DR7 keeps judgement criteria out of the validator |
| A valid issue number is reported as non-existent — because it is closed, or because a default `gh issue list` truncated at 30 | The author hunts for a typo that isn't there | The lookup is per-number `gh issue view` (C16), which has no limit and no state default. AC2.9 requires the closed and missing messages to differ, and AC2.10 runs a low-numbered open issue against real GitHub, which a truncating implementation fails |
| A per-shape template set creeps back in | The register #82 exists to remove | DR1 forbids it. AC1.1 is a directory-listing equality, so a third file fails; AC1.3 asserts one key set |
| GitHub surfaces the `.json` as an issue template, or a `.md`/`.yml` is added beside it | Contributors get a broken template picker | DR3 creates no `.md`/`.yml` and AC1.2 checks for their absence locally. The default-branch behaviour is observable only after merge, which is what the post-merge confirmation below §5 is for |
| `automation/` tests leak into the application suite | The application baseline moves for reasons unrelated to the application | DR8's `testpaths`, checked by AC4.3. Without it nothing enforces the split — C14 shows the existing `scripts-deprecated/` claim is already untrue |
| The schema file and the script disagree about a rule | Two sources of truth, drifting silently | DR9 splits them: the file declares keys and types, the script owns cross-field and live-state rules. Nothing appears in both |
| `--create` runs on wrong content and a public issue is created | An issue that must be closed by hand | DR5 makes creation opt-in, DR4 makes validation total, so `--create` cannot run past a failure. Close with `gh issue close`; the number is consumed either way |
| Ordering semantics leak in from #84 | This spec pre-empts #84's queue mechanism | DR6 restricts the Project interaction to `--project`; §4.3 specifies no other Project parameter |
| The schema hardcodes a label or milestone list and goes stale | The register §1.3 forbids | DR2. AC2.6 checks for the type-label literal; AC2.5 requires label/milestone checks against live state |

Rollback is `git revert` of the step commits. The branch is `chore/*`, so no tag, Release,
or version bump exists to unwind. No GitHub object is created by the spec itself.
