WorkmAIn
GIT_WORKFLOW_STANDARDS v1.2
20260410

# WorkmAIn Git Workflow Standards

This document is a standing instruction for Claude Code.
Read this before touching any code in any session.
These rules are permanent and apply to all future work.

---

## Version History
- v1.0 (20260306): Initial standards
- v1.1 (20260319): Added hotfix → feature branch exception
- v1.2 (20260410): Updated dev → main cadence (after every feature merge, not phase completion); added explicit branch deletion rules and cleanup commands

---

## Branch Strategy

WorkmAIn uses a three-tier branching model:

```
main        — production-stable. Direct commits NEVER permitted.
dev         — integration branch. All feature work merges here first.
feature/*   — full phase or major feature work. Branches from dev, merges to dev.
hotfix/*    — targeted fixes only. Branches from main, merges to main AND dev.
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
  git push origin --delete feature/phase-7-gdocs         # delete remote
  # verify stable, then:
  git checkout main
  git merge --no-ff dev
  git tag v<version>
  git push && git push --tags
  ```

### `hotfix/*`
- Used for: targeted bug fixes, small corrections, config/path changes
- Naming: `hotfix/<descriptor>` e.g. `hotfix/staging-eod`
- Branch from: `main`
- Merge to: `main` AND `dev` (both, in that order)
- Must be minimal scope — if fix grows beyond 3 files, escalate to a feature branch
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

Always update `__version__.py` AND `CHANGELOG.md` together on every merge to main.

---

## Session Start Checklist for Claude Code

Before writing any code in any session:

1. `git status` — confirm working directory is clean
2. `git branch` — confirm which branch you are on
3. Determine work type:
   - Full phase or multi-gate feature → `feature/*` from `dev`
   - Targeted fix → `hotfix/*` from `main`
4. Create the appropriate branch before writing any code
5. Never work directly on `main` or `dev`

---

## What Claude Code Must NEVER Do

- Commit directly to `main`
- Commit directly to `dev` (except trivial version/changelog chores post-merge)
- Merge a feature branch directly to `main` (must go through `dev` first)
- Skip the version bump on a merge to `main`
- Combine hotfix and feature work on the same branch
- Start writing code before creating the appropriate branch
- Leave a branch alive after it has been merged
- Let `dev` sit ahead of `main` after a feature merge is verified stable

---

END OF GIT WORKFLOW STANDARDS
WorkmAIn — Standing Instruction for Claude Code
v1.2 — 20260410
