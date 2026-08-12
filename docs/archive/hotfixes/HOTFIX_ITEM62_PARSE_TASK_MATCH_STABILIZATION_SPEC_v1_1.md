WorkmAIn
HOTFIX_ITEM62_PARSE_TASK_MATCH_STABILIZATION_SPEC v1.1
20260725

Version History:
- v1.0 (20260725): Initial spec. DRAFT — pending Opus (Role 2) review.
- v1.1 (20260725): Opus review round 1 applied. Gate 3: explicit note-dedup
  restructure block added (shared trailing append diverges from task-match
  shape); body-level exception handler marked do-not-touch. Gate 1: tests
  must let the availability probe pass. Gate 4/AC8: raw-mode correctness
  spot-check added (prior live measurement included the SYSTEM block).
  Design Rule 9: cause-chain wording corrected; warning scoped to CLI
  surface. Opus re-review clean (20260725); approved by Ray 20260725
  (status-only update, no version increment).

---

## Status

Approved by Ray on 20260725. Ready for Role 3 implementation.
Recon basis: `docs/dev/design/RECON_SPEC_SLACK_LLM_COMPLETION_SPRINT_20260725.md`
(Findings §1 and Addendum A) — referenced, not reproduced.

## Scope

**In scope:**
- Fix 1 — Per-call `raw: true` Ollama mode so `parse_task_match()` /
  `parse_note_duplicate()` requests bypass the Modelfile-baked ~1,800-token
  SYSTEM block (prompt drops ~2,400 → ~600 tokens; prompt_eval well under the
  30 s ceiling).
- Fix 2 — Wrap bare `TimeoutError` in `OllamaProvider.generate()` into the
  provider-error hierarchy (`ProviderUnavailableError`).
- Fix 3 — `parse_task_match()`/`parse_note_duplicate()` propagate
  `ProviderError`; Step 3c and Step 3d demote `ollama_available` on any
  `ProviderError` from a generate call and engage the keyword fallback for the
  current and remaining items.

**Out of scope:**
- Any change to `IntentParser.parse()` (Slack path — healthy, and it depends
  on the baked SYSTEM block).
- Any change to `provider_manager.py`, `base_provider.py`, `ai_settings.json`
  (timeout value stays 30), the system prompt, or the Modelfile (no rebuild).
- Slack-side surfacing of the demotion warning — the daemon does not run
  Step 3c/3d today; when the Slack_LLM_Completion_Sprint wires Slack EOD
  through these steps, warning delivery on that surface belongs to the sprint.
- Prompt prefix-cache reordering (backlog #65, conditional).
- Step 3c cancel path / remaining #48 ACs.

## Design Rules

1. `raw` mode is opt-in per request: callers set
   `generation_options={"raw": True}`; `OllamaProvider.generate()` **pops**
   the key out of the options dict into the top-level payload key `raw`. It
   must never appear inside the payload's `options` object and must never be
   applied blanket.
2. `IntentParser.parse()` must NOT set `raw` — the Slack path requires the
   Modelfile-baked SYSTEM block. Only `parse_task_match()` and
   `parse_note_duplicate()` set it.
3. `_build_prompt()` is unchanged — its client-side `[INST] … [/INST]`
   wrapping is exactly what raw mode requires for Mistral.
4. Timeout wrapping catches `TimeoutError` (`socket.timeout` is an alias of
   `TimeoutError` on Python ≥3.10 — do not add a separate `socket.timeout`
   clause) and raises `ProviderUnavailableError` with `from e`.
5. Step 3c/3d demotion keys on exception **type** (`except ProviderError`),
   never on message substrings — `ProviderManager.generate()` re-wraps the
   provider's exception into a new generic `ProviderError` before it reaches
   the parse methods, so any `"timed out"` string check would never match
   (recon Addendum A).
6. Demotion trigger is any `ProviderError` from a generate call (not timeout
   narrowly). Demotion is per-step local: Step 3c and Step 3d each hold their
   own `ollama_available` and demote independently; 3c's demotion does not
   carry into 3d.
7. The item whose call raised is re-run through the keyword matcher in the
   same iteration — never silently skipped.
8. `parse_task_match()`/`parse_note_duplicate()` catch only
   `(json.JSONDecodeError, ValueError, TypeError)` for malformed model output
   (`TypeError` covers e.g. `float(None)` on a null confidence — without it a
   malformed-but-parseable response would crash the EOD run instead of
   returning no-match). `ProviderError` propagates to the caller.
9. On demotion, emit a warning through the same output mechanism as adjacent
   Step 3c/3d user-facing messages (e.g. the "No matches found above
   threshold" line). This is CLI-surface output — the only surface that runs
   these steps today. The warning includes the caught exception `e` and walks
   its cause chain for diagnosis: `e.__cause__` is the Fix-2
   `ProviderUnavailableError` (message carries "timed out …"), and the raw
   `TimeoutError` sits at `e.__cause__.__cause__`. Cause-chain content is
   display-only — never branch on it (Rule 5).

## Branch & Git Workflow

Per `GIT_WORKFLOW_STANDARDS.md` (check the live doc version).

- **Branch type:** `hotfix/*`
- **Branch name:** `hotfix/parse-task-match-stabilization`
- **Branches from:** `main`
- **Merges to:** `main` **and** `dev`
- **Commit strategy:** one descriptive commit per gate (body: files changed,
  decisions applied, test count). `Co-Authored-By: Claude` on all commits.
- **Application-file scope:** exactly 3 application files
  (`workmain/ai/providers/ollama.py`, `workmain/ai/intent_parser.py`,
  `workmain/workflows/eod_workflow.py`) — within the hotfix limit; tests,
  `__version__.py`, `CHANGELOG.md` excluded from the count.
- **Deployment:** touches `workmain/**` → **restart-and-verify mandatory.**
  After merging to `dev`:
  ```bash
  systemctl --user restart workmain-notify.service
  systemctl --user show workmain-notify.service --property=ActiveEnterTimestamp
  ```
  Confirm `ActiveEnterTimestamp` postdates the merge commit before reporting
  deployed.
- **Version bump:** `__version__.py` 1.26.0 → **1.26.1**.
- **Release:** after tagging `v1.26.1` and pushing tags, create the GitHub
  Release object (`gh release create v1.26.1 --generate-notes`) — the tag
  alone does not complete the release (standards v1.7).

## Gates

### Gate 1 — Provider layer (Fixes 1 + 2)

- **Files:** `workmain/ai/providers/ollama.py` (v1.3 → v1.4), tests
- **Changes:**

  In `generate()`, replace the options/payload construction and the exception
  handling as follows (all other lines unchanged from v1.3; verify against the
  actual file, which matches the recon §1 Q3 quote):

  ```python
  options = {"num_predict": request.max_tokens or 512}
  if request.generation_options:
      options.update(request.generation_options)
  raw_mode = bool(options.pop("raw", False))
  payload = {
      "model": self._model,
      "prompt": self._build_prompt(request),
      "stream": False,
      "keep_alive": -1,
      "options": options,
  }
  if raw_mode:
      payload["raw"] = True
  ```

  ```python
  except urllib.error.URLError as e:
      raise ProviderUnavailableError(f"Ollama request failed: {e}") from e
  except TimeoutError as e:
      raise ProviderUnavailableError(
          f"Ollama generation timed out after {self._timeout}s"
      ) from e
  ```

  No change to `check_availability()` or `_build_prompt()`.

- **Tests** (in the existing test module covering `OllamaProvider`):

  `generate()` calls `self.check_availability()` before the POST (its own
  `/api/tags` `urlopen` inside a blanket except). All three tests below must
  let that probe pass — stub `check_availability()` to return
  `ProviderStatus.AVAILABLE`, or sequence the `urlopen` mock so the first
  call returns a valid tags response — otherwise the test exercises the
  availability guard (which raises `ProviderUnavailableError` without
  `from e`) instead of the POST path it claims to prove.

  - `test_generate_raw_flag_promoted_to_top_level` — with
    `generation_options={"raw": True}`: payload has top-level `"raw": True`
    and `"raw"` is absent from `payload["options"]`.
  - `test_generate_no_raw_by_default` — without the flag: no `"raw"` key
    anywhere in the payload.
  - `test_generate_timeout_wrapped` — mocked POST-path `urlopen` (or
    `.read()`) raising `TimeoutError("timed out")`: `generate()` raises
    `ProviderUnavailableError` whose `__cause__` is the original
    `TimeoutError`.
- **Version bump:** `ollama.py` header v1.4 + version-history line.
- **Human approval checkpoint:** Ray confirms payload shape (raw placement)
  and exception wrapping before Gate 2.

### Gate 2 — Intent parser (Fix 1 wiring + Fix 3 contract)

- **Files:** `workmain/ai/intent_parser.py` (v1.3 → v1.4), tests
- **Changes:**

  In BOTH `parse_task_match()` and `parse_note_duplicate()`:

  1. Add `generation_options={"raw": True}` to the `GenerationRequest`
     construction.
  2. Replace the two-tier exception handling: keep the malformed-output catch,
     widened to `except (json.JSONDecodeError, ValueError, TypeError)` (same
     log message and no-match return as today); **delete the bare
     `except Exception` clause entirely** so `ProviderError` (and anything
     else provider-raised) propagates to the caller.
  3. Update both docstrings: "Raises ProviderError if the provider call
     fails; caller is responsible for fallback."

  `parse()` is untouched (Design Rule 2).

- **Tests** (existing intent-parser test module):
  - `test_parse_task_match_sets_raw` — the `GenerationRequest` passed to the
    mocked provider manager has `generation_options == {"raw": True}`.
  - `test_parse_note_duplicate_sets_raw` — same for note dedup.
  - `test_parse_task_match_propagates_provider_error` — mocked
    `provider_manager.generate` raising `ProviderError("x")`: the call
    raises, does not return a no-match dict.
  - `test_parse_note_duplicate_propagates_provider_error` — same.
  - `test_parse_task_match_null_confidence_returns_no_match` — mocked
    response content `{"matched": true, "confidence": null, "note_id": 1}`:
    returns `{"matched": False, "confidence": 0.0, "note_id": None}` (proves
    the `TypeError` widening; exact input matters — `null` confidence is the
    case the old bare except silently covered).
  - `test_parse_sets_no_raw` — `parse()`'s `GenerationRequest` has no `raw`
    in `generation_options` (pins Design Rule 2 against regression).
- **Version bump:** `intent_parser.py` header v1.4 + version-history line.
- **Human approval checkpoint:** Ray confirms the narrowed contract before
  Gate 3.

### Gate 3 — Step 3c/3d demotion (Fix 3)

- **Files:** `workmain/workflows/eod_workflow.py` (v1.10 → v1.11), tests
- **Changes:**

  **Task match.** In `_run_task_match_step()`, restructure the per-task
  selection (v1.10 lines 558–568 per recon §1 Q4) so the keyword branch is
  reachable as a fall-through after demotion:

  ```python
  if ollama_available:
      try:
          result = intent_parser.parse_task_match(ts, candidate_notes)
      except ProviderError as e:
          ollama_available = False
          # user-visible warning per Design Rule 9, e.g.:
          # "Ollama generation failed ({e}); falling back to keyword
          #  matching for this and remaining tasks. Cause: {e.__cause__}"
      else:
          if result["confidence"] < 0.7:
              continue
          matched_note = notes_by_id.get(result["note_id"])
          candidates.append((result["confidence"], ts, matched_note))
          continue
  # keyword path — reached when ollama_available is False at loop entry
  # OR immediately after demotion for the item that raised
  result = _keyword_score_match(ts, candidate_notes)
  if result["score"] < 0.2:
      continue
  candidates.append((result["score"], ts, result["note"]))
  ```

  **Note dedup.** In `_run_note_dedup_step()`, restructure the per-pair
  selection (v1.10 lines 758–780). This block is NOT structurally identical
  to task-match — v1.10 has a single shared `duplicates_found.append(...)`
  after both branches. The restructure moves that append inside each path.
  The duplicated append is intentional — it mirrors the task-match
  fall-through shape; do not refactor it into a flag variable. Identifier
  names, call arguments, threshold expressions, and the append tuple below
  are indicative — transplant them verbatim from actual v1.10 source (the
  block below fixes the control shape only):

  ```python
  if ollama_available:
      try:
          result = intent_parser.parse_note_duplicate(<args verbatim from v1.10>)
      except ProviderError as e:
          ollama_available = False
          # user-visible warning per Design Rule 9 (note-dedup wording:
          # "... falling back to keyword matching for this and remaining
          #  pairs ...")
      else:
          if not result["duplicate"] or result["confidence"] < 0.7:
              continue
          duplicates_found.append((ts_a, ts_b))
          continue
  # keyword path — reached when ollama_available is False at loop entry
  # OR immediately after demotion for the pair that raised
  result = _keyword_note_dedup_match(<args verbatim from v1.10>)
  if result["score"] < 0.5:
      continue
  duplicates_found.append((ts_a, ts_b))
  ```

  If actual v1.10 source diverges from the indicative thresholds/keys above,
  the v1.10 source values win — surface any divergence that changes control
  flow (not mere naming) to Role 1 before proceeding.

  Import `ProviderError` from `workmain.ai.base_provider` locally within each
  step function, matching the existing local-import pattern of the probe
  blocks. No change to the probe blocks themselves.

  **Do not touch:** the body-level `except Exception` handler at
  ~eod_workflow.py:650 remains exactly as-is — it is the step's outer
  backstop. The new `except ProviderError` sits inside the loop and
  intercepts before it; do not widen, narrow, or remove the outer handler.

- **Tests** (existing eod-workflow test module):
  - `test_task_match_demotes_on_provider_error` — 3 carry-forward tasks;
    mocked `parse_task_match` raises `ProviderError` on the first call:
    asserts exactly one LLM call total, all 3 tasks scored by
    `_keyword_score_match` (including the first), and the demotion warning
    emitted.
  - `test_task_match_llm_path_unchanged_when_healthy` — no error: all tasks
    go through `parse_task_match`, keyword matcher never called.
  - `test_note_dedup_demotes_on_provider_error` — mirror of the first test
    for Step 3d (pairs via keyword, including the pair that raised).
  - `test_note_dedup_independent_of_task_match_demotion` — 3c demoted, 3d's
    probe passes: 3d still calls `parse_note_duplicate` (pins Design Rule 6).
- **Version bump:** `eod_workflow.py` header v1.11 + version-history line.
- **Human approval checkpoint:** Ray confirms demotion behavior and warning
  wording before Gate 4.

### Gate 4 — Close-out, live verification, release

- **Files:** `__version__.py` (1.26.1), `CHANGELOG.md`
- **Changes:** version bump; CHANGELOG entry under 1.26.1 summarizing the
  three fixes. Full test suite run (baseline 869 + ~13 new; record actual
  count in the commit body).
- **Live verification (on the hotfix branch, before merge):**
  1. `workmain eod` WITHOUT `--skip task_match`, real carry-forward tasks and
     today's notes: Step 3c completes with real match attempts, no per-item
     ~30 s stalls (AC1/AC2).
  2. Raw-mode correctness spot-check: at least one carry-forward task known
     to be completed (with a note describing its completion among today's
     notes) is detected at confidence ≥ 0.7 via the LLM path in raw mode. If
     no natural candidate exists on verification day, stage one: create a
     carry-forward task and add a note describing its completion, then run
     Step 3c (AC8). Latency alone does not satisfy this — the prior "answer
     correct" measurement was taken WITH the SYSTEM block present; raw mode
     has never been correctness-verified.
  3. Induced-failure run: temporarily set
     `config/ai_settings.json providers.ollama.timeout` to `1`, rerun Step 3c
     — the `/api/tags` probe still passes (~0.01 s), generation times out,
     demotion fires on the first item, warning prints, all items complete via
     keyword matching (AC3). Restore `timeout: 30` and confirm restored value
     before merge.
- **Merge & deploy:** merge to `main` and `dev` (no-ff); restart daemon;
  confirm `ActiveEnterTimestamp` postdates the merge commit; Slack smoke test
  — send a normal time-entry message, confirm normal confirmation-gate
  behavior (AC4).
- **Release:** tag `v1.26.1`, push tags, create the GitHub Release object.
- **Human approval checkpoint:** Ray confirms all ACs including live
  verification before the item is reported complete.

## Acceptance Criteria

Live verification required for AC1–AC4 and AC6–AC8; tests alone do not check
these boxes.

Final disposition (20260725, Ray): item closed Complete with AC2/AC3/AC8
carried/superseded rather than met as originally written — see
`FEATURE_BACKLOG.md` Item 62 entry for the authoritative status line and
Items 65/66 for the carried/superseded work.

- [x] AC1 — A full `workmain eod` run without `--skip task_match` completes
      Step 3c with real LLM match attempts against real carry-forward tasks
      (no 30 s per-item timeouts, no `--skip` workaround). Live-verified ×2
      (20260725) — no total-failure hang, no `--skip` needed.
- [ ] AC2 — Task-match and note-dedup requests run in raw mode; observed
      per-item latency is seconds, not timeout-bound (prompt no longer
      carries the baked SYSTEM block). NOT MET as written — stragglers hit
      the full 30 s on every live run; Fix 3's demotion absorbed them as
      designed. Root cause (novel-prompt eval, zero KV prefix-cache reuse)
      superseded to backlog Item 65.
- [ ] AC3 — Under an induced generation timeout with a passing `/api/tags`
      probe, Step 3c (and 3d, if induced there) demotes on the first
      `ProviderError`, emits the CLI-visible warning, and completes every
      item — including the one that raised — via the keyword matcher.
      CARRIED to backlog Item 66 — the spec's induced `timeout: 1` test was
      never run; natural demotion observed live ×3 (Step 3c only — Step 3d's
      demotion path has zero live proof to date).
- [x] AC4 — The Slack `parse()` path is unchanged: no `raw` on its requests,
      and a live Slack time-entry message behaves normally post-deploy.
      Confirmed by Ray post-merge (20260725).
- [x] AC5 — Full test suite passes: all 869 baseline tests plus the new
      tests in this spec, zero regressions. 882 passed (869 + 13) at Gate 3;
      reconfirmed on `dev` post-merge.
- [x] AC6 — Daemon restarted after merge; `ActiveEnterTimestamp` postdates
      the merge commit. Merge commit 2026-07-25 17:29:04 PDT;
      `ActiveEnterTimestamp` 2026-07-25 17:30:18 PDT.
- [x] AC7 — `v1.26.1` tag pushed AND GitHub Release object created.
      <https://github.com/lockdwn20/workmain/releases/tag/v1.26.1>
- [ ] AC8 — Raw-mode correctness: a known-completed carry-forward task is
      detected at confidence ≥ 0.7 via the LLM path with `raw: true`
      (staged if necessary per Gate 4). NOT RUN, not failed — no natural
      candidate cleared 0.7 live, and evidence suggests a staged pair never
      actually entered the attempt pool (see Item 66 Gate 0 recon ask (f)).
      CARRIED to backlog Item 66 verbatim.

## Test Plan

Summarized per gate above; new tests total ~13 across the three existing test
modules covering `OllamaProvider`, `IntentParser`, and the EOD workflow.
Exact-input-critical cases:
- `test_parse_task_match_null_confidence_returns_no_match` — must use JSON
  `null` confidence, not a missing key (a missing key defaults via `.get()`
  and would not exercise the `TypeError` path).
- `test_generate_timeout_wrapped` — must raise `TimeoutError`, not
  `urllib.error.URLError` (or it proves the pre-existing clause), and must
  let the availability probe pass so the POST path is reached.

## Backlog Item Update (for `FEATURE_BACKLOG.md`, verbatim on approval)

```
#### Item 62 — parse_task_match/parse_note_duplicate total-failure stabilization
**Status:** Open — In Progress
**Priority:** High
**Effort:** ~3–4 hrs
**Added:** 20260725
**Target Phase:** Hotfix (pre-Slack_LLM_Completion_Sprint)
**Description:** Step 3c task matching timed out on every item (novel
~2,400-token prompts exceed the 30 s socket timeout on CPU inference; the
bare TimeoutError bypassed provider-error wrapping; the /api/tags probe kept
the keyword fallback structurally unreachable). Fixes: per-call raw mode
bypassing the Modelfile SYSTEM block for task_match/note_dedup; TimeoutError
wrapped into ProviderUnavailableError; Step 3c/3d demote ollama_available on
any ProviderError and engage keyword fallback for current and remaining
items.
**Acceptance Criteria:** See spec HOTFIX_ITEM62_PARSE_TASK_MATCH_STABILIZATION_SPEC_v1_1.md.
**Files Affected:** workmain/ai/providers/ollama.py, workmain/ai/intent_parser.py,
workmain/workflows/eod_workflow.py, tests, __version__.py, CHANGELOG.md
```

---

*Ready for Role 3 (Claude Code / Sonnet) implementation. Paste this
document — not the planning-chat review history — as the opening message
of a fresh Claude Code / Sonnet session. Session discipline: Gate 1 only
in the first session; handoff at every gate boundary. Design questions
stop and surface to Role 1 — never resolved in-flow.*
