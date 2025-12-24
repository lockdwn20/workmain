#!/usr/bin/env python3
"""
WorkmAIn Template CLI Demo
Template CLI Demo v1.0
20251224

Demonstrates template CLI commands.
"""

import subprocess
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_header(title: str):
    """Print formatted section header."""
    print(f"\n{'='*70}")
    print(f"{title}")
    print('='*70)


def run_command(cmd: str, description: str = ""):
    """Run a CLI command and show output."""
    if description:
        print(f"\n[{description}]")
    print(f"$ {cmd}\n")
    
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return result.returncode == 0


def main():
    """Run template CLI demo."""
    print("\nWorkmAIn Template CLI Demo")
    print("=" * 70)
    
    # Check if workmain is available
    result = subprocess.run(
        "workmain --version",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("✗ 'workmain' command not found")
        print("  Make sure you've installed the CLI and activated the virtual environment")
        return 1
    
    print(f"Using: {result.stdout.strip()}")
    
    # Demo commands
    print_header("1. List Available Templates")
    run_command(
        "workmain templates list",
        "Show all report templates"
    )
    
    print_header("2. Show Template Details (Daily Internal)")
    run_command(
        "workmain templates show daily_internal",
        "Display daily internal report structure"
    )
    
    print_header("3. Show Template Details (Weekly Client)")
    run_command(
        "workmain templates show weekly_client",
        "Display weekly client report structure"
    )
    
    print_header("4. Validate All Templates")
    run_command(
        "workmain templates validate",
        "Check template structure and schema"
    )
    
    print_header("5. Validate Single Template")
    run_command(
        "workmain templates validate daily_internal",
        "Validate specific template"
    )
    
    print_header("6. Preview Daily Internal Report")
    run_command(
        "workmain templates preview daily_internal",
        "Preview with today's data"
    )
    
    print_header("7. Preview Weekly Client Report")
    run_command(
        "workmain templates preview weekly_client",
        "Preview with this week's data"
    )
    
    print_header("Demo Complete!")
    print("\nAll template CLI commands demonstrated.")
    print("\nAvailable commands:")
    print("  • workmain templates list                    - List all templates")
    print("  • workmain templates show <name>             - Show template details")
    print("  • workmain templates validate [name]         - Validate templates")
    print("  • workmain templates preview <name> [--date] - Preview with data")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
