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
| 20260901 | Ray | AC10.1's grep is wider than §1's scope: `acknowledgment.py:104` is a fourth bare `write_text` on a daemon state file, named in neither §1 nor step 1 | Accepted. Widened §1 and step 1 rather than narrowing the AC — narrowing would have made DR8 false. §2's "three files, three bare writers" was itself wrong and is corrected here and at design study F8 |
| 20260901 | Ray | DR5 read literally makes the text path always fail — a user typing an affirmative supplies no action id, and AC2.2 depends on the comparison being conditional | Accepted. DR5 now states that the id is compared only when one is given |
| 20260901 | Ray | Four of §6's coverage bullets had no AC behind them, including the two-thread `take_pending()` race that §7 itself calls load-bearing; close-out verifies ACs, so that coverage could silently not land | Accepted. Added AC10.2 and AC11–AC14, and every §6 bullet now names its AC |
| 20260901 | Ray | A pending action offered before `start eod` survives the whole session and can still fire afterwards — `_dispatch_message()` sets pending and the `start_eod` branch returns without touching it | Accepted. New DR10, implemented in step 3, verified by AC14.1 |
| 20260901 | Ray | Step 4 bundled about seven distinct changes across three modules and reverted all-or-nothing, against §1.4 | Accepted. The `confirmation_gate.py` change is now step 4 on its own; the daemon and scheduler work is step 5 |
| 20260901 | Ray | DR2 and DR3 together put the fsync inside the lock, which is correct, but nothing said how far the lock may extend | Accepted. DR3 now states the lock is held across a store method and nothing else — never across an Ollama call, a Slack post, or an EOD step |
| 20260901 | Caliper | F1 — AC3.1 requires three `take_pending` call sites but step 5 named two; and the Reject button's value is the literal `"reject"`, not a serialized action, so §2 and step 4 were true of Approve only | Accepted. §2 records both button values, step 4 replaces both, step 5 gives the reject branch its `take_pending` call, verified by AC15.1 |
| 20260901 | Caliper | F2 — `_maybe_offer_eod_resume()` is a restore, not a cleanup, and the step 2 API had no way to obtain a restored session without already knowing its `user_id` | Accepted. `restored_sessions()` added to the API; the resume path is named in step 5 and verified by AC16.1 |
| 20260901 | Caliper | F3 — `EOD_SESSION_TTL` was named in step 2 but no step applied it and no AC checked it, so a week-old session would be restored and offered | Accepted. New DR9a puts both TTLs in `load()`; AC16.2 checks the session one |
| 20260901 | Caliper | F4 — §1's out-of-scope rationale for `pending_action` was asserted and is false: it is persisted and restored, and cleared in memory without a save, so a restart resurrects a consumed action | Accepted. §1 restated, new DR6a requires a save after every session mutation, implemented in step 3 and verified by AC17.1. Kept in this spec rather than raised as a separate hotfix under §1.2: the clear sits in a function step 3 already rewrites, and leaving it would make DR2's mirror false for sessions in our own new code |
| 20260901 | Caliper | F5 — AC8.2's `SlackEodSession(` grep is vacuous; `daemon.py` never constructs one, so the AC was green before any work started | Accepted. Changed to `SlackEodSession\.` |
| 20260901 | Caliper | F6 — §2 understated what cannot be serialized: `steps` holds live `runner` callables, so `from_dict()` needs a `workmain/workflows/` import the spec never named | Accepted. §2 corrected and step 2 states the import is deferred, as `load()` does today, so `workmain/daemon/` gains no module-level edge |
| 20260901 | Caliper | F7 — step 1 did not say whether `write_json_atomic()` creates the parent directory, and the three adopting callers disagree today | Accepted. The writer owns the mkdir; the two caller-side mkdirs come out and `_write_scheduled_jobs()` gains one |
| 20260901 | Caliper | F8 — a behaviour change rode inside "deleting the duplicated executor block": the two paths post different text and nothing decided which survives | Accepted. `_execute_action()` takes the fallback so an empty message can never post an empty DM; AC18.1, and the deviations table at close-out |
| 20260901 | Caliper | F9 — §6's rewrite note was narrower than the breakage; five further test sites break without any grep catching them | Accepted. §6 now lists every site that breaks |
| 20260901 | Caliper | DR3's "read-decide-write must not be split across the lock" is a promise the design deliberately does not keep for sessions | Accepted. Scoped to pending records, with the session case stated as the deliberate exception it is |
| 20260901 | Caliper | R1 — DR6a said "every mutation of session state" while step 3 named one site, so two implementers could both claim conformance | Accepted, and scoped narrower than either option offered: the `pending_action` pair are the only session mutations that reach no save on any path. The control-word branches and `_reprompt_current_step()`'s block fall through into `_advance_step()`, which already persists, so DR6a excludes them and says why. AC17.1 and AC17.2 |
| 20260901 | Caliper | R1b — step 3's "every `session.save()` becomes `save_session()`" does not reach the insertion at `slack_eod.py:197`, which has no save today | Accepted. Step 3 names it, and step 2 states `save_session()` is an upsert so registering and persisting are one call. AC17.3 |
| 20260901 | Caliper | R2 — DR4 ("nothing else removes a pending record") contradicts DR9a's load-time prune | Accepted. DR4 carves out expiry, and distinguishes it from consumption: a pruned record is never returned to a caller |
| 20260901 | Caliper | R3 — the reject branch's unconditional `'Action rejected.'` contradicts DR5: a stale Reject click would report a rejection while the current offer stayed live | Accepted. The reject branch mirrors approve exactly, refusing when no record comes back. AC15.2 |
| 20260901 | Caliper | R4 — §1 carried two stale counts after §2 reclassified `daemon.py:568` as a restore | Accepted. §1 now says two cleanups plus the restore, and both button values |

---

## 1. Scope

**In scope:**

- New module `workmain/daemon/conversation_state.py` — `PendingAction`, `SlackEodSession` (moved, not rewritten), and `ConversationStore`, which owns both in memory and persists both to one file.
- `workmain/daemon/state_io.py` — new `write_json_atomic()`; `write_last_inspection()`, `_write_scheduled_jobs()` (currently in `daemon.py`) and `AcknowledgmentStore._save()` (`workmain/daemon/acknowledgment.py`) adopt it. All four daemon state files, not only the new one — DR8 says every one of them, so naming three would make DR8 false.
- `workmain/daemon/daemon.py` — `_pending` removed; the store is owned, loaded at start and reached through one clearing function on both the text and block-action paths; the duplicated executor block in `handle_block_action` collapses into the existing `_execute_action()`; its two ad-hoc EOD-session cleanups (`:419`, `:587-588`) converge on `discard_session()`, and `_maybe_offer_eod_resume()`'s restore moves onto `restored_sessions()`.
- `workmain/integrations/slack/slack_eod.py` — `SlackEodManager` loses `_sessions` and takes the store; `SlackEodSession` loses `save()`/`load()`/`clear()`/`_SESSION_PATH`.
- `workmain/daemon/scheduler.py` — `_send_t4_checkin()`'s reach into `_eod_manager._sessions`.
- `workmain/orchestration/confirmation_gate.py` — `format_blocks()` takes an action id and puts it in both button values — replacing the serialized action on Approve and the literal `"reject"` on Reject.
- `docs/SLACK_SETUP.md` — the state-file table row.

**Out of scope:**

- **`SlackEodSession.pending_action`** is not merged into `PendingAction`. It rides inside the session record, so it reaches the one store as soon as sessions do, and it never posts buttons, so the block-action double-execution of §2 cannot reach it. Unifying it would give it a uuid and a TTL it has no use for. **It is not, however, untouched:** an earlier draft of this section claimed neither failure mode applied to it, which is false — it is persisted and restored but cleared in memory without a save, so a restart between the clear and the next save resurrects a consumed action. DR6a covers that, and step 3 implements it. Only the merge into `PendingAction` is out of scope.
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
| The Approve button's value is the serialized action; the Reject button's is the literal string `"reject"` | `workmain/orchestration/confirmation_gate.py:124`, `"value": json.dumps(action)`; `:131`, `"value": "reject"` |
| `format_blocks()` has exactly one production caller | `daemon.py:503` |
| The EOD error branch pops the in-memory session without clearing the file | `daemon.py:419`, `self._eod_manager._sessions.pop(user_id, None)` |
| `_maybe_offer_eod_resume()` is a restore, not a cleanup: it calls `SlackEodSession.load()` and assigns straight into the manager's private dict. The past-the-end branch then does its own two-store bookkeeping | `daemon.py:560-573`, `:563`, `:568`; `daemon.py:587-588` |
| `_advance_step()` and `_abort_session()` each pair `SlackEodSession.clear()` with `del self._sessions[...]` by hand | `slack_eod.py:346-348` and `slack_eod.py:571-582` |
| The T4 suppression check iterates the manager's private dict | `workmain/daemon/scheduler.py:346-347` |
| The session holds three things that cannot be serialized: a live `Thread` and `Event`, whose identity `_abort_session()` depends on, and `steps`, whose entries hold a live `runner` callable. `load()` rebuilds `steps` by calling `get_step_sequence()` through a deferred import | `slack_eod.py:71-75` (`compare=False, repr=False`); `slack_eod.py:569-570`; `eod_workflow.py:1412`, `runner = step['runner']`; `slack_eod.py:113`, `:125-128` |
| Session staleness is an inline 24-hour literal, not a named constant | `slack_eod.py:109`, `timedelta(hours=24)` |
| No daemon state file is written atomically; four files under `{WORKMAIN_STATE_DIR}/daemon/`, four bare writers, one chmod | `state_io.py:14` `daemon_state_path()`; `state_io.py:33` `write_text`; `daemon.py:107` `write_text`; `acknowledgment.py:104` `write_text`; `slack_eod.py:98-99` `write_text` + `chmod(0o600)` |
| Nothing outside `slack_eod.py` names the session file; one document does | `grep -rn 'eod_session' workmain/` returns one hit, `slack_eod.py:81`; `docs/SLACK_SETUP.md:215` |
| `SlackEodSession.pending_action` is persisted and restored, but `handle_reply()` clears it in memory with no `save()` — a restart between that clear and the next save resurrects a consumed action | `slack_eod.py:95`, `:123`, `:212` |
| Inbound events are dispatched one unbounded thread per event, so two handlers can run at once | `socket_client.py:126-131`, `:137-142` |
| The `block_actions` payload carries the acting user at `payload['user']['id']` — **asserted from the Slack API contract, not verified against this tree** | design study F19; `daemon.py:436-471`; `tests/test_orchestration.py:72-82` |

## 3. Design rules

- **DR1 — One module owns conversational state.** `workmain/daemon/conversation_state.py` defines every record type and the only store. `daemon.py` and `slack_eod.py` hold a reference to the store and reach state through its methods; neither keeps a dict of its own, and neither touches the other's state directly.
- **DR2 — Memory is authoritative, the file is a mirror.** The store holds live objects, because `SlackEodSession._cancel_event` and `._step_thread` cannot be serialized and `_abort_session()` depends on their identity. Every mutating method writes the whole file through before returning. The file is read exactly once, at daemon start.
- **DR3 — Every mutation happens under one `threading.RLock` held by the store.** Inbound events arrive one thread per event and long-running EOD steps continue on their own thread, so a **pending** record's read-decide-write must never be split across the lock: `take_pending()` is one atomic pop, which is what makes AC2 true under two threads. Session mutation is deliberately not held that way — `_advance_step()` mutates the object and then calls `save_session()` — because holding the lock across a step would violate the boundary below. The write-through of DR2, fsync included, happens inside the lock — releasing it first would race memory against the file. **The lock is held across a store method and nothing else.** No caller holds it across an Ollama call, a Slack post, or an `eod_workflow` step: a background step that took the lock before its LLM call would stall every inbound DM for the duration.
- **DR4 — `take_pending()` is the only function that clears a pending action.** The text path, the approve path and the reject path all call it. Nothing else removes a pending record, with one carve-out: `load()` prunes records that have outlived their TTL as it reads the file (DR9a). That is expiry, not consumption — a pruned record is never returned to a caller and never executed.
- **DR5 — A pending record is returned once or never.** `take_pending(user_id, action_id=None)` returns the record only if it exists, has not outlived `PENDING_ACTION_TTL`, and the id matches. **The id is compared only when one is given:** a call with no id matches whatever record the user has, which is the text path, where someone typing an affirmative supplies nothing; a call with an id matches only the record carrying it, which is the button path. A mismatched id leaves the record in place — a stale button click must not destroy the current offer. An expired record is removed and `None` is returned.
- **DR6 — The store, not the client, supplies the action that gets executed.** The button value is an opaque correlation token. No execution path parses an action out of a Slack payload.
- **DR6a — Both sides of `session.pending_action` are persisted.** The set (`slack_eod.py:533`) and the clear (`:212`) each get a `save_session()`; saving only the clear would leave the pair asymmetric. These two are the only session mutations that reach no save on any path today. The control-word branches (`:254-256`, `:264-266`, `:275`) and `_reprompt_current_step()`'s completed block (`:507-509`) are deliberately **not** in this rule: each falls through into `_advance_step()`, which persists through `_handle_step_result()`'s existing `save_session()`, so adding saves there would be redundant rather than corrective. The session insertion is covered by step 3's mapping rule, not by this one.
- **DR7 — Discarding an EOD session is one call.** `discard_session(user_id)` removes it from memory and from the file together. No caller pairs those two operations by hand.
- **DR8 — Every daemon state file is written atomically.** `state_io.write_json_atomic()` writes a sibling temp file, flushes, fsyncs, sets the mode, then `os.replace()`s it into place. No `write_text()` call remains for a state file.
- **DR9 — This spec adds no database access.** Offering, expiring, correlating and clearing a pending action touch no session and no repository.

- **DR9a — `load()` is where both TTLs are enforced.** A pending record older than `PENDING_ACTION_TTL` and a session older than `EOD_SESSION_TTL` are dropped as the file is read, and the pruned state is written back. `take_pending()` applies the pending TTL again at read time, because a daemon that has been up for hours has not re-read the file. Naming `EOD_SESSION_TTL` without moving today's check (`slack_eod.py:104-111`) would restore and offer a week-old session.
- **DR10 — Opening an EOD session discards any pending action for that user.** The two state machines share one channel and one reply stream, so an offer made before a session starts must not survive it: today `_dispatch_message()` sets pending and the `start_eod` branch returns without touching it, so a 09:00 offer outlives the whole session and an affirmative afterwards still fires it. `handle_start_eod()` calls `take_pending()` and drops the result.

An implementer hitting anything these rules do not cover stops at the current step and reports it — `CLAUDE.md` Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `write_json_atomic(path, payload, mode=0o600)` in `state_io.py` — temp sibling, flush, fsync, chmod, `os.replace`. **The writer owns the parent-directory creation** (`mkdir(mode=0o700, parents=True, exist_ok=True)`), so the caller-side mkdirs at `state_io.py:23` and `acknowledgment.py:103` come out and `_write_scheduled_jobs()`, which has none today and relies on `_ensure_daemon_dirs()`, gains one. All three pre-existing writers adopt it: `write_last_inspection()`, `_write_scheduled_jobs()` and `AcknowledgmentStore._save()`. All three files become mode 600, which the 700 state directory already implies. | `workmain/daemon/state_io.py`, `workmain/daemon/daemon.py`, `workmain/daemon/acknowledgment.py`, `tests/test_orchestration.py` |
| 2 | New `workmain/daemon/conversation_state.py`: `PENDING_ACTION_TTL = timedelta(minutes=15)`, `EOD_SESSION_TTL = timedelta(hours=24)` (the inline literal, named), `PendingAction`, `SlackEodSession` moved verbatim except that `save`/`load`/`clear`/`_SESSION_PATH` become `to_dict()`/`from_dict()`, and `ConversationStore`. Store API: `load()`, `restored_sessions()`, `put_pending()`, `take_pending()`, `get_session()`, `has_session()`, `has_any_session()`, `save_session()`, `discard_session()`. `save_session()` is an upsert: it registers a session the store has not seen and persists one it has. `restored_sessions()` returns what `load()` brought back from disk, which is the only way the resume path can find a session whose `user_id` it does not yet know (F2). `load()` enforces both TTLs per DR9a. `from_dict()` rebuilds `steps` through a **deferred** `from workmain.workflows.eod_workflow import get_step_sequence`, exactly as `load()` does today — the entries hold live `runner` callables and are not serialized; the import stays inside the function so `workmain/daemon/` gains no module-level edge on `workmain/workflows/`. One file, `conversation_state.json`, written via DR8, mutated under DR3's lock. `load()` unlinks a legacy `eod_session.json` with an INFO log. `slack_eod.py` imports `SlackEodSession` from its new home. | `workmain/daemon/conversation_state.py`, `workmain/integrations/slack/slack_eod.py` |
| 3 | `SlackEodManager` takes the store in its constructor and loses `_sessions`. `has_session()` delegates; `has_any_session()` and `discard_session()` added. Every `session.save()` becomes `store.save_session(session)`, and so does the insertion at `slack_eod.py:197` (`self._sessions[user_id] = session`), which has no `save()` today and is the line that registers the session at all — `save_session()` is an upsert, so registering and persisting are the same call. Both `SlackEodSession.clear()` + `del self._sessions[...]` pairs become `store.discard_session(user_id)`. `handle_start_eod()` discards any pending action for the user per DR10. `handle_reply()`'s clear of `session.pending_action` (`slack_eod.py:212`) gains the `save_session()` it lacks, per DR6a. | `workmain/integrations/slack/slack_eod.py` |
| 4 | `format_blocks(action, action_id)` puts the id in both button values — replacing the serialized action on Approve and the literal `"reject"` on Reject, so both branches of step 5 can correlate. Its one production caller is updated in step 5; this step stands alone so the module that no other step touches has its own revert point. | `workmain/orchestration/confirmation_gate.py` |
| 5 | `daemon.py`: `_pending` deleted; store constructed in `__init__`, `load()`ed in `start()` before the manager is built, passed to it; `_operator_user_id` cached in `start()`. `handle_message()` uses `take_pending(user_id)`. `handle_block_action()` resolves the actor (`payload['user']['id']`, falling back to the cached operator id), calls `take_pending(user_id, value)`, refuses with a message when it gets `None`, and otherwise calls the existing `_execute_action()` — deleting its duplicated executor block. **The reject branch calls `take_pending(user_id, value)` too** and mirrors the approve branch exactly: `'Action rejected.'` when a record comes back, and the same refusal message when it does not. It must not report a rejection unconditionally — under DR5 a mismatched id leaves the record in place, so a stale Reject click on an older Block Kit message would tell the operator the action was rejected while the current offer stayed live and a following affirmative fired it. This is the third call site AC3.1 counts. **`_execute_action()` adopts the block path's `result.message or 'Action completed.'`** rather than the bare `result.message` it posts today, so an empty message can never reach Slack as an empty DM — a deliberate behaviour change on the text path, recorded in the deviations table at close-out. `_maybe_offer_eod_resume()` reads `restored_sessions()` instead of `SlackEodSession.load()` and the private dict; `_send_eod_resume_offer()`'s past-the-end branch and the `handle_reply` error branch call `discard_session()`. `scheduler._send_t4_checkin()` calls `has_any_session()`. | `workmain/daemon/daemon.py`, `workmain/daemon/scheduler.py` |
| 6 | Tests per §6, and the `docs/SLACK_SETUP.md:215` file-table row. | `tests/test_orchestration.py`, `tests/test_eod_workflow.py`, `docs/SLACK_SETUP.md` |

### Authorization points

**None.** No migration, no GitHub object deleted, no force-push, no merge to `main` within these steps. The branch is `feature/*`, so it ends with a daemon restart per `docs/DEVELOPMENT_STANDARDS.md` — that restart is the post-merge carve-out, not an authorization point. The dev→main PR at close-out is opened, not merged.

## 5. Acceptance criteria

AC1–AC7 map to issue #101's ACs in order, and AC5 restates the issue's wording per the Decision Log. AC8–AC18 have no counterpart in the issue: AC8 closes the two-stores loophole, AC9 records the two #102 ACs delivered early, and AC10–AC18 exist so that no coverage §6 promises can quietly fail to land while the issue still closes green. AC15–AC18 come from Caliper's two passes and cover paths the earlier drafts changed without stating. Edit the issue's ACs at close-out.

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
| AC8.2 | Both surfaces reach conversational state only through the store | `grep -rn 'SlackEodSession\.' workmain/daemon/daemon.py` returns zero hits; `grep -n 'def save\|def load\|def clear\|_SESSION_PATH' workmain/integrations/slack/slack_eod.py` returns zero hits |
| AC9.1 | The button value is an opaque id, not the action (delivers #102 AC3 early) | `grep -n 'json.dumps(action)' workmain/orchestration/confirmation_gate.py` returns zero hits |
| AC9.2 | A 4000-character note produces a button value under 2000 characters (delivers #102 AC4 early) | `pytest tests/test_orchestration.py -k test_long_action_button_value_under_slack_cap` |
| AC10.1 | Every daemon state file is written atomically | `grep -rn 'write_text' workmain/daemon/ workmain/integrations/slack/slack_eod.py` returns zero hits |
| AC10.2 | The atomic writer replaces content rather than appending, sets mode 600, and leaves no temp sibling behind | `pytest tests/test_orchestration.py -k test_write_json_atomic` |
| AC11.1 | Two threads calling `take_pending()` for the same record return it to exactly one caller | `pytest tests/test_orchestration.py -k test_concurrent_take_pending_returns_one_winner` |
| AC11.2 | The store round-trips both record types through a fresh `load()`, and loads a corrupt file as empty state rather than raising | `pytest tests/test_orchestration.py -k test_store_round_trip or test_store_load_corrupt_file` |
| AC11.3 | A mismatched action id leaves the pending record in place | `pytest tests/test_orchestration.py -k test_mismatched_action_id_leaves_record` |
| AC11.4 | A legacy `eod_session.json` is unlinked at load | `pytest tests/test_orchestration.py -k test_legacy_session_file_removed_on_load` |
| AC12.1 | A block payload carrying `user.id` uses it; one without falls back to the cached operator id | `pytest tests/test_orchestration.py -k test_actor_resolution` |
| AC13.1 | T4 suppression asks the manager, not a dict | `pytest tests/test_orchestration.py -k test_t4_suppressed_during_active_t5_session`; `grep -n 'has_any_session' workmain/daemon/scheduler.py` returns one hit |
| AC14.1 | Opening an EOD session discards any pending action for that user (DR10) | `pytest tests/test_orchestration.py -k test_start_eod_discards_pending_action` |
| AC15.1 | Rejecting via the button clears the pending record, so a following affirmative executes nothing | `pytest tests/test_orchestration.py -k test_block_reject_clears_pending` |
| AC16.1 | A session restored from disk is offered for resume without the daemon knowing its `user_id` in advance | `pytest tests/test_orchestration.py -k test_resume_offer_from_restored_session` |
| AC16.2 | A session older than `EOD_SESSION_TTL` is not restored and is not offered (DR9a) | `pytest tests/test_orchestration.py -k test_stale_session_not_restored` |
| AC17.1 | Clearing `session.pending_action` is persisted, so a restart does not resurrect a consumed inline correction (DR6a) | `pytest tests/test_orchestration.py -k test_cleared_inline_pending_not_resurrected` |
| AC17.2 | Setting `session.pending_action` is persisted too, so the pair is symmetric (DR6a) | `pytest tests/test_orchestration.py -k test_set_inline_pending_persisted` |
| AC17.3 | Starting a session persists it immediately, before any step runs | `pytest tests/test_orchestration.py -k test_start_eod_persists_session_on_insert` |
| AC15.2 | A Reject click carrying a stale id refuses rather than reporting a rejection, and leaves the live pending record intact | `pytest tests/test_orchestration.py -k test_stale_reject_does_not_clear_current_pending` |
| AC18.1 | An `ActionResult` with an empty message posts a fallback, never an empty DM, on both the text and button paths | `pytest tests/test_orchestration.py -k test_empty_result_message_posts_fallback` |

## 6. Test plan

- **Baseline before this work:** 953 passed, 0 failed — `CHANGELOG.md` [1.30.0].
- **Expected after:** 953 + ~36 = ~989 passed.

`tests/test_orchestration.py` is the established home for daemon dispatch, Block Kit and T5 persistence coverage and takes the bulk of this. Its `TestT5SessionPersistence` group currently patches `SlackEodSession._SESSION_PATH`; that attribute is gone, so the group's setUp switches to pointing a `ConversationStore` at a temp directory. `_make_daemon()` loses `daemon._pending` and gains a store. `test_format_blocks_action_serialized_in_value` asserts the defect this spec removes and is rewritten to assert the opaque id — record it in the results artifact's deviations table with the two #102 ACs.

**Existing tests that will break, in full.** AC4.1's grep catches only the `_eod_manager._sessions` form, so the rest surface as failures under AC7.1 rather than as a grep: `test_orchestration.py:37` (`daemon._pending`), `:43`, `:442`, `:511-576` (the `_eod_manager._sessions` block), `:703-710` and `:716-803` (`_SESSION_PATH` patching and the `save`/`load`/`clear` group), `:813` and `:820` (`manager._sessions`), and `test_eod_workflow.py:861`, `:904`, `:932` (`manager._sessions`). Anvil should expect to touch all of them; a green suite that skipped one means it was deleted rather than rewritten.

New coverage:

Every bullet below carries an AC, so none of it can quietly fail to land and still close green:

- **Store unit tests** — round-trip and corrupt-file handling (AC11.2), mismatched id leaves the record (AC11.3), legacy file unlinked (AC11.4), and two threads racing `take_pending()` (AC11.1). AC11.1 is the one that proves "exactly one write" under the concurrency §2 establishes; §7 calls it the load-bearing part, so it is an AC and not a promise.
- **Double-execution** — AC2.1 and AC2.2, both orderings.
- **TTL** — AC5.1, plus an expired pending falling through to a fresh intent parse rather than executing.
- **Session lifecycle** — AC6.1: the `handle_reply` error branch, `_abort_session()` and the past-the-end resume branch each leave no resumable state, and `discard_session()` is the only path that does it.
- **Pending discarded at session start** — AC14.1, covering DR10.
- **Actor resolution** — AC12.1, both branches.
- **Atomic write** — AC10.2.
- **T4** — AC13.1; the existing tests that set `daemon._eod_manager._sessions` directly are rewritten against the public method.
- **Reject path** — AC15.1 and AC15.2, the matching and stale-id cases.
- **Resume on restart** — AC16.1 and AC16.2.
- **Inline correction persistence** — AC17.1 and AC17.2, both sides of the pair; AC17.3 for the insertion.
- **Empty result message** — AC18.1.

All Slack and Ollama calls stay mocked; no test touches the real state directory.

## 7. Risks and rollback

- **An in-flight EOD session does not survive the upgrade.** The new store reads `conversation_state.json`, which will not exist on first start; the legacy `eod_session.json` is unlinked rather than migrated. A session open at restart time is lost and must be restarted with `start eod`. Deliberate: writing a one-shot importer for a file that can only be hours old, for a single operator, costs more than the restart. Restart the daemon outside an EOD session.
- **The block_actions actor field is asserted from the Slack API contract, not verified against this tree** (§2, last row). If `payload['user']['id']` is absent in practice, the fallback to the cached operator id keeps Approve working, because the DM channel is resolved from that same operator id. Both branches are covered by tests.
- **Mode 600 on `last_inspection.json` and `scheduled_jobs.json` is a change.** Both are read only by the same user through `notifications status`, inside a directory already expected at 700. If something unanticipated reads them as another user it will now fail loudly rather than silently.
- **Concurrency is the load-bearing part.** The lock is what makes "exactly one write" true when Approve and "yes" arrive on two threads at once; the test that drives two threads through `take_pending()` is the one that proves it. #97 will later move dispatch to a bounded pool, which does not change the requirement.
- **Rollback:** every step is an independent commit and individually revertible. Reverting steps 2–5 restores `SlackEodSession`'s own persistence; the only residue is a `conversation_state.json` the old code ignores. Step 1 stands alone and is worth keeping either way.
