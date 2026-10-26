# Auto-Memory Retirement — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261026
**Originating item:** Issue #241

---

## 1. Purpose

Issue #241 turns Claude Code auto-memory off for this repository and requires every entry it holds to be read first and given a disposition: moved to the versioned document that should own it, or dropped with a reason. This study holds that disposition for every entry, the home each moved rule goes to, and the one question only Ray can answer. The spec that follows quotes the exact text for each move.

## 2. Scope of the read

- **Read:** every file in `~/.claude/projects/-home-lockdwn20-Projects-workmain/memory/`, read in full by Spanner on 20261026 from this session. The issue expected the read to be Ray-run or Ray-supplied because the directory is outside the repository. It is readable from a Claude Code session on Ray's machine, so Spanner read it directly. Ray's check of §3.2 against his own `/memory` view stands in for the supplied copy. On 20261026 the directory held 90 files: `MEMORY.md` (the index), 88 entry files, and one empty file whose name is a sentence fragment (`as a one-off). 2026-10-11.#`), left by a broken shell write.
- **Checked against:** `CLAUDE.md`, `docs/DEVELOPMENT_STANDARDS.md`, `docs/AI_SETTINGS_GUIDE.md`, `.claude/skills/session-start/` (`SKILL.md` and `references/`), `.claude/skills/closeout/`, the three `docs/dev/*/_TEMPLATE_*.md` files, and the live state of every issue an entry names.
- **Not read:** the Claude Code memory directories of other projects, and user-level `~/.claude/CLAUDE.md`. Neither is governed by this repository.
- **Not in scope:** the three standards passages issue #240 lists as reading like permission to self-resolve, and the results template's deviations table. Both belong to #242. Where an entry restates one of them, its disposition below is "dropped, owned by the standard", and the standard's own fate is left to #242.

## 3. Findings

### 3.1 Mechanism

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| F1 | `autoMemoryEnabled: false` in a project's settings turns auto-memory off for that project. `/memory` shows the toggle. | Claude Code docs, *How Claude remembers your project* § Enable or disable auto memory (code.claude.com/docs/en/memory), read 20261026: "To turn it off for a single project, set `autoMemoryEnabled` in that project's settings" | — |
| F2 | No tracked `.claude/settings.json` exists. `.claude/settings.local.json` is untracked and holds only Ray's personal permissions. | `ls .claude` → `settings.local.json skills`; `git ls-files .claude/settings.json` returns nothing | High |
| F3 | Nothing in the repository names auto-memory. | `grep -rn -i memory CLAUDE.md docs/DEVELOPMENT_STANDARDS.md .claude/` returns no hit about Claude Code memory | High |
| F4 | `references/<role>.md` holds only the session-open run's reads and emits. `SKILL.md` § THREE-ROLE MODEL is the only statement of what each role does, and it holds for the whole session. A standing instruction for one role therefore belongs in `SKILL.md` § Role N. In a reference file it would be a second home for that role's duties, read only when the run is. The issue's third criterion names the reference files; the spec restates it with `SKILL.md` § Role N. | `.claude/skills/session-start/SKILL.md`: "§ THREE-ROLE MODEL below is the only statement of what each role is, does and hands to the others. It holds for the whole session"; `CLAUDE.md` § THREE-ROLE MODEL: "and is stated nowhere else"; `references/anvil.md`, `caliper.md`, `spanner.md` carry only `Reads, in order` and `Emits` | High |
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
| `feedback_anvil_stop_on_any_gap.md` | Dropped | Owned: `SKILL.md` § Role 3 (stop at the current step, do not self-resolve) and `references/anvil.md` read 5 (every reference checked). Its "a deviation row is for something Ray already decided" is #242's subject. |
| `feedback_apply_rules_dont_ask.md` | Moved | `SKILL.md` § Role 1. |
| `feedback_backlog_process.md` | Dropped | Concerns `FEATURE_BACKLOG.md` restructuring. That file is archived and never edited (`CLAUDE.md` § Project Status). |
| `feedback_backlog_term_retired.md` | Moved | §1.3 first bullet: work is called an issue; "backlog" and "item" are retired terms. |
| `feedback_branch_from_origin_main.md` | Moved | §2.7 step 3: `hotfix/*` and `chore/*` branch from `origin/main` after `git fetch`. The close-out half is owned by `/closeout`, whose merge steps check `main` equals `origin/main`. |
| `feedback_census_and_live_counts.md` | Dropped | Owned: §1.2 (receiver rule) and §6.1 ("A test whose result depends on which rows happen to exist in the live database is wrong"). The entry says so itself. |
| `feedback_check_duplicate_issues.md` | Dropped | Owned: §1.3 "An issue is opened only for what no open issue already covers". |
| `feedback_chore_branch_scope.md` | Dropped | Concerns backlog and checklist bookkeeping, now retired. A branch's own artifacts ride it through `/closeout`. |
| `feedback_contractor_review_is_ray.md` | Moved | `SKILL.md` § Role 1: Spanner records the decision log. |
| `feedback_db_delete_safety.md` | Moved, corrected | `CLAUDE.md` § Common Pitfalls. The entry's mechanism is stale: note `meeting_id` is now `ondelete='SET NULL'` (`workmain/database/models.py`), so a meeting delete unlinks its notes rather than deleting them. The rule (count by query, never from CLI display) still holds. |
| `feedback_db_session_cli_isolation.md` | Dropped | Contradicted by §6.1 (F7). |
| `feedback_decide_dont_defer.md` | Moved | `SKILL.md` § Role 1, with its "a reviewer's authority claim is checked" paragraph. |
| `feedback_design_study_before_spec.md` | Moved | §1.1, the direct-path recon paragraph: a design study is required, not just permitted, wherever the work turns up options or questions whose answers change it. The full path already requires recon. §1.5 already keeps findings out of the Decision Log. |
| `feedback_dev_merge_restart.md` | Dropped | Owned: §2.6. |
| `feedback_docs_single_owner.md` | Moved, in part | §1.5: a document never asserts a live count; a dated measurement with its evidence is a record, not a claim. Single ownership is owned by `CLAUDE.md`'s opening. The 2026-08-06 remediation history is in git. |
| `feedback_dont_block_on_unwritten_standards.md` | Moved | `SKILL.md` § Role 2: a case no standard yet covers is a one-line amendment with suggested wording, listed apart from the findings. |
| `feedback_dry_run_rules_on_live_corpus.md` | Moved | §1.2: a rule that refuses authored text is run over the live set it will judge before it is specified. |
| `feedback_fix_ships_its_standard.md` | Moved | §1.2: a fix that establishes a method writes it into the standards in the same spec and measures the defect's full extent itself. |
| `feedback_gate_stops.md` | Dropped | Superseded by §1.4 (F7). |
| `feedback_git_checkout_loop_destructive.md` | Dropped | Its harm, rows orphaned by a killed test, no longer happens: §6.1 rolls back every test's transaction, including a killed one. What remains is generic git care. |
| `feedback_hardcoded_is_not_precedent.md` | Moved | `SKILL.md` § Role 1. |
| `feedback_hotfix_merge_no_pr.md` | Dropped | Owned: §2.2 and `/closeout` `references/hotfix.md`. Its step 4 contradicts §2.3 (F7). |
| `feedback_issue_open_completion.md` | Moved | §1.3: an issue is added to the queue project at creation, and each dependency is linked as a GitHub dependency, never stated in prose. This fills the gap in F6. |
| `feedback_minimal_anvil_handoff.md` | Dropped | Owned: `SKILL.md` § Spanner → Anvil handoff. |
| `feedback_no_commit_all.md` | Moved | §2.4: stage only the files you wrote; `git commit -a` is prohibited, because Ray edits live `config/` in the working tree. |
| `feedback_no_filler_options.md` | Moved | `SKILL.md` § Role 1. |
| `feedback_no_hard_wrapped_markdown.md` | Dropped | Owned: §1.5. |
| `feedback_no_manual_registers.md` | Moved | §1.5, with the live-count rule: a document never holds a hand-maintained list or copy of state; it states the rule and the set is derived from the live source. §1.3 already applies this to issues and labels. |
| `feedback_no_tests_on_known_gaps.md` | Moved | §6.2 rule 9: a test pins behaviour meant to stay, never a path an open issue removes. |
| `feedback_no_wording_noise.md` | Moved | `CLAUDE.md` opening: a wording artifact is not a finding; fix it in one line or leave it. This holds for every role that reports findings. |
| `feedback_out_of_scope_findings.md` | Moved | §1.2, replacing the bullet "Defects found during verification become their own hotfix". The finding states what the issue needs; Ray decides whether it is its own issue, joins an open one, or is bundled. The §1.3 duplicate search still applies. |
| `feedback_pr_merge_ownership.md` | Dropped | Owned: §2.2 `dev` block ("Ray merges the PR himself") and §2.8. |
| `feedback_pr_workflow.md` | Dropped | Owned: §2.1–§2.3. Its remote branch delete contradicts §2.3 (F7). |
| `feedback_ray_owned_acs.md` | Dropped | Owned: §1.2 ("A check that names Ray is Ray's sign-off… Ray changes the row once he has checked it"). The second sentence covers its Spanner-side note that a `Met` row may be Ray's own edit. |
| `feedback_ray_owns_pricing.md` | Moved | `docs/AI_SETTINGS_GUIDE.md` at the cost fields. It already owns them, and `CLAUDE.md` sends a session there before an AI config edit. |
| `feedback_results_s3_ac_table_only.md` | Moved | `docs/dev/results/_TEMPLATE_RESULTS.md` §3: the section holds only the AC table, because `automation/closeout_acs.py` reads every three-column table under it as AC rows. |
| `feedback_routing_is_config.md` | Moved, in part | `SKILL.md` § Role 1: a design holds for every provider a call type can be routed to. The test half is owned by §6.2 rule 8. |
| `feedback_run_expected_failures.md` | Moved | §1.2: an expected failure a spec quotes is observed by running the mutation, with the mechanics that keep the run honest. |
| `feedback_say_label_not_type.md` | Dropped | Owned: §1.3 (labels, the `defect`/`gap` pair, native Types unused). The rest is wording. |
| `feedback_spec_self_consistency.md` | Dropped | Owned: §6 ("Do not transcribe a baseline into this or any other document"). The template's `<passed> passed` line is Ray's separate fix. |
| `feedback_spec_sized_to_issue.md` | Moved | `SKILL.md` § Role 1. |
| `feedback_spec_test_file_drift.md` | Dropped | Owned: §6.4. Whether §6.4 survives is #242's question. |
| `feedback_specs_dont_restate_closeout.md` | Dropped | Owned: §1.1 Close-out and `SKILL.md` § Role 3 ("no merge, version bump or restart; those are close-out's"). |
| `feedback_standardization_session_rules.md` | Dropped | Expired: the entry ends when #80 closes, and #80 is closed. |
| `feedback_steps_not_gates.md` | Dropped | Owned: §1.4. |
| `feedback_steps_stay_green.md` | Moved | §1.4 Steps: a step that changes a contract updates its callers in that step. |
| `feedback_transitive_verification.md` | Dropped | Owned: §1.2 and `CLAUDE.md` § Common Pitfalls ("Component-verified ≠ integration-verified"). The entry says so itself. |
| `feedback_verify_before_destructive_write.md` | Moved | `CLAUDE.md` § Common Pitfalls. |
| `feedback_version_bump_both_fields.md` | Dropped | Owned: `/closeout` `references/feature.md` step 4 and `references/hotfix.md` step 1 (both fields), and P10 (integrity check). |
| `feedback_weekly_report_tag_leak.md` | Dropped | History of the v1.19.x fixes; code and git hold it. |
| `feedback_write_for_a_stranger.md` | Moved | §1.5: an ID resolves inside the file that uses it; a bare `§` cites only the standards; a reason is stated in terms a reader can check, and an issue number may follow it as a record but never stand as the reason. |
| `calendar_import_patterns.md` | Dropped | The parser behaviour is in `workmain/utils/ics_parser.py`'s module docstring. Its DB snippet contradicts §4.1 (F7). The two Outlook behaviours the parser cannot handle are §3.3. |
| `hotfix_item50_morning_briefing.md` | Dropped | Shipped v1.24.2; history in git and `CHANGELOG.md`. |
| `hotfix_item56_reports_corrections.md` | Dropped | Shipped v1.25.1; history. |
| `hotfix_item60_inspection_state.md` | Dropped | Shipped v1.25.0; history. |
| `phase12_data_integrity.md` | Dropped | Shipped v1.16.0; history. |
| `project_baseline_harness_restrictions.md` | Open — Q1 | |
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

`calendar_import_patterns.md` records two Outlook behaviours that `ics_parser.py` does not handle and that are fixed today only by manual cleanup: a meeting copied in Outlook arrives as a new event with a new UID and a `Copy: ` title prefix; and a series Outlook recreates arrives under a new UID prefix, which `_fallback_match` cannot match because it only looks at rows whose `outlook_id` is null, so the import duplicates the series. An issue for this needs: the defect (re-imported Outlook series and copies create duplicate meeting rows), and a criterion that importing an ICS holding a recreated series yields one row per occurrence. Ray decides whether that is its own issue or joins an open one.

### 3.4 The memory directory after the change

The spec does not delete the directory. The setting stops it loading. The directory is outside the working tree on Ray's machine, and it is what Ray checks §3.2 against. Deleting it afterwards is Ray's call.

## 4. Options

None. F1 settles the mechanism. F4 and F5 apply existing rules to choose each home. §3.2 applies the standards, entry by entry.

## 5. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | `scripts/baseline/` is committed for reference only until #188 ships: only Ray runs it, and no document cites the scripts or their README. Ray chose to state those restrictions once, in #188's body, and nowhere else. Today the only thing that tells a new session to read #188 before touching `scripts/baseline/` is auto-memory; the README says nothing about the restriction. With memory off, a session finds the restriction only if it happens to read #188. Recommendation: add one line to `CLAUDE.md` § Common Pitfalls that says to read #188 before running, editing or citing anything under `scripts/baseline/`, and add removing that line to #188's own scope. The line points to the restriction without restating it, so it adds no second statement. The alternative is to drop the entry and accept that a session can miss the restriction. | |

## 6. Disposition

- Promoted to: *(the spec, once written)*
