"""
WorkmAIn Template CLI Commands
Template Commands v1.2
20251224

CLI commands for template management.

Version History:
- v1.0: Initial implementation with 4 commands
- v1.1: Fixed date module shadowing bug in preview command
- v1.2: Fixed preview command to pass template_name instead of template dict to renderer
"""

import click
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import date

from workmain.templates_engine import (
    get_template_loader,
    get_template_validator,
    FieldManager,
    TemplateRenderer
)
from workmain.database.connection import get_db

console = Console()


@click.group()
def templates():
    """Template management commands."""
    pass


@templates.command()
def list():
    """
    List all available templates.
    
    Examples:
        workmain templates list
    """
    try:
        loader = get_template_loader()
        available = loader.list_templates()
        
        if not available:
            console.print("[yellow]No templates found in templates/reports/[/yellow]")
            return
        
        console.print(f"\n[bold cyan]Available Templates ({len(available)})[/bold cyan]\n")
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("Name", style="cyan", width=20)
        table.add_column("Type", style="green", width=15)
        table.add_column("Version", style="yellow", width=8)
        table.add_column("Description", style="white", width=50)
        
        for template_name in sorted(available):
            try:
                template = loader.load(template_name)
                
                table.add_row(
                    template.get("name", template_name),
                    template.get("template_type", "unknown"),
                    template.get("version", "N/A"),
                    template.get("description", "")[:47] + "..." 
                        if len(template.get("description", "")) > 50 
                        else template.get("description", "")
                )
            except Exception as e:
                table.add_row(
                    template_name,
                    "[red]ERROR[/red]",
                    "",
                    f"Failed to load: {str(e)[:40]}"
                )
        
        console.print(table)
        console.print()
        
    except Exception as e:
        console.print(f"[red]✗ Error listing templates: {e}[/red]")


@templates.command()
@click.argument('template_name')
def show(template_name: str):
    """
    Show detailed information about a template.
    
    Examples:
        workmain templates show daily_internal
        workmain templates show weekly_client
    """
    try:
        loader = get_template_loader()
        template = loader.load(template_name)
        
        if not template:
            console.print(f"[red]✗ Template '{template_name}' not found[/red]")
            return
        
        # Header
        console.print(f"\n[bold cyan]Template: {template.get('name', template_name)}[/bold cyan]")
        console.print("=" * 70)
        
        # Basic info
        console.print(f"\n[bold]Basic Information:[/bold]")
        console.print(f"  Type: {template.get('template_type', 'N/A')}")
        console.print(f"  Version: {template.get('version', 'N/A')}")
        console.print(f"  Recipient: {template.get('recipient_type', 'N/A')}")
        console.print(f"  Output Format: {template.get('output_format', 'N/A')}")
        
        if 'description' in template:
            console.print(f"\n[bold]Description:[/bold]")
            console.print(f"  {template['description']}")
        
        # Subject line
        if 'subject_line' in template:
            console.print(f"\n[bold]Subject Line:[/bold]")
            console.print(f"  {template['subject_line']}")
        
        # Sections
        sections = template.get('sections', [])
        if sections:
            console.print(f"\n[bold]Sections ({len(sections)}):[/bold]")
            
            for i, section in enumerate(sections, 1):
                console.print(f"\n  {i}. [cyan]{section.get('title', section.get('name', 'Untitled'))}[/cyan]")
                console.print(f"     Name: {section.get('name', 'N/A')}")
                console.print(f"     Required: {'Yes' if section.get('required', False) else 'No'}")
                console.print(f"     Format: {section.get('format', 'N/A')}")
                console.print(f"     AI Provider: {section.get('ai_provider', 'N/A')}")
                
                # Data sources
                if 'data_sources' in section:
                    console.print(f"     Data Sources: {', '.join(section['data_sources'])}")
                
                # Tag filter
                if 'tag_filter' in section:
                    tag_filter = section['tag_filter']
                    if 'include' in tag_filter:
                        console.print(f"     Include Tags: {', '.join(tag_filter['include'])}")
                    if 'exclude' in tag_filter:
                        console.print(f"     Exclude Tags: {', '.join(tag_filter['exclude'])}")
                
                # AI instruction (first 100 chars)
                if 'ai_instruction' in section:
                    instruction = section['ai_instruction']
                    preview = instruction[:100] + "..." if len(instruction) > 100 else instruction
                    console.print(f"     AI Instruction: {preview}")
        
        # Delivery
        if 'delivery' in template:
            delivery = template['delivery']
            console.print(f"\n[bold]Delivery:[/bold]")
            console.print(f"  Method: {delivery.get('method', 'N/A')}")
            if 'to_from_config' in delivery:
                console.print(f"  Recipients: From config ({delivery['to_from_config']})")
        
        # Metadata
        if 'metadata' in template:
            metadata = template['metadata']
            console.print(f"\n[bold]Metadata:[/bold]")
            if 'ai_provider_preference' in metadata:
                console.print(f"  Preferred AI: {metadata['ai_provider_preference']}")
            if 'based_on_user_examples' in metadata:
                console.print(f"  Based on user examples: {metadata['based_on_user_examples']}")
        
        console.print("\n" + "=" * 70 + "\n")
        
    except FileNotFoundError:
        console.print(f"[red]✗ Template '{template_name}' not found[/red]")
    except Exception as e:
        console.print(f"[red]✗ Error loading template: {e}[/red]")


@templates.command()
@click.argument('template_name', required=False)
def validate(template_name: str = None):
    """
    Validate template structure.
    
    Examples:
        workmain templates validate                  # Validate all
        workmain templates validate daily_internal   # Validate one
    """
    try:
        loader = get_template_loader()
        validator = get_template_validator()
        
        # Get templates to validate
        if template_name:
            templates_to_check = [template_name]
        else:
            templates_to_check = loader.list_templates()
        
        if not templates_to_check:
            console.print("[yellow]No templates found to validate[/yellow]")
            return
        
        console.print(f"\n[bold cyan]Validating {len(templates_to_check)} template(s)[/bold cyan]\n")
        
        all_valid = True
        
        for tpl_name in templates_to_check:
            try:
                # Load template
                template = loader.load(tpl_name)
                
                # Validate
                errors = validator.validate(template)
                
                if not errors:
                    console.print(f"[green]✓ {tpl_name}[/green] - Valid")
                else:
                    all_valid = False
                    console.print(f"[red]✗ {tpl_name}[/red] - {len(errors)} error(s):")
                    for error in errors:
                        console.print(f"    - {error}")
                    console.print()
                
            except FileNotFoundError:
                all_valid = False
                console.print(f"[red]✗ {tpl_name}[/red] - File not found")
            except Exception as e:
                all_valid = False
                console.print(f"[red]✗ {tpl_name}[/red] - Error: {e}")
        
        console.print()
        
        if all_valid:
            console.print("[bold green]✓ All templates valid![/bold green]\n")
        else:
            console.print("[bold red]✗ Some templates have errors[/bold red]\n")
        
    except Exception as e:
        console.print(f"[red]✗ Validation error: {e}[/red]")


@templates.command()
@click.argument('template_name')
@click.option('--date', '-d', help='Report date (YYYY-MM-DD, default: today)')
def preview(template_name: str, date: str = None):
    """
    Preview template with actual data.
    
    Examples:
        workmain templates preview daily_internal
        workmain templates preview weekly_client --date 2025-12-20
    """
    try:
        # Parse date
        from datetime import datetime, date as date_module
        if date:
            try:
                report_date = datetime.strptime(date, '%Y-%m-%d').date()
            except ValueError:
                console.print(f"[red]✗ Invalid date format. Use YYYY-MM-DD[/red]")
                return
        else:
            report_date = date_module.today()
        
        # Load template to check it exists
        loader = get_template_loader()
        template = loader.load(template_name)
        
        if not template:
            console.print(f"[red]✗ Template '{template_name}' not found[/red]")
            return
        
        # Get database session
        db = get_db()
        session = db.get_session()
        
        try:
            # Initialize renderer
            renderer = TemplateRenderer(session)
            
            # Render template (pass template_name, not template dict)
            output, metadata = renderer.render(template_name, report_date)
            
            # Display
            console.print(f"\n{'='*70}")
            console.print(f"[bold cyan]TEMPLATE PREVIEW: {template.get('name', template_name)}[/bold cyan]")
            console.print('='*70)
            
            # Show metadata
            console.print(f"\n[bold]Report Date:[/bold] {report_date}")
            
            if template.get('template_type') == 'weekly_client':
                console.print(f"[bold]Date Range:[/bold] {metadata.get('start_date')} to {metadata.get('end_date')}")
            
            if 'subject_line' in template:
                # Build variables
                variables = loader.build_variables(report_date, template.get('template_type'))
                subject = loader.substitute_variables(template['subject_line'], variables)
                console.print(f"[bold]Subject:[/bold] {subject}")
            
            console.print("\n" + "-"*70 + "\n")
            
            # Show output
            console.print("[bold]OUTPUT:[/bold]\n")
            console.print(output)
            
            console.print("\n" + "-"*70 + "\n")
            
            # Show data summary
            console.print("[bold]DATA SUMMARY:[/bold]\n")
            
            for section_name, section_data in metadata.get('section_data', {}).items():
                console.print(f"  [cyan]{section_name}:[/cyan]")
                
                summary = section_data.get('summary', {})
                console.print(f"    Notes: {summary.get('note_count', 0)}")
                console.print(f"    Time entries: {summary.get('time_entry_count', 0)}")
                console.print(f"    Total hours: {summary.get('total_hours', 0.0):.2f}h")
                console.print()
            
            console.print('='*70)
            console.print("\n[dim]Note: This preview shows raw data formatting.[/dim]")
            console.print("[dim]      AI generation will be added in Phase 4.[/dim]\n")
            
        finally:
            session.close()
        
    except FileNotFoundError:
        console.print(f"[red]✗ Template '{template_name}' not found[/red]")
    except Exception as e:
        console.print(f"[red]✗ Preview error: {e}[/red]")
        import traceback
        traceback.print_exc()


# Export command group
__all__ = ['templates']