"""
Targeted tests to improve coverage for backend.ai.model_router.ModelRouter

Covers:
- stream_request fallback when first provider fails and second succeeds
- rate-limit skip path in route_request
- circuit breaker activation on repeated errors and reset via reset_circuit_breakers()
- get_provider_status aggregation and values
- load_configuration updates default policy and provider configs
"""

import sys
from pathlib import Path
import asyncio
import pytest

# Make backend importable
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.ai.model_router import ModelRouter, RoutingPolicy, RoutingStrategy
from backend.ai.providers.base import LLMProvider, Message, ModelConfig, ModelResponse, ModelCapability, ProviderError


class FakeOkProvider(LLMProvider):
    def __init__(self, name: str = "ok", models=None, **kwargs):
        super().__init__(api_key="x", **kwargs)
        self._name = name
        self._models = models or ["grok-3-mini", "local-small"]

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def supported_capabilities(self):
        return [ModelCapability.TEXT_GENERATION, ModelCapability.STREAMING]

    @property
    def available_models(self):
        return list(self._models)

    async def initialize(self) -> None:
        return None

    async def generate_response(self, messages, config):
        return ModelResponse(
            content="ok",
            model=config.model_name,
            provider=self._name,
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )

    async def stream_response(self, messages, config):
        for chunk in ["o", "k"]:
            yield chunk

    async def validate_api_key(self) -> bool:
        return True

    def estimate_cost(self, messages, config) -> float:
        return 0.001

    def count_tokens(self, text: str) -> int:
        return len(text)


class FakeFailProvider(FakeOkProvider):
    def __init__(self, name: str = "fail", **kwargs):
        super().__init__(name=name, **kwargs)

    async def generate_response(self, messages, config):
        raise ProviderError("boom", self._name)

    async def stream_response(self, messages, config):
        raise ProviderError("boom", self._name)

    async def validate_api_key(self) -> bool:
        return True

    def estimate_cost(self, messages, config) -> float:
        return 0.002


@pytest.mark.asyncio
async def test_stream_request_fallback_to_second_provider():
    router = ModelRouter()
    # Add failing provider as primary, ok provider as fallback
    await router.add_provider(FakeFailProvider(name="p1"), priority=10, fallback_order=0)
    await router.add_provider(FakeOkProvider(name="p2"), priority=9, fallback_order=1)

    messages = [Message(role=__import__("backend.ai.providers.base", fromlist=["MessageRole"]).MessageRole.USER, content="hi")]
    config = ModelConfig("grok-3-mini")

    policy = RoutingPolicy(strategy=RoutingStrategy.FAILOVER, retry_attempts=1)

    chunks = []
    async for c in router.stream_request(messages, config, policy):
        chunks.append(c)
    assert "".join(chunks) == "ok"


@pytest.mark.asyncio
async def test_route_request_skips_when_rate_limited():
    router = ModelRouter(default_policy=RoutingPolicy(strategy=RoutingStrategy.FAILOVER))
    await router.add_provider(FakeOkProvider(name="rl"), priority=10, fallback_order=0)

    # Simulate immediate rate limit by setting provider limit to 0
    router.providers["rl"].max_requests_per_minute = 0

    messages = [Message(role=__import__("backend.ai.providers.base", fromlist=["MessageRole"]).MessageRole.USER, content="hi")]
    config = ModelConfig("grok-3-mini")

    # No eligible provider should process due to rate limit; expect ProviderError
    with pytest.raises(ProviderError):
        await router.route_request(messages, config)


@pytest.mark.asyncio
async def test_circuit_breaker_activation_and_reset():
    router = ModelRouter()
    await router.add_provider(FakeFailProvider(name="bad"), priority=10)

    messages = [Message(role=__import__("backend.ai.providers.base", fromlist=["MessageRole"]).MessageRole.USER, content="x")]
    config = ModelConfig("grok-3-mini")

    # Trigger multiple errors to activate circuit breaker (>5)
    with pytest.raises(ProviderError):
        await router.route_request(messages, config, RoutingPolicy(retry_attempts=1))
    with pytest.raises(ProviderError):
        await router.route_request(messages, config, RoutingPolicy(retry_attempts=1))
    with pytest.raises(ProviderError):
        await router.route_request(messages, config, RoutingPolicy(retry_attempts=1))
    with pytest.raises(ProviderError):
        await router.route_request(messages, config, RoutingPolicy(retry_attempts=1))
    with pytest.raises(ProviderError):
        await router.route_request(messages, config, RoutingPolicy(retry_attempts=1))
    with pytest.raises(ProviderError):
        await router.route_request(messages, config, RoutingPolicy(retry_attempts=1))

    # Circuit breaker should be set
    assert router._circuit_breakers.get("bad", False) is True

    # Reset
    await router.reset_circuit_breakers()
    assert router._circuit_breakers.get("bad", False) is False
    assert router._error_counts.get("bad", -1) == 0


@pytest.mark.asyncio
async def test_get_provider_status_snapshot():
    router = ModelRouter()
    await router.add_provider(FakeOkProvider(name="ok"), priority=2, weight=2.5)

    status = await router.get_provider_status()
    assert "ok" in status
    s = status["ok"]
    assert s["enabled"] is True
    assert s["priority"] == 2
    assert s["weight"] == 2.5
    assert "average_latency" in s
    assert "recent_requests" in s
    assert s["api_key_valid"] in (True, False) or "status" in s  # health_check contract


@pytest.mark.asyncio
async def test_load_configuration_updates_policy_and_providers():
    router = ModelRouter()
    await router.add_provider(FakeOkProvider(name="ok"), priority=5, weight=1.0)

    cfg = {
        "default_policy": {
            "strategy": "latency_optimized",
            "max_cost_threshold": 0.02,
            "max_latency_threshold": 3.0,
            "required_capabilities": ["text_generation"],
            "preferred_providers": ["ok"],
            "fallback_enabled": True,
            "retry_attempts": 2,
        },
        "providers": {
            "ok": {
                "priority": 9,
                "weight": 3.0,
                "max_requests_per_minute": 30,
                "max_cost_per_request": 0.2,
                "enabled": True,
                "fallback_order": 1,
            }
        },
    }

    router.load_configuration(cfg)

    # Policy checks
    assert router.default_policy.strategy == RoutingStrategy.LATENCY_OPTIMIZED
    assert abs(router.default_policy.max_cost_threshold - 0.02) < 1e-9
    assert abs(router.default_policy.max_latency_threshold - 3.0) < 1e-9
    assert router.default_policy.retry_attempts == 2

    # Provider config checks
    pc = router.providers["ok"]
    assert pc.priority == 9
    assert abs(pc.weight - 3.0) < 1e-9
    assert pc.max_requests_per_minute == 30
    assert abs(pc.max_cost_per_request - 0.2) < 1e-9
    assert pc.enabled is True
    assert pc.fallback_order == 1
