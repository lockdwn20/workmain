## 4. Database Standards

### 4.1 Session pattern

- Application code under `workmain/` opens a session only through `DatabaseConnection.session_scope()`, reached through `get_db()`. The scope commits when its block exits normally, rolls back when an `Exception` leaves the block, and closes the session in every case.

  ```python
  from workmain.database.connection import get_db

  db = get_db()
  with db.session_scope() as session:
      repo = SomeRepository(session)
      # ... work ...
  ```

- **The code that opens a scope owns its unit of work.** It may commit inside the scope. Code it hands the session to — a repository, a service, an orchestrator such as `ActionExecutor` — reads and writes through that session and never commits it, rolls it back or opens another. Two exceptions: it may contain a failure in a savepoint (`session.begin_nested()`, below), and it records an outside action in a session of its own (§4.3).
- **The owner commits before it waits.** If the scope has written since its last commit, the owner commits immediately before it prompts, opens an editor, starts a child `workmain` process or performs an outside action. No transaction holding a write stays open across user input, a child process or a call to another system.
- `get_session()` is a method on `DatabaseConnection`, not a module-level function. In application code under `workmain/`, only `session_scope()` calls it; tests follow §6.1.
- **A handler that recovers from an exception sits outside the `with`, or outside a savepoint inside it.** A handler that wraps the `with` runs after the scope has rolled back. Inside the block, the guarded work runs in `with session.begin_nested():` and the handler wraps that, so a failure rolls back to the savepoint and the scope carries on. Nothing inside a savepoint commits: a commit there commits the whole transaction. A handler inside the block that swallows a database error without a savepoint leaves the transaction failed, and the scope's commit then raises.
- **An exception that is not an `Exception` skips both commit and rollback.** `SystemExit` (from `sys.exit()` or `raise SystemExit`) and `KeyboardInterrupt` derive only from `BaseException`, so the scope only closes the session and its uncommitted writes are discarded. `ctx.exit()` and `click.Abort` are `Exception`s and roll the scope back.

### 4.2 Session discipline

- Objects must be re-queried inside the session that will modify them. Passing an ORM object across a session boundary causes **silent** persistence failures — no exception, no write.

- No ORM object is read after its `session_scope()` block exits. The exit commit expires every loaded attribute, and a read afterwards raises `DetachedInstanceError`. Read the values the code after the block needs while the block is open.

### 4.3 Repository pattern

- All data access goes through a repository.
- Models are SQLAlchemy declarative base.

  ```python
  class SomethingRepository:
      def __init__(self, session: Session):
          self.session = session

      def create(self, ...) -> Model:
          obj = Model(...)
          self.session.add(obj)
          self.session.flush()
          self.session.refresh(obj)
          return obj
  ```

- **A repository method never commits.** It flushes after a write, so the row has its id and its database defaults, and later queries in the session see it.
- **A repository method that returns rows loads, with them, every related record a caller reads on each row.** A relationship is lazy by default. Reading one issues a query the first time for each row, or for each distinct related row of a many-to-one, so a list of N rows costs up to N + 1 queries. The method uses `contains_eager` where its query already joins the related table, `joinedload` for a many-to-one it doesn't join, and `selectinload` for a one-to-many. It loads only what its callers read. A caller that reads none of it still gets it, and pays one join or one query per call, which doesn't grow with the rows. A change that adds a per-row read of a relationship adds the loader to the method in the same change. §6.2 states how the loading is tested.
- **A write that records an outside action commits on its own.** A row that records something already done outside WorkmAIn's database — a provider call that has been billed, a file in Drive, a Slack message, an entry in Clockify — is written in its own session, opened with `get_db().record_scope()`, immediately after the action, independent of the command's unit of work, so a later failure in the command can't undo the record of something that can't be undone. `record_scope()` is `session_scope()` with a lock timeout, so a record that reaches a row another transaction holds fails instead of waiting.
  - It never writes or references a row the command's open transaction has written. A second session can't see an uncommitted row, and waits on a row the transaction has locked.
  - Its failure is never silent. Cost recording logs a warning and carries on. Every other record reports, on stderr, what happened outside, what was not recorded and what will repeat. The command's exit status doesn't change: the outside action succeeded, and a non-zero exit invites a rerun that would repeat it.
  - It is tested at the function that writes it (§6.1).

### 4.4 PostgreSQL arrays

  ```python
  query.filter(Model.tags.op('&&')(['tag1', 'tag2']))   # overlap — shares any element
  query.filter(Model.tags.op('@>')(['tag1']))           # contains all
  query.filter(~Model.tags.op('@>')(['tag1']))          # does not contain
  ```

### 4.5 Migrations

- SQL files, numbered `NNN_name.sql`.
- **Execution is an authorization point** — see §1.4.
- The approval is at execution, not the spec that contains it.

### 4.6 Write-path convergence

- Note and paired-TimeEntry creation goes through the service layer only — see `CLAUDE.md` "§ Note Write-Path Convergence" design decision for the authoritative call map.
