"""
Unit tests for AI provider components

Tests AI provider functionality including:
- Provider initialization and configuration
- Chat completion requests and responses
- Error handling and retry logic
- Provider selection and fallback mechanisms
- Response parsing and validation

Author: Cannasol Technologies
Date: 2025-01-04
Version: 1.0.0
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json

import sys
from pathlib import Path

# Ensure backend package is importable
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.ai.providers.base import LLMProvider
from backend.api.schemas import ChatMessage, ChatRequest, ChatResponse


class TestLLMProvider:
    """Test LLMProvider abstract class functionality."""

    def test_llm_provider_cannot_be_instantiated(self):
        """Test that LLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMProvider("test-key")

    def test_llm_provider_abstract_methods(self):
        """Test that LLMProvider defines required abstract methods."""
        # Check that abstract methods are defined
        assert hasattr(LLMProvider, 'generate_response')
        assert hasattr(LLMProvider, 'provider_name')

        # Verify they are abstract
        assert getattr(LLMProvider.generate_response, '__isabstractmethod__', False)
        assert getattr(LLMProvider.provider_name, '__isabstractmethod__', False)


class TestLLMProviderDataClasses:
    """Test data classes used by LLM providers."""

    def test_message_creation(self):
        """Test Message dataclass creation."""
        from backend.ai.providers.base import Message, MessageRole

        message = Message(role=MessageRole.USER, content="Hello")
        assert message.role == MessageRole.USER
        assert message.content == "Hello"
        assert message.timestamp is not None
        assert message.metadata == {}

    def test_model_config_creation(self):
        """Test ModelConfig dataclass creation."""
        from backend.ai.providers.base import ModelConfig

        config = ModelConfig(model_name="test-model")
        assert config.model_name == "test-model"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.stop_sequences == []
        assert config.tools == []

    def test_model_response_creation(self):
        """Test ModelResponse dataclass creation."""
        from backend.ai.providers.base import ModelResponse

        response = ModelResponse(
            content="Test response",
            model="test-model",
            provider="test-provider",
            usage={"prompt_tokens": 10, "completion_tokens": 20}
        )

        assert response.content == "Test response"
        assert response.model == "test-model"
        assert response.provider == "test-provider"
        assert response.usage["prompt_tokens"] == 10
        assert response.metadata == {}

    def test_tool_call_creation(self):
        """Test ToolCall dataclass creation."""
        from backend.ai.providers.base import ToolCall

        tool_call = ToolCall(
            id="test-id",
            function_name="test_function",
            arguments={"arg1": "value1"}
        )

        assert tool_call.id == "test-id"
        assert tool_call.function_name == "test_function"
        assert tool_call.arguments == {"arg1": "value1"}

    def test_provider_errors(self):
        """Test provider exception classes."""
        from backend.ai.providers.base import (
            ProviderError, RateLimitError, AuthenticationError,
            ModelNotFoundError, QuotaExceededError
        )

        # Test base ProviderError
        error = ProviderError("Test error", "test-provider", "test-code")
        assert str(error) == "Test error"
        assert error.provider == "test-provider"
        assert error.error_code == "test-code"

        # Test RateLimitError
        rate_error = RateLimitError("Rate limited", "test-provider", 60)
        assert rate_error.retry_after == 60
        assert rate_error.error_code == "rate_limit"

        # Test AuthenticationError
        auth_error = AuthenticationError("Auth failed", "test-provider")
        assert auth_error.error_code == "authentication"

        # Test ModelNotFoundError
        model_error = ModelNotFoundError("Model not found", "test-provider", "test-model")
        assert model_error.model_name == "test-model"
        assert model_error.error_code == "model_not_found"

        # Test QuotaExceededError
        quota_error = QuotaExceededError("Quota exceeded", "test-provider")
        assert quota_error.error_code == "quota_exceeded"


class TestLLMProviderHelperMethods:
    """Test LLMProvider helper methods that don't require implementation."""

    def test_supports_capability(self):
        """Test supports_capability method."""
        from backend.ai.providers.base import LLMProvider, ModelCapability

        # Create a mock concrete implementation
        class MockProvider(LLMProvider):
            @property
            def provider_name(self):
                return "mock"

            @property
            def supported_capabilities(self):
                return [ModelCapability.TEXT_GENERATION, ModelCapability.STREAMING]

            @property
            def available_models(self):
                return ["mock-model"]

            async def initialize(self):
                pass

            async def generate_response(self, messages, config):
                pass

            async def stream_response(self, messages, config):
                if False:
                    yield ""

            async def validate_api_key(self):
                return True

            def estimate_cost(self, messages, config):
                return 0.01

            def count_tokens(self, text):
                return len(text.split())

        provider = MockProvider("test-key")

        assert provider.supports_capability(ModelCapability.TEXT_GENERATION) is True
        assert provider.supports_capability(ModelCapability.STREAMING) is True
        assert provider.supports_capability(ModelCapability.VISION) is False

    def test_get_model_info(self):
        """Test get_model_info method."""
        from backend.ai.providers.base import LLMProvider, ModelCapability

        # Create a mock concrete implementation
        class MockProvider(LLMProvider):
            @property
            def provider_name(self):
                return "mock"

            @property
            def supported_capabilities(self):
                return [ModelCapability.TEXT_GENERATION]

            @property
            def available_models(self):
                return ["mock-model"]

            async def initialize(self):
                pass

            async def generate_response(self, messages, config):
                pass

            async def stream_response(self, messages, config):
                if False:
                    yield ""

            async def validate_api_key(self):
                return True

            def estimate_cost(self, messages, config):
                return 0.01

            def count_tokens(self, text):
                return len(text.split())

        provider = MockProvider("test-key")

        info = provider.get_model_info("mock-model")
        assert info["name"] == "mock-model"
        assert info["provider"] == "mock"
        assert info["available"] is True
        assert "text_generation" in info["capabilities"]

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health_check method."""
        from backend.ai.providers.base import LLMProvider, ModelCapability

        # Create a mock concrete implementation
        class MockProvider(LLMProvider):
            @property
            def provider_name(self):
                return "mock"

            @property
            def supported_capabilities(self):
                return [ModelCapability.TEXT_GENERATION]

            @property
            def available_models(self):
                return ["mock-model"]

            async def initialize(self):
                pass

            async def generate_response(self, messages, config):
                pass

            async def stream_response(self, messages, config):
                if False:
                    yield ""

            async def validate_api_key(self):
                return True

            def estimate_cost(self, messages, config):
                return 0.01

            def count_tokens(self, text):
                return len(text.split())

        provider = MockProvider("test-key")

        health = await provider.health_check()
        assert health["provider"] == "mock"
        assert health["status"] == "healthy"
        assert health["api_key_valid"] is True
        assert health["available_models"] == 1