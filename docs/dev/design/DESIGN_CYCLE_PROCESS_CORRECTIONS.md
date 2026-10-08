# Cycle Process Corrections — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261008
**Originating item:** Issue #180

---

## 1. Purpose

Issue #180 carries four independent process gaps found while building `/session-start` (#85). Item 2 is mechanical. Items 1, 3 and 4 each change a rule that is stated or cited in several documents, and items 1 and 4 have more than one defensible answer. This study records what the documents and code say today and recommends an answer for each open question, so the spec is written against settled decisions. The work is `chore/*`, on the direct path (`docs/DEVELOPMENT_STANDARDS.md` §1.1), which permits a recon where a change spans documents that may contradict each other.

## 2. Scope of the read

Read: `CLAUDE.md`; `docs/DEVELOPMENT_STANDARDS.md` §1.1–§1.6, §2.2–§2.8; `.claude/skills/session-start/SKILL.md` and its three references; `.claude/skills/closeout/SKILL.md` preflight table; `docs/dev/specs/_TEMPLATE_SPEC.md`, `docs/dev/design/_TEMPLATE_DESIGN.md`, `docs/dev/results/_TEMPLATE_RESULTS.md`; every write to a file under `config/` or `templates/` in `workmain/`; `ProviderManager` lifetime in the daemon; commit `e5727c5`; every live (non-archive) mention of a handoff.

Not read: `docs/archive/` beyond confirming handoff history and the #85 artifact set; the IaC repository; `automation/` beyond what close-out cites.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | The CLI writes four git-tracked files during normal use: `config/ai_settings.json`, `config/template_aliases.json`, `config/meeting_templates.json`, and `templates/reports/*.json`. | `workmain/cli/commands/providers.py:30` `_SETTINGS_PATH`, `:364` write in `set_default_provider`; `workmain/config_manager/alias_manager.py:44,180`; `workmain/utils/meeting_templates.py:33,46`; `workmain/cli/commands/templates.py:387,393,503,524` | High |
| F2 | §2.8 forbids `config/*` and `templates/*` on `chore/*`; §2.2 permits `config/*` only on `feature/*` or `hotfix/*`, both of which are the full path (spec, recon, review) and a release. No rule covers a value Ray sets through the CLI. | `docs/DEVELOPMENT_STANDARDS.md` §2.2 `**chore/***`, §2.8 bullet 8, §1.1 opening | High |
| F3 | The daemon and the CLI share one working tree. The daemon reads `ai_settings.json` once, through the `ProviderManager` singleton built at startup, so a CLI routing change reaches the daemon only after a restart, and it reaches git only if someone commits it. | `workmain/ai/provider_manager.py:589` `get_provider_manager`; `workmain/daemon/daemon.py:314`; `docs/DEVELOPMENT_STANDARDS.md` §2.6 | Medium |
| F4 | On #85 an operational change was committed to a `chore/*` branch on Ray's direction, against §2.8. Caliper flagged it on criterion 4. | `e5727c5` `chore(config): swap daily and weekly report providers to Gemini primary`; `docs/archive/specs/SESSION_START_SPEC.md:24` | Medium |
| F5 | Both artifact templates show `**Originating item:** Backlog Item #N | Ray request, YYYYMMDD`. `spanner.md` read 4 matches `Issue #<N>`, and `caliper.md` read 2 resolves the issue from the same field. | `docs/dev/specs/_TEMPLATE_SPEC.md:8`; `docs/dev/design/_TEMPLATE_DESIGN.md:7`; `.claude/skills/session-start/references/spanner.md` read 4 | Low |
| F6 | §1.1 names each stage and who does it, but not the artifact or field that shows it done. `spanner.md` § Emits Next stage has to cite §1.2, §1.5 and `_TEMPLATE_RESULTS.md` §3 to judge it. | `docs/DEVELOPMENT_STANDARDS.md` §1.1; `.claude/skills/session-start/references/spanner.md` § Emits | Medium |
| F7 | **Analysis** has no recorded artifact. §1.1 says "decisions are logged" without saying where. Design studies carry no decision log (§1.5) but do carry §5 Open questions with an Answer column; specs carry a Decision Log. | `docs/DEVELOPMENT_STANDARDS.md` §1.1 Analysis, §1.5 Decision Log bullet; `docs/dev/design/_TEMPLATE_DESIGN.md` §5 | Medium |
| F8 | **Review** leaves a trace only when Caliper finds something. A clean pass emits `No findings.`, and nothing requires it to be recorded in the spec, so a reviewed spec with no findings looks the same as an unreviewed one. | `.claude/skills/session-start/references/caliper.md` § Emits | Medium |
| F9 | The results template header offers `Shipped | Superseded`, but §1.5 gives results artifacts `Active`, close-out sets `Shipped`, and #85's results artifact was committed as `Active`. An implementer filling in the template literally would mark the work shipped before close-out. | `docs/dev/results/_TEMPLATE_RESULTS.md:3`; `docs/DEVELOPMENT_STANDARDS.md` §1.5; `.claude/skills/closeout/SKILL.md` P5; `191c260` | Low |
| F10 | No live document defines the Spanner→Anvil handoff. The only live mentions are the one-home statement (`CLAUDE.md:32`, `SKILL.md:16`) and §1.1's note that the direct path has nothing to hand off. | `grep -rni handoff` outside `docs/archive/` | Medium |
| F11 | `/session-start Anvil <spec path>` already loads the spec, checks `Status: Approved`, a clean tree and the branch, and resolves every reference. Each thing Ray's handoff prompts have had to name already has a home: commit per step (§1.4), results artifact as the last step (`_TEMPLATE_RESULTS.md` §3), passed/failed/skipped (`_TEMPLATE_RESULTS.md` §5, §6), restart as close-out's (§1.1 Close-out, §2.6), and Ray-owned checks (§1.2 stated-reading rule). Role 3 cites none of them. | `.claude/skills/session-start/references/anvil.md`; `.claude/skills/session-start/SKILL.md` § Role 3 | Medium |

## 4. Options

### Item 1 — Operational config changes

**Option A — Operational changes ride `chore/*`, as their own commit.** Amend the §2.2 `chore/*` block and §2.8 so that a value written by a `workmain` CLI command during normal use may be committed on `chore/*`, alone in its commit, typed `chore(config)`. No spec, no release. It stays on the branch that is open when it is noticed; with none open, Ray cuts a `chore/*` for it.

- **Pros:** uses an existing branch type, so `/closeout`'s P3, P4 and P11 are unchanged. Matches what `e5727c5` did.
- **Cons:** `chore/*` is defined as "changes no application behaviour", and a routing change does change it. The definition gets an exception that has to be stated precisely. It also requires a spec (§1.1, close-out P4), which is an absurd cost for a config value.

**Option B — Operational changes are committed directly to `dev`, then reach `main` through the next `dev → main` PR.** Extend §2.2's `dev` direct-commit exception from version/changelog to "a value a `workmain` CLI command wrote during normal use". No spec, no release of its own; it travels with whatever release next carries `dev`.

- **Pros:** `dev` is what the daemon runs (§2.6), so the commit lands where the change already lives. No spec and no close-out for something that isn't development. A one-line change to an existing exception.
- **Cons:** `main` lags until the next PR, so a `hotfix/*` cut from `main` in between doesn't carry the change, and the working tree then has to be switched to that hotfix branch with the change uncommitted. §2.7 step 1 requires a clean tree, so the commit to `dev` has to come first. Requires leaving the working branch to commit, or a `git stash` round-trip.

**Option C — Operational state leaves git.** Move CLI-mutable values (report routing, aliases, meeting templates) to a gitignored overlay or `~/.workmain/`, so tracked `config/` holds only what development changes.

- **Pros:** removes the mixed ownership F1 shows at its root. No commit rule needed.
- **Cons:** it's an application change across four writers and their readers. It's `feature/*` work, not a docs rule, and outside a `chore/*` issue's scope. On its own it doesn't satisfy #180's AC1.

**Recommendation: B.** F3 shows the change is already live in `dev`'s working tree when it's made, so `dev` is the honest place to record it. The existing `dev` exception is the one place §2.2 already lets a non-development change skip the feature path. A is wrong on its own definition: `chore/*` is "no application behaviour" and close-out requires a spec. C is the long-term architecture; the spec should name it, but it belongs in its own issue and doesn't replace AC1's rule.

### Item 3 — Done conditions (no real alternative; stated for approval)

One row per stage, with the field or artifact that shows it done. It goes in §1.1, against each stage's existing bullet:

| Stage | Done when |
| --- | --- |
| Recon | A `docs/dev/design/` artifact names the issue in `**Originating item:**`. |
| Analysis | Every open question in that artifact's §5 carries an answer. |
| Spec | A `docs/dev/specs/` artifact names the issue in `**Originating item:**`. |
| Review | The spec's Decision Log carries a `Caliper` row, and every `Caliper` row carries a resolution. A clean pass is recorded as a `Caliper` row reading `No findings.` |
| Approval | The spec's `**Status:**` is `Approved`. |
| Implementation | A results artifact names the spec in `**Spec:**`, with its `**Status:**` set to `Active`. |
| Close-out | The spec's `**Status:**` is `Shipped` and the set is in `docs/archive/`. |

This resolves F7 by naming the design study's §5 answers as Analysis's record, F8 by recording a clean pass as a row, and F9 by setting the results template header to `Active | Shipped | Superseded`. The F9 fix is one value in the template header, which `spanner.md` would otherwise have to work around.

### Item 4 — Spanner→Anvil handoff

**Option A — The handoff is the approved spec's path, given as `/session-start Anvil <spec path>`.** State that in a `### Handoff` subsection of `SKILL.md` § THREE-ROLE MODEL. Role 1 and Role 3 cite it. Role 3 gains citations of the obligations F11 lists, so the extras no longer depend on what a prompt names.

- **Pros:** the spec already carries everything an implementer needs, and `anvil.md` already checks it. Nothing is added that could drift from the spec. It ends the reliance on Spanner remembering the extras in prose.
- **Cons:** Role 3's text grows by a few citations.

**Option B — The handoff is a composed block** that Spanner writes for each spec: spec path, branch, commit-per-step, results artifact, test-count form, and which AC rows are Ray's.

- **Pros:** explicit for every run.
- **Cons:** it restates the spec and four standards sections every time, which `CLAUDE.md`'s one-home rule forbids. It's the hand-written prompt this issue exists to replace, and it's how Ray-owned checks leaked into Anvil's evidence on #179.

**Recommendation: A.** The handoff home is `SKILL.md` § THREE-ROLE MODEL, because that section is already "the only statement of what each role ... hands to the others".

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Item 1: which option governs an operational config change — A (`chore/*`), B (direct commit to `dev`), or C (move the state out of git)? Recommended B, with C opened as its own issue. | |
| Q2 | Item 3: approve the done-condition table, including the `No findings.` Caliper row and the results template header change? | |
| Q3 | Item 4: which option defines the handoff — A (the spec path, with Role 3 citing the existing obligations) or B (a composed block)? Recommended A. | |

## 6. Disposition

- Promoted to: <spec, once Q1–Q3 are answered>
