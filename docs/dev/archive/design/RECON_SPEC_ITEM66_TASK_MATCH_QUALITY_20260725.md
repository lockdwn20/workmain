WorkmAIn
RECON_SPEC_ITEM66_TASK_MATCH_QUALITY v1.0
20260725

---

## Critical Instructions — Read Before Acting

**This is a read-only pass. No code changes, no fixes, no refactors, no
suggestions inline with findings.** Verbatim source quotations and
observations only. Read-only shell commands (grep, psql SELECT, git log)
are permitted where explicitly requested below. No writes of any kind
outside the Findings section of this document.

**Pitfall #12 applies throughout (component-verified ≠ integration-verified).**
The central question of Section F is not "does a creation mechanism exist" —
it is "what actually invokes it, from which live surface, and does that
surface run in Ray's daily flow." A hook that exists but is never called is
the expected failure shape here. Trace every call site's provenance; do not
stop at confirming the leaf function works when handed the right input.

**Version anchors:** codebase v1.26.1 (post-#62 merge, `main`==`dev`).
`intent_parser.py` v1.4+, `eod_workflow.py` v1.11+, `ollama.py` v1.4+ —
verify actual versions in file headers and quote line numbers against what
is on disk NOW, not against the 20260725 sprint recon's v1.26.0 quotes.

**Output:** Append all findings to the END of this same file, below the
`## Findings` placeholder. Do not create a separate output file. Complete
and document each section in full before proceeding to the next. Work
sequentially; no parallel agents or sub-tasks.

---

## Purpose

Gate 0 recon for Item #66 (raw-mode task-match output quality — carries
#62's AC3/AC8) and, in Section G, evidence expansion for Item #67
(`get_filtered` silent limit cap). Produces the source facts needed to:

- Determine whether the observed false 1.00-confidence match candidate can
  originate from the keyword scorer or must be the LLM path (Section E)
- Explain why CF-note → TaskStatus creation has effectively ceased, which
  gates AC8 staging and explains Step 3d's permanent empty-pool behavior
  (Section F)
- Confirm the CLI `tasks list` surface shares #67's silent cap and document
  its exact semantics (Section G)

## Context — Live Evidence (20260725, Ray's terminal)

Three commands, same database, seconds apart:

| Command | Header reported | Rows shown | Notes |
|---|---|---|---|
| `tasks list` | "20 found, status=active" | 20 | newest ID 15053 (2026-06-24) |
| `tasks list --all` | "20 found" | 20 | completed rows included; still 20 rows; completed rows displace active ones |
| `tasks carryover` (deprecated) | "143 found, status=active" | 143 | full active set |

Observed task-creation timeline from the full 143-row listing:

- Bulk of tasks: created 2026-02-02 → **2026-05-27** (Phase 12 / PC-2
  task carry-forward shipped v1.16.0 on 20260528; task 2727 "Gate3 test
  note for carry-forward hook", 2026-05-27, is a PC-2 test artifact)
- Exactly **one** task created after that: ID 15053, **2026-06-24**
- **Zero** tasks created 2026-06-25 → today, despite daily EOD runs and
  daily CF-tagged notes (the pre-flight inspection CF check has been
  matching tag-based CF notes throughout this period — see #62 session
  Saturday-run evidence)
- ID sequence gap: 2727 → 15053 with nothing between in the task listing

---

## Section E — `_keyword_score_match` Internals

Goal: determine whether the keyword fallback scorer can emit a 1.00
confidence, or whether the observed false 1.00-confidence candidate
(non-deterministic across two identical runs — #62 Gate 4 exploration)
must have come from the LLM path.

**Questions:**

E1. Quote `_keyword_score_match` (and any helper it calls for
    tokenization/normalization) verbatim from its current location, with
    file path, version header, and line range.

E2. State the scoring metric precisely: what is compared to what, how the
    score is computed, its theoretical range, and under exactly what input
    conditions it can reach 1.00 (identical strings? subset match? empty
    edge case?).

E3. Is the scorer deterministic for identical inputs? Identify any source
    of ordering or nondeterminism (set iteration, dict ordering, DB result
    ordering feeding it).

E4. Quote the call site(s): where in Step 3c does keyword scoring run —
    only when the LLM path is demoted, always as a pre-filter, or both?
    Confirm whether a keyword-scored candidate and an LLM-scored candidate
    are distinguishable in the confirmation UI / logs (i.e., could Ray's
    observed 1.00 candidate be attributed to a path from the output alone?).

## Section F — CF-Note → Active TaskStatus Creation (HIGHEST PRIORITY)

Goal: establish the complete mechanism and its live invocation status. The
evidence above says creation worked during/around PC-2 implementation
(bulk backfill or hook-driven through 2026-05-27), fired once on
2026-06-24, and has not fired since. Explain that shape from source and
history.

**Questions:**

F1. Locate EVERY code path that creates a `TaskStatus` row (grep for the
    model/repo constructor and any `create`/`add` on the tasks repo).
    Quote each creation call site verbatim with file, version, line range.
    For each: trace provenance upward — which command, workflow step,
    daemon trigger, or migration/backfill script reaches it, and under
    what conditions.

F2. For the PC-2 carry-forward hook specifically (Phase 12,
    `FEATURE_SPEC` references "carry-forward hook"; test task 2727 names
    it): where does it live NOW at v1.26.1, what invokes it, and is that
    invoking surface part of Ray's daily flow (`workmain eod`, daemon
    triggers, note-creation commands, Slack path)? If it is wired into an
    EOD step: state precisely which step, and whether `--skip task_match`
    (Ray's daily workaround 2026-06-24 → #62 merge) would have bypassed it.

F3. Git history: `git log --oneline --follow` on the file(s) containing
    the hook and its call sites, from v1.16.0 (20260528) to HEAD. Identify
    any commit (DB Schema Sprint v1.22.0, keep-alive hotfix 20260624,
    Sprint 3 v1.23.0, #60, #61, #62) that moved, rewired, or orphaned the
    hook or its invoking surface. The single 2026-06-24 firing and the
    silence afterward should correlate with something in this history —
    name the commit(s) if so, or state explicitly that history shows no
    change and the explanation must be behavioral (e.g., skip-flag usage).

F4. Read-only DB verification (psql, SELECT only):
    - `SELECT status, COUNT(*) FROM task_status GROUP BY status;`
    - Creation timeline: count of task_status rows joined to their note's
      `created_date`, grouped by month (confirm the Feb–May bulk, the
      single June row, the zero since).
    - Post-2026-06-24 CF-tagged notes lacking TaskStatus: count of notes
      with `tags @> ARRAY['carry-forward']` and `created_date >
      '2026-06-24'` that have no task_status row. A nonzero count is the
      defect made concrete; quote the number.

F5. Clarify the `tasks list` ID column: is it `task_status.id` or
    `note_id`? Explain the 2727 → 15053 gap accordingly (shared sequence,
    note-id passthrough, or genuine row-id gap).

F6. AC8 staging determination (the ask this section exists to answer):
    given F1–F4, state exactly what actions would be required TODAY to get
    a staged CF-note pair into Step 3c's attempt set and Step 3d's
    today-partition — or state that no user-reachable action produces a
    TaskStatus at v1.26.1 (in which case AC8 is unverifiable until the
    creation mechanism is repaired).

## Section G — CLI `tasks list` Limit Surface (routes to Item #67)

G1. Quote the `tasks list` command implementation (file, version, lines):
    how it calls `get_filtered`, which limit it passes (or omits →
    default 20), and what `--all` actually maps to (status filter only?).

G2. Quote where the "N found" header count comes from — is it
    `len(results)` post-limit (i.e., the header can never exceed the cap
    and misreports the true match count)?

G3. Quote the `tasks carryover` deprecated path showing how it avoids the
    cap (limit=0 or different repo call).

G4. Confirm against `CLI_STANDARDS.md` §5.3 whether `--all` is specified
    to mean "all statuses," "no row limit," or both — quote the standard's
    wording. Note (observation only): `-all` currently errors as
    "No such option: -a" (Click short-option parsing).

---

## Findings

<!-- Opus: append all findings below this line, section by section
     (E, then F, then G). Verbatim quotes with file/version/line ranges.
     Do not edit anything above this line. -->

**Recon performed:** 2026-07-25, Opus (Role 2). Read-only. Codebase on disk:
`workmain/__version__.py` v1.26.1; `git branch --show-current` = `dev`;
`git diff main dev --stat` empty (main == dev, confirmed). Version anchors verified
against file headers on disk: `eod_workflow.py` **v1.11** (20260725), `intent_parser.py`
**v1.4** (20260725), `ollama.py` header not re-quoted here (not needed for E/F/G — no
finding depends on it beyond the #62 raw-mode note already in the version log).

---

### Section E — `_keyword_score_match` Internals

**E1 — Verbatim source.** `workmain/workflows/eod_workflow.py` **v1.11**, lines 195–235.
The scorer is two module-level functions plus a stop-word set and tokenizer:

```python
# eod_workflow.py:195-214
_STOP_WORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'was', 'will', 'have', 'has', 'had',
    'been', 'be', 'are', 'were', 'that', 'this', 'it', 'its', 'i', 'my',
    'me', 'we', 'our', 'you', 'they', 'their', 'he', 'she', 'him', 'her',
    'do', 'did', 'get', 'got',
}


def _tokenize(text: str) -> set:
    """Lowercase, strip punctuation, split on whitespace, remove stop words."""
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    return {t for t in text.split() if t not in _STOP_WORDS}


def _score_match(task_tokens: set, entry_tokens: set) -> float:
    """Score = overlap / task token count. Returns 0.0 if task_tokens is empty."""
    if not task_tokens:
        return 0.0
    return len(task_tokens & entry_tokens) / len(task_tokens)
```

```python
# eod_workflow.py:217-235
def _keyword_score_match(task, notes: list) -> dict:
    """Score a carry-forward task against today's notes using keyword overlap.

    Returns dict with keys: score (float 0.0-1.0), note (Note|None).
    """
    task_note = task.note
    if not task_note or not task_note.content:
        return {"score": 0.0, "note": None}
    task_tokens = _tokenize(task_note.content)
    best_score = 0.0
    best_note = None
    for note in notes:
        if not note.content:
            continue
        score = _score_match(task_tokens, _tokenize(note.content))
        if score > best_score:
            best_score = score
            best_note = note
    return {"score": best_score, "note": best_note}
```

**E2 — Scoring metric, precisely.** The score is **directional token-recall of the task
against a candidate note**: `len(task_tokens & note_tokens) / len(task_tokens)`
(`_score_match`, line 214). Not Jaccard, not symmetric — the denominator is the *task's*
token count only. Range: **[0.0, 1.0]**. It reaches **1.00 whenever every task token
(after lowercasing, punctuation-stripping, and stop-word removal) is present in a
candidate note's token set** — i.e. the task's content-words are a **subset** of the
note's content-words. Identical strings are the trivial case; a subset is sufficient and
is the far more common way to hit 1.00 (e.g. task "Call Bob" → note "Called Bob back
about the invoice this morning" yields tokens `{call, bob}` ⊆ note tokens → **1.00**).
Empty edge case: if the task's post-tokenization set is empty (content is only stop-words
/punctuation), `_score_match` returns 0.0 (guarded, line 212–213), and
`_keyword_score_match` also returns `{"score": 0.0, "note": None}` when the task note is
missing/empty (line 223–224). So **1.00 is readily reachable and is NOT rare** — it does
not require string identity, only task-token containment.

**E3 — Determinism.** The **score value is fully deterministic** for identical inputs:
`_score_match` is pure set-cardinality arithmetic; token *set* iteration order does not
affect `len(a & b)` or `len(a)`. The **only** nondeterministic element is **which note
wins a tie** for `best_note`: the loop uses strict `if score > best_score` (line 232), so
the *first* note reaching the max score is kept, and "first" depends on the ordering of
the `notes` list. That list is `candidate_notes`, derived from
`note_repo.get_by_date(target_date)` (eod_workflow.py:495) — see G/F for its ordering.
**Bottom line for E3: the keyword scorer cannot produce a nondeterministic *score*.** A
given (task, note-set) yields the same 1.00 (or same sub-1.0) on every run; only the
identity of the matched note could vary under exact ties.

→ **Consequence for the central Section-E question:** Ray's observed false 1.00 that
appeared in one run and not in an identical re-run (#62 Gate 4 exploration) **cannot
originate from the keyword scorer** — that path is score-deterministic. It is consistent
only with the **LLM path** (`parse_task_match`), which returns a model-emitted
`confidence` float parsed straight from Mistral's JSON (`intent_parser.py:234`,
`"confidence": float(result.get("confidence", 0.0))`) under temperature-based sampling.
The model can and does emit `"confidence": 1.0`, and its output varies run-to-run.

**E4 — Call sites in Step 3c and path-attributability.**
`_run_task_match_step()` (eod_workflow.py:445). Ollama is probed once per step
(lines 503–521); if `check_availability() == ProviderStatus.AVAILABLE` the LLM path is
armed (`ollama_available = True`). Per task (loop at line 541):

```python
# eod_workflow.py:570-591
            if ollama_available:
                try:
                    result = intent_parser.parse_task_match(ts, candidate_notes)
                except ProviderError as e:
                    ollama_available = False
                    print(
                        f"  ⚠ Ollama generation failed ({e}); falling back to "
                        f"keyword matching for this and remaining tasks. "
                        f"Cause: {e.__cause__}"
                    )
                else:
                    if result["confidence"] < 0.7:
                        continue
                    matched_note = notes_by_id.get(result["note_id"])
                    candidates.append((result["confidence"], ts, matched_note))
                    continue
            # keyword path — reached when ollama_available is False at loop
            # entry OR immediately after demotion for the item that raised
            result = _keyword_score_match(ts, candidate_notes)
            if result["score"] < 0.2:
                continue
            candidates.append((result["score"], ts, result["note"]))
```

So keyword scoring is **not** a pre-filter and **not** always-on — it runs **only when the
LLM path is unavailable**: either Ollama failed the initial availability probe
(`ollama_available == False` at loop entry) **or** a `ProviderError` demoted it mid-loop
(line 574), after which every remaining task uses keyword. When Ollama is reachable (Ray's
normal state post-#62), **every** task goes through the LLM path and keyword never runs.
Thresholds differ by path: LLM candidates need `confidence >= 0.7` (line 581); keyword
candidates need `score >= 0.2` (line 589).

**Path is NOT distinguishable from the confirmation UI or the candidate record.** The
candidate tuple is `(score, ts, note)` with no path tag; the review UI shows only a
derived label and the raw number (eod_workflow.py:623, 630):
`confidence = "high" if score >= 0.5 else "medium"` and
`print(f"  Match found ({confidence} confidence — {score:.2f}):")`. A 1.00 renders
identically ("high confidence — 1.00") whether it came from the LLM or from a keyword
subset match. The **only** path signal in the output is the demotion warning at line
575–579 — if that line did **not** appear earlier in the run, all candidates in that run
came from the LLM path. Therefore Ray's 1.00 is attributable to the LLM **if** no
"⚠ Ollama generation failed … falling back to keyword" warning preceded it in that run
(the expected situation when Ollama is up). The score alone is not attributive.

---

### Section F — CF-Note → Active TaskStatus Creation (HIGHEST PRIORITY)

> **SUPERSEDED (TM7, 20260728):** corrected by
> `RECON_SPEC_TASK_MATCH_DATA_INTEGRITY_SPRINT_20260725.md` §I2 — the 147
> pre-2026-05-28 task rows are a migration-015 backfill artifact, not
> live hook output; the live hook has fired exactly once ever
> (2026-06-24). Do not cite F1/F3 below uncorrected.

**F1 — Every TaskStatus-row creation path.** The model constructor `TaskStatus(...)` is
called in exactly **one** place: `TaskStatusRepository.create_active()`
(`workmain/database/repositories/task_status_repo.py` **v1.1**, line 54:
`ts = TaskStatus(note_id=note_id, status='active')`). `create_active` is reached by
`ensure_active()` (same file, line 80) for the not-yet-tracked case. Grepping every caller
of `create_active`/`ensure_active` across `workmain/**.py` yields **exactly two live call
sites**, both in `workmain/cli/commands/notes.py`:

- **`notes add`** — `notes.py:375-377`:
  ```python
          if 'carry-forward' in (note.tags or []):
              TaskStatusRepository(session).ensure_active(note.id)
              session.commit()
  ```
- **`notes edit`** — `notes.py:500-507` (fires only on a CF-tag *transition*, add or remove):
  ```python
              if new_tags is not None:
                  task_repo = TaskStatusRepository(session)
                  if 'carry-forward' in new_tags and 'carry-forward' not in old_tags:
                      task_repo.ensure_active(note_id)
                      session.commit()
                  elif 'carry-forward' not in new_tags and 'carry-forward' in old_tags:
                      task_repo.set_dismissed_by_tag_removal(note_id)
                      session.commit()
  ```

No other creation path exists. All other repo callers only *read* or *transition* existing
rows: `action_executor.py` (get_filtered/set_completed/set_dismissed/set_forwarding_note,
lines 179–323), `eod_workflow.py` Step 3c/3d (get_filtered/set_completed/set_dismissed/
set_forwarding_note), `scheduler.py:157` (get_filtered read), `tasks.py` (list/show/
complete/dismiss — read + transition only). **There is no daemon, no EOD-step, no Slack,
and no migration/backfill code path that creates a TaskStatus row.** Creation is
CLI-`notes`-only, gated on the literal string `'carry-forward'` in the tag list.

**F2 — The PC-2 "carry-forward hook" today, and Ray's daily flow.** The hook that test
task 2727 ("Gate3 test note for carry-forward hook", 2026-05-27) named is precisely the
`notes.py` `ensure_active` call added in Phase 12 Gate 3 (see F3). At v1.26.1 it lives
**only** on the two CLI branches above. Critically:

- The **Slack intent path does NOT create a TaskStatus**, even for a CF-tagged note.
  `action_executor._execute_create_note()` (action_executor.py:155-173) calls
  `notes_service.create_note(self.session, content=content, tags=tags)` and returns —
  **no `ensure_active`** anywhere in `action_executor.py` (grep for `ensure_active` in that
  file returns nothing; grep for `create_active` likewise).
- The **shared canonical write path does NOT create a TaskStatus** either.
  `workmain/services/notes_service.py` `create_note()` contains no TaskStatus / carry-
  forward / ensure_active logic (grep: only the `def create_note` line matches). The
  `ensure_active` calls in `notes.py` are layered *on top of* `create_note`'s return value
  by the CLI command, not inside the service.

Therefore the CF→TaskStatus hook is wired into **exactly one surface: the interactive
`workmain notes add` / `workmain notes edit` CLI commands.** It is **not** part of the
daemon triggers, **not** part of `workmain eod` (the EOD steps only consume/transition
existing tasks), and **not** part of the Slack note-capture flow that became Ray's primary
inbound surface at v1.23.0. Re `--skip task_match`: that flag only skips Step 3c
*consumption* of tasks; it never touched creation (creation isn't in EOD at all), so the
skip workaround is **not** the cause of the creation gap — it is orthogonal.

**F3 — Git history: the hook has not moved or been orphaned; the change is behavioral.**
`git log -S "ensure_active" -- workmain/cli/commands/notes.py` returns a **single** commit:
`ab2f4d2 feat(phase12): Gate 3 — tasks lifecycle group, notes carry-forward hooks`,
dated **2026-05-27**. The CLI hook has been byte-stable since Phase 12 — no later commit
(#60, #61, #62, keep-alive hotfix, Sprint 3, service layer) moved, rewired, or removed it.
`git log -S "ensure_active" -- workmain/orchestration/action_executor.py` returns
**nothing** — the Slack path **never** had a CF-task hook to lose; it was never wired, so
this is a *never-implemented* gap, not a regression/orphaning.

Timeline (commit dates, `%ad` short):

| Date | Commit | Relevance |
|---|---|---|
| 2026-05-27 | `ab2f4d2` Phase 12 Gate 3 | CF hook added to `notes.py` CLI (only creation path ever). Test task 2727 dated same day. |
| 2026-06-12 | `70b86e5` intent-action-service-layer | `action_executor._execute_create_note` delegates to `notes_service.create_note` — **no** `ensure_active` added. |
| **2026-06-24** | — | **Last TaskStatus ever created** (note_id 15053; see F4). Last CLI CF-note add. |
| 2026-06-25 | `1e2c417` Sprint 3 Gate 1 → `9ba809d` Gate 8 (v1.23.0) | **Socket Mode inbound goes live.** |

The single 2026-06-24 firing and the total silence afterward correlate cleanly with the
**2026-06-25 Socket Mode cutover**: the day Slack inbound went live, Ray's CF notes began
arriving through `action_executor` → `notes_service` (no hook) instead of `notes add`
(hook), and creation stopped. **History shows no code change that broke creation; the
explanation is behavioral — a surface shift from CLI to Slack onto a path that was never
wired for CF-task creation.**

**F4 — Read-only DB verification** (Python app connection per project convention; no
direct psql). Live results, workmain DB, 2026-07-25:

- **Status counts** — `SELECT status, COUNT(*) FROM task_status GROUP BY status`:
  `active = 143`, `completed = 5`, (no `dismissed` rows). Total 148 task_status rows.
  (The 143 active exactly matches `tasks carryover`'s "143 found" in the Context table.)
- **Creation timeline** — task_status joined to `notes.created_date`, by month:
  `2026-02 → 31`, `2026-03 → 44`, `2026-04 → 50`, `2026-05 → 22`, `2026-06 → 1`,
  **and zero in 2026-07** (no row). Confirms the Feb–May bulk, the single June row, the
  silence since. A direct `WHERE n.created_date > '2026-06-24'` on task_status returns
  **0 rows**.
- **The defect made concrete** — CF-tagged notes created after 2026-06-24 that have **no**
  task_status row: **16**. And the total number of CF-tagged notes created after
  2026-06-24 is **also 16** — i.e. **100% (16 of 16) of post-cutover carry-forward notes
  have no task record.** Every carry-forward note Ray has entered since the Slack cutover
  is invisible to Step 3c and Step 3d.

**F5 — The `tasks list` ID column is `note_id`, not `task_status.id`.** Confirmed two ways.
(1) Source: `tasks.py:251` renders `table.add_row(str(note.id), …)` — it prints
`ts.note.id`. (2) DB: `MAX(task_status.id) = 2538` while `MAX(notes.id) = 28232`; the value
`15053` shown as the newest row in `tasks list` exceeds every possible `task_status.id`, so
it must be a note_id. Direct lookup confirms: the row displayed as "15053" is
`task_status.id=2538, note_id=15053, created 2026-06-24`; the row "2727" is
`task_status.id=147, note_id=2727, created 2026-05-27`. **The 2727 → 15053 gap is a
note-id gap** (note IDs advanced by ~12k across all note-creation surfaces between those
dates; only those two notes received CF tasks) — it is note-id passthrough in the display
column, **not** a `task_status` row-id gap (task_status ids 147 → 2538 are themselves far
apart because that sequence also spans all CF tasks created in the interval).

**F6 — AC8 staging determination.** Given F1–F4: **no Slack-reachable or daemon-reachable
action produces a TaskStatus at v1.26.1.** To get a staged CF-note pair into Step 3c's
attempt set and Step 3d's today-partition **today**, the CF notes must be created through
the **CLI** surface that carries the hook. Concretely, the actions required today are:

1. Create (or re-tag) the "task" CF note via CLI so a TaskStatus row exists:
   `workmain notes add "<task text>" --tags cf` (hits `notes.py:376 ensure_active`), or on
   an existing note `workmain notes edit <id> --tags cf` (hits `notes.py:503`). A note
   captured via Slack will **not** do this.
2. Create the matching "completion" note for the same `target_date` (any surface — Step 3c
   reads all `notes.get_by_date(target_date)` as candidates), with content that shares
   task tokens so the matcher fires. It must be a **different** note than the task's own
   note (self-match is excluded at eod_workflow.py:564).
3. Ensure Step 3b flagged a `carry_forward` observation for `target_date` in
   `last_inspection.json`, or Step 3c short-circuits with "No carry-forward items flagged"
   (eod_workflow.py:469-479). This is tag-driven inspection, independent of TaskStatus,
   so a CF-tagged note satisfies it.

So AC8 **is** stageable today, but **only via the CLI note path** — which is exactly the
surface Ray stopped using at the 2026-06-25 cutover. Stated plainly for the spec:
**the CF→TaskStatus creation mechanism is intact but reachable from only one non-daily
surface; every carry-forward note from Ray's actual daily (Slack) flow since 2026-06-24
produces no task, which is why Step 3c/3d operate on a stale 143-row backlog and never
see today's carry-forwards.** AC8 verification is possible via a CLI-seeded pair, but AC8
as experienced in Ray's real flow is **unverifiable until the creation hook is extended to
the Slack/service write path** (design decision for Role 1 — not resolved here).

---

### Section G — CLI `tasks list` Limit Surface (routes to Item #67)

**G1 — Command implementation.** `workmain/cli/commands/tasks.py`, `task_list`
(decorators lines 161–169, body 170–257). Options:
`--limit/-n type=int default=20` (line 169), `--all` → `show_all` flag `default=False`
(line 164), `--status` `default='active'` (line 162). Body: `effective_status = 'all' if
show_all else status_filter` (line 187), then:
```python
# tasks.py:201-207
        repo = TaskStatusRepository(session)
        tasks_result = repo.get_filtered(
            status=effective_status,
            search=search,
            date_filter=date_filter,
            limit=limit,
        )
```
When `--limit` is omitted it passes **20**. In `TaskStatusRepository.get_filtered`
(task_status_repo.py v1.1, lines 199–237): `limit: int = 20`, applied as
`if limit: q = q.limit(limit)` (line 234-235), with the docstring stating
**"limit: Maximum number of results. 0 means no limit."** (line 213). **`--all` maps to
status only** (`effective_status='all'`) — it does **not** alter `limit`. So
`tasks list --all` still caps at 20 rows, which is exactly the live evidence: "20 found"
with completed rows displacing active ones. Note the docstring at tasks.py:175 —
*"Default (no options): all active tasks, no age limit."* — is **misleading**: there is no
*age* filter, but there **is** a hard 20-**row** cap, so "all active tasks" is false
whenever more than 20 active tasks exist (143 today).

**G2 — Header count is post-limit `len(results)`.** `tasks.py:219`:
`title_parts = [f"Tasks ({len(tasks_result)} found"]`. `tasks_result` is the already-
capped list from `get_filtered`. **The header can never exceed the limit and therefore
misreports the true match count** — "20 found" when 143 active tasks match. It is a count
of *rows returned*, not *rows matching*.

**G3 — How `carryover` avoids the cap.** `tasks.py:416-447` (`task_carryover`, deprecated
alias). It prints a deprecation notice then delegates to the same `task_list` via
`ctx.invoke`, differing **only** in the limit it passes:
```python
# tasks.py:439-447
    effective_limit = limit if limit is not None else 0
    ctx.invoke(
        task_list,
        status_filter='active',
        show_all=False,
        search=None,
        date_str=None,
        limit=effective_limit,
    )
```
Its `--limit` default is **`None`** (line 419), mapped to **`limit=0`** → `get_filtered`'s
"no cap" branch (the `if limit:` at task_status_repo.py:234 is falsy for 0). That is why
`tasks carryover` returned the full 143 while `tasks list` returned 20 — **same repo, same
query, different limit value** (0 vs 20). `tasks today` (tasks.py:284) likewise passes
`limit=0`.

**G4 — `CLI_STANDARDS.md` §5.3 on `--all`.** The standard does **not** define `--all` for
`tasks list`. §5.3's only `--all` entries are in the "Flags with no short form" table
(lines 383, 386): `--all` on `clockify sync push` = "Infrequent bulk override"; `--all` on
costs commands = **"disables the default current-month filter to show full history."**
Neither says "all statuses"; to the extent the standard establishes any precedent, its
documented `--all` semantics are **"bypass the default filter and show everything"** — a
*window/limit* sense. The `tasks list` implementation contradicts that precedent: its
`--all` broadens **status** only and leaves the 20-row cap intact. There is no §5.3 clause
sanctioning `--all` as status-only. (Observation, as requested: `-all` errors "No such
option: -a" because `--all` on `tasks list` has no short form (consistent with §5.3's
no-short-form table), and Click parses `-all` as the bundle `-a -l -l`, whose `-a` is
undefined.)

---

*End of Opus findings — Sections E, F, G complete. Read-only pass; no source modified
outside this Findings block.*
