# Cycle Close-Out — Recon

**Status:** Active
**Kind:** Recon
**Author:** Spanner (Role 1)
**Date:** 20260819
**Originating item:** Issue #83, child of #80

---

## 1. Purpose

Issue #83 asks for a user-initiated skill in `.claude/skills/` that performs cycle
close-out mechanically: it walks every AC on an issue against delivered code, cannot
report success while any AC is unmet, checks the §2.2 Release object and the §2.6
`ActiveEnterTimestamp`, selects which of those checks apply from the issue's branch type,
and refuses to complete without a `docs/dev/results/` artifact carrying a `Status:` field.

`RECON_CYCLE_MECHANICS.md` covers #80's family but censuses the *queue* and
*issue-creation* surfaces; it establishes nothing about close-out inputs, and two of the
artifacts a close-out would read — `automation/issue_validator.py` and
`scripts/check_release_integrity.py` — did not exist when it was written. This document is
the census of the five surfaces a close-out skill must read: the skill mechanism itself,
the AC surface on issues, the issue → branch-type linkage, the release and deployment
check surface, and the results artifact.

**Read-only contract.** No code changed, no configuration modified, no GitHub object
created or edited during the read. The one file created is this document. No fixes and no
suggestions appear inline with findings. This document makes no recommendation; the
mechanism choice is an Analysis decision.

---

## 2. Scope of the read

**Examined:**

- Working tree — `.claude/` (absent), `.github/ISSUE_TEMPLATE/`, `automation/`,
  `scripts/check_release_integrity.py`, `.githooks/pre-push`, `.gitignore`,
  `pyproject.toml`, `.markdownlint.json`
- `docs/dev/{design,specs,results}/` — every artifact's header block; both templates
- `docs/DEVELOPMENT_STANDARDS.md` §1.1–§1.5, §2.2–§2.8, §7; `CLAUDE.md`
- `docs/archive/design/GITHUB_ISSUES_MIGRATION_MANIFEST.md` — for the numbering rule only
- Live GitHub — every issue body in every state, classified by AC shape; close metadata on
  #81, #82, #86; issue #83, #84, #85, #87 bodies
- Live git — merge subjects on `main`, branch-name shape, `main`/`dev` divergence
- Live systemd — `workmain-notify.service` `ActiveState` and `ActiveEnterTimestamp`
- The installed Claude Code skills reference and the bundled example skills under
  `~/.claude/plugins/marketplaces/claude-plugins-official/`

**Deliberately not examined:**

- `workmain/**` application code. #83 lands no application change; nothing in the close-out
  surface reads it, and the skill treats it as evidence, not as a dependency.
- The test suite was **not run.** A close-out reads the suite's result at run time; the
  count is not a fact this document should carry.
- #84's and #85's mechanisms beyond their stated ACs, and the queue ordering surface —
  owned by `RECON_CYCLE_MECHANICS.md` and not re-read here.
- What a close-out should *do* with a failing check. That is design, not census.

---

## 3. Findings

### 3.1 The skill mechanism

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | `.claude/` **still does not exist** at repo or user level, and no `SKILL.md` exists anywhere outside the bundled official marketplace. `RECON_CYCLE_MECHANICS.md` F15 holds unchanged as of this read | `ls .claude`, `ls ~/.claude/skills`, `find / -name SKILL.md` | Medium |
| F2 | `.gitignore` carries **no** `claude` entry, so `.claude/**` is tracked by git with no change required. A repo-level skill is therefore shareable and reviewable as source | `grep -n claude .gitignore` — no match | Low |
| F3 | A custom skill is `.claude/skills/<name>/SKILL.md` with YAML frontmatter. Documented keys: `name`, `description`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `context: fork`, `agent` | `…/claude-code-setup/skills/claude-automation-recommender/references/skills-reference.md:67-95` | High |
| F4 | Invocation control is a three-way table: default = user **and** Claude; `disable-model-invocation: true` = **user-only**, described verbatim as for *"Side effects (deploy, send)"*; `user-invocable: false` = Claude-only. #83's "user-initiated" maps to exactly one key | `skills-reference.md:100-106` | High |
| F5 | A skill **may bundle its own files** — scripts, checklists, templates — in the skill directory, referenced relatively from `SKILL.md`. Two shipped examples do so: `create-migration` bundles `scripts/validate-migration.sh`, `pr-check` bundles `checklist.md` | `skills-reference.md:161-190, 266-288` | High |
| F6 | `SKILL.md` bodies can embed shell output inline with `` !`cmd` `` — the shipped `pr-check` skill sources its diff as ``- Diff: !`gh pr diff` `` | `skills-reference.md:279-281` | Medium |

### 3.2 The AC surface on issues

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F7 | Issue ACs exist in **three** shapes, not one. **(a)** `**ACs**` followed by flat `-` bullets — the shape `automation/issue_validator.py` renders, carried by every issue created since #81. **(b)** `## Acceptance criteria` followed by `- [ ]` checkboxes — every migrated issue. **(c)** No AC section at all — parent issues whose ACs live on children, and several migrated items. A fourth variant exists on #75, where the checkbox list sits under `## Remaining scope` with no AC heading | `automation/issue_validator.py:224-227` `render_body()`; the classifier in F8 | High |
| F8 | The three shapes are separable mechanically. `gh issue list --state all --limit 200 --json number,body -q '.[] \| "\(.number)\t\(if (.body\|test("(?m)^\\*\\*ACs\\*\\*")) then "acs-bold" elif (.body\|test("(?i)acceptance criteria")) then "prose" elif (.body\|test("(?m)^- \\[ \\]")) then "checkbox" else "none" end)"'` partitions the corpus. The counts are derived by that command and are deliberately not written here | The command above, run at read time | High |
| F9 | **No issue in any state carries a checked box.** One consequence, which is why it was read: a parser must not treat `- [x]` as "AC met". Checkbox state is unmaintained and is not evidence | `gh issue list --state all --limit 200 --json number,body -q '.[] \| select(.body\|test("- \\[x\\]";"i")) \| .number'` returns nothing | Medium |
| F10 | The `**ACs**` section is **terminal** — `render_body()` emits context, a blank line, `**ACs**`, then one `-` line per AC and nothing after. A parser reads from `**ACs**` to end of body; there is no closing delimiter to anchor on | `automation/issue_validator.py:224-227` | Medium |
| F11 | `issue.schema.json` requires `acs` as a non-empty array of strings, so every issue created through the validator has at least one AC. Nothing enforces this on issues created any other way | `.github/ISSUE_TEMPLATE/issue.schema.json`, key `acs` | Low |

### 3.3 Issue → branch-type linkage

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F12 | **The issue records no branch type.** `issue.schema.json`'s full key set is `title`, `context`, `acs`, `milestone`, `parent`, `labels`, `type`, `blocked_by`, `blocking`. `type` is the `bug`/`enhancement` discriminator per §1.3, not a branch type | `.github/ISSUE_TEMPLATE/issue.schema.json` | High |
| F13 | The spec header **does** record it, as **Branch:** `chore/issue-82-issue-creation` (from `main`, merges to `main` and `dev`). Every spec in `docs/dev/specs/` carries the field | Header block of all six specs in `docs/dev/specs/` | High |
| F14 | The spec's back-link to its issue is **not uniform**. Four distinct forms are live in `**Originating item:**` — `Issue #82, child of #80`; `Backlog Item #69`; `Backlog Items #71, #67, #70, #66`; `Ray request, 20260731`. A grep for one form finds a subset | Header blocks, `docs/dev/specs/*.md` | High |
| F15 | **A `#N` citation is ambiguous across the corpus.** Per the migration manifest, *"Legacy `#N` citations in specs, CHANGELOG and commits continue to mean backlog item N, not a GitHub issue."* The collision is live: `FEATURE_ITEM69_WRITE_PATH_CONVERGENCE_SPEC_v1_2.md` cites `Backlog Item #69`, while GitHub #69 is *Clockify Bidirectional Reconciliation*. Migrated issues carry their origin in the body as `> Migrated from \`docs/FEATURE_BACKLOG.md\` **Item 42**` | `docs/archive/design/GITHUB_ISSUES_MIGRATION_MANIFEST.md` § Numbering; the spec header; `gh issue view 69`; `gh issue view 30` body | High |
| F16 | The issue → commit link is **in git, not in GitHub's issue metadata**. `closedByPullRequestsReferences` is `[]` for #81, #82 and #86, because `chore/*` merges locally to both `main` and `dev` with no PR per §2.2. The merge commit records the branch name, and the branch name carries the issue number — `Merge branch 'chore/issue-86-steps-authorization'`. That is the link | `gh issue view {81,82,86} --json closedByPullRequestsReferences`; `git log --oneline --merges main` | High |
| F17 | Branch names created since the issue migration embed the issue number (`chore/issue-81-tracking-semantics`, `chore/issue-82-issue-creation`, `chore/issue-86-steps-authorization`) and the merge subject preserves the branch name. Pre-migration branches do not (`feature/write-path-convergence`, `feature/file-header-removal`). The convention is unwritten — §2.2 states no naming rule beyond the prefix | `git log --oneline --merges main`; `docs/DEVELOPMENT_STANDARDS.md` §2.2 | Medium |

### 3.4 The release and deployment check surface

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F18 | `scripts/check_release_integrity.py` **already implements** the §2.2 half of #83's third AC: for every `vN.N.N` tag it checks a matching non-empty `CHANGELOG.md` section and the existence of a GitHub Release, plus `__version__.py` agreement. It exits non-zero on any mismatch at or above `BASELINE`, is stdlib-only, and takes `--no-remote` / `--show-historical` | `scripts/check_release_integrity.py:1-50`, `BASELINE = "1.26.0"` | High |
| F19 | It is tag-wide: it sweeps every tag rather than one issue's release. Scoping is the caller's, since the close-out already knows which tag it just cut — the script is a **tool the skill invokes**, not a check the skill reimplements | `scripts/check_release_integrity.py`, `main()` | Medium |
| F20 | It is already wired into `.githooks/pre-push`, which builds its path from the repo root as `checker="$repo_root/scripts/check_release_integrity.py"`. Issue #87 proposes moving it to `automation/` and requires every reference updated — `.githooks/pre-push:27` is one, `ISSUE_CREATION_VALIDATION_SPEC.md:87` and `:102` cite the current path, and `docs/archive/design/DESIGN_PLANNING_DOCS_STANDARDS_REVIEW.md:329` cites it in the archive | `.githooks/pre-push:5,27`; `grep -rn check_release_integrity` | High |
| F21 | It has **no tests**. `automation/issue_validator.py` has `automation/issue_validator_test.py` beside it; `scripts/` carries no equivalent | `ls automation/`, `ls scripts/`; `grep -rl check_release_integrity tests/` returns nothing | Medium |
| F22 | §2.2 exempts `chore/*` verbatim — *"No version bump, no `CHANGELOG.md` entry, no tag, no Release."* The release checks are therefore **inapplicable, not merely passing**, for every `chore/*` issue, which is what #83's fourth AC turns on | `docs/DEVELOPMENT_STANDARDS.md` §2.2 | High |
| F23 | The §2.6 deployment check is two commands and a comparison: `ActiveEnterTimestamp` must postdate the `dev` merge commit. Live at read time the service is `active` since `Thu 2026-08-13 08:54:38 PDT`, which **predates** the 20260819 merges of #86 — correct and expected, because a `chore/*` branch changes no code the daemon loads. The check is conditional on what the merge touched, not on the merge existing | `systemctl --user show workmain-notify.service`; `docs/DEVELOPMENT_STANDARDS.md` §2.6 | High |
| F24 | The results template names the file-path trigger for the §2.6 check verbatim: *"Daemon restart (if `workmain/**` or `config/*` changed)"* | `docs/dev/results/_TEMPLATE_RESULTS.md` §5 | Low |
| F25 | `main` currently sits two merge commits ahead of `dev` (`165293f`, `14855fd`), with no commits on `dev` absent from `main`. This is the normal `chore/*` shape — each branch merges to both — and §2.2's *"`dev` always equal to, or one feature ahead of, `main`"* does not describe it | `git log --oneline dev..main`, `git log --oneline main..dev` | Medium |

### 3.5 The results artifact

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F26 | `_TEMPLATE_RESULTS.md` is **the skill's output template**: §3 is an AC table with `Met / Not met / Carried` checked against delivered code, citing Item 32 as the reason it exists; §5 carries the test-suite result, live verification, and the daemon-restart confirmation. The header carries `**Status:**` | `docs/dev/results/_TEMPLATE_RESULTS.md` §3, §5 | High |
| F27 | The template's `Status:` vocabulary is `Shipped \| Superseded` — **no in-progress value**. A results artifact written before close-out completes has no legal status to carry, and #83's fifth AC requires the artifact to exist for the close-out to complete | `docs/dev/results/_TEMPLATE_RESULTS.md:3`; `docs/DEVELOPMENT_STANDARDS.md` §1.5, which allows `Active`, `Shipped`, `Superseded` | High |
| F28 | §1.5's vocabulary and the results template's disagree: §1.5 states *"Every artifact carries a `Status:` field — `Active`, `Shipped`, or `Superseded`"*; the results template offers two of the three | `docs/DEVELOPMENT_STANDARDS.md` §1.5; `_TEMPLATE_RESULTS.md:3` | Medium |
| F29 | The results header carries `**Spec:**` and `**Released as:**` but **no issue number**. There is no machine link from a results artifact back to the issue it closes, in either direction | `_TEMPLATE_RESULTS.md` header; the two live results artifacts | High |
| F30 | **No results artifact exists for #81, #82 or #86.** `docs/dev/results/` holds two `SESSION_HANDOFF_*` documents, both for pre-migration feature sprints. The cause is that neither Spanner nor Anvil recognised the artifact as required — which is the gap #83 exists to close | `ls docs/dev/results/` | High |
| F31 | Both live results artifacts are named `SESSION_HANDOFF_<subject>_<date>.md`, against §1.5's subject-based rule and the template's own `<SUBJECT>_RESULTS.md`. Neither carries an `**Originating item:**` field | `ls docs/dev/results/`; header blocks | Medium |
| F32 | `pyproject.toml` sets `testpaths = ["tests"]`, so a bare `pytest` collects the application suite only; `automation/`'s tests run only when named explicitly. A close-out that runs "the tests" is running one of two disjoint sets | `pyproject.toml` `[tool.pytest.ini_options]`; `ISSUE_CREATION_VALIDATION_SPEC.md` AC4.1, AC4.3 | Medium |

### 3.6 Naming and neighbours

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F33 | #80 assigns three skill namespaces by role — `/spanner-*` *"answers what's next"*, `/caliper-*` *"whether a specification is ready"*, `/anvil-*` *"implementation of approved specifications"*. Close-out belongs to none of the three verbs, and #83's own text proposes no name | `gh issue view 80` body | High |
| F34 | #85 owns *per-role session-open* skills — a different job from close-out, so the two do not collide in function. #85 is blocked by #84; #83 is blocked only by #86, which is closed. #83 therefore ships **first**, and whatever naming convention it sets, #85 inherits | `gh issue view 85`; `gh api …/83/dependencies/blocked_by` → `86`; `…/85/…` → `84` | High |
| F35 | #87 (*move `check_release_integrity.py` to `automation/`*) sits **after** #85 in board order but is a direct dependency of anything the close-out invokes, since it changes the path. Its ACs require every reference updated | Project #3 item order; `gh issue view 87` body | Medium |

### Explicitly not verified

- **N1 — Whether a project-level `.claude/skills/` skill is discovered by this Claude Code
  build without further configuration.** F3 documents the location from the installed
  reference; no skill has ever existed in this repo, so discovery has not been observed.
  The first implementation step settles it empirically.
- **N2 — Whether `` !`cmd` `` substitution (F6) works in a project-level skill, or only in
  plugin-bundled ones.** Only plugin examples were available to read.
- **N3 — What an AC-to-evidence check costs in practice.** Every finding here concerns
  *inputs*. Whether walking N ACs against delivered code is one pass or many is a
  behaviour of the skill, not a property of the surfaces, and cannot be censused.
- **N4 — Whether the migrated issues' ACs are still accurate.** They were written against
  `docs/FEATURE_BACKLOG.md` before the migration. A close-out reads them as authoritative;
  this recon did not audit them.

---

## 5. Open questions

Answered by Ray in Analysis on 20260819 except where marked.

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Given F7, does the close-out read all three AC shapes, or only F7(a)? | **All three.** The migrated issues were never going to match standards written after them. They are corrected at the issue that is being worked, not rewritten as a batch |
| Q2 | Given F12–F17, how does the close-out learn an issue's branch type? | **From git.** The merge commit records the branch name and the branch name carries the issue number (F16). Where an older issue does not follow the convention, it is corrected when that issue is reached |
| Q3 | Given F18–F21, does the close-out invoke `check_release_integrity.py` or carry its own release check? | **Invokes it.** The script is a tool of the skill. Tag-wide versus issue-scoped is not a problem to solve — the close-out already knows which tag it cut |
| Q4 | Given F26/F29/F30, does the close-out **write** the `docs/dev/results/` artifact or **verify** one exists? | **Writes it**, from `_TEMPLATE_RESULTS.md`, which is a tool of the skill. The artifact has not been produced to date because its necessity was not recognised, not because the template was unclear |
| Q5 | Given F33/F34, what is the skill called? #83 ships before #85 and sets the precedent both inherit | *pending* |
| Q6 | Given F27/F28, what `Status:` does a results artifact carry while close-out is running? | *pending* |
| Q7 | Given F30, are #81, #82 and #86 backfilled? | **No.** Consistent with Q1/Q2 — closed work is not reopened to satisfy a standard written after it |
| Q8 | Given F16/F29, is a durable issue ↔ artifact link created? | **Not needed as a new mechanism.** Git already carries it (F16). Whether the results header gains an `**Originating item:**` field rides Q6 as a template question |

---

## 6. Disposition

- Promoted to: *pending — Analysis with Ray, then spec*
- Superseded by: *n/a*
