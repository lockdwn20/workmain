WorkmAIn
GIT_WORKFLOW_STANDARDS v1.1
20260319

# WorkmAIn Git Workflow Standards

This document is a standing instruction for Claude Code.
Read this before touching any code in any session.
These rules are permanent and apply to all future work.

---

## Branch Strategy

WorkmAIn uses a three-tier branching model:

```
main        — production-stable only. Direct commits NEVER permitted.
dev         — integration branch. All feature work merges here first.
feature/*   — full phase or major feature work. Branches from dev, merges to dev.
hotfix/*    — targeted fixes only. Branches from main, merges to main AND dev.
```

---

## Branch Rules

### `main`
- **Never commit directly to main.**
- Only receives merges from: `dev` (phase completions) or `hotfix/*` (targeted fixes)
- Every merge to main must bump `__version__.py` and update `CHANGELOG.md`
- Tag every merge to main: `git tag v<version>`

### `dev`
- Integration branch — always ahead of or equal to main
- Receives merges from `feature/*` branches
- Claude Code may commit directly to `dev` only for trivial version/changelog updates
  after a feature branch has already merged
- Must be merged to main only when a full phase is complete and verified

### `feature/*`
- Used for: full phases, major features, multi-gate implementations
- Naming: `feature/<descriptor>` e.g. `feature/phase-7-gdocs`
- Branch from: `dev`
- Merge to: `dev` (never directly to main)
- One feature branch per phase
- Example workflow:
  ```bash
  git checkout dev
  git pull
  git checkout -b feature/phase-7-gdocs
  # ... implement gates ...
  git checkout dev
  git merge --no-ff feature/phase-7-gdocs
  git branch -d feature/phase-7-gdocs
  ```

### `hotfix/*`
- Used for: targeted bug fixes, small corrections, config/path changes
- Naming: `hotfix/<descriptor>` e.g. `hotfix/staging-eod`
- Branch from: `main`
- Merge to: `main` AND `dev` (both, in that order)
- Must be minimal scope — if fix grows beyond 3 files, escalate to a feature branch
- Example workflow:
  ```bash
  git checkout main
  git pull
  git checkout -b hotfix/staging-eod
  # ... targeted fix ...
  git checkout main
  git merge --no-ff hotfix/staging-eod
  git tag v<version>
  git checkout dev
  git merge --no-ff hotfix/staging-eod
  git branch -d hotfix/staging-eod
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
git branch -d hotfix/some-fix

# Fix travels with the feature branch through dev → main
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

| Merge type           | Version change         | Example         |
|----------------------|------------------------|-----------------|
| Hotfix → main        | Patch bump (x.x.N+1)   | 1.3.0 → 1.3.1   |
| Feature/phase → dev → main | Minor bump (x.N+1.0) | 1.3.1 → 1.4.0 |
| Breaking change      | Major bump (N+1.0.0)   | 1.4.0 → 2.0.0   |

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

---

END OF GIT WORKFLOW STANDARDS
WorkmAIn — Standing Instruction for Claude Code
v1.1 — 20260319
