"""
WorkmAIn Template Validator
Template Validator v1.0
20251224

Validates JSON template structure against schema requirements.
Ensures templates have all required fields and proper data types.
"""

from typing import Dict, Any, List, Optional, Set


class TemplateValidationError(Exception):
    """Raised when template validation fails."""
    pass


class TemplateValidator:
    """
    Validate report template structure.
    
    Ensures templates contain:
    - All required fields
    - Correct data types
    - Valid section configurations
    - Valid AI provider references
    - Valid tag filters
    - Valid output formats
    """
    
    # Valid output formats
    VALID_OUTPUT_FORMATS = {'markdown', 'html', 'text'}
    
    # Valid AI providers
    VALID_AI_PROVIDERS = {'claude', 'gemini'}
    
    # Valid section formats
    VALID_SECTION_FORMATS = {'bullets', 'prose', 'time_summary', 'numbered_list'}
    
    # Valid data sources
    VALID_DATA_SOURCES = {'notes', 'time_entries', 'meetings', 'projects', 'clockify'}
    
    # Valid tags (from our tag system)
    VALID_TAGS = {
        'internal-only', 'client-report', 'info-only', 
        'both', 'carry-forward', 'blocker'
    }
    
    def __init__(self):
        """Initialize template validator."""
        pass
    
    def validate(self, template: Dict[str, Any]) -> List[str]:
        """
        Validate a template against schema requirements.
        
        Args:
            template: Template dictionary to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate top-level structure
        errors.extend(self._validate_top_level(template))
        
        # Validate sections
        if 'sections' in template:
            errors.extend(self._validate_sections(template['sections']))
        
        # Validate output format
        if 'output_format' in template:
            errors.extend(self._validate_output_format(template['output_format']))
        
        # Validate AI provider
        if 'ai_provider_default' in template:
            errors.extend(self._validate_ai_provider(template['ai_provider_default']))
        
        # Validate subject line variables
        if 'subject_line' in template:
            errors.extend(self._validate_subject_line(template['subject_line']))
        
        return errors
    
    def _validate_top_level(self, template: Dict[str, Any]) -> List[str]:
        """Validate top-level template fields."""
        errors = []
        
        # Required fields
        required = ['name', 'sections', 'output_format']
        
        for field in required:
            if field not in template:
                errors.append(f"Missing required field: '{field}'")
        
        # Type checks
        if 'name' in template and not isinstance(template['name'], str):
            errors.append("Field 'name' must be a string")
        
        if 'sections' in template and not isinstance(template['sections'], list):
            errors.append("Field 'sections' must be a list")
        
        if 'output_format' in template and not isinstance(template['output_format'], str):
            errors.append("Field 'output_format' must be a string")
        
        # Optional fields type checks
        if 'description' in template and not isinstance(template['description'], str):
            errors.append("Field 'description' must be a string")
        
        if 'version' in template and not isinstance(template['version'], str):
            errors.append("Field 'version' must be a string")
        
        if 'template_type' in template and not isinstance(template['template_type'], str):
            errors.append("Field 'template_type' must be a string")
        
        return errors
    
    def _validate_sections(self, sections: List[Dict[str, Any]]) -> List[str]:
        """Validate sections array."""
        errors = []
        
        if not sections:
            errors.append("Template must have at least one section")
            return errors
        
        section_names = set()
        
        for idx, section in enumerate(sections):
            # Check if section is a dict
            if not isinstance(section, dict):
                errors.append(f"Section {idx} must be a dictionary")
                continue
            
            # Validate individual section
            section_errors = self._validate_section(section, idx)
            errors.extend(section_errors)
            
            # Check for duplicate section names
            name = section.get('name')
            if name:
                if name in section_names:
                    errors.append(f"Duplicate section name: '{name}'")
                section_names.add(name)
        
        return errors
    
    def _validate_section(self, section: Dict[str, Any], idx: int) -> List[str]:
        """Validate individual section."""
        errors = []
        prefix = f"Section {idx}"
        
        # Required fields
        required = ['name', 'title']
        
        for field in required:
            if field not in section:
                errors.append(f"{prefix}: Missing required field '{field}'")
        
        # Type checks
        if 'name' in section and not isinstance(section['name'], str):
            errors.append(f"{prefix}: Field 'name' must be a string")
        
        if 'title' in section and not isinstance(section['title'], str):
            errors.append(f"{prefix}: Field 'title' must be a string")
        
        # Validate data sources
        if 'data_sources' in section:
            if not isinstance(section['data_sources'], list):
                errors.append(f"{prefix}: Field 'data_sources' must be a list")
            else:
                for source in section['data_sources']:
                    if source not in self.VALID_DATA_SOURCES:
                        errors.append(
                            f"{prefix}: Invalid data source '{source}'. "
                            f"Must be one of: {self.VALID_DATA_SOURCES}"
                        )
        
        # Validate tag filter
        if 'tag_filter' in section:
            tag_errors = self._validate_tag_filter(section['tag_filter'], prefix)
            errors.extend(tag_errors)
        
        # Validate format
        if 'format' in section:
            fmt = section['format']
            if fmt not in self.VALID_SECTION_FORMATS:
                errors.append(
                    f"{prefix}: Invalid format '{fmt}'. "
                    f"Must be one of: {self.VALID_SECTION_FORMATS}"
                )
        
        # Validate AI provider
        if 'ai_provider' in section:
            provider = section['ai_provider']
            if provider not in self.VALID_AI_PROVIDERS:
                errors.append(
                    f"{prefix}: Invalid AI provider '{provider}'. "
                    f"Must be one of: {self.VALID_AI_PROVIDERS}"
                )
        
        # Validate required field
        if 'required' in section and not isinstance(section['required'], bool):
            errors.append(f"{prefix}: Field 'required' must be a boolean")
        
        return errors
    
    def _validate_tag_filter(self, tag_filter: Any, prefix: str) -> List[str]:
        """Validate tag filter structure."""
        errors = []
        
        if not isinstance(tag_filter, dict):
            errors.append(f"{prefix}: tag_filter must be a dictionary")
            return errors
        
        # Validate include tags
        if 'include' in tag_filter:
            if not isinstance(tag_filter['include'], list):
                errors.append(f"{prefix}: tag_filter.include must be a list")
            else:
                for tag in tag_filter['include']:
                    if tag not in self.VALID_TAGS:
                        errors.append(
                            f"{prefix}: Invalid tag '{tag}' in include filter. "
                            f"Must be one of: {self.VALID_TAGS}"
                        )
        
        # Validate exclude tags
        if 'exclude' in tag_filter:
            if not isinstance(tag_filter['exclude'], list):
                errors.append(f"{prefix}: tag_filter.exclude must be a list")
            else:
                for tag in tag_filter['exclude']:
                    if tag not in self.VALID_TAGS:
                        errors.append(
                            f"{prefix}: Invalid tag '{tag}' in exclude filter. "
                            f"Must be one of: {self.VALID_TAGS}"
                        )
        
        return errors
    
    def _validate_output_format(self, output_format: str) -> List[str]:
        """Validate output format."""
        errors = []
        
        if output_format not in self.VALID_OUTPUT_FORMATS:
            errors.append(
                f"Invalid output_format '{output_format}'. "
                f"Must be one of: {self.VALID_OUTPUT_FORMATS}"
            )
        
        return errors
    
    def _validate_ai_provider(self, provider: str) -> List[str]:
        """Validate AI provider."""
        errors = []
        
        if provider not in self.VALID_AI_PROVIDERS:
            errors.append(
                f"Invalid AI provider '{provider}'. "
                f"Must be one of: {self.VALID_AI_PROVIDERS}"
            )
        
        return errors
    
    def _validate_subject_line(self, subject_line: str) -> List[str]:
        """Validate subject line for proper variable syntax."""
        errors = []
        
        # Check for unmatched braces
        open_count = subject_line.count('{')
        close_count = subject_line.count('}')
        
        if open_count != close_count:
            errors.append("Subject line has unmatched curly braces")
        
        # Extract variable names and check if they're valid
        import re
        variables = re.findall(r'\{(\w+)\}', subject_line)
        
        valid_variables = {
            'user_full_name', 'day_name', 'date_long', 'date_short',
            'date_iso', 'week_of', 'recipients'
        }
        
        for var in variables:
            if var not in valid_variables:
                errors.append(
                    f"Unknown variable '{{{var}}}' in subject line. "
                    f"Valid variables: {valid_variables}"
                )
        
        return errors
    
    def validate_and_raise(self, template: Dict[str, Any]) -> None:
        """
        Validate template and raise exception if invalid.
        
        Args:
            template: Template to validate
            
        Raises:
            TemplateValidationError: If template is invalid
        """
        errors = self.validate(template)
        
        if errors:
            error_msg = "Template validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise TemplateValidationError(error_msg)
    
    def is_valid(self, template: Dict[str, Any]) -> bool:
        """
        Check if template is valid.
        
        Args:
            template: Template to check
            
        Returns:
            True if valid, False otherwise
        """
        errors = self.validate(template)
        return len(errors) == 0


# Global validator instance
_template_validator: Optional[TemplateValidator] = None


def get_template_validator() -> TemplateValidator:
    """
    Get global template validator instance.
    
    Returns:
        TemplateValidator instance
    """
    global _template_validator
    if _template_validator is None:
        _template_validator = TemplateValidator()
    return _template_validator


def validate_template(template: Dict[str, Any]) -> List[str]:
    """
    Convenience function to validate a template.
    
    Args:
        template: Template to validate
        
    Returns:
        List of validation errors (empty if valid)
    """
    validator = get_template_validator()
    return validator.validate(template)
