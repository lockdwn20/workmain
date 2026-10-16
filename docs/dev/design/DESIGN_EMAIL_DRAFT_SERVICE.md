# Email Draft Service — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261016
**Originating item:** Issue #104

---

## 1. Purpose

Issue #104 asks for the email draft pipeline to become a function in `workmain/services/` that the EOD workflow imports and calls, replacing step 4b's `workmain email save daily_internal` child process, with the CLI reduced to a wrapper over the same function. The issue asks to be revised against #58's final design, which set the service shape (a function that takes a session and returns a frozen dataclass) and the error path (`ServiceValidationError` through `WorkmAInGroup`). This study measures the pipeline and its callers on `main` `7135fae` and settles what the spec has to decide.

## 2. Scope of the read

Read: `workmain/cli/commands/email.py` (the whole pipeline and every command that uses it), `workmain/cli/commands/reports.py` `report_resend`, `workmain/workflows/eod_workflow.py` (`_run_email_step`, `_run_weekly_email_step`, `_build_step_sequence`, `run_step`, `_is_interactive`, `_echo_workmain`), `workmain/integrations/slack/slack_eod.py` (`_advance_step`, `_handle_step_result`), `workmain/cli/commands/eod.py` (the step loop), `workmain/cli/output.py` `WorkmAInGroup`, `workmain/cli/interface.py`, `workmain/services/tasks_service.py`, `results.py` and `exceptions.py`, `workmain/ai/report_generator.py` (where report staging files are written), and the tests that reach these: `tests/test_email.py`, `tests/test_email_recipients_client.py`, `tests/test_eod_workflow.py`, `tests/test_report_history.py`, `tests/test_eod_pipeline.py`.

Call-site search, whole repository: `git grep -nE "'email', 'save'|email save|_generate_draft|_get_draft_recipients|_find_latest_report|_extract_report_date|_build_subject|_build_draft_content|_EMAIL_DIR|_REPORTS_DIR|_run_email_step|_run_weekly_email_step|staging/email" -- workmain tests automation scripts config templates`. Each hit's receiver was read.

Not read: the other email commands (`list`, `show`, `recipients`, `assign`) beyond their use of `_EMAIL_DIR` — their conversion is #205. The other twelve EOD subprocess sites.

Open issues read for overlap: #192, #205, #212, #115.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | The issue's line references are stale. #94 routed every self-invocation through `run_workmain`. The step now runs `run_workmain(['email', 'save', 'daily_internal'], timeout=TIMEOUT_NETWORK)` and its retry, and the comment the issue quotes reads "Invoke email pipeline via the workmain binary (no get_email_generator() API exists)" in `report_resend`. | `eod_workflow.py:1093`, `:1113-1115` `_run_email_step`; `reports.py:699-700` `report_resend`; `utils/self_invoke.py:100` `run_workmain` | Low |
| F2 | The generation logic is in `email.py`, not `reports.py`. `_generate_draft` finds the newest `staging/reports/<template>_*.md` by mtime, takes its date from the file name, builds the subject from the template name, resolves recipients and builds the draft text. `email_save` writes it to `staging/email/<template>_<YYYYMMDD_HHMMSS>.txt`. `email preview` calls the same `_generate_draft`. The pipeline takes any template name; nothing in it is specific to `daily_internal`. | `email.py:48-61` `_find_latest_report`, `_extract_report_date`; `:64-76` `_build_subject`; `:79-98` `_build_draft_content`; `:101-140` `_get_draft_recipients`; `:171-211` `_generate_draft`; `:272` `email_preview`; `:305-315` `email_save` | High |
| F3 | Every caller of the pipeline. Production: EOD step 4b and its retry, the Friday EOD step 8, `reports resend`, `email preview`, `email save`. Tests: `test_email.py` imports `_build_subject`, `_generate_draft`, `_REPORTS_DIR`, `_EMAIL_DIR` and calls `_generate_draft(…, session=db_session)`; `test_email_recipients_client.py` calls `_get_draft_recipients(…, session=db_session)` four times. Nothing in `automation/`, `scripts/`, `config/`, `templates/`, the daemon or the Slack action executor runs `email save` or imports the pipeline. | `eod_workflow.py:1093,1114,1298`; `reports.py:700`; `email.py:272,305`; `tests/test_email.py:12-17,168-173,183,213,218-226`; `tests/test_email_recipients_client.py:192,205,212,226,233,245,252,254` | High |
| F4 | `email save` exits 0 when it finds no report: `_generate_draft` prints the error and returns `None`, and `email_save` returns. No recipients is a warning, and the draft is still saved. So neither case reaches step 4b's non-zero branch. That branch prints "No recipients configured? Run: workmain email recipients add <email>", which names a case that exits 0. Only an unhandled exception in the child reaches it. | `email.py:186-194`, `:200-207`, `:305-307`; `eod_workflow.py:1101-1104` | Medium |
| F5 | Step 4b's policy today: a timeout returns FAILED. A non-zero exit returns FAILED with the child's stderr when `_is_interactive()` is false (`sys.stdin.isatty()`, false under the daemon). Interactively it asks retry or skip, and both end COMPLETED, retry failing or not. A zero exit returns COMPLETED with no `message`. | `eod_workflow.py:1094-1125`, `:94-102` `_is_interactive` | Medium |
| F6 | What the surfaces read from a step result. The CLI loop prints `result.error` on FAILED and never reads `message`. Slack posts `result.message` on COMPLETED, falling back to "Step N — desc complete.", and `result.error` on FAILED. The child's stdout goes only to the process's own stdout through `_echo_workmain`, so in Slack the operator never learns the draft's path or that it has no recipients. Step 4b runs synchronously in `_advance_step`, because it is not in `_LONG_RUNNING_STEPS`. | `cli/commands/eod.py:206-213`; `slack_eod.py:233-238`, `:281-289`, `:314-327`, `:40` `_LONG_RUNNING_STEPS`; `eod_workflow.py:105-117` `_echo_workmain` | Medium |
| F7 | The root group is `cls=WorkmAInGroup`; the `email` group is a plain `click.group()`. A `ServiceValidationError` raised by a command in a nested plain group still reaches the user as `Error: <message>` on stderr with exit 1. Probe: a root `WorkmAInGroup` → plain `email` group → `save` raising `ServiceValidationError("No report found for template 'x'")`, run through `CliRunner(mix_stderr=False)`, gave exit `1`, stdout `''`, stderr `"Error: No report found for template 'x'\n"`. | `cli/interface.py:80`; `email.py:216` `email`; `cli/output.py:330-344` `WorkmAInGroup.invoke` | High |
| F8 | #58's service shape: "Functions take a session and return frozen dataclasses; none opens, commits or rolls back a session". Errors are `ServiceValidationError` subclasses in `services/exceptions.py`. `_get_draft_recipients` breaks this. Given no session, it opens its own `session_scope()`, and the `session` parameter exists so tests can pass one in. Every caller in production passes none. | `services/tasks_service.py:1-5`; `services/exceptions.py`; `email.py:101-140`, `:183-184` | High |
| F9 | `reports resend` opens a `session_scope()` and reads the report. It writes `staging/reports/<type>_<date>.md`, prompting first if the file exists. It then runs `email save <type>` as a child inside that scope and echoes the child's output. It prints ✓ or ✗, and exits 0 either way unless the ID is unknown. Nothing is written to the database in that scope. Its tests patch `reports.run_workmain` three times. | `reports.py:659-712` `report_resend`; `tests/test_report_history.py:227-320` `TestReportResend`, patches at `:265`, `:291`, `:306` | Medium |
| F10 | Three step 4b tests drive it through a patched `run_workmain`: timeout, non-zero stderr in the FAILED message, and stderr echoed on an interactive retry. An in-process call has no timeout, so the first has no counterpart after the change. | `tests/test_eod_workflow.py:1253-1258`, `:1262-1268`, `:1290-1305` | Medium |
| F11 | The pipeline's tests write to the live tree. `test_email.py` writes a report into the real `staging/reports/` and a draft into the real `staging/email/`, and removes them by hand. §6.2 rule 7 makes a test's directory `tmp_path`. The paths are module constants built from the file's location. `ReportGenerator` takes an optional `output_dir` for the same job. | `email.py:38-41`; `tests/test_email.py:26-37`, `:218-226`; `ai/report_generator.py:80-84` | Medium |
| F12 | Five lines describe step 4b as running `email save daily_internal`. After the change the step no longer runs it. | `eod_workflow.py:1088` (dry run), `:1351` (step description, printed in the plan table); `cli/commands/eod.py:13`, `:88`; `cli/interface.py:227` | Low |
| F13 | Overlaps. #205 "builds on #104's service". Its "Also in scope" removes the `session` parameter from `_get_draft_recipients` and `_generate_draft`, and its Tests section names `test_email.py` and `test_email_recipients_client.py`. #212 states "#104 removes `reports resend`'s child process for `email save`". #192 owns choosing the report by date: "Whichever lands first, the other carries the date-selection behaviour unchanged." #104's own body: "Whether the remaining thirteen follow is a decision to take after this one ships". The Friday step 8 (`email save weekly_client`) is one of the thirteen. | `gh issue view 205`, `212`, `192`, `104` | High |
| F14 | The change touches at least four application files: a new `workmain/services/` module, `email.py` (the wrapper, F2), `reports.py` (`resend`, F9) and `eod_workflow.py`. With F12's help text it is six, adding `eod.py` and `interface.py`. The issue's own text names three files, because it puts the wrapper in `reports.py`. §2.2 escalates a `hotfix/*` to `feature/*` above three application files, and adds that "file count is a proxy, not the test. The real metric is whether the fix is one traceable root cause." | F2, F9, F12; `docs/DEVELOPMENT_STANDARDS.md` §2.2 `hotfix/*` | High |

### Settled by the findings or a standing rule

- **Service API.** The service API is two functions in `workmain/services/email_service.py`, over the logic F2 lists, moved unchanged. `build_draft(session, template) -> EmailDraft` serves `email preview`. `save_draft(session, template) -> SavedDraft` serves `email save`, step 4b and `reports resend`, and its result carries the draft's path. Both take any template name. That is the only valid shape: `email save` and `email preview` take any template (F2), and the issue requires the CLI and the step to call the same function. A function limited to `daily_internal` would be a second path. "No report" is raised as a `ServiceValidationError` subclass (F8). "No recipients" is a field on the result, not an error, as it is today (F4).
- **The `session` parameter goes.** Under #58's shape the caller owns the scope (F8), so `_get_draft_recipients`'s self-opened scope and its test-only `session=None` parameter can't move into the service as they are. The two test files in F3 are rewritten against the service in this issue. This takes over #205's "Also in scope" item and its two test files.
- **Step 4b keeps its policy, with the service's error in place of the exit code.** The step opens a `session_scope()`, calls `save_draft` and returns COMPLETED. Its `message` names the draft path and says when no recipients are assigned, which is what the issue's fifth acceptance criterion asks for and what Slack shows (F6). When the service raises, the step uses the same branch a non-zero exit uses today (F5). Non-interactive returns FAILED with the error's message. Interactive asks retry or skip. The wrong recipients hint (F4) is replaced by the error's own message. The timeout test (F10) is removed, since an in-process call has no timeout, and the other two are rewritten against the service.
- **Date selection is unchanged.** `_find_latest_report`'s newest-by-mtime choice moves as it is (#192, F13).
- **The Friday step 8 stays a child process**, as #104's body says (F13). It keeps working, because `email save` calls the same service.
- **F12's five lines are corrected in this issue.** They describe the site being changed.
- **`reports resend` calls `save_draft` on its own session** and keeps its ✓/✗ output and exit 0. Converting it further is #212's work. Its three tests patch the service instead of `run_workmain` (F9).

## 4. Options

### What `email save` does when no report exists

Today it prints an error and exits 0 (F4). The service raises (settled above), so the wrapper either lets the error reach `WorkmAInGroup` or catches it.

#### Option A — let the error propagate: `Error: …` on stderr, exit 1

- **Approach:** `email save` and `email preview` don't catch the service's error. F7 shows it reaching the user as Click's error line with exit 1, with no code in the command.
- **Pros:** The wrapper keeps no logic of its own, which the issue's third criterion asks for. The output matches §5.6's Error row. It meets the no-file case of #192's second criterion. The Friday step 8 already has a branch for a non-zero exit (FAILED under the daemon, a warning interactively), so it needs no code change.
- **Cons:** It changes `email save`'s exit-code contract for one remaining child-process caller, the Friday step 8. Under the daemon, a Friday with no weekly report moves step 8 from COMPLETED to FAILED, and the Slack EOD pauses there. §1.2 then needs a step 8 test driven by `run_workmain` returning 1.

#### Option B — catch it and keep exit 0

- **Approach:** The wrapper catches the service's error, prints it red and returns, as today.
- **Pros:** No caller's contract changes, and #192 takes the whole exit-code change.
- **Cons:** It writes new code whose only job is to keep a known defect (#192's second criterion). The wrapper gains error handling of its own. Step 4b and step 8 would also disagree on the same condition: step 4b fails on no report, while step 8 completes.

**Recommendation: A.** The service raises either way. Option B adds code to the wrapper only to keep the defect #192 is open to remove, and the one caller whose contract changes already has a branch for the new exit code. The cost is one test on step 8.

### How the service's tests reach `tmp_path`

F11: the staging directories are module constants, and §6.2 rule 7 wants the test in `tmp_path`.

#### Option A — module constants in the service, patched by the test

- **Approach:** `email_service` holds `_REPORTS_DIR` and `_EMAIL_DIR`. A test patches them to `tmp_path` in its body with `patch.object(email_service, "_REPORTS_DIR", tmp_path)`.
- **Pros:** No parameter that only tests pass. This is the reason #205 gives for removing the `session` parameter.
- **Cons:** The test depends on private names.

#### Option B — optional directory parameters

- **Approach:** `save_draft(session, template, reports_dir=None, email_dir=None)`, defaulting to the staging tree, as `ReportGenerator(output_dir=None)` does.
- **Pros:** The test passes `tmp_path` with nothing patched. There is precedent in the codebase.
- **Cons:** Every production caller passes neither argument, so they are parameters that exist for tests. That is the same kind of parameter as the `session` one this issue removes.

**Recommendation: A.** This issue removes one test-only parameter on that very ground. Adding two more in the same change would contradict it.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | The change touches four application files, six counting the help text, against `hotfix/*`'s limit of three (F14). It has one root cause: there is no function for creating an email draft. §2.2 says file count is a proxy and the root cause is the test. Does `hotfix/*` stand (recommended: yes, it is one root cause), or does the work move to a `feature/*` branch cut from `dev`? | |
| Q2 | When no report exists, does `email save` exit 1 with Click's error line (Option A, recommended), or keep exit 0 until #192 (Option B)? Under A, the Friday step 8 fails under the daemon on a day with no weekly report. | |
| Q3 | Do the service tests patch the staging-directory constants (Option A, recommended), or does the service take optional directory parameters (Option B)? | |
| Q4 | This issue takes over #205's `session`-parameter removal and its two test files, and #212's `reports resend` child-process removal. At close-out, are both issue bodies edited to drop those items (recommended), or kept as written? | |

## 6. Disposition

- Promoted to:
- Superseded by:
