# Structured Issue Acceptance Criteria — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261006
**Originating item:** Issue #120

---

## 1. Purpose

Issue #120 asks the issue schema to carry an acceptance criterion's property and its check as separate fields, and asks the validator to reject a criterion that states only a command. The shape of the fields and the recursion that validates them are settled by the existing mechanism (§3). Three questions are not: how much the validator can reject beyond a missing field, how a two-field criterion renders on GitHub, and what happens to the real issue AC3 requires be created. Each changes the spec.

## 2. Scope of the read

Read: `.github/ISSUE_TEMPLATE/issue.schema.json`, `.github/ISSUE_TEMPLATE/issue.template.json`, `automation/issue_validator.py`, `automation/issue_validator_test.py`, `automation/fixtures/*.json`, `docs/DEVELOPMENT_STANDARDS.md` §1.2, §1.5, §2.2, §6, `docs/dev/specs/_TEMPLATE_SPEC.md` §5, `.claude/skills/closeout/`, `automation/closeout_acs.py`.

Searched the whole repository outside `docs/archive/` for `issue.schema`, `issue.template`, `issue_validator`, and `acs` to find every consumer of the field. Not read: existing issues' bodies, which #120 leaves untouched.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | `acs` is an array whose items are typed by a bare type name, `"items": "string"`; `single_line` sits on the array and applies to each string item. | `.github/ISSUE_TEMPLATE/issue.schema.json:11-17` | — |
| F2 | `validate_schema` handles only scalar item types. `_check_type` knows `integer`, `string`, `array`; there is no object type and no recursion into an item. Its key checks — unknown key, missing required key, null, type, non-empty, `max_length`, `single_line` — are all per-key and reusable on a nested object unchanged. | `automation/issue_validator.py:104-111` `_check_type`; `:114-172` `validate_schema` |  — |
| F3 | The validator is the only reader of `acs`. It reads it once, in `main`, to render the body. Nothing in `automation/`, `.claude/skills/closeout/` or `workmain/` parses an issue body's ACs back out; `closeout_acs.py` reads spec and results tables only. | `automation/issue_validator.py:346`; `automation/closeout_acs.py:43-46` (`_SPEC_AC_ROW_RE` on spec rows) | — |
| F4 | `render_body` emits one `- ` bullet per string AC. The `single_line` rule exists because of that render: a newline inside an AC would split its bullet. | `automation/issue_validator.py:94-101` `_has_line_break`; `:227-230` `render_body` | — |
| F5 | `--new` prints the template file verbatim, so the skeleton's shape is whatever `issue.template.json` holds — today `"acs": []`, which shows no item shape at all. | `automation/issue_validator.py:315-318`; `.github/ISSUE_TEMPLATE/issue.template.json:4` | — |
| F6 | §1.2 states the issue-side half of the rule in terms of the current shape: "where `.github/ISSUE_TEMPLATE/issue.schema.json` types an acceptance criterion as one string, the wording is what carries that separation instead." It becomes false the moment the schema changes. | `docs/DEVELOPMENT_STANDARDS.md:67` | — |
| F7 | `build_command` adds `--project "WorkmAIn Queue"` to every create, so any issue made through `--create` joins the board. | `automation/issue_validator.py:253` | — |
| F8 | The spec template's §5 already names the two halves `Criterion` and `How it is checked`. | `docs/dev/specs/_TEMPLATE_SPEC.md` §5 | — |

**Settled by the findings, not open:** each `acs` item becomes an object with two required, non-empty, single-line string fields. The item's schema is written in the same key-spec form as the top level, and `validate_schema` validates it by calling itself on each item, so every existing per-key rule applies to the nested fields with no new mechanism (F2). Errors name the path, `acs[1].criterion`. Field names follow F8: `criterion` and `check`. A legacy string item fails the type check by name.

## 4. Options

Three independent questions, D1–D3.

### D1 — What the validator rejects beyond a missing field

Structure alone makes a missing or empty `criterion` unrepresentable. It does not stop an author writing the command into `criterion` — which is the flattened form again, in the field built for the property.

#### Option D1-A — Structure only

- **Approach:** both fields required, non-empty, single-line. Nothing reads their content.
- **Pros:** no content rule to maintain; no false rejection possible.
- **Cons:** `{"criterion": "`grep -rn x workmain/`", "check": "`grep -rn x workmain/`"}` validates. The issue's second AC — a criterion that states only a command is rejected — is met only for the case where the author leaves `criterion` empty.

#### Option D1-B — Structure plus two content rules on `criterion`

- **Approach:** in addition to D1-A, reject a `criterion` that (1) has no text left once its backtick code spans, whitespace and punctuation are removed, or (2) contains verbatim any backtick code span that also appears in its own `check`.
- **Pros:** rejects the bare-command criterion and the criterion that restates its check, which are the two mechanical forms of "the command is the criterion". §1.2's good example passes: its criterion's only code span is `workmain/`, which its check does not carry as a span of its own. Neither rule needs a list of commands — both compare the entry against itself.
- **Cons:** a criterion written as a command plus prose with a different check text still passes (`` `grep x` returns zero hits `` with check "run it"). What separates a property from a description of a command's output is a reading, and stays with §1.2's wording rule and Caliper's question 7.

A third approach, recognising commands in `criterion` by name, needs a list of command names — a hand-maintained register — and is not offered.

**Recommendation: D1-B.** The issue's purpose is that the flattened form cannot be created through the supported path. Under D1-A the flattened form moves into the `criterion` field and validates. D1-B closes the two forms a validator can see without a register, and the spec states the residual case as the boundary where §1.2 and review take over.

### D2 — How a criterion renders on GitHub

#### Option D2-A — Nested bullet

- **Approach:** `- <criterion>` with a child bullet `  - Checked by: <check>`.
- **Pros:** no escaping; long criteria wrap naturally; unchanged `**ACs**` heading and bullet list, so the body reads like every existing issue with one added line per criterion.
- **Cons:** the two halves are distinguished by indentation and a label, not by columns.

#### Option D2-B — Table, `Criterion | How it is checked`

- **Approach:** a two-column Markdown table matching the spec template's §5 (F8).
- **Pros:** visually identical to the spec's AC table, so mapping issue ACs to spec ACs is column-to-column.
- **Cons:** every `|` in a check must be escaped as `\|` — commands piped through `jq` or `grep` are common in this project's checks (§1.6's own command has two); long prose in a narrow table cell reads poorly on GitHub's issue view.

**Recommendation: D2-A.** The separation is visible either way. D2-A needs no escaping rule, so a check can never render differently from how it was written.

### D3 — The issue AC3 requires be created

AC3 is checked by reading an issue created from a test payload. That issue joins the board (F7) and outlives the check.

#### Option D3-A — Create through `--create`, then close as not planned

- **Approach:** the step runs `python3 automation/issue_validator.py <payload> --create`; Ray reads the body; it is closed with `gh issue close <N> --reason "not planned"`.
- **Pros:** exercises the supported entry path end to end, the one AC2 names; the issue stays resolvable, so the results artifact cites it as evidence; no authorization point.
- **Cons:** a closed test issue remains in the repository and on the board (filtered out of §1.6's `is:open` read).

#### Option D3-B — Create through `--create`, then delete

- **Approach:** as D3-A, then `gh issue delete <N>` once Ray has read it.
- **Pros:** no residue.
- **Cons:** deleting a GitHub object is an authorization point (§1.4); the evidence the results artifact cites stops resolving.

#### Option D3-C — Render only, through `gh api markdown`

- **Approach:** post the rendered body to GitHub's Markdown endpoint and read the HTML; no issue is created.
- **Pros:** no write to GitHub at all.
- **Cons:** never exercises `--create`; AC3 as worded names a created issue, so the AC would be restated to something weaker than what was asked.

**Recommendation: D3-A.** It is the only option that checks the rendered body on the path authors actually use and leaves durable evidence, and it adds no authorization point.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | D1: structure only, or structure plus the two content rules? | Answered 20261007: D1-B. Rule (2) as written here also refuses §1.2's own good form when a check names a path; the spec proposes narrowing it to spans containing whitespace, pending Ray |
| Q2 | D2: nested bullet or table? | Answered 20261007: D2-A |
| Q3 | D3: close the test issue as not planned, delete it, or render without creating? | Answered 20261007: D3-A, a one-time check |

## 6. Disposition

- Promoted to: `../specs/ISSUE_AC_FIELDS_SPEC.md`
- Superseded by:
