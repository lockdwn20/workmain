# Deviation Record and Self-Resolution Passages — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261026
**Originating item:** Issue #242

---

## 1. Purpose

Issue #242 makes the results artifact's deviations record show that the implementer stopped before departing from the spec. It also requires every passage in the standards that reads as permission to self-resolve to be adjudicated: kept as a named exception to the stop rule in `.claude/skills/session-start/SKILL.md` § Role 3 (the rule that an implementer who meets anything the spec does not cover stops at the current step, tells Ray, and does not resolve it), rewritten to stop, or removed. The issue names three passages and asks for a search for others of the same kind. This study holds that search, a recommended adjudication for each hit, and the two questions only Ray can answer. The spec that follows quotes the exact text for each change.

## 2. Scope of the read

- **Read in full:** `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/dev/specs/_TEMPLATE_SPEC.md`, `docs/DEVELOPMENT_STANDARDS.md` §1, §2 and §6, `.claude/skills/session-start/SKILL.md` § THREE-ROLE MODEL, `.claude/skills/session-start/references/anvil.md` and `references/spanner.md`, issues #240, #242 and #243.
- **Searched:** the document set `docs/DEVELOPMENT_STANDARDS.md` §1.5 names for a rule change (`CLAUDE.md`, `docs/DEVELOPMENT_STANDARDS.md`, the skills under `.claude/skills/`, the three `docs/dev/*/_TEMPLATE_*.md` files), plus `docs/AI_SETTINGS_GUIDE.md`, `.github/` and `automation/`, on 20261026 from branch `chore/issue-242-deviation-record` at `aa058a9`. Terms, each case-insensitive, run one per `grep -rniE`: `deviation|approved by|mid-flight|departure`, `implementer`, `anvil`, `role 3`, `obvious`, `judg`, `interpret`, `carr(y|ies) on`, `proceed`, `note it`, `discretion`, `isn't there|doesn't exist|does not exist|not found`, `self-resol`, `in-flow|mid-flight|mid-implementation`, `stop`. Every hit was read in its paragraph. §3.1 lists those that bear on self-resolution; every other hit states a rule unrelated to an implementer departing from a spec.
- **Read for practice:** §4 of the two most recent results artifacts, `docs/archive/results/CLOCKIFY_COMMANDS_RESULTS.md` (#202, full path) and `docs/archive/results/AUTO_MEMORY_RETIREMENT_RESULTS.md` (#241, direct path). They are cited as the record of what happened, not as the basis for a decision.
- **Read for impact:** `automation/closeout_acs.py` and its fixtures under `automation/fixtures/`, to find whether anything parses results §4.
- **Not in scope:** Caliper's post-implementation review and the disposition of an unstopped departure it finds. Both are #243's, which checks against the record this issue defines.

## 3. Findings

### 3.1 Passages

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | The results template's §4 records a departure and who approved it, and says it "Includes anything surfaced during implementation and resolved by Ray mid-flight". A departure made without stopping and approved afterward fills the same row as one that stopped. | `docs/dev/results/_TEMPLATE_RESULTS.md:44-48`, columns `# \| Deviation \| Reason \| Approved by` | High |
| F2 | §1.1's account of what the direct path trades says that scope no criterion named "is caught *after* implementation, by the results artifact's deviations table". It names the record as the place a gap is caught, and says nothing of a stop. Issue #242 names this passage. | `docs/DEVELOPMENT_STANDARDS.md:51`, § 1.1 "What the direct path trades" | High |
| F3 | §2.2's hotfix-into-feature exception ends "Document the deviation in the feature spec." The deviation is from §2.2's own branch flow (a hotfix that never merges to `main` alone), and it is decided when the feature spec is written, before any step runs. It is not a departure from an approved spec and grants the implementer nothing. Its word "deviation" is the same word as results §4's, for a different thing. Issue #242 names this passage. | `docs/DEVELOPMENT_STANDARDS.md:231-239`, § 2.2 "hotfix/* → feature/* exception" | Low |
| F4 | §6.4 tells whoever meets a spec-named test file that does not exist to "use the established file for that coverage and document the deviation". That is a departure made without stopping. The same case already stops elsewhere: `references/anvil.md` read 5 resolves every file the spec names before step 1 and emits one that does not resolve as a discrepancy, and § Role 3 says discrepancies are reported before step 1. No document cites §6.4. Issue #242 names this passage. | `docs/DEVELOPMENT_STANDARDS.md:791-793`; `.claude/skills/session-start/references/anvil.md` § Reads 5 and § Emits; `grep -rnE '§ ?6\.4\|6\.4 '` over the searched set returns only the heading | High |
| F5 | The commit-message template's body asks the committer to "Note any deviations from spec." A departure recorded in a commit body is the same after-the-fact record as F1, in a second place. Results §4 is the departure record. Found by the search. | `docs/DEVELOPMENT_STANDARDS.md:259`, § 2.4 | Medium |
| F6 | The spec template says the design rules "are what an implementer falls back on when the spec doesn't cover a case". Read as written, an implementer who meets an uncovered case resolves it from the design rules instead of stopping. The template's next paragraph sends that case to § Role 3. A case a design rule decides is covered by the spec; the first sentence says otherwise. Found by the search. | `docs/dev/specs/_TEMPLATE_SPEC.md:56` and `:61`, § 3 Design rules | Medium |
| F7 | On the direct path the implementer is Role 1, in the session that wrote the spec (§1.1). Spanner's working rules "hold for the whole Spanner session", which includes that implementation. Two of them read as self-resolution when applied to an implementation step: "Apply a rule; do not ask … state the answer in one line and carry on", and "A case no standard yet covers does not block the work … the work carries on." Both are right for authoring a spec. Issue #240 names the same advice, held then in auto-memory, as a contributor to #202's unstopped departures. Found by the search. | `.claude/skills/session-start/references/spanner.md` § Working rules, first and ninth bullets, and its opening sentence; `docs/DEVELOPMENT_STANDARDS.md:44`, § 1.1 direct path "Implementation" | High |
| F8 | Nothing states that the stop rule binds Role 1 when it implements on the direct path. § Role 3 is addressed to Anvil. `CLAUDE.md` § Critical Rules "Stop and surface" is global but is written for a design question, not for a departure from an approved spec. | `.claude/skills/session-start/SKILL.md` § Role 3; `CLAUDE.md` § Critical Rules; `docs/DEVELOPMENT_STANDARDS.md:44` | High |

### 3.2 Hits read and found not to grant self-resolution

| Passage | Why it does not |
| --- | --- |
| `docs/DEVELOPMENT_STANDARDS.md:111` § 1.4 Steps, "No approval stop. A step ends with a commit, not with a request to continue." and `docs/dev/specs/_TEMPLATE_SPEC.md:65` "There is no approval stop between steps." | They govern a step that goes as specified: no routine check-in between steps. They say nothing about a case the spec does not cover. |
| `docs/dev/specs/_TEMPLATE_SPEC.md:30`, a Decision Log row with Source `Anvil` | A place for a finding Anvil raised to be recorded with its resolution. It grants no decision to Anvil. |
| `.claude/skills/closeout/SKILL.md:96` "STOP and surface to Ray. No self-resolution" | Consistent with § Role 3. |
| `docs/AI_SETTINGS_GUIDE.md:48`, a model-change step "stops and reports" | Consistent with § Role 3. |
| `CLAUDE.md` § Common Pitfalls, "surface the disagreement before running either" | Consistent with § Role 3. |
| `docs/dev/results/_TEMPLATE_RESULTS.md` § 3, "Anything not met is listed here and carried to an issue" | About an unmet criterion, not a departure. |

### 3.3 Practice

| # | Finding | Evidence |
| --- | --- | --- |
| F9 | #202's §4 carries six rows, each approved "Ray, 20261026" or "Spec corrected". Row 3 says "I recorded it here instead of stopping"; row 6 says "I did not record this in the first pass". The template could not show which rows had a stop. | `docs/archive/results/CLOCKIFY_COMMANDS_RESULTS.md` § 4 |
| F10 | #241's §4, on the direct path, carries two rows Spanner made without stopping (a removed blank line; trimmed trailing blank lines on two issue bodies), each with `Approved by` "Not stopped for: recorded here instead". | `docs/archive/results/AUTO_MEMORY_RETIREMENT_RESULTS.md` § 4, rows 2 and 3 |
| F11 | Nothing parses results §4. `automation/closeout_acs.py` reads only the table under `## 3.` and stops at the next `##` heading. The fixtures carry a `## 4. Deviations from spec` heading with `None.` under it. Changing §4's columns breaks no check. | `automation/closeout_acs.py:176-183`; `automation/fixtures/closeout_results_*.md` |

## 4. Options

Two corrections Ray gave earlier bear on this. On #202's implementation (20261026): "A results Deviations row is for something Ray already decided, not a substitute for stopping." And the note §6.4 was written from (20260725, during the implementation of pre-migration backlog Item 61, Report Review & Weekly Generation Unification, shipped in v1.26.0; the note was held in auto-memory, which #241 retired): "This is a 'proceed with the obviously-correct interpretation and note it' situation, not a 'stop the gate and wait for Ray' situation — the latter is reserved for actual design ambiguity (scope, architecture, behavior), not filename bookkeeping." Issue #242 carries both. The second is the earlier, and it is the position issue #240 sets out to close.

### 4.1 Results template §4

Issue #242 states the change, and no option is open. A departure is any difference between the approved spec and what was delivered, including an ambiguity the spec did not settle, and every one is listed with how it was handled, how it was resolved and who resolved it. The columns become `#`, `Departure or ambiguity`, `Step stopped at`, `Resolution`, `Resolved by`. `Step stopped at` holds the step the implementer stopped at; `within approved meaning` for a wording or mechanical change Role 1 made without stopping on its own direct-path spec (Q1's answer), never used by Anvil; or `none` for a change made without the stop it required, which breaks the stop rule. A `none` row is still listed, because a record that leaves it out hides it. #243's review reads these values. The heading `## 4. Deviations from spec` is kept: F11 shows nothing depends on it, and keeping it costs nothing. The issue's wording says "a Role 3 violation"; under Q1's answer the stop rule is § Role 3 for Anvil and `references/spanner.md` § Working rules for Role 1, so §4 names both.

### 4.2 §1.1 "What the direct path trades" (F2)

- **Keep as a named exception.** Defeated: the passage describes a cost of the path, not a case where stopping is waived. Making it an exception would grant the direct-path implementer exactly the permission F10 shows being taken.
- **Remove.** Defeated: the passage gives the reason the path is keyed on branch type, which nothing else states.
- **Rewrite to stop.** The only valid option. The trade is unchanged: with no recon and no review, a gap in the spec is found only at implementation. The rewrite says it is found *during* implementation, when the implementer stops on it, and is then recorded in results §4, rather than caught *after* implementation by that record.

### 4.3 §2.2 hotfix-into-feature exception (F3)

- **Keep as a named exception.** Defeated: it is not an exception to the stop rule, because it is decided at spec time. Marking it as one would say the implementer could take it on its own.
- **Remove.** Defeated: the exception is a real branch flow and the record of it is needed.
- **Rewrite.** The only valid option. "Document the deviation in the feature spec" becomes a statement that the feature spec's Decision Log records the folded hotfix, which puts the decision before approval and drops the word "deviation" that results §4 now owns.

### 4.4 §6.4 spec-named test file does not exist (F4)

- **Keep as a named exception.** This is the 20260725 note's position: filename bookkeeping is not design ambiguity. It is defeated by Ray's later correction on #202, by issue #240's requirement that every departure show a stop, and by the fact that "the established file for that coverage" is a judgment about where tests belong, which `docs/DEVELOPMENT_STANDARDS.md` §6.3 makes at spec time.
- **Rewrite to stop.** It works, but a rewritten §6.4 would state a second time what `references/anvil.md` read 5 and § Role 3 already do for every unresolved file reference, of which a test file is one case.
- **Remove the section.** Recommended. The case already stops before step 1 by the Anvil session-open read, and nothing cites §6.4.

Q2 asks Ray to choose, because his two corrections conflict here.

### 4.5 §2.4 commit body (F5)

Remove "Note any deviations from spec." from the body placeholder. It is the only valid option. Results §4 is the departure record, and `CLAUDE.md`'s opening gives each fact one home. Kept as an exception, it would invite the after-the-fact record #242 removes. Rewritten, it would restate §4 in a commit body.

### 4.6 Spec template §3 design rules (F6)

Rewrite the sentence. It is the only valid option. A design rule still decides the cases it covers, so it should not be removed. Recommended text: design rules are invariants the implementation holds to; a case one decides is covered by the spec, and a case none decides is not, so it stops under `.claude/skills/session-start/SKILL.md` § Role 3. The template's existing pointer to § Role 3 stays.

### 4.7 Direct-path implementer (F7, F8)

Depends on Q1.

- **A — the stop rule binds whoever implements.** `references/spanner.md` § Working rules gains a rule that Role 1, implementing a direct-path spec, stops under the stop rule in `.claude/skills/session-start/SKILL.md` § Role 3, with Ray deciding directly, since Spanner is the one he would bring it to; and its opening sentence says the other working rules govern authoring and do not apply to an implementation step. That file is the home because `CLAUDE.md` § THREE-ROLE MODEL puts a rule for how a single role works in that role's reference file, and only a Spanner session loads it. §1.1 and `SKILL.md` do not change. Results §4's wording names the stop rule, not "Role 3", so it reads correctly on both paths.
  - **Pros:** one record with one meaning on both paths. #243's check for a §4 entry with no recorded stop works the same on either path. Closes the route F10 shows was used.
  - **Cons:** Role 1 stops on whitespace-level departures like F10's, which costs a round trip each time. Touches `references/spanner.md`, beyond the files issue #242 names.
- **B — the stop rule binds Anvil only.** Results §4 keeps issue #242's "Role 3 violation" wording. On the direct path, a row without a stop is allowed, as in F10.
  - **Pros:** no change outside the three named files. Fast for trivial direct-path edits.
  - **Cons:** §4 means one thing on the full path and another on the direct path. The Spanner working rules that issue #240 names as a contributor stay in force during an implementation. #243 would have to tell the two paths apart.

**Recommendation: A.** Issue #240's requirement is that every departure shows a stop, and F10 shows the direct path is where one was most recently skipped. The extra files are where F7 and F8 put the defect; leaving them would leave the route open.

**Answer (Ray, revised 20261027): neither A nor B as written.** The stop rule binds Anvil on every departure, because Anvil holds no design authority. When Role 1 implements its own direct-path spec, it holds design authority, and Ray's approval of the spec is the only review between the spec and the edit (§1.1). So Role 1 keeps its judgment over wording and mechanics within the meaning, scope and file set Ray approved, records such a change in results §4 as `within approved meaning`, and stops on any change to meaning, scope or file set. An ambiguity about which kind a change is counts as a change of meaning. "Apply a rule; do not ask" and "A case no standard yet covers does not block the work" do not decide a change of meaning, scope or file set during that implementation; the other working rules are unaffected. The first answer, A, made Role 1 an Anvil for docs work, the work its judgment is most needed for, and would have stopped both of F10's whitespace fixes. The rule goes in `references/spanner.md` § Working rules, for the reason option A gives.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | On the direct path, Role 1 implements its own spec, and nothing states that the stop rule in `.claude/skills/session-start/SKILL.md` § Role 3 binds it. Spanner's working rules ("apply a rule; do not ask", "the work carries on") stay in force during that implementation. #241's results show Spanner departing from its spec twice without stopping and recording it afterward. Should the stop rule bind whichever role implements (option A in §4.7: §1.1 and `references/spanner.md` change, and results §4 names the stop rule instead of "Role 3"), or Anvil only (option B: those files stay as they are, and a direct-path §4 row may carry no stop)? Recommendation: A. | Answered 20261027 (Ray), revised the same day: the stop rule binds Anvil on every departure. Role 1, implementing its own direct-path spec, keeps its judgment over wording and mechanics within the meaning, scope and file set Ray approved, and stops on any change to them, because it holds design authority and Ray's approval is the only review on that path. The first answer, binding whichever role implements, made Role 1 an Anvil for docs work. §4.7 records it. |
| Q2 | `docs/DEVELOPMENT_STANDARDS.md` §6.4 tells an implementer who meets a spec-named test file that does not exist to use the established file and record the deviation. Ray's 20260725 note, made while pre-migration backlog Item 61 (Report Review & Weekly Generation Unification) was implemented, says that is bookkeeping, not a stop. His 20261026 correction on #202 says a deviation row is never a substitute for stopping. The same case is already stopped before step 1 by `references/anvil.md`'s check of every file the spec names. Should §6.4 be removed (recommended: the case already stops, and nothing cites §6.4), rewritten to stop (a second statement of the session-open check), or kept as a named exception (the 20260725 note's position)? | Answered 20261027 (Ray): remove §6.4. |

## 6. Disposition

- Promoted to:
