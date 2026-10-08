# Spanner session open

**Role:** `CLAUDE.md` § Role 1. **Target:** an issue number, optional.

## Reads, in order

1. **The item.** With a target, the item is that issue; skip to read 2. Without one, run the board read in `docs/DEVELOPMENT_STANDARDS.md` §1.6 exactly as written there. Walk the result in board order: for each item, read `gh issue view <N> --json subIssuesSummary`; the item is the first whose `subIssuesSummary.total` equals `subIssuesSummary.completed`. Every item passed over is a parent with open children. When no item qualifies, the item is `none` and reads 2–5 are skipped.
2. `gh issue view <N> --json number,title,state,body,labels,milestone,parent,subIssuesSummary`
3. `gh api repos/{owner}/{repo}/issues/<N>/dependencies/blocked_by --jq '.[] | "#\(.number) \(.state) \(.title)"'`
4. `grep -lE '^\*\*Originating item:\*\* .*Issue #<N>([^0-9]|$)' docs/dev/design/*.md docs/dev/specs/*.md`, and the `**Status:**` and `**Branch:**` lines of each file found.
5. `git branch --list '*/issue-<N>-*'`

## Emits

- **Item** — number, title, state, milestone, labels, parent, or `none`. Without a target, also each parent passed over in read 1.
- **Blocked by** — each blocker with its state, or `none`.
- **Artifacts** — each design study and spec found, with its `Status:`, or `none`.
- **Next stage** — the first stage of the `docs/DEVELOPMENT_STANDARDS.md` §1.1 path whose artifact read 4 did not find. The path is the branch type a found spec's `**Branch:**` field or the issue body states; where neither states one, say so and name the first stage of each path.
- **Branch** — the branch read 5 found, or `none exists`.
