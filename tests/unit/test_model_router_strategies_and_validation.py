"""
Coverage focus for backend.ai.model_router.ModelRouter

Covers:
- _sort_providers across COST_OPTIMIZED, LATENCY_OPTIMIZED, CAPABILITY_BASED,
  ROUND_ROBIN, FAILOVER, LOAD_BALANCED branches
- update_provider_config validation errors (priority, weight, max_requests_per_minute,
  max_cost_per_request, fallback_order) and success updates
- enable/disable provider unknown provider errors
- get_configuration_snapshot structure
"""

import sys
from pathlib import Path
import asyncio
import random
import pytest

# Make backend importable
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.ai.model_router import ModelRouter, RoutingPolicy, RoutingStrategy
from backend.ai.providers.base import LLMProvider, Message, ModelConfig, ModelResponse, ModelCapability


class FakeProvider(LLMProvider):
    def __init__(self, name: str, cost: float, caps, models, latency: float):
        super().__init__(api_key="x")
        self._name = name
        self._cost = float(cost)
        self._caps = list(caps)
        self._models = list(models)
        self._fixed_latency = latency

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def supported_capabilities(self):
        return list(self._caps)

    @property
    def available_models(self):
        return list(self._models)

    async def initialize(self) -> None:
        return None

    async def generate_response(self, messages, config):
        # Simulate latency
        await asyncio.sleep(self._fixed_latency / 1000.0)
        return ModelResponse(
            content=f"resp-{self._name}",
            model=config.model_name,
            provider=self._name,
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )

    async def stream_response(self, messages, config):
        yield f"s-{self._name}"

    async def validate_api_key(self) -> bool:
        return True

    def estimate_cost(self, messages, config) -> float:
        return self._cost

    def count_tokens(self, text: str) -> int:
        return len(text)


@pytest.mark.asyncio
async def test_sorting_strategies_cover_all_branches(monkeypatch):
    router = ModelRouter()

    # Providers: p1 cheaper but slower, p2 more capabilities, p3 weighted heavy
    p1 = FakeProvider("p1", cost=0.001, caps=[ModelCapability.TEXT_GENERATION], models=["grok-3-mini"], latency=50)
    p2 = FakeProvider("p2", cost=0.005, caps=[ModelCapability.TEXT_GENERATION, ModelCapability.STREAMING, ModelCapability.REASONING], models=["grok-3-mini"], latency=10)
    p3 = FakeProvider("p3", cost=0.003, caps=[ModelCapability.TEXT_GENERATION, ModelCapability.STREAMING], models=["grok-3-mini"], latency=30)

    await router.add_provider(p1, priority=5, weight=1.0, fallback_order=2)
    await router.add_provider(p2, priority=10, weight=1.0, fallback_order=0)
    await router.add_provider(p3, priority=7, weight=3.0, fallback_order=1)

    messages = []
    config = ModelConfig("grok-3-mini")

    # COST_OPTIMIZED -> by cost: p1 (0.001), p3 (0.003), p2 (0.005)
    policy = RoutingPolicy(strategy=RoutingStrategy.COST_OPTIMIZED, max_cost_threshold=1.0)
    eligible = await router._get_eligible_providers(messages, config, policy)
    assert eligible[:3] == ["p1", "p3", "p2"]

    # LATENCY_OPTIMIZED -> by avg latency ascending: p2 (10) < p3 (30) < p1 (50)
    # seed for stability in case of ties
    random.seed(42)
    policy.strategy = RoutingStrategy.LATENCY_OPTIMIZED
    eligible = await router._get_eligible_providers(messages, config, policy)
    assert eligible[:3] == ["p2", "p3", "p1"]

    # CAPABILITY_BASED -> by capability count desc: p2(3) > p3(2) > p1(1)
    policy.strategy = RoutingStrategy.CAPABILITY_BASED
    eligible = await router._get_eligible_providers(messages, config, policy)
    assert eligible[:3] == ["p2", "p3", "p1"]

    # ROUND_ROBIN -> preserves input order from eligibility (which for us is provider dict insertion)
    policy.strategy = RoutingStrategy.ROUND_ROBIN
    eligible = await router._get_eligible_providers(messages, config, policy)
    assert set(eligible[:3]) == {"p1", "p2", "p3"}

    # FAILOVER -> by fallback_order: p2(0) < p3(1) < p1(2)
    policy.strategy = RoutingStrategy.FAILOVER
    eligible = await router._get_eligible_providers(messages, config, policy)
    assert eligible[:3] == ["p2", "p3", "p1"]

    # LOAD_BALANCED -> uses weighted shuffle; ensure all present and p3 likely near front
    policy.strategy = RoutingStrategy.LOAD_BALANCED
    eligible = await router._get_eligible_providers(messages, config, policy)
    assert set(eligible[:3]) == {"p1", "p2", "p3"}


def test_update_provider_config_validations_and_snapshot():
    router = ModelRouter()

    # Minimal sync provider for config-only tests
    class P(LLMProvider):
        @property
        def provider_name(self):
            return "x"

        @property
        def supported_capabilities(self):
            return [ModelCapability.TEXT_GENERATION]

        @property
        def available_models(self):
            return ["grok-3-mini"]

        async def initialize(self):
            return None

        async def generate_response(self, messages, config):
            return ModelResponse(content="ok", model=config.model_name, provider="x", usage={})

        async def stream_response(self, messages, config):
            yield "ok"

        async def validate_api_key(self) -> bool:
            return True

        def estimate_cost(self, messages, config) -> float:
            return 0.001

        def count_tokens(self, text: str) -> int:
            return len(text)

    # Create provider
    loop = asyncio.get_event_loop()
    loop.run_until_complete(router.add_provider(P(api_key="k"), priority=1, weight=1.0))

    # Validation errors
    with pytest.raises(ValueError):
        router.update_provider_config("x", {"priority": 0})
    with pytest.raises(ValueError):
        router.update_provider_config("x", {"weight": 0})
    with pytest.raises(ValueError):
        router.update_provider_config("x", {"max_requests_per_minute": 0})
    with pytest.raises(ValueError):
        router.update_provider_config("x", {"max_cost_per_request": 0})
    with pytest.raises(ValueError):
        router.update_provider_config("x", {"fallback_order": -1})

    # Successful updates
    router.update_provider_config("x", {"priority": 9, "weight": 2.0, "enabled": False, "max_requests_per_minute": 30, "max_cost_per_request": 0.2, "fallback_order": 3})

    snap = router.get_configuration_snapshot()
    assert snap["providers"]["x"]["priority"] == 9
    assert abs(snap["providers"]["x"]["weight"] - 2.0) < 1e-9
    assert snap["providers"]["x"]["max_requests_per_minute"] == 30
    assert abs(snap["providers"]["x"]["max_cost_per_request"] - 0.2) < 1e-9
    assert snap["providers"]["x"]["enabled"] is False
    assert snap["providers"]["x"]["fallback_order"] == 3

    # Enable/disable unknown provider errors
    with pytest.raises(ValueError):
        router.enable_provider("nope")
    with pytest.raises(ValueError):
        router.disable_provider("nope")
