# WorkmAIn Development Standards

How work gets built. `CLAUDE.md` owns who does what (the three-role model), what this
project is (stack, architecture), and domain decisions (tag system, time format, trigger
terminology, write-path map). This document owns everything else — process, git workflow,
code patterns, database, CLI structure, and testing.

Read the relevant section before writing code. The only text here also stated in
`CLAUDE.md` is its § Critical Rules subset; nothing else appears in both.

---

## 1. Development Workflow

### 1.1 Recon before spec

No spec is written without a read-only audit first. Recon produces a findings document in
`docs/dev/design/`; decisions are made from it; only then is a spec written.

```text
RECON  →  ANALYSIS  →  SPEC  →  REVIEW  →  APPROVAL  →  IMPLEMENTATION
```

- **Recon** — read-only pass, verbatim findings, no fixes and no inline suggestions.
- **Analysis** — Ray plus Role 1 decide; decisions are logged.
- **Spec** — written to `docs/dev/specs/`.
- **Review** — Role 2 findings go back to Role 1, never forward to the implementer.
- **Approval** — Ray approves explicitly. No implementation without an approved spec.
- **Implementation** — Role 3, step by step, from the approved spec only. Steps commit
  without a stop; authorization points are the hard stops — see §1.4.

### 1.2 Spec authoring rules

- Every claim about existing behaviour is verified against source at authoring time — cite
  file and symbol. Assertions that were not verified are the most common spec defect.
- Changes to an existing spec are surgical, not wholesale rewrites.
- Defects found during verification become their own hotfix, not sprint scope.
- Acceptance criteria must be mechanically testable. If an AC cannot be checked by running
  something, rewrite it until it can.
- At least one Role 2 review pass before a spec is approved.

### 1.3 Issue discipline

- Work is tracked in GitHub Issues. State is GitHub's own — open or closed. There is no
  status vocabulary to maintain in prose, and no register or statistics table to keep in
  step.
- Labels carry area. `bug`/`enhancement` is the type discriminator, applied *only* to
  issues with no milestone — so a type label appearing inside a milestone means that work
  was pulled in later, not planned as part of it. What each label means beyond that is its
  description on GitHub, readable with `gh label list` — not enumerated here, since a
  prose list is a register that goes stale the first time a label is added.
- A milestone carries the exit condition that closes it, and that condition must cover
  every issue in it.
- An issue must be independently verifiable on its own: split into sub-issues only where
  each piece leaves the repository in a coherent state its own acceptance criteria can
  verify. Where steps are strictly sequential and individually meaningless, they stay
  inline as steps in one issue — not split into a parent with children for its own sake.
- **Verify every AC against delivered code before marking an item complete.** Item 32 was
  marked complete in Phase 13 Sprint 2 (v1.21.0) with all four of its acceptance criteria
  unmet, and had to be reopened eleven days later when the gap was noticed. The work
  actually landed in Ops_Config_Correction_Sprint (v1.24.0), via
  `TaskStatusRepository.set_forwarding_note()`. A spec's say-so is not evidence.

### 1.4 Steps and authorization points

A spec's §4 is ordered work, defined below.

- **Steps.** Ordered work inside a spec. Committed individually, reviewable and revertible
  individually. No approval stop. A step ends with a commit, not with a request to
  continue.
- **Authorization points.** Attached to specific *actions* that are irreversible or
  reach outside the working tree. This is a property of the action, so it does not scale
  with scope: a one-step issue can contain one and a twenty-step issue can contain none.
  An authorization point is a hard stop — state what is about to happen, then wait for
  Ray's explicit approval.
- **The authorization set.** Executing a DB migration; deleting a GitHub object (issue,
  label, milestone, branch, release); merging to `main`; force-pushing any branch; changing
  the run state of a live service beyond the carve-out below. Anything not on this list is
  a step.
- **Carve-out — the post-merge restart is not an authorization point.** §2.6 requires
  restarting `workmain-notify.service` after a merge to `dev`, and §2.8 forbids reporting a
  merge as deployed without it. That restart is a documented obligation, not a
  discretionary state change, so it is a step. The authorization set covers service state
  changes *other than* that restart.

### 1.5 Documentation rules

- Dev artifacts always live in `docs/dev/<type>/`, never in the `docs/` root: `design/`
  (design studies and recon), `specs/`, `results/` (implementation results).
- **Filenames are subject-based** — no version suffix, no date. Artifacts are updated in
  place, so filenames never change and citations never break.
- **Every artifact carries a `Status:` field** — `Active`, `Shipped`, or `Superseded`.
  - While work is live, retirement is a status edit, not a file move. An artifact stays
    where it is, and where it is cited, for as long as it is being referenced.
  - **`docs/archive/`** holds artifacts whose work is complete. Move an artifact there
    once it is finished and no longer a live reference — it is kept for reference only,
    is never authoritative, and is always superseded by the current `design/`, `specs/`,
    and `results/`. It is git-tracked, so citations to it stay resolvable.
  - Never cite an archived artifact as the basis for a current decision. If it still
    governs something, it has not finished being live and does not belong in the archive.
- **Specs carry a Decision Log** — decisions and review findings with their resolution,
  only.
  - Never a description of what changed in the document; git covers that.
  - Design and results artifacts carry neither a decision log nor a version history.
- **No version headers or version-history blocks in any document.** Git is the version
  record. See §3.1 for the code equivalent.
- Each `docs/dev/` subdirectory holds a `_TEMPLATE_*.md` starting point. Templates are
  advisory — **template compliance is not a Caliper review criterion.**
- Always create the spec in the correct subdirectory before writing any code.

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

### 2.2 Branch rules

**`main`**

- Never commit directly.
- Receives merges only from `dev` or `hotfix/*`.
- Every merge bumps `workmain/__version__.py` and updates `CHANGELOG.md`.
- Tag every merge: `git tag v<version>`.
- **The tag alone is not a release.** Every tag on `main` needs a GitHub Release object
  (`gh release create v<version> --generate-notes`), verified with `gh release view`.
  *Added because the step was silently skipped for v1.25.0, v1.25.1, and v1.26.0.*

**`dev`**

- Always equal to, or one feature ahead of, `main`.
- Direct commits permitted only for trivial version/changelog updates after a feature merge.
- **`dev → main` MUST go through a GitHub PR — never a local merge.** Push `dev`,
  `gh pr create`, verify on GitHub. **Ray merges the PR himself** — open it and stop.

**`feature/*`** — from `dev`, merges to `dev` only. One per phase. Delete immediately after merge.

**`hotfix/*`** — from `main`, merges to `main` then `dev`.

- Escalate to `feature/*` if the fix touches more than 3 **application** files
  (`workmain/**/*.py`, `config/*`, `templates/*`). Tests, `__version__.py`, and
  `CHANGELOG.md` are mandatory companions and do not count. *Clarified after the Item #58
  hotfix read as escalation-triggering at 8 total files despite being correctly scoped.*
- File count is a proxy, not the test. The real question is whether the fix is one
  traceable root cause. Bundled unrelated concerns escalate regardless of count.

**`chore/*`** — from `main`, merges to `main` then `dev`.

- For `docs/**`, standards documents, and dev tooling that changes no application behaviour
  (`.gitignore`, `.githooks/`, `.github/`, `automation/`, editor/CI config).
- **Exception:** a change to `workmain/**`, `tests/**`, or `scripts/**` may use `chore/*`
  if it is mechanically proven behaviour-neutral (e.g. AST-equality) *and* the governing
  spec states the proof method.
- **No version bump, no `CHANGELOG.md` entry, no tag, no Release.** A doc-only change is
  not an application release.
- Scope: one document, or one tightly-related set edited for a single reason.
- Backlog and checklist updates that document a branch's own just-shipped work ride that
  feature branch — not a separate `chore/*`, even though `docs/**` would qualify on path alone.

**Hotfix → feature exception.** When a hotfix is a direct prerequisite for a feature branch
and has no standalone value: branch from `main`, merge into the feature branch before its
step 1, delete it, and document the deviation in the feature spec. The version bump rides
the feature.

### 2.3 Branch deletion

Delete every branch, local and remote, immediately after merge. No exceptions. Tags and
`CHANGELOG.md` are the permanent record; a merged branch adds nothing.

### 2.4 Commit messages

```text
<type>(<scope>): <short description>

<body — what and why, not how. Files changed, decisions made, expected test count.
Note any deviations from spec.>

Co-Authored-By: Claude
```

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`.

- This is the **only** commit format. Step context belongs in the body, not the subject —
  `feat(notes): converge write path` with `Step 3 of 7` in the body, never `Step 3: ...`
  as the subject.
- `git commit --no-verify` is **prohibited**. It bypasses commit validation.

**Enforced by `.githooks/commit-msg`.** Enable it once per clone — it is not automatic,
because git does not track `.git/hooks/`:

```bash
git config core.hooksPath .githooks
```

The hook exempts merge, revert, and fixup/squash subjects, which git generates itself.
It validates format only — it cannot tell you a scope is wrong or a description is
useless. Do not work around a rejection with `--no-verify`; fix the subject.

### 2.5 Version bumps

| Merge type | Change | Example |
| --- | --- | --- |
| Hotfix → main | Patch | 1.3.0 → 1.3.1 |
| Feature/phase → dev → main | Minor | 1.3.1 → 1.4.0 |
| Breaking change | Major | 1.4.0 → 2.0.0 |

Update `workmain/__version__.py` and `CHANGELOG.md` together on every merge to `main`.

### 2.6 Deployment

`workmain-notify.service` (systemd `--user`) tracks **`dev`**, not `main`.

**Every `feature/*` and `hotfix/*` branch ends with a service restart.** The daemon loads
code once at process start, so a merge to `dev` is not deployed until it restarts.
`chore/*` carries no restart — it changes no application code.

```bash
systemctl --user restart workmain-notify.service
systemctl --user show workmain-notify.service --property=ActiveEnterTimestamp
```

Confirm the new `ActiveEnterTimestamp` postdates the merge commit before calling anything
deployed. *An apparent Item #58 regression traced to a daemon running continuously since
before the fix merged — the code was correct in `dev` and `main` the whole time.*

### 2.7 Session start checklist

1. `git status` — working directory clean.
2. `git branch` — confirm where you are.
3. Determine work type: phase/multi-step → `feature/*` from `dev`; targeted application
   fix → `hotfix/*` from `main`; docs/process only → `chore/*` from `main`.
4. Create the branch **before** writing anything.
5. Never work directly on `main` or `dev`.

### 2.8 Never do

- Commit to `main`, or to `dev` beyond trivial post-merge version/changelog updates.
- Merge a feature branch straight to `main`, or merge `dev → main` locally.
- Merge the `dev → main` PR yourself — Ray does that.
- Skip the version bump, the tag, or the GitHub Release on a merge to `main`.
- Combine hotfix and feature work on one branch.
- Write code before creating the branch.
- Leave a merged branch alive, or let `dev` sit ahead of `main`.
- Use `chore/*` for application code, `config/*`, `templates/*`, `tests/**`, or
  `CHANGELOG.md` — except under the proven-behaviour-neutral exception in §2.2.
- Report a `dev` merge as deployed without a confirmed post-merge restart.
- Use `git commit --no-verify`.

---

## 3. Code Standards

### 3.1 Module headers

PEP 257 module docstring, description only. **No version, no date, no version-history block.**
Git tags, `CHANGELOG.md`, and `workmain/__version__.py` are the version record.

```python
"""
Provides tag parsing, validation, conversion, and display formatting.
Tags are case-insensitive, normalized, and validated against config/tags.json.
"""
```

*Duplicating version history in every file invited drift and was retired in v1.29.0.*

### 3.2 Import organization

Standard library, then third-party, then local — blank line between groups.

```python
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from workmain.database.models import Note, Meeting, Project
```

### 3.3 Singletons

Module-level `_<name>_instance = None`, created on first call, accessed through a
**descriptive** getter.

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

Descriptive docstring, import classes *and* singleton getters, declare `__all__`.
No `__version__` constant.

### 3.5 Type hints and docstrings

Type hints on every parameter and return. Google-style docstrings on every public
function and class.

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

Enhance an existing command file when adding to an existing group. New files are only for
approved distinct command groups.

### 3.7 Security

Never commit secrets. API keys come from the environment and are Fernet-encrypted at rest.
`.env` and `~/.workmain/encryption.key` are `chmod 600`.

---

## 4. Database Standards

### 4.1 Session pattern

`get_session()` is a **method on the `Database` class**, not a module-level function.
Always `get_db()` first.

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

Objects must be re-queried inside the session that will modify them. Passing an ORM object
across a session boundary causes **silent** persistence failures — no exception, no write.

In daemon code, access ORM relationships inside the `try` block, before `session.close()`.

### 4.3 Repository pattern

All data access goes through a repository. Models are SQLAlchemy declarative base.

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

SQL files, numbered `NNN_name.sql`. **Execution is an authorization point** — see §1.4. The
approval is at execution, not the spec that contains it.

### 4.6 Write-path convergence

Note and paired-TimeEntry creation goes through the service layer only — see
`CLAUDE.md` § Note Write-Path Convergence for the authoritative call map.

---

## 5. CLI Standards

Governs everything in `workmain/cli/commands/`. Read before authoring or modifying a command.

### 5.1 Hierarchy

```text
workmain <group> <subcommand> [ARGUMENT] [OPTIONS]
    │         │         │
  noun      verb    what/how
```

Top-level standalone commands (`eod`, `status`, `today`) are permitted **only** for
orchestration workflows that coordinate across multiple groups. New ones need explicit
justification against that criterion.

### 5.2 Groups

- Groups are nouns. Verb-named groups are not permitted.
- Plural for collections (`notes`, `meetings`, `reports`); singular for a single
  integration (`clockify`, `gdocs`, `slack`) or for configuration/state (`schedule`,
  `notifications`). If `<group> list` would be valid, it should be plural.
- One domain, one group. Never split a service across two top-level groups.
- Subgroups are permitted one level deep and follow the same noun rule, with three carve-outs:
  - **`set`** as a configuration namespace (`clients set active`, `providers set default`,
    `slack set channel`) — valid only when the parent has more than one configurable
    property and the subcommands are the property nouns.
  - **`sync`** with `push` / `pull` / `both` (`clockify sync push`).
  - **`upload`** with an artifact noun (`gdocs upload notes`).

### 5.3 Subcommands

Imperative verbs. Use the standard vocabulary; do not invent synonyms.

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

`upload` archives to a personal store; `send` addresses a recipient. Slack uses `post`
(publishing to a channel, not addressing a recipient) with a required `PERIOD` argument.

**Domain-specific verbs** are permitted only with prior approval, must be imperative, must
be documented in `--help`, and must not duplicate a standard verb. Currently approved:

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

Aliases are permitted for discoverability but must be documented in `--help`. The canonical
name must match the standard.

### 5.4 Arguments vs. options

- **Positional** when the value is required and unambiguous. Cap at two per command;
  beyond that, use named options for all but the primary target.
- **Option** when the value is optional, is one of several independent modifiers, or needs
  a label to be understood.
- **Name-or-ID targeting is mandatory.** Every command operating on a database record
  accepts either the ID or the name. Exact name match resolves directly; multiple matches
  invoke the fuzzy picker with enough context (date, type, status) to disambiguate. Build
  this in from the start — never as a retrofit.
- **Free-form text** supports both inline (quoted positional) and an interactive prompt
  when omitted. Use `click.prompt()` — raw `input()` is not permitted.

### 5.5 Flags

Every option has a `--long-form` in lowercase-hyphenated words. Short forms are optional.

**Case convention:** lowercase short forms are for frequent flags; uppercase for the
less-used variant of a related concept (`-t/--tags` vs `-T/--time`). This pairing is
self-documenting.

Reserved across all commands — no flag may reuse these:

| Short | Long | Scope |
| --- | --- | --- |
| `-h` | `--help` | Click built-in; never reassign |
| `-t` / `-T` | `--tags` / `--time` | All / `time add` (required there) |
| `-n` / `-N` | `--limit` / `--notes` | List commands / `time add` |
| `-d` / `-D` | `--date` / `--description` | All / `time edit` |
| `-c` / `-C` | `--content` / `--category` | `notes edit` / `time add`, `time edit` |
| `-l` / `-L` | `--title` / `--duration` | `meetings edit`, `schedule *  add` / `time edit` |
| `-m` | `--meeting` | `notes log`, `time add` |
| `-p` / `-P` | `--project` / `--provider` | `time add` / costs commands |
| `-M` | `--month` | costs commands |
| `-s` | `--search` | Filter commands |
| `-q` | `--silent` | Quiet-mode commands |
| `-i` | `--show-ids` | Group level only |
| `-f` | `--source` / `--fallback` | `notes add` / `providers set default` |
| `-b` / `-e` | `--start` / `--end` | Ranged commands; "begin" avoids the `-s` conflict |
| `-H` | `--history` | `notes list` with `--meeting` |
| `-S` | `--skip` | `eod` |
| `-R` | `--type` | `reports list` |

Check any new short form against this table **and** every other flag on the same command.
If nothing unambiguous is available, omit it rather than create a conflict.

**Intentionally no short form** — safety-critical or infrequent, where friction is the point:
`--dry-run`, `--force`, `--send`, `--preview`, `--recurring`, `--until`,
`--include-weekends`, `--cancelled`, `--status`, `--all`.

Boolean flags use `is_flag=True`, never `type=bool`. Multi-value flags use `multiple=True`
with comma-delimited input (`--tags ilo,cf`), never repeated flags.

### 5.6 Output

Rich is required. Raw `print()` is not permitted in command files.

| Situation | Pattern |
| --- | --- |
| Single record | `rich.Panel`, title `"<Resource> #<id> — <descriptor>"` |
| Collection | `rich.Table`, consistent column ordering |
| Success | `console.print("[green]✓[/green] <past-tense action>")` |
| Warning | `console.print("[yellow]⚠[/yellow] <message>")` |
| Error | `console.print("[red]Error:[/red] <message>")` then `sys.exit(1)` |
| Dry run | Prefix `[dim][DRY RUN][/dim]`; no side effects |
| Prompt | `click.confirm()` / `click.prompt()` — never `input()` |

Exit codes: `0` success, `1` user-facing error or unhandled exception (after logging),
`2` integration error (API, auth). Never expose a raw stack trace — catch at the command
level and emit a clean message.

Destructive or externally-sending commands must confirm unless `--force` is passed, and the
prompt must state exactly what will happen.

Every command needs a docstring serving as `--help`, with a one-line summary and at least
one `Examples:` block.

### 5.7 Files and registration

One top-level group per file, at `workmain/cli/commands/<group>.py`. All groups registered
explicitly in `workmain/cli/interface.py`, ordered: core data → output/generation →
integrations → scheduling/automation → utilities.

---

## 6. Testing Standards

pytest is the exclusive runner. `testpaths` in `pyproject.toml` resolves a bare `pytest` to
the application suite. Non-application suites exist and are reached by explicit path — §6.3
is the owner of test placement.

```bash
pytest                              # full suite
pytest -v                           # verbose
pytest tests/test_x.py::TestClass::test_name
```

The current expected pass count is whatever `main` last shipped — read it from the most
recent `CHANGELOG.md` entry or run `pytest --collect-only -q`. Do not transcribe a baseline
into this document; it goes stale immediately.

### 6.1 The `db_session` fixture

Every test touching the database **must** take `db_session`. It redirects `commit()` to
`flush()` and rolls back at teardown, so nothing persists.

| Action | Effect |
| --- | --- |
| `repo.create(...)` | Visible **within** the test session |
| `session.commit()` inside a repo | Redirected to `flush()` |
| Test ends | `rollback()` removes every write |
| Production DB | Unaffected, always |

Never call `get_db()` or `db.get_session()` directly in a test.

**Pitfall — fixture data is invisible to `CliRunner`.** A CLI command invoked through
`CliRunner` opens its *own* session and transaction, so rows flushed-but-uncommitted by
`db_session` are never visible to it. For any test that seeds data *and* invokes a CLI
command, use a real committed session with explicit `tearDown` cleanup — the pattern in
`tests/test_report_history.py`. Confirmed by direct probe during Item #56.

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
2. **Sentinel dates** for anything asserting exact totals or counts — e.g.
   `date(2099, 1, 1)` — so production data cannot skew the result.
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
| `automation/` | Non-application dev tooling and its own tests (`*_test.py`), never mixed with the application suite — `testpaths` keeps a bare `pytest` on `tests/` only |

`scripts-deprecated/` is excluded from collection. Do not add to it and do not run it with
pytest; if you need a diagnostic script, put it in `scripts/`.

### 6.4 Spec-named test file doesn't exist

If a spec names a test file that isn't there, use the established file for that coverage,
document the deviation, and keep going. That is not a design question and does not stop
implementation.

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
