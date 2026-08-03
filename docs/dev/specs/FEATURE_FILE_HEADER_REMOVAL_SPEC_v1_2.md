# Feature Spec — File Header Removal

**Author:** Spanner (Role 1)
**Date:** 20260803
**Spec version:** v1.2
**Branch:** `feature/file-header-removal` (from `dev`)
**Target release:** v1.29.0
**Originating item:** Ray request, 20260731
**Design study:** `docs/dev/design/DESIGN_FILE_HEADER_REMOVAL_20260731_v1.0.md`

## Revision history

- **v1.0** (20260803) — initial spec from Ray's Q1–Q6 answers.
- **v1.1** (20260803) — Caliper review applied. All three findings accepted after
  independent verification against live source:
  - **Finding 1** — `tests/test_recurring_meetings.py` had orphaned `Version:` /
    `Date:` lines falling in a gap between §4.1 and §4.2. §4.4 rewritten with
    explicit handling. A repo-wide transform simulation confirmed this is the only
    such file; that simulation is now **AC6.10**.
  - **Finding 2** — two further `DEVELOPMENT_STANDARDS_REVIEW.md` sections
    (lines 456–459, line 508) instruct the retired practice. Added to the §5a table
    with **AC5.6** / **AC5.7**.
  - **Finding 3** — AC5.5 was semantic and unautomatable. Replaced with a grep-based
    check rather than waived.
- **v1.2** (20260803) — Caliper re-review applied.
  - **Finding 4** — AC5.5's unanchored `\d{8}` grep false-positives on the
    `### Mistake 4: … (20251226)` heading at line 466. Caliper suggested dropping the
    pattern; **not taken** — `\d{8}` is the only grep in the list that reaches §6
    Import Organization, so dropping it would trade a false positive for a false
    negative. Anchored to a bare whole line instead, which resolves the false
    positive and keeps the coverage. Validated empirically.
  - **§6 Import Organization (lines 145–171) added to the §5a table** — found while
    validating Finding 4's grep. Its example embeds a full version header, so it
    displays the retired format as current.
  - Consistency note applied: §7 risk table said "eight sections". Corrected to
    "ten" — and while fixing it, the underlying count was found wrong in both v1.0
    and v1.1: both tallies had included the DOCSTRINGS row, which is an explicit
    *keep*. The §5a table now has eleven rows covering ten changed sections.

---

## 1. Decisions carried in from the design study

Ray answered all open questions 20260803. These are settled and are not re-opened
by this spec:

| Q | Decision |
| --- | --- |
| Q1 | **Option A** — strip version scaffolding, retain the descriptive paragraph as a PEP 257 module docstring |
| Q2 | **Option 2C** — trim `workmain/__version__.py`, but reconcile `CHANGELOG.md` first |
| Q3 | **Option 3A** — remove the ten unused package `__version__` constants in this sprint |
| Q4 | `scripts-deprecated/` — **out of scope** |
| Q5 | `.sql` migrations — **out of scope** |
| Q6 | **`feature/*` branch** — documents the minor code changes and the major documentation changes |

Ray's additional direction, incorporated into Gate 5:

- `docs/DEVELOPMENT_STANDARDS_REVIEW.md` must be modified to match the new standard.
- `CLAUDE.md` Critical Rule 1 must reflect the use of "PEP 257 module docstring".
- `CLAUDE.md` Role 1 gains: *"Any conflicts in design and project documentation will
  be resolved during planning in order to prevent implementation issues. Ray is the
  final authority on all documentation changes."*
- `docs/DEVELOPMENT_STANDARDS_REVIEW.md` is added to the "Deep Reference Docs" table.

---

## 2. Scope

**In scope:** module docstring headers in `workmain/`, `tests/`, `scripts/`; the ten
package `__version__` constants; `workmain/__version__.py`; the documentation set in
Gate 5.

**Out of scope:** `scripts-deprecated/` (Q4), `.sql` migrations (Q5), `docs/` header
blocks generally (the two docs edited in Gate 5 are edited for *content*, not to
strip their own headers), any behaviour change beyond §4.3.

### 2.1 Verified file inventory

Measured by AST parse across 192 `.py` files. `__pycache__` excluded.

| Tree | Files with a header | Header lines | Of which carry `Version History` |
| --- | ---: | ---: | ---: |
| `workmain/` (excl. `__version__.py`) | 96 | 2,726 | 89 |
| `tests/` | 61 | 1,287 | 56 |
| `scripts/` | 13 | 235 | 11 |
| `workmain/__version__.py` | 1 | 594 | 1 |
| **Total in scope** | **171** | **4,842** | **157** |

Files with **no** module docstring — untouched by Gates 1–3: 15, all package
`__init__.py` plus `scripts/sanitize_ics.py` and `setup.py`.

Note: the 14 in-scope files categorised as "plain docstring, no `Version History`"
(7 in `workmain/`, 5 in `tests/`, 2 in `scripts/`) **do** carry the title/version/date
metadata block and are therefore in scope for §4.1 metadata stripping. They are
simply exempt from §4.2. Verified by inspection — e.g. `workmain/database/connection.py`
opens `WorkmAIn` / `Database Connection v0.1.0` / `20251219`.

---

## 3. Design rules

**DR1 — Prose is preserved verbatim.** The descriptive paragraph is retained
byte-for-byte. No re-wrapping, no rewriting, no summarising. If an implementer
believes prose should change, that is a separate item and it stops at the gate.

**DR2 — The transform is AST-driven, never regex-over-the-file.**
`ast.get_docstring()` plus `module.body[0].lineno` / `.end_lineno` gives the exact
docstring line range with no false positives from strings elsewhere in the file.

**DR3 — Behaviour is provably unchanged.** Every modified file must satisfy the
AST-equality check in §6.1. A file that fails is a defect, not a judgement call.

**DR4 — No file outside the gate's declared tree is touched.**

**DR5 — Hand-handled files are enumerated, not discovered.** §4.4 lists every file
requiring human judgement. If an implementer finds a file needing judgement that is
**not** on that list, that is a spec gap: **STOP at the gate and surface to Ray.**

---

## 4. The transform

### 4.1 Metadata block removal (applies to all 170 in-scope files, Gates 1–3)

**Rule:** delete from the first line of the docstring through the first blank line
inclusive.

**This rule is verified safe, not assumed.** Across all 170 files carrying a
docstring in the three in-scope trees, the run of lines before the first blank line
was measured:

| Run length | Files |
| ---: | ---: |
| 2 lines | 1 (see §4.4) |
| 3 lines | 158 |
| 4 lines | 11 |

- Files where a prose-looking line appears inside that run: **0** (excluding the
  single §4.4 exception).
- Files whose docstring contains no blank line at all: **0**.

The 11 four-line variants are legitimate metadata (title split across two lines, or
a bare `v1.5` on its own line) and are handled correctly by the same rule:

`workmain/ai/intent_parser.py`, `workmain/cli/commands/clockify.py`,
`workmain/cli/commands/gdocs.py`, `workmain/cli/commands/slack.py`,
`workmain/integrations/clockify/__init__.py`, `workmain/integrations/clockify/auth.py`,
`workmain/integrations/clockify/client.py`, `workmain/integrations/clockify/sync.py`,
`workmain/utils/editor.py`, `workmain/workflows/eod_workflow.py`,
`tests/test_slack.py`

### 4.2 Version History block removal (applies to the 156 files that have one)

**Rule:** locate the line matching `^\s*Version History:?\s*$`. Delete that line,
any blank line(s) immediately preceding it, and every following line that is blank,
begins with `-`, or is an indented continuation (`^\s{2,}\S`).

**Stop at the first line that is non-blank, non-`-`, and non-indented.** That line
is resumed prose and must be retained.

**Four files have prose after the Version History block.** A naive "delete to end of
docstring" destroys real content in each:

| File | Content that must survive |
| --- | --- |
| `workmain/ai/prompt_builder.py` | `Workflow:` + numbered steps |
| `workmain/ai/report_generator.py` | `Workflow:` + numbered steps |
| `tests/test_ai_clients.py` | `Note: These tests make real API calls…` + run instructions |
| `tests/test_ai_foundation.py` | `Run with: python3 test_ai_foundation.py` |

### 4.3 The only intentional behaviour change

`scripts/task_pool_stale_dismissal_20260728.py:71`:

```python
parser = argparse.ArgumentParser(description=__doc__)
```

This is the **only** programmatic `__doc__` read in the repository (verified by
repo-wide grep). After §4.1/§4.2 the docstring still exists and is non-empty, so
`--help` will not break — but its text changes, and the metadata lines it currently
prints disappear.

**Required:** replace `description=__doc__` with an explicit inline description
string preserving the operational summary. Do not leave it depending on the
docstring. Handled in Gate 3.

### 4.4 The single hand-handled file

> Revised in v1.1 — Caliper Finding 1.

`tests/test_recurring_meetings.py` is the sole exception in the codebase. Its full
header, verified at lines 1–14:

```text
"""
Unit tests for recurring meetings functionality.   <- prose
Tests Phase 5.1 operational fixes.                 <- prose
                                                   <- first blank line
Version: 1.3                                       <- orphaned metadata
Date: 20260610                                     <- orphaned metadata

Version History:
- v1.0: Initial test suite with placeholder db_session fixture
...
"""
```

Two distinct problems, both requiring hand-handling:

1. **The opening two-line run is pure prose**, not metadata. Applying §4.1 blindly
   deletes the file's only description. **Exempt this file from §4.1.**
2. **`Version: 1.3` and `Date: 20260610` sit in a gap between the rules** — below the
   first blank line so §4.1 cannot reach them, above `Version History:` so §4.2's
   forward-deletion does not touch them, and not blank-lines-immediately-preceding so
   §4.2's backward sweep misses them too.

**Required handling:** apply §4.2 as normal, and **additionally delete the
`Version: 1.3` and `Date: 20260610` lines and the blank line preceding them.** These
are version metadata — precisely the content Q1/Option A retires — so removing them
is the approved decision applied to an edge case, not a new design decision.

**Expected result:**

```python
"""
Unit tests for recurring meetings functionality.
Tests Phase 5.1 operational fixes.
"""
```

**This is the only such file.** Verified by simulating §4.1 + §4.2 across all 170
in-scope files and scanning every resulting docstring for surviving metadata
(`Version:`, `Date:`, `Updated:`, `Author:`, bare `vN.N`, bare `YYYYMMDD`, `*.py vN`):
exactly one file matched, this one. Zero files produced an empty docstring. The
mechanical form of this check is **AC6.10**.

### 4.5 Resulting shape

```python
"""
Service layer for note creation. Shared by the CLI (notes add) and
action_executor (create_note). Handles client_id resolution, tag validation,
and defaults - callers pass a session and domain parameters only.
"""
```

Constraints:

- Shebang lines (`#!/usr/bin/env python3`) precede the docstring in some files and
  **must be preserved**. AST-driven editing handles this; naive "delete first N
  lines" does not.
- If the transform would leave an empty docstring, **STOP and surface to Ray** — no
  file is expected to hit this (verified: prose count is 0 in exactly 0 files).

---

## 5. Gates

Each gate is a hard stop: commit, report, **wait for Ray's explicit "proceed"**.

### Gate 0 — CHANGELOG reconciliation (prerequisite for Gate 4)

No code. Closes the Q2/2C condition before anything is deleted.

**Verified delta** — 83 unique versions in `__version__.py`, 78 in `CHANGELOG.md`:

**Documented ONLY in `__version__.py` — would be permanently lost on trim:**
`0.1.0`, `0.2.0`, `0.3.0`, `0.4.0`, `0.5.0`, `0.6.0`, `0.7.0`, `0.8.0`, `1.2.0`

**Documented only in `CHANGELOG.md`** (no action needed): `1.3.1`, `1.4.1`, `1.4.2`, `1.4.3`

This finding vindicates 2C over 2A: a straight trim would have destroyed the entire
pre-1.0 release history.

**Deliverable:** back-fill those 9 releases into `CHANGELOG.md` in Keep-a-Changelog
format, sourced verbatim from the `__version__.py` docstring entries.

**AC0.1** All 9 versions appear as `## [x.y.z]` sections in `CHANGELOG.md`.
**AC0.2** Re-running the version-set diff yields an empty "only in `__version__.py`" set.
**AC0.3** No existing CHANGELOG section is modified.

### Gate 1 — `workmain/` headers (96 files, 2,726 lines)

Apply §4.1 + §4.2. Excludes `workmain/__version__.py` (Gate 4). 89 of the 96 carry
a `Version History` block; the other 7 take §4.1 only.

**AC1.1** All 96 files transformed; §6.1 AST-equality passes on every one.
**AC1.2** No `Version History` string remains under `workmain/` except `__version__.py`.
**AC1.3** The four §4.2 files retain their post-block prose.
**AC1.4** `python -m pytest tests/` → 921 passed, 0 failed, 0 errors.
**AC1.5** `python -c "import workmain"` succeeds.

### Gate 2 — `tests/` headers (61 files, 1,287 lines)

Apply §4.1 + §4.2, honouring the §4.4 exemption. 56 of the 61 carry a
`Version History` block; the other 5 take §4.1 only.

**AC2.1** All 61 files transformed; §6.1 passes on every one.
**AC2.2** `tests/test_recurring_meetings.py` retains both prose lines (§4.4).
**AC2.3** `tests/test_ai_clients.py` and `tests/test_ai_foundation.py` retain post-block prose.
**AC2.4** `python -m pytest tests/` → 921 passed, 0 failed, 0 errors.

### Gate 3 — `scripts/` headers + argparse fix (13 files, 235 lines)

Apply §4.1 + §4.2, plus the §4.3 change. 11 of the 13 carry a `Version History`
block; the other 2 take §4.1 only.

**AC3.1** All 13 files transformed; §6.1 passes on every one.
**AC3.2** `task_pool_stale_dismissal_20260728.py` no longer references `__doc__`.
**AC3.3** `python scripts/task_pool_stale_dismissal_20260728.py --help` exits 0 and
prints a non-empty description. **Run with `--help` only — never `--execute`.**
**AC3.4** `python -m pytest tests/` → 921 passed, 0 failed, 0 errors.

### Gate 4 — Version constants

**4a.** Trim `workmain/__version__.py` to the constant plus a short docstring
pointing at `CHANGELOG.md`. **`__version__ = "1.28.0"` at line 596 must survive** —
`workmain/cli/interface.py:61` imports it and `interface.py:131` feeds it to
`@click.version_option`. Preserve `__version_info__`, `__author__`,
`__description__` if present.

**4b.** Remove the ten unused package `__version__` constants (Q3). Verified: zero
consumers repo-wide.

`workmain/ai/__init__.py:115`, `workmain/orchestration/__init__.py:26`,
`workmain/database/repositories/__init__.py:28`,
`workmain/templates_engine/__init__.py:39`, `workmain/ai/providers/__init__.py:29`,
`workmain/daemon/__init__.py:18`, `workmain/integrations/gdrive/__init__.py:34`,
`workmain/integrations/slack/__init__.py:68`, `workmain/services/__init__.py:21`,
`workmain/integrations/outlook/__init__.py:16`

**AC4.1** `workmain/__version__.py` ≤ 15 lines; `__version__ == "1.28.0"`.
**AC4.2** `workmain --version` prints the correct version.
**AC4.3** Gate 0 completed — no release history exists only in the deleted docstring.
**AC4.4** `grep -rn "^__version__" workmain/` returns exactly one hit: `__version__.py`.
**AC4.5** `python -m pytest tests/` → 921 passed, 0 failed, 0 errors.

### Gate 5 — Documentation

The standards doc is **more entangled than the design study estimated**: **ten**
sections reference the retired practice, not three — seven found while specc'ing, two
more by Caliper Finding 2, and §6 Import Organization found while validating Finding
4's grep. Every one must be reconciled or the standard silently re-grows the headers.

The table below has **eleven rows**: the ten sections to change, plus the DOCSTRINGS
row which is an explicit **keep** and does not reference the retired practice.

**5a. `docs/DEVELOPMENT_STANDARDS_REVIEW.md` → v3.0** (currently 521 lines):

| Lines | Section | Action |
| --- | --- | --- |
| 17–36 | §1 File Header Pattern | Rewrite to the PEP 257 shape (§4.5) |
| 76–101 | §4 Version History Pattern | **Delete** — practice retired |
| 102–144 | §5 Package `__init__.py` Pattern | Remove the version-history docstring from the example; **delete standard #4 "`__version__` at module level"** and the `__version__ = '1.2'` line — this is the rule that mandated the Q3 constants |
| 145–171 | §6 Import Organization | **Trim the example's header** to the §4.5 PEP 257 shape. The section's subject is import ordering, but its `notes_repo.py` example embeds a full `WorkmAIn Notes Repository` / `Notes Repository v1.3` / `20251222` header, displaying the retired format as current |
| 191–209 | FILE VERSIONING | **Delete** — incl. the stale "In header comment for SQL files" claim (recon: no `.sql` file has a version block) |
| 210–311 | VERSION TRACKING LOCATIONS | Rewrite: git tags + `CHANGELOG.md` + `workmain/__version__.py` are the tracking locations. Drop "File headers (Each .py file)". Drop the `grep -r "v[0-9]"` and `head -15 … \| grep "v[0-9]"` recipes — they no longer find anything |
| 456–459 | Mistake 2: Removed `__init__.py` Structure | **Rewrite** — its "**Right**: Full docstring, version history, `__all__`, `__version__`" line instructs the retired practice as the *correct* pattern. Must become "Full docstring, `__all__`" |
| 471–477 | Mistake 5 | Rewrite or delete — cites SESSION_HANDOFF as version source of truth |
| 489–496 | SUMMARY → Version Tracking | Rewrite the ✅/❌ list |
| 508 | SUMMARY → Code Quality | **Delete** the `✅ Version history in files` bullet — marks the retired practice as a quality standard |
| 410–434 | DOCSTRINGS | **Keep unchanged** — Google-style function docstrings are unaffected |

Also update the doc's own `Version History:` block with a v3.0 entry (this doc's own
header is a `docs/` header and stays — Q5/§2 keeps `docs/` out of scope).

**5b. `CLAUDE.md`** — three edits, per Ray:

1. **Critical Rule 1 (File Versioning)** — rewrite to state that module headers are
   PEP 257 module docstrings: a description only, no version, no date, no version
   history; git is the version record.
2. **Role 1 section** — append: *"Any conflicts in design and project documentation
   will be resolved during planning in order to prevent implementation issues. Ray
   is the final authority on all documentation changes."*
3. **Deep Reference Docs table** — add a `docs/DEVELOPMENT_STANDARDS_REVIEW.md` row.
   Suggested *When to Read*: "Before writing any new module or package."

**5c. `docs/GIT_WORKFLOW_STANDARDS.md`** — add one sentence covering
behaviour-neutral changes that touch code files, so the `chore/*` vs `feature/*`
question this sprint raised is settled for the next one. **Flagged for Ray's
approval at the gate — Ray is final authority on documentation changes (§5b.2).**

**AC5.1** No section of `DEVELOPMENT_STANDARDS_REVIEW.md` instructs adding a version
header, a `Version History:` block, or a package-level `__version__`.
**AC5.2** `CLAUDE.md` Rule 1 names "PEP 257 module docstring" explicitly.
**AC5.3** The Role 1 sentence appears verbatim as Ray worded it.
**AC5.4** The Deep Reference Docs table contains the new row.
**AC5.5** No remaining contradiction between `CLAUDE.md` and
`DEVELOPMENT_STANDARDS_REVIEW.md` on file headers. *(Caliper Finding 3: this was
semantic and unautomatable as originally worded. Replaced with the mechanical
check below — the judgement is now made once here, at spec time, rather than left
to the implementer.)*

Mechanically: in `docs/DEVELOPMENT_STANDARDS_REVIEW.md`, **each of these greps must
return zero hits**, excluding the doc's own `Version History:` header block (which
is a `docs/` header and stays per §2):

- `Version History` — outside the doc's own header block
- `__version__` — the package-level constant standard
- `^\s*-\s*v\d+\.\d+:` — version-history entry examples
- `^[[:space:]]*[0-9]{8}[[:space:]]*$` — a **bare** date line in a header example.
  Anchored to a whole line by Caliper Finding 4: an unanchored `\d{8}` also matches
  the `### Mistake 4: Tests in Wrong Directory (20251226)` heading at line 466, which
  has nothing to do with the retired practice. Verified: the anchored form matches
  lines 3, 23, 83, 108, 152, 219, 256 (all header-example dates, all in sections this
  gate rewrites or deletes) and matches neither the Mistake 4 nor Mistake 5 heading.
  Line 3 is the doc's own header date and is covered by the exclusion above.
- `Component Name v` / `File Header Pattern`

**AC5.6 / AC5.7** Both greps below return zero hits (Caliper Finding 2 — line 508
and lines 456–459 respectively):

```bash
grep -n "Version history in files"  docs/DEVELOPMENT_STANDARDS_REVIEW.md   # AC5.6
grep -n "version history, "         docs/DEVELOPMENT_STANDARDS_REVIEW.md   # AC5.7
```

### Gate 6 — Verification and release prep

**AC6.1** Repo-wide: `grep -rn "Version History" --include="*.py" .` returns **zero**
hits outside `scripts-deprecated/` (Q4, out of scope).
**AC6.2** §6.1 AST-equality passes across every file modified in Gates 1–3.
**AC6.3** `python -m pytest tests/` → 921 passed, 0 failed, 0 errors.
**AC6.4** `workmain --version` and `workmain --help` both succeed.
**AC6.5** Line-count reduction reported against the §2.1 baseline.
**AC6.6** Version bumped to **v1.29.0**; `CHANGELOG.md` entry added.
**AC6.7** Merge to `dev` (`--no-ff`), then **open** the `dev → main` PR with
`gh pr create` and **STOP**. Ray merges the PR himself — never run `gh pr merge`.
**AC6.8** After Ray merges: tag `v1.29.0`, push tags, create the GitHub Release
object (`gh release create` — the tag alone is not a release, per
`GIT_WORKFLOW_STANDARDS.md` lines 104–110).
**AC6.9** Restart `workmain-notify.service` and confirm `ActiveEnterTimestamp`
postdates the merge — a `dev` merge is not live until the daemon restarts.
**AC6.10 — metadata residue scan.** Parse every in-scope file's resulting module
docstring and assert that **no line** matches `Version:`, `Date:`, `Updated:`,
`Author:`, a bare `vN.N`, a bare `YYYYMMDD`, or `*.py vN`, and that **no docstring
is empty**. This is the mechanical guard against Caliper Finding 1's failure class —
metadata stranded in a gap between §4.1 and §4.2. Pre-verified expectation: zero
hits once §4.4 is applied.

---

## 6. Verification method

### 6.1 The mechanical proof of zero behaviour change

For every file modified in Gates 1–3:

```python
import ast
before = ast.parse(original_source)
after  = ast.parse(modified_source)
# drop the module docstring node from the ORIGINAL tree
if (before.body and isinstance(before.body[0], ast.Expr)
        and isinstance(before.body[0].value, ast.Constant)
        and isinstance(before.body[0].value.value, str)):
    before.body.pop(0)
# and from the MODIFIED tree
if (after.body and isinstance(after.body[0], ast.Expr)
        and isinstance(after.body[0].value, ast.Constant)
        and isinstance(after.body[0].value.value, str)):
    after.body.pop(0)
assert ast.dump(before) == ast.dump(after), f"{path}: non-docstring content changed"
```

This is a hard, automatable proof that nothing but the module docstring moved. It
satisfies Caliper review criterion 1 (mechanically testable acceptance criteria).

The verification script is a throwaway — place it in the session scratchpad, **not**
in `scripts/`, and do not commit it.

### 6.2 Test baseline

**921 passed, 0 failed, 0 errors.** Verified safe to hold flat: **no test asserts on
any docstring or header**. The `Version History` grep hits under `tests/` are the
test files' own headers and nothing more.

Any deviation from 921 is a defect — **STOP and surface to Ray.**

---

## 7. Risks

| Risk | Mitigation |
| --- | --- |
| Prose lost to an over-broad delete | §4.1 rule verified against all 170 files; §4.2 stops at resumed prose; 4 affected files enumerated |
| `tests/test_recurring_meetings.py` prose destroyed | §4.4 exemption, called out with its own AC (AC2.2) |
| Pre-1.0 release history destroyed | Gate 0 back-fills 9 releases before Gate 4 deletes anything |
| `workmain --version` breaks | AC4.1/AC4.2; `interface.py:61` + `:131` dependency stated explicitly |
| Shebang clobbered | DR2 AST-driven editing; §4.5 constraint |
| Standards doc re-grows the practice | Gate 5 reconciles all ten sections; AC5.5 |
| One-off script `--help` regresses | §4.3 explicit fix; AC3.3 — `--help` only, never `--execute` |
| Metadata stranded in a gap between §4.1 and §4.2 | AC6.10 residue scan; §4.4 handles the one known instance (Caliper Finding 1) |
| Standards doc retains an instruction the §5a table missed | AC5.5/5.6/5.7 grep checks rather than a semantic read (Caliper Findings 2, 3) |
| Implementer hits an unlisted judgement call | DR5 — stop at the gate, surface to Ray |

---

## 8. Expected outcome

- **~2,900 lines removed** — every one of them genuinely held by git.
- **~1,967 lines of module-purpose prose preserved** — the material git does not hold.
- Test count unchanged at 921. No behaviour change beyond §4.3.
- `CLAUDE.md` and `DEVELOPMENT_STANDARDS_REVIEW.md` agree on file headers for the
  first time since Rule 1 was written.

**On sprint close:** the design study
(`docs/dev/design/DESIGN_FILE_HEADER_REMOVAL_20260731_v1.0.md`) and this spec retire
to `docs/dev/archive/`, per the Documentation Standards in `CLAUDE.md`.

---

## 9. Status

**CALIPER REVIEW COMPLETE — Findings 1–3 applied in v1.1, Finding 4 and the
consistency note applied in v1.2. Caliper approved pending Finding 4, now resolved.**

**AWAITING RAY'S APPROVAL TO BEGIN GATE 0.**

No implementation may begin until Ray approves this spec.
