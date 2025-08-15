"""
Unit tests for ModelRouter fallback, retries, and circuit breaker (Task 4.2.2)

Author: Cannasol Technologies (cascade-03)
Date: 2025-08-15
"""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Any, AsyncGenerator

import pytest
from unittest.mock import AsyncMock, patch

# Ensure backend is importable
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from ai.model_router import ModelRouter, RoutingPolicy, RoutingStrategy
from ai.providers.base import (
    LLMProvider,
    Message,
    MessageRole,
    ModelConfig,
    ModelResponse,
    ModelCapability,
    ProviderError,
    RateLimitError,
)


class FlakyProvider(LLMProvider):
    """Provider that can fail a configured number of times before succeeding."""

    def __init__(
        self,
        name: str,
        models: List[str],
        capabilities: List[ModelCapability],
        fail_times: int = 0,
        rate_limit_times: int = 0,
        api_key: str = "test",
    ):
        super().__init__(api_key=api_key)
        self._name = name
        self._models = models
        self._capabilities = capabilities
        self._fail_times = fail_times
        self._rate_limit_times = rate_limit_times
        self._calls = 0

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
        self._calls += 1
        # Simulate rate limiting first, then generic provider failures
        if self._rate_limit_times > 0:
            self._rate_limit_times -= 1
            raise RateLimitError("rate limit", self._name)
        if self._fail_times > 0:
            self._fail_times -= 1
            raise ProviderError("transient", self._name)
        return ModelResponse(
            content=f"ok from {self._name}",
            model=config.model_name,
            provider=self._name,
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )

    async def stream_response(
        self, messages: List[Message], config: ModelConfig
    ) -> AsyncGenerator[str, None]:
        yield "ok"

    async def validate_api_key(self) -> bool:
        return True

    def estimate_cost(self, messages: List[Message], config: ModelConfig) -> float:
        return 0.01

    def count_tokens(self, text: str) -> int:
        return len(text)


def make_message(text: str = "hi") -> List[Message]:
    return [Message(role=MessageRole.USER, content=text)]


@pytest.mark.asyncio
async def test_fallback_on_provider_error_routes_to_next():
    router = ModelRouter()

    bad = FlakyProvider(
        name="bad",
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION],
        fail_times=10,  # guaranteed to fail
    )
    good = FlakyProvider(
        name="good",
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION],
    )

    await router.add_provider(bad, fallback_order=0)
    await router.add_provider(good, fallback_order=1)

    policy = RoutingPolicy(strategy=RoutingStrategy.FAILOVER, max_cost_threshold=1.0, retry_attempts=1)

    with patch("ai.model_router.asyncio.sleep", new=AsyncMock()) as _:
        resp = await router.route_request(
            messages=make_message(),
            config=ModelConfig(model_name="grok-3-mini"),
            policy=policy,
        )

    assert resp.provider == "good"


@pytest.mark.asyncio
async def test_rate_limit_skips_and_uses_next_provider():
    router = ModelRouter()

    limited = FlakyProvider(
        name="limited",
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION],
        rate_limit_times=5,  # always rate limited within single call
    )
    ok = FlakyProvider(
        name="ok",
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION],
    )

    await router.add_provider(limited, fallback_order=0)
    await router.add_provider(ok, fallback_order=1)

    policy = RoutingPolicy(strategy=RoutingStrategy.FAILOVER, max_cost_threshold=1.0, retry_attempts=1)

    with patch("ai.model_router.asyncio.sleep", new=AsyncMock()) as _:
        resp = await router.route_request(
            messages=make_message(),
            config=ModelConfig(model_name="grok-3-mini"),
            policy=policy,
        )

    assert resp.provider == "ok"


@pytest.mark.asyncio
async def test_circuit_breaker_trips_after_errors_and_skips_provider():
    router = ModelRouter()

    # Create a provider that will fail many times to trip circuit breaker (>5 errors)
    flaky = FlakyProvider(
        name="flaky",
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION],
        fail_times=100,
    )
    healthy = FlakyProvider(
        name="healthy",
        models=["grok-3-mini"],
        capabilities=[ModelCapability.TEXT_GENERATION],
    )

    await router.add_provider(flaky, fallback_order=0)
    await router.add_provider(healthy, fallback_order=1)

    # Manually record enough errors to simulate prior failures and trip breaker
    for _ in range(6):
        router._record_error("flaky")

    # Ensure circuit breaker marked active
    assert router._error_counts["flaky"] == 6
    router._circuit_breakers["flaky"] = True

    policy = RoutingPolicy(strategy=RoutingStrategy.FAILOVER, max_cost_threshold=1.0, retry_attempts=1)

    with patch("ai.model_router.asyncio.sleep", new=AsyncMock()) as _:
        resp = await router.route_request(
            messages=make_message(),
            config=ModelConfig(model_name="grok-3-mini"),
            policy=policy,
        )

    assert resp.provider == "healthy"
