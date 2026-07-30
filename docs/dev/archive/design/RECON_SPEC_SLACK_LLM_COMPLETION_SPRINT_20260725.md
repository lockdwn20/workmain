WorkmAIn
RECON_SPEC_SLACK_LLM_COMPLETION_SPRINT v1.0
20260725

---

## Critical Instructions — Read Before Acting

**Read this entire document before opening any file.**

The sections are not fully independent. Section 1 (parse_task_match failure
diagnosis) establishes the Ollama call-path facts that Sections 2 and 5
reference. Section 2 (schema/executor wiring) establishes the schema and
executor context Sections 3 and 6 reference. Proceeding without reading the
full scope first risks framing findings incorrectly.

**Complete and document each section in full before proceeding to the next.**

**This is a read-only pass. No code changes, no fixes, no refactors, no
suggestions inline with findings.** Verbatim source quotations and
observations only. Proposed solutions are handled separately after this
document is reviewed by the planner (Role 1). Read-only shell commands
(journalctl, curl, ollama CLI, grep, time) are permitted where explicitly
requested below. No writes of any kind outside the Findings section of this
document.

Do not spin up parallel agents or sub-tasks across sections. Work
sequentially through each section as a single task.

**Pitfall #12 applies throughout (component-verified ≠ integration-verified).**
For every mechanism examined: trace handle/session/config provenance at every
call site — do not just confirm a leaf method works if given the right input;
confirm every caller actually supplies it. Where two code paths are claimed
to be "the same pattern," diff them verbatim, not at the shape level.

**Version drift warning:** A prior recon
(`docs/dev/design/RECON_IMPLEMENTATION_AUDIT_20260629.md`) covered some of
this ground at v1.23.0. The codebase is now at v1.26.0 — `intent_parser.py`
v1.3, `action_executor.py` v1.4, `scheduler.py` v1.14, `daemon.py` v1.21,
`slack_eod.py` v1.8, `eod_workflow.py` v1.10, `prompt_builder.py` v2.3,
`report_generator.py` v1.15 — with structural changes in exactly the areas
this sprint touches (`register_all_jobs()` consolidation,
`build_weekly_prompt()` removal, Step 3c re-scope). Do NOT reuse the June
findings as facts. Where a June finding is relevant, re-verify it against
current source and note explicitly whether it still holds.

---

## Purpose

Produce the exact source facts (signatures, schemas, call paths, live
runtime evidence) needed to write the Slack_LLM_Completion_Sprint
implementation spec accurately. This recon does not produce a spec and does
not propose designs.

Sprint scope this recon serves (per `docs/implementation-checklist.md` v3.9,
as amended by planning decisions 20260725):

- Gate 1 — Model schema rebuild: Items #42 (remove dead `project` field),
  #44 (`entry_date`/`category` fields)
- Gate 2 — Slack capability completions: Items #43 (meeting_id auto-link),
  #45 (`tags` field passthrough)
- Gate 3 — Weekly report / meeting quality: Item #23 (internal meeting
  exclusion) plus verification of what, if anything, remains of the former
  Item #46 concerns after Item #61 removed `build_weekly_prompt()`
- Former Gate 4 (Item #31, `--attendees` restoration) is REMOVED from the
  sprint — do not investigate it
- NEW, highest priority: root-cause diagnosis of the total
  `parse_task_match` failure (Section 1) — this has never produced a match
  in live operation and the sprint cannot credibly rebuild the model on a
  path that is 100% non-functional without understanding why

## Context

Live symptom, reported by Ray and reproduced daily: `workmain eod` Step 3c
(`task_match`) times out on **every** item, every run — all N carry-forward
tasks each burn the full 30s provider timeout
(`WARNING:workmain.ai.intent_parser:parse_task_match error: timed out`,
once per item). No task match has **ever** succeeded via the LLM path, and
the keyword fallback **never engages** either. Ray routes around it daily
with `workmain eod --skip task_match`. `OLLAMA_KEEP_ALIVE=-1` is set both
in the Ollama systemd service override on the LXC and in the
`OllamaProvider` API payload (v1.22.3), so cold-load alone should not
explain persistent 30s timeouts. Separately, in the Slack daemon context,
every non-standard input returns the identical canned follow-up ("What
would you like to do? I can log time, add a note...") — it is currently
unknown whether that message is the model genuinely returning the `unknown`
action or the parser's own error/timeout fallback presenting itself as a
parse result.

The Sprint 1 benchmark (v1.19.0) validated the model 9/10 — so the model
answered *something* correctly at *some point* via *some* call path. The
central diagnostic question is where the production call paths diverge from
whatever the benchmark exercised.

Environment facts to keep in mind: the CLI (`workmain eod`) runs from WSL
Ubuntu on the dev box; the daemon runs on the Proxmox host; Ollama runs in
a separate LXC (`workmain-ollama.lab.haloschaos.com:11434`, CPU inference).
The CLI and daemon may not have identical network reachability to the LXC.

| Backlog Item | Title |
|---|---|
| #23 | Meeting visibility/tagging for report prompt context |
| #42 | Remove dead `project` field from `create_time_entry` schema |
| #43 | meeting_id auto-link for Slack-created entries |
| #44 | Add `entry_date`/`category` to `create_time_entry` schema |
| #45 | `tags` field for `create_time_entry` via Slack |
| (none) | parse_task_match total-failure root cause — item to be assigned after findings |

---

## Section 1 — parse_task_match Total Failure Diagnosis (HIGHEST PRIORITY)

Goal: determine why every `parse_task_match()` call times out, why the
fallback never engages, and whether the daemon-side `parse()` path shares
the same failure. Distinguish between (at minimum): network unreachability
from the calling environment, a request that reaches Ollama but never
completes in 30s, a request malformed enough that Ollama never responds, a
wrong model/tag/host in config, and a probe/fallback seam that structurally
prevents the fallback from ever running.

**Questions to answer:**

1. Quote `IntentParser.parse_task_match()` from `workmain/ai/intent_parser.py`
   (v1.3) verbatim — full method, line range. Then state:
   - How the prompt is constructed: what goes into a single call (one task
     vs. batched), and the approximate character/token size of a realistic
     prompt (use a representative active `task_status` count of ~20 and
     real note lengths if determinable from code).
   - Which provider object/method it calls, and how that provider instance
     is constructed (trace the provenance: who instantiates it, which
     config file/keys supply host, model name, timeout).
   - The exact exception handling on timeout: what is caught, what is
     logged, what is returned to the caller.

2. Quote `IntentParser.parse_note_duplicate()` verbatim (same file) with the
   same three sub-answers. State whether it shares `parse_task_match()`'s
   provider construction and call pattern verbatim or diverges (diff them —
   Pitfall #12).

3. Quote `OllamaProvider.generate()` (and any request-building helper it
   calls) from `workmain/ai/providers/ollama.py` (v1.3) verbatim. State:
   - The exact endpoint URL construction (scheme, host source, port, path)
   - The full request payload keys (`model`, `keep_alive`, `stream`,
     options, prompt/system structure)
   - Where the 30s timeout is applied (connect vs. read vs. total; which
     library call) and where the value comes from (`ai_settings.json` key
     path, default fallback)
   - Whether `stream` is true or false, and if false, whether the timeout
     applies to the complete generation

4. Quote the Ollama availability probe and LLM-vs-fallback selection logic
   for Step 3c from `workmain/workflows/eod_workflow.py` (v1.10) — the
   current `_run_task_match_step()` (or its successor under the collapsed
   runner) and any `check_availability()`/probe call it depends on,
   verbatim with line ranges. Then answer explicitly:
   - Under what exact condition does the keyword fallback engage?
   - If the probe succeeds but every subsequent `parse_task_match()` call
     times out, does the code ever fall back, retry, or short-circuit — or
     does it loop all N items at full timeout? Trace the actual control
     flow, do not infer from names.
   - Same questions for the note↔note dedup step and its
     `parse_note_duplicate()` probe/fallback.

5. Quote `check_availability()` from the Ollama provider verbatim. State
   exactly what it requests (endpoint, timeout) and what counts as
   "available." Note specifically whether a host that answers `/api/tags`
   quickly but generates slowly/never would pass this probe.

6. Compare against the benchmark path: locate the Sprint 1 benchmark
   harness (search `scripts/`, `tests/`, and docs for the 9/10 benchmark —
   e.g. anything matching `benchmark`, `intent_bench`, or the 10 sample
   inputs). Quote how it invokes the model (same `OllamaProvider.generate()`
   code path? direct `curl`/`ollama run`? different host/model/timeout?).
   State precisely where the benchmark path and the production
   `parse_task_match()` path diverge, if anywhere.

7. Compare against the daemon `parse()` path: quote `IntentParser.parse()`
   verbatim (the Slack inbound intent path), including its timeout/error
   handling and what it returns on failure. Then quote the daemon-side
   consumer of that return (in `daemon.py` v1.21 / dispatch code): when
   `parse()` fails vs. when the model genuinely returns
   `{"action": "unknown", "follow_up": ...}`, what message does the user
   see in each case? State whether the two outcomes are distinguishable
   from the Slack side, and quote the source of the exact canned string
   "What would you like to do? I can log time, add a note, update a task,
   confirm/correct a report, or start the EOD review." — is it model
   output per the system prompt's example, a hardcoded fallback string in
   Python, or both?

8. Live runtime evidence (read-only). Run from the WSL dev environment:
   - `journalctl --user -u workmain-notify.service --since "-14 days" | grep -i -E "parse|ollama|timed out|intent" | tail -80`
     — capture whether the *daemon* logs the same timeout warnings as the
     CLI, or whether daemon-side parses succeed.
   - Resolve and reach the host as the CLI would:
     `getent hosts workmain-ollama.lab.haloschaos.com` and
     `curl -sS -m 5 http://workmain-ollama.lab.haloschaos.com:11434/api/tags`
     — report resolution result, HTTP result, and elapsed time.
   - Timed minimal generation with the production model and payload shape:
     `time curl -sS -m 120 http://workmain-ollama.lab.haloschaos.com:11434/api/generate -d '{"model":"workmain-intent:latest","prompt":"spent 2 hours on XSOAR migration","stream":false,"keep_alive":-1}'`
     — report wall time and whether output is valid JSON per the schema.
     Then repeat once with a prompt sized like a real `parse_task_match()`
     call (constructed per Q1's findings) and report wall time.
   - If SSH access to the Ollama LXC is available, additionally capture
     `ollama ps` and `ollama list` output and the tail of the Ollama server
     log during the timed calls (are the production-shaped requests
     arriving at the server at all?). If SSH access is not available from
     this session, state that and list the exact commands for Ray to run —
     do not guess at their output.
   - Quote the current `ai_settings.json` `providers.ollama` block verbatim
     (host, model, timeout) and state whether the model name in config
     matches a tag present in `ollama list`.

*Document Section 1 findings before proceeding to Section 2.*

---

## Section 2 — Intent Parse Schema and Executor Wiring (Gate 1: #42, #44; Gate 2: #45)

The current schema (repo `config/intent_parse_system_prompt.txt`,
`config_version: 1.6`) is known; this section verifies the code either side
of it at current versions.

**Questions to answer:**

1. Confirm the live repo copy of `config/intent_parse_system_prompt.txt`
   matches header values `config_version: 1.6` / `config_updated: 20260611`
   / `model_built: workmain-intent:v1.6`, and quote the full
   `create_time_entry` action block verbatim (fields, IMPORTANT rules,
   examples). Confirm the dead field is named `project` (not `project_id`).

2. Quote `ActionExecutor._execute_create_time_entry()` from
   `workmain/orchestration/action_executor.py` (v1.4) verbatim with line
   range. List: every key it reads from the action dict; every parameter it
   passes to `time_entry_service.create_time_entry()`; every key it
   silently ignores. Confirm whether `tags` is already forwarded (the
   forward-prep noted in the checklist) and whether any `project`
   extraction exists anywhere in the file (grep the whole file).

3. Quote how `IntentParser` handles fields returned by the model between
   raw JSON and the action dict handed to the executor: is there a
   per-action field whitelist, validation, or coercion layer, or is the
   model's dict passed through as-is? Quote the relevant code verbatim.
   State exactly what (if anything) must change in `intent_parser.py` for
   new schema fields (`entry_date`, `category`, `tags`) to survive the trip
   to the executor.

4. Quote the full signature of `time_entry_service.create_time_entry()`
   verbatim, confirming `entry_date: Optional[date]`, `category:
   Optional[str]`, and `tags` parameters and their defaults/validation.
   Note what the service does with an unparseable or future `entry_date`
   and with an unvalidated `category` string.

5. Identify where an ISO-8601 `entry_date` string from the model would be
   parsed to a `date`: does an existing shared helper fit
   (`workmain/utils/time_parser.py` v1.0, `date_utils`, or similar)? Quote
   candidate helper signatures verbatim. Do not choose one — list what
   exists.

6. Quote the IaC touchpoint as visible from this repo: the tuning-workflow
   comment block in `intent_parse_system_prompt.txt` and any repo-side
   script or doc reference to `build_workmain_intent.sh` / Modelfile sync.
   State what, from this repo's perspective, constitutes "rebuild complete"
   (fields to update, files to touch).

*Document Section 2 findings before proceeding to Section 3.*

---

## Section 3 — Active-Meeting Context for meeting_id Auto-Link (Gate 2: #43)

The June recon found no active-meeting context stored anywhere —
`_send_t2()` received `meeting_id` only as a closure argument. Since then,
`scheduler.py` moved to v1.14 with all job registration consolidated into
`register_all_jobs(daemon)`. Re-verify at current source.

**Questions to answer:**

1. Quote the current T2/T3 job registration and the `_send_t2()`/
   `_send_t3()` implementations from `workmain/daemon/scheduler.py` (v1.14)
   verbatim with line ranges. State where `meeting_id` is available at T2
   fire time and whether anything persists it (instance variable,
   `system_state` key, file). If nothing does, state that explicitly.

2. Can two meetings' T2 fire before an intervening T3 (overlapping or
   back-to-back meetings)? Answer from the scheduling code and
   `get_active_for_date()` usage, not assumption — quote the relevant
   registration loop. This determines whether "active meeting" is a single
   value or must handle overlap.

3. Quote the T3 path and the 15-minute rescan job as they relate to
   clearing/refreshing any would-be context (what fires at meeting end;
   what happens for meetings without a T3, e.g. daemon restart mid-meeting).

4. Quote `MeetingsRepository.get_active_for_date()` and any
   current-time-window query capability (a method answering "which meeting
   is happening at datetime X," if one exists). If none exists, state that.

5. Confirm `meeting_id` is absent from both `create_note` and
   `create_time_entry` schema blocks in `intent_parse_system_prompt.txt`
   (expected: absent). Then state, from the executor side: does
   `ActionExecutor` have access to daemon-held context at execution time
   (how is the executor instantiated and called from the daemon — quote the
   construction and call sites verbatim), such that a context-derived
   `meeting_id` could be injected without the model extracting anything?
   This is a factual wiring question, not a design recommendation.

6. Quote `notes_service.create_note()`'s and
   `time_entry_service.create_time_entry()`'s `meeting_id` parameter
   handling (already-forward-compatible per backlog #43) — confirm both
   accept and persist it.

*Document Section 3 findings before proceeding to Section 4.*

---

## Section 4 — Weekly Prompt Reality Post-Item-#61 (Gate 3: #23 and ex-#46 residue)

Item #61 removed `build_weekly_prompt()` and `get_confirmed_dailies()`;
weekly generation is now one unconditional `build_prompt()` call. Item #46
is closed. This section establishes what the weekly prompt actually
contains today so Gate 3 can be re-derived.

**Questions to answer:**

1. Quote `build_prompt()`'s date-range derivation for `weekly_client` from
   `workmain/ai/prompt_builder.py` (v2.3) verbatim — how week start/end are
   computed for a given report date. State whether the range is hard-coded
   Mon–Fri/calendar-week arithmetic and whether `ScheduleService`
   (`is_working_day()`, `previous_working_day()`) is consulted anywhere in
   prompt building. If any code still assumes five weekdays or flags
   "missing" days, quote it; if nothing does, state that explicitly.

2. Quote the meeting-fetch and meeting-formatting path in `build_prompt()`
   verbatim: which repository method fetches meetings (does it use
   `get_active_for_date()` or the unfiltered `get_by_date()`/range
   equivalent — i.e., do cancelled meetings currently enter prompts?), and
   how meeting titles/content are injected into section context.

3. Quote each section's `data_sources` declaration from
   `templates/reports/weekly_client.json` verbatim. Given the v1.19.2
   `data_sources` gating, state exactly which weekly_client sections
   receive meeting context today. Do the same for
   `templates/reports/daily_internal.json` (one line per section is
   sufficient) so #23's blast radius is known for both report types.

4. Confirm from `workmain/database/models.py` that the `Meeting` model has
   no tag/visibility field today, and list what it does have that could
   bear on filtering (`client_id`, `is_cancelled`, `source`, etc.) —
   column names and types verbatim from the model definition.

5. State what the AI receives today, end-to-end, when an internal meeting
   (e.g. title containing "Internal Sync") exists in the report week: for
   each weekly_client section, does its prompt context contain that
   meeting title? Base this on the code quoted in Q2–Q3, and if quick
   verification is possible via a dry-run/preview code path without
   writing anything, note the code path that would prove it (do not
   execute a generation that calls a paid provider).

*Document Section 4 findings before proceeding to Section 5.*

---

## Section 5 — Ambiguity / `unknown` Loop Delivered State

The checklist defers "follow-up question when parse confidence is low" to
this sprint, but schema v1.6 already defines action 9 `unknown` with a
`follow_up` field. Establish what is actually delivered.

**Questions to answer:**

1. From Section 1 Q7's findings (do not re-read those files): summarize in
   one short table the three outcomes — model returns `unknown`, parse
   timeout/error, model returns unparseable JSON — and the exact user-facing
   message for each.

2. When the daemon sends a `follow_up` question, is there any pending-
   clarification state held anywhere (so the user's next message is
   interpreted as an answer), or is every inbound message parsed fresh with
   no memory of the question? Quote the dispatch/state code verbatim. Check
   `daemon.py`, `slack_eod.py`, and any confirmation-gate state.

3. Against the delivered code, state plainly: is the checklist line
   "Ambiguous input handling: follow-up question when parse confidence is
   low" (a) delivered, (b) delivered at the single-turn level only (a
   question is asked but the answer starts from zero), or (c) not
   delivered? Cite the code that supports the classification.

*Document Section 5 findings before proceeding to Section 6.*

---

## Section 6 — Action Type Extensibility Re-Verification (Decision D8)

The June recon answered this at v1.23.0. Re-verify at current versions —
this is a short section.

**Questions to answer:**

1. Quote `ActionExecutor`'s dispatch mechanism (v1.4) verbatim and name the
   pattern (dict lookup / elif chain / match).

2. List every file that must change, and the specific addition in each,
   when a new action type is added today: `intent_parse_system_prompt.txt`,
   `intent_parser.py` (any constants/whitelist per Section 2 Q3),
   `action_executor.py`, `confirmation_gate.py` (does the confirmation UX
   need per-type formatting?), tests. State whether the additions are
   independent or lockstep (strings defined in one file referenced in
   another).

3. State whether anything changed since June that makes the cascade longer
   or shorter (e.g. new per-type handling added in Sprint 3 / ops sprint).

*Document Section 6 findings, then write the Executive Summary at the top
of the Findings section.*

---

## Output

**Append all findings to the END of THIS SAME FILE**
(`docs/dev/design/RECON_SPEC_SLACK_LLM_COMPLETION_SPRINT_20260725.md`),
below the `## Findings` placeholder at the bottom. Do NOT create a separate
output file. Flat naming, no per-session subfolders — this file is the
single recon artifact for this sprint.

Findings structure:

```
## Findings

### Executive Summary
[Write LAST — 4–6 sentences: the parse_task_match root-cause determination
(or the narrowed candidate set if not conclusively determined), the biggest
surprises, and anything that blocks spec-writing.]

### Section 1 — parse_task_match Total Failure Diagnosis
### Section 2 — Intent Parse Schema and Executor Wiring
### Section 3 — Active-Meeting Context (meeting_id)
### Section 4 — Weekly Prompt Reality Post-#61
### Section 5 — Ambiguity / unknown Loop
### Section 6 — Action Type Extensibility

### Open Questions
[Anything that cannot be determined from code/runtime evidence alone and
requires Ray's input or an LXC-side command Ray must run. Be specific about
what decision or datum is needed and why.]
```

For every finding that cites a file: file path, header-docstring version,
and line range. Quote source, SQL, config, and command output verbatim in
fenced code blocks with the file path and line range on the opening fence
line. Do not paraphrase signatures, schemas, or payloads.

**Do not propose fixes. Do not write any code. Read only.**

---

## Findings

Recon executed by Claude Code / Opus (Role 2), 20260725. Read-only pass. All
file citations give path, header version, and line range. Live command output
is quoted verbatim.

### Executive Summary

The `parse_task_match` total failure is root-caused and reproduced live: a
realistic task-match prompt is ~2400 tokens (the ~1800-token baked SYSTEM prompt
rides every call), and prompt evaluation of a *novel* prompt that size on the LXC
CPU takes **~35 s — over the 30 s socket timeout** (measured: 40.8 s total wall,
35.0 s of it `prompt_eval`, model warm, answer correct). Because `stream=false`
the client blocks until generation finishes, so the read times out mid-eval; the
bare `TimeoutError` is not a `urllib.error.URLError` (so `generate()` doesn't wrap
it) and not a `ProviderError` (so the provider-manager fallback skips it), landing
in `parse_task_match`'s generic `except` which logs `timed out` and returns a
no-match. The keyword fallback never fires because Step 3c's one-shot `/api/tags`
probe (~0.01 s) always passes. The decisive regression: the Sprint-1 benchmark
validated only the short `parse()` path under a **120 s** timeout, then the
`ollama-keep-alive` hotfix cut the default timeout to **30 s** — fixing weight
residency but leaving large-prompt `prompt_eval` exposed. **This is a
latency/timeout/exception-plumbing defect, not a model-quality or reachability
problem** — the model returns correct JSON when allowed to finish. Separately, the
Slack `parse()` path is *working* (short prompts, ~8 s warm, daemon log shows no
timeouts), so the canned follow-up Ray sees is the model genuinely returning
`unknown` (that exact full string is model output, not a Python fallback) — a
model-classification observation, distinct from the task-match timeout, worth
confirming with Ray.

Biggest surprises for spec-writing: (1) the service layer is **already** wired for
`entry_date`/`category`/`tags`/`meeting_id`, and `IntentParser` is a pure
pass-through with no whitelist — so #45 is schema-only, #44 is schema + two
executor reads, #42 removes a field nothing reads, and none of the three needs a
parser change; (2) **meetings do not enter the weekly_client OR daily_internal
prompt at all today** — every section's `data_sources` omits `meetings`, so #23's
"internal meeting exclusion" is moot until meetings are first *added*, and the
`Meeting` model has no visibility field to exclude on; (3) no active-meeting
context is persisted anywhere (#43 needs a holder + a time-window query + an
executor context channel, none of which exist); (4) the low-confidence follow-up
loop is single-turn only with no clarification memory and no actual confidence
metric. Nothing blocks spec-writing; the only items needing Ray's input are the
remediation-direction choices captured in Open Questions (all design calls the
recon deliberately does not make).

---

### Section 1 — parse_task_match Total Failure Diagnosis

**ROOT CAUSE (empirically confirmed): a realistic `parse_task_match()` prompt is
~2400 tokens, and prompt evaluation of a novel prompt that size on the LXC's CPU
takes ~35 s — longer than the 30 s socket timeout. Because `stream=false`, the
HTTP client receives nothing until generation finishes, so the read times out
mid-`prompt_eval` on every call. The raw timeout is not the wrapped provider
error the fallback machinery expects, so it bypasses provider-manager fallback
and lands in `parse_task_match()`'s generic `except Exception`, which logs
`timed out` and returns a no-match. The keyword fallback never engages because
Step 3c's availability probe hits only `/api/tags` (≈0.01 s) and always passes.**

#### Q1 — `parse_task_match()` verbatim

`workmain/ai/intent_parser.py` (header **v1.3**, 20260707), lines 158–232:

```python
# workmain/ai/intent_parser.py:158-232 (v1.3)
    def parse_task_match(self, task, notes: list) -> dict:
        """Determine if a carry-forward task was completed based on today's notes.
        ...
        """
        task_content = task.note.content if task.note else ""
        if not task_content or not notes:
            return {"matched": False, "confidence": 0.0, "note_id": None}

        notes_text = "\n".join(
            f"- ID {n.id}: {n.content}"
            for n in notes
            if n.content
        )
        if not notes_text:
            return {"matched": False, "confidence": 0.0, "note_id": None}

        prompt = (
            f"Given this carry-forward task:\nTask: {task_content}\n\n"
            f"And today's notes:\n{notes_text}\n\n"
            "Did the user complete or work on this task today? "
            "Return ONLY a JSON object with:\n"
            '- matched: boolean (true if task appears completed/worked on)\n'
            '- confidence: float 0.0-1.0\n'
            '- note_id: integer (ID of best-matching note) or null\n\n'
            'Example: {"matched": true, "confidence": 0.85, "note_id": 42}'
        )

        request = GenerationRequest(
            system_prompt=None,
            prompt=prompt,
            max_tokens=64,
        )

        try:
            response, _ = self._provider_manager.generate(
                request, provider_override=ProviderType.OLLAMA
            )
            raw = response.content.strip()
            if raw.startswith("```"):
                lines = raw.splitlines()
                raw = "\n".join(
                    l for l in lines if not l.strip().startswith("```")
                ).strip()
            result = json.loads(raw)
            return {
                "matched": bool(result.get("matched", False)),
                "confidence": float(result.get("confidence", 0.0)),
                "note_id": result.get("note_id"),
            }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("parse_task_match failed to parse response: %s", e)
            return {"matched": False, "confidence": 0.0, "note_id": None}
        except Exception as e:
            logger.warning("parse_task_match error: %s", e)
            return {"matched": False, "confidence": 0.0, "note_id": None}
```

- **Prompt construction / size:** ONE call per task (not batched). One task line
  (`Task: {task.note.content}`) plus the full candidate-note list, one line per
  note (`- ID {n.id}: {n.content}`), plus a fixed ~380-char instruction/exemplar
  tail. Step 3c passes `candidate_notes` = today's notes minus the task's own
  note (eod_workflow.py:552), so for a ~20-note day the prompt body is ~1.9 KB of
  text. **Measured live prompt size for a representative 20-note day: 2400 prompt
  tokens** (see Q8) — because the workmain-intent Modelfile TEMPLATE prepends the
  baked ~8 KB / ~1800-token SYSTEM block to every `/api/generate` call, even
  though `system_prompt=None` is passed here.
- **Provider object/method + provenance:** calls
  `self._provider_manager.generate(request, provider_override=ProviderType.OLLAMA)`.
  `self._provider_manager` is the module singleton from `get_provider_manager()`
  (intent_parser.py:61). `ProviderManager._load_config()`
  (provider_manager.py:303–361) reads `config/ai_settings.json` and instantiates
  `OllamaProvider(provider_cfg)` from the `providers.ollama` block. That block
  supplies host `workmain-ollama.lab.haloschaos.com`, port 11434, model
  `workmain-intent:latest`, **timeout 30** (ai_settings.json:36–43).
- **Exception handling on timeout:** the `try` wraps the `generate()` call. Two
  catches: `(json.JSONDecodeError, ValueError)` → logs "failed to parse response",
  returns no-match; and a bare `except Exception` → logs `parse_task_match error:
  %s` and returns `{"matched": False, "confidence": 0.0, "note_id": None}`. A
  socket read timeout reaches this second catch (see Q3 note on why it is *not*
  caught earlier). The exact production log string reported by Ray —
  `parse_task_match error: timed out` — is produced by line 231 with
  `str(e) == "timed out"`, the message of a bare `socket.timeout`/`TimeoutError`.

#### Q2 — `parse_note_duplicate()` verbatim + diff vs parse_task_match

`workmain/ai/intent_parser.py` (v1.3), lines 234–277:

```python
# workmain/ai/intent_parser.py:234-277 (v1.3)
    def parse_note_duplicate(self, note_a: str, note_b: str) -> dict:
        """... Mirrors parse_task_match()'s body exactly ..."""
        request = GenerationRequest(
            system_prompt=None,
            prompt=f"Are these two notes describing the same item?\n\nNote A: {note_a}\nNote B: {note_b}",
            max_tokens=64,
        )
        try:
            response, _ = self._provider_manager.generate(
                request, provider_override=ProviderType.OLLAMA
            )
            raw = response.content.strip()
            if raw.startswith("```"):
                lines = raw.splitlines()
                raw = "\n".join(
                    l for l in lines if not l.strip().startswith("```")
                ).strip()
            result = json.loads(raw)
            return {
                "duplicate": bool(result.get("duplicate", False)),
                "confidence": float(result.get("confidence", 0.0)),
                "note_id": result.get("note_id"),
            }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("parse_note_duplicate: malformed response: %s", e)
            return {"duplicate": False, "confidence": 0.0, "note_id": None}
        except Exception as e:
            logger.warning("parse_note_duplicate: provider error: %s", e)
            return {"duplicate": False, "confidence": 0.0, "note_id": None}
```

- **Provider construction / call pattern:** IDENTICAL to `parse_task_match()` —
  same singleton `self._provider_manager`, same `provider_override=
  ProviderType.OLLAMA`, same `system_prompt=None`, same `max_tokens=64`, same
  fence-strip, same two-tier `except`. **Diff (Pitfall #12, verbatim not shape):**
  the only substantive differences are (a) the prompt string (a short two-note
  question rather than the task+notes block — so this call is *smaller* and will
  NOT hit the 30 s prompt_eval wall the same way), (b) the return keys
  (`duplicate` vs `matched`), and (c) the log prefixes. The provider call is the
  same code path. **Consequence:** note-dedup calls (short prompts) will behave
  like the Slack `parse()` path — fast when warm — not like the large
  task_match prompt. The two AI substeps of Step 3 do NOT share a failure mode.

#### Q3 — `OllamaProvider.generate()` / `check_availability()` / `_build_prompt()` verbatim

`workmain/ai/providers/ollama.py` (header **v1.3**, 20260624), lines 43–109:

```python
# workmain/ai/providers/ollama.py:43-109 (v1.3)
    def check_availability(self) -> ProviderStatus:
        """GET /api/tags and confirm configured model is listed."""
        try:
            url = f"http://{self._host}:{self._port}/api/tags"
            resp = urllib.request.urlopen(url, timeout=self._timeout)
            data = json.loads(resp.read())
            available = [m["name"] for m in data.get("models", [])]
            model_base = self._model.split(":")[0]
            if any(m.split(":")[0] == model_base for m in available):
                return ProviderStatus.AVAILABLE
            return ProviderStatus.UNAVAILABLE
        except Exception:
            return ProviderStatus.UNAVAILABLE

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """POST /api/generate with stream=false."""
        if self.check_availability() != ProviderStatus.AVAILABLE:
            raise ProviderUnavailableError(
                f"Ollama ({self._model}) unreachable at {self._host}:{self._port}"
            )
        options = {"num_predict": request.max_tokens or 512}
        if request.generation_options:
            options.update(request.generation_options)
        payload = {
            "model": self._model,
            "prompt": self._build_prompt(request),
            "stream": False,
            "keep_alive": -1,
            "options": options,
        }
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"http://{self._host}:{self._port}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=self._timeout)
            result = json.loads(resp.read())
            response_text = result.get("response", "").strip()
            prompt_tokens = result.get("prompt_eval_count", 0)
            completion_tokens = result.get("eval_count", 0)
            return GenerationResponse(...)
        except urllib.error.URLError as e:
            raise ProviderUnavailableError(f"Ollama request failed: {e}") from e

    def _build_prompt(self, request: GenerationRequest) -> str:
        """Format prompt in Mistral [INST] instruction format."""
        if request.system_prompt:
            return f"[INST] {request.system_prompt}\n\n{request.prompt} [/INST]"
        return f"[INST] {request.prompt} [/INST]"
```

- **Endpoint URL:** hardcoded scheme `http://`, host `self._host`
  (`workmain-ollama.lab.haloschaos.com`), port `self._port` (11434), path
  `/api/generate` (and `/api/tags` for the probe). Built by f-string, no TLS.
- **Payload keys:** `model` (`workmain-intent:latest`), `prompt` (the
  `[INST] … [/INST]`-wrapped user prompt — SYSTEM comes from the Modelfile
  TEMPLATE server-side), `stream: False`, `keep_alive: -1`,
  `options: {"num_predict": <max_tokens>}` (plus any `generation_options`, which
  intent parsing leaves unset).
- **Timeout application + source:** `self._timeout` (default 30, sourced from
  `ai_settings.json providers.ollama.timeout = 30`) is passed as the
  `urllib.request.urlopen(..., timeout=...)` argument on BOTH the probe and the
  POST. In urllib this is the **socket timeout** — the max idle time on any single
  blocking socket op (connect / send / read), NOT a total-generation budget.
- **stream=false ⇒ timeout covers the whole generation:** with `stream: False`
  Ollama sends no bytes until the entire completion is ready. The client blocks in
  the response read for the full server-side `total_duration`. If that exceeds
  30 s, the read times out. **Pitfall #12 note:** the timeout during the response
  read is raised as a bare `socket.timeout`/`TimeoutError` *after* `urlopen`
  returns (or during status-line read), which is NOT a `urllib.error.URLError`;
  therefore `generate()`'s `except urllib.error.URLError` does **not** catch it,
  and it is **not** converted to `ProviderUnavailableError`. Ground-truth proof:
  the production log reads `parse_task_match error: timed out` — the bare
  timeout's message — not `Ollama request failed:` or `unreachable`, which is what
  the wrapped path would have produced.

#### Q4 — Step 3c probe + LLM-vs-fallback selection verbatim

`workmain/workflows/eod_workflow.py` (header **v1.10**, 20260724),
`_run_task_match_step()` lines 435–655. Probe (lines 493–511):

```python
# workmain/workflows/eod_workflow.py:493-511 (v1.10)
        # Check Ollama availability — semantic matching when available, keyword fallback otherwise
        ollama_available = False
        intent_parser = None
        try:
            from workmain.ai.providers.ollama import OllamaProvider
            from workmain.ai.base_provider import ProviderStatus
            import os as _os
            _probe = OllamaProvider({
                "model": "workmain-intent:latest",
                "host": _os.environ.get("OLLAMA_HOST", "workmain-ollama.lab.haloschaos.com"),
                "port": int(_os.environ.get("OLLAMA_PORT", "11434")),
                "timeout": 15,
            })
            if _probe.check_availability() == ProviderStatus.AVAILABLE:
                from workmain.ai.intent_parser import IntentParser
                intent_parser = IntentParser()
                ollama_available = True
        except Exception:
            pass
```

Per-task selection (lines 558–568):

```python
# workmain/workflows/eod_workflow.py:558-568 (v1.10)
            if ollama_available:
                result = intent_parser.parse_task_match(ts, candidate_notes)
                if result["confidence"] < 0.7:
                    continue
                matched_note = notes_by_id.get(result["note_id"])
                candidates.append((result["confidence"], ts, matched_note))
            else:
                result = _keyword_score_match(ts, candidate_notes)
                if result["score"] < 0.2:
                    continue
                candidates.append((result["score"], ts, result["note"]))
```

- **When does the keyword fallback engage?** ONLY when `ollama_available` is
  `False`, which is decided **once**, before the loop, purely by
  `_probe.check_availability()` (a GET `/api/tags`, separate provider instance,
  timeout 15). It is never re-evaluated per task.
- **If the probe passes but every generate times out:** the code loops all N
  tasks through `intent_parser.parse_task_match(...)`. Each call times out at
  30 s and returns `{"confidence": 0.0}`; `0.0 < 0.7` → `continue`. **No retry, no
  fallback, no short-circuit** — it runs the full N × ~30 s, then falls out with
  zero candidates and prints "No matches found above threshold" (line 573). The
  `else` keyword branch is structurally unreachable in this state because
  `ollama_available` stayed `True`. This is the exact seam the recon asked about:
  probe-availability and per-call-generation-health are decoupled, and the probe
  only measures `/api/tags` latency, which is unaffected by generation load.
- **Note↔note dedup (Step 3d, `_run_note_dedup_step()` lines 658–869):** SAME probe
  block (lines 720–738, timeout 15) and SAME `if ollama_available: … else:
  _keyword_note_dedup_match(...)` structure (lines 769–776). Difference: its LLM
  call is `parse_note_duplicate()` (short prompt, Q2), so it will not hit the
  large-prompt timeout wall; if Ollama is up it will actually complete. Its
  fallback is likewise gated on the one-shot probe.

#### Q5 — `check_availability()` semantics

Quoted in full under Q3 (ollama.py:43–55). It issues **GET `/api/tags`** with
`timeout=self._timeout` and returns `AVAILABLE` iff any listed model's base name
(before `:`) matches the configured model's base name (`workmain-intent`). **A
host that answers `/api/tags` quickly but generates slowly or never WILL pass
this probe** — `/api/tags` returns the static model registry and never touches
the inference engine. Live-measured `/api/tags` round trip: **0.0117 s** (Q8). The
probe therefore always passes while generation independently times out.

#### Q6 — Benchmark path vs production path

There is **no benchmark harness file** in `scripts/`, `tests/`, or the repo
(searched `benchmark`, `intent_bench`, `9/10`; none found). The Sprint 1 "9/10"
benchmark was a **manual gate**, its inputs specified in
`docs/dev/specs/PHASE13_SPRINT1_OLLAMA_PROVIDER_SPEC_v1_8.md` §2c (lines 897–901)
and its results recorded in
`docs/dev/handoffs/SESSION_HANDOFF_PHASE13_SPRINT1_COMPLETE_20260605.md` (lines
70–93). Key facts from that record:

- The 10 inputs were run **through `IntentParser.parse()`** (the general Slack
  path) — NOT `parse_task_match()`. All 10 are short single sentences
  (e.g. `"spent 90 minutes on the TIE team XSOAR migration"`).
- Recorded latencies: **Sample 1 = 72.1 s (cold model load); Samples 2–10 = 2.7–
  10.9 s (warm).** The handoff explicitly states: *"120s timeout provides
  headroom. Sprint 2 warm-up ping will eliminate this."*
- **Where the paths diverge:** (1) **Timeout** — the benchmark ran under a **120 s**
  timeout; production now runs under **30 s** (OllamaProvider **v1.3**
  "ollama-keep-alive" hotfix reduced the default 120→30 s per its own version
  history). (2) **Prompt size** — the benchmark used short prompts (~1.8 KB, all
  SYSTEM); `parse_task_match()` uses a ~2400-token prompt. (3) **Method** — the
  benchmark exercised `parse()`, never the task-match path. The benchmark's own
  cold-start number (72.1 s) already exceeded today's 30 s timeout; nothing in the
  benchmark ever validated a prompt of task-match size against a 30 s ceiling.

#### Q7 — Daemon `parse()` path + the canned string

`IntentParser.parse()` (intent_parser.py:90–156) builds
`GenerationRequest(system_prompt=None, prompt=user_message,
max_tokens=self._prompt_config.get("max_tokens", 256))` and calls the SAME
`self._provider_manager.generate(..., provider_override=ProviderType.OLLAMA)`.
It has **no try/except around the generate call** — a timeout propagates as a
raw `TimeoutError` to the caller; a non-JSON body raises `IntentParseError`
(lines 127–131).

Daemon consumer `WorkmAInDaemon._dispatch_message()`
(`workmain/daemon/daemon.py`, header **v1.21**), lines 574–603:

```python
# workmain/daemon/daemon.py:574-603 (v1.21)
    def _dispatch_message(self, user_id: str, text: str) -> None:
        parser = self._get_intent_parser()
        if parser is None:
            self.post_message("Intent parsing unavailable — Ollama unreachable.")
            return
        try:
            action = parser.parse(text)
        except Exception as e:
            logger.warning("Intent parse error: %s", e)
            self.post_message("Sorry, I couldn't understand that. Try rephrasing.")
            return
        action_type = action.get("action", "unknown")
        if action_type == "unknown":
            follow_up = action.get("follow_up", "What would you like to do?")
            self.post_message(follow_up)
            return
        if action_type == "start_eod":
            self._eod_manager.handle_start_eod(user_id, self._dm_channel)
            return
        self._pending[user_id] = action
        self.post_blocks(
            blocks=self._gate.format_blocks(action),
            fallback_text=self._gate.format_prompt(action),
        )
```

User-facing message per outcome (**the three outcomes ARE distinguishable from
the Slack side**):

| Outcome | Code path | Exact message shown |
|---|---|---|
| Model returns `{"action":"unknown","follow_up":X}` | line 590–592 | the model's `follow_up` text |
| Model returns `unknown` with no `follow_up` key | line 591 default | `What would you like to do?` (short) |
| Parse timeout / raw error | except at 583–585 | `Sorry, I couldn't understand that. Try rephrasing.` |
| Model returns unparseable JSON | `IntentParseError` → same except | `Sorry, I couldn't understand that. Try rephrasing.` |
| `IntentParser()` init fails entirely | line 577–578 | `Intent parsing unavailable — Ollama unreachable.` |

**Source of the exact string** `"What would you like to do? I can log time, add a
note, update a task, confirm/correct a report, or start the EOD review."`: it
appears in exactly ONE place — the `unknown` action example in
`config/intent_parse_system_prompt.txt:123` (baked into the model). It is **model
output**, produced when the model classifies input as `unknown` and emits that
`follow_up`. It is **NOT** a hardcoded Python fallback: daemon.py:591's fallback
default is the shorter `"What would you like to do?"` (no "I can log time…"
suffix). **Therefore, if Ray is seeing the full string, the model is genuinely
returning `unknown` — the Slack `parse()` path is *working* (model responds),
and the symptom is model classification quality, not a timeout.** A timeout on
the Slack path would instead print `Sorry, I couldn't understand that.` (This
distinction should be confirmed with Ray — see Open Questions.)

#### Q8 — Live runtime evidence (from WSL dev box, 20260725)

- **Daemon journal** (`journalctl --user -u workmain-notify.service --since
  "-14 days"`): the ONLY Ollama/parse-related line in 14 days is
  `Jul 25 00:33:03 ana python[2369139] … root INFO Ollama warm-up complete.`
  No `timed out`, no `parse_task_match`, no `Checking N/…` lines. The daemon does
  not run (or log) Step 3c task-match; the timeouts Ray sees are from interactive
  `workmain eod` runs, whose logging goes to his terminal, not journald.
- **Host resolution:** `getent hosts workmain-ollama.lab.haloschaos.com` →
  `192.168.5.50` (reachable from WSL).
- **`/api/tags` (`curl -m 5`):** HTTP 200, **time_total = 0.0117 s**. Returns
  `workmain-intent:latest` (digest 220dad75…, 4.37 GB, 7.2B params, Q4_K_M),
  alongside `workmain-intent:v1.1`–`v1.6` and `mistral:latest`. The config model
  name `workmain-intent:latest` **matches** a present tag.
- **Timed generation** (`stream:false, keep_alive:-1`, production payload shape):

  | Call | Prompt tokens | total_duration | prompt_eval | eval (out) | Result |
  |---|---|---|---|---|---|
  | Small (Slack-shaped, `num_predict 256`), warm | 1864 | **8.07 s** | 1.31 s | 6.69 s / 31 tok | `{"action":"create_time_entry","duration_minutes":120,…}` ✓ |
  | **Large (task_match-shaped, ~20 notes, `num_predict 64`), novel** | **2400** | **40.83 s** | **35.04 s** | 5.76 s / 25 tok | `{"matched": true, "confidence": 0.9, "note_id": 104}` ✓ (correct) |
  | Large, immediate identical repeat (cached prefix) | 2400 | 6.0 s | 0.25 s | 5.71 s / 25 tok | same ✓ |
  | Small, repeat | 1864 | 7.87 s | 1.15 s | — | ✓ |

  `load_duration` was 0.02 s on all calls → the model was **resident**
  (`keep_alive:-1` + daemon warm-up are working; this is NOT a model-load / cold-
  weights problem). The decisive number is **prompt_eval = 35.04 s for a novel
  2400-token prompt** vs **0.25 s when the identical prompt's prefix is cached** —
  Ollama's KV prefix cache. In production each of the N task_match calls has a
  **distinct `Task:` line early in the prompt**, so the cache cannot be reused
  across tasks, and each call pays the full ~35 s `prompt_eval`, exceeding the
  30 s timeout. The model's *answers* are correct — this is purely a latency-vs-
  timeout failure, not a correctness or reachability failure.
- **SSH to the LXC** (`ollama ps` / `ollama list` / server-log tail): **not
  available from this session** (`Host key verification failed`; no local `ollama`
  CLI on WSL). Not blocking — `load_duration ≈ 0.02 s` already establishes the
  model is resident (what `ollama ps` would confirm), and `/api/tags` already
  gave the `ollama list` inventory. Commands for Ray to run on the LXC if a
  server-side view of arriving requests is wanted:
  `ollama ps`, `ollama list`, and (during a live `workmain eod` task-match run)
  `journalctl -u ollama -f` or the Ollama server log tail, to confirm the
  production-shaped requests are arriving and to read server-side
  `prompt_eval_duration`.
- **`ai_settings.json providers.ollama` block** (ai_settings.json:36–43):

```json
// config/ai_settings.json:36-43
    "ollama": {
      "enabled": true,
      "model": "workmain-intent:latest",
      "host": "workmain-ollama.lab.haloschaos.com",
      "port": 11434,
      "timeout": 30,
      "cost_structure": "Local — no API cost"
    }
```

  Model name matches a present tag (verified against `/api/tags`).

**Section 1 causal chain (all links evidence-backed):**
1. Sprint 1 validated `parse()` on short prompts under a **120 s** timeout (warm
   7–11 s, cold 72 s).
2. OllamaProvider **v1.3** cut the default timeout **120→30 s** (and added
   `keep_alive:-1`). Keep-alive fixed weight residency (`load_duration ≈ 0`);
   `prompt_eval` time for large prompts was never in scope and was left exposed to
   the new, much lower ceiling.
3. `parse_task_match()` (added later) sends **~2400-token** prompts. A novel
   prompt that size takes **~35 s of `prompt_eval`** on the LXC CPU (measured) —
   over the 30 s ceiling.
4. With `stream:false`, the client blocks until generation completes, so the
   socket read times out. The bare `TimeoutError` is **not** a `urllib.error.URLError`,
   so `generate()` does not wrap it; it is **not** a `ProviderError`, so
   `ProviderManager.generate()`'s fallback `except` does not catch it; it lands in
   `parse_task_match()`'s `except Exception`, logs `timed out`, returns no-match.
5. Step 3c's one-shot `/api/tags` probe (≈0.01 s) always passes, so
   `ollama_available` stays `True` and the keyword `else` branch is never reached.
   Net effect: all N tasks time out at 30 s, zero matches, no fallback — exactly
   the reported symptom.

---

### Section 2 — Intent Parse Schema and Executor Wiring (#42, #44, #45)

**Headline: the service layer is already fully wired for `entry_date`, `category`,
`tags`, and `meeting_id`; `IntentParser` passes the model's dict through with no
whitelist. So #42 is schema-only (remove a dead field nothing reads), #45 is
schema-only (executor already forwards `tags`), and #44 needs a schema change plus
the executor reading two keys it currently ignores.**

#### Q1 — System prompt header + `create_time_entry` block verbatim

`config/intent_parse_system_prompt.txt` header confirmed: `config_version: 1.6`,
`config_updated: 20260611`, `model_built: workmain-intent:v1.6` (lines 4–8) —
matches expected. The `create_time_entry` block (lines 56–74):

```
# config/intent_parse_system_prompt.txt:56-74
2. create_time_entry
   Required: duration_minutes (integer), description (string)
   Optional: start_time (string — 24-hour HH:MM or HHMM, only if explicitly stated),
             project (string)
   IMPORTANT: duration_minutes is in minutes. Do NOT convert minutes to anything
   else. Only convert hours to minutes (2 hours = 120, 90 min = 90, 30 min = 30).
   IMPORTANT: Only include start_time if the user explicitly states a clock time
   (e.g. "at 0530", "at 14:30", "starting at 9am"). Convert to 24-hour HH:MM.
   Do NOT infer or guess a start_time if one is not stated.
   IMPORTANT: description must contain the user's full text describing what they
   did. Remove only the duration prefix ("spent Xh", "logged Xm") and the time
   prefix ("at HH:MM"). Keep all other words exactly as written. Do NOT
   paraphrase, summarize, or shorten.
   Example input: "spent 2 hours on the XSOAR migration playbook updates and alert tuning"
   Example output: {"action": "create_time_entry", "duration_minutes": 120, "description": "XSOAR migration playbook updates and alert tuning"}
   Example input: "logged 30 min for email triage, cleared 12 tickets and flagged 2 for follow-up"
   Example output: {"action": "create_time_entry", "duration_minutes": 30, "description": "email triage, cleared 12 tickets and flagged 2 for follow-up"}
   Example input: "spent 1h at 0530 scheduling my GCP Security Operations Engineer cert exam for 13JUL2026. ..."
   Example output: {"action": "create_time_entry", "duration_minutes": 60, "start_time": "05:30", "description": "scheduling ..."}
```

- Dead field confirmed named **`project`** (string), line 59 — NOT `project_id`.
- `entry_date`, `category`, and `tags` are **absent** from this block today.
  (Note: `create_note`, action 1, DOES model an optional `tags` array, lines
  47–48 — so a `tags` pattern already exists in the schema, just not on action 2.)
- The closing global rule "Never invent fields not listed in the schema above"
  (line 139) means adding `entry_date`/`category`/`tags` requires editing this
  file AND rebuilding the model (Q6) — the model will not emit unlisted fields.

#### Q2 — `_execute_create_time_entry()` verbatim + key audit

`workmain/orchestration/action_executor.py` (header **v1.4**, 20260624),
lines 100–153 (quoted at Section 1 context; key facts here):

- **Keys read from the action dict:** `description` (line 106),
  `duration_minutes` (107), `start_time` (111), `tags` (122). Nothing else.
- **Params passed to `time_entry_service.create_time_entry()`** (lines 125–131):
  `session`, `description`, `duration_hours` (derived from duration_minutes),
  `entry_time` (parsed from start_time), `tags`.
- **Silently ignored keys:** any `project`, `entry_date`, `category`,
  `meeting_id`, `project_id` present in the action dict — none are read.
- **`tags` already forwarded:** YES (lines 119–130). The code comment says:
  *"create_time_entry has no `tags` field in the schema (v1.6) — always None
  today. Pass it anyway so no further change is needed if a tags field is added
  later."* So **#45's executor + service side is already done**; the only gap for
  #45 is the schema/Modelfile so the model actually emits `tags`.
- **`project` extraction anywhere in the file:** `grep -n "project"
  action_executor.py` → **no matches**. The schema's `project` string is read by
  nothing. #42's removal is therefore purely a schema/Modelfile edit + rebuild;
  no Python references it.

#### Q3 — Field handling between model JSON and executor (whitelist?)

`IntentParser.parse()` (intent_parser.py:90–156) does: `result =
json.loads(raw)` (line 126) → assert `"action"` key present (133) → record cost
(non-fatal) → `return result` (156). **There is NO per-action field whitelist, NO
validation, and NO coercion layer.** The model's dict is passed through verbatim.
The same is true of `parse_task_match()`/`parse_note_duplicate()` (they build
their own fixed dicts, not general actions). **Consequence for the sprint:** for
new schema fields (`entry_date`, `category`, `tags`) to survive the trip to the
executor, `intent_parser.py` needs **no change** — a field the model emits lands
in the action dict automatically. The required changes are only (a) the
schema/Modelfile (so the model emits the field) and (b) the executor (so it reads
the field and forwards it). This directly contradicts any assumption that a
parser-side whitelist must be extended.

#### Q4 — `time_entry_service.create_time_entry()` signature verbatim

`workmain/services/time_entry_service.py` (header **v1.0**, 20260612),
lines 26–56:

```python
# workmain/services/time_entry_service.py:26-56 (v1.0)
def create_time_entry(
    session,
    description: str,
    duration_hours: float,
    entry_time: Optional[time_type] = None,
    entry_date: Optional[date] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    meeting_id: Optional[int] = None,
    project_id: Optional[int] = None,
) -> TimeEntry:
    """...
    Args:
        entry_time: Start time. Required — raises MissingStartTimeError if None.
        entry_date: Calendar date. Defaults to today if None.
        category: Optional category string (no validation; passthrough).
        tags: Full-name tags. None or empty defaults to ["internal-only"].
              Invalid values raise InvalidTagsError.
        meeting_id: Forward-compatible; always None in v1.
        project_id: Optional project ID (CLI --project flag, already an int).
    """
```

- **`entry_date: Optional[date] = None`** — confirmed. Defaults to `date.today()`
  when None (line 61–62). **No validation** — a future or past date is accepted
  as-is; when `entry_date != today` it also backdates the linked note's
  `created_at` (lines 79–82). A model-supplied future `entry_date` would be
  silently honored. (Note: the service takes a `date` object, not a string —
  string→date parsing must happen upstream, in the executor; see Q5.)
- **`category: Optional[str] = None`** — confirmed. Explicit passthrough, **no
  validation** (line 45 docstring; passed straight to `TimeEntriesRepository.
  create(category=category)` line 97). Any string is stored.
- **`tags: Optional[List[str]] = None`** — confirmed. Validated against the tag
  vocabulary (lines 66–73); empty/None → `["internal-only"]`; invalid → raises
  `InvalidTagsError` (which the executor already catches, action_executor.py:138).

The service is fully forward-compatible for all three fields. #44's only code gap
is the executor reading `entry_date`/`category` and (for entry_date) parsing the
string to a `date`.

#### Q5 — ISO-8601 `entry_date` string → `date` parsing helpers (list, don't choose)

There is **no standalone `parse_date(str) -> date` helper** in `workmain/utils/`.
What exists:

- `workmain/utils/time_parser.py` (v1.0) — `parse_time(time_str) -> time`
  (time-of-day, 24h/12h) and `parse_duration_hours(str) -> float`. **No date
  function.** This is the module the executor already uses (via
  `TimeEntriesRepository.parse_time`) for `start_time`, and the natural home for a
  new `parse_date` by pattern.
- `workmain/utils/date_utils.py` (v1.0) — `resolve_date_window(...)` and
  `format_date_window_label(...)`. Internally calls **`date.fromisoformat(date_str)`**
  (lines 65, 68–69) but only inside CLI window-resolution (imports `click`); no
  reusable single-date parser is exposed.
- `workmain/utils/date_format.py` (v1.0) — `format_date_display(d: date) -> str`
  (date→string, display only; the inverse direction).
- Stdlib `datetime.date.fromisoformat()` — already imported/used in
  `date_utils.py` and `action_executor.py` imports `date`. Directly parses
  `"2026-07-25"` → `date`, raising `ValueError` on bad input.

(No selection made, per recon instruction.)

#### Q6 — IaC touchpoint / "rebuild complete" from this repo's perspective

- The tuning workflow is documented in the `intent_parse_system_prompt.txt`
  header (lines 27–33): *"1. Edit this file 2. Sync SYSTEM block to
  `ollama-lxc/models/workmain-intent/Modelfile` 3. Run `build_workmain_intent.sh`
  on Proxmox LXC 4. Update model_built date above and ollama_model if version
  incremented 5. Update ai_settings.json model field if model name changed."*
  Echoed in `intent_parse_prompt.json` `_doc.notes` (line 9).
- **`build_workmain_intent.sh` and the Modelfile live in the IaC repo, not here.**
  `grep` across `workmain/ config/ scripts/` finds only *references* to them (the
  header above and the prompt.json note) — no script file in this repo.
- **"Rebuild complete," from this repo's side, means:** (1) `config/intent_parse_
  system_prompt.txt` content edited to the new schema; (2) its header
  `config_version` bumped and `config_updated` + `model_built` dates updated
  (this file is the sole version authority per its own header and CLAUDE.md);
  (3) `config/ai_settings.json providers.ollama.model` updated **only if** the
  model name/tag changed (it is pinned to `workmain-intent:latest`, so normally
  untouched). The actual `.sh` run and Modelfile SYSTEM-block sync happen out of
  this repo (Proxmox LXC / IaC), and are Ray's manual step — a code spec here can
  only stage the prompt content + version metadata and flag the rebuild as a
  human gate.

---

### Section 3 — Active-Meeting Context for meeting_id Auto-Link (#43)

**The June finding still holds at v1.14: no active-meeting context is persisted
anywhere. `meeting_id` exists only as a per-job closure arg at T2/T3 fire time and
is gone the instant `_send_t2()` returns. Overlapping/back-to-back meetings mean
"active meeting" is not a single value. Both service write-paths already accept and
persist `meeting_id`, but the `ActionExecutor` is constructed with only a session
and has no channel to any daemon-held context.**

#### Q1 — T2/T3 registration + `_send_t2()`/`_send_t3()` verbatim; is context persisted?

`workmain/daemon/scheduler.py` (header **v1.14**, 20260716). Registration loop,
`_schedule_today_meeting_triggers()` lines 291–337:

```python
# workmain/daemon/scheduler.py:291-337 (v1.14)
def _schedule_today_meeting_triggers(daemon: Any) -> None:
    """Schedule T2/T3 DateTrigger jobs for today's meetings. Idempotent."""
    ...
    meetings = MeetingsRepository(session).get_by_date(date.today())
    ...
    now = datetime.now()
    for meeting in meetings:
        if meeting.is_cancelled:
            continue
        if meeting.start_time and meeting.start_time > now:
            _scheduler.add_job(
                lambda mid=meeting.id: _send_t2(mid, daemon),
                trigger=DateTrigger(run_date=meeting.start_time),
                id=f't2_{meeting.id}',
                replace_existing=True,
            )
        if meeting.end_time and meeting.end_time > now:
            _scheduler.add_job(
                lambda mid=meeting.id: _send_t3(mid, daemon),
                trigger=DateTrigger(run_date=meeting.end_time),
                id=f't3_{meeting.id}',
                replace_existing=True,
            )
```

`_send_t2()`/`_send_t3()` lines 340–384:

```python
# workmain/daemon/scheduler.py:340-384 (v1.14)
def _send_t2(meeting_id: int, daemon: Any) -> None:
    """T2 — Meeting start notification."""
    ...
    meeting = MeetingsRepository(session).get_by_id(meeting_id)
    if not meeting:
        logger.warning('T2: meeting %d not found', meeting_id)
        return
    dur = f' ({int(meeting.duration_hours * 60)} min)' if meeting.duration_hours else ''
    daemon.post_message(
        f'*{meeting.title}* is starting now{dur}.\n'
        f'Add notes: message me here or use `workmain note add`'
    )
    ...
    _reschedule_t4_checkin(daemon)

def _send_t3(meeting_id: int, daemon: Any) -> None:
    """T3 — Meeting end notification."""
    ...
    meeting = MeetingsRepository(session).get_by_id(meeting_id)
    ...
    daemon.post_message(f'*{meeting.title}* has ended.\n...')
    ...
    _reschedule_t4_checkin(daemon)
```

- **Where `meeting_id` is available at T2:** only as the default-arg binding
  `mid=meeting.id` on the scheduled lambda (line 318). `_send_t2()` re-queries the
  meeting by that id, posts a message, and returns. **Nothing persists it** — no
  daemon instance variable, no `system_state` key, no file. There is no
  `self._active_meeting` (or equivalent) written anywhere in `_send_t2`/`_send_t3`
  or the daemon. The June finding stands verbatim at v1.14.

#### Q2 — Can two T2s fire before an intervening T3? (overlap)

**Yes.** Each meeting gets an independent `t2_{id}` and `t3_{id}` DateTrigger job
keyed by its own `meeting.id` (lines 320, 329), fired at that meeting's
`start_time`/`end_time`. For overlapping or back-to-back meetings, meeting A's
`t2_A` (start) and meeting B's `t2_B` (start) both fire before A's `t3_A` (end) —
the jobs coexist because their ids differ. There is no single "current meeting"
slot and nothing serializes them. **Implication for #43: "active meeting" must be
modeled as a set/stack that tolerates overlap, not a scalar.** (Note the loop
reads `get_by_date()` — unfiltered — then skips cancelled inline at line 313,
rather than calling `get_active_for_date()`; OQ2's "show surfaces stay unfiltered"
asymmetry.)

#### Q3 — T3 / rescan behavior around context

- `_send_t3()` (364–384) fires at `end_time`, posts "has ended", reschedules T4.
  It clears nothing because there is nothing to clear.
- **Meetings without a T3:** if a meeting's `end_time <= now` at scan time, no T3
  job is scheduled (guard at line 325). **Daemon restart mid-meeting:**
  `_schedule_today_meeting_triggers()` reschedules only future triggers — a
  meeting already in progress (start passed, end future) gets a T3 but **no T2**,
  so its start notification is lost and, under any T2-sets-context design, its
  context would never be set on that restart.
- **Rescans** (register_all_jobs, lines 549–568): a **midnight** `CronTrigger(hour=0,
  minute=0)` rescan (id `t2t3_midnight_rescan`) and a **15-minute**
  `IntervalTrigger(minutes=15)` rescan (id `t2t3_interval_rescan`), both calling
  `_schedule_today_meeting_triggers` with `replace_existing=True`, plus an initial
  scan at startup (line 568). The 15-min interval means an impromptu meeting is
  picked up within ≤15 min; it also means any T2-set context is only as granular
  as these triggers, and a note logged during a meeting whose T2 was missed
  (restart case) would have no context to attach.

#### Q4 — `get_active_for_date()` + any current-time-window query

`workmain/database/repositories/meetings_repo.py`, `get_active_for_date()`
lines 286–307:

```python
# workmain/database/repositories/meetings_repo.py:286-307
    def get_active_for_date(self, target_date: date) -> List[Meeting]:
        """Get non-cancelled meetings on a specific date. ..."""
        return (
            self.session.query(Meeting)
            .filter(Meeting.start_time >= datetime.combine(target_date, time.min))
            .filter(Meeting.start_time < datetime.combine(target_date, time.max))
            .filter(Meeting.is_cancelled.is_(False))
            .order_by(Meeting.start_time.asc())
            .all()
        )
```

This is a **whole-day** query (all non-cancelled meetings for `target_date`),
filtered only on `start_time` falling within the day and `is_cancelled == False`.
**There is NO "which meeting is happening at datetime X" method** in the
repository — `grep` for time-window/`between`/current-time predicates finds only
`get_by_date` (266, unfiltered), `get_active_for_date` (above), and
`get_by_id` (155). A "meeting active at time T" query (`start_time <= T <
end_time`) does not exist and would have to be added, or the auto-link must derive
`meeting_id` from held T2 context (Q1) rather than a query.

#### Q5 — Schema absence + executor access to daemon context

- **`meeting_id` absent from both schema blocks:** confirmed. `create_time_entry`
  (Section 2 Q1) has no `meeting_id`; `create_note` (action 1, lines 45–54) has
  only `content` + optional `tags`. Neither models `meeting_id` — as expected, the
  model is not meant to extract it.
- **Does `ActionExecutor` have access to daemon-held context?** No. Both
  construction/call sites pass **only a session**:
  - `daemon.py:553` (block-action / Approve): `ActionExecutor(session).execute(action_dict)`
  - `daemon.py:611` (`_execute_action`, confirmed-pending path): `ActionExecutor(session).execute(action)`
  `ActionExecutor.__init__(self, session)` (action_executor.py:52–53) stores only
  the session; there is no `daemon`, no context object, no `meeting_id` channel.
  **Therefore a context-derived `meeting_id` cannot be injected today without a
  wiring change** — either (a) the daemon stamps `meeting_id` into the action dict
  before calling `execute()`, or (b) `ActionExecutor` is given the daemon/context
  at construction. Both presuppose that active-meeting context is being *held*
  somewhere first (Q1: it is not). This is a factual wiring statement, not a
  recommendation.

#### Q6 — Service `meeting_id` persistence (forward-compat confirmed)

- `notes_service.create_note(..., meeting_id: Optional[int] = None, ...)`
  (notes_service.py:23–30) forwards it: `NotesRepository(session).create(...,
  meeting_id=meeting_id, ...)` (line 66). Docstring: *"Forward-compatible; always
  None in v1."*
- `time_entry_service.create_time_entry(..., meeting_id: Optional[int] = None,
  ...)` (Section 2 Q4) forwards it: `TimeEntriesRepository(session).create(...,
  meeting_id=meeting_id, ...)` (time_entry_service.py:99).

Both accept and persist `meeting_id`. The entire #43 gap is upstream of the
services: (1) nothing holds the active meeting, (2) no time-window query exists,
(3) the executor has no path to context. The persistence target is ready.

---

### Section 4 — Weekly Prompt Reality Post-Item-#61 (#23, ex-#46)

**Headline: meetings do NOT enter the weekly_client OR daily_internal prompt today
— every section of both templates declares a `data_sources` list that omits
`meetings`, so `_get_meetings()` is never called for either report type. #23's
"internal meeting exclusion" is therefore moot under current wiring: there is zero
meeting content to exclude until meetings are first *added* to a section. The
weekly date range is hard-coded Mon–Fri; ScheduleService is never consulted in
prompt building. The `Meeting` model has no tag/visibility field.**

#### Q1 — Weekly date-range derivation; is ScheduleService consulted?

`workmain/ai/prompt_builder.py` (header **v2.3**, 20260724), `_get_date_range()`
lines 397–430 (weekly branch):

```python
# workmain/ai/prompt_builder.py:412-422 (v2.3)
        metadata = template.get("metadata", {})
        frequency = metadata.get("frequency", "daily")
        if frequency == "daily":
            return report_date, report_date
        elif frequency == "weekly":
            # Get Monday to Friday of the week containing report_date
            days_since_monday = report_date.weekday()
            start_date = report_date - timedelta(days=days_since_monday)
            end_date = start_date + timedelta(days=4)  # Friday
            return start_date, end_date
```

- **Hard-coded Mon–Fri calendar arithmetic.** `start = report_date − weekday()`
  (Monday), `end = Monday + 4 days` (Friday). No working-day logic.
- **`ScheduleService` is NOT consulted anywhere in prompt building** — no import,
  no `is_working_day()`, no `previous_working_day()` call in `prompt_builder.py`
  (grep confirms none). The range is a pure date span; the note/entry queries
  simply select rows whose date falls in `[Monday, Friday]`.
- **No code assumes exactly five populated weekdays or flags "missing" days.** A
  holiday inside the week is neither excluded nor flagged — it just contributes no
  rows. (The former Item #34 five-weekday-coverage gating and Item #46's
  substitutive branch lived in `build_weekly_prompt()`, which **Item #61 Gate 3
  removed** — per this file's own v2.3 history note; nothing replaced that
  gating.)

#### Q2 — Meeting fetch + formatting path

`_get_meetings()` (prompt_builder.py) fetches via
**`MeetingsRepository.get_for_date_client(start_date, end_date, client_id,
filter_client)`** — NOT `get_active_for_date()` and NOT the plain `get_by_date()`:

```python
# workmain/ai/prompt_builder.py — _get_meetings()
        meetings = self.meetings_repo.get_for_date_client(
            start_date=start_date, end_date=end_date,
            client_id=self._client_id, filter_client=self._filter_client,
        )
        return [{
            "title": meeting.title,
            "start_time": meeting.start_time.strftime("%H:%M"),
            "duration_minutes": int((meeting.end_time - meeting.start_time).total_seconds() / 60),
            "attendees": len(meeting.attendees) if meeting.attendees else 0
        } for meeting in meetings]
```

`get_for_date_client()` (meetings_repo.py:117–150) is a `start_time`-range query
with an optional `client_id` WHERE clause — **it does NOT filter `is_cancelled`.**
So *if* meetings were fed into a section, **cancelled meetings would enter the
prompt** (unlike the notify/inspect surfaces that use `get_active_for_date()`).
Formatting, when reached (`_get_section_data` lines 384–393): a `### Meetings:`
header then one line per meeting `- {HH:MM} - {title} ({N attendees})` — i.e.
**the meeting title is injected verbatim** into that section's context. This is
the code that would leak an internal meeting title *if the gate below allowed it*.

#### Q3 — `data_sources` per section (both templates)

`templates/reports/weekly_client.json` (frequency `weekly`):

| Section | data_sources | tag_filter include / exclude |
|---|---|---|
| 1. What are you working on? | `["notes","time_entries"]` | incl client-report, both / excl internal-only, info-only |
| 2. When do you plan to complete these tasks? | `["notes"]` | incl carry-forward, client-report, both / excl internal-only, info-only |
| 3. Risks or Blockers? | `["notes"]` | incl blocker, client-report, both / excl internal-only, info-only |
| 4. Requests you are unsure of? | `["notes"]` | incl client-report, both / excl internal-only, info-only |
| 5. Location of Artifacts | `["notes"]` | incl client-report, both / excl internal-only, info-only |

`templates/reports/daily_internal.json` (frequency `daily`): Deliverables =
`["notes","time_entries"]`; Accomplishments, In-Progress Items, Blockers, Risks,
Need Help?, Tomorrow's Plan = `["notes"]`.

**No section of either template lists `meetings` in `data_sources`.** Given the
gate `include_meetings = ("meetings" in data_sources) if data_sources else True`
(prompt_builder.py:322–324) and the fact that every section has a **non-empty**
`data_sources` that omits `meetings`, `include_meetings` evaluates to **False for
every section in both templates**. Meetings are fetched for **neither**
weekly_client nor daily_internal today.

#### Q4 — `Meeting` model columns (no tag/visibility field)

From `workmain/database/models.py`, `Meeting.__table__.columns`:

```
id: INTEGER            outlook_id: VARCHAR(255)      outlook_recurring_id: VARCHAR(255)
title: VARCHAR(255)    start_time: DATETIME          end_time: DATETIME
attendees: ARRAY       is_recurring: BOOLEAN         is_manually_modified: BOOLEAN
is_cancelled: BOOLEAN  notes_captured: BOOLEAN       reminder_sent: BOOLEAN
condensed_summary: TEXT  condensed_at: DATETIME       client_id: INTEGER
created_at: DATETIME
```

- **No `tag`, `visibility`, `is_internal`, or `source` column exists.** (`Meeting`
  has no `source` field, unlike `Note`.) The only columns bearing on filtering for
  #23 are **`client_id` (INTEGER)** and **`is_cancelled` (BOOLEAN)**, plus `title`
  (VARCHAR) if a title-string heuristic is contemplated. Any per-meeting internal
  vs. client visibility flag would require a new column/migration (a DB gate — see
  CLAUDE.md Gate Discipline) or a derivation from `client_id`/title.

#### Q5 — End-to-end: does an internal meeting title reach a weekly_client section today?

**No.** For every weekly_client section, `include_meetings` is `False` (Q3), so
`_get_meetings()` is never invoked and no `### Meetings:` block is appended. An
`"Internal Sync"` meeting existing in the report week contributes **nothing** to
any weekly_client (or daily_internal) prompt section under current templates and
current `_get_section_data` gating. The only meeting-derived content that can
reach a report is via **condensed meeting summaries stored as notes** (the EOD
"condense" step writes `condensed_summary`; those enter through the `notes`
data source with their own tags), not through the `_get_meetings()` path.

**#23 blast radius, therefore:** the exclusion problem is not live today because
inclusion isn't either. Making #23 meaningful first requires a decision to add
`meetings` to some section's `data_sources`; only then does "which meetings, and
how to exclude internal ones" arise — at which point the absence of a
visibility field (Q4) and `get_for_date_client()`'s non-filtering of cancelled
(Q2) both become relevant. **Zero-cost verification path** (not executed here, no
provider call): `PromptBuilder(session).build_prompt(template, report_date)`
assembles and returns the full prompt string without invoking any AI provider
(generation happens later in `report_generator`), so printing its output for a
week containing an internal meeting would empirically confirm the meeting title
is absent — the code path above already proves it.

---

### Section 5 — Ambiguity / `unknown` Loop Delivered State

**The `unknown`/`follow_up` message is single-turn only. The daemon holds no
pending-clarification state — after sending a follow-up question it returns
without storing anything, so the user's next message is parsed from scratch with
no memory of the question. There is also no "confidence" metric anywhere in the
parse path; `unknown` is the model's own discrete classification, not a
threshold.**

#### Q1 — Three outcomes → exact user-facing message (from Section 1 Q7)

| Outcome | Where decided | Exact message to user |
|---|---|---|
| Model returns `{"action":"unknown","follow_up":X}` | daemon.py:590–592 | the model's `follow_up` text (e.g. the full "What would you like to do? I can log time, add a note, …" string, which is model output per system-prompt example line 123) |
| Parse **timeout / provider error** | daemon.py:583–585 (`except Exception`) | `Sorry, I couldn't understand that. Try rephrasing.` |
| Model returns **unparseable JSON** | `IntentParseError` (intent_parser.py:127–131) → same except | `Sorry, I couldn't understand that. Try rephrasing.` |

(An `unknown` with no `follow_up` key falls back to the short `What would you like
to do?` — daemon.py:591 default.) The `unknown` case and the error/timeout case
produce **different** strings, so they are distinguishable from the Slack side.

#### Q2 — Is any pending-clarification state held?

**No.** The complete inbound dispatch precedence, `WorkmAInDaemon` message handler
lines 511–532:

```python
# workmain/daemon/daemon.py:511-532 (v1.21)
        # Active EOD session takes priority over the confirmation gate
        if self._eod_manager.has_session(user_id):
            ... self._eod_manager.handle_reply(user_id, text) ...
            return
        if user_id in self._pending:
            pending = self._pending.pop(user_id)
            if self._gate.is_confirmation(text):
                self._execute_action(pending); return
            elif self._gate.is_rejection(text):
                self.post_message('Cancelled.'); return
            # Unrecognised reply — cancel pending, process fresh
            logger.info("Pending action cancelled by new message from user=%s", user_id)
        self._dispatch_message(user_id, text)
```

There are exactly **two** inbound-state stores (declared at daemon.py:423–425):
`self._eod_manager._sessions` (EOD workflow step state, T5) and `self._pending`
(`{user_id: action_dict}` — a *parsed action awaiting confirm/reject*, NOT a
clarification answer). `self._gate = ConfirmationGate()` (line 426) is used
statelessly for text classification (`is_confirmation`/`is_rejection`) and Block
Kit formatting; it holds no per-user pending question.

Crucially, the `unknown` branch in `_dispatch_message` (lines 590–593) posts the
`follow_up` and **returns without writing `self._pending`** (that write only
happens for a real actionable type at line 599). So after a follow-up question:
the user's next message is not in an EOD session and not in `_pending` → it falls
straight to `self._dispatch_message()` → **a fresh `parser.parse(text)` with zero
memory of the prior question**. No clarification/answer-linking state exists in
`daemon.py`, `slack_eod.py`, or the confirmation gate.

#### Q3 — Classification of the checklist line

The checklist line *"Ambiguous input handling: follow-up question when parse
confidence is low"* is delivered at **(b) the single-turn level only** — a
clarifying question IS asked (the model's `follow_up` when it returns `unknown`,
posted at daemon.py:592), but the answer starts from zero: no state links the next
message to the question (Q2). Two additional precisions:

- **There is no "confidence" mechanism.** Nothing in `parse()` computes or
  thresholds a confidence score; the branch is driven solely by the model
  emitting `"action":"unknown"` (a discrete class, schema action 9). The
  "confidence" framing in the checklist is not reflected in code.
- So the honest reading is between (b) and (c): a *stateless* clarifying question
  exists (closer to (b)), but the *stateful low-confidence follow-up loop* the
  checklist envisions — ask, remember, interpret the reply as the answer — is
  **not delivered** ((c)). Supporting code: daemon.py:590–593 (post-and-return,
  no state) and the absence of any clarification store in the dispatch chain
  (511–532).

---

### Section 6 — Action Type Extensibility Re-Verification (Decision D8)

**Dispatch is a dict lookup. Adding an action type touches the system prompt
(+ Modelfile rebuild), the executor dispatch dict + a new handler, optionally a
confirmation-gate branch (a generic fallback exists), and tests. `intent_parser.py`
needs NO change — the parser is a pass-through (Section 2 Q3). The coupling is the
raw action-type STRING, hardcoded in each file (no shared enum/constant).**

#### Q1 — Dispatch mechanism (v1.4)

`workmain/orchestration/action_executor.py` (**v1.4**), lines 73–85 — a **dict
lookup** (not an elif chain, not `match`):

```python
# workmain/orchestration/action_executor.py:73-85 (v1.4)
        dispatch = {
            "create_time_entry":    self._execute_create_time_entry,
            "create_note":          self._execute_create_note,
            "update_task":          self._execute_update_task,
            "defer_task":           self._execute_defer_task,
            "confirm_report":       self._execute_confirm_report,
            "correct_report":       self._execute_correct_report,
            "deduplicate_task":     self._execute_deduplicate_task,
            "write_correction_note": self._execute_write_correction_note,
        }
        handler = dispatch.get(action_type)
        if handler is None:
            raise ActionExecutorError(f"Unknown action_type: '{action_type}'")
```

(Note: `start_eod` is NOT in this dict — it is intercepted earlier in
`daemon._dispatch_message` at line 595 and routed to the EOD manager, never
reaching the executor. So the executor dispatch and the model's action vocabulary
are not 1:1.)

#### Q2 — Files that must change to add a new action type

| File | Required addition |
|---|---|
| `config/intent_parse_system_prompt.txt` | New numbered action block (fields, IMPORTANT rules, examples); the model won't emit unlisted fields/actions (rule line 139). **+ Modelfile SYSTEM sync + `build_workmain_intent.sh` rebuild on the LXC** (IaC, human gate — Section 2 Q6). |
| `workmain/ai/intent_parser.py` | **NONE.** `parse()` returns `json.loads(raw)` verbatim; no whitelist/validation/coercion (Section 2 Q3). A new action flows through untouched. |
| `workmain/orchestration/action_executor.py` | One entry in the `dispatch` dict (lines 73–82) **and** a new `_execute_<type>(self, action)` handler method. |
| `workmain/orchestration/confirmation_gate.py` | **Optional.** `format_prompt()` is an `if action_type == …` chain (lines 54–103) with a **generic fallback** at line 104: `return f"I'll execute '{action_type}'. Confirm? (yes/no)"`. A new type works without a branch (generic prompt); a tailored prompt needs one added `if`. `format_blocks()` (106+) just wraps `format_prompt()`, so no separate change. |
| tests | New handler test(s); a gate-format test if a branch was added. |

**Independent or lockstep?** Lockstep on the **action-type string literal**: the
same string is (a) emitted by the model per the prompt, (b) used as the `dispatch`
dict key, and (c) matched in the gate's `if` chain (if a branch is added). There
is **no shared constant or enum** — each file hardcodes the literal, so a typo in
any one silently routes to the generic path or the `Unknown action_type` error.
The prompt↔executor pair is the hard-coupled minimum; the gate branch and parser
are not required (parser never, gate only for tailored UX).

#### Q3 — Change since June (cascade longer or shorter?)

- The dispatch is **still a dict lookup**; v1.4's only structural addition to the
  dispatch was `write_correction_note` (a new 8th entry) plus fixes to the
  confirm/correct handlers — no change to the *extension pattern*.
- The cascade is **no longer than June and arguably shorter**, for two reasons
  both re-verified here: (1) `intent_parser.py` is a pure pass-through, so it is
  NOT in the cascade at all (Section 2 Q3); (2) `confirmation_gate.format_prompt`
  has a generic fallback (line 104), so the gate is an *optional* touchpoint, not
  a required one. No per-type handling added in Sprint 3 / the ops sprint length­ens
  the chain — the ops sprint's changes were within existing handlers, not new
  per-type branches elsewhere. The minimal hard cascade to add a type remains:
  **system prompt (+ rebuild) → executor dict + handler → tests.**

---

### Open Questions

These require Ray's input or an LXC-side action; the recon does not resolve them
(all are design/remediation calls for Role 1, or data only Ray can supply).

1. **Which exact string does Ray see for "non-standard input" on Slack?** The code
   makes model-`unknown` (the full "What would you like to do? I can log time…"
   follow-up) and parse-timeout ("Sorry, I couldn't understand that. Try
   rephrasing.") **distinguishable** (Section 1 Q7, Section 5 Q1). If it's the
   former, the Slack `parse()` path is healthy and the issue is model
   classification quality; if it's the latter, the Slack path is *also* timing out
   and shares the task-match root cause. This changes whether the sprint needs any
   Slack-path latency work at all. *Needed: Ray to quote the literal message.*

2. **parse_task_match remediation direction (Role 1 design call).** The recon
   establishes the cause but proposes no fix. The decision space touches at least:
   the 30 s timeout value vs. task-match latency; `stream=true` (so the read never
   idles 30 s) vs. staying `stream=false`; wrapping the bare `TimeoutError` so
   provider-manager fallback engages; making Step 3c re-evaluate availability or
   fall back per-item on timeout rather than one-shot; and whether the ~1800-token
   SYSTEM prompt should ride the task-match call at all (it is not needed for a
   task↔note match and is the bulk of the `prompt_eval` cost). *These are locked
   architecture surfaces (OllamaProvider, IntentParser, eod_workflow) — Role 1
   must choose; Role 2 will not.*

3. **LXC server-side confirmation (optional, Ray to run).** SSH to the Ollama LXC
   was unavailable from this session. If a server-side view is wanted, run on the
   LXC during a live `workmain eod` task-match: `ollama ps`, `ollama list`, and
   `journalctl -u ollama -f` (or the Ollama server-log tail), to confirm
   production-shaped requests arrive and to read server-side `prompt_eval_duration`
   under real load. The client-side evidence (Section 1 Q8) already establishes the
   cause; this is corroboration only.

4. **#23 scope confirmation.** Because meetings currently enter *no* report prompt
   (Section 4), "internal meeting exclusion" presupposes a prior decision to *add*
   meetings to a section's `data_sources`. *Needed from Role 1: is #23 (a) purely
   defensive (ensure meetings stay out — already true, near-zero work), or (b) an
   intent to surface client meetings in weekly_client while excluding internal
   ones — which requires a visibility signal the `Meeting` model lacks (new
   column/migration = DB gate, or a client_id/title heuristic)?*

5. **#43 active-meeting source of truth.** Auto-linking `meeting_id` needs an
   active-meeting holder that tolerates overlap (Section 3 Q2). *Needed from Role 1:
   should this be daemon-held state set at T2/cleared at T3 (loses context on
   restart mid-meeting, Section 3 Q3), a new `system_state` key, or a new
   "meeting active at time T" repository query — and how should overlapping
   meetings resolve to a single link?* This is an architecture decision, not a
   code detail.

6. **entry_date validation policy (#44).** `time_entry_service.create_time_entry`
   accepts any `entry_date` with **no future/past guard** and backdates the linked
   note (Section 2 Q4). *Needed from Role 1: should a model-supplied `entry_date`
   be range-validated (e.g. reject future dates), and which parse helper should own
   the ISO-string→date conversion (Section 2 Q5 lists candidates; recon chose
   none)?*

---

### Addendum A (20260725) — `ProviderManager.generate()` override/fallback seam (micro-recon, requested by Role 1)

**Question from Role 1:** under `provider_override=ProviderType.OLLAMA`, when
`provider.generate()` raises a `ProviderError` (the world Fix 2 newly creates by
wrapping the timeout), does `ProviderManager.generate()` pin the provider and
propagate the error, or does it fall back to another provider (Claude)? This seam
was referenced but not quoted in Section 1.

**Answer: it PINS the provider — no fallback. The wrapped error propagates to the
caller (`parse_task_match()`). It does NOT route to Claude.**

`workmain/ai/provider_manager.py` (header **v1.2**, 20260603),
`ProviderManager.generate()` lines 166–235, verbatim:

```python
# workmain/ai/provider_manager.py:186-235 (v1.2)
        if provider_override:
            primary = provider_override
            fallback = None
            fallback_mode = FallbackMode.MANUAL
        elif report_type and report_type in self._report_configs:
            config = self._report_configs[report_type]
            primary = config.primary_provider
            fallback = config.fallback_provider
            fallback_mode = config.fallback_mode
        else:
            primary = ProviderType.CLAUDE
            fallback = ProviderType.GEMINI
            fallback_mode = FallbackMode.AUTO

        try:
            provider = self.get_provider(primary.value)
            response = provider.generate(request)
            return response, False

        except (ProviderError, RateLimitError) as e:
            if not fallback:
                raise ProviderError(
                    f"Primary provider {primary.value} failed and no fallback configured"
                ) from e

            if fallback_mode == FallbackMode.MANUAL:
                raise ProviderError(
                    f"Primary provider {primary.value} failed. "
                    f"Fallback to {fallback.value} available but manual mode enabled. "
                    f"Use --provider {fallback.value} to retry."
                ) from e

            try:
                fallback_provider = self.get_provider(fallback.value)
                ...
                response = fallback_provider.generate(request)
                return response, True
            except (ProviderError, RateLimitError) as fallback_error:
                raise ProviderError(...) from fallback_error
```

**Trace under `provider_override=ProviderType.OLLAMA` (the intent-parse call site
— intent_parser.py:210 and :112 both pass this override):**

1. Lines 186–189 set `primary = OLLAMA`, **`fallback = None`**, `fallback_mode =
   MANUAL`.
2. `provider.generate(request)` raises the (Fix-2-wrapped) `ProviderError` /
   `ProviderUnavailableError` (the latter is a `ProviderError` subclass —
   base_provider.py:223).
3. `except (ProviderError, RateLimitError) as e` (line 205) catches it.
4. **First guard fires:** `if not fallback:` — `fallback is None` → True →
   `raise ProviderError("Primary provider ollama failed and no fallback
   configured") from e` (lines 207–209). Control never reaches the fallback
   provider call at line 227.
5. **Redundant second guard:** even if `fallback` were somehow set, `fallback_mode
   == FallbackMode.MANUAL` (line 211) would raise rather than fall back. Two
   independent guards both prevent any Claude/Gemini call under override.

**So Fix 3's world is confirmed: pinned provider, wrapped error propagates to
`parse_task_match()`. No wrong-model call, no API cost, no masking of the timeout
from Step 3c.**

**⚠️ Consequence Fix 2/3 MUST account for (Pitfall #12 — trace the actual object,
not the name):** the exception that reaches `parse_task_match()` is **NOT** the
wrapped timeout object. Line 207–209 raises a **new, generic `ProviderError`**
whose message is the literal `"Primary provider ollama failed and no fallback
configured"`, with the original wrapped error attached as `__cause__` (via
`from e`), which in turn has the underlying `socket.timeout`/`TimeoutError` as
*its* cause. Therefore:

- After Fix 2, `parse_task_match()`'s `except Exception as e:
  logger.warning("parse_task_match error: %s", e)` (intent_parser.py:231) will log
  **`parse_task_match error: Primary provider ollama failed and no fallback
  configured`** — the current `timed out` string **disappears**.
- Any Fix 3 demotion/fallback logic that keys on the **message substring
  `"timed out"`** will silently break once Fix 2 lands. Fix 3 should key on the
  exception **type** (`ProviderError` / `ProviderUnavailableError`) or walk
  `.__cause__` to recover the underlying `TimeoutError`, never on the message text.
- Current (pre-Fix-2) behavior for contrast: today the bare `TimeoutError` is
  NOT caught by line 205 (it is not a `ProviderError`), so it propagates raw and
  unchanged through `ProviderManager.generate()` to `parse_task_match()` — which
  is exactly why the current log reads `timed out` (Section 1 Q3/Q8). Fix 2 moves
  the exception from "raw, uncaught, passes through" to "caught, re-wrapped,
  re-raised as a different ProviderError" — a behavioral change at this seam, not
  just at the provider.

---

### Addendum B (20260725) — Item #62 close-out: EOD carry-forward query surfaces + notes view divergence (micro-recon, requested by Role 1)

Read-only pass, requested during Item #62 close-out. Four questions plus a
cross-cutting synthesis. All citations give file path, header version, and line
range; source quoted verbatim. No fixes proposed — divergences noted only.

#### (a) Step 3c skip-gate condition + attempt-set query (the Gate-4 blocker)

`workmain/workflows/eod_workflow.py` (header **v1.10**, 20260724),
`_run_task_match_step()`. **Skip-gate**, lines 469–479:

```python
# eod_workflow.py:469-479 (v1.10)
        has_cf_observations = False
        payload = state_io.read_last_inspection()
        if payload is not None and state_io.matches_target_date(payload, target_date):
            for obs in payload.get('observations', []):
                if obs.get('type') == 'carry_forward':
                    has_cf_observations = True
                    break

        if not has_cf_observations:
            print("  No carry-forward items flagged — skipping task match")
            return EodStepResult(status=EodStepStatus.COMPLETED)
```

3c runs ONLY if Step 3b's `last_inspection.json` payload both matches
`target_date` (`state_io.matches_target_date`) AND contains a `carry_forward`
observation. Two further skip conditions follow: no active tasks (lines 490–492),
no notes for the date (lines 497–499).

**Attempt-set query**, line 488:

```python
# eod_workflow.py:488 (v1.10)
        active_tasks = task_repo.get_filtered(status='active')
```

`TaskStatusRepository.get_filtered()`
(`workmain/database/repositories/task_status_repo.py`, lines 199–237) signature
defaults **`limit: int = 20`**:

```python
# task_status_repo.py:199-237
    def get_filtered(
        self,
        status: Optional[str] = 'active',
        search: Optional[str] = None,
        date_filter: Optional[date] = None,
        limit: int = 20,
    ) -> List[TaskStatus]:
        q = (
            self.session.query(TaskStatus)
            .join(Note, TaskStatus.note_id == Note.id)
        )
        if status and status != 'all':
            q = q.filter(TaskStatus.status == status)
        ...
        q = q.order_by(Note.created_at.desc())
        if limit:
            q = q.limit(limit)
        return q.all()
```

The query keys purely on `TaskStatus.status == 'active'` — **no date filter, no
source filter, no carry-forward-tag filter** — joins Note, orders by
`created_at DESC`.

⚠️ **STANDOUT / likely Gate-4 blocker:** 3c calls `get_filtered` with the
**default `limit=20`**, so with >20 active tasks it silently attempts only the 20
most-recently-created. Contrast Step 3d (line 712) which passes `limit=0`
(unlimited). Asymmetry between the two AI substeps of Step 3.

#### (b) Step 3d "new carry-forward notes today" query — source filter? "today"/"new" basis?

`_run_note_dedup_step()`. **Pool query**, line 712:

```python
# eod_workflow.py:712 (v1.10)
        active_tasks = task_repo.get_filtered(status='active', limit=0)
```

**Source filter: NO.** `get_filtered` never references `Note.source`; filters
solely on `TaskStatus.status == 'active'`. Any active task qualifies regardless of
source (`'meeting'`/`'task'`/`'ad-hoc'` per `models.py:221`).

**"today"/"new" basis** — Python partition, lines 720–726:

```python
# eod_workflow.py:720-726 (v1.10)
        for ts in active_tasks:
            if not ts.note or not ts.note.content:
                continue
            if ts.note.created_date == target_date:
                today_tasks.append(ts)
            else:
                existing_tasks.append(ts)
```

"New/today" ⟺ `Note.created_date == target_date`. `created_date` is a
**DB-computed generated column** —
`Column(Date, Computed("(created_at::DATE)"))` (`models.py:233`) — i.e.
`created_at::DATE` in the DATABASE timezone, not the caller's local date. Also:
"carry-forward" here means *active TaskStatus*, NOT `Note.tags @> ['carry-forward']`
— a note whose CF tag was later removed but whose TaskStatus is still `active`
still counts.

#### (c) Pre-flight carry-forward check working-day logic

`_run_pre_flight_inspection_step()` (eod_workflow.py:407) →
`InspectionEngine.run(target_date)` → `_check_carry_forward()`
(`workmain/daemon/inspection_engine.py`, lines 226–280):

```python
# inspection_engine.py:238-258
        prev_biz_day = ScheduleService(self.session).previous_working_day(target_date)

        prev_cf_notes = (
            self.session.query(Note)
            .filter(
                Note.created_date == prev_biz_day,
                Note.tags.op('@>')(['carry-forward']),
            )
            .all()
        )
        if not prev_cf_notes:
            return []

        today_cf_notes = (
            self.session.query(Note)
            .filter(
                Note.created_date == target_date,
                Note.tags.op('@>')(['carry-forward']),
            )
            .all()
        )
        today_contents = {n.content.strip().lower() for n in today_cf_notes}
```

Working-day logic = **`ScheduleService.previous_working_day(target_date)`**
(line 238) — steps back over weekends/holidays. Flags a CF item when a
`carry-forward`-**tagged** note existed on the previous working day and no
CF-tagged note with the same content (case-insensitive, stripped) exists on
`target_date`. This path keys on the **actual `carry-forward` tag**, not on
TaskStatus.

#### (d) `notes show` vs `notes today` — tag-loading paths + divergence

`workmain/cli/commands/notes.py`. **`notes show`** (lines 918–958) →
`_resolve_note()` (lines 237–279) → `get_by_id()` (digit id) or
`find_by_content_like()` (substring). Single note, no date scoping, no tag filter:

```python
# notes.py:942, 953 (show render)
        console.print(f"Tags:       {note.display_tags if note.tags else '(none)'}")
        ...
        source = note.source or 'ad-hoc'
        console.print(f"Source:     {source}")
```

**`notes today`** (lines 961–1007) → `get_today(include_tags)` →
`get_by_date(date.today(), include_tags)`
(`workmain/database/repositories/notes_repo.py`, lines 166–178):

```python
# notes_repo.py:166-178
        query = self.session.query(Note).filter(Note.created_date == target_date)
        if include_tags:
            query = query.filter(Note.tags.op('&&')(include_tags))   # OR / overlap
        if exclude_tags:
            for tag in exclude_tags:
                query = query.filter(~Note.tags.op('@>')([tag]))
        return query.order_by(Note.created_at).all()
```

Renders via `format_note_display()` → `note.display_tags if note.tags`
(notes.py:107–108).

**Where they diverge — and where they do NOT:**

- **Tag loading/rendering is IDENTICAL.** Both read `note.tags` (a scalar
  `ARRAY(Text)` column, `models.py:220` — loaded with the row, no relationship,
  no lazy/deferred fetch) and format via the same `display_tags` property →
  `format_tags(self.tags)` (`models.py:249-256`), guarded by `if note.tags`.
  **There is no eager/lazy tag-load difference between the two commands.**
- **Selection diverges:** `show` = one note by id/substring, unscoped by date;
  `today` = a list scoped to `Note.created_date == date.today()`.
- **"today" basis diverges from local:** `notes today` passes the process-local
  `date.today()` but filters the DB-computed `created_date` (`created_at::DATE`,
  DB timezone). If DB TZ ≠ local TZ, a near-midnight note's `created_date` can be a
  day off from local "today" — so a note visible via `notes show <id>` can be
  ABSENT from `notes today` (and, symmetrically, from Step 3c's
  `get_by_date(target_date)` and Step 3d's partition). This is the CLAUDE.md
  known `created_date`-is-DB-computed asymmetry biting at a view boundary.
- **Tag *filtering* diverges:** `today -t` applies `Note.tags && include_tags`
  (overlap); `show` never filters tags.

#### Cross-cutting synthesis (observation, not a fix)

The EOD pipeline carries **three non-identical definitions of "carry-forward,"**
which can legitimately disagree on the same note:

| Surface | "Carry-forward" means | Date basis |
|---|---|---|
| Pre-flight / inspection (c) | `Note.tags @> ['carry-forward']` | `previous_working_day` vs `target_date` |
| 3c attempt set (a) / 3d pool (b) | `TaskStatus.status == 'active'` (tag-independent) | 3c: any date, **limit 20**; 3d: `created_date == target_date` |
| `notes today -t cf` (d) | `Note.tags && ['carry-forward']` | `created_date == date.today()` |

A note whose CF tag was removed while its TaskStatus stayed `active`, or an active
task whose `created_date` sits a day off from local "today," surfaces in one lens
and not another. The (a) `limit=20` cap and the `created_date`-vs-local divergence
are the strongest candidates behind the Item #62 close-out complications. Any
remediation is a design call for Role 1 — this addendum records the facts only.
