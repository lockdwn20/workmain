# Tracking Semantics Consolidation — Spec

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20260814
**Branch:** `chore/issue-81-tracking-semantics` (from `main`, merges to `main` and `dev`)
**Target release:** none — `chore/*` carries no version bump, no `CHANGELOG.md` entry, no tag, no Release
**Originating item:** Issue #81, child of #80
**Design study:** `docs/dev/design/RECON_CYCLE_MECHANICS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260814 | Ray | `documentation` (GitHub system label) is canonical; the custom `docs` label is removed in favour of it. Recon Q6 | Accepted. Ray offered "within #81 or as a sub-issue to #81"; taken **within #81** as Step 4, since it is one label operation and splitting it would cost a second branch and spec for a change smaller than its own overhead |
| 20260814 | Ray | Recon Q4 — whether `.claude/skills/` is chore-eligible — closed as a non-issue | Branch type follows §2.2 without further distinction. `chore/*` |
| 20260814 | Spanner | §1.3 and CLAUDE.md Project Status are the only two carriers of tracking semantics — no third copy exists | Verified, see §2 C5. Consolidation is a two-file change |
| 20260814 | Ray | The gate table in this spec's first draft was a task list with approval ceremony attached. Gates compensated for oversized scope in the archive specs; once one issue is one independently verifiable outcome, per-step approval buys nothing | Accepted. §4 is **Steps**, not gates. Approval attaches to *irreversible actions* — here, one: deleting the `docs` label. Reversible text edits on a branch carry no stop |
| 20260814 | Ray | Revising gate discipline itself in `CLAUDE.md` and `DEVELOPMENT_STANDARDS.md`, and reviewing the two for conflicts, is **not** in this spec | Filed as its own child of #80. Folding a standards revision into a documentation-consolidation issue is how the archive specs grew. This spec adopts the steps/authorization shape ahead of that issue and does not codify it |
| 20260814 | Caliper | F3, F5 — AC1.1 greps the whole file while claiming a range; AC1.3 alternation passes on a partial result | Accepted. AC1.1 uses the `sed` range form; AC1.3 split into AC1.3a and AC1.3b, each a single assertion |
| 20260814 | Caliper | F6 — `gh issue list --label <nonexistent>` returns `[]` with exit 0, so AC2.1's post-deletion check is vacuous | Accepted, and independently reproduced. AC2.1 now verifies the additive half **before** the authorization point, against list `L` captured at Step 4 start, and is the evidence Ray approves against |
| 20260814 | Caliper | F7 — AC4.1 let the implementer choose the phrase, so its strictness was theirs | Accepted. The phrase list is fixed in the AC |
| 20260814 | Caliper | F8, F9 — C4 cited `CLAUDE.md:76-77` for a rule at 77-78; C2's range overran into out-of-scope content | Accepted, both re-verified against source. C4 → 77-78, C2 → 61-82 with the exclusion stated |
| 20260814 | Caliper | F10 — AC2.1 hardcoded the issue list while C7 says to re-derive | Accepted. The list is derived at Step 4 start and recorded in the commit message. C7 keeps its numbers: it is a dated observation carrying its evidence, not a claim about live state |
| 20260814 | Caliper | F1 — the CLAUDE.md step's "every rule removed" contradicted §1's out-of-scope list, and the retained `gh` ≥ 2.6x sentence was welded to a deleted one | Accepted, **closed by Ray 20260814**. That step is now a three-bullet deletion with verbatim replacement text, so there is no exhaustive "what survives" list to contradict. The rescued sentence sits beneath the `gh` code block as an environment constraint. AC3.5 enforces a single diff hunk, so straying outside the region fails mechanically rather than being caught in review |
| 20260814 | Caliper | G2 — AC4.1's `independently verifiable` phrase returns zero hits before any edit, because CLAUDE.md wraps it across lines; the assertion could not fail | Accepted, reproduced. Replaced with `each child is independently`. Every phrase in the list was then confirmed to return exactly `1` pre-edit, so none is dead |
| 20260814 | Caliper | G3 — Step 2's ordering rationale still argued from the deleted DR5 | Accepted. Spanner's call: the migration moves **last**. There is no dependency either way, so it is ordered on the property that matters — all reversible work and its verification completes before the one irreversible action |
| 20260814 | Caliper | G4 — C1 and C8 supported the deleted DR5 and now prove the opposite | Accepted. C1's third clause reframed as correct behaviour; C8 repurposed onto label descriptions as the live source |
| 20260814 | Caliper | G5 — AC1.2 was itself a four-name register, and passed on an untouched file | Accepted, and it was the same defect as F2 one level down. Replaced with Caliper's derived form, which excludes only the type discriminator — a rule, not a list — and additionally catches `documentation` leaking into §1.3 |
| 20260814 | Caliper | G6 — a risk row asserted an AC-checked control with no AC behind it | Accepted. AC1.4 added |
| 20260814 | Caliper | G7, G8 — "four issues" residue in rollback; AC3.5 not runnable after commit | Accepted. Rollback references list `L`; AC3.5 carries both pre- and post-commit forms |
| 20260814 | Caliper | G1 — DR4 put the sequencing rule in §1.3 while `CLAUDE.md:64` already states it, recreating the duplication #81 exists to remove | Accepted, **closed 20260814**. §1.3 says nothing about sequencing; `CLAUDE.md:64` stays sole owner. Ray: *"By our rules it should be option 2, I don't know why we are discussing it"* — DR1 plus DR2's existing precedent already decided this, and presenting it as a three-way choice was a wasted turn |
| 20260814 | Caliper | H1 — DR4 says §1.3 says nothing about sequencing, but no AC caught the bare word, and §1.3's current text carries *"milestone for sequencing"* | Accepted, reproduced: the phrase is live today and would have passed every AC. Folded into AC1.5 |
| 20260814 | Caliper | H2 — AC1.2 grepped bare label names, and `process`, `tests`, `reports`, `templates`, `daemon`, `documentation` are ordinary words a section about process may use | Accepted. Matches the backticked form instead, which is the artifact DR5 actually forbids |
| 20260814 | Caliper | H3 — the risk table still cited pre-renumbering step numbers | Accepted. The G3 Decision Log row keeps its original numbering as historical record; only live guidance was corrected |
| 20260814 | Caliper | Third pass: all G- and H-findings verified closed against live source. Verdict — approve | Recorded |
| 20260814 | Ray | **Spec approved for implementation** | Status → Approved. Anvil works from this document only |
| 20260814 | Ray | **F2 dissolved by deleting DR5.** DR5 was Spanner's invention, not a Ray decision, and it proposed a maintained label register inside the section that forbids registers. Labels carry descriptions on GitHub; that is the source of truth | Accepted. §1.3 states label *rules* only. Root cause: reaching for a static list because a static list is the cheapest thing to write a `grep` against — a copy is always a maintained artifact. Do not trade a maintenance burden for AC convenience |

---

## 1. Scope

**In scope:**

- `docs/DEVELOPMENT_STANDARDS.md` §1.3 — becomes the single owner of issue tracking
  semantics: label meaning including the type discriminator, milestone meaning, and
  parent/child meaning.
- `CLAUDE.md` Project Status — the Milestones, Labels and Parent-issues bullets deleted,
  replaced by the surviving `gh` version constraint and a pointer to §1.3. See §4 for the
  verbatim replacement text.
- The `docs` → `documentation` label migration on GitHub — deleting one duplicate label.

**Out of scope:**

- The `gh` version floor sentence, the Operating context block, and the Document table in
  CLAUDE.md. None is tracking semantics — the first is an environment constraint, the second
  role context, the third navigation — and CLAUDE.md legitimately owns all three. The
  Document table's GitHub Issues row stays as written (Ray, 20260814).
- Any change to §1.1, §1.2, or §2.2. #81 is a duplication defect, not a workflow revision.
- The ranked queue and Project #3. That is #84, and §1.3 must not acquire sequencing
  mechanics ahead of it — see DR4.
- Issue *creation* structure (templates, JSON validator). That is #82.
- `docs/archive/**`. Archived documents are never updated, per CLAUDE.md.

## 2. Verified current state

| # | Claim | Evidence |
| --- | --- | --- |
| C1 | §1.3 is four bullets and states *"a milestone for sequencing and labels for area"*. It does not mention the `bug`/`enhancement` type discriminator, and does not define parent/child beyond "a parent issue with children". It names no area label — under DR5 that is correct behaviour, not part of the defect | `docs/DEVELOPMENT_STANDARDS.md:40-53` |
| C2 | CLAUDE.md Project Status carries the full semantics — the `gh --json` command, the milestone exit-condition rule with the `gh` ≥ 2.6x floor, the area-label list with the type-discriminator rule, and the parent-issue rule | `CLAUDE.md:61-82`. The range stops at 82 deliberately: 84-88 is the Operating context block and 90-94 the Document table, both out of scope per §1 |
| C3 | The milestone exit-condition rule is stated in **both** documents — `DEVELOPMENT_STANDARDS.md:47-48` and `CLAUDE.md:72-73`. This is a live duplication, not merely an omission | Both cited lines |
| C4 | The parent/child rule is stated in **both** — *"An issue must be independently verifiable on its own"* (`DEVELOPMENT_STANDARDS.md:45-46`) and *"each child is independently verifiable on its own"* (`CLAUDE.md:77-78`) | Both cited lines |
| C5 | No third document carries these rules. A grep for the discriminator, `milestone for sequencing`, `labels for area`, and `subIssuesSummary` across all tracked `.md` outside `docs/archive/` returns hits in exactly these two files | `grep -rn --include=*.md`, repo root |
| C6 | Both documents open by declaring the boundary: CLAUDE.md — *"`docs/DEVELOPMENT_STANDARDS.md` owns how we build … Nothing is duplicated between them"*; DEVELOPMENT_STANDARDS.md — *"`CLAUDE.md` owns who does what … Nothing here is duplicated in `CLAUDE.md`"*. Both statements are currently false | `CLAUDE.md:5-9`; `docs/DEVELOPMENT_STANDARDS.md:3-7` |
| C7 | The `documentation` label exists and carries no issues in any state; the custom `docs` label carries four — #47, #48, #53, #59 | Recon F27; re-derive at execution with `gh issue list --state all --label` |
| C8 | Every label carries a description on GitHub, returned by `gh label list --json name,description`. That is the live source of what a label means, and is why DR5 needs no list in prose | `gh label list --json name,description` |

## 3. Design rules

- **DR1 — One owner, others link.** After this spec, every tracking-semantics rule is
  stated in §1.3 exactly once. CLAUDE.md points to §1.3 and restates nothing. A rule
  appearing in both files is a defect regardless of how the wording differs.
- **DR2 — CLAUDE.md keeps the operational command.** The `gh issue list --json` invocation
  stays in CLAUDE.md, because it is what a session actually runs, not a rule about how work
  is tracked. It is the one intentional exception to DR1 and is not duplicated into §1.3.
- **DR3 — The archive warning stays in CLAUDE.md.** It governs what may be cited as the
  basis for a decision, which is orientation, not build process.
- **DR4 — §1.3 says nothing about sequencing at all.** `CLAUDE.md:64` already states that
  state, priority and sequencing live in GitHub Issues, and it remains the sole owner of that
  sentence — the same orient-versus-govern split that keeps the `gh` command in CLAUDE.md
  under DR2. §1.3 restating it would breach DR1. §1.3 also names no sequencing *mechanism*:
  #84 has not shipped, and naming Project #3 would put a mechanism in the standards ahead of
  the spec that establishes it.
- **DR5 — §1.3 states label rules, never a label list.** What a label means is its
  description on GitHub, readable with `gh label list`. Enumerating labels in prose would
  create exactly the register §1.3 forbids, and it would go stale the first time a label is
  added. The rule is stated; the membership is derived.
- **DR6 — The label migration is additive-then-subtractive.** Every issue carrying `docs`
  gains `documentation` before the `docs` label is deleted. Deleting a label removes it from
  every issue that carries it, and that is not recoverable from the API.
- **Anything not covered here: STOP and surface to Ray.** No self-resolution, no scope
  adjustment, no in-flow wording calls on documents Ray owns. This is unconditional and does
  not wait for a step boundary.

## 4. Steps

Ordered, each committed on completion. **No step is an approval stop.** Every step below
except one is a text edit on a branch, undone by `git revert`; stopping to ask permission
before continuing would buy nothing and cost a round-trip each.

AC identifiers are keyed to **subject**, not to step order, so they stay stable if steps are
resequenced. The mapping is in the table.

| Step | Deliverable | Files | Verification |
| --- | --- | --- | --- |
| 1 | §1.3 rewritten as the single owner — label semantics incl. the type discriminator (DR5), milestone semantics incl. the exit condition, and parent/child semantics. Says nothing about sequencing (DR4) | `docs/DEVELOPMENT_STANDARDS.md` | AC1.1, AC1.2, AC1.3a, AC1.3b, AC1.4, AC1.5 |
| 2 | **Delete exactly three bullets** from CLAUDE.md Project Status — Milestones, Labels, Parent issues (`CLAUDE.md:72-78` at authoring time; anchor on the bullet text, not the numbers). **Insert in their place** the two lines given below. Nothing else in the section is touched | `CLAUDE.md` | AC3.1 – AC3.5 |
| 3 | Cross-document verification — no rule stated twice; both files' opening boundary claims (C6) are now true | both | AC4.1, AC4.2 |
| 4 | Label migration — `documentation` applied to every issue carrying `docs`, then `docs` deleted. **Contains the authorization point below** | GitHub only, no files | AC2.1, AC2.2 |

**Why the label migration runs last.** Its original position was justified by the deleted
DR5 — §1.3 had to enumerate the label set before the duplicate could go — and that reason
died with the enumeration. There is no dependency between the migration and either document
edit, so rather than leave the order arbitrary it is ordered on the property that does
matter: every reversible action and its verification completes first, and the single
irreversible action runs last, with nothing pending behind it. If Ray declines the
authorization, Steps 1–3 still stand on their own and #81's three ACs are all met — the
migration is Ray's Q6 addition, not part of the originating issue.

### Step 2 replacement text — verbatim

The three deleted bullets are replaced by exactly this, and by nothing else:

```markdown
Requires `gh` ≥ 2.6x for `parent` / `subIssues` / `subIssuesSummary` (Issues 2.0 support).

What milestones, labels, and parent/child structure mean: `docs/DEVELOPMENT_STANDARDS.md` §1.3.
```

The first line is the surviving half of the Milestones bullet — an environment constraint on
the `gh` command above it, not a rule about milestones — and it sits directly beneath the
code block for that reason. Approved by Ray 20260814, so it is not an in-flow wording call
and does not trigger §3's stop.

Everything else in Project Status is untouched: the Version and Test-suite bullets, the
"Item state, priority, and sequencing live in GitHub Issues" sentence, the `gh` code block,
the archive warning, the Operating context block, and the Document table. AC3.5 enforces
this mechanically rather than trusting the instruction.

### Authorization point

**`gh label delete docs` — stop and wait for Ray's explicit approval before running it.**

Deleting a label strips it from every issue carrying it, and the API will not return the
association. This is the only action in this spec that a revert cannot undo, and the stop
attaches to *that property*, not to its position in the sequence. Applying `documentation`
(the additive half of Step 4, per DR6) needs no approval and runs without stopping.

No DB migration appears in this spec.

**Anything the spec does not cover: STOP and surface to Ray** — that rule is unchanged and
is independent of step boundaries.

## 5. Acceptance criteria

Mapped to #81's three ACs: AC1.x and AC4.x carry #81's first, AC3.x its second, AC4.1 its
third. AC2.x carries Ray's Q6 decision. Each row is a single assertion — no row passes on a
partial result via an alternation.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | §1.3 states the type-label discriminator | `sed -n '/### 1.3/,/^---/p' docs/DEVELOPMENT_STANDARDS.md \| grep -c 'enhancement'` returns non-zero |
| AC1.2 | §1.3 names no label except the two type labels | Derived, not listed — see the command below the table |
| AC1.3a | §1.3 states the milestone exit-condition rule | `sed -n '/### 1.3/,/^---/p' docs/DEVELOPMENT_STANDARDS.md \| grep -c 'exit condition'` returns non-zero |
| AC1.3b | §1.3 states parent/child semantics | `sed -n '/### 1.3/,/^---/p' docs/DEVELOPMENT_STANDARDS.md \| grep -c 'parent'` returns non-zero |
| AC1.4 | §1.3 names no sequencing mechanism, per DR4 | `sed -n '/### 1.3/,/^---/p' docs/DEVELOPMENT_STANDARDS.md \| grep -cE 'Project #3\|WorkmAIn Queue\|item-list'` returns `0` |
| AC1.5 | §1.3 says nothing about sequencing at all — not the location sentence, and not the word. `CLAUDE.md:64` stays sole owner, per DR4 | `sed -n '/### 1.3/,/^---/p' docs/DEVELOPMENT_STANDARDS.md \| grep -ciE 'sequenc\|lives? in GitHub\|never in a document'` returns `0`. Note the current §1.3 contains *"milestone for sequencing"*, so this fails until Step 1 removes it — it is a real check, not a formality |
| AC2.1 | Every issue that carried `docs` also carries `documentation`, checked **before** the label is deleted | Capture `gh issue list --state all --limit 300 --label docs --json number` at Step 4 start as list `L`, recorded in the Step 4 commit message. After the additive half, `gh issue list --state all --limit 300 --label documentation --json number` contains every element of `L`. This check is the evidence presented at the authorization point — a post-deletion `--label docs` query returns `[]` with exit 0 even when the label never existed, so it proves nothing and is not used |
| AC2.2 | The `docs` label no longer exists | `gh label list --limit 100 \| grep -w docs` returns nothing |
| AC3.1 | The three bullets are gone | `sed -n '/^## Project Status/,/^## Tech Stack/p' CLAUDE.md \| grep -cE '\*\*Milestones\*\*\|\*\*Labels\*\*\|\*\*Parent issues\*\*'` returns `0` |
| AC3.2 | The `gh issue list --json` command survives verbatim | `grep -c 'subIssuesSummary' CLAUDE.md` returns non-zero |
| AC3.3 | Project Status points to §1.3 by name | `sed -n '/^## Project Status/,/^## Tech Stack/p' CLAUDE.md \| grep -c '§1.3'` returns non-zero |
| AC3.4 | The `gh` ≥ 2.6x constraint survives the deletion of the bullet it was welded to | `grep -c '≥ 2.6x' CLAUDE.md` returns non-zero |
| AC3.5 | Nothing outside the replaced region changed — Operating context, the Document table, the archive warning and the Version/Test-suite bullets are intact | Pre-commit: `git diff -U0 CLAUDE.md \| grep -c '^@@'` returns `1`. Post-commit, and at review time: `git show -U0 --format= <CLAUDE.md-step-sha> -- CLAUDE.md \| grep -c '^@@'` returns `1`. A single contiguous hunk — the three bullets are adjacent and the insertion lands in their place — so any second hunk means the edit strayed outside them |
| AC4.1 | No tracking-semantics rule appears in both documents | `grep -cF` each of these fixed phrases across `CLAUDE.md`, all returning `0`: `exit condition`, `each child is independently`, `applied *only*`, `carry area`, `group work that must ship together`. Each was confirmed to return exactly `1` **before** the edit, so none is an assertion that cannot fail — `independently verifiable` was dropped for that reason: CLAUDE.md wraps it across lines and `grep -F` never matched it. The list is fixed here rather than left to the implementer, so the AC's strictness is not theirs to choose |
| AC4.2 | The test suite is unaffected | `python -m pytest tests/` — same pass count as the baseline recorded at Step 1, zero failures |

**AC1.2 command.** Every live label other than the type discriminator must be absent from
§1.3 *as a code span* — a label enumeration would be written as code spans, which is the
artifact DR5 forbids. Matching the backticked form rather than the bare name keeps ordinary
prose from tripping it: `process`, `tests`, `reports`, `templates`, `daemon` and
`documentation` are all live label names *and* ordinary words that a section about process
may legitimately use.

```bash
gh label list --limit 100 --json name -q '.[].name' \
  | grep -vxE 'bug|enhancement' \
  | while read -r l; do
      sed -n '/### 1.3/,/^---/p' docs/DEVELOPMENT_STANDARDS.md | grep -qF "\`$l\`" && echo "$l"
    done   # must print nothing
```

The `bug|enhancement` exclusion is the rule AC1.1 requires, not a list of areas, so this
introduces no register. It also catches `documentation` leaking into §1.3. This is an absence
guard and passes on an untouched file by design — AC1.1, AC1.3a and AC1.3b are what prove
Step 1 happened.

## 6. Test plan

No code changes, so no new tests. `pytest` runs as a regression guard only.

- **Baseline:** derive at Step 1 with `python -m pytest tests/`; record the number in
  the Step 1 commit message, not in this spec.
- **Expected after:** identical, zero failures.
- No new test files. Verification is `grep`/`gh`-based per §5, which is what makes a
  documentation spec mechanically testable at all.

## 7. Risks and rollback

| Risk | Blast radius | Rollback |
| --- | --- | --- |
| Step 4 deletes `docs` before `documentation` is applied | Every issue carrying `docs` silently loses its area label; not recoverable from the API | DR6 orders it additive-first, and AC2.1 verifies the additive half **before** the authorization point rather than after deletion. Rollback is manual re-application from list `L`, which is why `L` is captured at Step 4 start and recorded in the commit message |
| §1.3 absorbs sequencing mechanics ahead of #84 | The standard names Project #3 before the spec establishing it is approved; needs re-editing when #84 lands | DR4 forbids it, and **AC1.4** checks it. Added because the earlier draft asserted this control in the risk table without any AC behind it |
| A rule is moved into §1.3 but not deleted from CLAUDE.md, leaving the duplication that #81 exists to remove | The defect survives its own fix | AC4.1 checks each moved sentence's phrase against CLAUDE.md rather than checking only that CLAUDE.md got shorter |
| Wording drift on documents Ray owns | Ray is final authority on all documentation | Steps 1 and 2 — the two document edits — are committed separately, so each diff is reviewable on its own and revertible on its own |

Rollback for the whole spec is `git revert` of the step commits plus re-creating the `docs`
label and re-applying it to the issues in list `L`. The branch is `chore/*`, so no tag, Release, or
version bump exists to unwind.
