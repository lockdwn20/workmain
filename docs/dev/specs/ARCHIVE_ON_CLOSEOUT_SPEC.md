# Archive on close-out — Spec

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20260831
**Branch:** `chore/issue-112-archive-on-closeout`
**Target release:** n/a — `chore/*` carries no version bump, tag or Release (`docs/DEVELOPMENT_STANDARDS.md` §2.2)
**Originating item:** Issue #112
**Design study:** `n/a` — direct path, no recon was run

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260831 | Spanner | Proposed that a shipped artifact set stays in `docs/dev/` until nothing outside it cites it, on the reading that §1.5's "no longer a live reference" is a second condition beyond completion. | **Not taken.** The measurement behind it was wrong: every citation into `docs/dev/` from a standing document (`CLAUDE.md`, `docs/DEVELOPMENT_STANDARDS.md`, `.claude/skills/closeout/`) is to the *directory*, never to a spec file. The counts were spec↔results pairs inside `docs/dev/` that move with the set. |
| 20260831 | Ray | A spec set to `Shipped` has no business being citable — citing spec references from production documents is the pattern that causes trouble. | Accepted, and it collapses the trigger: completion *is* the archive condition. §1.5's "and no longer a live reference" clause is struck, since it is what made the two conditions look separate. |
| 20260831 | Ray | The archive step is step 2 in `chore` and `feature`, step 3 in `hotfix`; every later step moves down one. | Accepted. In all three variants that position is the same one — on the branch, immediately after the `Status: Shipped` commit and before any merge — correctly translated for `hotfix`, whose version bump occupies step 1. |
| 20260831 | Spanner | `automation/closeout_acs.py` hard-codes `docs/dev/specs` and `docs/dev/results`, so once a set is archived a `--branch` re-run reads `git ls-tree <merge>^2:docs/dev/specs/` and finds nothing — `P4`, `P5`, `P5a` and `P6` all fail before § Resume point can observe the close-out is complete. Scope not named by issue #112. | Ray: rides #112. Without it the issue would close having reintroduced the re-entry defect #91 was raised to fix. |
| 20260831 | Ray | After sweeping the shipped backlog into `docs/archive/`, asked whether the existing archived files can be left as they are, with the repointing applied only from here on. | Yes. `--branch` re-runs read every file from `<merge>^2`, where those paths were correct, so nothing mechanical breaks; only a working-tree read of an old artifact dangles, and filenames never change. The existing archive is left alone. |
| 20260831 | Ray | Proposed writing citations relative — `../design/<file>.md` — instead of repointing them on the move. | Adopted, and it replaces DR4 rather than refining it. `docs/archive/<type>/` mirrors `docs/dev/<type>/` and a set moves whole, so a relative intra-set pointer is invariant under the move: the archive step becomes a pure rename with nothing to repoint, and `P5a` resolves relative to the spec instead of searching two roots. Non-set citations stay repo-root, which makes the form itself the difference between a pointer and a record — the distinction the repointing rule would otherwise have had to judge case by case. |
| 20260831 | Ray | Asked to confirm the script must search the archive for re-entry to work. | Confirmed by probe: a set resolvable only from `docs/archive/` fails the current script with `no spec names branch <name>`, exit 2 — `P4`, `P5`, `P5a` and `P6` all abort before § Resume point runs. Added DR5a: resolution finds the set in either root and forms no opinion about which is correct. |
| 20260831 | Ray | Asked whether the archive step ends with a commit of its own, as step 1 does. | Yes, and the step's `Done when` was tightened to require it — as first written it observed the working tree, which a staged-but-uncommitted `git mv` would have satisfied. The move and the citation repointing commit together; see §4 Step 4. |
| 20260831 | Ray | `automation/closeout_acs.py`'s module docstring cited `docs/dev/specs/CLOSEOUT_PERFORMS_SPEC.md` §4.4 as the source of the module's behaviour. | Ray corrected it directly in the working tree; the edit is carried onto this branch as part of step 2. A second instance at line 151 citing the archived `CYCLE_CLOSEOUT_SPEC.md` is fixed by the same step. |

---

## 1. Scope

**In scope:**

- `docs/DEVELOPMENT_STANDARDS.md` §1.5 — the `docs/archive/` bullet: the folder names it gets wrong, and the trigger clause that made completion and citability read as two conditions.
- `docs/archive/README.md` — a second home for §1.5's rule, citing a `CLAUDE.md` section that no longer exists.
- `automation/closeout_acs.py` and `automation/closeout_acs_test.py` — spec and results lookup across both roots, and the two spec-file citations in its docstrings.
- `.claude/skills/closeout/SKILL.md` — `P4`, `P5`, `P5a`.
- `.claude/skills/closeout/references/{chore,feature,hotfix}.md` — the new archive step and the renumbering it forces.
- `docs/DEVELOPMENT_STANDARDS.md` §1.5 — the citation-form rule that makes the move a pure rename, and the three `docs/dev/*/_TEMPLATE_*.md` header fields that carry it.

**Out of scope:**

- Archiving anything other than the closing branch's own artifact set. A sweep of `docs/dev/` for other eligible sets is a different mechanism with a different trigger, and nothing in issue #112 asks for one.
- `docs/archive/`'s existing `handoffs/` and `hotfixes/` subdirectories. They are pre-migration, and no artifact this skill moves is ever routed to them.
- The `_TEMPLATE_*.md` files. The step moves a named set, never a directory, so no template is reachable by it and no exclusion rule is needed.
- Rewriting the citations already in `docs/archive/`. They are repo-root paths written before the citation-form rule existed; nothing mechanical reads them, and `--branch` re-runs resolve from `<merge>^2` where those paths were correct.
- `docs/DEVELOPMENT_STANDARDS.md` §7's placement table. It states where dev artifacts are *written*, which this change does not alter.

## 2. Verified current state

Omitted — direct path (`docs/DEVELOPMENT_STANDARDS.md` §1.2). Each step below quotes the text it replaces.

## 3. Design rules

- **DR1 — The unit is the set, never the directory.** The step moves exactly the three files close-out has already resolved by name: the spec from `P4`, the results artifact from `P5`, and the design artifact from `P5a` where the spec names one. It never lists a directory and never moves a file it did not resolve.
- **DR2 — `docs/archive/<type>/` mirrors `docs/dev/<type>/`.** `design/` → `design/`, `specs/` → `specs/`, `results/` → `results/`. A hotfix spec archives to `docs/archive/specs/`, not to `docs/archive/hotfixes/`.
- **DR3 — Filenames never change.** §1.5 already requires it. The basename that arrives in the archive is the basename that left `docs/dev/`, so a citation that carries only the filename stays resolvable without an edit.
- **DR4 — A pointer between artifacts of the same set is relative, so the move repoints nothing.** `../design/<file>.md` from a spec, `../specs/<file>_SPEC.md` from a results artifact. `docs/archive/<type>/` mirrors `docs/dev/<type>/` (DR2) and the set moves whole (DR6), so a relative pointer resolves identically on both sides of the move and the archive step is a pure rename.
  - Every other citation stays a repo-root path — a standards section, an artifact from a different set, and any path inside a `git show <ref>:<path>` or quoted command output. Those are either targets that do not move or records of where something was at a stated moment, and rewriting a record makes it false.
  - Artifacts written before this rule keep their repo-root pointers. The existing `docs/archive/` is not rewritten.
- **DR5 — Lookup is dev-first, then archive.** Both `automation/closeout_acs.py` and preflight resolve an artifact by searching `docs/dev/<type>/` and then `docs/archive/<type>/`. A spec found in both roots is a half-finished move and is reported as the existing "more than one spec names branch" failure.
- **DR5a — Resolution is location-agnostic; it never judges location.** Finding a set in `docs/archive/` is a normal result, not a finding. A script that treated the archive root as wrong would fail the preflight of every close-out that had already completed its archive step — the re-entry defect this rule exists to prevent, relocated one layer down. Whether the move has happened is the archive step's own `Done when`, checked once, when that step runs.
- **DR6 — The results artifact is looked for in the same root its spec was found in.** A set moves as a unit, so spec and results are always co-located; deriving the results root from the spec's own path keeps that an invariant rather than a second search.
- **DR7 — No production file cites a spec, design or results artifact as the source of its behaviour.** The rule it implements is stated where it is implemented, or cited from `docs/DEVELOPMENT_STANDARDS.md`.

Anything this spec does not cover: `CLAUDE.md` Role 3 escalation — stop at the step, surface to Ray, do not self-resolve.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | §1.5's archive bullet names `docs/dev/design/`, `docs/dev/specs/` and `docs/dev/results/`, and its trigger reads completion alone. `docs/archive/README.md` reduces to a pointer at §1.5. | `docs/DEVELOPMENT_STANDARDS.md`, `docs/archive/README.md` |
| 2 | `closeout_acs.py` resolves a spec dev-first then archive, derives the results path from the spec's own root, and carries no spec-file citation in its docstrings. Tests cover both roots. | `automation/closeout_acs.py`, `automation/closeout_acs_test.py` |
| 3 | `P4`, `P5` and `P5a` state the two-root lookup. | `.claude/skills/closeout/SKILL.md` |
| 4 | The archive step exists in all three variants at Ray's placement, with every later step renumbered. | `.claude/skills/closeout/references/{chore,feature,hotfix}.md` |
| 5 | §1.5 states the citation-form rule; the three templates carry it in their header fields; the archive step and `P5a` are rewritten against it. | `docs/DEVELOPMENT_STANDARDS.md`, `docs/dev/*/_TEMPLATE_*.md`, `.claude/skills/closeout/SKILL.md`, `.claude/skills/closeout/references/{chore,feature,hotfix}.md` |

### Step 1 — the standard

`docs/DEVELOPMENT_STANDARDS.md:104` reads:

> - **`docs/archive/`** holds artifacts whose work is complete. Move an artifact there once it is finished and no longer a live reference — it is kept for reference only, is never authoritative, and is always superseded by the current `design/`, `specs/`,  and `results/`. It is git-tracked, so citations to it stay resolvable.

becomes:

> - **`docs/archive/`** holds artifacts whose work is complete. An artifact moves there when its issue closes out — `/closeout` performs the move as a step — and `docs/archive/<type>/` mirrors `docs/dev/<type>/`. It is kept for reference only, is never authoritative, and is always superseded by `docs/dev/design/`, `docs/dev/specs/` and `docs/dev/results/`. It is git-tracked, and filenames never change on the move, so citations to it stay resolvable.

`docs/archive/README.md`, whole file, becomes:

> # `docs/archive/`
>
> Artifacts whose work is complete. `docs/DEVELOPMENT_STANDARDS.md` §1.5 owns what that means, when an artifact arrives here, and why nothing here may be cited as the basis for a current decision.

### Step 2 — the AC guard

`automation/closeout_acs.py:44-45` reads:

> ```python
> SPECS_DIR = Path("docs/dev/specs")
> RESULTS_DIR = Path("docs/dev/results")
> ```

becomes an ordered pair of roots, dev first (DR5), with the results directory derived per lookup from the spec's own root (DR6) rather than held as a constant.

`automation/closeout_acs.py:151` reads:

> cell that quotes a pipe-bearing command or regex (the `CYCLE_CLOSEOUT_SPEC.md`
> F12 lesson)."""

The citation is to an artifact already in `docs/archive/specs/`, which §1.5 forbids relying on. The parenthetical is dropped; the sentence before it already states the rule (DR7).

Ray's working-tree correction to the module docstring is committed as part of this step.

### Step 4 — the archive step

Inserted at step 2 of `chore.md`, step 2 of `feature.md` and step 3 of `hotfix.md` — in each case immediately after the step that commits `**Status:** Shipped`, and before any merge. Every later step in that file moves down one.

| # | Step | Done when |
| --- | --- | --- |
| n | `git mv` this branch's artifact set — the spec from `P4`, the results artifact from `P5`, and the design artifact from `P5a` where the spec names one — from `docs/dev/<type>/` to `docs/archive/<type>/`. Commit on the branch, in a commit of its own, before any merge. Nothing is repointed (DR4) — `docs/DEVELOPMENT_STANDARDS.md` §1.5, §2.2 | The branch tip carries each of the set under `docs/archive/<type>/` and none of it under `docs/dev/<type>/`, `git status --porcelain` is empty, and the commit is a pure rename |

**The step's own commit.** The move is committed separately from the `Status: Shipped` commit that precedes it — a reason the general "a step ends with a commit" rule (`docs/DEVELOPMENT_STANDARDS.md` §1.4) does not cover on its own: the move is the first thing in this sequence that touches paths rather than content. Folding it into the `Shipped` commit would mix a rename set with a status edit, and the first live run is exactly where that wants to be revertible on its own.

The commit's subject names the action and the issue, so the archive is legible in `git log` without reading the diff — `docs(closeout): archive the issue #<N> artifact set`. `git mv` records the moves as renames, and because DR4 leaves nothing to repoint the commit carries no content change at all — which is what its **Done when** checks.

### Authorization points

**None.** This spec adds no authorization point and removes none. The one its close-out crosses is the merge to `main` that every close-out crosses (`docs/DEVELOPMENT_STANDARDS.md` §1.4) — a property of that action, not of this change.

## 5. Acceptance criteria

Sub-ACs map to issue #112's two ACs: `AC1.m` to its first, `AC2.m` to its second.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | §1.5's archive bullet names the three `docs/dev/` paths and no bare `design/`, `specs/`, `results/` | `grep -n 'docs/archive/' docs/DEVELOPMENT_STANDARDS.md` shows all three `docs/dev/` paths in the bullet |
| AC1.2 | The bullet's trigger is completion alone — the "no longer a live reference" clause is gone | `grep -c 'no longer a live reference' docs/DEVELOPMENT_STANDARDS.md` returns `0` |
| AC1.3 | `docs/archive/README.md` states no rule of its own and cites no section that does not exist | `grep -n 'Documentation Standards' docs/archive/README.md` returns nothing; the file is a pointer at §1.5 |
| AC2.1 | All three variant references carry the archive step at Ray's placement, and each states that it commits on the branch before any merge | `grep -n 'docs/archive' .claude/skills/closeout/references/*.md` returns a step row in each of the three files, and each row's `Done when` names the branch tip |
| AC2.2 | Each variant's steps are numbered `1..n` with no gap or repeat after the insertion | `grep -oE '^\| [0-9]+ \|' .claude/skills/closeout/references/<f>.md` is consecutive from 1 in each file |
| AC2.3 | `closeout_acs.py` resolves a spec whose set has already been archived | `python3 -m pytest automation/closeout_acs_test.py` — a new test placing spec and results under `docs/archive/` exits `0` |
| AC2.4 | A spec present in both roots is reported, not silently resolved | new test asserts the "more than one spec names branch" error |
| AC2.5 | No file under `automation/` cites a spec, design or results artifact by filename | `grep -rnE '_(SPEC|RESULTS)(_v[0-9_]+)?\.md\|RECON_[A-Z_]+\.md' automation/*.py` returns nothing outside fixture filenames |
| AC2.6 | `P4` states the two-root lookup, and `P5` and `P5a` state that they follow from the spec rather than searching | Ray reads `.claude/skills/closeout/SKILL.md` — semantic, per `docs/DEVELOPMENT_STANDARDS.md` §1.2 |
| AC2.7 | Both suites stay green | `pytest` and `pytest automation/` |
| AC2.8 | §1.5 states the citation-form rule, and all three templates carry a relative intra-set pointer | `grep -n '\.\./design/\|\.\./specs/' docs/dev/specs/_TEMPLATE_SPEC.md docs/dev/results/_TEMPLATE_RESULTS.md docs/dev/design/_TEMPLATE_DESIGN.md` returns a hit in each, and `docs/DEVELOPMENT_STANDARDS.md` §1.5 carries the rule |
| AC2.9 | The archive step repoints nothing, in all three variants | `grep -c 'Nothing is repointed' .claude/skills/closeout/references/{chore,feature,hotfix}.md` returns `1` each |

## 6. Test plan

- **Baseline before this work:** 934 passed (main suite), 37 passed (`automation/`) — both measured on `dev` at `8234c2a`.
- **Expected after:** 934 passed unchanged, and `automation/` at 37 + 3.
- `automation/closeout_acs_test.py` gains: a spec and results resolved from `docs/archive/` alone (AC2.3); a spec present in both roots reported as a collision (AC2.4); the results path derived from the spec's own root rather than a fixed constant (DR6). The existing assertion at line 90 against the `RESULTS_DIR` constant is rewritten, not deleted.
- No file under `tests/` is touched, so the main suite is a regression check only.

## 7. Risks and rollback

- **The change is doc- and dev-tooling-only.** No file under `workmain/` is touched, so no application behaviour can regress and `docs/DEVELOPMENT_STANDARDS.md` §2.6 requires no restart.
- **Highest-blast-radius step is 2.** A wrong search order would make close-out resolve a stale archived spec in preference to a live one. Dev-first ordering (DR5) is what prevents it, and AC2.4 covers the case where both exist.
- **This branch archives its own set at its own close-out**, which is the first live exercise of the new step. If it fails there, the remedy is `git mv` back and a fix on a follow-up branch — the artifacts are git-tracked throughout and nothing is deleted.
- **Rollback** is per step: each is one commit against documents or dev tooling, revertible with `git revert` in any order.
