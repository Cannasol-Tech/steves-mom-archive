"""
Additional unit tests for backend.ai.model_router.ModelRouter internals.

Covers:
- route_request fallback when first provider rate-limited
- circuit breaker skip after repeated errors
- stream_request retries and fallback yielding chunks
- _policy_from_env parsing from environment variables
"""

import asyncio
import os
from typing import List, AsyncGenerator

import pytest

from backend.ai.model_router import ModelRouter, RoutingPolicy, RoutingStrategy, _policy_from_env
from backend.ai.providers.base import LLMProvider, Message, MessageRole, ModelConfig, ModelResponse, ModelCapability, ProviderError


class ProviderOK(LLMProvider):
    def __init__(self, name: str = "ok", cost: float = 0.01, models: List[str] | None = None):
        super().__init__(api_key="key")
        self._name = name
        self._cost = cost
        self._models = models or ["grok-3-mini"]

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def supported_capabilities(self) -> List[ModelCapability]:
        return [ModelCapability.TEXT_GENERATION]

    @property
    def available_models(self) -> List[str]:
        return self._models

    async def initialize(self) -> None:
        return None

    async def generate_response(self, messages: List[Message], config: ModelConfig) -> ModelResponse:
        return ModelResponse(content="ok", model=config.model_name, provider=self._name, usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2})

    async def stream_response(self, messages: List[Message], config: ModelConfig) -> AsyncGenerator[str, None]:
        yield "chunk1"
        yield "chunk2"

    def estimate_cost(self, messages: List[Message], config: ModelConfig) -> float:
        return self._cost


class ProviderFail(ProviderOK):
    async def generate_response(self, messages: List[Message], config: ModelConfig) -> ModelResponse:
        raise ProviderError("boom", self._name)

    async def stream_response(self, messages: List[Message], config: ModelConfig) -> AsyncGenerator[str, None]:
        raise ProviderError("boom", self._name)


@pytest.mark.asyncio
async def test_route_request_skips_rate_limited_and_uses_next(monkeypatch):
    router = ModelRouter()
    p1 = ProviderOK(name="p1", cost=0.01)
    p2 = ProviderOK(name="p2", cost=0.02)

    await router.add_provider(p1)
    await router.add_provider(p2)

    # Eligible providers will be [p1, p2]. Force rate limit fail for p1 only.
    calls = {"checked": []}

    def fake_check(name: str) -> bool:
        calls["checked"].append(name)
        return name != "p1"

    monkeypatch.setattr(router, "_check_rate_limit", fake_check)

    resp = await router.route_request([Message(role=MessageRole.USER, content="hi")], ModelConfig(model_name="grok-3-mini"), RoutingPolicy(max_cost_threshold=1.0))

    assert resp.provider == "p2"
    assert calls["checked"] == ["p1", "p2"]


@pytest.mark.asyncio
async def test_circuit_breaker_activates_after_errors(monkeypatch):
    router = ModelRouter()
    bad = ProviderFail(name="bad", cost=0.01)
    good = ProviderOK(name="good", cost=0.02)

    await router.add_provider(bad)
    await router.add_provider(good)

    # Simulate multiple errors for bad to trigger breaker
    for _ in range(6):
        router._record_error("bad")
    assert router._circuit_breakers["bad"] is True

    resp = await router.route_request([Message(role=MessageRole.USER, content="hi")], ModelConfig(model_name="grok-3-mini"), RoutingPolicy(max_cost_threshold=1.0))
    assert resp.provider == "good"


@pytest.mark.asyncio
async def test_stream_request_fallback_on_error(monkeypatch):
    router = ModelRouter()
    bad = ProviderFail(name="bad", cost=0.01)
    good = ProviderOK(name="good", cost=0.02)

    await router.add_provider(bad)
    await router.add_provider(good)

    chunks = []
    async for ch in router.stream_request([Message(role=MessageRole.USER, content="hi")], ModelConfig(model_name="grok-3-mini"), RoutingPolicy(max_cost_threshold=1.0)):
        chunks.append(ch)

    assert chunks == ["chunk1", "chunk2"]


def test_policy_from_env_parsing(monkeypatch):
    monkeypatch.setenv("AI_ROUTING_STRATEGY", "latency_optimized")
    monkeypatch.setenv("AI_MAX_COST_THRESHOLD", "0.11")
    monkeypatch.setenv("AI_MAX_LATENCY_MS", "2500")
    monkeypatch.setenv("AI_RETRY_ATTEMPTS", "5")

    policy = _policy_from_env()

    assert policy.strategy == RoutingStrategy.LATENCY_OPTIMIZED
    assert abs(policy.max_cost_threshold - 0.11) < 1e-9
    assert abs(policy.max_latency_threshold - 2.5) < 1e-9
    assert policy.retry_attempts == 5
