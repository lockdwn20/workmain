WorkmAIn
Feature Backlog v5.25
20260623

# WorkmAIn Feature Backlog

Items deferred from various phases for future implementation.

**Version History:**

- v1.0 (20251224): Initial backlog with Phase 2 & 3 deferrals
- v2.0 (20251226): Added Phase 3.5/Pre-Phase 4 deferrals
- v3.0 (20260127): Added Phase 5.1 deferrals
- v3.1 (20260210): Added AI provider management items
- v3.2 (20260303): Added CLI Sprint deferral (clockify report subcommand)
- v3.3 (20260305): Added Phase 6 technical debt (email.py internal session)
- v3.4 (20260309): Added Phase 7 technical debt (datetime.utcnow) and pre-Phase 15 test debt (Items 14–16)
- v3.6 (20260311): Added Phase 8 deferral (eod day-aware → Phase 9)
- v3.7 (20260311): Retargeted Item 17 → Phase 9; added Item 18 (templates preview ImportError)
- v3.8 (20260319): Items 17 and 18 marked COMPLETE (Phase 9, v1.6.0)
- v4.0 (20260421): Phase restructure (old 12→14, 13→15). Added Items 19–22.
- v4.1 (20260421): Restored accidentally dropped Items 23–26.
- v4.2 (20260501): Item 26 marked COMPLETE (v1.10.0).
- v5.0 (20260504): Structural overhaul — Quick Reference Register added; Items 27–29 assigned to previously unnumbered items; standard template enforced; duplicate changelog blocks and math errors removed.
- v5.1 (20260504): Backlog Item Template added; Philosophy on Deferrals moved before register; Summary Statistics moved after register; Status column last in register, simplified to ✓ complete only; items in numerical order.
- v5.2 (20260504): Collapsed Open Items / Conditional / Deferred Indefinitely / Completed into one flat ## Backlog Items section, all 29 items in numerical order. Status tracked in each item's fields and the register — no section moves needed when status changes.
- v5.3 (20260505): Added Item 30 — System Service Promotion for workmain-notify (Phase 10 deferral); updated register and statistics.
- v5.4 (20260508): Item 27 marked COMPLETE (v1.12.0).
- v5.5 (20260512): Item 20 marked COMPLETE (v1.13.0); Item 24 re-targeted to Phase 15 (Phase 11 did not expand tasks scope); Item 28 updated (clients delivered, config/provider remain).
- v5.6 (20260522): Item 28 updated — Phase 11.5 wired client distribution (slack_channel, recipient scoping); config/provider still deferred to Phase 14.
- v5.7 (20260526): Added Item 31 — meetings create attendees CLI option removed; model/repo storage preserved for Phase 14+. Items 24 and 25 re-targeted from Phase 15/14 to Phase 12 (Notes & Tasks Foundation Sprint per CLI_STANDARDS.md V6/V7 update).
- v5.8 (20260528): Items 24 and 25 marked RESOLVED (Phase 12, v1.16.0). Added Items 32 and 33 (Phase 13 targets deferred from Phase 12).
- v5.9 (20260528): Added Item 34 — weekly report prompt using confirmed daily summaries as context instead of raw data re-query (token cost reduction, Phase 13).
- v5.10 (20260529): Added Item 35 — AI model config-driven selection; model strings currently hardcoded in claude_client.py and gemini_client.py; ai_settings.json already has model fields that are not read.
- v5.11 (20260529): Item 13 marked COMPLETE (v1.17.0 cost tracking sprint).
- v5.12 (20260603): Items 10, 11, 35 marked COMPLETE (v1.18.0 Provider Foundation Sprint);
  Item 36 added (ProviderConfig dead code cleanup).
- v5.13 (20260603): Quick Reference Register — Items 10, 11, 35 ✓ added (were missed in v5.12);
  Item 36 row added to register.
- v5.14 (20260603): Summary Statistics fully corrected — Item 13 (v1.17.0) and Items 10, 11, 35
  (v1.18.0) reflected; Item 36 added to Open/Low/Phase 15; counts and effort total updated.
- v5.15 (20260605): Phase 13 Sprint 1 (v1.19.0) — Item 36 marked COMPLETE; Item 19 status updated
  (CPU path delivered, GPU deferred); Items 37 and 38 added (Modelfile tuning workflow, Ollama
  warm-up ping as Sprint 2 Gate 0 prerequisite); register and statistics updated.
- v5.16 (20260610): Item 39 added — re-tag audit for 242 stub notes created during Phase 13
  DB Schema Sprint Gate 4 (time_entries note_id backfill extension).
- v5.17 (20260610): Item 23 priority elevated to High — meeting visibility
  gap identified as same structural issue resolved for time entries in this
  sprint; Phase 15 target retained pending scheduling review.
- v5.18 (20260610): Item 39 marked COMPLETE — re-tag audit finished; 214 → both,
  28 → internal-only, 1 → info-only; 0 unreviewed stubs remaining.
- v5.19 (20260611): Item 40 added — Daemon Scheduler configurable trigger times (Phase 14).
- v5.20 (20260612): Item 41 added — Clockify command exits 0 on staging write failure;
  discovered during Phase 13 Sprint 2 live testing (systemd EROFS).
- v5.21 (20260612): Items 32, 33, 34, 38 marked COMPLETE (Phase 13 Sprint 2, v1.21.0);
  statistics updated.
- v5.22 (20260612): Items 42, 43, 44 added — three items deferred from
  INTENT_ACTION_SERVICE_LAYER_PART_1 (v1.22.0): project_id Slack schema removal,
  meeting_id non-interactive linkage, entry_date/category schema fields.
- v5.23 (20260623): Item 45 added — `tags` field for `create_time_entry`
- v5.24 (20260623): Item 46 added — `build_weekly_prompt()` edge cases: short weeks,
  Thursday draft, internal content pollution in confirmed daily summaries
- v5.25 (20260623): Item 32 reopened — incorrectly marked COMPLETE in Sprint 2;
  Step 3c investigation required before scope can be determined
  via Slack (separate from Item 44 which covers `entry_date`/`category`).

---

## Backlog Item Template

Use this template for every new backlog item. All fields are required except Files Affected.

```
#### Item N — Title

**Status:** Open — Deferred to Phase X
**Priority:** High / Medium / Low
**Effort:** ~X hours
**Added:** YYYYMMDD
**Target Phase:** Phase X — Name

**Description:**
What the feature or fix is.

**Why Deferred:**
Reason this work was not done in the originating phase.

**Acceptance Criteria:**
- [ ] Criterion one
- [ ] Criterion two

**Files Affected:** (optional — list known files when scope is clear)
```

---

## Philosophy on Deferrals

- Focus on MVP functionality first
- Defer UX polish until core features are solid
- Avoid over-engineering (YAGNI principle)
- Add enhancements based on actual usage patterns, not speculation
- Don't abstract until patterns are proven across multiple implementations

Build first, refactor later. See the complete picture before abstracting.

---

## Quick Reference Register

| # | Title | Priority | Target Phase | Effort | Status |
|---|-------|----------|--------------|--------|--------|
| 1 | Command Aliases | Low | Phase 15 | ~20 min | |
| 2 | Shell Autocomplete | Medium | Phase 15 | ~2 hrs | |
| 3 | Template Interactive Editor | Medium | Phase 15 | ~4 hrs | |
| 4 | Field-Database Sync | Low | Phase 11+ | ~8 hrs | |
| 5 | Template Versioning | Low | — | ~3 hrs | |
| 6 | Template Sharing/Export | Low | — | ~2 hrs | |
| 7 | formatters.py Extraction | Medium | Phase 15 | ~4 hrs | |
| 8 | master_log_template.md | Low | Phase 15 | ~1 hr | |
| 9 | examples.json | Low | Conditional | ~2 hrs | |
| 10 | Streamlined Model Update Process | Medium | Phase 15 | ~4–6 hrs | ✓ |
| 11 | Add New AI Provider | Low | — | ~8–12 hrs | ✓ |
| 12 | email.py Internal Session Refactor | Low | Phase 15 | ~30 min | |
| 13 | datetime.utcnow() Deprecation | Low | Phase 15 | ~30 min | ✓ |
| 14 | test_database.py Engine Fixture | Medium | Phase 15 | ~1–2 hrs | |
| 15 | test_templates.py Stale Import | Medium | Phase 15 | ~1 hr | |
| 16 | auth.py RefreshError → GDriveAuthError | Low | Phase 15 | ~30 min | |
| 17 | eod Day-Aware Thu/Fri Steps | — | Phase 9 | — | ✓ |
| 18 | templates preview get_session ImportError | — | Phase 9 | — | ✓ |
| 19 | Ollama / Mistral 7B GPU Offloading | Low | Phase 13+ | ~2–3 hrs | |
| 20 | Multi-Client Data Attribution | — | Phase 11 | — | ✓ |
| 21 | Cloudflare Tunnel / Slack Events API | Low | — | ~3–4 hrs | |
| 22 | Active Client Context Data Model | — | → Item 20 | — | |
| 23 | Meeting Visibility / Tagging | Medium | Phase 15 | ~3–5 hrs | |
| 24 | tasks carryover Group Review | — | Phase 12 | — | ✓ |
| 25 | reports costs + providers costs Audit | — | Phase 12 | — | ✓ |
| 26 | Name-or-ID Rule (Edit/Delete) | — | Phase 14 | — | ✓ |
| 27 | Recurring Meeting Advanced Features | Medium | Phase 15 | ~12–16 hrs | ✓ |
| 28 | Placeholder Command Groups | Low | Phase 11+ | varies | |
| 29 | clockify report Subcommand Refactor | Low | Phase 15 | ~30 min | |
| 30 | System Service Promotion for workmain-notify | Low | Phase 18 | ~4 hours | |
| 31 | meetings create --attendees Restoration | Low | Phase 14 | ~30 min | |
| 32 | Task Deduplication and Forwarding | Low | Phase 13 (TBD) | TBD | |
| 33 | correction_note Field Population | Low | Phase 13 | ~2 hrs | ✓ |
| 34 | Weekly Report Prompt — Confirmed Daily Summaries as Context | Medium | Phase 13 | ~3–4 hrs | ✓ |
| 35 | AI Model Config-Driven Selection | Medium | Phase 14 | ~2–3 hrs | ✓ |
| 36 | ProviderConfig Dead Code Cleanup | Low | next base_provider.py mod | ~15 min | ✓ |
| 37 | Ollama Modelfile Tuning Workflow | Low | Sprint 2/3 maintenance | ~30 min/rebuild | |
| 38 | Ollama Warm-Up Ping on Bot Startup | Medium | Sprint 2 Gate 0 | ~30 min | ✓ |
| 39 | Re-tag Audit — 242 Gate 4 Stub Notes | Medium | Phase 13 (post-v1.20.0) | ~1–2 hrs | ✓ |
| 40 | Daemon Scheduler — Configurable Trigger Times | Low | Phase 14 | ~1–2 hrs | |
| 41 | Clockify Command Exits 0 on Staging Write Failure | Low | Phase 14 | ~30 min | |
| 42 | project_id Slack Schema Removal — create_time_entry | Low | next intent_parse rebuild | ~30 min | |
| 43 | meeting_id Non-Interactive Linkage for create_note/create_time_entry | Medium | Phase 13 Sprint 3 (T6) | ~4–6 hrs | |
| 44 | entry_date/category as IntentParser Schema Fields (Phase 2) | Low | next model rebuild | ~1–2 hrs | |
| 45 | `tags` for `create_time_entry` via Slack | Medium | Phase 13 Sprint 3 | ~3h | |
| 46 | `build_weekly_prompt()` Edge Cases — Short Weeks, Thursday Draft, Internal Pollution | Medium | Phase 13 | ~3–4 hrs | |

---

## Summary Statistics

**Total Items:** 46 (Item 22 is a redirect — no separate deferred work; see Item 20)
**Completed:** 16 (Items 10, 11, 13, 17, 18, 20, 24, 25, 26, 27, 33, 34, 35, 36, 38, 39)
**Open:** 29

| Status | Count | Items |
|--------|-------|-------|
| Open (targeted) | 25 | 1, 2, 3, 4, 7, 8, 12, 14, 15, 16, 19, 23, 28, 29, 30, 31, 32, 37, 40, 41, 42, 43, 44, 45, 46 |
| Conditional | 1 | 9 |
| Indefinitely | 3 | 5, 6, 21 |
| Complete | 16 | 10, 11, 13, 17, 18, 20, 24, 25, 26, 27, 33, 34, 35, 36, 38, 39 |
| Redirect | 1 | 22 → Item 20 |

| Priority | Count | Items |
|----------|-------|-------|
| High | 0 | — |
| Medium | 13 | 2, 3, 7, 10, 14, 15, 23, 34, 35, 38, 43, 45, 46 |
| Low | 24 | 1, 4, 5, 6, 8, 11, 12, 13, 16, 19, 21, 28, 29, 30, 31, 32, 33, 36, 37, 40, 41, 42, 44 |
| Conditional | 1 | 9 |

| Target Phase | Items |
|-------------|-------|
| Phase 11+ | 4, 28 |
| Phase 13 | 32, 33, 34, 46 |
| Phase 13 Sprint 3 | 43, 45 |
| Phase 14+ | 19, 31 |
| Phase 14 | 40, 41 |
| Phase 15 | 1, 2, 3, 7, 8, 10, 12, 13, 14, 15, 16, 23, 29 |
| Phase 18 | 30 |
| Sprint 2/3 | 37, 38 |
| Next model rebuild | 42, 44 |
| Conditional | 9 |
| Indefinitely | 5, 6, 11, 21 |

**Total Deferred Effort (open items):** ~87–92 hours

---

## Backlog Items

---

#### Item 1 — Command Aliases

**Status:** Open — Deferred to Phase 15
**Priority:** Low (UX polish)
**Effort:** ~20 minutes
**Added:** 20251223
**Target Phase:** Phase 15

**Description:**
Add short aliases for frequently used command groups.

**Proposed Aliases:**

```
workmain n  → workmain note
workmain m  → workmain meetings
workmain tk → workmain tasks
```

**Why Deferred:**
UX polish. Core CLI works without aliases. Phase 15 documentation/polish pass is the appropriate time.

**Acceptance Criteria:**

- [ ] All main command groups have 1–2 letter aliases
- [ ] `--help` shows both full name and alias
- [ ] No alias conflicts
- [ ] Documentation updated

---

#### Item 2 — Shell Autocomplete

**Status:** Open — Deferred to Phase 15
**Priority:** Medium (UX enhancement)
**Effort:** ~2 hours
**Added:** 20251223
**Target Phase:** Phase 15

**Description:**
Tab completion for bash and zsh shells with command, option, and value completion.

**Why Deferred:**
UX polish. No impact on functionality. Phase 15 documentation/polish pass.

**Acceptance Criteria:**

- [ ] Bash completion working
- [ ] Zsh completion working
- [ ] Tag completion shows all 6 tags
- [ ] Command completion shows all subcommands
- [ ] Installation documented

---

#### Item 3 — Template Interactive Editor

**Status:** Open — Deferred to Phase 15
**Priority:** Medium
**Effort:** ~4 hours
**Added:** 20251223
**Target Phase:** Phase 15

**Description:**
Interactive editor for template JSON files that opens the file in `$EDITOR` with live validation on save.

**Why Deferred:**
Templates are modified infrequently. Direct JSON editing works. Phase 15 polish pass.

**Acceptance Criteria:**

- [ ] Opens template in `$EDITOR` with live validation
- [ ] Prevents saving invalid templates
- [ ] Version bump on save

---

#### Item 4 — Field-Database Sync

**Status:** Open — Deferred to Phase 11+
**Priority:** Low
**Effort:** ~8 hours
**Added:** 20251223
**Target Phase:** Phase 11+ (exact phase TBD after multi-client data model is locked)

**Description:**
Auto-migrate database schema when new fields are added to templates. Currently adding a field to a template JSON requires a manual database migration. This feature would detect new fields and apply schema changes automatically.

**Why Deferred:**
Template schema has been stable since Phase 3. Auto-migration adds significant complexity for a problem that hasn't been painful in practice. Phase 11 multi-client data model changes are the better evaluation point for whether this pattern is needed.

**Acceptance Criteria:**

- [ ] Detect new fields in templates vs current schema
- [ ] Auto-migrate database schema when new fields found
- [ ] Validate field compatibility before migration
- [ ] Migration safety checks (dry run, rollback path)

---

#### Item 5 — Template Versioning

**Status:** Deferred Indefinitely
**Priority:** Low
**Effort:** ~3 hours
**Added:** 20251223
**Target Phase:** None (revisit if template management complexity grows)

**Description:**
Track version history for individual template JSON files — version bump, timestamp, and changelog entry when template structure changes.

**Why Deferred:**
No practical use case identified. Templates are infrequently modified and changes are visible in git history. YAGNI until template management becomes complex enough to warrant it.

**Acceptance Criteria (if implemented):**

- [ ] Templates have a `version` field in their JSON structure
- [ ] Version increments on save via template editor (depends on Item 3)
- [ ] `workmain templates list` shows current version per template

---

#### Item 6 — Template Sharing/Export

**Status:** Deferred Indefinitely
**Priority:** Low
**Effort:** ~2 hours
**Added:** 20251223
**Target Phase:** None (revisit if multi-installation use case emerges)

**Description:**
Export templates to a portable format for sharing between WorkmAIn installations.

**Why Deferred:**
Single-installation use case. No multi-user or deployment scenario identified. YAGNI.

**Acceptance Criteria (if implemented):**

- [ ] `workmain templates export <name> --output <path>` exports to JSON
- [ ] `workmain templates import <path>` imports and validates
- [ ] Conflict resolution on import (existing template with same name)

---

#### Item 7 — formatters.py Extraction

**Status:** Open — Deferred to Phase 15
**Priority:** Medium
**Effort:** ~4 hours
**Added:** 20251226
**Target Phase:** Phase 15

**Description:**
Extract formatting functions scattered across command files into a shared `formatters.py` module. Deferred until all commands are built so real patterns are visible before abstracting.

**Why Deferred:**
Premature abstraction risk. All commands needed to be built first to see the real pattern. Phase 15 refactor pass is the right time.

**Acceptance Criteria:**

- [ ] Common formatting functions extracted to `workmain/utils/formatters.py` (or similar)
- [ ] All command files updated to import from shared module
- [ ] No behavior change — formatting output identical
- [ ] Tests updated if formatting functions have unit tests

**Files Affected:**

- `workmain/cli/commands/*.py` (all command files)
- New: `workmain/utils/formatters.py`

---

#### Item 8 — master_log_template.md

**Status:** Open — Deferred to Phase 15
**Priority:** Low
**Effort:** ~1 hour
**Added:** 20251226
**Target Phase:** Phase 15

**Description:**
Create a `master_log_template.md` documenting the expected format for daily master log files used as reference context for AI report generation.

**Why Deferred:**
AI report quality is acceptable without formal template documentation. Useful reference but not blocking any feature. Phase 15 docs pass.

**Acceptance Criteria:**

- [ ] `master_log_template.md` created in `templates/` or `docs/`
- [ ] Documents all section headers and expected content format
- [ ] Reviewed against actual daily master logs for accuracy

---

#### Item 9 — examples.json

**Status:** Conditional — create only if AI output quality is poor without it
**Priority:** Low
**Effort:** ~2 hours
**Added:** 20251226
**Target Phase:** Conditional (re-evaluate if quality issues arise)

**Description:**
Create `examples.json` for AI prompts providing few-shot examples of high-quality report output. Only warranted if AI report quality is insufficient without explicit examples.

**Why Deferred:**
AI report quality has been acceptable without examples. Creating them speculatively adds maintenance overhead for no current benefit.

**Acceptance Criteria (if triggered):**

- [ ] `examples.json` created with representative high-quality report sections
- [ ] Prompt builder updated to include examples when available
- [ ] Report quality measurably improved vs baseline

---

#### Item 10 — Streamlined Model Update Process

**Status:** ✓ COMPLETE — v1.18.0 (Provider Foundation Sprint)
**Priority:** Medium
**Effort:** ~4–6 hours
**Added:** 20260210
**Completed:** 20260603
**Target Phase:** Phase 15

**Description:**
Documented process for updating AI model versions — steps for testing new model versions, updating model identifiers in code, verifying output quality, and committing changes. Demonstrated informally during Claude Sonnet 4 → 4.5 update.

**Resolution:**
`docs/ai_settings_guide.md` v1.0 added in the Provider Foundation Sprint. Documents
the config-driven model update mechanism (edit `config/ai_settings.json providers.<name>.model`,
no Python edits required), provider assignment changes, how to add new providers, and
the Phase 13-1 Ollama activation checklist. Model identifiers are now config-only
(Item 35 closes the code side).

**Acceptance Criteria:**

- [x] Written process in `docs/` covering: locate model identifiers, test report quality, update config
- [x] Model identifier locations documented (`config/ai_settings.json providers.<name>.model`)
- [x] Config-driven approach documented (change model in config, takes effect on next invocation)

**Files Affected:**

- New: `docs/ai_settings_guide.md`

---

#### Item 11 — Add New AI Provider

**Status:** ✓ COMPLETE — v1.18.0 (Provider Foundation Sprint)
**Priority:** Low
**Effort:** ~8–12 hours
**Added:** 20260210
**Completed:** 20260603
**Target Phase:** None (revisit if a specific use case emerges)

**Description:**
Add support for a third AI provider beyond Claude and Gemini. Required N-provider
extensible registry so adding a provider is one file + one config section.

**Resolution:**
Provider Foundation Sprint delivered: `PROVIDER_REGISTRY` in `workmain/ai/providers/__init__.py`
as the single registration point; `OllamaProvider` (Phase 13-1 stub, `enabled: false`) as the
third provider. `providers list` iterates registry dynamically. To add any future provider:
one Python file implementing `BaseProvider`, one registry entry, one `ai_settings.json` section.
See `docs/ai_settings_guide.md` for the three-step process.

**Acceptance Criteria:**

- [x] N-provider registry implemented (PROVIDER_REGISTRY)
- [x] OllamaProvider stub in place (Phase 13-1 activation ready)
- [x] `workmain providers list` shows all three providers including disabled Ollama
- [x] Adding a new provider requires no changes beyond registry + config

---

#### Item 12 — email.py Internal Session Refactor

**Status:** Open — Deferred to Phase 15
**Priority:** Low
**Effort:** ~30 min
**Added:** 20260305
**Target Phase:** Phase 15

**Description:**
`_generate_draft()` in `email.py` uses an internal session pattern rather than receiving a session via the standard `get_db()` path. Low risk but inconsistent with the rest of the codebase.

**Why Deferred:**
No functional bug. Internal session is self-contained and works correctly. Technical debt only. Phase 15 cleanup pass.

**Acceptance Criteria:**

- [ ] `_generate_draft()` receives session via parameter instead of creating internally
- [ ] Pattern consistent with other command files (`get_db()` + `try/finally`)
- [ ] No functional change to email draft behavior

**Files Affected:**

- `workmain/cli/commands/email.py`

---

#### Item 13 — datetime.utcnow() Deprecation

**Status:** ✓ COMPLETE — v1.17.0 (cost tracking sprint)
**Priority:** Low
**Effort:** ~30 min
**Added:** 20260309
**Completed:** 20260529
**Target Phase:** Phase 15

**Description:**
`gdrive_repository.py` uses `datetime.utcnow()` (deprecated in Python 3.12). Logs a `DeprecationWarning`. No functional impact.

**Fix:** Replace with `datetime.now(timezone.utc)`.

**Why Deferred:**
No functional impact. Warning only. Phase 15 cleanup pass.

**Resolution:**
Fixed as part of the Gate 1 cost tracking sprint (v1.17.0). Both affected call sites replaced:

- `workmain/database/models.py` — `GDriveUpload.created_at` default
- `workmain/integrations/gdrive/gdrive_repository.py` — inline `created_at=` assignment

**Acceptance Criteria:**

- [x] All `datetime.utcnow()` calls replaced with `datetime.now(timezone.utc)`
- [x] No `DeprecationWarning` on `workmain gdocs` operations

**Files Affected:**

- `workmain/integrations/gdrive/gdrive_repository.py`

---

#### Item 14 — test_database.py Missing Engine Fixture

**Status:** Open — Deferred to Phase 15
**Priority:** Medium
**Effort:** ~1–2 hours
**Added:** 20260309
**Target Phase:** Phase 15

**Description:**
`tests/test_database.py` requires a raw SQLAlchemy `engine` object for schema-level assertions. `conftest.py` only provides `db_session`. 13 tests currently erroring due to missing fixture.

**Why Deferred:**
Erroring tests don't block the suite baseline (161 passed). Schema-level assertions are a nice-to-have validation, not blocking any feature work. Phase 15 test debt cleanup.

**Acceptance Criteria:**

- [ ] `engine` fixture added to `conftest.py`
- [ ] `test_database.py` passes with 0 errors
- [ ] No regression to existing test baseline

**Files Affected:**

- `tests/conftest.py`
- `tests/test_database.py`

---

#### Item 15 — test_templates.py Stale Import

**Status:** Open — Deferred to Phase 15
**Priority:** Medium
**Effort:** ~1 hour
**Added:** 20260309
**Target Phase:** Phase 15

**Description:**
Stale import in `test_templates.py` causes a collection error. The entire file is non-functional.

**Why Deferred:**
File doesn't block the suite (collection errors are isolated). Template behavior covered by other tests. Phase 15 test debt cleanup.

**Acceptance Criteria:**

- [ ] Stale import identified and removed or updated
- [ ] `test_templates.py` collects and passes with 0 errors
- [ ] No regression to existing test baseline

**Files Affected:**

- `tests/test_templates.py`

---

#### Item 16 — auth.py RefreshError → GDriveAuthError

**Status:** Open — Deferred to Phase 15
**Priority:** Low
**Effort:** ~30 min
**Added:** 20260311
**Target Phase:** Phase 15

**Description:**
`_require_auth()` in `auth.py` does not catch `RefreshError` and convert it to a clean `GDriveAuthError`. On token expiry, an unhandled exception surfaces instead of a user-friendly message.

**Why Deferred:**
Edge case — only triggers on token expiry, which is infrequent. No silent data loss. Phase 15 cleanup pass.

**Acceptance Criteria:**

- [ ] `_require_auth()` catches `RefreshError` from `google.auth.exceptions`
- [ ] Raises clean `GDriveAuthError` with user-friendly message
- [ ] No raw traceback on token expiry

**Files Affected:**

- `workmain/integrations/gdrive/auth.py`

---

#### Item 17 — workmain eod Day-Aware Thursday/Friday Steps

**Status:** ✓ Complete — Phase 9, v1.6.0 (20260319)
**Priority:** —
**Effort:** —
**Added:** 20260311
**Target Phase:** Phase 9

Day-aware EOD pipeline: Thursday adds `slack post weekly` (step 7/8); Friday adds weekly report + email (steps 7–8/9). New `--skip weekly` flag on `workmain eod`. New commands: `reports history`, `reports show <id>`, `reports resend <id>`. 21 new tests added.

---

#### Item 18 — workmain templates preview get_session ImportError

**Status:** ✓ Complete — Phase 9 Gate 0, v1.6.0 (20260319)
**Priority:** —
**Effort:** —
**Added:** 20260311
**Target Phase:** Phase 9

`workmain templates preview` raised `ImportError` due to stale `get_session` import. Fixed by migrating to the `get_db()` + `db.get_session()` pattern.

---

#### Item 19 — Ollama / Mistral 7B GPU Offloading

**Status:** Open — Deferred to Phase 14+ (CPU path delivered in Phase 13 Sprint 1, v1.19.0)
**Priority:** Low (performance enhancement — not blocking)
**Effort:** ~2–3 hours
**Added:** 20260421
**Target Phase:** Phase 14+

**Description:**
Phase 13 Sprint 1 delivered the CPU path — Mistral 7B (Q4_K_M) running on Proxmox
(i9-12950HX) via workmain-intent:latest. Warm latency: ~7–11s per parse. Acceptable
for Sprint 2/3 use given the 10s Slack polling interval.

The Alienware M18R2 (RTX 4070 laptop GPU) is available on the home network and can serve as an optional GPU inference host when online, reducing parse latency to ~60–80 tok/s.

**Why Deferred:**
Phase 13 primary path (Proxmox CPU) is sufficient. GPU offloading is a latency improvement, not a correctness requirement. Adding infrastructure complexity before the base path is validated is premature.

**Acceptance Criteria:**

- [ ] WorkmAIn Ollama client accepts configurable host endpoint via env var (`OLLAMA_HOST`)
- [ ] Fallback to Proxmox CPU host if configured GPU host unreachable
- [ ] README includes GPU offloading setup instructions for Ollama on RTX 4070
- [ ] Benchmark results documented (CPU vs GPU latency for Mistral 7B)

**Files Affected:**

- `workmain/ai/` (Ollama client)
- `README.md` or `docs/` (setup instructions)

---

#### Item 20 — Multi-Client Data Attribution

**Status:** ✓ Complete — Phase 11, v1.13.0 (20260512)
**Priority:** —
**Effort:** —
**Added:** 20260421
**Target Phase:** Phase 11

Full client attribution delivered in Phase 11: `client_id` FK (nullable, ON DELETE SET NULL)
on `notes`, `meetings`, `time_entries`, and `reports`. All data-creation commands
(`notes add/log`, `meetings create`, `time add`, `reports save`, `slack post`) read
`active_client_id` from `system_state` and stamp it on every new record. Report generator
reads `recipient_type` from the active template and applies `get_client_filter()` — client
reports filter to active client's data; internal reports are unfiltered. Active client
context managed via `workmain clients set active <name>` / `workmain clients status`.
`system_state` KV store is the single source of truth for `active_client_id`.

**Note:** Item 22 pointed to this item — there is no separate deferred work for Item 22; it is fully subsumed here.

---

#### Item 21 — Cloudflare Tunnel / Slack Events API Upgrade

**Status:** Deferred Indefinitely (revisit if home lab infrastructure expands)
**Priority:** Low
**Effort:** ~3–4 hours
**Added:** 20260421
**Target Phase:** None (optional upgrade post-Phase 13)

**Description:**
Phase 13 uses Slack Web API polling (~10 second latency) for inbound messages. The Slack Events API (webhook/push model) would reduce latency to ~1 second but requires a publicly reachable HTTPS endpoint from WSL. Cloudflare Tunnel is the cleanest solution — creates a persistent public URL forwarding to localhost without port forwarding or a static IP.

**When to reconsider:**

- If home lab gains other services that benefit from Cloudflare Tunnel
- If polling latency becomes noticeable friction in daily use
- If Cloudflare Tunnel is set up for other reasons and the upgrade becomes low-cost

**Why Deferred:**
Polling is sufficient for Phase 13. Cloudflare Tunnel adds infrastructure complexity and a new failure mode (tunnel outage = silent loss of inbound messages) before the base path is proven.

**Acceptance Criteria (if implemented):**

- [ ] Cloudflare Tunnel configured and running as systemd service
- [ ] Slack Events API webhook handler replaces poll loop
- [ ] Tunnel outage falls back to polling gracefully
- [ ] Tunnel health monitored and logged

---

#### Item 22 — Active Client Context Data Model

**Status:** Merged into Item 20 — no separate deferred work
**Priority:** —
**Effort:** —
**Added:** 20260421
**Target Phase:** → See Item 20

The design decision (Option A — active client context switch) was approved 20260421. Phase 11 delivers the UI. The data model migration work is tracked entirely under Item 20.

---

#### Item 23 — Meeting Visibility / Tagging for Report Prompt Context

**Status:** Open — Deferred
**Priority:** High (same structural gap resolved for time entries in Phase 13 DB Schema Sprint)
**Effort:** ~3–5 hours
**Added:** 20260327
**Target Phase:** Phase 15 (prompt quality pass — scheduling review pending)

**Description:**
Meetings are fetched for the full week and appended to every section's context in the AI prompt without filtering. Because meetings have no tag equivalent, internal meetings (e.g., "Splunk Normalization Project - Internal Sync") are exposed when generating client-facing reports (`weekly_client`), potentially causing AI-generated content about internal discussions.

**Options to evaluate:**

1. **Meeting-level tag** — Add a `visibility` or `tags` field to the Meeting model (e.g., `internal-only`, `client-report`, `both`). Prompt builder filters meetings the same way it filters notes.
2. **Respect `data_sources`** — Prompt builder currently ignores `data_sources` for meetings. Wrap meeting fetch in a `"meetings" in data_sources` check.
3. **Exclude meetings from weekly_client entirely** — Don't include meeting titles in weekly report prompts at all; meeting content is already captured in tagged notes.

**Context:**
Investigated 2026-03-27 after weekly report included AI-generated content derived from an "Internal Sync" meeting title. Note-level `internal-only` filtering confirmed working — issue is unfiltered meeting context in the prompt.

**Why Deferred:**
Workaround exists (internal meetings captured as internal-only notes). Requires design decision between three options before implementation. Phase 15 prompt quality pass.

**Acceptance Criteria:**

- [ ] Evaluate which option best fits the workflow
- [ ] Internal meetings do not appear in `weekly_client` report prompt context
- [ ] If meeting tags added: Meeting model updated, migration written, CLI updated
- [ ] If `data_sources` gating: `prompt_builder.py` updated
- [ ] Tests updated to cover meeting filtering behavior

**Files Affected:**

- `workmain/ai/prompt_builder.py`
- `workmain/database/models.py` (if adding meeting tags)
- `templates/reports/weekly_client.json`

---

#### Item 24 — tasks carryover Single-Command Group Review

**Status:** ✓ Resolved — Phase 12, v1.16.0 (20260528)
**Priority:** Low (structural inconsistency, no user impact)
**Effort:** ~1 hour
**Added:** 20260331
**Target Phase:** Phase 12

`tasks carryover` single-command group expanded to full lifecycle group in v1.16.0: `tasks list`, `tasks today`, `tasks show`, `tasks complete`, `tasks dismiss`. Deprecated alias `tasks carryover` introduced with yellow warning; full retirement Phase 15. V6 resolved in CLI_STANDARDS.md v2.4.

---

#### Item 25 — reports costs + providers costs Duplicate Surface Audit

**Status:** ✓ Resolved — Phase 12, v1.16.0 (20260528)
**Priority:** Low (possible redundancy, no immediate user impact)
**Effort:** ~1 hour
**Added:** 20260331
**Target Phase:** Phase 12

Gate 4 audit confirmed genuinely distinct purposes: `reports costs` = aggregate AI cost totals across all reports (summary view); `providers costs` = per-report cost breakdown by provider. No redundancy — both surfaces retained. V7 resolved in CLI_STANDARDS.md v2.4.

---

#### Item 26 — Name-or-ID Rule on Edit/Delete Commands

**Status:** ✓ Complete — feature/name-or-id-resolution, v1.10.0 (20260501)
**Priority:** —
**Effort:** —
**Added:** 20260331
**Target Phase:** Phase 14

§4.3 of `CLI_STANDARDS.md` requires all commands targeting a specific DB resource to accept either record ID or name (fuzzy picker on ambiguous matches). Implemented for `notes edit/delete`, `time edit/delete`, `meetings delete/rename/edit`, `email recipients delete`, `notes meeting`, `meetings condense`, and `meetings merge`. Both directions resolved: ID-only commands now accept names; name-only commands now accept IDs.

---

#### Item 27 — Recurring Meeting Advanced Features

**Status:** Complete — v1.12.0 (20260508)
**Priority:** Medium (nice-to-have enhancements)
**Effort:** ~12–16 hours
**Added:** 20260127
**Target Phase:** Phase 15

**Description:**
Advanced recurring meeting management features beyond basic creation and instance selection:

1. **Edit Series** — Modify all future instances of a recurring meeting
2. **Skip Occurrence** — Mark a specific instance as skipped without deleting
3. **Reschedule Instance** — Move a single occurrence to a different time
4. **Recurring Templates** — Pre-defined patterns (daily standup, weekly review)

**Proposed Commands:**

```bash
workmain meetings edit-series "Daily Standup" --start 10:00 --end 10:15
workmain meetings skip "Daily Standup" --date 2026-02-15
workmain meetings reschedule 42 --date 2026-02-20 --start 14:00
```

**Why Deferred:**
Core recurring functionality (create, view, delete) is complete and working. These are convenience features with known workarounds. Phase 5.1 focused on critical bugs preventing basic usage.

**Acceptance Criteria:**

- [x] Can edit all future instances of recurring series
- [x] Can skip individual occurrences without deleting
- [x] Can reschedule single instance to different time/date
- [x] Changes properly tracked in database
- [x] UI clearly shows modified instances

**Files Affected:**

- `workmain/cli/commands/meetings.py`
- `workmain/database/repositories/` (meeting repository)

---

#### Item 28 — Placeholder Command Groups

**Status:** Open — clients delivered (Phase 11); distribution wired (Phase 11.5); config/provider remain
**Priority:** Low
**Effort:** Varies
**Added:** 20260127
**Target Phase:** Phase 11+ for config; audit for provider

**Description:**
Command groups that were placeholders in `interface.py`, removed in v1.1.0. Current status:

- **clients** — ✓ Complete. Full `workmain clients` group delivered in Phase 11 (v1.13.0). Per-client distribution (Slack channel + email recipient scoping) wired in Phase 11.5 (v1.14.0).
- **notifications** — ✓ Complete. `workmain notifications` group delivered in Phase 10 (v1.11.0).
- **config** (Phase 14) — Settings like default tags, trigger times, Ollama host. Phase 14 setup wizard is the intended home.
- **provider** (Low) — Overlaps with existing `providers` command. Likely redundant; needs audit.

**Why Deferred:**
`config` deferred to Phase 14. `provider` redundancy should be confirmed before any work is done.

**Acceptance Criteria:**

- [ ] Phase 14 setup wizard covers `config` use case — or `config` group re-added at that time
- [ ] `provider` vs `providers` audited; if redundant, confirm `providers` covers all need with no gap

---

#### Item 29 — clockify report Subcommand Refactor

**Status:** Open — Deferred to Phase 15
**Priority:** Low (cosmetic consistency)
**Effort:** ~30 min
**Added:** 20260303
**Target Phase:** Phase 15

**Description:**
Refactor `clockify report ACTION` to use a consistent subcommand pattern matching `clockify sync push/pull/both`. Currently `clockify report save` uses the action as a positional argument rather than a Click subcommand.

**Desired state:**

```bash
workmain clockify report save daily    # consistent subcommand pattern
```

**Why Deferred:**
Current behavior works correctly. Cosmetic CLI consistency issue only. Phase 15 polish pass.

**Acceptance Criteria:**

- [ ] `clockify report save` follows the same subcommand pattern as `clockify sync`
- [ ] `--help` output consistent with `clockify sync` format
- [ ] No functional change to report behavior

**Files Affected:**

- `workmain/cli/commands/` (clockify-related command file)

---

#### Item 30 — System Service Promotion for workmain-notify

**Status:** Deferred — design decision required before Phase 18 Gate 0
**Priority:** Low
**Effort:** ~4 hours
**Added:** 20260505
**Target Phase:** Phase 18

**Background:**
Phase 10 ships `workmain-notify` as a systemd user service. This is correct for development
and single-user interactive sessions where desktop notification delivery (`wsl-notify-send` /
`notify-send`) requires access to `DISPLAY` and `DBUS_SESSION_BUS_ADDRESS` from the
logged-in user's session context. A dedicated system user cannot access these without
additional plumbing.

**Design decision required at Phase 18:**

Option A — Promote to system service:
  Dedicated `workmain` system user and group; `/opt` install path;
  `/var/lib/workmain` state directory; session environment injection
  mechanism for notification delivery (env file or D-Bus bridge);
  `postinst` script creates user/group on package install.

Option B — Keep as user service installed from `/opt`:
  Simpler; notification delivery unchanged; acceptable for single-user
  personal productivity tool. No session plumbing required.

**Why both are viable:**
A system service provides stronger isolation and allows the daemon to run before interactive
login. A user service is simpler and works correctly for a single-user tool on a machine
where the user is always logged in interactively. For a home lab / personal productivity
setup, the difference in security posture is marginal.

**Why Phase 10 enables this transition:**
All daemon paths are derived from `WORKMAIN_STATE_DIR` (environment variable). This was an
explicit Phase 10 design decision so that a future system service promotion requires
environment file changes rather than a code rewrite.

**WSL2 exceptions to re-enable on native Linux (documented in service unit):**

- `CapabilityBoundingSet=` and `AmbientCapabilities=` — kernel EPERM on WSL2
- `LimitNPROC=64` — kernel EPERM when combined with other security directives on WSL2

**Acceptance Criteria:**

- [ ] Architecture decision documented before Phase 18 Gate 0
- [ ] If Option A: `postinst` creates `workmain` user/group; daemon starts without
      interactive user logged in; notifications confirmed delivered
- [ ] If Option B: install path documented; functional behaviour unchanged
- [ ] WSL2 service unit exceptions resolved or documented for target platform

**Files Affected:**

- `deploy/workmain-notify.service`
- `workmain/daemon/daemon.py` (path config, if Option A changes state dir)
- `workmain/__version__.py` (packaging phase)

---

#### Item 31 — meetings create --attendees CLI Option Restoration

**Status:** Open — Deferred to Phase 14
**Priority:** Low (feature-complete for current use case; CLI option removed as dead code)
**Effort:** ~30 min
**Added:** 20260526
**Target Phase:** Phase 14

**Description:**
The `--attendees/-a` CLI option was removed from `workmain meetings create` during the
Notes & Tasks Foundation Sprint (v1.15.0, Gate 2). The option accepted a list of email
addresses but was never surfaced in any output, report, or downstream workflow. The option
was dead CLI weight.

The `Meeting.attendees` model column and `meetings_repo.create(attendees=...)` parameter
are **fully intact** — no data layer was changed. Restoration is a CLI-only task.

When the meetings display or export surface is built (Phase 14+ UI or reporting), restore
the `--attendees` option with a proper short form that does not conflict with §5.3 reserved
flags (note: `-a` conflicts with the `--all` pattern; a new assignment is needed).

**Why Deferred:**
The CLI option had no wired functionality. Restoring it has zero value until attendees are
surfaced in output, reports, or notifications. Phase 14 (Setup Wizard and Configuration)
is the earliest point where attendee management becomes user-facing.

**Acceptance Criteria:**

- [ ] Attendees surfaced in at least one user-facing output (meetings show, weekly report, etc.)
- [ ] `--attendees` restored to `meetings create` with a compliant short form
- [ ] Short form assigned in CLI_STANDARDS.md §5.3 reserved table

**Files Affected:**

- `workmain/cli/commands/meetings.py`
- `docs/CLI_STANDARDS.md` (§5.3 reserved table — new short form assignment)

---

#### Item 32 — Task Deduplication and Forwarding (Phase 13)

**Status:** Open — Pending Step 3c investigation (reopened 20260623)
**Priority:** Low
**Effort:** TBD — pending investigation
**Added:** 20260528
**Target Phase:** Phase 13 (scope TBD after Step 3c investigation)

**Description:**
When multiple active carry-forward notes appear to cover the same work item, Phase 13's
Mistral 7B intent parser should identify them during Step 3c matching and propose a merge.
The surviving note keeps its `task_status` record (re-confirmed active); the deprecated
note's record is set to dismissed with `forwarding_note_id` pointing to the surviving note.

The `forwarding_note_id` column is already present in `task_status` as of v1.16.0 — no
additional migration needed.

**Reopened:**
Item 32 was incorrectly marked COMPLETE in Phase 13 Sprint 2. The Step 3c work that was
delivered matches CF tasks to time entries (for completion/dismissal), which is a different
problem from detecting semantically duplicate CF notes. Before this item can be properly
scoped, a Step 3c investigation is needed to understand why CF tasks are not moving forward
in practice — that finding may significantly reshape what this item needs to be.

**Why Deferred:**
Requires the Mistral 7B intent parser (Phase 13 Item 19). The `forwarding_note_id` column
is a Phase 12 placeholder; no Phase 12 business logic uses it.

**Acceptance Criteria:**

- [ ] Mistral 7B intent parser detects semantically duplicate active CF tasks
- [ ] Step 3c surfaces merge candidates with [m]erge / [s]kip prompt
- [ ] Dismissed note's task_status.forwarding_note_id set to surviving note ID
- [ ] `tasks show` displays forwarding_note_id when set

---

#### Item 33 — correction_note Field Population (Phase 13)

**Status:** ✓ COMPLETE — 20260612 (Phase 13 Sprint 2, v1.21.0)
**Priority:** Low
**Effort:** ~2 hours
**Added:** 20260528
**Target Phase:** Phase 13

**Description:**
The `correction_note` column on the `reports` table (added v1.16.0) has no CLI write path
in Phase 12. Phase 13's Ollama intent parser should populate this field when corrections
arrive via Slack DM, providing structured context about why the correction was made. This
enables correction audit trails in the weekly aggregation context.

**Why Deferred:**
No CLI write path is needed until Slack DM intent parsing is implemented (Phase 13). The
column exists as a Phase 12 schema placeholder only.

**Acceptance Criteria:**

- [x] Ollama/Mistral parses Slack DM correction intent and extracts reason
- [x] `reports correct` (or Slack handler) writes structured reason to `correction_note`
- [x] `reports show` displays `correction_note` when populated (hotfix v1.22.2, 20260623)

---

#### Item 34 — Weekly Report Prompt — Confirmed Daily Summaries as Context

**Status:** ✓ COMPLETE — 20260612 (Phase 13 Sprint 2, v1.21.0)
**Priority:** Medium (token cost reduction + accuracy improvement)
**Effort:** ~3–4 hours
**Added:** 20260528
**Target Phase:** Phase 13

**Description:**
The weekly report (`weekly_client`) currently assembles its AI prompt by re-querying all
`notes`, `time_entries`, and `meetings` for the Mon–Fri date range directly via
`prompt_builder.py`. This means every Friday's weekly report re-ingests 5 days of raw rows,
even though the user has already reviewed and confirmed (or corrected) each day's daily
report via the EOD Step 4a workflow added in v1.16.0.

Phase 13 should wire `ReportsRepository.get_confirmed_dailies(start_date, end_date)` into
the weekly prompt-building path so that the prompt uses confirmed/corrected daily report
content as its source instead of raw data. The confirmed `content` field (or
`corrected_content` when set) represents the user-reviewed, accurate version of each day.

**Benefits:**

- **Token cost reduction** — a week of 5 compact daily summaries is significantly smaller
  than 5 days of raw notes + time entries + meetings joined together
- **Accuracy** — the weekly prompt reflects the user's reviewed and corrected account of
  events rather than raw unfiltered data
- **Consistency** — corrections made via `reports correct` (e.g., fixing a wrong client
  attribution) automatically flow into the weekly report without manual re-editing

**Implementation notes:**

- `get_confirmed_dailies(start_date, end_date)` already exists in `ReportsRepository`
  (added v1.16.0); it returns confirmed/corrected `daily_internal` reports ordered ASC
- `prompt_builder.py` needs a new code path: if confirmed dailies exist for the full
  week, use their content fields; fall back to raw data query if any day is missing
- Use `corrected_content` when set (non-None); otherwise use `content`
- The fallback path ensures backward compatibility for weeks where EOD wasn't run or
  reports were left unconfirmed

**Why Deferred:**
Requires Phase 13's Ollama integration work to be scoped alongside this — changing the
prompt-building path for the weekly report is a meaningful refactor of `prompt_builder.py`
that should be done with full Phase 13 context rather than bolted on mid-phase.

**Files Affected:**

- `workmain/ai/prompt_builder.py` — new `_get_confirmed_daily_summaries()` method; wire
  into `build_prompt()` when template frequency is `weekly`
- `workmain/database/repositories/reports_repo.py` — `get_confirmed_dailies()` already
  present; no changes needed unless signature needs extension

**Acceptance Criteria:**

- [x] Weekly prompt uses confirmed/corrected daily content when all 5 weekdays have a
  confirmed or corrected daily report (hotfix v1.22.2, 20260623)
- [x] Falls back to raw notes/time_entries/meetings query when any weekday lacks a
  confirmed daily (same behavior as today) (hotfix v1.22.2, 20260623)
- [x] `corrected_content` preferred over `content` when set on a given day's report
  (hotfix v1.22.2, 20260623)
- [x] Token count of weekly prompt measurably reduced versus baseline (raw data path)
  — confirmed path skips raw DB data entirely when all 5 dailies present (hotfix v1.22.2)

---

#### Item 35 — AI Model Config-Driven Selection

**Status:** ✓ COMPLETE — v1.18.0 (Provider Foundation Sprint)
**Priority:** Medium
**Effort:** ~2–3 hours
**Added:** 20260529
**Completed:** 20260603
**Target Phase:** Phase 14 (Setup Wizard)

**Description:**
Model strings were hardcoded in Python client files. Fix: read model from
`ai_settings.json` at provider instantiation with hardcoded fallback.

**Resolution:**
`claude_client.py` and `gemini_client.py` deleted; replaced by `providers/claude.py`
(ClaudeProvider) and `providers/gemini.py` (GeminiProvider). Both read:
`self.model = config.get('model', _FALLBACK_MODEL)` in `__init__`. Model changes are
config-only — no Python edits needed. Verified end-to-end: setting
`providers.claude.model = test-model-gate2` showed in `providers list` model column.

**Acceptance Criteria:**

- [x] `ClaudeProvider.__init__` reads `config.get('model', fallback)`
- [x] `GeminiProvider.__init__` reads `config.get('model', fallback)`
- [x] `workmain providers list` model column reflects config value
- [x] Changing model in `ai_settings.json` takes effect on next invocation
- [x] Item 10 updated to reflect config-driven approach (docs/ai_settings_guide.md)

**Files Affected:**

- `workmain/ai/providers/claude.py` — `self.model = config.get('model', _FALLBACK_MODEL)`
- `workmain/ai/providers/gemini.py` — same pattern
- `config/ai_settings.json` — `model` field already present, now actually read

---

#### Item 36 — ProviderConfig Dead Code Cleanup

**Status:** ✓ COMPLETE — v1.19.0 (Phase 13 Sprint 1 Gate 1, 20260605)
**Priority:** Low
**Effort:** ~15 min
**Added:** 20260603
**Target Phase:** Next `base_provider.py` modification

**Description:**
`ProviderConfig` dataclass in `workmain/ai/base_provider.py` has no remaining consumers
post-v1.18.0. Its only consumers were `claude_client.py` and `gemini_client.py`, both
deleted in the Provider Foundation Sprint. The class is currently exported from
`workmain/ai/__init__.py` for backward compat but nothing in the codebase imports it.

**Why Deferred:**
No functional impact. Remove when `base_provider.py` is next modified to avoid
a dedicated one-line-removal commit.

**Acceptance Criteria:**

- [x] `ProviderConfig` class removed from `base_provider.py`
- [x] `ProviderConfig` removed from `workmain/ai/__init__.py` exports and `__all__`
- [x] `grep -rn "ProviderConfig" workmain/` returns empty (no remaining imports)

**Files Affected:**

- `workmain/ai/base_provider.py`

---

#### Item 37 — Ollama Modelfile Tuning Workflow

**Status:** Open — ongoing Sprint 2/3 maintenance
**Priority:** Low
**Effort:** ~30 min per rebuild
**Added:** 20260605
**Target Phase:** Sprint 2/3 maintenance

**Description:**
workmain-intent:latest Modelfile delivered in Phase 13 Sprint 1. As the action
vocabulary grows in Sprint 2 and 3 (new action types, refined examples, tuned
generation parameters), the Modelfile must be rebuilt after each schema update.

Long-term: consider fine-tuning on actual WorkmAIn usage data once sufficient
real interaction logs are accumulated (post-Sprint 2 go-live). Fine-tuning on
real inputs would significantly improve multi-tag inference (currently limited
by 7B model size) and domain-specific phrasing recognition.

**Why Deferred:**
Requires real usage data from Sprint 2+ to have value. Fine-tuning on synthetic
examples would not improve on the current prompt-engineered approach.

**Acceptance Criteria:**

- [ ] Rebuild Modelfile after each Sprint 2/3 action schema change
- [ ] `config/intent_parse_system_prompt.txt` versioning header kept in sync
- [ ] `config_version` incremented and `model_built` date updated on each rebuild
- [ ] Evaluate fine-tuning feasibility after 30 days of production usage

**Files Affected:**

- `config/intent_parse_system_prompt.txt`
- `config/intent_parse_prompt.json`
- `ollama-lxc/models/workmain-intent/Modelfile` (IaC repo)

---

#### Item 38 — Ollama Warm-Up Ping on Bot Startup

**Status:** ✓ COMPLETE — 20260612 (Phase 13 Sprint 2, v1.21.0)
**Priority:** Medium (UX — cold start is 55–72s, unacceptable for first Slack message)
**Effort:** ~30 min
**Added:** 20260605
**Target Phase:** Sprint 2 Gate 0

**Description:**
Observed in Phase 13 Sprint 1 benchmark: first request after model idle takes
55–72s (Ollama loading workmain-intent:latest from storage into RAM). Subsequent
warm requests complete in 7–11s. With a 10s Slack polling interval, the first
message after a container restart would appear to hang for over a minute.

Sprint 2 Slack bot startup should send a no-op generate request (e.g. a single
token `[INST] ping [/INST]`) to pre-warm the model before the bot begins polling.
This eliminates the cold-start penalty in normal operation.

**Why Deferred:**
No Slack bot in Sprint 1. Sprint 2 is where the bot starts up and polls.

**Acceptance Criteria:**

- [ ] Bot startup sequence sends warm-up ping to workmain-intent:latest before poll loop
- [ ] Warm-up ping is logged but not cost-tracked (no meaningful token count)
- [ ] Cold-start latency after bot restart is ≤ 15s for first real user message

**Files Affected:**

- Sprint 2 Slack bot startup module (TBD)
- `workmain/ai/__init__.py`

---

#### Item 39 — Re-tag Audit: 242 Gate 4 Stub Notes

**Status:** ✓ COMPLETE — 20260610 (data audit, no code change)
**Priority:** Medium (data quality — affects report tag filtering accuracy)
**Effort:** ~1–2 hours
**Added:** 20260610
**Completed:** 20260610
**Target Phase:** Phase 13 (post-v1.20.0 merge, before Sprint 2)

**Description:**
During Phase 13 DB Schema Sprint Gate 4 (migration 021), 242 time entries
had no note with matching content+date. These were resolved by creating stub
notes with `tags=['internal-only']` as a safe default. The internal-only tag
was chosen to prevent accidental client report inclusion pending review.

These 242 stubs need to be reviewed and re-tagged to their correct values
(`both`, `client-report`, `carry-forward`, etc.) based on the actual work
context captured in their content.

**Identification query:**

```sql
SELECT
    n.id          AS note_id,
    n.content,
    n.created_date,
    te.id         AS time_entry_id,
    te.duration_hours,
    te.category
FROM notes n
JOIN time_entries te ON te.note_id = n.id
WHERE n.source = 'task'
  AND n.tags = ARRAY['internal-only']::text[]
  AND n.created_at::time = '00:00:00'
ORDER BY n.created_date, n.id;
```

Note: This query also returns the single stub note created for `te.id=2`
(2026-02-02, Google PMLE lab), which was explicitly approved as
`internal-only` in Gate 3 and does NOT require re-tagging. Exclude it
by adding `AND n.id != 7606` if needed.

**Why Deferred:**
Migration needed to complete before tag reviews could begin. Stub notes
were intentionally defaulted to `internal-only` to be conservative — no
content leaks into client reports pending this audit.

**Completion Notes:**
214 notes → `both`, 28 notes → `internal-only` (verified, not defaulted), 1 note → `info-only`.
Identification query confirmed 0 unreviewed stubs remaining.

**Acceptance Criteria:**

- [x] All 242 stub notes reviewed against work context
- [x] Tags updated to correct values via `workmain notes edit <id> --tags <tags>`
- [x] Any notes confirmed as internal-only are verified, not just left by default
- [x] Identification query returns 0 rows after re-tag (or only note id=7606)

**Files Affected:**

- `notes` table (data only — tag updates via `workmain notes edit`)
- `workmain/cli/commands/notes.py` (no code change needed)

---

#### Item 40 — Daemon Scheduler — Configurable Trigger Times

**Status:** Open
**Priority:** Low
**Effort:** ~1–2 hours
**Added:** 20260611
**Target Phase:** Phase 14 (Setup Wizard)

**Description:**
All trigger times in `workmain/daemon/scheduler.py` are hardcoded constants
(workday start 05:30, daily closeout 14:00, EOD prompt 14:30, T1 morning
briefing 05:30). Changing any of these requires editing Python source code.
They should be read from a JSON config file (e.g. `config/scheduler.json`)
so times can be adjusted without a code change, aligned with the Phase 14
Setup Wizard scope already noted in the scheduler.py docstring.

**Why Deferred:**
Low operational urgency — current times work well for the target user's
schedule. Phase 14 is the natural home for all user-configurable settings.
Premature configuration adds complexity without immediate benefit.

**Acceptance Criteria:**

- [ ] `config/scheduler.json` defines trigger times with sensible defaults
- [ ] `scheduler.py` reads from config at `build_scheduler()` time; falls back
      to hardcoded defaults if config absent or key missing
- [ ] All existing trigger IDs and behaviors preserved
- [ ] `workmain notifications config` (Phase 14) exposes time settings

**Files Affected:**

- `workmain/daemon/scheduler.py`
- `config/scheduler.json` (new file)

---

#### Item 41 — Clockify Command Exits 0 on Staging Write Failure

**Status:** Open
**Priority:** Low
**Effort:** ~30 min
**Added:** 20260612
**Target Phase:** Phase 14

**Description:**
`workmain clockify report save daily` prints `✗ Error downloading report: <msg>` to
stdout when it fails to write the Clockify PDF to `staging/clockify/`, but the Click
command exits with code 0. `_run_clockify_step` in `eod_workflow.py` checks
`result.returncode` to detect failure; since the command always exits 0, the step
runner cannot detect write failures and reports `COMPLETED` in the Slack EOD surface
even when the PDF was not staged. Discovered during Phase 13 Sprint 2 live testing:
`[Errno 30] Read-only file system` on `staging/clockify/` caused the step to show
"✓ complete" in Slack while the backend logged the error. The root filesystem
sandboxing issue was resolved (systemd `ReadWritePaths` fix in v1.21.0), but the
command should still return a non-zero exit code on write failure as a defensive
invariant.

**Why Deferred:**
The staging write failure that exposed this bug was caused by a systemd
`ProtectHome=read-only` misconfiguration now fixed. Low operational risk until the
next edge case triggers it. Fix is small and self-contained; Phase 14 is the natural
consolidation point for similar CLI robustness tasks.

**Acceptance Criteria:**

- [ ] `workmain clockify report save daily` exits with code 1 when the report
      download or staging write fails (exception caught or `success=False`)
- [ ] `_run_clockify_step` correctly reports `FAILED` when the clockify command
      exits non-zero in daemon context

**Files Affected:**

- `workmain/cli/commands/clockify.py` (add `sys.exit(1)` on failure paths)

---

#### Item 42 — project_id Slack Schema Removal — create_time_entry

**Status:** Open — Deferred to next intent_parse rebuild
**Priority:** Low
**Effort:** ~30 min
**Added:** 20260612
**Target Phase:** Next `intent_parse_system_prompt.txt` rebuild

**Description:**
The `create_time_entry` action schema in `intent_parse_system_prompt.txt` includes
a `project` field (a string). There is no `ProjectsRepository`, and no project-by-name
resolution exists anywhere in the local DB layer. The field cannot be wired to
`project_id` (an integer FK) without a resolution path, so any value the model
extracts is silently dropped by `action_executor`. The field should be removed from the
schema entirely to prevent user confusion when `project` is stated but not recorded.

The CLI's `--project` flag (`time.py:187`, `type=int`) is unaffected — it is already
a Click-validated integer and is passed through to `time_entry_service.create_time_entry()`
as `project_id`. This item is Slack/schema-specific only.

**Why Deferred:**
Requires a `intent_parse_system_prompt.txt` edit + `config_version` bump + model
rebuild. Intentionally separated from INTENT_ACTION_SERVICE_LAYER_PART_1 to keep the
spec focused. The service layer already accepts `project_id: Optional[int] = None`
as a forward-compatible parameter.

**Acceptance Criteria:**

- [ ] `project` field removed from `create_time_entry` schema in
      `config/intent_parse_system_prompt.txt`
- [ ] `config_version` bumped and model rebuilt to new version
- [ ] `action_executor._execute_create_time_entry` no longer extracts or attempts
      to pass a string `project` field

**Files Affected:**

- `config/intent_parse_system_prompt.txt`
- `config/intent_parse_prompt.json` (`config_version`, `model_built`)
- `workmain/orchestration/action_executor.py` (remove dead `project` extraction if present)

---

#### Item 43 — meeting_id Non-Interactive Linkage for create_note / create_time_entry

**Status:** Open — Deferred to Phase 13 Sprint 3 (T6)
**Priority:** Medium
**Effort:** ~4–6 hrs
**Added:** 20260612
**Target Phase:** Phase 13 Sprint 3 — T6 conversational flow

**Description:**
The `notes_service.create_note()` and `time_entry_service.create_time_entry()` service
signatures accept `meeting_id: Optional[int] = None` as a forward-compatible parameter,
but it is always `None` in v1. Wiring it requires a non-interactive meeting resolution
path: given a meeting title or fuzzy description extracted from a Slack message, resolve
it to a `Meeting.id` without `click.confirm`/`click.prompt`. The current
`fuzzy_match_meeting()` and `interactive_meeting_picker()` helpers are built entirely
around interactive CLI I/O and cannot be used in daemon context.

**Why Deferred:**
Non-interactive meeting resolution is most naturally built as part of Sprint 3 T6
(conversational inline correction / multi-step clarification flow). The service
parameters are already in place; only the resolver and the `action_executor` wiring
remain.

**Acceptance Criteria:**

- [ ] A non-interactive `resolve_meeting_id(session, title_or_fragment)` helper exists
      that returns a `Meeting.id` or `None` (no interactive I/O)
- [ ] `action_executor._execute_create_note` and `_execute_create_time_entry` extract
      `meeting` from the action dict and pass a resolved `meeting_id` to the service
- [ ] Ambiguous matches return a clarification `ActionResult` (T6 pattern)
- [ ] Tests cover: exact match, fuzzy match, no match, ambiguous match

**Files Affected:**

- `workmain/database/repositories/meetings_repo.py` (non-interactive resolver)
- `workmain/orchestration/action_executor.py`
- `tests/test_action_executor.py`

---

#### Item 44 — entry_date / category as IntentParser Schema Fields (Phase 2)

**Status:** Open — Deferred to next model rebuild
**Priority:** Low
**Effort:** ~1–2 hrs
**Added:** 20260612
**Target Phase:** Next `intent_parse_system_prompt.txt` rebuild

**Description:**
`time_entry_service.create_time_entry()` already accepts `entry_date: Optional[date]`
and `category: Optional[str]` as parameters, added in v1.22.0 as forward-compatible
stubs. The service defaults `entry_date` to today and passes `category` through without
validation. To make these fields model-extractable from Slack messages, they need to be
added to the `create_time_entry` schema in `intent_parse_system_prompt.txt` with
examples, the `config_version` bumped, and the model rebuilt.

**Why Deferred:**
Deliberately separated from INTENT_ACTION_SERVICE_LAYER_PART_1 to keep the service
layer spec focused on the service extraction itself. The service is ready; only the
schema wiring and model rebuild remain.

**Acceptance Criteria:**

- [ ] `entry_date` field added to `create_time_entry` schema (ISO 8601 string, optional)
- [ ] `category` field added to `create_time_entry` schema (string, optional)
- [ ] At least 3 new examples in `intent_parse_system_prompt.txt` covering
      backdated entries and category extraction
- [ ] `config_version` bumped and model rebuilt
- [ ] `action_executor._execute_create_time_entry` extracts `entry_date` (parsed to
      `date`) and `category` and passes them to `time_entry_service.create_time_entry()`

**Files Affected:**

- `config/intent_parse_system_prompt.txt`
- `config/intent_parse_prompt.json` (`config_version`, `model_built`)
- `workmain/orchestration/action_executor.py`

---

#### Item 45 — `tags` Field for `create_time_entry` via Slack

**Status:** Open — Deferred to Phase 13 Sprint 3
**Priority:** Medium
**Effort:** ~3 hours
**Added:** 20260623
**Target Phase:** Phase 13 Sprint 3 — Slack UX / Block Kit

**Description:**
`create_time_entry` has no `tags` field in its IntentParser action schema,
so users cannot specify tags when creating time entries through the Slack
interface. Adding this requires two independent deliverables: (1) `tags`
field added to the `create_time_entry` action schema in
`config/intent_parse_system_prompt.txt`, which requires a `config_version`
bump and `workmain-intent` model rebuild; (2) Sprint 3 Block Kit UX work to
surface tag selection/input for Slack-originated time entry creation.
`time_entry_service.create_time_entry()` already accepts a `tags` parameter —
no service layer changes are needed; only the `action_executor` thin adapter
needs to forward `tags` from the action dict if present. Note: this item is
distinct from Item 44, which covers `entry_date` and `category` as
IntentParser schema fields and does not cover tags.

**Why Deferred:**
Both prerequisites (schema field addition + Block Kit UX) are Sprint 3 scope.
Neither was in scope during the service layer work (v1.22.0).

**Acceptance Criteria:**

- [ ] `tags` field added to `create_time_entry` schema in
      `intent_parse_system_prompt.txt`
- [ ] `config_version` bumped; `workmain-intent` model rebuilt and
      retagged `latest`
- [ ] `action_executor._execute_create_time_entry` forwards `tags` from
      action dict to service layer (absent field → empty list default)
- [ ] Block Kit UX surfaces tag selection/input for Slack time entry creation
- [ ] Slack-originated time entries correctly persist requested tags
- [ ] New tests cover `tags` passthrough in action_executor adapter

**Files Affected:**

- `config/intent_parse_system_prompt.txt`
- `workmain/orchestration/action_executor.py`
- Block Kit UX files (TBD — Sprint 3 Track 2)

---

#### Item 46 — `build_weekly_prompt()` Edge Cases: Short Weeks, Thursday Draft, Internal Content Pollution

**Status:** Open — Deferred to Phase 13
**Priority:** Medium
**Effort:** ~3–4 hours
**Added:** 20260623
**Target Phase:** Phase 13

**Description:**
Three known gaps in `build_weekly_prompt()` (introduced v2.1, partially corrected
v2.2 in hotfix items-33-34-incomplete-impl) that were not addressed during the
Item 34 work and require a coordinated fix:

**Gap 1 — Short work weeks:**
The confirmed-path condition is `weekdays_covered == {0, 1, 2, 3, 4}`. If Monday
is a bank holiday and EOD was only run Tue–Fri, `weekdays_covered = {1, 2, 3, 4}`,
which always falls back to raw data regardless of how many confirmed dailies exist.
Any week with a holiday or unworked day is permanently blocked from the confirmed
path.

**Gap 2 — Thursday draft weekly:**
On Thursday EOD the pipeline posts a Slack draft weekly report. At that point only
Mon–Thu confirmed dailies exist (Friday hasn't run yet), so `weekdays_covered`
never equals `{0, 1, 2, 3, 4}` and the confirmed path is unreachable. The Thursday
draft always uses raw data even if Mon–Thu are fully confirmed.

**Gap 3 — Internal content pollution:**
`get_confirmed_dailies()` returns `daily_internal` reports. Those reports are built
from all non-`client-report`/non-`info-only` notes — meaning they contain
`internal-only`, `carry-forward`, and `blocker` tagged content that should never
appear in a client-facing weekly report. Injecting confirmed daily summaries
verbatim into the `weekly_client` prompt risks leaking internal information to the
client.

**Why Deferred:**
Gaps 1 and 2 require a decision on the correct fallback threshold (count-based vs.
date-range-aware vs. day-of-week-aware). Gap 3 requires either: (a) filtering the
confirmed daily content before injection using tag-aware stripping, or (b) a
separate `daily_client` report type whose content is safe to forward. Both
approaches have downstream implications for the EOD pipeline and report schema that
should be scoped as a coherent unit rather than patched ad-hoc.

**Acceptance Criteria:**

- [ ] Short work weeks: confirmed path activates when all *actual working days* in
      the Mon–Fri range have a confirmed daily (e.g., 4 confirmed dailies on a
      Monday-holiday week satisfies the threshold)
- [ ] Thursday draft: confirmed path available for Thu EOD draft using the confirmed
      dailies that exist at that point (Mon–Thu), without requiring Friday
- [ ] Internal content filtering: confirmed daily summaries injected into the weekly
      client prompt contain only client-safe content; `internal-only`,
      `carry-forward`, and `blocker`-tagged content is excluded before injection
- [ ] Existing behavior (raw data fallback) preserved when no confirmed dailies exist

**Files Affected:**

- `workmain/ai/prompt_builder.py` — `build_weekly_prompt()` threshold + filtering logic
- `workmain/database/repositories/reports_repo.py` — `get_confirmed_dailies()` may
  need a `client_safe=True` variant or the caller handles filtering
