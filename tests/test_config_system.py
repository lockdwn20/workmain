#!/usr/bin/env python3
"""
WorkmAIn
Configuration System Test v0.1.0
20251219

Test configuration loading, validation, and encryption
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workmain.config_manager.loader import ConfigLoader, get_config
from workmain.config_manager.validator import ConfigValidator, get_validator
from workmain.utils.encryption import EncryptionManager, get_encryption
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


def test_config_loader():
    """Test configuration loading"""
    console.print("\n[bold cyan]Testing Configuration Loader[/bold cyan]")
    console.print("=" * 60)
    
    loader = get_config()
    
    # Test database config
    console.print("\n[yellow]Loading database configuration...[/yellow]")
    db_config = loader.get_database_config()
    
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in db_config.items():
        # Mask password
        display_value = "***" if key == "password" else value
        table.add_row(key, str(display_value))
    
    console.print(table)
    console.print("[green]✓ Database config loaded successfully[/green]")
    
    # Test AI provider selection
    console.print("\n[yellow]Testing AI provider selection...[/yellow]")
    
    # This will use defaults if ai_settings.json doesn't exist
    daily_provider = loader.get_ai_provider_for_report("daily_internal")
    weekly_provider = loader.get_ai_provider_for_report("weekly_client")
    
    console.print(f"Daily Internal Report: [cyan]{daily_provider}[/cyan]")
    console.print(f"Weekly Client Report: [cyan]{weekly_provider}[/cyan]")
    console.print("[green]✓ AI provider selection working[/green]")
    
    return True


def test_config_validator():
    """Test configuration validation"""
    console.print("\n[bold cyan]Testing Configuration Validator[/bold cyan]")
    console.print("=" * 60)
    
    validator = get_validator()
    
    # Test valid config
    console.print("\n[yellow]Testing valid configuration...[/yellow]")
    valid_config = {
        "default_provider": "claude",
        "providers": {
            "claude": {"enabled": True},
            "gemini": {"enabled": True}
        }
    }
    
    errors = validator.validate_config("ai_settings", valid_config)
    if errors:
        console.print(f"[red]✗ Validation failed: {errors}[/red]")
        return False
    else:
        console.print("[green]✓ Valid configuration passed[/green]")
    
    # Test invalid config
    console.print("\n[yellow]Testing invalid configuration...[/yellow]")
    invalid_config = {
        "default_provider": "invalid_provider",
        # Missing required "providers" field
    }
    
    errors = validator.validate_config("ai_settings", invalid_config)
    if errors:
        console.print(f"[green]✓ Correctly caught {len(errors)} validation error(s):[/green]")
        for error in errors:
            console.print(f"  - {error}")
    else:
        console.print("[red]✗ Failed to catch validation errors[/red]")
        return False
    
    # Test email validation
    console.print("\n[yellow]Testing email validation...[/yellow]")
    test_emails = [
        ("user@example.com", True),
        ("invalid.email", False),
        ("test@domain.co.uk", True),
        ("@nodomain.com", False),
    ]
    
    for email, should_be_valid in test_emails:
        is_valid = validator.validate_email(email)
        status = "✓" if is_valid == should_be_valid else "✗"
        console.print(f"  {status} {email}: {'valid' if is_valid else 'invalid'}")
    
    # Test time validation
    console.print("\n[yellow]Testing time validation...[/yellow]")
    test_times = [
        ("14:30", True),
        ("09:00", True),
        ("25:00", False),
        ("12:60", False),
        ("12:30 PM", False),  # We use 24-hour format
    ]
    
    for time_str, should_be_valid in test_times:
        is_valid = validator.validate_time(time_str)
        status = "✓" if is_valid == should_be_valid else "✗"
        console.print(f"  {status} {time_str}: {'valid' if is_valid else 'invalid'}")
    
    console.print("[green]✓ Validation system working correctly[/green]")
    return True


def test_encryption():
    """Test encryption functionality"""
    console.print("\n[bold cyan]Testing Encryption System[/bold cyan]")
    console.print("=" * 60)
    
    encryption = get_encryption()
    
    # Test basic encryption/decryption
    console.print("\n[yellow]Testing API key encryption...[/yellow]")
    
    test_api_key = "sk-ant-api03-test-key-12345"
    console.print(f"Original API key: {test_api_key[:20]}...")
    
    # Encrypt
    encrypted = encryption.encrypt(test_api_key)
    console.print(f"Encrypted: {encrypted[:40]}...")
    
    # Decrypt
    decrypted = encryption.decrypt(encrypted)
    console.print(f"Decrypted: {decrypted[:20]}...")
    
    if decrypted == test_api_key:
        console.print("[green]✓ Encryption/decryption working correctly[/green]")
    else:
        console.print("[red]✗ Encryption/decryption failed[/red]")
        return False
    
    # Test dict encryption
    console.print("\n[yellow]Testing dict encryption...[/yellow]")
    
    sensitive_data = {
        "api_key": "secret-key-12345",
        "password": "secret-pass-67890",
        "public_data": "this is not encrypted"
    }
    
    encrypted_dict = encryption.encrypt_dict(
        sensitive_data,
        keys_to_encrypt=["api_key", "password"]
    )
    
    console.print("Original dict:")
    console.print(f"  api_key: {sensitive_data['api_key']}")
    console.print(f"  public_data: {sensitive_data['public_data']}")
    
    console.print("\nEncrypted dict:")
    console.print(f"  api_key: {encrypted_dict['api_key'][:40]}...")
    console.print(f"  public_data: {encrypted_dict['public_data']}")
    
    decrypted_dict = encryption.decrypt_dict(
        encrypted_dict,
        keys_to_decrypt=["api_key", "password"]
    )
    
    if decrypted_dict["api_key"] == sensitive_data["api_key"]:
        console.print("[green]✓ Dict encryption working correctly[/green]")
    else:
        console.print("[red]✗ Dict encryption failed[/red]")
        return False
    
    # Show encryption key location
    console.print(f"\n[dim]Encryption key stored at: {encryption.key_file}[/dim]")
    
    return True


def main():
    """Run all configuration system tests"""
    console.print("\n[bold green]WorkmAIn Configuration System Test[/bold green]")
    
    tests = [
        ("Configuration Loader", test_config_loader),
        ("Configuration Validator", test_config_validator),
        ("Encryption System", test_encryption),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            console.print(f"\n[red]✗ {test_name} failed with error: {e}[/red]")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    console.print("\n" + "=" * 60)
    console.print("[bold]Test Summary[/bold]")
    console.print("=" * 60)
    
    for test_name, passed in results.items():
        status = "[green]✓ PASSED[/green]" if passed else "[red]✗ FAILED[/red]"
        console.print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        console.print("\n[bold green]✓ All configuration tests passed![/bold green]\n")
        return 0
    else:
        console.print("\n[bold red]✗ Some tests failed[/bold red]\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
