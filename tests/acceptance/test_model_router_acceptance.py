"""
Acceptance tests for ModelRouter end-to-end scenarios

Tests complete user workflows and business requirements for the
AI model routing system with realistic use cases.

Author: Cannasol Technologies
Date: 2025-08-15
Version: 1.0.0
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import patch, AsyncMock

# Make backend importable
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.ai.model_router import (
    ModelRouter, RoutingPolicy, RoutingStrategy, create_router_from_env
)
from backend.ai.providers.base import (
    ModelConfig, Message, MessageRole, ModelCapability, ProviderError
)


class AcceptanceTestScenario:
    """Helper class for acceptance test scenarios."""
    
    @staticmethod
    def create_conversation(length: int = 3) -> List[Message]:
        """Create a realistic conversation for testing."""
        messages = [
            Message(role=MessageRole.USER, content="I need help with ultrasonic processing for cannabis extraction."),
            Message(role=MessageRole.ASSISTANT, content="I'd be happy to help with ultrasonic processing for cannabis extraction. What specific aspect would you like to know about?"),
            Message(role=MessageRole.USER, content="What are the optimal frequency settings for maximum cannabinoid extraction?")
        ]
        return messages[:length]
    
    @staticmethod
    def create_business_query() -> List[Message]:
        """Create a business-focused query."""
        return [
            Message(role=MessageRole.USER, content="Generate a quarterly report summary for Cannasol Technologies' ultrasonic processing equipment sales.")
        ]
    
    @staticmethod
    def create_technical_query() -> List[Message]:
        """Create a technical support query."""
        return [
            Message(role=MessageRole.USER, content="Debug error code E-404 on Model ULP-2000 ultrasonic processor. Equipment shows 'Frequency Modulation Failure' on display.")
        ]


@pytest.mark.asyncio
async def test_cost_conscious_business_user_workflow():
    """
    Acceptance Test: Cost-conscious business user wants cheapest responses
    
    As a business user concerned about costs,
    I want the system to always route to the cheapest available provider,
    So that I can minimize operational expenses while getting quality responses.
    """
    # Setup cost-optimized router
    router = ModelRouter(
        default_policy=RoutingPolicy(
            strategy=RoutingStrategy.COST_OPTIMIZED,
            max_cost_threshold=0.05  # Strict cost limit
        )
    )
    
    with patch('backend.ai.providers.local_provider.LocalProvider') as MockLocal, \
         patch('backend.ai.providers.grok_provider.GROKProvider') as MockGrok:
        
        # Local provider: cheap but basic
        local_mock = MockLocal.return_value
        local_mock.provider_name = "local"
        local_mock.available_models = ["grok-3-mini"]
        local_mock.supported_capabilities = [ModelCapability.TEXT_GENERATION]
        local_mock.estimate_cost.return_value = 0.01  # Very cheap
        local_mock.initialize = AsyncMock()
        local_mock.generate_response = AsyncMock(return_value=type('Response', (), {
            'content': 'Local AI response for cannabis extraction guidance',
            'provider': 'local',
            'model': 'grok-3-mini',
            'usage': {'input_tokens': 50, 'output_tokens': 100}
        })())
        local_mock.supports_capability.return_value = True
        
        # GROK provider: expensive but high quality
        grok_mock = MockGrok.return_value
        grok_mock.provider_name = "grok"
        grok_mock.available_models = ["grok-3-mini"]
        grok_mock.supported_capabilities = [ModelCapability.TEXT_GENERATION, ModelCapability.REASONING]
        grok_mock.estimate_cost.return_value = 0.08  # Exceeds cost threshold
        grok_mock.initialize = AsyncMock()
        grok_mock.supports_capability.return_value = True
        
        await router.add_provider(local_mock, priority=5)
        await router.add_provider(grok_mock, priority=10)  # Higher priority but too expensive
        
        # Business user makes query
        messages = AcceptanceTestScenario.create_business_query()
        config = ModelConfig(model_name="grok-3-mini", max_tokens=200)
        
        response = await router.route_request(messages, config)
        
        # Should route to local (cheaper) despite GROK having higher priority
        assert response.provider == "local"
        assert "cannabis extraction" in response.content.lower()
        local_mock.generate_response.assert_called_once()
        grok_mock.generate_response.assert_not_called()


@pytest.mark.asyncio
async def test_high_availability_production_workflow():
    """
    Acceptance Test: Production system requires high availability
    
    As a production system administrator,
    I want automatic failover when providers fail,
    So that the system maintains 99.9% uptime for critical business operations.
    """
    router = ModelRouter(
        default_policy=RoutingPolicy(
            strategy=RoutingStrategy.FAILOVER,
            retry_attempts=2,
            fallback_enabled=True
        )
    )
    
    with patch('backend.ai.providers.grok_provider.GROKProvider') as MockGrok, \
         patch('backend.ai.providers.local_provider.LocalProvider') as MockLocal, \
         patch('backend.ai.model_router.asyncio.sleep', new=AsyncMock()):
        
        # Primary provider (GROK) - will fail
        grok_mock = MockGrok.return_value
        grok_mock.provider_name = "grok"
        grok_mock.available_models = ["grok-3-mini"]
        grok_mock.supported_capabilities = [ModelCapability.TEXT_GENERATION]
        grok_mock.estimate_cost.return_value = 0.02
        grok_mock.initialize = AsyncMock()
        grok_mock.generate_response = AsyncMock(side_effect=ProviderError("Service temporarily unavailable", "grok"))
        grok_mock.supports_capability.return_value = True
        
        # Backup provider (Local) - will succeed
        local_mock = MockLocal.return_value
        local_mock.provider_name = "local"
        local_mock.available_models = ["grok-3-mini"]
        local_mock.supported_capabilities = [ModelCapability.TEXT_GENERATION]
        local_mock.estimate_cost.return_value = 0.01
        local_mock.initialize = AsyncMock()
        local_mock.generate_response = AsyncMock(return_value=type('Response', (), {
            'content': 'Backup system handling your ultrasonic processing query',
            'provider': 'local',
            'model': 'grok-3-mini'
        })())
        local_mock.supports_capability.return_value = True
        
        await router.add_provider(grok_mock, fallback_order=0)  # Primary
        await router.add_provider(local_mock, fallback_order=1)  # Backup
        
        # Critical business query during primary provider outage
        messages = AcceptanceTestScenario.create_technical_query()
        config = ModelConfig(model_name="grok-3-mini", max_tokens=300)
        
        response = await router.route_request(messages, config)
        
        # Should successfully failover to backup
        assert response.provider == "local"
        assert "ultrasonic processing" in response.content.lower()
        
        # Verify both providers were attempted
        grok_mock.generate_response.assert_called()
        local_mock.generate_response.assert_called_once()


@pytest.mark.asyncio
async def test_capability_based_routing_workflow():
    """
    Acceptance Test: Complex queries require specific AI capabilities
    
    As a technical user with complex requirements,
    I want the system to route to providers with the right capabilities,
    So that I get accurate responses for specialized technical queries.
    """
    router = ModelRouter(
        default_policy=RoutingPolicy(
            strategy=RoutingStrategy.CAPABILITY_BASED,
            required_capabilities=[ModelCapability.REASONING, ModelCapability.CODE_GENERATION]
        )
    )
    
    with patch('backend.ai.providers.grok_provider.GROKProvider') as MockGrok, \
         patch('backend.ai.providers.local_provider.LocalProvider') as MockLocal:
        
        # Local provider: basic capabilities only
        local_mock = MockLocal.return_value
        local_mock.provider_name = "local"
        local_mock.available_models = ["grok-3-mini"]
        local_mock.supported_capabilities = [ModelCapability.TEXT_GENERATION]  # Missing required capabilities
        local_mock.estimate_cost.return_value = 0.01
        local_mock.initialize = AsyncMock()
        local_mock.supports_capability.side_effect = lambda cap: cap == ModelCapability.TEXT_GENERATION
        
        # GROK provider: advanced capabilities
        grok_mock = MockGrok.return_value
        grok_mock.provider_name = "grok"
        grok_mock.available_models = ["grok-3-mini"]
        grok_mock.supported_capabilities = [
            ModelCapability.TEXT_GENERATION,
            ModelCapability.REASONING,
            ModelCapability.CODE_GENERATION
        ]
        grok_mock.estimate_cost.return_value = 0.05
        grok_mock.initialize = AsyncMock()
        grok_mock.generate_response = AsyncMock(return_value=type('Response', (), {
            'content': 'Advanced technical analysis with code examples for ultrasonic frequency optimization',
            'provider': 'grok',
            'model': 'grok-3-mini'
        })())
        grok_mock.supports_capability.side_effect = lambda cap: cap in [
            ModelCapability.TEXT_GENERATION,
            ModelCapability.REASONING,
            ModelCapability.CODE_GENERATION
        ]
        
        await router.add_provider(local_mock, priority=10)  # Higher priority but lacks capabilities
        await router.add_provider(grok_mock, priority=5)    # Lower priority but has required capabilities
        
        # Complex technical query requiring reasoning and code generation
        messages = [
            Message(
                role=MessageRole.USER,
                content="Write Python code to calculate optimal ultrasonic frequency based on liquid viscosity and temperature. Include error handling and validation."
            )
        ]
        config = ModelConfig(model_name="grok-3-mini", max_tokens=500)
        
        response = await router.route_request(messages, config)
        
        # Should route to GROK despite lower priority (has required capabilities)
        assert response.provider == "grok"
        assert "technical analysis" in response.content.lower()
        grok_mock.generate_response.assert_called_once()
        local_mock.generate_response.assert_not_called()


@pytest.mark.asyncio
async def test_dynamic_configuration_management_workflow():
    """
    Acceptance Test: System administrators need runtime configuration control
    
    As a system administrator,
    I want to modify routing policies and provider settings without downtime,
    So that I can optimize system performance based on real-time conditions.
    """
    # Start with default configuration
    router = ModelRouter()
    
    with patch('backend.ai.providers.local_provider.LocalProvider') as MockLocal:
        local_mock = MockLocal.return_value
        local_mock.provider_name = "local"
        local_mock.available_models = ["grok-3-mini"]
        local_mock.supported_capabilities = [ModelCapability.TEXT_GENERATION]
        local_mock.estimate_cost.return_value = 0.01
        local_mock.initialize = AsyncMock()
        local_mock.generate_response = AsyncMock(return_value=type('Response', (), {
            'content': 'Response from local provider',
            'provider': 'local',
            'model': 'grok-3-mini'
        })())
        local_mock.supports_capability.return_value = True
        
        await router.add_provider(local_mock, priority=5, max_requests_per_minute=60)
        
        # Initial configuration snapshot
        initial_config = router.get_configuration_snapshot()
        assert initial_config["providers"]["local"]["priority"] == 5
        assert initial_config["providers"]["local"]["max_requests_per_minute"] == 60
        
        # Administrator updates configuration during runtime
        new_config = {
            "default_policy": {
                "strategy": "latency_optimized",
                "max_cost_threshold": 0.08,
                "retry_attempts": 5
            },
            "providers": {
                "local": {
                    "priority": 10,
                    "max_requests_per_minute": 120,
                    "enabled": True
                }
            }
        }
        
        router.load_configuration(new_config)
        
        # Verify configuration was applied
        updated_config = router.get_configuration_snapshot()
        assert updated_config["default_policy"]["strategy"] == "latency_optimized"
        assert updated_config["default_policy"]["max_cost_threshold"] == 0.08
        assert updated_config["providers"]["local"]["priority"] == 10
        assert updated_config["providers"]["local"]["max_requests_per_minute"] == 120
        
        # System continues to work with new configuration
        messages = AcceptanceTestScenario.create_conversation()
        config = ModelConfig(model_name="grok-3-mini")
        
        response = await router.route_request(messages, config)
        assert response.provider == "local"


@pytest.mark.asyncio
async def test_environment_deployment_workflow():
    """
    Acceptance Test: DevOps team deploys with environment-specific configuration
    
    As a DevOps engineer,
    I want to configure the router through environment variables,
    So that I can deploy the same code across dev/staging/prod with different settings.
    """
    # Simulate production environment configuration
    prod_env = {
        "LOCAL_ENABLED": "true",
        "LOCAL_PRIORITY": "1",
        "AI_ROUTING_STRATEGY": "failover",
        "AI_MAX_COST_THRESHOLD": "0.10",
        "AI_MAX_LATENCY_MS": "5000",
        "AI_RETRY_ATTEMPTS": "3"
    }
    
    with patch.dict(os.environ, prod_env), \
         patch('backend.ai.providers.config_manager.ProviderConfigManager') as MockPCM:
        
        # Mock provider config manager
        pcm_mock = MockPCM.return_value
        pcm_mock.get_available_providers.return_value = [
            type('ProviderCred', (), {
                'provider_type': 'local',
                'priority': 1
            })()
        ]
        
        with patch('backend.ai.providers.local_provider.LocalProvider') as MockLocal:
            local_mock = MockLocal.return_value
            local_mock.provider_name = "local"
            local_mock.available_models = ["grok-3-mini"]
            local_mock.supported_capabilities = [ModelCapability.TEXT_GENERATION]
            local_mock.estimate_cost.return_value = 0.02
            local_mock.initialize = AsyncMock()
            local_mock.generate_response = AsyncMock(return_value=type('Response', (), {
                'content': 'Production environment response',
                'provider': 'local',
                'model': 'grok-3-mini'
            })())
            local_mock.supports_capability.return_value = True
            
            pcm_mock.create_provider.return_value = local_mock
            
            # Create router from environment (as would happen in production)
            router = await create_router_from_env()
            
            # Verify environment configuration was applied
            assert router.default_policy.strategy == RoutingStrategy.FAILOVER
            assert router.default_policy.max_cost_threshold == 0.10
            assert router.default_policy.max_latency_threshold == 5.0
            assert router.default_policy.retry_attempts == 3
            assert "local" in router.providers
            
            # Production workload test
            messages = AcceptanceTestScenario.create_business_query()
            config = ModelConfig(model_name="grok-3-mini", max_tokens=250)
            
            response = await router.route_request(messages, config)
            assert response.provider == "local"
            assert "production environment" in response.content.lower()


@pytest.mark.asyncio
async def test_monitoring_and_observability_workflow():
    """
    Acceptance Test: Operations team needs visibility into system health
    
    As an operations engineer,
    I want comprehensive health and performance metrics,
    So that I can monitor system performance and troubleshoot issues.
    """
    router = ModelRouter()
    
    with patch('backend.ai.providers.local_provider.LocalProvider') as MockLocal:
        local_mock = MockLocal.return_value
        local_mock.provider_name = "local"
        local_mock.available_models = ["grok-3-mini"]
        local_mock.supported_capabilities = [ModelCapability.TEXT_GENERATION]
        local_mock.estimate_cost.return_value = 0.01
        local_mock.initialize = AsyncMock()
        local_mock.generate_response = AsyncMock(return_value=type('Response', (), {
            'content': 'Health check response',
            'provider': 'local',
            'model': 'grok-3-mini'
        })())
        local_mock.supports_capability.return_value = True
        local_mock.health_check = AsyncMock(return_value={
            "status": "healthy",
            "latency": 0.05,
            "available": True,
            "last_request": "2025-08-15T07:25:00Z"
        })
        
        await router.add_provider(local_mock, priority=10, weight=1.5)
        
        # Simulate some requests to generate metrics
        messages = AcceptanceTestScenario.create_conversation(1)
        config = ModelConfig(model_name="grok-3-mini")
        
        for _ in range(3):
            await router.route_request(messages, config)
        
        # Operations team checks system health
        status = await router.get_provider_status()
        
        # Verify comprehensive monitoring data is available
        assert "local" in status
        provider_status = status["local"]
        
        # Health metrics
        assert provider_status["status"] == "healthy"
        assert provider_status["available"] == True
        assert provider_status["latency"] == 0.05
        
        # Configuration metrics
        assert provider_status["priority"] == 10
        assert provider_status["weight"] == 1.5
        assert provider_status["enabled"] == True
        
        # Performance metrics
        assert provider_status["circuit_breaker"] == False
        assert provider_status["error_count"] == 0
        assert provider_status["recent_requests"] == 3
        assert "average_latency" in provider_status
