"""
Base LLM Provider Interface for Steve's Mom AI Chatbot

This module defines the abstract base class for all AI model providers,
ensuring consistent interface across GROK, OpenAI, Claude, and other providers.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from dataclasses import dataclass
from enum import Enum
import time
import uuid


class ModelCapability(Enum):
    """Enumeration of AI model capabilities."""
    TEXT_GENERATION = "text_generation"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    STREAMING = "streaming"


class MessageRole(Enum):
    """Enumeration of message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: MessageRole
    content: str
    timestamp: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ToolCall:
    """Represents a tool/function call from the AI model."""
    id: str
    function_name: str
    arguments: Dict[str, Any]
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class ModelResponse:
    """Represents a response from an AI model."""
    content: str
    model: str
    provider: str
    usage: Dict[str, int]  # tokens, cost, etc.
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Optional[str] = None
    response_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ModelConfig:
    """Configuration for AI model requests."""
    model_name: str
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    
    def __post_init__(self):
        if self.stop_sequences is None:
            self.stop_sequences = []
        if self.tools is None:
            self.tools = []


class LLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    
    This class defines the standard interface that all AI model providers
    must implement, ensuring consistency across different services.
    """
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, **kwargs):
        """
        Initialize the LLM provider.
        
        Args:
            api_key: API key for the provider
            base_url: Base URL for the provider's API (if applicable)
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs
        self._client = None
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider."""
        pass
    
    @property
    @abstractmethod
    def supported_capabilities(self) -> List[ModelCapability]:
        """Return list of capabilities supported by this provider."""
        pass
    
    @property
    @abstractmethod
    def available_models(self) -> List[str]:
        """Return list of available models for this provider."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider client and validate configuration."""
        pass
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Message],
        config: ModelConfig
    ) -> ModelResponse:
        """
        Generate a response from the AI model.
        
        Args:
            messages: List of conversation messages
            config: Model configuration parameters
            
        Returns:
            ModelResponse containing the AI's response
        """
        pass
    
    @abstractmethod
    async def stream_response(
        self,
        messages: List[Message],
        config: ModelConfig
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from the AI model.
        
        Args:
            messages: List of conversation messages
            config: Model configuration parameters
            
        Yields:
            Chunks of the AI's response as they become available
        """
        pass
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """
        Validate that the API key is working.
        
        Returns:
            True if API key is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, messages: List[Message], config: ModelConfig) -> float:
        """
        Estimate the cost of a request in USD.
        
        Args:
            messages: List of conversation messages
            config: Model configuration parameters
            
        Returns:
            Estimated cost in USD
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        pass
    
    def supports_capability(self, capability: ModelCapability) -> bool:
        """
        Check if this provider supports a specific capability.
        
        Args:
            capability: Capability to check
            
        Returns:
            True if capability is supported
        """
        return capability in self.supported_capabilities
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get information about a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary containing model information
        """
        return {
            "name": model_name,
            "provider": self.provider_name,
            "capabilities": [cap.value for cap in self.supported_capabilities],
            "available": model_name in self.available_models
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the provider.
        
        Returns:
            Dictionary containing health status information
        """
        try:
            is_valid = await self.validate_api_key()
            return {
                "provider": self.provider_name,
                "status": "healthy" if is_valid else "unhealthy",
                "api_key_valid": is_valid,
                "available_models": len(self.available_models),
                "capabilities": [cap.value for cap in self.supported_capabilities]
            }
        except Exception as e:
            return {
                "provider": self.provider_name,
                "status": "error",
                "error": str(e),
                "api_key_valid": False
            }
    
    def __repr__(self) -> str:
        """String representation of the provider."""
        return f"{self.__class__.__name__}(provider={self.provider_name})"


class ProviderError(Exception):
    """Base exception for provider-related errors."""
    
    def __init__(self, message: str, provider: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code


class RateLimitError(ProviderError):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(self, message: str, provider: str, retry_after: Optional[int] = None):
        super().__init__(message, provider, "rate_limit")
        self.retry_after = retry_after


class AuthenticationError(ProviderError):
    """Exception raised when authentication fails."""
    
    def __init__(self, message: str, provider: str):
        super().__init__(message, provider, "authentication")


class ModelNotFoundError(ProviderError):
    """Exception raised when requested model is not available."""
    
    def __init__(self, message: str, provider: str, model_name: str):
        super().__init__(message, provider, "model_not_found")
        self.model_name = model_name


class QuotaExceededError(ProviderError):
    """Exception raised when quota is exceeded."""
    
    def __init__(self, message: str, provider: str):
        super().__init__(message, provider, "quota_exceeded")
