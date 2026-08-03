"""
Template system for report generation.
"""

from .loader import TemplateLoader, get_template_loader
from .validator import TemplateValidator, get_template_validator
from .field_manager import FieldManager
from .renderer import TemplateRenderer
from .style_adapter import StyleAdapter, get_style_adapter


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