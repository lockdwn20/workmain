"""
WorkmAIn Templates Engine
Templates Engine Package v1.3
20260319

Template system for report generation.

Version History:
- v1.0: Initial package with loader, validator, field_manager, renderer
- v1.1: Added style_adapter for writing style integration
- v1.2: Fixed validator singleton name (get_template_validator) and restored full package structure
- v1.3: Added validate_template() module-level convenience function
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

__version__ = '1.3'