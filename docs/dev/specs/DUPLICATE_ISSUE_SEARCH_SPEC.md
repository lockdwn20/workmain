# Duplicate Issue Search and Issue Splits — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261009
**Branch:** `chore/issue-183-duplicate-issue-search`
**Target release:** n/a — `chore/*`, `docs/DEVELOPMENT_STANDARDS.md` §2.2
**Originating item:** Issue #183, child of #80
**Design study:** n/a — direct path, no recon was run

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261009 | Ray | #183 first asked how `/closeout` should handle a design study cited by several specs. That situation came from one cause: #182 was opened without searching for #148, #149 and #155. #183 is rewritten in place to fix that cause instead. | Issue #183 retitled and rewritten. The `#155 blocked by #183` link was removed, since #155 no longer waits on it. |
| 20261009 | Ray | #182's design study is split into the write-ups of #148, #149 and #155, and each of them gets a design study of its own covering only its own items. No spec cites a study shared with another. | Out of scope here. It is done on GitHub and on each child's branch, not by this spec. |
| 20261009 | Ray | A design study can show that its own issue must be split, even after a proper duplicate search. #183 also covers that case: the new issues carry the findings, and the study is narrowed to the originating issue's remaining work or deleted. | Issue #183 retitled, with AC3 added. Step 1 adds the second §1.3 bullet. |
| 20261009 | Ray | "Backlog" is a retired term, recently removed from the templates. Neither edited template line may carry it, and the one left in `_TEMPLATE_DESIGN.md` §6 goes in the same step. | Step 2, AC2.3. |
| 20261009 | Spanner | A study left with no work of its own is deleted, not set to `Superseded`. Under §1.5 a `Superseded` artifact stays in `docs/dev/design/`, where it reads as live, and its content already lives in the new issues. | Step 1, the split bullet. |
| 20261009 | Spanner | The rules live in `docs/DEVELOPMENT_STANDARDS.md` §1.3, which is where issue discipline lives. The places that open issues cite it. | Steps 1 and 2. |
| 20261009 | Spanner | `automation/issue_validator.py` gets no duplicate check. A keyword match can only list candidates for someone to read. The rule is the search plus the reading, and the validator cannot do the reading. | Out of scope. |

---

## 1. Scope

**In scope:**

- Two new bullets in `docs/DEVELOPMENT_STANDARDS.md` §1.3: the search-before-opening rule, and the rule for an issue that its design study splits.
- Removal of the retired term "backlog" from `docs/dev/results/_TEMPLATE_RESULTS.md` §3 and `docs/dev/design/_TEMPLATE_DESIGN.md` §6.
- A citation of it from each place that tells a role to open an issue or carry work to one. The places are found by the search in AC2.1: `docs/DEVELOPMENT_STANDARDS.md` §1.2's verification-defect bullet, and `docs/dev/results/_TEMPLATE_RESULTS.md` §3's carried-AC sentence and §6's Follow-ups sentence.

**Out of scope:**

- Any change to `automation/issue_validator.py` (Decision Log, 20261009).
- What to do with a duplicate found after both issues are open. The rule prevents the duplicate. #182, the one existing case, is already restructured.
- A sweep of the open queue for existing duplicates. §1.2 applies new rules forward only.
- Splitting #182's design study (Decision Log, 20261009).

## 3. Design rules

- **DR1 —** Each rule is stated once, in §1.3. Every other place cites §1.3 and restates none of it (`CLAUDE.md` opening).
- **DR2 —** Neither rule names who follows it. Both apply to every role, and the search applies wherever an issue is opened.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Add the two §1.3 bullets and cite the first from §1.2, with the exact text in § Step 1. Commit `docs(standards): search before opening an issue, and carry a split's findings, issue #183`. | `docs/DEVELOPMENT_STANDARDS.md` |
| 2 | Cite §1.3 from the results template and remove the retired term "backlog" from both templates, with the exact text in § Step 2. Commit `docs(templates): cite the duplicate search and drop "backlog", issue #183`. | `docs/dev/results/_TEMPLATE_RESULTS.md`, `docs/dev/design/_TEMPLATE_DESIGN.md` |
| 3 | Write the results artifact from `docs/dev/results/_TEMPLATE_RESULTS.md`. Its §3 table carries this spec's §5 ACs, with AC1.1, AC2.1 and AC3.1 at `Not met` / `Awaiting Ray`, AC2.2's command output, and the suite counts. Commit `docs(results): record the duplicate issue search results for issue #183`. | `docs/dev/results/DUPLICATE_ISSUE_SEARCH_RESULTS.md` |

### Step 1 — `docs/DEVELOPMENT_STANDARDS.md`

In §1.3, insert these two bullets, in this order, after the bullet that begins `- An issue must be independently verifiable on its own:`:

```markdown
- **An issue is opened only for what no open issue already covers.** Before any issue is opened — while planning, at close-out, or to carry a finding or an unmet acceptance criterion forward — the open issues are searched for one covering the same defect or gap: `gh issue list --state open --search "<term>"` once for each symbol, file and behaviour the new issue would name, and every result read. A finding an open issue already covers is added to that issue's context or acceptance criteria, and a new issue carries only the rest. #182 was opened for four defects found at #181's close-out. Three were already open as #148, #149 and #155, and a design study had been written across all four before the overlap was found.
- **An issue split by its design study takes its findings with it.** When a design study shows that its issue must be split into several issues, each new issue's write-up carries the study's findings and settled answers for that issue, so it can be worked on without the study, and each new issue gets a design study of its own. The originating issue's study is narrowed to the work that issue keeps. If the originating issue is left as a parent with no work of its own, its study is deleted, and git keeps its history. A spec cites only a design study written for its own issue, because `/closeout` archives a spec's design study along with the spec (§1.5).
```

In §1.2, replace:

```markdown
- Defects found during verification become their own hotfix, not sprint scope.
```

with:

```markdown
- Defects found during verification become their own hotfix, not sprint scope — on an open issue that already covers them where one exists, §1.3.
```

### Step 2 — `docs/dev/results/_TEMPLATE_RESULTS.md` and `docs/dev/design/_TEMPLATE_DESIGN.md`

In §3, replace:

```markdown
Anything not met is listed here and carried to the backlog with an item number. Do not quietly drop an unmet AC.
```

with:

```markdown
Anything not met is listed here and carried to an issue, cited by its number — an open issue that already covers it where one exists, `docs/DEVELOPMENT_STANDARDS.md` §1.3. Do not quietly drop an unmet AC.
```

In §6, replace:

```markdown
Additional issues created by this work, and any item deliberately left for later.
```

with:

```markdown
Additional issues created by this work, or the open issue an item was added to where one already covered it (`docs/DEVELOPMENT_STANDARDS.md` §1.3), and any item deliberately left for later.
```

In `docs/dev/design/_TEMPLATE_DESIGN.md` §6, replace:

```markdown
- Promoted to: <`../specs/<file>_SPEC.md`, Locked Architecture Decision, or backlog item>
```

with:

```markdown
- Promoted to: <`../specs/<file>_SPEC.md`, Locked Architecture Decision, or issue #N>
```

### Authorization points

None. A `chore/*` branch's only authorization point is the merge to `main`, which belongs to `/closeout`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | The standards require the open issues to be searched for one covering the same defect or gap before any issue is opened, and state what is done when a match is found | Ray reads `docs/DEVELOPMENT_STANDARDS.md` §1.3 and walks #182's opening against it. Following the rule as written would have found #148, #149 and #155 before #182 was opened, and would have put their findings on those issues |
| AC2.1 | Every place that tells a role to open an issue or carry work to one cites the §1.3 rule and restates none of it | Ray reads each line returned by `grep -rnE 'gh issue create\|issue_validator\|own hotfix\|carried to an issue\|issues created by' docs/DEVELOPMENT_STANDARDS.md CLAUDE.md .claude/ docs/dev/*/_TEMPLATE_*.md` and confirms that each line that opens an issue cites §1.3 |
| AC2.2 | The rule's search command is stated once, in §1.3, and nowhere else outside this artifact set and the archive | `grep -rn 'state open --search' docs/DEVELOPMENT_STANDARDS.md CLAUDE.md .claude/ docs/dev/*/_TEMPLATE_*.md` returns exactly one line, and it is in `docs/DEVELOPMENT_STANDARDS.md` §1.3 |
| AC2.3 | No template names the retired "backlog" as the place work goes. Work is carried to an issue | `grep -rni 'backlog' docs/dev/*/_TEMPLATE_*.md` returns zero hits |
| AC3.1 | The standards state where a design study's findings go and what becomes of the study when the study shows its issue must be split into several issues, so that no spec cites a design study written for another issue | Ray reads `docs/DEVELOPMENT_STANDARDS.md` §1.3 and walks #182's history against it. #182's study covered #148, #149 and #155. The rule as written puts each child's findings into that child's issue, gives each child a design study of its own, and decides whether #182's study is narrowed or deleted |

## 6. Test plan

Omitted. The change touches no file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` (`docs/dev/specs/_TEMPLATE_SPEC.md`, direct path). Close-out runs the suites regardless.

## 7. Risks and rollback

The change is four edited lines and two added bullets, in three documents. Rollback is `git revert` of the Step 1 and Step 2 commits.
