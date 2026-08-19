# Release-Check Relocation — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20260819
**Branch:** `chore/issue-87-release-check-relocation` (from `main`, merges to `main` and `dev`)
**Target release:** none — `chore/*` carries no version bump, no `CHANGELOG.md` entry, no tag, no Release
**Originating item:** Issue #87
**Design study:** `docs/dev/design/RECON_RELEASE_CHECK_RELOCATION.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260819 | Ray | This is a `chore/*` branch and only a `chore/*` branch. The script is not application code, the standards are being built, and the move into the correct location is allowed on that basis | Accepted. No behaviour-neutrality proof method, no split-commit structure, and no §2.2 exception argument appears in this spec. Recon F17 and Q1's proof framing are withdrawn — Ray had already settled the branch type before the recon was written and it should not have been reopened |
| 20260819 | Ray | Recon Q1 — if `find_repo_root` is the standard, the script is adjusted to meet it | Accepted. DR2, step 1 |
| 20260819 | Ray | Recon Q3 — the `.githooks/` reference sweep is in scope. Fix it | Accepted. DR4, steps 2 and 3 |
| 20260819 | Ray | Recon Q4 — the fail-open guard is in scope. Fix it | Accepted. DR3, step 2 |
| 20260819 | Spanner | Recon Q5 — `chore/issue-83-cycle-closeout` is parked by Ray's decision; #87 reaching into it would unpark it. `docs/archive/**` is never updated per `CLAUDE.md` | Both are out of scope, §1. The parked branch corrects its own citations when it unparks |
| 20260819 | Spanner | Recon Q6 — #87 adds no tests and `testpaths` stays `["tests"]` | No `pyproject.toml` change. AC4.1 is a captured before/after run, not a collected test |
| 20260819 | Caliper | AC5.1's grep matches this spec and its own recon, so it cannot pass on the branch that satisfies every other AC | Accepted. AC5.1 gains two `--exclude` flags and states why they are not a loophole |
| 20260819 | Caliper | AC2.2 directed a real push to `main` or a tag — if the fix under test is wrong, the push lands | Accepted. AC2.2 is now an offline hook invocation with crafted stdin. No network, no push |
| 20260819 | Caliper | AC4.1 and C17 pinned live release counts and the current version, which go stale | Accepted, and it is the standing rule that a live count never goes into a document. C17 no longer quotes them; AC4.1 is a before/after capture taken at implementation time |
| 20260819 | Caliper | AC1.2 could not distinguish `git mv` from delete-and-create, so it did not verify DR1's mechanism claim | Accepted. AC1.2 is dropped and DR1 is reworded to an instruction that no AC pretends to verify |
| 20260819 | Caliper | Four further findings — a shipped spec's evidence table, the §7 discriminator, a docstring on `find_repo_root`, and the §2.2 proof-method note | **Not taken**, withdrawn by Caliper on re-triage: all four hold this spec to standards still being written. The `find_repo_root` docstring specifically stays matched to `automation/issue_validator.py`, since consistency between the two modules beats retro-fitting §3.5 into one of them |
| 20260819 | Spanner | `automation/` is not a package — it has no `__init__.py`, and both modules are stdlib-only standalone scripts. Importing `find_repo_root` across them is not available | Each module carries its own copy, matching shape and message. A shared `automation/` helper is worth doing when a third module needs it, not before |

---

## 1. Scope

**In scope:**

- `scripts/check_release_integrity.py` → `automation/check_release_integrity.py`, with its repo-root anchor converged on the `automation/` pattern and its own usage docstring repointed.
- `.githooks/pre-push` — the two old-path references, the fail-open guard, and the missing standards citation.
- `.githooks/commit-msg` — the two lines carrying gate wording that issue #86 retired.
- `docs/dev/specs/ISSUE_CREATION_VALIDATION_SPEC.md` — two old-path citations in a live, shipped spec.

**Out of scope:**

- **`docs/archive/design/DESIGN_PLANNING_DOCS_STANDARDS_REVIEW.md:329`.** `CLAUDE.md` states the archive is never updated and must not be cited as the basis for a current decision.
- **`docs/dev/specs/CYCLE_CLOSEOUT_SPEC.md` and `docs/dev/design/RECON_CYCLE_CLOSEOUT.md`.** Both live only on `chore/issue-83-cycle-closeout`, which Ray parked on 20260819. Editing them requires unparking it. They carry their own correction when that branch resumes.
- **Tests for `check_release_integrity.py`.** It has none today (recon F16) and #87 states no test AC. Adding them is separate work.
- **`docs/DEVELOPMENT_STANDARDS.md`.** §7 already routes non-application dev tooling to `automation/`; this move brings the repository into line with a rule that needs no amendment.
- **`automation/issue_validator.py`.** DR2 converges the moved script onto that file's pattern; it is not itself changed.

## 2. Verified current state

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| C1 | `ROOT = Path(__file__).resolve().parent.parent`, with `CHANGELOG`, `VERSION_FILE` and `sh()`'s `cwd=ROOT` all derived from it — `scripts/check_release_integrity.py:37-39`, `:52` |
| C2 | The usage block names the old path three times — `scripts/check_release_integrity.py:20-22` |
| C3 | The script's failure idiom is a return code through `sys.exit(main())`; `main()` prints and returns an int. It defines no exception class — `scripts/check_release_integrity.py:72`, `:154-174` |
| C4 | `automation/issue_validator.py` anchors with `find_repo_root(Path(__file__))`, which walks `(current, *current.parents)` for a `.git` entry and raises `ValidationAbort` when none is found — `automation/issue_validator.py:304`, `def find_repo_root` |
| C5 | `automation/` contains no `__init__.py`; it holds `issue_validator.py`, `issue_validator_test.py`, and `fixtures/` — `ls automation/` |
| C6 | Nothing imports the script as a module; the hook is its only caller — repository-wide grep for `import check_release_integrity` returns no hits outside `.git/` |
| C7 | `.githooks/pre-push` names the old path in prose at `:5` and executably at `:27` as `checker="$repo_root/scripts/check_release_integrity.py"`, where `repo_root` is `git rev-parse --show-toplevel` |
| C8 | `.githooks/pre-push:29` is `[ -f "$checker" ] || exit 0` — a missing checker exits zero, printing nothing, and the push proceeds unverified |
| C9 | `.githooks/pre-push` cites no `DEVELOPMENT_STANDARDS.md` section anywhere, although §2.2 owns the CHANGELOG / tag / GitHub Release rule it enforces — full file read |
| C10 | `.githooks/commit-msg` cites §2.4 at `:8` and `:64`, and both citations are correct: §2.4 owns commit-message format and prohibits `--no-verify` |
| C11 | Gate wording in `.githooks/` is exactly two lines, both in `commit-msg`: `:58` `  Gate context belongs in the body, never the subject:` and `:62` `    Gate 3 of 7. Files changed, decisions made, expected test count.` `grep -rni gate .githooks/` returns those two lines and nothing else |
| C12 | §2.4 already carries the replacement wording: "Step context belongs in the body, not the subject — `feat(notes): converge write path` with `Step 3 of 7` in the body, never `Step 3: ...` as the subject" — `docs/DEVELOPMENT_STANDARDS.md` §2.4 |
| C13 | `core.hooksPath` is `.githooks` in this clone, so both hooks are live — `git config --get core.hooksPath` |
| C14 | Neither script carries the executable bit; the hook invokes `python3 "$checker"` at `:54`, so mode is irrelevant — `ls -l`, `.githooks/pre-push:54` |
| C15 | Live old-path citations outside the parked branch and the archive are `docs/dev/specs/ISSUE_CREATION_VALIDATION_SPEC.md:87` and `:102` — repository-wide grep |
| C16 | `pyproject.toml` is `[tool.pytest.ini_options]` / `testpaths = ["tests"]` and nothing else — no packaging table, no console-script entry point that could name either directory |
| C17 | The script runs clean from `scripts/` today: `python3 scripts/check_release_integrity.py --no-remote` exits `0` and prints an `OK — ...` line plus a pre-baseline count line. The literal counts are deliberately **not** quoted here — they move as releases are cut, and a document that pins them goes stale. AC4.1 compares a before-capture against an after-capture taken at implementation time instead |

## 3. Design rules

- **DR1 — use `git mv`.** It is the correct instruction and it keeps rename detection clean, but no AC claims to verify which mechanism was used, because `git log --follow` cannot tell them apart. Nothing outside the four files named in §1 is touched.
- **DR2 — the moved script anchors the way its new neighbour does.** `ROOT = find_repo_root(Path(__file__))`, with `find_repo_root` defined locally in the same shape as `automation/issue_validator.py`: walk `(current, *current.parents)` for a `.git` entry, return the first match. On no match, raise `SystemExit` with the same message text — the script defines no exception class (C3) and `SystemExit` is what its `sys.exit(main())` idiom already produces.
- **DR3 — the hook never fails open.** A missing checker is a failure with a message, not a silent `exit 0`. The relocation is exactly the event that would trip the current guard (C8), and C13 confirms the hook is live.
- **DR4 — a hook that enforces a standard cites the section that owns it.** `commit-msg` already does (C10); `pre-push` gains the same for §2.2.
- **DR5 — no version bump, no `CHANGELOG.md` entry, no tag, no Release.** `chore/*` per §2.2.
- **Not covered by this spec:** stop at the step and follow `CLAUDE.md` Role 3 — document it in chat and take it to Ray. No self-resolution, no scope adjustment.

## 4. Steps

Each step ends with a commit. There is no approval stop between steps.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `git mv` the script to `automation/`; replace the `.parent.parent` anchor with a local `find_repo_root` per DR2; repoint the three usage lines in its docstring | `automation/check_release_integrity.py` |
| 2 | `pre-push`: repoint the prose and `checker=` path; replace the fail-open guard per DR3; add the §2.2 citation per DR4 | `.githooks/pre-push` |
| 3 | `commit-msg`: replace both gate lines with §2.4's own wording (C12) | `.githooks/commit-msg` |
| 4 | Repoint the two live old-path citations | `docs/dev/specs/ISSUE_CREATION_VALIDATION_SPEC.md` |

**Verification run.** After step 2, run `python3 automation/check_release_integrity.py --no-remote` and record its output and exit code in the step 2 commit message, for comparison against C17.

### Authorization points

**This spec contains none.** No DB migration, no GitHub object deletion, no merge to `main`, no force-push, no live-service state change. Per §2.6 the restart rule attaches to `feature/*` and `hotfix/*`; `chore/*` carries none. The eventual merges to `main` and `dev` are local `--no-ff` merges Ray performs, outside this spec's steps.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The script lives in `automation/` and no longer in `scripts/` | `test -f automation/check_release_integrity.py && test ! -e scripts/check_release_integrity.py` exits `0` |
| AC1.3 | The anchor is the `automation/` pattern, and the old one is gone | Both required. **(a)** `grep -c 'find_repo_root' automation/check_release_integrity.py` prints at least `2` (definition and call). **(b)** `grep -c 'parent.parent' automation/check_release_integrity.py` prints `0` — compare stdout, not exit status, since `grep -c` exits `1` when it prints `0` |
| AC1.4 | The script's own usage block names its real path | Both required: `grep -c 'automation/check_release_integrity.py' automation/check_release_integrity.py` prints `3`, and `grep -c 'scripts/check_release_integrity' automation/check_release_integrity.py` prints `0` |
| AC2.1 | `pre-push` invokes the new path and names no old one | Within `.githooks/pre-push`: `grep -c 'automation/check_release_integrity.py'` prints `2`, and `grep -c 'scripts/check_release_integrity'` prints `0` |
| AC2.2 | A missing checker fails loudly instead of exiting zero | `grep -c '|| exit 0' .githooks/pre-push` prints `0`. Behavioural check, **offline — no push**: invoke the hook directly with a crafted stdin line, `sha=$(git rev-parse HEAD); printf 'refs/heads/main %s refs/heads/main %s\n' "$sha" "$sha" \| .githooks/pre-push origin git@example.invalid:x.git`. With the checker present it exits `0`; with it temporarily renamed it exits non-zero and prints a message naming the missing file. Restore the file immediately and record both exit codes in the step 2 commit message |
| AC2.3 | `pre-push` cites the section that owns its rule | `grep -c 'DEVELOPMENT_STANDARDS.md §2.2' .githooks/pre-push` prints at least `1` |
| AC3.1 | No file in `.githooks/` carries gate wording | `grep -rnic gate .githooks/` prints `0` for both files — compare stdout, not exit status |
| AC3.2 | The replacement is §2.4's own wording, not a new phrasing | `grep -c 'Step context belongs in the body' .githooks/commit-msg` prints `1` and `grep -c 'Step 3 of 7' .githooks/commit-msg` prints `1`, and both strings appear in §2.4 — `awk '/^### 2\.4/,/^### 2\.5/' docs/DEVELOPMENT_STANDARDS.md \| grep -c 'Step context belongs in the body'` prints `1` |
| AC3.3 | Every remaining reference in `.githooks/` resolves | For each `§N.N` cited in either hook, `grep -c "^### N.N" docs/DEVELOPMENT_STANDARDS.md` prints `1`. Enumerate with `grep -oE '§[0-9]+\.[0-9]+' .githooks/* \| sort -u` |
| AC4.1 | The script runs from its new location with the same output as before the move | Capture before and after at implementation time on the same commit range, so nothing is pinned to a number that ages. **Before**, as the first action of step 1: `python3 scripts/check_release_integrity.py --no-remote > /tmp/rci_before.txt 2>&1; echo $? >> /tmp/rci_before.txt`. **After**, at step 2: the same with `automation/` into `/tmp/rci_after.txt`. `diff /tmp/rci_before.txt /tmp/rci_after.txt` prints nothing. Paste the captured output into the step 2 commit message |
| AC4.2 | The hook path resolves from a subdirectory as well as the root, since `repo_root` is `git rev-parse --show-toplevel` | From `docs/`, `python3 "$(git rev-parse --show-toplevel)/automation/check_release_integrity.py" --no-remote` exits `0` |
| AC5.1 | No live old-path citation remains outside the archive, the parked branch, and this spec's own pair | `grep -rn 'scripts/check_release_integrity' . --exclude-dir=.git --exclude-dir=archive --exclude=RELEASE_CHECK_RELOCATION_SPEC.md --exclude=RECON_RELEASE_CHECK_RELOCATION.md` returns no hits. This spec and its recon quote the old path as the subject of the work — recording where it *was* is their job, and excluding them is not a loophole around AC2.1, which greps `.githooks/pre-push` in both directions on its own |
| AC5.2 | The application suite is untouched | `python -m pytest tests/ -q` — zero failures, and the pass count equals the baseline recorded in the step 1 commit message. No file under `workmain/` or `tests/` is changed: `git diff --name-only main...HEAD \| grep -cE '^(workmain\|tests)/'` prints `0` |
| AC5.3 | `chore/*` bookkeeping is respected | `git diff --name-only main...HEAD` contains neither `CHANGELOG.md` nor `workmain/__version__.py`, and `git tag --contains HEAD` prints nothing |

## 6. Test plan

- **Baseline before this work:** Anvil runs `python -m pytest tests/ -q` before touching anything at step 1 and records the pass count in the step 1 commit message. That commit is the baseline of record; no count is written into this document, per the standing rule that a live count never goes into a document.
- **Expected after:** unchanged. No test is added, and no file under `tests/` or `workmain/` is touched (AC5.2).
- **No new test file.** `check_release_integrity.py` has no tests today (recon F16) and #87 states no test AC; `testpaths` stays `["tests"]`, so a test beside the module would not be collected by a bare `pytest` run in any case (C16). Adding both the tests and the `testpaths` change is separate work.
- The two behavioural checks that are not pytest — AC2.2's rejected push and AC4.1's output comparison — are run once and recorded in their step's commit message, which is where a `chore/*` branch's evidence lives.

## 7. Risks and rollback

| Risk | Mitigation |
| --- | --- |
| The hook stops protecting `main` because a path was missed. This is the whole point of the issue, and today it happens silently (C8) | AC2.1 greps both directions, and DR3 removes the silence: after step 2 a missing checker is a rejected push with a message. AC2.2 proves it against a real push |
| `find_repo_root` behaves differently from `.parent.parent` in some invocation (worktree, symlinked path, submodule) | The two agree whenever a `.git` entry sits one level above the module, which is every invocation this repository makes. AC4.1 and AC4.2 exercise both the direct run and the hook's `--show-toplevel` form. A worktree's `.git` is a file, and `Path.exists()` is true for a file, so the walk still matches |
| Two copies of `find_repo_root` now exist in `automation/` and drift | Accepted deliberately, Decision Log 20260819: `automation/` is not a package (C5) and both modules are standalone stdlib scripts. Extraction is worth doing at a third caller |
| The parked branch's citations go stale and are forgotten | They are named in §1 out-of-scope with the reason, and `CYCLE_CLOSEOUT_SPEC.md` already carries #87 in its own risk table. The parked branch cannot merge without passing through them |
| A reference exists that this spec did not find | AC5.1 is a repository-wide grep rather than a list of known sites, so it fails on anything missed rather than on anything enumerated |

**Rollback.** Every step is a self-contained commit against four files, with no schema change, no migration, and no application code touched. `git revert` of any step undoes it; `git revert` of all four returns the repository to `main`.
