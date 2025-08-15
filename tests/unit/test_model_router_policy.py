"""
Unit tests for ModelRouter routing policy schema and behavior (Task 4.2.1)

Covers:
- RoutingPolicy defaults and fields
- Capability-based eligibility filtering
- Cost threshold filtering (policy and provider-specific)
- Sorting strategies: cost_optimized, latency_optimized, capability_based,
  round_robin, failover, load_balanced

Author: Cannasol Technologies (cascade-03)
Date: 2025-08-15
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncGenerator

import pytest

# Ensure backend is importable
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from ai.model_router import (
    ModelRouter,
    RoutingPolicy,
    RoutingStrategy,
)
from ai.providers.base import (
    LLMProvider,
    Message,
    MessageRole,
    ModelConfig,
    ModelResponse,
    ModelCapability,
)


class FakeProvider(LLMProvider):
    """Minimal fake provider for router testing with controllable behavior."""

    def __init__(
        self,
        name: str,
        cost: float,
        models: List[str],
        capabilities: List[ModelCapability],
        response_text: str = "ok",
        api_key: str = "test",
        base_url: Optional[str] = None,
    ):
        super().__init__(api_key=api_key, base_url=base_url)
        self._name = name
        self._cost = cost
        self._models = models
        self._capabilities = capabilities
        self._response_text = response_text

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def supported_capabilities(self) -> List[ModelCapability]:
        return self._capabilities

    @property
    def available_models(self) -> List[str]:
        return self._models

    async def initialize(self) -> None:
        return None

    async def generate_response(
        self, messages: List[Message], config: ModelConfig
    ) -> ModelResponse:
        return ModelResponse(
            content=self._response_text,
            model=config.model_name,
            provider=self._name,
            usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        )

    async def stream_response(
        self, messages: List[Message], config: ModelConfig
    ) -> AsyncGenerator[str, None]:
        yield self._response_text

    async def validate_api_key(self) -> bool:
        return True

    def estimate_cost(self, messages: List[Message], config: ModelConfig) -> float:
        return self._cost

    def count_tokens(self, text: str) -> int:
        return len(text.split())


def make_message(text: str = "hi") -> List[Message]:
    return [Message(role=MessageRole.USER, content=text)]


@pytest.mark.asyncio
async def test_routing_policy_defaults():
    policy = RoutingPolicy()
    assert policy.strategy == RoutingStrategy.COST_OPTIMIZED
    assert policy.max_cost_threshold == 0.05
    assert policy.max_latency_threshold == 10.0
    assert policy.required_capabilities == []
    assert policy.preferred_providers == []
    assert policy.fallback_enabled is True
    assert policy.retry_attempts == 3


@pytest.mark.asyncio
async def test_capability_filtering_excludes_non_supporting():
    router = ModelRouter()

    p_text = FakeProvider(
        name="text-only",
        cost=0.01,
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION],
    )
    p_function = FakeProvider(
        name="func",
        cost=0.01,
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.FUNCTION_CALLING],
    )

    await router.add_provider(p_text)
    await router.add_provider(p_function)

    policy = RoutingPolicy(
        strategy=RoutingStrategy.CAPABILITY_BASED,
        required_capabilities=[ModelCapability.FUNCTION_CALLING],
        max_cost_threshold=1.0,
    )

    # Access protected method for targeted unit behavior check
    eligible = await router._get_eligible_providers(
        messages=make_message(),
        config=ModelConfig(model_name="grok-3-mini"),
        policy=policy,
    )

    # Only provider with FUNCTION_CALLING should be eligible
    assert eligible == ["func"]


@pytest.mark.asyncio
async def test_cost_threshold_filters_providers():
    router = ModelRouter()

    cheap = FakeProvider(
        name="cheap",
        cost=0.01,
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION],
    )
    pricey = FakeProvider(
        name="pricey",
        cost=0.10,
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION],
    )

    await router.add_provider(cheap)
    await router.add_provider(pricey)

    policy = RoutingPolicy(strategy=RoutingStrategy.COST_OPTIMIZED, max_cost_threshold=0.05)

    eligible = await router._get_eligible_providers(
        messages=make_message(),
        config=ModelConfig(model_name="grok-3-mini"),
        policy=policy,
    )

    assert eligible == ["cheap"], "Providers above policy max_cost_threshold must be excluded"


@pytest.mark.asyncio
async def test_cost_optimized_sorting_orders_by_estimated_cost():
    router = ModelRouter()

    p1 = FakeProvider(
        name="p1",
        cost=0.03,
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION],
    )
    p2 = FakeProvider(
        name="p2",
        cost=0.01,
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION],
    )
    p3 = FakeProvider(
        name="p3",
        cost=0.02,
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION],
    )

    await router.add_provider(p1)
    await router.add_provider(p2)
    await router.add_provider(p3)

    # All eligible under a high threshold, then sorted by cost asc
    policy = RoutingPolicy(strategy=RoutingStrategy.COST_OPTIMIZED, max_cost_threshold=1.0)

    eligible = await router._get_eligible_providers(
        messages=make_message(),
        config=ModelConfig(model_name="grok-3-mini"),
        policy=policy,
    )

    assert eligible == ["p2", "p3", "p1"]


@pytest.mark.asyncio
async def test_latency_optimized_uses_latency_history():
    router = ModelRouter()

    slow = FakeProvider(
        name="slow",
        cost=0.01,
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION],
    )
    fast = FakeProvider(
        name="fast",
        cost=0.01,
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION],
    )

    await router.add_provider(slow)
    await router.add_provider(fast)

    # Simulate recorded latencies
    router._record_request("slow", latency=2.0)
    router._record_request("fast", latency=0.5)

    policy = RoutingPolicy(strategy=RoutingStrategy.LATENCY_OPTIMIZED, max_cost_threshold=1.0)

    eligible = await router._get_eligible_providers(
        messages=make_message(),
        config=ModelConfig(model_name="grok-3-mini"),
        policy=policy,
    )

    assert eligible[0] == "fast"


@pytest.mark.asyncio
async def test_failover_sorted_by_fallback_order():
    router = ModelRouter()

    a = FakeProvider(
        name="a",
        cost=0.01,
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION],
    )
    b = FakeProvider(
        name="b",
        cost=0.01,
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION],
    )

    await router.add_provider(a, fallback_order=1)
    await router.add_provider(b, fallback_order=0)

    policy = RoutingPolicy(strategy=RoutingStrategy.FAILOVER, max_cost_threshold=1.0)

    eligible = await router._get_eligible_providers(
        messages=make_message(),
        config=ModelConfig(model_name="grok-3-mini"),
        policy=policy,
    )

    assert eligible == ["b", "a"], "Lower fallback_order should come first"


@pytest.mark.asyncio
async def test_round_robin_preserves_input_order_when_all_equal():
    router = ModelRouter()

    p1 = FakeProvider("p1", 0.01, ["grok-3-mini"], [ModelCapability.TEXT_GENERATION])
    p2 = FakeProvider("p2", 0.01, ["grok-3-mini"], [ModelCapability.TEXT_GENERATION])

    await router.add_provider(p1)
    await router.add_provider(p2)

    policy = RoutingPolicy(strategy=RoutingStrategy.ROUND_ROBIN, max_cost_threshold=1.0)

    eligible = await router._get_eligible_providers(
        messages=make_message(),
        config=ModelConfig(model_name="grok-3-mini"),
        policy=policy,
    )

    assert eligible == ["p1", "p2"], "Round-robin returns providers as-is (stateless)"


@pytest.mark.asyncio
async def test_load_balanced_weighted_shuffle_is_permutation():
    router = ModelRouter()

    p1 = FakeProvider("p1", 0.01, ["grok-3-mini"], [ModelCapability.TEXT_GENERATION])
    p2 = FakeProvider("p2", 0.01, ["grok-3-mini"], [ModelCapability.TEXT_GENERATION])
    p3 = FakeProvider("p3", 0.01, ["grok-3-mini"], [ModelCapability.TEXT_GENERATION])

    await router.add_provider(p1)
    await router.add_provider(p2)
    await router.add_provider(p3)

    policy = RoutingPolicy(strategy=RoutingStrategy.LOAD_BALANCED, max_cost_threshold=1.0)

    eligible = await router._get_eligible_providers(
        messages=make_message(),
        config=ModelConfig(model_name="grok-3-mini"),
        policy=policy,
    )

    assert sorted(eligible) == ["p1", "p2", "p3"], "Weighted shuffle should be a permutation of inputs"
