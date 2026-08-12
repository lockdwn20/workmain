# Planning Documents Standards Review — Design Study

**Status:** Superseded
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20260806
**Originating item:** Ray request, 20260806
**Superseded by:** the GitHub Issues migration — see §7.

---

## 1. Purpose

Ray asked for a senior-level review of `docs/implementation-checklist.md` and
`docs/FEATURE_BACKLOG.md` against the project's own written standards, on the premise that
the two documents have drifted out of compliance and are steering development incorrectly.

The review question is narrower than "are these documents tidy." It is: **can Role 3 be
handed the next sprint from these documents and build the right thing?** The answer today
is no, and the reason is not formatting. Four items the checklist schedules as future work
were closed in the backlog on 20260725, and one High-priority item that replaced them is
absent from the checklist entirely. The next sprint's scope, as written, is wrong.

This document reports what was found, proposes a structural correction, and annotates the
decisions that are Ray's to make (§5) rather than raising them mid-review.

## 2. Scope of the read

**Read in full:** `docs/implementation-checklist.md` (1403 lines),
`docs/FEATURE_BACKLOG.md` (3424 lines), `docs/DEVELOPMENT_STANDARDS.md` (611 lines),
`CLAUDE.md` (241 lines).

**Read selectively, to verify a specific claim:** `docs/dev/specs/` and `docs/dev/design/`
(existence and filenames only), `workmain/database/repositories/task_status_repo.py`,
`workmain/orchestration/action_executor.py`, `workmain/workflows/eod_workflow.py`,
`workmain/__version__.py`, git history at `8bc1dc1` and across all refs.

**Deliberately not examined:** the correctness of any *implemented* feature. This review
takes shipped code as given and asks only whether the two planning documents describe it,
and the work ahead of it, accurately. `CHANGELOG.md`, `docs/AI_SETTINGS_GUIDE.md`,
`docs/OAUTH_SETUP.md`, and `docs/SLACK_SETUP.md` were not reviewed except where the two
target documents cite them.

**Verification standard applied:** every claim below was checked against source, git, or
the live file at authoring time. Nothing here is asserted from recollection. Where a claim
rests on absence of evidence, that is stated explicitly.

## 3. Findings

### 3.1 What is working

Stating this first, because the remediation plan deliberately preserves it and because an
accurate review has to distinguish structural failure from sloppiness. There is little
sloppiness here.

- **The effort reconciliation is arithmetically correct.** `FEATURE_BACKLOG.md:428–436`
  claims ~59–69 hours over a named item set. Summing the register's own figures for
  Items 1–9, 12, 16, 19, 29, 30, 42, 44–48, 55, 57, 59 gives 58.83–68.83. It reconciles,
  and the excluded items (TBD/varies/Unknown) are named rather than silently dropped.
- **The Summary Statistics counts reconcile.** 35 Complete + 1 Partial + 4 Closed/Stale +
  26 Open-targeted + 1 Conditional + 2 Indefinitely + 3 Redirect = 72 = stated total.
- **AC dispositions are recorded honestly.** Where an AC was not met, the backlog says so
  in specific terms and names where it went (Item 66's AC11 → Item 72). This is the
  opposite of the Item 32 failure mode, whatever the status label says about it (F3).
- **Design-decision provenance is captured.** The checklist records *why* a design changed,
  not merely that it did — `implementation-checklist.md:1099–1112` on `workmain config` is
  a good example of correctly refusing to treat inherited scope as settled.

The problems below are structural, not clerical. They come from two documents both owning
item scope, and from a record that grew append-only until it outweighed the plan.

### 3.2 Findings table

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | The next sprint's scope is stale. `SLACK_LLM_COMPLETION_SPRINT` Gates 2–4 schedule four items the backlog closed on 20260725 | `implementation-checklist.md:971–1017` vs `FEATURE_BACKLOG.md:980` (#23 Closed), `:1212` (#31 Closed), `:1736` (#43 Closed), `:1862` (#46 Closed) | Critical |
| F2 | Gate 2 specifies the exact design that was rejected at closure | Checklist `:977–983` mandates active-meeting-window auto-link via "a `system_state` key set at T2 and cleared at T3"; `FEATURE_BACKLOG.md:1751–1752` records "Time-window auto-link design rejected (meeting always named in message header; time-of-entry must not factor in)" | Critical |
| F3 | Item #63 (High priority, register target "Slack_LLM Sprint G2") appears nowhere in the checklist. Items #64, #65 likewise absent | `FEATURE_BACKLOG.md:367–369` vs `grep '#63\|#64\|#65' docs/implementation-checklist.md` → no hits | Critical |
| F4 | Items are marked `✓ Complete` with unmet ACs, and this is now cited as precedent | `FEATURE_BACKLOG.md:3003–3007` (Item 66: "AC11/AC12 carried… Per Item 62 precedent"); AC11 marked `✗ as written` at `:3042`. Inverts `DEVELOPMENT_STANDARDS.md:44–46` | Critical |
| F5 | Two documents cited as decision authorities were never tracked in git, in any ref, ever | `SESSION_HANDOFF_TASK_MATCH_PLANNING_20260725.md` (cited checklist `:162, :857, :938` as the authority for decision TM6) and `SESSION_HANDOFF_ITEM69_SCOPE_LOCK_20260727.md` (cited `FEATURE_BACKLOG.md:3239` for WPC3–WPC6). `git log --all --name-only` → no match | Critical |
| F6 | Eleven further cited artifacts were deleted with `docs/dev/archive/` and are now unresolvable without git archaeology | Commit `8bc1dc1`, 122 files. Affects citations to `RECON_SPEC_ITEM66_TASK_MATCH_QUALITY_20260725.md` (checklist `:917`), `RECON_SPEC_SLACK_LLM_COMPLETION_SPRINT_20260725.md`, `BACKLOG_ITEM60_..._SPEC_v1_2.md`, and 8 others | High |
| F7 | Twelve citations point at standards documents deleted on 20260806 | `CLI_STANDARDS.md` / `GIT_WORKFLOW_STANDARDS.md`: 6 in the checklist (`:61, :79, :673, :880, :1092, :1105`), 6 in the backlog (`:31, :102, :1029, :1041, :1053, :2590`) | High |
| F8 | Version-history blocks in both documents, prohibited for every document since 20260806 | `implementation-checklist.md:1–141` (141 lines), `FEATURE_BACKLOG.md:1–259` (259 lines). Violates `CLAUDE.md` § Documentation Standards, "No version headers or version-history blocks in any document" | High |
| F9 | Eight cross-document citations address the backlog *by version number*, and those versions exist only inside the block F8 requires deleting | Checklist `:13, :24, :32, :37, :42, :48, :53, :77` — e.g. "Full detail in `docs/FEATURE_BACKLOG.md` v5.42, Items 66/67/70/71/72" | High |
| F10 | The checklist contradicts itself three ways on Item #58 | `:683` "Not delivered this sprint — carried forward"; `:843` "[x] T4 activity-gap suppression (Backlog #58) — Complete" listed as a *sprint* deliverable; `:1350` timeline row "#58 activity-gap detection not delivered, carried forward". (#58 did ship — as hotfix v1.24.1, outside the sprint) | High |
| F11 | Item #48 — High priority, Partial, two ACs carried — is scheduled nowhere forward. Every checklist mention is retrospective | Backlog `:352` (Partial, High, "Phase 14"); checklist Phase 14 §`:1082–1150` does not mention it | High |
| F12 | Status vocabulary has drifted to ~50 distinct strings across 73 `Status:` fields; the standard sanctions three | `DEVELOPMENT_STANDARDS.md:42–43` permits `Open — Deferred to Phase X`, `Complete`, `Closed — Stale`. Live values include `~ Partial`, `Closed — Won't Implement`, `Closed — Resolved by Architecture`, `Closed — Superseded by Item 63`, `✓ COMPLETE`, `✓ Complete`, `✓ Resolved`, `Conditional`, `Deferred Indefinitely`, `Merged into Item 20` | Medium |
| F13 | The register's `✓` column conflates Complete with Closed | Items 14, 15, 23, 31 carry `✓` at `:318, :319, :327, :335` but are counted under Closed/Stale at `:385`. Per v5.1 the column was defined as "✓ complete only" | Medium |
| F14 | The Target Phase table is unfiltered by status, so it cannot be used for planning | `:409` "Phase 14 \| 47, 48, 50, 56, 58" — Items 50, 56, 58 are all Complete. The Priority table has the same defect and covers only 44 of 72 items | Medium |
| F15 | The checklist's headline project state is six minor versions stale | `:148` "**v1.23.0 delivered:**"; `workmain/__version__.py:5` is `1.29.0` | Medium |
| F16 | Both documents transcribe test counts and version numbers into prose, against the standard's own reasoning | ~40 instances (`921→934 tests`, `840→869`, `671 tests`). `DEVELOPMENT_STANDARDS.md:516–518`: "Do not transcribe a baseline into this document; it goes stale immediately" | Medium |
| F17 | The checklist uses seven status conventions simultaneously | `- [x]` (194), `- [ ]` (117), `- ✓` (32, Phases 10 and 13 only), `✓ COMPLETE` (21), `⏳` (5), `- [~]` (5), `⚠ PARTIAL` (2) | Low |
| F18 | Filename `implementation-checklist.md` is the only lowercase document in `docs/` | vs `FEATURE_BACKLOG.md`, `DEVELOPMENT_STANDARDS.md`, `AI_SETTINGS_GUIDE.md`, `OAUTH_SETUP.md`, `SLACK_SETUP.md`. Already known and deferred by Ray | Low |

### 3.3 Conflicts in documents outside the two under review

Ray asked specifically that these be identified.

**C1 — `DEVELOPMENT_STANDARDS.md` §1.3 and `CLAUDE.md` § Common Pitfalls both assert, in
the present tense, a fact that is no longer true.**

Both say `set_forwarding()` has zero callers, offered as live evidence that Item 32 was
falsely closed:

> `DEVELOPMENT_STANDARDS.md:44–46` — "Item 32 was marked complete with all four ACs unmet;
> `set_forwarding()` still has zero callers. A spec's say-so is not evidence."

Verified against source: there is no method named `set_forwarding()` in the codebase.
`set_forwarding_note()` exists at `task_status_repo.py:127` with three live callers —
`action_executor.py:304`, `eod_workflow.py:568`, `eod_workflow.py:800`. The third is the
note↔note dedup path that satisfies Item 32's actual AC, delivered in
Ops_Config_Correction_Sprint Gate 5. Item 32 is `✓ Complete` in the backlog and the
delivery is real.

The *lesson* remains valid and should survive. The *evidence sentence* is stale and, worse,
is the sole worked example behind the project's most important backlog rule. Leaving a
falsifiable claim attached to that rule weakens it. This is a conflict between the standards
documents and delivered code, not between the two documents under review — but it must be
corrected in the same pass, because F4 proposes tightening the very rule it illustrates.

**C2 — `CLAUDE.md` § Locked Architecture Decisions OQ4 describes Items #48 and #32 as work
still to be specced together.**

> "Items #48 and #32 must be specced and implemented together."

Both were specced and implemented together, in Ops_Config_Correction_Sprint Gate 5. #32 is
Complete; #48 is Partial with two carried ACs. The locked decision reads as forward-looking
direction when it is now a description of something already done. Low severity, but it is
the kind of drift that causes an implementer to look for work that no longer exists.

**C3 — No conflict found between the two documents and `docs/DEVELOPMENT_STANDARDS.md` §2
(git), §3–§7.** The workflow rules are consistently *described*; the failures above are
failures to apply the documentation standards, not contradictions of them. Worth stating
explicitly so the remediation is not scoped wider than it needs to be.

### 3.4 Root cause

Three mechanisms produce every Critical and High finding above. Naming them matters,
because a fix that does not address them will be re-doing this review in two sprints.

**Two documents own the same fact.** Item scope lives in the backlog item *and* in the
checklist gate that schedules it. Nothing keeps them in step. When four items were closed
on 20260725, the backlog was updated and the checklist was not — producing F1, F2 and F3.
This is the single-owner rule failing at the document level: the backlog owns item state,
but the checklist restates it, so "updating the backlog" silently means "updating half the
record." Every planning-document standard the project has assumes one owner per fact.

**The record grew inside the plan.** 141 and 259 lines of version history, plus per-item
close-out narrative, now dominate both files. The checklist's first 141 lines must be read
past before reaching a single actionable item, and its most load-bearing sentence — which
sprint comes next — sits at `:149`, expressed in terms of a version that shipped six
releases ago. Git already holds this history. Retaining it in-file made the plan hard to
scan, and hard-to-scan plans do not get reconciled.

**Close-out reconciliation is a manual, unaided pass.** Every finding F10 through F15 is a
transcription that was correct when written and decayed afterwards. There is no check that
would catch a register `✓` disagreeing with a Status field, or a Target Phase row listing
completed items, or a citation to a deleted file. The discipline here is genuinely high —
the arithmetic reconciles, which is rare — and it is still not enough, because the surface
requiring manual reconciliation is far larger than it needs to be.

## 4. Options

### Option A — Patch the findings in place

Fix each finding individually. Update the four stale gates, repair citations, delete the
version-history blocks, normalize glyphs.

- **Pros:** smallest change; no reader has to relearn anything; can be done in one sitting.
- **Cons:** does not touch any root cause. The checklist still restates backlog scope, so
  F1 recurs at the next close-out. Leaves ~400 lines of history to re-delete later.
- **Verdict:** necessary but not sufficient. This is the content of Gate 2 below, not a
  strategy on its own.

### Option B — Separate the record from the plan, and give each fact one owner

Keep both documents, and make the split between them structural rather than
conventional:

- **`FEATURE_BACKLOG.md` is the sole owner of item state.** Status, ACs, effort, priority,
  disposition, and close-out narrative live here and only here. It stays long; that is
  appropriate for a register.
- **`implementation-checklist.md` becomes a forward-looking plan only.** It owns sequence
  and gate structure — what comes next, in what order, gated how. It references items by
  number and title, and states no item's status, scope, or ACs. Completed phases collapse
  to one line each in the timeline table.
- **Version-history blocks deleted from both** (F8), with the eight version-pinned
  citations (F9) rewritten to cite items, not versions: "Item 66" rather than
  "FEATURE_BACKLOG.md v5.42, Item 66."
- **Status vocabulary fixed and enforced**, with `DEVELOPMENT_STANDARDS.md` §1.3 widened to
  the set actually needed (F12, and see Q1).

- **Pros:** kills the duplication that causes F1/F2/F3; the checklist becomes short enough
  to reconcile at every close-out; each document does one job. Preserves the genuinely good
  work in §3.1 untouched — the register, the statistics, the effort reconciliation, the AC
  dispositions all stay exactly where they are.
- **Cons:** the checklist loses its self-contained narrative; a reader wanting full context
  on a gate must follow the item reference. Roughly 900 lines of checklist body get
  rewritten, which is real work and carries its own transcription risk.

### Option C — Merge into a single planning document

Fold the checklist into the backlog as a "Sequence" section.

- **Pros:** duplication becomes structurally impossible.
- **Cons:** produces one ~3,500-line document serving two different reading modes — "what
  do I build next" and "what is the state of item N". The checklist is read at sprint start
  by Role 3; the backlog is read during planning by Role 1. Merging them optimizes for
  neither, and the phase/gate narrative genuinely does not belong in a per-item register.
- **Verdict:** rejected. The two documents exist for good reason; the boundary between them
  is what is wrong, not their separateness.

**Recommendation: Option B**, with Option A's repairs executed inside it as one gate.

The rationale is the project's own architectural principle. CLAUDE.md's Role 1 rule says
the easiest path is not automatically the correct one, and the documentation single-owner
rule already governs standards documents — one document owns each rule, nothing is
duplicated. Option B is that same rule applied to planning documents, which are currently
the one place it is not enforced. Option A is the easier path and leaves the defect
generator running.

The cost is a ~900-line rewrite of the checklist body. That is the correct cost to pay
once, rather than re-reconciling two divergent scope statements at every sprint close-out
indefinitely.

## 5. Open questions

Annotated for Ray's review rather than raised mid-work, per the review request. Each
changes the resulting work.

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | **Status vocabulary — widen the standard, or narrow the practice?** `DEVELOPMENT_STANDARDS.md` §1.3 sanctions three values; the backlog needs at least seven (`Open`, `Complete`, `Partial`, `Closed — Stale`, `Closed — Won't Implement`, `Closed — Superseded by Item N`, `Redirect → Item N`, plus `Conditional`/`Deferred Indefinitely`). My reading is the standard is too narrow for real project state and should be widened to a fixed enumeration, not that the backlog should discard information. Confirm the enumeration. | |
| Q2 | **F4 — what should an item with carried ACs be called?** Item 66 shipped 2 of 4 ACs and is marked `✓ Complete` "per Item 62 precedent." The disposition is honest and traceable; only the *label* is wrong, and the label is what the register, the statistics, and the Complete count all read. Recommend: such items take `Partial` (as Item 48 already correctly does), and `Complete` becomes reserved for all-ACs-met. This reclassifies Items 62 and 66 and moves Complete 35 → 33, Partial 1 → 3. Confirm before I touch the counts. | |
| Q3 | **F5 — do the two never-tracked handoff documents exist outside the repo?** Decision TM6 reordered the entire sprint chain and cites a document git has never seen. If the content exists elsewhere, it should be committed to `docs/dev/results/`. If it does not, TM6 and WPC3–WPC6 need their rationale restated inline in the backlog, or they are decisions of record with no retrievable basis. I cannot determine this from the repository. | |
| Q4 | **F1/F2 — what is the actual remaining scope of `SLACK_LLM_COMPLETION_SPRINT`?** With #23, #31, #43, #46 closed, what survives is: Gate 1 (#42, #44) intact; one regression test pinning `include_meetings == False` (per Item 23's own closure note at `FEATURE_BACKLOG.md:989–993`); Item #63 as the replacement for #43; and Gates 3–4 otherwise empty. That is close to a one-gate sprint. Should it be rescoped around #63, merged into another sprint, or re-specced from scratch? This is the decision the whole remediation is in service of. | |
| Q5 | **F11 — where does Item #48's carried scope land?** High priority, Partial since 20260708, target "Phase 14", scheduled nowhere. Own hotfix, folded into the rescoped Slack sprint, or explicitly deferred with the target corrected? | |
| Q6 | **Should the completed phases (1–13) collapse to timeline rows?** Option B implies it. Phases 1–13 occupy ~420 checklist lines describing shipped work already recorded in `CHANGELOG.md`, git tags, and the backlog. Collapsing them is the largest single reduction available; keeping them is defensible if they are read as an architecture orientation for new sessions. I lean toward collapsing, but this is a judgment about how *you* use the document. | |
| Q7 | **F18 — rename `implementation-checklist.md` now?** Already deferred once, to ride with this work. `IMPLEMENTATION_CHECKLIST.md` matches every other document in `docs/`. Doing it in this pass costs one `git mv` plus ~6 reference updates; the spec-filename version suffixes (also deferred, ~25 citations) are a separate question I have not scoped here. | |

## 6. Plan of action

Sequenced as gates, per project convention. Each is a hard stop: I report and wait.

**Branch:** `chore/planning-docs-reconciliation`, from `main`, merging to `main` **and**
`dev`. Documentation-only, so no version bump, no `CHANGELOG.md` entry, no tag, no Release
— per `DEVELOPMENT_STANDARDS.md` §2.2. This is standalone doc remediation, not a branch
documenting its own shipped work, so `chore/*` is correct here and the exception at §2.2's
last bullet does not apply.

**Gate 0 — Decisions.** Ray answers Q1–Q7. Nothing is edited before this. Q1, Q2 and Q4
each change what the later gates produce, and Q4 in particular determines whether Gate 3
is a rescope or a rewrite.

**Gate 1 — Truth repair, backlog.** No structural change; corrections only.

- Reclassify per Q2; update register, Summary Statistics, and counts to match (F4, F13).
- Filter the Target Phase and Priority tables to open items only (F14).
- Repair or remove the 6 dead standards citations (F7) and the deleted-artifact citations
  (F6) — repointing live ones to `DEVELOPMENT_STANDARDS.md` sections, and marking
  historical ones as git-history references rather than live pointers.
- Apply Q3's outcome to the phantom citations (F5).
- Verify: every `✓` in the register agrees with its item's `Status:` field; the four
  statistics tables still reconcile to the item total.

**Gate 2 — Truth repair, checklist.** Same treatment, no restructure yet.

- Resolve the #58 three-way contradiction (F10).
- Correct the headline project state to v1.29.0 (F15).
- Repair the 6 dead standards citations and the 8 version-pinned backlog citations (F7, F9).
- Normalize the seven status conventions to `- [x]` / `- [ ]` / `- [~]` (F17).

**Gate 3 — Scope reconciliation.** The gate that fixes the Critical findings.

- Rewrite `SLACK_LLM_COMPLETION_SPRINT` to Q4's answer: remove closed-item scope (F1),
  remove the rejected design from Gate 2 (F2), place Item #63 (F3).
- Place Item #48's carried scope per Q5 (F11).
- Cross-check **every** remaining unchecked checklist box against its backlog item's live
  Status. This is the reconciliation that was skipped on 20260725 and is the substance of
  the gate — the four known-stale items are what a targeted read found, not a guarantee
  that no fifth exists.

**Gate 4 — Structural separation.** Option B proper.

- Strip both version-history blocks (F8).
- Move all item state out of the checklist; it references items, never restates them.
- Collapse Phases 1–13 per Q6.
- Rename per Q7 if approved (F18).

**Gate 5 — Standards correction.** Closes the loop on §3.3, and must come last so it
codifies what the earlier gates actually did.

- `DEVELOPMENT_STANDARDS.md` §1.3: widen the status enumeration per Q1; add the rule from
  Q2 that `Complete` requires all ACs met and carried ACs mean `Partial`.
- Add a standing rule that the checklist may not restate item state — the durable form of
  the single-owner fix, without which Gate 4 decays.
- Correct C1 in **both** `DEVELOPMENT_STANDARDS.md` §1.3 and `CLAUDE.md` § Common Pitfalls:
  keep the Item 32 lesson, replace the falsified `set_forwarding()` evidence.
- Correct C2 — restate OQ4 as a shipped decision rather than pending direction.

**Not in scope.** The spec-filename version suffixes under `docs/dev/specs/` (~25
citations) are a known deferred item and a separate branch; folding them in here would
bundle two unrelated concerns, which §2.2 prohibits by the same reasoning it applies to
hotfixes. Flagging so it is not lost, not proposing it.

## 7. Disposition

**Superseded 20260810.** Ray rejected the premise of §6 — a six-gate remediation to fix a
problem caused by long documents and too many gates was the disease, not the cure. The
review's diagnosis stood; its plan did not. Item state moved to **GitHub Issues** instead,
planned in `GITHUB_ISSUES_MIGRATION_MANIFEST.md`. §4 Option B survives only in the sense
that record and plan are now separated — by tooling, not by rewriting two documents.

Recorded here because this artifact is archived and must not strand live work.

**Retracted.** F6 was wrong: citing material that git can retrieve is not a broken
citation, and the archive has since been restored to `docs/archive/`, so those artifacts
are present again. Most of F7 goes with it — a line recording what a decision was resolved
against in 20260629 is history, not a dangling pointer.

**Resolved by the migration, structurally rather than by editing prose** — F1, F2, F3
(closed items simply do not migrate), F11 (Item 48 becomes an explicit issue), F12, F13,
F14, F17 (the register, the four statistics tables and the seven glyph conventions cease
to exist rather than being corrected), F16 (milestone exit conditions replace transcribed
counts).

**Resolved separately during the same work** — the v1.28.0 CHANGELOG section, found to
have been deleted by commit `974f1d5` rather than never written, restored and now guarded
by `scripts/check_release_integrity.py` and `.githooks/pre-push`. The `CLAUDE.md`
archive-rule contradiction, corrected when `docs/archive/` was restored.

**Still open — these have no home yet and are the reason this section exists:**

| # | Thread | Needs |
| --- | --- | --- |
| F5 | `SESSION_HANDOFF_TASK_MATCH_PLANNING_20260725.md` and `SESSION_HANDOFF_ITEM69_SCOPE_LOCK_20260727.md` were never tracked in git, in any ref. Decision TM6 (which reordered the whole sprint chain) and WPC3–WPC6 cite them. | Q3 was never answered. Either commit the content if it exists outside the repo, or restate the rationale inline in the issues that inherit it. |
| F4 | Items closed `✓ Complete` with unmet ACs, cited as precedent. `DEVELOPMENT_STANDARDS.md` §1.3 forbids exactly this. | The carried ACs are tracked (Item 66's → Item 72). The standards-versus-practice conflict is not resolved. |
| F8, F9 | 141 + 259 lines of version history in the two planning documents, and eight citations addressing the backlog by version number. | The backlog banner and checklist trim, still not done. |
| F10 | The checklist contradicts itself three ways on Item #58. | Dies with the checklist trim, or needs fixing if the checklist survives. |
| F15 | Checklist headline still reads "v1.23.0 delivered" at v1.29.0. | Same. |
| F18 | `implementation-checklist.md` is the only lowercase filename in `docs/`. | Deferred twice now. |
| C1 | `DEVELOPMENT_STANDARDS.md` §1.3 and `CLAUDE.md` § Common Pitfalls both assert, present tense, that `set_forwarding()` has zero callers. No such method exists; `set_forwarding_note()` has three callers and Item 32 is delivered. It is the sole worked example behind the project's most important backlog rule. | Not corrected. |
| C2 | `CLAUDE.md` Locked Decision OQ4 reads as forward direction for work shipped in v1.24.0. | Not corrected. |

**Not superseded:** §3.4's root cause — two documents owning the same fact, the record
growing inside the plan, and reconciliation being manual and unaided. That diagnosis is
what the migration acts on, and it is the part worth re-reading if this is ever revisited.
