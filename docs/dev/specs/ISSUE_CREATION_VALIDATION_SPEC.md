# Issue Creation and Validation — Spec

**Status:** Draft — awaiting Role 2 review
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

---

## 1. Scope

**In scope:**

- One JSON schema and one skeleton template describing a WorkmAIn issue.
- `scripts/gh_issue.py` — a stdlib-only client-side validator that checks a JSON issue
  file against the schema and against live GitHub state, then creates the issue through
  `gh issue create`.
- Tests covering the validator's rules.
- `CLAUDE.md` — the plain-speech directive and the gate→step wording, which ride this branch.

**Out of scope:**

- **Rank and ordering.** Items land in Project #3 as members; where they sit in the queue
  is #84's mechanism and this spec must not acquire it. See DR6.
- **Existing issues.** They predate this template. Nothing here reads, validates, or
  reconciles them; they are revised when they come up for planning.
- **Issue editing.** `gh issue edit`. This spec covers creation.
- **Milestone and label administration.** The validator checks names against live GitHub
  and fails on a name that does not exist; it never creates one.
- **`.github/ISSUE_TEMPLATE/`.** Server-side Markdown/YAML templates, ruled out by recon
  F24/F25. Nothing is placed in that reserved directory. See DR3.
- Any change to `workmain/**`, `config/**`, or `templates/**`. Nothing in the application
  imports this script, and the script imports nothing from the application.

## 2. Verified current state

| # | Claim | Evidence |
| --- | --- | --- |
| C1 | `gh` is **2.97.0**, and `gh issue create` carries `--title`, `--body`, `--body-file`, `--label`, `--milestone`, `--parent`, `--blocked-by`, `--blocking`, `--project`, `--type` | `gh --version`; `gh issue create --help`, read at authoring time. Confirms recon F23 |
| C2 | The token holds the `project` scope alongside `repo`, so `--project` works | `gh auth status` — scopes list. Confirms recon F28 |
| C3 | Project **#3 "WorkmAIn Queue"** is linked to this repository and is the only open one; a closed untitled #2 is also linked | `gh api graphql` on `repository(owner:"lockdwn20",name:"workmain"){projectsV2}` — #3 `closed=false`, #2 `closed=true`. `--project` resolves against linkage, so an ownership query is not sufficient evidence |
| C4 | `.github/` **does not exist** in the working tree | Filesystem read at repo root. Confirms recon F14 |
| C5 | `scripts/check_release_integrity.py` is the precedent for standards-enforcing dev tooling: `scripts/`, stdlib only, module docstring stating why it exists, non-zero exit on failure. It has no tests | The file's imports and docstring; `grep -rl check_release_integrity tests/` returns nothing |
| C6 | §1.3, quoted whole: *"Labels carry area. `bug`/`enhancement` is the type discriminator, applied only to issues with no milestone — so a type label appearing inside a milestone means that work was pulled in later, not planned as part of it."* The trailing clause matters: milestone + type label is a legitimate state, not an error. §1.3 also states that what a label means *"is its description on GitHub … not enumerated here"* | `docs/DEVELOPMENT_STANDARDS.md:45-49`, as it stands after #81 |
| C7 | §1.3 also states *"A milestone carries the exit condition that closes it"* and *"An issue must be independently verifiable on its own"* | `docs/DEVELOPMENT_STANDARDS.md:50-53` |
| C8 | The live label set and milestone set are each readable in one call — `gh label list --json name` and `gh api repos/:owner/:repo/milestones --jq '.[].title'`. Neither is transcribed into this spec | Both commands run at authoring time |
| C9 | The `docs` label no longer exists; `documentation` carries the four issues that had it | `gh label list --limit 100` — confirms #81 shipped |
| C10 | Python is **3.12.3** and no JSON-schema library is a project dependency | `python3 --version`; `requirements.txt` |
| C11 | The `type` discriminator cannot be set through `gh issue create --type`: `Repository.issueTypes` is `null` for this repository | Recon F26, re-checked at authoring time |
| C12 | GitHub cannot distinguish a type label from an area label. `gh label list --json` offers eight fields — `color`, `createdAt`, `description`, `id`, `isDefault`, `name`, `updatedAt`, `url` — and none marks type. `isDefault` is `true` for `documentation`, `question` and `wontfix` as well as `bug` and `enhancement`, so it does not separate them. With `issueTypes` null (C11), the discriminator is knowable only from §1.3 | `gh label list --json` field list; `gh label list --limit 100 --json name,isDefault`; C11 |

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
- **DR3 — The template is not a GitHub template.** Files live in
  `.github/issue-templates/`, never `.github/ISSUE_TEMPLATE/`. The reserved directory is
  read server-side from the default branch and accepts Markdown/YAML only (F24), so a
  `.json` placed there would be ignored or mis-parsed.
- **DR4 — Validation is total.** All checks run before the script exits; it never stops at
  the first error. Each failure names the offending key and what was wrong with it. The
  script never repairs, defaults, or rewrites a field.
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
- **Anything not covered here: STOP and surface to Ray.** No self-resolution, no scope
  adjustment. Unconditional, and independent of step boundaries.

## 4. Steps

Ordered, each committed on completion. **No step is an approval stop** — every step is a
new file on a branch, undone by `git revert`.

| Step | Deliverable | Files | Verification |
| --- | --- | --- | --- |
| 1 | The JSON schema and the skeleton template | `.github/issue-templates/` | AC1.1, AC1.2, AC1.3 |
| 2 | The validator — schema checks, the §1.3 discriminator parse, then live-state checks, per DR4 | `scripts/gh_issue.py` | AC2.1 – AC2.8 |
| 3 | `gh issue create` invocation: parameter mapping per §4.3, `--create` opt-in | `scripts/gh_issue.py` | AC3.1 – AC3.5 |
| 4 | Tests, including the shape fixtures AC1.4 needs | `tests/test_gh_issue.py`, `tests/fixtures/` | AC1.4, AC4.1, AC4.2 |

### 4.1 The schema

`.github/issue-templates/issue.schema.json` — a hand-rolled schema, since no JSON-schema
library is a dependency (C10) and adding one for a dev script is not warranted. Field set:

| Key | Type | Required | Rule |
| --- | --- | --- | --- |
| `title` | string | yes | non-empty after strip; ≤ 256 characters |
| `context` | string | yes | non-empty after strip. Becomes the body's prose |
| `acs` | array of string | yes | ≥ 1 entry, each non-empty after strip |
| `milestone` | string or `null` | yes — key must be present | if non-`null`, must match a live milestone title exactly |
| `parent` | integer or `null` | yes — key must be present | if non-`null`, must be an existing issue in this repository |
| `labels` | array of string | yes | ≥ 1 entry; every entry must be a live label; **no entry may be a type label** (see below) |
| `type` | string or `null` | yes — key must be present | if non-`null`, must be one of the §1.3 type labels **and** must exist as a live label — the same check `labels[]` gets, since both are passed to `--label` |
| `blocked_by` | array of integer | no — defaults `[]` | every entry an existing issue |
| `blocking` | array of integer | no — defaults `[]` | every entry an existing issue |

Every key must be present even when its value is `null`. A missing `milestone` key is an
omission; `"milestone": null` is a decision.

Any key not in this table fails, naming the key. That is what catches a typo.

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
reads §1.3, which owns the rule. It takes the §1.3 section of
`docs/DEVELOPMENT_STANDARDS.md`, finds the line containing `type discriminator`, and
collects the backtick-delimited tokens on it — currently `bug` and `enhancement`, verified
at authoring time. If the section, line, or tokens are missing it exits non-zero naming the
file and the phrase. There is no built-in fallback list.

`.github/issue-templates/issue.template.json` is the skeleton — every key present, values
empty or `null`, ready to copy. `scripts/gh_issue.py --new` writes a copy of it to stdout so
the path never has to be remembered.

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

The two forms differ: `gh issue create --help` documents `--label name` as repeatable and
`--blocked-by numbers` as comma-joined (C1). An empty `blocked_by` or `blocking` omits the
flag rather than passing an empty value.

`--type` is never passed. It is inert on this repository (C11) and the discriminator travels
as a label.

### 4.4 Authorization point

Creating a GitHub issue is outward-facing. Per DR5 the stop is the tool's default: no
`--create`, no issue. Ray runs the script, reads the printed command and the validation
report, then re-runs with `--create`. No separate approval step is needed, because the tool
cannot create anything without the flag.

No DB migration appears in this spec.

## 5. Acceptance criteria

Mapped to #82's three ACs: AC1.x carries its first, AC2.x its second, AC3.x its third.
AC4.x is the test obligation §1.2 imposes on any spec. Each row is a single assertion.

Issue #82's first AC — one template, with shape expressed by which fields are populated —
is met by AC1.1 (one schema on disk) and AC1.4 (every shape validates through it). The
shape set is the cross product of the schema's own fields, so it is complete by
construction rather than by anyone having listed the shapes correctly.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The template directory holds exactly the schema and the skeleton, per DR1 | `ls .github/issue-templates/ \| sort` prints exactly two lines: `issue.schema.json`, `issue.template.json`. An equality, so a third file fails |
| AC1.2 | Nothing was placed in the GitHub-reserved directory, per DR3 | `test -e .github/ISSUE_TEMPLATE` exits non-zero |
| AC1.3 | The skeleton carries every schema key and no other | `python3 scripts/gh_issue.py --new \| python3 -c "import json,sys; print(sorted(json.load(sys.stdin)))"` equals the sorted key list from `issue.schema.json` |
| AC1.4 | Every issue shape validates through the one schema, per DR1 | Eight fixtures covering the cross product of `milestone` set/null × `parent` set/null × `type` set/null. The four satisfying the type rule validate and exit `0`: scheduled standalone, scheduled child, unscheduled standalone, unscheduled child. The parent case is covered by the standalone fixtures, since a parent leaves `parent` null at creation (DR1). The other four violate it and fail with the AC2.3 messages. Shape is therefore carried by field population, and no fixture needs a template of its own |
| AC2.1 | A missing required key fails, naming the key | Fixture with `milestone` deleted → exit non-zero, stderr contains `milestone` |
| AC2.2 | An unknown key fails, naming the key | Fixture with `mileston` (typo) → exit non-zero, stderr contains `mileston` |
| AC2.3 | Both halves of the type rule fail, and are distinguishable | Fixture A (`milestone: null`, `type: null`) and fixture B (`milestone` set, `type` set) each exit non-zero with different messages |
| AC2.4 | A type label inside `labels` fails | Fixture with a live type-label name in `labels` → exit non-zero |
| AC2.5 | A non-existent label, milestone, or parent fails against live state | Three fixtures, each exiting non-zero and naming the offending value |
| AC2.6 | The type-label names are parsed from §1.3, not hardcoded — DR2, §4.1 | Both required. **(a)** `grep -cE "['\"](bug\|enhancement)['\"]" scripts/gh_issue.py` prints `0`. Compare stdout, not exit status — `grep -c` exits `1` when it prints `0`. **(b)** Against a fixture standards file whose discriminator line reads ``` `alpha`/`beta` is the type discriminator ```, the validator treats `alpha` and `beta` as type labels and `bug` as an area label |
| AC2.7 | Validation is total, per DR4 | Fixture with three independent errors → stderr names all three in one run |
| AC2.8 | A missing §1.3 discriminator line fails rather than falling back, per §4.1 | Fixture standards file with the `type discriminator` line deleted → exit non-zero, stderr names `DEVELOPMENT_STANDARDS.md` and `type discriminator`. No issue created |
| AC3.1 | The default run creates nothing | On a valid fixture, `python3 scripts/gh_issue.py <file>` exits `0`, prints the `gh issue create` command, and `gh issue list --limit 300 --json number \| jq length` is unchanged before and after |
| AC3.2 | The printed command carries every populated field in the form `gh` expects, per §4.3 | For a fixture with two labels, a type, and two `blocked_by` entries: the command contains `--title`, `--body-file`, `--milestone`, `--parent`, `--project`; exactly three `--label` occurrences; and exactly one `--blocked-by` with the numbers comma-joined. Presence alone would pass a wrong form |
| AC3.3 | `--project "WorkmAIn Queue"` is present unconditionally, per DR6 | Printed command for a *minimal* fixture (no milestone, no parent, no blockers) still contains `--project` |
| AC3.4 | `--type` is never passed, per C11 | `grep -c '\-\-type' scripts/gh_issue.py` prints `0`. Compare stdout, not exit status, as in AC2.6(a) |
| AC3.5 | Empty `blocked_by` / `blocking` omit the flag rather than passing an empty value | Printed command for the minimal fixture contains neither `--blocked-by` nor `--blocking` |
| AC4.1 | The validator's rules are covered by tests | `python -m pytest tests/test_gh_issue.py -q` passes, with at least one test per AC2.x row |
| AC4.2 | The suite is unaffected apart from the new file | `python -m pytest tests/` — zero failures, and the pass count equals the baseline recorded at Step 1 plus the count of new tests |

## 6. Test plan

- **New file:** `tests/test_gh_issue.py`. `scripts/` has no `__init__.py`, so the script is
  loaded by path with `importlib.util.spec_from_file_location`.
- **No `db_session`.** Nothing here touches the database, so §6.1's fixture does not apply.
- **No live network in tests.** The live-state checks (labels, milestones, parent existence)
  are behind a seam that tests substitute — the validator takes the live sets as arguments
  rather than fetching them internally, so the pure rules are testable offline and the
  fetch happens once at the top of the run.
- **Second seam:** the §1.3 parse (§4.1) takes the path to `DEVELOPMENT_STANDARDS.md` as
  an argument. AC2.6(b) and AC2.8 substitute a fixture standards file and need it.
- **Fixtures:** JSON files in `tests/fixtures/`, per §6.3 — the eight shape fixtures AC1.4
  needs, plus the invalid fixtures AC2.x needs. Two Markdown fixtures for the standards
  seam: one with a substituted discriminator line, one with it removed.
- **Baseline:** derive at Step 1 with `python -m pytest tests/` and record it in the Step 1
  commit message, not in this spec.
- **Deviation from C5:** this is the first tested script. #82's second AC is about
  validator behaviour, which tests are the only way to assert. §6.3's *"`scripts/` —
  utilities and demos, never tests"* governs where test files live; this one is in `tests/`.

## 7. Risks and rollback

| Risk | Blast radius | Rollback |
| --- | --- | --- |
| The validator rejects a correctly-authored issue and creation stalls behind the tool | Work stoppage | AC1.4's eight fixtures cover every shape the schema can express, so a rule that rejects a valid shape fails at Step 4 rather than in use. DR7 keeps judgement criteria out of the validator |
| A per-shape template set creeps back in | The register #82 exists to remove | DR1 forbids it. AC1.1 is a directory-listing equality, so a third file fails; AC1.3 asserts one key set |
| `.json` placed in `.github/ISSUE_TEMPLATE/` | GitHub ignores it; the template appears to exist and does nothing | DR3, checked by AC1.2 |
| `--create` runs on wrong content and a public issue is created | An issue that must be closed by hand | DR5 makes creation opt-in, DR4 makes validation total, so `--create` cannot run past a failure. Close with `gh issue close`; the number is consumed either way |
| Ordering semantics leak in from #84 | This spec pre-empts #84's queue mechanism | DR6 restricts the Project interaction to `--project`; §4.3 specifies no other Project parameter |
| The schema hardcodes a label or milestone list and goes stale | The register §1.3 forbids | DR2. AC2.6 checks for the type-label literal; AC2.5 requires label/milestone checks against live state |

Rollback is `git revert` of the step commits. The branch is `chore/*`, so no tag, Release,
or version bump exists to unwind. No GitHub object is created by the spec itself.
