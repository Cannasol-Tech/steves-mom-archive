import asyncio
import pytest

from backend.ai.model_router import ModelRouter, RoutingPolicy
from backend.ai.providers.base import (
    LLMProvider,
    Message,
    MessageRole,
    ModelCapability,
    ModelConfig,
    ModelResponse,
    ProviderError,
)


class AlwaysFailProvider(LLMProvider):
    """Provider that always raises ProviderError to trigger circuit breaker."""

    def __init__(self, name: str, models: list[str] | None = None):
        super().__init__(api_key="test")
        self._name = name
        self._models = models or ["grok-3-mini"]

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def supported_capabilities(self):
        return [ModelCapability.TEXT_GENERATION]

    @property
    def available_models(self):
        return list(self._models)

    async def initialize(self) -> None:
        return None

    async def generate_response(self, messages, config):
        raise ProviderError("fail", self._name)

    async def stream_response(self, messages, config):
        yield "never"

    async def validate_api_key(self) -> bool:
        return True

    def estimate_cost(self, messages, config) -> float:
        return 0.01

    def count_tokens(self, text: str) -> int:
        return len(text)


class GoodProvider(LLMProvider):
    def __init__(self, name: str = "good", models: list[str] | None = None):
        super().__init__(api_key="test")
        self._name = name
        self._models = models or ["grok-3-mini"]

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def supported_capabilities(self):
        return [ModelCapability.TEXT_GENERATION]

    @property
    def available_models(self):
        return list(self._models)

    async def initialize(self) -> None:
        return None

    async def generate_response(self, messages, config):
        user_text = ".".join(m.content for m in messages if m.role == MessageRole.USER)
        return ModelResponse(content=f"ok:{self._name}:{user_text}", model=config.model_name, provider=self._name, usage={"tokens": 1})

    async def stream_response(self, messages, config):
        yield "chunk"

    async def validate_api_key(self) -> bool:
        return True

    def estimate_cost(self, messages, config) -> float:
        return 0.005

    def count_tokens(self, text: str) -> int:
        return len(text)


@pytest.mark.asyncio
async def test_circuit_breaker_trips_and_router_skips_failing_provider(monkeypatch):
    router = ModelRouter()

    # Avoid real sleeping to keep test fast (record sleeps for sanity)
    sleeps: list[float] = []

    async def fake_sleep(x: float):
        sleeps.append(x)
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    bad = AlwaysFailProvider("bad")
    good = GoodProvider("good")

    # Add bad with higher priority so it's tried first; good as fallback
    await router.add_provider(bad, priority=10, fallback_order=1)
    await router.add_provider(good, priority=1, fallback_order=2)

    msgs = [Message(role=MessageRole.USER, content="hello")]
    cfg = ModelConfig(model_name="grok-3-mini")

    # Need >5 errors to open breaker; with retry_attempts high, the inner loop will
    # encounter 'bad' repeatedly, trip the breaker (>5), then still attempt 'good'
    policy = RoutingPolicy(retry_attempts=8)

    resp = await router.route_request(msgs, cfg, policy)
    assert resp.provider == "good"

    # After enough errors the circuit breaker should be open for 'bad'
    assert router._circuit_breakers.get("bad", False) is True
    assert router._error_counts.get("bad", 0) >= 6

    # Subsequent call should not try 'bad' (skipped due to breaker) and succeed immediately
    sleeps.clear()
    resp2 = await router.route_request(msgs, cfg, policy)
    assert resp2.provider == "good"
    # No backoff expected when first attempt succeeds without retries
    assert sleeps == []
