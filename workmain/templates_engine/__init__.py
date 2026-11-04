"""
Template system for report generation.
"""

from .field_manager import FieldManager
from .loader import TemplateLoader, get_template_loader
from .renderer import TemplateRenderer
from .style_adapter import StyleAdapter, get_style_adapter
from .validator import TemplateValidator, get_template_validator


def validate_template(template):
    """Module-level convenience wrapper for TemplateValidator.validate_template()."""
    return get_template_validator().validate_template(template)


__all__ = [
    'TemplateLoader',
    'get_template_loader',
    'TemplateValidator',
    'get_template_validator',
    'validate_template',
    'FieldManager',
    'TemplateRenderer',
    'StyleAdapter',
    'get_style_adapter',
]