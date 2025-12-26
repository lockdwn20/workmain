"""
WorkmAIn Template CLI Commands
Template Commands v2.0
20251226

CLI commands for template management with interactive creation.

Version History:
- v1.0: Initial implementation (list, show, validate)
- v1.1: Fixed date module shadowing
- v1.2: Fixed renderer argument type
- v1.3: Fixed return value unpacking
- v1.4: Fixed output formatting
- v2.0: Added create and add-section commands for template extensibility
"""

import click
import json
from pathlib import Path
from datetime import datetime as dt
from typing import Optional, List, Dict, Any

from workmain.templates_engine.loader import TemplateLoader, get_loader
from workmain.templates_engine.validator import TemplateValidator, get_validator
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
    loader = get_loader()
    
    try:
        template_list = loader.list_templates()
        
        if not template_list:
            click.echo("No templates found.")
            return
        
        click.echo(f"\nAvailable Templates ({len(template_list)}):\n")
        click.echo("=" * 60)
        
        for template_name in sorted(template_list):
            template = loader.load_template(template_name)
            
            # Template info
            description = template.get("description", "No description")
            version = template.get("version", "unknown")
            section_count = len(template.get("sections", []))
            
            click.echo(f"\n{template_name}")
            click.echo(f"  Description: {description}")
            click.echo(f"  Version: {version}")
            click.echo(f"  Sections: {section_count}")
        
        click.echo("\n" + "=" * 60)
        
    except Exception as e:
        click.echo(f"Error listing templates: {e}", err=True)


@templates.command()
@click.argument('template_name')
def show(template_name: str):
    """
    Show details of a specific template.
    
    Example:
        workmain templates show daily_internal
    """
    loader = get_loader()
    
    try:
        template = loader.load_template(template_name)
        
        # Template metadata
        click.echo(f"\nTemplate: {template_name}")
        click.echo("=" * 60)
        click.echo(f"Name: {template.get('name', 'Unknown')}")
        click.echo(f"Description: {template.get('description', 'No description')}")
        click.echo(f"Version: {template.get('version', 'unknown')}")
        
        if "recipient_type" in template:
            click.echo(f"Recipient Type: {template['recipient_type']}")
        
        if "output_format" in template:
            click.echo(f"Output Format: {template['output_format']}")
        
        # Sections
        sections = template.get("sections", [])
        click.echo(f"\nSections ({len(sections)}):")
        click.echo("-" * 60)
        
        for i, section in enumerate(sections, 1):
            click.echo(f"\n{i}. {section.get('title', 'Unnamed Section')}")
            click.echo(f"   Name: {section.get('name', 'unnamed')}")
            click.echo(f"   Required: {'Yes' if section.get('required', False) else 'No'}")
            
            if "format" in section:
                click.echo(f"   Format: {section['format']}")
            
            if "data_sources" in section:
                click.echo(f"   Data Sources: {', '.join(section['data_sources'])}")
            elif "data_source" in section:
                click.echo(f"   Data Source: {section['data_source']}")
            
            if "ai_provider" in section:
                click.echo(f"   AI Provider: {section['ai_provider']}")
        
        click.echo()
        
    except FileNotFoundError:
        click.echo(f"Template '{template_name}' not found.", err=True)
    except Exception as e:
        click.echo(f"Error loading template: {e}", err=True)


@templates.command()
@click.argument('template_name', required=False)
def validate(template_name: Optional[str]):
    """
    Validate template(s) against schema and field definitions.
    
    Examples:
        workmain templates validate              # Validate all
        workmain templates validate daily_internal  # Validate one
    """
    loader = get_loader()
    validator = get_validator()
    
    try:
        if template_name:
            # Validate single template
            template = loader.load_template(template_name)
            errors = validator.validate_template(template)
            
            if errors:
                click.echo(f"\nValidation errors for '{template_name}':")
                for error in errors:
                    click.echo(f"  ✗ {error}")
                click.echo()
            else:
                click.echo(f"✓ Template '{template_name}' is valid")
        
        else:
            # Validate all templates
            template_list = loader.list_templates()
            
            if not template_list:
                click.echo("No templates found to validate.")
                return
            
            all_valid = True
            results = []
            
            for name in sorted(template_list):
                template = loader.load_template(name)
                errors = validator.validate_template(template)
                
                if errors:
                    all_valid = False
                    results.append((name, errors))
                else:
                    results.append((name, None))
            
            # Display results
            click.echo(f"\nValidation Results ({len(template_list)} templates):\n")
            click.echo("=" * 60)
            
            for name, errors in results:
                if errors:
                    click.echo(f"\n✗ {name}: {len(errors)} error(s)")
                    for error in errors:
                        click.echo(f"    • {error}")
                else:
                    click.echo(f"✓ {name}: Valid")
            
            click.echo("\n" + "=" * 60)
            
            if all_valid:
                click.echo("✓ All templates are valid")
            else:
                click.echo(f"✗ {sum(1 for _, e in results if e)} template(s) have errors")
    
    except Exception as e:
        click.echo(f"Error during validation: {e}", err=True)


@templates.command()
@click.argument('template_name')
def preview(template_name: str):
    """
    Preview template output (without data).
    
    Example:
        workmain templates preview daily_internal
    """
    loader = get_loader()
    renderer = TemplateRenderer()
    
    try:
        template = loader.load_template(template_name)
        
        # Render with empty data
        output = renderer.render_template(template, {})
        
        # Display
        click.echo(f"\nPreview: {template.get('name', template_name)}")
        click.echo("=" * 60)
        click.echo(output)
        click.echo("=" * 60)
    
    except FileNotFoundError:
        click.echo(f"Template '{template_name}' not found.", err=True)
    except Exception as e:
        click.echo(f"Error rendering template: {e}", err=True)


@templates.command()
@click.argument('template_name')
@click.option('--type', '-t', 'template_type',
              type=click.Choice(['daily_internal', 'weekly_client', 'custom'], case_sensitive=False),
              default='custom',
              help='Template type (determines default settings)')
def create(template_name: str, template_type: str):
    """
    Create a new template interactively.
    
    Examples:
        workmain templates create "Monthly Summary"
        workmain templates create "Sprint Report" --type custom
    """
    loader = get_loader()
    validator = get_validator()
    
    click.echo(f"\nCreating template: {template_name}")
    click.echo("=" * 60)
    
    # Check if template already exists
    existing_templates = loader.list_templates()
    template_filename = template_name.lower().replace(" ", "_")
    
    if template_filename in existing_templates:
        click.echo(f"✗ Template '{template_filename}' already exists.")
        if not click.confirm("Overwrite?", default=False):
            click.echo("Cancelled.")
            return
    
    # Interactive prompts
    click.echo("\nTemplate Configuration:")
    
    # Description
    description = click.prompt("Description", default=f"{template_name} report")
    
    # Recipient type
    recipient_types = validator.get_recipient_types()
    click.echo(f"\nAvailable recipient types: {', '.join(recipient_types)}")
    recipient_type = click.prompt(
        "Recipient type",
        type=click.Choice(recipient_types, case_sensitive=False),
        default='custom'
    )
    
    # Output format
    output_formats = validator.get_output_formats()
    click.echo(f"\nAvailable output formats: {', '.join(output_formats)}")
    output_format = click.prompt(
        "Output format",
        type=click.Choice(output_formats, case_sensitive=False),
        default='markdown'
    )
    
    # AI provider preference
    ai_providers = validator.get_valid_ai_providers()
    click.echo(f"\nAvailable AI providers: {', '.join(ai_providers)}")
    ai_provider_pref = click.prompt(
        "AI provider preference",
        type=click.Choice(ai_providers, case_sensitive=False),
        default='claude'
    )
    
    # Build template structure
    template = {
        "name": template_name,
        "description": description,
        "version": "1.0",
        "recipient_type": recipient_type,
        "sections": [],
        "output_format": output_format,
        "metadata": {
            "ai_provider_preference": ai_provider_pref,
            "created_at": dt.now().strftime("%Y-%m-%d"),
            "template_type": template_type
        }
    }
    
    # Add delivery section if not custom
    if template_type == 'daily_internal':
        template["delivery"] = {
            "method": "outlook_draft",
            "to_from_config": "daily",
            "subject_template": f"{template_name} - {{date:%B %d, %Y}}"
        }
    elif template_type == 'weekly_client':
        template["delivery"] = {
            "method": "outlook_draft",
            "to_from_config": "weekly",
            "cc_from_config": "weekly",
            "subject_template": f"{template_name} - Week Ending {{date:%B %d, %Y}}"
        }
    
    # Validate template
    errors = validator.validate_template(template)
    if errors:
        click.echo("\n⚠️  Validation errors:")
        for error in errors:
            click.echo(f"  • {error}")
        
        if not click.confirm("\nSave anyway?", default=False):
            click.echo("Cancelled.")
            return
    
    # Save template
    try:
        loader.save_template(template_filename, template)
        click.echo(f"\n✓ Template '{template_filename}' created successfully")
        click.echo(f"  Location: templates/reports/{template_filename}.json")
        click.echo(f"\nNext steps:")
        click.echo(f"  1. Add sections: workmain templates add-section {template_filename} \"Section Title\"")
        click.echo(f"  2. Validate: workmain templates validate {template_filename}")
        click.echo(f"  3. Preview: workmain templates preview {template_filename}")
    
    except Exception as e:
        click.echo(f"\n✗ Error saving template: {e}", err=True)


@templates.command(name='add-section')
@click.argument('template_name')
@click.argument('section_title')
def add_section(template_name: str, section_title: str):
    """
    Add a section to an existing template interactively.
    
    Examples:
        workmain templates add-section monthly_summary "Key Metrics"
        workmain templates add-section sprint_report "Accomplishments"
    """
    loader = get_loader()
    validator = get_validator()
    
    try:
        # Load existing template
        template = loader.load_template(template_name)
        
        click.echo(f"\nAdding section to template: {template_name}")
        click.echo("=" * 60)
        click.echo(f"Section title: {section_title}")
        
        # Interactive section configuration
        click.echo("\nSection Configuration:")
        
        # Section name (auto-generate from title)
        default_name = section_title.lower().replace(" ", "_").replace("&", "and")
        section_name = click.prompt("Section name", default=default_name)
        
        # Required
        required = click.confirm("Is this section required?", default=True)
        
        # Format
        valid_formats = validator.get_valid_formats()
        click.echo(f"\nAvailable formats:")
        for i, fmt in enumerate(valid_formats, 1):
            fmt_info = validator.get_format_info(fmt)
            if fmt_info:
                desc = fmt_info.get('description', '')
                click.echo(f"  {i}. {fmt} - {desc}")
            else:
                click.echo(f"  {i}. {fmt}")
        
        format_choice = click.prompt(
            "Format",
            type=click.Choice(valid_formats, case_sensitive=False),
            default='bullets'
        )
        
        # AI Provider
        valid_providers = validator.get_valid_ai_providers()
        click.echo(f"\nAvailable AI providers: {', '.join(valid_providers)}")
        ai_provider = click.prompt(
            "AI provider",
            type=click.Choice(valid_providers, case_sensitive=False),
            default=template.get('metadata', {}).get('ai_provider_preference', 'claude')
        )
        
        # Data sources
        valid_sources = validator.get_valid_data_sources()
        click.echo(f"\nAvailable data sources: {', '.join(valid_sources)}")
        
        data_sources_input = click.prompt(
            "Data sources (comma-separated)",
            default="notes"
        )
        data_sources = [s.strip() for s in data_sources_input.split(',')]
        
        # Validate data sources
        source_errors = []
        for source in data_sources:
            if source not in valid_sources:
                source_errors.append(f"Invalid data source: {source}")
        
        if source_errors:
            click.echo("\n⚠️  Data source errors:")
            for error in source_errors:
                click.echo(f"  • {error}")
            
            if not click.confirm("Continue anyway?", default=False):
                click.echo("Cancelled.")
                return
        
        # Tags
        valid_tags = validator.get_valid_tags()
        click.echo(f"\nAvailable tags: {', '.join(valid_tags)}")
        
        # Include tags
        include_tags_input = click.prompt(
            "Include tags (comma-separated, or leave empty)",
            default="both,internal-only",
            show_default=True
        )
        
        include_tags = []
        if include_tags_input.strip():
            include_tags = [t.strip() for t in include_tags_input.split(',')]
        
        # Exclude tags
        exclude_tags_input = click.prompt(
            "Exclude tags (comma-separated, or leave empty)",
            default="",
            show_default=False
        )
        
        exclude_tags = []
        if exclude_tags_input.strip():
            exclude_tags = [t.strip() for t in exclude_tags_input.split(',')]
        
        # AI instruction
        click.echo("\nAI Instruction (how the AI should process this section):")
        ai_instruction = click.prompt(
            "Instruction",
            default=f"Summarize {section_title.lower()} in {format_choice} format"
        )
        
        # Build section
        section = {
            "name": section_name,
            "title": section_title,
            "required": required,
            "ai_instruction": ai_instruction,
            "data_sources": data_sources,
            "format": format_choice,
            "ai_provider": ai_provider
        }
        
        # Add tags if specified
        if include_tags:
            section["include_tags"] = include_tags
        if exclude_tags:
            section["exclude_tags"] = exclude_tags
        
        # Validate section
        section_errors = validator.validate_section(section)
        if section_errors:
            click.echo("\n⚠️  Section validation errors:")
            for error in section_errors:
                click.echo(f"  • {error}")
            
            if not click.confirm("\nAdd section anyway?", default=False):
                click.echo("Cancelled.")
                return
        
        # Add section to template
        if "sections" not in template:
            template["sections"] = []
        
        template["sections"].append(section)
        
        # Validate complete template
        template_errors = validator.validate_template(template)
        if template_errors:
            click.echo("\n⚠️  Template validation warnings:")
            for error in template_errors:
                click.echo(f"  • {error}")
        
        # Save updated template
        loader.save_template(template_name, template)
        
        click.echo(f"\n✓ Section '{section_title}' added successfully")
        click.echo(f"  Template now has {len(template['sections'])} section(s)")
        click.echo(f"\nNext steps:")
        click.echo(f"  1. Add more sections: workmain templates add-section {template_name} \"Another Section\"")
        click.echo(f"  2. Validate: workmain templates validate {template_name}")
        click.echo(f"  3. Preview: workmain templates preview {template_name}")
    
    except FileNotFoundError:
        click.echo(f"✗ Template '{template_name}' not found.", err=True)
        click.echo(f"  Create it first: workmain templates create \"{template_name}\"")
    except Exception as e:
        click.echo(f"✗ Error adding section: {e}", err=True)


# Export command group
__all__ = ['templates']