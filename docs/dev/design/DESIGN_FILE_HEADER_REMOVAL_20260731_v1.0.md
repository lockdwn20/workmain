# Design Study — File Header Removal

**Author:** Spanner (Role 1)
**Date:** 20260731
**Status:** OPEN — no decision made. Options presented for Ray's analysis.
**Branch:** `chore/file-header-removal`

---

## 1. Purpose

Ray has asked to plan the removal of file headers across the application, with two
stated goals:

1. **Lower context** — headers consume tokens on every file read.
2. **Bring the application in line with current standards** — version history is
   already tracked in GIT.

This study establishes the verified blast radius, isolates the decisions that must
be made before a spec can be written, and gives a recommendation on each. It does
not authorise any change.

**Nothing in this document has been decided.** Every option below is live.

---

## 2. What a "file header" actually is here

The pattern is defined in `docs/DEVELOPMENT_STANDARDS_REVIEW.md` lines 17–35 and
211–228, and appears as a module-level docstring:

```python
"""
WorkmAIn Notes Service            <- title line
Notes Service v1.2                <- component + version   } metadata
20260728                          <- date (YYYYMMDD)        }

Service layer for note creation. Shared by the CLI (notes add) and
action_executor (create_note). Handles client_id resolution, tag validation,
and defaults - callers pass a session and domain parameters only.
                                  ^ descriptive prose

Version History:
- v1.0: Initial implementation
- v1.1: Item 69 Gate 1 - add created_at backdate param to create_note() ...
- v1.2: Item 69 Gate 2 - add update_note(), a general single-call note update ...
"""
```

Source: `workmain/services/notes_service.py` lines 1–20, quoted verbatim.

The header is therefore **three distinct things fused into one docstring**, and they
have different relationships to git:

| Part | Lines (repo-wide) | Reproduced by git? |
| --- | --- | --- |
| Title / `Component vN.N` / date | 322 | Yes — tag + `git log` |
| `Version History:` block | 2,019 | Yes — that *is* what git log is |
| Descriptive prose | 1,967 | **No** — git records what changed, never what a module is for |

Counts exclude `workmain/__version__.py`, which is treated separately in §5.

This split is the crux of the study. The "already tracked via GIT" rationale is
airtight for the first two rows and does not apply to the third.

---

## 3. Verified blast radius

Measured by AST parse (`ast.get_docstring` + `body[0].lineno/end_lineno`) across all
192 `.py` files in `workmain/`, `tests/`, `scripts/`, `scripts-deprecated/`, and
`setup.py`. `__pycache__` excluded.

### 3.1 File categories

| Category | Files | Header lines |
| --- | ---: | ---: |
| Versioned header (has `Version History:`) | 160 | 4,842 |
| Plain module docstring, no version block | 16 | 60 |
| No module docstring at all | 16 | — |
| **Total** | **192** | **4,902** |

Total Python in repo: **53,653 lines**. Headers are **9.1%** of the tree.

### 3.2 Versioned headers by tree

| Tree | Files | Header lines |
| --- | ---: | ---: |
| `workmain/` | 90 | 3,256 |
| `tests/` | 56 | 1,243 |
| `scripts/` | 11 | 221 |
| `scripts-deprecated/` | 3 | 46 |

`workmain/__version__.py` contributes 594 of the `workmain/` total on its own.

### 3.3 Largest headers

| Header lines | % of file | File |
| ---: | ---: | --- |
| 594 | 99.0% | `workmain/__version__.py` |
| 107 | 14.6% | `workmain/daemon/daemon.py` |
| 102 | 7.1% | `workmain/workflows/eod_workflow.py` |
| 96 | 16.7% | `workmain/daemon/scheduler.py` |
| 91 | 28.7% | `workmain/cli/commands/eod.py` |
| 88 | 11.3% | `workmain/utils/ics_parser.py` |
| 87 | 8.9% | `workmain/cli/commands/reports.py` |
| 75 | 6.2% | `workmain/cli/commands/notes.py` |
| 73 | 3.8% | `workmain/cli/commands/meetings.py` |
| 70 | 11.6% | `workmain/ai/prompt_builder.py` |

### 3.4 The finding that shapes the decision

**Zero of the 176 headers are pure version metadata.** Every single one carries
descriptive prose. There is no subset of files where "delete the docstring" and
"delete the version tracking" are the same operation.

---

## 4. DECISION 1 — How far does the removal go?

### Option A — Strip the version scaffolding, keep the prose *(Spanner recommends)*

Remove the title / version / date lines and the entire `Version History:` block.
Retain the descriptive paragraph as a normal PEP 257 module docstring.

```python
"""
Service layer for note creation. Shared by the CLI (notes add) and
action_executor (create_note). Handles client_id resolution, tag validation,
and defaults - callers pass a session and domain parameters only.
"""
```

- **Removes:** ~2,341 lines (~4.4% of the tree)
- **Pros:** Every removed line is genuinely recoverable from git, which is exactly
  the stated rationale. Module docstrings are the current Python standard, so this
  is what "in line with current standards" points at. Preserves 1,967 lines of
  orientation prose that materially reduces the cost of reading unfamiliar modules —
  which serves the *context* goal too, since a reader who has to reconstruct a
  module's purpose from its code spends far more context than the docstring cost.
- **Cons:** Roughly half the available savings. Requires a two-part transform
  (metadata lines + history block) rather than one deletion, so the tooling is
  marginally more involved. Leaves a judgement call on headers whose prose is thin.

### Option B — Remove the header docstring entirely

Delete the whole module docstring from every file.

- **Removes:** ~4,308 lines (~8.1% of the tree)
- **Pros:** Maximum context reduction, near double Option A. Single unambiguous
  rule, trivially mechanised, no per-file judgement. Matches the most literal
  reading of CLAUDE.md Rule 1.
- **Cons:** Destroys 1,967 lines of module-purpose prose that git does **not**
  reproduce. The "already tracked via GIT" justification does not cover this
  material — it is the one part of the header git has never held. Recovery later
  means reading each module and rewriting it from scratch. Also leaves files opening
  directly on imports, which is a step away from PEP 257 rather than toward it.

### Option C — Remove the `Version History:` block only

Leave the title / version / date metadata lines intact.

- **Removes:** ~2,019 lines (~3.8% of the tree)
- **Pros:** Most conservative, smallest diff, zero information loss.
- **Cons:** Retains a per-file `Component vN.N` marker that git already supersedes
  and that CLAUDE.md Rule 1 explicitly retires — so it leaves the practice's most
  drift-prone artefact in place. Every future edit still poses "do I bump this?"
  Spanner's view: this preserves the wrong half.

### Recommendation on Decision 1

**Option A.** It removes everything the git rationale actually justifies, and stops
exactly where that rationale stops. Option B is the easier transform, but the
easiest way is not the correct way when the difference is 1,967 lines of
documentation that no other system holds.

If raw context reduction outranks that, Option B is defensible and will be specced
cleanly — but it should be chosen deliberately, on the record, not arrived at
because the `sed` was simpler.

---

## 5. DECISION 2 — `workmain/__version__.py`

**Current state:** 600 lines, of which **594 are the docstring** — 83 `- vN.N.N:`
entries running from the earliest release to v1.28.0.

**Constraints verified against source:**

- CLAUDE.md names this file the canonical version store ("**Version:**
  `workmain/__version__.py`").
- `workmain/cli/interface.py:61` does `from workmain.__version__ import __version__`,
  consumed at `interface.py:131` by `@click.version_option`. **The constant at
  `__version__.py:596` must survive any option below.**
- `CHANGELOG.md` independently carries **79 release sections** against the docstring's
  83 entries — substantially the same ground, maintained in Keep-a-Changelog format.
- No code anywhere reads the docstring. Verified: the only `__doc__` read in the
  entire repo is the argparse site in §7.1.

### Option 2A — Trim to the constant plus a pointer *(Spanner recommends)*

Keep `__version__ = "1.28.0"` and a short docstring pointing at `CHANGELOG.md`.

- **Removes:** ~590 lines from a single file — 12% of all header lines in the repo.
- **Pros:** Largest single-file win available. The content is duplicative of a file
  that is already the maintained release record. Eliminates the standing obligation
  to write every release note twice.
- **Cons:** CHANGELOG.md must be accepted as canonical for release history. The 83-vs-79
  gap is unexplained until checked (see 2C).

### Option 2B — Leave fully intact

Exempt the file from this sprint.

- **Pros:** Zero risk to the canonical version store. CLAUDE.md needs no amendment here.
- **Cons:** Leaves the single largest header in the repo untouched — a 600-line file
  that is 99% header. If the sprint's purpose is context reduction, skipping this
  file forgoes the highest-density target in the codebase.

### Option 2C — Trim, but reconcile CHANGELOG first

As 2A, preceded by a gate that diffs the 83 docstring entries against CHANGELOG.md's
79 sections and back-fills any release documented only in the docstring.

- **Pros:** Guarantees no release history is lost. Turns the 83-vs-79 gap from an
  assumption into a verified fact before anything is deleted.
- **Cons:** One extra gate. The gap may prove to be nothing more than point-releases
  folded into a single CHANGELOG section.

### Recommendation on Decision 2

**Option 2C.** The trim is right, but the 83-vs-79 gap is currently an *assumption*
and this document should not let an assumption authorise a 590-line deletion. One
gate converts it to a fact. If the diff comes back clean, 2C collapses into 2A at
negligible cost.

---

## 6. DECISION 3 — Unused `__version__` constants in package `__init__.py`

Ten package `__init__.py` files carry a module version constant:

| File | Value |
| --- | --- |
| `workmain/ai/__init__.py:115` | `'1.5'` |
| `workmain/orchestration/__init__.py:26` | `'1.0'` |
| `workmain/database/repositories/__init__.py:28` | `"1.3"` |
| `workmain/templates_engine/__init__.py:39` | `'1.3'` |
| `workmain/ai/providers/__init__.py:29` | `'1.0'` |
| `workmain/daemon/__init__.py:18` | `"1.0"` |
| `workmain/integrations/gdrive/__init__.py:34` | `"1.0"` |
| `workmain/integrations/slack/__init__.py:68` | `"1.5"` |
| `workmain/services/__init__.py:21` | `"1.0"` |
| `workmain/integrations/outlook/__init__.py:16` | `"1.0"` |

**Verified: nothing reads any of them.** The only `__version__` import anywhere in
the repo is `interface.py:61`, which targets `workmain/__version__.py` (the app
version), not any package constant.

These are the same per-file versioning practice expressed as code rather than as a
docstring.

- **Option 3A — remove in this sprint (recommended).** Same practice, same rationale,
  verified zero consumers. Leaving them means the sprint claims to retire per-file
  versioning while ten instances survive in executable form.
- **Option 3B — out of scope.** Keeps the sprint strictly to docstrings; constants
  become a backlog item. Cost: the job is knowingly left half-done, and a future
  reader has no way to tell the survivors were deliberate.

---

## 7. Collateral that must move with the change

These are not optional extras. If they are not in the same branch, the change is
incomplete or actively broken.

### 7.1 `scripts/task_pool_stale_dismissal_20260728.py:71` — the only `__doc__` consumer

```python
parser = argparse.ArgumentParser(description=__doc__)
```

This is the **only** programmatic docstring read in the repository. Under Option B
(and under Option A if the prose is trimmed hard) `description` silently becomes
`None` and the script's `--help` goes blank. **This is a real behaviour change, not
a cosmetic one.** It must be replaced with an explicit inline description string.

### 7.2 `docs/DEVELOPMENT_STANDARDS_REVIEW.md` — currently contradicts CLAUDE.md

The doc mandates the header in three places:

- Lines 17–35 — "File Header Pattern", with the format spec
- Lines 211–228 — "Where Versions ARE Tracked → 1. File Headers (Each .py file)"
- Lines 281–291 — "Single Source of Truth: ... File headers provide self-documentation"

CLAUDE.md Rule 1 already retires the practice. **These two documents are in direct
conflict today.** If the standards doc is not amended in the same branch, the
standard silently re-grows the headers on the next module written against it.

### 7.3 CLAUDE.md Rule 1 wording

Current text:

> Previous file versioning denoted by a Header beginning and ending with `"""` should
> be removed to include the accompanying version history within the header.

This sentence is ambiguous — it can be read as "remove the header, including its
version history" (Option B) or "remove the versioning, including the version
history" (Option A). Whichever option is chosen, **Rule 1 should be rewritten to
state it unambiguously**, since this study exists partly because the rule as written
does not settle the question.

### 7.4 Scope boundaries to confirm

- **`tests/`** — 56 files, 1,243 header lines. Recommend in scope; same rationale applies.
- **`scripts-deprecated/`** — 3 files, 46 lines. CLAUDE.md: excluded from test
  collection, "do NOT add to it". Recommend **out of scope** — it is frozen legacy,
  and touching it produces churn with no reader to benefit.
- **`.sql` migrations** — 23 files in `workmain/database/migrations/`, all 23 opening
  with a `--` comment block, **114 comment lines total**. Verified: **none contains a
  `Version History:` block** — they are pure descriptive comments explaining what the
  migration does (e.g. `023_task_status_orphan_backfill.sql` lines 1–4). Recommend
  **out of scope**: they carry no version scaffolding, migrations are immutable
  historical records, and 114 lines across the whole set is negligible context.
- **`docs/`** — out of scope. Doc headers are a separate practice with separate value.

---

## 8. Mechanics and verification

The transform is mechanically verifiable, which matters for Caliper's review
criterion 1 (mechanically testable acceptance criteria).

**Transform:** AST-driven, not regex. `ast.get_docstring()` plus
`module.body[0].lineno` / `.end_lineno` yields the exact line range of every module
docstring with no false positives from strings elsewhere in the file.

**Proposed mechanical AC — proves zero behaviour change:**

For every modified file, parse the before and after sources, delete the module
docstring node from the *before* AST, and assert `ast.dump()` equality of the two
trees. This is a hard, automatable proof that nothing but the docstring moved. Any
file failing the assertion is a defect, not a judgement call.

**Supporting ACs:**

- `python -m pytest tests/` holds at the 921-test baseline, 0 failures, 0 errors.
  Confirmed safe: **no test asserts on any docstring or header** — the `Version
  History` grep hits under `tests/` are the test files' own headers, nothing more.
- `python -c "import workmain"` and `workmain --version` both succeed
  (guards `interface.py:131`).
- The §7.1 argparse site emits non-empty `--help` output.

**Sequencing note:** this touches ~176 files. Recommend gating by tree
(`workmain/` → `tests/` → `scripts/` → docs/collateral) so each gate has a bounded,
reviewable diff, rather than one 176-file commit that cannot be meaningfully reviewed.

---

## 9. Open questions for Ray

| # | Question | Spanner's recommendation |
| --- | --- | --- |
| Q1 | Decision 1 — scaffolding only, full removal, or history only? | **Option A** |
| Q2 | Decision 2 — `workmain/__version__.py` treatment? | **Option 2C** |
| Q3 | Decision 3 — remove the ten unused `__init__.py` constants? | **Option 3A** |
| Q4 | Is `scripts-deprecated/` in scope? | **No** — frozen legacy |
| Q5 | Are `.sql` migration files in scope? | **No** — recon done, §7.4; no version blocks present |
| Q6 | Branch type — `chore/*` or `feature/*`? | See below |
| Q7 | Version bump and tag, or not? | See below |

### On Q6 / Q7 — branch and release handling

`docs/GIT_WORKFLOW_STANDARDS.md` v1.6 scopes `chore/*` to documentation-only changes:
branch from main, merge to both main and dev, no version bump, no tag.

This change is **doc-only in nature but code-file in location** — it edits ~176 `.py`
files while (under the mechanical AC in §8) provably changing no behaviour. That is
precisely the case the standard does not currently address, and it is a genuine
judgement call rather than an oversight on Ray's part.

Spanner's view: the *intent* test is the right one, so `chore/*` fits and no version
bump or tag is warranted — with two caveats that argue the other way:

1. The §7.1 argparse fix **is** a behaviour change, however small.
2. A 176-file diff touching the whole package is not what a reader expects a `chore/*`
   branch to contain.

This is Ray's call. Whichever way it goes, `docs/GIT_WORKFLOW_STANDARDS.md` should
gain a sentence covering behaviour-neutral code-file changes, so the next one does
not re-litigate this.

---

## 10. Summary

- Headers are **9.1%** of the Python tree (4,902 of 53,653 lines).
- They fuse three things: metadata (322 lines), version history (2,019 lines), and
  **descriptive prose (1,967 lines)**. Git reproduces the first two and not the third.
- **No header is pure version metadata** — "delete the docstring" and "delete the
  version tracking" are not the same operation in any file in this repo.
- Recommended package: **Option A + 2C + 3A**, scripts-deprecated out of scope,
  removing roughly **2,900 lines** — all of it genuinely held by git — while
  preserving module-purpose documentation that nothing else holds.
- Three collateral items (§7.1 argparse, §7.2 standards doc, §7.3 CLAUDE.md Rule 1)
  must ride the same branch or the change is incomplete.

**No spec will be written until Q1–Q3 and Q6 are answered.**
