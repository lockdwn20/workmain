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
| 20260814 | Ray | Recon Q3 — issue content is authored as JSON, a client-side script validates it, and the validated values stream into `gh issue create` parameters. Required-field enforcement moves from the template (impossible per F24/F25) to the validator | Accepted. This is the whole mechanism of the spec |
| 20260817 | Spanner | The live population has four shapes, not the three #82's first AC names; scheduled-standalone (30 of 57 open issues) is unnamed. Proposed rewording the AC | **Rejected by Ray.** *"The ACs are a check on the issue, not a checklist of what to plan."* The AC is not rewritten; the mechanism is designed to satisfy it. Recorded because the reflex — treating an AC as a scope boundary — is the error, not the finding |
| 20260817 | Ray | One template is acceptable *"if it does plan correctly and is able to perform the required checks to cover all issue conditions"* | Accepted. DR1. The coverage obligation is discharged mechanically by AC1.4, which validates every live open issue through the schema — so "all issue conditions" is derived from GitHub, never enumerated in the template or in this spec |
| 20260817 | Ray | The script validates and then invokes `gh issue create` itself | Accepted. DR5. The outward-facing stop is carried by the tool's `--create` flag, not by process ceremony — see §4 |
| 20260817 | Ray | *"Any issue created within this repo should be assigned to the WorkmAIn Queue project."* | Accepted. DR6. Membership, not rank — #84 keeps the ordering mechanism entirely |
| 20260817 | Ray | *"We are essentially building the process as we are using it and allowances need to be made until it is resolved. Do not make things so rigid that we are creating circular issues over and over."* | Accepted, and it is a design rule rather than a note: DR7. Every validation failure is a *reported* failure with the offending field named, never a silent rewrite; and no rule is added that this spec's own issue could not have passed |
| 20260817 | Spanner | `gh issue create --type` is inert here — `Repository.issueTypes` is `null`, native Issue Types being an organisation feature (recon F26) | Verified again at authoring time. The type discriminator is applied as a **label**, never through `--type`. See C6 |

---

## 1. Scope

**In scope:**

- One JSON schema and one skeleton template describing a WorkmAIn issue.
- `scripts/gh_issue.py` — a stdlib-only client-side validator that checks a JSON issue
  file against the schema and against live GitHub state, then creates the issue through
  `gh issue create`.
- Tests covering the validator's rules.

**Out of scope:**

- **Rank and ordering.** Items land in Project #3 as members; where they sit in the queue
  is #84's mechanism and this spec must not acquire it. See DR6.
- **Issue editing.** `gh issue edit` and any reconciliation of the 57 existing open issues
  against the schema. #82 is about creation. AC1.4 *reads* the existing population as a
  coverage check and changes none of it.
- **Milestone and label administration.** The validator checks names against live GitHub
  and fails on a name that does not exist; it never creates one.
- **`.github/ISSUE_TEMPLATE/`.** Server-side Markdown/YAML templates are a different
  mechanism that recon F24/F25 rules out. Nothing is placed in that reserved directory —
  see DR3.
- Any change to `workmain/**`. This is dev tooling; nothing in the application imports it.

## 2. Verified current state

| # | Claim | Evidence |
| --- | --- | --- |
| C1 | `gh` is **2.97.0**, and `gh issue create` carries `--title`, `--body`, `--body-file`, `--label`, `--milestone`, `--parent`, `--blocked-by`, `--blocking`, `--project`, `--type` | `gh --version`; `gh issue create --help`, read at authoring time. Confirms recon F23 |
| C2 | The token holds the `project` scope alongside `repo`, so `--project` works | `gh auth status` — scopes list. Confirms recon F28 |
| C3 | Project **#3 "WorkmAIn Queue"** is the only open Project on the account and is linked to the repository | `gh project list --owner lockdwn20 --format json` — one row, `closed=false` |
| C4 | `.github/` **does not exist** in the working tree | Filesystem read at repo root. Confirms recon F14 |
| C5 | `scripts/check_release_integrity.py` is the established precedent for standards-enforcing dev tooling: `scripts/`, stdlib only (`argparse`, `re`, `subprocess`, `sys`, `pathlib`), a module docstring stating *why it exists*, `--` flags, non-zero exit on failure. It has no tests | The file's imports and docstring; `grep -rl check_release_integrity tests/` returns nothing |
| C6 | §1.3 states the type rule verbatim: *"`bug`/`enhancement` is the type discriminator, applied only to issues with no milestone"*, and that what a label means *"is its description on GitHub, readable with `gh label list` — not enumerated here"* | `docs/DEVELOPMENT_STANDARDS.md:45-49`, as it stands after #81 |
| C7 | §1.3 also states *"A milestone carries the exit condition that closes it"* and *"An issue must be independently verifiable on its own"* | `docs/DEVELOPMENT_STANDARDS.md:50-53` |
| C8 | Issue bodies already follow one convention: prose context, then a `**ACs**` heading, then `- ` bullets. #82, #83, #84 and #86 all match it | `gh issue view <n> --json body` for each |
| C9 | The live label set and the live milestone set are both readable in one call each — `gh label list --json name` and `gh api repos/:owner/:repo/milestones --jq '.[].title'`. Neither is transcribed into this spec, per C6's rule | Both commands run at authoring time |
| C10 | The `docs` label no longer exists; `documentation` carries the four issues that had it | `gh label list --limit 100` — confirms #81 shipped |
| C11 | Python is **3.12.3** and no JSON-schema library is a project dependency | `python3 --version`; `requirements.txt` |
| C12 | The `type` discriminator cannot be set through `gh issue create --type`: `Repository.issueTypes` is `null` for this repository | Recon F26, re-checked at authoring time |

## 3. Design rules

- **DR1 — One schema, rules not shapes.** There is a single template. Issue *shape*
  (parent, child, scheduled, unscheduled) is not a template variant and is not enumerated
  anywhere; it is a consequence of which fields are populated, and the validator enforces
  the cross-field rules §1.3 already states. A per-shape template set would be a register
  of shapes, and the first shape not on the list would be unprompted — which is the defect
  #82 exists to remove, one level up.
- **DR2 — Nothing is enumerated that GitHub can be asked.** Valid label names, valid
  milestone titles, and whether a parent issue exists are all read live at validation time.
  This spec contains no list of labels, milestones, or issue numbers, and neither does the
  schema. §1.3's own reasoning (C6) applies unchanged to the validator.
- **DR3 — The template is not a GitHub template.** Files live in
  `.github/issue-templates/`, **never** `.github/ISSUE_TEMPLATE/`. The reserved directory
  is read server-side from the default branch and accepts Markdown/YAML only (F24), so a
  `.json` placed there would be silently ignored or mis-parsed. The directory name is
  chosen to be adjacent and obviously not the reserved one.
- **DR4 — Validation is total, and it reports.** All checks run and every failure is
  collected before the script exits; it never stops at the first error. A failure names the
  offending JSON key and what was wrong with it. The script never repairs, defaults, or
  rewrites a field — a bad value is Ray's to fix, not the tool's to guess.
- **DR5 — Creation is opt-in.** The default invocation validates and prints the exact
  `gh issue create` command it *would* run, and exits without creating anything. Passing
  `--create` performs the creation. The authorization stop for an outward-facing,
  publicly-visible action is therefore carried by the tool itself rather than by a step in
  a process document, which is what keeps it from being ceremony.
- **DR6 — Every created issue joins the Queue, and nothing more.** `--project "WorkmAIn
  Queue"` is passed on every creation (Ray, 20260817). Membership only: no field is set, no
  position is chosen, and #84 keeps the rank mechanism whole. GitHub auto-populates the
  built-in `Status` field to `Todo`; that is recon F32's known behaviour, is not written by
  this script, and is ignored.
- **DR7 — No rule this spec's own issue would fail.** The process is being built while it
  is in use. Before any validation rule is added, it is checked against the live population
  by AC1.4; a rule that a real, correctly-authored issue fails is a defect in the rule.
  Where §1.3 states a *judgement* rather than a mechanical property — "independently
  verifiable", "the exit condition covers every issue" — the validator does not attempt to
  score it, because a validator that guesses at judgement blocks correct work.
- **Anything not covered here: STOP and surface to Ray.** No self-resolution, no scope
  adjustment. Unconditional, and independent of step boundaries.

## 4. Steps

Ordered, each committed on completion. **No step is an approval stop** — every step is a
new file on a branch, undone by `git revert`.

| Step | Deliverable | Files | Verification |
| --- | --- | --- | --- |
| 1 | The JSON schema and the skeleton template | `.github/issue-templates/` | AC1.1, AC1.2 |
| 2 | The validator — schema checks, then live-state checks, per DR4 | `scripts/gh_issue.py` | AC2.1 – AC2.6 |
| 3 | `gh issue create` invocation: parameter mapping, `--dry-run` default, `--create` | `scripts/gh_issue.py` | AC3.1 – AC3.4 |
| 4 | Coverage check — every live open issue validates through the schema | `scripts/gh_issue.py` | AC1.4 |
| 5 | Tests | `tests/test_gh_issue.py` | AC4.1, AC4.2 |

### 4.1 The schema

`.github/issue-templates/issue.schema.json` — a hand-rolled schema, since no JSON-schema
library is a dependency (C11) and adding one for a dev script is not warranted. Field set:

| Key | Type | Required | Rule |
| --- | --- | --- | --- |
| `title` | string | yes | non-empty after strip; ≤ 256 characters |
| `context` | string | yes | non-empty after strip. Becomes the body's prose |
| `acs` | array of string | yes | ≥ 1 entry, each non-empty after strip |
| `milestone` | string or `null` | yes — key must be present | if non-`null`, must match a live milestone title exactly |
| `parent` | integer or `null` | yes — key must be present | if non-`null`, must be an existing issue in this repository |
| `labels` | array of string | yes | ≥ 1 entry; every entry must be a live label; **no entry may be a type label** (see below) |
| `type` | string or `null` | yes — key must be present | if non-`null`, one of the live type labels |
| `blocked_by` | array of integer | no — defaults `[]` | every entry an existing issue |
| `blocking` | array of integer | no — defaults `[]` | every entry an existing issue |

Every key is required to be *present* even when its value is `null`. A missing `milestone`
key and a `"milestone": null` are different mistakes, and only the second is a decision.

Any key not in this table is a hard failure naming the key — that is what catches a typo,
which a permissive schema would swallow.

**The type rule (C6, §1.3).** `type` is non-`null` **if and only if** `milestone` is
`null`. Both violations are reported distinctly:

- `milestone` is `null` and `type` is `null` → *unscheduled issue carries no type label*.
- `milestone` is set and `type` is non-`null` → *a scheduled issue must not carry a type
  label*.

`type` is a separate key from `labels`, and a type label appearing inside `labels` fails,
so there is exactly one path by which the discriminator can be set and the cross-field rule
cannot be routed around. Which names count as type labels is not written down here; per DR2
the validator derives them, and the derivation is stated in AC2.6.

`.github/issue-templates/issue.template.json` is the skeleton — every key present, values
empty or `null`, ready to copy. `scripts/gh_issue.py --new` writes a copy of it to stdout so
the path never has to be remembered.

### 4.2 Body rendering

The body is assembled from `context` and `acs` into the convention the repository already
uses (C8), so a generated issue is indistinguishable from a hand-written one:

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
| `labels` + `type` (non-`null`) | one `--label` per name |
| `blocked_by` | `--blocked-by` |
| `blocking` | `--blocking` |
| — | `--project "WorkmAIn Queue"`, always (DR6) |

`--type` is **never** passed: it is inert on this repository (C12), and the discriminator
travels as a label.

### 4.4 Authorization point

**Creating a GitHub issue is outward-facing and publicly visible.** Per DR5 the stop is the
tool's own default: no `--create`, no issue. Ray runs the script, reads the printed command
and the validation report, and re-runs with `--create`. There is no separate approval step
in this document, because the tool cannot create anything without the flag.

No DB migration appears in this spec.

## 5. Acceptance criteria

Mapped to #82's three ACs: AC1.x carries its first, AC2.x its second, AC3.x its third.
AC4.x is the test obligation §1.2 imposes on any spec. Each row is a single assertion.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The schema and skeleton exist at the non-reserved path | `test -f .github/issue-templates/issue.schema.json && test -f .github/issue-templates/issue.template.json` exits `0` |
| AC1.2 | Nothing was placed in the GitHub-reserved directory, per DR3 | `test -e .github/ISSUE_TEMPLATE` exits non-zero |
| AC1.3 | The skeleton carries every schema key and no other | `python3 scripts/gh_issue.py --new \| python3 -c "import json,sys; print(sorted(json.load(sys.stdin)))"` equals the sorted key list from `issue.schema.json` |
| AC1.4 | **The single template covers every issue condition present in the repository.** Every open issue, converted to the JSON form, validates | `python3 scripts/gh_issue.py --check-live` reads all open issues via `gh issue list --json number,title,body,milestone,parent,labels --limit 300`, maps each to the schema shape, validates it, and exits `0` only if every one passes; it prints one line per issue with its verdict. This is the mechanical discharge of "parent, child, and unscheduled" — the set is derived from GitHub, not enumerated. Existing issues are read only; none is modified |
| AC2.1 | A missing required key fails, naming the key | Fixture with `milestone` deleted → exit non-zero, stderr contains `milestone` |
| AC2.2 | An unknown key fails, naming the key | Fixture with `mileston` (typo) → exit non-zero, stderr contains `mileston` |
| AC2.3 | Both halves of the type rule fail, and are distinguishable | Fixture A (`milestone: null`, `type: null`) and fixture B (`milestone` set, `type` set) each exit non-zero with different messages |
| AC2.4 | A type label inside `labels` fails | Fixture with a live type-label name in `labels` → exit non-zero |
| AC2.5 | A non-existent label, milestone, or parent fails against live state | Three fixtures, each exiting non-zero and naming the offending value |
| AC2.6 | The type-label names are derived, not hardcoded — DR2 | `grep -cE "'(bug\|enhancement)'\|\"(bug\|enhancement)\"" scripts/gh_issue.py` returns `0`. The derivation is `gh label list --json name,color` restricted to those the repository marks as type labels, resolved at Step 2; whichever derivation is used, this AC forbids the literal |
| AC2.7 | Validation is total, per DR4 | Fixture with three independent errors → stderr names all three in one run |
| AC3.1 | The default run creates nothing | On a valid fixture, `python3 scripts/gh_issue.py <file>` exits `0`, prints the `gh issue create` command, and `gh issue list --limit 300 --json number \| jq length` is unchanged before and after |
| AC3.2 | The printed command carries every populated field | The printed command for a fully-populated fixture contains `--title`, `--body-file`, `--milestone`, `--parent`, `--label`, `--blocked-by`, `--blocking`, `--project` |
| AC3.3 | `--project "WorkmAIn Queue"` is present unconditionally, per DR6 | Printed command for a *minimal* fixture (no milestone, no parent, no blockers) still contains `--project` |
| AC3.4 | `--type` is never passed, per C12 | `grep -c '"--type"' scripts/gh_issue.py` returns `0` |
| AC4.1 | The validator's rules are covered by tests | `python -m pytest tests/test_gh_issue.py -q` passes, with at least one test per AC2.x row |
| AC4.2 | The suite is unaffected apart from the new file | `python -m pytest tests/` — zero failures, and the pass count equals the baseline recorded at Step 1 plus the count of new tests |

**On AC2.6.** The prohibition is on the *literal*, not on the concept. If no reliable live
signal distinguishes a type label from an area label, that is a finding to surface under §3,
not a licence to hardcode — the fallback is to read the discriminator from
`docs/DEVELOPMENT_STANDARDS.md` §1.3, which owns the rule (C6) and is the one place a change
to it would land.

## 6. Test plan

- **New file:** `tests/test_gh_issue.py`. `scripts/` has no `__init__.py`, so the script is
  loaded by path with `importlib.util.spec_from_file_location`.
- **No `db_session`.** Nothing here touches the database, so §6.1's fixture does not apply.
- **No live network in tests.** The live-state checks (labels, milestones, parent existence)
  are behind a seam that tests substitute — the validator takes the live sets as arguments
  rather than fetching them internally, so the pure rules are testable offline and the
  fetch happens once at the top of the run.
- **Fixtures:** JSON files in `tests/fixtures/`, per §6.3.
- **Baseline:** derive at Step 1 with `python -m pytest tests/` and record it in the Step 1
  commit message, not in this spec.
- **Deviation from C5, stated rather than silent:** `scripts/check_release_integrity.py`
  ships untested, so this spec adds the first tested script. §1.2 requires mechanically
  testable ACs and #82's second AC is entirely about validator behaviour, which cannot be
  asserted any other way. §6.3's *"`scripts/` — utilities and demos, never tests"* governs
  where test *files* live, not whether a script may be tested; the test file is in
  `tests/`.

## 7. Risks and rollback

| Risk | Blast radius | Rollback |
| --- | --- | --- |
| The validator rejects a correctly-authored issue, and issue creation stalls behind the tool | Work stoppage — exactly the outcome Ray flagged in DR7 | AC1.4 runs every existing issue through the schema before the script is used in anger, so a rule stricter than reality fails at Step 4, not in use. DR7 additionally bars the validator from scoring judgement criteria |
| A per-shape template set creeps back in, one file per shape | The register #82 exists to remove, reintroduced as its own artifact | DR1 forbids it; AC1.1 asserts exactly two files at that path and AC1.3 asserts one key set |
| `.json` placed in `.github/ISSUE_TEMPLATE/` and silently ignored by GitHub | The template appears to exist and does nothing; the failure is invisible | DR3, checked by AC1.2 |
| `--create` runs on unvalidated or wrong content and a public issue is created | An outward-facing object exists that must be closed or deleted by hand | DR5 makes creation opt-in and DR4 makes validation total, so `--create` cannot run past a failure. A wrongly-created issue is closed with `gh issue close`; the number is consumed either way |
| Ordering semantics leak in from #84 | This spec pre-empts the queue mechanism it was told not to touch | DR6 restricts the Project interaction to `--project` alone; AC3.3 checks that flag and no other Project parameter is specified anywhere in §4.3 |
| The schema hardcodes a label or milestone list and goes stale | The register §1.3 forbids, one level down | DR2; AC2.6 checks the type-label literal, and AC2.5 requires the label/milestone checks to run against live state |

Rollback is `git revert` of the step commits. The branch is `chore/*`, so no tag, Release,
or version bump exists to unwind. No GitHub object is created by the spec itself.
