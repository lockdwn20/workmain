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
