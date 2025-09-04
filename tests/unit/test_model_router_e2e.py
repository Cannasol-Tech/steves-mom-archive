import os
from typing import List, AsyncGenerator

import pytest

from backend.ai.model_router import ModelRouter, RoutingPolicy, RoutingStrategy, create_default_router
from backend.ai.providers.base import LLMProvider, Message, MessageRole, ModelConfig, ModelResponse, ModelCapability, ProviderError, RateLimitError


class OkProv(LLMProvider):
    def __init__(self, name: str, cost: float):
        super().__init__(api_key="key")
        self._name = name
        self._cost = cost

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def supported_capabilities(self) -> List[ModelCapability]:
        return [ModelCapability.TEXT_GENERATION]

    @property
    def available_models(self) -> List[str]:
        return ["grok-3-mini"]

    async def initialize(self) -> None:  # pragma: no cover - noop
        return None

    async def generate_response(self, messages: List[Message], config: ModelConfig) -> ModelResponse:
        return ModelResponse(
            content=f"ok-{self._name}",
            model=config.model_name,
            provider=self._name,
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )

    async def stream_response(self, messages: List[Message], config: ModelConfig) -> AsyncGenerator[str, None]:  # pragma: no cover - not used here
        yield f"chunk-{self._name}"

    async def validate_api_key(self) -> bool:  # pragma: no cover - not used
        return True

    def estimate_cost(self, messages: List[Message], config: ModelConfig) -> float:
        return self._cost

    def count_tokens(self, text: str) -> int:  # pragma: no cover - not used
        return max(1, len(text) // 4)


class FailProv(OkProv):
    def __init__(self, name: str, cost: float, error: Exception):
        super().__init__(name, cost)
        self._error = error

    async def generate_response(self, messages: List[Message], config: ModelConfig) -> ModelResponse:
        raise self._error


@pytest.mark.asyncio
async def test_route_request_happy_path_cost_optimized():
    router = ModelRouter(default_policy=RoutingPolicy(strategy=RoutingStrategy.COST_OPTIMIZED))
    p_expensive = OkProv("exp", cost=0.03)
    p_cheap = OkProv("cheap", cost=0.01)

    await router.add_provider(p_expensive, priority=1)
    await router.add_provider(p_cheap, priority=1)

    messages = [Message(role=MessageRole.USER, content="hi")]
    cfg = ModelConfig(model_name="grok-3-mini")

    resp = await router.route_request(messages, cfg)
    assert resp.provider == "cheap"


@pytest.mark.asyncio
async def test_route_request_failover_on_error_then_success(monkeypatch):
    router = ModelRouter(default_policy=RoutingPolicy(strategy=RoutingStrategy.FAILOVER, retry_attempts=2))
    bad = FailProv("bad", cost=0.01, error=RateLimitError("rl", provider="bad"))
    good = OkProv("good", cost=0.02)

    await router.add_provider(bad, priority=2, fallback_order=0)
    await router.add_provider(good, priority=1, fallback_order=1)

    messages = [Message(role=MessageRole.USER, content="hi")]
    cfg = ModelConfig(model_name="grok-3-mini")

    resp = await router.route_request(messages, cfg)
    assert resp.provider == "good"


@pytest.mark.asyncio
async def test_create_default_router_uses_grok_provider(monkeypatch):
    # Ensure GROK API key present to allow provider construction
    monkeypatch.setenv("GROK_API_KEY", "dummy")

    router = await create_default_router()

    # Should contain a provider named 'grok'
    assert any(name == "grok" for name in router.providers.keys())
