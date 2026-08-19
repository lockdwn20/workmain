# Steps and Authorization Points — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20260818
**Branch:** `chore/issue-86-steps-authorization` (from `main`, merges to `main` and `dev`)
**Target release:** none — `chore/*` carries no version bump, no `CHANGELOG.md` entry, no tag, no Release
**Originating item:** Issue #86, child of #80
**Design study:** `docs/dev/design/RECON_STEPS_AUTHORIZATION_POINTS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260814 | Ray | Spec §4 is Steps, not gates; approval attaches to irreversible actions | Codified here. Precedents: `TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md:20`, `:108` |
| 20260818 | Ray | Ownership test agreed | DR1 |
| 20260818 | Ray | Q4 — fix the F26 restart collision | DR6. §2.6 and §2.8 unedited; editing them would weaken the rule added after Item #58 |
| 20260818 | Ray | Q3 — `_TEMPLATE_RESULTS.md` in scope, though no issue AC names it | Accepted as a declared scope extension. Step 7 |
| 20260818 | Ray | Q5 — the unmerged recon rides this branch | Step 8 |
| 20260818 | Ray | Q6 — the two stale `Status: Approved` values are advanced here, not left for #83 | Step 8 |
| 20260818 | Ray | §1.1 forbids dispositions in a recon, so recon findings had nowhere to carry their fixes | Decisions with no other home go in this log rather than being lost |
| 20260818 | Spanner | Recon's first pass missed `DEVELOPMENT_STANDARDS.md:185` (F35) | Every AC derives its own set from a command; none is checked against the recon's tables |
| 20260819 | Ray | Issue #86 updated with the `pytest` and test-location criteria | AC13–AC15, DR10, step 3. No longer a scope extension |
| 20260819 | Spanner | Issue wording *"approved locations (currently only `automation/`)"* would put a second location list in §6 | Not written in; §6 cites §6.3 as owner. Deviates from the issue's literal wording — AC15 guards it |
| 20260819 | Ray | `CLAUDE.md:3` is a style rule, so it never fires on duplication — each restatement is individually concise. Prompted by this spec's own Decision Log restating its design rules | Replaced with a single-home output rule covering all output, not just chat. Step 5b, AC16. Folded here rather than a separate branch because step 4 already edits `CLAUDE.md` |
| 20260819 | Spanner | The new line 3 is adjacent to DR1 — both are single-owner rules — and could read as an AC8 duplication | Not a duplicate. DR1 decides which *document* owns a rule; line 3 governs everything Claude emits, including chat and commit messages. Line 3 stays in `CLAUDE.md` as role behaviour. No design rule restates it here, which is the rule applied to itself |
| 20260819 | Caliper | Findings 1, 2, 3, 6, 7, 8, 9 — scope omissions (`_TEMPLATE_SPEC.md` §6, `_TEMPLATE_RESULTS.md` §4 mis-labelled §3, four unnamed `CLAUDE.md` sections), step 2 writing destinations before step 4 read the sources, DR10's §7 ownership claim, and three unmechanical or noisy ACs | **Accepted in full.** All seven verified against source before acceptance |
| 20260819 | Caliper | Finding 4 — DR6's rationale *"carried by the approval for the merge itself"* is false; §2.6's restart follows a merge to `dev`, which DR5 does not make an authorization point | **Accepted.** Rationale replaced: the restart is a documented obligation, not a discretionary state change, so it is a step. Conclusion unchanged |
| 20260819 | Ray | Applying DR1 mechanically would move "Spec before implementation" (F15) and "Integration over separation" (F19) out of § Critical Rules, leaving the most important rule in the project in a document a session may not have read — the failure the section exists to prevent | **DR1a.** § Critical Rules is exempt: it is the always-visible subset, restated by design |
| 20260819 | Ray | Issue AC7 amended to *"with the exception of any Critical Rule stated in the CLAUDE.md and approved by Ray"* | The exemption is now carried by the originating item, so it is no longer a spec deviation. The added *"approved by Ray"* clause makes **membership** of the section a decision, not a judgement call — folded into DR1a and checked by AC17 |
| 20260819 | Ray | A rule placed after the role definitions can be read as scoped to a role — which is how this spec came to propose moving stop-and-surface into Role 1 | **DR1b.** § Critical Rules becomes the first section of `CLAUDE.md`, ahead of the three-role model. Position is the structural guard, not another rule that can be misread |
| 20260819 | Caliper | Round 2, findings 1–6 — F20 at `CLAUDE.md:111` reached by no step; `DEVELOPMENT_STANDARDS.md:7` keeps the no-duplication claim DR1a falsifies; §1's scope list fell behind §4's steps again; § Common Pitfalls `:234` restates § Key Design Decisions inside the same file; step 6's DR8 citation; DR1b silent on placement against the `:1-7` preamble | **Accepted in full**, verified against source. `:234` is deleted rather than promoted — § Key Design Decisions owns it, and no DR1a carve-out covers an intra-file restatement. AC9 extended to catch that class |
| 20260819 | Caliper | Round 3, findings 1–2 — AC18's zero-hit sweep contradicts steps 1 and 5, which *reword* the no-duplication claims rather than removing the phrase; AC17's *"every entry cites a `DEVELOPMENT_STANDARDS.md` section"* is unsatisfiable for the stop-and-surface entry, whose full statement lives in § Critical Rules itself | **Accepted in full.** The replacement wording for both `:7` lines is now stated verbatim in §4 so the phrase disappears; AC17 reworded to DR1a's own *"names the section that owns its full statement"* |
| 20260819 | Caliper | Finding 5 — stop-and-surface stays duplicated inside `CLAUDE.md` at `:121` and `:50-55`, colliding with the new line 3 | **Not taken.** § Critical Rules carries no role qualifier — it applies to every session in any role, which is why the rule lives there. `:121` and Role 3's `:50-55` are a global obligation and its implementation-specific form, not two copies. Both stay unchanged. Corrected by Ray after an intermediate revision had wrongly moved `:121` into Role 1 |

---

## 1. Scope

**In scope** — four files:

- `CLAUDE.md` — line 3; line 7; the § THREE-ROLE MODEL marker at `:11`; Role 1 `:24-25`;
  Role 3 `:48`; § Tech Stack `:111`; § Critical Rules `:117`, `:118-120`, `:123`; § Project
  Status `:62`; § Locked Architecture Decisions OQ4 `:223`; § Common Pitfalls; § Documentation
  Standards; and the position of § Critical Rules itself, which becomes the first section.
  **`:121-122` is verified unchanged, not edited** — see DR8.
- `docs/DEVELOPMENT_STANDARDS.md` — preamble ownership sentence `:3-4` and the
  no-duplication claim at `:7`; §1.1 pipeline and bullets; §1.2; §1.3; §2.2; §2.4; §2.7;
  §3.6; §4.5; §6 preamble and command block; §6.3; §6.4; §7; plus a new §1.4 defining steps
  and authorization points and a new §1.5 receiving the documentation rules.
- `docs/dev/specs/_TEMPLATE_SPEC.md` — §3, §4, §6, §7.
- `docs/dev/results/_TEMPLATE_RESULTS.md` — §2, §4.

Plus two housekeeping actions carried by Decision Log Q5 and Q6: merging
`chore/cycle-mechanics-recon`, and advancing two `Status:` values.

**Out of scope:**

- **The four `Status: Shipped` specs and both session handoffs.** They are historical
  records of work performed under gate discipline. Rewriting them would falsify the record
  of how that work actually ran.
- **`workmain/**`, `tests/**`, `config/*`, `templates/*`.** No application behaviour
  changes. Recon F33 establishes that `.github/ISSUE_TEMPLATE/` and
  `automation/issue_validator.py` carry neither vocabulary, and F34 that `.claude/` does
  not exist.
- **The close-out mechanism.** #83's deliverable. §1.1's pipeline terminates at
  `IMPLEMENTATION` here and #83 extends it — this spec deliberately does not add a
  close-out stage it cannot define.
- **`CHANGELOG.md`.** Append-only historical record; recon N2 leaves it unread and nothing
  here depends on it.
- **Any change to §2.6 or §2.8.** See DR6.

## 2. Verified current state

All claims verified against source on 20260818 at recon time; findings cited as `Fn` are
from `docs/dev/design/RECON_STEPS_AUTHORIZATION_POINTS.md`.

| Claim | Evidence (file:line) | Recon |
| --- | --- | --- |
| Gate rule stated in CLAUDE.md § Critical Rules | `CLAUDE.md:118-120` | F1 |
| Role 3 says "Gate 1" at `:48` but "the current step" at `:52`; the `:52` edit was #82's, documented as covered by no AC | `CLAUDE.md:48`, `:52`; `ISSUE_CREATION_VALIDATION_SPEC.md:89` | F2, F3 |
| Preamble assigns gate discipline to CLAUDE.md | `docs/DEVELOPMENT_STANDARDS.md:3-4` | F4 |
| Pipeline reads `… → IMPLEMENTATION → GATE REVIEW → COMMIT` | `docs/DEVELOPMENT_STANDARDS.md:19` | F5 |
| §1.1 bullets: "gate by gate"; "human approval at every gate" | `docs/DEVELOPMENT_STANDARDS.md:27-28` | F6 |
| §1.3 split rule ends "never one issue spanning several gates"; the independent-verifiability sentence sits immediately above it | `docs/DEVELOPMENT_STANDARDS.md:52-53` | F7, F27 |
| §2.2 hotfix→feature exception says "at Gate 0" | `docs/DEVELOPMENT_STANDARDS.md:118` | F8 |
| §2.4 commit-subject rule worked in `Gate 3 of 7` terms | `docs/DEVELOPMENT_STANDARDS.md:139-140` | F9 |
| §2.7 routes branch type by "phase/multi-gate" | `docs/DEVELOPMENT_STANDARDS.md:185` | F35 |
| §4.5 states the migration rule with the same "the gate is the approval" clause as `CLAUDE.md:120` | `docs/DEVELOPMENT_STANDARDS.md:350-351` | F14 |
| §6.4 ends "does not stop a gate" | `docs/DEVELOPMENT_STANDARDS.md:598` | F10 |
| Spec template carries gate structure in §3 (`:65`), §4 (`:67-78`), §6 (`:99`), and §7 (`:103`) — §6 spans `:92-100` | `_TEMPLATE_SPEC.md:65`, `:67-78`, `:99`, `:103` | F11 |
| Results template §2 titled "What shipped, by gate" (`:27-29`); the second occurrence is in **§4 Deviations** (`:47-54`), not §3, which spans `:34-46` and contains no gate word | `_TEMPLATE_RESULTS.md:27-29`, `:50` | F12 |
| The F14–F25 duplicated rules sit in `CLAUDE.md` sections beyond § Common Pitfalls: Role 1 `:24-25` (F16, F17), § Critical Rules `:117` (F15) and `:123` (F19), § Documentation Standards `:243` (F21) | `CLAUDE.md:24-25`, `:117`, `:123`, `:243` | F15–F21 |
| Under DR1, most of § Documentation Standards — subject-based filenames, the `Status:` field, archive rules, the Decision Log requirement, no version headers — is "how work is built" | `CLAUDE.md:241-`; DR1 | new |
| Two historical gate citations exist that are facts, not process rules | `docs/DEVELOPMENT_STANDARDS.md:57`; `CLAUDE.md:223` | §3.1 census |
| Both documents assert "nothing is duplicated" and both are false | `CLAUDE.md:7`; `docs/DEVELOPMENT_STANDARDS.md:7` | §3.2 |
| A set of process rules is stated in both documents, enumerated at recon §3.2 | `docs/dev/design/RECON_STEPS_AUTHORIZATION_POINTS.md` §3.2 | F14–F25 |
| Stop-and-surface appears at `CLAUDE.md:121` (§ Critical Rules, which carries no role qualifier), `CLAUDE.md:50-55` (Role 3's escalation procedure), and `_TEMPLATE_SPEC.md:65`. Only the template form ties it to a boundary | `CLAUDE.md:121`, `:50-55`; `_TEMPLATE_SPEC.md:65` | F28 |
| `#81` and `#82` specs already use `## 4. Steps` | `TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md:108`; `ISSUE_CREATION_VALIDATION_SPEC.md:162` | F13 |
| Those two specs are `Status: Approved` despite having shipped and merged | `grep "^\*\*Status:\*\*" docs/dev/specs/*.md`; `git log origin/main..origin/dev` | F29, F30 |
| `RECON_CYCLE_MECHANICS.md` is on an unmerged local branch and cited by a merged spec | `git branch -a`; `ISSUE_CREATION_VALIDATION_SPEC.md:9` | F31 |
| `origin/main` and `origin/dev` are content-identical | `git diff origin/main origin/dev` empty | F32 |
| `pyproject.toml` contains `[tool.pytest.ini_options]` with `testpaths = ["tests"]`, and nothing else — a bare `pytest` resolves to the application suite | `pyproject.toml:1-2` | new |
| §6's command block still passes an explicit path in three invocations, and the baseline note passes a fourth | `docs/DEVELOPMENT_STANDARDS.md:523-525`, `:529` | new |
| §6's preamble asserts *"Everything lives in `tests/`"*, contradicted by §6.3's own `automation/` row twenty lines below it | `docs/DEVELOPMENT_STANDARDS.md:520` vs `:590` | new |
| §6.3's `tests/` row states pytest *"only discovers here"* — true of a bare `pytest` under `testpaths`, misleading as a statement about pytest | `docs/DEVELOPMENT_STANDARDS.md:586` | new |
| `CLAUDE.md` § Project Status gives the test suite as `python -m pytest tests/` | `CLAUDE.md:62` | new |
| Line 3 reads *"All responses should be direct, concise and plainly spoken"* — scoped to responses, and stating no rule against restating content elsewhere | `CLAUDE.md:3` | new |
| The templates' pytest references are single-test invocations, where an explicit path is still correct | `_TEMPLATE_SPEC.md:86`; `_TEMPLATE_RESULTS.md:42` | new |

## 3. Design rules

- **DR1 — Ownership test.** `docs/DEVELOPMENT_STANDARDS.md` owns any rule governing *how
  work is built* — process, git, code, database, CLI, testing, file placement. `CLAUDE.md`
  owns *who does what* (the three-role model), *what this project is* (stack,
  architecture), and *domain decisions* (tag system, time format, trigger terminology,
  write-path map). When a rule could plausibly sit in either, it is a "how work is built"
  rule and goes to `DEVELOPMENT_STANDARDS.md`.

- **DR1a — § Critical Rules is exempt from DR1, by design.** It is not a set of rules that
  happen to be duplicated; it is the always-visible subset, deliberately restated in full
  from `DEVELOPMENT_STANDARDS.md` because a session that has read nothing else must still
  have them. The exemption is stated in the section itself, so a future reader can tell it
  apart from the accidental drift DR1 exists to remove. Every entry must name the section
  that owns its full statement. **Membership is Ray-approved** — an entry is added,
  reworded, or removed only with his explicit approval, which is what bounds the exemption
  instead of making it a licence to restate anything. Approving a spec that names the
  entries is that approval; nothing is added to the section in flight.

- **DR1b — § Critical Rules is the first section of `CLAUDE.md`.** It sits ahead of the
  three-role model, because a rule placed after the roles can be read as scoped to a role —
  which is exactly how this spec came to propose relocating stop-and-surface into Role 1.
  Position is the guard against that recurring. "First section" means the first `##`
  heading: the H1, the line 3 output rule, and the ownership sentence at `:5-7` stay where
  they are, and § Critical Rules goes directly beneath them.

- **DR2 — A pointer is not a duplicate.** One document may name another's rule and cite the
  section, provided it states no part of the rule's content. `§4.6` already does this in
  the CLAUDE.md direction and is the precedent. A sentence that would still be actionable
  with the cited section deleted is a duplicate, not a pointer.

- **DR3 — Steps.** Ordered work inside a spec. Committed individually, reviewable and
  revertible individually. **No approval stop.** A step ends with a commit, not with a
  request to continue.

- **DR4 — Authorization points.** Attached to specific *actions* that are irreversible or
  reach outside the working tree. This is a property of the action, so it does not scale
  with scope: a one-step issue can contain one and a twenty-step issue can contain none. An
  authorization point is a hard stop — state what is about to happen, then wait for Ray's
  explicit approval.

- **DR5 — The authorization set.** Executing a DB migration; deleting a GitHub object
  (issue, label, milestone, branch, release); merging to `main`; force-pushing any branch;
  changing the run state of a live service beyond DR6's carve-out. Anything not on this
  list is a step.

- **DR6 — The post-merge restart is not an authorization point.** §2.6 requires restarting
  `workmain-notify.service` after a merge to `dev`, and §2.8 forbids reporting a merge as
  deployed without it. That restart is a documented obligation, not a discretionary state
  change, so it is a step. DR5 covers service state changes *other than* that restart.
  §2.6 and §2.8 are not edited by this spec.

- **DR7 — The split test.** Split into sub-issues only where each piece leaves the
  repository in a coherent state its own acceptance criteria can verify. Where steps are
  strictly sequential and individually meaningless, they stay inline as steps — an issue
  whose closure leaves the repository worse than before is already forbidden by §1.3.

- **DR8 — Stop and surface is unconditional, and § Critical Rules is its home.** That
  section carries no role qualifier: it applies to every Claude session whatever role it is
  operating in, which is why the rule sits there rather than under a role. It stays. Role
  3's four-step escalation procedure is the implementation-specific form of the same
  obligation — narrower trigger, added specifics — and is not a duplicate of it. Neither
  may be stated with reference to steps, gates, or any position in a sequence. Both are
  triggered by what is encountered.

- **DR9 — Historical citations are facts, not rules.** Where an existing document cites a
  gate as part of a historical record, the citation is reworded to name the release instead
  of the gate. No information is lost — the version is the durable identifier — and the
  acceptance criteria can then use an unqualified zero-hit sweep.

- **DR10 — Test invocation and test locations.** The application suite is run as a bare
  `pytest`; `testpaths` in `pyproject.toml` resolves it, and passing `tests/` explicitly is
  redundant. An explicit path stays correct for two cases only: targeting a single file,
  class, or test, and reaching a suite that sits outside `testpaths`. The standard states
  that non-application suites exist and are reached by explicit path — it does **not**
  enumerate them. **§6.3 is the single owner of test placement**, and §6's preamble cites
  §6.3. §7 is the application-layout table and its `automation/` row records dev tooling,
  not a test suite; pointing §6 there would leave the fact in one table and the citation
  in another.

When something is not covered here, **STOP and surface to Ray**. No self-resolution, no
scope adjustment, no in-flow architecture calls.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | New `§1.4 Steps and authorization points` carrying DR3–DR6, the authorization set, and the DR6 carve-out named in place. Preamble ownership sentence rewritten to DR1, and `:7`'s *"Nothing here is duplicated in `CLAUDE.md`"* **replaced** with the wording below — after DR1a it is the more wrong of the two paired claims, and qualifying it in place would leave AC18's sweep failing | `docs/DEVELOPMENT_STANDARDS.md` |
| 2 | §1.1 pipeline terminates at `IMPLEMENTATION`; §1.1 bullets reworded to steps with a §1.4 pointer; §1.3 split rule replaced by DR7; §2.2, §2.4, §2.7, §6.4 reworded to step vocabulary; §4.5 keeps the migration rule as a §1.4 pointer per DR2 | `docs/DEVELOPMENT_STANDARDS.md` |
| 3 | §6 preamble and command block reconciled with `testpaths` per DR10 — bare `pytest`, and the "everything lives in `tests/`" claim replaced by a statement that non-application suites are reached by explicit path, citing §6.3. §6.3's `tests/` row reworded off "only discovers here" | `docs/DEVELOPMENT_STANDARDS.md` |
| 4 | **Both sides of every duplication, in one commit.** Per DR1, every F14–F25 rule except the two DR1a exempts (F15, F19) lands in `docs/DEVELOPMENT_STANDARDS.md` and leaves `CLAUDE.md`; each pair is diffed before the `CLAUDE.md` copy is deleted, and any wording the surviving copy lacks is merged into it. Sources: Role 1 `:24-25`, § Tech Stack `:111` (the `scripts-deprecated/` clause only — the §7 pointer beside it is a clean DR2 pointer and stays), § Common Pitfalls, § Documentation Standards. § Common Pitfalls `:234` is deleted rather than moved: it restates § Key Design Decisions → Report Correction Fields (`:179-185`) inside the same file, and no DR1a carve-out covers it. § Critical Rules `:117` and `:123` stay put under DR1a and are instead given owning-section citations in step 5. Destinations: §1.2, §1.3, §3.6, §6.3, §7, and a §1.5 for the documentation rules arriving from § Documentation Standards | `CLAUDE.md`, `docs/DEVELOPMENT_STANDARDS.md` |
| 5 | § Critical Rules moved to become the first section, ahead of the three-role model, per DR1b; the DR1a exemption stated in the section itself and each entry given the `DEVELOPMENT_STANDARDS.md` section that owns its full statement; the role model's "READ THIS FIRST" marker reworded, since it is no longer first; line 7's "Nothing is duplicated between them" **replaced** with the wording below; line 3 replaced with the output rule below; the gate bullet replaced by an authorization-point entry that states the rule and cites §1.4 as its owner — a bare pointer would contradict DR1a, since this is precisely a rule a session must have without reading further; `:121` and `:122` retained unchanged per DR8; Role 3 `:48` reworded and `:50-55` retained; § Project Status test command becomes `pytest`; OQ4 citation reworded per DR9 | `CLAUDE.md` |
| 6 | §3 stop-and-surface restated as a pointer to `CLAUDE.md` Role 3 — the implementer-facing form, which is what a spec template is read for; DR8 makes § Critical Rules the home of the global rule and Role 3 the derived form, and this cites the derived one deliberately; §4 retitled **Steps** with a `Step / Deliverable / Files` table and an **Authorization points** subsection; §6 and §7 reworded to steps. The `:86` single-test invocation is left as-is per DR10 | `docs/dev/specs/_TEMPLATE_SPEC.md` |
| 7 | §2 retitled "What shipped, by step" with a `Step / Delivered / Files changed / Tests` table; §4's "surfaced at a gate" reworded. §3 needs no change | `docs/dev/results/_TEMPLATE_RESULTS.md` |
| 8 | `chore/cycle-mechanics-recon` merged into this branch, restoring `RECON_CYCLE_MECHANICS.md` and fixing #82's broken citation; `Status:` advanced to `Shipped` on `TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md` and `ISSUE_CREATION_VALIDATION_SPEC.md` | `docs/dev/design/RECON_CYCLE_MECHANICS.md`, two spec headers |
| 9 | Full acceptance sweep per §5, then merge | — |

### Step 5a — the § Critical Rules entry set

These four, and nothing else. Membership is Ray-approved per DR1a; an implementer who
believes a fifth belongs stops and surfaces rather than adding it.

| Entry | Owning section |
| --- | --- |
| Spec before implementation | `§1.1` |
| Authorization points — the action list, and that a migration's approval is at execution | `§1.4` |
| Stop and surface — unchanged at `:121-122` | This entry **is** the full statement of the global rule per DR8; `CLAUDE.md` Role 3 holds the implementation form |
| Integration over separation | `§3.6` |

### Steps 1 and 5 — the replacements for the paired no-duplication claims

Verbatim. Both drop the phrase rather than qualifying it, so AC18's sweep is satisfiable.

`docs/DEVELOPMENT_STANDARDS.md:7`:

> Read the relevant section before writing code. Everything here has exactly one home; the
> only text restated elsewhere is the `CLAUDE.md` § Critical Rules subset.

`CLAUDE.md:7`:

> Only the § Critical Rules entries are restated from it; everything else has exactly one
> home.

### Step 5b — the replacement for `CLAUDE.md:3`

Verbatim. This is the deliverable, not a description of it:

> All output — chat, specs, design docs, commit messages, code comments — is direct,
> concise, and plainly spoken. Every fact, decision, and rule has exactly one home. State
> it there; everywhere else cites it. Do not summarize back what the reader can already
> read: not the artifact in chat, not a section in another section, not a design rule in a
> decision log.

### Authorization points

This spec contains **one**, at step 9: the merge to `main`. It carries no DB migration, no
GitHub object deletion, no force push, and no service state change. Per DR3, steps 1–8
proceed without stopping.

Per §2.2 this is a `chore/*` branch — it merges to `main` and `dev` with no version bump,
no `CHANGELOG.md` entry, no tag, and no Release.

## 5. Acceptance criteria

Every criterion derives its own set from a command. None is checked against a list
transcribed from the recon.

| AC | Criterion | How it is checked | Issue AC |
| --- | --- | --- | --- |
| AC1 | No gate vocabulary survives in the four in-scope files | `grep -inE '\bgates?\b' CLAUDE.md docs/DEVELOPMENT_STANDARDS.md docs/dev/specs/_TEMPLATE_SPEC.md docs/dev/results/_TEMPLATE_RESULTS.md` returns zero hits | 2, 3, 5 |
| AC2 | The historical citations were reworded, not deleted — the underlying facts survive | `grep -n "v1.24.0" CLAUDE.md docs/DEVELOPMENT_STANDARDS.md` still returns both the OQ4 row and the §1.3 Item 32 narrative | 1 |
| AC3 | `DEVELOPMENT_STANDARDS.md` defines both concepts in one section, and defines authorization by irreversibility | `grep -n "^### 1.4" docs/DEVELOPMENT_STANDARDS.md` returns one hit; that section contains `irreversible` and `reach outside the working tree` | 2 |
| AC4 | The DB-migration rule survives, expressed as an authorization point | `grep -n "migration" docs/DEVELOPMENT_STANDARDS.md` returns the §4.5 rule; §4.5 contains a `§1.4` citation and does **not** restate the definition — verified by DR2's test, that the sentence is not actionable with §1.4 deleted | 3 |
| AC5 | A stated split test exists, keyed on independent verifiability | §1.3 contains the DR7 sentence; `grep -n "independently verifiable" docs/DEVELOPMENT_STANDARDS.md` returns a hit inside §1.3 | 4 |
| AC6 | Spec template §4 matches the revised standard and matches the two working precedents | `grep -n "^## 4. Steps" docs/dev/specs/_TEMPLATE_SPEC.md docs/dev/specs/TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md docs/dev/specs/ISSUE_CREATION_VALIDATION_SPEC.md` returns three hits | 5 |
| AC7 | Stop-and-surface is retained in § Critical Rules and stated independent of any boundary; Role 3's escalation procedure survives alongside it | `grep -n "STOP and WAIT" CLAUDE.md` returns one hit, inside § Critical Rules; `grep -n "Do NOT self-resolve" CLAUDE.md` returns one hit, inside Role 3. AC1's sweep plus `grep -in "step boundary" CLAUDE.md` returning zero covers the boundary clause | 6 |
| AC8 | No process rule is stated in both documents, except the Ray-approved § Critical Rules entries | Every rule in recon §3.2 F14–F25 that is **not** a § Critical Rules entry appears in exactly one of the two files. Checked per rule with a distinguishing phrase; e.g. `grep -c "own hotfix" CLAUDE.md docs/DEVELOPMENT_STANDARDS.md` returns `0` and `1`. F15 and F19 are the exempted pair, checked by AC17 | 7, 1 |
| AC9 | The surviving § Common Pitfalls bullets have no counterpart in `DEVELOPMENT_STANDARDS.md` **and** none restates another `CLAUDE.md` section | For each surviving bullet, its distinguishing phrase returns zero hits in `docs/DEVELOPMENT_STANDARDS.md` and exactly one hit in `CLAUDE.md`. `grep -c "different write paths" CLAUDE.md` returns `1`, inside § Key Design Decisions | 7 |
| AC10 | #82's design-study citation resolves | `test -f docs/dev/design/RECON_CYCLE_MECHANICS.md` succeeds on this branch, and the path matches `ISSUE_CREATION_VALIDATION_SPEC.md:9` | — (Q5) |
| AC11 | No spec is `Status: Approved` while its issue is closed | `grep "^\*\*Status:\*\*" docs/dev/specs/TRACKING_SEMANTICS_CONSOLIDATION_SPEC.md docs/dev/specs/ISSUE_CREATION_VALIDATION_SPEC.md` returns `Shipped` for both. Restricted to the two files — a glob matches `_TEMPLATE_SPEC.md:3`'s `Draft \| Approved \| Shipped \| Superseded` legend | — (Q6) |
| AC12 | No application behaviour changed | `git diff --stat main -- workmain/ tests/ config/ templates/ automation/ .github/ pyproject.toml` is empty | — |
| AC13 | No in-scope document instructs the reader to run the application suite with an explicit path | Over the four in-scope files only: `grep -n "python -m pytest"` returns zero hits, and `grep -n "pytest tests/" \| grep -v "tests/test_"` returns zero hits. The surviving `pytest tests/test_x.py::...` forms are single-test invocations, correct per DR10. Shipped specs and handoffs are excluded — they record commands as they were run | 8 |
| AC14 | No document claims tests exist only in `tests/` | `grep -n "Everything lives in" docs/DEVELOPMENT_STANDARDS.md` returns zero hits; §6's preamble names non-application suites and cites §6.3; `grep -n "only discovers here" docs/DEVELOPMENT_STANDARDS.md` returns zero hits | 9 |
| AC15 | Test placement has one owner | The §6 preamble text added for AC14 contains no path other than `tests/`, and cites §6.3. `automation/` appears in §6.3, §7, and §2.2 — the same three places as today, with no fourth added | 9 |
| AC16 | `CLAUDE.md:3` states the single-home output rule and is not restated anywhere | `grep -c "exactly one home" CLAUDE.md` returns `1`; the same grep over `docs/DEVELOPMENT_STANDARDS.md` and both templates returns `0`; `grep -n "All responses should be" CLAUDE.md` returns zero hits | — (Ray, 20260819) |
| AC17 | § Critical Rules is first, declares its exemption, and holds exactly the Ray-approved entries this spec names | `grep -n "^## " CLAUDE.md \| head -1` returns `## Critical Rules`; the section contains the DR1a sentence; its entries are exactly those named at §4 step 5a and no others; every entry names the section that owns its full statement, per DR1a | 7 |
| AC18 | Neither document still claims they share no content, and nothing else claims to be read first | `grep -rn "Nothing is duplicated\|Nothing here is duplicated" CLAUDE.md docs/DEVELOPMENT_STANDARDS.md` returns zero hits — the step 1 and step 5 replacements drop the phrase rather than qualifying it; `grep -n "READ THIS FIRST" CLAUDE.md` returns zero hits | — (Ray, 20260819) |

## 6. Test plan

No application code changes, so no test changes. The suite must be **identical** before and
after — same collected set, same result.

- Run `pytest` on this branch before step 1 and record the result outside this document;
  run it again after step 9 and compare. Running on the branch rather than `main` is
  equivalent — AC12 proves the application diff is empty — and avoids a checkout. `testpaths = ["tests"]` in `pyproject.toml` resolves a
  bare `pytest` to the application suite, so no path argument is passed. No count is
  transcribed here — per the standing rule, live counts are derived at point of use, not
  written into artifacts.
- `automation/` carries its own suite (`*_test.py`), outside `testpaths` and reached only
  by an explicit path per §6.3. It is untouched, but run `pytest automation/` once at
  step 9 to confirm F33's finding still holds.
- AC12 is the mechanical guard: if the application diff is empty, the suite cannot have
  moved.

## 7. Risks and rollback

| Risk | Blast radius | Mitigation |
| --- | --- | --- |
| A rule is deleted from `CLAUDE.md` as a duplicate when the `DEVELOPMENT_STANDARDS.md` copy says something subtly different | A standard silently weakens | Step 4 diffs each pair before deleting, and any wording the two do not share is merged into the surviving copy rather than dropped. AC8 checks presence, not equivalence — this is the one place a human read is required |
| The § Critical Rules authorization entry and §1.4 drift apart, since DR1a has them stating the same rule | The always-visible copy silently goes stale | DR1a requires every entry to name its owning section, so the pair is discoverable. This is the accepted cost of the exemption: two copies that must move together, in exchange for the rule being visible to a session that has read nothing else |
| § Critical Rules moving to the top displaces the three-role model, which announces itself as what to read first | Two sections both claim primacy | Step 5 rewords the role model's marker in the same commit. AC18 checks the old marker is gone |
| Step 8's branch merge drags in unrelated commits | Scope creep on a `chore/*` branch | `chore/cycle-mechanics-recon` touches one file. Verified with `git diff --stat main...chore/cycle-mechanics-recon` before merging; if it shows anything but `RECON_CYCLE_MECHANICS.md`, stop and surface |
| The §6 rewrite for AC14 reintroduces a location list, or `pyproject.toml` is edited to "fix" a path | A second register to maintain, or a config change on a docs-only branch | AC15 checks the first; AC12's diff now covers `pyproject.toml` and catches the second. `testpaths` is already correct and this spec does not touch it |
| The four Shipped specs still read in gate vocabulary, contradicting the new standard | A reader treats a historical spec as current guidance | Accepted deliberately — they are records of how that work ran. Their `Status: Shipped` is the signal. #83 may add an explicit banner; not this spec's call |

Rollback is per step: each is a single commit on a `chore/*` branch touching documentation
only. `git revert` of any one step restores the prior wording with no application impact.
Nothing here is irreversible before the step 9 merge.
