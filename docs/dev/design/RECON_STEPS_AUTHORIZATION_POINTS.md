# Steps and Authorization Points — Recon

**Status:** Shipped
**Kind:** Recon
**Author:** Spanner (Role 1)
**Date:** 20260818
**Originating item:** Issue #86, child of #80

---

## 1. Purpose

Issue #86 replaces gate discipline with two separated concepts — **steps** (ordered work
inside a spec, committed and revertible individually, no approval stop) and
**authorization points** (attached to irreversible or outward-reaching *actions*). Its
first and last acceptance criteria require the two governing documents to be read against
each other and every duplicated or conflicting process rule resolved into exactly one of
them. This recon is that read.

It answers two questions: where does gate vocabulary actually appear in the live document
set, and which process rules are currently stated in both `CLAUDE.md` and
`docs/DEVELOPMENT_STANDARDS.md`.

**Read-only contract.** No file was modified. No fixes were applied and no suggestions
appear alongside the findings. Decisions belong to Analysis and are recorded in §5, not
here.

## 2. Scope of the read

**Examined in full:**

- `CLAUDE.md` — every section.
- `docs/DEVELOPMENT_STANDARDS.md` — every section.
- `docs/dev/specs/_TEMPLATE_SPEC.md`, `docs/dev/design/_TEMPLATE_DESIGN.md`,
  `docs/dev/results/_TEMPLATE_RESULTS.md`.
- `Status:` field of every artifact in `docs/dev/specs/`, `docs/dev/design/`,
  `docs/dev/results/`.
- `docs/dev/specs/TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md` and
  `docs/dev/specs/ISSUE_CREATION_VALIDATION_SPEC.md` — the two non-Shipped specs, read for
  the structure they already adopted.
- Branch topology: `origin/main` against `origin/dev`, and the unmerged local
  `chore/cycle-mechanics-recon`.
- `.github/ISSUE_TEMPLATE/issue.template.json`, `.github/ISSUE_TEMPLATE/issue.schema.json`,
  and `automation/issue_validator.py` — #82's delivered issue surface, read for gate and
  step vocabulary only.
- Repo root and `~/.claude/`, for the existence of skill or command surfaces.

**Deliberately not examined:**

- The four `Status: Shipped` specs and both session handoffs, beyond their `Status:` field
  and their gate vocabulary. They are historical records; whether they are retrofitted is
  Q3, and nothing here depends on their internal detail.
- `docs/archive/**` — never authoritative per `CLAUDE.md` § Project Status.
- Any file under `workmain/**`, `tests/**`, or `automation/**`. #86 changes no application
  behaviour, and no finding here required reading application source.
- Issues #83, #84, #85 beyond #86's stated blocking relationship to #83.

## 3. Findings

### 3.1 Gate vocabulary in the live governing set

| # | Finding | Evidence (file:line) | Severity |
| --- | --- | --- | --- |
| F1 | `CLAUDE.md` § Critical Rules carries the gate rule verbatim: *"**Gate discipline ⭐.** Gates are hard stops: stop, report status, wait."* with *"Never proceed past a gate without Ray's explicit 'proceed'."* | `CLAUDE.md:118-120` | High |
| F2 | `CLAUDE.md` Role 3 is internally inconsistent: line 48 reads *"report discrepancies before touching Gate 1"* while line 52 reads *"**STOP at the current step**"*. Not accidental — F3 records the cause | `CLAUDE.md:48`, `CLAUDE.md:52` | Medium |
| F3 | The line 52 `gate`→`step` edit was made by #82 and is documented there as *"Committed on this branch, covered by no AC"*. Line 48 was left untouched, producing F2 | `docs/dev/specs/ISSUE_CREATION_VALIDATION_SPEC.md:89` | Medium |
| F4 | The `DEVELOPMENT_STANDARDS.md` preamble assigns ownership: *"`CLAUDE.md` owns who does what (three-role model, **gate discipline**, key design decisions)"*. The document's own header names gate discipline as a CLAUDE.md-owned concept | `docs/DEVELOPMENT_STANDARDS.md:3-4` | High |
| F5 | §1.1's pipeline diagram terminates `… → IMPLEMENTATION → GATE REVIEW → COMMIT`, placing gate review between implementation and commit | `docs/DEVELOPMENT_STANDARDS.md:19` | High |
| F6 | §1.1 bullets state *"**Implementation** — Role 3, gate by gate, from the approved spec only"* and *"**Gate review** — human approval at every gate; DB migrations are always a hard gate"* | `docs/DEVELOPMENT_STANDARDS.md:27-28` | High |
| F7 | §1.3 states *"Work that only makes sense as a set becomes a parent issue with children, never one issue spanning several gates"* — the split rule is currently expressed in gate terms | `docs/DEVELOPMENT_STANDARDS.md:53` | High |
| F8 | §2.2's hotfix→feature exception instructs *"merge into the feature branch at Gate 0"* — gate vocabulary inside the git section | `docs/DEVELOPMENT_STANDARDS.md:119` | Medium |
| F9 | §2.4 states the commit-subject rule entirely in gate terms: *"Gate context belongs in the body, not the subject — `feat(notes): converge write path` with `Gate 3 of 7` in the body, never `Gate 3: ...` as the subject"* | `docs/DEVELOPMENT_STANDARDS.md:139-141` | Medium |
| F10 | §6.4 closes with *"That is not a design question and does not stop a gate"* | `docs/DEVELOPMENT_STANDARDS.md:598` | Low |
| F11 | `_TEMPLATE_SPEC.md` carries gate structure in four places: §3's *"**STOP at the gate and surface to Ray**"*, §4 titled *"Gates"* with a `Gate / Deliverable / Files / Verification` table, §4's DB-migration callout, and §7's *"how to undo each gate"* | `docs/dev/specs/_TEMPLATE_SPEC.md:65`, `:67-78`, `:103` | High |
| F12 | `_TEMPLATE_RESULTS.md` §2 is titled *"What shipped, by gate"* with a `Gate / Delivered / Files changed / Tests` table, and §3 refers to issues *"surfaced at a gate and resolved by Ray mid-flight"*. **No #86 acceptance criterion names this file** | `docs/dev/results/_TEMPLATE_RESULTS.md:27-29`, `:50` | Medium |
| F35 | §2.7's session-start checklist routes work type by *"phase/multi-gate → `feature/*` from `dev`"* — gate vocabulary carrying decision weight in the branch-selection rule. Found on a word-boundary sweep after the first pass missed it | `docs/DEVELOPMENT_STANDARDS.md:185` | Medium |
| F13 | The target shape already exists in practice. Both non-Shipped specs use `## 4. Steps` rather than a gate table, and #81's Decision Log records Ray's 20260814 decision that *"§4 is **Steps**, not gates. Approval attaches to *irreversible actions*"*, together with the ruling that codifying it is #86's job and *"This spec adopts the steps/authorization shape ahead of that issue and does not codify it"* | `docs/dev/specs/TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md:20-21`, `:108`; `docs/dev/specs/ISSUE_CREATION_VALIDATION_SPEC.md:162` | High |

### 3.2 Process rules stated in both documents

`CLAUDE.md:7` asserts *"Nothing is duplicated between them."* `DEVELOPMENT_STANDARDS.md:7`
asserts *"Nothing here is duplicated in `CLAUDE.md`."* Both statements are false as of this
read. #86's final AC — *"No process rule is stated in both documents"* — is therefore not a
touch-up; the following are live violations. The set below is what this read found; it is
not asserted to be exhaustive, and the acceptance criteria derive their own set from a
command rather than from this table.

| # | Rule stated twice | In `CLAUDE.md` | In `DEVELOPMENT_STANDARDS.md` | Severity |
| --- | --- | --- | --- | --- |
| F14 | DB migrations require explicit human approval, with the same *"the approval is the gate, not the spec that contains it"* clause in both | `:120` | `§4.5`, `:350` | High |
| F15 | No implementation without an approved spec | `:117` | `§1.1`, `:26` | High |
| F16 | Every claim about existing behaviour is verified against source at authoring time; cite file and symbol | `:24` | `§1.2`, `:32` | High |
| F17 | Defects found during verification become their own hotfix rather than sprint scope | `:25` | `§1.2`, `:35` | High |
| F18 | Verify every AC against delivered code before marking complete — the Item 32 narrative is told in full in both | `:233` | `§1.3`, `:54-58` | High |
| F19 | Integration over separation — enhance an existing command file; new files only for approved distinct groups | `:123` | `§3.6`, `:285-289` | Medium |
| F20 | `scripts-deprecated/` is excluded from test collection; do not add to it | `:111` | `§6.3`, `:592-593` | Low |
| F21 | Dev artifacts always live in `docs/dev/<type>/`, never in the `docs/` root | `:243` | `§7`, `:625` | Medium |
| F22 | `get_session()` is a method on `Database`, not a module-level function; `get_db()` first | `:230` | `§4.1`, `:301-302` | Medium |
| F23 | SQLAlchemy session discipline — objects re-queried in the session that modifies them; cross-boundary passing fails silently | `:231` | `§4.2`, `:316-321` | Medium |
| F24 | Staged output goes to `staging/`, not `output/`, which does not exist | `:232` | `§7`, `:617` | Low |
| F25 | A `dev` merge is not deployed until `workmain-notify.service` restarts and `ActiveEnterTimestamp` postdates the merge | `:237` | `§2.6`, `:165-179` | Medium |

F18 and F22–F25 all sit in `CLAUDE.md` § Common Pitfalls (`:227-237`). Most of that
section restates a rule `DEVELOPMENT_STANDARDS.md` also states. The bullets that do **not**
have a counterpart there are Master Logs (`:229`), `correction_note` vs `corrected_content`
(`:234` — which duplicates `CLAUDE.md`'s own Key Design Decisions section rather than the
other document), phase scope creep (`:235`), and component-verified ≠ integration-verified
(`:236`).

### 3.3 Conflicts, as distinct from duplication

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F26 | #86's issue body names *"restarting a live service"* as an authorization point. §2.6 makes restarting `workmain-notify.service` **mandatory** after a `dev` merge, and §2.8 lists reporting a merge as deployed without it as a "never do". The two documents would place an approval stop and a standing obligation on the same act | Issue #86 body; `docs/DEVELOPMENT_STANDARDS.md:165-179`, `:201` | High |
| F27 | §1.3 already carries an independent-verifiability sentence — *"An issue must be independently verifiable on its own"* (`:52`) — immediately before the gate-worded split rule at `:53`. #86's fourth AC asks for a stated split test keyed on independent verifiability; a partial form exists and is not currently expressed as a test | `docs/DEVELOPMENT_STANDARDS.md:52-53` | Medium |
| F28 | The unconditional stop-and-surface rule that #86's sixth AC requires be retained is currently stated three times: `CLAUDE.md` § Critical Rules (`:121`), `CLAUDE.md` Role 3 as a four-step procedure (`:50-55`), and `_TEMPLATE_SPEC.md:65`. Two of the three tie it to a gate or step boundary | `CLAUDE.md:121`, `:50-55`; `docs/dev/specs/_TEMPLATE_SPEC.md:65` | High |

### 3.4 Artifact and branch state

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F29 | Four specs are `Status: Shipped` (`FEATURE_FILE_HEADER_REMOVAL_SPEC_v1_3.md`, `FEATURE_ITEM69_WRITE_PATH_CONVERGENCE_SPEC_v1_2.md`, `TASK_MATCH_DATA_INTEGRITY_SPRINT_SPEC_v1_3.md`, and the Item 69 spec's embedded sub-status). **Two are `Status: Approved`, not Shipped** — `TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md` (#81) and `ISSUE_CREATION_VALIDATION_SPEC.md` (#82) | `grep "^\*\*Status:\*\*" docs/dev/specs/*.md` | Medium |
| F30 | Both `Status: Approved` specs have shipped — #81 and #82 are closed and merged (`fbc62cb`, `7e2be25`) — yet neither status was advanced to `Shipped`. This is the close-out gap #83 exists to address, observed live | `gh issue list --state closed`; `git log origin/main..origin/dev`; F29 | Medium |
| F31 | `docs/dev/design/RECON_CYCLE_MECHANICS.md` exists only on the unmerged local branch `chore/cycle-mechanics-recon`. `ISSUE_CREATION_VALIDATION_SPEC.md:9` cites it as its design study, and that spec is merged to both `main` and `dev`. The citation does not resolve on either integration branch | `git branch -a`; `git log --all -- docs/dev/design/RECON_CYCLE_MECHANICS.md`; filesystem read of `docs/dev/design/` | High |
| F32 | `origin/main` and `origin/dev` are **content-identical** — `git diff origin/main origin/dev` is empty. `dev` carries six merge commits `main` does not, all `chore/*`, whose content reached `main` by its own merges. Reading either branch yields the same governing documents | `git diff --stat origin/main origin/dev`; `git log --oneline origin/main..origin/dev` | Low |
| F33 | The #82 issue surface is **clean of both vocabularies** — `.github/ISSUE_TEMPLATE/issue.template.json`, `issue.schema.json`, and `automation/issue_validator.py` contain no occurrence of `gate` or `step` in any case. #86 does not reach the issue-creation path | `grep -in "gate\|step"` across all three files, zero hits | Medium |
| F34 | `.claude/` **still does not exist** at repo or user level — no skills, no commands. The #80 recon's F15 holds unchanged, and #85 has not yet created content. There is no fourth surface | Filesystem read, repo root and `~/.claude/` | Medium |

### Explicitly not verified

- **N1 — Whether any `.claude/` skill, hook, or command text references gate vocabulary.**
  **Closed by F34: the directory does not exist, so there is nothing to reference it.**
- **N2 — Whether `CHANGELOG.md` entries reference gates.** Not read. It is an append-only
  historical record, so the answer does not change #86's scope, but the claim is not made
  either way.
- **N3 — Whether the four Shipped specs' gate tables would still parse as coherent under
  step vocabulary.** Not examined; they were read for vocabulary presence only. Depends on
  Q3.

## 5. Open questions - all closed

Q1–Q6 were answered during Analysis on 20260819; the answers are recorded in `STEPS_AND_AUTHORIZATION_POINTS_SPEC.md`'s Decision Log

## 6. Disposition

Analysis complete — Q1–Q6 were answered on 20260819 and are recorded in the spec's Decision Log. Findings are complete for the surfaces named in §2. N1 is closed by F34; N2 and N3 do not change scope. Taken with F33 and F34, the surfaces #86 touched are exactly four files: `CLAUDE.md`, `docs/DEVELOPMENT_STANDARDS.md`, `docs/dev/specs/_TEMPLATE_SPEC.md`, and `docs/dev/results/_TEMPLATE_RESULTS.md`.

- Promoted to: `docs/dev/specs/STEPS_AND_AUTHORIZATION_POINTS_SPEC.md`
- Superseded by: *n/a*
