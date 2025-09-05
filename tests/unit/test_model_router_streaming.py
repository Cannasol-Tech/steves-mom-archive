import pytest
import asyncio
from typing import Any, AsyncGenerator, Dict, List

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


class StubStreamingProvider(LLMProvider):
    def __init__(self, name: str = "stub", models: List[str] = None, cost: float = 0.001):
        super().__init__(api_key="test")
        self._name = name
        self._models = models or ["grok-3-mini"]
        self._cost = cost

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def supported_capabilities(self) -> List[ModelCapability]:
        return [ModelCapability.TEXT_GENERATION, ModelCapability.STREAMING]

    @property
    def available_models(self) -> List[str]:
        return self._models

    async def initialize(self) -> None:
        return None

    async def generate_response(self, messages: List[Message], config: ModelConfig) -> ModelResponse:
        return ModelResponse(
            content="ok",
            model=config.model_name,
            provider=self.provider_name,
            usage={"tokens": 1},
        )

    async def stream_response(self, messages: List[Message], config: ModelConfig) -> AsyncGenerator[str, None]:
        for part in ["hel", "lo"]:
            await asyncio.sleep(0)
            yield part

    async def validate_api_key(self) -> bool:
        return True

    def estimate_cost(self, messages: List[Message], config: ModelConfig) -> float:
        return self._cost

    def count_tokens(self, text: str) -> int:
        return len(text.split())


@pytest.mark.asyncio
async def test_stream_request_happy_path_yields_chunks():
    router = ModelRouter()
    provider = StubStreamingProvider(name="stub-stream", models=["grok-3-mini"], cost=0.001)
    await router.add_provider(provider)

    messages = [Message(role=MessageRole.USER, content="hi")]
    config = ModelConfig(model_name="grok-3-mini", stream=True)
    policy = RoutingPolicy()

    chunks = []
    async for chunk in router.stream_request(messages, config, policy):
        chunks.append(chunk)

    assert "".join(chunks) == "hello"


@pytest.mark.asyncio
async def test_stream_request_no_eligible_providers_raises():
    router = ModelRouter()
    # High cost ensures it exceeds strict policy threshold
    provider = StubStreamingProvider(name="stub-high-cost", models=["grok-3-mini"], cost=1.0)
    await router.add_provider(provider)

    messages = [Message(role=MessageRole.USER, content="hi")]
    config = ModelConfig(model_name="grok-3-mini", stream=True)
    strict_policy = RoutingPolicy()
    strict_policy.max_cost_threshold = 0.0001

    with pytest.raises(ProviderError, match="No eligible providers available for streaming"):
        async for _ in router.stream_request(messages, config, strict_policy):
            pass


@pytest.mark.asyncio
async def test_stream_request_skips_when_rate_limited_and_exhausts_retries():
    router = ModelRouter()
    provider = StubStreamingProvider(name="stub-rate", models=["grok-3-mini"], cost=0.00001)
    await router.add_provider(provider)

    # Set a very low per-minute limit and pre-fill request counts to hit the limit
    router.update_provider_config("stub-rate", {"max_requests_per_minute": 1})
    # Simulate one recent request just now to reach the limit
    now = __import__("time").time()
    router._request_counts["stub-rate"] = [now]

    messages = [Message(role=MessageRole.USER, content="hi")]
    config = ModelConfig(model_name="grok-3-mini", stream=True)
    policy = RoutingPolicy()
    policy.retry_attempts = 2

    with pytest.raises(ProviderError, match="All providers failed to stream"):
        async for _ in router.stream_request(messages, config, policy):
            pass
