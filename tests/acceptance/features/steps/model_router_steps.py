"""
Step definitions for the model_router.feature file.
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock
from behave import given, when, then, step
import asyncio

# Make backend importable
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.ai.model_router import (
    ModelRouter, RoutingPolicy, RoutingStrategy, create_router_from_env
)
from backend.ai.providers.base import (
    ModelConfig, Message, MessageRole, ModelCapability, ProviderError
)

# Helper to create mock providers
def create_mock_provider(name, cost, capabilities, priority=5, should_fail=False):
    provider_mock = AsyncMock()
    provider_mock.provider_name = name
    provider_mock.available_models = ["grok-3-mini"]
    provider_mock.supported_capabilities = capabilities
    provider_mock.estimate_cost.return_value = cost
    provider_mock.initialize = AsyncMock()
    
    if should_fail:
        provider_mock.generate_response.side_effect = ProviderError(f"{name} failed", name)
    else:
        provider_mock.generate_response.return_value = type('Response', (), {
            'content': f'Response from {name}',
            'provider': name,
            'model': 'grok-3-mini',
            'usage': {'input_tokens': 10, 'output_tokens': 20}
        })()

    def supports_capability(cap):
        return cap in capabilities
    provider_mock.supports_capability.side_effect = supports_capability
    
    provider_mock.health_check = AsyncMock(return_value={
        "status": "healthy", "latency": 0.05, "available": True
    })

    return provider_mock

@given('a ModelRouter instance')
def step_impl(context):
    context.router = ModelRouter()
    context.providers = {}

@given('a "{policy_name}" routing policy with a max cost of ${max_cost:f}')
def step_impl(context, policy_name, max_cost):
    strategy = RoutingStrategy[policy_name.upper()]
    context.router.default_policy = RoutingPolicy(
        strategy=strategy,
        max_cost_threshold=max_cost
    )

@given('a "{provider_name}" provider is configured with a cost of ${cost:f} and priority {priority:d}')
def step_impl(context, provider_name, cost, priority):
    capabilities = [ModelCapability.TEXT_GENERATION, ModelCapability.REASONING]
    if provider_name == "grok":
        capabilities.append(ModelCapability.CODE_GENERATION)
    
    mock_provider = create_mock_provider(provider_name, cost, capabilities)
    context.providers[provider_name] = mock_provider
    asyncio.run(context.router.add_provider(mock_provider, priority=priority))

@when('a business user sends a query')
def step_impl(context):
    messages = [Message(role=MessageRole.USER, content="Business query")]
    config = ModelConfig(model_name="grok-3-mini")
    context.response = asyncio.run(context.router.route_request(messages, config))

@then('the router should select the "{provider_name}" provider')
def step_impl(context, provider_name):
    assert context.response.provider == provider_name, f"Expected {provider_name}, got {context.response.provider}"

@then('the "{provider_name}" provider should not be called')
def step_impl(context, provider_name):
    context.providers[provider_name].generate_response.assert_not_called()

@given('a "{policy_name}" routing policy with fallback enabled')
def step_impl(context, policy_name):
    strategy = RoutingStrategy[policy_name.upper()]
    context.router.default_policy = RoutingPolicy(strategy=strategy, fallback_enabled=True, retry_attempts=1)

@given('a primary "{provider_name}" provider is configured to fail')
def step_impl(context, provider_name):
    mock_provider = create_mock_provider(provider_name, 0.02, [ModelCapability.TEXT_GENERATION], should_fail=True)
    context.providers[provider_name] = mock_provider
    asyncio.run(context.router.add_provider(mock_provider, fallback_order=0))

@given('a backup "{provider_name}" provider is configured to succeed')
def step_impl(context, provider_name):
    mock_provider = create_mock_provider(provider_name, 0.01, [ModelCapability.TEXT_GENERATION])
    context.providers[provider_name] = mock_provider
    asyncio.run(context.router.add_provider(mock_provider, fallback_order=1))

@when('a user sends a technical query')
def step_impl(context):
    messages = [Message(role=MessageRole.USER, content="Technical query")]
    config = ModelConfig(model_name="grok-3-mini")
    # Patch sleep to avoid delays during retry
    with patch('asyncio.sleep', new=AsyncMock()):
        context.response = asyncio.run(context.router.route_request(messages, config))

@then('the router should select the "{provider_name}" provider after the primary fails')
def step_impl(context, provider_name):
    assert context.response.provider == provider_name
    context.providers['grok'].generate_response.assert_called()
    context.providers['local'].generate_response.assert_called_once()

@given('a "{policy}" routing policy requiring "{cap1}" and "{cap2}"')
def step_impl(context, policy, cap1, cap2):
    context.router.default_policy = RoutingPolicy(
        strategy=RoutingStrategy.CAPABILITY_BASED,
        required_capabilities=[ModelCapability[cap1], ModelCapability[cap2]]
    )

@given('a "{p_name}" provider is configured with "{cap}" capability and priority {priority:d}')
def step_impl(context, p_name, cap, priority):
    mock_provider = create_mock_provider(p_name, 0.01, [ModelCapability[cap]])
    context.providers[p_name] = mock_provider
    asyncio.run(context.router.add_provider(mock_provider, priority=priority))

@given('a "{p_name}" provider is configured with "{cap1}" and "{cap2}" capabilities and priority {priority:d}')
def step_impl(context, p_name, cap1, cap2, priority):
    capabilities = [ModelCapability[cap1], ModelCapability[cap2], ModelCapability.TEXT_GENERATION]
    mock_provider = create_mock_provider(p_name, 0.05, capabilities)
    context.providers[p_name] = mock_provider
    asyncio.run(context.router.add_provider(mock_provider, priority=priority))

@when('a user sends a query requiring code generation')
def step_impl(context):
    messages = [Message(role=MessageRole.USER, content="Code gen query")]
    config = ModelConfig(model_name="grok-3-mini")
    context.response = asyncio.run(context.router.route_request(messages, config))

@given('a "{p_name}" provider is configured with priority {priority:d} and {rpm:d} max requests per minute')
def step_impl(context, p_name, priority, rpm):
    mock_provider = create_mock_provider(p_name, 0.01, [ModelCapability.TEXT_GENERATION])
    context.providers[p_name] = mock_provider
    asyncio.run(context.router.add_provider(mock_provider, priority=priority, max_requests_per_minute=rpm))

@when('the administrator loads a new configuration with priority {priority:d} and {rpm:d} max requests per minute')
def step_impl(context, priority, rpm):
    new_config = {
        "providers": {
            "local": {"priority": priority, "max_requests_per_minute": rpm, "enabled": True}
        }
    }
    context.router.load_configuration(new_config)

@then('the router\'s configuration should be updated successfully')
def step_impl(context):
    config = context.router.get_configuration_snapshot()
    assert config['providers']['local']['priority'] == 10
    assert config['providers']['local']['max_requests_per_minute'] == 120

@then('the system should continue to operate correctly')
def step_impl(context):
    messages = [Message(role=MessageRole.USER, content="Test query")]
    config = ModelConfig(model_name="grok-3-mini")
    response = asyncio.run(context.router.route_request(messages, config))
    assert response.provider == 'local'

@given('the environment is configured for "{strategy}" routing with a "{provider_name}" provider')
def step_impl(context, strategy, provider_name):
    context.env_vars = {
        f"{provider_name.upper()}_ENABLED": "true",
        f"{provider_name.upper()}_PRIORITY": "1",
        "AI_ROUTING_STRATEGY": strategy
    }

@when('the router is created from the environment')
def step_impl(context):
    with patch.dict(os.environ, context.env_vars), \
         patch('backend.ai.providers.config_manager.ProviderConfigManager') as MockPCM:
        
        pcm_mock = MockPCM.return_value
        pcm_mock.get_available_providers.return_value = [
            type('ProviderCred', (), {'provider_type': 'local', 'priority': 1})()
        ]
        
        mock_provider = create_mock_provider('local', 0.01, [ModelCapability.TEXT_GENERATION])
        pcm_mock.create_provider.return_value = mock_provider
        
        context.router = asyncio.run(create_router_from_env())

@then('its configuration should match the environment variables')
def step_impl(context):
    assert context.router.default_policy.strategy == RoutingStrategy.FAILOVER
    assert 'local' in context.router.providers

@given('a "{p_name}" provider is configured for health checks')
def step_impl(context, p_name):
    mock_provider = create_mock_provider(p_name, 0.01, [ModelCapability.TEXT_GENERATION])
    context.providers[p_name] = mock_provider
    asyncio.run(context.router.add_provider(mock_provider))

@when('{count:d} requests are sent to the router')
def step_impl(context, count):
    messages = [Message(role=MessageRole.USER, content="Health check query")]
    config = ModelConfig(model_name="grok-3-mini")
    for _ in range(count):
        asyncio.run(context.router.route_request(messages, config))

@then('the provider status should report as "{status}"')
def step_impl(context, status):
    provider_status = asyncio.run(context.router.get_provider_status())['local']
    assert provider_status['status'] == status

@then('show {count:d} recent requests')
def step_impl(context, count):
    provider_status = asyncio.run(context.router.get_provider_status())['local']
    assert provider_status['recent_requests'] == count
