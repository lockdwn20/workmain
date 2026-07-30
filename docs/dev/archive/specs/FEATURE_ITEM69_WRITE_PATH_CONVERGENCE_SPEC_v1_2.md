WorkmAIn
FEATURE_ITEM69_WRITE_PATH_CONVERGENCE_SPEC v1.2
20260728

Version History:

- v1.0 (20260728): Initial spec. DRAFT — pending Opus (Role 2) review.
- v1.1 (20260728): Opus review round 1 applied.
  - **B1 (blocking, fixed):** Design Rule 8's condensed-tag classifier had
    a logic defect — a `both`-tagged source note voted client-facing but
    not internal, so a meeting whose only tagged note was `['both']`
    wrongly resolved to `['client-report']` instead of `['both']`.
    Corrected: `both` now votes on both axes.
  - **Ray's decisions (20260728), folded into the corrected classifier:**
    genuinely mixed internal-only + client-facing sources now
    conservatively collapse to `['internal-only']` (not `['both']`) —
    Ray: expected to be rare/should-not-occur, conservative if it does.
    All-info-only sources now output `['info-only']` (not
    `['internal-only']`) — Ray clarified this branch isn't actually
    reached via AI condensation today (the existing v1.6.7 has-notes gate
    redirects to a fixed "Attended `<Meeting>`" note first); that
    fallback note is treated as info-only here, matching its all-info-only
    provenance. Flagged for Ray's confirmation in chat, not re-elicited.
  - **B2 (blocking, fixed):** Gate 7's original AC1/AC2 close-out grep
    (`NotesRepository(.*\.create(`) only matched inline-instantiation call
    sites and missed every locally-bound-variable form (e.g.
    `notes_repo.create(...)`) — 7 of 8 direct-repo callers this item
    removes. It would have false-passed before any work was done.
    Replaced with a two-part audit (Gate 7). AC1 wording corrected to
    "outside `notes_service.py`/`time_entry_service.py`" —
    `create_time_entry()` legitimately calls `NotesRepository.create()`
    directly (Design Rule 6); the original AC1 prose contradicted the
    Gate 7 grep's own correct allowlist.
  - **D1 (Role 1 resolution, no viable alternative):** Clockify's
    `pull_entries(interactive: bool = True)` (sync.py:150) doesn't thread
    that flag into `_import_clockify_entry()` (sync.py:206). Gate 6's new
    per-entry tag prompt would block/raise under a non-interactive call.
    New Design Rule 15: thread `interactive` through; skip the prompt and
    apply the Design Rule 7 default when `False`.
  - **Gate 2 redesign (Opus caution addressed):** `update_note_tags()`
    replaced with a general `update_note()` that issues one repo call
    carrying whatever fields `notes edit` actually changed (matching
    `NotesRepository.update()`'s existing None-means-unchanged partial-update
    semantics, confirmed via the `time edit` H5 precedent) — removes the
    double-update/ordering risk of splitting tags into a separate call
    from content/meeting/project field updates.
  - **AC10/Gate 7:** the 882 baseline is unconfirmed as of this revision
    (v1.26.1's CHANGELOG states it, but may have drifted) — Gate 1 must
    confirm the live baseline via `python -m pytest tests/` before any
    other work begins, not trust the number in this spec.
  - Non-blocking / accepted as-is, no spec change: `create_time_entry()`
    keeping its own direct Note creation + manual hook call rather than
    composing `create_note()`/`create_paired_time_entry()` (Opus O1) —
    logged as a future cleanup candidate, not actioned this item.
- v1.2 (20260728): Opus review round 2 applied — targeted fix to the
  condensed-tag section only (round 2 independently verified
  `NotesRepository.update()`'s None-means-unchanged partial-update
  semantics against source, confirming Gate 2's redesign is sound, and
  confirmed B1/B2/D1/D2 all resolved correctly in v1.1). Two corrections:
  (1) the fabricated `"v1.6.7"` version citation (Design Rule 8, Gate 5)
  is removed — `note_condenser.py` is actually v2.1; the Attended-fallback
  behavior originated at the file's own v1.4, the info-only query filter
  at v1.3. (2) The mechanism explanation was inverted: the classifier
  never sees `info-only`-tagged notes at all —
  `condense_meeting()`'s own note-selection query (note_condenser.py:104-109)
  already filters them out before the classifier runs. An all-info-only
  meeting reaches `_compute_condensed_tags([])` — an empty list — not a
  list of info-only notes. Gate 5 now explicitly instructs both of
  `condense_meeting()`'s two return paths (the early "Attended
  `<Meeting>`" return, note_condenser.py:111-117, and the AI-summary
  return, note_condenser.py:168) to return a `(summary, resolved_tags)`
  tuple computed from that same query result — and warns against
  re-querying or falling through to `create_note()`'s default on the
  early-return path. Also removed the over-claim that the classifier's
  final branch "is not reached via AI condensation today" — a non-empty,
  no-routing-tag source set can reach it too (e.g. a carry-forward-only
  note, pending confirmation of `parse_tags`' default behavior at
  implementation time). Design Rule 14 updated from "must be confirmed"
  to a confirmed statement of `condense_meeting()`'s actual current
  return behavior. Opus confirmed this revision clean; approved by Ray
  20260728 (status-only update, no version increment).

---

## Status

**Approved by Ray on 20260728. Ready for Role 3 implementation.**
Opus confirmed round 2 clean (condensed-tag section correction verified);
no further review round required.

Recon basis: `RECON_SPEC_TASK_MATCH_DATA_INTEGRITY_SPRINT_20260725.md`,
Sections H/I/J and Addendum K — referenced, not reproduced.

Scope, shape, and Clockify disposition locked by Ray 20260727
(`SESSION_HANDOFF_ITEM69_SCOPE_LOCK_20260727.md`, decisions WPC1–WPC8).
Clockify `client_id`/tag-UX and condensed-tag classification decided by
Ray 20260728. All review-round findings (Opus rounds 1 and 2) applied.

Ready to hand to Role 3 (Claude Code / Sonnet). One Gate only per
session; handoff at every gate boundary to carry forward to new session.
Design questions stop and surface to Role 1 — never resolved in-flow.

## Scope

**In scope:**

- Converge all twelve H3 note-write surfaces onto three service-layer
  functions — `notes_service.create_note()`, `time_entry_service.create_time_entry()`,
  and a new `time_entry_service.create_paired_time_entry()` — plus two
  internal hook helpers, eliminating every direct
  `NotesRepository.create()` / `TimeEntriesRepository.create()` call
  outside the service layer.
- Relocate the CF→TaskStatus hook (`ensure_active` on creation,
  `ensure_active`/`set_dismissed_by_tag_removal` on tag transition) from
  the `notes.py` CLI layer into the service layer; remove the CLI-layer
  duplicate calls.
- Give surfaces #2, #8, #12 real, caller-specifiable tags, replacing their
  hard-coded `['both']` / `['internal-only']` literals.
- Fix #4/#9's condensed-summary output tag to reflect the actual tag
  composition of the notes it condensed, replacing the unconditional
  `['both']`.
- Fix #7's silently-defaulted `source` (`'ad-hoc'` → `'meeting'`, matching
  every sibling meeting-note surface).
- Stamp `client_id` consistently (auto-resolved `active_client_id`) on
  every surface that pairs a Note with a TimeEntry, including Clockify
  import (#12) — fixes the NULL-on-five-surfaces divergence K6 flagged.
- Add an interactive per-entry tag prompt to Clockify import (#12),
  mirroring the existing `notes log` per-line prompt pattern, gated on
  the surrounding call's existing `interactive` flag (Design Rule 15).
- Add a `created_at` backdate parameter to `notes_service.create_note()`
  (the repo already supports it — notes_repo.py:91; the gap is
  service-layer only).
- Document the converged write path as a CLAUDE.md contract.

**Out of scope:**

- Real tag input on Slack surfaces #10/#11 (schema/`action_executor.py`
  changes) — belongs to Item 45 / the Slack_LLM_Completion_Sprint. This
  spec only guarantees the plumbing is correct so that work needs zero
  additional service-layer wiring when it lands.
- Any change to `IntentParser.parse()` or the Slack action schema.
- Single-transaction atomicity across a Note+TimeEntry pair. Two-phase
  commit (Note commits, then TimeEntry commits) is preserved exactly as
  it behaves today on every migrated surface.
- Refactoring `create_time_entry()` to compose through `create_note()` +
  `create_paired_time_entry()` instead of its own direct Note creation
  (Opus O1) — touches a tested, currently-working function for a
  code-purity win with no user-visible behavior change; logged as a
  future cleanup candidate, not this item.
- Task_Match_Data_Integrity Sprint items (#48, #32, Item 70's orphan
  backfill / stale-dismissal repair) — sequenced after this item per the
  scope-lock handoff.
- `workmain tasks` command block gaps (Section J: paging, bulk
  complete/dismiss, `carryover` deprecation) — that is Sprint Gate 2,
  Item 67-adjacent, not this item.
- Any new CLI flag beyond what's needed to fix a stated bug (e.g., no new
  `--date` on `notes add`).
- Backdating Clockify import (#12). `created_at` stays import-time, not
  work-date — Ray confirmed this is by-design (2026-07-27), not a defect;
  `entry_date` on the paired TimeEntry continues to carry the real work
  date.

## Design Rules

Numbered, settled, non-negotiable.

1. **The converged family is three functions, not one universal
   signature** (WPC4): `notes_service.create_note()` (pure-note — also the
   first half of every paired write), `time_entry_service.create_time_entry()`
   (task-shaped, atomic, unchanged shape), and new
   `time_entry_service.create_paired_time_entry()` (the TimeEntry half of a
   meeting/condensed/Clockify pair, taking an already-created `Note`). Do
   not add a fourth signature or collapse these into one.

2. **Two internal hook helpers, defined once, in `notes_service.py`:**
   `apply_cf_hook_on_create(session, note)` and
   `apply_cf_hook_on_tag_update(session, note_id, old_tags, new_tags)`.
   `time_entry_service.py` imports both from `notes_service`. After this
   spec lands, no file outside `notes_service.py` may call
   `TaskStatusRepository(...).ensure_active(...)` or
   `.set_dismissed_by_tag_removal(...)` directly.

3. **Hook logic is relocated verbatim, not redesigned.** Both helpers
   reproduce the exact trigger conditions quoted in
   `RECON_SPEC_ITEM66_TASK_MATCH_QUALITY_20260725.md` F1
   (`notes.py:375-377` for create, `notes.py:500-507` for transition) —
   same `'carry-forward' in (...)` checks, same `session.commit()`
   placement. Only the location changes.

4. **`client_id` is auto-resolved internally on every surface**, including
   Clockify (#12) — Ray, 20260728. `create_note()` and `create_time_entry()`
   already resolve `active_client_id` internally (unchanged pattern);
   `create_paired_time_entry()` resolves it by reading `note.client_id`
   from the already-created Note, never independently — this guarantees
   the pair can never diverge, which is exactly how #8/#9/#12 ended up
   with a NULL-on-TimeEntry-only omission today (K3/K4).

5. **`created_at` backdating.** `create_note()` gains a `created_at`
   parameter forwarded straight to `NotesRepository.create()` (already
   supported — notes_repo.py:91). Backdating callers (#5, #7) pass it.
   Clockify (#12) explicitly passes `created_at=None` (import time) — do
   not backdate it to `entry_date`; this is confirmed intentional (Ray,
   2026-07-27), not a gap to close.

6. **Task-shaped stays task-shaped.** `create_time_entry()`'s `source`
   stays hard-coded `"task"` (not caller-settable) and `meeting_id`/
   `project_id` stay routed to the TimeEntry only, never the Note (WPC4,
   intentional). Do not add a `source` param or Note-side `meeting_id`
   routing to this function.

7. **Tag default is unchanged and universal:** any caller that supplies no
   tags (or an empty list) resolves to `['internal-only']` — the existing
   `create_note()`/`create_time_entry()` behavior, applied without
   exception to every new caller, including a skipped/blank Clockify
   per-entry prompt (also the non-interactive fallback per Design Rule 15).

8. **Condensed-summary tag classification** (`#4`/`#9`, computed in
   `note_condenser.py`, consumed by both call sites), over the note set
   `condense_meeting()`'s existing note-selection query already returns
   (note_condenser.py:104-109, which pre-filters out `info-only` notes
   via `~Note.tags.op('@>')(['info-only'])`) — *not* a separately-queried
   set (Gate 5 has the full two-return-path wiring):

   ```python
   def _compute_condensed_tags(source_notes: List[Note]) -> List[str]:
       all_tags = set()
       for n in source_notes:
           all_tags |= set(n.tags or [])

       has_internal_only = 'internal-only' in all_tags
       has_client_report = 'client-report' in all_tags
       has_both = 'both' in all_tags
       is_client_facing = has_client_report or has_both

       if has_internal_only and is_client_facing:
           # Genuinely mixed-audience sources: conservative -- keep the
           # whole synthesized summary out of the client report rather
           # than risk blending internal-only content into client-visible
           # output (Ray, 20260728). Expected to be rare in practice.
           return ['internal-only']
       if is_client_facing:
           # No internal-only source present: honor the sources' own
           # explicit client-facing intent, including a pure 'both'
           # source (fixes the B1 classifier defect -- Opus review round 1
           # -- where a lone 'both'-tagged source wrongly failed to vote
           # on the internal axis).
           return ['both'] if has_both else ['client-report']
       if has_internal_only:
           return ['internal-only']
       # Empty (or, in principle, non-empty-but-no-routing-tag) source
       # set. Reached two ways in practice (Opus review round 2): (a)
       # condense_meeting()'s own query already filters info-only notes
       # out before this function ever sees them, so an all-info-only
       # meeting produces an EMPTY notes list here -- the classifier
       # isn't "inspecting" info-only content, it's falling through on a
       # set with no internal/client-facing signal at all (this is the
       # set behind the existing "Attended <Meeting>" fallback -- see
       # Gate 5 for the exact wiring); or (b) a non-empty set where no
       # note carries any report-routing tag (e.g. a carry-forward-only
       # note, if parse_tags permits that -- confirm at implementation
       # time, do not assume it can't happen). Either way, ['info-only']
       # keeps the result out of both reports.
       return ['info-only']
   ```

9. **`create_paired_time_entry()` derives, never re-resolves.**
   `meeting_id` and `client_id` on the TimeEntry come from `note.meeting_id`
   / `note.client_id` on the Note object passed in — not from independent
   parameters — by construction, so the pair cannot re-diverge the way
   #8/#9/#12 have today.

10. **The `existing_today` create-or-relink branch (#4/#9) is preserved
    verbatim** (`notes.py:754`, `meetings.py:956`). Only its *target*
    changes — from a direct repo call to `create_note()` +
    (conditionally) `create_paired_time_entry()` or a relink — the branch
    condition itself is untouched. Quote the current branch from source
    before editing it (Pitfall #12 — do not work from this spec's
    paraphrase alone).

11. **Interactive tag prompts added to #2, #8, #12 mirror the existing
    `notes log` per-line prompt** (`notes.py:669`, advertising `#cf`) —
    do not invent new prompt UX. Quote the existing pattern from source
    before implementing the new call sites.

12. **#7's `source` bug fix:** default becomes `'meeting'` (was silently
    `'ad-hoc'` via omission) — matches every sibling meeting-note surface
    (#2, #3, #5, #8).

13. **Two-phase commit is preserved, not atomized.** `create_note()`'s
    repo call commits; `create_paired_time_entry()`'s repo call commits
    separately after it. This matches every migrated surface's existing
    behavior — introducing cross-entity transactional atomicity is out of
    scope for this item.

14. **`note_condenser.condense_meeting()`'s current behavior, confirmed
    against source (Opus review rounds 1–2):** exactly two callers
    (`meetings.py:919`, `notes.py:733`); two return statements, both
    currently returning a bare `str` — the early
    `f"Attended {db_meeting.title}"` return (note_condenser.py:111-117,
    fired when the note-selection query returns empty) and the
    AI-summary return (note_condenser.py:168). Gate 5 changes both to
    return `(summary, resolved_tags)` — see Gate 5 for the exact
    per-path instructions; do not extend only one path.

15. **Clockify's per-entry tag prompt only fires when the surrounding
    call is interactive** (Opus review round 1, D1). `pull_entries(interactive:
    bool = True)` (sync.py:150) must thread that flag into
    `_import_clockify_entry()` (sync.py:206, which currently receives no
    interactivity signal — confirmed against source). When `interactive=False`:
    skip the prompt entirely and apply the Design Rule 7 default
    (`['internal-only']`) — never block or raise.

## Branch & Git Workflow

Per `GIT_WORKFLOW_STANDARDS.md` v1.7 (check the live doc — don't assume
this citation is still current).

- **Branch type:** `feature/*`
- **Branch name:** `feature/write-path-convergence`
- **Branches from:** `dev`
- **Merges to:** `dev` (then `dev` → `main` via GitHub PR, per standard flow)
- **Commit strategy:** one descriptive commit per gate (body: files
  changed, decisions applied, test count). `Co-Authored-By: Claude` on all
  commits. Session discipline: one gate per Claude Code session; handoff
  at every gate boundary; design questions stop and surface to Role 1,
  never resolved in-flow.
- **Deployment:** touches `workmain/**` → **restart-and-verify mandatory**
  after the feature branch merges to `dev`:

  ```bash
  systemctl --user restart workmain-notify.service
  systemctl --user show workmain-notify.service --property=ActiveEnterTimestamp
  ```

  Confirm the new `ActiveEnterTimestamp` postdates the merge commit before
  reporting deployed.
- **Version bump:** `__version__.py` **1.26.1 → 1.27.0** (feature merge =
  minor bump, per Version Bump Rules).
- **Release:** after `dev` → `main` via PR, tag `v1.27.0`, push tags,
  create the GitHub Release object
  (`gh release create v1.27.0 --generate-notes`) — the tag alone is not a
  complete release (standards v1.7). Verify with
  `gh release view v1.27.0` before reporting the release complete.

## Gates

### Gate 1 — Pure-note family convergence + CF hook relocation (create path)

- **Files:** `workmain/services/notes_service.py` (v1.0 → v1.1),
  `workmain/cli/commands/notes.py` (v4.2 → v4.3),
  `workmain/cli/commands/time.py` (v1.7 → v1.8),
  `tests/test_notes_service.py`, `tests/test_notes.py`, `tests/test_time.py`
- **Pre-work (blocking, do first):** run `python -m pytest tests/` and
  record the actual current baseline before touching any source — this
  spec's "882" figure (from v1.26.1's CHANGELOG) is unconfirmed and may
  have drifted (Opus review round 1).
- **Changes:**

  In `notes_service.py`, add two new module-level functions (service-internal,
  but imported by `time_entry_service.py` — not underscore-prefixed):

  ```python
  def apply_cf_hook_on_create(session, note: Note) -> None:
      """Create an active TaskStatus row if the note carries carry-forward.
      Relocated verbatim from notes.py:375-377 (Phase 12 Gate 3)."""
      if 'carry-forward' in (note.tags or []):
          TaskStatusRepository(session).ensure_active(note.id)
          session.commit()

  def apply_cf_hook_on_tag_update(session, note_id: int, old_tags: List[str], new_tags: List[str]) -> None:
      """Handle a CF tag transition (add or remove) on an existing note.
      Relocated verbatim from notes.py:500-507 (Phase 12 Gate 3)."""
      if new_tags is None:
          return
      task_repo = TaskStatusRepository(session)
      if 'carry-forward' in new_tags and 'carry-forward' not in (old_tags or []):
          task_repo.ensure_active(note_id)
          session.commit()
      elif 'carry-forward' not in new_tags and 'carry-forward' in (old_tags or []):
          task_repo.set_dismissed_by_tag_removal(note_id)
          session.commit()
  ```

  Extend `create_note()`'s signature with `created_at: Optional[datetime] = None`,
  forward it to `NotesRepository(session).create(..., created_at=created_at)`,
  and call `apply_cf_hook_on_create(session, note)` on the returned note
  before returning it. All other body logic (tag resolution/validation,
  `active_client_id` resolution) is unchanged.

  In `notes.py`:
  - `notes add` (#1): remove the CLI-layer `if 'carry-forward' in (note.tags
    or []): TaskStatusRepository(session).ensure_active(note.id);
    session.commit()` block (notes.py:375-377) — the service now does this.
  - `notes log -m` per-line (#3): replace the direct
    `NotesRepository(session).create(...)` call (notes.py:701) with
    `notes_service.create_note(session, content=clean_text, tags=note_tags
    or ['internal-only'], source='meeting', meeting_id=meeting_obj.id)`.
    Confirm the exact current parameter names/values against source before
    substituting — this spec's paraphrase must match what K3 quoted.

  In `time.py`:
  - `time add` extra note (#7): replace the direct
    `NotesRepository(session).create(...)` call (time.py:361) with
    `notes_service.create_note(session, content=note_content,
    tags=note_tags, source='meeting', meeting_id=meeting_obj.id,
    created_at=note_created_at)` — Design Rule 12's source fix is applied
    here (was omitted → silently `'ad-hoc'`).

  No code change required for #10 (Slack create-note) — it already calls
  `notes_service.create_note()`; it benefits from the hook automatically.

- **Tests:**
  - `test_create_note_fires_cf_hook_when_carry_forward_tagged` —
    `tags=['carry-forward']`; asserts an active `TaskStatus` row exists
    for the returned note's id.
  - `test_create_note_no_hook_without_carry_forward` — `tags=['internal-only']`;
    asserts no `TaskStatus` row is created.
  - `test_create_note_backdates_created_at` — exact input
    `created_at=datetime(2026, 7, 1, 9, 0)`; asserts the returned note's
    `created_at` equals that exact value, not "now".
  - `test_notes_log_per_line_routes_through_service` — mocks/spies
    `notes_service.create_note`; asserts it's called once per line with
    the per-line parsed tags.
  - `test_time_add_extra_note_source_defaults_to_meeting` — no `--source`
    supplied; asserts the created note's `source == 'meeting'` (not
    `'ad-hoc'`) — regression test for Design Rule 12.
- **Version bump:** `notes_service.py` v1.1, `notes.py` v4.3, `time.py` v1.8,
  each with a version-history line describing the change.
- **Human approval checkpoint:** Ray confirms the hook fires correctly on
  `notes add` and `notes log -m` (manual smoke test) before Gate 2.

### Gate 2 — Tag-transition convergence (update path)

- **Files:** `workmain/services/notes_service.py` (v1.1 → v1.2),
  `workmain/cli/commands/notes.py` (v4.3 → v4.4),
  `tests/test_notes_service.py`, `tests/test_notes.py`
- **Changes:**

  In `notes_service.py`, add a general update function — **not** a
  tags-only function — so `notes edit` keeps making one repo call instead
  of splitting into two (Opus review round 1 caution: a separate
  tags-only call alongside a separate content/meeting/project call risks
  a double-update/ordering seam):

  ```python
  def update_note(
      session,
      note_id: int,
      content: Optional[str] = None,
      tags: Optional[List[str]] = None,
      meeting_id: Optional[int] = None,
      project_id: Optional[int] = None,
  ) -> Note:
      """General note update; applies the CF-transition hook when tags
      change. Single repo call -- relies on NotesRepository.update()'s
      existing None-means-unchanged partial-update semantics (confirmed
      via the 'time edit' precedent, H5). Do not split this into
      per-field update calls."""
      existing = NotesRepository(session).get_by_id(note_id)
      old_tags = list(existing.tags or [])
      if tags is not None:
          tag_system = get_tag_system()
          _, invalid = tag_system.validate_full_names(tags)
          if invalid:
              valid_vocab = tag_system.get_valid_full_names()
              raise InvalidTagsError(invalid_tags=invalid, valid_tags=valid_vocab)
      updated_note = NotesRepository(session).update(
          note_id=note_id, content=content, tags=tags,
          meeting_id=meeting_id, project_id=project_id,
      )
      if tags is not None:
          apply_cf_hook_on_tag_update(session, note_id, old_tags, tags)
      return updated_note
  ```

  `NotesRepository.get_by_id()` exists (confirmed against source, Opus
  review round 1: notes_repo.py:137).

  In `notes.py`, `notes edit`'s current update call(s) (notes.py:488-507)
  are replaced with a single call to `notes_service.update_note(session,
  note_id, content=..., tags=..., meeting_id=..., project_id=...)`,
  passing `None` for whatever fields the user didn't change. **Quote the
  exact current structure from source first** — confirm whether `notes
  edit` already issues one combined `update()` call or two separate ones;
  if source shows two, converge them into this single call, don't
  preserve a split (Opus review round 1 flagged this as a real
  integration seam, not a paraphrase nit).

- **Tests:**
  - `test_update_note_transitions_cf_add` — `old_tags=['internal-only']`,
    `new_tags=['internal-only', 'carry-forward']`; asserts a new active
    `TaskStatus` row appears.
  - `test_update_note_transitions_cf_remove` — `old_tags=['carry-forward']`,
    `new_tags=['internal-only']`; asserts the existing `TaskStatus` row is
    dismissed via `set_dismissed_by_tag_removal`.
  - `test_update_note_no_transition_when_cf_unchanged` — CF present in
    both old and new tags; asserts no additional hook call fires.
  - `test_update_note_content_only_does_not_touch_tags_or_hook` — `tags=None`,
    `content=<new text>`; asserts tags are unchanged and no hook call
    fires — proves the None-means-unchanged path is respected.
  - `test_notes_edit_routes_through_single_service_call` — CLI-level test
    confirming `notes edit` calls `update_note()` exactly once per
    invocation, not a separate tags call plus a separate content call.
- **Version bump:** `notes_service.py` v1.2, `notes.py` v4.4.
- **Human approval checkpoint:** Ray confirms `notes edit` CF add/remove
  and plain content edits still behave identically from the CLI (manual
  smoke test) before Gate 3.

### Gate 3 — Task-shaped family hook wiring (#6, #11)

- **Files:** `workmain/services/time_entry_service.py` (v1.0 → v1.1),
  `tests/test_time_entry_service.py`, `tests/test_action_executor.py`
  (verification only — no source change expected)
- **Changes:**

  In `time_entry_service.py`, import the two hook helpers from
  `notes_service` and call `apply_cf_hook_on_create(session, note)`
  immediately after the Note is created in `create_time_entry()`
  (notes-repo call at time_entry_service.py:84-90), before the
  `TimeEntriesRepository(session).create(...)` call. No parameter-list
  change to `create_time_entry()` — Design Rule 6 applies.

  No CLI or `action_executor.py` change is required for #6 or #11 — both
  already route through this service (H3); they inherit the hook for
  free.

- **Tests:**
  - `test_create_time_entry_fires_cf_hook` — `tags=['carry-forward']` on a
    non-meeting `time add`-style call; asserts an active `TaskStatus` row
    exists for the created note.
  - `test_create_time_entry_no_hook_without_carry_forward` — control case.
  - `test_action_executor_slack_time_entry_cf_note_creates_task` —
    exercises `_execute_create_time_entry` with a CF tag (if the
    action schema permits it today per K3's #11 note — if the schema
    truly cannot carry tags at all yet, this test documents that gap
    rather than asserting a false pass; confirm current schema capability
    against `action_executor.py` before writing this test).
- **Version bump:** `time_entry_service.py` v1.1.
- **Human approval checkpoint:** Ray confirms a live `time add` (no
  `-m`) with `--tags cf` produces an active task before Gate 4.

### Gate 4 — Meeting-shaped family (#2, #5, #8) + `create_paired_time_entry()`

- **Files:** `workmain/services/time_entry_service.py` (v1.1 → v1.2),
  `workmain/cli/commands/notes.py` (v4.4 → v4.5),
  `workmain/cli/commands/time.py` (v1.8 → v1.9),
  `workmain/cli/commands/meetings.py` (v4.5 → v4.6),
  `tests/test_time_entry_service.py`, `tests/test_notes.py`,
  `tests/test_time.py`, `tests/test_meetings.py`
- **Changes:**

  In `time_entry_service.py`, add:

  ```python
  def create_paired_time_entry(
      session,
      note: Note,
      duration_hours: float,
      entry_date: date,
      entry_time: time_type,
      category: Optional[str] = None,
      project_id: Optional[int] = None,
      clockify_id: Optional[str] = None,
  ) -> TimeEntry:
      """Create the TimeEntry half of a Note+TimeEntry pair. meeting_id and
      client_id are derived from the already-created note (Design Rules
      4 and 9) so the pair cannot diverge. synced_at is stamped whenever
      clockify_id is supplied."""
      return TimeEntriesRepository(session).create(
          note_id=note.id,
          duration_hours=duration_hours,
          entry_date=entry_date,
          entry_time=entry_time,
          category=category,
          project_id=project_id,
          meeting_id=note.meeting_id,
          client_id=note.client_id,
          clockify_id=clockify_id,
          synced_at=datetime.now() if clockify_id else None,
      )
  ```

  `TimeEntriesRepository.create()`'s existing signature (v1.11,
  time_entries_repo.py:93-106) already accepts every parameter used here
  — no repo change needed (K5).

  In `notes.py`, #2 (meeting time-entry follow-on, notes.py:402-408):
  replace the direct-repo write (`tags=['both']` hard-coded) with an
  interactive tag prompt (Design Rule 11, mirroring notes.py:669's
  pattern — quote it first), then:

  ```python
  new_note = notes_service.create_note(session, content=time_description,
      tags=prompted_tags, source='meeting', meeting_id=note.meeting.id)
  time_entry_service.create_paired_time_entry(session, new_note,
      duration_hours=meeting_duration,
      entry_date=note.meeting.start_time.date(),
      entry_time=note.meeting.start_time.time(), category='meeting')
  ```

  In `time.py`, #5 (`time add -m` meeting path, time.py:313-319 +
  paired TimeEntry): replace both direct-repo calls with:

  ```python
  new_note = notes_service.create_note(session, content=primary_content,
      tags=note_tags, source='meeting', meeting_id=meeting_obj.id,
      created_at=note_created_at)
  time_entry_service.create_paired_time_entry(session, new_note,
      duration_hours=duration_hours, entry_date=entry_date,
      entry_time=entry_time, category=category, project_id=project)
  ```

  This is also where #5's `client_id`-NULL omission is fixed — it now
  flows through `create_note()`'s existing internal resolution, same as
  every sibling surface.

  In `meetings.py`, #8 (meetings-flow time-entry note, meetings.py:752-765):
  same pattern as #2 — add the tag prompt, then `create_note()` +
  `create_paired_time_entry()`, fixing its `client_id`-NULL omission on
  both the Note and the TimeEntry (K3).

  Quote each of #2/#5/#8's current source blocks verbatim before editing
  — this spec's paraphrase of exact variable names may not match a source
  that has drifted since the 20260725/20260727 recon passes (Pitfall #12).

- **Tests:**
  - `test_create_paired_time_entry_derives_meeting_id_from_note` — note
    with `meeting_id=42`; asserts the created TimeEntry's `meeting_id == 42`
    without it being passed as a separate argument.
  - `test_create_paired_time_entry_derives_client_id_from_note` — note
    with `client_id=<X>` that differs from whatever `active_client_id`
    would resolve to at call time; asserts the TimeEntry's `client_id`
    matches the note's, proving derivation-from-note, not independent
    resolution (Design Rule 9).
  - `test_notes_add_meeting_followon_prompts_and_stamps_real_tag` — #2
    end-to-end; asserts the created note carries the tag entered at the
    prompt, not `['both']`.
  - `test_time_add_meeting_path_client_id_no_longer_null` — #5 regression
    test; asserts both the Note and TimeEntry carry `active_client_id`.
  - `test_meetings_flow_time_entry_client_id_no_longer_null` — #8
    equivalent.
- **Version bump:** `time_entry_service.py` v1.2, `notes.py` v4.5,
  `time.py` v1.9, `meetings.py` v4.6.
- **Human approval checkpoint:** Ray confirms live: a real meeting note
  follow-on (#2) and a real `meetings` flow entry (#8) each prompt for a
  tag and the tag sticks, before Gate 5.

### Gate 5 — Condensed-summary tag fix (#4, #9)

- **Files:** `workmain/ai/note_condenser.py` (v2.1 → v2.2 — confirmed
  against source, Opus review round 2),
  `workmain/cli/commands/notes.py` (v4.5 → v4.6),
  `workmain/cli/commands/meetings.py` (v4.6 → v4.7),
  `tests/test_note_condenser.py` (confirm exact filename against `tests/`),
  `tests/test_notes.py`, `tests/test_meetings.py`
- **Changes:**

  In `note_condenser.py`, add the classification helper exactly as
  specified in Design Rule 8 (`_compute_condensed_tags()`).

  `condense_meeting()`'s existing note-selection query (note_condenser.py:104-109)
  already filters out `info-only` notes via
  `~Note.tags.op('@>')(['info-only'])`. Compute
  `resolved_tags = _compute_condensed_tags(notes)` **once**, immediately
  after that query runs, using its result — before either of the
  function's two return statements (Opus review round 2, correcting this
  spec's earlier inverted account of how the info-only case resolves):
  - **Early return** (note_condenser.py:111-117:
    `if not notes: return f"Attended {db_meeting.title}"`) — change to
    `return f"Attended {db_meeting.title}", resolved_tags`. `notes` is
    `[]` on this path, so `resolved_tags` correctly resolves to
    `['info-only']` via the classifier's final branch — a property of the
    empty filtered set, not of the classifier "seeing" info-only content
    (it never does; those notes are already excluded from `notes` by the
    query itself, before this function runs).
  - **AI-summary return** (note_condenser.py:168) — change to also
    return `summary, resolved_tags`.

  **Do not** re-query to include `info-only` notes on the early-return
  path, and **do not** let either path fall through to `create_note()`'s
  `['internal-only']` default — either would silently reintroduce
  internal-report visibility for content this change is meant to exclude
  (the exact regression the original hard-coded `['both']` produced).

  Update both of `condense_meeting()`'s two confirmed call sites
  (`meetings.py:919`, `notes.py:733`) to unpack the new two-tuple return.

  In `notes.py`, #4: replace `tags=['both']` with the condenser's
  `resolved_tags`; replace the direct-repo Note+TimeEntry writes with
  `notes_service.create_note(..., source='condensed')`, then —
  preserving the `existing_today` branch verbatim (notes.py:754, Design
  Rule 10) — either `create_paired_time_entry()` (no existing entry today)
  or the existing relink (`entry.note_id = new_note.id`).

  In `meetings.py`, #9: identical pattern, preserving its own
  `existing_today` branch at meetings.py:956.

- **Tests:**
  - `test_compute_condensed_tags_all_client_report` → `['client-report']`.
  - `test_compute_condensed_tags_all_internal_only` → `['internal-only']`.
  - `test_compute_condensed_tags_single_both_tagged_source` — source notes
    `['both']` only (no separate `internal-only`/`client-report` tag) →
    `['both']` — direct regression test for the B1 classifier defect
    (Opus review round 1).
  - `test_compute_condensed_tags_mixed_internal_and_client_report_collapses_to_internal` —
    source notes `[internal-only, client-report]` → `['internal-only']`
    (Ray's conservative rule, 20260728).
  - `test_compute_condensed_tags_mixed_internal_and_both_collapses_to_internal` —
    source notes `[internal-only, both]` → `['internal-only']` (same
    conservative rule applied to the `both` variant).
  - `test_compute_condensed_tags_empty_set_returns_info_only` —
    `_compute_condensed_tags([])` → `['info-only']` — the classifier call
    behind the "Attended `<Meeting>`" fallback path (Opus review round 2:
    the query pre-filters `info-only` notes out upstream, so this path
    always sees an empty list, never a list of `info-only`-tagged notes).
  - `test_compute_condensed_tags_no_routing_tags_non_empty_returns_info_only` —
    a non-empty source-note list where no note carries `internal-only`/
    `client-report`/`both` (e.g. carry-forward-only tags) → `['info-only']`
    — proves the AI path can also reach this branch, correcting this
    spec's earlier over-claim that it couldn't (Opus review round 2).
  - `test_condense_meeting_attended_fallback_returns_tuple` — end-to-end:
    a meeting whose only notes are `info-only`; asserts `condense_meeting()`
    returns `("Attended <Meeting>", ['info-only'])` as a 2-tuple, not a
    bare string.
  - `test_condense_meeting_ai_path_returns_tuple` — end-to-end: a normal
    AI-summarized meeting; asserts the return is also a
    `(summary, resolved_tags)` 2-tuple.
  - `test_notes_log_condense_uses_computed_tags_not_both` — end-to-end #4;
    asserts the condensed note's tags are no longer unconditionally `['both']`.
  - `test_meetings_condense_uses_computed_tags_not_both` — #9 equivalent.
  - `test_condense_existing_today_relinks_not_recreates` — regression test
    for Design Rule 10; asserts a second same-day condensation relinks the
    existing TimeEntry's `note_id` rather than creating a second TimeEntry.
- **Version bump:** `note_condenser.py` v2.2, `notes.py` v4.6, `meetings.py` v4.7.
- **Human approval checkpoint:** Ray reviews a live condensed summary from
  a meeting with genuinely mixed-tag source notes and confirms the output
  tag is `['internal-only']` (not `['both']`, not a crash), before Gate 6.

### Gate 6 — Clockify family (#12)

- **Files:** `workmain/integrations/clockify/sync.py` (v1.4 → v1.5),
  `tests/` — clockify sync test module (confirm exact filename against
  `tests/` before this gate)
- **Changes:**

  #12 (sync.py:330-343): add an interactive per-entry tag prompt to the
  pull loop (Ray's decision, 20260728), mirroring the existing `notes log`
  prompt pattern (Design Rule 11 — quote it first), gated on the
  interactivity threading required by Design Rule 15. Replace the
  direct-repo writes with:

  ```python
  new_note = notes_service.create_note(session, content=description,
      tags=prompted_tags, source='clockify')  # created_at omitted -- Design Rule 5
  time_entry_service.create_paired_time_entry(session, new_note,
      duration_hours=duration_hours, entry_date=start_dt.date(),
      entry_time=start_dt.time().replace(tzinfo=None),
      clockify_id=clockify_entry['id'])
  ```

  `client_id` is no longer explicitly omitted — it now flows through
  `create_note()`'s existing internal `active_client_id` resolution
  (Ray's decision, 20260728: stamp the active client at import time,
  consistent with every other surface).

  Thread `pull_entries(interactive: bool = True)`'s existing flag
  (sync.py:150) into `_import_clockify_entry()` (sync.py:206, confirmed
  against source to currently receive no interactivity signal — Opus
  review round 1): when `interactive=False`, skip the prompt and apply
  the `['internal-only']` default (Design Rule 15) rather than blocking.

  Quote the current pull loop verbatim before restructuring it — this
  spec has not seen the file directly (source `.py` files aren't in the
  project's knowledge base per its own documented limitation); the line
  numbers above are as confirmed by Opus's review-round-1 source check,
  not this spec's own recon. Stop and surface to Role 1 if the actual
  structure diverges materially from what this spec assumes (Pitfall #12).

- **Tests:**
  - `test_clockify_import_stamps_active_client_id` — asserts the imported
    Note and TimeEntry both carry `active_client_id`, not NULL.
  - `test_clockify_import_created_at_not_backdated` — asserts `created_at`
    is close to "now" at test run time and explicitly not equal to
    `entry_date`'s midnight — not just "not backdated" in the abstract.
  - `test_clockify_import_per_entry_tag_prompt` — asserts a tag entered at
    the prompt is stamped on the imported note, not the hard-coded
    `['internal-only']`.
  - `test_clockify_import_blank_prompt_defaults_internal_only` — control
    case for Design Rule 7.
  - `test_clockify_import_skips_prompt_when_noninteractive` —
    `pull_entries(interactive=False)`; asserts no prompt is invoked and
    the imported note defaults to `['internal-only']` — regression test
    for Design Rule 15.
  - `test_clockify_import_cf_tag_creates_task` — a Clockify entry tagged
    `carry-forward` at the prompt produces an active TaskStatus row
    (confirms the hook now reaches Clockify too).
- **Version bump:** `clockify/sync.py` v1.5.
- **Human approval checkpoint:** Ray runs a live `workmain clockify sync`
  pull, confirms the per-entry prompt appears, tags stick, and
  `client_id` is stamped, before Gate 7.

### Gate 7 — CLAUDE.md contract, close-out, live verification, release

- **Files:** `CLAUDE.md`, `__version__.py` (1.27.0), `CHANGELOG.md`
- **Changes:**

  Add a new subsection under CLAUDE.md's "Key Design Decisions":

  ```
  ### Note Write-Path Convergence — Source of Truth

  All note and paired-TimeEntry creation goes through the service layer:
  - `notes_service.create_note()` — pure-note writes; also the first half
    of every paired write.
  - `time_entry_service.create_time_entry()` — task-shaped paired write
    (source='task', meeting_id never reaches the Note — intentional).
  - `time_entry_service.create_paired_time_entry()` — the TimeEntry half
    of a meeting/condensed/Clockify pair; derives meeting_id/client_id
    from the already-created Note.

  No file outside notes_service.py calls TaskStatusRepository.ensure_active
  or .set_dismissed_by_tag_removal directly. The CF->TaskStatus hook fires
  from notes_service.apply_cf_hook_on_create() (on any create call) and
  notes_service.apply_cf_hook_on_tag_update() (on any tag-mutating update,
  e.g. `notes edit` via update_note()). No direct NotesRepository.create() /
  TimeEntriesRepository.create() call should exist outside
  notes_service.py / time_entry_service.py.
  ```

  While in the file, correct the stale "671 passing" baseline reference
  (Architecture section) to the current suite count as of this item's close
  — opportunistic, single-line, no scope expansion.

  Full regression suite run: confirmed live baseline (from Gate 1's
  pre-work) + all new tests from Gates 1–6, record the actual total in the
  commit body, zero regressions.

  **Live verification (expanded set, per
  `SESSION_HANDOFF_ITEM69_SCOPE_LOCK_20260727.md`):**
  1. A CF-tagged note through each of `notes log -m`, `time add`, and
     Slack produces an active TaskStatus row.
  2. Each of #2, #4/#9, #8 (previously hard-coded `['both']`) and #12
     (Clockify) is demonstrated live carrying a real, content-accurate
     tag — not the old hard-coded literal.
  3. #7's `source` is confirmed `'meeting'` on the additional-note path.
  4. #4/#9's condensed-summary output tag is confirmed to reflect the
     actual tag composition of the notes it condensed on a real
     mixed-tag meeting (expect `['internal-only']` per Ray's conservative
     rule, not an unconditional `['both']`).
  5. A meeting whose notes are all `info-only` produces its "Attended
     `<Meeting>`" fallback note tagged `['info-only']` (excluded from
     both reports) — not the old unconditional `['both']`, and not a
     crash on the new tuple return.
  6. Close-out audit (Opus review round 1 correction — the naive grep
     originally specified here would have false-passed by missing every
     locally-bound-variable call form, e.g. `notes_repo.create(...)`):
     a. `grep -rn "\.create(" workmain/cli/commands/notes.py workmain/cli/commands/time.py workmain/cli/commands/meetings.py workmain/integrations/clockify/sync.py`
        — confirm every hit's receiver is `notes_service.create_note(`,
        `time_entry_service.create_time_entry(`, or
        `time_entry_service.create_paired_time_entry(`, never a
        `NotesRepository`/`TimeEntriesRepository` instance or a variable
        bound to one (`notes_repo`, `repo`, `time_repo`, etc.).
     b. `grep -rn "NotesRepository(\|TimeEntriesRepository(" workmain/ --include="*.py"`
        excluding `notes_repo.py`, `time_entries_repo.py`,
        `notes_service.py`, `time_entry_service.py`, and `tests/` — every
        remaining instantiation must be read-only (get/list/update),
        never followed by `.create(`.

  **Merge & deploy:** merge `feature/write-path-convergence` to `dev`
  (no-ff); restart daemon; confirm `ActiveEnterTimestamp` postdates the
  merge commit; PR `dev` → `main`; tag `v1.27.0`; push tags; create the
  GitHub Release object; verify with `gh release view v1.27.0`.

- **Human approval checkpoint:** Ray confirms all ACs, including every
  live-verification item above, before the item is reported complete.

## Acceptance Criteria

Live verification required for AC3, AC4, AC5, AC6, AC8, AC11, AC12 —
passing tests alone do not check these boxes (standing project rule).

- [ ] AC1 — Zero direct `NotesRepository.create()` callers remain outside
      `notes_service.py`/`time_entry_service.py` across all twelve H3
      surfaces. Verified per Gate 7's corrected two-part audit (6a/6b),
      not a single naive grep pattern.
- [ ] AC2 — Zero direct `TimeEntriesRepository.create()` callers remain
      outside `notes_service.py`/`time_entry_service.py`. Same audit method.
- [ ] AC3 — A CF-tagged note created on any CF-capable surface (#1, #3,
      #5, #6, #7, #10, and now #2, #8, #12 via the new tag prompts)
      produces an active TaskStatus row. Live-verified via `notes log -m`,
      `time add`, and Slack.
- [ ] AC4 — #2, #8, and #12 carry real, content-accurate, caller-specified
      tags in place of their former hard-coded literals. Live-verified.
- [ ] AC5 — #4/#9's condensed-summary tag reflects the actual composition
      of the notes it condensed (Design Rule 8's classification), not an
      unconditional `['both']`. Live-verified against a real mixed-tag
      meeting.
- [ ] AC6 — #7's `source` defaults to `'meeting'` on the additional-note
      path (was silently `'ad-hoc'`). Live-verified.
- [ ] AC7 — CF tag transitions (add and remove) are handled via
      `notes_service.update_note()`; the CLI-layer duplicate
      `ensure_active`/`set_dismissed_by_tag_removal` calls are removed
      from `notes.py`.
- [ ] AC8 — `client_id` is stamped (active client) consistently on every
      paired-write surface, including Clockify import. Live-verified: a
      real Clockify sync produces non-NULL `client_id` matching the
      active client at sync time.
- [ ] AC9 — CLAUDE.md contract added documenting the converged write-path
      family and hook placement.
- [ ] AC10 — Full regression suite passes: confirmed live baseline
      (Gate 1 pre-work) + all new tests from Gates 1–6, zero regressions.
- [ ] AC11 — Daemon restarted after the `dev` merge; `ActiveEnterTimestamp`
      postdates the merge commit.
- [ ] AC12 — `v1.27.0` tag pushed AND the GitHub Release object created
      and verified (`gh release view v1.27.0`).

## Test Plan

Summarized per gate above. Exact-input-critical cases, restated for
visibility:

- `test_create_note_backdates_created_at` — `created_at=datetime(2026, 7, 1, 9, 0)`
  exactly; asserts the stored value equals it, not "now" — proves the
  parameter is forwarded, not silently dropped.
- `test_create_paired_time_entry_derives_client_id_from_note` — the note's
  `client_id` must differ from whatever `active_client_id` would resolve
  to at call time, or the test cannot distinguish "derived from note" from
  "independently resolved and happened to match."
- `test_compute_condensed_tags_single_both_tagged_source` — must use a
  source set whose ONLY tag present is `both` (no separate `internal-only`
  or `client-report`), or the test cannot isolate the B1 defect from the
  mixed-source conservative-collapse rule.
- `test_compute_condensed_tags_empty_set_returns_info_only` — must call
  the classifier with an actual empty list (`[]`), matching what
  `condense_meeting()`'s own query produces for an all-info-only meeting
  — not a list containing `info-only`-tagged notes, which the classifier
  never actually receives (Opus review round 2: the query filters those
  out upstream, before the classifier runs).
- `test_clockify_import_created_at_not_backdated` — must assert `created_at`
  is close to "now" at test run time and explicitly *not* equal to
  `entry_date`'s midnight, or a coincidental same-day sync could pass for
  the wrong reason.
- `test_clockify_import_skips_prompt_when_noninteractive` — must call
  through `pull_entries(interactive=False)`, not just unit-test the
  tag-resolution helper in isolation, or it doesn't actually prove the
  threading (Design Rule 15) works end-to-end.

## Backlog Item Update (for `FEATURE_BACKLOG.md`, verbatim on approval)

```
#### Item 69 — Note Write-Path Convergence — Service-Layer Unification + Canonical CF Hook
**Status:** Open — In Progress
**Priority:** High
**Effort:** ~14–20 hrs
**Added:** 20260725 (scope/shape locked 20260727; spec drafted 20260728;
Opus review rounds 1–2 applied 20260728)
**Target Phase:** Standalone feature (v1.27.0), precedes Task_Match_Data_Integrity Sprint
**Description:** Converges all twelve note-write surfaces onto three
service-layer functions (create_note, create_time_entry,
create_paired_time_entry) plus two internal CF-hook helpers, eliminating
every direct repo-write bypass. Relocates the CF->TaskStatus hook from
the notes.py CLI layer into the service layer (create and tag-transition
paths, via a single general update_note()). Fixes: #2/#8/#12's hard-coded
tags become real, caller-specified tags; #4/#9's condensed-summary tag
reflects actual source-note composition (mixed internal+client-facing
sources conservatively collapse to internal-only; all-info-only sources
resolve to info-only) instead of unconditional ['both']; #7's
silently-'ad-hoc' source now defaults to 'meeting'; client_id NULL on
five surfaces (#5,#7,#8,#9,#12) now auto-resolves consistently, including
Clockify import, which also gains an interactive per-entry tag prompt
(skipped when the pull is non-interactive).
**Acceptance Criteria:** See spec `FEATURE_ITEM69_WRITE_PATH_CONVERGENCE_SPEC_v1_2.md`.
**Files Affected:** `workmain/services/notes_service.py`,
`workmain/services/time_entry_service.py`,
`workmain/cli/commands/notes.py`, `workmain/cli/commands/time.py`,
`workmain/cli/commands/meetings.py`,
`workmain/integrations/clockify/sync.py`, `workmain/ai/note_condenser.py`,
`CLAUDE.md`, `__version__.py`, `CHANGELOG.md`, tests
```

---

*Ready for Role 3 (Claude Code / Sonnet) implementation. Paste this
document — not the planning-chat review history — as the opening message
of a fresh Claude Code / Sonnet session. Session discipline: One Gate only
per session; handoff at every gate boundary to carry forward to new session.
Design questions stop and surface to Role 1 — never resolved in-flow.*
