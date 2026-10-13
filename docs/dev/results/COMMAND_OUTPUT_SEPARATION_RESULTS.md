# Command Output Separation — Implementation Results

**Status:** Shipped
**Author:** Spanner (Role 1)
**Date:** 20261012
**Spec:** `../specs/COMMAND_OUTPUT_SEPARATION_SPEC.md`
**Released as:** n/a — `chore/*`

---

## 1. Summary

Complete. #58 is rewritten as the pilot. Sixteen conversion issues, #201–#216, are open under #198, each blocked by #58. #159 and #160 are narrowed to their rows outside `workmain/cli/`. #95, #96 and #168 carry the context the spec gives them, and #95 and #96 each gain one criterion. Every dependency link the spec names exists on GitHub. The design study records which issue converts each census entry and each width-dependent test.

## 2. What shipped, by step

| Step | Delivered | Files changed | Tests |
| --- | --- | --- | --- |
| 0 | Pre-edit bodies of #58, #95, #96, #159, #160 and #168 saved to the scratchpad; duplicate search run for all 16 groups, with no open issue covering a group's conversion (§5) | none | n/a |
| 1 | #58 retitled "Build the CLI output module and its rules on the tasks commands", body replaced, `tests` label added, blocked by #96 | none (GitHub) | n/a |
| 2 | #201–#216 created through `automation/issue_validator.py --create` | none (GitHub) | n/a |
| 3 | #96 ← #95, #104 ← #58, #115 ← #214 and #207 | none (GitHub) | n/a |
| 4 | #159, #160, #95, #96 and #168 edited | none (GitHub) | n/a |
| 5 | Issue numbers recorded in the study's Appendices A–C and §6 | `docs/dev/design/DESIGN_COMMAND_OUTPUT_SEPARATION.md` | n/a |
| 6 | This artifact | `docs/dev/results/COMMAND_OUTPUT_SEPARATION_RESULTS.md` | n/a |

## 3. Acceptance criteria

| AC | Status | Evidence |
| --- | --- | --- |
| AC1.1 | Met | every name from `ls workmain/cli/commands/*.py` except `__init__.py` has a `###` section in Appendix A; the loop over them prints nothing |
| AC2.1 | Met | Reviewed by Ray |
| AC3.1 | Met | every §5 row of the study carries an answer dated 20261012; commit `9df9624`, which recorded the last answer, is 2026-10-12T16:01:07-07:00; the earliest new issue, #201, was created at 2026-10-13T05:00:18Z (2026-10-12 22:00:18 -07:00) |
| AC4.1 | Met | The mechanical part is met. All 18 Appendix A headings and all 29 Appendix B rows name an issue; `gh issue view 198 --json subIssues` lists 58, 136, 199, 200 and 201–216; the grep for `\bF[0-9]+\b`, `Appendix`, `design study` and `DESIGN_` over the live bodies of #58 and #201–#216 finds nothing. The reading of three bodies was done by Ray. |
| AC4.2 | Met | Reviewed by Ray |
| AC5.1 | Met | Over the live bodies, each of the fourteen files appears in a criterion using the X-TC pattern: `tests/test_task_lifecycle.py` in #58; `test_clients_commands.py` in #204; `test_meetings_condense.py` and `test_meetings_track.py` in #208; `test_notes_add.py`, `test_notes_edit.py` and `test_notes_log.py` in #209; `test_ai_arguments.py`, `test_report_correction.py`, `test_report_history.py` and `test_reports_corrections.py` in #212; `test_slack.py` and `test_slack_channel_config.py` in #214; `test_time_add.py` in #216. #212 carries X-OPT and #214 carries X-ENTRY. |
| AC6.1 | Met | Appendix C has a row for each of #158, #159, #160, #161, #167, #168, #169, #95, #104, #140, #136 and #58; the `blocked_by` read-back in §5 shows every link AC6.1 lists |

## 4. Deviations from spec

| # | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| D1 | Copying the Appendix A tables, the `(costs in the AI-costs table)` note in the `meetings.py`, `notes.py`, `providers.py` and `reports.py` headings was replaced with `(its costs command is converted with the other AI cost commands)` | "the AI-costs table" refers to the study, which DR1 keeps out of every body | Spanner, within DR1; for Ray's review |
| D2 | Bullets naming spec criterion labels were rewritten in plain words in the bodies: top-level's "C1 for this group…", templates' "C3's 'tested at the service'…" and the AI-costs bullet about C1 and C2. Clockify's "(§5.6, the shared picker)" names `docs/DEVELOPMENT_STANDARDS.md` | C1–C6 are labels in the spec, not in an issue body, so a reader of the issue could not resolve them | Spanner, within DR1; for Ray's review |
| D3 | Each conversion's width criterion names its test files as "every test file under Tests, narrowed by node id where another group shares it, plus the service and command test files this issue adds", rather than listing paths | the service and command test files do not exist until the conversion writes them; this is the spec's `{tests}` definition in words | Spanner; for Ray's review |

## 5. Verification

- **Test suite:** 1274 passed, 0 failed, 0 skipped at close-out preflight (baseline: 1274 passed, 0 failed, 0 skipped, the full-width sweep runs at `b61e321`). No file under `tests/`, `automation/`, `workmain/`, `config/` or `templates/` changed (spec §6).
- **Live verification:** the GitHub state this work produced. Every issue body, label, parent and `blocked_by` link listed below was read back from GitHub after it was written.
- **Daemon restart:** n/a. A `chore/*` branch changes no application code, so `docs/DEVELOPMENT_STANDARDS.md` §2.6 requires none.
- **Issues created** (Step 2), each by `python3 automation/issue_validator.py <scratchpad payload> --create`, which ran `gh issue create … --parent 198 --label defect --label cli --label tests [--label <area>] --blocked-by <set> --project 'WorkmAIn Queue'`:

| Group | Issue | Area label | Blocked by |
| --- | --- | --- | --- |
| AI costs | #201 | `ai-llm` | #58 |
| clockify | #202 | `clockify` | #58 |
| calendar | #203 | — | #58 |
| clients | #204 | — | #58 |
| email | #205 | `reports` | #58, #104 |
| top-level (`eod`, `status`, `today`, `init`) | #206 | — | #58 |
| gdocs | #207 | `gdrive` | #58 |
| meetings | #208 | — | #58, #168, #201 |
| notes | #209 | — | #58, #168, #201 |
| notifications | #210 | `daemon` | #58 |
| providers | #211 | `ai-llm` | #58, #201 |
| reports | #212 | `reports` | #58, #167, #201 |
| schedule | #213 | `daemon` | #58 |
| slack | #214 | `slack` | #58, #167 |
| templates | #215 | `templates` | #58 |
| time | #216 | — | #58, #202 |

- **Other `gh` writes:**
  - `gh issue edit 58 --title "Build the CLI output module and its rules on the tasks commands" --body-file <scratchpad>/58.md --add-label tests --add-blocked-by 96`
  - `gh issue edit 96 --add-blocked-by 95`
  - `gh issue edit 104 --add-blocked-by 58`
  - `gh issue edit 115 --add-blocked-by 214,207`
  - `gh issue edit <N> --body-file <scratchpad>/<N>.md` for 159, 160, 95, 96 and 168. Each file was checked to be non-empty and to start with the body's expected first line before the write. Each live body was read back afterwards and matches its file, ignoring the trailing whitespace GitHub trims.
- **`blocked_by` read-back**, by `gh api repos/{owner}/{repo}/issues/<N>/dependencies/blocked_by`: #58 ← 96, 199; #95 ← none; #96 ← 95; #104 ← 58; #115 ← 207, 214; #201–#216 as in the table above.
- **Duplicate search** (Step 0), `gh issue list --state open --search "<group> commands"` for each of the 16 groups. Every result was an overlap the spec already names (#58, #104, #115, #132, #140, #141, #142, #143, #151, #155, #158, #159, #160, #165, #167, #168, #192, #198, #199), a flag issue (#138, #139), or unrelated (#42, #45, #63, #69, #73). None covers a group's conversion.

## 6. Follow-ups

| Item | Description | Why deferred |
| --- | --- | --- |
| Close-out | `/closeout` for `chore/issue-199-command-output-recon` | close-out's, not this spec's |
