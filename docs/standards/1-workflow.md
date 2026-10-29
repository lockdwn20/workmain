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

- **Steps.** Ordered work inside a spec. Committed individually, reviewable and revertible individually. No approval stop: a step that goes as the spec writes it ends with a commit, not with a request to continue. A departure is the exception. Anvil stops on every departure before the step's commit (`.claude/skills/session-start/SKILL.md` § Role 3). Role 1, on its own direct-path spec, stops on one that changes the meaning, scope or file set Ray approved (`.claude/skills/session-start/references/spanner.md` § Working rules). A step that changes a signature, a required input or an invariant updates every caller in that step, or keeps the old call working, so each step's commit leaves the suite green.
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
