# Standards Split — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261029
**Branch:** `chore/issue-244-standards-split` (from `main`)
**Target release:** n/a — `chore/*`
**Originating item:** Issue #244
**Design study:** `n/a` — direct path, no recon was run

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261029 | Ray | Branch type `chore/*`, direct path. The `workmain/` and `tests/` edits are comment and docstring citations, taken under the `docs/DEVELOPMENT_STANDARDS.md` §2.2 `chore/*` exception. | Applied. DR6 states the proof method the exception requires. |
| 20261029 | Spanner | The directory is `docs/standards/`, and each section file is named `<N>-<slug>.md`. With the top-level number at the front of the name, a bare `§4.3` resolves to its file without the README, so `docs/DEVELOPMENT_STANDARDS.md` §1.5's rule that a bare § is a section of this document keeps working unchanged. The files also sort in section order. | DR3. |
| 20261029 | Spanner | The issue leaves it to the spec whether historical `CHANGELOG.md` entries are rewritten. They are not. `docs/DEVELOPMENT_STANDARDS.md` §1.5 keeps a historical citation as written, and §2.8 forbids a `chore/*` branch to change `CHANGELOG.md`. Every entry citing the file is released history, and `[Unreleased]` is empty. The same rule keeps `automation/check_release_integrity.py`'s comment that the Release rule "only entered DEVELOPMENT_STANDARDS §2.2 at v1.26.0": that file did not exist at v1.26.0 under its new name, so rewriting the comment would make it false. | DR5. AC3.1 names both as intended lines. |
| 20261029 | Spanner | Restated issue AC3. Its check, `grep -rn DEVELOPMENT_STANDARDS.md --exclude-dir=archive`, cannot see the form `DEVELOPMENT_STANDARDS §4.3` (no `.md`), which eleven code comments and docstrings use. It also reads three untracked files ignored through `.git/info/exclude` (`issues.json`, `queue.json`, `issues-closed.json`). AC3.1 uses `git grep` on `DEVELOPMENT_STANDARDS`. The issue body needs the edit at close-out (`docs/DEVELOPMENT_STANDARDS.md` §1.2). | AC3.1. |
| 20261029 | Spanner | Restated issue AC2. Diffing the sorted heading lists shows that the headings survived, but not that the rule text under them moved without change. AC2.1 checks that the section files, read in order, reproduce the old file's text exactly from `## 1.` onward, apart from the `---` separators. That covers the headings as well. | AC2.1. |
| 20261029 | Spanner | Which standards files each role's session-open run reads, beyond `README.md` and §1, which every role reads because §1 governs all of them. Every role also reads §2. Spanner applies §2.2 in its Next stage and cuts the branch under §2.7. Caliper takes the diff base for its post-implementation review from §2.2. Anvil commits at the end of every step, under §2.4. Caliper also reads §3, because review criterion 6 in `.claude/skills/session-start/SKILL.md` § Role 2 cites §3.8. Anvil also reads §6, as the issue asks. §3, §4, §5 and §7 are not read at open. A spec that touches code cites the sections it relies on, and Caliper's read 4 and Anvil's read 5 already read every section a spec cites. | DR7, Step 4. |
| 20261029 | Spanner | `automation/issue_validator_test.py` builds the standards path itself, in two places, instead of reading `issue_validator.STANDARDS_RELATIVE_PATH`. If the test keeps its own copy of the path, the next move can update the module and leave the test reading a stale path. After this spec, the path is stated once, in the module. | Step 1d. |
| 20261029 | Spanner | Open issue bodies that cite `docs/DEVELOPMENT_STANDARDS.md` are not edited. An issue body is not a file in the repository, and editing every open issue is outside what #244 asks. A citation by § number in an issue body resolves through the README's statement of where the single file went, as `docs/archive/`'s citations do. | §1 Out of scope. |
| 20261029 | Caliper | 2: DR4 says "every list in the census stays within one top-level section", so a list keeps its single path. That is not true for three lines. `.claude/skills/closeout/references/chore.md:8`, `feature.md:8` and `hotfix.md:9` each end with `` `docs/DEVELOPMENT_STANDARDS.md` §1.5, §2.2 ``. The Step 2b census records these lines as "§1.5, §1.5" and leaves out §2.2, because the census regex `(§[0-9.]+)?` captures only the first § after the path. Applied as written, DR4 produces `` `docs/standards/1-workflow.md` §1.5, §2.2 ``, which sends §2.2 to the §1 file. | Accepted. A second census search, quoted in §2, finds every list after a path. DR4 keeps a single path only where every member of the list is in one top-level section. Step 2c quotes the three crossing lines with one path per section, and the Step 2b rows record every § in each list. |
| 20261029 | Caliper | 7: AC3.2 checks only the first § after each path. Its regex and the §6 loop never read a later list member, so the misfiled `§1.5, §2.2` above passes AC3.2. | Accepted. The §6 check tests every § in a list against the file it follows. Run on sample lines on 20261029, it printed `WRONG FILE docs/standards/1-workflow.md §2.2` for the misfiled list, printed `NO HEADING` for a section that does not exist, and passed the corrected form. |
| 20261029 | Spanner | Found while resolving the list finding: `.claude/skills/closeout/references/feature.md:7` reads `` `docs/DEVELOPMENT_STANDARDS.md` §2.5, §5 suite results ``. Its `§5` is the results artifact's §5, not a standards section. A check that treated every `, §N` after a path as a list member would report it as misfiled. | Every standards list member in the census is a subsection (`§N.M`), so the §6 check reads `, §N.M` as a list member and nothing else. `feature.md:7` is rewritten under DR4 with one path, for §2.5. |
| 20261029 | Caliper | 3: The DR6 script cannot see uncommitted edits, and Step 3 and §6 run it before Step 3's commit. It gets its file list from `git diff --name-only <base> HEAD -- workmain tests`, which covers committed changes only. Before that commit it prints `0 files checked` and exits `0`, and the quoted mutation result cannot occur. This is an expected failure that was reasoned, not observed. | Accepted. The script diffs the merge base against the working tree (`git diff --name-only <base> -- workmain tests`). Its outputs were observed on 20261029, each mutation reverted with `git checkout --`, and §6 quotes them. |
| 20261029 | Spanner | Three `CLAUDE.md` § Critical Rules entries cite the file by path ("Full statement: `docs/DEVELOPMENT_STANDARDS.md` §1.1"). Only the path changes. No entry is added, reworded or removed, so the section's membership rule is not engaged. The section's intro sentence, which points at the standards' preamble, is repointed to the README. Ray's approval of this spec covers both edits. | Step 2a. |
| 20261029 | Caliper (post-implementation) | No findings. | n/a |

---

## 1. Scope

**In scope:**

- `docs/DEVELOPMENT_STANDARDS.md` is removed. Its text moves unchanged into `docs/standards/`: a `README.md` that holds the header and the index, and one file for each of §1–§7.
- Every live citation of the old file is rewritten to the new path: `CLAUDE.md`, `.claude/skills/closeout/` (`SKILL.md`, `references/chore.md`, `references/feature.md`, `references/hotfix.md`), `.claude/skills/session-start/` (`SKILL.md`, `references/caliper.md`, `references/spanner.md`), `.githooks/commit-msg`, `.githooks/pre-push`, `automation/` (`check_release_integrity.py`, `closeout_acs.py`, `issue_validator.py`, `issue_validator_test.py`), `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/dev/specs/_TEMPLATE_SPEC.md`, and comments or docstrings in nine `workmain/` modules and two `tests/` modules (Step 3).
- Each role's session-open reference names the standards files its run reads (`references/spanner.md`, `references/caliper.md`, `references/anvil.md`).

**Out of scope:**

- Any change to the wording of a standard. The text moves exactly as it is. Issue #250 edits standards text, and it edits the split files after this spec ships.
- `CHANGELOG.md` and the historical comment in `automation/check_release_integrity.py` (Decision Log, DR5).
- `docs/archive/`, which is reference-only. The README says where the single file went.
- Open issue bodies (Decision Log).
- Citations of a standards section by bare §, such as `§2.5` in `docs/dev/results/_TEMPLATE_RESULTS.md`. A § number does not change, so a bare citation still resolves.

## 2. Verified current state

On the direct path, each step quotes the text it replaces. The census in Step 2 and Step 3 is the output of `git grep -noE '`?(docs/)?DEVELOPMENT_STANDARDS(\.md)?`?(:| )?(§[0-9.]+)?' -- . ':!docs/archive' ':!CHANGELOG.md'`, taken on 20261029 at `3a585d5` (`origin/main`, which equals `dev`). That search captures only the first § after a path. A second search, `git grep -nE 'DEVELOPMENT_STANDARDS(\.md)?`? ?§[0-9.]+((, ?| and | or )§[0-9.]+)+' -- . ':!docs/archive' ':!CHANGELOG.md' ':!docs/dev/specs'`, found every list after a path: `.claude/skills/closeout/references/chore.md` lines 8, 10 and 11, `feature.md` lines 7–10, and `hotfix.md` lines 9, 11 and 13. The split method in Step 1 was dry-run in a scratch directory on the same date. The section files it produced passed AC2.1's check, and a one-character change to one of them failed it. `issue_validator.parse_label_pair` returned `['defect', 'gap']` from the dry-run `1-workflow.md`.

## 3. Design rules

- **DR1 — Exact text.** Each edit is made as quoted or as DR4 defines it. A wording or mechanical change within the meaning, scope and file set approved here is recorded in the results artifact's §4 as `within approved meaning`. A quote or census line that does not match the file stops the step.
- **DR2 — Text moves unchanged.** Every line of `docs/DEVELOPMENT_STANDARDS.md` from `## 1. Development Workflow` to the end is placed in exactly one section file, in order, with nothing changed. The seven `---` separator lines are dropped, and so are the blank lines left at the end of a file. The title and the preamble (lines 1–6) are replaced by the README Step 1b quotes.
- **DR3 — Files.** `docs/standards/` holds:

  | File | Holds |
  | --- | --- |
  | `README.md` | Header and index |
  | `1-workflow.md` | `## 1. Development Workflow` |
  | `2-git.md` | `## 2. Git Workflow` |
  | `3-code.md` | `## 3. Code Standards` |
  | `4-database.md` | `## 4. Database Standards` |
  | `5-cli.md` | `## 5. CLI Standards` |
  | `6-testing.md` | `## 6. Testing Standards` |
  | `7-file-placement.md` | `## 7. File Placement` |

- **DR4 — Citation rewrite.** A citation of a section, in any form, becomes the repo-root path of the file DR3 gives for the section's top-level number, followed by the same §. A citation that was backticked stays backticked, and one that was not stays unquoted. The forms are:
  - `` `docs/DEVELOPMENT_STANDARDS.md` §N.M `` becomes `` `docs/standards/<file>` §N.M ``.
  - `docs/DEVELOPMENT_STANDARDS.md §N.M`, unquoted, becomes `docs/standards/<file> §N.M`.
  - `DEVELOPMENT_STANDARDS.md §N.M` or `` `DEVELOPMENT_STANDARDS.md` §N.M ``, a path without `docs/`, becomes the repo-root path under `docs/DEVELOPMENT_STANDARDS.md` §1.5.
  - `DEVELOPMENT_STANDARDS §N.M`, with no extension, becomes `docs/standards/<file> §N.M`.
  - `DEVELOPMENT_STANDARDS.md:§1.1` becomes `` `docs/standards/1-workflow.md` §1.1 ``.

  A list of sections after one citation, such as `§2.2, §2.3`, keeps its single path where every member is in the same top-level section. A list that crosses sections gets one path for each section, and the three in the census are quoted in Step 2c. In `.claude/skills/closeout/references/feature.md` line 7, the `§5` in "§2.5, §5 suite results" is the results artifact's §5 and is not part of the citation. A citation of the whole document is not rewritten under this rule. Each one is quoted in Step 1 or Step 2a.
- **DR5 — Historical citations stay.** `CHANGELOG.md`, `docs/archive/`, and `automation/check_release_integrity.py`'s comment "only entered DEVELOPMENT_STANDARDS §2.2 at v1.26.0" are not changed.
- **DR6 — `workmain/` and `tests/` are behaviour-neutral.** This is the proof the `docs/DEVELOPMENT_STANDARDS.md` §2.2 `chore/*` exception requires. For every `.py` file under `workmain/` or `tests/` that differs from the merge base, the module's AST with every docstring blanked is identical before and after, and no changed docstring belongs to a function decorated with a Click `command` or `group`, because a Click command's docstring is its `--help` text. The script in AC6.2 proves both. A comment or docstring may be reflowed within itself where the longer path pushes a line past its neighbours.
- **DR7 — Role reads.** At session open, every role reads `docs/standards/README.md`, `docs/standards/1-workflow.md` and `docs/standards/2-git.md`. Caliper also reads `docs/standards/3-code.md`, and Anvil also reads `docs/standards/6-testing.md`. Each read is a new last numbered read in that role's reference, so no existing read is renumbered.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | The standards are split into `docs/standards/`, and the issue validator and its test read §1.3 from the new file | `docs/DEVELOPMENT_STANDARDS.md` (removed), `docs/standards/README.md`, `docs/standards/1-workflow.md`, `docs/standards/2-git.md`, `docs/standards/3-code.md`, `docs/standards/4-database.md`, `docs/standards/5-cli.md`, `docs/standards/6-testing.md`, `docs/standards/7-file-placement.md`, `automation/issue_validator.py`, `automation/issue_validator_test.py` |
| 2 | Every live citation outside `workmain/` and `tests/` names the new file | `CLAUDE.md`, `.claude/skills/closeout/SKILL.md`, `.claude/skills/closeout/references/chore.md`, `.claude/skills/closeout/references/feature.md`, `.claude/skills/closeout/references/hotfix.md`, `.claude/skills/session-start/SKILL.md`, `.claude/skills/session-start/references/caliper.md`, `.claude/skills/session-start/references/spanner.md`, `.githooks/commit-msg`, `.githooks/pre-push`, `automation/check_release_integrity.py`, `automation/closeout_acs.py`, `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/dev/specs/_TEMPLATE_SPEC.md` |
| 3 | Every comment and docstring citation in `workmain/` and `tests/` names the new file | `workmain/cli/commands/gdocs.py`, `workmain/cli/commands/slack.py`, `workmain/cli/interface.py`, `workmain/cli/output.py`, `workmain/database/connection.py`, `workmain/services/ai_cost_service.py`, `workmain/services/clockify_service.py`, `workmain/utils/ai_arguments.py`, `workmain/workflows/eod_workflow.py`, `tests/test_meetings_merge.py`, `tests/test_meetings_reschedule.py` |
| 4 | Each role's session-open run reads its standards files | `.claude/skills/session-start/references/spanner.md`, `.claude/skills/session-start/references/caliper.md`, `.claude/skills/session-start/references/anvil.md` |
| 5 | Results artifact | `docs/dev/results/STANDARDS_SPLIT_RESULTS.md` |

Close-out is not in this table. It is `/closeout`.

Steps 1 and 2 must each leave the suite green (`docs/DEVELOPMENT_STANDARDS.md` §1.4). Step 1 therefore carries the validator change, since the validator's test reads the standards file. Between Step 1 and Step 2 the citations point at a file that no longer exists. Nothing executes them, and Step 2 follows directly.

### Step 1 — split

**1a.** Create the seven section files from `docs/DEVELOPMENT_STANDARDS.md` under DR2 and DR3, then `git rm docs/DEVELOPMENT_STANDARDS.md`. The split is made by heading, never by line number. A line beginning `## <N>. ` starts file `<N>`, and every line up to the next such heading goes to that file, except a `---` line. Trailing blank lines are trimmed from each file. The dry run used this script:

```bash
awk -v d=docs/standards 'BEGIN{split("workflow git code database cli testing file-placement",n," ")} /^## [1-7]\. /{s=substr($2,1,1); f=d"/"s"-"n[s]".md"} f && $0!="---"{print > f}' docs/DEVELOPMENT_STANDARDS.md
for f in docs/standards/[1-7]-*.md; do sed -i -e :a -e '/^\n*$/{$d;N;ba' -e '}' "$f"; done
```

**1b.** Create `docs/standards/README.md` with exactly this text. It replaces the old file's lines 1–6:

```markdown
# WorkmAIn Development Standards

How work gets built. `.claude/skills/session-start/SKILL.md` owns who does what (the three-role model). `CLAUDE.md` owns what this project is (stack, architecture) and domain decisions (tag system, time format, trigger terminology, write-path map). This document owns everything else — process, git workflow, code patterns, database, CLI structure, and testing.

The only text here also stated in `CLAUDE.md` is its § Critical Rules subset; nothing else appears in both.

## How this document is stored

This is one document, stored as this header and one file for each top-level section. Sections are numbered once across all the files: the file holding a section is the one whose name begins with the section's top-level number, so `§4.3` is in `docs/standards/4-database.md`. "This document", in any of these files, means all of them.

It was a single file, `docs/DEVELOPMENT_STANDARDS.md`, until issue #244 split it. No § number changed. A citation of that file, in `docs/archive/`, `CHANGELOG.md` or an issue body, resolves by its § number to the file below.

## Sections

Read the section that covers the work before doing it.

| File | Section | Read it before |
| --- | --- | --- |
| `docs/standards/1-workflow.md` | §1 Development Workflow | any work — it governs every role |
| `docs/standards/2-git.md` | §2 Git Workflow | cutting a branch, committing, merging or releasing |
| `docs/standards/3-code.md` | §3 Code Standards | writing or changing a module |
| `docs/standards/4-database.md` | §4 Database Standards | code that opens a session or uses a repository, or a migration |
| `docs/standards/5-cli.md` | §5 CLI Standards | adding or changing a command |
| `docs/standards/6-testing.md` | §6 Testing Standards | writing a test, or recording test evidence |
| `docs/standards/7-file-placement.md` | §7 File Placement | creating a file |
```

The old preamble's "Read the relevant section before writing code." is replaced by the line above the table and the table's last column.

**1c.** In `automation/issue_validator.py`, replace:

```text
STANDARDS_RELATIVE_PATH = Path("docs/DEVELOPMENT_STANDARDS.md")
```

with:

```text
STANDARDS_RELATIVE_PATH = Path("docs/standards/1-workflow.md")
```

and in its module docstring, line 13, apply DR4 to `` `docs/DEVELOPMENT_STANDARDS.md` §1.3 ``.

**1d.** In `automation/issue_validator_test.py`, replace both occurrences of:

```text
ROOT / "docs" / "DEVELOPMENT_STANDARDS.md"
```

(lines 21 and 111) with:

```text
ROOT / issue_validator.STANDARDS_RELATIVE_PATH
```

### Step 2 — citations outside `workmain/` and `tests/`

**2a.** Whole-document citations in `CLAUDE.md` and `.claude/skills/session-start/SKILL.md`. Each is replaced as quoted:

- `CLAUDE.md` line 9: replace `**`docs/DEVELOPMENT_STANDARDS.md` owns how we build** — git workflow, code patterns, database, CLI, and testing.` with `**`docs/standards/` owns how we build** — git workflow, code patterns, database, CLI, and testing. `docs/standards/README.md` is its header and index.`
- `CLAUDE.md` line 17: replace `` `docs/DEVELOPMENT_STANDARDS.md` states the same carve-out in its preamble. `` with `` `docs/standards/README.md` states the same carve-out. ``
- `CLAUDE.md` line 26: replace `` Coding, database, CLI, git, and testing rules all live in `docs/DEVELOPMENT_STANDARDS.md`. `` with `` Coding, database, CLI, git, and testing rules all live in `docs/standards/`. ``
- `CLAUDE.md` line 38: replace `` A rule lives in this file, in `docs/DEVELOPMENT_STANDARDS.md`, or in the skill `` with `` A rule lives in this file, in `docs/standards/`, or in the skill ``
- `CLAUDE.md` line 70: replace `` | `docs/DEVELOPMENT_STANDARDS.md` | Before committing, or writing any module, command, or test | `` with `` | `docs/standards/README.md` | Before committing, or writing any module, command, or test — it names the section file each needs | ``
- `.claude/skills/session-start/SKILL.md` line 34: replace `` cited by its section of `CLAUDE.md` or `docs/DEVELOPMENT_STANDARDS.md`, never copied. `` with `` cited by its section of `CLAUDE.md` or of a `docs/standards/` file, never copied. ``

**2b.** Section citations, rewritten under DR4. The census, at `3a585d5`, gives the file, the line and the section each citation names:

| File | Line: section cited |
| --- | --- |
| `CLAUDE.md` | 19: §1.1 · 20: §1.4 · 24: §3.6 · 54: §1.6 · 58: §1.3 · 93: §7 · 196: §1.2 |
| `.claude/skills/closeout/SKILL.md` | 10: §2.8 · 30: §2.2 · 31: §1.1 (form `DEVELOPMENT_STANDARDS.md:§1.1`) · 32: §1.5 · 33: §1.5, §1.5, §1.1, §1.1 · 34: §1.2 · 39: §2.2 · 71: §1.4, §2.2 · 75: §1.4 · 77: §2.3, §1.4, §2.3 · 88: §2.2 · 89: §2.6 |
| `.claude/skills/closeout/references/chore.md` | 3: §2.2, §2.6 · 7: §2.2 · 8: §1.5, and the list §1.5, §2.2 (Step 2c) · 10: list §2.2, §2.3 · 11: list §2.2, §2.3 · 12: §2.3 |
| `.claude/skills/closeout/references/feature.md` | 7: §2.5 (the following `§5` is the results artifact's), §2.2 · 8: §1.5, and the list §1.5, §2.2 (Step 2c) · 9: list §2.2, §2.3 · 10: list §2.2, §2.5 · 11: §2.6 · 12: §2.3 · 13: §2.2 · 15: §2.2 |
| `.claude/skills/closeout/references/hotfix.md` | 7: §2.5 · 8: §2.2 · 9: §1.5, and the list §1.5, §2.2 (Step 2c) · 11: list §2.2, §2.3 · 12: §2.2 · 13: list §2.2, §2.3 · 14: §2.6 · 15: §2.3 |
| `.claude/skills/session-start/SKILL.md` | 83: §3.8 · 84: §1.2 · 86: §1.2 · 96: §1.4 · 107: §1.2 · 111: §1.1 |
| `.claude/skills/session-start/references/caliper.md` | 26: §1.1 · 33: §2.2 · 37: §2.2 · 40: §1.2, §1.2 · 51: §1.1 |
| `.claude/skills/session-start/references/spanner.md` | 7: §1.6 · 18: §1.1, §2.2 · 35: §1.1 |
| `.githooks/commit-msg` | 8: §2.4 · 64: §2.4 |
| `.githooks/pre-push` | 7: §2.2 (form `DEVELOPMENT_STANDARDS.md §2.2`) |
| `automation/check_release_integrity.py` | 16: §2.2 (form `` `DEVELOPMENT_STANDARDS.md` §2.2 ``) · 149: §2.5 (form `DEVELOPMENT_STANDARDS.md §2.5`, inside the f-string the script prints) |
| `automation/closeout_acs.py` | 39: §1.5 |
| `docs/dev/results/_TEMPLATE_RESULTS.md` | 15: §2.2 · 34: §1.1 · 42: §1.3 · 50: §1.1 · 57: §6 · 59: §2.6 · 64: §1.3 |
| `docs/dev/specs/_TEMPLATE_SPEC.md` | 13: §1.5 · 15: §1.1 · 49: §1.2 · 53: §1.2 · 75: §1.4 · 86: §1.2 · 88: §1.2 · 92: §6 · 93: §6 · 94: §6 |

`automation/check_release_integrity.py` line 44 is not changed (DR5).

**2c.** Lists that cross sections. In `.claude/skills/closeout/references/chore.md` line 8, `.claude/skills/closeout/references/feature.md` line 8 and `.claude/skills/closeout/references/hotfix.md` line 9, replace:

```text
survive the move unedited — `docs/DEVELOPMENT_STANDARDS.md` §1.5, §2.2 |
```

with:

```text
survive the move unedited — `docs/standards/1-workflow.md` §1.5, `docs/standards/2-git.md` §2.2 |
```

### Step 3 — `workmain/` and `tests/`

Rewritten under DR4, and checked under DR6 before the commit. Each citation is in a comment or a docstring. None of these docstrings belongs to a Click command: `_record_upload`, `_record_slack_post`, `_configure_cli_logging`, `_IntegrationFailure`, `record_scope`, `_record_clockify_link`, `failure_exit_code` and `_completed` are helpers, an exception class and a context manager, and the remaining citations are module docstrings or comments.

| File | Line: section cited (form) |
| --- | --- |
| `workmain/cli/commands/gdocs.py` | 59: §4.3 (`DEVELOPMENT_STANDARDS §4.3`) |
| `workmain/cli/commands/slack.py` | 61: §4.3 (`DEVELOPMENT_STANDARDS §4.3`) |
| `workmain/cli/interface.py` | 71: §5.6 (`DEVELOPMENT_STANDARDS §5.6`) |
| `workmain/cli/output.py` | 439: §5.6 (`DEVELOPMENT_STANDARDS §5.6`) |
| `workmain/database/connection.py` | 18: §4.3 (`DEVELOPMENT_STANDARDS §4.3`) · 95: §4.3 (`docs/DEVELOPMENT_STANDARDS.md §4.3`) |
| `workmain/services/ai_cost_service.py` | 7: §4.3 (`` `docs/DEVELOPMENT_STANDARDS.md` §4.3 ``) |
| `workmain/services/clockify_service.py` | 8: §4.3 · 59: §4.3 (both `DEVELOPMENT_STANDARDS §4.3`) |
| `workmain/utils/ai_arguments.py` | 12: §5.6 · 31: §5.6 (both `docs/DEVELOPMENT_STANDARDS.md §5.6`) |
| `workmain/workflows/eod_workflow.py` | 268: §5.6 (`DEVELOPMENT_STANDARDS §5.6`) |
| `tests/test_meetings_merge.py` | 4: §4.1 (`DEVELOPMENT_STANDARDS §4.1`) |
| `tests/test_meetings_reschedule.py` | 5: §4.1 (`DEVELOPMENT_STANDARDS §4.1`) |

### Step 4 — role reads

**4a.** In `.claude/skills/session-start/references/spanner.md` § Reads, after the line beginning `5. `git branch --list`, add:

```text
6. `docs/standards/README.md`, `docs/standards/1-workflow.md` and `docs/standards/2-git.md`, end to end.
```

Read 1's "reads 2–5 are skipped" is unchanged, so read 6 runs whether or not an item is found.

**4b.** In `.claude/skills/session-start/references/caliper.md` § Reads, after the line beginning `4. Every source the spec cites`, add:

```text
5. `docs/standards/README.md`, `docs/standards/1-workflow.md`, `docs/standards/2-git.md` and `docs/standards/3-code.md`, end to end.
```

**4c.** In `.claude/skills/session-start/references/anvil.md` § Reads, after the line beginning `5. Every reference the spec makes`, add:

```text
6. `docs/standards/README.md`, `docs/standards/1-workflow.md`, `docs/standards/2-git.md` and `docs/standards/6-testing.md`, end to end.
```

No Emits list changes. A standards file that cannot be read is reported under `.claude/skills/session-start/SKILL.md` § Rules every run holds.

### Step 5 — results

`docs/dev/results/STANDARDS_SPLIT_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`, with `**Spec:** `../specs/STANDARDS_SPLIT_SPEC.md``.

### Authorization points

None. The merge to `main` is `/closeout`'s, which stops at it.

## 5. Acceptance criteria

`<base>` is `git merge-base origin/main HEAD`.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The standards are one directory holding a README and one file per top-level section, each file holding exactly the section its name numbers, and the single file no longer exists outside `docs/archive/` | `ls docs/standards` lists `README.md` and the seven DR3 files and nothing else; `for f in docs/standards/[1-7]-*.md; do echo "$f $(grep -c '^## ' "$f") $(head -1 "$f")"; done` prints a count of `1` and a first line `## <N>. ` matching each file's prefix; `git ls-files docs/DEVELOPMENT_STANDARDS.md` prints nothing |
| AC1.2 | The README states that the files are one document, how a § number finds its file, where the single file went, and which section to read before which work | Stated reading by Ray of `docs/standards/README.md`, for those four things |
| AC2.1 | Every section, headings included, moved with its text unchanged | `diff <(git show <base>:docs/DEVELOPMENT_STANDARDS.md \| sed -n '/^## 1\. /,$p' \| grep -vx -e '---' \| cat -s) <(for f in docs/standards/{1-workflow,2-git,3-code,4-database,5-cli,6-testing,7-file-placement}.md; do cat "$f"; echo; done \| cat -s \| sed '${/^$/d}')` prints nothing |
| AC3.1 | No live tracked file outside `docs/archive/` cites the old file, except the two historical lines DR5 keeps and the README's statement of where the file went | `git grep -n DEVELOPMENT_STANDARDS -- ':!docs/archive' ':!CHANGELOG.md' ':!docs/dev/specs/STANDARDS_SPLIT_SPEC.md' ':!docs/dev/results/STANDARDS_SPLIT_RESULTS.md'` prints exactly two lines: `docs/standards/README.md`'s "It was a single file" line and `automation/check_release_integrity.py`'s "only entered DEVELOPMENT_STANDARDS §2.2 at v1.26.0" line |
| AC3.2 | Every rewritten citation names the file that holds the section it cites, every member of a list included | The AC3.2 check in §6 prints nothing |
| AC3.3 | The whole-document citations in `CLAUDE.md` and `.claude/skills/session-start/SKILL.md` point at the directory or its README and still say what they said | Stated reading by Ray of the six lines Step 2a quotes, for each pointing at `docs/standards/` or its README with its meaning unchanged |
| AC4.1 | The issue validator reads the §1.3 label pair from the §1 file, and its test reads the same path through the module's constant | `pytest automation/` prints `0 failed`, `test_the_live_standards_file_yields_exactly_the_label_pair` among the passed; `grep -n 'DEVELOPMENT_STANDARDS\|"docs"' automation/issue_validator_test.py` prints nothing |
| AC5.1 | Every role's session-open run reads the README, §1 and the other section files DR7 gives it | Stated reading by Ray of § Reads in `references/spanner.md`, `references/caliper.md` and `references/anvil.md`, for the files DR7 names |
| AC6.1 | The application suite passes | `pytest` prints the baseline counts in §6 |
| AC6.2 | The `workmain/` and `tests/` changes do not change behaviour: code is unchanged apart from docstrings, and no changed docstring is a Click command's help text | The DR6 script in §6 exits `0` |

## 6. Test plan

- **Baseline before this work:** 1598 passed, 0 failed, 0 skipped (`CHANGELOG.md` [1.55.0]).
- **Expected after:** 1598 passed, 0 failed, 0 skipped. No test is added or removed. `pytest automation/` is a separate suite, and its counts are recorded before Step 1 and after Step 1.
- **AC3.2 check**, run from the repository root. A citation is a path, its first §, and every `, §N.M` that follows it. Every § is checked against the file it follows: the file must exist, its prefix must be the section's top-level number, and it must hold a `##` or `###` heading for that section. This spec and its results artifact are excluded, because they quote misfiled citations as examples.

  ```bash
  git grep -hoE 'docs/standards/[1-7]-[a-z-]+\.md`? §[0-9]+(\.[0-9]+)?(, §[0-9]+\.[0-9]+)*' -- ':!docs/archive' ':!docs/dev/specs/STANDARDS_SPLIT_SPEC.md' ':!docs/dev/results/STANDARDS_SPLIT_RESULTS.md' | sort -u | while read -r cite; do
    f=$(echo "$cite" | grep -oE 'docs/standards/[^` ]+')
    [ -f "$f" ] || { echo "MISSING $cite"; continue; }
    for s in $(echo "$cite" | grep -oE '§[0-9]+(\.[0-9]+)?' | tr -d '§'); do
      [ "$(basename "$f" | cut -d- -f1)" = "${s%%.*}" ] || { echo "WRONG FILE $f §$s"; continue; }
      grep -qE "^#{2,3} ${s//./\\.}[. ]" "$f" || echo "NO HEADING $f §$s"
    done
  done
  ```

  It prints nothing. It was observed on 20261029 against the dry-run split, fed sample lines. `` `docs/standards/1-workflow.md` §1.5, §2.2 `` printed `WRONG FILE docs/standards/1-workflow.md §2.2`. `docs/standards/4-database.md §4.9` printed `NO HEADING docs/standards/4-database.md §4.9`. Nothing was printed for the Step 2c form, a same-section list (`§2.2, §2.3`), `feature.md` line 7's `§2.5, §5 suite results`, or `docs/standards/7-file-placement.md §7`.
- **DR6 script**, written to the scratchpad, not committed, and run as `python3 -I <script>` from the repository root:

  ```python
  import ast, subprocess, sys

  base = subprocess.check_output(["git", "merge-base", "origin/main", "HEAD"], text=True).strip()
  paths = subprocess.check_output(["git", "diff", "--name-only", base, "--", "workmain", "tests"], text=True).split()
  KINDS = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

  def docstrings(tree):
      out = {}
      for node in ast.walk(tree):
          if isinstance(node, KINDS) and node.body and isinstance(node.body[0], ast.Expr) \
                  and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
              out[getattr(node, "name", "<module>")] = (node, node.body[0].value)
      return out

  failed = False
  for path in paths:
      old = ast.parse(subprocess.check_output(["git", "show", f"{base}:{path}"], text=True))
      new = ast.parse(open(path).read())
      old_docs, new_docs = docstrings(old), docstrings(new)
      for name, (node, const) in new_docs.items():
          if name in old_docs and old_docs[name][1].value != const.value:
              decos = [ast.unparse(d) for d in getattr(node, "decorator_list", [])]
              if any("command" in d or "group" in d for d in decos):
                  print(f"{path}: {name} is a Click command; its docstring is --help text"); failed = True
      for _, const in list(old_docs.values()) + list(new_docs.values()):
          const.value = ""
      if ast.dump(old) != ast.dump(new):
          print(f"{path}: code changed beyond docstrings"); failed = True
  print(f"{len(paths)} files checked")
  sys.exit(1 if failed else 0)
  ```

  It compares the merge base with the working tree, so Step 3 runs it on its edits before the commit and records the output in the results artifact. Observed on 20261029, each run with a fresh `PYTHONPYCACHEPREFIX`, and each mutation reverted with `git checkout -- workmain/cli/commands/gdocs.py`:
  - Clean tree: `0 files checked`, exit `0`.
  - `_record_upload`'s `(DEVELOPMENT_STANDARDS §4.3)` rewritten to `(docs/standards/4-database.md §4.3)`: `1 files checked`, exit `0`.
  - The same edit, plus `x = 1` appended to the module: `workmain/cli/commands/gdocs.py: code changed beyond docstrings`, exit `1`.
  - `Changed. ` prefixed to the docstring of `gdocs_auth`, which is decorated `@gdocs.command("auth")`: `workmain/cli/commands/gdocs.py: gdocs_auth is a Click command; its docstring is --help text`, exit `1`.

## 7. Risks and rollback

- **A citation the census missed** points at a missing file. AC3.1 searches every form that contains `DEVELOPMENT_STANDARDS`. A citation written without that word, such as "the standards file", carries no path that can break.
- **A session open before the merge** has the old path loaded. That is harmless, because the file stays readable at `git show main:docs/DEVELOPMENT_STANDARDS.md` and the § numbers are unchanged.
- **Issue #250** is blocked by this issue and edits the split files after it ships. Nothing in this spec edits standards text, so the two do not conflict.
- **Rollback:** each step is one commit, and reverting the commits in reverse order restores the single file and every citation. Before close-out, `git branch -D` the unmerged branch.
