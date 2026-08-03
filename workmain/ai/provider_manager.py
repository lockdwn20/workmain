"""
Manages AI providers with intelligent fallback and selection.

Features:
- N-provider extensible registry (claude, gemini, ollama, ...)
- Per-report-type provider selection from ai_settings.json
- Configurable fallback (manual/automatic)
- Provider health monitoring
- Notification on fallback
- Disabled provider tracking (no connectivity check for disabled providers)
"""

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
    RateLimitError
)
from workmain.ai.providers import PROVIDER_REGISTRY


class FallbackMode(Enum):
    """Fallback behavior modes."""
    AUTO = "auto"
    MANUAL = "manual"


@dataclass
class ReportTypeConfig:
    """
    Configuration for a specific report type.

    Attributes:
        report_type: Type of report (daily_internal, weekly_client)
        primary_provider: Primary provider to use
        fallback_provider: Fallback provider if primary fails
        fallback_mode: AUTO or MANUAL fallback
        max_cost_per_report: Optional cost limit
    """
    report_type: str
    primary_provider: ProviderType
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
        self._all_configs: Dict[str, dict] = {}          # name → config dict (all providers)
        self._settings: dict = {}                        # full ai_settings.json
        self._report_configs: Dict[str, ReportTypeConfig] = {}
        self._fallback_notifications: List[str] = []

        self._load_config()

    def get_provider(self, name: str) -> BaseProvider:
        """
        Get provider instance by name.

        Args:
            name: Provider name string (e.g. 'claude', 'gemini')

        Returns:
            Provider instance

        Raises:
            ProviderUnavailableError: If provider is disabled or not registered
        """
        if name in self._disabled:
            raise ProviderUnavailableError(
                f"Provider '{name}' is disabled. "
                f"Set 'enabled: true' in config/ai_settings.json to enable it."
            )
        if name not in self._providers:
            raise ProviderUnavailableError(
                f"Provider '{name}' is not registered. "
                f"Add it to PROVIDER_REGISTRY and config/ai_settings.json."
            )
        return self._providers[name]

    def get_all_provider_configs(self) -> Dict[str, dict]:
        """Returns config dict for ALL providers including disabled.
        Used by providers list to display complete provider table."""
        return self._all_configs

    def get_registered_provider_names(self) -> List[str]:
        """Returns list of all provider names in registry.
        Used for dynamic CLI validation."""
        return list(PROVIDER_REGISTRY.keys())

    def is_disabled(self, name: str) -> bool:
        """Returns True if the named provider is disabled in config."""
        return name in self._disabled

    def configure_report_type(
        self,
        report_type: str,
        primary_provider: ProviderType,
        fallback_provider: Optional[ProviderType] = None,
        fallback_mode: FallbackMode = FallbackMode.AUTO,
        max_cost: Optional[float] = None
    ):
        """
        Configure provider selection for a report type.

        Args:
            report_type: Report type name
            primary_provider: Primary provider to use
            fallback_provider: Optional fallback provider
            fallback_mode: Fallback behavior (AUTO/MANUAL)
            max_cost: Optional max cost per report
        """
        config = ReportTypeConfig(
            report_type=report_type,
            primary_provider=primary_provider,
            fallback_provider=fallback_provider,
            fallback_mode=fallback_mode,
            max_cost_per_report=max_cost
        )
        self._report_configs[report_type] = config

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
            report_type: Report type (for provider selection)
            provider_override: Optional provider override

        Returns:
            Tuple of (GenerationResponse, fallback_used)

        Raises:
            ProviderError: If generation fails with all providers
        """
        if provider_override:
            primary = provider_override
            fallback = None
            fallback_mode = FallbackMode.MANUAL
        elif report_type and report_type in self._report_configs:
            config = self._report_configs[report_type]
            primary = config.primary_provider
            fallback = config.fallback_provider
            fallback_mode = config.fallback_mode
        else:
            primary = ProviderType.CLAUDE
            fallback = ProviderType.GEMINI
            fallback_mode = FallbackMode.AUTO

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
        """
        if report_type in self._report_configs:
            return self._report_configs[report_type].primary_provider
        return ProviderType.CLAUDE

    def get_fallback_notifications(self) -> List[str]:
        """Get list of fallback notifications."""
        return self._fallback_notifications.copy()

    def clear_fallback_notifications(self):
        """Clear fallback notification history."""
        self._fallback_notifications.clear()

    def set_fallback_mode(self, report_type: str, mode: FallbackMode):
        """
        Update fallback mode for a report type.

        Args:
            report_type: Report type to update
            mode: New fallback mode
        """
        if report_type in self._report_configs:
            self._report_configs[report_type].fallback_mode = mode

    def get_report_config(self, report_type: str) -> Optional[ReportTypeConfig]:
        """
        Get configuration for a report type.

        Args:
            report_type: Report type name

        Returns:
            Report type configuration or None
        """
        return self._report_configs.get(report_type)

    def estimate_cost(
        self,
        report_type: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Estimate cost for a report generation.

        Args:
            report_type: Type of report
            prompt_tokens: Estimated prompt tokens
            completion_tokens: Estimated completion tokens

        Returns:
            Estimated cost in USD
        """
        provider_type = self.get_provider_for_report(report_type)
        provider = self.get_provider(provider_type.value)
        return provider.estimate_cost(prompt_tokens, completion_tokens)

    def _load_config(self):
        """Load provider and report-type configuration from ai_settings.json.

        Instantiates enabled providers from PROVIDER_REGISTRY.
        Tracks disabled providers in _disabled (no connectivity check).
        """
        import json
        from pathlib import Path

        config_file = self.config_path or str(
            Path(__file__).parent.parent.parent / 'config' / 'ai_settings.json'
        )

        if not Path(config_file).exists():
            return

        with open(config_file, 'r') as f:
            self._settings = json.load(f)

        # Instantiate providers from registry
        for name, provider_cfg in self._settings.get('providers', {}).items():
            self._all_configs[name] = provider_cfg
            if not provider_cfg.get('enabled', True):
                self._disabled.add(name)
                continue
            cls = PROVIDER_REGISTRY.get(name)
            if cls:
                try:
                    self._providers[name] = cls(provider_cfg)
                except Exception:
                    # Provider instantiation failed (e.g. missing API key in env).
                    # Mark as disabled so callers get a clear error rather than
                    # an unhandled exception at import time.
                    self._disabled.add(name)

        # Build report-type configs
        provider_map = {
            'claude': ProviderType.CLAUDE,
            'gemini': ProviderType.GEMINI,
            'ollama': ProviderType.OLLAMA,
        }
        fallback_mode_map = {
            'auto':   FallbackMode.AUTO,
            'manual': FallbackMode.MANUAL,
        }

        for report_type, cfg in self._settings.get('report_types', {}).items():
            primary  = provider_map.get(cfg.get('primary_provider',  'claude'), ProviderType.CLAUDE)
            fallback = provider_map.get(cfg.get('fallback_provider', 'gemini'), ProviderType.GEMINI)
            fb_mode  = fallback_mode_map.get(cfg.get('fallback_mode', 'auto'), FallbackMode.AUTO)
            max_cost = cfg.get('max_cost_per_report', 1.0)

            self.configure_report_type(
                report_type=report_type,
                primary_provider=primary,
                fallback_provider=fallback,
                fallback_mode=fb_mode,
                max_cost=max_cost,
            )


# Singleton instance
_provider_manager_instance: Optional[ProviderManager] = None


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
