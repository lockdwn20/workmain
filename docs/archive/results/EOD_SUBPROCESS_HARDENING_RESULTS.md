# EOD subprocess hardening — Implementation Results

**Status:** Shipped
**Author:** Anvil (Role 3)
**Date:** 20260831
**Spec:** `../specs/EOD_SUBPROCESS_HARDENING_SPEC.md`
**Released as:** v1.30.0 (tag v1.30.0)

---

## 1. Summary

Complete. Every self-invocation of the `workmain` binary now routes through one hardened runner, `workmain/utils/self_invoke.py`, which passes an explicit per-call timeout and reports a timeout or a non-zero exit on a `WorkmainRun` result rather than hanging or raising. All 14 `subprocess.run` sites in `eod_workflow.py` and the one in `reports.py` `report_resend` were converted; `_resolve_workmain_bin()` / `_WORKMAIN_BIN` and the `import subprocess` in both modules were removed. A timeout now fails the EOD step (DR7) even at the sites that previously ignored `returncode`; a non-zero exit keeps each site's existing retry/skip/fatal policy. Captured stdout is echoed where the operator was reading the child's screen (DR5), and non-empty captured stderr is always echoed (DR9). The three sites whose child can prompt — `meetings condense`, `gdocs upload all`, `slack post weekly` — capture only when the parent is non-interactive (DR4).

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 1 | `workmain/utils/self_invoke.py`: `resolve_workmain_bin()`, `TIMEOUT_LOCAL/NETWORK/AI/INTERACTIVE`, `WorkmainRun` (`.ok`, `.failure_message()`), `run_workmain(args, *, timeout, capture=True)`. | `workmain/utils/self_invoke.py` (new), `tests/test_self_invoke.py` (new) | +10 |
| 2 | All 14 `eod_workflow.py` sites converted to `run_workmain()` per the spec's per-site table. `_resolve_workmain_bin`/`_WORKMAIN_BIN` and `import subprocess` removed. `_echo_workmain()` helper added for DR5/DR9. DR7 timeout→`FAILED` branch on every affected step. `_is_interactive` docstring reworded. Existing test patches repointed to `run_workmain` and the new signature; `_WORKMAIN_BIN` imports moved to `workmain.utils.self_invoke`. | `workmain/workflows/eod_workflow.py`, `tests/test_eod_workflow.py`, `tests/test_eod_pipeline.py` | +0 (repoints only) |
| 3 | `report_resend` converted to `run_workmain(['email','save',report_type], timeout=TIMEOUT_NETWORK)`, replacing `check=True` + `except CalledProcessError`; fixes the unresolvable bare `'workmain'` name. `import subprocess` removed. `tests/test_report_history.py:269,295` repointed to `reports.run_workmain` returning a `WorkmainRun`. | `workmain/cli/commands/reports.py`, `tests/test_report_history.py` | +1 |
| 4 | `TestSubprocessHardening`: step-level timeout and non-zero-exit coverage at a representative step of each policy class. | `tests/test_eod_workflow.py` | +8 |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | `grep -rlE "^import subprocess\|subprocess\." workmain/ --include=*.py` → `self_invoke.py`, `utils/editor.py`, `cli/commands/notes.py`, `daemon/delivery.py` only. |
| AC1.2 | Met | `grep -cE "^import subprocess\|subprocess\." workmain/workflows/eod_workflow.py` → `0`. |
| AC1.3 | Met | `pytest tests/test_self_invoke.py::TestRunWorkmain::test_timeout_is_required` — passes (`run_workmain(['x'])` raises `TypeError`). |
| AC1.4 | Met | `grep -rn "run_workmain(" workmain/ --include=*.py \| grep -v "def run_workmain"` → 15 call sites, every one passing `timeout=`; equals the 15 rows of the spec's per-site table (14 in `eod_workflow.py` + `reports.py:745`). |
| AC2.1 | Met | `pytest tests/test_self_invoke.py::TestRunWorkmain::test_capture_flags` — passes. |
| AC2.2 | Met | `grep -n "capture=" workmain/workflows/eod_workflow.py` → exactly 3 hits, all `capture=not _is_interactive()`, at the condense, gdocs and slack sites. |
| AC3.1 | Met | `pytest tests/test_eod_workflow.py -k timeout` — `test_condense_timeout_returns_failed`, `test_review_timeout_returns_failed`, `test_email_timeout_returns_failed_with_value_named` all assert `FAILED` with the timeout value in `result.error`. |
| AC3.2 | Met | `pytest tests/test_eod_workflow.py -k "timeout and (condense or review)"` — 2 tests, both pass; the condense site only warns on non-zero and the review site discards the result, yet both fail on a timeout. |
| AC4.1 | Met | `pytest tests/test_eod_workflow.py -k "nonzero_stderr"` — `test_email_nonzero_stderr_in_failed_message` asserts `'no recipients configured'` in `result.error`. |
| AC4.2 | Met | `pytest tests/test_eod_workflow.py -k "nonzero and policy"` — condense, review and sync-retry sites still return `COMPLETED` on a non-zero exit. |
| AC4.3 | Met | `pytest tests/test_report_history.py -k resend` — `test_resend_reports_failed_draft_without_raising` asserts exit code 0 and `'Email draft failed'` in output. |
| AC4.4 | Met | `pytest tests/test_eod_workflow.py -k "stderr and continue"` — `test_email_retry_stderr_echoed_when_warn_and_continue` asserts `'SMTP down'` reaches stdout at the warn-and-continue retry site. |
| AC5.1 | Met | `pytest` — 953 passed, 0 failed (baseline 934). |

Issue #94's original AC1, AC2 and AC4 are superseded by the rows above per spec §5 and are due as issue-body edits at close-out.

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 1 | Retry calls (`clockify sync push` retry, report/email/clockify retries) are written as their own `run_workmain()` invocations rather than a shared inner call, so the grep in AC1.4 returns 15 call-site lines. This matches the spec's own per-site table, which already counts the four retry lines (246, 903, 1057, 1096) and the two review-loop lines (302, 304) as distinct sites. | The spec's §2 census and §4 table both treat these as separate sites; no consolidation was specified. | — (no design decision; consistent with spec) |

## 5. Verification

- **Test suite:** 953 passed, 0 failed (baseline was 934). Breakdown: +10 `test_self_invoke.py`, +1 `test_report_history.py` (AC4.3), +8 `test_eod_workflow.py::TestSubprocessHardening`.
- **Live verification:** none — the change is a subprocess-invocation wrapper with full unit coverage of the timeout, non-zero, capture, and OSError-propagation paths; no schema, service boundary, or step ordering changed. The daemon restart at close-out exercises the daemon path.
- **Daemon restart** (`feature/*`, per `docs/DEVELOPMENT_STANDARDS.md` §2.6): performed by `/closeout`; `ActiveEnterTimestamp` must postdate the `dev` merge commit. Timestamp carried by the issue's closing comment, not here.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| #114 | `config/ai_settings.json` `timeout_seconds` is read nowhere; the Claude and Gemini clients construct with no per-call timeout and `retry_attempts: 3` loops an unbounded call. Wire `timeout_seconds` through the providers; `TIMEOUT_AI` then derives from it rather than being a chosen ceiling. | Separate defect — spec §4 and Decision Log (Caliper, 20260831). Opened 20260831. |
| — | Milestone 6's exit text carried an absolute "No `subprocess.run` in `workmain/**` lacks `timeout=`", which `utils/editor.py:43` cannot satisfy. | Closed 20260831 — Ray amended the milestone to carve out a `$EDITOR` launch. |
| #104 | Extract daily-internal email generation into a service and remove its subprocess call — pilots removing the subprocess boundary this spec only hardened. | Out of scope — spec §1. |
| #115 | Making `slack post weekly` / `gdocs upload all` non-interactive and moving their approval into the EOD step, so every call can capture unconditionally. | Out of scope — spec §1. Opened 20260831. |
| (to open) | A step-level deadline (monotonic clock threaded through multi-call loops, plus a decision on what a half-condensed step returns). Today a step is bounded at N × its per-call timeout. | Out of scope — spec DR3; different mechanism. Ray deferred opening it until this issue closes out, so the real per-step timings are visible first. |
