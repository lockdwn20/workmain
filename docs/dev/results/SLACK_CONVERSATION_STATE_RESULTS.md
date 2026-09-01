# Slack Conversation State — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20260901
**Spec:** `../specs/SLACK_CONVERSATION_STATE_SPEC.md`
**Released as:** v1.31.0 (tag v1.31.0)

---

## 1. Summary

Complete. One module, `workmain/daemon/conversation_state.py`, now owns every piece of Slack DM conversational state: pending confirmation actions (`PendingAction`) and in-progress T5 EOD sessions (`SlackEodSession`, moved here verbatim from `slack_eod.py`). `ConversationStore` holds both record types in memory under one `RLock`, mirrors the whole state to one file (`conversation_state.json`) on every mutation via a new atomic writer, and reads that file once at daemon start — pruning both TTLs and unlinking the legacy `eod_session.json`.

The double-execution defect (#101 F1) is closed on both surfaces: the block-action path no longer parses an action out of the Slack payload — the button value is an opaque correlation id, and `take_pending()` is the single function that consumes a pending record, called by the text path, the approve branch and the reject branch. `SlackEodSession.pending_action`'s unguarded read-modify-write (F13) is closed the same way, via `set_session_pending()` / `take_session_pending()` holding the lock. All four daemon state files are now written atomically. `_pending` is gone from `daemon.py`; nothing reaches into a manager session dict; T4 suppression asks `has_any_session()`.

No database access was added. No authorization points. The branch ends with the standard `feature/*` daemon restart.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `state_io.write_json_atomic(path, payload, mode=0o600)` — temp sibling, flush, fsync, chmod, `os.replace`; owns parent-dir creation. `write_last_inspection()`, `_write_scheduled_jobs()`, `AcknowledgmentStore._save()` adopt it; their caller-side mkdirs removed. | `workmain/daemon/state_io.py`, `workmain/daemon/daemon.py`, `workmain/daemon/acknowledgment.py`, `tests/test_orchestration.py` | +1 |
| 2 | New `workmain/daemon/conversation_state.py`: `PENDING_ACTION_TTL` (15 min), `EOD_SESSION_TTL` (24 h), `PendingAction`, `SlackEodSession` (moved; `save`/`load`/`clear`/`_SESSION_PATH` → `to_dict()`/`from_dict()`, `from_dict()` rebuilds `steps` through a deferred `get_step_sequence` import), `ConversationStore` (full API per spec step 2). `load()` enforces both TTLs, writes the pruned state back, unlinks legacy `eod_session.json` with an INFO log. `slack_eod.py` imports `SlackEodSession` from the new home and re-exports it. | `workmain/daemon/conversation_state.py`, `workmain/integrations/slack/slack_eod.py` | (see step 6) |
| 3 | `SlackEodManager` takes the store, loses `_sessions`; adds `has_any_session()` / `discard_session()`. `_run_step_async()` saves before `thread.start()`. Every `session.save()` and the bare insert at `slack_eod.py:197` become `store.save_session()` (upsert). Both `clear()`+`del` pairs become `store.discard_session()`. `handle_start_eod()` drops any pending action (DR10). `_handle_inline_correction()` → `store.set_session_pending()`; `handle_reply()`'s read-modify-write → `store.take_session_pending()`. | `workmain/integrations/slack/slack_eod.py` | (see step 6) |
| 4 | `format_blocks(action, action_id)` — the id replaces the serialized action on Approve and the literal `"reject"` on Reject. `import json` removed (now unused). | `workmain/orchestration/confirmation_gate.py` | (see step 6) |
| 5 | `daemon.py`: `_pending` deleted; store built in `__init__`, `load()`ed in `start()` before the manager, passed to it; `_operator_user_id` cached. `handle_message()` uses `take_pending(user_id)`. `handle_block_action()` resolves the actor (`payload['user']['id']` → cached operator id), calls `take_pending(user_id, value)` on **both** the approve and reject branches, refuses with a message on `None`, and calls the existing `_execute_action()` — its duplicated executor block deleted. `_execute_action()` adopts `result.message or 'Action completed.'`. `_maybe_offer_eod_resume()` → `restored_sessions()`; past-the-end branch and `handle_reply` error branch → `discard_session()`. `scheduler._send_t4_checkin()` → `has_any_session()`. | `workmain/daemon/daemon.py`, `workmain/daemon/scheduler.py` | (see step 6) |
| 6 | T5-persistence group and `SlackEodManager` test helpers rewritten against `ConversationStore`; `format_blocks()` callers and T4 mocks updated; `test_format_blocks_action_serialized_in_value` rewritten to assert the opaque id. New coverage: store round-trip/corrupt/TTL/legacy-unlink, both double-execution orderings, two-thread `take_pending()` and `take_session_pending()` races, mismatched-id, actor resolution, DR10, reject path (matching + stale), resume-on-restart, inline-pending persistence (both sides), async-dispatch save window, empty-message fallback. `docs/SLACK_SETUP.md` state-file row. | `tests/test_orchestration.py`, `tests/test_eod_workflow.py`, `docs/SLACK_SETUP.md` | +18 (net over steps 2–6) |

Steps 2 and 3 landed in one commit (`ba413bc`): both edit `slack_eod.py`, and the manager cannot compile against a half-moved `SlackEodSession`. Reverting 6→5→4→2 in order still works.

## 3. Acceptance criteria

Baseline suite: 953. Final suite: **972 passed, 0 failed**. All new test names below are in `tests/test_orchestration.py` unless noted.

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met (intent) | `grep -n 'self\._pending' workmain/daemon/daemon.py` → zero hits; the daemon-level dict is gone. The spec's literal grep (`'_pending'`, zero hits) is stale — it predates the store's spec-mandated `take_pending()`/`put_pending()` API, which daemon.py necessarily calls (4 hits). See Deviation 3. |
| AC1.2 | Met | `grep -rn 'eod_session.json' workmain/` → two hits, both the legacy-cleanup constant/docstring in `conversation_state.py` |
| AC2.1 | Met | `pytest -k test_block_approve_then_yes_executes_once` — `_execute_action` called once; `yes` falls through to `_dispatch_message` |
| AC2.2 | Met | `pytest -k test_yes_then_block_approve_executes_once` — executes once; the later click is refused with "no longer active" |
| AC3.1 | Met (intent) | `grep -n 'take_pending' workmain/daemon/daemon.py` → three call sites (text `:427`, approve `:459`, reject `:466`). Second grep (`del self\._pending\|_pending.pop`, zero hits) is stale: `take_pending()` in `conversation_state.py` *is* the one clearing function DR4 mandates, and it deletes from its own dict. See Deviation 3. |
| AC4.1 | Met | `grep -rn '_eod_manager\._sessions' workmain/ tests/` → zero hits |
| AC4.2 | Met | `grep -n 'self\._sessions' workmain/integrations/slack/slack_eod.py` → zero hits (one stale comment reference fixed during implementation) |
| AC5.1 | Met | `pytest -k test_expired_pending_not_executed` — a record past `PENDING_ACTION_TTL` is dropped and `take_pending()` returns `None`; fall-through-to-fresh-parse is exercised by `test_block_approve_then_yes_executes_once` |
| AC5.2 | Met | `grep -rn 'PENDING_ACTION_TTL' workmain/` → one assignment (`conversation_state.py:33`) plus uses |
| AC6.1 | Met | `pytest -k test_eod_error_leaves_no_resumable_state` — drives the `handle_reply` error branch, then a fresh `ConversationStore.load()` restores no session |
| AC7.1 | Met | `pytest` → 972 passed (≥ 953) |
| AC8.1 | Met | `grep -rn 'class PendingAction\|class SlackEodSession\|class ConversationStore' workmain/` → one each, all in `conversation_state.py` |
| AC8.2 | Met | `grep -rn 'SlackEodSession\.' workmain/daemon/daemon.py` → zero; `grep -n 'def save\|def load\|def clear\|_SESSION_PATH' workmain/integrations/slack/slack_eod.py` → zero |
| AC9.1 | Met | `grep -n 'json.dumps(action)' workmain/orchestration/confirmation_gate.py` → zero |
| AC9.2 | Met | `pytest -k test_long_action_button_value_under_slack_cap` — a 4000-char note yields button values of 32 chars |
| AC10.1 | Met | `grep -rn 'write_text' workmain/daemon/ workmain/integrations/slack/slack_eod.py` → zero |
| AC10.2 | Met | `pytest -k test_write_json_atomic` — replaces (not appends), mode 600, no `.tmp` sibling, creates parent dir |
| AC11.1 | Met | `pytest -k test_concurrent_take_pending_returns_one_winner` — two barrier-synced threads, exactly one non-`None` |
| AC11.2 | Met | `pytest -k "test_store_round_trip or test_store_load_corrupt_file"` |
| AC11.3 | Met | `pytest -k test_mismatched_action_id_leaves_record` |
| AC11.4 | Met | `pytest -k test_legacy_session_file_removed_on_load` |
| AC12.1 | Met | `pytest -k test_actor_resolution` — payload with `user.id` uses it; payload without falls back to the cached operator id |
| AC13.1 | Met | `pytest -k test_t4_suppressed_during_active_t5_session`; `grep -n 'has_any_session' workmain/daemon/scheduler.py` → one hit |
| AC14.1 | Met | `pytest -k test_start_eod_discards_pending_action` |
| AC15.1 | Met | `pytest -k test_block_reject_clears_pending` — after a matching Reject, a following `yes` executes nothing |
| AC15.2 | Met | `pytest -k test_stale_reject_does_not_clear_current_pending` — a stale-id Reject refuses and leaves the live record intact |
| AC16.1 | Met | `pytest -k test_resume_offer_from_restored_session` — offered from `restored_sessions()` without the daemon knowing the `user_id` |
| AC16.2 | Met | `pytest -k test_stale_session_not_restored` — a session older than `EOD_SESSION_TTL` is neither restored nor offered |
| AC17.1 | Met | `pytest -k test_cleared_inline_pending_not_resurrected` — the clear is persisted; a fresh `load()` shows `pending_action is None` |
| AC17.2 | Met | `pytest -k test_set_inline_pending_persisted` |
| AC17.3 | Met | `pytest -k test_start_eod_persists_session_on_insert` — a fresh `load()` finds the session before any step runs |
| AC17.4 | Met | `pytest -k test_concurrent_take_session_pending_returns_one_winner` — two threads, exactly one winner |
| AC17.5 | Met | `grep -rn 'pending_action =' workmain/integrations/slack/ workmain/daemon/daemon.py` → zero |
| AC17.6 | Met | `pytest -k test_async_dispatch_persists_before_thread_start` — `save` recorded before `Thread.start()` |
| AC18.1 | Met | `pytest -k test_empty_result_message_posts_fallback` — an empty `ActionResult.message` posts `'Action completed.'`; both surfaces route through `_execute_action()` |

Nothing unmet. No AC carried to the backlog.

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | `SlackEodManager.__init__` gains a required `store` parameter; `format_blocks()` gains a required `action_id`. Both are signature changes the spec describes but does not spell as "required". | The store and the id have no meaningful default; every call site is updated in the same steps. | Spec steps 3, 4 |
| 2 | `#102` AC3 (opaque button value) and AC4 (button value under Slack's 2000-char cap) are delivered here, ahead of `#102`. | Spec Decision Log 20260831 (Ray) / spec AC9. Edit `#102`'s ACs at close-out. | Ray |
| 3 | AC1.1 and AC3.1's second grep are stale mechanical checks: they were written against the pre-move daemon-level `self._pending` dict and are contradicted by the store's spec-mandated `take_pending()`/`put_pending()` API. The **intent** of both is met (no daemon-level pending dict; one function clears pending). The spec-named methods were **not** renamed to satisfy the greps. | Precedent: a stale verification check is check drift, not a design question — document and proceed (`feedback_spec_test_file_drift`). Reword the ACs at close-out / on the issue if desired. | Anvil — flagged to Ray, pending his call on the AC wording |
| 4 | `_execute_action()` (the text path) now posts `result.message or 'Action completed.'` instead of the bare `result.message`. | Spec F8 / step 5 / AC18.1 — an empty message must never post an empty DM; the block path already had this fallback and the two paths converged on one executor. | Spec (Caliper F8) |
| 5 | `test_format_blocks_action_serialized_in_value` renamed to `test_format_blocks_opaque_id_in_both_values` and rewritten to assert the opaque id. | Spec §6 — that test asserted the defect this spec removes. | Spec §6 |
| 6 | Steps 2 and 3 committed together (`ba413bc`). | Both edit `slack_eod.py`; the manager cannot compile against a half-moved `SlackEodSession`. Reverting in reverse step order still works. | Anvil |
| 7 | ~19 net new tests, not the spec §6 estimate of ~40. | Every §6 coverage bullet has a named AC test; the estimate was high. Suite 953 → 972. | Anvil |

## 5. Verification

- **Test suite:** 972 passed, 0 failed (baseline 953). Clean working tree on `feature/issue-101-slack-conversation-state`.
- **Live verification:** not yet performed — no running daemon exercised. To confirm post-merge: (a) start the daemon with no `conversation_state.json` and an in-flight `eod_session.json` present → legacy file is unlinked with an INFO log, no session offered; (b) parse an intent, click Approve, then type `yes` → action executes once, second input falls through to a fresh parse; (c) start an EOD session, restart the daemon mid-session → "Welcome back" resume offer.
- **Daemon restart** (`feature/*`, `docs/DEVELOPMENT_STANDARDS.md` §2.6): required after the `dev` merge — confirm `ActiveEnterTimestamp` of `workmain-notify.service` postdates the merge commit. Carried by the issue's closing comment, not this file.
  - A merge is not a deployment.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #102 | Edit AC3 / AC4 to record that the opaque button value and the <2000-char cap shipped early with #101. | Issue-edit at close-out, per spec Decision Log. |
| #101 | Add the equivalent AC for "one module owns both record types, reached only through it" (spec AC8) and restate AC5 as "a stated TTL" (spec AC5.1); consider rewording AC1.1 / AC3.1's stale greps (Deviation 3). | Issue-edit at close-out, per spec §5 preamble. |
| — | Provider `timeout_seconds`, step-level deadline, EOD child-command approvals (#114, #115, #117) and the `session_scope()` / pool work (#95–#97) remain out of scope; this spec added no `get_session()` call site. | Explicitly out of scope (spec §1). |
