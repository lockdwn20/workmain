# EOD subprocess hardening — Spec

**Status:** Draft
**Author:** Spanner (Role 1)
**Date:** 20260831
**Branch:** `feature/issue-94-eod-subprocess-hardening` (from `dev`)
**Target release:** v1.30.0
**Originating item:** Issue #94 (parent #93, milestone *Daemon Stability and Transaction Integrity*)
**Design study:** `../design/RECON_EOD_SUBPROCESS_HARDENING.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20260831 | Ray | Option D — one reusable runner, not fourteen hand-written call sites. | Adopted. §3 DR1. |
| 20260831 | Ray | Acceptance criteria validate work; they do not specify it. The design is settled on its merits and the issue's criteria are adjusted afterwards to match. | Adopted. §5 restates issue AC1 and AC2 and names them as issue-body edits due at close-out. |
| 20260831 | Ray | `subprocess.run(['workmain', ...])` in `report_resend` is pulled into this issue rather than opened separately — it is the same defect. | Adopted. Step 3. |
| 20260831 | Ray | Issue #94's dangling "C10" reference corrected in the issue body to "Issue #104". | Closed, no spec impact. |
| 20260831 | Spanner | Capturing the stdout of a child that prompts the operator hides the prompt while the child still blocks on stdin. `slack post weekly` prompts unconditionally; `gdocs upload all` prompts on sub-upload failure. | DR4 — those two sites capture only when the parent is non-interactive. Under systemd the child aborts on EOF, so capture there is pure gain; in the CLI the prompt is preserved. |
| 20260831 | Spanner | A timeout is not the same event as a non-zero exit. Four sites currently ignore `returncode` entirely and must still fail on a timeout, because a hung child is exactly what this issue exists to stop. | DR7 — a timeout is always `FAILED`; a non-zero exit keeps each site's existing policy. |
| 20260831 | Spanner | `check=` would collapse every site's distinct retry/skip/fatal policy into one exception path. | DR6 — not used. Exit codes stay explicit. |
| 20260831 | Ray | `workmain_cli` is the wrong module name — it reads as a general CLI-calling facility, inside a package already called `workmain`. | Renamed `workmain/utils/self_invoke.py`. The module owns self-invocation of the `workmain` entry point and nothing else; DR1 states the boundary and §1 names the three `subprocess` sites that must never route through it. |
| 20260831 | Spanner | Census: `subprocess` appears in `workmain/**` at five places. Fifteen calls invoke the `workmain` binary (14 in `eod_workflow`, 1 in `report_resend`) and all are in scope; the other three invoke `$EDITOR` or `wsl-notify-send`. The runner therefore covers every self-invocation that exists, and there is no second tranche to extend it to later. | §1 out of scope. Issue #104 removes one self-invocation by extracting a service, so the count trends down, not up. |
| 20260831 | Spanner | Timeout constants live with the runner, not with a caller, because Step 3 gives the runner a second caller. | `workmain/utils/self_invoke.py`. |

---

## 1. Scope

**In scope**

- New module `workmain/utils/self_invoke.py`: binary resolution, timeout constants, a `WorkmainRun` result, and `run_workmain()` — the only place in the project that invokes the `workmain` binary as a subprocess.
- `workmain/workflows/eod_workflow.py`: all 14 `subprocess.run` sites converted to `run_workmain()`; `_resolve_workmain_bin()` and `_WORKMAIN_BIN` removed; timeout handling added to every affected step; captured stdout echoed where the operator was previously reading the child's screen output.
- `workmain/cli/commands/reports.py` `report_resend`: its one `subprocess.run(['workmain', ...])` converted to `run_workmain()`, which also fixes its unresolvable bare binary name.
- `tests/test_eod_workflow.py`, `tests/test_eod_pipeline.py`: repointed to the new patch target and call signature.
- New `tests/test_self_invoke.py`.

**Out of scope**

- Removing the subprocess boundary. Issue #104 pilots that; this spec only stops the boundary hanging the daemon.
- `workmain/utils/editor.py:43` and `workmain/cli/commands/notes.py:587`. Both launch `$EDITOR` and wait on a human by design; a timeout there would be a defect, not a fix.
- `workmain/daemon/delivery.py:120`. Already passes `timeout=`, `check=`, `capture_output=` and `text=`, and invokes `wsl-notify-send`, not the `workmain` binary. It is the pattern this spec follows, not a target of it.
- Generalising the runner to any binary other than the `workmain` entry point. It is not a shared `subprocess` facility, and a later caller wanting to run something else does not extend it.
- Making `slack post weekly` or `gdocs upload all` non-interactive. That is the correct end state and belongs in its own issue; it changes two CLI command contracts that issue #94 does not name.
- Any change to which steps run, in what order, or to any step's existing retry/skip/fatal policy on a non-zero exit.

## 2. Verified current state

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| 14 `subprocess.run` sites in `eod_workflow.py`; none passes `timeout=`, `capture_output=` or `text=`. | `eod_workflow.py:213,236,246,302,304,892,903,1043,1057,1083,1096,1123,1164,1205` |
| All 14 invoke `_WORKMAIN_BIN`, resolved once at import from `sys.executable`'s parent directory. | `eod_workflow.py:24-29`, `_resolve_workmain_bin` |
| Four sites discard the result entirely and never inspect `returncode`. | `eod_workflow.py:246` (sync retry), `:302`, `:304` (review loop display) |
| One site inspects `returncode` but only warns and continues. | `eod_workflow.py:213-215`, `_run_condense_step` |
| One site inspects `returncode` and offers `[y]es / [r]etry / [s]kip` with no `_is_interactive()` guard, so under systemd it takes the EOF default and continues. | `eod_workflow.py:236-250`, `_run_sync_step` |
| Six sites inspect `returncode` and branch on `_is_interactive()`, returning `FAILED` when non-interactive. | `eod_workflow.py:892,1043,1083,1123,1164,1205` |
| Three retry sites inspect `returncode` with their own handling — one returns `FAILED`, two warn and continue. | `eod_workflow.py:903` (FAILED), `:1057`, `:1096` (warn) |
| `workmain slack post weekly` prompts for approval on stdout before posting. | `slack.py:630`, `post_choice = click.prompt(...)` |
| `workmain gdocs upload all` prompts on stdout after a failed sub-upload. | `gdocs.py:625,647`, `gdocs_upload_all` |
| The other invoked children contain no prompt: `reports save`, `email save`, `time today`, `time date`, `clockify sync push`, `clockify report save`, `meetings condense`. | `reports.py:257-283`; `email.py:292-330`; `time.py:480,579`; `clockify.py` (no `click.prompt`/`click.confirm` in file); `meetings.py` `condense` body |
| `_is_interactive()` returns `sys.stdin.isatty()`, and is False under systemd. | `eod_workflow.py:96-104` |
| `_run_review_step` runs `time today` / `time date` purely so the operator can read the entries before `_confirm()`. Nothing else consumes that output. | `eod_workflow.py:300-310` |
| `report_resend` runs `subprocess.run(['workmain', 'email', 'save', report_type], check=True)` — no timeout, and a bare binary name that cannot resolve under systemd. | `reports.py:744-753`, `report_resend` |
| 14 test sites patch `workmain.workflows.eod_workflow.subprocess.run`; 4 of them assert the exact positional call with no keywords. | `tests/test_eod_workflow.py:168,176,181,188,988,997,1010,1022,1034,1045,1054,1062,1118,1135,1153`; `tests/test_eod_pipeline.py:127,135,140` |
| Three tests drive failure with `side_effect=OSError('boom')` and rely on the step's `except Exception` catching it. | `tests/test_eod_workflow.py:1045,1054,1062` |
| `tests/test_eod_pipeline.py` and `tests/test_eod_workflow.py` import `_WORKMAIN_BIN` from `eod_workflow`. | `test_eod_pipeline.py:13`; `test_eod_workflow.py:38` |
| An already-hardened exemplar exists: `timeout=5, check=True, capture_output=True, text=True` with `TimeoutExpired` handled. | `daemon/delivery.py:120-132`, `_deliver_os` |

## 3. Design rules

- **DR1 — One runner.** `workmain/utils/self_invoke.py` holds the only `subprocess` invocation of the `workmain` binary in the project. After this work, `grep -rn "subprocess" workmain/ --include=*.py` returns hits only in that module, `utils/editor.py`, `cli/commands/notes.py` and `daemon/delivery.py` — none of which invoke the `workmain` binary. The module is not a general `subprocess` facility: `$EDITOR` and `wsl-notify-send` callers stay where they are, because a timeout on `$EDITOR` would be a defect rather than a fix.
- **DR2 — The runner never raises for the two conditions it exists to report.** A timeout and a non-zero exit are both reported on the returned `WorkmainRun`. Everything else — a missing binary, an `OSError` — propagates unchanged, so each step's existing `except Exception` handler keeps working exactly as it does today.
- **DR3 — Every call passes an explicit `timeout=`.** `run_workmain()` has no default timeout and the parameter is keyword-only and required. A caller that does not know its bound is given one in §4's table; it is never allowed to omit it.
- **DR4 — Capture is the default; two sites capture conditionally.** `slack post weekly` and `gdocs upload all` prompt the operator on stdout, so they pass `capture=not _is_interactive()`: captured in the daemon, where the child would abort on EOF anyway and the captured text is the only thing the Slack surface can relay; passed through in the CLI, where the prompt has to reach a human. No other site is conditional.
- **DR5 — The runner prints nothing.** Echoing captured output is the caller's job, in the caller's own primitives — plain `print()` in `eod_workflow.py`, which deliberately imports neither `click` nor `rich`, and `console.print` in `reports.py`.
- **DR6 — No `check=`.** Exit codes are inspected explicitly. Each site's retry, skip and fatal policy is keyed on `returncode` today and stays that way; an exception path would collapse all of them into one.
- **DR7 — A timeout always returns `FAILED`; a non-zero exit keeps each site's existing policy.** These are different events. A timeout means the daemon thread was hung, which is the whole reason this issue exists, so it fails the step even at the four sites that ignore `returncode` and the one that only warns. A non-zero exit changes no site's behaviour — where a site already returns `FAILED`, that message now carries captured stderr; where a site warns or continues, it still warns or continues.
- **DR8 — Failure message wording is owned by `WorkmainRun.failure_message()`,** not written out at each site, so a step's `FAILED` message reads the same wherever it came from.

Anything this spec does not cover: stop at the current step and follow `CLAUDE.md` Role 3.

## 4. Steps

Each step ends with a commit.

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | `workmain/utils/self_invoke.py` — `resolve_workmain_bin()`, the four timeout constants, `WorkmainRun`, `run_workmain()`. Unit tests for timeout capture, non-zero capture, success, `capture=False`, and `OSError` propagation. | `workmain/utils/self_invoke.py`, `tests/test_self_invoke.py` |
| 2 | Convert all 14 `eod_workflow.py` sites to `run_workmain()` per the table below. Delete `_resolve_workmain_bin` and `_WORKMAIN_BIN`. Add the DR7 timeout branch to every affected step. Echo captured stdout in `_run_review_step` before `_confirm()`, and at the condense, sync, clockify-report and report-generation sites. Repoint the 17 existing test patch sites and the two `_WORKMAIN_BIN` imports. | `workmain/workflows/eod_workflow.py`, `tests/test_eod_workflow.py`, `tests/test_eod_pipeline.py` |
| 3 | Convert `report_resend`'s call to `run_workmain()`, replacing `check=True` + `except CalledProcessError` with a `WorkmainRun` check, and add a test that a non-zero exit still reports the draft failure without raising. | `workmain/cli/commands/reports.py`, `tests/test_report_history.py` |
| 4 | Step-level failure tests: a timeout returns `FAILED` with the timeout named, and a non-zero exit returns `FAILED` with stderr in the message, at a representative step of each policy class. | `tests/test_eod_workflow.py` |

**Per-site conversion table.** Every row loses its `_WORKMAIN_BIN` prefix — `run_workmain()` prepends the resolved binary.

| Line | Call | Timeout | Capture | Notes |
| --- | --- | --- | --- | --- |
| 213 | `meetings condense <title>` | `TIMEOUT_AI` | default | Non-zero still warns only (DR7). Echo stdout. |
| 236 | `clockify sync push` | `TIMEOUT_NETWORK` | default | Echo stdout. |
| 246 | `clockify sync push` (retry) | `TIMEOUT_NETWORK` | default | Currently discards result; now fails on timeout only. |
| 302 | `time today` | `TIMEOUT_LOCAL` | default | Echo stdout before `_confirm()` (DR5). |
| 304 | `time date <iso>` | `TIMEOUT_LOCAL` | default | Echo stdout before `_confirm()`. |
| 892 | `reports save <type> --date <iso>` | `TIMEOUT_AI` | default | |
| 903 | same (retry) | `TIMEOUT_AI` | default | |
| 1043 | `email save daily_internal` | `TIMEOUT_NETWORK` | default | |
| 1057 | same (retry) | `TIMEOUT_NETWORK` | default | |
| 1083 | `clockify report save daily --start --end` | `TIMEOUT_NETWORK` | default | |
| 1096 | same (retry) | `TIMEOUT_NETWORK` | default | |
| 1123 | `gdocs upload all --date [--force]` | `TIMEOUT_INTERACTIVE` | `not _is_interactive()` | Prompts on sub-upload failure (DR4). |
| 1164 | `slack post weekly` | `TIMEOUT_INTERACTIVE` | `not _is_interactive()` | Prompts unconditionally (DR4). |
| 1205 | `email save weekly_client` | `TIMEOUT_NETWORK` | default | |
| `reports.py:746` | `email save <report_type>` | `TIMEOUT_NETWORK` | default | Step 3. |

**Timeout constants** — `workmain/utils/self_invoke.py`:

| Constant | Seconds | Rationale |
| --- | --- | --- |
| `TIMEOUT_LOCAL` | 120 | Local database read and render; nothing here touches the network. |
| `TIMEOUT_NETWORK` | 300 | One integration round trip — Clockify, Drive, Slack, email staging. |
| `TIMEOUT_AI` | 600 | An AI generation that may make several provider calls, each of which `config/ai_settings.json` already bounds at 60s of its own. |
| `TIMEOUT_INTERACTIVE` | 1800 | Bounds an abandoned terminal, not a human's thinking time. |

### Authorization points

**None.** This spec executes no DB migration, deletes no GitHub object, merges nothing to `main` and force-pushes nothing. The post-merge daemon restart this `feature/*` branch requires falls under the §1.4 carve-out and is performed by `/closeout` as a step.

## 5. Acceptance criteria

Issue #94's AC1 and AC2 are written against fourteen hand-written call sites and do not survive the runner. AC1.1 and AC2.1 below are their replacements, and editing the issue body to match is a close-out task.

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | `subprocess` is invoked against the `workmain` binary in exactly one place. `grep -rn "subprocess" workmain/ --include=*.py` returns hits only in `utils/self_invoke.py`, `utils/editor.py`, `cli/commands/notes.py` and `daemon/delivery.py`. | the stated `grep` |
| AC1.2 | `grep -c "subprocess" workmain/workflows/eod_workflow.py` returns 0. | the stated `grep` |
| AC1.3 | `run_workmain` has no default timeout: calling it without `timeout=` raises `TypeError`. | `pytest tests/test_self_invoke.py::TestRunWorkmain::test_timeout_is_required` |
| AC1.4 | All 15 converted call sites pass an explicit `timeout=`. | `grep -n "run_workmain(" workmain/ -r --include=*.py` — every hit passes `timeout=`, count is 15 |
| AC2.1 | `run_workmain` passes `capture_output=True, text=True` when `capture` is true, and neither when it is false. | `pytest tests/test_self_invoke.py::TestRunWorkmain::test_capture_flags` |
| AC2.2 | The two prompting sites pass `capture=not _is_interactive()`; no other site passes `capture=`. | `grep -n "capture=" workmain/workflows/eod_workflow.py` returns exactly 2 hits, both `not _is_interactive()` |
| AC3.1 | A subprocess exceeding its timeout returns `EodStepStatus.FAILED` with the timeout value named in the result message. | `pytest tests/test_eod_workflow.py -k timeout` — patches `subprocess.run` to raise `TimeoutExpired` |
| AC3.2 | A timeout fails the step even at a site whose non-zero-exit path only warns (`_run_condense_step`) and at one that discards the result (`_run_review_step`). | `pytest tests/test_eod_workflow.py -k "timeout and (condense or review)"` |
| AC4.1 | A non-zero exit at a site that already returns `FAILED` puts captured stderr in the result message. | `pytest tests/test_eod_workflow.py -k "nonzero_stderr"` |
| AC4.2 | A non-zero exit changes no site's existing policy — the condense, sync-retry and review sites still continue. | `pytest tests/test_eod_workflow.py -k "nonzero and policy"` |
| AC4.3 | `report_resend` reports a failed draft without raising when the child exits non-zero. | `pytest tests/test_report_history.py -k resend` |
| AC5.1 | `pytest` passes at or above baseline. | `pytest` |

## 6. Test plan

- **Baseline before this work:** 934 passed, 0 failed (`CHANGELOG.md`, File Header Removal — "flat at 934 passed throughout all six gates").
- **Expected after:** 934 + 14 = 948 passed. No test is deleted; 17 existing patch sites are repointed in place.

| File | Covers |
| --- | --- |
| `tests/test_self_invoke.py` (new, ~7 tests) | `resolve_workmain_bin` both branches; `timeout=` required; capture flags on and off; `TimeoutExpired` → `WorkmainRun(timed_out=True)`; non-zero → `returncode` and `stderr` carried; `OSError` propagates rather than being swallowed (DR2). |
| `tests/test_eod_workflow.py` (~6 new) | AC3.1, AC3.2, AC4.1, AC4.2. Repoint 14 patch targets from `eod_workflow.subprocess.run` to `eod_workflow.run_workmain`; update the 4 exact-call assertions to the new signature; the 3 `side_effect=OSError` tests keep working unchanged under DR2. |
| `tests/test_eod_pipeline.py` (0 new) | Repoint 1 patch target and 2 call assertions; repoint the `_WORKMAIN_BIN` import. |
| `tests/test_report_history.py` (~1 new) | AC4.3. |

## 7. Risks and rollback

| Risk | Blast radius | Mitigation / rollback |
| --- | --- | --- |
| A timeout value is too low and kills a step that was working. `TIMEOUT_AI` against a slow provider is the likeliest. | One EOD step returns `FAILED`; the workflow's existing retry/skip path handles it and no data is lost — every affected child command is independently re-runnable from the CLI. | Constants are four named values in one module. Raising one is a one-line change. |
| DR4's conditional capture is wrong about the daemon and the two prompting children behave differently than expected under systemd. | Thursday's Slack weekly post and the Drive upload step. | `capture=not _is_interactive()` degrades to today's behaviour in the CLI; in the daemon the pre-existing `_is_interactive()` guard already returns `FAILED` on non-zero, so the worst case is a step that fails where it previously failed. |
| The 17 repointed test patch sites hide a real behaviour change behind a mechanical rename. | The EOD suite's coverage of step dispatch. | Step 2's commit is reviewable on its own, and the 4 exact-call assertions are the check — they assert the new signature explicitly rather than accepting any call. |
| DR7 makes four previously result-ignoring sites able to fail a step. | An EOD run that previously continued past a hung child now stops at it. | This is the intended change and is what issue #94 asks for. If it proves wrong for the condense site specifically, DR7 is one branch to remove at one site. |

Each step is a single commit and reverts independently. Step 1 adds a module nothing yet calls, so reverting Steps 2–4 leaves a dead module rather than a broken one; reverting all four returns the tree to `dev`.
