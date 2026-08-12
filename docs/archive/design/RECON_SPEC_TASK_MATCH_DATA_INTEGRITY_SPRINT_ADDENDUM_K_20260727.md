WorkmAIn
RECON_SPEC_TASK_MATCH_DATA_INTEGRITY_SPRINT — Addendum K
20260727

---

**PASTE TARGET:** Append everything below the `---` divider directly onto
the END of `docs/dev/design/RECON_SPEC_TASK_MATCH_DATA_INTEGRITY_SPRINT_20260725.md`,
after its existing closing line (`*End of Opus findings — Sections H, I, J
complete...*`). This is an addendum to that recon, not a new recon file —
per the Addendum A/B precedent in
`RECON_SPEC_SLACK_LLM_COMPLETION_SPRINT_20260725.md`. Do not bump the
file's version header; addenda accumulate in place.

---

### Addendum K (20260727) — Write-path parameter surface for Item 69 service convergence (micro-recon, requested by Role 1)

**Critical instructions (carried forward from the parent recon):**
- Read-only pass. No code changes, no fixes, no refactors, no design
  suggestions inline with findings — verbatim quotes and observations
  only.
- **Pitfall #12 applies:** component-verified ≠ integration-verified.
  Confirming a service function *could* accept a parameter is not the
  same as confirming a given H3 call site actually supplies it — quote
  each call site verbatim to prove it, don't infer from the shape of the
  call.
- **Version-drift caution:** Section H/I/J were run at codebase v1.26.1
  (`main`==`dev`) against file headers `notes.py` v4.2, `time.py` v1.7,
  `meetings.py` v4.5, `clockify/sync.py` v1.4, `time_entry_service.py`
  v1.0, `notes_service.py` v1.0, `action_executor.py` v1.4,
  `notes_repo.py` v2.1. Re-check each header now; if any file has moved
  since 20260725, note the new version and re-verify the relevant H3 row
  rather than assuming it's unchanged.
- **Output:** append findings below this addendum's own
  `#### Addendum K — Findings` placeholder, in the same file. Do not
  create a separate output file.

**Purpose.** Item 69 (Note Write-Path Convergence) will converge all
twelve H3 note-write surfaces onto a single service-layer contract. H4
already established that `notes_service.create_note` and
`time_entry_service.create_time_entry` are siblings — each sees only its
own 1–2 callers today, not the full twelve-surface contract. Before Role
1 can design the converged API shape, it needs:

1. The complete current signature and body of both services, verbatim.
2. The complete, per-parameter call pattern of every one of the twelve
   H3 surfaces — not just whether a surface *can* pass tags/CF (H3
   already answered that), but literally every argument it passes today,
   including any that neither service currently declares.

Without this, a converged signature designed against only the two
current callers risks silently dropping a parameter one of the other ten
surfaces depends on (a hard-coded tag list, a `source` value, a
`created_at` backdate, a `client_id` passthrough) — exactly the
integration gap Pitfall #12 exists to catch.

**Questions:**

**K1.** Quote `notes_service.create_note()` in full — signature and
body, file path, version header, line range
(`workmain/services/notes_service.py`, last known v1.0).

**K2.** Quote `time_entry_service.create_time_entry()` in full —
signature and body, file path, version header, line range
(`workmain/services/time_entry_service.py`, last known v1.0). H4 already
quoted lines 84–90 (the `NotesRepository.create()` call inside it) —
quote the FULL method: parameter list, anything before/after that call
(including any TimeEntry-side construction), return value.

**K3.** For EACH of the twelve H3 surfaces (use the same #1–#12
numbering as the H3 table), quote the exact call site verbatim — full
argument list as written in source, not paraphrased — showing every
parameter passed to whichever write path that surface uses (service
call, or direct `NotesRepository.create()` / model construction). At
minimum, capture per surface whether each of the following is present,
and its literal value or source, or explicitly state it is absent:
- `content`
- `tags` (literal list, user-supplied, or parsed)
- `source` (literal value)
- `client_id`
- `meeting_id` — confirm from `models.py` whether `meeting_id` is an
  actual `Note` column or lives elsewhere (e.g. a `meeting` relationship
  joined separately); H3 didn't surface this explicitly and it must not
  be assumed
- `created_at` (any override/backdate — H already flagged #6's
  `note_created_at`; confirm whether #12 Clockify's import backdates too,
  and check the remaining surfaces)
- surface-specific extras: #2/#4/#8/#9's hard-coded `['both']` tag list
  (quote it literally per surface — confirm it's the same list object or
  four independent literals), #9's `source='condensed'`, #12's
  `source='clockify'` and whether any external Clockify reference id is
  stored on the `Note` or a related row, #10/#11 Slack's intent-derived
  values, #11's H3 note that the create-time-entry schema "has no tags
  field (v1.6)" — confirm that's still current at whatever version
  `action_executor.py` is at now.

**K4.** For the surfaces that pair a Note write with a TimeEntry write
(#5, #6, #7 — the `time add` paths — and #11, Slack create-time-entry),
quote the TimeEntry-side creation call(s) alongside the Note-side call,
with the same per-parameter treatment as K3 (`entry_date`, `client_id`,
duration/hours, `meeting_id`, `category` if it exists as a column).
Item 69 needs to know whether the converged hook point has to account
for a paired TimeEntry write, not just the Note write, on these
surfaces.

**K5. (Primary deliverable) Superset parameter table.** One table:
rows = the union of every parameter name observed across K1/K2
(declared by the services) and K3/K4 (actually passed at any call
site); columns = the twelve H3 surfaces (#1–#12) plus the two service
signatures. Cell contents = the value/source passed on that surface, or
`—` if omitted/left to default, or `N/A` if the parameter doesn't apply
to that surface's write path (e.g. TimeEntry-only fields on a pure-Note
surface). This table is the direct input to Item 69's spec — it must
show the FULL contract the converged API needs to support, not the
two-caller subset either service currently sees.

**K6.** Explicitly flag any parameter found in K3/K4 that is NOT in
either service's current declared signature (K1/K2) — these are gaps
the converged API must *add*, not just relocate. For each gap, name
which of the ten non-service surfaces (#2, #3, #4, #5, #7, #8, #9, #12,
plus the TimeEntry side of #6/#11) depends on it, so Role 1 can size the
spec's parameter-addition scope accurately.

**Output:** Append all findings below this line, under a
`#### Addendum K — Findings` heading, at the END of
`RECON_SPEC_TASK_MATCH_DATA_INTEGRITY_SPRINT_20260725.md` (after the
existing H/I/J closing line). Verbatim quotes with file/version/line
ranges throughout. Do not edit anything above this line in the live
file. Do not create a separate output file.
