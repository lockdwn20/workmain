"""
WorkmAIn AI Provider Manager
Provider Manager v1.0
20251229

Manages AI providers with intelligent fallback and selection.

Features:
- Multi-provider support (Claude + Gemini)
- Per-report-type provider selection
- Configurable fallback (manual/automatic)
- Provider health monitoring
- Notification on fallback
- Cost-aware selection

Fallback Modes:
- AUTO: Automatic fallback with notification
- MANUAL: Prompt user before fallback
"""

import os
from typing import Dict, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass

try:
    from workmain.ai.base_provider import (
        BaseProvider,
        ProviderType,
        ProviderStatus,
        ProviderConfig,
        GenerationRequest,
        GenerationResponse,
        ProviderError,
        RateLimitError
    )
except ModuleNotFoundError:
    # Fallback for standalone testing
    from base_provider import (
        BaseProvider,
        ProviderType,
        ProviderStatus,
        ProviderConfig,
        GenerationRequest,
        GenerationResponse,
        ProviderError,
        RateLimitError
    )


class FallbackMode(Enum):
    """Fallback behavior modes."""
    AUTO = "auto"  # Automatic fallback with notification
    MANUAL = "manual"  # Prompt user before fallback


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
    
    Handles:
    - Loading provider configurations
    - Selecting appropriate provider per report type
    - Fallback to alternative provider on failure
    - Provider health monitoring
    - Notifications on fallback
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize provider manager.
        
        Args:
            config_path: Path to ai_settings.json config file
        """
        self.config_path = config_path
        self._providers: Dict[ProviderType, BaseProvider] = {}
        self._report_configs: Dict[str, ReportTypeConfig] = {}
        self._fallback_notifications: List[str] = []
        
        if config_path:
            self._load_config()
    
    def register_provider(
        self,
        provider_type: ProviderType,
        provider: BaseProvider
    ):
        """
        Register a provider instance.
        
        Args:
            provider_type: Type of provider
            provider: Provider instance
        """
        self._providers[provider_type] = provider
    
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
        # Determine primary provider
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
            # Default to Claude
            primary = ProviderType.CLAUDE
            fallback = ProviderType.GEMINI
            fallback_mode = FallbackMode.AUTO
        
        # Try primary provider
        try:
            provider = self._get_provider(primary)
            response = provider.generate(request)
            return response, False
            
        except (ProviderError, RateLimitError) as e:
            # Primary failed - check fallback
            if not fallback:
                raise ProviderError(
                    f"Primary provider {primary.value} failed and no fallback configured"
                ) from e
            
            # Handle fallback based on mode
            if fallback_mode == FallbackMode.MANUAL:
                # Manual mode - would need user input
                # For now, raise error with fallback suggestion
                raise ProviderError(
                    f"Primary provider {primary.value} failed. "
                    f"Fallback to {fallback.value} available but manual mode enabled. "
                    f"Use --provider {fallback.value} to retry."
                ) from e
            
            # AUTO mode - try fallback with notification
            try:
                fallback_provider = self._get_provider(fallback)
                notification = (
                    f"⚠️  Primary provider {primary.value} failed. "
                    f"Automatically falling back to {fallback.value}. "
                    f"Reason: {str(e)}"
                )
                self._fallback_notifications.append(notification)
                
                response = fallback_provider.generate(request)
                return response, True
                
            except (ProviderError, RateLimitError) as fallback_error:
                # Both failed
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
        return ProviderType.CLAUDE  # Default
    
    def check_provider_status(
        self,
        provider_type: ProviderType
    ) -> ProviderStatus:
        """
        Check status of a specific provider.
        
        Args:
            provider_type: Provider to check
            
        Returns:
            Provider status
        """
        try:
            provider = self._get_provider(provider_type)
            return provider.check_availability()
        except KeyError:
            return ProviderStatus.UNAVAILABLE
    
    def get_all_provider_statuses(self) -> Dict[ProviderType, ProviderStatus]:
        """
        Get status of all registered providers.
        
        Returns:
            Dictionary mapping provider types to statuses
        """
        return {
            ptype: self.check_provider_status(ptype)
            for ptype in ProviderType
        }
    
    def get_fallback_notifications(self) -> List[str]:
        """
        Get list of fallback notifications.
        
        Returns:
            List of notification messages
        """
        return self._fallback_notifications.copy()
    
    def clear_fallback_notifications(self):
        """Clear fallback notification history."""
        self._fallback_notifications.clear()
    
    def set_fallback_mode(
        self,
        report_type: str,
        mode: FallbackMode
    ):
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
        provider = self._get_provider(provider_type)
        return provider.estimate_cost(prompt_tokens, completion_tokens)
    
    def _get_provider(self, provider_type: ProviderType) -> BaseProvider:
        """
        Get provider instance.
        
        Args:
            provider_type: Type of provider
            
        Returns:
            Provider instance
            
        Raises:
            KeyError: If provider not registered
        """
        if provider_type not in self._providers:
            raise KeyError(
                f"Provider {provider_type.value} not registered. "
                f"Available: {list(self._providers.keys())}"
            )
        return self._providers[provider_type]
    
    def _load_config(self):
        """
        Load configuration from ai_settings.json.
        
        This will be implemented once the config file format is finalized.
        For now, providers should be registered and configured manually.
        """
        # TODO: Implement config loading in Phase 4
        # Will load from config/ai_settings.json
        # Format:
        # {
        #   "report_types": {
        #     "daily_internal": {
        #       "primary_provider": "claude",
        #       "fallback_provider": "gemini",
        #       "fallback_mode": "auto",
        #       "max_cost_per_report": 1.0
        #     },
        #     "weekly_client": {
        #       "primary_provider": "gemini",
        #       "fallback_provider": "claude",
        #       "fallback_mode": "auto",
        #       "max_cost_per_report": 2.0
        #     }
        #   },
        #   "providers": {
        #     "claude": {...},
        #     "gemini": {...}
        #   }
        # }
        pass


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
