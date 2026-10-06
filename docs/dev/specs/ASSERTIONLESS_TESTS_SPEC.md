# Assertionless Tests — Spec

**Status:** Approved
**Author:** Spanner (Role 1)
**Date:** 20261006
**Branch:** `feature/issue-137-assertionless-tests` (from `dev`)
**Target release:** v1.42.0
**Originating item:** Issue #137
**Design study:** `../design/DESIGN_ASSERTIONLESS_TESTS.md`

---

## Decision Log

| Date | Source | Decision or finding | Resolution |
| --- | --- | --- | --- |
| 20261006 | Ray | Six of the 17 tests exercise code with no application caller (design study F6, Q1). | Option B. The dead code is deleted with its tests, and the eleven tests over live code are converted. The encryption module predates the move to `.env` and `python-dotenv`. B touches six application files, so the branch is `feature/*` from `dev` (`docs/DEVELOPMENT_STANDARDS.md` §2.2). |
| 20261006 | Spanner | The issue counts 18 tests. #150 deleted one, so 17 remain (design study F1). | The spec works from 17. The issue's count and its AC3 wording ("converted", which now also covers "deleted with the code it covered") are updated at close-out. |
| 20261006 | Spanner | Issue AC1 is repository-wide. Seven tests outside the four files also have no assertion (design study F2–F4). | In scope, as Step 4. Each one gets an assertion that the code path its name describes was actually reached, and a mutation that proves it. |
| 20261006 | Spanner | Issue AC5 asks for no reduction in the passed count. Option B deletes six tests and converts the others into parametrised cases. | AC5.1 states the exact expected count instead. It is derived in §6, so a lost test shows up as a wrong number rather than hiding inside "not fewer". |
| 20261006 | Spanner | `ClockifyAuth` imports `Fernet` and `Path` and uses neither. Its docstring says it uses Fernet for storage, and the key is read in plaintext from the environment. `docs/DEVELOPMENT_STANDARDS.md` §3.7 says API keys are Fernet-encrypted at rest, which is false. | In scope, in Step 1. With `workmain/utils/encryption.py` gone, these are the last claims that something encrypts at rest. |
| 20261006 | Spanner | Should the `cryptography==41.0.7` pin in `requirements.txt` go with the module? | No. `google-auth` requires `cryptography` (`pip show cryptography`, Required-by), so the pin still fixes the version that installs. Removing it would be a dependency-policy change, not dead-code removal. |
| 20261006 | Spanner | `load_dotenv()` at module level in `workmain/config_manager/loader.py` served only `get_with_env_override`. | Kept. Its effect is process-wide, and `workmain/ai/provider_manager.py` imports this module at top level. Whether to delete it is #176's review. Only `import os` goes, because it becomes unused. |
| 20261006 | Spanner | A one-time scan proves AC1 and AC2 on the day they are checked. It does not stop the next test that returns a value. | Step 5 sets `filterwarnings = ["error::pytest.PytestReturnNotNoneWarning"]` in `pyproject.toml`, so such a test fails the suite. This guards the property AC2 names at its source, it is one line, and it adds no register. |
| 20261006 | Anvil | M20's row gives its old text as prose. `if report is None:` / `return` occurs twice in `workmain/database/repositories/reports_repo.py` (`:263` and `:285`), so it isn't a literal that matches once. Anvil ran it with the following `report.corrected_content = edited_body` line as context. | Accepted. This is the spec defect Caliper's re-review found in M15, left unfixed in M20. Anvil applied the mutation inside `apply_correction`, as the row states, and it failed as expected. |
| 20261006 | Ray | Is the spec approved for implementation? | Approved, after Caliper's re-review and the M15 literal correction. |
| 20261006 | Caliper 1 | M14 fails `test_get_active_none` only because the live database happens to hold a client. On an empty database the mutation would pass. | Accepted. The test creates `_NAME_A` before `clear_active()`, so a non-active row always exists. M14 was re-run and observed failing. |
| 20261006 | Caliper 2 | `test_clear_active_no_active` never establishes that nothing was active before the call its name is about. Its new assertions would hold even if that call did nothing. M15 also fails the original test, so it can't tell the strengthened test from the unstrengthened one. | Accepted. The test seeds `create` → `set_active` → `clear_active` and asserts nothing is active before the call under test. M15 is now "the `is_active` update in `clear_active` removed": the original test passes under it and the strengthened one fails. Both were observed. |
| 20261006 | Caliper 3 | The replacement §3.7 text says "`.env` is `chmod 600`". The live `.env` is `700`. It also restates the "All secrets are stored as KV pairs in the .env" bullet above it. | Accepted. The bullet is written as a rule, "Nothing encrypts secrets at rest; `.env` must be `chmod 600`." Ray was told the live file was `700`, and has since set it to `600`. |
| 20261006 | Caliper 4 | `test_shipped_config_loads` reads the private `_all_configs`. The public `get_all_provider_configs()` (`workmain/ai/provider_manager.py:124`) returns the same dict. | Accepted. M19 was re-run against the public accessor and still fails. |
| 20261006 | Caliper re-review | M15 is the only mutation row written as prose. The proposed literal was the three-line `update(...)` statement. | Accepted, with a correction: those three lines occur twice in `workmain/database/repositories/client_repository.py`, because `set_active` opens with the same statement. The row's literal includes the `delete('active_client_id')` line that follows, which occurs once. |
| 20261006 | Spanner | When mutations were run during drafting, two of them (M2 and M11a) ran against stale bytecode. Each was applied within a second of the previous mutation and left the file the same byte size, so Python reused the previous mutation's `.pyc`. | DR5. Every mutation run sets `PYTHONPYCACHEPREFIX` to a fresh directory. |

---

## 1. Scope

**In scope:**

- **Dead code with no application caller, deleted** (design study F6):
  - `workmain/utils/encryption.py`
  - `workmain/config_manager/validator.py`
  - `ConfigLoader.get_database_config` and `ConfigLoader.get_with_env_override`
  - `DatabaseConnection.test_connection` and `DatabaseConnection.get_table_count`
  - `TagSystem.get_tags_for_report`
  - `TemplateLoader.get_sections`
- **The unused `Fernet` and `Path` imports in `workmain/integrations/clockify/auth.py`**, and its false docstring line.
- **The package docstrings** of `workmain/utils/__init__.py` and `workmain/config_manager/__init__.py`, which name the deleted modules.
- **`docs/DEVELOPMENT_STANDARDS.md` §3.3 and §3.7**, which cite encryption.
- **Tests:**
  - `tests/test_config_system.py` and `tests/test_db_connection.py`, deleted.
  - `tests/test_tag_system.py` and `tests/test_templates.py`, rewritten.
  - Seven tests in `tests/test_client_repository.py`, `tests/test_delivery.py`, `tests/test_provider_foundation.py` and `tests/test_report_correction.py`, strengthened.
- **`pyproject.toml`:** one `filterwarnings` entry.

**Out of scope:**

- **`requirements.txt`.** The `cryptography` pin stays (Decision Log).
- **`~/.workmain/encryption.key` and `load_dotenv()` in `workmain/config_manager/loader.py`.** Both are reviewed for deletion by #176, which is blocked by this issue.
- **The other repository filters that select report content by literal tag name** (`workmain/database/repositories/meetings_repo.py:396`, `:422`). They are live and are not touched.
- **`monthly_executive.json` reusing the weekly subject line.** That is template content, not a test defect.
- **#136.** The `unittest.TestCase` fixture problem is a separate issue.
- **Any test not named in §4.**

## 2. Verified current state

Verified on `dev` `44bada1`, 20261006.

| Claim | Evidence (file:line, symbol) |
| --- | --- |
| The 17 tests have no assertion and return a value. | `tests/test_tag_system.py:30`, `:62`, `:91`, `:119`, `:147`, `:175`, `:214`, `:249`, `:278`; `tests/test_templates.py:35`, `:72`, `:111`, `:163`; `tests/test_config_system.py:22`, `:48`, `:88`; `tests/test_db_connection.py:20` |
| The seven other assertionless tests are: | `tests/test_client_repository.py:80` `TestClientRepositoryActiveContext.test_get_active_none`, `:143` `.test_clear_active_no_active`; `tests/test_delivery.py:90` `TestDeliverWslNotify.test_subprocess_failure_does_not_raise`, `:127` `TestDeliverSlack.test_no_daemon_logs_warning_no_crash`, `:142` `.test_daemon_post_message_failure_does_not_raise`; `tests/test_provider_foundation.py:975` `test_shipped_config_loads`; `tests/test_report_correction.py:602` `TestApplyCorrection.test_unknown_report_id_is_a_no_op` |
| Nothing outside the two modules imports `workmain/utils/encryption.py` or `workmain/config_manager/validator.py`, in `workmain/`, `scripts/` or `tests/`, apart from `tests/test_config_system.py`. | grep, design study F6a, F6b |
| `get_database_config` has no caller. `get_with_env_override` is called only by it. After both go, `os` is unused in that module. | `workmain/config_manager/loader.py:5`, `:139-171`, `:208-232` |
| `test_connection` and `get_table_count` have no caller. After both go, `text` is unused in that module. | `workmain/database/connection.py:6`, `:84-121`, `:123-135` |
| `get_tags_for_report` has no caller. | `workmain/utils/tag_utils.py:340-357` |
| `get_sections` has no caller. | `workmain/templates_engine/loader.py:184-195` |
| `ClockifyAuth` imports `Fernet` and `Path`, uses neither, and its class docstring says "Uses Fernet encryption for secure storage." | `workmain/integrations/clockify/auth.py:7-8`, `:16` |
| §3.3's singleton table lists `get_encryption()`. §3.7 says API keys are "Fernet-encrypted at rest" and names `~/.workmain/encryption.key`. | `docs/DEVELOPMENT_STANDARDS.md:344`, `:378-379` |
| `workmain/utils/__init__.py`'s docstring names "encryption". `workmain/config_manager/__init__.py`'s says "loading, validation and alias resolution". | both files, lines 1-6 |
| `_load_config` returns without reading anything when the config path does not exist. | `workmain/ai/provider_manager.py:367-368` |
| `apply_correction` returns before any write when the report id is unknown. | `workmain/database/repositories/reports_repo.py:262-264` |
| `_deliver_wsl_notify` returns early when `NOTIFY_CMD` is `None`, and logs `OS notification failed` when the subprocess raises. `_deliver_slack` logs `no daemon handle` when it has no daemon. | `workmain/daemon/delivery.py:106-112`, `:130-131`, `:135-137` |
| `pyproject.toml` `[tool.pytest.ini_options]` holds only `testpaths`. pytest is 7.4.3. | `pyproject.toml`; `pip show pytest` |
| Bare `pytest` gives `1128 passed, 0 failed, 0 skipped` and 17 `PytestReturnNotNoneWarning` lines, one for each of the 17 tests. `pytest automation/` gives `51 passed, 0 failed, 0 skipped`. | run on `origin/main` `0c126ec`, 20261006. The tests are the same as on `dev` `44bada1`. |

## 3. Design rules

- **DR1 — A test asserts the behaviour its name states, and its name or docstring states it.** A name like "test conversion" is replaced by one that says what conversion does.
- **DR2 — Tests over shipped templates derive the set from `TemplateLoader.list_templates()`.** Never a hand-written list of names, and never literal section names (design study F9, F10).
- **DR3 — Substitution is asserted on a template the test builds,** with exact expected strings.
- **DR4 — A "must not raise" test also asserts that the path its name describes was reached:** the failing call was made, or the warning was logged. It must not be able to pass because the code returned early.
- **DR5 — A mutation is observed, never reasoned about.** Run each one from §4 Step 6's table:
  - Apply it to a clean file.
  - Run its test with `PYTHONPYCACHEPREFIX` set to a fresh directory, so no `.pyc` from an earlier mutation is reused.
  - Record the failing assertion.
  - Restore the file with `git checkout -- <file>`.
  - Confirm `git status --short workmain/` is empty before the next mutation.
  - A mutation that fails for a reason other than its expected failure is a stop under `CLAUDE.md` Role 3.
- **DR6 — Nothing under `workmain/` changes except the deletions and the import and docstring edits in Step 1.**

Anything this spec does not cover stops at `CLAUDE.md` Role 3.

## 4. Steps

| Step | Deliverable | Files |
| --- | --- | --- |
| 1 | Dead code and its tests removed; encryption claims corrected | `workmain/utils/encryption.py`, `workmain/config_manager/validator.py`, `workmain/config_manager/loader.py`, `workmain/database/connection.py`, `workmain/utils/tag_utils.py`, `workmain/templates_engine/loader.py`, `workmain/integrations/clockify/auth.py`, `workmain/utils/__init__.py`, `workmain/config_manager/__init__.py`, `tests/test_config_system.py`, `tests/test_db_connection.py`, `tests/test_tag_system.py`, `tests/test_templates.py`, `docs/DEVELOPMENT_STANDARDS.md` |
| 2 | Tag tests rewritten | `tests/test_tag_system.py` |
| 3 | Template tests rewritten | `tests/test_templates.py` |
| 4 | Seven other tests assert what their names claim | `tests/test_client_repository.py`, `tests/test_delivery.py`, `tests/test_provider_foundation.py`, `tests/test_report_correction.py` |
| 5 | A test that returns a value fails the suite | `pyproject.toml` |
| 6 | Mutation runs, verification, results artifact | `docs/dev/results/ASSERTIONLESS_TESTS_RESULTS.md` |

### Step 1 — Remove the dead code

1. `git rm workmain/utils/encryption.py workmain/config_manager/validator.py tests/test_config_system.py tests/test_db_connection.py`.
2. `workmain/config_manager/loader.py`: delete `get_with_env_override` (`:139-171`) and `get_database_config` (`:208-232`), and delete `import os` (`:5`). `load_dotenv` stays.
3. `workmain/database/connection.py`: delete `test_connection` (`:84-121`) and `get_table_count` (`:123-135`). Change `:6` to `from sqlalchemy import create_engine`.
4. `workmain/utils/tag_utils.py`: delete `get_tags_for_report` (`:340-357`).
5. `workmain/templates_engine/loader.py`: delete `get_sections` (`:184-195`).
6. `workmain/integrations/clockify/auth.py`: delete `:7` `from cryptography.fernet import Fernet`, `:8` `from pathlib import Path`, and `:16` `    Uses Fernet encryption for secure storage.`
7. `workmain/utils/__init__.py`: `date, duration, editor, encryption and similar` becomes `date, duration, editor and similar`.
8. `workmain/config_manager/__init__.py`: the docstring becomes:

   ```text
   Package marker for template and alias configuration management.

   Holds no code of its own; configuration loading and alias resolution live in
   their own modules under this package.
   ```

9. `tests/test_tag_system.py`: delete `test_report_filtering` (`:249-275`). `tests/test_templates.py`: delete `test_section_structure` (`:163-210`). Steps 2 and 3 replace both files whole; these deletions keep this step's commit green.
10. `docs/DEVELOPMENT_STANDARDS.md`:
    - §3.3: delete the row `` | `get_encryption()` | `get_encryptor()` | ``.
    - §3.7: replace these two bullets

      ```text
      - API keys come from the environment and are Fernet-encrypted at rest.
      - `.env` and `~/.workmain/encryption.key` are `chmod 600`.
      ```

      with

      ```text
      - Nothing encrypts secrets at rest; `.env` must be `chmod 600`.
      ```

### Step 2 — `tests/test_tag_system.py`

Replace the file with:

```python
"""
Tag parsing, validation, conversion, normalisation and display tests.

Runs against the shipped config/tags.json, whose vocabulary is a fixed design
decision.
"""

import pytest

from workmain.utils.tag_utils import TagSystem, format_tags, get_valid_tags, parse_tags


@pytest.fixture
def ts():
    return TagSystem()


class TestTagSystem:
    """TagSystem's individual pipeline stages."""

    @pytest.mark.parametrize('text, expected_clean, expected_tags', [
        ("Fixed bug #ilo", "Fixed bug", ["ilo"]),
        ("Deployed #both #cf", "Deployed", ["both", "cf"]),
        ("Meeting notes #ILO #CF", "Meeting notes", ["ilo", "cf"]),
        ("No tags here", "No tags here", []),
        ("Multiple   spaces  #ilo", "Multiple spaces", ["ilo"]),
        ("#ilo at start", "at start", ["ilo"]),
        ("at end #ilo", "at end", ["ilo"]),
        ("#ilo #cr #ifo multiple tags", "multiple tags", ["ilo", "cr", "ifo"]),
    ])
    def test_extract_tags_strips_hashtags_and_lowercases_them(
        self, ts, text, expected_clean, expected_tags
    ):
        """extract_tags() returns the text with hashtags and extra whitespace removed, and the hashtags lowercased in order of appearance."""
        assert ts.extract_tags(text) == (expected_clean, expected_tags)

    @pytest.mark.parametrize('tags, expected_valid, expected_invalid', [
        (["ilo", "cf"], ["ilo", "cf"], []),
        (["ilo", "typo"], ["ilo"], ["typo"]),
        (["invalid"], [], ["invalid"]),
        (["ilo", "cr", "both"], ["ilo", "cr", "both"], []),
        (["ILO", "CR"], ["ilo", "cr"], []),
    ])
    def test_validate_tags_splits_known_from_unknown_case_insensitively(
        self, ts, tags, expected_valid, expected_invalid
    ):
        """validate_tags() returns the configured shortcuts, lowercased, and the unknown ones as given."""
        assert ts.validate_tags(tags) == (expected_valid, expected_invalid)

    @pytest.mark.parametrize('shorts, expected_full', [
        (["ilo"], ["internal-only"]),
        (["cr"], ["client-report"]),
        (["both", "cf"], ["both", "carry-forward"]),
        (["ilo", "cr", "blk"], ["internal-only", "client-report", "blocker"]),
    ])
    def test_convert_to_full_names_maps_each_shortcut_in_order(self, ts, shorts, expected_full):
        """convert_to_full_names() maps each shortcut to its full name, keeping input order."""
        assert ts.convert_to_full_names(shorts) == expected_full

    @pytest.mark.parametrize('tags, expected', [
        (["internal-only", "carry-forward"], ["carry-forward", "internal-only"]),
        (["blocker", "both", "internal-only"], ["blocker", "both", "internal-only"]),
        (["internal-only", "internal-only", "both"], ["both", "internal-only"]),
        (["client-report"], ["client-report"]),
    ])
    def test_normalize_tags_deduplicates_and_sorts(self, ts, tags, expected):
        """normalize_tags() drops duplicate full names and sorts the rest alphabetically."""
        assert ts.normalize_tags(tags) == expected

    @pytest.mark.parametrize('tags, expected', [
        (["internal-only"], "[internal-only]"),
        (["carry-forward", "internal-only"], "[carry-forward] [internal-only]"),
        (["blocker", "both", "internal-only"], "[blocker] [both] [internal-only]"),
        ([], ""),
    ])
    def test_format_display_brackets_each_tag_space_separated(self, ts, tags, expected):
        """format_display() wraps each tag in brackets and joins them with a space; no tags gives an empty string."""
        assert ts.format_display(tags) == expected

    @pytest.mark.parametrize('text, apply_default, expected', [
        ("Fixed a bug", True, ("Fixed a bug", ["internal-only"], [])),
        ("Fixed a bug #both", True, ("Fixed a bug", ["both"], [])),
        ("Fixed a bug", False, ("Fixed a bug", [], [])),
    ])
    def test_default_tag_applies_only_when_text_has_no_tags_and_default_requested(
        self, ts, text, apply_default, expected
    ):
        """process_tags() adds internal-only only when the text carries no tag and apply_default is true."""
        assert ts.process_tags(text, apply_default=apply_default) == expected


class TestModuleFunctions:
    """The module-level convenience functions over the shared TagSystem."""

    @pytest.mark.parametrize('text, expected', [
        ("Fixed login bug #ilo", ("Fixed login bug", ["internal-only"], [])),
        ("Deployed patch #both #cf", ("Deployed patch", ["both", "carry-forward"], [])),
        ("Database migration blocked #blk", ("Database migration blocked", ["blocker"], [])),
        ("Meeting notes #ilo #cr", ("Meeting notes", ["client-report", "internal-only"], [])),
        ("Task with typo #ilo #typo", ("Task with typo", ["internal-only"], ["typo"])),
        ("No tags provided", ("No tags provided", ["internal-only"], [])),
        ("#both multiple #cf #both tags", ("multiple tags", ["both", "carry-forward"], [])),
    ])
    def test_parse_tags_returns_clean_text_normalised_full_names_and_unknowns(self, text, expected):
        """parse_tags() runs the whole pipeline: clean text, deduplicated and sorted full names, unknown shortcuts."""
        assert parse_tags(text, apply_default=True) == expected

    def test_format_tags_keeps_caller_order(self):
        """format_tags() formats full names in the order given, without re-sorting."""
        assert format_tags(["internal-only", "carry-forward"]) == "[internal-only] [carry-forward]"

    def test_get_valid_tags_lists_every_shortcut_sorted(self):
        """get_valid_tags() returns every configured shortcut, sorted."""
        assert get_valid_tags() == ["blk", "both", "cf", "cr", "ifo", "ilo"]
```

### Step 3 — `tests/test_templates.py`

Replace the file with:

```python
"""
Report template loading, validation and variable substitution tests.

Loading and validation run over every template shipped in templates/reports/;
substitution runs on a template the test builds, so shipped content does not
decide the result.
"""

from datetime import date

import pytest

from workmain.templates_engine import TemplateLoader, validate_template


@pytest.fixture
def loader():
    return TemplateLoader()


class TestShippedTemplates:
    """Every template under templates/reports/."""

    def test_every_shipped_template_loads_with_its_required_fields(self, loader):
        """load() returns each listed template with name, sections and output_format."""
        names = loader.list_templates()
        assert names
        for name in names:
            template = loader.load(name)
            assert {'name', 'sections', 'output_format'} <= template.keys(), name

    def test_every_shipped_template_passes_validation(self, loader):
        """validate_template() reports no error for any listed template."""
        for name in loader.list_templates():
            assert validate_template(loader.load(name)) == [], name


class TestTemplateValidation:
    """validate_template() on templates the test builds."""

    def test_missing_required_field_is_reported(self):
        """A template without a version is reported as missing that field."""
        template = {'name': 'x', 'description': 'x', 'sections': []}
        assert validate_template(template) == ['Missing required field: version']

    def test_section_missing_required_field_is_reported(self):
        """A section without a title is reported against that section."""
        template = {
            'name': 'x', 'description': 'x', 'version': '1',
            'sections': [{'name': 's', 'required': True}],
        }
        assert validate_template(template) == ['Section 0 (s): Missing required field: title']


class TestVariableSubstitution:
    """build_variables() and substitute_variables()."""

    def test_build_variables_formats_the_report_date(self, loader):
        """build_variables() derives every date field from the report date, with the week starting Monday."""
        variables = loader.build_variables(
            report_date=date(2025, 12, 24),
            user_full_name='Tom Kitten',
            recipients=['Benjamin', 'Bunny', 'Flopsy'],
        )
        assert variables == {
            'user_full_name': 'Tom Kitten',
            'day_name': 'Wednesday',
            'date_long': 'December 24, 2025',
            'date_short': '12/24/2025',
            'date_iso': '2025-12-24',
            'week_of': 'Week of December 22, 2025',
            'recipients': 'Benjamin, Bunny, Flopsy',
        }

    def test_substitute_variables_replaces_every_placeholder_in_subject_line(self, loader):
        """substitute_variables() fills each {name} in subject_line and leaves the input template unchanged."""
        template = {'subject_line': '{day_name}, {date_long} – {user_full_name}'}
        variables = {'day_name': 'Wednesday', 'date_long': 'December 24, 2025', 'user_full_name': 'Tom Kitten'}
        result = loader.substitute_variables(template, variables)
        assert result['subject_line'] == 'Wednesday, December 24, 2025 – Tom Kitten'
        assert template['subject_line'] == '{day_name}, {date_long} – {user_full_name}'
```

### Step 4 — The seven other tests

Each test keeps its name, its class and its position. The replacements are below. Add any import a body needs to its file, following `docs/DEVELOPMENT_STANDARDS.md` §3.2: `json` and `logging` from the standard library, `SystemStateRepository` where it is not imported already.

`tests/test_client_repository.py` `TestClientRepositoryActiveContext`:

```python
    def test_get_active_none(self, db_session):
        """get_active() returns None when no client has is_active=True."""
        repo = ClientRepository(db_session)
        repo.create(_NAME_A)
        repo.clear_active()
        assert repo.get_active() is None

    def test_clear_active_no_active(self, db_session):
        """clear_active() does not raise when nothing is active, and leaves nothing active."""
        repo = ClientRepository(db_session)
        state_repo = SystemStateRepository(db_session)
        client = repo.create(_NAME_A)
        repo.set_active(client.id)
        repo.clear_active()
        assert repo.get_active() is None
        assert state_repo.get('active_client_id') is None
        repo.clear_active()
        assert repo.get_active() is None
        assert state_repo.get('active_client_id') is None
```

`tests/test_delivery.py` `TestDeliverWslNotify`:

```python
    def test_subprocess_failure_does_not_raise(self, caplog):
        import subprocess as real_subprocess
        with patch.object(delivery, 'NOTIFY_CMD', '/usr/bin/wsl-notify-send'), \
             patch.object(delivery.subprocess, 'run',
                           side_effect=real_subprocess.TimeoutExpired(cmd='x', timeout=5)) as mock_run, \
             caplog.at_level(logging.ERROR, logger=delivery.logger.name):
            delivery._deliver_wsl_notify('Title', 'Body')  # must not raise
        mock_run.assert_called_once()
        assert 'OS notification failed' in caplog.text
```

`tests/test_delivery.py` `TestDeliverSlack`:

```python
    def test_no_daemon_logs_warning_no_crash(self, caplog):
        with caplog.at_level(logging.WARNING, logger=delivery.logger.name):
            delivery._deliver_slack('Title', 'Body', None)  # must not raise
        assert 'no daemon handle' in caplog.text
```

```python
    def test_daemon_post_message_failure_does_not_raise(self):
        daemon = MagicMock()
        daemon.post_message.return_value = None  # simulates a failed/unreachable post
        delivery._deliver_slack('Title', 'Body', daemon)  # must not raise
        daemon.post_message.assert_called_once()
```

`tests/test_provider_foundation.py`:

```python
def test_shipped_config_loads():
    """The shipped config meets the schema it ships with."""
    config = Path(__file__).parent.parent / 'config' / 'ai_settings.json'
    manager = ProviderManager(config_path=str(config))
    assert set(manager.get_all_provider_configs()) == set(json.loads(config.read_text())['providers'])
```

`tests/test_report_correction.py` `TestApplyCorrection`:

```python
    def test_unknown_report_id_is_a_no_op(self, db_session):
        repo = get_reports_repository(db_session)
        with patch.object(db_session, 'commit') as commit:
            repo.apply_correction(999999999, 'Edited body.')  # must not raise
        commit.assert_not_called()
```

### Step 5 — `pyproject.toml`

Add under `[tool.pytest.ini_options]`, after `testpaths`:

```toml
filterwarnings = ["error::pytest.PytestReturnNotNoneWarning"]
```

### Step 6 — Mutation runs, verification and results artifact

Run every mutation under DR5. Leading spaces inside a code span are part of the text to match, and each old text occurs exactly once in its file. Each expected failure was observed on 20261006, with the tests drafted exactly as in Steps 2–4. The original test passed under every mutation.

| M | File | Change (old → new) | Test that must fail | Expected failure |
| --- | --- | --- | --- | --- |
| M1 | `workmain/utils/tag_utils.py` | `tags = [tag.lower() for tag in tags]` → `tags = [tag for tag in tags]` | `test_extract_tags_strips_hashtags_and_lowercases_them` | `['ILO', 'CF'] != ['ilo', 'cf']` |
| M2 | same | `if tag.lower() in self.tag_mappings:` → `if tag in self.tag_mappings:` | `test_validate_tags_splits_known_from_unknown_case_insensitively` | `([], ['ILO', 'CR']) == (['ilo', 'cr'], [])` |
| M3 | same | `full_names.append(self.tag_mappings[tag_lower]["full_name"])` → `full_names.append(tag_lower)` | `test_convert_to_full_names_maps_each_shortcut_in_order` | `['ilo'] == ['internal-only']` |
| M4a | same | `            unique_tags.sort()` → `            pass` | `test_normalize_tags_deduplicates_and_sorts` | `'internal-only' != 'carry-forward'` at index 0 |
| M4b | same | `seen.add(tag)` → `pass` | `test_normalize_tags_deduplicates_and_sorts` | left contains one more item, `'internal-only'` |
| M5 | same | `formatted = [f"[{tag}]" for tag in tags]` → `formatted = tags` | `test_format_display_brackets_each_tag_space_separated` | `'internal-only' == '[internal-only]'` |
| M6 | same | `            return [self.default_tag]` → `            return tags` | `test_default_tag_applies_only_when_text_has_no_tags_and_default_requested` | `[] != ['internal-only']` |
| M7 | same | `normalized_tags = self.normalize_tags(full_tags)` → `normalized_tags = full_tags` | `test_parse_tags_returns_clean_text_normalised_full_names_and_unknowns` | `['internal-only', 'client-report'] != ['client-report', 'internal-only']` |
| M8 | same | `    return ts.format_display(tags)` → `    return ts.format_display(sorted(tags))` | `test_format_tags_keeps_caller_order` | `'[carry-forward] [internal-only]' == '[internal-only] [carry-forward]'` |
| M9 | same | `return sorted(self.tag_mappings.keys())` → `return list(self.tag_mappings.keys())` | `test_get_valid_tags_lists_every_shortcut_sorted` | `'ilo' != 'blk'` at index 0 |
| M10 | `workmain/templates_engine/loader.py` | `f"{template_name}.json"` → `f"{template_name}.yaml"` in `load` | `test_every_shipped_template_loads_with_its_required_fields` | `FileNotFoundError: Template 'daily_internal' not found` |
| M11a | `workmain/templates_engine/validator.py` | `required_fields = ["name", "description", "version", "sections"]` → append `"owner"` | `test_every_shipped_template_passes_validation` | `AssertionError: daily_internal`, `['Missing required field: owner'] == []` |
| M11b | same | the same list → `["name", "description", "sections"]` | `test_missing_required_field_is_reported` | `[] == ['Missing required field: version']` |
| M11c | same | `required_fields = ["name", "title", "required"]` → `["name", "required"]` | `test_section_missing_required_field_is_reported` | `[] == ['Section 0 (s): Missing required field: title']` |
| M12 | `workmain/templates_engine/loader.py` | `week_start = report_date - timedelta(days=report_date.weekday())` → `week_start = report_date` | `test_build_variables_formats_the_report_date` | dict mismatch on `week_of` |
| M13a | same | `subject = subject.replace(f"{{{var_name}}}", str(var_value))` → `pass` | `test_substitute_variables_replaces_every_placeholder_in_subject_line` | `'{day_name}, ...' == 'Wednesday, ...'` |
| M13b | same | `template_copy = copy.deepcopy(template)` → `template_copy = template` | `test_substitute_variables_replaces_every_placeholder_in_subject_line` | the input template's `subject_line` was substituted |
| M14 | `workmain/database/repositories/client_repository.py` | `return self.session.query(Client).filter(Client.is_active == True).first()` → `return self.session.query(Client).first()` | `test_get_active_none` | `assert <Client …> is None` |
| M15 | same | `        self.session.query(Client).filter(Client.is_active == True).update(` / `            {Client.is_active: False}, synchronize_session='fetch'` / `        )` / `        SystemStateRepository(self.session).delete('active_client_id')` → `        SystemStateRepository(self.session).delete('active_client_id')`. The first three lines alone also open `set_active`, and the `delete` line is what makes the match unique. | `test_clear_active_no_active` | `assert <Client …> is None` on the first precondition assertion |
| M16 | `workmain/daemon/delivery.py` | `    if NOTIFY_CMD is None:` → `    if True:` | `test_subprocess_failure_does_not_raise` | `Expected 'run' to have been called once. Called 0 times.` |
| M17 | same | `        logger.warning("Slack delivery requested but no daemon handle provided")` → `        pass` | `test_no_daemon_logs_warning_no_crash` | `assert 'no daemon handle' in ''` |
| M18 | same | `    daemon.post_message(text)` → `    pass` | `test_daemon_post_message_failure_does_not_raise` | `Expected 'post_message' to have been called once. Called 0 times.` |
| M19 | `workmain/ai/provider_manager.py` | `        if not Path(config_file).exists():` → `        if True:` | `test_shipped_config_loads` | `set() == {'claude', 'gemini', 'ollama'}` |
| M20 | `workmain/database/repositories/reports_repo.py` | in `apply_correction`, `if report is None:` / `return` → `if report is None:` / `self.session.commit()` / `return` | `test_unknown_report_id_is_a_no_op` | `Expected 'commit' to not have been called. Called 1 times.` |

Then run the §5 checks and write `docs/dev/results/ASSERTIONLESS_TESTS_RESULTS.md` from `docs/dev/results/_TEMPLATE_RESULTS.md`. Its §3 holds only the AC table. Put the mutation results and the AC1.1 script output in §5.

### Authorization points

None. No migration, no GitHub object deletion and no force-push. The merge to `main` and the restart belong to `/closeout`.

## 5. Acceptance criteria

| AC | Criterion | How it is checked |
| --- | --- | --- |
| AC1.1 | Every test function under `tests/` contains an assertion: an `assert` statement, an `assert*` mock call, or `pytest.fail`, `pytest.raises` or `pytest.warns`. | The scan below prints nothing. It printed 24 lines on `dev` `44bada1`. |
| AC1.2 | Each of the seven tests Step 4 changes fails when the path its name describes is not taken. | M14–M20, each observed under DR5 and recorded in the results artifact. |
| AC2.1 | No test signals its result by returning a value. | The warning count below prints `0`. It printed `17` on `dev` `44bada1`. |
| AC2.2 | A test that returns a value fails the application suite. | The guard check below reports `1 failed`. Without Step 5 it reports `1 passed, 1 warning`. |
| AC3.1 | Each converted tag and template test fails when the behaviour its name states is broken. | M1–M13b, each observed under DR5 and recorded in the results artifact. |
| AC3.2 | Code whose only consumer was one of the 17 tests is gone, along with those tests. | The dead-code check below returns zero hits and lists no file. |
| AC3.3 | `docs/DEVELOPMENT_STANDARDS.md` no longer claims that anything encrypts secrets at rest, and no longer cites the encryption module. | Ray reads §3.3 and §3.7. |
| AC4.1 | Each test in Steps 2 and 3 states in its name or docstring what it asserts. | Ray reads `tests/test_tag_system.py` and `tests/test_templates.py` for whether each docstring says what passing proves. |
| AC5.1 | The application suite is green and lost no test. | A bare `pytest` reports exactly 26 more passed than the start-of-branch count recorded in the results artifact, with 0 failed and 0 skipped. The +26 is derived in §6. |
| AC5.2 | The automation suite is unaffected. | `pytest automation/` reports the start-of-branch count, with 0 failed and 0 skipped. |

AC1.1 scan:

```bash
python3 - <<'EOF'
import ast, pathlib
def checks(fn):
    for n in ast.walk(fn):
        if isinstance(n, ast.Assert):
            return True
        if isinstance(n, ast.Call):
            f = n.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, 'id', '')
            if name.startswith('assert') or name in ('fail', 'raises', 'warns'):
                return True
    return False
for p in sorted(pathlib.Path('tests').rglob('*.py')):
    for node in ast.walk(ast.parse(p.read_text())):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test') and not checks(node):
            print(f'{p}:{node.lineno} {node.name}')
EOF
```

AC2.1 warning count:

```bash
pytest -q -p no:cacheprovider 2>&1 | grep -c PytestReturnNotNoneWarning
```

AC2.2 guard check. `$SCRATCH` is any directory outside `tests/`:

```bash
printf 'def test_returns():\n    return True\n' > "$SCRATCH/test_returns.py"
pytest -q -p no:cacheprovider -c pyproject.toml "$SCRATCH/test_returns.py"
```

AC3.2 dead-code check:

```bash
grep -rnE 'get_database_config|get_with_env_override|get_table_count|get_tags_for_report|get_sections|utils\.encryption|EncryptionManager|get_encryption|ConfigValidator|config_manager\.validator|Fernet' workmain/ scripts/ tests/
grep -n 'def test_connection' workmain/database/connection.py
ls workmain/utils/encryption.py workmain/config_manager/validator.py tests/test_config_system.py tests/test_db_connection.py 2>&1 | grep -v 'No such file'
```

## 6. Test plan

- **Baseline before this work:** recorded in the results artifact at the start of the branch, in the form `docs/DEVELOPMENT_STANDARDS.md` §6 requires. On `origin/main` `0c126ec`, 20261006, it was `1128 passed, 0 failed, 0 skipped`.
- **Expected after:** start-of-branch passed + 26, 0 failed, 0 skipped. On the 1128 baseline that is `1154 passed, 0 failed, 0 skipped`.

  | Change | Tests |
  | --- | --- |
  | `tests/test_tag_system.py`: 9 out, 37 in (8 + 5 + 4 + 4 + 4 + 3 + 7 parametrised cases, plus 2) | +28 |
  | `tests/test_templates.py`: 4 out, 6 in | +2 |
  | `tests/test_config_system.py` deleted | −3 |
  | `tests/test_db_connection.py` deleted | −1 |
  | Step 4: the seven are changed in place | 0 |

- **Per step:** after each of Steps 1–5, a bare `pytest` reports 0 failed and 0 skipped. After Step 5 it also reports no `PytestReturnNotNoneWarning`.

## 7. Risks and rollback

- **A deleted function turns out to be used dynamically,** for example through `getattr` or a CLI string. The grep in design study F6 found no such use. If one appears, the import or attribute error names it at once. Revert the Step 1 commit.
- **`filterwarnings` promotes only `PytestReturnNotNoneWarning`.** No other warning becomes an error, and the other warnings bare `pytest` emits today are unaffected. Revert by removing the line.
- **`~/.workmain/encryption.key` stays on disk,** with nothing to read it. It is `chmod 600` and outside the repository. No step touches it, and #176 decides what happens to it.
- **Rollback:** each step is its own commit, and `git revert` of any one leaves the others standing. Step 1 is the only step that touches `workmain/`.
