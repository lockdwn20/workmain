"""
WorkmAIn Template Validator
Template Validator v1.1
20251226

Validates templates against JSON schema and field definitions.

Version History:
- v1.0: Initial implementation with schema validation
- v1.1: Added field definitions validation for data sources, tags, and formats
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class TemplateValidator:
    """
    Validates templates against schema and field definitions.
    
    Ensures templates have required fields, valid data sources,
    valid tags, and supported formats.
    """
    
    def __init__(self, field_definitions_path: Optional[Path] = None):
        """
        Initialize validator.
        
        Args:
            field_definitions_path: Path to field_definitions.json
                                   If None, loads from templates/fields/field_definitions.json
        """
        if field_definitions_path is None:
            # Default to templates/fields/field_definitions.json
            project_root = Path(__file__).parent.parent.parent
            field_definitions_path = project_root / "templates" / "fields" / "field_definitions.json"
        
        self.field_definitions_path = Path(field_definitions_path)
        self.field_definitions = None
        
        # Load field definitions if file exists
        if self.field_definitions_path.exists():
            self.load_field_definitions()
    
    def load_field_definitions(self) -> Dict[str, Any]:
        """
        Load field definitions from JSON file.
        
        Returns:
            Field definitions dictionary
            
        Raises:
            FileNotFoundError: If field_definitions.json not found
            json.JSONDecodeError: If invalid JSON
        """
        try:
            with open(self.field_definitions_path, 'r') as f:
                self.field_definitions = json.load(f)
            return self.field_definitions
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Field definitions not found at {self.field_definitions_path}. "
                "This file is required for template validation."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in field definitions: {e}")
    
    def validate_template(self, template: Dict[str, Any]) -> List[str]:
        """
        Validate a complete template.
        
        Args:
            template: Template dictionary to validate
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Validate required fields
        required_fields = ["name", "description", "version", "sections"]
        for field in required_fields:
            if field not in template:
                errors.append(f"Missing required field: {field}")
        
        if "sections" in template:
            if not isinstance(template["sections"], list):
                errors.append("Field 'sections' must be a list")
            else:
                # Validate each section
                for i, section in enumerate(template["sections"]):
                    section_errors = self.validate_section(section)
                    for error in section_errors:
                        errors.append(f"Section {i} ({section.get('name', 'unnamed')}): {error}")
        
        # Validate version format
        if "version" in template:
            version = template["version"]
            if not isinstance(version, str):
                errors.append("Field 'version' must be a string")
        
        return errors
    
    def validate_section(self, section: Dict[str, Any]) -> List[str]:
        """
        Validate a template section.
        
        Args:
            section: Section dictionary to validate
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Validate required section fields
        required_fields = ["name", "title", "required"]
        for field in required_fields:
            if field not in section:
                errors.append(f"Missing required field: {field}")
        
        # Validate data sources if field definitions are loaded
        if self.field_definitions:
            # Check data_sources or data_source field
            if "data_sources" in section:
                data_source_errors = self.validate_data_sources(section["data_sources"])
                errors.extend(data_source_errors)
            elif "data_source" in section:
                data_source_errors = self.validate_data_sources([section["data_source"]])
                errors.extend(data_source_errors)
            
            # Validate tags
            if "include_tags" in section:
                tag_errors = self.validate_tags(section["include_tags"])
                for error in tag_errors:
                    errors.append(f"include_tags: {error}")
            
            if "exclude_tags" in section:
                tag_errors = self.validate_tags(section["exclude_tags"])
                for error in tag_errors:
                    errors.append(f"exclude_tags: {error}")
            
            # Validate format
            if "format" in section:
                format_errors = self.validate_format(section["format"])
                errors.extend(format_errors)
            
            # Validate AI provider
            if "ai_provider" in section:
                provider_errors = self.validate_ai_provider(section["ai_provider"])
                errors.extend(provider_errors)
        
        return errors
    
    def validate_data_sources(self, data_sources: List[str]) -> List[str]:
        """
        Validate data sources against field definitions.
        
        Args:
            data_sources: List of data source names
            
        Returns:
            List of error messages
        """
        if not self.field_definitions:
            return []
        
        errors = []
        valid_sources = self.field_definitions.get("data_sources", {}).keys()
        
        for source in data_sources:
            if source not in valid_sources:
                errors.append(
                    f"Invalid data source '{source}'. "
                    f"Valid sources: {', '.join(valid_sources)}"
                )
        
        return errors
    
    def validate_tags(self, tags: List[str]) -> List[str]:
        """
        Validate tags against available tags in field definitions.
        
        Args:
            tags: List of tag full names
            
        Returns:
            List of error messages
        """
        if not self.field_definitions:
            return []
        
        errors = []
        available_tags_data = self.field_definitions.get("available_tags", {})
        valid_tags = set(available_tags_data.get("tag_list_full", []))
        
        for tag in tags:
            if tag not in valid_tags:
                errors.append(
                    f"Invalid tag '{tag}'. "
                    f"Valid tags: {', '.join(sorted(valid_tags))}"
                )
        
        return errors
    
    def validate_format(self, format_name: str) -> List[str]:
        """
        Validate format against supported formats in field definitions.
        
        Args:
            format_name: Format name to validate
            
        Returns:
            List of error messages
        """
        if not self.field_definitions:
            return []
        
        errors = []
        formats_data = self.field_definitions.get("formats", {})
        valid_formats = set(formats_data.get("format_list", []))
        
        if format_name not in valid_formats:
            errors.append(
                f"Invalid format '{format_name}'. "
                f"Valid formats: {', '.join(sorted(valid_formats))}"
            )
        
        return errors
    
    def validate_ai_provider(self, provider: str) -> List[str]:
        """
        Validate AI provider against configured providers.
        
        Args:
            provider: Provider name to validate
            
        Returns:
            List of error messages
        """
        if not self.field_definitions:
            return []
        
        errors = []
        providers_data = self.field_definitions.get("ai_providers", {})
        valid_providers = set(providers_data.get("provider_list", []))
        
        if provider not in valid_providers:
            errors.append(
                f"Invalid AI provider '{provider}'. "
                f"Valid providers: {', '.join(sorted(valid_providers))}"
            )
        
        return errors
    
    def get_valid_data_sources(self) -> List[str]:
        """
        Get list of valid data sources.
        
        Returns:
            List of data source names
        """
        if not self.field_definitions:
            self.load_field_definitions()
        
        return list(self.field_definitions.get("data_sources", {}).keys())
    
    def get_valid_tags(self) -> List[str]:
        """
        Get list of valid tag full names.
        
        Returns:
            List of tag full names
        """
        if not self.field_definitions:
            self.load_field_definitions()
        
        available_tags = self.field_definitions.get("available_tags", {})
        return available_tags.get("tag_list_full", [])
    
    def get_valid_formats(self) -> List[str]:
        """
        Get list of valid formats.
        
        Returns:
            List of format names
        """
        if not self.field_definitions:
            self.load_field_definitions()
        
        formats = self.field_definitions.get("formats", {})
        return formats.get("format_list", [])
    
    def get_valid_ai_providers(self) -> List[str]:
        """
        Get list of valid AI providers.
        
        Returns:
            List of provider names
        """
        if not self.field_definitions:
            self.load_field_definitions()
        
        providers = self.field_definitions.get("ai_providers", {})
        return providers.get("provider_list", [])
    
    def get_data_source_info(self, source_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a data source.
        
        Args:
            source_name: Name of data source
            
        Returns:
            Data source info dictionary or None
        """
        if not self.field_definitions:
            self.load_field_definitions()
        
        sources = self.field_definitions.get("data_sources", {})
        return sources.get(source_name)
    
    def get_tag_info(self, tag_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a tag.
        
        Args:
            tag_name: Tag full name or short name
            
        Returns:
            Tag info dictionary or None
        """
        if not self.field_definitions:
            self.load_field_definitions()
        
        available_tags = self.field_definitions.get("available_tags", {})
        tags = available_tags.get("tags", [])
        
        for tag in tags:
            if tag.get("full_name") == tag_name or tag.get("short_name") == tag_name:
                return tag
        
        return None
    
    def get_format_info(self, format_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a format.
        
        Args:
            format_name: Format name
            
        Returns:
            Format info dictionary or None
        """
        if not self.field_definitions:
            self.load_field_definitions()
        
        formats = self.field_definitions.get("formats", {})
        
        # Check text formats
        text_formats = formats.get("text_formats", {})
        if format_name in text_formats:
            return text_formats[format_name]
        
        # Check data formats
        data_formats = formats.get("data_formats", {})
        if format_name in data_formats:
            return data_formats[format_name]
        
        return None
    
    def get_recipient_types(self) -> List[str]:
        """
        Get list of valid recipient types.
        
        Returns:
            List of recipient type names
        """
        if not self.field_definitions:
            self.load_field_definitions()
        
        recipient_types = self.field_definitions.get("recipient_types", {})
        return recipient_types.get("type_list", [])
    
    def get_output_formats(self) -> List[str]:
        """
        Get list of valid output formats.
        
        Returns:
            List of output format names
        """
        if not self.field_definitions:
            self.load_field_definitions()
        
        output_formats = self.field_definitions.get("output_formats", {})
        return output_formats.get("format_list", [])


# Singleton instance
_validator_instance = None


def get_template_validator() -> TemplateValidator:
    """
    Get singleton template validator instance.
    
    Returns:
        TemplateValidator instance
    """
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = TemplateValidator()
    return _validator_instance