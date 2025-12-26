"""
WorkmAIn Template CLI Commands
Template Commands v2.1
20251226

CLI commands for template management with interactive creation.

Version History:
- v1.0: Initial implementation with list, show, validate, preview
- v1.1: Fixed date module shadowing
- v1.2: Fixed renderer argument type
- v1.3: Fixed return value unpacking
- v1.4: Fixed output formatting
- v2.0: Added create and add-section commands for interactive template creation
- v2.1: Fixed loader method calls (load_template → load)
"""

import click
import json
from pathlib import Path
from datetime import datetime as dt
from typing import Optional, List

from workmain.templates_engine.loader import get_template_loader
from workmain.templates_engine.validator import get_template_validator
from workmain.templates_engine.renderer import TemplateRenderer
from workmain.templates_engine.field_manager import FieldManager


@click.group()
def templates():
    """Template management commands."""
    pass


@templates.command()
def list():
    """
    List all available templates.
    
    Example:
        workmain templates list
    """
    loader = get_template_loader()
    
    try:
        template_list = loader.list_templates()
        
        if not template_list:
            click.echo("No templates found.")
            return
        
        click.echo(f"\nAvailable templates ({len(template_list)}):\n")
        click.echo("=" * 60)
        
        for template_info in template_list:
            click.echo(f"\nName: {template_info['name']}")
            click.echo(f"  File: {template_info['filename']}")
            click.echo(f"  Type: {template_info.get('recipient_type', 'N/A')}")
            click.echo(f"  Sections: {template_info.get('section_count', 0)}")
            click.echo("-" * 60)
        
    except Exception as e:
        click.echo(f"Error listing templates: {e}", err=True)


@templates.command()
@click.argument('template_name')
def show(template_name: str):
    """
    Show detailed template information.
    
    Example:
        workmain templates show daily_internal
    """
    loader = get_template_loader()
    
    try:
        template = loader.load(template_name)
        
        if not template:
            click.echo(f"Template '{template_name}' not found.", err=True)
            return
        
        click.echo(f"\nTemplate: {template['name']}")
        click.echo("=" * 60)
        click.echo(f"Description: {template.get('description', 'N/A')}")
        click.echo(f"Version: {template.get('version', 'N/A')}")
        click.echo(f"Recipient: {template.get('recipient_type', 'N/A')}")
        click.echo(f"Output Format: {template.get('output_format', 'N/A')}")
        
        if 'sections' in template:
            click.echo(f"\nSections ({len(template['sections'])}):")
            click.echo("-" * 60)
            
            for i, section in enumerate(template['sections'], 1):
                click.echo(f"\n{i}. {section.get('title', 'Untitled')}")
                click.echo(f"   Name: {section.get('name', 'N/A')}")
                click.echo(f"   Required: {section.get('required', False)}")
                
                if 'data_sources' in section:
                    click.echo(f"   Data Sources: {', '.join(section['data_sources'])}")
                elif 'data_source' in section:
                    click.echo(f"   Data Source: {section['data_source']}")
                
                if 'include_tags' in section:
                    click.echo(f"   Include Tags: {', '.join(section['include_tags'])}")
                
                if 'exclude_tags' in section:
                    click.echo(f"   Exclude Tags: {', '.join(section['exclude_tags'])}")
                
                if 'format' in section:
                    click.echo(f"   Format: {section['format']}")
                
                if 'ai_provider' in section:
                    click.echo(f"   AI Provider: {section['ai_provider']}")
        
        click.echo("\n" + "=" * 60)
        
    except Exception as e:
        click.echo(f"Error showing template: {e}", err=True)


@templates.command()
@click.argument('template_name', required=False)
def validate(template_name: Optional[str]):
    """
    Validate template(s) against schema.
    
    Examples:
        workmain templates validate              # Validate all
        workmain templates validate daily_internal
    """
    loader = get_template_loader()
    validator = get_template_validator()
    
    try:
        if template_name:
            # Validate specific template
            template = loader.load(template_name)
            if not template:
                click.echo(f"Template '{template_name}' not found.", err=True)
                return
            
            errors = validator.validate_template(template)
            
            if errors:
                click.echo(f"\nValidation errors in '{template_name}':")
                for error in errors:
                    click.echo(f"  - {error}")
                click.echo(f"\nTotal errors: {len(errors)}")
            else:
                click.echo(f"Template '{template_name}' is valid.")
        else:
            # Validate all templates
            template_list = loader.list_templates()
            
            if not template_list:
                click.echo("No templates found.")
                return
            
            click.echo(f"\nValidating {len(template_list)} template(s)...\n")
            
            all_valid = True
            for template_info in template_list:
                template = loader.load(template_info['filename'])
                errors = validator.validate_template(template)
                
                if errors:
                    all_valid = False
                    click.echo(f"INVALID: {template_info['name']}")
                    for error in errors:
                        click.echo(f"  - {error}")
                    click.echo()
                else:
                    click.echo(f"VALID: {template_info['name']}")
            
            if all_valid:
                click.echo(f"\nAll templates are valid.")
            else:
                click.echo(f"\nSome templates have errors.")
    
    except Exception as e:
        click.echo(f"Error validating template: {e}", err=True)


@templates.command()
@click.argument('template_name')
@click.option('--date', '-d', help='Date for report (YYYY-MM-DD)')
def preview(template_name: str, date: Optional[str]):
    """
    Preview rendered template output.
    
    Examples:
        workmain templates preview daily_internal
        workmain templates preview weekly_client --date 2025-12-20
    """
    loader = get_template_loader()
    
    try:
        template = loader.load(template_name)
        if not template:
            click.echo(f"Template '{template_name}' not found.", err=True)
            return
        
        # Use provided date or today
        if date:
            try:
                report_date = dt.strptime(date, '%Y-%m-%d').date()
            except ValueError:
                click.echo(f"Invalid date format. Use YYYY-MM-DD", err=True)
                return
        else:
            report_date = dt.now().date()
        
        # Create field manager for data retrieval
        field_manager = FieldManager()
        
        # Create renderer
        renderer = TemplateRenderer(field_manager)
        
        # Render template
        output = renderer.render(template, report_date)
        
        # Display preview
        click.echo(f"\nTemplate Preview: {template['name']}")
        click.echo(f"Date: {report_date}")
        click.echo("=" * 60)
        click.echo(output)
        click.echo("=" * 60)
        
    except Exception as e:
        click.echo(f"Error previewing template: {e}", err=True)


@templates.command()
@click.argument('name')
@click.option('--type', '-t', 'template_type', 
              type=click.Choice(['daily_internal', 'weekly_client', 'custom'], case_sensitive=False),
              help='Template type')
def create(name: str, template_type: Optional[str]):
    """
    Create a new template interactively.
    
    Examples:
        workmain templates create "Monthly Summary"
        workmain templates create "Sprint Report" --type custom
    """
    validator = get_template_validator()
    
    try:
        click.echo(f"\nCreating template: {name}")
        click.echo("=" * 60)
        
        # Get template type
        if not template_type:
            click.echo("\nTemplate types:")
            click.echo("  1. daily_internal - Daily internal status report")
            click.echo("  2. weekly_client - Weekly client report")
            click.echo("  3. custom - Custom template")
            
            type_choice = click.prompt("\nSelect type (1-3)", type=int, default=3)
            type_map = {1: 'daily_internal', 2: 'weekly_client', 3: 'custom'}
            template_type = type_map.get(type_choice, 'custom')
        
        # Get description
        description = click.prompt("Description", default=f"{name} report template")
        
        # Get recipient type
        recipient_types = validator.get_recipient_types()
        click.echo(f"\nRecipient types: {', '.join(recipient_types)}")
        recipient_type = click.prompt("Recipient type", 
                                     type=click.Choice(recipient_types, case_sensitive=False),
                                     default='internal_management')
        
        # Get output format
        output_formats = validator.get_output_formats()
        click.echo(f"\nOutput formats: {', '.join(output_formats)}")
        output_format = click.prompt("Output format",
                                    type=click.Choice(output_formats, case_sensitive=False),
                                    default='markdown')
        
        # Get AI provider preference
        ai_providers = validator.get_valid_ai_providers()
        click.echo(f"\nAI providers: {', '.join(ai_providers)}")
        ai_provider = click.prompt("AI provider preference",
                                  type=click.Choice(ai_providers, case_sensitive=False),
                                  default='claude')
        
        # Create template structure
        template = {
            "name": name,
            "description": description,
            "version": "1.0",
            "recipient_type": recipient_type,
            "sections": [],
            "output_format": output_format,
            "delivery": {
                "method": "outlook_draft",
                "subject_template": f"{name} - {{date:%B %d, %Y}}"
            },
            "metadata": {
                "ai_provider_preference": ai_provider,
                "created_at": dt.now().isoformat()
            }
        }
        
        # Validate template
        errors = validator.validate_template(template)
        if errors:
            click.echo("\nValidation errors:")
            for error in errors:
                click.echo(f"  - {error}")
            click.echo("\nTemplate not created.")
            return
        
        # Save template
        project_root = Path(__file__).parent.parent.parent
        templates_dir = project_root / "templates" / "reports"
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename from name
        filename = name.lower().replace(' ', '_').replace('-', '_') + '.json'
        template_path = templates_dir / filename
        
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        click.echo(f"\nTemplate created: {template_path}")
        click.echo(f"\nNext steps:")
        click.echo(f"  1. Add sections: workmain templates add-section {filename.replace('.json', '')} \"Section Title\"")
        click.echo(f"  2. Validate: workmain templates validate {filename.replace('.json', '')}")
        click.echo(f"  3. Preview: workmain templates preview {filename.replace('.json', '')}")
        
    except Exception as e:
        click.echo(f"Error creating template: {e}", err=True)


@templates.command(name='add-section')
@click.argument('template_name')
@click.argument('section_title')
def add_section(template_name: str, section_title: str):
    """
    Add a section to an existing template interactively.
    
    Examples:
        workmain templates add-section monthly_summary "Executive Summary"
        workmain templates add-section sprint_report "Key Metrics"
    """
    loader = get_template_loader()
    validator = get_template_validator()
    
    try:
        # Load existing template
        template = loader.load(template_name)
        if not template:
            click.echo(f"Template '{template_name}' not found.", err=True)
            return
        
        click.echo(f"\nAdding section to: {template['name']}")
        click.echo("=" * 60)
        click.echo(f"Section title: {section_title}")
        
        # Generate section name from title
        section_name = section_title.lower().replace(' ', '_').replace('-', '_')
        click.echo(f"Section name: {section_name}")
        
        # Get required flag
        required = click.confirm("\nIs this section required?", default=True)
        
        # Get format
        formats = validator.get_valid_formats()
        click.echo(f"\nAvailable formats:")
        for i, fmt in enumerate(formats, 1):
            fmt_info = validator.get_format_info(fmt)
            desc = fmt_info.get('description', 'No description') if fmt_info else 'No description'
            click.echo(f"  {i}. {fmt} - {desc}")
        
        format_choice = click.prompt("\nSelect format (name or number)", default='bullets')
        
        # Convert number to format name if needed
        try:
            format_idx = int(format_choice) - 1
            if 0 <= format_idx < len(formats):
                format_name = formats[format_idx]
            else:
                format_name = format_choice
        except ValueError:
            format_name = format_choice
        
        # Validate format
        format_errors = validator.validate_format(format_name)
        if format_errors:
            click.echo(f"\nInvalid format: {format_errors[0]}")
            return
        
        # Get AI provider
        ai_providers = validator.get_valid_ai_providers()
        click.echo(f"\nAI providers: {', '.join(ai_providers)}")
        ai_provider = click.prompt("AI provider",
                                  type=click.Choice(ai_providers, case_sensitive=False),
                                  default=template.get('metadata', {}).get('ai_provider_preference', 'claude'))
        
        # Get data sources
        data_sources = validator.get_valid_data_sources()
        click.echo(f"\nAvailable data sources: {', '.join(data_sources)}")
        data_sources_input = click.prompt("Data sources (comma-separated)", default='notes')
        selected_sources = [s.strip() for s in data_sources_input.split(',')]
        
        # Validate data sources
        ds_errors = validator.validate_data_sources(selected_sources)
        if ds_errors:
            click.echo(f"\nData source errors:")
            for error in ds_errors:
                click.echo(f"  - {error}")
            return
        
        # Get tags
        available_tags = validator.get_valid_tags()
        click.echo(f"\nAvailable tags: {', '.join(available_tags)}")
        
        include_tags_input = click.prompt("Include tags (comma-separated, or 'none')", default='none')
        if include_tags_input.lower() == 'none':
            include_tags = []
        else:
            include_tags = [t.strip() for t in include_tags_input.split(',')]
        
        exclude_tags_input = click.prompt("Exclude tags (comma-separated, or 'none')", default='none')
        if exclude_tags_input.lower() == 'none':
            exclude_tags = []
        else:
            exclude_tags = [t.strip() for t in exclude_tags_input.split(',')]
        
        # Validate tags
        if include_tags:
            tag_errors = validator.validate_tags(include_tags)
            if tag_errors:
                click.echo(f"\nInclude tag errors:")
                for error in tag_errors:
                    click.echo(f"  - {error}")
                return
        
        if exclude_tags:
            tag_errors = validator.validate_tags(exclude_tags)
            if tag_errors:
                click.echo(f"\nExclude tag errors:")
                for error in tag_errors:
                    click.echo(f"  - {error}")
                return
        
        # Get AI instruction
        default_instruction = f"Generate {section_title.lower()} section with clear, concise content."
        ai_instruction = click.prompt("\nAI instruction (or press Enter for default)", 
                                     default=default_instruction)
        
        # Create section
        section = {
            "name": section_name,
            "title": section_title,
            "required": required,
            "data_sources": selected_sources,
            "format": format_name,
            "ai_provider": ai_provider,
            "ai_instruction": ai_instruction
        }
        
        if include_tags:
            section["include_tags"] = include_tags
        
        if exclude_tags:
            section["exclude_tags"] = exclude_tags
        
        # Add section to template
        template['sections'].append(section)
        
        # Validate updated template
        errors = validator.validate_template(template)
        if errors:
            click.echo("\nValidation errors:")
            for error in errors:
                click.echo(f"  - {error}")
            click.echo("\nSection not added.")
            return
        
        # Save updated template
        project_root = Path(__file__).parent.parent.parent
        templates_dir = project_root / "templates" / "reports"
        
        # Find template file
        template_files = list(templates_dir.glob(f"{template_name}.json"))
        if not template_files:
            # Try with underscores
            template_files = list(templates_dir.glob(f"{template_name.replace('-', '_')}.json"))
        
        if not template_files:
            click.echo(f"\nCould not find template file for '{template_name}'", err=True)
            return
        
        template_path = template_files[0]
        
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        click.echo(f"\nSection added to {template['name']}")
        click.echo(f"Total sections: {len(template['sections'])}")
        click.echo(f"\nNext steps:")
        click.echo(f"  - Add more sections: workmain templates add-section {template_name} \"Title\"")
        click.echo(f"  - Validate: workmain templates validate {template_name}")
        click.echo(f"  - Preview: workmain templates preview {template_name}")
        
    except Exception as e:
        click.echo(f"Error adding section: {e}", err=True)


# Export command group
__all__ = ['templates']