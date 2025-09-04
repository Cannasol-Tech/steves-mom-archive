import asyncio
from typing import Any, AsyncGenerator, List

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


class FlakyProvider(LLMProvider):
    """Provider that fails N-1 times then succeeds, to exercise retry/backoff."""

    def __init__(self, name: str, fail_times: int = 2, models: List[str] | None = None):
        super().__init__(api_key="test")
        self._name = name
        self._fail_times = fail_times
        self._calls = 0
        self._models = models or ["grok-3-mini"]

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def supported_capabilities(self) -> List[ModelCapability]:
        return [ModelCapability.TEXT_GENERATION]

    @property
    def available_models(self) -> List[str]:
        return list(self._models)

    async def initialize(self) -> None:
        return None

    async def generate_response(self, messages: List[Message], config: ModelConfig) -> ModelResponse:
        self._calls += 1
        if self._calls <= self._fail_times:
            raise ProviderError("boom", self._name)
        content = "".join(m.content for m in messages if m.role == MessageRole.USER)
        return ModelResponse(content=f"ok:{self._name}:{content}", model=config.model_name, provider=self._name, usage={"tokens": 1})

    async def stream_response(self, messages: List[Message], config: ModelConfig) -> AsyncGenerator[str, None]:
        yield "chunk"

    async def validate_api_key(self) -> bool:
        return True

    def estimate_cost(self, messages: List[Message], config: ModelConfig) -> float:
        return 0.01

    def count_tokens(self, text: str) -> int:
        return len(text.split())


class SimpleProvider(LLMProvider):
    def __init__(self, name: str, capabilities: List[ModelCapability], models: List[str]):
        super().__init__(api_key="test")
        self._name = name
        self._capabilities = list(capabilities)
        self._models = list(models)

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
        content = "".join(m.content for m in messages if m.role == MessageRole.USER)
        return ModelResponse(content=f"ok:{self._name}:{content}", model=config.model_name, provider=self._name, usage={"tokens": 1})

    async def stream_response(self, messages: List[Message], config: ModelConfig) -> AsyncGenerator[str, None]:
        yield "chunk"

    async def validate_api_key(self) -> bool:
        return True

    def estimate_cost(self, messages: List[Message], config: ModelConfig) -> float:
        return 0.01

    def count_tokens(self, text: str) -> int:
        return len(text.split())


@pytest.mark.asyncio
async def test_retry_with_exponential_backoff(monkeypatch):
    router = ModelRouter()

    # Sleep recorder to avoid real delays
    sleeps: list[float] = []

    async def fake_sleep(x: float):
        sleeps.append(x)
        return None

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    flaky = FlakyProvider("flaky", fail_times=2)
    await router.add_provider(flaky, priority=10)

    msgs = [Message(role=MessageRole.USER, content="hello")]
    cfg = ModelConfig(model_name="grok-3-mini")

    # Policy with 3 attempts: 1st and 2nd fail, 3rd succeeds
    policy = RoutingPolicy(retry_attempts=3)

    resp = await router.route_request(msgs, cfg, policy)
    assert resp.provider == "flaky"
    # Backoff sleeps should be [1, 2] for attempts 0 and 1
    assert sleeps == [1, 2]


@pytest.mark.asyncio
async def test_no_eligible_when_provider_disabled():
    router = ModelRouter()
    p = SimpleProvider("p", capabilities=[ModelCapability.TEXT_GENERATION], models=["grok-3-mini"])
    await router.add_provider(p, enabled=False)

    msgs = [Message(role=MessageRole.USER, content="x")]
    cfg = ModelConfig(model_name="grok-3-mini")

    with pytest.raises(ProviderError):
        await router.route_request(msgs, cfg)


@pytest.mark.asyncio
async def test_capability_requirement_filters_providers():
    router = ModelRouter()
    a = SimpleProvider("a", capabilities=[ModelCapability.TEXT_GENERATION], models=["grok-3-mini"])
    b = SimpleProvider("b", capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.FUNCTION_CALLING], models=["grok-3-mini"])

    await router.add_provider(a, priority=5)
    await router.add_provider(b, priority=1)

    msgs = [Message(role=MessageRole.USER, content="tool please")] 
    cfg = ModelConfig(model_name="grok-3-mini")

    policy = RoutingPolicy(required_capabilities=[ModelCapability.FUNCTION_CALLING])
    resp = await router.route_request(msgs, cfg, policy)
    assert resp.provider == "b"


@pytest.mark.asyncio
async def test_model_availability_filtering():
    router = ModelRouter()
    a = SimpleProvider("a", capabilities=[ModelCapability.TEXT_GENERATION], models=["other-model"])  # does not have grok-3-mini
    b = SimpleProvider("b", capabilities=[ModelCapability.TEXT_GENERATION], models=["grok-3-mini"])  # has desired model

    await router.add_provider(a, priority=10)
    await router.add_provider(b, priority=1)

    msgs = [Message(role=MessageRole.USER, content="hi")]
    cfg = ModelConfig(model_name="grok-3-mini")

    resp = await router.route_request(msgs, cfg)
    assert resp.provider == "b"
