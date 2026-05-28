WorkmAIn
Feature Backlog v5.8
20260528

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
| 10 | Streamlined Model Update Process | Medium | Phase 15 | ~4–6 hrs | |
| 11 | Add New AI Provider | Low | — | ~8–12 hrs | |
| 12 | email.py Internal Session Refactor | Low | Phase 15 | ~30 min | |
| 13 | datetime.utcnow() Deprecation | Low | Phase 15 | ~30 min | |
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
| 32 | Task Deduplication and Forwarding | Low | Phase 13 | ~2–3 hrs | |
| 33 | correction_note Field Population | Low | Phase 13 | ~2 hrs | |

---

## Summary Statistics

**Total Items:** 33 (Item 22 is a redirect — no separate deferred work; see Item 20)
**Completed:** 7 (Items 17, 18, 20, 24, 25, 26, 27)
**Open:** 25

| Status | Count | Items |
|--------|-------|-------|
| Open (targeted) | 20 | 1, 2, 3, 4, 7, 8, 10, 12, 13, 14, 15, 16, 19, 23, 28, 29, 30, 31, 32, 33 |
| Conditional | 1 | 9 |
| Indefinitely | 4 | 5, 6, 11, 21 |
| Complete | 7 | 17, 18, 20, 24, 25, 26, 27 |
| Redirect | 1 | 22 → Item 20 |

| Priority | Count | Items |
|----------|-------|-------|
| High | 0 | — |
| Medium | 7 | 2, 3, 7, 10, 14, 15, 23 |
| Low | 17 | 1, 4, 5, 6, 8, 11, 12, 13, 16, 19, 21, 28, 29, 30, 31, 32, 33 |
| Conditional | 1 | 9 |

| Target Phase | Items |
|-------------|-------|
| Phase 11+ | 4, 28 |
| Phase 13 | 19, 32, 33 |
| Phase 14 | 31 |
| Phase 15 | 1, 2, 3, 7, 8, 10, 12, 13, 14, 15, 16, 23, 29 |
| Phase 18 | 30 |
| Conditional | 9 |
| Indefinitely | 5, 6, 11, 21 |

**Total Deferred Effort (open items):** ~87 hours

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

**Status:** Open — Deferred to Phase 15
**Priority:** Medium
**Effort:** ~4–6 hours
**Added:** 20260210
**Target Phase:** Phase 15

**Description:**
Documented process for updating AI model versions — steps for testing new model versions, updating model identifiers in code, verifying output quality, and committing changes. Demonstrated informally during Claude Sonnet 4 → 4.5 update.

**Why Deferred:**
Process exists informally and works. No urgent need to formalize. Phase 15 documentation pass.

**Acceptance Criteria:**
- [ ] Written process in `docs/` covering: locate model identifiers, test report quality, update code, commit format
- [ ] Model identifier locations documented (which files contain model strings)
- [ ] Quality checklist for comparing old vs new model output

**Files Affected:**
- New: `docs/MODEL_UPDATE_PROCESS.md`
- `workmain/ai/` (model identifier locations to document)

---

#### Item 11 — Add New AI Provider

**Status:** Deferred Indefinitely
**Priority:** Low
**Effort:** ~8–12 hours
**Added:** 20260210
**Target Phase:** None (revisit if a specific use case emerges)

**Description:**
Add support for a third AI provider beyond Claude (daily internal reports, note condensation) and Gemini (weekly client reports). A new provider would require a client in `workmain/ai/`, cost tracker entry, and template configuration.

**Why Deferred:**
No current use case. Two-provider architecture covers all report types. Speculative work until a specific provider or use case is identified. YAGNI.

**Acceptance Criteria (if implemented):**
- [ ] New provider client implemented in `workmain/ai/`
- [ ] Cost tracking supports new provider
- [ ] Template configuration supports provider assignment
- [ ] `workmain providers list` shows new provider

**Files Affected:**
- `workmain/ai/` (new provider client)
- `workmain/ai/cost_tracker.py`
- Template configuration files

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

**Status:** Open — Deferred to Phase 15
**Priority:** Low
**Effort:** ~30 min
**Added:** 20260309
**Target Phase:** Phase 15

**Description:**
`gdrive_repository.py` uses `datetime.utcnow()` (deprecated in Python 3.12). Logs a `DeprecationWarning`. No functional impact.

**Fix:** Replace with `datetime.now(timezone.utc)`.

**Why Deferred:**
No functional impact. Warning only. Phase 15 cleanup pass.

**Acceptance Criteria:**
- [ ] All `datetime.utcnow()` calls replaced with `datetime.now(timezone.utc)`
- [ ] No `DeprecationWarning` on `workmain gdocs` operations

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

**Status:** Open — Deferred to Phase 13 polish pass
**Priority:** Low (performance enhancement — not blocking)
**Effort:** ~2–3 hours
**Added:** 20260421
**Target Phase:** Phase 13 polish pass (after primary CPU path is validated)

**Description:**
Phase 13 deploys Mistral 7B on the Proxmox server (i9-12950HX) via Ollama for CPU-only intent parsing. Estimated latency: ~4–7 seconds per parse. Acceptable for Phase 13 use.

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
**Priority:** Medium (report quality / data leakage risk)
**Effort:** ~3–5 hours
**Added:** 20260327
**Target Phase:** Phase 15 (prompt quality pass)

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

**Status:** Open — Deferred to Phase 13
**Priority:** Low
**Effort:** ~2–3 hours
**Added:** 20260528
**Target Phase:** Phase 13

**Description:**
When multiple active carry-forward notes appear to cover the same work item, Phase 13's
Mistral 7B intent parser should identify them during Step 3c matching and propose a merge.
The surviving note keeps its `task_status` record (re-confirmed active); the deprecated
note's record is set to dismissed with `forwarding_note_id` pointing to the surviving note.

The `forwarding_note_id` column is already present in `task_status` as of v1.16.0 — no
additional migration needed.

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

**Status:** Open — Deferred to Phase 13
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
- [ ] Ollama/Mistral parses Slack DM correction intent and extracts reason
- [ ] `reports correct` (or Slack handler) writes structured reason to `correction_note`
- [ ] `reports show` displays `correction_note` when populated
