"""
Integration tests for ModelRouter with real provider interactions

Tests the complete flow from router configuration through provider
selection and response handling with realistic scenarios.

Author: Cannasol Technologies
Date: 2025-08-15
Version: 1.0.0
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, AsyncMock

# Make backend importable
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.ai.model_router import (
    ModelRouter, RoutingPolicy, RoutingStrategy, create_router_from_env
)
from backend.ai.providers.base import (
    ModelConfig, Message, MessageRole, ModelCapability
)
from backend.ai.providers.grok_provider import GROKProvider
from backend.ai.providers.local_provider import LocalProvider


@pytest.fixture
def sample_messages():
    """Sample conversation messages for testing."""
    return [
        Message(role=MessageRole.USER, content="Hello, how are you?"),
        Message(role=MessageRole.ASSISTANT, content="I'm doing well, thank you!"),
        Message(role=MessageRole.USER, content="Can you help me with a task?")
    ]


@pytest.fixture
def model_config():
    """Standard model configuration for testing."""
    return ModelConfig(
        model_name="grok-3-mini",
        max_tokens=100,
        temperature=0.7
    )


@pytest.mark.asyncio
async def test_router_with_multiple_providers_cost_optimization(sample_messages, model_config):
    """Test router selects cheapest provider for cost optimization."""
    router = ModelRouter(
        default_policy=RoutingPolicy(strategy=RoutingStrategy.COST_OPTIMIZED)
    )
    
    # Mock providers with different costs
    with patch('backend.ai.providers.grok_provider.GROKProvider') as MockGrok, \
         patch('backend.ai.providers.local_provider.LocalProvider') as MockLocal:
        
        # Configure mock providers
        grok_mock = MockGrok.return_value
        grok_mock.provider_name = "grok"
        grok_mock.available_models = ["grok-3-mini"]
        grok_mock.supported_capabilities = [ModelCapability.TEXT_GENERATION]
        grok_mock.estimate_cost.return_value = 0.05  # More expensive
        grok_mock.initialize = AsyncMock()
        grok_mock.generate_response = AsyncMock(return_value=type('MockResponse', (), {
            'content': 'Grok response',
            'provider': 'grok',
            'model': 'grok-3-mini'
        })())
        grok_mock.supports_capability.return_value = True
        
        local_mock = MockLocal.return_value
        local_mock.provider_name = "local"
        local_mock.available_models = ["grok-3-mini"]
        local_mock.supported_capabilities = [ModelCapability.TEXT_GENERATION]
        local_mock.estimate_cost.return_value = 0.01  # Cheaper
        local_mock.initialize = AsyncMock()
        local_mock.generate_response = AsyncMock(return_value=type('MockResponse', (), {
            'content': 'Local response',
            'provider': 'local',
            'model': 'grok-3-mini'
        })())
        local_mock.supports_capability.return_value = True
        
        # Add providers to router
        await router.add_provider(grok_mock, priority=5)
        await router.add_provider(local_mock, priority=5)
        
        # Route request - should select local (cheaper)
        response = await router.route_request(sample_messages, model_config)
        
        assert response.provider == "local"
        local_mock.generate_response.assert_called_once()
        grok_mock.generate_response.assert_not_called()


@pytest.mark.asyncio
async def test_router_fallback_on_provider_failure(sample_messages, model_config):
    """Test router falls back to next provider on failure."""
    router = ModelRouter(
        default_policy=RoutingPolicy(
            strategy=RoutingStrategy.FAILOVER,
            retry_attempts=1
        )
    )
    
    with patch('backend.ai.providers.grok_provider.GROKProvider') as MockGrok, \
         patch('backend.ai.providers.local_provider.LocalProvider') as MockLocal, \
         patch('backend.ai.model_router.asyncio.sleep', new=AsyncMock()):
        
        # Primary provider fails
        grok_mock = MockGrok.return_value
        grok_mock.provider_name = "grok"
        grok_mock.available_models = ["grok-3-mini"]
        grok_mock.supported_capabilities = [ModelCapability.TEXT_GENERATION]
        grok_mock.estimate_cost.return_value = 0.01
        grok_mock.initialize = AsyncMock()
        grok_mock.generate_response = AsyncMock(side_effect=Exception("Provider failed"))
        grok_mock.supports_capability.return_value = True
        
        # Fallback provider succeeds
        local_mock = MockLocal.return_value
        local_mock.provider_name = "local"
        local_mock.available_models = ["grok-3-mini"]
        local_mock.supported_capabilities = [ModelCapability.TEXT_GENERATION]
        local_mock.estimate_cost.return_value = 0.01
        local_mock.initialize = AsyncMock()
        local_mock.generate_response = AsyncMock(return_value=type('MockResponse', (), {
            'content': 'Fallback response',
            'provider': 'local',
            'model': 'grok-3-mini'
        })())
        local_mock.supports_capability.return_value = True
        
        # Add providers in fallback order
        await router.add_provider(grok_mock, fallback_order=0)
        await router.add_provider(local_mock, fallback_order=1)
        
        # Route request - should fallback to local
        response = await router.route_request(sample_messages, model_config)
        
        assert response.provider == "local"
        assert response.content == "Fallback response"
        grok_mock.generate_response.assert_called_once()
        local_mock.generate_response.assert_called_once()


@pytest.mark.asyncio
async def test_router_configuration_update_during_runtime(sample_messages, model_config):
    """Test router configuration can be updated during runtime."""
    router = ModelRouter()
    
    with patch('backend.ai.providers.local_provider.LocalProvider') as MockLocal:
        local_mock = MockLocal.return_value
        local_mock.provider_name = "local"
        local_mock.available_models = ["grok-3-mini"]
        local_mock.supported_capabilities = [ModelCapability.TEXT_GENERATION]
        local_mock.estimate_cost.return_value = 0.01
        local_mock.initialize = AsyncMock()
        local_mock.generate_response = AsyncMock(return_value=type('MockResponse', (), {
            'content': 'Response',
            'provider': 'local',
            'model': 'grok-3-mini'
        })())
        local_mock.supports_capability.return_value = True
        
        await router.add_provider(local_mock)
        
        # Initial request
        response1 = await router.route_request(sample_messages, model_config)
        assert response1.provider == "local"
        
        # Disable provider
        router.disable_provider("local")
        
        # Request should fail (no enabled providers)
        with pytest.raises(Exception):
            await router.route_request(sample_messages, model_config)
        
        # Re-enable provider
        router.enable_provider("local")
        
        # Request should work again
        response2 = await router.route_request(sample_messages, model_config)
        assert response2.provider == "local"


@pytest.mark.asyncio
async def test_environment_based_router_creation():
    """Test router creation from environment variables."""
    test_env = {
        "LOCAL_ENABLED": "true",
        "LOCAL_PRIORITY": "1",
        "AI_ROUTING_STRATEGY": "cost_optimized",
        "AI_MAX_COST_THRESHOLD": "0.10",
        "AI_RETRY_ATTEMPTS": "2"
    }
    
    with patch.dict(os.environ, test_env), \
         patch('backend.ai.providers.config_manager.ProviderConfigManager') as MockPCM:
        
        # Mock config manager
        pcm_mock = MockPCM.return_value
        pcm_mock.get_available_providers.return_value = [
            type('MockCred', (), {
                'provider_type': 'local',
                'priority': 1
            })()
        ]
        
        with patch('backend.ai.providers.local_provider.LocalProvider') as MockLocal:
            local_mock = MockLocal.return_value
            local_mock.provider_name = "local"
            local_mock.initialize = AsyncMock()
            
            pcm_mock.create_provider.return_value = local_mock
            
            router = await create_router_from_env()
            
            # Check policy configuration
            assert router.default_policy.strategy == RoutingStrategy.COST_OPTIMIZED
            assert router.default_policy.max_cost_threshold == 0.10
            assert router.default_policy.retry_attempts == 2
            
            # Check provider was added
            assert "local" in router.providers


@pytest.mark.asyncio
async def test_router_health_check_integration():
    """Test router health check with real provider status."""
    router = ModelRouter()
    
    with patch('backend.ai.providers.local_provider.LocalProvider') as MockLocal:
        local_mock = MockLocal.return_value
        local_mock.provider_name = "local"
        local_mock.initialize = AsyncMock()
        local_mock.health_check = AsyncMock(return_value={
            "status": "healthy",
            "latency": 0.05,
            "available": True
        })
        
        await router.add_provider(local_mock, priority=10, weight=2.0)
        
        status = await router.get_provider_status()
        
        assert "local" in status
        provider_status = status["local"]
        assert provider_status["status"] == "healthy"
        assert provider_status["priority"] == 10
        assert provider_status["weight"] == 2.0
        assert provider_status["enabled"] == True
        assert provider_status["circuit_breaker"] == False


@pytest.mark.asyncio
async def test_router_circuit_breaker_integration():
    """Test circuit breaker functionality in integration scenario."""
    router = ModelRouter()
    
    with patch('backend.ai.providers.local_provider.LocalProvider') as MockLocal, \
         patch('backend.ai.model_router.asyncio.sleep', new=AsyncMock()):
        
        local_mock = MockLocal.return_value
        local_mock.provider_name = "local"
        local_mock.available_models = ["grok-3-mini"]
        local_mock.supported_capabilities = [ModelCapability.TEXT_GENERATION]
        local_mock.estimate_cost.return_value = 0.01
        local_mock.initialize = AsyncMock()
        local_mock.supports_capability.return_value = True
        local_mock.generate_response = AsyncMock(side_effect=Exception("Provider error"))
        
        await router.add_provider(local_mock)
        
        # Manually trigger circuit breaker by directly calling _record_error
        for _ in range(6):
            router._record_error("local")
        
        # Manually check circuit breaker state
        assert router._error_counts["local"] > 5
        assert router._circuit_breakers["local"] == True
        
        # Reset circuit breaker
        await router.reset_circuit_breakers()
        
        # Check circuit breaker is reset
        assert router._circuit_breakers["local"] == False
        assert router._error_counts["local"] == 0
