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
| 20260817 | Caliper | F1 — AC1.4 fails on 52 of 57 open issues, because `acs ≥ 1` is applied to a population that predates the rule. It was the sole discharge of #82's first AC | Accepted, reproduced (5 issues carry `**ACs**`). Root cause was mine and is narrower than "too strict": AC1.4 fused *structural coverage* — can the schema express every live shape — with *content compliance*. Only the first is #82's question, and it passes 57/57. AC1.4 now asserts that half alone; body content is a creation-time standard making no retroactive claim. DR7 is what should have caught this at authoring time |
| 20260817 | Caliper | F2 — C8's "one convention" was evidenced from four issues Spanner authored | Accepted, reproduced: 5 issues use `**ACs**`, 36 use an `## Acceptance criteria` form, 16 carry none. C8 restated. §4.2's *"indistinguishable from a hand-written one"* justification is **deleted**, not repaired — it was false. The rendering is a convention this spec establishes |
| 20260817 | Caliper | F3 — AC1.4's map-to-schema step was unspecified, and parser strictness alone decided the verdict | Accepted. §5.1 states the conversion, and it reads metadata only — no Markdown parsing survives in the check, which dissolves the lever |
| 20260817 | Caliper | F4 — AC2.6's derivation was circular, and `gh label list` carries no type marking | Accepted, verified (labels expose name, color, description only). The hedge is removed: §4.1 states the §1.3 parse as *the* mechanism. DR2's premise does not apply where GitHub cannot be asked |
| 20260817 | Caliper | F6 — C6 truncated §1.3's sentence one clause early; the dropped clause makes milestone + type label a legitimate state, which §4.1 hard-fails | Accepted. C6 quotes it whole, and the rule is scoped explicitly to creation — a newly created issue is never a pull-in |
| 20260817 | Caliper | F7 — `grep -c` prints `0` but **exits 1**, so AC2.6 and AC3.4 would fail on a passing implementation | Accepted, reproduced. Both restated as stdout comparisons |
| 20260817 | Caliper | F8 — C3's citation established ownership, not linkage | Accepted. Re-cited to `repository.projectsV2`, which returns #3 open and #2 closed |
| 20260817 | Caliper | F9 — `--blocked-by` takes comma-joined numbers while `--label` repeats; adjacent rows, different forms, undistinguished | Accepted. §4.3 states each form and AC3.2 checks the form, not just presence |
| 20260817 | Caliper | F10 — §7 credited AC1.1 with an exclusivity check it did not make | Accepted. AC1.1 is now a directory-listing equality, so a per-shape template set fails mechanically |
| 20260817 | Ray | F5 — `scripts/**` has no §2.2 category for *new* dev tooling, only a behaviour-neutrality exception a new file cannot meet | **`chore/*` and `scripts/`.** The script concerns development tracking, not application operation, and `scripts/` exists for exactly what supports the project without being part of its functionality. Ray: do not argue it in the spec — apply the standard as already defined. §2.2's missing category, if it needs one, is #86's |

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
- Any change to `workmain/**`, `config/**`, or `templates/**`. Nothing in the application
  imports this script, and the script imports nothing from the application.

## 2. Verified current state

| # | Claim | Evidence |
| --- | --- | --- |
| C1 | `gh` is **2.97.0**, and `gh issue create` carries `--title`, `--body`, `--body-file`, `--label`, `--milestone`, `--parent`, `--blocked-by`, `--blocking`, `--project`, `--type` | `gh --version`; `gh issue create --help`, read at authoring time. Confirms recon F23 |
| C2 | The token holds the `project` scope alongside `repo`, so `--project` works | `gh auth status` — scopes list. Confirms recon F28 |
| C3 | Project **#3 "WorkmAIn Queue"** is **linked to this repository** and is the only open one; a closed untitled #2 is also linked | `gh api graphql` on `repository(owner:"lockdwn20",name:"workmain"){projectsV2}` — returns #3 `closed=false` and #2 `closed=true`. Linkage is what `--project` resolves against, so the ownership query (`gh project list --owner`) is not sufficient evidence and is not cited |
| C4 | `.github/` **does not exist** in the working tree | Filesystem read at repo root. Confirms recon F14 |
| C5 | `scripts/check_release_integrity.py` is the established precedent for standards-enforcing dev tooling: `scripts/`, stdlib only (`argparse`, `re`, `subprocess`, `sys`, `pathlib`), a module docstring stating *why it exists*, `--` flags, non-zero exit on failure. It has no tests | The file's imports and docstring; `grep -rl check_release_integrity tests/` returns nothing |
| C6 | §1.3 states the type rule verbatim and **whole**: *"Labels carry area. `bug`/`enhancement` is the type discriminator, applied only to issues with no milestone — so a type label appearing inside a milestone means that work was pulled in later, not planned as part of it."* The trailing clause is load-bearing: §1.3 treats milestone + type label as a legitimate state carrying information, not as an error. §1.3 also states that what a label means *"is its description on GitHub, readable with `gh label list` — not enumerated here"* | `docs/DEVELOPMENT_STANDARDS.md:45-49`, as it stands after #81 |
| C7 | §1.3 also states *"A milestone carries the exit condition that closes it"* and *"An issue must be independently verifiable on its own"* | `docs/DEVELOPMENT_STANDARDS.md:50-53` |
| C8 | Issue bodies follow **three** conventions, not one. Of 57 open issues: **5** use prose then `**ACs**` then `- ` bullets; **36** use an `## Acceptance criteria` heading; **16** state no acceptance criteria at all. There is no established house style to inherit — §4.2 therefore *establishes* one rather than matching one | `gh issue list --state open --limit 300 --json number,body`, counted at authoring time |
| C9 | The live label set and the live milestone set are both readable in one call each — `gh label list --json name` and `gh api repos/:owner/:repo/milestones --jq '.[].title'`. Neither is transcribed into this spec, per C6's rule | Both commands run at authoring time |
| C10 | The `docs` label no longer exists; `documentation` carries the four issues that had it | `gh label list --limit 100` — confirms #81 shipped |
| C11 | Python is **3.12.3** and no JSON-schema library is a project dependency | `python3 --version`; `requirements.txt` |
| C12 | The `type` discriminator cannot be set through `gh issue create --type`: `Repository.issueTypes` is `null` for this repository | Recon F26, re-checked at authoring time |
| C13 | **GitHub exposes no way to tell a type label from an area label.** `gh label list --json` returns `name`, `color`, `description` and nothing else; with `issueTypes` null (C12) there is no native type facet either. The discriminator is knowable only from §1.3 | `gh label list --limit 100 --json name,color,description`; C12 |
| C14 | The live population satisfies every metadata cross-rule in §4.1: of 57 open issues, **0** carry a milestone *and* a type label, **0** carry neither, and **0** have zero area labels | `gh issue list --state open --limit 300 --json number,milestone,labels`, partitioned at authoring time. This is what AC1.4 asserts |

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
  **Where GitHub cannot be asked, the owning document is** — the type discriminator is not
  a GitHub facet (C13), so it is read from §1.3, which owns the rule. That is the same
  principle, not an exception to it: derive from the source of truth, whatever it is.
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
- **DR6 — Every created issue joins the Queue, and nothing more.**
  `--project "WorkmAIn Queue"` is passed on every creation (Ray, 20260817).
  Membership only: no field is set, no
  position is chosen, and #84 keeps the rank mechanism whole. GitHub auto-populates the
  built-in `Status` field to `Todo`; that is recon F32's known behaviour, is not written by
  this script, and is ignored.
- **DR7 — No rule this spec's own issue would fail.** The process is being built while it
  is in use. Where §1.3 states a *judgement* rather than a mechanical property —
  "independently verifiable", "the exit condition covers every issue" — the validator does
  not attempt to score it, because a validator that guesses at judgement blocks correct
  work.
- **DR8 — Structure is checked against history; content is not.** A rule about *shape* —
  which fields may coexist — must hold for every issue in the repository, because the
  schema claims to express them all; AC1.4 enforces that. A rule about *body content* is a
  forward standard binding what this script creates, and makes no claim about issues
  authored before it. Conflating the two is what made the first draft's coverage check
  unpassable (F1): 52 issues predate the `**ACs**` convention and none of them is a defect.
  A new content rule is therefore never justified by, nor invalidated by, the existing
  population.
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
| 4 | `--check-live` — the structural coverage check, per §5.1 and DR8 | `scripts/gh_issue.py` | AC1.4, AC1.5 |
| 5 | Tests | `tests/test_gh_issue.py`, `tests/fixtures/` | AC4.1, AC4.2 |

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

**This rule is scoped to creation and says nothing about the state of an existing issue.**
§1.3's full sentence (C6) makes milestone + type label meaningful — it marks work pulled
into a milestone after planning. That state is legitimate and is reached by *editing*: an
unscheduled issue acquires a milestone later and keeps its type label. It is not reachable
at creation, because a brand-new issue has not been pulled into anything. Should the
validator ever gate `gh issue edit` — out of scope per §1, which does not put it out of
existence — this rule must be revisited before it is reused, not inherited.

`type` is a separate key from `labels`, and a type label appearing inside `labels` fails,
so there is exactly one path by which the discriminator can be set and the cross-field rule
cannot be routed around.

**Deriving the type-label names.** GitHub cannot be asked (C13), so §1.3 is, per DR2. The
validator reads `docs/DEVELOPMENT_STANDARDS.md`, takes the §1.3 section, finds the single
line containing `type discriminator`, and collects every backtick-delimited token on that
line. Against the current text this yields exactly `bug` and `enhancement` — verified at
authoring time. If the section, the line, or the tokens are absent, the validator **exits
non-zero naming the file and the missing phrase**; it never falls back to a built-in list,
because a fallback would silently outlive the rule it is meant to track. This is the
mechanism, not a contingency.

`.github/issue-templates/issue.template.json` is the skeleton — every key present, values
empty or `null`, ready to copy. `scripts/gh_issue.py --new` writes a copy of it to stdout so
the path never has to be remembered.

### 4.2 Body rendering

The body is assembled from `context` and `acs` into the form below. Per C8 the repository
has three body conventions and no house style, so **this spec establishes one** for
generated issues; it does not match an existing majority and must not be justified as
doing so. The `**ACs**` form is chosen because it is what the cycle-mechanics issues
already use and it is the cheapest to parse should anything later need to. Per DR8 this
binds nothing already in the repository:

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

The two forms differ and the difference is not cosmetic: `gh issue create --help` documents
`--label name` as repeatable and `--blocked-by numbers` as a comma-joined list (C1). An
empty `blocked_by` or `blocking` omits the flag entirely rather than passing an empty value.

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

**On #82's first AC.** *"A json template exists for parent, child, and unscheduled issues"*
is discharged by AC1.4, which validates every open issue through the one schema — so the
shape set is derived from GitHub rather than enumerated by me, and a shape I failed to
anticipate fails the AC. AC1.4 asserts *structural* coverage only, per DR8; it is not a
compliance audit of existing issue bodies and does not become one.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The template directory holds **exactly** the schema and the skeleton, per DR1 — a per-shape template set fails here | `ls .github/issue-templates/ \| sort` prints exactly `issue.schema.json` and `issue.template.json`, two lines. An equality, not two existence tests, so a third file is a failure |
| AC1.2 | Nothing was placed in the GitHub-reserved directory, per DR3 | `test -e .github/ISSUE_TEMPLATE` exits non-zero |
| AC1.3 | The skeleton carries every schema key and no other | `python3 scripts/gh_issue.py --new \| python3 -c "import json,sys; print(sorted(json.load(sys.stdin)))"` equals the sorted key list from `issue.schema.json` |
| AC1.4 | **The single schema expresses every issue shape present in the repository, and every live issue satisfies the cross-field rules.** Structural only, per DR8 | `python3 scripts/gh_issue.py --check-live` exits `0` and prints one verdict line per issue. It reads `gh issue list --state open --limit 300 --json number,title,milestone,parent,labels`, converts each per §5.1, and applies **only** the metadata rules — type-vs-milestone, no type label inside `labels`, ≥ 1 area label, milestone and label names live, parent resolvable. Expected `0` failures across all 57 open issues (C14). Issues are read only; none is modified |
| AC1.5 | AC1.4 makes no body-content assertion, per DR8 — the check cannot be quietly re-fused | `python3 scripts/gh_issue.py --check-live` passes with `--limit 300` even though 52 open issues carry no acceptance criteria in any form (C8). Additionally, the `--check-live` code path contains no reference to `acs` or `context`: `grep -nE 'acs\|context' scripts/gh_issue.py` shows no hit inside the `--check-live` function |
| AC2.1 | A missing required key fails, naming the key | Fixture with `milestone` deleted → exit non-zero, stderr contains `milestone` |
| AC2.2 | An unknown key fails, naming the key | Fixture with `mileston` (typo) → exit non-zero, stderr contains `mileston` |
| AC2.3 | Both halves of the type rule fail, and are distinguishable | Fixture A (`milestone: null`, `type: null`) and fixture B (`milestone` set, `type` set) each exit non-zero with different messages |
| AC2.4 | A type label inside `labels` fails | Fixture with a live type-label name in `labels` → exit non-zero |
| AC2.5 | A non-existent label, milestone, or parent fails against live state | Three fixtures, each exiting non-zero and naming the offending value |
| AC2.6 | The type-label names are parsed from §1.3, never hardcoded — DR2, §4.1 | Two assertions, both required. **(a)** `grep -cE "['\"](bug\|enhancement)['\"]" scripts/gh_issue.py` **prints `0`** — a stdout comparison, since `grep -c` exits `1` on no match and an exit-status reading would fail a correct implementation. **(b)** With `docs/DEVELOPMENT_STANDARDS.md` temporarily copied to a fixture whose §1.3 discriminator line reads ``` `alpha`/`beta` is the type discriminator ```, the validator treats `alpha` and `beta` as the type labels and `bug` as an ordinary area label. (b) is what proves the parse is live rather than a literal wearing a disguise |
| AC2.8 | A missing or unparseable §1.3 discriminator line fails loudly, never silently, per §4.1 | Fixture standards file with the `type discriminator` line deleted → validator exits non-zero and stderr names both `DEVELOPMENT_STANDARDS.md` and `type discriminator`. No issue is created and no built-in list is used |
| AC2.7 | Validation is total, per DR4 | Fixture with three independent errors → stderr names all three in one run |
| AC3.1 | The default run creates nothing | On a valid fixture, `python3 scripts/gh_issue.py <file>` exits `0`, prints the `gh issue create` command, and `gh issue list --limit 300 --json number \| jq length` is unchanged before and after |
| AC3.2 | The printed command carries every populated field **in the form `gh` expects**, per §4.3 | For a fixture with two labels, a type, and two `blocked_by` entries, the printed command contains `--title`, `--body-file`, `--milestone`, `--parent`, `--project`; **exactly three** `--label` occurrences (two areas + the type); and **exactly one** `--blocked-by` whose value is the two numbers comma-joined. Checking presence alone would pass a wrong form that fails at runtime |
| AC3.3 | `--project "WorkmAIn Queue"` is present unconditionally, per DR6 | Printed command for a *minimal* fixture (no milestone, no parent, no blockers) still contains `--project` |
| AC3.5 | Empty `blocked_by` / `blocking` omit the flag rather than passing an empty value | Printed command for the minimal fixture contains neither `--blocked-by` nor `--blocking` |
| AC3.4 | `--type` is never passed, per C12 | `grep -c '\-\-type' scripts/gh_issue.py` **prints `0`** — a stdout comparison, per AC2.6(a)'s reasoning about `grep -c`'s exit status |
| AC4.1 | The validator's rules are covered by tests | `python -m pytest tests/test_gh_issue.py -q` passes, with at least one test per AC2.x row |
| AC4.2 | The suite is unaffected apart from the new file | `python -m pytest tests/` — zero failures, and the pass count equals the baseline recorded at Step 1 plus the count of new tests |

### 5.1 The `--check-live` conversion

AC1.4 rests on converting a live issue into the schema shape. The rule is stated here rather
than left to the implementer, because parser strictness would otherwise decide the verdict —
a lenient parser makes the AC vacuous, a strict one makes it unpassable. **The conversion
reads metadata only, so no Markdown parsing is involved at all:**

| Schema key | Taken from | If absent |
| --- | --- | --- |
| `title` | `.title` | — always present |
| `milestone` | `.milestone.title` | `null` |
| `parent` | `.parent.number` | `null` |
| `type` | the member of `.labels[].name` that the §1.3 parse names a type label | `null` |
| `labels` | `.labels[].name` minus the type labels | `[]` — fails the ≥ 1 area rule |
| `context`, `acs` | **not derived** | not checked, per DR8 and AC1.5 |
| `blocked_by`, `blocking` | **not derived** | not checked — dependencies are not fetched |

`context` and `acs` are supplied as fixed non-empty placeholders so the shared validator can
run unchanged; they assert nothing about the issue. This is the whole of the F3 fix: with no
body parsing in the path, there is no strictness lever to tune.

## 6. Test plan

- **New file:** `tests/test_gh_issue.py`. `scripts/` has no `__init__.py`, so the script is
  loaded by path with `importlib.util.spec_from_file_location`.
- **No `db_session`.** Nothing here touches the database, so §6.1's fixture does not apply.
- **No live network in tests.** The live-state checks (labels, milestones, parent existence)
  are behind a seam that tests substitute — the validator takes the live sets as arguments
  rather than fetching them internally, so the pure rules are testable offline and the
  fetch happens once at the top of the run.
- **The standards path is the second seam.** The §1.3 discriminator parse (§4.1) takes the
  path to `DEVELOPMENT_STANDARDS.md` as an argument rather than resolving it internally.
  AC2.6(b) and AC2.8 both depend on substituting a fixture standards file, and without this
  seam neither is runnable.
- **Fixtures:** JSON files in `tests/fixtures/`, per §6.3, plus two Markdown fixtures for
  the standards seam — one with a substituted discriminator line, one with it removed.
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
| The validator rejects a correctly-authored issue, and issue creation stalls behind the tool | Work stoppage — exactly the outcome Ray flagged in DR7 | AC1.4 runs every existing issue's *metadata* through the rules, so a structural rule stricter than reality fails at Step 4, not in use. DR7 bars the validator from scoring judgement criteria. Content rules carry no such guard by design (DR8) and are held to one bar instead: a rule must be one this spec's own issue would pass |
| A content rule is validated against the existing population and rejected, or a structural rule is exempted from it | Either the first draft's unpassable check (F1) or an unguarded schema | DR8 draws the line and AC1.5 enforces the half that is easy to erode — it asserts `--check-live` makes no body assertion, so re-fusing the two checks fails mechanically rather than passing review unnoticed |
| A per-shape template set creeps back in, one file per shape | The register #82 exists to remove, reintroduced as its own artifact | DR1 forbids it; **AC1.1 is a directory-listing equality**, so a third file at that path fails, and AC1.3 asserts one key set. Corrected after the first draft claimed this guard while AC1.1 ran two existence tests that could not detect an extra file |
| `.json` placed in `.github/ISSUE_TEMPLATE/` and silently ignored by GitHub | The template appears to exist and does nothing; the failure is invisible | DR3, checked by AC1.2 |
| `--create` runs on unvalidated or wrong content and a public issue is created | An outward-facing object exists that must be closed or deleted by hand | DR5 makes creation opt-in and DR4 makes validation total, so `--create` cannot run past a failure. A wrongly-created issue is closed with `gh issue close`; the number is consumed either way |
| Ordering semantics leak in from #84 | This spec pre-empts the queue mechanism it was told not to touch | DR6 restricts the Project interaction to `--project` alone; AC3.3 checks that flag and no other Project parameter is specified anywhere in §4.3 |
| The schema hardcodes a label or milestone list and goes stale | The register §1.3 forbids, one level down | DR2; AC2.6 checks the type-label literal, and AC2.5 requires the label/milestone checks to run against live state |

Rollback is `git revert` of the step commits. The branch is `chore/*`, so no tag, Release,
or version bump exists to unwind. No GitHub object is created by the spec itself.
