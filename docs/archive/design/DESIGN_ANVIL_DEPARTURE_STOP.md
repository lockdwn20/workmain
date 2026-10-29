# Anvil Departure Stop — Design Study

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261029
**Originating item:** Issue #250

---

## 1. Purpose

Issue #250 makes Anvil (Role 3) stop before it makes a departure, rather than make one and record it afterwards. #203's results artifact listed four departures with `Step stopped at` set to `none`, three of them written by Anvil itself. The issue names eight gaps and fixes eight acceptance criteria. Most of the change is decided by the issue and the standards, and §4.1 states it so the spec can cite it. Two questions remain, and each changes the work: whether the new rule for `none` also binds Role 1 on the direct path, and whether Caliper reviews this spec.

## 2. Scope of the read

- **Read in full:** `.claude/skills/session-start/SKILL.md` and its three references; `docs/dev/results/_TEMPLATE_RESULTS.md`; `docs/dev/specs/_TEMPLATE_SPEC.md`; `docs/standards/README.md`, `docs/standards/1-workflow.md`, `docs/standards/2-git.md`; issues #240 and #250; `docs/archive/results/CALENDAR_COMMANDS_RESULTS.md` §4, the #203 record the issue rests on.
- **Searched:** the document set `docs/standards/1-workflow.md` §1.5 names for a rule change (`CLAUDE.md`, `docs/standards/`, `.claude/`, the `docs/dev/*/_TEMPLATE_*.md` files), plus `.github/` and `automation/`. The search ran on 20261029 on branch `chore/issue-250-anvil-stop-on-departure` at `da37417`, as `git grep -nEi 'departure|approval stop|go-ahead|discrepanc|document the issue|deviation|STOP at|stops? (it|on|at)|before touching step'`, and every hit was read. Its live statements are F1–F8.
- **Read for precedent:** `docs/archive/design/DESIGN_DEVIATION_RECORD.md` (#242, which introduced `none`) and `docs/archive/specs/POST_IMPLEMENTATION_REVIEW_SPEC.md` (#243, whose criterion AC3.1 ran a live session check against its own branch).
- **Not in scope:** `docs/standards/6-testing.md`. #244 added it to Anvil's session-open reads. The issue moves that part to #244, and it shipped there.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | Role 3's stop trigger is "anything the spec doesn't cover, or that requires a design decision". The full definition of a departure ("any difference between the approved spec and what was delivered, including an ambiguity the spec did not settle") is stated only in the results template, which calls itself advisory. Role 1's reference relies on the full definition: "`SKILL.md` § Role 3 stops it on every departure". A different route to the same end state is a departure under the template but not under Role 3's trigger. | `.claude/skills/session-start/SKILL.md:100`; `docs/dev/results/_TEMPLATE_RESULTS.md:46`, `:17`; `.claude/skills/session-start/references/spanner.md:36` | High |
| F2 | `none` is one of three `Step stopped at` values, and the template says what the other columns hold when it is used. Writing the row is therefore something an implementer can do instead of stopping. #203 has three such rows that Anvil wrote and a fourth that Caliper found. | `docs/dev/results/_TEMPLATE_RESULTS.md:50`; `docs/archive/results/CALENDAR_COMMANDS_RESULTS.md` §4 rows 1–4 | High |
| F3 | The issue's AC2 reserves `none` for "a departure the post-implementation review finds". Under that wording, a departure Anvil finds itself after making it can be recorded with no value at all: it did not stop before it, and it is not a review finding. On the direct path, where the review runs only if Ray chose a Caliper review of the spec, no departure could ever get a `none` row. The property AC2 is for — a `none` row is never written as a substitute for a stop — holds if a `none` row is written only after Ray has ruled on the departure, whoever found it. | `docs/standards/1-workflow.md:25-28` (§1.1 Implementation review: Ray rules on each unstopped departure as the resolution of its Decision Log row, and results §4 then lists it with `none`); `docs/standards/1-workflow.md` §1.2 last bullet (direct-path review at Ray's discretion) | High |
| F4 | Nothing governs the work between the session-open run and the results artifact. `references/anvil.md` ends at its Discrepancies emit. It has no § Working rules, though `CLAUDE.md` § THREE-ROLE MODEL makes that section the home of a single role's rules, and Spanner's and Caliper's references each have one. | `.claude/skills/session-start/references/anvil.md:14-23`; `CLAUDE.md` § THREE-ROLE MODEL; `references/spanner.md` § Working rules; `references/caliper.md` § Working rules | High |
| F5 | §1.4 says "No approval stop. A step ends with a commit, not with a request to continue", and the spec template says "There is no approval stop between steps". Neither names an exception. | `docs/standards/1-workflow.md:109`; `docs/dev/specs/_TEMPLATE_SPEC.md:66` | Medium |
| F6 | Role 3 says to "report discrepancies before touching step 1". Nothing says Anvil waits for Ray after the report, or what Ray's go-ahead covers. In #203, "Proceed" was read as clearing the whole run. | `.claude/skills/session-start/SKILL.md:92`; `references/anvil.md:23` ("What happens next is `SKILL.md` § Role 3") | Medium |
| F7 | Read 5 checks "Every reference the spec makes — file, symbol, line, section or command — at the cited location". It does not say what resolving each kind means, so two runs can check to different depths and both print `none`. It names no quoted text to be replaced and no claim about behaviour, which a step or a §2 row carries. | `.claude/skills/session-start/references/anvil.md:11`, `:21` | Medium |
| F8 | A stop has no stated form: "Document the issue clearly in chat". | `.claude/skills/session-start/SKILL.md:103` | Medium |
| F9 | Nothing parses results §4. `automation/closeout_acs.py` reads only `## 3.`, and the fixtures carry `## 4.` with no rows. Changing what `none` may hold breaks no check. | `git grep -nEi 'stopped\|Awaiting Ray' -- automation .claude/skills/closeout` returns no §4 reader | Low |
| F10 | The issue's AC8 asks for a test spec "whose step states a route that differs from the cheapest route" to its design rule's end state, and expects a stop. A stated route that can be followed produces no departure, so Anvil following it correctly stops on nothing, and the check fails on correct behaviour. A stop is due only where the stated route cannot reach the design rule's end state and a different route can. | Issue #250 AC8; this study §4.1 item 8 | Medium |

## 4. Options and decided mechanics

### 4.1 Decided by rule

Each item is the issue's stated change. Where it says how, the issue or a standard fixed it.

1. **One definition of a departure, in `SKILL.md` § Role 3** (F1, AC1). A departure is any difference between what the spec says a step delivers and what is about to be delivered. What the spec says covers the step's deliverable, its Files entry, its quoted text, and the design rules and criteria that govern it. The definition names a different route to the same end state, a change the step does not name, an ambiguity, and a conflict inside the spec. It is worded for "about to be delivered", so it is the trigger for a stop and not only a record. The results template and `references/spanner.md` cite it. It goes in `SKILL.md`, not in Anvil's § Working rules, because three roles use it.
2. **`none` is written only after Ray's ruling** (F2, F3, AC2). A departure Anvil finds after making it is stopped on where it is found, in the stop form (item 6). Its row takes `none` only once Ray's ruling sits in the spec's Decision Log, with `Resolved by` naming Ray and that row's date, as §1.1 states. Anvil never writes a `none` row before the ruling exists. This restates the issue's AC2, under `docs/standards/1-workflow.md` §1.2 (a design that makes a criterion wrong restates it): reserving `none` for review findings alone leaves a self-found departure unrecordable (F3). `caliper.md` check I3 (a `none` row with `Resolved by` `Awaiting Ray`) still catches a row written in place of a stop, and needs no change. Whether this binds Role 1 too is Q1.
3. **Anvil's § Working rules: a per-step procedure** (F4, AC3). Before a step's first change, Anvil re-reads the step and every design rule and criterion that governs it. Before the commit, it stages only the files it wrote (`docs/standards/2-git.md` §2.4), compares the staged set with the step's Files entry, and compares the staged diff with the step's text. Any difference in either direction stops the step: a file or change the step does not name, or something the step names that was not delivered. The issue's own gap 3 names the re-read before the step as well as the check before the commit, so both are in.
4. **§1.4 and the spec template name the exception** (F5, AC4). Each keeps "no approval stop" for a step that goes as written and states that a departure stops the step, citing `SKILL.md` § Role 3. Both texts govern direct-path steps too, so each also cites `references/spanner.md` § Working rules for Role 1.
5. **The go-ahead** (F6, AC5). `SKILL.md` § Role 3 states that Anvil waits for Ray's go-ahead after the discrepancy list, `none` included. The go-ahead authorizes the steps as the spec writes them and nothing that departs from them. It resolves no discrepancy: each one is settled by what Ray states for it, and a defect in the spec is settled in the spec (`SKILL.md` § Spanner → Anvil handoff). `references/anvil.md` cites the statement.
6. **The stop form** (F8, AC7). In `SKILL.md` § Role 3, with these fields: the step; the spec text, quoted (the step's text, or the design rule or criterion); what would be delivered instead, and why; what the step has changed in the working tree so far; and the options Anvil sees. It has no recommendation field, because Anvil holds no design authority (`SKILL.md` § Role 3).
7. **The depth of the reference check** (F7, AC6). `references/anvil.md` states, for each kind of reference, what resolving it means:
   - a path exists;
   - a symbol is defined in the file named, with any signature the spec gives;
   - a line holds what the spec says it holds;
   - quoted text a step replaces occurs verbatim, as many times as the step says;
   - a section's heading exists and the section says what the spec says it says;
   - a claim about behaviour is shown by the evidence cited;
   - an issue exists, in any state the spec gives;
   - a command is run only if it reads, and otherwise each thing it names is checked to exist.

   A path, symbol or test that a step creates resolves against that step and must not exist yet.
8. **The live check** (F10, AC8). The test spec states a route that cannot reach its design rule's end state, where a cheaper route can. Its step copies a helper verbatim, and the design rule requires behaviour the original does not have. The spec quotes the test spec in full. Ray commits it on a throwaway branch cut from this branch after the rule steps, and runs `/session-start Anvil` against it in a new session. A stop before Step 1's commit, and no `none` row, pass. The branch is never pushed and is deleted locally afterwards, which is not an authorization point (`docs/standards/1-workflow.md` §1.4). This restates the issue's AC8 under §1.2.

### 4.2 Whether the `none` rule binds Role 1 (Q1)

Today the results template lets Role 1, implementing its own direct-path spec, write a `none` row with `Resolved by` `Awaiting Ray` for a change it made without the stop `references/spanner.md` § Working rules requires. Issue #250 names only Anvil.

#### Option A — Anvil only

- **Approach:** the rule in item 2 binds Anvil. Role 1 can still write `none` with `Awaiting Ray`.
- **Pros:** builds only what the issue names.
- **Cons:** one value with two rules in one template bullet. The defect the issue names — a row written instead of a stop — is just as open to Role 1, and on the direct path Role 1's own record may be the only check, since a Caliper review is optional there.

#### Option B — Both implementing roles

- **Approach:** the same rule binds Role 1. `references/spanner.md` § Working rules cites `SKILL.md` § Role 3's statement for it, and the template states one rule.
- **Pros:** one rule for one value. A self-found departure is still recorded, after a stop and a ruling, so nothing is hidden.
- **Cons:** it changes Role 1's working rules, which the issue did not ask for.

**Recommendation:** Option B. The mechanism the issue closes does not depend on the role, and the direct path is where no other check is required. The extra surface is one citation in `references/spanner.md`.

### 4.3 Caliper review of this spec (Q2)

On the direct path, Ray decides at the start whether Caliper reviews the spec, and the post-implementation review runs exactly when it did (`docs/standards/1-workflow.md` §1.2). **Recommendation:** review it. #240's second criterion depends on this rule set working the first time a full-path cycle uses it. A reviewer reading the per-step procedure and the stop form against criterion 3 (where would an implementer have to guess?) is cheaper than another failed cycle.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Does the rule that a `none` row is written only after Ray's ruling bind Role 1 on the direct path as well as Anvil (§4.2)? | Answered 20261029 by Ray: yes, Option B. The rule binds Role 1 implementing its own direct-path spec. |
| Q2 | Does Caliper review this spec, and so also the delivered branch (§4.3)? | Answered 20261029 by Ray: yes, Caliper reviews this spec. |

## 6. Disposition

- Promoted to: `../specs/ANVIL_DEPARTURE_STOP_SPEC.md`
- Superseded by:
