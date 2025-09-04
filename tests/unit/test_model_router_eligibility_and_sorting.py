import asyncio
from typing import List, AsyncGenerator, Dict, Any

import pytest

from backend.ai.model_router import (
    ModelRouter,
    RoutingPolicy,
    RoutingStrategy,
)
from backend.ai.providers.base import (
    LLMProvider,
    Message,
    MessageRole,
    ModelConfig,
    ModelResponse,
    ModelCapability,
)


class SimpleProvider(LLMProvider):
    def __init__(self, name: str, cost: float, caps: List[ModelCapability] | None = None):
        super().__init__(api_key="key")
        self._name = name
        self._cost = cost
        self._caps = caps or [ModelCapability.TEXT_GENERATION]

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def supported_capabilities(self) -> List[ModelCapability]:
        return self._caps

    @property
    def available_models(self) -> List[str]:
        return ["grok-3-mini"]

    async def initialize(self) -> None:
        return None

    async def generate_response(self, messages: List[Message], config: ModelConfig) -> ModelResponse:
        return ModelResponse(
            content=f"ok-{self._name}",
            model=config.model_name,
            provider=self._name,
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )

    async def stream_response(self, messages: List[Message], config: ModelConfig) -> AsyncGenerator[str, None]:
        yield f"chunk-{self._name}"

    async def validate_api_key(self) -> bool:
        return True

    def estimate_cost(self, messages: List[Message], config: ModelConfig) -> float:
        return float(self._cost)

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)


@pytest.mark.asyncio
async def test_eligibility_filters_capability_and_cost():
    router = ModelRouter()

    p1 = SimpleProvider("p1", cost=0.01, caps=[ModelCapability.TEXT_GENERATION])
    p2 = SimpleProvider("p2", cost=0.10, caps=[ModelCapability.TEXT_GENERATION])
    p3 = SimpleProvider("p3", cost=0.02, caps=[ModelCapability.VISION])  # wrong capability

    await router.add_provider(p1, priority=5, max_cost_per_request=0.05)
    await router.add_provider(p2, priority=5, max_cost_per_request=0.05)  # too expensive per-request
    await router.add_provider(p3, priority=5, max_cost_per_request=0.05)

    policy = RoutingPolicy(
        strategy=RoutingStrategy.COST_OPTIMIZED,
        max_cost_threshold=0.05,
        required_capabilities=[ModelCapability.TEXT_GENERATION],
    )

    messages = [Message(role=MessageRole.USER, content="hello")]
    config = ModelConfig(model_name="grok-3-mini")

    eligible = await router._get_eligible_providers(messages, config, policy)
    # Only p1 should qualify (p2 over thresholds, p3 missing capability)
    assert eligible == ["p1"]


@pytest.mark.asyncio
async def test_sorting_strategies_cost_latency_capability_roundrobin_failover_loadbalanced(monkeypatch):
    router = ModelRouter()

    p1 = SimpleProvider("a", cost=0.02)
    p2 = SimpleProvider("b", cost=0.01)
    p3 = SimpleProvider("c", cost=0.03)

    await router.add_provider(p1, priority=1, weight=1.0, fallback_order=2)
    await router.add_provider(p2, priority=3, weight=3.0, fallback_order=1)
    await router.add_provider(p3, priority=2, weight=2.0, fallback_order=3)

    names = ["a", "b", "c"]
    msgs = [Message(role=MessageRole.USER, content="x")]
    cfg = ModelConfig(model_name="grok-3-mini")

    # COST_OPTIMIZED should use cost_map ascending: b (0.01), a (0.02), c (0.03)
    cost_sorted = router._sort_providers(
        names,
        RoutingPolicy(strategy=RoutingStrategy.COST_OPTIMIZED),
        msgs,
        cfg,
        cost_map={"a": 0.02, "b": 0.01, "c": 0.03},
    )
    assert cost_sorted == ["b", "a", "c"]

    # LATENCY_OPTIMIZED: patch average latency
    monkeypatch.setattr(router, "_get_average_latency", lambda n: {"a": 0.5, "b": 0.2, "c": 0.7}[n])
    lat_sorted = router._sort_providers(names, RoutingPolicy(strategy=RoutingStrategy.LATENCY_OPTIMIZED), msgs, cfg)
    assert lat_sorted == ["b", "a", "c"]

    # CAPABILITY_BASED: ensure providers with TEXT_GENERATION come first (all have it)
    cap_sorted = router._sort_providers(names, RoutingPolicy(strategy=RoutingStrategy.CAPABILITY_BASED), msgs, cfg)
    assert cap_sorted == names  # stability when all equal

    # ROUND_ROBIN: relies on recent request counts; seed _request_counts to make a deterministic order
    router._request_counts["a"] = [1, 2]
    router._request_counts["b"] = [1]
    router._request_counts["c"] = []
    rr_sorted = router._sort_providers(names, RoutingPolicy(strategy=RoutingStrategy.ROUND_ROBIN), msgs, cfg)
    assert rr_sorted == ["c", "b", "a"]

    # FAILOVER: sort by fallback_order ascending
    fo_sorted = router._sort_providers(names, RoutingPolicy(strategy=RoutingStrategy.FAILOVER), msgs, cfg)
    assert fo_sorted == ["b", "a", "c"]

    # LOAD_BALANCED: ensure result contains all names and is deterministic with patched shuffle
    # Monkeypatch _weighted_shuffle to return a specific order for test stability
    monkeypatch.setattr(router, "_weighted_shuffle", lambda ns: ["b", "c", "a"]) 
    lb_sorted = router._sort_providers(names, RoutingPolicy(strategy=RoutingStrategy.LOAD_BALANCED), msgs, cfg)
    assert lb_sorted == ["b", "c", "a"]


@pytest.mark.asyncio
async def test_get_provider_status_and_configuration_load(monkeypatch):
    router = ModelRouter()

    p = SimpleProvider("prov", cost=0.02)
    await router.add_provider(p, priority=4, weight=2.5, max_requests_per_minute=30, max_cost_per_request=0.07, enabled=True, fallback_order=1)

    # Seed histories to check aggregation fields
    router._latency_history["prov"] = [0.1, 0.2, 0.3]
    router._request_counts["prov"] = [1.0, 2.0]

    status = await router.get_provider_status()
    assert "prov" in status
    s = status["prov"]
    assert s["enabled"] is True
    assert s["priority"] == 4
    assert s["weight"] == 2.5
    assert s["average_latency"] >= 0.0
    assert s["recent_requests"] == 2

    # Now load new configuration and assert updates applied
    config_dict: Dict[str, Any] = {
        "default_policy": {
            "strategy": RoutingStrategy.FAILOVER.value,
            "max_cost_threshold": 0.11,
            "max_latency_threshold": 3.0,
            "required_capabilities": [ModelCapability.TEXT_GENERATION.value],
            "preferred_providers": ["prov"],
            "fallback_enabled": False,
            "retry_attempts": 5,
        },
        "providers": {
            "prov": {
                "priority": 10,
                "weight": 1.0,
                "max_requests_per_minute": 120,
                "max_cost_per_request": 0.09,
                "enabled": False,
                "fallback_order": 0,
            }
        },
    }

    router.load_configuration(config_dict)

    snap = router.get_configuration_snapshot()
    assert snap["default_policy"]["strategy"] == RoutingStrategy.FAILOVER.value
    assert abs(snap["default_policy"]["max_cost_threshold"] - 0.11) < 1e-9
    assert snap["default_policy"]["retry_attempts"] == 5
    assert snap["providers"]["prov"]["priority"] == 10
    assert snap["providers"]["prov"]["enabled"] is False
