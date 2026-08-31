# Archive on close-out — Implementation Results

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20260831
**Spec:** `docs/dev/specs/ARCHIVE_ON_CLOSEOUT_SPEC.md`
**Released as:** n/a — `chore/*` (`docs/DEVELOPMENT_STANDARDS.md` §2.2)

---

## 1. Summary

Complete. `/closeout` now moves the closing branch's artifact set to `docs/archive/<type>/` as a step of its own, in all three variants, committed on the branch before any merge. `docs/DEVELOPMENT_STANDARDS.md` §1.5 names the three `docs/dev/` paths it previously named bare, and its archive trigger is completion alone — the "no longer a live reference" clause is gone, because nothing outside `docs/dev/` cites an artifact by name and it was never a second condition.

The change issue #112 did not name is the one that makes the rest work: `automation/closeout_acs.py` hard-coded `docs/dev/specs` and `docs/dev/results`, so an archived set could not be resolved at all. It now searches live-then-archive and derives the results path from the spec's own root.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | §1.5's archive bullet names `docs/dev/design/`, `docs/dev/specs/` and `docs/dev/results/`, states that `/closeout` performs the move, and gates it on completion alone. `docs/archive/README.md` reduced from a full restatement of the rule to a pointer at §1.5 | `docs/DEVELOPMENT_STANDARDS.md`, `docs/archive/README.md` | +0 |
| 2 | `SPEC_ROOTS` searches `docs/dev/specs` then `docs/archive/specs`; `derive_results_path` resolves beside the spec's own root rather than at a constant; both spec-file citations dropped from the docstrings | `automation/closeout_acs.py`, `automation/closeout_acs_test.py` | +4 |
| 3 | `P4`, `P5` and `P5a` state the two-root lookup, and a new paragraph states that resolving from the archive is a normal result rather than a finding | `.claude/skills/closeout/SKILL.md` | +0 |
| 4 | The archive step at step 2 of `chore` and `feature` and step 3 of `hotfix`, with every later step and every step-number cross-reference renumbered | `.claude/skills/closeout/references/{chore,feature,hotfix}.md`, `.claude/skills/closeout/SKILL.md` | +0 |
| 4a | A fixture that cited a live spec by name and a review finding id now describes the AC shape it is a fixture for | `automation/fixtures/closeout_spec_bare_acn.md` | +0 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | The §1.5 archive bullet at `docs/DEVELOPMENT_STANDARDS.md:104` names all three of `docs/dev/design/`, `docs/dev/specs/` and `docs/dev/results/`, and no bare `design/`, `specs/` or `results/` remains in it |
| AC1.2 | Met | `grep -c 'no longer a live reference' docs/DEVELOPMENT_STANDARDS.md` returns `0` |
| AC1.3 | Met | `grep -c 'Documentation Standards' docs/archive/README.md` returns `0`; the file is 3 lines, stating no rule of its own |
| AC2.1 | Met | `grep -c 'docs/archive' .claude/skills/closeout/references/{chore,feature,hotfix}.md` returns `1` each, and each row's `Done when` opens `The branch tip carries` |
| AC2.2 | Met | `grep -oE '^\| [0-9]+ \|'` returns `1 2 3 4 5 6` for `chore`, `1..9` for `feature` and `hotfix` — consecutive, no gap or repeat |
| AC2.3 | Met | `pytest automation/closeout_acs_test.py` — `test_ac2_3_archived_set_resolves_and_passes` and `test_ac2_3_results_root_follows_the_spec_root` pass. Also exercised end to end: a scratch repo holding a set only under `docs/archive/` exited `2` with `no spec names branch chore/probe` before the change and `0` after, in both working-tree and `--tree HEAD` mode |
| AC2.4 | Met | `test_ac2_4_spec_in_both_roots_is_reported_not_resolved` asserts `more than one spec` and a `None` label |
| AC2.5 | Met | Every `.md` basename under `docs/dev/**` and `docs/archive/**` grepped against `automation/` returns no hit. One hit existed at verification time and was fixed — see step 4a and deviation 2 |
| AC2.6 | Met | Semantic, per `docs/DEVELOPMENT_STANDARDS.md` §1.2 — Ray to read `.claude/skills/closeout/SKILL.md` `P4`, `P5`, `P5a` and the paragraph above § "If any row fails" |
| AC2.7 | Met | `pytest` 934 passed, 0 failed; `pytest automation/` 41 passed, 0 failed |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | §6 predicted `automation/` at 37 + 3; it is 37 + 4 | DR5's dev-first ordering had no test of its own. `test_ac2_3_live_root_wins_when_a_stale_copy_sits_in_the_archive` asserts the constant's order directly, so a reordering that would make close-out prefer an archived spec over a live one fails a test rather than passing silently | Spanner |
| 2 | AC2.5's stated check — `grep -rnE '_(SPEC\|RESULTS)...' automation/*.py` — was too broad and too narrow at once | It matched the module's own filename-pattern regexes and its tests' synthetic fixture names, none of which are citations, while missing `automation/fixtures/*.md`, where the one real citation was. Verified against the precise predicate instead: every real artifact basename under `docs/dev/**` and `docs/archive/**`, grepped across all of `automation/`. That found `closeout_spec_bare_acn.md` naming a live spec, fixed in step 4a | Spanner |
| 3 | Step 4 also touched `.claude/skills/closeout/SKILL.md`, which §4 assigned to step 3 | The closing comment's "the path to the results artifact" is ambiguous once the artifact moves. One clause added saying it is the archived path, since the comment is composed after the move in all three variants | Spanner |
| 4 | `feature.md`'s "Why this order" gained a fifth bullet, and its count word with it | The archive step's placement before the merge is exactly the kind of thing that section exists to explain, and the standards do not explain it: archiving after the merge would mean editing documents directly on `dev` or `main`, which §2.2 forbids | Spanner |

## 5. Verification

- **Test suite:** 934 passed, 0 failed (baseline 934). `automation/`: 41 passed, 0 failed (baseline 37).
- **`automation/check_release_integrity.py`:** exit `0`.
- **Live verification:** the re-entry failure was reproduced and then cleared in a scratch git repository holding a spec and results artifact under `docs/archive/` alone — exit `2` against the pre-change module, exit `0` against the post-change module, in both working-tree and `--tree` mode. The archive step itself gets its first live exercise on this branch's own close-out.
- **Daemon restart:** `n/a` — `chore/*` carries none (`docs/DEVELOPMENT_STANDARDS.md` §2.6).

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| — | The sets already sitting `Shipped` in `docs/dev/` — six design, seven spec, four results artifacts — are not archived by this work | Out of scope by §1: the step archives the closing branch's own set. Whether the existing backlog is swept, and by what, is a separate decision for Ray |
