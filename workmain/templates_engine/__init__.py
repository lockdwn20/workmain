"""
WorkmAIn Templates Engine
Templates Engine Package v1.0
20251224

Template system for report generation.

Components:
- loader: Load and manage JSON templates
- validator: Validate template structure
- field_manager: Manage fields and data retrieval
- renderer: Render templates with data
"""

from workmain.templates_engine.loader import (
    TemplateLoader,
    get_template_loader,
)

from workmain.templates_engine.validator import (
    TemplateValidator,
    TemplateValidationError,
    get_template_validator,
    validate_template,
)

from workmain.templates_engine.field_manager import (
    FieldManager,
    get_field_manager,
)

from workmain.templates_engine.renderer import (
    TemplateRenderer,
    get_template_renderer,
    render_template,
)

__all__ = [
    # Loader
    'TemplateLoader',
    'get_template_loader',
    
    # Validator
    'TemplateValidator',
    'TemplateValidationError',
    'get_template_validator',
    'validate_template',
    
    # Field Manager
    'FieldManager',
    'get_field_manager',
    
    # Renderer
    'TemplateRenderer',
    'get_template_renderer',
    'render_template',
]

__version__ = "1.0"
