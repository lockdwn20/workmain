# Slack Conversation State — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20260901
**Branch:** `feature/issue-101-slack-conversation-state` (from `dev`)
**Target release:** v1.31.0
**Originating item:** Issue #101, child of #99, milestone 7 *Slack Intent Contract*
**Design study:** `../design/DESIGN_SLACK_CONVERSATION_STATE.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260831 | Ray | Q1 — the single store persists to a JSON file, not a `system_state` row | Accepted. Rationale and rejected options: design study §4 Q1, answered at §5 Q1 |
| 20260831 | Ray | `write_json_atomic()` belongs in `state_io.py`, and the two pre-existing state files adopt it | Accepted — closes design study F8 for all three files, not only the new one. Step 1 |
| 20260831 | Ray | Q2 — a button click correlates to its pending record by uuid, not by comparing payloads | Accepted. Design study §4 Q2, answered at §5 Q2 |
| 20260831 | Ray | This delivers #102's AC3 and AC4 ahead of #102 | Accepted deliberately. Recorded as AC9 below, to be entered in the results artifact's deviations table and #102's ACs edited at close-out |
| 20260831 | Ray | Q3 — the pending TTL is a module constant, not a `system_state` key | Accepted. Design study §4 Q3, answered at §5 Q3 |
| 20260831 | Ray | Issue #101's ACs are all satisfiable with two stores intact — moving `_pending` into `SlackEodManager` beside `_sessions` turns every one of them green | Accepted as AC8 below. Add the equivalent AC to the issue at close-out. Design study §5 Q4 |
| 20260831 | Ray | Issue #101 AC5's "a configured TTL" prejudges Q3 | Accepted. Restated as "a stated TTL" in AC5.1. Edit the issue's AC at close-out. Design study §5 Q5 |
| 20260901 | Spanner | `SlackEodSession` must move modules, which issue #101 does not name | Required rather than chosen: the store persists both record types, so co-locating the record with the store is what makes AC8 true without a lazy import between the two modules. Stated in §1 |
| 20260901 | Spanner | Design study §5 Q6 — whether `SlackEodSession.pending_action` is in scope as a third pending store — is open | Spanner's position is no, recorded in §1 out of scope with its reasoning. Ray to confirm or overturn before approval |

---

## 1. Scope

**In scope:**

- New module `workmain/daemon/conversation_state.py` — `PendingAction`, `SlackEodSession` (moved, not rewritten), and `ConversationStore`, which owns both in memory and persists both to one file.
- `workmain/daemon/state_io.py` — new `write_json_atomic()`; `write_last_inspection()` and `_write_scheduled_jobs()` (currently in `daemon.py`) adopt it.
- `workmain/daemon/daemon.py` — `_pending` removed; the store is owned, loaded at start and reached through one clearing function on both the text and block-action paths; the duplicated executor block in `handle_block_action` collapses into the existing `_execute_action()`; the three ad-hoc EOD-session cleanups converge on one call.
- `workmain/integrations/slack/slack_eod.py` — `SlackEodManager` loses `_sessions` and takes the store; `SlackEodSession` loses `save()`/`load()`/`clear()`/`_SESSION_PATH`.
- `workmain/daemon/scheduler.py` — `_send_t4_checkin()`'s reach into `_eod_manager._sessions`.
- `workmain/orchestration/confirmation_gate.py` — `format_blocks()` takes an action id and puts it in the button value instead of the serialized action.
- `docs/SLACK_SETUP.md` — the state-file table row.

**Out of scope:**

- **`SlackEodSession.pending_action`** stays as it is. It is a third pending mechanism, but it rides inside the session record, so it lands in the one store automatically once sessions do. Neither failure mode in this issue applies to it: it never posts buttons (so no block-action path can double-execute it), and it is set and consumed inside the same `handle_reply()` that owns the session. Unifying it with `PendingAction` would give it a TTL and a uuid it has no use for. Named here so it is not mistaken for an oversight.
- The action vocabulary, its validation, and the typed contract — #100.
- Confirmation-word matching (`is_confirmation`/`is_rejection` stay exact-match frozensets) — #102.
- Task targeting and fuzzy matching — #103.
- `session_scope()` adoption, repository commit boundaries, and the connection pool — #95, #96, #97. This spec deliberately introduces no new `get_session()` call site.
- `last_inspection.json` and `scheduled_jobs.json` keep their own files, schemas and readers. They adopt the atomic writer and nothing else.

## 2. Verified current state

Verified against source on 20260831 on `main` at `e589f9d`. This table carries the claims the steps below depend on; the full census, including the findings that only bore on rejected options, is the design study's §3.

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| Pending actions are an in-memory dict on the daemon, with no expiry and no persistence | `workmain/daemon/daemon.py:327`, `self._pending: dict = {}` |
| The text path pops pending before deciding confirm, reject or fall-through | `daemon.py:423-424`, `handle_message()` |
| The block-action path executes from the button value and never touches `_pending` | `daemon.py:436-471`, `handle_block_action()` — `json.loads(action['value'])` at `:446`, `ActionExecutor(session).execute(action_dict)` at `:455` |
| The block-action path duplicates `_execute_action()`'s body, differing only in posting `result.message or 'Action completed.'` instead of `result.message` | `daemon.py:451-464` against `_execute_action()` at `daemon.py:507-522` |
| The button value is the serialized action | `workmain/orchestration/confirmation_gate.py:124`, `"value": json.dumps(action)` |
| `format_blocks()` has exactly one production caller | `daemon.py:503` |
| The EOD error branch pops the in-memory session without clearing the file | `daemon.py:419`, `self._eod_manager._sessions.pop(user_id, None)` |
| Resume restore and the past-the-end branch each do their own bookkeeping across both stores | `daemon.py:568`; `daemon.py:587-588` |
| `_advance_step()` and `_abort_session()` each pair `SlackEodSession.clear()` with `del self._sessions[...]` by hand | `slack_eod.py:346-348` and `slack_eod.py:571-582` |
| The T4 suppression check iterates the manager's private dict | `workmain/daemon/scheduler.py:346-347` |
| The session holds a live `Thread` and `Event` that are never persisted, and `_abort_session()` depends on that `Event`'s identity | `slack_eod.py:71-75` (`compare=False, repr=False`); `slack_eod.py:569-570` |
| Session staleness is an inline 24-hour literal, not a named constant | `slack_eod.py:109`, `timedelta(hours=24)` |
| No daemon state file is written atomically; three files, three bare writers, one chmod | `state_io.py:14` `daemon_state_path()`; `state_io.py:33` `write_text`; `daemon.py:107` `write_text`; `slack_eod.py:98-99` `write_text` + `chmod(0o600)` |
| Nothing outside `slack_eod.py` names the session file; one document does | `grep -rn 'eod_session' workmain/` returns one hit, `slack_eod.py:81`; `docs/SLACK_SETUP.md:215` |
| Inbound events are dispatched one unbounded thread per event, so two handlers can run at once | `socket_client.py:126-131`, `:137-142` |
| The `block_actions` payload carries the acting user at `payload['user']['id']` — **asserted from the Slack API contract, not verified against this tree** | design study F19; `daemon.py:436-471`; `tests/test_orchestration.py:72-82` |

## 3. Design rules

- **DR1 — One module owns conversational state.** `workmain/daemon/conversation_state.py` defines every record type and the only store. `daemon.py` and `slack_eod.py` hold a reference to the store and reach state through its methods; neither keeps a dict of its own, and neither touches the other's state directly.
- **DR2 — Memory is authoritative, the file is a mirror.** The store holds live objects, because `SlackEodSession._cancel_event` and `._step_thread` cannot be serialized and `_abort_session()` depends on their identity. Every mutating method writes the whole file through before returning. The file is read exactly once, at daemon start.
- **DR3 — Every mutation happens under one `threading.RLock` held by the store.** Inbound events arrive one thread per event and long-running EOD steps continue on their own thread, so read-decide-write must not be split across the lock. `take_pending()` in particular is one atomic pop.
- **DR4 — `take_pending()` is the only function that clears a pending action.** The text path, the approve path and the reject path all call it. Nothing else removes a pending record.
- **DR5 — A pending record is returned once or never.** `take_pending(user_id, action_id)` returns the record only if it exists, has not outlived `PENDING_ACTION_TTL`, and its id matches the one supplied. A mismatched id leaves the record in place — a stale button click must not destroy the current offer. An expired record is removed and `None` is returned.
- **DR6 — The store, not the client, supplies the action that gets executed.** The button value is an opaque correlation token. No execution path parses an action out of a Slack payload.
- **DR7 — Discarding an EOD session is one call.** `discard_session(user_id)` removes it from memory and from the file together. No caller pairs those two operations by hand.
- **DR8 — Every daemon state file is written atomically.** `state_io.write_json_atomic()` writes a sibling temp file, flushes, fsyncs, sets the mode, then `os.replace()`s it into place. No `write_text()` call remains for a state file.
- **DR9 — This spec adds no database access.** Offering, expiring, correlating and clearing a pending action touch no session and no repository.

An implementer hitting anything these rules do not cover stops at the current step and reports it — `CLAUDE.md` Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `write_json_atomic(path, payload, mode=0o600)` in `state_io.py` — temp sibling, flush, fsync, chmod, `os.replace`. `write_last_inspection()` and `_write_scheduled_jobs()` adopt it. Both files become mode 600, which the 700 state directory already implies. | `workmain/daemon/state_io.py`, `workmain/daemon/daemon.py`, `tests/test_orchestration.py` |
| 2 | New `workmain/daemon/conversation_state.py`: `PENDING_ACTION_TTL = timedelta(minutes=15)`, `EOD_SESSION_TTL = timedelta(hours=24)` (the inline literal, named), `PendingAction`, `SlackEodSession` moved verbatim except that `save`/`load`/`clear`/`_SESSION_PATH` become `to_dict()`/`from_dict()`, and `ConversationStore`. Store API: `load()`, `put_pending()`, `take_pending()`, `get_session()`, `has_session()`, `has_any_session()`, `save_session()`, `discard_session()`. One file, `conversation_state.json`, written via DR8. `load()` unlinks a legacy `eod_session.json` with an INFO log. `slack_eod.py` imports `SlackEodSession` from its new home. | `workmain/daemon/conversation_state.py`, `workmain/integrations/slack/slack_eod.py` |
| 3 | `SlackEodManager` takes the store in its constructor and loses `_sessions`. `has_session()` delegates; `has_any_session()` and `discard_session()` added. Every `session.save()` becomes `store.save_session(session)`; both `SlackEodSession.clear()` + `del self._sessions[...]` pairs become `store.discard_session(user_id)`. | `workmain/integrations/slack/slack_eod.py` |
| 4 | `format_blocks(action, action_id)` puts the id in both button values. `daemon.py`: `_pending` deleted; store constructed in `__init__`, `load()`ed in `start()` before the manager is built, passed to it; `_operator_user_id` cached in `start()`. `handle_message()` uses `take_pending(user_id)`. `handle_block_action()` resolves the actor (`payload['user']['id']`, falling back to the cached operator id), calls `take_pending(user_id, value)`, refuses with a message when it gets `None`, and otherwise calls the existing `_execute_action()` — deleting its duplicated executor block. The three EOD cleanups call `discard_session()`. `scheduler._send_t4_checkin()` calls `has_any_session()`. | `workmain/orchestration/confirmation_gate.py`, `workmain/daemon/daemon.py`, `workmain/daemon/scheduler.py` |
| 5 | Tests per §6, and the `docs/SLACK_SETUP.md:215` file-table row. | `tests/test_orchestration.py`, `tests/test_eod_workflow.py`, `docs/SLACK_SETUP.md` |

### Authorization points

**None.** No migration, no GitHub object deleted, no force-push, no merge to `main` within these steps. The branch is `feature/*`, so it ends with a daemon restart per `docs/DEVELOPMENT_STANDARDS.md` — that restart is the post-merge carve-out, not an authorization point. The dev→main PR at close-out is opened, not merged.

## 5. Acceptance criteria

AC1–AC7 map to issue #101's ACs in order. AC5 restates the issue's wording per the Decision Log. AC8 is new and has no counterpart in the issue yet. Edit both at close-out.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | One store holds pending actions and EOD sessions | `grep -n '_pending' workmain/daemon/daemon.py` returns zero hits |
| AC1.2 | One file holds both | `grep -rn 'eod_session.json' workmain/` returns zero hits outside the legacy-cleanup line in `conversation_state.py` |
| AC2.1 | Approve then an affirmative text executes exactly once | `pytest tests/test_orchestration.py -k test_block_approve_then_yes_executes_once` — asserts `ActionExecutor.execute` called once |
| AC2.2 | An affirmative text then Approve executes exactly once, and the click is refused | `pytest tests/test_orchestration.py -k test_yes_then_block_approve_executes_once` |
| AC3.1 | One function clears pending, called by the text path and the block-action path | `grep -n 'take_pending' workmain/daemon/daemon.py` returns three call sites (text, approve, reject); `grep -rn 'del self\._pending\|_pending.pop' workmain/` returns zero hits |
| AC4.1 | Nothing reaches into the manager's session dict | `grep -rn '_eod_manager\._sessions' workmain/ tests/` returns zero hits |
| AC4.2 | The manager keeps no session dict of its own | `grep -n 'self\._sessions' workmain/integrations/slack/slack_eod.py` returns zero hits |
| AC5.1 | A pending action older than the **stated** TTL is not executed | `pytest tests/test_orchestration.py -k test_expired_pending_not_executed` |
| AC5.2 | The TTL is stated in one place | `grep -rn 'PENDING_ACTION_TTL' workmain/` returns one definition |
| AC6.1 | A session discarded on error leaves nothing resumable on disk | `pytest tests/test_orchestration.py -k test_eod_error_leaves_no_resumable_state` — drives the `handle_reply` error branch, then asserts a fresh `ConversationStore.load()` restores no session |
| AC7.1 | Suite at or above baseline | `pytest` — 953 or higher |
| AC8.1 | One module owns both record types and the store | `grep -rn 'class PendingAction\|class SlackEodSession\|class ConversationStore' workmain/` returns one definition each, all in `conversation_state.py` |
| AC8.2 | Both surfaces reach conversational state only through the store | `grep -rn 'SlackEodSession(' workmain/daemon/daemon.py` returns zero hits; `grep -n 'def save\|def load\|def clear\|_SESSION_PATH' workmain/integrations/slack/slack_eod.py` returns zero hits |
| AC9.1 | The button value is an opaque id, not the action (delivers #102 AC3 early) | `grep -n 'json.dumps(action)' workmain/orchestration/confirmation_gate.py` returns zero hits |
| AC9.2 | A 4000-character note produces a button value under 2000 characters (delivers #102 AC4 early) | `pytest tests/test_orchestration.py -k test_long_action_button_value_under_slack_cap` |
| AC10.1 | Every daemon state file is written atomically | `grep -rn 'write_text' workmain/daemon/ workmain/integrations/slack/slack_eod.py` returns zero hits |

## 6. Test plan

- **Baseline before this work:** 953 passed, 0 failed — `CHANGELOG.md` [1.30.0].
- **Expected after:** 953 + ~22 = ~975 passed.

`tests/test_orchestration.py` is the established home for daemon dispatch, Block Kit and T5 persistence coverage and takes the bulk of this. Its `TestT5SessionPersistence` group currently patches `SlackEodSession._SESSION_PATH`; that attribute is gone, so the group's setUp switches to pointing a `ConversationStore` at a temp directory. `_make_daemon()` loses `daemon._pending` and gains a store. `test_format_blocks_action_serialized_in_value` asserts the defect this spec removes and is rewritten to assert the opaque id — record it in the results artifact's deviations table with the two #102 ACs.

New coverage:

- **Store unit tests** — put/take round-trip; take returns `None` on an unknown user, an expired record, and a mismatched id; a mismatched id leaves the record in place; write-through survives a fresh `load()`; a corrupt file loads as empty state rather than raising; a legacy `eod_session.json` is unlinked at load; concurrent `take_pending()` from two threads returns the record to exactly one caller.
- **Double-execution** — AC2.1 and AC2.2, both orderings.
- **TTL** — AC5.1, plus an expired pending falling through to a fresh intent parse rather than executing.
- **Session lifecycle** — the `handle_reply` error branch, `_abort_session()` and the past-the-end resume branch each leave no resumable state; `discard_session()` is the only path that does it.
- **Actor resolution** — a payload carrying `user.id` uses it; a payload without one falls back to the cached operator id.
- **Atomic write** — `write_json_atomic()` leaves no `.tmp` sibling behind, sets mode 600, and replaces existing content rather than appending.
- **T4** — `has_any_session()` suppresses the check-in; the existing tests that set `daemon._eod_manager._sessions` directly are rewritten against the public method.

All Slack and Ollama calls stay mocked; no test touches the real state directory.

## 7. Risks and rollback

- **An in-flight EOD session does not survive the upgrade.** The new store reads `conversation_state.json`, which will not exist on first start; the legacy `eod_session.json` is unlinked rather than migrated. A session open at restart time is lost and must be restarted with `start eod`. Deliberate: writing a one-shot importer for a file that can only be hours old, for a single operator, costs more than the restart. Restart the daemon outside an EOD session.
- **The block_actions actor field is asserted from the Slack API contract, not verified against this tree** (§2, last row). If `payload['user']['id']` is absent in practice, the fallback to the cached operator id keeps Approve working, because the DM channel is resolved from that same operator id. Both branches are covered by tests.
- **Mode 600 on `last_inspection.json` and `scheduled_jobs.json` is a change.** Both are read only by the same user through `notifications status`, inside a directory already expected at 700. If something unanticipated reads them as another user it will now fail loudly rather than silently.
- **Concurrency is the load-bearing part.** The lock is what makes "exactly one write" true when Approve and "yes" arrive on two threads at once; the test that drives two threads through `take_pending()` is the one that proves it. #97 will later move dispatch to a bounded pool, which does not change the requirement.
- **Rollback:** every step is an independent commit and individually revertible. Reverting steps 2–5 restores `SlackEodSession`'s own persistence; the only residue is a `conversation_state.json` the old code ignores. Step 1 stands alone and is worth keeping either way.
