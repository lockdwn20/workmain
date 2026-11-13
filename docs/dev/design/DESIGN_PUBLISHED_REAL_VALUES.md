# Published Real Values — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261113
**Originating item:** Issue #276

---

## 1. Purpose

`CLAUDE.md` § Client Reference, the rule that nothing published from this repository contains a real client, workspace, channel, user, recipient or Drive value, was widened by #274. Values written before that are still published. #275's check (`automation/style_check.py`) reads only what a branch changes, so it does not find them. This study counts where they are now, and weighs removing them from the current tree only against removing them from history as well.

## 2. Scope of the read

Every count below was taken on 20261113 with the matcher #275 ships, `real_values` and `_value_patterns` in `automation/style_check.py`: each entry of `DEV_REAL_VALUES` in `.env`, matched in any letter case wherever the character on each side is absent or not an ASCII letter or digit. Values are named by their position in `DEV_REAL_VALUES`, as #275's report names them, and are never printed. `DEV_REAL_VALUES` listed 7 values when read.

Read:

- every tracked file on `origin/main` (`959c52c`), its path and its text
- the messages of every commit on `origin/main` and `origin/dev`, and of every commit any local ref reaches
- the diff of every commit any local ref reaches, for the first commit that adds a line holding each value
- the message of every annotated tag
- the refs `origin` publishes (`git ls-remote origin`) and the repository's fork count (`gh repo view`)
- published GitHub text, through GraphQL for issues and pull requests and REST for the rest: the title and body of all 216 issues and 60 pull requests; all 97 issue comments and 3 pull request comments; every pull request review body and review comment, of which there are none; every earlier version of each of these in its edit history (`userContentEdits`), 393 body versions and 2 comment versions, none of them deleted; the name and notes of all 67 Releases; every commit comment, of which there are none; and the 8 milestones, 27 labels and the repository's description, homepage and topics

No collection was cut off by a page limit. The wiki is enabled but has never been created (`git ls-remote` of its repository: not found), and Discussions are disabled.

Not read: the `WorkmAIn Queue` project's own fields, the contents of the one fork, and the commits of the one pull request head that is not in the local clone.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | Ten tracked files on `main` hold a value: nine under `docs/archive/` and `tests/test_slack_channel_config.py`. There are 40 line hits: value 1 on 6 lines, value 2 on 4, value 4 on 20, value 6 on 10. No file path holds a value. | Census of `origin/main` at `959c52c` | High |
| F2 | Of the nine `docs/archive/` files, `docs/archive/specs/OLLAMA_PROVIDER_ALIGNMENT_SPEC.md` is not in the issue's list. It holds value 1 at line 225. | Census of `origin/main` at `959c52c` | High |
| F3 | Value 1 is contained in values 2 and 3, and value 4 in value 6. A line holding value 2 or value 6 is therefore counted against two values. This is why value 1 and value 2, and value 4 and value 6, share lines in F1. | Containment test over `DEV_REAL_VALUES` | Low |
| F4 | `tests/test_slack_channel_config.py:186` asserts the workspace name. #214, open, replaces that test, and its criteria check the file for the workspace name (#214 body, criteria on `tests/test_slack.py` and `tests/test_slack_channel_config.py`). #214 is a `feature/*` change, so it reaches `main` only through the `dev → main` pull request. Until it does, #276's first criterion cannot hold on `main`. | #214 body, lines on `TestSlackSetWorkspace` | High |
| F5 | Five commit messages hold value 4, all on both `main` and `dev`: `98198cb` 20260512, `1789b0b` 20260522, `0ee9ebf` 20260522 (a merge commit), `e7c1255` 20260610, `3334ab9` 20260610. No other value appears in any message. 2,088 commits were read on `main` and `dev`, and 2,115 across all local refs, with the same five found. | Census of `git log origin/main origin/dev` and `git log --all` | High |
| F6 | The oldest commit that adds a line holding a value is `42f5950`, 20260304. Seventeen commits add such a line. A history rewrite that removes file contents starts at `42f5950` and gives new SHAs to 1,984 of the 2,088 commits on `main` and `dev`. A rewrite of messages alone starts at `98198cb` and gives new SHAs to 1,758. | `git rev-list --ancestry-path` from each root | High |
| F7 | All 117 tags descend from `42f5950`, and 75 descend from `98198cb`. 67 Releases sit on those tags. A rewrite from either root moves every tag it reaches, and a tag moved on `origin` is a force-push. | `git merge-base --is-ancestor` per tag; Releases API | High |
| F8 | Tracked files on `main` cite 596 commit SHAs, in 148 files, that a rewrite from `42f5950` would leave pointing at nothing. Issue bodies, comments and Release notes cite more. These were not counted. | Every 7–40 hex-digit token in the tree resolved against the rewritten set | High |
| F9 | `origin` publishes 60 `refs/pull/<N>/head` refs. 59 of them descend from `42f5950`; the other is not in the local clone. GitHub creates these refs itself and does not let a push change or delete them, so a force-push of `main` and `dev` leaves every old commit fetchable by SHA through them. GitHub's documentation for removing sensitive data says that only GitHub Support can remove these refs and the cached views. This is what that documentation states; it was not tested here. | `git ls-remote origin 'refs/pull/*/head'` | High |
| F10 | The repository has one fork. A fork's history is not reached by any change to this repository. The one pull request from a fork is #234. | `gh repo view --json forkCount` | Medium |
| F11 | Of all the published GitHub text §2 lists, only one item holds a value: the current body of PR #11 (merged 20260522), which holds value 4 where it names a config key. No earlier version in any edit history holds a value. The issue's census reports none of the 129 issues and pull requests it read holding a value. PR #11's body has no edit history yet, so editing it creates one, and the version before the edit holds the value. GitHub shows those earlier versions to anyone who opens the edit history, and the author can delete one. This is GitHub's documented behaviour and was not tested here. | GraphQL and REST census, 20261113 | High |
| F12 | A history rewrite reaches clones made before it, including every local clone used for this project, only if each one is re-cloned or reset. The issue body already states this. | Issue #276 body | — |

## 4. Options

Both options edit the current tree the same way. The files in F1 under `docs/archive/` have each value replaced with a placeholder that names where the value is held, as `CLAUDE.md` § Client Reference requires. They differ only in what happens to history.

### Option A — Clean the current tree; keep history

- **Approach:** Edit the nine `docs/archive/` files. Record the five commit messages in F5 in the spec's Decision Log as kept by Ray's decision, with the reason, which the issue's second criterion allows. No force-push and no authorization point.
- **Pros:** Every SHA, tag, Release and citation stays valid (F7, F8). There is nothing to coordinate with clones (F12). The work is a chore of nine documents.
- **Cons:** Every value stays in history from `42f5950` on, and in five messages, readable by anyone who clones the repository or browses an old commit.

### Option B — Rewrite history from `42f5950` and force-push

- **Approach:** Use `git filter-repo` with `--replace-text` and `--replace-message`, fed from `DEV_REAL_VALUES`, over `main`, `dev` and every tag. Force-push `main`, `dev` and the tags (each push is an authorization point, `docs/standards/1-workflow.md` §1.4). Ask GitHub Support to remove the pull request refs and cached views, which is Ray's to do (F9).
- **Pros:** A clone made after Support has acted holds no value anywhere.
- **Cons:** 1,984 commits get new SHAs (F6). All 117 tags move, under 67 Releases (F7). 596 SHA citations in 148 tracked files stop resolving, and more in issues and Release notes (F8). That record is what `docs/standards/2-git.md` §2.3 calls permanent. Until Support acts, nothing is removed from GitHub, because the pull request refs keep the old commits (F9). The fork, existing clones and outside caches keep everything regardless (F10, F12). The `--replace-text` match is not #275's bounded match, so the rewrite needs a check of its own that it replaced exactly the bounded matches.

A rewrite of messages alone is not offered. It costs 1,758 new SHAs and every tag from `98198cb` on (F6, F7), and it still leaves every value in file history.

**Recommendation:** Option A. Option B does not achieve what it is for. The values have been public since 20260304, and the fork, the clones and the caches keep them whatever this repository does. Removing them from GitHub itself depends on a Support request that this repository cannot make or verify. In exchange, B breaks the SHA record that `CHANGELOG.md`, every spec, every results artifact and every Release depend on. A stops the values being republished in the tree, which is what `CLAUDE.md` § Client Reference governs from here on. The issue's second criterion already provides for keeping a message by Ray's decision.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Option A or Option B? The choice decides whether the spec has authorization points and a GitHub Support request (§4). | Q1 answered 20261113 by Ray: Option A. History is kept, and the five commit messages in F5 are recorded as kept by this decision. |
| Q2 | PR #11's body holds the client name (F11). Is the body edited in this issue, or carried to an issue of its own? Recommendation: in this issue, since it is the same rule and a single edit. The spec would add a criterion for it, and the issue body's criteria would be edited at close-out (`docs/standards/1-workflow.md` §1.2). Ray also deletes the earlier version from the body's edit history in the web UI, which nothing in this repository can do. | Q2 answered 20261113 by Ray: all published GitHub text is in this issue's scope, meaning every issue and pull request body and comment, every review comment, and all Release notes. Edit-history versions that hold a value are listed for Ray to delete by hand in the web UI. Git history, the fork and clones are out of scope. |
| Q3 | #214 owns the hit at `tests/test_slack_channel_config.py:186` and checks it (F4). Does #276 wait for #214, linked as `blocked_by` so that the issue's first criterion holds on `main` exactly as worded? Or does the spec restate that criterion in its §5 to leave out the line #214's criterion checks, so that each value has one owner and #276 ships on its own? Recommendation: restate it. #214 already carries the check, and waiting holds a chore behind a feature release for a line this branch does not touch. | Q3 answered 20261113 by Ray: the spec restates the first criterion to leave `tests/test_slack_channel_config.py:186` to #214. |
| Q4 | Value 1 is matched at `docs/archive/specs/OLLAMA_PROVIDER_ALIGNMENT_SPEC.md:225` (F2). Is that line reworded, or does value 1 come out of `DEV_REAL_VALUES`? The list is Ray's (`CLAUDE.md` § Client Reference). Recommendation: keep value 1 listed and reword the line. | Q4 answered 20261113 by Ray: value 1 stays listed and the line is reworded. The hit is a true positive. A census reports every match as a hit and does not classify it, and Ray decides any exception. |

## 6. Disposition

- Promoted to: `../specs/PUBLISHED_REAL_VALUES_SPEC.md`
- Superseded by:
