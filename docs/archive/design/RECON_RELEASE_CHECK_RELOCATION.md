# Release-Check Relocation — Recon

**Status:** Shipped
**Kind:** Recon
**Author:** Spanner (Role 1)
**Date:** 20260819
**Originating item:** Issue #87

---

## 1. Purpose

Issue #87 moves `scripts/check_release_integrity.py` to `automation/` and requires that every reference to the old path be updated, that the script's path-relative logic still resolve, and that no file in `.githooks/` carry outdated wording or stale references — the latter added because issue #86 replaced gate discipline with steps and authorization points, and `.githooks/` was not swept at the time.

This is a **recon**: read-only. No file was modified, no fix was applied, and no recommendation appears alongside any finding. Options and recommendations are deliberately absent — §4 of the design template is omitted, per its own instruction for a recon. Open questions are collected in §5 for Ray and Role 1 to answer before the spec is written.

## 2. Scope of the read

**Read:**

- `scripts/check_release_integrity.py` — full file header, path constants, invocation surface
- `.githooks/commit-msg` and `.githooks/pre-push` — both files in full; these are the only two files in the directory
- `automation/` — directory census, and `automation/issue_validator.py` for its repo-root precedent
- `scripts/` — directory census, to establish what the directory otherwise holds
- `docs/DEVELOPMENT_STANDARDS.md` §1.1, §2.1, §2.2, §2.4, §7
- `pyproject.toml`, `.gitignore`, and `git config core.hooksPath`
- A repository-wide reference census: `grep -rn check_release_integrity` excluding `.git/`

**Not read:**

- The body of `check_release_integrity.py` below its constants — its internal logic is not changed by a relocation, and #87 asserts no behaviour change. Its correctness is out of scope.
- `docs/archive/**` beyond confirming one citation exists. CLAUDE.md states the archive is never updated.
- Any CI/CD configuration, because none exists in this repository — `.github/` holds issue templates only. #87's third AC names "CI/CD config" as a reference site; there is none.
- The application suite. #87 touches no application code.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | `scripts/` otherwise holds only application-adjacent utilities: nine `migrate_*.py`, `database/`, `demo_template_cli.py`, `preview_templates.py`, `sanitize_ics.py`, `task_pool_stale_dismissal_20260728.py`. `check_release_integrity.py` is the single non-application entry, which is #87's premise and it holds | `ls scripts/`; §7 rows "Utility scripts → `scripts/`" and "Non-application dev tooling → `automation/`" | High |
| F2 | The script's path anchor is `ROOT = Path(__file__).resolve().parent.parent`. Both `scripts/` and `automation/` sit exactly one directory below the repository root, so `ROOT` resolves to the same path after the move. `CHANGELOG`, `VERSION_FILE`, and `sh()`'s `cwd=ROOT` all derive from it | `scripts/check_release_integrity.py:37-39`, `:52` | High |
| F3 | The destination directory's existing module does **not** use that pattern. `automation/issue_validator.py` calls `find_repo_root(Path(__file__))`, which walks `current` and `current.parents` for a `.git` entry and raises `ValidationAbort` if none is found. It is depth-independent; `.parent.parent` is depth-dependent. This is a divergence between the two files, not a defect in either | `automation/issue_validator.py:304`, `def find_repo_root` | Medium |
| F4 | Nothing imports the script as a module. `grep -rn "import check_release_integrity\|from check_release_integrity"` returns no hits outside `.git/`. Its only programmatic caller is the hook | repository-wide grep | High |
| F5 | `.githooks/pre-push` references the old path twice: once in prose (`# Runs scripts/check_release_integrity.py, which cross-checks git tags against`) and once executably (`checker="$repo_root/scripts/check_release_integrity.py"`), where `repo_root` comes from `git rev-parse --show-toplevel` | `.githooks/pre-push:5`, `:27` | Critical |
| F6 | The hook guards the checker with `[ -f "$checker" ] | | exit 0`. A stale path therefore **fails open and silent**: the push succeeds, no message is printed, and the release record is no longer verified. The relocation is precisely the event that triggers this, and nothing in the hook would report it | `.githooks/pre-push:29` | Critical |
| F7 | The hook is live in this clone — `git config --get core.hooksPath` returns `.githooks`. F6 is therefore a real exposure here, not a hypothetical one | `git config --get core.hooksPath` | High |
| F8 | Neither `scripts/check_release_integrity.py` nor `automation/issue_validator.py` carries the executable bit (`-rw-r--r--`). The hook invokes the checker as `python3 "$checker"`, so the mode is irrelevant and `git mv` preserves it either way | `ls -l`; `.githooks/pre-push:54` | Low |
| F9 | Outdated gate wording in `.githooks/` is exactly two lines, both in `commit-msg`, verbatim: `Gate context belongs in the body, never the subject:` and `Gate 3 of 7. Files changed, decisions made, expected test count.` `pre-push` contains no occurrence of "gate" in any case | `.githooks/commit-msg:58`, `:62`; `grep -rni gate .githooks/` | High |
| F10 | §2.4 already carries the corrected form of both lines: "Step context belongs in the body, not the subject — `feat(notes): converge write path` with `Step 3 of 7` in the body, never `Step 3: ...` as the subject." The hook contradicts a canonical source that already states the replacement wording | `docs/DEVELOPMENT_STANDARDS.md` §2.4 | High |
| F11 | `commit-msg`'s other references are current: it cites `docs/DEVELOPMENT_STANDARDS.md §2.4` twice (header comment and footer), and §2.4 does own commit-message format and does prohibit `--no-verify`. Its enable instruction `git config core.hooksPath .githooks` matches §2.4's | `.githooks/commit-msg:8`, `:64`; §2.4 | Low |
| F12 | `pre-push` cites **no** standards section anywhere, though §2.2 owns the rule it enforces (CHANGELOG entry, tag, and GitHub Release on every merge to `main`). `commit-msg` cites its section twice. The two hooks are asymmetric on this point | `.githooks/pre-push` full file; §2.2 | Medium |
| F13 | The script's own module docstring names the old path three times in its usage block: `python3 scripts/check_release_integrity.py`, `... --no-remote`, `... --show-historical` | `scripts/check_release_integrity.py:20-22` | High |
| F14 | Remaining old-path citations in the repository, by disposition: **live** — `docs/dev/specs/ISSUE_CREATION_VALIDATION_SPEC.md:87,102` (Status: Shipped); **parked** — `docs/dev/specs/CYCLE_CLOSEOUT_SPEC.md:47,63,82,113,120,141,205,226,237` and `docs/dev/design/RECON_CYCLE_CLOSEOUT.md:15,25,81,82,83,84`, none of which are on `main`; **archive** — `docs/archive/design/DESIGN_PLANNING_DOCS_STANDARDS_REVIEW.md:329`, which CLAUDE.md states is never updated | repository-wide grep; `git log main..chore/issue-83-cycle-closeout` | High |
| F15 | `pyproject.toml` is two lines: `[tool.pytest.ini_options]` and `testpaths = ["tests"]`. `automation/issue_validator_test.py` therefore is not collected by a bare `pytest` run and must be invoked as `pytest automation/`. No packaging, console-script entry point, or `[project]` table exists that could reference either directory | `pyproject.toml` | Medium |
| F16 | `check_release_integrity.py` has no tests, before or after the move. `grep -rl check_release_integrity tests/` returns nothing. #87 states no test AC | `ls`, grep | Medium |
| F17 | §2.2's `chore/*` clause lists `.githooks/` and `automation/` as qualifying paths outright, but adds: a change to `workmain/**`, `tests/**`, or `scripts/**` "may use `chore/*` if it is mechanically proven behaviour-neutral (e.g. AST-equality) *and* the governing spec states the proof method." A rename out of `scripts/` touches both halves of that rule at once | `docs/DEVELOPMENT_STANDARDS.md` §2.2 | High |
| F18 | Two standards commits sit on the parked branch `chore/issue-83-cycle-closeout` and are **not** on `main`: `0cc9676` (§2.6 restart rule by branch type) and `a5bec5d` (§1.5 markdown is never hard-wrapped). Work branching from `main`, including #87, does so against a `DEVELOPMENT_STANDARDS.md` that carries neither. Ray decided on 20260819 to leave them parked | `git log main..chore/issue-83-cycle-closeout --stat`; Ray, 20260819 | Medium |
| F19 | `scripts/__pycache__/` and `automation/__pycache__/` both exist on disk and are covered by `.gitignore`'s `__pycache__/`. Neither is tracked, so neither follows the move | `ls`, `.gitignore` | Low |

**Nothing above is asserted without a citation.** One item is explicitly unverified: whether `.githooks/` contains wording made outdated by issues *other* than #86 was checked only for the word "gate" and for the references listed in F11 and F12. A line could be stale for a reason this read did not think to look for.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Given F2 and F3, does the move keep `ROOT = Path(__file__).resolve().parent.parent` unchanged, or adopt the destination directory's `find_repo_root()` pattern? Keeping it makes the move a pure rename, which is the strongest available form of the behaviour-neutrality proof F17 requires. Adopting the sibling's pattern converges the two `automation/` modules but forfeits that proof and puts content change inside the same commit as the rename | **Answered 20260819 (Ray).** The script is adjusted to meet the standard: it adopts `find_repo_root`. The proof-method framing in this question is **withdrawn** — Ray had settled the branch type before this recon was written, and F17 should not have reopened it. |
| Q2 | Does F13 — the script's own docstring naming the old path three times — count as content change for Q1's purposes, or is it part of the rename? It must change regardless, since leaving it would ship a file whose usage block is wrong | **Answered 20260819 (Spanner).** Moot once Q1 is answered — the docstring changes regardless. |
| Q3 | How far does "outdated wording" in `.githooks/` reach? F9 is the two gate lines and is unambiguous. F12 — `pre-push` citing no standards section while `commit-msg` cites its own twice — is an inconsistency this read surfaced but which #86 did not create | **Answered 20260819 (Ray).** In scope. Fix it. |
| Q4 | Does #87 address F6, the fail-open guard? It is outside #87's stated ACs, but the relocation is the exact event that would trip it, and F7 confirms the hook is live in this clone | **Answered 20260819 (Ray).** In scope. Fix it. |
| Q5 | Per F14, do the parked `CYCLE_CLOSEOUT_SPEC.md` and `RECON_CYCLE_CLOSEOUT.md` citations fall under #87's "any references to the old path are updated", or does the parked branch carry its own correction when it unparks? #87 cannot reach them without unparking the branch Ray just parked | **Answered 20260819 (Spanner).** Out of scope. The parked branch corrects its own citations when it unparks; `docs/archive/**` is never updated. |
| Q6 | Per F15, does anything in #87 need `testpaths` widened to include `automation/`? #87 adds no tests, but AC4 requires the script "runs successfully from `automation/` with the same output as before the move", and how that is evidenced depends on the answer | **Answered 20260819 (Spanner).** No. `testpaths` stays `["tests"]`; AC4.1 is a captured before/after run. |

## 6. Disposition

- Promoted to: `docs/dev/specs/RELEASE_CHECK_RELOCATION_SPEC.md`
- Note: finding F17 and the proof-method framing built on it are withdrawn — see Q1.
