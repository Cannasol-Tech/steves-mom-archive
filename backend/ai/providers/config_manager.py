"""
Provider Configuration Manager

This module handles configuration and credential management for all AI providers,
including environment variable loading, validation, and secure storage.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

import os
import logging
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, field
from enum import Enum

from .base import ModelConfig, ModelCapability
from .grok_provider import GROKProvider
from .openai_provider import OpenAIProvider
from .claude_provider import ClaudeProvider
from .local_provider import LocalProvider

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Enumeration of available provider types."""
    GROK = "grok"
    OPENAI = "openai"
    CLAUDE = "claude"
    LOCAL = "local"


@dataclass
class ProviderCredentials:
    """Container for provider credentials and configuration."""
    provider_type: ProviderType
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: str = "default"
    enabled: bool = True
    priority: int = 1  # Lower numbers = higher priority
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProviderConfigManager:
    """
    Manages configuration and credentials for all AI providers.
    
    Handles environment variable loading, validation, and provides
    a centralized way to configure and instantiate providers.
    """
    
    # Default configurations for each provider
    DEFAULT_CONFIGS = {
        ProviderType.GROK: {
            "base_url": "https://api.x.ai",
            "model_name": "grok-3-mini",
            "env_key": "CUSTOM_OPENAI_API_KEY",
            "priority": 1
        },
        ProviderType.OPENAI: {
            "base_url": "https://api.openai.com/v1",
            "model_name": "gpt-4",
            "env_key": "OPENAI_API_KEY",
            "priority": 2
        },
        ProviderType.CLAUDE: {
            "base_url": "https://api.anthropic.com",
            "model_name": "claude-3-sonnet",
            "env_key": "ANTHROPIC_API_KEY",
            "priority": 3
        },
        ProviderType.LOCAL: {
            "base_url": "http://localhost:11434",
            "model_name": "llama-3.1-8b",
            "env_key": None,  # No API key needed for local
            "priority": 4
        }
    }
    
    # Provider class mapping
    PROVIDER_CLASSES = {
        ProviderType.GROK: GROKProvider,
        ProviderType.OPENAI: OpenAIProvider,
        ProviderType.CLAUDE: ClaudeProvider,
        ProviderType.LOCAL: LocalProvider
    }
    
    def __init__(self):
        """Initialize the configuration manager."""
        self._credentials: Dict[ProviderType, ProviderCredentials] = {}
        self._load_from_environment()
    
    def _load_from_environment(self) -> None:
        """Load provider configurations from environment variables."""
        logger.info("Loading provider configurations from environment")
        
        for provider_type, defaults in self.DEFAULT_CONFIGS.items():
            # Get API key from environment if specified
            api_key = None
            if defaults.get("env_key"):
                api_key = os.environ.get(defaults["env_key"])
            
            # Check if provider is explicitly disabled
            enabled_key = f"{provider_type.value.upper()}_ENABLED"
            enabled = os.environ.get(enabled_key, "true").lower() == "true"
            
            # Override model name if specified
            model_key = f"{provider_type.value.upper()}_MODEL"
            model_name = os.environ.get(model_key, defaults["model_name"])
            
            # Override base URL if specified
            url_key = f"{provider_type.value.upper()}_BASE_URL"
            base_url = os.environ.get(url_key, defaults["base_url"])
            
            # Override priority if specified
            priority_key = f"{provider_type.value.upper()}_PRIORITY"
            priority = int(os.environ.get(priority_key, defaults["priority"]))
            
            # Create credentials object
            credentials = ProviderCredentials(
                provider_type=provider_type,
                api_key=api_key,
                base_url=base_url,
                model_name=model_name,
                enabled=enabled,
                priority=priority
            )
            
            self._credentials[provider_type] = credentials
            
            # Log configuration (without exposing API keys)
            key_status = "configured" if api_key else "not configured"
            logger.info(f"{provider_type.value}: {key_status}, model={model_name}, enabled={enabled}")
    
    def get_credentials(self, provider_type: ProviderType) -> Optional[ProviderCredentials]:
        """Get credentials for a specific provider."""
        return self._credentials.get(provider_type)
    
    def get_enabled_providers(self) -> List[ProviderCredentials]:
        """Get list of enabled providers sorted by priority."""
        enabled = [cred for cred in self._credentials.values() if cred.enabled]
        return sorted(enabled, key=lambda x: x.priority)
    
    def get_available_providers(self) -> List[ProviderCredentials]:
        """Get list of providers that have valid credentials."""
        available = []
        for cred in self._credentials.values():
            if not cred.enabled:
                continue
            
            # Check if provider has required credentials
            if cred.provider_type == ProviderType.LOCAL:
                # Local provider doesn't need API key
                available.append(cred)
            elif cred.api_key:
                # Other providers need API key
                available.append(cred)
        
        return sorted(available, key=lambda x: x.priority)
    
    def create_provider(self, provider_type: ProviderType) -> Optional[Any]:
        """Create and configure a provider instance."""
        credentials = self.get_credentials(provider_type)
        if not credentials or not credentials.enabled:
            logger.warning(f"Provider {provider_type.value} not available or disabled")
            return None
        
        provider_class = self.PROVIDER_CLASSES.get(provider_type)
        if not provider_class:
            logger.error(f"No provider class found for {provider_type.value}")
            return None
        
        try:
            # Instantiate provider with credentials
            # Handle the case where api_key might be None for local providers
            api_key = credentials.api_key if credentials.api_key else ""

            provider = provider_class(
                api_key=api_key,
                base_url=credentials.base_url,
                **credentials.metadata
            )
            logger.info(f"Created {provider_type.value} provider with model {credentials.model_name}")
            return provider
            
        except Exception as e:
            logger.error(f"Failed to create {provider_type.value} provider: {e}")
            return None
    
    def create_all_providers(self) -> Dict[ProviderType, Any]:
        """Create all available provider instances."""
        providers = {}
        
        for provider_type in ProviderType:
            provider = self.create_provider(provider_type)
            if provider:
                providers[provider_type] = provider
        
        logger.info(f"Created {len(providers)} providers: {list(providers.keys())}")
        return providers
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current provider configuration."""
        validation_results = {
            "valid": True,
            "providers": {},
            "warnings": [],
            "errors": []
        }
        
        available_providers = self.get_available_providers()
        
        if not available_providers:
            validation_results["valid"] = False
            validation_results["errors"].append("No providers have valid credentials")
        
        for provider_type, credentials in self._credentials.items():
            provider_result = {
                "enabled": credentials.enabled,
                "has_credentials": bool(credentials.api_key) or provider_type == ProviderType.LOCAL,
                "model": credentials.model_name,
                "priority": credentials.priority
            }
            
            if credentials.enabled and not provider_result["has_credentials"]:
                validation_results["warnings"].append(
                    f"{provider_type.value} is enabled but missing credentials"
                )
            
            validation_results["providers"][provider_type.value] = provider_result
        
        return validation_results
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration."""
        available = self.get_available_providers()
        enabled = self.get_enabled_providers()
        
        return {
            "total_providers": len(self._credentials),
            "enabled_providers": len(enabled),
            "available_providers": len(available),
            "primary_provider": available[0].provider_type.value if available else None,
            "provider_status": {
                ptype.value: {
                    "enabled": cred.enabled,
                    "available": bool(cred.api_key) or ptype == ProviderType.LOCAL,
                    "model": cred.model_name,
                    "priority": cred.priority
                }
                for ptype, cred in self._credentials.items()
            }
        }


# Global configuration manager instance
config_manager = ProviderConfigManager()


# Convenience functions
def get_primary_provider():
    """Get the primary (highest priority) available provider."""
    available = config_manager.get_available_providers()
    if available:
        return config_manager.create_provider(available[0].provider_type)
    return None


def get_all_providers():
    """Get all available provider instances."""
    return config_manager.create_all_providers()


def validate_providers():
    """Validate provider configuration."""
    return config_manager.validate_configuration()
