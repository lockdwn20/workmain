# Caliper reads HEAD from a temporary worktree, and every statement of where results live names the folder — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261110
**Branch:** `chore/issue-270-caliper-worktree-results-path`
**Target release:** n/a — `chore/*`, `docs/standards/2-git.md` §2.2
**Originating item:** Issue #270
**Design study:** `n/a` — direct path, no recon was run

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261110 | Ray | Branch type `chore/*`, direct path. | n/a |
| 20261110 | Ray | Direction on the issue: a spec review reads `HEAD` from a temporary detached worktree and removes it at the end, the clean-tree refusal goes, and every statement of where results live names the folder exactly. | n/a |
| 20261110 | Spanner | The census (§1) finds the ambiguous results wording in four places the issue does not name: `.claude/skills/session-start/references/spanner.md` read 4 ("beside it"), `.claude/skills/closeout/SKILL.md` P5 ("beside the spec `P4` resolved"), and two docstrings in `automation/`. Ray's direction covers every statement, so all are in scope. | n/a |
| 20261110 | Spanner | `.claude/skills/session-start/SKILL.md` § `/session-start` says the run "writes no file". A worktree is files on disk and an entry in `.git/worktrees/`, so that sentence would contradict read 1. It is amended to name the worktree as the one exception. | Superseded by Ray's ruling below, 20261110. |
| 20261110 | Ray | Non-blocking: § Post-implementation review check I6 runs `automation/architecture_check.py` and `automation/style_check.py` "on `<branch>`", but both read the working tree, so uncommitted work can produce findings that aren't on the branch. Verified: both set `ROOT = Path(__file__).resolve().parent.parent`, and `style_check.py`'s module docstring says "Uncommitted and untracked files count as changed". | Accepted. I6 runs its commands in a temporary detached worktree of `<branch>`, created and removed as read 1's is (step 1). § 1 Out of scope is corrected. |
| 20261110 | Spanner | Boundary check on that change: in a detached worktree, `style_check.py` `main` gets `HEAD` from `git rev-parse --abbrev-ref HEAD`, and `base_branch` then returns `main`, which is wrong for a `feature/*` branch. I6 therefore passes `--base <parent>`, with `<parent>` as read 4 names it. `architecture_check.py` reads no branch or base: its only argument is `--check-issues`. | n/a |
| 20261110 | Ray | No exceptions in `.claude/skills/session-start/SKILL.md`. The § `/session-start` sentences that make the run read-only are replaced with: "The session-open run assembles the state a role needs before it acts, from the sources that role's reference names, in the order named. It creates no branch or commit and edits no tracked file. Anything else it does is stated in that role's reference." This replaces the Caliper exception, and it also covers `.claude/skills/session-start/references/spanner.md` § Emits' label edit (`gh issue edit <N> --add-label`), which the old sentence "makes no GitHub change" contradicted. | Step 1 carries it. |
| 20261110 | Spanner | The frontmatter `description` of `.claude/skills/session-start/SKILL.md` ends "Read-only.", another statement of the rule Ray replaced. Under `docs/standards/1-workflow.md` §1.2 a revision changes every statement of what it changes, so step 1 deletes those two words. | n/a |

---

## 1. Scope

**In scope:**

- `.claude/skills/session-start/references/caliper.md`: read 1, the pass-row sentence and the `Not reviewed:` paragraph of § Emits, post-implementation read 2, and post-implementation check I6.
- `.claude/skills/session-start/SKILL.md`: the § `/session-start` paragraph stating what the run does, and the frontmatter `description`'s "Read-only.".
- `.claude/skills/session-start/references/spanner.md`: read 4's results directory.
- `docs/standards/1-workflow.md` §1.1: the Implementation row of "What shows each stage done".
- `.claude/skills/closeout/SKILL.md`: P5's wording.
- `automation/closeout_acs.py` `derive_results_path` and `automation/closeout_acs_test.py` `test_ac2_3_results_root_follows_the_spec_root`: docstrings only.

Census of where results live, by `grep -rn 'beside' CLAUDE.md docs/standards .claude docs/dev docs/ARCHITECTURE.md automation .github .githooks` at `b0144f6`: the six sites above. `automation/architecture_check.py:311` and `:330` also match, and both are about Python modules, not results. Census of the clean-tree rule, by `grep -rnE 'clean (working )?tree|porcelain|not clean|worktree'` over the same paths: `caliper.md` lines 11 and 32, and `anvil.md` lines 9 and 31. Census of commands Caliper runs against the working tree, by reading `caliper.md` end to end: spec-review read 6 (`automation/architecture_check.py`, covered by read 1's worktree) and post-implementation check I6.

**Out of scope:**

- `.claude/skills/session-start/references/anvil.md`'s clean-tree check. Anvil writes to the tree, so it needs a clean one. The issue is about Caliper only.
- § Post-implementation review's reads 1 to 4. They already read from `<branch>` with `git show`, `git grep <branch>` and `git diff`, and never read the working tree. Only the commands check I6 runs read the working tree, and I6 is in scope.
- `.claude/skills/closeout/SKILL.md` line 41, which already says "the `results/` directory of the spec's own root".

## 3. Design rules

- **DR1 — A spec review reads one commit, and it is `HEAD`.** Read 1 creates the worktree from `HEAD`. Every later read and command uses it. The pass row's `<commit>` is that worktree's `HEAD`.
- **DR2 — The worktree is created at a fresh path from `mktemp -d`.** Two Caliper sessions can run at the same time, so a fixed sibling path like `../workmain-caliper` could collide. `git worktree add` accepts an existing empty directory.
- **DR3 — The worktree is removed with `--force` before § Emits.** Caliper writes nothing, so whatever is in the worktree came from running a read's command (for example `__pycache__/` from `automation/architecture_check.py`). Nothing in it is worth keeping, so `--force` makes sure the removal succeeds. The emitted text comes from the reads, so the worktree isn't needed after read 7.
- **DR4 — The results directory is named one way everywhere:** "the `results/` directory of the spec's own root (`docs/dev/` or `docs/archive/`)". Closeout's P4 already searches those two roots, and `docs/standards/1-workflow.md` §1.5 makes `docs/archive/<type>/` mirror `docs/dev/<type>/`.
- **DR5 — The post-implementation review's commands run on `<branch>`, not on the working tree.** Check I6 runs in a temporary detached worktree of `<branch>`, created as DR2 states and removed as DR3 states. `style_check.py` is given its base explicitly, because in a detached worktree it can't read the branch name.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Caliper's spec review reads `HEAD` from a temporary worktree, and check I6 runs in one of `<branch>`. The clean-tree refusal is gone. | `.claude/skills/session-start/references/caliper.md`, `.claude/skills/session-start/SKILL.md` |
| 2 | Every statement of where results live names the folder | `docs/standards/1-workflow.md`, `.claude/skills/session-start/references/caliper.md`, `.claude/skills/session-start/references/spanner.md`, `.claude/skills/closeout/SKILL.md`, `automation/closeout_acs.py`, `automation/closeout_acs_test.py` |
| 3 | Results artifact | `docs/dev/results/CALIPER_WORKTREE_AND_RESULTS_PATH_RESULTS.md` |

### Step 1 — `fix(skills): Caliper reads HEAD from a temporary worktree`

`.claude/skills/session-start/references/caliper.md` read 1. Replace:

> 1. The spec at the target path, end to end, read with a clean working tree. Where `git status --porcelain` prints anything, the run reviews nothing (§ Emits). A clean tree makes this read, and every read of a repository file below, one of the commit at `HEAD`.

with:

> 1. The spec at the target path, end to end, read from a temporary detached worktree of `HEAD`, created with `git worktree add --detach "$(mktemp -d)" HEAD`. Every read of a repository file below is made in that worktree, and every command below is run with it as the working directory, so the review reads the commit at `HEAD` whatever the working tree holds. Once read 7 is done, and before § Emits, the run removes the worktree with `git worktree remove --force <worktree path>`.

`caliper.md` § Emits, pass-row sentence. Replace:

> `<commit>` is `git rev-parse --short HEAD`, the commit the spec and every repository file were read at.

with:

> `<commit>` is `git rev-parse --short HEAD`, run in read 1's worktree: the commit the spec and every repository file were read at.

`caliper.md` § Emits, the paragraph that begins "A run that reviews nothing". Replace:

> A run that reviews nothing, because `HEAD` holds no spec at the target path (§ Choosing the review) or the working tree is not clean (read 1), emits no table and no row to record. It emits one line, `Not reviewed:` and the reason, followed by each path `git status --porcelain` lists where the tree is not clean. No other commentary.

with:

> A run that reviews nothing, because `HEAD` holds no spec at the target path (§ Choosing the review), emits no table and no row to record. It emits one line, `Not reviewed:` and the reason. No other commentary.

`.claude/skills/session-start/SKILL.md` § `/session-start`. Replace:

> The session-open run **reads**. It writes no file, creates no branch or commit, and makes no GitHub change. It assembles the state a role needs before it acts, from the sources that role's reference names, in the order named.

with:

> The session-open run assembles the state a role needs before it acts, from the sources that role's reference names, in the order named. It creates no branch or commit and edits no tracked file. Anything else it does is stated in that role's reference.

`.claude/skills/session-start/SKILL.md` frontmatter `description`. Replace:

> emitting the state that role needs before it acts. Read-only.

with:

> emitting the state that role needs before it acts.

`caliper.md` § Post-implementation review, check I6. Replace:

> - **I6** — A new finding from `automation/architecture_check.py` or a violation from `automation/style_check.py`, each run on `<branch>`.

with:

> - **I6** — A new finding from `automation/architecture_check.py`, or a violation from `automation/style_check.py --base <parent>`, with `<parent>` as read 4 names it. Both are run with a temporary detached worktree of `<branch>` as the working directory, created with `git worktree add --detach "$(mktemp -d)" <branch>` and removed with `git worktree remove --force <worktree path>` once both have run. Both scripts read the tree they are run from, so a run in the main working tree would check uncommitted work as well as the branch. `style_check.py` is given `--base` because in a detached worktree it can't read the branch name, and it would fall back to `main`.

### Step 2 — `docs(standards): name the results folder exactly`

`docs/standards/1-workflow.md` §1.1, Implementation row. Replace:

> A results artifact in the `results/` directory beside the spec names it in its `**Spec:**` field.

with:

> A results artifact in the `results/` directory of the spec's own root (`docs/dev/` or `docs/archive/`) names it in its `**Spec:**` field.

`.claude/skills/session-start/references/caliper.md` § Post-implementation review, read 2. Replace:

> where `<results dir>` is the `results/` directory beside the spec.

with:

> where `<results dir>` is the `results/` directory of the spec's own root (`docs/dev/` or `docs/archive/`).

`.claude/skills/session-start/references/spanner.md` read 4. Replace:

> over the `results/` directory beside it,

with:

> over the `results/` directory of its own root (`docs/dev/` or `docs/archive/`),

`.claude/skills/closeout/SKILL.md` P5. Replace:

> The results artifact exists beside the spec `P4` resolved — the `results/` directory of that spec's own root — and its

with:

> The results artifact exists in the `results/` directory of the root holding the spec `P4` resolved (`docs/dev/` or `docs/archive/`), and its

`automation/closeout_acs.py` `derive_results_path` docstring. Replace:

```python
    """Strip the spec suffix, append `_RESULTS.md`, and look for it in the results
    directory beside the spec's own root — a set is archived whole, so its spec
```

with:

```python
    """Strip the spec suffix, append `_RESULTS.md`, and look for it in the `results/`
    directory of the spec's own root — a set is archived whole, so its spec
```

`automation/closeout_acs_test.py` `test_ac2_3_results_root_follows_the_spec_root` docstring. Replace:

```python
    """DR6 — a set is archived whole, so the results artifact is looked for beside
    the spec rather than at a fixed docs/dev/ constant."""
```

with:

```python
    """DR6 — a set is archived whole, so the results artifact is looked for in the
    results/ directory of the spec's own root, not at a fixed docs/dev/ constant."""
```

### Step 3 — `docs(results): issue #270 results artifact`

Written from `docs/dev/results/_TEMPLATE_RESULTS.md`, with `**Released as:** n/a`.

### Authorization points

None. Nothing here migrates, deletes a GitHub object, merges to `main`, force-pushes or touches a service. The temporary worktree is local and removed by the run that creates it.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | A Caliper spec review runs with uncommitted work in the tree. It reads `HEAD` and leaves no worktree behind. | Ray opens `/session-start Caliper docs/dev/specs/CALIPER_WORKTREE_AND_RESULTS_PATH_SPEC.md` on this branch with an untracked file in the tree. The run emits a pass row naming this branch's `HEAD`, and afterwards `git worktree list` shows only the main worktree. |
| AC1.2 | Nothing in the Caliper reference makes a spec review depend on the working tree's state | `grep -n -e porcelain -e clean .claude/skills/session-start/references/caliper.md` prints nothing |
| AC1.3 | The post-implementation review's check I6 checks `<branch>`, not the working tree, and leaves no worktree behind. This criterion comes from Ray's ruling, not the issue; the issue body gains it at close-out (`docs/standards/1-workflow.md` §1.2). | During the AC2.1 run, Ray leaves an untracked `automation/_i6_probe.py` in the tree containing a line `ruff` rejects. I6 reports no violation for that file, and afterwards `git worktree list` shows only the main worktree. |
| AC2.1 | The post-implementation review finds a results artifact in `docs/dev/results/` and selects § Post-implementation review | Ray runs a Caliper post-implementation review of this spec after step 3, when its results artifact is in `docs/dev/results/`. The run emits `Caliper (post-implementation)` rows. |
| AC2.2 | Every statement of where results live names the folder | `grep -rnw 'beside' .claude docs/standards automation/closeout_acs.py automation/closeout_acs_test.py` prints nothing. The issue's check, `grep -rn 'beside the spec'`, cannot see spanner.md's "beside it", so this check replaces it (`docs/standards/1-workflow.md` §1.2); the issue body is edited to match at close-out. |
| AC2.3 | The docstring edits change no behaviour of the close-out tooling | `pytest automation/` passes, 101 passed, 0 failed, 0 skipped |

## 6. Test plan

- **Baseline before this work:** `pytest automation/` at `b0144f6`: 101 passed, 0 failed, 0 skipped.
- **Expected after:** 101 passed, 0 failed, 0 skipped. The steps only change docstrings, and no test is added.

## 7. Risks and rollback

- If a session dies between creating a worktree (read 1, or check I6) and removing it, the worktree is left behind. `git worktree list` shows it, and `git worktree remove --force <path>` clears it. AC1.1's check is what catches it.
- Each step is one commit and is reverted with `git revert`.
