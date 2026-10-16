# Email Draft Service — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20261016
**Branch:** `hotfix/issue-104-daily-internal-email-service` (from `main`)
**Target release:** v1.52.1
**Originating item:** Issue #104
**Design study:** `../design/DESIGN_EMAIL_DRAFT_SERVICE.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261016 | Ray | Study Q1: branch type, with five application files touched against `hotfix/*`'s three | `hotfix/*` stands. The change has one root cause: there is no function that makes an email draft (`docs/DEVELOPMENT_STANDARDS.md` §2.2). |
| 20261016 | Ray | Study Q2: what `email save` does when no report exists | The service's error reaches `WorkmAInGroup`, which prints `Error: …` on stderr and exits 1. DR4. |
| 20261016 | Ray | Study Q3: how the service tests reach `tmp_path` | The staging directories are module constants in the service, and tests patch them. DR1. |
| 20261016 | Ray | Study Q4: the parts of #205 and #212 this issue takes over | #205's `session`-parameter removal and its two test files, and #212's `reports resend` child process, are dropped from those issues' bodies at close-out. |
| 20261016 | Spanner | The issue puts the CLI wrapper in `reports.py`. The draft logic is in `email.py`, and `reports.py` holds `reports resend`, which runs `email save` as a child process (study F2, F9). | Issue AC3 is read as `reports resend`, AC3.1. The `email` commands are covered by AC3.2. The issue's ACs need no edit. |
| 20261016 | Spanner | The directory constants are public (`REPORTS_DIR`, `EMAIL_DIR`). `email list`, `email show` and `_resolve_draft_file` also read the drafts directory. | Those commands read `email_service.EMAIL_DIR` at call time, so the path has one home. Converting them is #205's work. |
| 20261016 | Spanner | `email preview` calls the same `build_draft` and raises the same error as `email save`. | It exits 1 on no report as well, by the same mechanism Ray chose for `email save` (Q2). It has no child-process caller (study F3). |
| 20261016 | Spanner | The step descriptions in `eod_workflow.py:1351`, `eod.py:13,88` and `interface.py:227` name `email save daily_internal` as the command that does what step 4b does, which stays true. | They are unchanged. Only the dry-run line, which says the step "would run" the command, changes (DR5). The study's settled list is corrected to match. |
| 20261016 | Spanner | A failure inside the child, whether no report, a database error or a write error, used to reach step 4b as a non-zero exit, which takes the retry-or-skip branch. | Step 4b sends every exception from the draft call down that branch, so each failure is handled as before (DR5). Before, the step's outer `except Exception` caught only failures to launch the child. The step's own code now has no other call that can raise. |
| 20261016 | Spanner | `reports resend` calls the service inside its own open `session_scope()`, and must report a failed draft without failing the command. | The call runs inside `session.begin_nested()`, so a database error rolls back to the savepoint and the scope can still commit (`docs/DEVELOPMENT_STANDARDS.md` §4.1). DR6. |

---

## 1. Scope

**In scope:**

- A new module, `workmain/services/email_service.py`, holding the draft logic moved out of `email.py`, with `build_draft` and `save_draft`.
- `workmain/services/exceptions.py`: `NoReportFoundError`.
- `workmain/cli/commands/email.py`: `email preview` and `email save` call the service. The six draft helpers and the `_PROJECT_ROOT`/`_REPORTS_DIR`/`_EMAIL_DIR` constants are removed.
- `workmain/cli/commands/reports.py` `report_resend`: calls `save_draft` instead of running `email save`.
- `workmain/workflows/eod_workflow.py` `_run_email_step`: calls `save_draft` in process.
- Tests: a new `tests/test_email_service.py`, plus `tests/test_email.py`, `tests/test_email_recipients_client.py`, `tests/test_report_history.py` and `tests/test_eod_workflow.py`.

**Out of scope:**

- **Which report a draft is built from.** It is still the newest `<template>_*.md` by mtime. #192 owns choosing by date, and this spec adds no test that pins the newest-by-mtime choice (study F13).
- **The Friday step 8** (`_run_weekly_email_step`). It still runs `email save weekly_client` as a child process, as the issue says. Its code is unchanged, and one test covers the new exit code (DR4).
- **The other email commands** (`list`, `show`, `send`, `recipients`, `assign`, `unassign`). They are unchanged except for the directory constant they read. Converting them to the output module is #205's work.
- **The rest of `reports resend`.** Its output, prompt, exit codes and `TestCase` test class stay as they are, apart from the draft call. Converting it is #212's work.
- **The other twelve EOD child-process sites.**

## 2. Verified current state

Verified on `hotfix/issue-104-daily-internal-email-service` at `d5ef00c`, which is `main` `7135fae` (v1.52.0) plus the study commits.

| Claim | Evidence |
| --- | --- |
| Call sites of the draft helpers and directory constants, found by `git grep -nE "'email', 'save'\|email save\|_generate_draft\|_get_draft_recipients\|_find_latest_report\|_extract_report_date\|_build_subject\|_build_draft_content\|_EMAIL_DIR\|_REPORTS_DIR\|_run_email_step\|_run_weekly_email_step\|staging/email" -- workmain tests automation scripts config templates`, with each receiver read. | `email.py`: `_find_latest_report` (`:48`, called `:186`), `_extract_report_date` (`:56`, called `:196`), `_build_subject` (`:64`, called `:198`), `_build_draft_content` (`:79`, called `:210`), `_get_draft_recipients` (`:101`, called `:199`), `_generate_draft` (`:171`, called `:272` `email_preview` and `:305` `email_save`), `_EMAIL_DIR` (`:41`, read `:151`, `:163` `_resolve_draft_file`, `:311-313` `email_save`, `:356-358` `email_list`). `_REPORTS_DIR` (`:40`, read only by `_find_latest_report`). Tests: `test_email.py:12-17` imports `_build_subject`, `_generate_draft`, `_REPORTS_DIR`, `_EMAIL_DIR`, `email_send`; `:168-173` `_build_subject`; `:183`, `:213` `_generate_draft(…, session=db_session)`; `:26`, `:32`, `:218-226` the directory constants. `test_email_recipients_client.py:192-254` calls `_get_draft_recipients(…, session=db_session)` four times. Child-process callers of `email save`: `eod_workflow.py:1093`, `:1114` (step 4b), `:1298` (step 8), `reports.py:700`. Nothing in `automation/`, `scripts/`, `config/` or `templates/`. No `getattr` reference: `git grep -nE "getattr\([^)]*(_generate_draft\|_get_draft_recipients\|_find_latest_report)" -- workmain tests` returns no hits. |
| The draft logic. `_find_latest_report` returns `max(_REPORTS_DIR.glob(f"{template}_*.md"), key=mtime)`, or `None`. `_extract_report_date` reads `_(YYYY-MM-DD).` from the name, or falls back to `date.today()`. `_build_subject` and `_build_draft_content` are pure. `_get_draft_recipients` reads `system_state.active_client_id`, calls `EmailRepository.list_for_client(template, active_client_id)` and dedupes by email, the client-scoped role winning. Given no session, it opens its own `session_scope()`. `_generate_draft` prints a red error and returns `None` when there is no report. It prints a yellow warning, and still builds the draft, when there are no recipients. | `email.py:48-211` |
| `email save` writes `draft_path.write_text(content)`, then `chmod(0o644)`, to `_EMAIL_DIR / f"{template}_{datetime.now():%Y%m%d_%H%M%S}.txt"`. It then prints `✓ Draft saved:`, Subject, To, CC and two hints. On no report it exits 0. | `email.py:290-327` |
| `email preview` prints a heading, Subject, To (or `(no recipients assigned)`), CC, a rule and the content. | `email.py:259-287` |
| Step 4b today (`_run_email_step`): the dry run prints two lines. Otherwise it runs the child and echoes it. A timeout returns FAILED. A non-zero exit prints a warning and the recipients hint. Non-interactive, it returns FAILED with `run.failure_message("Email draft")`. Interactive, it prompts `[r]etry / [s]kip`. A retry reruns the child, and a timeout on the retry returns FAILED. Any other ending returns COMPLETED with no `message`. The outer `except Exception` returns FAILED. | `eod_workflow.py:1085-1129` |
| How the surfaces read a step's result. `workmain eod` calls `run_step(step, dry_run, today)` and prints `result.error` on FAILED. Slack calls `run_step(step, dry_run=False, target_date=…, non_interactive=True)`, posts `result.message` on COMPLETED and `result.error` on FAILED. `run_step` passes `non_interactive` only to a runner that declares it, and `_run_email_step` doesn't. | `cli/commands/eod.py:206-213`; `slack_eod.py:233-238`, `:281-327`; `eod_workflow.py:1393-1418` `run_step` |
| `_run_weekly_email_step` on a non-zero exit: FAILED with `run.failure_message("Weekly email draft")` when not interactive. Interactive, it prints `Continuing to Complete.` and returns COMPLETED. No test covers it. | `eod_workflow.py:1290-1320`; `git grep -n _run_weekly_email_step tests` → no hits |
| `report_resend` runs inside `with db.session_scope() as session:`. It reads the report, writes `staging/reports/<type>_<date>.md` (prompting if the file exists), runs `email save <type>`, echoes the child, then prints `✓ Email draft created. View with: workmain email list`, or on failure `✗ Email draft failed: …` followed by the `Retry with` hint. It writes nothing to the database. `run_workmain` and `TIMEOUT_NETWORK` are used only at `:700`. | `reports.py:659-712`; `reports.py:37`; `git grep -n "run_workmain\|TIMEOUT_NETWORK" workmain/cli/commands/reports.py` → `:37`, `:700` |
| `TestReportResend` patches `workmain.cli.commands.reports.run_workmain` in `test_resend_writes_staging_file`, `test_resend_prompts_on_existing_file` and `test_resend_reports_failed_draft_without_raising`. The last asserts exit 0, `Email draft failed` in the output, and that the staging file exists. | `tests/test_report_history.py:257-312` |
| Three step 4b tests drive the child: `test_email_timeout_returns_failed_with_value_named`, `test_email_nonzero_stderr_in_failed_message` and `test_email_retry_stderr_echoed_when_warn_and_continue`. | `tests/test_eod_workflow.py:1253-1305` |
| A `ServiceValidationError` raised in a command of the plain `email` group reaches the user as `Error: <message>` on stderr with exit 1, through the root `cli` group's `WorkmAInGroup`. Probed with `CliRunner(mix_stderr=False)`: exit `1`, stdout `''`, stderr `"Error: No report found for template 'x'\n"`. | `cli/interface.py:80`; `cli/output.py:330-344`; study F7 |
| #58's service shape: a service function takes a session and returns frozen dataclasses, and never opens, commits or rolls back a session. Service exceptions subclass `ServiceValidationError` in `services/exceptions.py`. A command test invokes the root `cli` with the service patched with `patch.object(<module>, "<name>", autospec=True)`. | `services/tasks_service.py:1-5`; `services/exceptions.py`; `tests/test_task_lifecycle.py:293`, `:463-468` |
| Baseline: 1418 tests collected on `d5ef00c`. CHANGELOG v1.52.0 records 1418 passed, 0 failed, 0 skipped. | `pytest --collect-only -q`; `CHANGELOG.md:23` |

## 3. Design rules

- **DR1 — `email_service`.** A new `workmain/services/email_service.py`. The logic in `email.py:48-140` and `:171-211` moves here with its behaviour unchanged, except that the service prints nothing and raises instead of returning `None`:

  ```python
  """
  Service layer for email drafts: builds a draft from the newest saved report
  for a template and saves it to staging/email/. Shared by the email and
  reports CLI groups and the EOD workflow. Functions take a session and return
  frozen dataclasses; none opens, commits or rolls back a session.
  """

  import re
  from dataclasses import dataclass
  from datetime import date, datetime, timedelta
  from pathlib import Path
  from typing import Optional, Tuple

  from sqlalchemy.orm import Session

  from workmain.database.repositories.email_repository import get_email_repository
  from workmain.database.repositories.system_state_repository import SystemStateRepository
  from workmain.services.exceptions import NoReportFoundError

  # Project root: workmain/services/email_service.py -> 3 parents up
  _PROJECT_ROOT = Path(__file__).parent.parent.parent
  REPORTS_DIR = _PROJECT_ROOT / "staging" / "reports"
  EMAIL_DIR = _PROJECT_ROOT / "staging" / "email"


  @dataclass(frozen=True)
  class EmailDraft:
      """An email draft built from a saved report."""

      template: str
      subject: str
      to: Tuple[str, ...]
      cc: Tuple[str, ...]
      report_date: date
      content: str


  @dataclass(frozen=True)
  class SavedDraft:
      """An email draft and the file it was saved to."""

      draft: EmailDraft
      path: Path
  ```

  - `_find_latest_report(template)`, `_extract_report_date(report_path)`, `_build_subject(template, report_date)` and `_build_draft_content(subject, to_list, cc_list, body, draft_date)` move with their bodies unchanged. `_find_latest_report` reads `REPORTS_DIR`.
  - `_draft_recipients(session: Session, template: str) -> Tuple[Tuple[str, ...], Tuple[str, ...]]` is `_get_draft_recipients`'s `_build_lists` body run on the given session: `SystemStateRepository(session).get_int('active_client_id')`, then `get_email_repository(session).list_for_client(template, active_client_id)`. It has no `session=None` mode and opens no scope.
  - `build_draft(session: Session, template: str) -> EmailDraft` does what `_generate_draft` does. Where that function prints and returns `None`, it raises `NoReportFoundError(template)`. Where it prints the recipients warning, it returns the draft with `to == cc == ()`.
  - `save_draft(session: Session, template: str) -> SavedDraft` calls `build_draft`. It then makes `EMAIL_DIR` if needed, writes the content to `EMAIL_DIR / f"{template}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"` and `chmod(0o644)`, exactly as `email_save` does today. Nothing is written when `build_draft` raises.
  - `build_draft` and `save_draft` carry Google docstrings with `Args:`, `Returns:` and `Raises:` (`docs/DEVELOPMENT_STANDARDS.md` §3.5).
  - The directories are read at call time, so a test that patches `email_service.REPORTS_DIR` and `email_service.EMAIL_DIR` redirects every read and write.
- **DR2 — `NoReportFoundError`.** Added to `workmain/services/exceptions.py`:

  ```python
  class NoReportFoundError(ServiceValidationError):
      """Raised when no saved report exists for an email draft's template."""

      def __init__(self, template: str) -> None:
          self.template = template
          super().__init__(
              f"No report found for template '{template}'. "
              f"Generate one first: workmain reports save {template}"
          )
  ```
- **DR3 — The email commands.** `email preview` and `email save` each run `with get_db().session_scope() as session:`, call `email_service.build_draft(session, template)` and `email_service.save_draft(session, template)` respectively, and close the scope before printing. When the draft has no recipients, each prints the two warning lines `_generate_draft` prints today (`email.py:201-207`), before its own output. Each then prints what it prints today, reading `draft.subject`, `draft.to`, `draft.cc` and `draft.content`, and for `save`, `saved.path.name`. Neither catches `NoReportFoundError`. The six helpers, `_PROJECT_ROOT`, `_REPORTS_DIR` and `_EMAIL_DIR` are removed from `email.py`. `email_list` and `_resolve_draft_file` read `email_service.EMAIL_DIR`. `email.py` imports `from workmain.services import email_service`, and imports nothing that no remaining code uses.
- **DR4 — `email save` exits 1 on no report.** `NoReportFoundError` reaches the root group's `WorkmAInGroup` and is printed as `Error: <message>` on stderr, exit 1 (§2). After this change the one child-process caller of `email save` is step 8. Its non-zero branch is unchanged: FAILED when not interactive, COMPLETED with `Continuing to Complete.` when interactive.
- **DR5 — Step 4b calls the service.** `eod_workflow.py` imports `from workmain.services import email_service`. `_run_email_step` (`:1085-1129`) is replaced with:

  ```python
  def _save_daily_draft() -> email_service.SavedDraft:
      """Save the daily_internal email draft in a unit of work of its own."""
      with get_db().session_scope() as session:
          return email_service.save_draft(session, 'daily_internal')


  def _run_email_step(dry_run: bool, target_date: date) -> EodStepResult:
      """Step 4b: Create email draft."""
      if dry_run:
          print("  Would save the daily_internal email draft")
          print("  Output: staging/email/daily_internal_YYYYMMDD_HHMMSS.txt")
          return EodStepResult(status=EodStepStatus.COMPLETED)

      try:
          saved = _save_daily_draft()
      except Exception as e:
          print()
          print(f"  ⚠ Email draft failed: {e}")
          if not _is_interactive():
              return EodStepResult(status=EodStepStatus.FAILED, error=f"Email draft failed: {e}")
          action = _prompt_choice("  Continue? [r]etry / [s]kip", default='s')
          if action != 'r':
              return EodStepResult(status=EodStepStatus.COMPLETED)
          try:
              saved = _save_daily_draft()
          except Exception as retry_error:
              print(f"  ⚠ Retry failed: {retry_error} — skipping email draft")
              return EodStepResult(status=EodStepStatus.COMPLETED)

      message = f"Email draft saved: {saved.path}"
      if not saved.draft.to and not saved.draft.cc:
          message += " (no recipients assigned — add with: workmain email assign)"
      print(f"  ✓ {message}")
      return EodStepResult(status=EodStepStatus.COMPLETED, message=message)
  ```

  The step-sequence description at `:1351` is unchanged. After this change, `run_workmain` is no longer called anywhere in step 4b.
- **DR6 — `reports resend` calls the service.** `reports.py:699-709`, from the comment through the `Retry with` line, is replaced with:

  ```python
              try:
                  with session.begin_nested():
                      saved = email_service.save_draft(session, report_type)
              except Exception as e:
                  console.print(f"[red]✗ Email draft failed: {e}[/red]")
                  console.print(f"[dim]Note: staging file written. Retry with: workmain email save {report_type}[/dim]")
              else:
                  console.print(f"[green]✓ Email draft created: {saved.path.name}. View with: workmain email list[/green]")
  ```

  `from workmain.utils.self_invoke import TIMEOUT_NETWORK, run_workmain` is removed and `from workmain.services import email_service` is added. Everything else in `report_resend` is unchanged.
- **DR7 — One patch target.** Every caller reaches the service as `email_service.<function>(…)` on the module, so a test patches `patch.object(email_service, "<function>", autospec=True)` once, whichever caller it drives.
- **Anything this spec does not cover:** stop and report, as `.claude/skills/session-start/SKILL.md` § Role 3 states.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `email_service` and `NoReportFoundError`, with T1–T6. The recipient tests are rewritten against the service. | `workmain/services/email_service.py`, `workmain/services/exceptions.py`, `tests/test_email_service.py`, `tests/test_email_recipients_client.py` |
| 2 | `email preview` and `email save` call the service, and the helpers are removed from `email.py`, with T7–T9 | `workmain/cli/commands/email.py`, `tests/test_email.py` |
| 3 | `reports resend` calls `save_draft`, and its tests patch the service | `workmain/cli/commands/reports.py`, `tests/test_report_history.py` |
| 4 | Step 4b calls `save_draft`, with T10–T14 replacing the three child-process tests | `workmain/workflows/eod_workflow.py`, `tests/test_eod_workflow.py` |
| 5 | Results artifact | `docs/dev/results/EMAIL_DRAFT_SERVICE_RESULTS.md` |

### Step 1 — The service

Apply DR1 and DR2. Write `tests/test_email_service.py` with T1–T6.

In `tests/test_email_recipients_client.py`, rewrite the four `TestGetDraftRecipients` tests against `email_service.build_draft`. Each test also takes `tmp_path`. In its body it patches `email_service.REPORTS_DIR` to `tmp_path` and writes `tmp_path / f"{_TMPL}_2099-01-05.md"`, keeps its current seeding, calls `email_service.build_draft(db_session, _TMPL)`, and asserts on `draft.to` and `draft.cc` exactly as it now asserts on `to_list` and `cc_list`. Rename the class `TestDraftRecipients` and update the module docstring's reference to `_get_draft_recipients()`.

At this step `email.py` still has its own helpers, so the suite stays green.

### Step 2 — The email commands

Apply DR3. In `tests/test_email.py`, delete `test_06_draft_generation` and `test_07_draft_save`, which T1, T2 and T4 replace. Delete `_TEST_REPORT_PATH`, `_TEST_REPORT_BODY`, `_create_test_report` and `_remove_test_report`, and reduce the `email` import to `email_send`. Add T7–T9 in a new class `TestEmailCommands`.

### Step 3 — `reports resend`

Apply DR6. In `TestReportResend`, replace each `patch('workmain.cli.commands.reports.run_workmain', …)` with `patch.object(email_service, "save_draft", autospec=True)`:

- `test_resend_writes_staging_file` and `test_resend_prompts_on_existing_file`: the patch's default return value. Each also asserts the mock was called once with `(ANY, 'daily_internal')`.
- `test_resend_reports_failed_draft_without_raising`: `side_effect=NoReportFoundError('daily_internal')`. Its assertions are unchanged.

Drop the `WorkmainRun` import if nothing else in the file uses it.

### Step 4 — Step 4b

Apply DR5. In `tests/test_eod_workflow.py` `TestSubprocessHardening`, delete `test_email_timeout_returns_failed_with_value_named`, `test_email_nonzero_stderr_in_failed_message` and `test_email_retry_stderr_echoed_when_warn_and_continue`. Add T10–T14 in a new class `TestEmailStepService`.

### Step 5 — Results artifact

`docs/dev/results/EMAIL_DRAFT_SERVICE_RESULTS.md`, from `docs/dev/results/_TEMPLATE_RESULTS.md`.

### Authorization points

None. This spec has no migration, GitHub deletion, merge to `main`, force-push or service run-state change.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | `workmain/services/email_service.py` exposes `build_draft` and `save_draft`. Every parameter and the return value of each is type-hinted, and each has a Google docstring with `Args:`, `Returns:` and `Raises:` (`docs/DEVELOPMENT_STANDARDS.md` §3.5). | `python -c "import inspect as i; from workmain.services import email_service as m; fs = (m.build_draft, m.save_draft); assert all(p.annotation is not i.Parameter.empty for f in fs for p in i.signature(f).parameters.values()); assert all(i.signature(f).return_annotation is not i.Signature.empty for f in fs); assert all(k in (f.__doc__ or '') for f in fs for k in ('Args:', 'Returns:', 'Raises:'))"` exits 0. |
| AC1.2 | The service never opens, commits or rolls back a session (`docs/DEVELOPMENT_STANDARDS.md` §4.1). | `git grep -nE "get_db\|session_scope\|\.commit\(\|\.rollback\(" workmain/services/email_service.py` returns no hits. |
| AC2.1 | Step 4b makes the daily draft in its own process, without launching `workmain`, through `run_step`, the entry path both `workmain eod` and the Slack EOD use. | `git grep -n "'email', 'save', 'daily_internal'" workmain/` returns no hits, and `pytest "tests/test_eod_workflow.py::TestEmailStepService::test_t10_step_saves_the_draft_in_process"` passes with `run_workmain` patched to fail if called. |
| AC3.1 | `reports resend` makes its draft by calling `email_service.save_draft`, not by running `email save`. | `git grep -nE "run_workmain\|'email', 'save'" workmain/cli/commands/reports.py` returns no hits, and `pytest tests/test_report_history.py::TestReportResend` passes with the service patched and its call asserted. |
| AC3.2 | `email save` and `email preview` hold none of the draft logic and reach it only through the service. | `git grep -nE "_find_latest_report\|_extract_report_date\|_build_subject\|_build_draft_content\|_get_draft_recipients\|_generate_draft\|list_for_client\|REPORTS_DIR" workmain/cli/` returns no hits, and `pytest tests/test_email.py::TestEmailCommands` passes. |
| AC3.3 | No caller passes a session to the draft logic for tests' sake. Every test of it goes through the service. | `git grep -nE "session=None\|session=db_session" workmain/cli/commands/email.py tests/test_email.py tests/test_email_recipients_client.py` returns no hits. |
| AC4.1 | The service is tested by calling it directly, with no child process and no installed binary, in `tmp_path` rather than the live staging tree. | `pytest tests/test_email_service.py tests/test_email_recipients_client.py::TestDraftRecipients` passes, and `git grep -nE "run_workmain\|subprocess\|_WORKMAIN_BIN\|staging" tests/test_email_service.py` returns no hits. |
| AC5.1 | Step 4b reports the draft's path in `EodStepResult.message` and says when it has no recipients. Its failures carry the error's message in `EodStepResult.error` when non-interactive. Interactively they offer retry or skip, as a non-zero exit does today. | `pytest tests/test_eod_workflow.py::TestEmailStepService` |
| AC5.2 | `email save` with no saved report prints `Error: <message>` on stderr and exits 1, through the root `workmain` group. Step 8, its one remaining child-process caller, fails on that exit when not interactive. | `pytest "tests/test_email.py::TestEmailCommands::test_t8_save_without_report_exits_1" "tests/test_eod_workflow.py::TestEmailStepService::test_t14_weekly_step_fails_on_exit_1"` |
| AC6.1 | The full suite passes, with the counts expected in §6. | `pytest` |

## 6. Test plan

- **Baseline:** 1418 passed, 0 failed, 0 skipped (`main` `7135fae`, v1.52.0). Re-run at Step 1 and record it in the results artifact.
- **Expected after:** 1429 passed, 0 failed, 0 skipped. That is the baseline, plus T1–T6 (8 collected, since T2 has 3 cases), T7–T9 (3) and T10–T14 (5), minus the 2 tests removed from `test_email.py` and the 3 removed from `test_eod_workflow.py`. The four rewritten recipient tests and the three repatched resend tests are counted in the baseline.

Every new service test takes `tmp_path`. In its body it patches `email_service.REPORTS_DIR` to `tmp_path / "reports"` and `email_service.EMAIL_DIR` to `tmp_path / "email"` with `patch.object`, and writes its report files there. A test that needs recipients takes `db_session`, seeds them with `get_email_repository(db_session)` on a sentinel template name that ends `_2099_test`, and sets or deletes `active_client_id` as `test_email_recipients_client.py` does.

| T | File::Class::test | What it shows |
| --- | --- | --- |
| T1 | `test_email_service.py::TestBuildDraft::test_t1_build_draft_assembles_the_draft` | With `daily_x_2099_test_2099-01-05.md` saved and one recipient assigned `to`, `build_draft` returns `template`, the subject `Daily Report — 05 Jan 2099`, `to == (email,)`, `cc == ()`, `report_date == date(2099, 1, 5)`, and `content` containing the `To:` and `Subject:` lines and the report body. |
| T2 | `same::test_t2_subject_follows_the_template_name`, parametrized over `daily_x_2099_test`, `weekly_x_2099_test` and `monthly_x_2099_test`, with a report dated `2099-03-04` (a Wednesday) | `Daily Report — 04 Mar 2099`, `Weekly Report — Week of 02 Mar 2099`, `Monthly Report — March 2099`. |
| T3 | `same::test_t3_build_draft_without_a_report_raises` | With no matching file, `build_draft` raises `NoReportFoundError`, whose `template` is the template and whose message contains `No report found for template '<template>'`. |
| T4 | `test_email_service.py::TestSaveDraft::test_t4_save_draft_writes_the_draft_file` | `save_draft` returns a `SavedDraft` whose `path` is in `EMAIL_DIR`, is named `<template>_<YYYYMMDD_HHMMSS>.txt`, holds `draft.content`, and has mode `0o644`. |
| T5 | `same::test_t5_save_draft_without_a_report_writes_nothing` | With no matching report, `save_draft` raises `NoReportFoundError`, and `EMAIL_DIR` holds no file. |
| T6 | `same::test_t6_save_draft_without_recipients_still_saves` | With a report and no assignments for the template, the result has `to == cc == ()`, and the file is written. |
| T7 | `test_email.py::TestEmailCommands::test_t7_save_calls_the_service` | `CliRunner(mix_stderr=False).invoke(cli, ["email", "save", "daily_internal"])`, with `save_draft` patched (DR7) to return a hand-built `SavedDraft` under `tmp_path`. The mock is called once with `(ANY, "daily_internal")`, and the exit code is 0. |
| T8 | `same::test_t8_save_without_report_exits_1` | The same invocation with `side_effect=NoReportFoundError("daily_internal")` exits 1, stderr starts `Error: No report found for template 'daily_internal'`, and stdout is empty. |
| T9 | `same::test_t9_preview_calls_the_service` | `invoke(cli, ["email", "preview", "weekly_client"])`, with `build_draft` patched to return a hand-built `EmailDraft`. The mock is called once with `(ANY, "weekly_client")`, and the exit code is 0. |
| T10 | `test_eod_workflow.py::TestEmailStepService::test_t10_step_saves_the_draft_in_process` | The directories are patched to `tmp_path`, and `daily_internal_2099-01-01.md` is written there. `eod_workflow.run_workmain` is patched with `side_effect=AssertionError` and `_is_interactive` to `False`. `run_step(<the 'email' step from get_step_sequence(0, [])>, dry_run=False, target_date=date(2099, 1, 1), non_interactive=True)` returns COMPLETED. `EMAIL_DIR` holds one file, which contains the report body, and `str(path)` is in `result.message`. |
| T11 | `same::test_t11_non_interactive_failure_carries_the_error` | `save_draft` is patched with `side_effect=NoReportFoundError("daily_internal")` and `_is_interactive` to `False`. `_run_email_step` returns FAILED, and `result.error` contains `No report found for template 'daily_internal'`. |
| T12 | `same::test_t12_interactive_retry_then_skip_completes` | The same side effect, with `_is_interactive` patched to `True` and `_prompt_choice` to `'r'`. The step returns COMPLETED, `save_draft` is called twice, and captured stdout contains `Retry failed`. |
| T13 | `same::test_t13_message_names_missing_recipients` | `save_draft` is patched to return a `SavedDraft` with `to == cc == ()`. The step returns COMPLETED, and `result.message` contains the path and `no recipients assigned`. |
| T14 | `same::test_t14_weekly_step_fails_on_exit_1` | `run_workmain` is patched to return `WorkmainRun(returncode=1, stderr="Error: No report found for template 'weekly_client'. …")` and `_is_interactive` to `False`. `_run_weekly_email_step(dry_run=False, target_date=date(2099, 1, 2))` returns FAILED, and `result.error` contains `No report found`. |

## 7. Risks and rollback

- **The Slack EOD now pauses at step 4b on no report, and at step 8 on a Friday with no weekly report.** Both used to report COMPLETED with no draft made. The pause is intended: it is the failure #192 describes, and the operator replies `continue` to go on, as at any other failed step.
- **Step 4b now runs in the daemon's process.** A failure that used to stay inside the child, such as a database error, now reaches the step as an exception. DR5 catches every exception from the draft call and handles it as a non-zero exit was handled, so the run carries on the same way.
- **Rollback.** Each step is one commit. Reverting Steps 4, 3 and 2, in that order, restores each child process. Step 1 adds code that nothing calls until Step 2.
