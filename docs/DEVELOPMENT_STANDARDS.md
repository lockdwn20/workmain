# WorkmAIn Development Standards

How work gets built. `.claude/skills/session-start/SKILL.md` owns who does what (the three-role model). `CLAUDE.md` owns what this project is (stack, architecture) and domain decisions (tag system, time format, trigger terminology, write-path map). This document owns everything else — process, git workflow, code patterns, database, CLI structure, and testing.

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
RECON  →  ANALYSIS  →  SPEC  →  REVIEW  →  APPROVAL  →  IMPLEMENTATION  →  IMPLEMENTATION REVIEW  →  CLOSE-OUT
```

- **Recon** — read-only pass, verbatim findings, no fixes and no inline suggestions. Where the findings turn up options, a trade-off, or questions whose answers change the work, the artifact is a design study instead: it adds the options with a recommendation and the open questions (`docs/dev/design/_TEMPLATE_DESIGN.md`), and it is written before the spec. Findings and options never go in the spec's Decision Log or only in chat, and each Decision Log decision cites the question it answers.
- **Analysis** — Ray plus Role 1 decide; decisions are logged.
- **Spec** — written to `docs/dev/specs/`.
- **Review** — Role 2 findings go back to Role 1, never forward to the implementer.
- **Approval** — Ray approves explicitly. No implementation without an approved spec.
- **Implementation** — Role 3, step by step, from the approved spec only.
- **Implementation review** — Role 2 reviews the delivered branch against the spec and its results artifact, on Ray's request in the Caliper session that reviewed the spec. `.claude/skills/session-start/references/caliper.md` § Post-implementation review states its reads and checks. Findings go back to Role 1, never forward to the implementer.
  - **An unstopped departure** is a change on the branch made without the stop it required: a change that traces to nothing in the spec, a results §4 row whose `Step stopped at` is `none`, or a `within approved meaning` change that altered the meaning, scope or file set Ray approved. Ray rules on each one, as the resolution of its Decision Log row, with one of two outcomes:
    - **Revert** — the change is reverted on the branch, and carried to an issue under §1.3 if it is still wanted.
    - **Keep** — the spec is amended so the change traces to it.
  - The ruling's home is the resolution of the finding's Decision Log row. Role 1 writes it there and writes the outcome into the spec, and the implementing role carries it out. Either way, results §4 lists the departure with `Step stopped at` set to `none`, so the record still shows the stop was skipped, and its `Resolved by` names Ray and the date of that Decision Log row.
- **Close-out** — Ray runs the `/closeout` skill against the branch being closed out, or `--branch <name>` for one already merged. It performs the merges, artifact completion, and whatever version bump, tag, Release and service restart its branch type requires, stopping at each authorization point it crosses. It composes the issue's closing comment and prints the command that would post it; posting the comment and closing the issue are Ray's, on the same principle as merging the `dev → main` PR.

**Direct path**

```text
SPEC  →  REVIEW*  →  APPROVAL  →  IMPLEMENTATION  →  IMPLEMENTATION REVIEW*  →  CLOSE-OUT
```

**The four unmarked stages are required.** The two marked `*` are the Role 2 review, which Ray calls for or not at the start (§1.2). Where they run, they are the full path's Review and Implementation review, done when the table below shows them done.

- **Spec** — written to `docs/dev/specs/`, from the same template. §1.2 states which sections it may omit and how it verifies existing state instead.
- **Approval** — Ray approves explicitly. No implementation without an approved spec.
- **Implementation** — Role 1, in the session that wrote the spec. A direct-path step quotes the exact replacement text, so there is nothing to hand off: a separate implementer would transcribe rather than implement, and a transcription is a new chance to get it wrong, not a second pair of eyes.
- **Close-out** — the same `/closeout` run, unchanged. A direct-path spec meets its preconditions as a full-path spec does.

**A design artifact is permitted on this path, and required where the work turns up options or questions whose answers change it** — the full path's Recon stage states what it then holds. A recon earns its place when the change spans documents that may contradict each other — where a rule is stated in one place and cited or restated in others, and the change has to find every site before it can be specified. Run one where that is true; it produces a design artifact in `docs/dev/design/` exactly as on the full path.

**Where no design artifact is written**, the spec's `**Design study:**` field reads `n/a`. That is the stated form of a direct-path spec, not a requirement quietly skipped: `/closeout`'s `P5a` accepts `n/a` only on a `chore/*` spec, and fails every other missing or broken design-study citation exactly as before.

**What the direct path trades.** With no recon, no required Role 2 pass and no separate implementer, **Ray's approval is the only review between the spec and the edit**, and scope that no acceptance criterion named is found only *during* implementation, when Role 1 stops on a change to the scope Ray approved (`.claude/skills/session-start/references/spanner.md` § Working rules), rather than *before* it by recon and review. On a document that is recoverable — the text is there to read and the fix is another edit. On application code it is not, which is why the path is keyed on the branch type and not on how small the change looks.

**What shows each stage done.** Each stage is done when its artifact or field shows it, and not before. A stage on both paths has the same condition on each, except where its row states a direct-path `n/a`.

| Stage | Done when |
| --- | --- |
| Recon | A `docs/dev/design/` artifact names the issue in its `**Originating item:**` field. |
| Analysis | Every row of that artifact's §5 Open questions carries an answer. |
| Spec | A `docs/dev/specs/` artifact names the issue in its `**Originating item:**` field. |
| Review | The spec's Decision Log carries at least one `Caliper` row, and every `Caliper` row has a resolution. A clean pass is the `No findings.` row `/session-start Caliper` emits for one. On the direct path the stage is `n/a` where the spec's `**Status:**` is `Approved` and it carries no `Caliper` row. |
| Approval | The spec's `**Status:**` is `Approved`. |
| Implementation | A results artifact in the `results/` directory beside the spec names it in its `**Spec:**` field. The implementing role writes it as its last implementation step. |
| Implementation review | The spec's Decision Log carries at least one `Caliper (post-implementation)` row, and every one has a resolution. A clean pass is the `No findings.` row the review emits for one. On the direct path the stage is `n/a` where the spec carries no `Caliper` row, because it runs only where the Review stage ran (§1.2). |
| Close-out | The spec's `**Status:**` is `Shipped`, and the artifact set is in `docs/archive/`. |

### 1.2 Spec authoring rules

- Every claim about existing behaviour is verified against source at authoring time — cite file and symbol. Assertions that were not verified are the most common spec defect. This principle is the same on both paths; only its form differs.
  - **Full path:** the §2 verified-current-state table carries the citations.
  - **Direct path:** the §2 table is not required. The text being replaced is quoted inline in the step that replaces it, which *is* the verification — the claim and its evidence are the same lines, and a quote that no longer matches the file is caught the moment the edit is applied.
- **A contract change enumerates its call sites.** Where a spec changes a signature, a required input, or an invariant of something already called elsewhere, its §2 table lists every call site found by a search of the whole repository — `tests/` and `automation/` included — together with the search that found them, and an acceptance criterion covers the whole enumerated set. A call site that bypasses the usual entry point is still a call site. #79 gave the providers a required policy input, its §2 enumerated nothing that constructs a provider, and the seven construction sites outside `ProviderManager` broke without any criterion covering them (#130).
- A call site found by a name search is confirmed by reading what the call is made on: a same-named method on another object is not a caller. A claim that a method has no caller states that references by name (getattr, a method passed uncalled) were also searched.
- Changes to an existing spec are surgical, not wholesale rewrites.
- **A finding outside the spec's scope is not fixed in it.** Whoever finds it states what an issue for it needs — the defect or gap, and its acceptance criteria — and names any open issue it could join, found by §1.3's search. Ray decides whether it becomes its own issue, joins that one, or is bundled with others.
- **An issue's acceptance criteria validate the work; they do not design it.** They are written before the design exists. Design on the merits. Where the design makes a criterion wrong, the spec restates it in its §5, says the issue body needs the edit, and the edit is made at close-out. A conflict between the design and an issue's criterion is not an open question. A criterion's check must be able to produce the answer the criterion states: a search that cannot see every form of what it counts proves nothing.
- **A fix that establishes a method writes it into this document in the same spec**, with an acceptance criterion of its own, so the next author follows it. This holds where the issue itself calls a missing rule a gap to raise elsewhere. The spec measures the defect's full extent itself — every site, every condition — and never takes the issue's list as the census.
- **An expected failure a spec quotes is observed, never reasoned.** Its author runs each mutation in the working tree, reverts it with `git checkout -- <file>`, and quotes what happened. Each run uses a fresh `PYTHONPYCACHEPREFIX`, because restoring and re-mutating a file within one second at the same size reuses the previous mutation's `.pyc`. Each mutation's old text is a literal that occurs once in its file. The test seeds its own rows, so the mutation cannot pass on whatever the database holds.
- **A rule that refuses authored text is run over the live set it will judge before it is specified** — every open issue, every spec row, whatever the rule reads — and the result is recorded in the spec before its options go to Ray. A rule tried only on its own example can refuse correct text it was never shown. A rule that must tell a property's subject from the evidence for it is a reading, not a pattern.
- Acceptance criteria must be mechanically testable. If an AC cannot be checked by running something, rewrite it until it can.
- **A criterion names a property of the delivered system. The command is evidence for that property, not the criterion itself.** Write it as "*<property>*, checked by `<command>`" — not as "`<command>` returns zero hits" standing alone. A command is a proxy, and a proxy has many ways to read green, only one of which is the change that was wanted. Naming the property is what tells a reviewer, and an implementer, which of those ways is the work.
  - The same criterion, written both ways:
    - **Check as the criterion:** `grep -rn '^Version:' workmain/ --include='*.py'` returns zero hits.
    - **Property, with the check as evidence:** no Python module under `workmain/` carries a version header in its docstring — git is the version record (§3.1) — checked by `grep -rn '^Version:' workmain/ --include='*.py'` returning zero hits.
    - The first is satisfied by renaming the header to `Ver:`. The second is not, and the difference is readable at review time, before any code exists.
  - `docs/dev/specs/_TEMPLATE_SPEC.md` §5 carries the two as separate columns, `Criterion` and `How it is checked`. On an issue, `.github/ISSUE_TEMPLATE/issue.schema.json` carries them as separate fields, and `automation/issue_validator.py` refuses a criterion that states only a command. A criterion that passes the validator still has to meet this rule.
- **A criterion that verifies changed behaviour names the entry path it exercises.** Where more than one entry path reaches the change, the criteria cover the set, or state which paths are omitted and why. A green check through the one path that works is not coverage: #79's live check ran `workmain providers test claude`, which goes through `ProviderManager` — the one path the #130 defect could not reach.
- **Where a criterion is a property of a document rather than of running code, the check may be a stated reading by Ray.** It is still a check, and it still names what is being read: the section, and what the reader is reading it for. `docs/dev/specs/_TEMPLATE_SPEC.md` §5 states the same and cites here.
  - **A check that names Ray is Ray's sign-off.** The implementer records its results row as `Not met`, with `Awaiting Ray` as its evidence, never `Met` on its own reading or run. Once he has checked it, the row becomes `Met` with evidence in the form `Ray, <YYYYMMDD>: <what he read or ran>`.
- **The wording rule and the entry-path rule apply to criteria authored from here forward.** Criteria already written are not rewritten and no issue is reopened to reword one; there is no retrospective sweep of the queue.
- A spec may map sub-ACs to the ACs on the originating issue using the numbering `ACn.m`, which is what lets close-out read the set mechanically. An unmapped sub-AC verifies nothing the issue asked for.
- At least one Role 2 review pass before a spec is approved, and a post-implementation review before close-out (§1.1 Implementation review) — on the full path. On the direct path both are at Ray's discretion, decided once, at the start: the post-implementation review runs exactly when Ray had Role 2 review the spec.

### 1.3 Issue discipline

- Work is tracked in GitHub Issues. State is GitHub's own — open or closed. There is no status vocabulary to maintain in prose, and no register or statistics table to keep in step. Work is called an issue and cited by its number. "Backlog", "backlog item" and "item number" are retired terms and are not written into new text; a quote of existing text, and the filename `docs/archive/FEATURE_BACKLOG.md`, stay as they are.
- Labels carry area, and `defect`/`gap` is the label pair that says what an unscheduled issue is. An issue with no milestone carries exactly one of them.
  - A **defect** is work the project asserted already worked — a spec acceptance criterion, a CHANGELOG entry, a man page — and does not. A **gap** is work never planned, documented, or designed.
  - The pair is not removed when an issue is later pulled into a milestone. A milestone carrying one means that work came from the unscheduled pool rather than being planned as part of it.
- What each area label means is its description on GitHub, readable with `gh label list` — not enumerated here, since a prose list is a register that goes stale the first time a label is added.
- GitHub's native issue Type field is not used, and cannot be: Types are an organisation-level feature, so `Repository.issueTypes` is null for this repository and `gh issue create --type` is inert. `defect` and `gap` are ordinary labels and travel as `--label`.
- A milestone carries the exit condition that closes it, and that condition must cover every issue in it.
- An issue must be independently verifiable on its own: split into sub-issues only where each piece leaves the repository in a coherent state its own acceptance criteria can verify. Where steps are strictly sequential and individually meaningless, they stay inline as steps in one issue — not split into a parent with children for its own sake.
- **An issue is opened only for what no open issue already covers.** Before any issue is opened — while planning, at close-out, or to carry a finding or an unmet acceptance criterion forward — the open issues are searched for one covering the same defect or gap: `gh issue list --state open --search "<term>"` once for each symbol, file and behaviour the new issue would name, and every result read. A finding an open issue already covers is added to that issue's context or acceptance criteria, and a new issue carries only the rest. #182 was opened for four defects found at #181's close-out. Three were already open as #148, #149 and #155, and a design study had been written across all four before the overlap was found.
- **An issue is opened when its body is written, it is on the board, and its dependencies are linked.** It is added to the `WorkmAIn Queue` project at creation — `gh project item-add 3 --owner lockdwn20 --url <issue-url>` — and every real dependency is linked as a GitHub dependency, whichever way it runs: the new issue may wait on an open one, or an open one may wait on it. The link is made on the issue that waits — `gh api --method POST repos/lockdwn20/workmain/issues/<blocked>/dependencies/blocked_by -F issue_id=<the blocking issue's id>`. "Depends on #N" in prose is not a dependency: nothing reads it, and the board shows the issue as ready. Each is verified by reading it back, in both directions — the board read in §1.6, `gh api repos/lockdwn20/workmain/issues/<blocked>/dependencies/blocked_by` and `gh api repos/lockdwn20/workmain/issues/<blocker>/dependencies/blocking` — because `item-add` prints nothing on success.
- **An issue split by its design study takes its findings with it.** When a design study shows that its issue must be split into several issues, each new issue's write-up carries the study's findings and settled answers for that issue, so it can be worked on without the study, and each new issue gets a design study of its own. The originating issue's study is narrowed to the work that issue keeps. If the originating issue is left as a parent with no work of its own, its study is deleted, and git keeps its history. A spec cites only a design study written for its own issue, because `/closeout` archives a spec's design study along with the spec (§1.5).
- Verification of every AC against delivered code before marking an item complete is required. A spec's say-so is not evidence.

### 1.4 Steps and authorization points

A spec's steps are ordered work, defined below.

- **Steps.** Ordered work inside a spec. Committed individually, reviewable and revertible individually. No approval stop. A step ends with a commit, not with a request to continue. A step that changes a signature, a required input or an invariant updates every caller in that step, or keeps the old call working, so each step's commit leaves the suite green.
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
- **Nothing is proposed that has to be kept up by hand.** No list, register, count, status table or copy of state that lives somewhere authoritative goes into a document, a spec step, a criterion or a script. A test count, queue size, version or status written as currently true is stale on the next commit, and the next reader spends a turn reconciling it. The rule is stated, and the set is derived from its live source: `pytest --collect-only -q`, `gh issue list`, `gh label list`, `workmain/__version__.py`. An operational bound, such as a `--limit`, is an instruction to derive it, never a remembered number. A list found already in a document is deleted, not updated: needing an update is the sign it should not exist. A criterion that would need such a list checks instead that the rule is stated. A document that cannot be trusted is deleted, not annotated. A dated measurement with its evidence, such as a recon's suite count at recon time, is a record and stays.
- **A change to a rule searches the whole document set** — `CLAUDE.md`, this document, the skills and the templates — for every other statement of it, and corrects each one. A historical citation stays as written; only a live, forward-looking reference is repointed.
- **A document is written for a reader who has read nothing else.** An issue, a criterion and a design study's open question each stand alone. The facts they depend on are stated in them. A rule is stated in a sentence, and another document is cited as its checklist, never as its definition. What breaks, and who notices, is spelled out. A design study's question says whether the problem it asks about is real before framing it, and a finding that cites two files says which one has the problem and which is there for contrast. An ID — a finding, a question, a design rule — is used only inside the file that defines it; anywhere else the thing is stated or cited in full. A bare `§` is only ever a section of this document, wherever it is written; a section of any other document is cited with that document's name, and on its first reference in a document with what the section is. A reason is stated in terms the reader can check. An issue number may follow it as the record, but never stands in as the reason. An example is set out as an example, not woven into the rule, and is checked against the rest of this document before it goes in.
- **No version headers or version-history blocks in any document.** Git is the version record. See §3.1 for the code equivalent.
- **A process rule never travels with the code.** Text that ships alongside what it describes says what the thing does and what it requires. It never says what a person should do about that. `CLAUDE.md` and this document are the two homes for a process rule; per `CLAUDE.md`'s opening, everywhere else cites them. This bullet exists because `tests/test_ai_clients.py` stated that an environment variable would skip its live API tests. Two roles, in two sessions, read a statement of what the flag did as an instruction to set it, ran a modified command in place of the suite, and shipped four real failures to `main` and to the running daemon.
- Each `docs/dev/` subdirectory holds a `_TEMPLATE_*.md` starting point. Templates are advisory — **template compliance is not a Role 2 review criterion.**

### 1.6 Sequencing

**The Github Project Board is the order.** Every issue joins the `WorkmAIn Queue` project at creation (§1.3), and its position there is the sequence. The next open item on the list is what comes next. There is no priority label and no rank field.

```bash
gh project item-list 3 --owner lockdwn20 --format json --query "is:open" \
  --limit "$(gh project view 3 --owner lockdwn20 --format json --jq .items.totalCount)" \
  | jq -r '.items[] | "#\(.content.number)\t\(.milestone.title // "—")\t\(.title)"'
```

Items come back in board order. `milestone` and `labels` arrive on each item, so rank within a milestone and rank across milestones are the same single read — filter with `jq`, do not re-sort.

Ordering is Ray's. Position is set in the Web UI, and nothing in this repository changes it. Adding a new issue to the board (§1.3) is the one write, and it orders nothing. The limit is the board's own item count, because `item-list` cuts its output at `--limit` without saying so. The project's `Status` field is auto-populated by GitHub and cannot be removed; it is ignored.

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

---

## 3. Code Standards

### 3.1 Module headers

- PEP 257 module docstring: a one-line summary, then a paragraph describing what the module does and why. **No version, no date, no version-history block** — git tags, `CHANGELOG.md`, and `workmain/__version__.py` are the version record. **No terminal command, no instruction to set an environment variable, no command-line flag, no terminal invocation, no trigger for when to run something, and no inventory of the module's own contents.** Naming an environment variable the module reads, or the API call that yields an instance of it, is a description of what the module requires and how it is obtained, and belongs here. A command belongs to `argparse` or to a Click command's own docstring (§5.6), which is where a reader looking for it will be.

  ```python
  """
  Parses, validates, converts and formats tags for display.

  Tags are case-insensitive, are normalized on entry, and are validated
  against config/tags.json. Callers receive full names; short forms are an
  input convenience and are never stored.
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

### 3.4 Package `__init__.py`

- A package that exposes an API gets a §3.1 docstring, imports of its classes *and* singleton getters, and an `__all__` declaring them. A package that exposes nothing — a namespace holding modules that callers import directly — gets the §3.1 docstring and nothing else. Which one a package is, is a fact about it: if no caller writes `from <package> import <name>`, it exposes nothing, and inventing exports to satisfy this section is not conformance. No `__version__` constant in either.

### 3.5 Function and class docstrings

- **This section governs functions and classes. It does not govern module headers, which are §3.1's.** Type hints on every parameter and return. Google-style docstrings on every public function and class — `Args:`, `Returns:`, `Raises:`, `Attributes:`. Those blocks belong to a function or a class and never appear in a module header.

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
- Nothing encrypts secrets at rest; `.env` must be `chmod 600`.

### 3.8 Framework mechanisms first

- **Use the mechanism Python's standard library, Click, Rich or SQLAlchemy provides before writing your own.** Where two of them do the job, either meets this rule, unless another section names one.
- **A spec that writes its own records why.** Its Decision Log names the mechanism it set aside and the reason it does not fit.
- The library's version is tested and behaves the same in every caller. A hand-written version has to get every edge case right on its own, and each copy can get a different one wrong.

| Job | Written by hand | Use instead |
| --- | --- | --- |
| Ask for a number from 1 to `n` | A loop that converts and bounds-checks the input. One that rejects only `0` and values above `n` accepts `-1`, which Python reads as an index from the end of the list. | `click.prompt(..., type=click.IntRange(1, n))` |
| Restrict an option to fixed values | An `if value not in (...)` check in the command body | `type=click.Choice([...])` on the option |
| Parse a `YYYY-MM-DD` date | Splitting on `-` and building a `date` from the parts | `date.fromisoformat(value)` |
| Build a file path | Joining strings with `/` | `pathlib.Path(base) / name` |

---

## 4. Database Standards

### 4.1 Session pattern

- Application code under `workmain/` opens a session only through `DatabaseConnection.session_scope()`, reached through `get_db()`. The scope commits when its block exits normally, rolls back when an `Exception` leaves the block, and closes the session in every case.

  ```python
  from workmain.database.connection import get_db

  db = get_db()
  with db.session_scope() as session:
      repo = SomeRepository(session)
      # ... work ...
  ```

- **The code that opens a scope owns its unit of work.** It may commit inside the scope. Code it hands the session to — a repository, a service, an orchestrator such as `ActionExecutor` — reads and writes through that session and never commits it, rolls it back or opens another. Two exceptions: it may contain a failure in a savepoint (`session.begin_nested()`, below), and it records an outside action in a session of its own (§4.3).
- **The owner commits before it waits.** If the scope has written since its last commit, the owner commits immediately before it prompts, opens an editor, starts a child `workmain` process or performs an outside action. No transaction holding a write stays open across user input, a child process or a call to another system.
- `get_session()` is a method on `DatabaseConnection`, not a module-level function. In application code under `workmain/`, only `session_scope()` calls it; tests follow §6.1.
- **A handler that recovers from an exception sits outside the `with`, or outside a savepoint inside it.** A handler that wraps the `with` runs after the scope has rolled back. Inside the block, the guarded work runs in `with session.begin_nested():` and the handler wraps that, so a failure rolls back to the savepoint and the scope carries on. Nothing inside a savepoint commits: a commit there commits the whole transaction. A handler inside the block that swallows a database error without a savepoint leaves the transaction failed, and the scope's commit then raises.
- **An exception that is not an `Exception` skips both commit and rollback.** `SystemExit` (from `sys.exit()` or `raise SystemExit`) and `KeyboardInterrupt` derive only from `BaseException`, so the scope only closes the session and its uncommitted writes are discarded. `ctx.exit()` and `click.Abort` are `Exception`s and roll the scope back.

### 4.2 Session discipline

- Objects must be re-queried inside the session that will modify them. Passing an ORM object across a session boundary causes **silent** persistence failures — no exception, no write.

- No ORM object is read after its `session_scope()` block exits. The exit commit expires every loaded attribute, and a read afterwards raises `DetachedInstanceError`. Read the values the code after the block needs while the block is open.

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
          self.session.flush()
          self.session.refresh(obj)
          return obj
  ```

- **A repository method never commits.** It flushes after a write, so the row has its id and its database defaults, and later queries in the session see it.
- **A repository method that returns rows loads, with them, every related record a caller reads on each row.** A relationship is lazy by default. Reading one issues a query the first time for each row, or for each distinct related row of a many-to-one, so a list of N rows costs up to N + 1 queries. The method uses `contains_eager` where its query already joins the related table, `joinedload` for a many-to-one it doesn't join, and `selectinload` for a one-to-many. It loads only what its callers read. A caller that reads none of it still gets it, and pays one join or one query per call, which doesn't grow with the rows. A change that adds a per-row read of a relationship adds the loader to the method in the same change. §6.2 states how the loading is tested.
- **A write that records an outside action commits on its own.** A row that records something already done outside WorkmAIn's database — a provider call that has been billed, a file in Drive, a Slack message, an entry in Clockify — is written in its own session, opened with `get_db().record_scope()`, immediately after the action, independent of the command's unit of work, so a later failure in the command can't undo the record of something that can't be undone. `record_scope()` is `session_scope()` with a lock timeout, so a record that reaches a row another transaction holds fails instead of waiting.
  - It never writes or references a row the command's open transaction has written. A second session can't see an uncommitted row, and waits on a row the transaction has locked.
  - Its failure is never silent. Cost recording logs a warning and carries on. Every other record reports, on stderr, what happened outside, what was not recorded and what will repeat. The command's exit status doesn't change: the outside action succeeded, and a non-zero exit invites a rerun that would repeat it.
  - It is tested at the function that writes it (§6.1).

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
- A group's callback does no work. Called with no subcommand, a group prints its help, which Click does itself when the group does not set `invoke_without_command`. What a group would report about its own state is a `status` subcommand (§5.3).

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
- **A command converted to the renderer** (`workmain/cli/output.py`) parses its arguments with Click types (`workmain/cli/params.py`), calls a function in `workmain/services/` inside a `session_scope()` it owns, closes the scope, and passes the service's result, unchanged, to the `Renderer` it receives through `@pass_renderer`, with a view it declares as a module constant. It builds no rows and formats no values. It imports no Rich, calls no `click.echo` or `print()`, and has no `sys.exit`. It catches no exception only to report it: `WorkmAInGroup` reports an exception no command handled as `Error: <type>: <message>` on stderr with exit 1. Its group is declared with `cls=WorkmAInGroup`, so a `ServiceValidationError` reaches the user as Click's `Error: <message>` on stderr with exit 1. A service raises `IntegrationError` (`workmain/services/exceptions.py`) when a call to another system fails or is refused, and `WorkmAInGroup` reports it as `Error: <message>` on stderr with exit 3. A setting that is missing, such as an API key, is a `ServiceValidationError`, exit 1. A command whose service calls another system reads what it needs in its scope, closes it, and then calls the service's function for the outside action, which records the action in a scope of its own (§4.3). A result that can partly fail carries an `error`, which the service builds: the command renders the result, then raises the error when it is set. A command that asks before it writes calls the service's preview function in one scope and closes it, then renders the preview. With nothing to apply it calls `renderer.nothing_to_do()` and stops. Otherwise it asks the preview's question with `click.confirm()`. On yes it calls the service's apply function in a new scope and renders its result; on no it calls `renderer.cancelled()`. The service composes the question, which states what the apply will do, and the preview carries whether there is anything to apply and what the apply function needs, so the command decides none of them. **A converted command that reports an error never exits `0`.** A cancelled pick and a warning are not errors, and exit `0`.
- **A view.** A `CollectionView` names its noun, its columns and an optional hint shown when it is empty. A `Column` names a field of the result's row, a label, a kind and an optional `fmt`. A `RecordView` names its resource, the fields that give its id and descriptor, its `Field`s, and an optional body field. A `ReportView` names a result in parts: its noun, the field holding its totals and their `Field`s, its `Section`s (each a field of the result holding a `Page`, and the `CollectionView` for it), an optional hint, an optional field holding the result's warnings, and whether its totals print when no section has rows (`totals_when_empty`). `fmt` is a pure function from the module that owns the value's domain, used only in human layouts.
- **Column kinds.** A **key** holds a value of bounded length (an ID, date, time, status, count or amount) and is printed at full width, never wrapped or shortened. A **text** column holds everything else, names and paths included, and wraps at spaces, folding a word longer than the column. No value is cut. A value too long to scan in a collection, such as a report body, is not a column; the item's `show` command prints it.
- **Table or list.** The renderer prints a collection as a table while every key column fits at full width and the whole table is at most 30 lines. Otherwise it prints a list: one record per row, a blank line between records, one unwrapped `Label: value` line per column with the labels aligned. The limit is fixed rather than the terminal's height, so captured output lays out as a terminal does. A long list is read through `less` or `grep`.
- **Titles and empty results** are written by the renderer from the filters the service applied: `Tasks (20 of 25 found, status=active)`, and `No tasks found (status=active).` followed by the view's hint.
- **A record** is a panel titled `<Resource> #<id> — <descriptor>`, showing each field that has a value. `None`, `""` and an empty tuple are no value; `0` and `False` are values.
- **A report** prints a title from its noun and the result's filters, one aligned `Label: value` line per totals field, then each section that has rows, after a blank line, as a collection. When no section has rows, it prints the empty line a collection prints, and the view's hint, unless the view sets `totals_when_empty`: then it prints the title and totals. A report whose totals mean something with no rows, such as a status or a write that changed counts but listed nothing, sets it. It then prints each of the result's warnings as a `⚠` line on stderr, whether or not any section has rows. Called with `quiet=True`, for a command's `--silent`, it prints only the warnings.
- **Values** reach Rich as `Text`, never as markup, because Rich reads `[#85019]` as a style and drops it. A `datetime` prints `YYYY-MM-DD HH:MM`, a `date` `YYYY-MM-DD`, and an empty value `—`.
- **Lines** that are not a table or panel print with `soft_wrap=True`: Rich inserts no break, so a caller capturing the output receives each line whole. A panel prints without it, because a panel under `soft_wrap` cuts its content.
- **The picker.** When text matches several records, `Renderer.pick` numbers them by the table-or-list rule (a `#` column, or a `[n]` line opening each record), says `<n> of <total> shown — refine the search` when the service capped them, and asks `Select [1-N, or q to cancel]` through `PickParamType`. `q` cancels. Enter with nothing typed, a number outside the list or other text asks again. The service finds the candidates in one call and acts on the chosen ID in another, which re-reads the record.

| Situation | Pattern |
| --- | --- |
| Single record | `rich.Panel`, title `"<Resource> #<id> — <descriptor>"` |
| Collection | `rich.Table`, consistent column ordering |
| Success | `console.print("[green]✓[/green] <past-tense action>")` |
| Warning | `console.print("[yellow]⚠[/yellow] <message>")`. A warning that a calling process must receive, such as how a result was produced, goes through the stderr `err_console` from the Error row instead. |
| Error | `err_console.print("[red]Error:[/red] <message>")` on a `Console(stderr=True, soft_wrap=True)`, then `sys.exit()` with the code the exit-code list below gives. Written to stderr, unwrapped, so a caller capturing the command's output, such as the EOD workflow, receives the cause as one line. |
| Dry run | Prefix `[dim][DRY RUN][/dim]`; no side effects. A converted command passes `dry_run=True` to `Renderer.report`, which puts the prefix on the report's first line. |
| Prompt | `click.confirm()` / `click.prompt()` — never `input()` |

- Exit codes:
  - `0` success
  - `1` user-facing error or unhandled exception (after logging)
  - `2` usage error: an unknown option, a missing argument or a rejected value. Click exits `2` for these itself; no command chooses it.
  - `3` integration error (API, auth), raised as `IntegrationError` (the converted-command bullet above).
    - Never expose a raw stack trace. `WorkmAInGroup` turns an exception no command handled into one `Error:` line on stderr, exit 1. The traceback is logged at `DEBUG`: run the command again with `LOG_LEVEL=DEBUG` to see it.

- Destructive or externally-sending commands must confirm unless `--force` is passed, and the prompt must state exactly what will happen.

- Every Click command function needs a docstring, with a one-line summary and at least one `Examples:` block. That docstring *is* the `--help` output, so it is written for the person running the command and is the one place invocations and flags belong. It is not a module header — §3.1 governs those and excludes exactly this content.

### 5.7 Files and registration

- One top-level group per file, at `workmain/cli/commands/<group>.py`.
- All groups registered explicitly in `workmain/cli/interface.py`, ordered:

  ```text
  core data → output/generation → integrations → scheduling/automation → utilities.
  ```

---

## 6. Testing Standards

- pytest is the exclusive runner.
- **The application suite is a bare `pytest` from the repository root.** `testpaths` in `pyproject.toml` is what resolves it to `tests/`. No other invocation stands in for it unless a spec names the alternative and states why. That covers a path subset, a `-k` or `-m` filter, and an environment variable that changes what runs.
- Non-application suites, such as `pytest automation/`, are reached by their own path. Each is a separate suite, not an alternative to this one. §6.3 owns test placement.
- **A test reports what actually happened.** Passed means it ran and its assertions held. Failed means it ran and did not — an error, a timeout or a wrong answer. Skipped means it did not run because a precondition declared with `@pytest.mark.skipif` was absent; that is the only way a test is skipped, and it is decided before the test exercises anything. A test never reports passed without having run, which is what an early `return` does, and never reports skipped after it has run. A skip is never added to turn a red suite green. Four live API tests in `tests/test_ai_clients.py` returned early under `SKIP_API_TESTS=1`, counted as passed, and the failures they hid shipped to `main` (#130, #131).
- **Recorded test evidence states all three counts, in the form `<passed> passed, <failed> failed, <skipped> skipped`, and writes each one even when it is zero.** pytest counts a skipped test separately from a passed one, so a record without the skipped count can't show whether a run did less than the full suite.

  ```bash
  pytest                              # full suite
  pytest -v                           # verbose
  pytest tests/test_x.py::TestClass::test_name
  ```

- The current expected pass count is whatever `main` last shipped — read it from the most recent `CHANGELOG.md` entry or run `pytest --collect-only -q`.
- Do not transcribe a baseline into this or any other document; it goes stale immediately.

### 6.1 Test isolation from the database

- **Every test runs inside one database transaction that is rolled back when it ends.** The autouse fixture `_isolated_database` in `tests/conftest.py` binds the application's session factory (`DatabaseConnection.SessionLocal`) to a connection the fixture owns, inside a transaction it began, with SQLAlchemy's `join_transaction_mode="create_savepoint"`. No test requests it and no test can opt out of it.
- Every session any code opens through `get_db()` joins that transaction: the test's own, a command run through `CliRunner`, and application code the test reaches without naming it. They share one connection, so each sees what the others wrote.

| Action | Effect |
| --- | --- |
| `commit()` anywhere | Releases a savepoint. The rows stay visible to every session in the test; nothing reaches the database. |
| `rollback()` anywhere | Discards that session's writes since its last commit, and every commit a session opened after it made in the meantime. Rows written before it began survive. |
| Test ends | The transaction rolls back; every write is discarded. |
| Process killed mid-test | The transaction was never committed; PostgreSQL discards it when the connection drops. |

- **A test that seeds or reads takes `db_session`.** It is a session from the same factory, so a command or service the test then calls sees what the test seeded. Commit it freely. Never call `get_db()` or `db.get_session()` in a test. The one exception is `tests/test_database_isolation.py`, whose tests stand in for application code in order to test this fixture.
- **Hand application code a session only before that code opens its own.** Sessions sharing the connection must finish last-in, first-out, because releasing a savepoint also releases every savepoint opened after it. A test that builds an application object on `db_session` and then runs a command that opens its own session fails with `InvalidSavepointSpecification` at the command's commit. Let the command build the object from the session it opens, as `tests/test_cost_display.py`'s `TestMeetingsCondenseTokenLine` does.
- **A record committed inside another session's open transaction is discarded by that session's rollback in a test**, though in production it is on its own connection and survives. Test an outside-action record (§4.3) at the function that writes it: call it, fail a later scope, and assert the record through `db_session`.
- **Inject a database failure; never rely on one.** Patch the module's `get_db` to raise, as `tests/test_ai_costs.py` does. A test whose result depends on which rows happen to exist in the live database is wrong.
- **Leaving the transaction fails the test.** During a test `DatabaseConnection.close()` raises, and replacing `SessionLocal` fails the test at teardown. Code that builds its own engine is outside the fixture, and no test may reach it.
- **A child process is outside the transaction.** A test that reaches code which launches `workmain` (`workmain/utils/self_invoke.py`, `workmain/workflows/eod_workflow.py`) patches the launch.
- **Every session in a test shares one connection, so database work stays on the test's thread.** A test that reaches a step thread replaces `threading.Thread`, as `tests/test_orchestration.py` does.
- **Committed rows are visible.** The test's transaction sees everything already in the database, so a test that asserts exact totals or counts uses sentinel values (§6.2 rule 2).
- **A row lock lasts the whole test.** A test that updates an existing row, such as a `system_state` key or a live client, holds that row's lock until it ends, and a CLI write to the row waits for it. Seed a row of the test's own wherever the test allows.

### 6.2 Writing a test

  ```python
  """
  <Feature> tests.
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

1. Take `db_session` for any session the test uses (§6.1).
2. **Sentinel dates** for anything asserting exact totals or counts — e.g. `date(2099, 1, 1)` — so production data cannot skew the result.
3. One assertion focus per test. Prefer several small tests over one large one.
4. No manual cleanup; §6.1's rollback discards every write.
5. Group related tests in `class Test<Topic>` so `-k TestTopic` works.
6. **A test is a method of a plain class, and it takes what it needs as arguments.** It takes `db_session` for a session (rule 1), `tmp_path` for a directory (rule 7) and `caplog` for log records; anything else it needs, it builds in its own body. pytest hands a fixture only to a test that names it as an argument, so this is the one form in which every test can reach every fixture.
7. **A test's directory is `tmp_path`.** pytest creates it for the test and keeps only its last three runs, so a test has no directory to clean up and the suite leaves nothing behind.
8. **A test that builds a real `ProviderManager` states the routing it needs.** It passes the primary and fallback of every call type it exercises, and never relies on the routing in `config/ai_settings.json`, which `workmain providers set default` changes in ordinary use. A provider the test does not stub must not be reachable: `tests/mocks/stub_providers.py`'s `stubbed_manager` takes the routing as a required argument and makes every unstubbed provider raise.
9. **A test pins behaviour meant to stay.** It never exercises a path an open issue is about to remove or narrow; it proves the same property with inputs that issue leaves valid. Opening an issue that narrows behaviour includes rewriting the open criteria and tests that exercise the narrowed path, and both issues say why.

**Each layer has one kind of test.**

- **Service.** All behaviour is tested here. The test takes `db_session`, seeds rows on sentinel dates (rule 2), calls the service function, and asserts the result's fields or the exception it raises.
- **Repository loading.** A method that loads related records with its rows (§4.3) has a test in its repository's test file that counts SQL statements. The test seeds one row on one sentinel value and five rows on another. Each of the five points at its own related rows, because a lazy many-to-one costs one query per distinct related row, so five rows sharing one would count the same as one with no loading at all. For a one-to-many, each of the five parents has at least one child. Related tables that are empty in live data are seeded in the test. A method with no filter that a sentinel can narrow is counted twice, after seeding one row and again after seeding four more. The second count includes the first row and any live rows, and with the loading in place it doesn't depend on them. The test calls `db_session.expunge_all()` after seeding, so no related row is already in the session. It then counts with a `before_cursor_execute` listener on `db_session.connection()`, around the method call and a read, on each row, of every relationship the method loads, and the count is equal for one and for five. Every session in a test shares that connection (§6.1), so an outside-action record (§4.3) on the path is patched out of the count. That record keeps its own test at the function that writes it.
- **Renderer.** These are the only tests that read printed text, and they are in `tests/test_output.py`. The test builds a view and a result by hand and renders them through `Renderer(console=Console(file=io.StringIO(), width=N))`, with the width written in the test, so `COLUMNS` cannot change the outcome. A picker test feeds its answers through `CliRunner().isolation(input=...)`.
- **Click parameter types** are tested in `tests/test_cli_params.py`, by calling `convert` and by a usage-error exit through `CliRunner`.
- **Command.** The test runs the command through `CliRunner(mix_stderr=False).invoke(group, args, obj=renderer)`, where `renderer` is a `Mock(spec=Renderer)`, and with the service function patched (`patch.object(<service module>, "<function>", autospec=True)`). It asserts the arguments the service received, that the renderer received the declared view and the service's return value, and the exit code. It reads no printed text except an `Error:` line on `result.stderr`.
- **A command the EOD workflow runs as a child process has a second entry path, `run_workmain`.** §6.1 has a test patch the launch, so the command test covers only the `CliRunner` path. The EOD step that runs the command is covered by that step's own test in `tests/test_eod_workflow.py`, which asserts what the step does with the command's exit code and output.

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

---

## 7. File Placement

| Content | Location |
| --- | --- |
| CLI commands | `workmain/cli/commands/` |
| CLI output: the renderer, views and the group class (`WorkmAInGroup`) | `workmain/cli/output.py` |
| CLI argument types | `workmain/cli/params.py` |
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
