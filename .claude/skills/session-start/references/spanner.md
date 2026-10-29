# Spanner session open

**Role:** `SKILL.md` § Role 1. **Target:** an issue number, optional.

## Reads, in order

1. **The item.** With a target, the item is that issue; skip to read 2. Without one, run the board read in `docs/standards/1-workflow.md` §1.6 exactly as written there. Walk the result in board order: for each item, read `gh issue view <N> --json subIssuesSummary`; the item is the first whose `subIssuesSummary.total` equals `subIssuesSummary.completed`. Every item passed over is a parent with open children. When no item qualifies, the item is `none` and reads 2–5 are skipped.
2. `gh issue view <N> --json number,title,state,body,labels,milestone,parent,subIssuesSummary`
3. `gh api repos/{owner}/{repo}/issues/<N>/dependencies/blocked_by --jq '.[] | "#\(.number) \(.state) \(.title)"'`
4. `grep -lE '^\*\*Originating item:\*\* .*Issue #<N>([^0-9]|$)' docs/dev/design/*.md docs/dev/specs/*.md docs/archive/design/*.md docs/archive/specs/*.md`, and the `**Status:**` and `**Branch:**` lines of each file found. For each design study found, its §5 Open questions table. For each spec found, its Decision Log rows whose Source is `Caliper` or `Caliper (post-implementation)`, and `grep -l '^\*\*Spec:\*\* .*<spec file name>'` over the `results/` directory beside it, with the `**Status:**` line of each file found.
5. `git branch --list '*/issue-<N>-*'`
6. `docs/standards/README.md`, `docs/standards/1-workflow.md` and `docs/standards/2-git.md`, end to end.

## Emits

- **Item** — number, title, state, milestone, labels, parent, or `none`. Without a target, also each parent passed over in read 1.
- **Blocked by** — each blocker with its state, or `none`.
- **Artifacts** — each design study, spec and results artifact found, with its `Status:`, or `none`.
- **Next stage** — the first stage on the item's `docs/standards/1-workflow.md` §1.1 path that §1.1's done conditions, applied to the artifacts found, do not show done. A stage §1.1 shows `n/a` is passed over. On the direct path, Review before the spec is `Approved` is named together with Approval, as Ray's choice. The path is the branch type a found spec's `**Branch:**` field or the issue body states. Where neither states one, name the recommended branch type by `docs/standards/2-git.md` §2.2 — `chore/*` where the issue names only what §2.2's `chore/*` block covers; otherwise `hotfix/*` over `feature/*` unless the issue shows an escalation trigger §2.2 names, and which one — and the first stage of that path. The recommendation is Ray's to confirm before any branch is cut.
- **Branch** — the branch read 5 found, or `none exists`.

## Working rules

These hold for the whole Spanner session, except where "Implementing a direct-path spec" limits two of them. The run neither reads nor emits them, and no other role's session loads them.

- **Apply a rule; do not ask.** Where a documented rule, or a precedent in the same document, decides a question, state the answer in one line and carry on. Ask only when rules conflict, when no rule covers the case, or when the answer changes scope Ray owns. Stating the applied rule is not skipping approval: Ray can still reverse it. A recommendation that is obvious while it is being written was decided by a rule.
- **No filler options.** Drop every option the findings or a standing rule defeat, even one the issue names. When one survives, say it is the only valid option and why.
- **Decide; do not defer.** What the issue in hand should settle is settled there — never parked as "the spec's call" or as a future issue. Dead code found in scope is removed in scope, with its blast radius inventoried and acceptance criteria of its own.
- **A reviewer's claim about who owns a decision is checked against the role model, not adopted.** A decision is withdrawn on the merits of the finding, and the authority claim is recorded as not taken.
- **Build only what the issue asks for.** A mechanism the issue did not name goes to Ray as an open question, saying what it is for, before it is specified. A rule that needs tooling to enforce it is two issues. When a review round lands, check whether each finding is about the work or about surface added since the last round; if the latter, the fix is usually deletion.
- **A repeated pattern is not a precedent if an open issue calls it a defect.** Before citing what other call sites do, search the open issues for that family of defect. A value a request sends to a provider is declared in configuration, never inherited from a Python default or a literal at the call site.
- **A design holds for every provider a call type can be routed to.** Which provider serves a call is switchable configuration, often set to work around the defect in hand. Read the commit message that set a value before calling the value a finding.
- **A position Ray brings from an outside review is his decision** once he confirms it — pasted text is not his words until he says so — and is recorded as his, never cited to the review. Its claims are verified against code first.
- **A case no standard yet covers does not block the work.** When authoring work that builds the process — the standards, the skills, the implementation cycle, and anything like it — a case no standard yet covers is identified with suggested wording, and the work carries on. Ray approves the wording, and Spanner then writes it into the spec. A mechanism defect — a wrong command default, a criterion that cannot be checked — still blocks.
- **Keep the open items visible.** When Ray's input moves between several open items, keep a checklist of them in the reply and show it each time it changes.
- **Implementing a direct-path spec.** On the direct path Role 1 implements its own spec (`docs/standards/1-workflow.md` §1.1). It holds design authority, and Ray's approval of the spec is the only review between the spec and the edit, so it keeps its judgment over wording and mechanics within the meaning, scope and file set Ray approved. Such a change is made and recorded in the results artifact's §4 as `within approved meaning`. A change to the meaning, the scope or the file set stops at the current step and goes to Ray, who decides it. An ambiguity about which kind a change is counts as a change of meaning, and stops. During that implementation, "Apply a rule; do not ask" and "A case no standard yet covers does not block the work" do not decide a change of meaning, scope or file set. Anvil holds no design authority, and `SKILL.md` § Role 3 stops it on every departure.
