# Baseline Harness Commit — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261009
**Branch:** `chore/issue-182-commit-baseline-harness`
**Target release:** n/a — `chore/*`, `docs/DEVELOPMENT_STANDARDS.md` §2.2
**Originating item:** Issue #182, parent of #148, #149, #155
**Design study:** n/a — direct path, no recon was run

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261009 | Ray | #182 became a parent of #148, #149 and #155, but it still carries acceptance criteria of its own. Its only work outside its children is committing the baseline harness. That commit goes on its own `chore/*` branch now, and #182 stays open until its children close. | This spec. |
| 20261009 | Spanner | Issue AC1 (`subIssuesSummary` shows 3 of 3 completed) is met by the three children's own branches, not this one. This spec maps only issue AC2. `/closeout` for this branch still composes #182's closing comment. Ray does not post it or close #182 until AC1 is met, and a later close-out of #182 checks AC1 then. | §5 maps AC2 only. |
| 20261009 | Spanner | `chore/*` covers this branch under §2.2. `.gitignore` is in the `chore/*` block. `scripts/**` falls under the block's exception, which requires a mechanical proof of behaviour-neutrality stated in the spec. The proof (DR2): the branch adds files under `scripts/baseline/` and touches no existing file except `.gitignore`, and no tracked file outside `scripts/baseline/` refers to the added scripts. These are new files, so there is nothing to compare by AST equality. | AC2.3. |
| 20261009 | Spanner | #182's design study (`DESIGN_PROVIDER_COST_RESPONSE_CHECKS.md`) covers none of the harness, so under §1.3's split rule it is not narrowed into this spec. Its findings move to the children. It is deleted when the children's studies exist, which is outside this branch. | Out of scope. |

---

## 1. Scope

**In scope:**

- `scripts/baseline/README.md`, `scripts/baseline/capture_baseline_prompts.py`, `scripts/baseline/run_baseline.py` and `scripts/baseline/variants/example_skeleton.json`, committed exactly as they stand in the working tree.
- The `staging/baseline/*` line in `.gitignore`, as it stands in the working tree.

**Out of scope:**

- Any edit to the harness files: the README's install section, its claim that `staging/` already covers the run output, the copied `_format_output`, the SDK clients, tests. #188 owns all of it and lifts the restrictions in its body.
- Running the harness. #188's body restricts that to Ray.
- Citing the harness from any document. #188's body forbids it.
- The work of #148, #149 and #155. Each child has its own branch.
- #182's design study and the parked branch that holds it (Decision Log).

## 3. Design rules

- **DR1 —** The harness files and the `.gitignore` line are committed byte for byte as they stand. Any fault found in them goes to #188, not into this branch.
- **DR2 —** The branch changes no application behaviour. It adds files only under `scripts/baseline/`, touches no existing file except `.gitignore`, and nothing outside `scripts/baseline/` imports or calls the added scripts.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Stage only the five paths named here, then commit `chore(scripts): commit the provider baseline harness for reference, issue #182`. The body says the files are committed as they stand, and that #188's body states the restrictions on them. | `scripts/baseline/README.md`, `scripts/baseline/capture_baseline_prompts.py`, `scripts/baseline/run_baseline.py`, `scripts/baseline/variants/example_skeleton.json`, `.gitignore` |
| 2 | Write the results artifact from `docs/dev/results/_TEMPLATE_RESULTS.md`. Its §3 table carries this spec's §5 ACs with each check's output. Commit `docs(results): record the baseline harness commit results, issue #182`. | `docs/dev/results/BASELINE_HARNESS_COMMIT_RESULTS.md` |

The `.gitignore` change being committed:

```diff
 staging/notes/*
+staging/baseline/*
 !staging/reports/.gitkeep
```

### Authorization points

None. A `chore/*` branch's only authorization point is the merge to `main`, which belongs to `/closeout`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC2.1 | The baseline harness is tracked in the repository, all four files of it | `git ls-files scripts/baseline` lists exactly `scripts/baseline/README.md`, `scripts/baseline/capture_baseline_prompts.py`, `scripts/baseline/run_baseline.py` and `scripts/baseline/variants/example_skeleton.json` |
| AC2.2 | Harness run output under `staging/baseline/`, which holds client work content, can't be committed by accident | `git check-ignore -q staging/baseline/runs/x/summary.md && git check-ignore -q staging/baseline/fixtures/x/manifest.json` exits 0 |
| AC2.3 | The branch changes no application behaviour (DR2, the `chore/*` exception proof in §2.2) | `git diff --name-status origin/main...HEAD` lists `A` only under `scripts/baseline/` and `docs/dev/`, and `M` only on `.gitignore`. `git grep -nE 'capture_baseline_prompts\|run_baseline\|scripts\.baseline\|scripts/baseline' -- . ':!scripts/baseline' ':!docs/dev/specs/BASELINE_HARNESS_COMMIT_SPEC.md' ':!docs/dev/results/BASELINE_HARNESS_COMMIT_RESULTS.md'` returns zero hits |
| AC2.4 | The harness is committed as it stood, with no edits (DR1) | `git diff --quiet HEAD -- scripts/baseline .gitignore` exits 0 after Step 1, and `git log --format=%s origin/main..HEAD -- scripts/baseline .gitignore` shows only the Step 1 commit |

## 6. Test plan

Omitted. The change touches no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` (`docs/dev/specs/_TEMPLATE_SPEC.md`, direct path). `pyproject.toml` sets `testpaths = ["tests"]`, so pytest does not collect `scripts/baseline/`. Close-out runs the suites regardless.

## 7. Risks and rollback

- **Run output committed by mistake.** AC2.2 covers it. Step 1 stages paths by name, never with `-A` or `-am`.
- **Rollback:** `git revert` of the Step 1 commit. The files stay on Ray's machine either way, since the run output under `staging/baseline/` is ignored and untracked.
