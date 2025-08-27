"""
Unit tests for backend.ai.providers.base_provider core behaviors

Covers:
- get_provider_info returns required keys and types
- validate_messages rejects empty/whitespace and accepts valid content
- _calculate_tokens returns positive value and scales with input length
"""

import sys
from pathlib import Path
from typing import List
import pytest

# Ensure backend is importable
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.models.ai_models import ChatMessage, MessageRole, AIModelConfig
from backend.ai.providers.base_provider import (
    LLMProvider,
    ProviderConfig,
    ProviderType,
    ProviderCapability,
)


class DummyProvider(LLMProvider):
    async def initialize(self) -> bool:
        self.is_initialized = True
        return True

    async def chat(self, messages: List[ChatMessage], model_config: AIModelConfig = None, **kwargs):
        raise NotImplementedError

    async def stream_chat(self, messages: List[ChatMessage], model_config: AIModelConfig = None, **kwargs):
        raise NotImplementedError

    async def health_check(self):
        return {"status": "ok"}

    def get_capabilities(self):
        return [ProviderCapability.CHAT]

    def get_cost_per_token(self, model_name: str = None):
        return {"input": 0.0, "output": 0.0}

    def get_context_window(self, model_name: str = None) -> int:
        return 8192


def make_messages(text: str) -> List[ChatMessage]:
    return [ChatMessage(role=MessageRole.USER, content=text)]


def test_get_provider_info_keys_and_types():
    cfg = ProviderConfig(provider_type=ProviderType.LOCAL, model_name="test-model")
    provider = DummyProvider(cfg)

    info = provider.get_provider_info()

    assert set(["provider_type", "model_name", "capabilities", "is_available", "config"]) <= set(info.keys())
    assert isinstance(info["provider_type"], str)
    assert isinstance(info["model_name"], str)
    assert isinstance(info["capabilities"], list)
    assert isinstance(info["is_available"], bool)
    assert isinstance(info["config"], dict)


@pytest.mark.asyncio
async def test_validate_messages_accepts_valid_and_rejects_empty():
    cfg = ProviderConfig(provider_type=ProviderType.LOCAL, model_name="test-model")
    provider = DummyProvider(cfg)

    assert await provider.validate_messages(make_messages("hello")) is True
    assert await provider.validate_messages([]) is False
    assert await provider.validate_messages(make_messages("   ")) is False


def test_calculate_tokens_positive_and_scaling():
    cfg = ProviderConfig(provider_type=ProviderType.LOCAL, model_name="test-model")
    provider = DummyProvider(cfg)

    short = provider._calculate_tokens("abcd")
    longer = provider._calculate_tokens("abcd" * 10)

    assert short >= 1
    assert longer > short

