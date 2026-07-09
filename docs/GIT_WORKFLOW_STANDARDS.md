WorkmAIn
GIT_WORKFLOW_STANDARDS v1.5
20260709

# WorkmAIn Git Workflow Standards

This document is a standing instruction for Claude Code.
Read this before touching any code in any session.
These rules are permanent and apply to all future work.

---

## Version History
- v1.0 (20260306): Initial standards
- v1.1 (20260319): Added hotfix → feature branch exception
- v1.2 (20260410): Updated dev → main cadence (after every feature merge, not phase completion); added explicit branch deletion rules and cleanup commands
- v1.3 (20260505): Explicit GitHub PR requirement for dev → main; never local merge
- v1.4 (20260709): Clarified hotfix file-count scope limit to **application files
  only** (`workmain/**/*.py`, `config/*`, `templates/*`) — test files (`tests/**`),
  `__version__.py`, and `CHANGELOG.md` no longer count toward the limit, since they
  are mandatory companions to any properly-tested change and previously made full
  compliance impossible by construction. Clarified that file count is a proxy for
  scope, not the test itself — a bundled-unrelated-concerns fix should escalate
  regardless of count. Prompted by Item #58 hotfix (3 production files, 8 total
  including tests/version/changelog, which read as escalation-triggering under the
  prior wording despite being correctly scoped). Also corrected a footer
  version/date mismatch left over from the v1.3 revision.
- v1.5 (20260709): Added `chore/*` branch category for documentation/process-only
  changes, so doc updates (standards documents, `docs/**`) no longer need to ride a
  `hotfix/*` branch alongside unrelated code changes, or be justified under
  `hotfix/*`'s "small corrections" language. Same branch-from/merge-to topology as
  `hotfix/*` (from `main`, to both `main` and `dev`), but explicitly exempt from the
  application version bump / `CHANGELOG.md` entry / `git tag` requirement, since a
  doc-only change is not an application release — the affected document's own
  internal version header still gets bumped per its own convention. Strictly scoped
  to non-application files; anything touching `workmain/**`, `config/*`,
  `templates/*`, `tests/**`, or `CHANGELOG.md` itself remains `hotfix/*` or
  `feature/*` regardless of size. Prompted directly by this revision's own history —
  the v1.4 change rode the Item #58 hotfix commit before being split out.

---

## Branch Strategy

WorkmAIn uses a three-tier branching model:

```
main        — production-stable. Direct commits NEVER permitted.
dev         — integration branch. All feature work merges here first.
feature/*   — full phase or major feature work. Branches from dev, merges to dev.
hotfix/*    — targeted fixes only. Branches from main, merges to main AND dev.
chore/*     — documentation/process-only changes. Branches from main, merges to main AND dev.
```

---

## Branch Rules

### `main`
- **Never commit directly to main.**
- Only receives merges from: `dev` (after each feature merge) or `hotfix/*` (targeted fixes)
- Every merge to main must bump `__version__.py` and update `CHANGELOG.md`
- Tag every merge to main: `git tag v<version>`

### `dev`
- Integration branch — always equal to or one feature ahead of main
- Receives merges from `feature/*` branches
- Claude Code may commit directly to `dev` only for trivial version/changelog updates
  after a feature branch has already merged
- **Must be merged to main after every feature branch merge, once the integrated work
  is verified stable. Do not let dev sit ahead of main.**
- **The dev → main merge MUST happen via GitHub PR — never a local `git merge`.**
  Push dev, create the PR with `gh pr create`, verify on GitHub, merge on GitHub,
  then `git pull origin main` locally.

### `feature/*`
- Used for: full phases, major features, multi-gate implementations
- Naming: `feature/<descriptor>` e.g. `feature/phase-7-gdocs`
- Branch from: `dev`
- Merge to: `dev` (never directly to main)
- One feature branch per phase
- **Delete the branch immediately after merge — the tag on main is the permanent record**
- Example workflow:
  ```bash
  git checkout dev
  git pull
  git checkout -b feature/phase-7-gdocs
  # ... implement gates ...
  git checkout dev
  git merge --no-ff feature/phase-7-gdocs
  git branch -d feature/phase-7-gdocs                    # delete local
  git push origin dev
  git push origin --delete feature/phase-7-gdocs         # delete remote

  # Create GitHub PR: dev → main  (NEVER merge dev → main locally)
  gh pr create --base main --head dev --title "..." --body "..."
  # Verify on GitHub, merge via GitHub UI or gh pr merge

  # After GitHub merges:
  git checkout main
  git pull origin main
  git tag v<version>
  git push --tags
  ```

### `hotfix/*`
- Used for: targeted bug fixes, small corrections, config/path changes
- Naming: `hotfix/<descriptor>` e.g. `hotfix/staging-eod`
- Branch from: `main`
- Merge to: `main` AND `dev` (both, in that order)
- Must be minimal scope — if the fix touches more than 3 **application** files
  (`workmain/**/*.py`, `config/*`, `templates/*`), escalate to a feature branch.
  Test files (`tests/**`), `__version__.py`, and `CHANGELOG.md` are expected
  companions to any properly-tested change and do not count toward this limit.
- File count is a proxy, not the actual test. The real question is whether the fix
  is one traceable root cause (one AC, one bug) or bundles multiple unrelated
  concerns — if a hotfix spec starts needing internal design decisions about
  unrelated pieces, that's the signal to split it, regardless of file count.
- **Delete the branch immediately after both merges are complete**
- Example workflow:
  ```bash
  git checkout main
  git pull
  git checkout -b hotfix/staging-eod
  # ... targeted fix ...
  git checkout main
  git merge --no-ff hotfix/staging-eod
  git tag v<version>
  git push && git push --tags
  git checkout dev
  git merge --no-ff hotfix/staging-eod
  git push
  git branch -d hotfix/staging-eod                       # delete local
  git push origin --delete hotfix/staging-eod            # delete remote
  ```

### Hotfix → Feature Branch Exception

When a hotfix is a direct prerequisite for a feature branch (i.e. it cannot
ship independently because it has no standalone value, and the feature branch
depends on it), the following alternative flow is permitted:

```
hotfix/* → feature/* → dev → main
```

**Rules for this exception:**
- The hotfix branch MUST still branch from `main`
- The fix MUST be minimal scope (single file or targeted correction)
- The deviation MUST be documented explicitly in the feature spec
- The hotfix branch is merged into the feature branch at Gate 0, then deleted
- The fix reaches `main` via the feature branch's normal merge path
- Version bump for the fix is included in the feature's version bump (no
  separate patch version)

**Example:**
```bash
# Branch hotfix from main
git checkout main && git checkout -b hotfix/some-fix

# Apply fix, commit
git commit -m "fix(...): ..."

# At feature Gate 0: merge hotfix into feature branch
git checkout feature/phase9-report-pipeline
git merge --no-ff hotfix/some-fix -m "fix: merge hotfix/some-fix"
git branch -d hotfix/some-fix                            # delete local
git push origin --delete hotfix/some-fix                 # delete remote

# Fix travels with the feature branch through dev → main
```

---

### `chore/*`
- Used for: documentation-only and process/tooling changes — standards documents
  (`CLAUDE.md`, `CLI_STANDARDS.md`, `GIT_WORKFLOW_STANDARDS.md`, `TESTING_STANDARDS.md`,
  `PROJECT_CUSTOM_INSTRUCTIONS.md`), `docs/**`, and non-behavioral dev-tooling files
  (`.gitignore`, editor/CI config). **Never** application code, `config/*`,
  `templates/*`, `tests/**`, or `CHANGELOG.md` itself — a change touching any of those
  is a `hotfix/*` or `feature/*`, however small, not a `chore/*`.
- Naming: `chore/<short-descriptor>` e.g. `chore/git-workflow-hotfix-scope-clarification`
- Branch from: `main`
- Merge to: `main` AND `dev` (both, in that order) — same topology as `hotfix/*`
- Must be minimal scope — one document, or one tightly-related set of documents edited
  for a single reason. Do not bundle unrelated document changes into one `chore/*`
  branch.
- **No application version bump, no `CHANGELOG.md` entry, no `git tag`.** A doc-only
  chore is not an application release, so none of the `main`-merge requirements above
  that are specific to shipping application code apply here. Still bump the affected
  document's own internal version header and changelog block, per that document's own
  versioning convention (e.g. `GIT_WORKFLOW_STANDARDS.md` v1.4 → v1.5).
- Delete the branch immediately after both merges are complete
- Example workflow:
  ```bash
  git checkout main
  git pull
  git checkout -b chore/some-doc-update
  # ... doc-only edit; bump the document's own version header/changelog ...
  git checkout main
  git merge --no-ff chore/some-doc-update
  git push
  git checkout dev
  git merge --no-ff chore/some-doc-update
  git push
  git branch -d chore/some-doc-update                    # delete local
  git push origin --delete chore/some-doc-update         # delete remote
  ```

---

## Branch Deletion Rules

Branches are temporary scaffolding. Once merged, delete them. Tags are the
permanent historical record — not branches.

**Rule:** Delete every branch (local and remote) immediately after it is merged.
There are no exceptions. If a branch is merged, it has no further purpose.

**Why tags are sufficient:**
- `git tag v1.9.0` on main marks exactly what shipped and when
- `CHANGELOG.md` records what was in scope
- The branch adds no information that the tag and commit history don't already have

**Cleanup commands for existing stale branches:**

```bash
# Delete all merged remote branches (except main and dev)
git branch -r --merged main \
  | grep -v "main\|dev" \
  | sed 's/origin\///' \
  | xargs -I {} git push origin --delete {}

# Delete all merged local branches (except main and dev)
git branch --merged main | grep -v "main\|dev" | xargs git branch -d

# Verify what remains
git branch -a
```

---

## Commit Message Standard

```
<type>(<scope>): <short description>

<optional body — what and why, not how>
```

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`

Examples:
```
feat(gdocs): add staging folder structure with gitkeep files
fix(eod): replace report daily --send with report save + email save
chore(staging): rename output/ to staging/ across all references
```

---

## Version Bump Rules

| Merge type                  | Version change           | Example         |
|-----------------------------|--------------------------|-----------------|
| Hotfix → main               | Patch bump (x.x.N+1)     | 1.3.0 → 1.3.1   |
| Feature/phase → dev → main  | Minor bump (x.N+1.0)     | 1.3.1 → 1.4.0   |
| Breaking change             | Major bump (N+1.0.0)     | 1.4.0 → 2.0.0   |
| Chore → main                | **None** — not an application release; see `chore/*` branch rules | — |

Always update `__version__.py` AND `CHANGELOG.md` together on every merge to main
**that ships application code** — `chore/*` merges are explicitly exempt (see above).

---

## Session Start Checklist for Claude Code

Before writing any code in any session:

1. `git status` — confirm working directory is clean
2. `git branch` — confirm which branch you are on
3. Determine work type:
   - Full phase or multi-gate feature → `feature/*` from `dev`
   - Targeted fix (application code) → `hotfix/*` from `main`
   - Documentation/process-only change, no application code → `chore/*` from `main`
4. Create the appropriate branch before writing any code
5. Never work directly on `main` or `dev`

---

## What Claude Code Must NEVER Do

- Commit directly to `main`
- Commit directly to `dev` (except trivial version/changelog chores post-merge)
- Merge a feature branch directly to `main` (must go through `dev` first)
- Merge `dev` into `main` locally — this merge MUST go through a GitHub PR
- Skip the version bump on a merge to `main`
- Combine hotfix and feature work on the same branch
- Start writing code before creating the appropriate branch
- Leave a branch alive after it has been merged
- Let `dev` sit ahead of `main` after a feature merge is verified stable
- Use `chore/*` for any change that touches application code, `config/*`,
  `templates/*`, `tests/**`, or `CHANGELOG.md` — those belong on `hotfix/*` or
  `feature/*` regardless of size

---

END OF GIT WORKFLOW STANDARDS
WorkmAIn — Standing Instruction for Claude Code
v1.5 — 20260709
