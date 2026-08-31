# WorkmAIn Development Standards

How work gets built. `CLAUDE.md` owns who does what (the three-role model), what this project is (stack, architecture), and domain decisions (tag system, time format, trigger terminology, write-path map). This document owns everything else — process, git workflow, code patterns, database, CLI structure, and testing.

Read the relevant section before writing code. The only text here also stated in `CLAUDE.md` is its § Critical Rules subset; nothing else appears in both.

---

## 1. Development Workflow

### 1.1 Two paths through the cycle

There are two paths, and **the branch type is which one applies**. §2.7 step 3 already makes that the first decision of any session, so by the time work starts the path is settled and no further judgement is needed.

- **`feature/*` and `hotfix/*` → the full path.** The change alters application behaviour.
- **`chore/*` → the direct path.** §2.2 defines what `chore/*` covers: `docs/**`, standards documents, `.claude/`, and dev tooling that changes no application behaviour.

**Full path**

No spec is written without a read-only audit first. Recon produces a findings document in `docs/dev/design/`; decisions are made from it; only then is a spec written.

```text
RECON  →  ANALYSIS  →  SPEC  →  REVIEW  →  APPROVAL  →  IMPLEMENTATION  →  CLOSE-OUT
```

- **Recon** — read-only pass, verbatim findings, no fixes and no inline suggestions.
- **Analysis** — Ray plus Role 1 decide; decisions are logged.
- **Spec** — written to `docs/dev/specs/`.
- **Review** — Role 2 findings go back to Role 1, never forward to the implementer.
- **Approval** — Ray approves explicitly. No implementation without an approved spec.
- **Implementation** — Role 3, step by step, from the approved spec only.
- **Close-out** — Ray runs the `/closeout` skill against the branch being closed out, or `--branch <name>` for one already merged. It performs the merges, artifact completion, and whatever version bump, tag, Release and service restart its branch type requires, stopping at each authorization point it crosses. It composes the issue's closing comment and prints the command that would post it; posting the comment and closing the issue are Ray's, on the same principle as merging the `dev → main` PR.

**Direct path**

```text
SPEC  →  APPROVAL  →  IMPLEMENTATION  →  CLOSE-OUT
```

**All four are required.** Nothing on this path is optional except the two things named below as optional.

- **Spec** — written to `docs/dev/specs/`, from the same template. §1.2 states which sections it may omit and how it verifies existing state instead.
- **Approval** — Ray approves explicitly. No implementation without an approved spec.
- **Implementation** — Role 1, in the session that wrote the spec. A direct-path step quotes the exact replacement text, so there is nothing to hand off: a separate implementer would transcribe rather than implement, and a transcription is a new chance to get it wrong, not a second pair of eyes.
- **Close-out** — the same `/closeout` run, unchanged. A direct-path spec meets its preconditions as a full-path spec does.

**A recon is permitted on this path**, and earns its place when the change spans documents that may contradict each other — where a rule is stated in one place and cited or restated in others, and the change has to find every site before it can be specified. Run one where that is true; it produces a design artifact in `docs/dev/design/` exactly as on the full path.

**Where no recon is run, no design artifact exists** and the spec's `**Design study:**` field reads `n/a`. That is the stated form of a direct-path spec, not a requirement quietly skipped: `/closeout`'s `P5a` accepts `n/a` only on a `chore/*` spec, and fails every other missing or broken design-study citation exactly as before.

**What the direct path trades.** With no recon, no Role 2 pass and no separate implementer, **Ray's approval is the only review between the spec and the edit**, and scope that no acceptance criterion named is caught *after* implementation, by the results artifact's deviations table, rather than *before* it by recon and review. On a document that is recoverable — the text is there to read and the fix is another edit. On application code it is not, which is why the path is keyed on the branch type and not on how small the change looks.

### 1.2 Spec authoring rules

- Every claim about existing behaviour is verified against source at authoring time — cite file and symbol. Assertions that were not verified are the most common spec defect. This principle is the same on both paths; only its form differs.
  - **Full path:** the §2 verified-current-state table carries the citations.
  - **Direct path:** the §2 table is not required. The text being replaced is quoted inline in the step that replaces it, which *is* the verification — the claim and its evidence are the same lines, and a quote that no longer matches the file is caught the moment the edit is applied.
- Changes to an existing spec are surgical, not wholesale rewrites.
- Defects found during verification become their own hotfix, not sprint scope.
- Acceptance criteria must be mechanically testable. If an AC cannot be checked by running something, rewrite it until it can.
- A spec may map sub-ACs to the ACs on the originating issue using the numbering `ACn.m`, which is what lets close-out read the set mechanically. An unmapped sub-AC verifies nothing the issue asked for.
- At least one Role 2 review pass before a spec is approved — on the full path. On the direct path a Role 2 pass is optional and at Ray's discretion.

### 1.3 Issue discipline

- Work is tracked in GitHub Issues. State is GitHub's own — open or closed. There is no status vocabulary to maintain in prose, and no register or statistics table to keep in step.
- Labels carry area. `defect`/`gap` is the discriminator pair, applied only to issues with no milestone.
  - A **defect** is work the project asserted already worked — a spec acceptance criterion, a CHANGELOG entry, a man page — and does not. A **gap** is work never planned, documented, or designed.
  - A discriminator appearing inside a milestone means that work was pulled in from the unscheduled pool later, not planned as part of it.
- What each area label means is its description on GitHub, readable with `gh label list` — not enumerated here, since a prose list is a register that goes stale the first time a label is added.
- The Github type field is not utilized.
- A milestone carries the exit condition that closes it, and that condition must cover every issue in it.
- An issue must be independently verifiable on its own: split into sub-issues only where each piece leaves the repository in a coherent state its own acceptance criteria can verify. Where steps are strictly sequential and individually meaningless, they stay inline as steps in one issue — not split into a parent with children for its own sake.
- Verification of every AC against delivered code before marking an item complete is required. A spec's say-so is not evidence.

### 1.4 Steps and authorization points

A spec's steps are ordered work, defined below.

- **Steps.** Ordered work inside a spec. Committed individually, reviewable and revertible individually. No approval stop. A step ends with a commit, not with a request to continue.
- **Authorization points.** Attached to specific *actions* that are irreversible or reach outside the working tree.
  - This is a property of the action, so it does not scale with scope: a one-step issue can contain one and a twenty-step issue can contain none.
  - An authorization point is a hard stop — state what is about to happen, then wait for   Ray's explicit approval.
  - **The authorization set (anything not on this list is a step):**
    - Executing a DB migration
    - Deleting a GitHub object (issue, label, milestone, branch, release)
      - The branch entry covers a branch on `origin`. Deleting a local branch that was never pushed is not a GitHub object deletion — see §2.3.
    - Merging to `main`
    - Force-pushing any branch
    - Changing the run state of a live service beyond the carve-out below.
      - **Carve-out.** The post-merge service restart is not an authorization point. §2.6 requires it after every `feature/*` and `hotfix/*` merge to `dev`, so close-out performs it as a step. A restart that §2.6 does not require is not covered by this carve-out.

### 1.5 Documentation rules

- Dev artifacts always live in `docs/dev/<type>/` (never in the `docs/` root):
  - `design/` (design studies and recon)
  - `specs/`
  - `results/` (implementation results).
- **Filenames are subject-based** — no version suffix, no date. Artifacts are updated in place, so filenames never change and citations never break.
- **Every artifact carries exactly one `Status:` field, in its header block.** A status on a section rather than on the document is not a status; it is a leftover from the retired per-section vocabulary.
  - Specs carry `Draft`, `Approved`, `Shipped` or `Superseded`
  - Design and Results artifacts carry `Active`, `Shipped` or `Superseded`.
- While work is live, retirement is a status edit, not a file move. An artifact stays where it is, and where it is cited, for as long as it is being referenced.
  - **`docs/archive/`** holds artifacts whose work is complete. An artifact moves there when its issue closes out — `/closeout` performs the move as a step — and `docs/archive/<type>/` mirrors `docs/dev/<type>/`. It is kept for reference only, is never authoritative, and is always superseded by `docs/dev/design/`, `docs/dev/specs/` and `docs/dev/results/`. It is git-tracked, and filenames never change on the move, so citations to it stay resolvable.
  - Never cite an archived artifact as the basis for a current decision. If it still governs something, it has not finished being live and does not belong in the archive.
- **A pointer between artifacts of the same set is written relative; every other citation is written from the repository root.** The set is a spec, its design study and its results artifact — the three that are archived together.
  - `**Design study:** `../design/<file>.md`` from a spec, `**Spec:** `../specs/<file>_SPEC.md`` from a results artifact. Because `docs/archive/<type>/` mirrors `docs/dev/<type>/` and a set is archived whole, a relative pointer resolves before and after the move and is never repointed.
  - Everything else is a repo-root path: a standards section, an artifact from a different set, and any path inside a `git show <ref>:<path>` or quoted command output. The form is therefore the tell — a relative path is a pointer to resolve now, a repo-root path is either a target that does not move or a record of where something was at a stated moment.
- **Specs carry a Decision Log** — decisions and review findings with their resolution only.
  - Never a description of what changed in the document or a restatement of information already included elsewhere in the spec.
  - Design and results artifacts carry neither a decision log nor a version history.
- **Markdown is never hard-wrapped.** One line per paragraph, per list item, per table row — let the editor wrap it. A paragraph broken across source lines makes every later edit a reflow, and turns a one-word change into a multi-line diff nobody can review. `MD013` is off in `.markdownlint.json` for this reason.
- **No version headers or version-history blocks in any document.** Git is the version record. See §3.1 for the code equivalent.
- Each `docs/dev/` subdirectory holds a `_TEMPLATE_*.md` starting point. Templates are advisory — **template compliance is not a Role 2 review criterion.**

### 1.6 Sequencing

**The Github Project Board is the order.** Every issue joins the `WorkmAIn Queue` project at creation (§1.3), and its position there is the sequence. The next open item on the list is what comes next. There is no priority label and no rank field.

```bash
gh project item-list 3 --owner lockdwn20 --format json --limit 200 --query "is:open" \
  | jq -r '.items[] | "#\(.content.number)\t\(.milestone.title // "—")\t\(.title)"'
```

Items come back in board order. `milestone` and `labels` arrive on each item, so rank within a milestone and rank across milestones are the same single read — filter with `jq`, do not re-sort.

Ordering is Ray's. Position is set in the Web UI, and nothing in this repository writes to the board. The project's `Status` field is auto-populated by GitHub and cannot be removed; it is ignored.

**Preemption is expressed by position, and by nothing else.** Work that preempts the schedule is moved to the top of the board. **No general category of preempting work is defined.** Future preemption is decided case by case, by Ray, and takes effect as a move on the board — not as a label, a milestone, or a rule added here.

---

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

**hotfix/* → feature/* exception.**

- When a hotfix is a direct prerequisite for a feature branch and has no standalone value
  - Branch from `main`
  - Merge the hotfix/** into the feature/* branch before its step 1
  - Delete the hotfix/*
  - Document the deviation in the feature spec.
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

<body — what and why, not how. Files changed, decisions made, expected test count. Note any deviations from spec.>

Co-Authored-By: Claude
```

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`.

- This is the **only** commit format. Step context belongs in the body, not the subject — `feat(notes): converge write path` with `Step 3 of 7` in the body, never `Step 3: ...` as the subject.
- `git commit --no-verify` is **prohibited**. It bypasses commit validation.
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

### 2.7 Session start checklist

1. `git status` — working directory clean.
2. `git branch` — confirm where you are.
3. Determine work type:
   - phase/multi-step → `feature/*` from `dev`
   - targeted application fix → `hotfix/*` from `main`
   - docs/process only → `chore/*` from `main`.
4. Create the branch **before** writing anything.
5. Never work directly on `main` or `dev`.

### 2.8 Never do

- Commit to `main`, or to `dev` beyond trivial post-merge version/changelog updates.
- Merge a feature branch straight to `main`, or merge `dev → main` locally.
- Merge the `dev → main` PR yourself — Ray does that.
- Skip the version bump, the tag, or the GitHub Release on a merge to `main` that carries application code. A `chore/*` merge carries none and takes none — §2.2.
- Combine hotfix and feature work on one branch.
- Write code before creating the branch.
- Leave a merged branch alive, or let `dev` sit ahead of `main`.
- Use `chore/*` for application code, `config/*`, `templates/*`, `tests/**`, or `CHANGELOG.md` — except under the `chore/*` exception in §2.2.
- Report a `dev` merge as deployed without a confirmed post-merge restart.
- Use `git commit --no-verify`.

---

## 3. Code Standards

### 3.1 Module headers

- PEP 257 module docstring, description only. **No version, no date, no version-history block.** Git tags, `CHANGELOG.md`, and `workmain/__version__.py` are the version record.

  ```python
  """
  Provides tag parsing, validation, conversion, and display formatting.
  Tags are case-insensitive, normalized, and validated against config/tags.json.
  """
  ```

- *NOTE: Duplicating version history in every file was retired in v1.29.0.*

### 3.2 Import organization

- Standard library, then third-party, then local — blank line between groups.

  ```python
  from datetime import date, datetime
  from typing import List, Optional

  from sqlalchemy import func, and_, or_
  from sqlalchemy.orm import Session

  from workmain.database.models import Note, Meeting, Project
  ```

### 3.3 Singletons

- Module-level `_<name>_instance = None`, created on first call, accessed through a **descriptive** getter.

  ```python
  _tag_system_instance = None

  def get_tag_system() -> TagSystem:
      """Get singleton instance of TagSystem."""
      global _tag_system_instance
      if _tag_system_instance is None:
          _tag_system_instance = TagSystem()
      return _tag_system_instance
  ```

| Correct | Wrong |
| --- | --- |
| `get_tag_system()` | `get_tags()` |
| `get_template_loader()` | `get_loader()` |
| `get_template_validator()` | `get_validator()` |
| `get_style_adapter()` | `get_adapter()` |
| `get_encryption()` | `get_encryptor()` |

### 3.4 Package `__init__.py`

- Descriptive docstring, import classes *and* singleton getters, declare `__all__`. No `__version__` constant.

### 3.5 Type hints and docstrings

- Type hints on every parameter and return. Google-style docstrings on every public function and class.

  ```python
  def create(self, content: str, tags: List[str], project_id: Optional[int] = None) -> Note:
      """
      Create a new note.

      Args:
          content: Note content (clean text without hashtags)
          tags: List of full tag names (e.g., ['internal-only'])
          project_id: Optional project ID to link

      Returns:
          Created Note object
      """
  ```

### 3.6 Integration over separation

- Enhance an existing command file when adding to an existing group.
- New files are only for approved distinct command groups.

### 3.7 Security

- Never commit secrets.
- All secrets are stored as KV pairs in the .env and utilized through python-dotenv
- API keys come from the environment and are Fernet-encrypted at rest.
- `.env` and `~/.workmain/encryption.key` are `chmod 600`.

---

## 4. Database Standards

### 4.1 Session pattern

- `get_session()` is a **method on the `Database` class**, not a module-level function.
- Always `get_db()` first.

  ```python
  from workmain.database.connection import get_db

  db = get_db()
  session = db.get_session()
  try:
      repo = SomeRepository(session)
      # ... work ...
  finally:
      session.close()
  ```

### 4.2 Session discipline

- Objects must be re-queried inside the session that will modify them. Passing an ORM object across a session boundary causes **silent** persistence failures — no exception, no write.

- In daemon code, access ORM relationships inside the `try` block, before `session.close()`.

### 4.3 Repository pattern

- All data access goes through a repository.
- Models are SQLAlchemy declarative base.

  ```python
  class SomethingRepository:
      def __init__(self, session: Session):
          self.session = session

      def create(self, ...) -> Model:
          obj = Model(...)
          self.session.add(obj)
          self.session.commit()
          self.session.refresh(obj)
          return obj
  ```

### 4.4 PostgreSQL arrays

  ```python
  query.filter(Model.tags.op('&&')(['tag1', 'tag2']))   # overlap — shares any element
  query.filter(Model.tags.op('@>')(['tag1']))           # contains all
  query.filter(~Model.tags.op('@>')(['tag1']))          # does not contain
  ```

### 4.5 Migrations

- SQL files, numbered `NNN_name.sql`.
- **Execution is an authorization point** — see §1.4.
- The approval is at execution, not the spec that contains it.

### 4.6 Write-path convergence

- Note and paired-TimeEntry creation goes through the service layer only — see `CLAUDE.md` "§ Note Write-Path Convergence" design decision for the authoritative call map.

---

## 5. CLI Standards

- Governs everything in `workmain/cli/commands/`.
- Read before authoring or modifying a command.

### 5.1 Hierarchy

  ```text
  workmain <group> <subcommand> [ARGUMENT] [OPTIONS]
      │         │         │
    noun      verb    what/how
  ```

- Top-level standalone commands (`eod`, `status`, `today`) are permitted **only** for orchestration workflows that coordinate across multiple groups.
  - New ones need explicit justification and approval against that criterion.

### 5.2 Groups

- Groups are nouns. Verb-named groups are not permitted.
  - Plural for collections (`notes`, `meetings`, `reports`)
  - singular for a single integration (`clockify`, `gdocs`, `slack`) or for configuration/state (`schedule`, `notifications`).
  - If `<group> list` would be valid, it should be plural.
- One domain, one group. Never split a service across two top-level groups.
- Subgroups are permitted one level deep and follow the same noun rule, with three carve-outs:
  - **`set`** as a configuration namespace (`clients set active`, `providers set default`, `slack set channel`) — valid only when the parent has more than one configurable property and the subcommands are the property nouns.
  - **`sync`** with `push` / `pull` / `both` (`clockify sync push`).
  - **`upload`** with an artifact noun (`gdocs upload notes`).

### 5.3 Subcommands

- Imperative verbs.
- Use the standard vocabulary; do not invent synonyms.

| Action | Verb | Do not use |
| --- | --- | --- |
| Create a record | `add` | `create`, `new`, `insert` |
| Create a structured resource | `create` | `make`, `build`, `generate` |
| Modify a record | `edit` | `update`, `modify`, `change` |
| Remove a record | `delete` | `remove`, `rm`, `drop` |
| List | `list` | `ls`, `all`, `view` |
| Show one item in detail | `show` | `get`, `detail`, `inspect` |
| Write output to disk | `save` | `export`, `write`, `dump` |
| Transmit to a recipient | `send` | `post` (except Slack) |
| Render without saving | `preview` | `draft`, `render` |
| Read an external file | `import` | `load`, `ingest` |
| Verify credentials | `auth` | `login`, `connect` |
| Check integration state | `status` | `info`, `health`, `ping` |
| Archive to an external store | `upload` | `send`, `push`, `sync` |

- NOTES:
  - `upload` archives to a personal store
  - `send` addresses a recipient
  - Slack uses `post` (publishing to a channel, not addressing a recipient) with a required `PERIOD` argument.

- **Domain-specific verbs** are permitted only with prior approval, must be imperative, must be documented in `--help`, and must not duplicate a standard verb.
- Currently approved:

| Verb | Used by | Rationale |
| --- | --- | --- |
| `condense` | `meetings condense` | AI summarization |
| `rename` | `meetings rename` | Rename without full edit |
| `merge` | `meetings merge` | Combine two records |
| `track` | `meetings track` | Time entry from a meeting; valid as a *subcommand* verb, not as a group name |
| `log` | `notes log` | Bulk multi-note editor workflow, distinct from `add` |
| `register` / `unregister` / `validate` | `templates` | Template lifecycle and schema validation |
| `complete` | `tasks complete` | Lifecycle closure; `edit` does not imply finality |
| `dismiss` | `tasks dismiss` | Deliberate non-completion |
| `confirm` | `reports confirm` | Attestation without modification |
| `correct` | `reports correct` | Targeted correction with audit trail; distinct write target |
| `carryover` | `tasks carryover` | **DEPRECATED (v1.16.0)** — alias for `tasks list`; retires Phase 15 |

- Aliases are permitted for discoverability but must be documented in `--help`.
  - The canonical name must match the standard.

### 5.4 Arguments vs. options

- **Positional**
  - when the value is required and unambiguous.
  - Cap at two per command
  - beyond that, use named options for all but the primary target.
- **Option**
  - when the value is optional
  - is one of several independent modifiers
  - or needs a label to be understood.
- **Name-or-ID targeting is mandatory.**
  - Every command operating on a database record accepts either the ID or the name.
  - Exact name match resolves directly
  - multiple matches invoke the fuzzy picker with enough context (date, type, status) to disambiguate.
  - Build this in from the start — never as a retrofit.
- **Free-form text**
  - supports both inline (quoted positional) and an interactive prompt when omitted.
  - Use `click.prompt()` — raw `input()` is not permitted.

### 5.5 Flags

- Every option has a `--long-form` in lowercase-hyphenated words.
- Short forms are optional.

**Case convention:** lowercase short forms are for frequent flags; uppercase for the
less-used variant of a related concept (`-t/--tags` vs `-T/--time`). This pairing is
self-documenting.

Reserved across all commands — no flag may reuse these:

| Short | Long | Scope |
| --- | --- | --- |
| `-b` | `--start` | `meetings edit` |
| `-C` | `--category` | `time add`, `time edit` |
| `-c` | `--content` | `notes edit` |
| `-D` | `--description` | `time edit` |
| `-d` | `--date` | All |
| `-e` | `--end` | `meetings edit` |
| `-f` | `--source` / `--fallback` | `notes add` / `providers set default` |
| `-H` | `--history` | `notes list` with `--meeting` |
| `-h` | `--help` | Click built-in; never reassign |
| `-i` | `--show-ids` | Group level only |
| `-L` | `--duration` | `time edit` |
| `-l` | `--title` | `meetings edit`, `schedule *  add` |
| `-M` | `--month` | costs commands |
| `-m` | `--meeting` | `notes log`, `time add` |
| `-N` | `--notes` | `time add` |
| `-n` | `--limit` | List commands |
| `-P` | `--provider` | costs commands |
| `-p` | `--project` | `time add` |
| `-q` | `--silent` | Quiet-mode commands |
| `-R` | `--type` | `reports list` |
| `-S` | `--skip` | `eod` |
| `-s` | `--search` | Filter commands |
| `-T` | `--time` | `time add` (required there) |
| `-t` | `--tags` | All |

- Check any new short form against this table **and** every other flag on the same command to prevent conflicts.

- **Intentionally no short form** — safety-critical or infrequent, where friction is the point:
  - `--dry-run`
  - `--force`
  - `--send`
  - `--preview`
  - `--recurring`
  - `--until`
  - `--include-weekends`
  - `--cancelled`
  - `--status`
  - `--all`.

- Boolean flags use `is_flag=True`, never `type=bool`.
- Multi-value flags use `multiple=True` with comma-delimited input (`--tags ilo,cf`), never repeated flags.

### 5.6 Output

- Rich is required.
- Raw `print()` is not permitted in command files.

| Situation | Pattern |
| --- | --- |
| Single record | `rich.Panel`, title `"<Resource> #<id> — <descriptor>"` |
| Collection | `rich.Table`, consistent column ordering |
| Success | `console.print("[green]✓[/green] <past-tense action>")` |
| Warning | `console.print("[yellow]⚠[/yellow] <message>")` |
| Error | `console.print("[red]Error:[/red] <message>")` then `sys.exit(1)` |
| Dry run | Prefix `[dim][DRY RUN][/dim]`; no side effects |
| Prompt | `click.confirm()` / `click.prompt()` — never `input()` |

- Exit codes:
  - `0` success
  - `1` user-facing error or unhandled exception (after logging)
  - `2` integration error (API, auth).
    - Never expose a raw stack trace — catch at the command level and emit a clean message.

- Destructive or externally-sending commands must confirm unless `--force` is passed, and the prompt must state exactly what will happen.

- Every command needs a docstring serving as `--help`, with a one-line summary and at least one `Examples:` block.

### 5.7 Files and registration

- One top-level group per file, at `workmain/cli/commands/<group>.py`.
- All groups registered explicitly in `workmain/cli/interface.py`, ordered:

  ```text
  core data → output/generation → integrations → scheduling/automation → utilities.
  ```

---

## 6. Testing Standards

- pytest is the exclusive runner.
- `testpaths` in `pyproject.toml` resolves a bare `pytest` to the application suite.
- Non-application suites exist and are reached by explicit path — §6.3 is the owner of test placement.

  ```bash
  pytest                              # full suite
  pytest -v                           # verbose
  pytest tests/test_x.py::TestClass::test_name
  ```

- The current expected pass count is whatever `main` last shipped — read it from the most recent `CHANGELOG.md` entry or run `pytest --collect-only -q`.
- Do not transcribe a baseline into this or any other document; it goes stale immediately.

### 6.1 The `db_session` fixture

- Every test touching the database **must** take `db_session`.
- It redirects `commit()` to `flush()` and rolls back at teardown, so nothing persists.

| Action | Effect |
| --- | --- |
| `repo.create(...)` | Visible **within** the test session |
| `session.commit()` inside a repo | Redirected to `flush()` |
| Test ends | `rollback()` removes every write |
| Production DB | Unaffected, always |

- Never call `get_db()` or `db.get_session()` directly in a test.

- **Pitfall — fixture data is invisible to `CliRunner`.**
  - A CLI command invoked through `CliRunner` opens its *own* session and transaction, so rows flushed-but-uncommitted by `db_session` are never visible to it.
  - For any test that seeds data *and* invokes a CLI command, use a real committed session with explicit `tearDown` cleanup — the pattern in `tests/test_report_history.py`.

### 6.2 Writing a test

  ```python
  """
  <Feature> tests.

  Uses db_session fixture from conftest.py for full transaction isolation.
  """

  import pytest
  from workmain.database.repositories.<repo> import <Repo>


  class Test<Feature>:
      """<What this class tests>."""

      def test_<scenario>(self, db_session):
          repo = <Repo>(db_session)
          # arrange, act, assert — no cleanup needed
  ```

Rules:

1. Always use `db_session`.
2. **Sentinel dates** for anything asserting exact totals or counts — e.g. `date(2099, 1, 1)` — so production data cannot skew the result.
3. One assertion focus per test. Prefer several small tests over one large one.
4. No manual cleanup; the fixture handles it. The only exception is a test of deletion itself.
5. Group related tests in `class Test<Topic>` so `-k TestTopic` works.

### 6.3 Placement

| Goes in | What |
| --- | --- |
| `tests/` root | `test_<component>.py` — resolved by `testpaths` for a bare `pytest` |
| `tests/fixtures/` | Test data (JSON, CSV) — never Python test files |
| `tests/mocks/` | Fakes for external services — never test files |
| `scripts/` | Utilities and demos, never tests |
| `automation/` | Non-application dev tooling and its own tests (`*_test.py`), never mixed with the application suite — `testpaths` |

- `scripts-deprecated/` is excluded from collection.
  - Do not add to it and do not run it with pytest
  - if you need a diagnostic script, put it in `scripts/`.

### 6.4 Spec-named test file doesn't exist

- If a spec names a test file that isn't there, use the established file for that coverage and document the deviation.

---

## 7. File Placement

| Content | Location |
| --- | --- |
| CLI commands | `workmain/cli/commands/` |
| Repositories | `workmain/database/repositories/` |
| Models | `workmain/database/models.py` |
| Migrations | `workmain/database/migrations/NNN_name.sql` |
| Daemon / scheduler | `workmain/daemon/` |
| AI providers | `workmain/ai/providers/` |
| Workflows | `workmain/workflows/` |
| Services | `workmain/services/` |
| Utilities | `workmain/utils/` |
| Configs | `config/` |
| Templates | `templates/` |
| Staged report output | `staging/` — **not** `output/`, which does not exist |
| Tests / data / mocks | `tests/`, `tests/fixtures/`, `tests/mocks/` |
| Utility scripts | `scripts/` |
| Non-application dev tooling | `automation/` |
| Design studies and recon | `docs/dev/design/` |
| Specs | `docs/dev/specs/` |
| Implementation results | `docs/dev/results/` |

Dev artifacts always go in `docs/dev/<type>/`, never in the `docs/` root.
