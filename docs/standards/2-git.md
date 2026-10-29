## 2. Git Workflow

### 2.1 Branch strategy

```text
main       — production-stable. Direct commits NEVER permitted.
dev        — integration branch. All feature work merges here first.
feature/*  — full phase or major feature work. From dev, merges to dev.
hotfix/*   — targeted fixes. From main, merges to main AND dev.
chore/*    — documentation/process/tooling only. From main, merges to main AND dev.
```

**Branch names are `<type>/issue-<N>-<slug>`.** The issue number is what links a merge commit back to its issue once §2.3 deletes the branch. Work with no issue behind it is the exception and names itself descriptively — this is an exception, not the standard.

### 2.2 Branch rules

**`main`**

- Never commit directly.
- Receives merges from `dev`, `hotfix/*` and `chore/*`.
  - `dev` reaches `main` through a pull request — the `dev` block below.
  - **A `hotfix/*` or `chore/*` branch is merged into `main` locally (§2.3), and `main` is pushed.** The repository ruleset `main-pr-required` requires a pull request for every change to `main`. This push passes it through the ruleset's bypass for the repository admin role, so GitHub prints `remote: - Changes must be made through a pull request.` and accepts the push. That line is expected on these two branch types and is not a failure. An account without the admin role cannot make this push.
  - The ruleset was added after a pull request was opened against `main` from a fork (#234). The bypass was added so this route would continue.
- **A merge carrying application code — from `dev` or `hotfix/*` — is a release.** It bumps `workmain/__version__.py`, updates `CHANGELOG.md`, is tagged `git tag v<version>`, and gets a GitHub Release: `gh release create v<version> --generate-notes`.
- **A `chore/*` merge is not a release and does none of those four things.** It changes no application behaviour, so there is nothing to version. This is the only exception, and the `chore/*` block below is its full statement.

**`dev`**

- Always equal to, or one feature ahead of, `main`.
- Direct commits permitted only for trivial version/changelog updates after a feature merge.
- **`dev → main` MUST go through a GitHub PR — never a local merge.**
  - Push `dev`-> `gh pr create` -> verify on GitHub -> stop. **Ray merges the PR himself**.

**`feature/*`**

- from `dev`
- merges to `dev` then to `main` via PR only.
- Stays local
- Deleted after merge.

**`hotfix/*`**

- from `main`
- merges to `main` and `dev`.
- Escalate to `feature/*` if the fix touches more than 3 **application** files (`workmain/**/*.py`, `config/*`, `templates/*`).
  - Tests, `__version__.py`, `CHANGELOG.md` and docs/ are mandatory companions and do not count.
  - File count is a proxy, not the test. The real metric is whether the fix is one traceable root cause.
  - Bundled unrelated concerns escalate regardless of count.

**`chore/*`**

- from `main`
- merges to `main` and `dev`.
- For `docs/**`, standards documents, `.claude/`, and dev tooling that changes no application behaviour (`.gitignore`, `.githooks/`, `.github/`, `automation/`, editor/CI config).
- **Exception:** a change to `workmain/**`, `tests/**`, or `scripts/**` may use `chore/*` if it is mechanically proven behaviour-neutral (e.g. AST-equality) *and* the governing spec states the proof method.
- **No version bump, no `CHANGELOG.md` entry, no tag, no Release.** A doc-only change is not an application release.
- Scope: One tightly-related set of files edited for a single reason.

**Operational changes from live use.**

- WorkmAIn is in daily use while it is developed, and some `workmain` commands write tracked files as part of normal operation — `workmain providers set default`, for example, writes `config/ai_settings.json`. The change appears uncommitted on whichever branch is checked out, and is not part of that branch's work.
- It is committed on the next branch to be completed, of any type, before `/closeout` runs: one commit, separate from the branch's own work, typed `chore(config)` or `chore(templates)`, whose body states that it is an operational change made through the CLI.
- It needs no spec and no acceptance criterion, is not scope of the issue the branch serves, and does not count toward the `hotfix/*` file limit.
- It does not change whether the merge is a release: a `chore/*` merge carrying it is still not one, and a `feature/*` or `hotfix/*` merge is released as it would be without it.
- It covers only a file a `workmain` command wrote. A hand edit to `config/` or `templates/` is development, and takes the branch its change requires.

**hotfix/* → feature/* exception.**

- When a hotfix is a direct prerequisite for a feature branch and has no standalone value
  - Branch from `main`
  - Merge the hotfix/** into the feature/* branch before its step 1
  - Delete the hotfix/*
  - The feature spec's Decision Log records the folded hotfix before the spec is approved.
  - The version bump rides the feature.

### 2.3 Branch deletion

- `main` and `dev` are the only branches on `origin`. **No `feature/*`, `hotfix/*` or `chore/*` branch is ever pushed** — feature branches merge to `dev` locally, and the only pull request is `dev → main`.
- A working branch is deleted locally once it has merged everywhere §2.2 sends it. There is no remote branch to delete, and a close-out that tries to delete one is following a rule this project does not have.
- A working branch that does reach `origin` is an exception, not the workflow. Deleting it there is a GitHub object deletion and an authorization point under §1.4.

**Every merge is `--no-ff`.**

- A fast-forward leaves no merge commit
- The merge commit is the only record of what the branch contained — its subject names the branch, and its second parent is the tip.
- A fast-forwarded branch is unrecoverable the moment it is deleted.
- Tags, `CHANGELOG.md` and the merge commit are the permanent record; the branch ref itself adds nothing.

### 2.4 Commit messages

```text
<type>(<scope>): <short description>

<body — what and why, not how. Files changed, decisions made, expected test count.>

Co-Authored-By: Claude
```

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`.

- This is the **only** commit format. Step context belongs in the body, not the subject — `feat(notes): converge write path` with `Step 3 of 7` in the body, never `Step 3: ...` as the subject.
- `git commit --no-verify` is **prohibited**. It bypasses commit validation.
- **Stage only the files you wrote** — `git add <path>`, never `git commit -a`. Ray edits live `config/` in the working tree mid-session, and `-a` commits his edit under your message. Check `git status --short` first; a file you did not touch stays unstaged and is mentioned.
- **Enforced by `.githooks/commit-msg`.** Enable it once per clone — it is not automatic, because git does not track `.git/hooks/`:

  ```bash
  git config core.hooksPath .githooks
  ```

  - The hook exempts merge, revert, and fixup/squash subjects, which git generates itself.
  - It validates format only — it cannot tell you a scope is wrong or a description is useless.

### 2.5 Version bumps

| Merge type | Change | Example |
| --- | --- | --- |
| Hotfix → main | Patch | 1.3.0 → 1.3.1 |
| Feature/phase → dev → main | Minor | 1.3.1 → 1.4.0 |
| Breaking change | Major | 1.4.0 → 2.0.0 |

Update `workmain/__version__.py` and `CHANGELOG.md` together on every `feature/*` and `hotfix/*` merge to `main`.

### 2.6 Deployment

`workmain-notify.service` (systemd `--user`) tracks **`dev`**, not `main`.

**Every `feature/*` and `hotfix/*` branch ends with a service restart.** The daemon loads code once at process start, so a merge to `dev` is not deployed until it restarts. `chore/*` carries no restart — it changes no application code.

```bash
systemctl --user restart workmain-notify.service
systemctl --user show workmain-notify.service --property=ActiveEnterTimestamp
```

Confirm the new `ActiveEnterTimestamp` postdates the merge commit before calling anything deployed.

**The CLI does not wait for the restart.** `workmain` is an editable install from the repository, so every `workmain` command runs whatever branch is checked out, in its own process. A live check made through the CLI passes on the working branch: where a spec has one that Ray runs, he runs it there, before `/closeout`. Only what the daemon runs — the T1–T6 triggers (`CLAUDE.md` § Trigger Terminology) and Slack Socket Mode — waits for the restart.

### 2.7 Session start checklist

1. `git status` — working directory clean.
2. `git branch` — confirm where you are.
3. Determine work type:
   - phase/multi-step → `feature/*` from `dev`
   - targeted application fix → `hotfix/*` from `main`
   - docs/process only → `chore/*` from `main`.
4. Create the branch **before** writing anything. A `hotfix/*` or `chore/*` branch is cut from `origin/main` after `git fetch` — `git checkout -b <branch> origin/main` — because pull requests merge on GitHub and a local `main` falls behind.
5. Never work directly on `main` or `dev`.

### 2.8 Never do

- Commit to `main`, or to `dev` beyond trivial post-merge version/changelog updates.
- Merge a feature branch straight to `main`, or merge `dev → main` locally.
- Merge the `dev → main` PR yourself — Ray does that.
- Skip the version bump, the tag, or the GitHub Release on a merge to `main` that carries application code. A `chore/*` merge carries none and takes none — §2.2.
- Combine hotfix and feature work on one branch.
- Write code before creating the branch.
- Leave a merged branch alive, or let `dev` sit ahead of `main`.
- Use `chore/*` for application code, `config/*`, `templates/*`, `tests/**`, or `CHANGELOG.md` — except under the `chore/*` exception or the operational-change exception in §2.2.
- Report a `dev` merge as deployed without a confirmed post-merge restart.
- Use `git commit --no-verify`.
