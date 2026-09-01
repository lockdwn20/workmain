# Slack Conversation State — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20260901
**Originating item:** Issue #101, child of #99, milestone 7 *Slack Intent Contract*

---

## 1. Purpose

Issue #101 asserts that two state machines share one Slack DM channel and that one of them can execute a confirmed action twice. This study verifies that assertion against source, establishes what else the DM channel's state touches, and settles three questions the issue leaves open: where a single store should persist, how a Block Kit button click should correlate to the pending record it confirms, and where the pending-action TTL belongs. It is being asked now because #101 is at board position 5 and the answer to the first question determines whether this code sits in the path of #95, #96 and #97.

All findings below were verified against source on 20260831 on `main` at `e589f9d`.

## 2. Scope of the read

**Read:** `workmain/daemon/daemon.py`, `workmain/daemon/scheduler.py`, `workmain/daemon/state_io.py`, `workmain/integrations/slack/slack_eod.py`, `workmain/integrations/slack/socket_client.py`, `workmain/orchestration/confirmation_gate.py`, `workmain/services/schedule_service.py`, `workmain/database/repositories/system_state_repository.py`, `workmain/database/models.py` (`SystemState` only), `tests/test_orchestration.py`, `tests/test_eod_workflow.py` (T5 groups), and the bodies of issues #95, #96, #97, #99, #100, #102, #103.

**Deliberately not read:** `workmain/orchestration/action_executor.py` beyond its call signature — its dispatch and task-matching internals are #100's and #103's subject. `workmain/ai/intent_parser.py` beyond the fact that `_dispatch_message()` calls `parse()` — the parse contract is #100's. The `eod_workflow` step runners, except `get_step_sequence()`, which session rehydration calls.

**Not covered, and therefore unknown:** whether any surface outside this repository reads `~/.workmain/daemon/*.json`. The read covers this tree only.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | The block-action path executes straight from the button value and never touches `_pending`, so clicking Approve and then typing an affirmative executes the same action twice and writes two records. The text path pops pending first; the button path has no equivalent. | `daemon.py:436-471` `handle_block_action()` — `json.loads(action['value'])` at `:446`, `ActionExecutor(session).execute(action_dict)` at `:455`; against `daemon.py:423-424` `handle_message()` | Critical |
| F2 | The EOD error branch removes the in-memory session without clearing the persisted file, so the next daemon start offers to resume a session that was discarded as broken. | `daemon.py:419`, `self._eod_manager._sessions.pop(user_id, None)` with no `SlackEodSession.clear()` | High |
| F3 | Pending actions have no expiry. An offer made in the morning executes on any affirmative later that day. | `daemon.py:327`, `self._pending: dict = {}` — no timestamp stored on the record | Medium |
| F4 | The button value is the serialized action. Slack caps that field at 2000 characters, so a long note or correction produces a payload Slack will not accept, and the executed payload round-trips through the client rather than being held server-side. | `confirmation_gate.py:124`, `"value": json.dumps(action)` | High |
| F5 | Session cleanup is written out by hand in four places, in two different combinations. `_advance_step()` and `_abort_session()` pair `SlackEodSession.clear()` with `del self._sessions[...]`; `_send_eod_resume_offer()` does the same; `daemon.py:419` does only half of it (F2). | `slack_eod.py:346-348`, `slack_eod.py:571-582`, `daemon.py:587-588`, `daemon.py:419` | High |
| F6 | Restoring a session at start writes directly into the manager's private dict from the daemon. | `daemon.py:568`, `self._eod_manager._sessions[session.user_id] = session` | Medium |
| F7 | The T4 suppression check iterates the manager's private dict and asks `has_session()` about each key it just read from that same dict — a tautology that exists only because no public "is any session active" method does. | `scheduler.py:346-347` | Low |
| F8 | No daemon state file is written atomically, and only one of the four sets a mode. `state_io.py` shares a path helper and nothing else: four files under `{WORKMAIN_STATE_DIR}/daemon/`, four independent `write_text()` writers, one `chmod`. A crash or a full disk mid-write truncates the file in place. | `state_io.py:14` `daemon_state_path()`; `state_io.py:33` `write_text`; `daemon.py:107` `write_text`; `acknowledgment.py:104` `write_text`; `slack_eod.py:98-99` `write_text` + `chmod(0o600)` | Medium |
| F9 | The block-action path duplicates `_execute_action()`'s body. The two differ only in that the block path posts `result.message or 'Action completed.'` and the text path posts `result.message` — so the same action produces different DM text depending on which path confirmed it. | `daemon.py:451-464` against `daemon.py:507-522` | Low |
| F10 | Inbound Slack events are dispatched one unbounded thread per event, so two DMs, or a DM and a button click, can be inside the handlers simultaneously. Any read-decide-write over shared state is racy today. | `socket_client.py:126-131`, `:137-142` | High |
| F11 | The EOD session holds a live `Thread` and `Event` that are deliberately excluded from persistence, and `_abort_session()` depends on the identity of that `Event` to cancel an in-flight background step. Any store design must hold live objects; no serialization can carry these. | `slack_eod.py:71-75` (`compare=False, repr=False`); `slack_eod.py:569-570`, `session._cancel_event.set()` | High |
| F12 | Session staleness is an inline 24-hour literal rather than a named constant, and is the only expiry rule anywhere in the DM channel's state. | `slack_eod.py:109`, `timedelta(hours=24)` | Low |
| F13 | `SlackEodSession.pending_action` is a third pending mechanism, distinct from `_pending` and from the session itself. It is set by `_handle_inline_correction()` and consumed at the top of `handle_reply()`, carries no TTL and no identifier, and never posts buttons. | `slack_eod.py:533` and `slack_eod.py:208-210` | Low |
| F14 | `system_state` is a generic KV table — `key` TEXT primary key, `value` TEXT, `updated_at`. Storing conversational state there requires no migration. | `models.py:24-34`, `SystemState` | Informational |
| F15 | `SystemStateRepository.set()` commits internally, on every call. | `system_state_repository.py:38`, `self.session.commit()` | Informational |
| F16 | Nothing in `workmain/daemon/daemon.py` or `workmain/integrations/slack/` imports `SystemStateRepository`. Offering, confirming and clearing a pending action currently touch no database at all; only executing one does, through the services. | `grep -rn 'SystemStateRepository' workmain/daemon/daemon.py workmain/integrations/slack/` returns zero hits | Informational |
| F17 | Exactly one production caller of `format_blocks()` exists, and one test asserts the serialized-action button value that F4 describes. | `daemon.py:503`; `tests/test_orchestration.py:253`, `test_format_blocks_action_serialized_in_value` | Informational |
| F18 | One document names the session file. Nothing else in the tree does outside `slack_eod.py` itself. | `docs/SLACK_SETUP.md:215`; `grep -rn 'eod_session' workmain/` returns one hit | Informational |
| F19 | **Asserted, not verified.** The Slack `block_actions` payload is taken to carry the acting user at `payload['user']['id']`. This comes from the Slack API contract, not from this tree: `handle_block_action()` reads no user field today, and the test helper builds a payload with no `user` key, so nothing here would catch it if the assumption were wrong. | `daemon.py:436-471`; `tests/test_orchestration.py:72-82`, `_block_action_payload()` | Flagged |

F1, F2 and F3 are the three consequences issue #101 names. All three reproduce as described. F4, F5, F8, F9, F10 and F13 are adjacent and were not named in the issue.

## 4. Options

Three decisions. The first two are independent; the third has a weak dependency on the first, noted below.

Every option in Q1 is identical above the persistence line. F11 forces it: the store holds live objects in memory whatever the durable form, because a `threading.Event`'s identity cannot be serialized and `_abort_session()` needs it. The choice is only where the bytes land.

### Q1 Option A — One JSON file under the daemon state directory

- **Approach:** `ConversationStore` holds both record types in memory under one lock and writes the whole state through to `~/.workmain/daemon/conversation_state.json` on every mutation. Read once at daemon start.
- **Pros:** keeps this code out of the database entirely, preserving F16 — offering a pending action stays DB-free. The daemon's other volatile state is already files in that directory. Debuggable with `cat`. No session lifecycle to get wrong inside the EOD background thread.
- **Cons:** atomic-write and permission correctness are ours to write. Contrary to an initial claim in this study's own drafting, **none of that is inherited** — F8 establishes that `state_io.py` shares a path helper and nothing more. The honest cost is roughly fifteen lines of `write_json_atomic()`. That cost has a payoff: applying it to the two pre-existing files closes the corruption window F8 describes in both.

### Q1 Option B — One row in `system_state`

- **Approach:** the same store, persisting a JSON document into one KV row through `SystemStateRepository`.
- **Pros:** no migration (F14). One durable-state technology. Each write is atomic for free. Backed up with the database. Readable by any other process through the existing repository.
- **Cons:** F15 — `set()` commits internally, and this would call it from a background thread on every EOD step and every pending set or take. That is precisely the pattern #96 exists to remove, and under the `NullPool` that #97 exists to replace, each of those commits opens a fresh Postgres connection from a Slack handler thread. #101 is at board position 5; #95 and #96 are at 13 and 14. The work would be written into the path of the next two issues and then reworked. It also spends the database's guarantees on data that needs none of them — single-process, single-user state that dies at restart plus TTL is not transactional, not concurrent across processes, and not queryable once it is an opaque JSON blob in a text column. "Backed up with the database" cuts the wrong way: a half-finished EOD session restored from a three-day-old backup is not a wanted outcome.

### Q1 Option C — Two files, one owning module

- **Approach:** `conversation_state.py` owns both `pending.json` and `eod_session.json`.
- **Pros:** smallest diff; the existing persistence tests survive unchanged. It does fix F1 and F2, which are logic errors rather than storage errors.
- **Cons:** does not answer the issue's stated ask, and leaves two files that can disagree after a crash between the two writes.

**Recommendation: Option A.** The deciding argument is sequencing rather than storage: Option B writes new code in the pattern #95 and #96 exist to eliminate, eight and nine board positions before those issues run. Option A leaves this code untouched by all three. The secondary argument is that the data has none of the properties the database is for.

### Q2 Option A — Correlate a button click by comparing its payload to the stored action

- **Approach:** the button value stays the serialized action; `take_pending()` returns the record only if the stored action equals the round-tripped payload.
- **Pros:** stays inside #101's boundary and leaves #102 exactly as written. No practical failure mode today — the only case it cannot distinguish is two identical pending actions, where executing one is the right answer anyway.
- **Cons:** leaves F4 open until #102, at board position 26. More seriously, #100's whole job is replacing the action dict with a typed model; the moment serialization changes, value-comparison either breaks or needs a normalization step that nothing in the code would remind anyone to write.

### Q2 Option B — Give the pending record a uuid and put only that in the button

- **Approach:** `PendingAction` carries a uuid4; `format_blocks()` puts it in the button value; the store supplies the action to execute.
- **Pros:** correlates by identity, which is immune to how the action is serialized and therefore survives #100 untouched. Less code than what is there now. Fixes F4 immediately.
- **Cons:** delivers #102's AC3 and AC4 ahead of #102, so those ACs must be edited at close-out and recorded in the results artifact's deviations table.

**Recommendation: Option B.** The deviations table exists for exactly this, and an issue boundary is not worth preserving at the cost of leaving a live defect in code the change is already rewriting.

### Q3 Option A — Module constant

- **Pros:** matches the two existing expiry rules in this area, both constants — F12's 24-hour session window and the 60-second socket dedupe window. Preserves F16: no database on the offer path.
- **Cons:** retuning needs a code change and a restart.

### Q3 Option B — `system_state` key read through a service

- **Pros:** matches `t4_interval_min`/`max` and the two progress intervals, all of which are tunable through the same mechanism. Reads unambiguously as "a configured TTL", which is the issue's own wording.
- **Cons:** puts a database read on a path that has none today (F16), and needs a default fallback for when the database is unreachable, which every getter in that family already carries.

**Recommendation: Option A.** The test that separates the two families is whether the correct value depends on Ray or on the world. The T4 window and the progress intervals are preferences — another operator would set them differently. How long a conversational offer stays meaningful is not a preference: above roughly half an hour an affirmative no longer plausibly refers to the offer, and below about five minutes it expires while you make coffee. That is the same category as the 24-hour and 60-second windows, both of which are constants for that reason. The dependency on Q1 is weak but real: if Q1 had gone to Option B the database would already be on this path and the argument would largely evaporate. Promoting a constant later is a handful of lines, which makes this the cheapest of the three decisions to reverse.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Where does the single store persist — a JSON file, a `system_state` row, or two files behind one module? | **Answered 20260831 (Ray): Option A**, the file, on the sequencing argument against #95–#97. Additionally directed that `write_json_atomic()` live in `state_io.py` and that the pre-existing state files adopt it, so F8 is closed for every file rather than only the new one. `acknowledgments.json` was missed when that was first written down and is included — Ray, 20260901. |
| Q2 | How does a Block Kit button click correlate to the pending record it confirms? | **Answered 20260831 (Ray): Option B**, the uuid, on the grounds that #100 will break value-comparison and that F4 is a live defect in code this change already rewrites. Early delivery of #102's AC3/AC4 to be recorded in the deviations table and the ACs edited at close-out. |
| Q3 | Does the pending-action TTL belong in a module constant or in `system_state`? | **Answered 20260831 (Ray): Option A**, the constant, on the tunable-versus-constant test stated above. |
| Q4 | Do issue #101's acceptance criteria actually assert that the two stores became one? | **Answered 20260831 (Ray): no.** AC1 removes `_pending` from `daemon.py` and AC4 removes reaching into `_eod_manager._sessions`; both are satisfied by moving `_pending` into `SlackEodManager` as a second dict beside `_sessions`, leaving two stores with every AC green. An AC requiring that one module own both, reached only through it, is to be added to the spec and to the issue at close-out. |
| Q5 | Issue #101's AC5 says "a configured TTL". Does that wording prejudge Q3? | **Answered 20260831 (Ray): yes.** To be restated as "a stated TTL" in the spec, and the issue's AC edited at close-out. |
| Q6 | Is `SlackEodSession.pending_action` (F13) in scope as a third pending store? | **Open — Spanner's position:** no. It rides inside the session record, so it reaches the one store automatically once sessions do; it never posts buttons, so F1 cannot apply to it; and it is set and consumed inside the same `handle_reply()` that owns the session, so F3 cannot either. Unifying it with `PendingAction` would give it a TTL and an identifier it has no use for. Recorded in the spec's out-of-scope section so it is not mistaken for an oversight. |

## 6. Disposition

- Promoted to: `../specs/SLACK_CONVERSATION_STATE_SPEC.md`
