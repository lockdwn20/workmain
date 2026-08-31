# EOD subprocess hardening — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20260831
**Originating item:** Issue #94 (parent #93, milestone *Daemon Stability and Transaction Integrity*)

---

## 1. Purpose

Issue #94 requires every `subprocess.run` in `workmain/workflows/eod_workflow.py` to pass `timeout=` and `capture_output=True`, and to turn a timeout or a non-zero exit into `EodStepStatus.FAILED` with a usable message. This study verifies the 14 call sites against source, establishes which of the child commands are interactive, and puts the resulting design choices in front of Ray before a spec is written. Two of the issue's acceptance criteria cannot both be met literally without breaking CLI behaviour that ships today; §4 and §5 carry the options and the questions.

## 2. Scope of the read

- `workmain/workflows/eod_workflow.py` — all 14 `subprocess.run` sites, full file.
- Every child command those sites invoke, in `workmain/cli/commands/` — `meetings.py`, `clockify.py`, `time.py`, `reports.py`, `email.py`, `gdocs.py`, `slack.py` — read for `click.prompt` / `click.confirm` / `input()` inside the invoked command only.
- Every other `subprocess` call in `workmain/**`, to place #94's scope against the milestone's exit condition.
- `tests/test_eod_workflow.py`, `tests/test_eod_pipeline.py`, `tests/test_eod_task_matching.py` — existing patches of `eod_workflow.subprocess.run`.

**Not examined:** the Slack EOD surface's own step dispatch (`workmain/slack/**`), the daemon scheduler, and issue #104's service-extraction path. Nothing in `workmain/services/**` was read — no service boundary changes here.

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | 14 `subprocess.run` call sites exist; none passes `timeout=`, `capture_output=` or `text=`. Confirmed by reading every site, not by grep count alone. | `workmain/workflows/eod_workflow.py:213,236,246,302,304,892,903,1043,1057,1083,1096,1123,1164,1205` | Critical |
| F2 | Every site invokes the same binary, `_WORKMAIN_BIN`, resolved once at import from `sys.executable`'s directory. There is exactly one command shape to harden, not fourteen. | `eod_workflow.py:24-29`, `_resolve_workmain_bin` | High |
| F3 | Six of the fourteen are retry re-invocations of a command already run in the same function; the retry site is a second literal `subprocess.run` of the same `cmd`. | `eod_workflow.py:246,903,1057,1096` (four retries) plus the two loop sites at `302,304` | Medium |
| F4 | `workmain slack post weekly` is unconditionally interactive: it prompts for approval before posting. Capturing its stdout hides that prompt from the operator. | `workmain/cli/commands/slack.py:630`, `post_choice = click.prompt(...)` | Critical |
| F5 | `workmain gdocs upload all` prompts on each sub-upload failure. Capturing its stdout hides those prompts. | `workmain/cli/commands/gdocs.py:625,647`, `gdocs_upload_all` | High |
| F6 | The other invoked children contain no prompt of their own: `reports save` (`reports.py:257-283`), `email save` (`email.py:292-330`), `time today` (`time.py:480`), `time date` (`time.py:579`), `clockify sync push` and `clockify report save` (`clockify.py`, no `click.prompt`/`click.confirm` anywhere in file), `meetings condense` (`meetings.py`, none in the command body). Capturing their output costs no interaction. | as cited | High |
| F7 | `time today` / `time date` exist at their call sites *solely* to render entries for the operator to eyeball before the parent's `_confirm()`. Capturing without echoing back leaves the operator confirming a blank screen. | `eod_workflow.py:300-310`, `_run_review_step` | High |
| F8 | Under systemd, stdin is `/dev/null`, so a child's `click.prompt` receives EOF and aborts rather than blocking. The daemon's hang exposure is therefore network and AI latency, not human prompts — which is what the timeout must be sized against. | `eod_workflow.py:96-104`, `_is_interactive` docstring; F4/F5 children | High |
| F9 | A hardened exemplar already exists in this codebase and is the pattern to follow: `timeout=`, `check=True`, `capture_output=True`, `text=True`, with `TimeoutExpired` handled. | `workmain/daemon/delivery.py:120-132`, `_deliver_os` | Medium |
| F10 | `workmain/cli/commands/reports.py:746` runs `subprocess.run(['workmain', 'email', 'save', report_type], check=True)` — no `timeout=`, and it hardcodes the bare name `'workmain'` rather than `_WORKMAIN_BIN`, so it cannot resolve the binary under systemd. Outside #94's stated scope; inside the milestone's exit condition. | `reports.py:744-753`, `report_resend` | High |
| F11 | `workmain/utils/editor.py:43` and `workmain/cli/commands/notes.py:587` launch `$EDITOR` and must never carry a timeout. Outside #94's scope; named here so a later sweep of the milestone's exit condition does not break them. | as cited | Medium |
| F12 | 13 existing tests patch `workmain.workflows.eod_workflow.subprocess.run`. Any change to how the call is made — including moving it behind a helper — has to keep that patch target valid or update all 13. | `tests/test_eod_workflow.py:168,188,988,997,1010,1022,1034,1045,1054,1062,1118,1135,1153`; `tests/test_eod_pipeline.py:127` | High |
| F13 | Issue #94's body cites "C10 pilots that" — a finding ID from a census not carried in the issue. No issue is titled or labelled C10; the nearest match is #104, *Extract daily-internal email generation into a service and remove its subprocess call*. The reference is unresolvable to a reader who has read nothing else. | `gh issue view 94`; `gh issue list --search` returns no C10 | Medium |
| F14 | Issue #94's body asserts "the subprocess writes to a stdout that does not exist under systemd". Not verified here as a claim about systemd's behaviour; what *is* verified is that no site captures output, so nothing a child prints is available to the caller. | `eod_workflow.py`, all 14 sites | Low |

## 4. Options

The tension is F4/F5 against the issue's second AC, *"Every subprocess.run call in workmain/workflows/eod_workflow.py passes capture_output=True"*. Two of the fourteen children prompt the operator on stdout. Capturing that stdout makes the prompt invisible while the child still blocks on stdin.

### Option A — Literal: capture at all 14 sites, echo the captured text back

- **Approach:** `capture_output=True, text=True, timeout=<n>` at every site; print `result.stdout`/`result.stderr` after the call so F7's display sites still show something.
- **Pros:** Meets every AC exactly as written. No issue amendment. Smallest diff.
- **Cons:** Breaks `slack post weekly` — the approval prompt is captured, the operator sees nothing, the child blocks until the timeout kills it mid-post. Same failure for `gdocs upload all` on any sub-upload failure. Echoing after the fact cannot fix a prompt, only a report.

### Option B — Two tiers: capture by default, pass through for the two interactive children

- **Approach:** One helper. Default path captures. `slack post weekly` and `gdocs upload all` are invoked in a pass-through mode that inherits stdio but still passes `timeout=`.
- **Pros:** Preserves shipped CLI behaviour. The daemon still gets its timeout on all 14 — which is the hang protection #94 exists for. Under systemd those two children abort on EOF anyway (F8), so capturing them buys the daemon nothing.
- **Cons:** AC2 fails literally for 2 of 14; the issue's AC needs rewording before implementation. In the Slack EOD surface the two pass-through steps still relay no child output.

### Option C — Make the two children non-interactive, then capture all 14

- **Approach:** Add non-interactive flags to `slack post weekly` and `gdocs upload all`; move the approval into the parent, which already has `_confirm()`. Then capture unconditionally.
- **Pros:** Architecturally the correct end state and the one the module docstring already asks for — interaction belongs to the surface, not to a child process. Meets every AC literally afterwards.
- **Cons:** Changes two CLI command contracts, which is scope no acceptance criterion on #94 named. Larger blast radius than the issue asked for, on the eve of #104 dissolving part of this boundary anyway.

### Option D — One `_run_workmain()` helper, applied on top of whichever of A/B/C is chosen

- **Approach:** Replace 14 literal `subprocess.run` calls with 14 calls to a single module-level helper that owns `timeout=`, `capture_output=`, `text=`, `TimeoutExpired` handling and the `EodStepResult` failure message. The helper contains the only `subprocess.run` in the file.
- **Pros:** `docs/DEVELOPMENT_STANDARDS.md` §3.6 — one place owns the rule. The retry sites (F3) get identical treatment for free. Failure-message wording is uniform, so the AC's *"timeout named in the result message"* and *"captured stderr in the result message"* are testable in one place rather than fourteen. F12's patch target `eod_workflow.subprocess.run` stays valid, because the helper lives in that module.
- **Cons:** The issue's first AC — `grep -c 'subprocess.run'` equals the count that also pass `timeout=` — becomes `1 == 1`, true but vacuous. It needs restating as an AC about the helper, or it verifies nothing.

**Recommendation: Option D over Option B.** D because the standards' integration rule already decides it and because it makes the two behavioural ACs checkable once instead of fourteen times; B over A and C because the daemon — the thing #94 is protecting — never runs those two children interactively (F8), so capturing them costs the CLI a working approval prompt and returns the daemon nothing, while C buys the same end state at the price of two CLI contract changes the issue never scoped. Option C's flag work should be opened as its own issue rather than absorbed here.

**Timeout values.** No timeout should be sized from a guess about the network. Proposed as module constants in `eod_workflow.py`, not `config/` — these are workflow parameters with no user story for tuning them, and `config/ai_settings.json` already owns the AI provider's own per-call timeout separately. Values below are a proposal for Ray, not a decision.

| Constant | Seconds | Sites |
| --- | --- | --- |
| `_TIMEOUT_LOCAL` | 120 | `time today`, `time date` |
| `_TIMEOUT_NETWORK` | 300 | `clockify sync push` ×2, `clockify report save`, `email save` ×3 |
| `_TIMEOUT_AI` | 600 | `meetings condense`, `reports save` ×2 |
| `_TIMEOUT_INTERACTIVE` | 1800 | `slack post weekly`, `gdocs upload all` |

`_TIMEOUT_INTERACTIVE` is deliberately long: it exists to bound an abandoned terminal, not to pace a human.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | Which option in §4 governs the two interactive children — A (literal capture, accept the broken prompts), B (pass through), or C (de-interactivise the children first)? | **Answered 20260831, Spanner.** Moot once the acceptance criteria stopped being read as design input (Q2). Capturing a child that prompts on stdout is wrong on its own terms, so no fork remains: the runner captures by default and the two interactive sites capture only when the parent is non-interactive. Recorded as DR4 in the spec. |
| Q2 | Approve Option D's helper, and with it the rewording of issue #94's first AC? | **Answered 20260831, Ray.** Option D approved — "it introduces a reusable function rather than attempting 14 different ways to do the same thing." Acceptance criteria validate work; they do not specify it. The design is set on its merits and the issue's criteria are adjusted to match. |
| Q3 | Are the four proposed timeout constants and their values acceptable, and do they belong in `eod_workflow.py` rather than `config/`? | **Answered 20260831, Spanner.** Values as proposed. Home moves to `workmain/utils/self_invoke.py` because Q7 gives the runner a second caller — the constants belong with the runner, not with one of its callers. |
| Q4 | Is `text=True` in scope? | **Answered 20260831, Spanner.** Yes. Without it captured output is `bytes` and cannot be put in a result message. |
| Q5 | Add `check=`? | **Answered 20260831, Spanner.** No. Each site already carries its own retry/skip/fatal policy keyed on `returncode`; raising instead would collapse all of them into one. Recorded as DR6. |
| Q6 | Should captured stdout from `time today` / `time date` be echoed before the `_confirm()`? | **Answered 20260831, Spanner.** Yes — the caller echoes, the runner never prints. Recorded as DR5. |
| Q7 | F10 — `reports.py:746`. Pull into #94, or open as its own issue? | **Answered 20260831, Ray.** Pull into #94 — "it specifically applies to the issue we are correcting." |
| Q8 | F13 — issue #94's body cites an unresolvable "C10". | **Answered 20260831, Ray.** Corrected in the issue; the body now reads "Issue #104 pilots that." |

## 6. Disposition

- Promoted to: `../specs/EOD_SUBPROCESS_HARDENING_SPEC.md`
