import pytest

from backend.ai.providers.local_provider import LocalProvider
from backend.ai.providers.base import Message, MessageRole, ModelConfig


def test_basic_properties():
    p = LocalProvider()
    assert p.provider_name == "local"
    assert set(p.available_models) >= {"llama-3.1-8b", "mistral-7b", "codellama-13b"}
    caps = p.supported_capabilities
    assert any(c.name == "TEXT_GENERATION" for c in caps)


def test_cost_and_tokens_and_max():
    p = LocalProvider()
    msgs = [Message(role=MessageRole.USER, content="Hello there")]
    cfg = ModelConfig(model_name="llama-3.1-8b", max_tokens=128, temperature=0.0)
    assert p.estimate_cost(msgs, cfg) == 0.0
    assert p.count_tokens("abcd" * 5) > 0
    assert p.get_max_tokens() == 8192


@pytest.mark.asyncio
async def test_generate_and_stream_and_health():
    p = LocalProvider()
    msgs = [Message(role=MessageRole.USER, content="Hi")]
    cfg = ModelConfig(model_name="llama-3.1-8b", max_tokens=32, temperature=0.0)

    # generate returns placeholder ModelResponse
    resp = await p.generate_response(msgs, cfg)
    assert resp.provider == "local"
    assert "not yet implemented" in resp.content

    # stream_generate yields a placeholder chunk
    chunks = []
    async for ch in p.stream_response(msgs, cfg):
        chunks.append(ch)
    assert any("not yet implemented" in c for c in chunks)

    # validate_api_key always True and health_check returns structured info
    ok = await p.validate_api_key()
    assert ok is True
    health = await p.health_check()
    assert health["provider"] == "local"
    assert health["available"] is False


def test_get_capabilities_and_cost_estimate():
    p = LocalProvider()
    caps = p.get_capabilities()
    assert len(caps) > 0
    assert p.get_cost_estimate(100, 200) == 0.0
