"""
Base LLM Provider Abstract Class

This module defines the abstract base class for all LLM providers,
ensuring a consistent interface across different AI services.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from ...models.ai_models import AIModelConfig, AIResponse, ChatMessage

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Enumeration of supported provider types."""

    GROK = "grok"
    OPENAI = "openai"
    CLAUDE = "claude"
    LOCAL = "local"
    AZURE_OPENAI = "azure_openai"


class ProviderCapability(str, Enum):
    """Provider capabilities for routing decisions."""

    CHAT = "chat"
    COMPLETION = "completion"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    VISION = "vision"
    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    MULTIMODAL = "multimodal"


@dataclass
class ProviderConfig:
    """Configuration for LLM providers."""

    provider_type: ProviderType
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: str = "default"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    capabilities: Optional[List[ProviderCapability]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.capabilities is None:
            self.capabilities = [ProviderCapability.CHAT]
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProviderResponse:
    """Standardized response from LLM providers."""

    content: str
    provider_type: ProviderType
    model_used: str
    usage: Dict[str, int]
    response_time_ms: int
    finish_reason: Optional[str] = None
    function_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.function_calls is None:
            self.function_calls = []
        if self.metadata is None:
            self.metadata = {}


class LLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    This class defines the standard interface that all providers must implement,
    ensuring consistency and interoperability across different AI services.
    """

    def __init__(self, config: ProviderConfig):
        """Initialize the provider with configuration."""
        self.config = config
        self.provider_type = config.provider_type
        self.is_initialized = False
        self._client = None

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the provider (authenticate, validate config, etc.).

        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        model_config: Optional[AIModelConfig] = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """
        Send chat messages and get response.

        Args:
            messages: List of chat messages
            model_config: Optional model configuration overrides
            **kwargs: Additional provider-specific parameters

        Returns:
            ProviderResponse: Standardized response object
        """
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[ChatMessage],
        model_config: Optional[AIModelConfig] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response in real-time.

        Args:
            messages: List of chat messages
            model_config: Optional model configuration overrides
            **kwargs: Additional provider-specific parameters

        Yields:
            str: Streaming response chunks
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider health and availability.

        Returns:
            Dict containing health status, latency, and other metrics
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[ProviderCapability]:
        """
        Get list of capabilities supported by this provider.

        Returns:
            List of supported capabilities
        """
        pass

    @abstractmethod
    def get_cost_per_token(self, model_name: Optional[str] = None) -> Dict[str, float]:
        """
        Get cost per token for input/output.

        Args:
            model_name: Optional specific model name

        Returns:
            Dict with 'input' and 'output' cost per token
        """
        pass

    @abstractmethod
    def get_context_window(self, model_name: Optional[str] = None) -> int:
        """
        Get maximum context window size for the model.

        Args:
            model_name: Optional specific model name

        Returns:
            Maximum context window size in tokens
        """
        pass

    # Common utility methods (implemented in base class)

    def is_available(self) -> bool:
        """Check if provider is available and initialized."""
        return self.is_initialized and self._client is not None

    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information and metadata."""
        return {
            "provider_type": self.provider_type.value,
            "model_name": self.config.model_name,
            "capabilities": [cap.value for cap in self.get_capabilities()],
            "is_available": self.is_available(),
            "config": {
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "timeout_seconds": self.config.timeout_seconds,
            },
        }

    async def validate_messages(self, messages: List[ChatMessage]) -> bool:
        """
        Validate message format and content.

        Args:
            messages: List of messages to validate

        Returns:
            bool: True if messages are valid
        """
        if not messages:
            return False

        for message in messages:
            if not message.content or not message.content.strip():
                return False

        return True

    def _calculate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4

    async def _handle_rate_limit(self, attempt: int) -> None:
        """
        Handle rate limiting with exponential backoff.

        Args:
            attempt: Current retry attempt number
        """
        delay = self.config.retry_delay * (2**attempt)
        logger.warning(f"Rate limited, waiting {delay}s before retry {attempt}")
        await asyncio.sleep(delay)

    def _create_error_response(self, error: Exception) -> ProviderResponse:
        """
        Create error response for failed requests.

        Args:
            error: Exception that occurred

        Returns:
            ProviderResponse with error information
        """
        return ProviderResponse(
            content=f"Error: {str(error)}",
            provider_type=self.provider_type,
            model_used=self.config.model_name,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            response_time_ms=0,
            finish_reason="error",
            metadata={"error": str(error), "error_type": type(error).__name__},
        )

    async def cleanup(self) -> None:
        """Clean up provider resources."""
        if self._client:
            # Close any connections, cleanup resources
            pass
        self.is_initialized = False
        logger.info(f"Provider {self.provider_type.value} cleaned up")


class ProviderError(Exception):
    """Base exception for provider-related errors."""

    def __init__(
        self,
        message: str,
        provider_type: "ProviderType",
        error_code: str,
        retriable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.provider_type = provider_type
        self.error_code = error_code
        self.retriable = retriable

    def __str__(self) -> str:
        return f"{self.provider_type.value.upper()} Error ({self.error_code}): {self.message}"


class ProviderAuthError(ProviderError):
    """Authentication error with provider."""

    def __init__(self, message: str, provider_type: "ProviderType", error_code: str):
        super().__init__(message, provider_type, error_code)


class ProviderRateLimitError(ProviderError):
    """Raised for rate limit errors."""

    def __init__(self, message: str, provider_type: "ProviderType", error_code: str):
        super().__init__(message, provider_type, error_code, retriable=True)


class ProviderTimeoutError(ProviderError):
    """Raised for timeout errors."""

    def __init__(self, message: str, provider_type: "ProviderType", error_code: str):
        super().__init__(message, provider_type, error_code, retriable=True)


class ProviderUnavailableError(ProviderError):
    """Raised for service unavailable errors."""

    def __init__(self, message: str, provider_type: "ProviderType", error_code: str):
        super().__init__(message, provider_type, error_code, retriable=False)
