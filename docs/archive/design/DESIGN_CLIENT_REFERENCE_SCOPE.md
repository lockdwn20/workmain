# What § Client Reference forbids — Design Study

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261112
**Originating item:** Issue #274

---

## 1. Purpose

`CLAUDE.md` § Client Reference forbids writing one real value, the default client's name, into the repository. Issue #274 asks for a rule that covers every real client name and the real identifiers of internal-only data, the Slack workspace among them, and that states how development references each one. The repository is public (`gh repo view --json visibility` → `PUBLIC`), so whatever the rule fails to cover is published. This study measures what real values exist, where they are held, and where they already appear, because the rule's reach depends on those answers.

This document quotes no real value. It names where each is held and cites each appearance by file.

## 2. Scope of the read

Read at `f6dbee5` (`origin/main`), on `chore/issue-274-client-reference-scope`, 20261112.

- **Where real values are held:** the key names in `.env`, `~/.workmain/integrations/slack/config.json`, and the columns of `workmain/database/models.py` that hold names, channels, addresses or external IDs.
- **Searched for each real value** (case-insensitive; the client name also with a word boundary, because it is three characters): every tracked file by `git grep`, excluding `scripts/baseline/` (`CLAUDE.md` § Common Pitfalls restricts it until #188 ships); every commit message on every ref; the title, body and comments of every issue and pull request (`gh issue list --state all`, 129 read of 129).
- **Searched for every statement of the rule:** `CLAUDE.md`, `docs/standards/`, `.claude/`, `.github/`, `docs/dev/`, `automation/`, `.env.example`.
- **Not read:** `~/.workmain/` files other than the Slack config, and `.env` values other than the ones named in F2. None of them holds a name or identifier of a client, a channel or a person.

## 3. Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | The rule has one statement, and it names one value: "During development, reference the default client via `WORKMAIN_DEFAULT_CLIENT` in `.env` — never the actual client name." No other document states or cites it. `.env.example:38` declares the key with the comment "Name of your first client", which states no rule. | `CLAUDE.md:158–160`; `grep -rnI -iE 'Client Reference\|WORKMAIN_DEFAULT_CLIENT\|real (client\|workspace\|name)\|actual client'` over the set in §2. | — |
| F2 | Real names and identifiers are held in three places. `.env`: `WORKMAIN_DEFAULT_CLIENT`, `USER_FULL_NAME`, `GDRIVE_TIMECARDS_ROOT`. `~/.workmain/integrations/slack/config.json`: `workspace_name`, `operator_user_id`. The database: `clients.name`, `clients.slack_channel`, `reports.slack_channel`, `reports.slack_workspace_name`, `recipients.email`, `gdrive_uploads.drive_folder_id`. The live database holds one client, and it is the default client. | `.env` key list; `jq 'paths(scalars)'` on the Slack config; `workmain/database/models.py:56`, `:58`, `:386`, `:387`, `:455`, `:502`; `select count(*), count(*) filter (where name = $WORKMAIN_DEFAULT_CLIENT) from clients` → `1\|1`. | — |
| F3 | The real Slack channel contains the client's name. A rule that forbids only the client's name therefore forbids the channel only by accident, and forbids nothing about a channel that does not contain it. | `clients.slack_channel` matched by a word-boundary search for `WORKMAIN_DEFAULT_CLIENT`. | Medium |
| F4 | **Tracked files outside `docs/archive/`.** The workspace name is asserted at `tests/test_slack_channel_config.py:186`; open issue #214 already removes it. The operator's own name (`USER_FULL_NAME`) is `__author__` at `workmain/__version__.py:7` and the style's display name at `templates/style/writing_style.json:2`. No tracked file outside `docs/archive/` holds the client name, a channel, `operator_user_id`, a recipient address or a Drive folder ID. `GDRIVE_TIMECARDS_ROOT` holds a generic folder word that is also the code's own default at `workmain/cli/commands/gdocs.py:365`, `:440`, `:523`, `:603`; it identifies nothing. | `git grep -l -i -F` per value, `:!scripts/baseline`. | Low |
| F5 | **`docs/archive/`.** The client name is in 8 files, the channel in 4, the workspace name in 2, and the operator's name in 2 (author lines). | Same search. Files: `docs/archive/design/DESIGN_TIME_ENTRIES_REFACTOR_20260608_v1.2md`, `docs/archive/handoffs/PHASE11_GATE0_ASSESSMENT_20260512.md`, `SESSION_HANDOFF_PHASE11_5_COMPLETE_20260522.md`, `SESSION_HANDOFF_PHASE11_COMPLETE_20260512.md`, `SESSION_HANDOFF_PHASE8_COMPLETE.md`, `docs/archive/specs/PHASE11_5_DISTRIBUTION_SPEC_v1_4.md`, `PHASE13_DB_SCHEMA_REFACTOR_SPRINT_SPEC_v1_2.md`, `PHASE6_DISCOVERY_RESULTS.md`. | Medium — out of scope |
| F6 | **Text published outside tracked files.** Five commit messages name the client: `98198cb`, `0ee9ebf`, `1789b0b`, `e7c1255`, `3334ab9` (20260512–20260610). No issue or pull request title, body or comment holds any real value from F2. A tracked-file rule does not reach a commit message, an issue or a pull request, and all three are public here. | `git log --all -i -w -F --grep`; `jq` over `gh issue list --state all --json number,title,body,comments`. | Medium |
| F7 | **How real values are already referenced.** #271 replaced real test values with invented ones (`"test-workspace"`, `#test-client-channel`) and its design study cited each real value by where it is held, never quoting it. The current rule's "reference … via `WORKMAIN_DEFAULT_CLIENT`" cannot mean a test reads `.env`: a test that reads live configuration is what #214 is removing from `TestSlackSetWorkspace`. | `docs/archive/specs/TEST_REAL_CLIENT_NAME_SPEC.md` DR1 and step 2; `docs/archive/design/DESIGN_TEST_REAL_CLIENT_NAME.md` §1, Q4. | — |

Every finding was checked against source or live data on the date above.

**Out of scope (F5, F6).** Removing the real values already published is not #274, which is a rule for what is written from now on. An issue for it needs: the 8 `docs/archive/` files and the 5 commit messages, with acceptance criteria that no tracked file and no commit message on `main` or `dev` holds a real value the rule covers. Rewriting commit messages rewrites history and force-pushes `main` and `dev`, an authorization point (`docs/standards/1-workflow.md` §1.4), and does not reach clones or forks already made. No open issue covers it (searched: `client name`, `workspace`, `archive`, `real name`, `slack channel`, `history`). Whether it is opened is Ray's.

## 4. Options

### What the rule covers (Q1)

**Option A — a list.** Every client's real name and the real Slack workspace name, as the issue names them.

- **Pros:** the narrowest change that meets the issue's first criterion.
- **Cons:** F2 shows a channel, a Slack user ID, a recipient address and a Drive folder ID held beside them, none of them named. F3 shows the channel is covered today only because it happens to contain the client's name. The next one written is the same hole #274 was opened for.

**Option B — a class, with the list as examples.** A real value is any value held in `.env`, `~/.workmain/` or the database that names or identifies a client, or identifies the operator's Slack workspace, its channels or users, a report recipient, or a Drive location. Client names and the workspace name are given as examples, not as the definition.

- **Pros:** covers every value in F2 and every one added later in the same places. Stating a rule by class rather than by list follows #134 (`docs/archive/specs/PROCESS_RULE_HOME_SPEC.md` Decision Log, 20260904) and `docs/standards/1-workflow.md` §1.5, which forbids lists kept by hand.
- **Cons:** the reader judges whether a value "identifies" something. F4's generic Drive folder word shows a held value that identifies nothing; Option B does not cover it, and should not.

**Recommendation:** B. Run over the live set (F4–F6), it refuses nothing outside `docs/archive/` and the commit history except the operator's own name, which Q2 decides, and the workspace assertion #214 already removes.

### How each is referenced

Only one form survives F7, so it is not an open question. The rule states it:

- **In a test or fixture:** an invented value that does not resemble the real one. A test never reads the real value from `.env`, `~/.workmain/` or the live database.
- **In any other text** (a document, a comment, a commit message): the place the value is held, which is the `.env` key, the `~/.workmain/` file and key, or the table and column. Never the value.

### Enforcement

Ray, 20261112: the problem exists only because the application is in live use while it is developed. Whatever is put in place serves that period and is removed after it. The real values the rule covers are listed in a `.env` key that `.env.example` does not declare, so it is local to development and outside the application's configuration contract. A check in `automation/` reads that key, and can run as part of `automation/style_check.py`, which close-out already runs (`.claude/skills/closeout/SKILL.md` P7).

`automation/style_check.py` checks only the lines a branch changed against its base, and already skips `docs/archive/`, so F5's values do not trip it. Working branches are never pushed (`docs/standards/2-git.md` §2.3), so a hit at close-out is fixed on the branch before anything is published, including the branch's own commit messages; rewording a local branch is not a force-push of `main` or `dev`.

The check is tooling, so it is an issue of its own. #274 states the rule and names the key; the second issue builds the check.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | The current rule forbids writing only the default client's name (F1). F2 shows real channels, Slack user IDs, recipient addresses and Drive folder IDs held beside the names #274 lists. Should the rule list what it forbids (A), or state a class with that list as examples (B)? §4 sets out both. Recommendation: B. | Ray, 20261112: B. The `.env` list (§4 Enforcement) is what the check reads; the class says what belongs in it. |
| Q2 | The operator's own name, `USER_FULL_NAME` in `.env`, is written as `__author__` at `workmain/__version__.py:7` and as the style's display name at `templates/style/writing_style.json:2` (F4). Under Option B it identifies a person in the operator's workspace. Should the rule exclude the operator's own name used as authorship or attribution (A), or cover it, which makes those two lines a finding for a separate issue (B)? Recommendation: A. It is attribution the operator wrote on purpose, not data the application processes. | Ray, 20261112: A. His name stays where it is. |
| Q3 | The issue's rule reaches tracked files. The repository is public, and five commit messages already name the client (F6). Issues and pull requests are public too, and are written by the same sessions. Should the rule reach only tracked files (A), or every text published from this repository: tracked files, commit messages, and issue and pull request text (B)? Recommendation: B. The exposure is the same, and F6 shows a commit message is where it has already happened. | Ray, 20261112: B. The check (§4 Enforcement) covers tracked files and the branch's commit messages; issue and pull request text is covered by the rule alone. |
| Q4 | Per §4 Enforcement, the rule exists only while the application is in live use during development, and is removed after. Should the rule state that reason, so the condition for removing it is readable where the rule is? | Ray, 20261112: settled on the rule's wording, in the spec. |
| Q5 | What is the `.env` key that lists the real values called? | Ray, 20261112: `DEV_REAL_VALUES`. No `WORKMAIN_` prefix, because the application never reads it. |

## 6. Disposition

- Promoted to: issue #275 (the check, §4 Enforcement)
- Superseded by:
