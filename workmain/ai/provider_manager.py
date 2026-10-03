"""
Manages AI providers with intelligent fallback and selection.

Provides an N-provider extensible registry,
per-report-type provider selection from ai_settings.json, configurable
manual or automatic fallback, provider health monitoring, notification on
fallback, and disabled provider tracking (no connectivity check runs for a
disabled provider).
"""

import json
import os
from typing import Dict, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass

from workmain.ai.base_provider import (
    BaseProvider,
    ProviderType,
    ProviderStatus,
    ProviderUnavailableError,
    GenerationRequest,
    GenerationResponse,
    ProviderError,
    RateLimitError,
    ConfigurationError,
)
from workmain.ai.providers import PROVIDER_REGISTRY
from workmain.config_manager.loader import ConfigLoader


class FallbackMode(Enum):
    """Fallback behavior modes."""
    AUTO = "auto"
    MANUAL = "manual"


class InstructionSource(Enum):
    """How a call type's instructions reach the model; meanings are in docs/AI_SETTINGS_GUIDE.md."""
    SYSTEM_PROMPT = "system_prompt"
    MODELFILE = "modelfile"
    RAW_PROMPT = "raw_prompt"


@dataclass
class ReportTypeConfig:
    """
    Configuration for a specific call type (a report_types or application_functions entry).

    Attributes:
        report_type: Call type name
        primary_provider: Primary provider to use
        max_tokens: Total output ceiling (thinking plus answer) for this call type
        instructions: How this call's instructions reach the model
        fallback_provider: Fallback provider if primary fails
        fallback_mode: AUTO or MANUAL fallback
        max_cost_per_report: Optional cost limit
    """
    report_type: str
    primary_provider: ProviderType
    max_tokens: int
    instructions: InstructionSource
    fallback_provider: Optional[ProviderType] = None
    fallback_mode: FallbackMode = FallbackMode.AUTO
    max_cost_per_report: Optional[float] = None


class ProviderManager:
    """
    Manage AI providers with intelligent selection and fallback.

    Instantiates providers from PROVIDER_REGISTRY based on ai_settings.json.
    Disabled providers (enabled: false) are tracked but never instantiated
    or connectivity-checked.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize provider manager.

        Args:
            config_path: Path to ai_settings.json config file
        """
        self.config_path = config_path
        self._providers: Dict[str, BaseProvider] = {}   # name → instantiated provider
        self._disabled: set = set()                      # names of disabled providers
        self._disabled_reasons: Dict[str, str] = {}      # name → construction failure reason
        self._all_configs: Dict[str, dict] = {}          # name → config dict (all providers)
        self._settings: dict = {}                        # full ai_settings.json
        self._call_configs: Dict[str, ReportTypeConfig] = {}
        self._fallback_notifications: List[str] = []

        self._load_config()

    def get_provider(self, name: str) -> BaseProvider:
        """
        Get provider instance by name.

        Args:
            name: Provider name (e.g. 'claude')

        Returns:
            Provider instance

        Raises:
            ProviderUnavailableError: If provider is disabled or not registered
        """
        if name in self._disabled_reasons:
            raise ProviderUnavailableError(
                f"Provider '{name}' is unavailable: {self._disabled_reasons[name]}"
            )
        if name in self._disabled:
            raise ProviderUnavailableError(
                f"Provider '{name}' is disabled. "
                f"Set 'enabled: true' in config/ai_settings.json to enable it."
            )
        if name not in self._providers:
            raise ProviderUnavailableError(
                f"Provider '{name}' is not configured. "
                f"Add it under 'providers' in config/ai_settings.json."
            )
        return self._providers[name]

    def get_all_provider_configs(self) -> Dict[str, dict]:
        """Returns config dict for ALL providers including disabled.
        Used by providers list to display complete provider table."""
        return self._all_configs

    def is_disabled(self, name: str) -> bool:
        """Returns True if the named provider is disabled in config."""
        return name in self._disabled

    def get_max_tokens(self, call_type: str) -> int:
        """
        Return the configured max_tokens cap for a call type.

        Reads the call type's entry in report_types or application_functions.
        No default, no fallback — a call type absent from both raises.

        Args:
            call_type: A report_types key or an application_functions key.

        Returns:
            The configured max_tokens cap.

        Raises:
            ConfigurationError: If call_type is not configured in either block.
        """
        if call_type in self._call_configs:
            return self._call_configs[call_type].max_tokens
        raise ConfigurationError(
            f"No max_tokens configured for call type '{call_type}'. "
            f"Add it to 'report_types' or 'application_functions' in "
            f"config/ai_settings.json."
        )

    def generate(
        self,
        request: GenerationRequest,
        report_type: Optional[str] = None,
        provider_override: Optional[ProviderType] = None
    ) -> Tuple[GenerationResponse, bool]:
        """
        Generate content using appropriate provider.

        Args:
            request: Generation request
            report_type: Call type (for provider selection); always required
            provider_override: Optional provider override; must accept the
                call type's instructions

        Returns:
            Tuple of (GenerationResponse, fallback_used)

        Raises:
            ProviderError: If generation fails with all providers
            ConfigurationError: If report_type is missing or not configured, or
                provider_override cannot serve it. Raised before any provider
                is called.
        """
        if report_type is None:
            raise ConfigurationError("generate() requires a report_type.")
        config = self._require_report_config(report_type)
        if provider_override:
            if provider_override.value not in self.get_eligible_provider_names(report_type):
                raise ConfigurationError(
                    f"Provider '{provider_override.value}' cannot serve call type "
                    f"'{report_type}' ({config.instructions.value}); providers that can: "
                    f"{', '.join(self.get_eligible_provider_names(report_type)) or 'none'}."
                )
            primary = provider_override
            fallback = None
            fallback_mode = FallbackMode.MANUAL
        else:
            primary = config.primary_provider
            fallback = config.fallback_provider
            fallback_mode = config.fallback_mode

        try:
            provider = self.get_provider(primary.value)
            response = provider.generate(request)
            return response, False

        except (ProviderError, RateLimitError) as e:
            if not fallback:
                raise ProviderError(
                    f"Primary provider {primary.value} failed and no fallback configured"
                ) from e

            if fallback_mode == FallbackMode.MANUAL:
                raise ProviderError(
                    f"Primary provider {primary.value} failed. "
                    f"Fallback to {fallback.value} available but manual mode enabled. "
                    f"Use --provider {fallback.value} to retry."
                ) from e

            try:
                fallback_provider = self.get_provider(fallback.value)
                notification = (
                    f"⚠️  Primary provider {primary.value} failed. "
                    f"Automatically falling back to {fallback.value}. "
                    f"Reason: {str(e)}"
                )
                self._fallback_notifications.append(notification)

                response = fallback_provider.generate(request)
                return response, True

            except (ProviderError, RateLimitError) as fallback_error:
                raise ProviderError(
                    f"Both providers failed. "
                    f"Primary ({primary.value}): {str(e)}. "
                    f"Fallback ({fallback.value}): {str(fallback_error)}"
                ) from fallback_error

    def get_provider_for_report(self, report_type: str) -> ProviderType:
        """
        Get primary provider for a report type.

        Args:
            report_type: Report type name

        Returns:
            Primary provider type

        Raises:
            ConfigurationError: If report_type has no report_types entry.
        """
        return self._require_report_config(report_type).primary_provider

    def _require_report_config(self, report_type: str) -> ReportTypeConfig:
        """Return the entry for call type report_type, or raise."""
        if report_type not in self._call_configs:
            raise ConfigurationError(_no_routing_message(report_type))
        return self._call_configs[report_type]

    def get_configured_provider_names(self) -> List[str]:
        """Return every name under 'providers', enabled or not, in config order."""
        return configured_provider_names(self._settings)

    def get_report_type_names(self) -> List[str]:
        """Return the configured report-type names in config order."""
        return report_type_names(self._settings)

    def get_eligible_provider_names(self, call_type: str) -> List[str]:
        """Return the providers that accept call_type's instructions, in config order."""
        return eligible_provider_names(self._settings, call_type)

    def get_fallback_notifications(self) -> List[str]:
        """Get list of fallback notifications."""
        return self._fallback_notifications.copy()

    def clear_fallback_notifications(self):
        """Clear fallback notification history."""
        self._fallback_notifications.clear()

    def get_report_config(self, report_type: str) -> Optional[ReportTypeConfig]:
        """
        Get configuration for a report type.

        Args:
            report_type: Report type name

        Returns:
            Report type configuration or None
        """
        return self._call_configs.get(report_type)

    def estimate_cost(
        self,
        report_type: str,
        prompt_tokens: int,
        completion_tokens: int,
        provider_override: Optional[ProviderType] = None
    ) -> float:
        """
        Estimate cost for a report generation.

        Args:
            report_type: Type of report
            prompt_tokens: Estimated prompt tokens
            completion_tokens: Estimated completion tokens
            provider_override: Price at this provider instead of the report
                type's primary provider

        Returns:
            Estimated cost in USD
        """
        provider_type = provider_override or self.get_provider_for_report(report_type)
        provider = self.get_provider(provider_type.value)
        return provider.estimate_cost(prompt_tokens, completion_tokens)

    def _load_provider_policy(self, name: str, cls: type) -> dict:
        """Load and validate a provider's request payload policy.

        Reads config/providers/<name>/settings.json through ConfigLoader and
        checks it against the provider class's REQUIRED_POLICY_KEYS. An absent
        file, unparseable JSON, or a missing required key each raises
        ConfigurationError naming the file — the failure must reach the caller
        rather than being absorbed into _disabled, so a payload typo cannot
        silently reproduce the request shape this policy exists to fix.

        Args:
            name: Provider name (e.g. 'claude').
            cls: Provider class from PROVIDER_REGISTRY.

        Returns:
            The loaded policy dict.

        Raises:
            ConfigurationError: If the policy is absent, unparseable, or
                missing a key the provider requires.
        """
        config_name = f"providers/{name}/settings"
        rel_path = f"config/{config_name}.json"
        try:
            policy = ConfigLoader().load(config_name)
        except FileNotFoundError as e:
            raise ConfigurationError(
                f"Provider '{name}' payload policy file is missing: {rel_path}"
            ) from e
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Provider '{name}' payload policy file is not valid JSON: {rel_path} ({e})"
            ) from e

        missing = cls.missing_policy_keys(policy or {})
        if missing:
            raise ConfigurationError(
                f"Provider '{name}' payload policy file {rel_path} is missing "
                f"required key(s): {', '.join(sorted(missing))}"
            )
        return policy or {}

    def _load_config(self):
        """Load provider and report-type configuration from ai_settings.json.

        Instantiates enabled providers from PROVIDER_REGISTRY.
        Tracks disabled providers in _disabled (no connectivity check).
        """
        from pathlib import Path

        config_file = self.config_path or str(
            Path(__file__).parent.parent.parent / 'config' / 'ai_settings.json'
        )

        if not Path(config_file).exists():
            return

        try:
            with open(config_file, 'r') as f:
                self._settings = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"config/ai_settings.json is not valid JSON: {config_file} ({e})"
            ) from e

        # Instantiate providers from registry
        for name, provider_cfg in self._settings.get('providers', {}).items():
            self._parse_provider_name(name, f"providers.{name}")
            cls = PROVIDER_REGISTRY.get(name)
            if cls is None:
                raise ConfigurationError(
                    f"'providers.{name}' has no provider class in workmain/ai/providers/."
                )
            self._all_configs[name] = provider_cfg
            if not provider_cfg.get('enabled', True):
                self._disabled.add(name)
                continue
            # Load the payload policy BEFORE construction, so an unusable
            # policy raises out of here rather than being absorbed into
            # _disabled by the blanket except below.
            policy = self._load_provider_policy(name, cls)
            try:
                instance = cls(provider_cfg, policy)
                self._providers[name] = instance
            except Exception as exc:
                # Provider instantiation failed (e.g. missing API key in env).
                # Mark as disabled so callers get a clear error rather than
                # an unhandled exception at import time; keep the reason so
                # get_provider can report it.
                self._disabled.add(name)
                self._disabled_reasons[name] = str(exc)

        report_types_cfg = self._settings.get('report_types', {})
        application_functions_cfg = self._settings.get('application_functions', {})

        overlap = set(report_types_cfg) & set(application_functions_cfg)
        if overlap:
            raise ConfigurationError(
                f"Call type(s) {sorted(overlap)} appear in both 'report_types' and "
                f"'application_functions' in config/ai_settings.json — a call type "
                f"may be declared in only one block."
            )

        for name, provider_cfg in self._settings.get('providers', {}).items():
            self._require_accepts(provider_cfg, f"providers.{name}.accepts")

        for block, entries in (
            ('report_types', report_types_cfg),
            ('application_functions', application_functions_cfg),
        ):
            for call_type, cfg in entries.items():
                self._call_configs[call_type] = self._parse_call_config(
                    block, call_type, cfg
                )

    def _parse_call_config(self, block: str, call_type: str, cfg) -> ReportTypeConfig:
        """Parse one report_types or application_functions entry; refuse an ineligible route."""
        key_prefix = f"{block}.{call_type}"
        if not isinstance(cfg, dict):
            raise ConfigurationError(
                f"'{key_prefix}' must be an object in config/ai_settings.json."
            )
        instructions = self._parse_instructions(
            cfg.get('instructions'), f"{key_prefix}.instructions"
        )
        primary_name = cfg.get('primary_provider')
        if primary_name is None:
            raise ConfigurationError(
                f"'{key_prefix}.primary_provider' is required in "
                f"config/ai_settings.json."
            )
        primary = self._parse_provider_name(
            primary_name, f"{key_prefix}.primary_provider"
        )
        fallback_name = cfg.get('fallback_provider')
        fallback = (
            None if fallback_name is None
            else self._parse_provider_name(
                fallback_name, f"{key_prefix}.fallback_provider"
            )
        )
        fb_mode = {
            'auto': FallbackMode.AUTO,
            'manual': FallbackMode.MANUAL,
        }.get(cfg.get('fallback_mode', 'auto'), FallbackMode.AUTO)
        max_tokens = self._require_positive_int(
            cfg.get('max_tokens'), f"{key_prefix}.max_tokens"
        )

        providers_cfg = self._settings.get('providers', {})
        eligible = eligible_provider_names(self._settings, call_type)
        for key, chosen in (
            ('primary_provider', primary),
            ('fallback_provider', fallback),
        ):
            if chosen is None:
                continue
            if chosen.value not in providers_cfg:
                raise ConfigurationError(
                    f"'{key_prefix}.{key}' names provider '{chosen.value}', which has "
                    f"no 'providers.{chosen.value}' entry in config/ai_settings.json."
                )
            if chosen.value not in eligible:
                raise ConfigurationError(
                    f"'{key_prefix}.{key}' is '{chosen.value}', which does not accept "
                    f"'{instructions.value}' instructions; providers that do: "
                    f"{', '.join(eligible) or 'none'}."
                )

        return ReportTypeConfig(
            report_type=call_type,
            primary_provider=primary,
            max_tokens=max_tokens,
            instructions=instructions,
            fallback_provider=fallback,
            fallback_mode=fb_mode,
            max_cost_per_report=cfg.get('max_cost_per_report', 1.0),
        )

    @staticmethod
    def _parse_instructions(value, key_name: str) -> InstructionSource:
        """Return the InstructionSource for value; else raise ConfigurationError naming key_name."""
        try:
            return InstructionSource(value)
        except ValueError:
            valid = ', '.join(i.value for i in InstructionSource)
            raise ConfigurationError(
                f"'{key_name}' is {value!r}; it is required and must be one of "
                f"({valid}) in config/ai_settings.json."
            ) from None

    @staticmethod
    def _require_accepts(provider_cfg, key_name: str) -> None:
        """Raise ConfigurationError unless provider_cfg['accepts'] is a non-empty list of InstructionSource values."""
        valid = [i.value for i in InstructionSource]
        accepts = provider_cfg.get('accepts') if isinstance(provider_cfg, dict) else None
        if (
            not isinstance(accepts, list)
            or not accepts
            or any(a not in valid for a in accepts)
        ):
            raise ConfigurationError(
                f"'{key_name}' is required and must be a non-empty list of "
                f"({', '.join(valid)}) in config/ai_settings.json."
            )

    @staticmethod
    def _parse_provider_name(value, key_name: str) -> ProviderType:
        """Return the ProviderType for value; else raise ConfigurationError naming key_name (DR2)."""
        try:
            return ProviderType(value)
        except ValueError:
            valid = ', '.join(p.value for p in ProviderType)
            raise ConfigurationError(
                f"'{key_name}' is '{value}', which is not a provider name "
                f"({valid}) in config/ai_settings.json."
            ) from None

    @staticmethod
    def _require_positive_int(value, key_name: str) -> int:
        """Return value if it is a positive int; else raise ConfigurationError naming key_name.

        Booleans are excluded — bool is a subclass of int in Python and a
        stray `true`/`false` must not silently pass as 1/0 (DR3).
        """
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ConfigurationError(
                f"'{key_name}' must be a positive integer in config/ai_settings.json."
            )
        return value


# Singleton instance
_provider_manager_instance: Optional[ProviderManager] = None


def configured_provider_names(settings: dict) -> List[str]:
    """Return the keys under 'providers' in settings, enabled or not, in config order."""
    return list(settings.get('providers', {}))


def report_type_names(settings: dict) -> List[str]:
    """Return the keys under 'report_types' in settings, in config order."""
    return list(settings.get('report_types', {}))


def _no_routing_message(call_type: str) -> str:
    return (
        f"No routing configured for call type '{call_type}'. "
        f"Add 'report_types.{call_type}' or 'application_functions.{call_type}' "
        f"to config/ai_settings.json."
    )


def eligible_provider_names(settings: dict, call_type: str) -> List[str]:
    """Return, in config order, the providers whose 'accepts' holds call_type's 'instructions'.

    Raises:
        ConfigurationError: If call_type is in neither block, or its entry has no 'instructions'.
    """
    for block in ('report_types', 'application_functions'):
        entry = settings.get(block, {}).get(call_type)
        if entry is not None:
            instructions = entry.get('instructions') if isinstance(entry, dict) else None
            if instructions is None:
                raise ConfigurationError(
                    f"'{block}.{call_type}.instructions' is required in "
                    f"config/ai_settings.json."
                )
            return [
                name for name, cfg in settings.get('providers', {}).items()
                if isinstance(cfg.get('accepts'), list) and instructions in cfg['accepts']
            ]
    raise ConfigurationError(_no_routing_message(call_type))


def get_provider_manager(config_path: Optional[str] = None) -> ProviderManager:
    """
    Get singleton instance of ProviderManager.

    Args:
        config_path: Optional path to ai_settings.json

    Returns:
        ProviderManager singleton instance
    """
    global _provider_manager_instance
    if _provider_manager_instance is None:
        _provider_manager_instance = ProviderManager(config_path)
    return _provider_manager_instance
