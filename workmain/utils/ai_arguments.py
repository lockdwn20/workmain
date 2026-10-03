"""
Checks a provider or report-type argument against the AI configuration.

A command's provider or report-type argument is accepted only if it names an
entry in config/ai_settings.json. The sets come from ProviderManager, so no
command keeps a list of its own. A rejected name prints one error listing the
valid names and exits 1; a configuration that will not load exits 1 with the
load error.
"""

import sys
from typing import List, Optional

from rich.console import Console
from rich.markup import escape

from workmain.ai.base_provider import ConfigurationError, ProviderType
from workmain.ai.provider_manager import eligible_provider_names, get_provider_manager

console = Console()


def _fail(message: str) -> None:
    """Print message as an error and exit 1."""
    console.print(f"[red]Error:[/red] {escape(message)}", soft_wrap=True)
    sys.exit(1)


def _manager():
    """Return the provider manager, or exit 1 with the load error."""
    try:
        return get_provider_manager()
    except ConfigurationError as e:
        _fail(str(e))


def require_provider(
    name: Optional[str], valid: Optional[List[str]] = None
) -> Optional[ProviderType]:
    """Return the ProviderType for a configured provider name; exit 1 otherwise.

    Args:
        name: Argument as typed; matched case-insensitively. Falsy returns None.
        valid: Names to accept. Defaults to the providers configured under
            'providers' in ai_settings.json, enabled or not.

    Returns:
        The ProviderType, or None when name is falsy.
    """
    if not name:
        return None
    if valid is None:
        valid = _manager().get_configured_provider_names()
    known = {p.value for p in ProviderType}
    usable = [v for v in valid if v in known]
    lowered = name.lower()
    if lowered not in usable:
        _fail(f"Unknown provider '{name}'. Valid providers: {', '.join(usable)}")
    return ProviderType(lowered)


def require_eligible_provider(
    name: Optional[str], call_type: str, settings: Optional[dict] = None
) -> Optional[ProviderType]:
    """Return the ProviderType for a provider that can serve call_type; exit 1 otherwise.

    Args:
        name: Argument as typed. Falsy returns None before anything is loaded.
            An unconfigured name fails as in require_provider.
        call_type: A report_types or application_functions key.
        settings: A parsed ai_settings.json to decide eligibility from. Defaults
            to the provider manager's loaded configuration.

    Returns:
        The ProviderType, or None when name is falsy.
    """
    if not name:
        return None
    configured = (
        list(settings.get('providers', {})) if settings is not None else None
    )
    provider = require_provider(name, valid=configured)
    try:
        if settings is not None:
            eligible = eligible_provider_names(settings, call_type)
        else:
            eligible = _manager().get_eligible_provider_names(call_type)
    except ConfigurationError as e:
        _fail(str(e))
    if provider.value not in eligible:
        if settings is not None:
            entry = settings.get('report_types', {}).get(call_type) \
                or settings.get('application_functions', {}).get(call_type)
            source = entry['instructions']
        else:
            source = _manager().get_report_config(call_type).instructions.value
        _fail(
            f"Provider '{provider.value}' cannot serve '{call_type}' "
            f"({source} instructions). Providers that can: "
            f"{', '.join(eligible) or 'none'}"
        )
    return provider


def require_report_type(
    name: Optional[str], valid: Optional[List[str]] = None
) -> Optional[str]:
    """Return name if it is a configured report type; exit 1 otherwise.

    Args:
        name: Argument as typed; matched exactly. Falsy returns None.
        valid: Names to accept. Defaults to the keys under 'report_types' in
            ai_settings.json.

    Returns:
        The report type, or None when name is falsy.
    """
    if not name:
        return None
    if valid is None:
        valid = _manager().get_report_type_names()
    if name not in valid:
        _fail(f"Unknown report type '{name}'. Valid report types: {', '.join(valid)}")
    return name
