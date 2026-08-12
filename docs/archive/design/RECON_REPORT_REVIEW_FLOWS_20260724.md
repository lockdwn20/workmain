# RECON — Daily / Draft-Weekly / Weekly Report Edit & Confirm Flows

**Date:** 2026-07-24
**Author role:** Role 2 — Claude Code / Opus (Spec Reviewer / Recon)
**Type:** Recon audit (pre-spec). No implementation performed.
**Requested by:** Ray

---

## 0. Purpose & scope

During interactive-CLI End-of-Day (EOD) runs the **daily** report offers a
`Review: [v]iew / [e]dit / [c]onfirm / [s]kip` menu that lets Ray edit and confirm the
report. The **weekly** report was implemented as a "parallel" copy of that flow, but on
**Friday** EOD runs Ray reports that he *usually does not get the option to edit the weekly
report*.

Ray's stated concern: he was previously told (by Sonnet, during earlier single-model work)
that building these as parallel / duplicated implementations was "the only way." He now
suspects that was not true. This recon tests that.

**Deliverables (all covered below):**

1. Rundown of the daily, draft-weekly, and weekly edit/confirm processes.
2. Where each process runs parallel to the others vs. shares the same process.
3. Files involved.
4. Root-cause diagnosis of the missing Friday weekly-edit option.
5. Merge-feasibility assessment.

**This document produces no code.** Per the three-role model, findings go back to Ray →
Claude Desktop (Role 1) to be turned into a spec.

---

## 1. The edit/confirm surfaces (there are five)

| # | Surface | Prompt shown | Code location | When it runs |
|---|---------|--------------|---------------|--------------|
| 1 | Daily EOD review (CLI) | `Review: [v]iew / [e]dit / [c]onfirm / [s]kip` (default `s`) | `eod_workflow.py:_run_report_step` (884–1039) | Every CLI EOD run, step 4a |
| 2 | Weekly EOD review (CLI) | `Review: [v]iew / [e]dit / [c]onfirm / [s]kip` (default `s`) | `eod_workflow.py:_run_weekly_report_step` (1193–1364) | **Friday** CLI EOD, step 7 |
| 5 | Slack EOD report steps | *(none — no edit path yet)* | same runners via `slack_eod.py:_run_step_thread` → `run_step` | Slack EOD, daemon thread — see §2.5 |
| 3 | Draft-weekly → Slack | `Post to #…? [y]es / [n]o / [e]dit` (default `n`) | `slack.py:slack_post` (762–796) via `_run_slack_weekly_step` (eod_workflow.py:1163–1191) | **Thursday** EOD, step 7 |
| 4 | Standalone correct | `$EDITOR` opened directly, no menu | `reports.py:report_correct` (575–615) | Manual `workmain reports correct` |

Plus `workmain reports confirm` (`reports.py:541–572`) which just sets `status='confirmed'`.

### 1.1 Daily EOD review (surface #1)

`_run_report_step` (eod_workflow.py:884–1039):

- **Pre-check** (894–913): if a `confirmed`/`corrected` `daily_internal` report already
  exists for the date, short-circuits (returns COMPLETED) — no menu.
- Generates via subprocess `reports save daily_internal`.
- **Non-interactive guard** (939–944): if `not _is_interactive()`, skips the review loop.
- Reloads the newest report and runs the `[v/e/c/s]` loop (976–1028):
  - `[v]iew` — prints full body, loops back to menu.
  - `[e]dit` — opens `$EDITOR` via `_eod_edit_in_editor`; seeds from `corrected_content`
    else `content`; on real change writes `report.corrected_content`, `status='corrected'`,
    commits, mirrors the staging `.md` file, then prompts for an optional correction note
    saved via `repo.set_correction_note()` (990–1013).
  - `[c]onfirm` — sets `status='confirmed'`, commits (1015–1020).
  - `[s]kip` / anything else — warns "left unconfirmed," no DB write (1022–1028).

### 1.2 Weekly EOD review (surface #2) — Friday only

`_run_weekly_report_step` (eod_workflow.py:1193–1364) is a **near-verbatim copy** of #1
with the same `[v/e/c/s]` menu (1303–1352) and identical edit/persist logic (1317–1340).
The only structural differences are the guards described in §3.

### 1.3 Draft-weekly → Slack (surface #3) — Thursday only

`slack.py:slack_post` (the `slack post weekly` command). Prompt at 762–765:

- `[n]o` — cancel, nothing posted.
- `[e]dit` — opens `_edit_in_editor` (slack.py copy), re-previews, then asks
  `Post edited content …? [y]es / [n]o`. The edited text is only what gets **posted**; it
  lands in `Report.content` on a **fresh insert** and touches neither `corrected_content`
  nor `correction_note`.
- `[y]es` — posts.

On post it **upserts** a `weekly_client` row keyed on `report_date == anchor`
(slack.py:820–841) and — importantly — **does not set `status`**, so the row stays
`unconfirmed`.

### 1.4 Standalone `reports correct` (surface #4)

`reports.py:report_correct` (575–615): resolves a report, opens `$EDITOR` (its own
`_edit_in_editor`), writes `corrected_content` + `status='corrected'`, mirrors the staging
file. Unlike the EOD edit branches, it **never** prompts for / writes `correction_note`.

---

## 2. KEY INSIGHT — the daily and weekly steps are structurally identical

Surface #1 (daily, `_run_report_step`, 884–1039) and surface #2 (weekly,
`_run_weekly_report_step`, 1193–1364) are the same code: identical confirmed/corrected
pre-check, identical generate-via-subprocess, identical non-interactive guard, identical
reload (`list_reports(..., limit=1)` ordered `created_at DESC`), identical `[v/e/c/s]` menu.

**The only extra gate weekly has is the active-client requirement (G1).**

Therefore there is **no structural reason the weekly menu should appear less reliably than
the daily one.** The cause of "usually no option on Friday" is **state-driven** (the DB rows
that exist for that Friday date at run time), not a code-path defect — which is exactly why
it is intermittent ("usually," not "always"). §3 works this through against Ray's live data.

> Note: surface #2 (Friday `[v/e/c/s]`) and surface #3 (Thursday `[y/n/e]` Slack draft) are
> different commands on different days. Ray is aware of this distinction; it is recorded here
> only so the surfaces stay disambiguated for a future implementer.

### 2.5 Slack EOD (surface #5) — reuses the same runner, and that is the gap

The bidirectional Slack EOD (`workmain/integrations/slack/slack_eod.py`, `SlackEodManager`)
does **not** have its own report flow. `_build_steps` (656–659) calls the same
`eod_workflow.get_step_sequence(weekday, skip=[])`, so on Friday the Slack EOD runs the same
`_run_weekly_report_step`. `_run_step_thread` (492–536) invokes it in a background thread via
`run_step(step, dry_run=False, target_date, non_interactive=True, cancel_event, daemon)`.

**Why there is no edit over Slack:** `run_step` only forwards `non_interactive` to runners
that *declare* the parameter (eod_workflow.py:1477–1486). The daily/weekly report runners
have signature `(dry_run, target_date)` — they do **not** declare it. So `non_interactive=True`
is dropped, and the runner falls back to its own `_is_interactive()` = `sys.stdin.isatty()`,
which is **False** in the daemon thread. The runner therefore hits its non-interactive guard
(1266–1271): *"Weekly client report generated — review with: workmain reports history"* and
returns COMPLETED **with no menu**. The report lands `unconfirmed`; the user corrects it later
via `reports correct` (surface #4).

This is the confirmed mechanism behind the "Slack EOD generates the weekly but won't let me
edit it" tedium — and it is **not** a parallelism defect. The edit path is stdin/`$EDITOR`-only
and cannot render over async Slack. Contrast with `task_match`/`note_dedup`, which *do* declare
`non_interactive` and return `PAUSED`, letting the Slack EOD drive them through its pause →
correct → confirm control-word model. The report runners were never wired into that model.

---

## 3. Root cause — why the Friday weekly `[e]dit` "usually" doesn't appear

The Friday `[e]dit` option **exists** and is byte-for-byte parallel to the daily one. It is
suppressed only by early-returns in `_run_weekly_report_step`, in evaluation order:

| # | Guard | Lines | Effect |
|---|-------|-------|--------|
| G1 | No active client set | 1211–1217 | returns COMPLETED, "skipped — no active client" |
| G2 | Confirmed/corrected pre-check | 1219–1236 | returns COMPLETED, "already confirmed … skipping generation" |
| G3 | Non-interactive / no TTY | 1266–1271 | skips review loop |
| G4 | Reload finds no report | 1286–1291 | returns COMPLETED, "could not load … for review" |
| G5 | Default action is skip | 1303–1307 | Enter → skip, but option **is** shown |

**G4 is ruled out:** `reports save weekly_client --date <friday>` stores `report_date=<friday>`
(reports.py:237–238), and the reload queries the same date (1279–1284). They match.
**G5 is ruled out:** it still renders the prompt. **G3 is ruled out** by interactive use.

### 3.1 What Ray's live data shows (`reports history --type weekly_client`, 2026-07-24)

The `weekly_client` history **disproves G2-as-a-consistent-cause** and points to a
state-driven, not structural, mechanism:

- **Recent Fridays reached edited/confirmed states through the flow:** 2026-07-17 →
  single row, `confirmed`; 2026-07-10 → single row, `corrected`. If the menu never appeared,
  these could not have become confirmed/corrected. **The menu demonstrably works.**
- **Older Fridays carry multiple duplicate rows** for one `report_date`: 2026-06-26 → 3 rows
  (all `unconfirmed`); 2026-06-05 → 5 rows (mixed). Because `list_reports` orders
  `created_at DESC` (reports_repo.py:163) and the EOD pre-check skips on the *first*
  confirmed/corrected row it sees, the EOD step could not have produced the *later*
  unconfirmed rows on 06-05 (the `corrected` row 3586 at 14:09 precedes unconfirmed rows at
  14:29–14:44). **Those duplicates come from `workmain reports save weekly_client` run
  directly, outside EOD** — which has no pre-check and inserts a fresh row every call (no
  dedup). This is a distinct finding worth a backlog note: duplicate weekly rows per date.

### 3.2 The operative cause, reconciled with Ray's usage (2026-07-24)

Ray confirmed: **he runs the interactive CLI Friday EOD only once.** That removes the
"repeat-run confirms it, then later runs skip" mechanism for the normal CLI case — there is
no earlier run to set `confirmed`/`corrected` first. He also confirmed the recent
`weekly_client` states were produced **outside** the CLI EOD menu: 2026-07-10 `corrected` was
a **manual `reports correct`** after a Slack EOD test; 2026-07-17 is `confirmed` (not
`corrected`), source not the CLI edit menu. So none of the recent rows are evidence that the
CLI menu did *or* did not appear.

**Reconciliation:**

- **Interactive CLI EOD, run once on a fresh Friday** — G1 (active client set) and G2 (no
  prior confirmed/corrected row) both pass; `_is_interactive()` is True. There is no code
  reason the `[v/e/c/s]` menu would not appear. This is what the §3.3 clean-slate run on
  2026-07-24 will confirm.
- **The recent "can't edit the weekly" experience is the Slack EOD path (§2.5)**, which
  generates the weekly report and silently skips the menu because `_is_interactive()` is
  False in the daemon thread. That is the tedium Ray described, and why he has been correcting
  weekly reports manually.

Residual CLI suppressors, if ever seen, remain G1 (active client not set at step 7 — weekly
only) and G2 (a pre-existing confirmed/corrected row from a manual `reports confirm/correct`).

> **Open design question for Role 1:** when G2 fires, should the step offer a re-review /
> re-edit path instead of silently skipping "already confirmed"? Apply the answer to daily
> and weekly identically (shared pre-check).

### 3.3 Decisive live confirmation (clean slate available now)

On **2026-07-24 (Friday)** there is **no `weekly_client` row yet** — a clean slate. First
EOD run today, active client set → G1 and G2 both pass → generate → **the menu should
appear.**

**✅ CONFIRMED LIVE (2026-07-24):** Ray ran the interactive CLI Friday EOD and the weekly
report presented the `[v]iew / [e]dit / [c]onfirm / [s]kip` menu as expected. The interactive
CLI path is healthy; the "usually no edit" experience was the **Slack EOD** path (§2.5), not
the CLI. This closes the root-cause question: the remaining work is the Slack EOD edit
unification (§7 item 5), not a CLI-path bug.

> Aside (out of scope): the weekly `weekly_client` report is generated by Gemini by default
> and Ray finds the output poor, so he regenerates with Claude — a template/provider quality
> issue slated for a separate upcoming sprint. Note this regeneration is a legitimate everyday
> source of the duplicate-rows-per-date finding (§3.1); the dedup design decision (§7 item 4)
> must accommodate intentional regeneration, not treat every extra row as an error.

---

## 4. Parallel vs. shared — the honest map

### 4.1 Already shared (so the "parallel was the only way" premise does not hold)

- **Generation + staging:** one path — `report_generator.py:generate_report()` +
  `reports.py:generate_report_impl` (211) — driven purely by template name
  (`daily_internal` vs `weekly_client`). No separate daily/weekly generator or module exists.
- **Repository** (`reports_repo.py`): every method (`list_reports`, `set_correction_note`,
  `get_filtered`, `get_confirmed_dailies`) is `report_type`-parametrized.
- **`Report` model** (models.py:381–428): single schema — `status`, `corrected_content`,
  `correction_note`, `report_metadata`.
- **EOD I/O + editor helpers:** `_prompt_choice` (138), `_prompt_raw` (147),
  `_is_interactive` (155), `_eod_edit_in_editor` (169) — used by both EOD steps.
- **Daily → weekly data feed:** `get_confirmed_dailies` (a genuine data dependency, not
  duplication).

### 4.2 Genuinely duplicated — the real unification targets

1. **`_run_report_step` (884–1039) vs `_run_weekly_report_step` (1193–1364)** — ~170 lines
   each, near-verbatim. They differ only by:
   - report_type string (`daily_internal` vs `weekly_client`);
   - a weekly-only active-client guard (G1);
   - one error-handling branch (daily returns FAILED on generation error; weekly treats it
     as non-fatal COMPLETED in interactive CLI — eod_workflow.py:935–937 vs 1260–1264);
   - cosmetic label/prose ("Daily" vs "Weekly").

   Collapsible into a single runner parametrized as
   `(report_type, label, require_active_client, generation_error_fatal)`.

2. **Three copies of the `$EDITOR` helper** — `reports.py:159`, `eod_workflow.py:169`,
   `slack.py:901`. Identical logic (`$EDITOR` + `NamedTemporaryFile(.md)` + `subprocess.run`
   + read back + unlink); differ only in Rich-vs-stdlib output and failure semantics
   (`None` vs "post as-is" vs original-content fallback). One shared helper with a
   print/failure callback removes two copies.

3. **The edit-and-save block** (write `corrected_content`, set `status='corrected'`, mirror
   the staging file, prompt for correction note) is implemented ~3× (both EOD steps + partly
   `reports correct`). Candidate for a repository method, e.g.
   `ReportsRepository.apply_correction(report_id, edited, note)`.

### 4.3 Where the flows legitimately must differ

- Weekly requires an **active client** (G1) and prepends **confirmed-daily context** in the
  prompt (`prompt_builder.build_weekly_prompt`). Both are small, isolated, and expressible
  as parameters — not reasons to fork the function.

### 4.4 Conclusion

Unification is **feasible and low-risk**. The forced parallelism was avoidable: the heavy
machinery (generation, staging, repo, model, editor) is already shared; only the two EOD
step runners and the editor helper are duplicated, and their differences are parametric.

---

## 5. Field-write discipline (per CLAUDE.md — must be preserved by any future fix)

- `corrected_content` = the edited report **body** (EOD edit branches + `reports correct`).
- `correction_note` = a human "what changed" **annotation** (only via `set_correction_note`).
- Thursday Slack `[e]dit` writes **neither** — edited text is posted and lands in
  `Report.content` on a fresh insert only.

Never conflate `corrected_content` and `correction_note`.

---

## 6. Files involved

| File | Header version | Role in these flows |
|------|----------------|---------------------|
| `workmain/workflows/eod_workflow.py` | v1.8 | Both EOD review menus (#1, #2) + step sequencing |
| `workmain/cli/commands/slack.py` | v1.7 | Thursday draft `[y/n/e]` (#3) + its editor helper |
| `workmain/cli/commands/reports.py` | v2.15 | `reports correct/confirm/corrections` (#4), `generate_report_impl`, editor helper |
| `workmain/database/repositories/reports_repo.py` | v1.5 | `list_reports`, `set_correction_note`, `get_filtered`, `get_confirmed_dailies` |
| `workmain/ai/report_generator.py` | v1.14 | Shared generator + staging (`staging/reports/`) |
| `workmain/database/models.py` | — | `Report` review-state fields (381–428) |
| `workmain/cli/commands/eod.py` | v2.14 | Thin EOD CLI surface / step dispatch |
| `workmain/integrations/slack/slack_eod.py` | — | Slack EOD (surface #5); reuses the same runners, no edit path yet (§2.5) |

---

## 7. Recommended next step (for Role 1 / Claude Desktop)

Spec a unification that:

1. **Collapses** `_run_report_step` and `_run_weekly_report_step` into one parametrized
   review runner (report_type, label, require_active_client, generation_error_fatal).
2. **Extracts** a single shared `$EDITOR` helper (or a `ReportsRepository.apply_correction`)
   used by daily, weekly, and `reports correct`.
3. **Resolves the G2 design question**: when a report is already confirmed/corrected, should
   the step offer re-review/re-edit rather than silently skip — applied identically to daily
   and weekly (since both carry the same pre-check).
4. **Considers the duplicate-row finding (§3.1)**: `reports save weekly_client` inserts a new
   row per call with no dedup, producing multiple rows per `report_date`. Decide whether save
   should upsert-by-date (like the Slack draft does) or whether the review flow should target
   an explicit report id rather than "newest for date." Candidate backlog item, separate from
   the unification.
5. **Unifies the Slack EOD edit path without a fifth fork (§2.5)** — the strategic point
   behind Ray's original concern. The report review is currently stdin/`$EDITOR`-only and
   cannot render over async Slack, which is why the Slack EOD generates the weekly but offers
   no edit. The correct design:
   - Extract the persistence core (`corrected_content` + `status='corrected'` +
     `correction_note` + staging-file mirror) into **one** method, e.g.
     `ReportsRepository.apply_correction(report_id, edited_body, note)`, called by the CLI
     menu, `reports correct`, **and** the future Slack edit alike.
   - Make the report runners **declare `non_interactive` and return `PAUSED`** (as
     `task_match`/`note_dedup` already do), so the Slack EOD drives report review through its
     existing pause → correct → confirm control-word / Block Kit model instead of silently
     self-skipping (1266–1271). The Slack edit becomes a new *front-end* on shared logic, not
     a parallel copy.

Before speccing, capture the §3.3 clean-slate observation (a first Friday CLI EOD run on a
date with no existing `weekly_client` row) to confirm the menu appears; if it does not,
instrument the step per-branch before designing the fix.
