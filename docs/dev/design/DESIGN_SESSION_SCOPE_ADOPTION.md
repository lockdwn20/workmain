# Session Scope Adoption — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261012
**Originating item:** Issue #95

---

## 1. Purpose

Issue #95 replaces every hand-written `get_session()` / `try` / `finally: session.close()` block under `workmain/` with `DatabaseConnection.session_scope()`. It also writes the §4.1 rule that a command owns its unit of work. The issue calls the change mechanical. This study checks that claim against the source.

`session_scope()` does two things the hand-written blocks do not: it commits when the block exits normally, and it rolls back on `Exception`. Those two additions are where a mechanical conversion stops being behaviour-neutral. This study finds every site where they change behaviour, and asks Ray the questions that decide how the spec handles each one.

## 2. Scope of the read

- **Read:** every `get_session()` call under `workmain/` except `workmain/database/connection.py`, plus the helpers those blocks call, walked transitively by name for process exits. Also every test under `tests/` that stubs `get_db` or `get_session`, `tests/conftest.py`'s isolation fixture, and every live document that states the session pattern.
- **Searches:** `grep -rn 'get_session()' workmain/ --include='*.py' | grep -v connection.py`, `grep -rnE "get_session(\.return_value| *=|\.side_effect)" tests/`, and `grep -rln 'get_session\|session\.close()\|session_scope' docs .claude CLAUDE.md`, excluding `docs/archive/`. The per-site shape (where the session opens, the handlers, any in-block swallow, values used after `close()`, explicit commits and rollbacks, exits inside the block) came from an AST walk of each site's enclosing function.
- **Not read:** `scripts/`, which is outside the issue's `workmain/` scope. It has its own `get_session()` calls and no `session_scope()` calls. `automation/` has neither.
- **Library behaviour** was observed, not reasoned. A sqlite-in-memory probe against the installed SQLAlchemy 2.0.23 reproduced the failures in F3 and F4.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | The connection leak the issue names is already gone. `intent_parser.py` no longer opens a session: #191 moved cost recording to `ai_cost_service.record_reply`, and that function closes its session in `finally`. Every `get_session()` site under `workmain/` now closes in a `finally`. No site is missing one. | `workmain/services/ai_cost_service.py:44-66` `record_reply`; commit `36ae559` | Medium — the issue's fourth acceptance criterion names a site that no longer exists |
| F2 | The class is `DatabaseConnection`. §4.1 calls it `Database`, and its example is the hand-written `try`/`finally` pattern this issue retires. `session_scope()` exists with commit, rollback on `Exception`, and close in `finally`. Its only caller is a test. | `workmain/database/connection.py:30,64-81`; `docs/DEVELOPMENT_STANDARDS.md` §4.1; `tests/test_database_isolation.py:46` | Low |
| F3 | **The exit commit expires every loaded object.** `sessionmaker` uses the default `expire_on_commit=True`. Today a block that only reads never commits, so its objects stay loaded after `close()`. Inside `session_scope()` the exit commit expires them, and the first attribute read after the block raises `DetachedInstanceError` (observed). Three sites read ORM attributes after the block. Every other value used after a block is a scalar, string, tuple or dict. | `workmain/daemon/scheduler.py:213` `_schedule_today_meeting_triggers` (`meeting.is_cancelled`, `.start_time`, `.id`); `workmain/cli/commands/notifications.py:186` `notifications_status` (`config.updated_at`, `.enabled`, `.method`); `workmain/cli/interface.py:138` `status` (`active_client.name`, `.id`) | High — the first breaks T2/T3 scheduling in the daemon |
| F4 | **A failed session that a handler swallows inside the block now fails at exit.** If a DB error is caught inside the block without a rollback, today's `close()` discards the session quietly. `session_scope()`'s exit commit raises `PendingRollbackError` (observed). The same applies to a handler that catches and returns inside the block when the `with` wraps it: the EOD steps' `except Exception: return EodStepResult(...)` and the CLI commands' `except Exception: console.print(...)` handlers. If the `with` sits outside the handler, the step that today reports "failed — continuing" raises out of the workflow instead. The AST walk found no handler on any site's own `try` that uses the session. | `workmain/workflows/eod_workflow.py:458,670,971` (own handlers → `return`); `workmain/cli/commands/notes.py:647` (`notes_log`'s per-line `except Exception`, after `notes_service.create_note`); `workmain/workflows/eod_workflow.py:612` (`except Exception: pass` around `set_forwarding_note`) | High — the handler's position relative to the `with` decides behaviour |
| F5 | **Process exits inside a block.** `SystemExit` is not an `Exception`, so `session_scope()` skips both commit and rollback and only closes. The repositories commit today, so no write is lost. #96 removes those commits, and the same exits will then discard the scope's writes. Four are raised directly inside a block. Eight more come through a helper called inside a block. No `ctx.exit()`, `click.Abort` or other `click` exception is raised inside a block. Those subclass `RuntimeError` (click 8.1.7), so a scope would roll back on them rather than skip. | Direct: `meetings.py:834` `meetings_condense`; `reports.py:544,623,696`. Via helper: `reports.py:438,472` (`_resolve_report`); `tasks.py:312,356,388` (`_resolve_task`); `gdocs.py:324,440,528` (`_get_client`). Helper matching is by bare function name. | Medium — inert under #95, and #96's spec lists each one (issue #96 body) |
| F6 | **Explicit commits stay correct inside a scope.** The mid-block commits in the EOD steps and five CLI commands commit per decision, so a cancelled EOD loses nothing already decided. A scope's exit commit after them is a no-op or commits the remainder. Commits outside the repositories (`notes_service`, `note_condenser`, Clockify sync) are #96's census, not #95's. | `eod_workflow.py:458,670,883,971`; `meetings.py:834`; `notes.py:520`; `reports.py:438`; `slack.py:593`; `tasks.py:356,388`; `workmain/services/notes_service.py:23,36,39`; `workmain/ai/note_condenser.py:164,180`; `workmain/integrations/clockify/sync.py:109,186` | Info |
| F7 | **Tests that inject a session through a `get_session` stub stop reaching the code.** After conversion the code calls `get_db().session_scope()`. On a patched `get_db` that returns a fresh `MagicMock`, the test's stubbed session is never used. Some of these tests then pass without exercising anything; others fail. The stubs fall into two forms. In `tests/test_eod_workflow.py` they hand in the real `db_session`, which the #136 fixture already makes unnecessary: the code's own session joins the test's transaction (§6.1). In `test_orchestration.py`, `test_eod_task_matching.py`, `test_gdrive.py`, `test_provider_foundation.py` and `test_ai_costs.py` they hand in a `MagicMock` session, often with repository fakes. `test_ai_costs.py:627` asserts `close` and `commit` on the stubbed session. | `grep -rnE "get_session(\.return_value\| *=\|\.side_effect)" tests/` | High — the conversion's test risk |
| F8 | **The test factory restates the production `sessionmaker` arguments.** `tests/conftest.py` builds its own `sessionmaker(autocommit=False, autoflush=False, ...)`. A change to the production factory's arguments, such as `expire_on_commit`, does not reach tests unless it is made in both places. | `tests/conftest.py:34-39`; `workmain/database/connection.py:51-55` | Medium — conditional on the Q1 answer |
| F9 | **§4.1's required rule depends on a rule no document states yet.** The issue's last criterion has §4.1 say a service never opens or commits a session "except for the writes §4.3 says commit on their own". The outside-action rule that defines those writes is in issue #96's body, and #96 writes it into §4.3. Until #96 ships, §4.1 would cite text that does not exist. Live code also contradicts "a service never commits" until #96 lands (F6), and `ai_cost_service` opens its own session as an outside-action write. | issue #96 body § Writes that record an outside action; `docs/DEVELOPMENT_STANDARDS.md` §4.3 | Medium — sequencing between two specs |
| F10 | **Other live documents restate the pattern.** §4.2 says "access ORM relationships inside the `try` block, before `session.close()`". Under F3 that rule has to cover every attribute, not only relationships, and its wording names the retired pattern. §6.1 says "Never call `get_db()` or `db.get_session()` in a test", which stays true. No other live document, skill or `CLAUDE.md` states the session pattern. | `docs/DEVELOPMENT_STANDARDS.md` §4.2, §6.1 | Low |
| F11 | **One helper opens a session only when the caller doesn't pass one.** `_get_draft_recipients` uses the caller's session when it gets one, and otherwise opens its own. That is the shape the new §4.1 rule forbids for a service. It is a CLI helper, not a service. | `workmain/cli/commands/email.py:101-149` | Low |

## 4. Options

### Q1 — objects read after the scope (F3)

#### Option A — keep objects inside the scope

- **Approach:** at the three F3 sites, read every value the code after the block needs while the scope is still open, or move that code inside the scope. §4.2 then states the rule: no ORM object is read after its scope exits. The factory keeps `expire_on_commit=True`.
- **Pros:** commit semantics stay as they are everywhere. It matches §4.2's existing rule that objects do not cross a session boundary. `scheduler.py:353` `_send_t4_checkin` already does it ("Captured before close"). A miss fails loudly with `DetachedInstanceError` rather than silently.
- **Cons:** a site the AST walk missed, for example an object reached through a value returned from a helper, fails at runtime. Only three sites were found, but the walk is name-based.

#### Option B — `expire_on_commit=False` on the session factory

- **Approach:** set `expire_on_commit=False` in `DatabaseConnection.connect()` and in `tests/conftest.py`'s factory (F8). Objects stay readable after the scope.
- **Pros:** one line in each factory, and no site can be missed.
- **Cons:** after an explicit mid-block commit, objects already in the identity map keep their pre-commit attribute values, and a later query does not refresh them without `populate_existing`. The EOD steps commit mid-loop and query again (`eod_workflow.py:628` `remaining = task_repo.get_filtered(...)`), and the repositories `commit()` then `refresh()` only the object they return. That turns a loud failure into stale reads. It also changes every session in the application, not only the converted ones, which is a wider blast radius than the issue.

**Recommendation:** Option A. The project already rules that ORM objects do not cross a session boundary (§4.2), and Option B quietly loosens that rule for the whole application to avoid three edits. Its failure mode, stale data with no error, is the one this milestone exists to remove.

### Q2 — where #95 states the outside-action exception (F9)

#### Option A — §4.1 cites §4.3, and #96 writes §4.3

- **Approach:** #95's §4.1 states the rule and cites §4.3 for the exception. §4.3 has no such text until #96 ships.
- **Pros:** neither issue's body changes.
- **Cons:** `main` carries a citation to text that does not exist for at least one release, which breaks the single-owner rule's "everywhere else cites it".

#### Option B — #95 writes the rule's text into §4.3, and #96 implements its sites

- **Approach:** #95 writes the outside-action rule, as #96's body words it, into §4.3, and §4.1 cites it. #96 keeps the site census, the per-site implementation and the tests. At #96's spec, its sixth criterion is restated to check that §4.3 states the rule, not to write it.
- **Pros:** the citation resolves the day #95 ships. The rule's text has one home from the start.
- **Cons:** it edits #96's acceptance criteria, which is Ray's call. Until #96 ships, §4.3 states a rule that four live sites do not yet follow.

**Recommendation:** Option B. A standard cited before it is written is a dangling reference in the one document that owns the rules. Writing a rule before its sites comply is the normal order here: #96 already exists to bring them into line, and its spec lists them.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | When a `with session_scope()` block exits, its commit expires every ORM object the block loaded, and reading one afterwards raises `DetachedInstanceError`. Three sites do that today: daemon meeting-trigger scheduling, `notifications status` and `workmain status`. Should those sites read what they need while the scope is open (§4.1 Option A), or should both session factories set `expire_on_commit=False` (Option B)? Recommended: A. | |
| Q2 | The §4.1 rule exempts "the writes §4.3 says commit on their own", but no document states that rule yet; issue #96's body does, and #96 is meant to write it. Should #95 write that rule's text into §4.3 now and leave #96 to bring its sites into line (§4.2 Option B), or should §4.1 cite §4.3 and wait for #96 (Option A)? Recommended: B. | |
| Q3 | `notes log` creates one note per entered line and swallows each line's failure. After a database error, every later line fails as well, and with `session_scope()` the exit commit then fails too and prints a second error. Should #95 fix this with a savepoint per line, or should it ship unchanged and the defect go to an issue of its own? Recommended: its own issue, because the defect exists today and the conversion only adds one more error line. | |

## 6. Disposition

- Promoted to:
- Superseded by:
