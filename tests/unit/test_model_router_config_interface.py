"""
TDD for 4.2.4: Configuration interface for routing rules

Tests for dynamic configuration management of routing policies,
provider settings, and runtime rule updates.

Author: Cannasol Technologies  
Date: 2025-08-15
Version: 1.0.0
"""

import pytest
import pytest_asyncio
import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch

# Make backend importable
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.ai.model_router import (
    ModelRouter, RoutingPolicy, RoutingStrategy, ProviderConfig
)
from backend.ai.providers.base import (
    LLMProvider, ModelConfig, Message, ModelResponse, ModelCapability
)


class MockProvider(LLMProvider):
    """Mock provider for testing."""
    
    def __init__(self, name: str, **kwargs):
        super().__init__(api_key="test-key", **kwargs)
        self._name = name
        self._initialized = False
    
    @property
    def provider_name(self) -> str:
        return self._name
    
    @property
    def supported_capabilities(self) -> list:
        return [ModelCapability.TEXT_GENERATION]
    
    @property
    def available_models(self) -> list:
        return ["test-model"]
    
    async def initialize(self) -> None:
        self._initialized = True
    
    async def generate_response(self, messages, config) -> ModelResponse:
        return ModelResponse(
            content="Test response",
            model="test-model",
            usage={"input_tokens": 10, "output_tokens": 5},
            provider="test"
        )
    
    async def stream_response(self, messages, config):
        """Mock streaming response."""
        yield "Test streaming response"
    
    def count_tokens(self, text: str) -> int:
        """Mock token counting."""
        return len(text) // 4
    
    def validate_api_key(self) -> bool:
        """Mock API key validation."""
        return True
    
    def estimate_cost(self, messages, config) -> float:
        return 0.01
    
    def supports_capability(self, capability) -> bool:
        return capability in self.supported_capabilities
    
    async def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "initialized": self._initialized}


@pytest_asyncio.fixture
async def router_with_providers():
    """Create router with test providers."""
    router = ModelRouter()
    
    provider1 = MockProvider("provider1")
    provider2 = MockProvider("provider2")
    
    await router.add_provider(provider1, priority=10, weight=2.0)
    await router.add_provider(provider2, priority=5, weight=1.0)
    
    return router


@pytest.mark.asyncio
async def test_update_routing_policy(router_with_providers):
    """Test updating the default routing policy."""
    router = router_with_providers
    
    # Initial policy
    assert router.default_policy.strategy == RoutingStrategy.COST_OPTIMIZED
    assert router.default_policy.max_cost_threshold == 0.05
    
    # Update policy
    new_policy = RoutingPolicy(
        strategy=RoutingStrategy.LATENCY_OPTIMIZED,
        max_cost_threshold=0.10,
        max_latency_threshold=5.0,
        retry_attempts=5
    )
    
    router.update_default_policy(new_policy)
    
    assert router.default_policy.strategy == RoutingStrategy.LATENCY_OPTIMIZED
    assert router.default_policy.max_cost_threshold == 0.10
    assert router.default_policy.max_latency_threshold == 5.0
    assert router.default_policy.retry_attempts == 5


@pytest.mark.asyncio
async def test_update_provider_config(router_with_providers):
    """Test updating provider configuration."""
    router = router_with_providers
    
    # Initial config
    config = router.providers["provider1"]
    assert config.priority == 10
    assert config.weight == 2.0
    assert config.enabled == True
    
    # Update provider config
    router.update_provider_config("provider1", {
        "priority": 15,
        "weight": 3.0,
        "enabled": False,
        "max_requests_per_minute": 120
    })
    
    updated_config = router.providers["provider1"]
    assert updated_config.priority == 15
    assert updated_config.weight == 3.0
    assert updated_config.enabled == False
    assert updated_config.max_requests_per_minute == 120


@pytest.mark.asyncio
async def test_enable_disable_provider(router_with_providers):
    """Test enabling and disabling providers."""
    router = router_with_providers
    
    # Initially enabled
    assert router.providers["provider1"].enabled == True
    
    # Disable provider
    router.disable_provider("provider1")
    assert router.providers["provider1"].enabled == False
    
    # Enable provider
    router.enable_provider("provider1")
    assert router.providers["provider1"].enabled == True


@pytest.mark.asyncio
async def test_get_configuration_snapshot():
    """Test getting complete configuration snapshot."""
    router = ModelRouter()
    
    provider = MockProvider("test_provider")
    await router.add_provider(provider, priority=8, weight=1.5)
    
    config = router.get_configuration_snapshot()
    
    assert "default_policy" in config
    assert "providers" in config
    
    # Check policy config
    policy_config = config["default_policy"]
    assert policy_config["strategy"] == "cost_optimized"
    assert policy_config["max_cost_threshold"] == 0.05
    
    # Check provider config
    provider_config = config["providers"]["test_provider"]
    assert provider_config["priority"] == 8
    assert provider_config["weight"] == 1.5
    assert provider_config["enabled"] == True


@pytest.mark.asyncio
async def test_load_configuration_from_dict():
    """Test loading configuration from dictionary."""
    router = ModelRouter()
    
    # Add provider first
    provider = MockProvider("test_provider")
    await router.add_provider(provider)
    
    config_dict = {
        "default_policy": {
            "strategy": "latency_optimized",
            "max_cost_threshold": 0.08,
            "max_latency_threshold": 8.0,
            "retry_attempts": 4
        },
        "providers": {
            "test_provider": {
                "priority": 12,
                "weight": 2.5,
                "enabled": False,
                "max_requests_per_minute": 100
            }
        }
    }
    
    router.load_configuration(config_dict)
    
    # Check policy was updated
    assert router.default_policy.strategy == RoutingStrategy.LATENCY_OPTIMIZED
    assert router.default_policy.max_cost_threshold == 0.08
    assert router.default_policy.max_latency_threshold == 8.0
    assert router.default_policy.retry_attempts == 4
    
    # Check provider was updated
    provider_config = router.providers["test_provider"]
    assert provider_config.priority == 12
    assert provider_config.weight == 2.5
    assert provider_config.enabled == False
    assert provider_config.max_requests_per_minute == 100


@pytest.mark.asyncio
async def test_configuration_validation():
    """Test configuration validation."""
    router = ModelRouter()
    
    # Invalid provider name
    with pytest.raises(ValueError, match="Provider.*not found"):
        router.update_provider_config("nonexistent", {"priority": 5})
    
    # Invalid configuration values
    provider = MockProvider("test_provider")
    await router.add_provider(provider)
    
    with pytest.raises(ValueError, match="Priority must be positive"):
        router.update_provider_config("test_provider", {"priority": -1})
    
    with pytest.raises(ValueError, match="Weight must be positive"):
        router.update_provider_config("test_provider", {"weight": 0})
    
    with pytest.raises(ValueError, match="Max requests per minute must be positive"):
        router.update_provider_config("test_provider", {"max_requests_per_minute": -5})


@pytest.mark.asyncio
async def test_provider_enable_disable_validation():
    """Test provider enable/disable validation."""
    router = ModelRouter()
    
    # Test with nonexistent provider
    with pytest.raises(ValueError, match="Provider.*not found"):
        router.enable_provider("nonexistent")
    
    with pytest.raises(ValueError, match="Provider.*not found"):
        router.disable_provider("nonexistent")


@pytest.mark.asyncio
async def test_configuration_roundtrip():
    """Test configuration snapshot and load roundtrip."""
    router = ModelRouter()
    
    # Set up initial configuration
    provider = MockProvider("test_provider")
    await router.add_provider(provider, priority=7, weight=1.8)
    
    policy = RoutingPolicy(
        strategy=RoutingStrategy.CAPABILITY_BASED,
        max_cost_threshold=0.12,
        retry_attempts=6
    )
    router.update_default_policy(policy)
    
    # Get snapshot
    snapshot = router.get_configuration_snapshot()
    
    # Create new router and load configuration
    new_router = ModelRouter()
    new_provider = MockProvider("test_provider")
    await new_router.add_provider(new_provider)
    
    new_router.load_configuration(snapshot)
    
    # Verify configuration matches
    assert new_router.default_policy.strategy == RoutingStrategy.CAPABILITY_BASED
    assert new_router.default_policy.max_cost_threshold == 0.12
    assert new_router.default_policy.retry_attempts == 6
    
    provider_config = new_router.providers["test_provider"]
    assert provider_config.priority == 7
    assert provider_config.weight == 1.8
