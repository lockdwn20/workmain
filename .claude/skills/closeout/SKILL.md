---
name: closeout
description: Mechanically verify an issue's close-out — every AC against delivered code, the release and deployment record against the branch type, and a docs/dev/results/ artifact — before Ray closes the issue on GitHub.
disable-model-invocation: true
---

# `/closeout <issue>`

User-initiated only. This skill makes no GitHub write — it reads issues, tags and
Releases, and writes one file in the working tree. It reports; it closes nothing.
Posting the closing comment and closing the issue are Ray's, on the same principle
as merging a `dev → main` PR.

## Procedure

1. Run the mechanical checks:

   ```bash
   python3 automation/closeout_checks.py <issue> [--branch <name>]
   ```

   `--branch` is the escape hatch for an issue whose branch does not follow the
   `<type>/issue-<N>-<slug>` convention (`docs/DEVELOPMENT_STANDARDS.md` §2.1) — pass
   it when the derived branch is wrong or the branch predates the convention.

2. If the script exits non-zero on issue resolution alone (stderr names the issue
   number), stop — there is nothing else to check.

3. For every other failure the script reports, read the failure and judge it:

   - A missing or dropped AC, a `Not met` row, or an uncited `Carried` row in the
     results artifact is not this skill's call to overturn — the script's exit
     code is the verdict (DR6). Fix the artifact or the underlying work, not the
     report.
   - **Whether an AC is actually met by delivered code is judgement, and lives
     here, not in the script** (DR3). Walk each AC against the code that shipped
     it — do not accept the spec's or the issue's own say-so as evidence.

4. Once every check passes, the script prints a `gh issue comment` command and the
   comment body on stdout. Show both to Ray. **Do not run the command** — DR2
   reserves posting for Ray, the same way PR merges are his.

5. Ray posts the comment and closes the issue himself, when he chooses to.

## The workpaths

The branch type selects which checks apply (`docs/DEVELOPMENT_STANDARDS.md` §2.1,
§2.2). A row that does not apply is reported `n/a` with its reason — never silently
omitted, so a skipped check cannot be mistaken for a passed one.

| Check | `chore/*` | `feature/*` | `hotfix/*` |
| --- | --- | --- | --- |
| Every AC met against delivered code | yes | yes | yes |
| Application suite passes | yes | yes | yes |
| `automation/` suite passes when the branch touched `automation/` | yes | yes | yes |
| Version bump present, of the §2.5 magnitude | n/a — §2.2 forbids it | minor | patch |
| Release ledger entry for the new version, non-empty | n/a — §2.2 forbids it | yes | yes |
| Tag on `main` for the new version | n/a — §2.2 forbids it | yes | yes |
| GitHub Release for that tag | n/a — §2.2 forbids it | yes | yes |
| `check_release_integrity.py` exits zero | yes | yes | yes |
| Daemon restarted after the `dev` merge, per §2.6 | n/a — no application code | yes | yes |
| Merged to both `main` and `dev` | yes | `dev` then `main` by PR | yes |
| Results artifact present and complete | yes | yes | yes |

The `chore/*` rows marked `n/a` are **assertions of absence**, not omissions: the
run fails if a `chore/*` branch bumped `workmain/__version__.py` or carries a tag —
§2.2 forbids both, and a silent skip would let a mis-typed branch pass.
