import os
import asyncio
import time
from typing import Any, AsyncGenerator, Dict, List

import pytest

from backend.ai.model_router import (
    ModelRouter,
    RoutingPolicy,
    RoutingStrategy,
    _policy_from_env,
)
from backend.ai.providers.base import (
    LLMProvider,
    Message,
    MessageRole,
    ModelCapability,
    ModelConfig,
    ModelResponse,
    RateLimitError,
)


class FakeProvider(LLMProvider):
    def __init__(self, name: str, models: List[str] = None, cost: float = 0.01, capabilities=None):
        super().__init__(api_key="test")
        self._name = name
        self._models = models or ["grok-3-mini"]
        self._cost = cost
        self._capabilities = capabilities or [ModelCapability.TEXT_GENERATION]

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def supported_capabilities(self) -> List[ModelCapability]:
        return list(self._capabilities)

    @property
    def available_models(self) -> List[str]:
        return list(self._models)

    async def initialize(self) -> None:
        return None

    async def generate_response(self, messages: List[Message], config: ModelConfig) -> ModelResponse:
        # Simulate slight latency
        await asyncio.sleep(0)
        content = "".join(m.content for m in messages if m.role == MessageRole.USER)
        return ModelResponse(
            content=f"ok:{self._name}:{content}",
            model=config.model_name,
            provider=self._name,
            usage={"tokens": 1},
        )

    async def stream_response(self, messages: List[Message], config: ModelConfig) -> AsyncGenerator[str, None]:
        yield "part1"
        yield "part2"

    async def validate_api_key(self) -> bool:
        return True

    def estimate_cost(self, messages: List[Message], config: ModelConfig) -> float:
        return float(self._cost)

    def count_tokens(self, text: str) -> int:
        return len(text.split())


@pytest.mark.asyncio
async def test_sorting_and_routing_cost_optimized():
    router = ModelRouter()
    cheap = FakeProvider("cheap", cost=0.001)
    mid = FakeProvider("mid", cost=0.01)
    pricey = FakeProvider("pricey", cost=0.2)

    await router.add_provider(cheap, priority=5)
    await router.add_provider(mid, priority=10)
    await router.add_provider(pricey, priority=1)

    policy = RoutingPolicy(strategy=RoutingStrategy.COST_OPTIMIZED, max_cost_threshold=0.05)

    msgs = [Message(role=MessageRole.USER, content="hi")]
    cfg = ModelConfig(model_name="grok-3-mini")

    resp = await router.route_request(msgs, cfg, policy)
    assert resp.provider == "cheap"


@pytest.mark.asyncio
async def test_rate_limit_and_circuit_breaker():
    router = ModelRouter()
    prov = FakeProvider("prov")
    await router.add_provider(prov, max_requests_per_minute=1)

    msgs = [Message(role=MessageRole.USER, content="x")]
    cfg = ModelConfig(model_name="grok-3-mini")

    # First request ok
    _ = await router.route_request(msgs, cfg)

    # Immediately second should be rate limited; router should skip and fail
    with pytest.raises(Exception):
        await router.route_request(msgs, cfg)

    # Record errors to trigger circuit breaker
    for _ in range(7):
        router._record_error("prov")
    assert router._circuit_breakers["prov"] is True


@pytest.mark.asyncio
async def test_weighted_shuffle_and_latency_strategy():
    router = ModelRouter()
    a = FakeProvider("a")
    b = FakeProvider("b")
    await router.add_provider(a, weight=0.1)
    await router.add_provider(b, weight=1.0)

    # Record latencies
    router._record_request("a", latency=5.0)
    router._record_request("b", latency=1.0)

    # LATENCY_OPTIMIZED should sort b before a
    ordered = router._sort_providers(["a", "b"], RoutingPolicy(strategy=RoutingStrategy.LATENCY_OPTIMIZED), [], ModelConfig(model_name="grok-3-mini"))
    assert ordered[0] == "b"

    # LOAD_BALANCED returns a shuffled order containing both; sanity check length
    res = router._sort_providers(["a", "b"], RoutingPolicy(strategy=RoutingStrategy.LOAD_BALANCED), [], ModelConfig(model_name="grok-3-mini"))
    assert set(res) == {"a", "b"}


@pytest.mark.asyncio
async def test_update_config_and_snapshots_and_status():
    router = ModelRouter()
    p = FakeProvider("p")
    await router.add_provider(p, priority=1, weight=1.0)

    # Update defaults
    router.update_default_policy(RoutingPolicy(strategy=RoutingStrategy.ROUND_ROBIN))

    # Update provider config
    router.update_provider_config("p", {"priority": 2, "weight": 2.0, "enabled": False, "max_requests_per_minute": 120, "max_cost_per_request": 0.2, "fallback_order": 3})
    snap = router.get_configuration_snapshot()
    assert snap["providers"]["p"]["priority"] == 2

    router.enable_provider("p")
    assert router.providers["p"].enabled is True
    router.disable_provider("p")
    assert router.providers["p"].enabled is False

    status = await router.get_provider_status()
    assert "p" in status
    assert "average_latency" in status["p"]


@pytest.mark.asyncio
async def test_policy_from_env_mapping(monkeypatch):
    monkeypatch.setenv("AI_ROUTING_STRATEGY", "latency_optimized")
    monkeypatch.setenv("AI_MAX_COST_THRESHOLD", "0.02")
    monkeypatch.setenv("AI_MAX_LATENCY_MS", "5000")
    monkeypatch.setenv("AI_RETRY_ATTEMPTS", "4")

    policy = _policy_from_env()
    assert policy.strategy == RoutingStrategy.LATENCY_OPTIMIZED
    assert policy.max_cost_threshold == 0.02
    assert policy.max_latency_threshold == 5.0
    assert policy.retry_attempts == 4
