import os
import pytest

from backend.ai.providers.grok_provider import GROKProvider
from backend.ai.providers.base import Message, MessageRole, ModelConfig, ProviderError


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    # Ensure api key is present for constructor
    monkeypatch.setenv("GROK_API_KEY", "test-key")


def test_basic_properties():
    p = GROKProvider()
    assert p.provider_name == "grok"
    assert len(p.available_models) > 0
    caps = p.supported_capabilities
    # Streaming is critical capability for GROK
    assert any(c.name == "STREAMING" for c in caps)


def test_create_system_message_toggle():
    p = GROKProvider()
    sm_on = p._create_system_message(True)
    sm_off = p._create_system_message(False)
    assert sm_on["role"] == "system" and "Steve's Mom" in sm_on["content"]
    assert sm_off["role"] == "system" and "helpful AI assistant" in sm_off["content"]


def test_convert_messages_and_token_count():
    p = GROKProvider()
    msgs = [
        Message(role=MessageRole.USER, content="Hello"),
        Message(role=MessageRole.ASSISTANT, content="Hi there"),
        Message(role=MessageRole.SYSTEM, content="Sys"),
    ]
    api_msgs = p._convert_messages(msgs)
    assert api_msgs == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
        {"role": "system", "content": "Sys"},
    ]

    # count_tokens without a tokenizer should use fallback heuristic
    approx = p.count_tokens("abcd" * 10)
    assert isinstance(approx, int)
    assert approx > 0


def test_estimate_cost_positive():
    p = GROKProvider()
    msgs = [Message(role=MessageRole.USER, content="How are you?")]
    cfg = ModelConfig(model_name="grok-3-mini", max_tokens=128, temperature=0.2)
    cost = p.estimate_cost(msgs, cfg)
    assert cost > 0.0


@pytest.mark.asyncio
async def test_generate_response_raises_provider_error_without_sdk():
    p = GROKProvider()
    msgs = [Message(role=MessageRole.USER, content="Say hi")]
    cfg = ModelConfig(model_name="grok-3-mini", max_tokens=16, temperature=0.0)
    with pytest.raises(ProviderError):
        await p.generate_response(msgs, cfg)


@pytest.mark.asyncio
async def test_stream_response_raises_provider_error_without_sdk():
    p = GROKProvider()
    msgs = [Message(role=MessageRole.USER, content="Stream it")]
    cfg = ModelConfig(model_name="grok-3-mini", max_tokens=16, temperature=0.0)
    with pytest.raises(ProviderError):
        # Exhaust the async generator to trigger underlying logic
        async for _ in p.stream_response(msgs, cfg):
            pass


@pytest.mark.asyncio
async def test_validate_api_key_false_without_sdk():
    p = GROKProvider()
    ok = await p.validate_api_key()
    assert ok is False
