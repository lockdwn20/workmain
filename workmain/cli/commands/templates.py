"""
WorkmAIn Template CLI Commands
Template Commands v2.8
20260319

CLI commands for template management with interactive creation and alias management.

Version History:
- v1.0: Initial implementation with list, show, validate, preview
- v1.1: Fixed date module shadowing
- v1.2: Fixed renderer argument type
- v1.3: Fixed return value unpacking
- v1.4: Fixed output formatting
- v2.0: Added create and add-section commands for interactive template creation
- v2.1: Fixed loader method calls (load_template → load)
- v2.2: Fixed project root path (3 parents → 4 parents for correct templates/ location)
- v2.3: Added detailed error traceback to add_section for debugging
- v2.4: Fixed glob/Click conflict by replacing glob() with iterdir() for file search
- v2.5: Fixed list command to handle string template names (load each template for details)
- v2.6: Added alias management (register, unregister, list-aliases) for simplified CLI usage
- v2.7: Phase 5.1 - Fixed help text formatting with \b escape sequence
- v2.8: Item 18 - Migrated preview command from get_session() to get_db() pattern
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
from workmain.config_manager.alias_manager import get_alias_manager


@click.group()
def templates():
    """Template management commands."""
    pass


@templates.command()
def list():
    """
    List all available templates.

    \b
    Example:
      workmain templates list
    """
    loader = get_template_loader()
    
    try:
        template_names = loader.list_templates()
        
        if not template_names:
            click.echo("No templates found.")
            return
        
        click.echo(f"\nAvailable templates ({len(template_names)}):\n")
        click.echo("=" * 60)
        
        for name in template_names:
            # Load each template to get details
            template = loader.load(name)
            if template:
                click.echo(f"\nName: {template['name']}")
                click.echo(f"  File: {name}.json")
                click.echo(f"  Type: {template.get('recipient_type', 'N/A')}")
                click.echo(f"  Sections: {len(template.get('sections', []))}")
                click.echo("-" * 60)
        
    except Exception as e:
        click.echo(f"Error listing templates: {e}", err=True)
        import traceback
        click.echo("\nFull error traceback:", err=True)
        traceback.print_exc()


@templates.command(name='list-aliases')
def list_aliases():
    """
    List all registered template aliases.

    Shows shortcut names that can be used instead of full template names.

    \b
    Example:
      workmain templates list-aliases
    """
    alias_manager = get_alias_manager()
    
    try:
        aliases = alias_manager.list_aliases()
        
        if not aliases:
            click.echo("\nNo template aliases registered.")
            click.echo("\nRegister an alias with:")
            click.echo("  workmain templates register <template_name> --alias <shortcut>")
            return
        
        click.echo(f"\nRegistered aliases ({len(aliases)}):\n")
        click.echo("=" * 60)
        
        for alias_info in aliases:
            click.echo(f"\n  {alias_info.alias} → {alias_info.template_name}")
        
        click.echo("\n" + "=" * 60)
        click.echo("\nUsage:")
        click.echo("  workmain report <alias> --send")
        click.echo("  Example: workmain report daily --send")
        
    except Exception as e:
        click.echo(f"Error listing aliases: {e}", err=True)


@templates.command()
@click.argument('template_name')
@click.option('--alias', required=True, help='Short alias name')
def register(template_name: str, alias: str):
    """
    Register a template alias for easier CLI usage.

    Creates a shortcut name that can be used in place of the full template name.

    \b
    Examples:
      workmain templates register monthly_executive --alias monthly
      workmain templates register security_audit --alias security

    After registration:
      workmain report monthly --send
    """
    loader = get_template_loader()
    alias_manager = get_alias_manager()
    
    try:
        # Verify template exists
        template = loader.load(template_name)
        if not template:
            click.echo(f"\n✗ Template '{template_name}' not found.", err=True)
            click.echo("\nAvailable templates:")
            for name in loader.list_templates():
                click.echo(f"  • {name}")
            return
        
        # Register alias
        success = alias_manager.register(alias, template_name)
        
        if not success:
            click.echo(f"\n✗ Alias '{alias}' already exists.", err=True)
            existing = alias_manager.get_template_for_alias(alias)
            click.echo(f"  Currently maps to: {existing}")
            click.echo(f"\nUnregister first:")
            click.echo(f"  workmain templates unregister {alias}")
            return
        
        click.echo(f"\n✓ Alias registered successfully!")
        click.echo(f"\n  {alias} → {template_name}")
        click.echo(f"\nUsage:")
        click.echo(f"  workmain report {alias} --send")
        click.echo(f"  workmain report {alias} --preview")
        
    except Exception as e:
        click.echo(f"\n✗ Error registering alias: {e}", err=True)


@templates.command()
@click.argument('alias')
def unregister(alias: str):
    """
    Unregister a template alias.

    Removes the shortcut name. The template itself is not affected.

    \b
    Examples:
      workmain templates unregister monthly
      workmain templates unregister security
    """
    alias_manager = get_alias_manager()
    
    try:
        # Check if alias exists
        template_name = alias_manager.get_template_for_alias(alias)
        if not template_name:
            click.echo(f"\n✗ Alias '{alias}' not found.", err=True)
            click.echo("\nRegistered aliases:")
            for alias_info in alias_manager.list_aliases():
                click.echo(f"  • {alias_info.alias} → {alias_info.template_name}")
            return
        
        # Unregister
        success = alias_manager.unregister(alias)
        
        if success:
            click.echo(f"\n✓ Alias '{alias}' unregistered.")
            click.echo(f"  Was mapped to: {template_name}")
        else:
            click.echo(f"\n✗ Failed to unregister alias.", err=True)
        
    except Exception as e:
        click.echo(f"\n✗ Error unregistering alias: {e}", err=True)


@templates.command()
@click.argument('template_name')
def show(template_name: str):
    """
    Show detailed template information.

    \b
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

    \b
    Examples:
      workmain templates validate
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
            
            is_valid, errors = validator.validate(template)
            
            if is_valid:
                click.echo(f"✓ Template '{template_name}' is valid")
            else:
                click.echo(f"✗ Template '{template_name}' has errors:", err=True)
                for error in errors:
                    click.echo(f"  • {error}", err=True)
        else:
            # Validate all templates
            template_names = loader.list_templates()
            all_valid = True
            
            for name in template_names:
                template = loader.load(name)
                if template:
                    is_valid, errors = validator.validate(template)
                    
                    if is_valid:
                        click.echo(f"✓ {name}")
                    else:
                        click.echo(f"✗ {name}:", err=True)
                        for error in errors:
                            click.echo(f"  • {error}", err=True)
                        all_valid = False
            
            click.echo()
            if all_valid:
                click.echo(f"All {len(template_names)} templates valid ✓")
            else:
                click.echo("Some templates have validation errors", err=True)
        
    except Exception as e:
        click.echo(f"Error validating templates: {e}", err=True)


@templates.command()
@click.argument('template_name')
@click.option('--date', default=None, help='Date for preview (YYYY-MM-DD)')
def preview(template_name: str, date: Optional[str]):
    """
    Preview rendered template with current data.

    Shows how the template will look when generated with AI.

    \b
    Examples:
      workmain templates preview daily_internal
      workmain templates preview weekly_client --date 2025-12-30
    """
    from workmain.database.connection import get_db

    loader = get_template_loader()

    try:
        template = loader.load(template_name)
        if not template:
            click.echo(f"Template '{template_name}' not found.", err=True)
            return

        # Parse date
        if date:
            preview_date = dt.strptime(date, '%Y-%m-%d').date()
        else:
            preview_date = dt.now().date()

        # Get database session
        db = get_db()
        session = db.get_session()
        
        try:
            # Create renderer with session
            renderer = TemplateRenderer(session)
            
            # Render template
            rendered = renderer.render(template, report_date=preview_date)
            
            click.echo(f"\nTemplate Preview: {template['name']}")
            click.echo(f"Date: {preview_date}")
            click.echo("=" * 60)
            click.echo(rendered)
            click.echo("=" * 60)
            
        finally:
            session.close()
        
    except Exception as e:
        click.echo(f"Error previewing template: {e}", err=True)


@templates.command()
@click.argument('name')
@click.option('--type', default='custom', help='Template type (internal/client/custom)')
def create(name: str, type: str):
    """
    Create a new blank template interactively.

    Prompts for template details and creates a new JSON file.

    \b
    Examples:
      workmain templates create "Monthly Executive" --type custom
      workmain templates create "Security Audit" --type client
    """
    field_manager = FieldManager()
    
    try:
        click.echo(f"\nCreating new template: {name}")
        click.echo("=" * 60)
        
        # Gather template details
        description = click.prompt("Description", default="")
        ai_provider = click.prompt(
            "AI Provider",
            type=click.Choice(['claude', 'gemini']),
            default='claude'
        )
        output_format = click.prompt(
            "Output Format",
            type=click.Choice(['markdown', 'text', 'html']),
            default='markdown'
        )
        
        # Determine recipient type
        if type == 'internal':
            recipient_type = 'internal'
        elif type == 'client':
            recipient_type = 'external'
        else:
            recipient_type = click.prompt(
                "Recipient Type",
                type=click.Choice(['internal', 'external']),
                default='internal'
            )
        
        # Create template structure
        template = {
            "name": name,
            "version": "1.0",
            "description": description,
            "recipient_type": recipient_type,
            "output_format": output_format,
            "metadata": {
                "ai_provider": ai_provider,
                "date_range": "day" if 'daily' in name.lower() else "week",
                "created_at": dt.now().isoformat(),
                "updated_at": dt.now().isoformat()
            },
            "sections": []
        }
        
        # Generate filename
        template_name = name.lower().replace(' ', '_').replace('-', '_')
        
        # Path from templates.py: workmain/cli/commands/templates.py
        # Need 4 levels up to get to project root
        project_root = Path(__file__).parent.parent.parent.parent
        templates_dir = project_root / "templates" / "reports"
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        template_path = templates_dir / f"{template_name}.json"
        
        # Save template
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        click.echo(f"\n✓ Template created: {template_path}")
        click.echo(f"\nNext steps:")
        click.echo(f"  1. Add sections: workmain templates add-section {template_name} \"Section Title\"")
        click.echo(f"  2. Validate: workmain templates validate {template_name}")
        click.echo(f"  3. Preview: workmain templates preview {template_name}")
        
    except Exception as e:
        click.echo(f"\nError creating template: {e}", err=True)


@templates.command(name='add-section')
@click.argument('template_name')
@click.argument('section_title')
def add_section(template_name: str, section_title: str):
    """
    Add a section to an existing template interactively.

    Prompts for section configuration and appends to template.

    \b
    Examples:
      workmain templates add-section monthly_executive "Summary"
      workmain templates add-section security_audit "Findings"
    """
    loader = get_template_loader()
    field_manager = FieldManager()
    
    try:
        # Load template
        template = loader.load(template_name)
        if not template:
            click.echo(f"\nTemplate '{template_name}' not found.", err=True)
            return
        
        click.echo(f"\nAdding section to: {template['name']}")
        click.echo("=" * 60)
        click.echo(f"Section Title: {section_title}")
        
        # Generate section name
        section_name = section_title.lower().replace(' ', '_').replace('-', '_')
        
        # Gather section details
        description = click.prompt("\nDescription", default="")
        
        required = click.confirm("Required section?", default=True)
        
        # Data source
        data_source = click.prompt(
            "Data Source",
            type=click.Choice(['notes', 'time_entries', 'meetings', 'tasks']),
            default='notes'
        )
        
        # Tags
        include_tags_str = click.prompt(
            "Include tags (comma-separated)",
            default="both"
        )
        include_tags = [t.strip() for t in include_tags_str.split(',') if t.strip()]
        
        exclude_tags_str = click.prompt(
            "Exclude tags (comma-separated, or leave empty)",
            default=""
        )
        exclude_tags = [t.strip() for t in exclude_tags_str.split(',') if t.strip()]
        
        # Format
        format_type = click.prompt(
            "Format",
            type=click.Choice(['bullets', 'numbered_list', 'paragraphs']),
            default='bullets'
        )
        
        # Create section
        section = {
            "name": section_name,
            "title": section_title,
            "description": description,
            "required": required,
            "data_source": data_source,
            "include_tags": include_tags,
            "format": format_type
        }
        
        if exclude_tags:
            section["exclude_tags"] = exclude_tags
        
        # Add section to template
        if 'sections' not in template:
            template['sections'] = []
        
        template['sections'].append(section)
        
        # Update metadata
        if 'metadata' in template:
            template['metadata']['updated_at'] = dt.now().isoformat()
        
        # Save updated template
        # Path from templates.py: workmain/cli/commands/templates.py
        # Need 4 levels up to get to project root
        project_root = Path(__file__).parent.parent.parent.parent
        templates_dir = project_root / "templates" / "reports"
        
        # Find template file using iterdir instead of glob (glob conflicts with Click)
        template_files = [
            f for f in templates_dir.iterdir() 
            if f.name == f"{template_name}.json"
        ]
        
        if not template_files:
            # Try with underscores
            template_files = [
                f for f in templates_dir.iterdir()
                if f.name == f"{template_name.replace('-', '_')}.json"
            ]
        
        if not template_files:
            click.echo(f"\nCould not find template file for '{template_name}'", err=True)
            return
        
        template_path = template_files[0]
        
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        click.echo(f"\n✓ Section added to {template['name']}")
        click.echo(f"Total sections: {len(template['sections'])}")
        click.echo(f"\nNext steps:")
        click.echo(f"  - Add more sections: workmain templates add-section {template_name} \"Title\"")
        click.echo(f"  - Validate: workmain templates validate {template_name}")
        click.echo(f"  - Preview: workmain templates preview {template_name}")
        
    except Exception as e:
        click.echo(f"\nError adding section: {e}", err=True)
        import traceback
        click.echo("\nFull error traceback:", err=True)
        traceback.print_exc()


# Export command group
__all__ = ['templates']