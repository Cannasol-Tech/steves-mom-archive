import os
import pytest
from unittest.mock import patch, AsyncMock
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


@pytest.mark.asyncio
async def test_grok_provider_api_error():
    """Test that an API error raises a ProviderError."""
    with patch('backend.ai.providers.grok_provider.AsyncClient') as mock_client:
        mock_client.return_value.post = AsyncMock(return_value=MockResponse(500, {}))
        provider = GROKProvider(api_key="test_api_key")
        with pytest.raises(ProviderError):
            await provider.chat_completion(
                model="grok-3-mini",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=50
            )


@pytest.mark.asyncio
async def test_grok_provider_rate_limit():
    """Test that a rate limit error is handled."""
    with patch('backend.ai.providers.grok_provider.AsyncClient') as mock_client:
        mock_client.return_value.post = AsyncMock(return_value=MockResponse(429, {}))
        provider = GROKProvider(api_key="test_api_key")
        with pytest.raises(ProviderError):
            await provider.chat_completion(
                model="grok-3-mini",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=50
            )


@pytest.mark.asyncio
async def test_grok_provider_timeout():
    """Test that a timeout error is handled."""
    with patch('backend.ai.providers.grok_provider.AsyncClient') as mock_client:
        mock_client.return_value.post = AsyncMock(side_effect=TimeoutError)
        provider = GROKProvider(api_key="test_api_key")
        with pytest.raises(ProviderError):
            await provider.chat_completion(
                model="grok-3-mini",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=50
            )


@pytest.mark.asyncio
async def test_generate_response_model_not_found():
    p = GROKProvider()
    msgs = [Message(role=MessageRole.USER, content="Say hi")]
    cfg = ModelConfig(model_name="non-existent-model", max_tokens=16, temperature=0.0)
    with pytest.raises(ModelNotFoundError):
        await p.generate_response(msgs, cfg)


@pytest.mark.asyncio
async def test_generate_response_success():
    # Mock the xai_sdk
    with patch('backend.ai.providers.grok_provider.XAI') as mock_xai:
        # Create a mock client and chat
        mock_client = mock_xai.return_value
        mock_chat = mock_client.chat.create.return_value

        # Mock the sample method to return a response
        mock_response = mock_chat.sample.return_value
        mock_response.content = "Hello! How can I assist you today?"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        p = GROKProvider()
        msgs = [Message(role=MessageRole.USER, content="Hello")]
        cfg = ModelConfig(model_name="grok-3-mini", max_tokens=50, temperature=0.0)

        response = await p.generate_response(msgs, cfg)

        assert response.content == "Hello! How can I assist you today?"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 20
        assert response.usage["total_tokens"] == 30


@pytest.mark.asyncio
async def test_stream_response_model_not_found():
    p = GROKProvider()
    msgs = [Message(role=MessageRole.USER, content="Stream it")]
    cfg = ModelConfig(model_name="non-existent-model", max_tokens=16, temperature=0.0)
    with pytest.raises(ModelNotFoundError):
        async for _ in p.stream_response(msgs, cfg):
            pass


@pytest.mark.asyncio
async def test_stream_response_success():
    # Mock the xai_sdk
    with patch('backend.ai.providers.grok_provider.XAI') as mock_xai:
        # Create a mock client and chat
        mock_client = mock_xai.return_value
        mock_chat = mock_client.chat.create.return_value

        # Mock the sample_stream method to return an async generator
        mock_chunk = AsyncMock()
        mock_chunk.content = "Hello"
        mock_chunk.usage = None
        mock_chunk2 = AsyncMock()
        mock_chunk2.content = " there"
        mock_chunk2.usage = None
        mock_final_chunk = AsyncMock()
        mock_final_chunk.content = "!"
        mock_final_chunk.usage = AsyncMock()
        mock_final_chunk.usage.prompt_tokens = 10
        mock_final_chunk.usage.completion_tokens = 3
        mock_final_chunk.usage.total_tokens = 13

        # Create an async generator that yields the chunks
        async def mock_sample_stream():
            yield mock_chunk
            yield mock_chunk2
            yield mock_final_chunk

        mock_chat.sample_stream = mock_sample_stream

        p = GROKProvider()
        msgs = [Message(role=MessageRole.USER, content="Hello")]
        cfg = ModelConfig(model_name="grok-3-mini", max_tokens=50, temperature=0.0)

        # Collect the streamed response
        content_chunks = []
        async for chunk in p.stream_response(msgs, cfg):
            content_chunks.append(chunk.content)

        # The final chunk should have the usage
        assert "".join(content_chunks) == "Hello there!"
        # The final usage should be set
        assert p._last_usage["prompt_tokens"] == 10
        assert p._last_usage["completion_tokens"] == 3
        assert p._last_usage["total_tokens"] == 13


@pytest.mark.asyncio
async def test_initialize_without_sdk():
    # Remove the xai_sdk if it was installed
    with patch.dict('sys.modules', xai_sdk=None):
        p = GROKProvider()
        with pytest.raises(ProviderError):
            await p.initialize()


@pytest.mark.asyncio
async def test_initialize_with_sdk():
    with patch('backend.ai.providers.grok_provider.xai_sdk') as mock_sdk:
        p = GROKProvider()
        await p.initialize()
        assert p._client is not None


@pytest.mark.asyncio
async def test_validate_api_key_success():
    with patch('backend.ai.providers.grok_provider.XAI') as mock_xai:
        mock_client = mock_xai.return_value
        mock_client.validate_api_key.return_value = True

        p = GROKProvider()
        await p.initialize()  # This will set the client
        valid = await p.validate_api_key()
        assert valid is True


@pytest.mark.asyncio
async def test_validate_api_key_failure():
    with patch('backend.ai.providers.grok_provider.XAI') as mock_xai:
        mock_client = mock_xai.return_value
        mock_client.validate_api_key.return_value = False

        p = GROKProvider()
        await p.initialize()
        valid = await p.validate_api_key()
        assert valid is False


def test_count_tokens_with_tokenizer():
    p = GROKProvider()
    # Mock the tokenizer
    p._tokenizer = MockTokenizer()
    count = p.count_tokens("Hello world")
    assert count == 2  # Because our mock tokenizer returns 2 for "Hello world"


def test_count_tokens_with_tokenizer_exception():
    p = GROKProvider()
    p._tokenizer = MockTokenizer(raise_exception=True)
    count = p.count_tokens("Hello world")
    assert count == len("Hello world") // 4  # Fallback to heuristic


class MockTokenizer:
    def __init__(self, raise_exception=False):
        self.raise_exception = raise_exception

    def encode(self, text):
        if self.raise_exception:
            raise Exception("Tokenization failed")
        return [1, 2]  # Two tokens
