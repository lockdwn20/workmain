# Spec Self-Consistency — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261029
**Originating item:** Issue #253

---

## 1. Purpose

In #203 and #204 a spec reached Anvil with two of its sections disagreeing, and in both cases Anvil took one of the readings without stopping. Issue #253 closes the three gaps that let that happen. The first is a step that restates a set another section owns. The second is a later Caliper pass that checks only the earlier findings. The third is a Review stage that can be marked done although no pass read the approved text. A fourth gap is Anvil's session-open check, which does not test a reference from one part of a spec to another. The issue fixes the homes of each change and seven acceptance criteria. §4.1 states what the issue and the standards already decide. Three questions remain, and each changes the work: which Caliper session runs the post-implementation review, what a reference from one section to a set another section owns may say, and whether Caliper reviews this spec.

## 2. Scope of the read

- **Read in full:** `.claude/skills/session-start/SKILL.md` and its three references; `docs/standards/README.md`, `docs/standards/1-workflow.md`, `docs/standards/2-git.md`; `docs/dev/specs/_TEMPLATE_SPEC.md`; `docs/dev/design/_TEMPLATE_DESIGN.md`; issue #253 and its parent #240.
- **Evidence the issue cites, re-checked:** `docs/archive/specs/CLIENTS_COMMANDS_SPEC.md` (Decision Log rows 26–41, Step 3.2 at line 160, §6 row C13 at line 262); commits `b946287` (12:23:24), `4dba26f` (12:31:14) and `e0c1702` (12:32:19), all 20261029 -0700; `docs/archive/specs/CALENDAR_COMMANDS_SPEC.md` line 42 (the I3 row on Step 4.2).
- **Searched:** the document set that `docs/standards/1-workflow.md` §1.5 names for a rule change (`CLAUDE.md`, `docs/standards/`, `.claude/`, the `docs/dev/*/_TEMPLATE_*.md` files), plus `.github/` and `automation/`. The search ran on 20261029 on branch `chore/issue-253-spec-self-consistency` at `eca8083`, as `git grep -nE` for `session that reviewed|in this session|same session|Caliper session|fresh session|clean pass|No findings|every .Caliper. row|second round|later pass|re-review`, and again for `review round|review pass|Role 2 review|Role 2 pass|Caliper pass|surgical|resolves a step|same spec|another section|restat`. Every hit was read. Its live statements are F2–F7.
- **Census:** each archived spec's §4, searched for an ID range (`[A-Z]{1,3}<n>–<n>`), by the command in F1.
- **Not in scope:** the archived specs themselves. They are a record and are never updated (`docs/standards/1-workflow.md` §1.5). The Implementation review stage's done condition, which the issue does not name.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | Steps restating an ID range that another section owns is the usual practice, not a one-off. 23 archived specs carry such a range in §4 (the command counts any spec with one or more matches). The greater part are **partitions**, where a step names the share of §6's tests or §3's design rules that it delivers ("Write `tests/test_email_service.py` with T1–T6"). The rest are **whole sets** ("replaced in full by C1–C12"). Of the 63 ranges, 16 are of sets the templates define (DR 12, AC 2, F 2). The other 47 are of labels the specs invented (T 18, C 7, S 5, O 4, P 3, W 2, R 2, and one each of M, L, I, G and E), mostly test labels. No standard or template defines a test label: `docs/standards/6-testing.md`, `docs/dev/specs/_TEMPLATE_SPEC.md` and `docs/dev/results/_TEMPLATE_RESULTS.md` carry none. #203's results artifact needed a table mapping each label to its pytest node (`docs/archive/results/CALENDAR_COMMANDS_RESULTS.md:100`). | `for f in docs/archive/specs/*.md; do awk '/^## 4\./{s=1} /^## 5\./{s=0} s' "$f" \| grep -oE '\b[A-Z]{1,3}[0-9]+(\.[0-9]+)?[–-][A-Z]{0,3}[0-9]+(\.[0-9]+)?\b'; done`; `docs/archive/specs/EMAIL_DRAFT_SERVICE_SPEC.md:209`, `:217`, `:266`; `UNIT_OF_WORK_BOUNDARY_SPEC.md:310`; `CLOCKIFY_COMMANDS_SPEC.md:199`; `ERROR_EXIT_ZERO_SPEC.md:105` | High |
| F2 | Two rules bear on this, and neither covers the case. The first forbids a hand-kept copy of state that lives somewhere authoritative, in a document or a spec step. It names live sources outside the spec (pytest, `gh`, `__version__.py`), and nothing applies it to one section of a spec copying another. The second says "Changes to an existing spec are surgical", and does not say that a change has to find every other statement of what it changes. The cross-document version of that duty exists only for a rule change, which "searches the whole document set". | `docs/standards/1-workflow.md:142` (§1.5), `:70` (§1.2), `:143` (§1.5) | High |
| F3 | Caliper is defined as a single pass: the run reads the spec end to end, emits its findings and stops. Nothing defines a later pass, what it reads, or which session it runs in. In #204 the second round raised one finding, and it was about a resolution (Decision Log row 31). The Step 3.2 / §6 conflict that `b946287` created went unseen until Anvil met it after Step 3's commit (row 36). | `.claude/skills/session-start/references/caliper.md:5-23`; `SKILL.md:76`; `docs/archive/specs/CLIENTS_COMMANDS_SPEC.md:30-31`, `:36` | High |
| F4 | The Review stage counts as done once every `Caliper` row has a resolution. A spec can therefore be approved on text that no pass has read. #204's last finding was resolved at 12:31:14, and the spec was marked Approved at 12:32:19. | `docs/standards/1-workflow.md:57`; `git show -s 4dba26f e0c1702` | High |
| F5 | Three places name the session that runs the post-implementation review, each in its own words. Each assumes there is only one Caliper session: §1.1 says "the Caliper session that reviewed the spec", Role 2 says "in the same session", and the Caliper reference says "in this session". Once every pre-implementation pass runs in a fresh session, a spec has as many Caliper sessions as it had passes, so none of the three phrases picks out a session. | `docs/standards/1-workflow.md:24`; `.claude/skills/session-start/SKILL.md:86`; `.claude/skills/session-start/references/caliper.md:27` | High |
| F6 | Anvil's session-open run checks a section reference against "the file named", for its heading and for what the section says. A step's "C1–C12 (§6)" names no file, so the reference passes as soon as §6 exists, whatever §6's rows hold. | `.claude/skills/session-start/references/anvil.md:16` | High |
| F7 | Caliper's amendment rule says an amendment "does not hold the spec". Spanner then writes the approved wording into the spec. The issue's sixth criterion requires a clean pass on the text that is approved, and once the wording is written in, the approved text is not the text the pass read. As worded, the rule allows exactly that. | `.claude/skills/session-start/references/caliper.md:58`; issue #253 AC6 | Medium |
| F8 | Role 2's seven criteria do not ask whether the spec says the same thing in two places, or whether those statements agree. | `.claude/skills/session-start/SKILL.md:78-84` | Medium |
| F9 | No tool reads the Caliper rows of a Decision Log. A search of `.claude/skills/closeout`, `automation/`, `.githooks/` and `.github/` for `Caliper` returns only a code comment. Changing the Review stage's done condition breaks no check, and `/session-start Spanner`'s Next stage applies whatever §1.1 states. | `git grep -n Caliper -- .claude/skills/closeout automation .githooks .github` → `automation/closeout_acs.py:49` (a comment); `.claude/skills/session-start/references/spanner.md` § Emits | Low |

## 4. Options and decided mechanics

### 4.1 Decided by rule

Each item is a change the issue states. Where the issue or a standard also fixes how it is made, that is stated with it.

1. **No numbered set beyond the template's** (F1, F2, AC1 as restated under Q2). §4.3 states the rule. It goes in `docs/standards/1-workflow.md` §1.2.
2. **A revision finds every statement** (F2, AC2). The "surgical" bullet in §1.2 is extended. A revision of a spec, including the resolution of a review finding, searches the spec for every statement of what it changes, and changes each one. This is the in-spec counterpart of §1.5's rule-change search, and it cites that rule.
3. **Criterion 8** (F8, AC5). Add to `SKILL.md` § Role 2: "Where does this spec state the same thing in more than one place, and do the statements agree?"
4. **Every pre-implementation pass is a full review in a fresh session** (F3, AC4). `SKILL.md` § Role 2 states the rule. Each pass, the first or a later one, is a review of the whole spec as it then stands, against every criterion, opened with a new `/session-start Caliper <spec path>`. A session runs one pass. `references/caliper.md` cites the rule. Its reads already take in the whole spec, Decision Log included, and "a point argued once and reaffirmed by Ray is decided" already keeps a fresh pass from reopening settled findings.
5. **Review is done only on a clean pass over the approved text** (F4, F7, AC6). The Review row in §1.1's table changes. The stage is done when the spec's latest `Caliper` row is the `No findings.` row a pass emits, and nothing in the spec except its `**Status:**` field has changed since the commit that recorded that row. The direct-path `n/a` clause stays as written. Under this rule, wording written in from an amendment is a change that needs another pass. `references/caliper.md` § Working rules is reworded to match: an amendment is not a finding against the spec, but the text it adds is reviewed like any other.
6. **Anvil resolves a reference to another part of its own spec** (F6, AC3). A new entry in `references/anvil.md` read 5. A step's statement of what another part of the same spec holds (a section, or a design rule, step or criterion a section numbers) resolves only when that part holds it. A label numbered outside the sets the template defines is a discrepancy, because §4.3's rule forbids it.
7. **The post-implementation session is stated once and cited** (F5, AC7). Which session runs it is Q1. Wherever the answer is stated, §1.1 Implementation review and `references/caliper.md` § Post-implementation review cite it and do not restate it.

### 4.2 Which Caliper session runs the post-implementation review (Q1)

#### Option A — a fresh session; the run chooses its mode from the artifacts

- **Approach:** Ray opens `/session-start Caliper <spec path>`. The run checks whether a results artifact in the `results/` directory beside the spec names it in its `**Spec:**` field, which is §1.1's done condition for Implementation. If one does, the run is the post-implementation review. If none does, it is a spec review. `references/caliper.md` states how the mode is chosen, and § Post-implementation review drops "in this session".
- **Pros:** every Caliper pass gets the same rule, so AC7's "consistently with fresh sessions" holds without an exception. No session has to stay open while the spec is implemented, which can take hours or days. The mode depends on a file, so the same repository state always gives the same run, which is what `SKILL.md` asks of the skill.
- **Cons:** the way a session opens changes. Once a results artifact exists, no spec review can be run, and no case calls for one.

#### Option B — a fresh session, with the mode as an argument

- **Approach:** `/session-start Caliper <spec path> post-implementation`.
- **Pros:** the mode is written in the command.
- **Cons:** Step 0's usage line and its refusal rules change. Ray can name the wrong mode, and the run has to refuse it by checking the very artifact Option A reads. The argument adds a way to fail and decides nothing the repository does not already show.

#### Option C — the session of the last pre-implementation pass

- **Approach:** the review runs in the session that emitted the clean pass.
- **Pros:** reads stay as they are today.
- **Cons:** that session has the approved spec text in context, which is the bias issue gap 2 names. It has to stay open through implementation. It is the one Caliper session that is not fresh, so AC7 needs an exception to hold.

**Recommendation:** Option A. It applies one rule to every Caliper pass, and it takes the mode from the same file §1.1 already uses to show Implementation done. Option B makes Ray type a fact the repository already holds. Option C keeps the context the issue removes.

### 4.3 What a spec may number (Q2)

The defect is not that a step names members of a set another section owns. A reference is what the one-home rule asks for. The ranges that went stale were of labels the spec invented (F1): C1–C12 in #204 was a numbering of §6's tests that no template defines and no rule governs. The test already has a name, its pytest node ID, in the file that is its one home. The label is a second name for it.

The rule, in `docs/standards/1-workflow.md` §1.2: a spec numbers only the sets its template defines, and names a test by its node ID. The revision rule (§4.1 item 2) keeps every reference to a numbered item true when the set changes, for every set alike. A rule that held some sets' IDs fixed and not others' would be a standard written for the exceptions.

The issue's AC1 forbade a step from restating a set's members at all, which treats a reference as the defect. The spec restates AC1 to this rule (`docs/standards/1-workflow.md` §1.2), and the issue body needs the edit at close-out.

### 4.4 Caliper review of this spec (Q3)

On the direct path, Ray decides at the start whether Caliper reviews the spec, and the post-implementation review runs exactly when the spec review did (`docs/standards/1-workflow.md` §1.2). **Recommendation:** review it. This spec changes how Caliper itself reviews and which session does it. It is also the first spec that has to end on a clean pass over its approved text, and a review is the cheapest way to show that holds before #240's second criterion depends on it.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Which Caliper session runs the post-implementation review: a fresh session that chooses its mode from whether a results artifact exists (A), a fresh session given the mode as an argument (B), or the session of the last pre-implementation pass (C) (§4.2)? | Answered 20261029 by Ray: Option A. The mode check is written into the Caliper skill. |
| Q2 | What may a spec number, and how does a reference to a numbered item stay true (§4.3)? | Answered 20261029 by Ray: the issue's AC1 misread the defect. A reference by ID is what the one-home rule wants. The stale ranges were of labels the spec invented. A spec numbers only the sets its template defines and names a test by its node ID; the revision rule covers every set alike. The rule in §4.3, with AC1 restated to it. |
| Q3 | Does Caliper review this spec, and so also the delivered branch (§4.4)? | Answered 20261029 by Ray: yes. The change crosses roles and needs Caliper's review. |

## 6. Disposition

- Promoted to: `../specs/SPEC_SELF_CONSISTENCY_SPEC.md`
- Superseded by:
