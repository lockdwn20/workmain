# Cycle Mechanics — Recon

**Status:** Active
**Kind:** Recon
**Author:** Spanner (Role 1)
**Date:** 20260813
**Originating item:** Issue #80 and children #81–#85

---

## 1. Purpose

Issue #80 states that the implementation cycle is defined but not invocable, sequenceable,
or verifiably complete. Its children propose four mechanisms and one documentation
consolidation. Three of those children carry deliberately outcome-shaped acceptance
criteria, because the mechanism that satisfies them was not known at authoring time.

This document is the read-only census that establishes what the tooling can and cannot
do, so that Analysis can choose mechanisms from fact rather than assumption. It is asked
now because #80 is unscheduled-but-preempting, and because per §1.1 no spec is written
without a recon first.

**Read-only contract.** No code changed, no files created outside this document, no
configuration modified, no GitHub object created or edited during the read. No fixes and
no suggestions appear inline with findings. This document makes no recommendation; the
choice between the mechanisms described in F2–F5 is an Analysis decision.

---

## 2. Scope of the read

**Examined:**

- GitHub GraphQL schema by introspection — `ProjectV2`, `ProjectV2Item`,
  `ProjectV2ItemOrder`, `ProjectV2ItemOrderField`, `ProjectV2CustomFieldType`
- `gh` CLI capability surface — `gh issue create --help`, `gh project item-list --help`,
  `gh --version`, `gh auth status`
- Live repository state — open issues, milestones (via REST), labels, ProjectsV2 linked
  to the repository
- Working tree — presence/absence of `.github/` and `.claude/`, contents of
  `docs/dev/{design,specs,results}/`
- `docs/DEVELOPMENT_STANDARDS.md` §1.1–§1.3, §2.2, §2.5–§2.8
- `CLAUDE.md` Project Status section
- Test suite state (`python -m pytest tests/`)

**Second read pass (20260814), during Analysis.** Undertaken to close N2, which F7 had left
open. Same read-only contract. Examined: GraphQL `IssueTemplate` and `Repository.issueTypes`
by introspection and live query; the full `gh issue create` flag set; the upstream state of
`cli/cli#5865`; and `documentation` / `docs` label usage across all issue states. Produced
F23–F27.

**Deliberately not examined:**

- `workmain/**` application code. Whether any child lands code there — the question that
  settles `chore/*` versus promotion to `feature/*` per #80 — depends on which mechanism
  Analysis selects, and cannot be answered ahead of that choice. **This recon does not
  answer the branch-type question.**
- The five existing milestones' contents beyond their exit conditions and due dates.
- Slack, Clockify, AI provider, and daemon surfaces. Out of scope for cycle mechanics.
- Issue #79 and the other eleven unscheduled issues, beyond counting them.

---

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | `ProjectV2Item` exposes **no `position` field**. Full field set: `content`, `createdAt`, `creator`, `fieldValueByName`, `fieldValues`, `fullDatabaseId`, `id`, `isArchived`, `project`, `type`, `updatedAt` | GraphQL introspection, `__type(name:"ProjectV2Item")` | High |
| F2 | `ProjectV2.items` **does** accept `orderBy: ProjectV2ItemOrder`, whose input fields are `field: ProjectV2ItemOrderField` and `direction: OrderDirection` | GraphQL introspection, `__type(name:"ProjectV2")`, field `items` args | High |
| F3 | `ProjectV2ItemOrderField` has **exactly one** enum value: `POSITION`, described verbatim as *"Order project v2 items by the their position in the project"* (typo GitHub's own) | GraphQL introspection, `__type(name:"ProjectV2ItemOrderField")` | High |
| F4 | Taken together, F1–F3: drag position **cannot be read as a value** but **can be used to order a result set**. A query can return items in rank order; it cannot report an item's rank number | F1, F2, F3 | High |
| F5 | `ProjectV2CustomFieldType` enum: `TEXT`, `SINGLE_SELECT`, `MULTI_SELECT`, `NUMBER`, `DATE`, `ITERATION`. A `NUMBER` field is therefore available as an explicit, readable rank | GraphQL introspection, `__type(name:"ProjectV2CustomFieldType")` | High |
| F6 | `gh project item-list` exposes **no ordering flag**. Its flags are `--field`, `--field-id`, `--format`, `--jq`, `--limit` (default 30), `--owner`, `--query`, `--template`. `--query` filters using Projects filter syntax; it is not documented as ordering | `gh project item-list --help` | High |
| F7 | `gh issue create --template` is documented verbatim as *"Template name to use as starting body text"*. It seeds body text; the help text describes no field-level prompting or validation | `gh issue create --help` | High |
| F8 | The active token holds `read:project` but **not** `project` (write). Reading Projects is possible today; creating or modifying one is not | `gh auth status` — scopes list | High |
| F9 | `gh` version is **2.97.0**, above the ≥2.6x floor CLAUDE.md states for Issues 2.0 (`parent`, `subIssues`, `subIssuesSummary`) | `gh --version` | Low |
| F10 | ProjectsV2 #1 and #2 are both linked to the repository, both `closed: true`, both `items.totalCount: 0` | GraphQL, `user(login:"lockdwn20"){projectV2(number:N)}` | Low |
| F11 | **All five milestones have `due_on: null`.** Milestone numbers 1–5 reflect creation order | REST `repos/:owner/:repo/milestones` | High |
| F12 | Milestone ordering exists only as prose inside milestone descriptions — e.g. Phase 14 carries *"Blocked until both Slack sprints close (Pre-Phase 14 Gate)."* Phases 15 and 18 state no relationship to any other milestone | REST milestone `description` fields | High |
| F13 | Twelve open issues carry no milestone (#68–#79), of which three are labelled `bug` (#73, #74, #79). Counted before #80–#85 were created | `gh issue list --json milestone` | Medium |
| F14 | `.github/` **does not exist** in the working tree — no issue templates, no workflows | Filesystem read at repo root | Medium |
| F15 | `.claude/` **does not exist** at repo or user level — no skills, no agents | Filesystem read, repo root and `~/.claude/` | Medium |
| F16 | §1.3 states verbatim *"a milestone for sequencing and labels for area"* and does not mention the `bug`/`enhancement` type discriminator anywhere. CLAUDE.md Project Status carries it: *"`bug`/`enhancement` is applied only to issues with no milestone"* | `docs/DEVELOPMENT_STANDARDS.md:42-43`; `CLAUDE.md` Project Status | Medium |
| F17 | §2.7 "Session start checklist" is five steps, all git hygiene: `git status`, `git branch`, determine work type, create branch, never work on `main`/`dev`. It defines no reading, no state assembly, and no output | `docs/DEVELOPMENT_STANDARDS.md:176-184` | High |
| F18 | §2.2 `chore/*` covers *"`docs/**`, standards documents, and non-behavioural dev tooling (`.gitignore`, `.githooks/`, editor/CI config)"* and mandates *"No version bump, no `CHANGELOG.md` entry, no tag, no Release."* `.githooks/` is listed as chore-eligible despite `commit-msg` rejecting commits | `docs/DEVELOPMENT_STANDARDS.md:98-107` | Medium |
| F19 | §2.2 requires every tag on `main` to carry a GitHub Release object created with `gh release create --generate-notes` and verified with `gh release view`, *"Added because the step was silently skipped for v1.25.0, v1.25.1, and v1.26.0."* | `docs/DEVELOPMENT_STANDARDS.md:77-79` | Low |
| F20 | Both `documentation` (GitHub default) and `docs` (custom) labels exist, with overlapping meaning | `gh label list` | Low |
| F21 | Test suite at recon time: **934 passed, 0 failed**, 30 warnings, 19.22s — matching the recorded baseline | `python -m pytest tests/` on `dev` | Low |
| F22 | `workmain-notify.service` is a systemd `--user` unit, active since 2026-08-13 08:54 PDT, running `.venv/bin/python -m workmain.daemon.daemon`, postdating every merge on `dev` | `systemctl --user status`, `ps aux` | Low |
| F23 | `gh issue create` carries **`--parent`, `--blocked-by`, `--blocking`, `--type`, `--project`, `--milestone`, `--label`**. Sub-issue linking and native issue *dependencies* are both reachable from the CLI at creation time. F7 examined `--template` only and did not establish this | `gh issue create --help` (2.97.0) | High |
| F24 | `Repository.issueTemplates` is a **server-side** GraphQL field. Its full field set is `filename`, `name`, `title`, `body`, `about`, `labels`, `assignees`, `type` — `body` is a flat `String` with no field-level structure. Templates therefore take effect from the repository's **default branch**, not from the working tree. Live value at read time: `[]` | GraphQL introspection `__type(name:"IssueTemplate")`; live `repository(…){issueTemplates}` | High |
| F25 | **`gh` does not support YAML issue forms.** Upstream request `cli/cli#5865` is OPEN, last updated 2025-02-16, unimplemented at 2.97.0. Consistent with F24: the GraphQL type exposes no per-field structure, so `validations: required` has no effect through any CLI path | `gh issue view 5865 --repo cli/cli`; F24 | High |
| F26 | `Repository.issueTypes` returns **`null`** for this repository — native GitHub Issue Types are an organisation-level feature and are unavailable here. `gh issue create --type` (F23) is therefore inert, and the `bug`/`enhancement` label discriminator remains the only type mechanism | GraphQL live query | Medium |
| F27 | The `documentation` label (GitHub default) carries **0 issues** across all states; the custom `docs` label carries **4** — #47, #48, #53, #59. F20's overlap is one-directional | `gh issue list --state all --label` | Low |

### Explicitly not verified

These are recorded as gaps rather than left silent:

- **N1 — Whether `gh project item-list` returns items in `POSITION` order by default.**
  F6 establishes no ordering flag exists; it does not establish what the default ordering
  is. This cannot be tested without a Project containing items, which requires the write
  scope absent per F8. *Answered by Ray in Analysis — see Q1. Confirmable empirically once
  a Project holds items; the recon did not establish it.*
- **N2 — Whether `gh` supports YAML issue forms (`.yml`) as distinct from Markdown
  templates, and whether `validations: required` has any effect through the CLI path.**
  F7 quotes the help text only. No empirical test was possible: no templates exist (F14),
  and creating them would exceed the read-only contract. **Closed by F24/F25 in the second
  read pass: it does not, and `validations: required` has no CLI effect.**
- **N3 — Whether a `NUMBER` field's values are returned by `gh project item-list --field`
  in a form sortable client-side.** Blocked by the same absence as N1. *Moot under Q1's
  answer, which selects drag `POSITION` and creates no `NUMBER` field.*
- **N4 — Whether any child requires code in `workmain/**`.** Depends on the mechanism
  Analysis selects; see §2. *Closed by Q4.*

---

## 5. Open questions

Answers are Ray's, recorded verbatim in substance during Analysis on 20260814.

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Given F4, does rank come from drag `POSITION` (ordering only, no readable rank value, zero maintained fields) or from an explicit `NUMBER` field (readable and sortable, but a maintained field)? Determines #84's mechanism and whether #84's third AC — *"the Project carries order and nothing else"* — is satisfied by a rank field at all | **Drag `POSITION`.** `gh project item-list` returns items in board position order; the next item is obtained with `--limit`. Ray sets the order through the Web UI once the sequence is established. No `NUMBER` field is created, so #84's third AC is satisfied literally. Supersedes N1 |
| Q2 | Does resolving N1/N2/N3 require granting the `project` scope (F8) before the spec is written, or can the spec carry the mechanism as a decision and let implementation verify it? | *Open — re-put to Ray after F23–F27 were recorded* |
| Q3 | Given F7, is #82's first AC — *"prompts every required field"* — achievable through the `gh` CLI path at all, or does it require the web UI? If it is not achievable, the AC needs rewording before the spec, not during implementation | *Open — re-put to Ray after F23–F27 were recorded* |
| Q4 | Does F18's precedent — `.githooks/` treated as chore-eligible while `commit-msg` actively rejects commits — settle `.claude/skills/` as non-behavioural dev tooling, or is a skill materially different? Determines the branch type per #80 | **Not a live question.** Closed by Ray as splitting hairs on a non-issue. Branch type follows #80's stated rule without further distinction. Closes N4 |
| Q5 | Do F11/F12 mean milestone ordering is migrated into the Project as well, or does the Project rank issues only, leaving milestone sequence in prose? #84's second AC requires rank *within* a milestone but does not state whether milestones themselves are ranked | **Migrated into the Project.** Resolving F11/F12 is the reason the Project is being implemented at all; milestone sequence does not remain in prose. Mechanism for expressing milestone-level order is a follow-up, since a ProjectV2 holds issues, PRs and drafts but not milestones |
| Q6 | Is F20 (`documentation` vs `docs`) in scope for #81, or a separate unscheduled item? | **`documentation` is canonical** — it is a GitHub system label; `docs` is removed in favour of it. Per F27 this relabels #47, #48, #53, #59 and deletes an unused label. Scope — #81 or a separate item — is a follow-up |

---

## 6. Disposition

- Promoted to: *pending — Analysis with Ray*
- Superseded by: *n/a*
