# Clockify Commands on the Output Module — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261023
**Branch:** `feature/issue-202-clockify-service` (from `dev`)
**Target release:** set by `/closeout`
**Originating item:** Issue #202
**Design study:** `../design/DESIGN_CLOCKIFY_COMMANDS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261023 | Ray | Branch type | `feature/*`. The change spans more than three application files: `clockify.py`, `sync.py`, the new service, `exceptions.py`, `output.py`, `time_entries_repo.py`, `time.py` and the package exports (`docs/DEVELOPMENT_STANDARDS.md` §2.2). |
| 20261023 | Ray | Study Q1: where the sync engine's logic lives | Into `workmain/services/clockify_service.py`. `workmain/integrations/clockify/sync.py` is deleted. DR2, Step 4. |
| 20261023 | Ray | Study Q2: a result that was printed and still fails | The result carries an `error`, built by the service. The command raises it after rendering. DR3, DR7. |
| 20261023 | Ray | Study Q3: the stderr report of an unrecorded outside action | `ReportView` names a field of warning lines composed by the service. The renderer prints them on stderr. DR8. |
| 20261023 | Ray | Study Q4: the EOD sync step under a Slack-started EOD | Not bundled. EOD runs from Slack only for specific tests until Slack can present a step's choice. The terminal path handles the new exits through the step's existing retry question. A line was added to #37's body, 20261023. |
| 20261023 | Ray | Study Q5: pull's `--silent` imports conflicts | The behaviour stands. WorkmAIn's entry is never changed by any answer. Only the option's help text changes. DR6. |
| 20261023 | Spanner | Where the `fmt` functions for the clockify views live | In `clockify_service.py`, the module that owns the domain (§5.6, "A view"). No clockify display module exists, and adding one for three pure functions would split the domain. |
| 20261023 | Spanner | Where the "N days ago" label is decided | `clockify_service.sync_age_label`, which returns the label the record shows. A `RecordView` leaves out a field with no value, so a `None` age would drop "Never" from the panel. The label is the decision the issue names under Decides. |
| 20261023 | Spanner | A pull's ignored tags | They join the result's warnings and print on stderr with the record failures (DR8). That is one mechanism for every warning a run produces. Today they print on stdout. |
| 20261023 | Spanner | `--silent` | `Renderer.report(view, result, quiet=True)` prints only the warnings. §4.3 has a record failure reach stderr whatever the flags, as `test_t24` asserts today. |
| 20261023 | Spanner | `sync both` renders two results | Push and pull are two service operations, each with its own result. The command renders each one with one `report` call. Splitting one result into parts is what study #201's Option B was rejected for, and this does not do that. |
| 20261023 | Spanner | `report save` and the pull apply calls open no session in the command | `report save` reads no database. A Clockify write and its record use `record_scope()` inside the service (§4.3). AC1.1 is restated for commands that read the database, and the issue's AC is corrected at close-out. |
| 20261025 | Caliper | 3, 5: S25 fails as written if both `classify` calls use `db_session`. The link is written by a separate `record_scope()` session, and a second query on `db_session` does not refresh the entry's already-loaded `clockify_id`, so the second classification still sees a conflict. DR4 avoids this in production with a fresh scope per classification. The spec does not say what S25 does between the calls. | Accepted. S25 seeds and commits as `test_clockify_sync.py::_seed_entry` does, and calls `db_session.expire_all()` before the second `classify`, which stands in for DR4's new scope. `classify` itself is unchanged: the fresh scope is the mechanism, and C16 pins it at the command. |
| 20261025 | Caliper | 7: Nothing checks F4's protection at the command, where DR4 puts it. A command that classified every entry in one scope before asking would pass AC8.3 and C8. | Accepted. C16: a pull of two entries asserts the calls alternate `classify`, `apply_pull`, `classify`, `apply_pull`, and that the two `classify` calls received different sessions. AC8.3 checks S25 and C16. Expected after rises by 1. |
| 20261025 | Caliper | 5: `plan_entry_push` reads `note` and `project` on the row `get_by_id` returns, and `get_by_id` loads neither. §4.3 says a change that adds a per-row read adds the loader. | **Not taken.** §4.3's loading rule governs "a repository method that returns rows", because a list of N rows costs up to N + 1 queries. `get_by_id` returns one row, so its two lazy loads cost a fixed two statements whatever the data, and §6.2's one-versus-five count cannot apply to it. Adding a loader would change the query for every other `get_by_id` caller, for no saving. |
| 20261025 | Caliper | 2: Step 4.4's mapping of the deleted tests leaves out `test_pull_entries_noninteractive_does_not_prompt`. | Accepted. Step 4.4 maps it to C8 (nothing is asked) and S27's `None`-answer case (the import). |
| 20261025 | Caliper | 3: DR6 gives `sync both`'s `--date` "default `date.today()`", which as an option default would be fixed when the module is imported. | Accepted. The option has no default, and the body uses `date.today()` when it is `None`, as `clockify.py:416` does today. The same holds for `sync pull`'s `--start`. |
| 20261026 | Anvil | Results deviation 1: `plan_entry_push` raises `ServiceValidationError("Time entry <id> not found")` when `get_by_id` returns `None`. DR3 was silent. | Approved, Ray 20261026. A spec gap: DR3 should have stated it. |
| 20261026 | Anvil | Results deviation 2: `classify` sets `local_id` for a `"linked"` item, and the skipped outcome carries it as `entry_id`. | Approved, Ray 20261026. The skipped row shows which local entry already holds the Clockify id. |
| 20261026 | Anvil | Results deviation 3: `format_pending`, `format_size` and `format_hours` have no test, because AC3.1 requires one for every added function and §6 pinned the count without them. | A defect in this spec: AC3.1 and §6 contradicted each other. Ray 20261026: the spec is corrected, not the criterion. S33–S35 are added, and Expected after is 1541. The deviation should have stopped implementation (`SKILL.md` § Role 3), not been recorded after it. |
| 20261026 | Anvil | Results deviation 4: the Clockify step's `run_workmain` calls are at `eod_workflow.py:1137` and `1156`, not `1144` and `1159`. | A defect in this spec's §2, which cited the lines unchecked. Corrected. |
| 20261026 | Anvil | Results deviation 5: `_seed_entry` in `tests/test_clockify_service.py` creates its project on the note's client. | Approved, Ray 20261026. A test-helper change only. |
| 20261026 | Spanner | Not in the results: `clockify.py` renames the parameters behind `--all` and `--date` to `include_synced` and `on_date`, where DR6 said options keep their names. The same rename was #201's results deviation 1. | Ray 20261026: recorded as a results deviation by Anvil, and approved on #201's reasoning. DR6 meant the flags, short forms, defaults and help text, which are unchanged. |

---

## 1. Scope

**In scope:**

- `workmain/services/clockify_service.py` (new): the result dataclasses, the functions DR3 lists, and three `fmt` functions.
- `workmain/services/exceptions.py`: `IntegrationError` and `ClockifyNotConfiguredError`.
- `workmain/services/__init__.py`: `clockify_service` imported and listed in `__all__`.
- `workmain/cli/output.py`: `ReportView.warnings_field`, `Renderer.report`'s `quiet` parameter and its warnings, and `WorkmAInGroup.invoke`'s integration branch.
- `workmain/database/repositories/time_entries_repo.py`: `get_all`, `count_unsynced`, `get_last_synced_at`.
- `workmain/cli/commands/clockify.py`: all five commands and the three group declarations.
- `workmain/cli/commands/time.py`: `time add`'s Clockify push only (lines 346-359 and the `ClockifySync` import).
- `workmain/integrations/clockify/sync.py` deleted. `workmain/integrations/clockify/__init__.py` stops exporting `ClockifySync`.
- Tests: `tests/test_clockify_service.py` (new), `tests/test_clockify.py`, `tests/test_clockify_sync.py` (deleted), `tests/test_time_entries_repo.py`, `tests/test_output.py`, `tests/test_time_add.py`, `tests/test_eod_workflow.py`, as §6 states.
- `docs/DEVELOPMENT_STANDARDS.md` §5.6.

**Out of scope:**

- The EOD sync step's behaviour under a Slack-started EOD (study F11). Placed with #36 and #37 by Ray, 20261023.
- What a pull does with a conflict under `--silent` (study F15). Only its help text changes.
- `sync push --all` re-creating synced entries in Clockify (study F16). #69 owns reconciliation.
- The rest of `time add`, and every other `time` command: #216.
- `ClockifyClient` and `ClockifyAuth`. The service calls them as they are. Their missing request timeouts are bounded by the EOD's `TIMEOUT_NETWORK` and are not this issue's.
- Which date forms a command accepts: #140.
- `failure_exit_code` and the AI commands' `sys.exit` exits. #208, #211 and #212 move them onto DR7's mechanism when they convert.
- #142's offer to condense before a push.

## 2. Verified current state

Verified on `dev` `44bc6f5`, 20261023. Study findings are cited as F-numbers and were re-read for this spec.

| Claim | Evidence |
| --- | --- |
| The five commands, their options and bodies: F1, F3. `status` and the three `sync` commands exit 0 on every failure, and `report save` exits 1 (F5, F6). | `clockify.py:40-455` |
| `ClockifySync`'s prints and prompts: F2. Its decisions: F3(c)–(g). Its conflict check runs per entry and sees earlier answers (F4). | `sync.py:68-375` |
| `ClockifyClient()` builds a `ClockifyAuth()`, which raises `ValueError("CLOCKIFY_API_KEY not found in environment. Please add it to your .env file.")` when the key is unset. Every request method raises a `requests.RequestException` subclass on failure: `raise_for_status()`, or the `HTTPError` that `create_time_entry` builds. `test_connection` returns a dict whose `workspace_id` may be `None`. `download_pdf_report` writes the file and returns `True`, or raises. | `auth.py:16-28`; `client.py:29-69`, `82-152`, `154-192`, `195-237` |
| `create_time_entry(description, start_time, duration_hours, project_id=None, tags=None)`. | `client.py:82-89` |
| `TimeEntry.entry_time` is nullable, so `datetime.combine(entry_date, None)` raises `TypeError` today for an entry with no time, and the push counts that entry as failed. | `models.py`, `class TimeEntry`; `sync.py:108` |
| `get_unsynced_entries` and `get_by_date` load `note` and `project` with `joinedload`. `get_by_id` and `get_by_clockify_id` load nothing. `mark_as_synced(entry_id, clockify_id)` sets `clockify_id` and `synced_at = datetime.now()` and returns `None` when the row is not found. | `time_entries_repo.py:120-148`, `178-202`, `494-533` |
| `parse_tags(text, apply_default=True)` returns `(clean_text, valid_full_tags, invalid_tags)`. | `tag_utils.py:354-362` |
| `notes_service.create_note(session, content, tags, source)` with `tags=None` applies the default tag. The import path is `create_note` then `time_entry_service.create_paired_time_entry(session, note, duration_hours, entry_date, entry_time, clockify_id)` in one `record_scope()`. | `sync.py:360-375` |
| `Renderer.report(view, result)` prints the empty line and returns when no section has rows. `Renderer.warning(text, stderr=False)` prints `⚠ <text>` with `soft_wrap=True`. `ReportView` has `noun`, `totals_field`, `totals`, `sections`, `empty_hint`. | `output.py:91-104`, `175-178`, `308-328` |
| `WorkmAInGroup.invoke` maps `NotImplementedError`, `ServiceValidationError`, passes Click's exceptions, and turns any other `Exception` into `Error: <type>: <message>`, exit 1. | `output.py:390-410` |
| Call sites of `ClockifySync`, `push_entries` and `pull_entries`, found by `git grep -n "ClockifySync\|push_entries\|pull_entries\|SyncConflict\|_record_clockify_link" -- workmain tests automation scripts docs ':!docs/archive'`: `clockify.py:19`, `270`, `295`, `357`, `375`, `423`, `430`, `444`; `time.py:14`, `352-353`; `workmain/integrations/clockify/__init__.py:7`, `9`; `tests/test_clockify_sync.py` (every test). Each was read and is made on `ClockifySync` or its module. No reference by name through `getattr`. | as cited |
| `time add` pushes inside its own `session_scope()`, after `session.commit()`, and prints `✓ Synced to Clockify` or `✗ Sync failed` with the first failure's error. No test takes its yes-to-sync path. | `time.py:346-359`; `tests/test_time_add.py` |
| Contract change: the clockify commands' exit codes and streams. After this spec, a Clockify API failure exits 3 with `Error:` on stderr, a missing API key exits 1, a push or pull with failed items exits 1 or 3 after printing its report, and a bad date is a usage error (exit 2, unchanged). Callers outside `tests/`, by `git grep -nE "'clockify'" -- workmain automation scripts`: `eod_workflow.py:287`, `303` (`sync push`), `1125` (`report save`, run at `1137` and `1156`). `self_invoke.py:104` is a docstring. | F11, F12 |
| `_run_sync_step` on a non-zero exit asks `y`/`r`/`s` and returns `_completed(run, ...)`, which carries stderr as its message. `_run_clockify_step` on a non-zero exit asks `r`/`s` when interactive and returns `FAILED` with `run.failure_message(...)` when not. No test drives `_run_clockify_step`. | `eod_workflow.py:281-318`, `263-276`, `1122-1170`; `tests/test_eod_workflow.py:1272-1278` |
| Contract change: `Renderer.report` gains a keyword parameter, and `ReportView` an optional field. Callers, by `git grep -n "renderer.report\|ReportView(" -- workmain tests`: the four costs commands and `tests/test_output.py`. Both additions default to today's behaviour. | `meetings.py:1706`, `notes.py:1021`, `providers.py:255`, `reports.py:779` |
| Contract change: `WorkmAInGroup.invoke` gains a branch for `IntegrationError`, a new type that nothing raises today. No other command's behaviour changes. | `git grep -n IntegrationError` (no hits) |
| The three clockify groups are plain `click.group()`. The root `cli` is a `WorkmAInGroup`. | `clockify.py:30`, `134`, `236`; `interface.py:90` |
| `DateParamType` returns a `date` for `today`, `yesterday`, or anything `date.fromisoformat` accepts, and fails otherwise. | `params.py:15-36` |
| Tests that name the group or `ClockifySync`: F14. The width sweep passed all of them at every width. | `pytest --collect-only -q`; sweep, 20261023 |

## 3. Design rules

- **DR1 — The layers.** A converted clockify command parses its options with Click types. Each read of the database is a call to `clockify_service` inside a `get_db().session_scope()` the command owns, in which the command writes nothing. The scope closes before the command asks anything, and before any Clockify call that creates something (§4.1). A read-only Clockify call, `status`'s connection check, may run inside it. A Clockify write and its record are a service call made outside any command scope. The command passes each result unchanged to the renderer through a view declared as a module constant. It imports the service as `from workmain.services import clockify_service`, so tests can patch it. It builds no rows, formats no values, imports no Rich, calls no `click.echo` or `print()`, and has no `sys.exit`. It catches nothing.

- **DR2 — Errors.** In `workmain/services/exceptions.py`:
  - `IntegrationError(Exception)`: a call to another system failed or was refused. It is not a `ServiceValidationError`.
  - `ClockifyNotConfiguredError(ServiceValidationError)`: `CLOCKIFY_API_KEY` is missing. Its message is the `ValueError`'s message.
  - In `clockify_service`, `_client()` builds `ClockifyClient()` and raises `ClockifyNotConfiguredError` from its `ValueError`. Every function that takes `client: Optional[ClockifyClient] = None` uses `_client()` when it is `None`. A `requests.RequestException` from a client call that ends the whole operation is raised as `IntegrationError(f"Clockify request failed: {e}")`, chained `from` it. Any other exception passes through unchanged.

- **DR3 — The service.** `clockify_service.py`, with frozen dataclasses of plain values. No function opens, commits or rolls back the session it is given. Each `record_scope()` it opens is its own, per §4.3. Its module docstring says so.
  - **Status.** `ClockifyStatus(workspace_id: str, user: Optional[str], email: Optional[str], pending: int, last_sync: str, next_step: Optional[str])`. `get_status(session, now: datetime, client=None) -> ClockifyStatus` calls `test_connection()` first, then `count_unsynced()` and `get_last_synced_at()`. `workspace_id` is the id, or `"—"` when it is `None`. `last_sync` is `sync_age_label(last, now)`. `next_step` is `"Run 'workmain clockify sync push' to sync pending entries"` when `pending > 0`, otherwise `None`.
  - `sync_age_label(last: Optional[datetime], now: datetime) -> str`: `"Never"` for `None`. Otherwise, with `age = now - last`: `f"{age.days} days ago"` when `age.days > 0`, `f"{age.seconds // 3600} hours ago"` when `age.seconds > 3600`, else `f"{age.seconds // 60} minutes ago"` (F3(i)).
  - **Report.** `report_range(period, start: Optional[date], end: Optional[date], today: date) -> Tuple[date, date, date]` returns start, end and the file-name date, exactly as `clockify.py:178-202` computes them (F3(j)). `SavedReport(file_name: str, period: str, start_date: date, end_date: date, path: str, size_kb: float)`. `save_report(period, start, end, today, client=None, directory: Path = CLOCKIFY_DIR) -> SavedReport`: `CLOCKIFY_DIR` is `<project root>/staging/clockify`. It creates the directory, names the file `Clockify_<file date YYYYMMDD>.pdf`, calls `download_pdf_report`, and returns the size in KB. `path` is `staging/clockify/<file_name>` when `directory` is `CLOCKIFY_DIR`, and `str(directory / file_name)` otherwise. An `OSError` passes through.
  - **Push plan.** `PushItem(entry_id: int, entry_date: date, entry_time: Optional[time], duration_hours: Decimal, description: str, project_clockify_id: Optional[str])`. `plan_push(session, on_date: Optional[date] = None, include_synced: bool = False) -> Page[PushItem]` selects as F3(a): `get_by_date(on_date)`, keeping only unsynced entries unless `include_synced`; `get_all()` when `include_synced` and no date; `get_unsynced_entries()` otherwise. `filters` is `("date", on_date)` when set, then `("all", True)` when `include_synced`. `total` is the row count. `plan_entry_push(session, entry_id) -> Page[PushItem]` returns the one entry from `get_by_id`, with `filters` `()`.
  - **Push.** `PushTotals(total, successful, failed, unrecorded)`, all `int`. `PushedEntry(entry_id: int, clockify_id: str, description: str)`. `FailedEntry(entry_id: int, description: str, error: str)`. `PushResult(filters, totals: PushTotals, pushed: Page[PushedEntry], failed: Page[FailedEntry], warnings: Tuple[str, ...], error: Optional[Exception])`. `push(plan: Page[PushItem], client=None) -> PushResult`. For each item, in order, it calls `create_time_entry(description, datetime.combine(entry_date, entry_time), duration_hours, project_id=project_clockify_id)`. Any exception there adds a `FailedEntry` with `str(e)` and the push continues (F3(d)). On success it records the link through `_record_clockify_link` (moved unchanged from `sync.py:19-24`). If that raises, the entry still counts as successful and is listed in `pushed`, `unrecorded` goes up by one, and the warning is `f"Entry {entry_id} is in Clockify as {clockify_id}, but recording it failed: {e}. The next push will create it again."` (F3(e), §4.3). `filters` is the plan's. `error` is `None` when nothing failed. Otherwise its message is `f"{failed} of {total} entries were not pushed to Clockify"`, and it is an `IntegrationError` when any failure was a `requests.RequestException`, and a `ServiceValidationError` otherwise. Every `Page`'s `filters` is `()`.
  - **Pull.** `ClockifyEntry(clockify_id: str, description: Optional[str], entry_date: date, entry_time: time, duration_hours: Decimal)`, built from the API's `timeInterval` converted to local time as `sync.py:340-347` does. `fetch_pull(start: date, end: Optional[date] = None, client=None) -> Tuple[ClockifyEntry, ...]`: `end` defaults to `start`. A `requests.RequestException` raises `IntegrationError`.
  - `ConflictRow(source: str, entry_id: object, entry_date: date, entry_time: Optional[time], duration_hours: Decimal, description: str)`. `PullItem(entry: ClockifyEntry, kind: str, local_id: Optional[int], pair: Page[ConflictRow])`. `classify(session, entry) -> PullItem`: `kind` is `"linked"` when `get_by_clockify_id` finds the entry; `"conflict"` when an unlinked local entry on `entry_date` has exactly `entry_time` (the first in `get_by_date` order, F3(f)); `"new"` otherwise. For a conflict, `local_id` is that entry's id and `pair` holds the local row (`source` `"WorkmAIn"`, the local description) then the Clockify row (`source` `"Clockify"`, `description or "N/A"`). Otherwise `pair` is `Page((), 0)`.
  - `PullAnswer(action: str, tags: Optional[str])`, `action` one of `"import"`, `"link"`, `"skip"`. `PullOutcome(clockify_id: str, description: str, result: str, entry_id: Optional[int], detail: Optional[str], warnings: Tuple[str, ...])`, `result` one of `"imported"`, `"linked"`, `"skipped"`, `"failed"`. `apply_pull(item, answer: Optional[PullAnswer]) -> PullOutcome`:
    - `kind` `"linked"`: skipped, `detail` `"already in WorkmAIn"`, whatever the answer.
    - `answer` `None` (no interaction): import with the default tag, for a conflict and a new entry alike (F3(f), F15).
    - `"skip"`: skipped, `detail` `"skipped"`.
    - `"link"`: `_record_clockify_link(local_id, clockify_id)`. If that raises: skipped, `detail` `"link not recorded"`, warning `f"Local entry {local_id} was not linked to Clockify entry {clockify_id}: {e}. The next pull will ask again."`. Otherwise linked, with `entry_id` `local_id`.
    - `"import"`: `parse_tags(answer.tags, apply_default=True)` when `tags` is not `None`. An invalid tag adds the warning `f"Invalid tags ignored for '{description}': {', '.join(invalid)}"`. It then writes the import as `sync.py:360-375` does, in its own `record_scope()`, with `description or "Imported from Clockify"` and `source='clockify'`. An exception from the write gives failed, with `detail` `str(e)`.
  - `PullTotals(total, imported, linked, skipped, failed)`, all `int`. `PulledEntry(clockify_id: str, entry_id: Optional[int], description: str, detail: Optional[str])`. `PullResult(filters, totals, imported: Page[PulledEntry], linked: Page[PulledEntry], skipped: Page[PulledEntry], failed: Page[PulledEntry], warnings, error)`. `pull_result(start, end, outcomes) -> PullResult` groups the outcomes in order, and `filters` is `(("from", start), ("to", end or start))`. `error` is `None`, or a `ServiceValidationError(f"{failed} of {total} Clockify entries were not imported")`.
  - **Formatters.** `format_pending(n: int) -> str`: `"0 entries (all synced ✓)"` at 0, otherwise `f"{n} entries"`. `format_size(kb: float) -> str`: `f"{kb:.1f} KB"`. `format_hours(h: Decimal) -> str`: `f"{h:.2f}h"`.

- **DR4 — Pull asks one entry at a time (F4).** The command calls `fetch_pull` once. Then, for each entry in order, it calls `classify` in a new `session_scope()`, closes it, asks (DR5) when interactive, and calls `apply_pull`, before it classifies the next entry. It then calls `pull_result`. So each classification sees the links and imports already applied, as today.

- **DR5 — The questions.** These are asked only when interactive (not `--silent`), and never for a `"linked"` item.
  - A conflict: `renderer.collection(CONFLICT, item.pair)`, then `click.prompt("Link (1), keep both (2) or skip (3)", type=click.Choice(["1", "2", "3"]))`. Click asks again for any other answer. `1` is `"link"`, `2` is `"import"` and `3` is `"skip"`, through a module constant in `clockify.py`.
  - An import (a new entry, or a conflict answered `2`): `click.prompt(f"Tags for '{description}' (#ilo #cf, blank for internal-only)", default="", show_default=False)`, where `description` is `entry.description or "Imported from Clockify"`.
  - Without interaction, `apply_pull(item, None)`.

- **DR6 — The commands.**

  | Command | Calls | Renders | Options |
  | --- | --- | --- | --- |
  | `status` | `get_status(session, datetime.now())` in a scope | `renderer.record(STATUS, status)` | — |
  | `report save PERIOD` | `save_report(period, start, end, date.today())`, no scope | `renderer.record(REPORT_SAVED, saved)` | `--start/-b`, `--end/-e` take `DateParamType()` |
  | `sync push` | `plan_push(session, date, all)` in a scope, then `push(plan)` | `renderer.report(PUSH, result, quiet=silent)`, then `raise result.error` when set | `--date/-d` takes `DateParamType()` |
  | `sync pull` | DR4 | `renderer.report(PULL, result, quiet=silent)`, then `raise result.error` when set | `--start/-b`, `--end/-e` take `DateParamType()`. `--start` has no default, and the body uses `date.today()` when it is `None`, as today. `--silent` help: `Silent mode (no prompts; conflicts are imported as separate entries)` |
  | `sync both` | `plan_push(session, on_date=d)` in a scope, `push(plan)`, then DR4 interactive for `d`, `d` | `report(PUSH, push_result)`, then `report(PULL, pull_result)`, then `raise push_result.error or pull_result.error` when either is set | `--date/-d` takes `DateParamType()`, with no default. `d` is the option's value, or `date.today()` in the body when it is `None`, as today |

  - Every other option keeps its name, short form, default and help text. Every docstring stays, except that `sync both`'s and `status`'s describe what they now print. The groups are declared `@click.group(cls=WorkmAInGroup)`. Each command takes `renderer` through `@pass_renderer`.
  - Views, as module constants in `clockify.py`:
    - `STATUS = RecordView("Clockify", "workspace_id", "user", (Field("email", "Email"), Field("pending", "Pending sync", fmt=clockify_service.format_pending), Field("last_sync", "Last sync"), Field("next_step", "Next step")))`.
    - `REPORT_SAVED = RecordView("Clockify report", "file_name", "period", (Field("start_date", "From"), Field("end_date", "To"), Field("path", "Saved to"), Field("size_kb", "Size", fmt=clockify_service.format_size)))`.
    - `PUSH = ReportView("time entries to push", "totals", (Field("total", "Total"), Field("successful", "Successful"), Field("failed", "Failed"), Field("unrecorded", "Not recorded locally")), (Section("pushed", CollectionView("pushed entries", (Column("entry_id", "ID", "key"), Column("clockify_id", "Clockify ID", "key"), Column("description", "Description", "text")))), Section("failed", CollectionView("failed entries", (Column("entry_id", "ID", "key"), Column("description", "Description", "text"), Column("error", "Error", "text"))))), warnings_field="warnings")`.
    - `PULL = ReportView("Clockify entries", "totals", (Field("total", "Total from Clockify"), Field("imported", "Imported"), Field("linked", "Linked"), Field("skipped", "Skipped"), Field("failed", "Failed")), (Section("imported", ...), Section("linked", ...), Section("skipped", ...), Section("failed", ...)), warnings_field="warnings")`. Each section's view is `CollectionView(<"imported entries" / "linked entries" / "skipped entries" / "failed entries">, (Column("clockify_id", "Clockify ID", "key"), Column("entry_id", "ID", "key"), Column("description", "Description", "text"), Column("detail", <"Reason" or "Error">, "text")))`. The imported and linked views omit the detail column.
    - `CONFLICT = CollectionView("conflicting entries", (Column("source", "Source", "key"), Column("entry_id", "ID", "key"), Column("entry_date", "Date", "key"), Column("entry_time", "Time", "key"), Column("duration_hours", "Hours", "key", fmt=clockify_service.format_hours), Column("description", "Description", "text")))`.

- **DR7 — The integration exit.** `WorkmAInGroup.invoke` gains a branch, after `ServiceValidationError`, that raises an `IntegrationError` as `_IntegrationFailure(str(e))`, chained `from` it. `_IntegrationFailure` is a `click.ClickException` subclass with `exit_code = 3`, so Click prints `Error: <message>` on stderr. A raised `result.error` reaches the same branches: exit 3 for an `IntegrationError`, exit 1 for a `ServiceValidationError`.

- **DR8 — Warnings and quiet.** `ReportView` gains `warnings_field: Optional[str] = None`, after `empty_hint`. `Renderer.report(view, result, quiet: bool = False)`. With `quiet`, it prints nothing on stdout. Otherwise it prints what it prints today. Then, in both cases, when `warnings_field` is set, it prints each string of that field through `self.warning(text, stderr=True)`, in order. That is also the case when every section is empty.

- **DR9 — `time add`.** After its existing `session.commit()` and confirm, `time add` calls `clockify_service.push(clockify_service.plan_entry_push(session, entry.id))`. It prints each warning with `click.echo(f"⚠ {line}", err=True)`, then `✓ Synced to Clockify` when `totals.successful > 0`, otherwise `✗ Sync failed` and, when there is a failed row, `Error: <its error>` indented two spaces, as today. It does not raise `result.error`: its exit code is unchanged and #216 converts it. It imports `clockify_service` and no longer imports `ClockifySync`.

- **DR10 — Repository methods** (§4.3), in `TimeEntriesRepository`:
  - `get_all() -> List[TimeEntry]`: every entry, with `joinedload` of `note` and `project`, ordered by `entry_date`, `entry_time`.
  - `count_unsynced() -> int`: the count of entries whose `clockify_id` is `NULL`.
  - `get_last_synced_at() -> Optional[datetime]`: `max(synced_at)`.

- **DR11 — Not covered here.** Anything this spec doesn't settle stops at the current step (`.claude/skills/session-start/SKILL.md` § Role 3).

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 0 | Baseline recorded | — |
| 1 | Repository methods and their tests | `workmain/database/repositories/time_entries_repo.py`, `tests/test_time_entries_repo.py` |
| 2 | Errors, the integration exit, report warnings and quiet, with renderer and wiring tests | `workmain/services/exceptions.py`, `workmain/cli/output.py`, `tests/test_output.py` |
| 3 | The service, its export and its tests | `workmain/services/clockify_service.py`, `workmain/services/__init__.py`, `tests/test_clockify_service.py` |
| 4 | The commands and `time add` on the service. `sync.py` removed, with command and `time add` tests | `workmain/cli/commands/clockify.py`, `workmain/cli/commands/time.py`, `workmain/integrations/clockify/__init__.py`, `workmain/integrations/clockify/sync.py`, `tests/test_clockify.py`, `tests/test_clockify_sync.py`, `tests/test_time_add.py` |
| 5 | EOD call-site tests | `tests/test_eod_workflow.py` |
| 6 | Standards | `docs/DEVELOPMENT_STANDARDS.md` |
| 7 | Results artifact | `docs/dev/results/CLOCKIFY_COMMANDS_RESULTS.md` |

### Step 0 — baseline

If `dev` has moved past `44bc6f5`, merge it into this branch (`git merge dev`) and re-check §2's citations. Run `pytest` and record the counts in the results artifact.

### Step 1 — repository

`time_entries_repo.py`: DR10. `tests/test_time_entries_repo.py`: G1 in `TestTimeEntriesRepoLoading`, and G2–G3 in a new `TestTimeEntriesRepoSyncState` (§6).

### Step 2 — renderer and errors

1. `exceptions.py`: DR2's two classes.
2. `output.py`: DR7 and DR8. The module docstring names the integration branch and the report's warnings.
3. `tests/test_output.py`: O1–O3 in `TestReport`, and W1–W2 in `TestWiring` (§6).

### Step 3 — service

1. `clockify_service.py` per DR2 and DR3. `_record_clockify_link` is copied from `sync.py` in this step and moved in Step 4, so every step stays green.
2. `services/__init__.py`: import `clockify_service` and list it in `__all__`, alphabetically.
3. `tests/test_clockify_service.py`: S1–S35 (§6).

### Step 4 — commands

1. `clockify.py`: DR1, DR4, DR5 and DR6. It removes the imports of `rich`, `ClockifyClient`, `ClockifyAuth`, `ClockifySync`, `TimeEntriesRepository`, `calendar`, `timedelta` and `Path` that it no longer uses, and `_PROJECT_ROOT` and `_CLOCKIFY_DIR`, whose job is now `clockify_service.CLOCKIFY_DIR`.
2. `time.py`: DR9.
3. Delete `workmain/integrations/clockify/sync.py`. In `workmain/integrations/clockify/__init__.py`, remove the `ClockifySync` import and its `__all__` entry, and the docstring's mention of sync, if any.
4. Delete `tests/test_clockify_sync.py`. Every behaviour it tested has a service test in Step 3: the import tests are S27, `t20`–`t22` are S17, S26 and S28, `t24` is S18 with O1–O3, `TestPushLoading` is S19, and `test_pull_entries_noninteractive_does_not_prompt` is C8 (nothing is asked) with S27's `None`-answer case (the import).
5. `tests/test_clockify.py`: replace `TestReportSaveExitCode` with C1–C16 in `TestClockifyCommands`, and update the module docstring.
6. `tests/test_time_add.py`: T1–T2 in `TestTimeAddUnitOfWork` (§6).

### Step 5 — EOD call sites

`tests/test_eod_workflow.py`: E1–E3 (§6). No change to `eod_workflow.py`.

### Step 6 — standards

`docs/DEVELOPMENT_STANDARDS.md` §5.6:

1. In the bullet beginning "**A command converted to the renderer**", after "so a `ServiceValidationError` reaches the user as Click's `Error: <message>` on stderr with exit 1.", insert: "A service raises `IntegrationError` (`workmain/services/exceptions.py`) when a call to another system fails or is refused, and `WorkmAInGroup` reports it as `Error: <message>` on stderr with exit 3. A setting that is missing, such as an API key, is a `ServiceValidationError`, exit 1. A command whose service calls another system reads what it needs in its scope, closes it, and then calls the service's function for the outside action, which records the action in a scope of its own (§4.3). A result that can partly fail carries an `error`, which the service builds: the command renders the result, then raises the error when it is set."
2. In the bullet beginning "**A view.**", replace "and an optional hint." at the end of the `ReportView` sentence with: "an optional hint, and an optional field holding the result's warnings."
3. In the bullet beginning "**A report**", append: "It then prints each of the result's warnings as a `⚠` line on stderr, whether or not any section has rows. Called with `quiet=True`, for a command's `--silent`, it prints only the warnings."
4. In the exit-code list, replace "`3` integration error (API, auth)." with "`3` integration error (API, auth), raised as `IntegrationError` (the converted-command bullet above)." The nested bullet under it is unchanged.

### Step 7 — results artifact

`docs/dev/results/CLOCKIFY_COMMANDS_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`. It holds the §5 table, and test counts in the form `docs/DEVELOPMENT_STANDARDS.md` §6 states. Its §5 holds four tables:

- each command, with the service functions it calls and the renderer calls it makes (AC1.2);
- each service function, with its tests (AC3.1);
- each command, with its command tests (AC4.1);
- each EOD call site in §2's contract row, with the exit codes the command now produces there, the step's policy for each, and the test that shows it (AC7.1).

### Authorization points

None. This spec runs no migration, deletes no GitHub object, merges nothing to `main`, force-pushes nothing and changes no service's run state.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | No clockify command opens a session other than through `session_scope()`, constructs a repository or queries. | `git grep -nE 'get_session\(\|Repository\(\|_repository\(\|\.query\(' workmain/cli/commands/clockify.py` returns no hits. |
| AC1.2 | Each clockify command that reads the database does so through a `clockify_service` function, inside a `session_scope()` it owns and closes before any question or Clockify write, and hands every result to the renderer unchanged. | A stated reading by Ray of the results artifact's table of each command, the service functions it calls and the renderer calls it makes, and `pytest tests/test_clockify.py::TestClockifyCommands` passes. |
| AC2.1 | Nothing in the clockify command file or the clockify service prints except through `workmain/cli/output.py`, and the sync engine that printed is gone. | `git grep -nE '\brich\b\|click\.echo\|console\.\|\bprint\(' workmain/cli/commands/clockify.py workmain/services/clockify_service.py` returns no hits, and `test ! -e workmain/integrations/clockify/sync.py`. |
| AC3.1 | Every service function this issue adds is tested at the service, by a test that calls it directly and asserts on its result. | A stated reading by Ray of the results artifact's table pairing each service function with its tests, and `pytest tests/test_clockify_service.py` passes. |
| AC4.1 | Every clockify command has a command test that runs it through `CliRunner` with its service functions patched and a mock renderer, asserting the service's arguments, that the renderer received the declared view and the service's result, and the exit code. | A stated reading by Ray of the results artifact's table pairing each command with its command tests, and `pytest tests/test_clockify.py::TestClockifyCommands` passes. |
| AC5.1 | No clockify test depends on terminal width. | `for w in $(seq 20 2 80) 100 120 200; do COLUMNS=$w pytest -q tests/test_clockify.py tests/test_clockify_service.py tests/test_time_entries_repo.py tests/test_output.py tests/test_time_add.py "tests/test_eod_workflow.py::TestClockifyCallSites"; done` reports 0 failed at every width. |
| AC6.1 | The full suite passes. | `pytest`, with the counts expected in §6. |
| AC7.1 | Each EOD step that runs a clockify command as a child process handles every exit code and output stream the converted command now produces, as that step's existing policy requires, through the `run_workmain` entry path. The `CliRunner` path is AC4.1's. | `pytest tests/test_eod_workflow.py::TestClockifyCallSites`, and a stated reading by Ray of the results artifact's call-site table. |
| AC8.1 | A Clockify API failure in a clockify command exits 3 with one `Error:` line on stderr and no traceback, a missing API key exits 1 the same way, and a push or pull that partly failed prints its report and then exits non-zero. | `pytest tests/test_output.py::TestWiring tests/test_clockify.py::TestClockifyCommands` |
| AC8.2 | A report's warnings reach stderr, one line each, whether or not it has rows and under `quiet`, and nothing else is printed under `quiet`. | `pytest tests/test_output.py::TestReport` |
| AC8.3 | A pull's conflict question sees the links and imports already applied in the same run: the command classifies each entry in a new scope, after the previous entry's answer is applied. | `pytest "tests/test_clockify_service.py::TestPull::test_s25_classification_sees_an_earlier_link" "tests/test_clockify.py::TestClockifyCommands::test_c16_pull_classifies_each_entry_after_the_last_is_applied"` |
| AC9.1 | A command author knows from `docs/DEVELOPMENT_STANDARDS.md` §5.6 how an integration error, a partly failed result, an outside call and a report's warnings are written. | A stated reading by Ray of §5.6 for exactly that. |

## 6. Test plan

- **Baseline:** the counts Step 0 records. On this branch at `44bc6f5`, 20261023: 1472 passed, 0 failed, 0 skipped.
- **Expected after:** the baseline, less 16 removed tests, plus 85 new, as collected:
  - **Removed:** the 3 tests of `tests/test_clockify.py` and the 13 of `tests/test_clockify_sync.py`.
  - **New:** service 51 (S2 collects 5, S3 2, S7 6, S27 6), repository 3, renderer and wiring 5, command 21 (C5 collects 4, C14 3), EOD 3, `time add` 2.
  - On the baseline above: 1541 passed, 0 failed, 0 skipped.

Test method names are the spec's where an AC cites the node. Anvil names the rest.

**`tests/test_clockify_service.py`.** Every database test takes `db_session` and seeds on 2099 sentinel dates. The client is a `MagicMock` passed as `client=`. A test that needs `_record_clockify_link` real spies `DatabaseConnection.record_scope` as `test_clockify_sync.py` does, and the "later failed scope" check is the one `test_clockify_sync.py::_fail_a_later_scope` makes.

| T | Class | What it shows |
| --- | --- | --- |
| S1 | `TestStatus` | `get_status` with `test_connection` returning a user: `workspace_id`, `user` and `email` are its values, `pending` is the live `count_unsynced()` measured before the call, and `last_sync` is `sync_age_label` of the live latest `synced_at`. |
| S2 | `TestStatus` | `sync_age_label`, parametrized: 2 days → `2 days ago`; 5 hours → `5 hours ago`; exactly 3600 seconds → `60 minutes ago`; 90 seconds → `1 minutes ago`; `None` → `Never`. |
| S3 | `TestStatus` | Parametrized over `count_unsynced` patched to 0 and to 3: `next_step` is `None`, and then the push hint. |
| S4 | `TestStatus` | `test_connection` raising `requests.HTTPError("401 ...")`: `IntegrationError`, with `401` in its message. |
| S5 | `TestStatus` | `clockify_service.ClockifyClient` patched to raise `ValueError("CLOCKIFY_API_KEY not found ...")`, and no `client`: `ClockifyNotConfiguredError` with that message, which is a `ServiceValidationError`. |
| S6 | `TestStatus` | `workspace_id` `None` from `test_connection`: `"—"`. |
| S7 | `TestReportSave` | `report_range`, parametrized over today `2026-10-21` (a Wednesday): daily with no dates; daily with a start; weekly with no dates (Monday 19th to Friday 23rd, file date 23rd); weekly with both; monthly with no dates (1st to 31st); monthly with a start and no end (end is the 31st of October). |
| S8 | `TestReportSave` | `save_report("daily", ...)` with `directory=tmp_path` and `download_pdf_report` writing 2048 bytes: `file_name` `Clockify_<date>.pdf`, the file exists, `size_kb` 2.0, and `path` is `str(tmp_path / file_name)`. |
| S9 | `TestReportSave` | `download_pdf_report` raising `requests.ConnectionError`: `IntegrationError`. |
| S10 | `TestPush` | `plan_push(on_date=d)`, with one unsynced and one synced entry on `d`, the unsynced one with a project that has a `clockify_project_id`: one item, carrying its note's content, date, time, hours and the project's Clockify id. `filters` is `(("date", d),)`. |
| S11 | `TestPush` | `plan_push(on_date=d, include_synced=True)`: both, and `("all", True)` in `filters`. |
| S12 | `TestPush` | `plan_push()`: the unsynced sentinel entry is among the items, and the synced one is not. `filters` is `()`. |
| S13 | `TestPush` | `plan_push(include_synced=True)`: both sentinel entries are among the items. |
| S14 | `TestPush` | `plan_entry_push(session, id)`: one item for that entry. |
| S15 | `TestPush` | `push` of two items, the second raising `requests.HTTPError`: totals `(2, 1, 1, 0)`, one `PushedEntry`, one `FailedEntry` with the error text, and `error` an `IntegrationError` reading `1 of 2 entries were not pushed to Clockify`. |
| S16 | `TestPush` | `push` of an item whose `entry_time` is `None`: failed, and `error` is a `ServiceValidationError`, not an `IntegrationError`. |
| S17 | `TestPush` | `push` that succeeds: `error` `None`, `record_scope` was used, and the link survives a later failed scope (was `t20`). |
| S18 | `TestPush` | `push` with `mark_as_synced` patched to return `None`: successful 1, unrecorded 1, the entry in `pushed`, one warning naming the entry id and the Clockify id and ending `The next push will create it again.`, and `error` `None` (was `t24`). |
| S19 | `TestPush` | Two tests, from `TestPushLoading`: the statements `plan_push()` issues, with `_record_clockify_link` patched out, do not grow from one seeded entry to five; and `push` sends each item's project Clockify id, or `None`. |
| S20 | `TestPull` | `fetch_pull` maps an API entry (UTC `timeInterval`, 1.5 hours) to a `ClockifyEntry` with local date and time, `Decimal` hours and the raw description, and `end` defaults to `start`. |
| S21 | `TestPull` | `get_time_entries` raising `requests.HTTPError`: `IntegrationError`. |
| S22 | `TestPull` | `classify` of an entry whose id a local entry holds: `"linked"`. |
| S23 | `TestPull` | `classify` against an unlinked local entry at the same date and time: `"conflict"`, `local_id` that entry, and `pair` the WorkmAIn row then the Clockify row. |
| S24 | `TestPull` | `classify` with no match: `"new"`, and `pair` empty. |
| S25 | `TestPull` | `test_s25_classification_sees_an_earlier_link`: two Clockify entries at the time of one unlinked local entry, seeded and committed as `test_clockify_sync.py::_seed_entry` does. The first classifies as a conflict. After `apply_pull(first, PullAnswer("link", None))` and `db_session.expire_all()`, which stands in for DR4's new scope, the second classifies as `"new"`. |
| S26 | `TestPull` | `apply_pull` with `"link"`: linked, through `record_scope`, and the link survives a later failed scope (was `t21`). |
| S27 | `TestPull` | Six tests, from `TestImportClockifyEntry`, through `apply_pull` with `"import"`: the active client is stamped; `created_at` is not backdated; tags `"#cf"` give `['carry-forward']`; tags `""` give `['internal-only']`; answer `None` gives `['internal-only']`; `"#cf"` creates an active task. |
| S28 | `TestPull` | An import survives a later failed scope (was `t22`). |
| S29 | `TestPull` | An import whose write raises: failed, with the error as `detail`, and `pull_result` gives an `error` that is a `ServiceValidationError` reading `1 of 1 Clockify entries were not imported`. |
| S30 | `TestPull` | A link whose record raises: skipped, `detail` `link not recorded`, and a warning ending `The next pull will ask again.` |
| S31 | `TestPull` | `pull_result` over one outcome of each result: the totals, each section's rows in order, `filters` `(("from", d), ("to", d))` with `end` `None`, and `error` `None` with no failure. |
| S32 | `TestPull` | Tags `"#nosuchtag"`: imported, with a warning naming the tag. |
| S33 | `TestFormatters` | `format_pending(0) == "0 entries (all synced ✓)"` and `format_pending(3) == "3 entries"`. |
| S34 | `TestFormatters` | `format_size(2.0) == "2.0 KB"`. |
| S35 | `TestFormatters` | `format_hours(Decimal("1.5")) == "1.50h"`. |

**`tests/test_time_entries_repo.py`**

| T | Class | What it shows |
| --- | --- | --- |
| G1 | `TestTimeEntriesRepoLoading` | `get_all`'s statements, with note and project read on each row, are equal after seeding one row and after seeding four more (§6.2, a method with no filter). |
| G2 | `TestTimeEntriesRepoSyncState` | `count_unsynced` rises by 2 when two unsynced entries are seeded, and not when a synced one is. |
| G3 | `TestTimeEntriesRepoSyncState` | `get_last_synced_at` returns a seeded `synced_at` of `2099-01-01 12:00`. |

**`tests/test_output.py`.** Renderers are built over `Console(file=io.StringIO(), width=N)` for both consoles.

| T | Class | What it shows |
| --- | --- | --- |
| O1 | `TestReport` | A view with `warnings_field` and a result with two warnings and rows: stdout is what it was without the field, and stderr holds `⚠ <first>` then `⚠ <second>`, each one line at width 20. |
| O2 | `TestReport` | Every section empty and one warning: stdout holds the empty line and hint, and stderr the warning. |
| O3 | `TestReport` | `quiet=True` with rows and one warning: stdout is empty, and stderr holds the warning. |
| W1 | `TestWiring` | A `WorkmAInGroup` command raising `IntegrationError("Clockify request failed: 401")`: exit 3, `result.stderr == "Error: Clockify request failed: 401\n"`, and no `Traceback` in either stream. |
| W2 | `TestWiring` | The same command in a plain `click.group()` under a `WorkmAInGroup` root: exit 3, the same stderr. |

**`tests/test_clockify.py::TestClockifyCommands`.** Each test runs `CliRunner(mix_stderr=False).invoke(clockify, args, obj=renderer)`, with `renderer` a `Mock(spec=Renderer)` and each service function it reaches patched with `patch.object(clockify_service, "<name>", autospec=True)`.

| T | What it shows |
| --- | --- |
| C1 | `status`: `get_status` received a session and a `datetime`. `renderer.record` was called once, with `STATUS` and its return value. Exit 0. |
| C2 | `status` with `get_status` raising `IntegrationError("x")`: exit 3, `Error: x` on stderr, and `record` not called. |
| C3 | `report save weekly -b 2099-01-05 -e 2099-01-09`: `save_report` received `"weekly"`, `date(2099, 1, 5)`, `date(2099, 1, 9)` and a `date`. `record` was called with `REPORT_SAVED` and its return value. |
| C4 | `report save` with `save_report` raising `ClockifyNotConfiguredError("k")`: exit 1, `Error: k` on stderr. |
| C5 | `sync push`, parametrized over no options, `-d 2099-01-05`, `--all`, and `-d 2099-01-05 --all`: `plan_push` received `on_date` and `include_synced` to match, and `push` received its return value. `report` was called with `PUSH`, `push`'s return value and `quiet=False`. Exit 0. |
| C6 | `sync push -q`: `report` called with `quiet=True`. |
| C7 | `sync push` with a result whose `error` is an `IntegrationError("1 of 2 ...")`: `report` was called first, then exit 3 with `Error: 1 of 2 ...` on stderr. |
| C8 | `sync pull -q -b 2099-01-05`: `fetch_pull` received `date(2099, 1, 5)` and `None`. With two entries, `classify` was called twice, `apply_pull` was called with `answer` `None` each time, nothing was prompted, and `report` was called with `PULL`, `pull_result`'s return value and `quiet=True`. |
| C9 | `sync pull` with `classify` returning a conflict and input `1\n`: `renderer.collection` was called with `CONFLICT` and the item's `pair`, and `apply_pull` received `PullAnswer("link", None)`. |
| C10 | `sync pull` with `classify` returning a new entry and input `#cf\n`: `apply_pull` received `PullAnswer("import", "#cf")`. |
| C11 | `sync pull` with a conflict and input `4\n2\n\n`: Click asks again, then `apply_pull` received `PullAnswer("import", "")`. |
| C12 | `sync both -d 2099-01-05`: `plan_push` received `on_date=date(2099, 1, 5)`, `fetch_pull` that date, and `report` was called with `PUSH`, then with `PULL`. |
| C13 | `sync both` with a push result whose `error` is set and a pull result whose `error` is `None`: both reports, then the push error's exit and line. |
| C14 | Parametrized over `clockify`, `clockify_report` and `clockify_sync`: each is a `WorkmAInGroup`. |
| C15 | `sync push -d 2026-13-01`: exit 2, `Error:` on stderr, and `plan_push` not called. |
| C16 | `test_c16_pull_classifies_each_entry_after_the_last_is_applied`: `sync pull -q` with `fetch_pull` returning two entries, and `classify` and `apply_pull` attached to one parent `Mock` so their order is recorded: the calls are `classify`, `apply_pull`, `classify`, `apply_pull`, and the session the second `classify` received is not the first's. |

**`tests/test_eod_workflow.py::TestClockifyCallSites`.** `run_workmain` is patched to return a `WorkmainRun`.

| T | What it shows |
| --- | --- |
| E1 | `_run_sync_step` with `returncode=3`, `stderr="Error: 1 of 2 entries were not pushed to Clockify\n"`, and `_prompt_choice` returning `y`: `COMPLETED`, with the `Error:` line in `message`, and `run_workmain` called once. Exit 1 on this site is already covered by `test_sync_retry_nonzero_policy_unchanged_continues`. |
| E2 | `_run_clockify_step` with `returncode=3`, interactive, and `_prompt_choice` returning `s`: `COMPLETED`. |
| E3 | `_run_clockify_step` with `returncode=3`, `stderr="Error: Clockify request failed: 401\n"`, and `_is_interactive` false: `FAILED`, with `exit code 3` and the `Error:` line in `error`. |

**`tests/test_time_add.py::TestTimeAddUnitOfWork`**

| T | What it shows |
| --- | --- |
| T1 | `time add "<sentinel>" 1h -T 0900` with input `y\n`, and `clockify_service.push` patched to return one pushed entry: `push` received a plan of one item whose `entry_id` is the new entry's. `✓ Synced to Clockify` is in the output, and the exit is 0. |
| T2 | The same, with `push` returning one failed entry with error `boom`: `✗ Sync failed` and `Error: boom` in the output, and the exit is 0. |

## 7. Risks and rollback

- **Exit codes change for the EOD.** `sync push` now exits non-zero when entries fail. On the terminal path the sync step asks to retry, as it already does for any non-zero exit (E1). `report save` exits 3 instead of 1, which the Clockify step treats as it does any non-zero exit (E2, E3). An EOD started from Slack takes the sync step's default "yes", which is out of scope (Decision Log, Q4).
- **Output wording changes.** `status` is a panel titled `Clockify #<workspace id> — <user>`, and the workspace id is printed whole. The push's per-entry progress lines become the report's sections, printed when the push ends. The "Staged for Drive upload (Phase 7)" line and the `Testing Clockify Connection...` lines go. A pull's ignored-tag notice moves to stderr. What is pushed, imported, linked or skipped does not change: S10–S32 pin it.
- **`sync.py` is deleted.** Every caller is in §2's call-site row and changes in Step 4. Rollback: revert Step 4. Steps 1–3 add code and tests only, and revert alone.
- **`time add`** keeps its own lines and exit code. A missing API key now reaches the user as `Error: CLOCKIFY_API_KEY ...` with exit 1, where today it is `Error: ValueError: ...` with exit 1. The entry is already committed in both cases.
- **Live configuration.** No test reads `config/ai_settings.json`, and none calls Clockify: every client is a mock.
- Each step is one commit and reverts alone. Step 4 depends on Steps 1–3.
