"""
Unit tests for backend.api.schemas

Tests Pydantic models for API request/response validation including:
- ChatMessage validation and serialization
- ChatRequest validation with field constraints
- ChatResponse model structure and optional fields
- Role type validation and constraints
- Edge cases and error handling

Author: Cannasol Technologies
Date: 2025-01-04
Version: 1.0.0
"""

import pytest
from pydantic import ValidationError
from typing import List

import sys
from pathlib import Path

# Ensure backend package is importable
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.api.schemas import ChatMessage, ChatRequest, ChatResponse, Role


class TestChatMessage:
    """Test ChatMessage model validation and behavior."""

    def test_valid_chat_message_creation(self):
        """Test creating valid ChatMessage instances."""
        # Test user message
        user_msg = ChatMessage(role="user", content="Hello, how are you?")
        assert user_msg.role == "user"
        assert user_msg.content == "Hello, how are you?"

        # Test assistant message
        assistant_msg = ChatMessage(role="assistant", content="I'm doing well, thank you!")
        assert assistant_msg.role == "assistant"
        assert assistant_msg.content == "I'm doing well, thank you!"

        # Test system message
        system_msg = ChatMessage(role="system", content="You are a helpful assistant.")
        assert system_msg.role == "system"
        assert system_msg.content == "You are a helpful assistant."

    def test_invalid_role_validation(self):
        """Test that invalid roles are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ChatMessage(role="invalid_role", content="Test content")

        error = exc_info.value.errors()[0]
        assert error["type"] == "literal_error"
        assert "invalid_role" in str(error["input"])

    def test_empty_content_validation(self):
        """Test that empty content is allowed."""
        # Empty string should be valid
        msg = ChatMessage(role="user", content="")
        assert msg.content == ""

    def test_chat_message_serialization(self):
        """Test ChatMessage serialization to dict and JSON."""
        msg = ChatMessage(role="user", content="Test message")

        # Test model_dump
        data = msg.model_dump()
        expected = {"role": "user", "content": "Test message"}
        assert data == expected

        # Test JSON serialization
        json_str = msg.model_dump_json()
        assert '"role":"user"' in json_str
        assert '"content":"Test message"' in json_str

    def test_chat_message_deserialization(self):
        """Test creating ChatMessage from dict."""
        data = {"role": "assistant", "content": "Response message"}
        msg = ChatMessage(**data)
        assert msg.role == "assistant"
        assert msg.content == "Response message"


class TestChatRequest:
    """Test ChatRequest model validation and constraints."""

    def test_valid_chat_request_creation(self):
        """Test creating valid ChatRequest instances."""
        messages = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi there!")
        ]

        request = ChatRequest(messages=messages)
        assert len(request.messages) == 2
        assert request.model is None  # Default value
        assert request.temperature == 0.2  # Default value
        assert request.max_tokens == 512  # Default value
        assert request.stream_reasoning is False  # Default value

    def test_chat_request_with_optional_fields(self):
        """Test ChatRequest with all optional fields set."""
        messages = [ChatMessage(role="user", content="Test")]

        request = ChatRequest(
            messages=messages,
            model="grok-3-mini",
            temperature=0.7,
            max_tokens=1024,
            stream_reasoning=True
        )

        assert request.model == "grok-3-mini"
        assert request.temperature == 0.7
        assert request.max_tokens == 1024
        assert request.stream_reasoning is True

    def test_empty_messages_validation(self):
        """Test that empty messages list is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(messages=[])

        error = exc_info.value.errors()[0]
        assert error["type"] == "too_short"
        assert "at least 1" in error["msg"]

    def test_messages_min_length_constraint(self):
        """Test that messages list must have at least one item."""
        # Single message should be valid
        messages = [ChatMessage(role="user", content="Test")]
        request = ChatRequest(messages=messages)
        assert len(request.messages) == 1

        # Multiple messages should be valid
        messages = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi"),
            ChatMessage(role="user", content="How are you?")
        ]
        request = ChatRequest(messages=messages)
        assert len(request.messages) == 3

    def test_temperature_validation(self):
        """Test temperature field validation."""
        messages = [ChatMessage(role="user", content="Test")]

        # Valid temperature values
        for temp in [0.0, 0.5, 1.0, 2.0]:
            request = ChatRequest(messages=messages, temperature=temp)
            assert request.temperature == temp

        # None should be valid (optional field)
        request = ChatRequest(messages=messages, temperature=None)
        assert request.temperature is None

    def test_max_tokens_validation(self):
        """Test max_tokens field validation."""
        messages = [ChatMessage(role="user", content="Test")]

        # Valid max_tokens values
        for tokens in [1, 100, 1000, 4096]:
            request = ChatRequest(messages=messages, max_tokens=tokens)
            assert request.max_tokens == tokens

        # None should be valid (optional field)
        request = ChatRequest(messages=messages, max_tokens=None)
        assert request.max_tokens is None

    def test_stream_reasoning_validation(self):
        """Test stream_reasoning boolean field."""
        messages = [ChatMessage(role="user", content="Test")]

        # Test both boolean values
        request_true = ChatRequest(messages=messages, stream_reasoning=True)
        assert request_true.stream_reasoning is True

        request_false = ChatRequest(messages=messages, stream_reasoning=False)
        assert request_false.stream_reasoning is False


class TestChatResponse:
    """Test ChatResponse model validation and structure."""

    def test_valid_chat_response_creation(self):
        """Test creating valid ChatResponse instances."""
        message = ChatMessage(role="assistant", content="Response content")

        response = ChatResponse(
            message=message,
            provider="grok",
            model="grok-3-mini"
        )

        assert response.message == message
        assert response.provider == "grok"
        assert response.model == "grok-3-mini"
        assert response.response_time_ms is None  # Default
        assert response.reasoning_content is None  # Default
        assert response.prompt_tokens is None  # Default
        assert response.completion_tokens is None  # Default
        assert response.total_tokens is None  # Default

    def test_chat_response_with_all_fields(self):
        """Test ChatResponse with all optional fields set."""
        message = ChatMessage(role="assistant", content="Full response")

        response = ChatResponse(
            message=message,
            provider="openai",
            model="gpt-4",
            response_time_ms=1500,
            reasoning_content="Thinking step by step...",
            prompt_tokens=50,
            completion_tokens=100,
            total_tokens=150
        )

        assert response.response_time_ms == 1500
        assert response.reasoning_content == "Thinking step by step..."
        assert response.prompt_tokens == 50
        assert response.completion_tokens == 100
        assert response.total_tokens == 150

    def test_chat_response_required_fields(self):
        """Test that required fields are enforced."""
        message = ChatMessage(role="assistant", content="Test")

        # Missing provider should raise ValidationError
        with pytest.raises(ValidationError):
            ChatResponse(message=message, model="test-model")

        # Missing model should raise ValidationError
        with pytest.raises(ValidationError):
            ChatResponse(message=message, provider="test-provider")

        # Missing message should raise ValidationError
        with pytest.raises(ValidationError):
            ChatResponse(provider="test-provider", model="test-model")

    def test_chat_response_serialization(self):
        """Test ChatResponse serialization."""
        message = ChatMessage(role="assistant", content="Test response")
        response = ChatResponse(
            message=message,
            provider="test-provider",
            model="test-model",
            response_time_ms=1000
        )

        data = response.model_dump()
        assert data["message"]["role"] == "assistant"
        assert data["message"]["content"] == "Test response"
        assert data["provider"] == "test-provider"
        assert data["model"] == "test-model"
        assert data["response_time_ms"] == 1000


class TestRoleType:
    """Test Role literal type validation."""

    def test_valid_roles(self):
        """Test that all valid roles are accepted."""
        valid_roles = ["user", "assistant", "system"]

        for role in valid_roles:
            msg = ChatMessage(role=role, content="Test")
            assert msg.role == role

    def test_role_type_annotation(self):
        """Test that Role type is properly defined."""
        # This tests the type annotation itself
        from backend.api.schemas import Role

        # Role should be a Literal type with specific values
        # We can't directly test Literal types, but we can test usage
        msg = ChatMessage(role="user", content="Test")
        assert isinstance(msg.role, str)
        assert msg.role in ["user", "assistant", "system"]


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_very_long_content(self):
        """Test handling of very long content strings."""
        long_content = "x" * 10000  # 10k characters
        msg = ChatMessage(role="user", content=long_content)
        assert len(msg.content) == 10000

    def test_unicode_content(self):
        """Test handling of Unicode characters."""
        unicode_content = "Hello 🌍! How are you? 你好 🚀"
        msg = ChatMessage(role="user", content=unicode_content)
        assert msg.content == unicode_content

    def test_special_characters_in_content(self):
        """Test handling of special characters."""
        special_content = 'Content with "quotes", newlines\n\nand tabs\t!'
        msg = ChatMessage(role="user", content=special_content)
        assert msg.content == special_content

    def test_nested_message_validation(self):
        """Test validation of nested ChatMessage in ChatRequest."""
        # Invalid nested message should be caught
        with pytest.raises(ValidationError):
            ChatRequest(messages=[{"role": "invalid", "content": "test"}])

    def test_model_dump_exclude_none(self):
        """Test serialization with exclude_none option."""
        message = ChatMessage(role="assistant", content="Test")
        response = ChatResponse(
            message=message,
            provider="test",
            model="test-model"
        )

        # With exclude_none=True, None values should be excluded
        data = response.model_dump(exclude_none=True)
        assert "response_time_ms" not in data
        assert "reasoning_content" not in data
        assert "prompt_tokens" not in data