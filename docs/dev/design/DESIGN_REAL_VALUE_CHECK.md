# Real-Value Check in the Style Check — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261112
**Originating item:** Issue #275

---

## 1. Purpose

`CLAUDE.md` § Client Reference forbids writing a real value (a client's name, or an identifier of the operator's Slack workspace, channels or users, a report recipient or a Drive location) into anything published from this public repository, and names `DEV_REAL_VALUES` in `.env` as the list of those values. Nothing reads a branch for them, so a value written into a file or a commit message is found only after the merge publishes it. Issue #275 puts that check in `automation/style_check.py`. The issue leaves four questions open whose answers change the work: the format of `DEV_REAL_VALUES`, what the check does when it has no values to read, how a value is matched, and which changed files and texts it reads. This study records what the code and the live data show and recommends an answer to each.

## 2. Scope of the read

- `automation/style_check.py` and `automation/style_check_test.py`, end to end.
- Every caller of `automation/style_check.py`: `.claude/skills/closeout/SKILL.md` P7, `.claude/skills/session-start/references/anvil.md` § Working rules check 5, `.claude/skills/session-start/references/caliper.md` I6. Found by `grep -rn style_check` over the repository, `docs/archive/` excluded. There is no `.github/workflows/`.
- `.claude/skills/closeout/references/chore.md`, `feature.md` and `hotfix.md`, for what close-out writes and when.
- `.gitignore`, for which `SKIPPED` paths can reach a branch.
- `.env`'s `DEV_REAL_VALUES` line, read for its shape only. No value was printed or written.
- Every tracked file, and every commit message reachable from any ref, matched against the listed values three ways (§3 F6). Only counts and file locations were printed.
- How the application reads `.env`: `grep -rn 'load_dotenv\|dotenv_values' workmain automation scripts`.

Not read: issue and pull request text (the issue puts it out of scope), and untracked files other than as `changed_lines` reports them.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | **What the check reads today.** `changed_lines(base)` diffs the working tree against `git merge-base HEAD <base>` with `--diff-filter=AM`, adds every untracked file not ignored (`git ls-files --others --exclude-standard`) as wholly changed, and drops every path that starts with an entry of `SKIPPED`. `check(changes)` runs the per-file checks and keeps a violation only where its span touches a changed line. `main` prints `<path>:<line> — <message>` for each and exits 1 on any. Nothing in the module reads a commit message or the branch name. | `automation/style_check.py` `changed_lines`, `check`, `main`, `SKIPPED` | — |
| F2 | **`SKIPPED` is a style exemption list, and two of its entries are published text.** It holds `CHANGELOG.md`, `docs/archive/`, `scripts-deprecated/`, `staging/`. `scripts-deprecated/` is ignored (`.gitignore:82`) and `staging/`'s subfolders are ignored but for their `.gitkeep` files (`.gitignore:56-64`), so neither can carry a value into a commit. `CHANGELOG.md` and `docs/archive/` are tracked and published. In the documented process both are written only by `/closeout` after preflight P7: the archive `git mv` (step 2 of `chore.md` and `feature.md`, step 3 of `hotfix.md`) and the `CHANGELOG.md` section (`hotfix.md` step 1 on the branch, `feature.md` step 4 on `dev`). A hand edit to either on a working branch is not caught by any check today. | `automation/style_check.py` `SKIPPED`; `.gitignore`; `.claude/skills/closeout/references/*.md` | Low |
| F3 | **Who runs the check, and what each reads.** `/closeout` P7 reads only the exit code. Anvil runs it before each step's commit, so a step's own commit message is first read by the next run, and the last one (the results artifact's) by P7. Caliper's I6 runs it with `--base <parent>` in a temporary detached worktree of the branch. | `.claude/skills/closeout/SKILL.md:35`; `.claude/skills/session-start/references/anvil.md` check 5; `.claude/skills/session-start/references/caliper.md:52` | — |
| F4 | **A detached worktree has no `.env`.** `.env` is ignored (`.gitignore:37`), so `git worktree add` does not put it in the worktree, and `ROOT` (`Path(__file__).resolve().parent.parent`) resolves to the worktree. A check that reads `ROOT / ".env"` finds no file in Caliper's I6 run. The main working tree is `git rev-parse --path-format=absolute --git-common-dir`'s parent, in a worktree and in the main working tree alike. | `automation/style_check.py` `ROOT`; `.gitignore:37`; `caliper.md:52` | High — without handling, I6 cannot run the check |
| F5 | **`DEV_REAL_VALUES` as it stands.** `.env` defines it once, as a double-quoted, comma-separated list of 7 values, 3 to 14 characters long. No value contains a space or a comma, and none starts or ends with a character other than a letter, digit or underscore. One value is a prefix of another. | `.env` line 42, read for shape only | — |
| F6 | **How a value is matched, run over the live set.** Every tracked file and every commit message reachable from any ref was matched against the listed values case-insensitively, three ways: as a substring; bounded by `\w` (what `grep -w` and `\b` use, which counts `_` as part of a word); and bounded by letters and digits only. In tracked files the three find 42, 41 and 42 occurrences. The one difference is the 3-character value next to an underscore, at `docs/archive/handoffs/SESSION_HANDOFF_PHASE11_COMPLETE_20260512.md:122`: a `\w` boundary misses a name joined into a snake_case word. A case-sensitive match finds 10 of the 3-character value's 21 `\w`-bounded occurrences; the other 11 differ only in case, and all 21 are the client's name, in prose, in code and inside channel names. In commit messages all three find the same 5 commits, those `docs/archive/design/DESIGN_CLIENT_REFERENCE_SCOPE.md` F6 lists. No branch name matches. Today's set holds no case where a substring match finds a value inside an unrelated word; with a 3-character value, new text can. | Census script run 20261112, counts and locations only | High — decides what the check refuses |
| F7 | **One tracked file outside `docs/archive/` holds real values.** `tests/test_slack_channel_config.py:186` asserts the real Slack workspace name, which holds two listed values. #214's criterion "No slack test reads the live Slack config file or names the real Slack workspace" covers it. The check reports it only if a branch changes that line. | Census (F6); `gh issue view 214` | Medium — covered by #214, out of scope here |
| F8 | **How `.env` is read elsewhere.** The application reads it with `python-dotenv` (`requirements.txt:4`, `python-dotenv==1.0.0`), through `load_dotenv()` at `workmain/config_manager/loader.py:12` and `workmain/database/connection.py:14`. No module under `automation/` reads `.env` today. The standard library has no `.env` parser, so `docs/standards/3-code.md` §3.8 names no mechanism for the job; `dotenv.dotenv_values(path)` parses a file into a dict without touching `os.environ`, handling quoting, `export` and comments. | `requirements.txt:4`; `loader.py:12`; `connection.py:14` | — |
| F9 | **The branch name is published too.** Every merge is `--no-ff`, and the merge commit's subject names the branch (`docs/standards/2-git.md` §2.3), so a branch slug reaches `main` and `dev`. Branch names are `<type>/issue-<N>-<slug>` (§2.1), and the slug is written by the session. The issue's criteria cover changed lines and commit messages, not the branch name. | `docs/standards/2-git.md` §2.1, §2.3 | Low |
| F10 | **What P7 cannot reach.** Commits `/closeout` makes after P7 (the Shipped status and archive commits on the branch, the version and `CHANGELOG.md` commit) are written after the check runs. | `.claude/skills/closeout/references/*.md` | Low — out of scope |

Every finding was checked against source or live data on the date above.

## 4. Options

The recommendations below are each Q's; §5 asks them.

### Matching (Q3)

- **Option A — substring, case-insensitive.** Finds every occurrence on today's set. With a 3-character value it refuses any word that contains those letters, so new text is refused for ordinary words.
- **Option B — bounded by `\w`, case-insensitive.** What `grep -w` does. Misses a value joined to a word by `_` (F6: one real occurrence today).
- **Option C — bounded by letters and digits, case-insensitive.** A value matches where the character on each side, if any, is not a letter or digit. Finds every occurrence on today's set (F6), including snake_case, and refuses no ordinary word that merely contains the letters.

**Recommendation:** C. On today's set it matches substring exactly, and it is the only one of the three that is both complete on today's set and safe for a 3-character value in new text. Case-insensitive in all three, because 11 of 21 occurrences of the short value differ from it only in case (F6).

### No values to read (Q1)

- **Option A — fail.** No `.env`, no key, or an empty list: the check exits 1, and the report says the real-value check could not run and why.
- **Option B — pass with a notice.** The other checks run, the report says the real-value check did not run, and the exit code ignores it.

**Recommendation:** A. The check exists only while development runs against live data, and the only environment that runs it then is the one holding `.env` (F3: close-out, Anvil, Caliper, all on Ray's machine; no CI). A check that passes because it could not read its input reads green, and P7 reads only the exit code (F3), so a notice under B would not stop a merge. A needs F4 handled: `.env` is read from the main working tree, found through `git rev-parse --git-common-dir`, so Caliper's worktree run reads the same file.

### Which changed text (Q4)

- **Option A — the changed lines `changed_lines` returns,** `SKIPPED` applied.
- **Option B — every changed line in every changed path,** `SKIPPED` not applied. The real-value check takes the unfiltered set; the existing checks keep `SKIPPED`.

**Recommendation:** B. `SKIPPED` exists because history is not restyled (the module docstring: "CHANGELOG.md is history and is never checked"). That reason does not apply to a real value, which is published whatever file holds it, and `CHANGELOG.md` and `docs/archive/` are published (F2). The ignored entries cost nothing either way (F2). B changes `changed_lines`'s contract, so the spec enumerates its callers.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | When there is no value to check against (`.env` absent from the main working tree, the key absent, or the list empty), should the style check fail (A) or pass with a notice (B)? Recommendation: A, per §4 No values to read. Under A, `.env` is read from the main working tree, so Caliper's detached-worktree run (F4) reads it too. | Ray, 20261112: B, pass with a notice. Ray, 20261113: changed to A, the check fails. B was chosen to avoid the worktree problem (F4), but the spec kept the main-working-tree read anyway, so B saved nothing and left a lost or emptied key passing every branch. With that read every caller (Anvil, P7, Caliper's I6) finds the same `.env`, so A needs no special case. |
| Q2 | What is the format of `DEV_REAL_VALUES`? Recommendation: the form `.env` already holds (F5): one line, values separated by commas, whitespace around each value ignored, empty entries ignored, quoting as `.env` allows it, read with `dotenv.dotenv_values` (F8). A value cannot contain a comma. The alternative, a JSON array, allows any character but is harder to edit by hand and would mean rewriting the existing line. | Ray, 20261112: comma-separated, as `.env` holds it (F5). No value contains a comma. |
| Q3 | How is a value matched? Recommendation: Option C of §4 Matching: case-insensitive, and bounded only by letters and digits, so a value joined into a snake_case word is still found (F6). | Ray, 20261112: Option C, the only option once a `\w` boundary is shown to miss a real occurrence. |
| Q4 | Does the real-value check read paths `SKIPPED` excludes from the style checks? Recommendation: B of §4 Which changed text: yes, every changed line in every changed path, because `CHANGELOG.md` and `docs/archive/` are published (F2). | Ray, 20261112: A, `SKIPPED` applies. Once #276's one-time removal has run, a value in a skipped path means the check missed it before it got there. |
| Q5 | The branch name reaches `main` and `dev` in the merge commit's subject (F9), and the issue does not name it. Should the check also refuse a branch name that holds a listed value (A), or leave it to the rule alone (B)? Recommendation: A. It is the same exposure as a commit message, the check already reads the branch name in `main`, and the fix (`git branch -m`) is local because working branches are never pushed (`docs/standards/2-git.md` §2.3). It adds a criterion the issue lacks, so it is your call on scope. | Ray, 20261112: B. The branch slug is taken from the issue title, and the rule governs issue text. |

**Settled by rule, not asked:**

- **What the report prints.** The file and line, or the commit's short hash, and the value's position in `DEV_REAL_VALUES` (for example "value 3"), never the value. The issue requires that the value not be printed; the position tells Ray which entry it is without printing it.
- **Out of scope**, per the issue: issue and pull request text; values already published in `docs/archive/` and commit history (F6's 5 commits); `tests/test_slack_channel_config.py:186`, which #214 covers (F7); commits `/closeout` makes after P7 (F10).

## 6. Disposition

- Promoted to: `../specs/REAL_VALUE_CHECK_SPEC.md`
