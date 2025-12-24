"""
WorkmAIn Template Renderer
Template Renderer v1.0
20251224

Renders templates by combining template structure with data.
Prepares data for AI processing and generates final output.
"""

from datetime import date, datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from workmain.templates_engine.loader import TemplateLoader, get_template_loader
from workmain.templates_engine.validator import TemplateValidator, get_template_validator
from workmain.templates_engine.field_manager import FieldManager, get_field_manager


class TemplateRenderer:
    """
    Render templates into final output.
    
    Workflow:
    1. Load template
    2. Validate template structure
    3. Get data for each section
    4. Format data according to section config
    5. Prepare for AI processing (Phase 4)
    6. Generate final markdown output
    """
    
    def __init__(
        self,
        session: Session,
        template_loader: Optional[TemplateLoader] = None,
        template_validator: Optional[TemplateValidator] = None,
        field_manager: Optional[FieldManager] = None
    ):
        """
        Initialize template renderer.
        
        Args:
            session: Database session
            template_loader: Template loader instance (optional)
            template_validator: Template validator instance (optional)
            field_manager: Field manager instance (optional)
        """
        self.session = session
        self.loader = template_loader or get_template_loader()
        self.validator = template_validator or get_template_validator()
        self.field_manager = field_manager or get_field_manager(session)
    
    def render(
        self,
        template_name: str,
        report_date: Optional[date] = None,
        user_full_name: Optional[str] = None,
        recipients: Optional[List[str]] = None,
        use_ai: bool = False
    ) -> Dict[str, Any]:
        """
        Render a template into final output.
        
        Args:
            template_name: Name of template to render
            report_date: Date for the report (defaults to today)
            user_full_name: User's full name for subject line
            recipients: List of recipient names
            use_ai: Whether to use AI for content generation (Phase 4)
            
        Returns:
            Dictionary containing:
            {
                'template_name': str,
                'template_type': str,
                'subject_line': str,
                'sections': [
                    {
                        'name': str,
                        'title': str,
                        'content': str,  # Final rendered content
                        'data': dict,    # Raw data used
                    }
                ],
                'output': str,  # Final complete output
                'metadata': {
                    'generated_at': datetime,
                    'report_date': date,
                    'ai_used': bool,
                }
            }
        """
        if report_date is None:
            report_date = date.today()
        
        # Load template
        template = self.loader.load(template_name)
        
        # Validate template
        self.validator.validate_and_raise(template)
        
        # Build variables for subject line
        variables = self._build_variables(report_date, user_full_name, recipients)
        
        # Substitute variables in template
        template = self.loader.substitute_variables(template, variables)
        
        # Get date range for this report type
        report_type = template.get('template_type', 'daily_internal')
        start_date, end_date = self.field_manager.get_date_range_for_report_type(
            report_type, report_date
        )
        
        # Render each section
        rendered_sections = []
        
        for section in template['sections']:
            rendered_section = self._render_section(
                section, start_date, end_date, use_ai
            )
            rendered_sections.append(rendered_section)
        
        # Generate final output
        output = self._generate_output(template, rendered_sections)
        
        # Build result
        result = {
            'template_name': template_name,
            'template_type': template.get('template_type'),
            'subject_line': template.get('subject_line', ''),
            'sections': rendered_sections,
            'output': output,
            'metadata': {
                'generated_at': datetime.now(),
                'report_date': report_date,
                'date_range': {
                    'start': start_date,
                    'end': end_date,
                },
                'ai_used': use_ai,
                'template_version': template.get('version', '1.0'),
            }
        }
        
        return result
    
    def _render_section(
        self,
        section: Dict[str, Any],
        start_date: date,
        end_date: date,
        use_ai: bool
    ) -> Dict[str, Any]:
        """
        Render a single section.
        
        Args:
            section: Section configuration
            start_date: Start date for data
            end_date: End date for data
            use_ai: Whether to use AI
            
        Returns:
            Rendered section dictionary
        """
        # Get data for section
        section_data = self.field_manager.get_section_data(
            section, start_date, end_date
        )
        
        # Format data
        formatted_data = self.field_manager.format_section_output(
            section_data, section
        )
        
        # Generate content
        if use_ai:
            # Phase 4: Use AI to generate content
            # For now, placeholder
            content = self._generate_content_with_ai(section, formatted_data)
        else:
            # Without AI: Just format the raw data
            content = self._generate_content_without_ai(section, section_data)
        
        return {
            'name': section['name'],
            'title': section['title'],
            'content': content,
            'data': section_data,
            'formatted_data': formatted_data,
        }
    
    def _generate_content_with_ai(
        self,
        section: Dict[str, Any],
        formatted_data: str
    ) -> str:
        """
        Generate section content using AI.
        
        This is a placeholder for Phase 4 implementation.
        
        Args:
            section: Section configuration
            formatted_data: Formatted data string
            
        Returns:
            AI-generated content
        """
        # Phase 4: Will call Claude or Gemini API here
        # For now, return placeholder
        return f"[AI content will be generated here in Phase 4]\n\n{formatted_data}"
    
    def _generate_content_without_ai(
        self,
        section: Dict[str, Any],
        section_data: Dict[str, Any]
    ) -> str:
        """
        Generate section content without AI (simple formatting).
        
        Args:
            section: Section configuration
            section_data: Section data
            
        Returns:
            Formatted content
        """
        lines = []
        
        # Format based on section format
        section_format = section.get('format', 'bullets')
        
        if section_format == 'bullets':
            # Generate bullet list from notes
            for note in section_data.get('notes', []):
                lines.append(f"- {note['content']}")
            
            # Add time entries if present
            for entry in section_data.get('time_entries', []):
                lines.append(f"- {entry['description']} ({entry['duration_hours']}h)")
        
        elif section_format == 'time_summary':
            # Generate time summary
            summary = section_data.get('summary', {})
            
            if summary.get('category_hours'):
                for category, hours in summary['category_hours'].items():
                    lines.append(f"- {category}: {hours:.2f}h")
                
                lines.append(f"- **Total**: {summary['total_hours']:.2f}h")
        
        elif section_format == 'numbered_list':
            # Generate numbered list
            for idx, note in enumerate(section_data.get('notes', []), 1):
                lines.append(f"{idx}. {note['content']}")
        
        else:
            # Default: prose (just concatenate)
            for note in section_data.get('notes', []):
                lines.append(note['content'])
        
        # If no content, check if section requires content
        if not lines:
            if section.get('required', False):
                lines.append("None at this time.")
            else:
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_output(
        self,
        template: Dict[str, Any],
        sections: List[Dict[str, Any]]
    ) -> str:
        """
        Generate final output from rendered sections.
        
        Args:
            template: Template configuration
            sections: List of rendered sections
            
        Returns:
            Final markdown output
        """
        lines = []
        
        # Add subject line if present
        if template.get('subject_line'):
            lines.append(f"**Subject:** {template['subject_line']}")
            lines.append("")
        
        # Add each section
        for section in sections:
            # Section title
            lines.append(f"#### {section['title']}")
            
            # Section content
            lines.append(section['content'])
            lines.append("")
        
        return "\n".join(lines)
    
    def _build_variables(
        self,
        report_date: date,
        user_full_name: Optional[str],
        recipients: Optional[List[str]]
    ) -> Dict[str, str]:
        """
        Build template variables.
        
        Args:
            report_date: Report date
            user_full_name: User's full name
            recipients: List of recipients
            
        Returns:
            Dictionary of variables
        """
        # Get user_full_name from config if not provided
        if user_full_name is None:
            user_full_name = self._get_user_full_name()
        
        # Build variables using loader's helper
        variables = self.loader.build_variables(
            report_date, user_full_name, recipients
        )
        
        return variables
    
    def _get_user_full_name(self) -> str:
        """
        Get user's full name from configuration.
        
        Returns:
            User's full name or default
        """
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Try environment variable first
        name = os.getenv('USER_FULL_NAME')
        
        if name:
            return name
        
        # Try config file
        try:
            from workmain.config_manager.loader import get_config
            config = get_config()
            name = config.get('user_preferences', 'user_full_name')
            
            if name:
                return name
        except Exception:
            pass
        
        # Default
        return "User Name"
    
    def preview(
        self,
        template_name: str,
        report_date: Optional[date] = None
    ) -> str:
        """
        Generate a preview of the template without AI processing.
        
        Args:
            template_name: Name of template
            report_date: Date for report (defaults to today)
            
        Returns:
            Preview text
        """
        result = self.render(
            template_name=template_name,
            report_date=report_date,
            use_ai=False
        )
        
        return result['output']


# Convenience function
def get_template_renderer(session: Session) -> TemplateRenderer:
    """
    Get template renderer instance.
    
    Args:
        session: Database session
        
    Returns:
        TemplateRenderer instance
    """
    return TemplateRenderer(session)


def render_template(
    session: Session,
    template_name: str,
    report_date: Optional[date] = None,
    use_ai: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to render a template.
    
    Args:
        session: Database session
        template_name: Template to render
        report_date: Date for report
        use_ai: Whether to use AI
        
    Returns:
        Rendered result dictionary
    """
    renderer = get_template_renderer(session)
    return renderer.render(template_name, report_date, use_ai=use_ai)
