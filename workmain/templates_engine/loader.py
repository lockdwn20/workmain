"""
WorkmAIn Template Loader
Template Loader v1.0
20251224

Loads and manages JSON template files for report generation.
Provides caching and validation of template structure.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class TemplateLoader:
    """
    Load and manage report templates from JSON files.
    
    Provides:
    - Loading templates from templates/reports/ directory
    - Caching loaded templates
    - Listing available templates
    - Reloading templates when changed
    - Variable substitution for template metadata
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template loader.
        
        Args:
            templates_dir: Path to templates directory. 
                          If None, uses project_root/templates/reports/
        """
        if templates_dir is None:
            # Default to project templates/reports directory
            project_root = Path(__file__).parent.parent.parent
            templates_dir = project_root / "templates" / "reports"
        
        self.templates_dir = Path(templates_dir)
        self._templates_cache: Dict[str, Dict[str, Any]] = {}
        self._loaded = False
        
        # Ensure templates directory exists
        if not self.templates_dir.exists():
            self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    def load(self, template_name: str, reload: bool = False) -> Dict[str, Any]:
        """
        Load a specific template by name.
        
        Args:
            template_name: Name of template (without .json extension)
            reload: If True, reload from disk even if cached
            
        Returns:
            Template dictionary
            
        Raises:
            FileNotFoundError: If template file not found
            json.JSONDecodeError: If template has invalid JSON
            ValueError: If template is missing required fields
        """
        # Check cache first (unless reload requested)
        if not reload and template_name in self._templates_cache:
            return self._templates_cache[template_name]
        
        # Build file path
        template_file = self.templates_dir / f"{template_name}.json"
        
        if not template_file.exists():
            raise FileNotFoundError(
                f"Template '{template_name}' not found at {template_file}"
            )
        
        # Load template
        try:
            with open(template_file, 'r') as f:
                template = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in template '{template_name}': {e.msg}",
                e.doc,
                e.pos
            )
        
        # Validate required top-level fields
        required_fields = ['name', 'sections', 'output_format']
        missing = [f for f in required_fields if f not in template]
        
        if missing:
            raise ValueError(
                f"Template '{template_name}' missing required fields: {missing}"
            )
        
        # Cache the template
        self._templates_cache[template_name] = template
        
        return template
    
    def load_all(self, reload: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Load all templates from the templates directory.
        
        Args:
            reload: If True, reload all templates from disk
            
        Returns:
            Dictionary mapping template names to template data
        """
        if reload or not self._loaded:
            self._templates_cache = {}
        
        # Find all .json files in templates directory
        template_files = list(self.templates_dir.glob("*.json"))
        
        templates = {}
        for template_file in template_files:
            template_name = template_file.stem  # Filename without extension
            
            try:
                template = self.load(template_name, reload=reload)
                templates[template_name] = template
            except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
                # Log error but continue loading other templates
                print(f"Warning: Failed to load template '{template_name}': {e}")
                continue
        
        self._loaded = True
        return templates
    
    def list_templates(self) -> List[str]:
        """
        List all available template names.
        
        Returns:
            List of template names (without .json extension)
        """
        template_files = list(self.templates_dir.glob("*.json"))
        return sorted([f.stem for f in template_files])
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """
        Get metadata about a template without loading full structure.
        
        Args:
            template_name: Name of template
            
        Returns:
            Dictionary with template metadata (name, description, version, etc.)
        """
        template = self.load(template_name)
        
        return {
            'name': template.get('name'),
            'template_type': template.get('template_type'),
            'description': template.get('description'),
            'version': template.get('version', '1.0'),
            'recipient_type': template.get('recipient_type'),
            'sections_count': len(template.get('sections', [])),
            'output_format': template.get('output_format'),
            'ai_provider_default': template.get('ai_provider_default'),
        }
    
    def reload(self, template_name: str) -> Dict[str, Any]:
        """
        Reload a specific template from disk.
        
        Args:
            template_name: Name of template to reload
            
        Returns:
            Reloaded template dictionary
        """
        return self.load(template_name, reload=True)
    
    def reload_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Reload all templates from disk.
        
        Returns:
            Dictionary of all reloaded templates
        """
        return self.load_all(reload=True)
    
    def get_section(
        self, 
        template_name: str, 
        section_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific section from a template.
        
        Args:
            template_name: Name of template
            section_name: Name of section to retrieve
            
        Returns:
            Section dictionary or None if not found
        """
        template = self.load(template_name)
        sections = template.get('sections', [])
        
        for section in sections:
            if section.get('name') == section_name:
                return section
        
        return None
    
    def get_sections(self, template_name: str) -> List[Dict[str, Any]]:
        """
        Get all sections from a template.
        
        Args:
            template_name: Name of template
            
        Returns:
            List of section dictionaries
        """
        template = self.load(template_name)
        return template.get('sections', [])
    
    def substitute_variables(
        self, 
        template: Dict[str, Any],
        variables: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Substitute variables in template strings.
        
        Variables like {user_full_name}, {date_long}, etc. are replaced
        with actual values.
        
        Args:
            template: Template dictionary
            variables: Dictionary of variable names to values
            
        Returns:
            Template with substituted variables
        """
        import copy
        
        # Deep copy to avoid modifying cached template
        template_copy = copy.deepcopy(template)
        
        # Substitute in subject_line
        if 'subject_line' in template_copy:
            subject = template_copy['subject_line']
            for var_name, var_value in variables.items():
                subject = subject.replace(f"{{{var_name}}}", str(var_value))
            template_copy['subject_line'] = subject
        
        # Could extend this to substitute in other template fields if needed
        
        return template_copy
    
    def get_available_variables(self) -> Dict[str, str]:
        """
        Get list of available template variables and their descriptions.
        
        Returns:
            Dictionary mapping variable names to descriptions
        """
        return {
            'user_full_name': 'User\'s full name (from config)',
            'day_name': 'Day of week (Monday, Tuesday, etc.)',
            'date_long': 'Long date format (December 24, 2025)',
            'date_short': 'Short date format (12/24/2025)',
            'date_iso': 'ISO date format (2025-12-24)',
            'week_of': 'Week of date (Week of December 22, 2025)',
            'recipients': 'Report recipients (from config)',
        }
    
    def build_variables(
        self,
        report_date: datetime,
        user_full_name: str,
        recipients: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Build template variables dictionary for a specific date.
        
        Args:
            report_date: Date for the report
            user_full_name: User's full name
            recipients: Optional list of recipient names
            
        Returns:
            Dictionary of variable name → value mappings
        """
        # Get week start (Monday)
        week_start = report_date - datetime.timedelta(days=report_date.weekday())
        
        variables = {
            'user_full_name': user_full_name,
            'day_name': report_date.strftime('%A'),
            'date_long': report_date.strftime('%B %d, %Y'),
            'date_short': report_date.strftime('%m/%d/%Y'),
            'date_iso': report_date.strftime('%Y-%m-%d'),
            'week_of': week_start.strftime('Week of %B %d, %Y'),
        }
        
        # Add recipients if provided
        if recipients:
            variables['recipients'] = ', '.join(recipients)
        else:
            variables['recipients'] = ''
        
        return variables


# Global template loader instance
_template_loader: Optional[TemplateLoader] = None


def get_template_loader() -> TemplateLoader:
    """
    Get global template loader instance.
    
    Returns:
        TemplateLoader instance
    """
    global _template_loader
    if _template_loader is None:
        _template_loader = TemplateLoader()
    return _template_loader
