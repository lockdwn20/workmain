# <Title> — Design Study | Recon

**Status:** Active | Shipped | Superseded
**Kind:** Design study | Recon
**Author:** Spanner (Role 1)
**Date:** YYYYMMDD
**Originating item:** Backlog Item #N | Ray request, YYYYMMDD

> Delete this block before use.
>
> **Filename:** subject-based, no version suffix, no date — `DESIGN_<SUBJECT>.md` for a design study, `RECON_<SUBJECT>.md` for a recon. This file is updated in place; git holds the history.
>
> **Two kinds, one template.** A *design study* explores options and makes a recommendation. A *recon* is a read-only census that reports findings and makes no recommendation at all. Pick one in the Kind field and delete the sections that don't apply — §4 Options is design-study only.
>
> This template is advisory. Add or drop sections as the work requires. Template compliance is not a Caliper review criterion.

---

## 1. Purpose

What question is this document answering, and why is it being asked now? One paragraph. If this is a recon, state the read-only contract explicitly: no code changes, no fixes, no suggestions inline with findings.

## 2. Scope of the read

What was examined, and what was deliberately not. Name the files, trees, and surfaces. A reader should be able to tell whether a given area was covered or simply not looked at — silence is the most common source of false confidence in a recon.

## 3. Findings

Every claim about existing behaviour is verified against source at authoring time and cites file and symbol. Quote verbatim where the exact wording matters.

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | | | Critical / High / Medium / Low |

Mark anything asserted-but-not-verified as such, explicitly. An unverified claim that looks verified is worse than an admitted gap.

## 4. Options *(design study only — delete for a recon)*

For each real option: what it is, what it costs, what it forecloses.

### Option A — <name>

- **Approach:**
- **Pros:**
- **Cons:**

### Option B — <name>

**Recommendation:** <which, and why>. State the rationale in terms of what the project already does — the easiest path is not automatically the correct one.

## 5. Open questions

Numbered, so answers can be cited later (`Q3 answered YYYYMMDD: ...`). Each question should be one that changes the resulting work depending on the answer. If the answer wouldn't change anything, it isn't an open question.

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | | |

## 6. Disposition

What happened to this study. Filled in when the work lands:

- Promoted to: <spec filename, Locked Architecture Decision, or backlog item>
- Superseded by: <filename, if applicable>
