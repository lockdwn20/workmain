# Assertionless Tests — Design Study

**Status:** Active
**Kind:** Design study
**Author:** Spanner (Role 1)
**Date:** 20261006
**Originating item:** Issue #137

---

## 1. Purpose

Issue #137 says 18 test functions report a result by returning it, which pytest ignores, so they cannot fail. This study checks that claim against the live tree, and records what each test exercises and whether the application still uses it. It also states the one design question the conversion raises: what to do where the only consumer of the code under test is the test itself.

## 2. Scope of the read

- **Read in full:** `tests/test_tag_system.py`, `tests/test_templates.py`, `tests/test_config_system.py`, `tests/test_db_connection.py`, `workmain/utils/tag_utils.py`, `workmain/utils/encryption.py`, `workmain/templates_engine/loader.py`, `workmain/templates_engine/__init__.py`, `workmain/templates_engine/validator.py` `validate_template`/`validate_section`, `workmain/config_manager/validator.py` `validate_email`/`validate_time`, `workmain/config_manager/loader.py` `get_database_config`, `workmain/database/connection.py`.
- **Swept:** every `test*` function under `tests/`, by AST, for one with neither an `assert` statement nor a call to `assert*`, `pytest.fail`, `pytest.raises` or `pytest.warns`. The script is the evidence for F2. Its mechanism is the same one #137 AC1 asks for.
- **Swept:** `workmain/` and `scripts/` for callers of every function the 17 tests exercise.
- **Run:** bare `pytest` and `pytest automation/` on `origin/main` `0c126ec`, 20261006. The suite gave `1128 passed, 0 failed, 0 skipped`, and `automation/` gave `51 passed, 0 failed, 0 skipped`. These are this study's run, not a baseline for the branch.
- **Not read:** the application paths that filter notes into reports by tag, beyond confirming where they live (F6).

## 3. Findings

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F1 | The count is **17**, not 18. #150 deleted `test_template_info` from `tests/test_templates.py` on 20261001, after #137 was written. The live split is tag 9, templates 4, config 3, database 1. | commit `61e9f3d`; `pytest` warning list, 20261006 | Low |
| F2 | The repository-wide sweep finds **24** test functions with no assertion: the 17, plus 7 elsewhere. #137 AC1 is worded over every test under `tests/`, so all 24 are inside it. | sweep, §2 | High |
| F3 | Six of the seven extra tests are "must not raise" tests. An exception fails them, so they can fail. They are still vacuous in one way: none of them checks that the failing call was actually reached. If the code under test returned early, each would still pass. | `tests/test_delivery.py:90` `test_subprocess_failure_does_not_raise`, `:127` `test_no_daemon_logs_warning_no_crash`, `:142` `test_daemon_post_message_failure_does_not_raise`; `tests/test_client_repository.py:143` `test_clear_active_no_active`; `tests/test_provider_foundation.py:975` `test_shipped_config_loads`; `tests/test_report_correction.py:602` `test_unknown_report_id_is_a_no_op` | Medium |
| F4 | The seventh, `test_get_active_none`, has the same defect as the 17. Its docstring says `get_active()` returns `None`, and a comment says it deliberately does not assert that, because a production active client is visible through `db_session`. It cannot fail. | `tests/test_client_repository.py:80-89` | High |
| F5 | All 17 return a truthy value today (16 return `True`, `test_database` returns `0`), and none prints a `✗` under `-s`. No hidden failure sits under the false green, so converting them should not turn the suite red. | `pytest -s` on the four files, 20261006 | Low |
| F6 | **Six of the 17 exercise code with no application caller.** The test is the only consumer. | see F6a–F6f | High |
| F6a | `test_encryption` exercises `workmain/utils/encryption.py`. Nothing in `workmain/` or `scripts/` imports that module. | grep `utils.encryption\|EncryptionManager\|encrypt_api_key`: zero hits outside the module | |
| F6b | `test_config_validator` exercises `workmain/config_manager/validator.py`. Nothing imports that module. | grep `config_manager.validator\|ConfigValidator\|get_validator`: zero hits outside the module | |
| F6c | `test_config_loader` exercises `ConfigLoader.get_database_config`, which has no caller. `get_with_env_override`'s only caller is `get_database_config`, so it is dead transitively. The live database settings are read straight from the environment in `workmain/database/connection.py:19-26`. `get_config()` itself is live. | `workmain/config_manager/loader.py:139`, `:208`; `workmain/templates_engine/renderer.py:351`; `workmain/ai/report_generator.py:331` | |
| F6d | `test_database` exercises `DatabaseConnection.test_connection` and `.get_table_count`, which have no caller. The other `.test_connection` hits are Clockify, Slack and intent-parser methods of the same name. `connect`, `get_session` and `session_scope` are live, through `get_db()`. #95 is planned to route `tests/conftest.py` through `session_scope`. | `workmain/database/connection.py:84`, `:123`; `tests/conftest.py:55` | |
| F6e | `test_report_filtering` exercises `TagSystem.get_tags_for_report`, which has no caller. Reports filter by tag in the repositories, by literal tag name, not through `config/tags.json` `report_inclusion`. So the test name claims report filtering, but it covers a method the reports never use. | `workmain/utils/tag_utils.py:340`; `workmain/database/repositories/meetings_repo.py:396`, `:422` | |
| F6f | `test_section_structure` exercises `TemplateLoader.get_sections`, which has no caller. | `workmain/templates_engine/loader.py:184` | |
| F7 | `test_encryption` runs against the real key, `~/.workmain/encryption.key`, through `get_encryption()`, and `_ensure_key_exists` creates and writes that file when it is missing. That file exists on Ray's machine, dated 20251219. This test is its only plausible author, since nothing else imports the module (F6a). | `workmain/utils/encryption.py:29-51`, `:163` | Medium |
| F8 | `test_database` counts rows in every public table of the live database, and prints the counts. | `tests/test_db_connection.py:43-48` | Low |
| F9 | `test_section_structure` pins the literal section names of the shipped `daily_internal` and `weekly_client` templates. `workmain templates section add` writes new sections into those same files. So a supported CLI action fails the test even though nothing is broken. | `tests/test_templates.py:157-174`; `workmain/cli/commands/templates.py:412`, `:525` | Medium |
| F10 | `test_template_loading` and `test_template_validation` name two templates by hand. `templates/reports/` also holds `monthly_executive.json`, which neither test loads. `TemplateLoader.list_templates()` derives the set. | `tests/test_templates.py:35-108`; `workmain/templates_engine/loader.py:129` | Low |
| F11 | `test_variable_substitution` substitutes into the shipped templates' `subject_line` and checks only that no `{` survives. `substitute_variables` takes any template dict, so a test can give it its own template and assert the exact output. A shipped template whose subject line contains a literal `{` would also break the current test. | `tests/test_templates.py:111-160`; `workmain/templates_engine/loader.py:197-229` | Low |
| F12 | None of the live functions behind the tag and template tests has coverage anywhere else in the suite, except `parse_tags`, which `tests/test_notes_add.py` reaches through the CLI. When converted, these tests become the only direct coverage. | grep of `tests/` for each function name | Medium |

**Not verified:** whether any planned issue intends to use `workmain/utils/encryption.py` or `ConfigValidator`. No open issue was searched. Ray settled it under Q1: the module predates `.env`.

**Found after Q1:**

| # | Finding | Evidence (file:line, symbol) | Severity |
| --- | --- | --- | --- |
| F13 | `ClockifyAuth` imports `Fernet` and `Path` and uses neither. Its docstring says it uses Fernet for storage, but the key is read in plaintext from the environment. `docs/DEVELOPMENT_STANDARDS.md` §3.7 says API keys are Fernet-encrypted at rest, which nothing does. | `workmain/integrations/clockify/auth.py:7-8`, `:16`; `docs/DEVELOPMENT_STANDARDS.md:378-379` | Medium |
| F14 | `cryptography` is still required, by `google-auth`. | `pip show cryptography`, Required-by | Low |
| F15 | A mutation applied within a second of the previous one, leaving the file the same byte size, runs against the previous mutation's cached `.pyc`. Two of the drafting runs did exactly that. | M2 and M11a, first run, 20261006 | High |

## 4. Options — code whose only consumer is the test (F6)

The 11 tests over live code (9 tag tests, minus `test_report_filtering`, plus `test_template_loading`, `test_template_validation` and `test_variable_substitution`) convert under any option. This question covers the other six.

### Option A — Convert all 17 as they stand

- **Approach:** give the six assertions over the dead code exactly as for the other eleven.
- **Pros:** stays inside the issue's literal scope. Remains a `hotfix/*`, because no application file changes.
- **Cons:** six tests then pin behaviour nothing uses, and they are what keeps that code from looking dead. `test_report_filtering` would go on asserting report filtering against a method the reports don't call (F6e), which is the same false confidence #137 exists to remove, in another form. `test_encryption` would go on writing a key into the user's home (F7) unless it is redirected.

### Option B — Delete the dead code with its tests; convert the rest

- **Approach:**
  - Delete `workmain/utils/encryption.py` and `workmain/config_manager/validator.py`.
  - Delete `ConfigLoader.get_database_config` and `get_with_env_override`, `DatabaseConnection.test_connection` and `get_table_count`, `TagSystem.get_tags_for_report`, and `TemplateLoader.get_sections`.
  - Delete the six tests over them, and `tests/test_config_system.py` and `tests/test_db_connection.py` with them, since nothing would be left in either.
  - Correct the two `docs/DEVELOPMENT_STANDARDS.md` citations of the encryption module (§3.3 singleton table, §3.7).
  - Convert the eleven tests over live code.
- **Pros:** every remaining test covers code the application runs. Nothing stays green only because something tests it. Consistent with removing dead code found in scope rather than deferring it. Database connectivity is still proven by every `db_session` test, so the suite errors if the database is unreachable.
- **Cons:** it touches six application files. Under `docs/DEVELOPMENT_STANDARDS.md` §2.2 that makes it `feature/*` from `dev`, not a `hotfix/*`. It takes code out of the application and is a minor release. If a planned consumer of encryption exists (§3, not verified), it would come back from git history.

### Option C — Delete the six tests; leave the dead code

- **Approach:** remove the tests, and open a follow-up issue to remove the code.
- **Pros:** stays a test-only `hotfix/*`.
- **Cons:** leaves application code with no consumer and no test, and defers a removal this branch has already found. Rejected for that reason. It is listed because it is the cheapest route, not as a candidate.

**Recommendation: Option B.** The issue's premise is that these tests should be evidence about the application. For six of them there is no application behaviour to be evidence about, so converting them meets AC3's wording while missing its point. That is the cheapest-way-versus-purpose case `CLAUDE.md` Role 3 names. B turns this into `feature/*` from `dev`. The branch cut this session, `hotfix/issue-137-assertionless-tests`, has no commits and would be deleted locally and recut.

## 5. Design rules the spec will carry (any option)

No open question remains on these; each comes from a finding or a standing rule.

- **The seven tests outside the four files are in scope** because #137 AC1 is repository-wide (F2). `test_get_active_none` gets a real assertion (F4): clear the active client inside the `db_session` transaction, which is rolled back, then assert `get_active()` returns `None`. Each "must not raise" test also asserts that the failing call was reached (F3), so it can no longer pass because the code returned early.
- **Shipped-template tests derive the set** from `list_templates()`, and assert the structure (load succeeds, `validate_template` returns no errors) rather than literal section names (F9, F10).
- **Variable substitution is asserted on a template the test builds itself**, with exact expected strings, so it does not depend on shipped content (F11).
- **Tag tests keep `config/tags.json` as their source.** The tag vocabulary is a `CLAUDE.md` Key Design Decision, so pinning it is pinning a decided contract, not a config value.
- **Each converted test gets a recorded mutation** with an expected failure that was observed by running it, not reasoned about.
- **#137 is restated in the spec at close-out:** 17, not 18 (F1), and under Option B, "converted or deleted with the code it covered".

## 6. Open questions

| Q | Question | Answer |
| --- | --- | --- |
| Q1 | For the six tests whose code has no application consumer (F6), Option A, B or C? B is recommended, and makes the branch `feature/*` from `dev`. | Q1 answered 20261006: Option B. Ray: the encryption module predates the move to `.env` and `python-dotenv`. |

## 7. Disposition

- Promoted to: `../specs/ASSERTIONLESS_TESTS_SPEC.md`
- Superseded by: —
