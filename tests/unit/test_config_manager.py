"""
Unit tests for ProviderConfigManager typed behaviors (1.4.MY.3.T)

Covers:
- enabled vs available providers and priority sorting
- create_provider behavior for Local and remote without API keys
- validate_configuration warnings/errors aggregation
- configuration summary keys and types
"""

import sys
from pathlib import Path
import os
from typing import Any, Dict
import pytest

# Ensure backend importable
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.ai.providers.config_manager import (
    ProviderConfigManager,
    ProviderType,
)
from backend.ai.providers.local_provider import LocalProvider


def with_env(env: Dict[str, str]):
    class EnvCtx:
        def __enter__(self):
            self._old = os.environ.copy()
            # Clear all provider-related environment variables first
            provider_keys = [
                "GROK_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
                "GROK_ENABLED", "OPENAI_ENABLED", "CLAUDE_ENABLED", "LOCAL_ENABLED",
                "GROK_PRIORITY", "OPENAI_PRIORITY", "CLAUDE_PRIORITY", "LOCAL_PRIORITY",
                "GROK_MODEL", "OPENAI_MODEL", "CLAUDE_MODEL", "LOCAL_MODEL",
                "GROK_BASE_URL", "OPENAI_BASE_URL", "CLAUDE_BASE_URL", "LOCAL_BASE_URL"
            ]
            for key in provider_keys:
                os.environ.pop(key, None)
            # Now set the test environment
            os.environ.update(env)
        def __exit__(self, exc_type, exc, tb):
            os.environ.clear()
            os.environ.update(self._old)
    return EnvCtx()


def test_enabled_vs_available_and_priority_sorting():
    env = {
        "LOCAL_ENABLED": "true",
        "GROK_ENABLED": "true",
        "OPENAI_ENABLED": "false",
        "CLAUDE_ENABLED": "true",
        # credentials
        # GROK_API_KEY missing -> not available
        "ANTHROPIC_API_KEY": "dummy",
        # priorities
        "LOCAL_PRIORITY": "3",
        "GROK_PRIORITY": "1",
        "CLAUDE_PRIORITY": "2",
    }
    with with_env(env):
        mgr = ProviderConfigManager()
        enabled = mgr.get_enabled_providers()
        # Enabled sorted by priority: GROK (1), CLAUDE (2), LOCAL (3)
        assert [c.provider_type for c in enabled] == [
            ProviderType.GROK,
            ProviderType.CLAUDE,
            ProviderType.LOCAL,
        ]
        available = mgr.get_available_providers()
        # Available should exclude GROK (no key), include CLAUDE (has key), LOCAL (no key required)
        assert [c.provider_type for c in available] == [
            ProviderType.CLAUDE,
            ProviderType.LOCAL,
        ]


def test_create_provider_local_without_api_key_returns_instance():
    env = {
        "LOCAL_ENABLED": "true",
        "LOCAL_PRIORITY": "5",
    }
    with with_env(env):
        mgr = ProviderConfigManager()
        provider = mgr.create_provider(ProviderType.LOCAL)
        assert isinstance(provider, LocalProvider)


def test_create_provider_remote_without_key_returns_none():
    env = {
        "GROK_ENABLED": "true",
        # No GROK_API_KEY
    }
    with with_env(env):
        mgr = ProviderConfigManager()
        provider = mgr.create_provider(ProviderType.GROK)
        assert provider is None


def test_validate_configuration_flags_warnings_and_errors():
    env = {
        "GROK_ENABLED": "true",
        "LOCAL_ENABLED": "false",  # disable local to force no available providers
        # No keys available for remote providers
    }
    with with_env(env):
        mgr = ProviderConfigManager()
        result = mgr.validate_configuration()
        assert result["valid"] is False
        assert any("missing credentials" in w for w in result["warnings"]) or result["errors"]


def test_configuration_summary_schema_and_types():
    env = {
        "LOCAL_ENABLED": "true",
        "LOCAL_PRIORITY": "1",
    }
    with with_env(env):
        mgr = ProviderConfigManager()
        summary: Dict[str, Any] = mgr.get_configuration_summary()
        assert set(["total_providers", "enabled_providers", "available_providers", "primary_provider", "provider_status"]).issubset(summary.keys())
        assert isinstance(summary["total_providers"], int)
        assert isinstance(summary["enabled_providers"], int)
        assert isinstance(summary["available_providers"], int)
        assert (summary["primary_provider"] is None) or isinstance(summary["primary_provider"], str)
        assert isinstance(summary["provider_status"], dict)

