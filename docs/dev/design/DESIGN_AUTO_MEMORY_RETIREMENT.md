# Auto-Memory Retirement — Design Study

**Status:** Shipped
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261026
**Originating item:** Issue #241

---

## 1. Purpose

Issue #241 turns Claude Code auto-memory off for this repository and requires every entry it holds to be read first and given a disposition: moved to the versioned document that should own it, or dropped with a reason. This study holds that disposition for every entry, the home each moved rule goes to, and the one question only Ray can answer. The spec that follows quotes the exact text for each move.

## 2. Scope of the read

- **Read:** every file in `~/.claude/projects/-home-lockdwn20-Projects-workmain/memory/`, read in full by Spanner on 20261026 from this session. The issue expected the read to be Ray-run or Ray-supplied because the directory is outside the repository. It is readable from a Claude Code session on Ray's machine, so Spanner read it directly. Ray's check of this study's §3.2 against his own `/memory` view stands in for the supplied copy. On 20261026 the directory held 90 files: `MEMORY.md` (the index), 88 entry files, and one empty file whose name is a sentence fragment (`as a one-off). 2026-10-11.#`), left by a broken shell write.
- **Checked against:** `CLAUDE.md`, `docs/DEVELOPMENT_STANDARDS.md`, `docs/AI_SETTINGS_GUIDE.md`, `.claude/skills/session-start/` (`SKILL.md` and `references/`), `.claude/skills/closeout/`, the three `docs/dev/*/_TEMPLATE_*.md` files, and the live state of every issue an entry names.
- **Not read:** the Claude Code memory directories of other projects, and user-level `~/.claude/CLAUDE.md`. Neither is governed by this repository.
- **Not in scope:** the three standards passages issue #240 lists as reading like permission to self-resolve, and the results template's deviations table. Both belong to #242. Where an entry bears on one of them, its point is carried into #242's body, and the standard's own fate is left to #242.

## 3. Findings

### 3.1 Mechanism

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | `autoMemoryEnabled: false` in a project's settings turns auto-memory off for that project. `/memory` shows the toggle. | Claude Code docs, *How Claude remembers your project* § Enable or disable auto memory (code.claude.com/docs/en/memory), read 20261026: "To turn it off for a single project, set `autoMemoryEnabled` in that project's settings" | — |
| F2 | No tracked `.claude/settings.json` exists. `.claude/settings.local.json` is untracked and holds only Ray's personal permissions. | `ls .claude` → `settings.local.json skills`; `git ls-files .claude/settings.json` returns nothing | High |
| F3 | Nothing in the repository names auto-memory. | `grep -rn -i memory CLAUDE.md docs/DEVELOPMENT_STANDARDS.md .claude/` returns no hit about Claude Code memory | High |
| F4 | A rule for one role must sit where only that role's session loads it. `SKILL.md` is loaded by every role, so a rule placed there with a sentence saying it does not apply to the others stays in every role's context. That is the mechanism F8 shows failing. `references/<role>.md` is loaded only by `/session-start <role>`. Today it holds only the run's reads and emits; it gains a § Working rules that holds for the session and that the run neither reads nor emits. `SKILL.md` and `CLAUDE.md`, which say the role model is stated only in `SKILL.md`, each gain a sentence naming that exception. | `.claude/skills/session-start/SKILL.md` § Choosing the reference ("Load exactly one"); `references/anvil.md`, `caliper.md`, `spanner.md` carry only `Reads, in order` and `Emits`; `SKILL.md`: "§ THREE-ROLE MODEL below is the only statement of what each role is, does and hands to the others" | High |
| F5 | The second criterion records the dispositions in the results artifact. They are decided here, before the spec, and Ray reads them before implementation. Their one home is §3.2 of this study, which is archived with the spec and results artifact. The results artifact cites it. | `CLAUDE.md` opening: "Every fact, decision, and rule has exactly one home" | Medium |
| F6 | `docs/DEVELOPMENT_STANDARDS.md` §1.6 says every issue joins the queue project "at creation (§1.3)". §1.3 says no such thing. The rule exists only in memory (`feedback_issue_open_completion.md`). | §1.6 first paragraph; §1.3 read in full | Medium |
| F7 | Several entries contradict the standards they cite and would mislead a session that followed them: `feedback_hotfix_merge_no_pr.md` and `feedback_pr_workflow.md` order a remote branch delete, which §2.3 forbids; `feedback_db_session_cli_isolation.md` prescribes a real committed session with `tearDown` cleanup, which §6.1 replaced; `feedback_gate_stops.md` requires a stop at every gate, which §1.4 replaced with steps; `calendar_import_patterns.md` gives `db.get_session()` as the connection snippet, which §4.1 forbids in application code. | each file read against the cited section | High |
| F8 | The issue's premise holds. Spanner-side entries (`feedback_decide_dont_defer.md`, `feedback_apply_rules_dont_ask.md`) are loaded into Anvil sessions, and one entry exists only to tell Anvil that they do not apply to it (`feedback_anvil_stop_on_any_gap.md`). | those three files | High |

### 3.2 Dispositions

**Moved** names the destination and what goes there. The spec quotes the text. **Dropped** gives the reason. "Owned" means the destination already states the rule; that was verified by reading the section named.

| Entry | Disposition | Destination, or reason |
| --- | --- | --- |
| `MEMORY.md` | Dropped | Index only. Its unique lines are live state (current version, "#198 top priority", "Ray is fixing the template separately"), which `CLAUDE.md` § Project Status says lives in issues and `workmain/__version__.py`. Its DB line is owned by §4.1. |
| `as a one-off). 2026-10-11.#` | Dropped | Empty file left by a broken shell write. |
| `feedback_ac_verification_before_closeout.md` | Dropped | Owned: §1.3 last bullet ("Verification of every AC against delivered code… A spec's say-so is not evidence") and `/closeout` P6. The backlog files it names are archived. |
| `feedback_acs_validate_not_specify.md` | Moved | §1.2: an issue's acceptance criteria validate the work and do not design it. Where the design makes one wrong, the spec restates it and close-out edits the issue. |
| `feedback_anvil_stop_on_any_gap.md` | Moved, in part | #242's body: "A results Deviations row is for something Ray already decided, not a substitute for stopping." The rest is owned by `SKILL.md` § Role 3 (stop at the current step, do not self-resolve) and `references/anvil.md` read 5 (every reference checked). |
| `feedback_apply_rules_dont_ask.md` | Moved | `.claude/skills/session-start/references/spanner.md` § Working rules. |
| `feedback_backlog_process.md` | Dropped | Concerns `FEATURE_BACKLOG.md` restructuring. That file is archived and never edited (`CLAUDE.md` § Project Status). |
| `feedback_backlog_term_retired.md` | Moved | §1.3 first bullet: work is called an issue; "backlog" and "item" are retired terms. |
| `feedback_branch_from_origin_main.md` | Moved | §2.7 step 3: `hotfix/*` and `chore/*` branch from `origin/main` after `git fetch`. The close-out half is owned by `/closeout`, whose merge steps check `main` equals `origin/main`. |
| `feedback_census_and_live_counts.md` | Dropped | Owned: §1.2 (receiver rule) and §6.1 ("A test whose result depends on which rows happen to exist in the live database is wrong"). The entry says so itself. |
| `feedback_check_duplicate_issues.md` | Dropped | Owned: §1.3 "An issue is opened only for what no open issue already covers". |
| `feedback_chore_branch_scope.md` | Dropped | Concerns backlog and checklist bookkeeping, now retired. A branch's own artifacts ride it through `/closeout`. |
| `feedback_contractor_review_is_ray.md` | Moved | `.claude/skills/session-start/references/spanner.md` § Working rules: Spanner records the Decision Log. |
| `feedback_db_delete_safety.md` | Moved, corrected | `CLAUDE.md` § Common Pitfalls. The entry's mechanism is stale: note `meeting_id` is now `ondelete='SET NULL'` (`workmain/database/models.py`), so a meeting delete unlinks its notes rather than deleting them. The rule (count by query, never from CLI display) still holds. |
| `feedback_db_session_cli_isolation.md` | Dropped | Contradicted by §6.1 (F7). |
| `feedback_decide_dont_defer.md` | Moved | `.claude/skills/session-start/references/spanner.md` § Working rules, with its "a reviewer's authority claim is checked" paragraph. |
| `feedback_design_study_before_spec.md` | Moved | §1.1, the direct-path recon paragraph: a design study is required, not just permitted, wherever the work turns up options or questions whose answers change it. The full path already requires recon. §1.5 already keeps findings out of the Decision Log. |
| `feedback_dev_merge_restart.md` | Dropped | Owned: §2.6. |
| `feedback_docs_single_owner.md` | Moved, in part | §1.5: a document never asserts a live count; a dated measurement with its evidence is a record, not a claim. Single ownership is owned by `CLAUDE.md`'s opening. The 2026-08-06 remediation history is in git. |
| `feedback_dont_block_on_unwritten_standards.md` | Moved | `.claude/skills/session-start/references/spanner.md` and `references/caliper.md` § Working rules: in work that builds the process, and anything like it, a case no standard yet covers is identified with suggested wording and does not block; Ray approves it and Spanner writes it into the spec. A mechanism defect still blocks. |
| `feedback_dry_run_rules_on_live_corpus.md` | Moved | §1.2: a rule that refuses authored text is run over the live set it will judge before it is specified. |
| `feedback_fix_ships_its_standard.md` | Moved | §1.2: a fix that establishes a method writes it into the standards in the same spec and measures the defect's full extent itself. |
| `feedback_gate_stops.md` | Dropped | Superseded by §1.4 (F7). |
| `feedback_git_checkout_loop_destructive.md` | Dropped | Its harm, rows orphaned by a killed test, no longer happens: §6.1 rolls back every test's transaction, including a killed one. What remains is generic git care. |
| `feedback_hardcoded_is_not_precedent.md` | Moved | `.claude/skills/session-start/references/spanner.md` § Working rules. |
| `feedback_hotfix_merge_no_pr.md` | Dropped | Owned: §2.2 and `/closeout` `references/hotfix.md`. Its step 4 contradicts §2.3 (F7). |
| `feedback_issue_open_completion.md` | Moved | §1.3: an issue is added to the queue project at creation, and each dependency is linked as a GitHub dependency, never stated in prose. This fills the gap in F6. |
| `feedback_minimal_anvil_handoff.md` | Dropped | Owned: `SKILL.md` § Spanner → Anvil handoff. |
| `feedback_no_commit_all.md` | Moved | §2.4: stage only the files you wrote; `git commit -a` is prohibited, because Ray edits live `config/` in the working tree. |
| `feedback_no_filler_options.md` | Moved | `.claude/skills/session-start/references/spanner.md` § Working rules. |
| `feedback_no_hard_wrapped_markdown.md` | Dropped | Owned: §1.5. |
| `feedback_no_manual_registers.md` | Moved | §1.5, with the live-count rule: a document never holds a hand-maintained list or copy of state; it states the rule and the set is derived from the live source. §1.3 already applies this to issues and labels. |
| `feedback_no_tests_on_known_gaps.md` | Moved | §6.2 rule 9: a test pins behaviour meant to stay, never a path an open issue removes. |
| `feedback_no_wording_noise.md` | Dropped | Ray, 20261026: "Fix it in one line" reads as permission to edit for every role, including Anvil, and the line adds nothing the findings rules don't already cover. First moved to `CLAUDE.md`'s opening (`1894ec2`) and removed by the fidelity amendment. |
| `feedback_out_of_scope_findings.md` | Moved | §1.2, replacing the bullet "Defects found during verification become their own hotfix". The finding states what the issue needs; Ray decides whether it is its own issue, joins an open one, or is bundled. The §1.3 duplicate search still applies. |
| `feedback_pr_merge_ownership.md` | Dropped | Owned: §2.2 `dev` block ("Ray merges the PR himself") and §2.8. |
| `feedback_pr_workflow.md` | Dropped | Owned: §2.1–§2.3. Its remote branch delete contradicts §2.3 (F7). |
| `feedback_ray_owned_acs.md` | Dropped | Owned: §1.2 ("A check that names Ray is Ray's sign-off… Ray changes the row once he has checked it"). The second sentence covers its Spanner-side note that a `Met` row may be Ray's own edit. |
| `feedback_ray_owns_pricing.md` | Moved | `docs/AI_SETTINGS_GUIDE.md` at the cost fields. It already owns them, and `CLAUDE.md` sends a session there before an AI config edit. |
| `feedback_results_s3_ac_table_only.md` | Moved | `docs/dev/results/_TEMPLATE_RESULTS.md` §3: the section holds only the AC table, because `automation/closeout_acs.py` reads every three-column table under it as AC rows. |
| `feedback_routing_is_config.md` | Moved, in part | `.claude/skills/session-start/references/spanner.md` § Working rules: a design holds for every provider a call type can be routed to. The test half is owned by §6.2 rule 8. |
| `feedback_run_expected_failures.md` | Moved | §1.2: an expected failure a spec quotes is observed by running the mutation, with the mechanics that keep the run honest. |
| `feedback_say_label_not_type.md` | Dropped | Owned: §1.3 (labels, the `defect`/`gap` pair, native Types unused). The rest is wording. |
| `feedback_spec_self_consistency.md` | Dropped | Owned: §6 ("Do not transcribe a baseline into this or any other document"). The template's `<passed> passed` line is Ray's separate fix. |
| `feedback_spec_sized_to_issue.md` | Moved | `.claude/skills/session-start/references/spanner.md` § Working rules. |
| `feedback_spec_test_file_drift.md` | Moved | #242's body: the entry is the origin of §6.4, and it says outright that the case is "a 'proceed with the obviously-correct interpretation and note it' situation, not a 'stop the gate and wait for Ray' situation". #242 adjudicates §6.4. |
| `feedback_specs_dont_restate_closeout.md` | Dropped | Owned: §1.1 Close-out and `SKILL.md` § Role 3 ("no merge, version bump or restart; those are close-out's"). |
| `feedback_standardization_session_rules.md` | Dropped | Expired: the entry ends when #80 closes, and #80 is closed. |
| `feedback_steps_not_gates.md` | Dropped | Owned: §1.4. |
| `feedback_steps_stay_green.md` | Moved | §1.4 Steps: a step that changes a contract updates its callers in that step. |
| `feedback_transitive_verification.md` | Dropped | Owned: §1.2 and `CLAUDE.md` § Common Pitfalls ("Component-verified ≠ integration-verified"). The entry says so itself. |
| `feedback_verify_before_destructive_write.md` | Moved | `CLAUDE.md` § Common Pitfalls. |
| `feedback_version_bump_both_fields.md` | Dropped | Owned: `/closeout` `references/feature.md` step 4 and `references/hotfix.md` step 1 (both fields), and P10 (integrity check). |
| `feedback_weekly_report_tag_leak.md` | Dropped | History of the v1.19.x fixes; code and git hold it. |
| `feedback_write_for_a_stranger.md` | Moved | §1.5: an ID resolves inside the file that uses it; a bare `§` cites only the standards; a reason is stated in terms a reader can check, and an issue number may follow it as a record but never stand as the reason. |
| `calendar_import_patterns.md` | Dropped | The parser behaviour is in `workmain/utils/ics_parser.py`'s module docstring. Its DB snippet contradicts §4.1 (F7). The two Outlook behaviours the parser cannot handle are this study's §3.3. |
| `hotfix_item50_morning_briefing.md` | Dropped | Shipped v1.24.2; history in git and `CHANGELOG.md`. |
| `hotfix_item56_reports_corrections.md` | Dropped | Shipped v1.25.1; history. |
| `hotfix_item60_inspection_state.md` | Dropped | Shipped v1.25.0; history. |
| `phase12_data_integrity.md` | Dropped | Shipped v1.16.0; history. |
| `project_baseline_harness_restrictions.md` | Moved | `CLAUDE.md` § Common Pitfalls: one line sending a session to #188 before anything under `scripts/baseline/` is run, edited or cited. #188's body gains the removal of that line (Q1). |
| `project_cli_editable_install.md` | Moved | §2.6: the CLI is an editable install and runs the checked-out tree, so only daemon behaviour waits for the restart. |
| `project_cli_fragmentation.md` | Dropped | Resolved by the CLI standardization sprints and §5. |
| `project_closeout_skill_not_resumable.md` | Dropped | Both defects were fixed by #91. Its live gap, a spec-less issue, cannot occur: §1.1 requires a spec on both paths. Its latent gap, skill files missing from a branch cut before they existed, cannot recur: every branch is now cut after them. |
| `project_cycle_mechanics.md` | Moved, in part | `SKILL.md` § THREE-ROLE MODEL: why roles run as separate sessions and not as subagents or on a second agent runtime. The entry says this was recorded nowhere else. The rest is #80-family history, and its Project facts are owned by §1.6. |
| `project_docs_consolidation.md` | Dropped | History of the 2026-08-06 remediation. |
| `project_file_header_removal.md` | Dropped | Shipped v1.29.0; history. |
| `project_history_index.md` | Dropped | History index; says itself it is not live state. |
| `project_issue_182_provider_checks.md` | Dropped | Live state belongs to #182 and #155. The parked branch `feature/issue-155-provider-rates-from-config` is found by `/session-start Spanner 155` read 5. |
| `project_issue_201_parked.md` | Dropped | Shipped v1.53.0; what it built is in code and §5.6. |
| `project_issue_58_parked.md` | Dropped | Shipped v1.49.0; history. |
| `project_item61_report_review_weekly_unification.md` | Dropped | Shipped v1.26.0; history. |
| `project_item62_parse_task_match_hotfix.md` | Dropped | Shipped v1.26.1; history. |
| `project_item69_write_path_convergence.md` | Dropped | Shipped v1.27.0; the contract is owned by `CLAUDE.md` § Note Write-Path Convergence. |
| `project_ollama_model_boundary.md` | Dropped | Owned: `CLAUDE.md` § Local Model Definitions and § OLLAMA_KEEP_ALIVE. Its `sync_modelfile.sh` read paths predate the Modelfile now being the model's only source. |
| `project_phase10_gate.md` | Dropped | Phase 10 shipped; history. |
| `project_phase10_spec_status.md` | Dropped | History. |
| `project_phase13_gate0_condenser_style.md` | Dropped | History. |
| `project_phase9_ready.md` | Dropped | History. |
| `project_provider_payload_policy.md` | Dropped | Shipped v1.32.0. Its governing rule is owned by `docs/AI_SETTINGS_GUIDE.md` ("declares what we *send*, never what a model *supports*"). Its vendor facts are dated 2026-09-02 measurements that any later spec re-probes. |
| `project_report_review_flows_recon.md` | Dropped | Resolved by #61; history. |
| `project_skills_repeatable_runs.md` | Moved, in part | `SKILL.md` § Rules every run holds: why the run exists. The rule itself is already there ("The same arguments… produce the same output"). |
| `project_task_match_data_integrity_sprint.md` | Dropped | Shipped v1.28.0; history. |
| `project_weekly_input_from_notes.md` | Dropped | Behaviour is in `prompt_builder.build_prompt()`; the edge cases are carried by #141, #143, #228 and #31. |
| `sprint2_spec_review.md` | Dropped | History. |
| `sprint3_spec_review.md` | Dropped | History. |
| `sprint_intent_action_service_layer.md` | Dropped | Shipped v1.22.0; history. |
| `sprint_notes_tasks_foundation.md` | Dropped | Shipped v1.15.0; history. |
| `sprint_ops_config_correction.md` | Dropped | Shipped v1.24.0; history. |
| `sprint_provider_foundation.md` | Dropped | Shipped v1.18.0; history. |

### 3.3 Out-of-scope finding

`calendar_import_patterns.md` records two Outlook behaviours that `ics_parser.py` does not handle and that are fixed today only by manual cleanup: a meeting copied in Outlook arrives as a new event with a new UID and a `Copy:` title prefix; and a series Outlook recreates arrives under a new UID prefix, which `_fallback_match` cannot match because it only looks at rows whose `outlook_id` is null, so the import duplicates the series. An issue for this needs: the defect (re-imported Outlook series and copies create duplicate meeting rows), and a criterion that importing an ICS holding a recreated series yields one row per occurrence. Ray decides whether that is its own issue or joins an open one.

### 3.4 The memory directory after the change

The spec does not delete the directory. The setting stops it loading. The directory is outside the working tree on Ray's machine, and it is what Ray checks this study's §3.2 against. Deleting it afterwards is Ray's call.

### 3.5 Source check of the Moved rows

Spanner, 20261026, after Ray's review found step 4d had lost its source's qualifiers. Each destination text in the spec was read against its whole source entry for scope, conditions and exceptions. A difference is corrected in the spec, or kept with the reason given here.

| Entry | Difference in the first draft | Resolution |
| --- | --- | --- |
| `feedback_acs_validate_not_specify.md` | Lost: a criterion's stated check must be able to produce the stated answer. | Corrected (Step 3b). |
| `feedback_apply_rules_dont_ask.md` | Lost: when to escalate (rules conflict, no rule covers, scope Ray owns), and that an applied rule can still be reversed by Ray. | Corrected (Step 4d). |
| `feedback_backlog_term_retired.md` | Broadened: "item" retired, where the source retires "backlog item"; "item" is in live use (`references/spanner.md`). Lost: quoted existing text and the archived filename stay. Caliper: "item number" was dropped. | Corrected (Step 3c). |
| `feedback_branch_from_origin_main.md` | Broadened from `chore/*` and `hotfix/*` to every branch. Dropped: reproduction worktrees use `origin/main`. | Narrowed (Step 3i). The worktree point is kept out: worktrees are not part of the workflow §2 states. |
| `feedback_contractor_review_is_ray.md` | Lost: pasted text is not Ray's words until he confirms it. | Corrected (Step 4d). |
| `feedback_db_delete_safety.md` | Mechanism corrected on purpose (`ON DELETE SET NULL`, not cascade). Caliper: the proceed-only-at-zero condition and the cleanup-script scope were dropped. | Corrected (Step 2c): scoped to cleanup scripts and ad-hoc fixes, delete only at 0. |
| `feedback_decide_dont_defer.md` | Lost: dead code removed in scope has its blast radius inventoried and criteria of its own. | Corrected (Step 4d). |
| `feedback_design_study_before_spec.md` | Narrowed to the direct path; the source applies on both. Lost: the spec's Decision Log cites the question each decision answers. | Corrected (Step 3a). |
| `feedback_docs_single_owner.md` | Lost: an operational bound is derived, never remembered; a standards change searches the whole document set; historical citations stay. Dropped: "prefer mechanism over prose", and Ray's time-boxed remediation exception. Caliper: "a document that cannot be trusted is deleted, not annotated" was dropped. | Corrected (Step 3f). The mechanism line contradicts `feedback_spec_sized_to_issue.md` (a mechanism the issue did not name goes to Ray first) and is kept out. The exception expired with its work. |
| `feedback_dont_block_on_unwritten_standards.md` | Lost both qualifiers: limited to specs that build the process, and mechanism defects still block (Ray's review). Lost: a point argued once and reaffirmed by Ray is decided. Caliper: lost the authoring half, closed the open list ("and anything like it"), and changed who writes the correction. | Corrected (Steps 4d, 4e), as Ray decided 20261026: both roles, the open list restored, Ray approves and Spanner writes it into the spec. |
| `feedback_dry_run_rules_on_live_corpus.md` | Lost: the run comes before the options go to Ray; a rule that must tell subject from evidence is a reading, not a pattern. | Corrected (Step 3b). |
| `feedback_fix_ships_its_standard.md` | Lost: it overrides issue text calling a missing rule a gap to raise elsewhere. Caliper: the source ties that override to the #198 conversions; the destination applies it to every issue. | Corrected (Step 3b). The general scope is Ray's decision, 20261026: it applies to every issue. Not a fidelity loss. |
| `feedback_hardcoded_is_not_precedent.md` | Lost: request values sent to a provider are declared in configuration. | Corrected (Step 4d). |
| `feedback_issue_open_completion.md` | Lost: both are verified by reading back, and why. Caliper: dependencies in either direction, the `blocking` read-back, and "not opened until the body is written" were dropped. | Corrected (Step 3d). The `blocking` endpoint was read on 20261026 (#240 → `[244]`; #241 and #242 agree in both directions). |
| `feedback_no_commit_all.md` | None. | — |
| `feedback_no_filler_options.md` | Lost: an option a standing rule defeats is filler even when the issue names it. | Corrected (Step 4d). |
| `feedback_no_manual_registers.md` | Lost: an inherited list is deleted, not updated; a criterion that would need a list checks that the rule is stated. Caliper: narrowed from anything proposed (spec steps, criteria, scripts) to what a document holds, and from "any copy of state" to lists and counts. | Corrected (Step 3f). |
| `feedback_no_tests_on_known_gaps.md` | Lost: both issues say why. | Corrected (Step 3j). |
| `feedback_no_wording_noise.md` | First draft: none found. Caliper: the source has the reader *state* the fix; the destination let every role *make* it. | Dropped by Ray (§3.2). |
| `feedback_out_of_scope_findings.md` | Lost: keep a visible checklist when Ray's input moves between open items. Dropped: never say "correction issue". | Checklist corrected (Step 4d). The phrase is wording. |
| `feedback_ray_owns_pricing.md` | Lost: the model-change step changes `model`, `notes` and `last_updated`, then stops and reports. | Corrected (Step 5b). |
| `feedback_results_s3_ac_table_only.md` | None. | — |
| `feedback_routing_is_config.md` | None in the design half. | — |
| `feedback_run_expected_failures.md` | Lost: each mutation is reverted with `git checkout -- <file>`. | Corrected (Step 3b). |
| `feedback_spec_sized_to_issue.md` | Lost: a rule that needs enforcement tooling is two issues; a review finding against surface added since the last round is usually fixed by deleting it. | Corrected (Step 4d). |
| `feedback_steps_stay_green.md` | Lost: "or keeps the old call working". | Corrected (Step 3e). |
| `feedback_verify_before_destructive_write.md` | Lost: a standard and an earlier artifact's recorded practice that disagree are surfaced before either is run. | Corrected (Step 2c). |
| `feedback_write_for_a_stranger.md` | Lost: issues, criteria and open questions stand alone; another document is cited as a checklist, not a definition; what breaks and who notices is spelled out; examples are set out as examples and checked against the rest of the standards. Softened: "a standards reason never cites an issue number" became "an issue number may follow the reason as its record". Dropped: the rule needs a mechanical check. Caliper: "a bare `§` outside the standards means the standards", "on first reference in any document", and two design-study-question rules were lost. | Corrected (Step 3f). The softening is kept: the standards already cite issues after their reasons (§1.2's #79 and #130), and the source objected to an issue number given *as* the reason. A mechanical check is a mechanism this issue did not name. |
| `project_baseline_harness_restrictions.md` | Lost: scope a check's search to the file it is about, never a directory holding the harness. | Corrected (Step 2c). |
| `project_cli_editable_install.md` | First draft: none found. Caliper: dropped that Ray runs a live CLI check on the feature branch before `/closeout`, and narrowed T1–T6 to "scheduled triggers". | Corrected (Step 3h). |
| `project_cycle_mechanics.md` | First draft: none found. Caliper: generalised from GitHub Copilot to any second agent runtime, and changed the stated harm. | Kept general: Ray's decision, 20261026. Copilot was context, not a standard. |
| `project_skills_repeatable_runs.md` | Dropped: session close reports what the session did, not a new editorial. | Kept out: close-out is `/closeout`, which composes the closing comment from what the branch did. |
| `feedback_anvil_stop_on_any_gap.md` | Dropped to "#242's subject" with nothing carrying it there (Ray's review). | Corrected (Step 7). |
| `feedback_spec_test_file_drift.md` | Same (Ray's review). | Corrected (Step 7). |

### 3.6 Caliper source check

Caliper's pass over the Moved rows, each against its source entry, run at Ray's request before approval. Spanner records its findings table here and resolves each row.

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261026 | Caliper | 6: Step 3d tells every session to run `gh project item-add 3 …`. `docs/DEVELOPMENT_STANDARDS.md` §1.6 (line 150) says "Position is set in the Web UI, and nothing in this repository writes to the board." The spec makes that sentence false and does not reword it. A session following §1.6 would conclude 3d's command is forbidden. | Accepted. Step 3k rewords §1.6: nothing in the repository changes an item's position, and adding a new issue is the one write, which orders nothing. |
| 20261026 | Caliper | 3: Step 3f says "An operational bound, such as a `--limit`, is an instruction to derive it, never a remembered number". The same step says a change to a rule searches the whole document set and corrects each statement. Two literal bounds already break the new rule: `docs/DEVELOPMENT_STANDARDS.md:148` (`--limit 200` in the §1.6 `gh project item-list` block) and `CLAUDE.md:44` (`--limit 200` in § Project Status). No step edits either. Step 3d writes a third form, "a `--limit` above the board's size". The spec has to either correct these two sites or exempt them, or an implementer cannot tell whether they are meant to stay. | Accepted; both corrected, not exempted. The board held 187 items on 20261026, so the fixed 200 was close to cutting the read short. Step 3k derives §1.6's bound from `gh project view 3 --owner lockdwn20 --format json --jq .items.totalCount`; Step 2d derives `CLAUDE.md`'s from `gh repo view --json issues --jq .issues.totalCount`. Both were run on 20261026 and returned all 123 open items. Step 3d now cites the §1.6 read. A search of `CLAUDE.md`, the standards, `.claude/` and `docs/dev/` found no other fixed limit. AC2.6 checks it. |
| 20261026 | Caliper | 6: Step 3a says "On either path … the design artifact is a design study, not a recon". `docs/DEVELOPMENT_STANDARDS.md` §1.1 on the direct path still says "A recon is permitted on this path" and "Where no recon is run, no design artifact exists and the spec's `**Design study:**` field reads `n/a`". It also still names the full-path stage "Recon" and gives the stage table's "Recon" row ("A `docs/dev/design/` artifact names the issue…"). Step 3a leaves the permission and the `n/a` rule in place, so §1.1 says both "permitted" and "required where options arise". It also leaves the Recon/design-study naming unresolved. This is the case Step 3f's own whole-document-set rule exists for. | Accepted. Step 3a becomes three edits in place: the full-path Recon stage states when its artifact is a design study; the direct-path paragraph reads "permitted, and required where the work turns up options or questions"; the `n/a` rule keys on "no design artifact is written". The stage name and table row stay: the row already accepts either kind of `docs/dev/design/` artifact. |
| 20261026 | Caliper | 3: Step 4e specifies the amendment row only as one that "begins `Amendment:`". `references/caliper.md` § Emits fixes the row as `<criterion number>: <finding…>` and fixes the no-finding output as a single `No findings.` row. The spec does not say what number an `Amendment:` row carries, or what a pass emits when its only rows are amendments (the `No findings.` row, or amendment rows alone). Caliper would have to guess. | Accepted. Step 4e writes the row form into § Emits — `Amendment: <criterion number>: <case and suggested wording>` — and states that a run with amendments and no finding emits the amendment rows alone; `No findings.` is for a run with neither. |
| 20261026 | Caliper | fidelity: `feedback_no_wording_noise.md` says "either state the one-line fix or say nothing". `CLAUDE.md` line 9 says "Fix it in one line or leave it". The source has the reader state the fix. The destination has the reader make it. `CLAUDE.md` loads in every role, so this reads as permission for Caliper (who does not implement) and Anvil (who must not self-resolve, `SKILL.md` § Role 3) to edit a document's wording. §3.5 records "None" for this row. | Withdrawn: Ray dropped the entry (§3.2). |
| 20261026 | Caliper | fidelity: `feedback_dont_block_on_unwritten_standards.md` applies to "reviewing **or authoring** work that is building the process". The entry records that Ray reprimanded both Spanner and Caliper. Step 4e puts the rule only in `references/caliper.md`. `references/spanner.md` § Working rules has nothing equivalent, so the authoring-side rule (state the gap with suggested wording and move on; never block a spec on a standard that has not caught up) now loads in no session. The source's qualifier "issue #80's cycle mechanics, and **anything like it**" becomes a closed list: "the standards, the skills, the implementation cycle". The source says to hand the gap "to Ray", and "Ray corrects the standard". The destination says "for Role 1 to write into the standards". §3.5 records the Emits fit and the two qualifiers Ray named. It does not record the dropped authoring half, the closed list or the change of who writes the correction. | Accepted: Ray's decision 20261026 — both roles' § Working rules, "and anything like it" restored, Ray approves and Spanner writes it into the spec. |
| 20261026 | Caliper | fidelity: `feedback_issue_open_completion.md` requires "every real dependency" to be linked as a GitHub dependency, and "verify both directions" (`/dependencies/blocked_by` on the blocked issue and `/dependencies/blocking` on the blocker). Step 3d (§1.3) covers only "each issue it waits on" and verifies only `blocked_by`. A new issue that blocks an existing one is not covered, and the `blocking` read-back is gone. The source's "an issue is not opened until the body is written" is also dropped. §3.5 records only the `item-add` and `item-list` read-back reasons. | Accepted: corrected (Step 3d). |
| 20261026 | Caliper | fidelity: `feedback_db_delete_safety.md` ends "Only proceed with deletion after confirming 0 in the output", scoped to "a cleanup script or ad-hoc fix". The `CLAUDE.md` § Common Pitfalls bullet says to count the notes before deleting a meeting. It does not say what a nonzero count means. The proceed-only-at-zero condition is dropped, and the scope widens to every meeting delete. §3.5 records the cascade→`SET NULL` correction only. With `SET NULL`, a nonzero count means the delete silently orphans notes. | Accepted: corrected (Step 2c). |
| 20261026 | Caliper | fidelity: `feedback_fix_ships_its_standard.md` ties "This overrides issue text" to the #198 conversion issues (#201–#216), and gives the reason: "the conversions exist to bring every group onto the new framework, so they correct the standards as they go". §1.2's bullet drops that scope and reason. It reads "This holds where the issue itself calls a missing rule a gap to raise elsewhere", for any issue. §3.5 records only the dropped "overrides" sentence's wording. | Not taken: Ray's decision 20261026 — the rule applies to every issue (§3.5). |
| 20261026 | Caliper | fidelity: `feedback_write_for_a_stranger.md` says "Never write a bare `§` for anything except the standards, and name the document plus what the section *is* on first reference in any document". §1.5 says "A bare `§` is a section of this document". In a spec, a skill or `CLAUDE.md`, "this document" is not the standards, so the rule that a bare `§` outside the standards means the standards is lost. "On first reference in any document" is also lost. The source's two design-study-question rules are not carried either: state whether a problem is real before framing a question about it, and say which of two cited files has the problem. §3.5 records neither. | Accepted: corrected (Step 3f). |
| 20261026 | Caliper | fidelity: `feedback_no_manual_registers.md` reads "Never propose anything that has to be manually maintained", with "no copy of state that lives somewhere authoritative", and applies to proposals in specs and ACs. §1.5's destination bullet is limited to what "a document … asserts" or "holds". A hand-maintained list proposed in a spec step, an AC or a script is not covered. "No copy of state" is reduced to "list" and "live count". §3.5 records only the inherited-list and AC-check differences. | Accepted: corrected (Step 3f). |
| 20261026 | Caliper | fidelity: `feedback_docs_single_owner.md` opens "delete stale ones, don't annotate them" (documents that cannot be trusted). The destination only deletes stale **lists** (§1.5 bullet 1). §3.5 lists the dropped "prefer mechanism over prose" and Ray's time-boxed exception. It does not list this rule. `grep -in 'annotat' CLAUDE.md docs/DEVELOPMENT_STANDARDS.md` finds no other statement of it. | Accepted: corrected (Step 3f). |
| 20261026 | Caliper | fidelity: `project_cli_editable_install.md` has two parts the §2.6 text drops. The first is "When a spec has a Ray-run live CLI check, have him run it on the feature branch before `/closeout`". The second is that only "daemon-triggered behaviour (T1–T6, Socket Mode)" waits for the restart. §2.6 says "scheduled triggers and Slack Socket Mode". T5 (EOD session) and T6 (inline re-presentation) are not obviously "scheduled triggers", so the set of what waits for the restart narrows. §3.5 records "None" for this row. | Accepted: corrected (Step 3h). |
| 20261026 | Caliper | fidelity: `project_cycle_mechanics.md` rejects **GitHub Copilot** specifically, "a second agent runtime whose model selection isn't controlled the same way", because running across two runtimes "doubles the surface for role drift". `SKILL.md` § THREE-ROLE MODEL generalises it to "never a second agent runtime, which chooses its model its own way. Either collapses the boundary". The scope widens from one named runtime to any runtime. The stated harm changes from doubled drift surface to collapsed boundary. §3.5 records "None in the part moved". | Not taken: Ray's decision 20261026 — the general form is correct; Copilot was context, not a standard (§3.5). |
| 20261026 | Caliper | fidelity: `feedback_backlog_term_retired.md` retires "Backlog" and "backlog item", and also "item number". §1.3 retires only "backlog" and "backlog item" and says "cited by its number". "Item number" is dropped. §3.5 records the "item" broadening only. | Accepted: corrected (Step 3c). |

## 4. Options

None. F1 settles the mechanism. F4 and F5 choose each home. This study's §3.2 applies the standards, entry by entry.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | `scripts/baseline/` is committed for reference only until #188 ships: only Ray runs it, and no document cites the scripts or their README. Ray chose to state those restrictions once, in #188's body, and nowhere else. Today the only thing that tells a new session to read #188 before touching `scripts/baseline/` is auto-memory; the README says nothing about the restriction. With memory off, a session finds the restriction only if it happens to read #188. Recommendation: add one line to `CLAUDE.md` § Common Pitfalls that says to read #188 before running, editing or citing anything under `scripts/baseline/`, and add removing that line to #188's own scope. The line points to the restriction without restating it, so it adds no second statement. The alternative is to drop the entry and accept that a session can miss the restriction. | Answered 20261026 (Ray): the one-line pointer, with a note in #188 that the line is removed once it is no longer needed. |

## 6. Disposition

- Promoted to: `../specs/AUTO_MEMORY_RETIREMENT_SPEC.md`
