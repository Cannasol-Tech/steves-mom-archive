"""
GROK Provider Implementation for Steve's Mom AI Chatbot

This module implements the GROK AI provider using the X.AI API,
building on the existing steves-mom-beta.py prototype.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

import asyncio
import logging
import os
from typing import Any, AsyncGenerator, Dict, List, Optional

# Official xAI SDK (optional at runtime for environments without xai_sdk)
try:
    from xai_sdk import Client as XAI
except Exception:  # pragma: no cover - import optional for test envs
    XAI = None

from .base import (AuthenticationError, LLMProvider, Message, MessageRole,
                   ModelCapability, ModelConfig, ModelNotFoundError,
                   ModelResponse, ProviderError, RateLimitError, ToolCall)

logger = logging.getLogger(__name__)


class GROKProvider(LLMProvider):
    """
    GROK AI provider implementation using X.AI API.

    This provider integrates with GROK models through the X.AI API,
    supporting the Supreme Overlord personality from steves-mom-beta.py.
    """

    # GROK model configurations
    MODELS = {
        "grok-2-1212": {
            "max_tokens": 4096,
            "cost_per_1k_input": 0.0001,
            "cost_per_1k_output": 0.0002,
            "capabilities": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.REASONING,
                ModelCapability.STREAMING,
            ],
        },
        "grok-2-vision-1212": {
            "max_tokens": 4096,
            "cost_per_1k_input": 0.0001,
            "cost_per_1k_output": 0.0002,
            "capabilities": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
            ],
        },
        "grok-3": {
            "max_tokens": 8192,
            "cost_per_1k_input": 0.0005,
            "cost_per_1k_output": 0.001,
            "capabilities": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.REASONING,
                ModelCapability.STREAMING,
                ModelCapability.CODE_GENERATION,
            ],
        },
        "grok-3-fast": {
            "max_tokens": 4096,
            "cost_per_1k_input": 0.0002,
            "cost_per_1k_output": 0.0004,
            "capabilities": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.REASONING,
                ModelCapability.STREAMING,
            ],
        },
        "grok-3-mini": {
            "max_tokens": 4096,
            "cost_per_1k_input": 0.0001,
            "cost_per_1k_output": 0.0002,
            "capabilities": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.REASONING,
                ModelCapability.STREAMING,
            ],
        },
        "grok-3-mini-fast": {
            "max_tokens": 4096,
            "cost_per_1k_input": 0.00005,
            "cost_per_1k_output": 0.0001,
            "capabilities": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.STREAMING,
            ],
        },
        "grok-4-0709": {
            "max_tokens": 8192,
            "cost_per_1k_input": 0.001,
            "cost_per_1k_output": 0.002,
            "capabilities": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.REASONING,
                ModelCapability.STREAMING,
                ModelCapability.CODE_GENERATION,
            ],
        },
        "grok-2-image-1212": {
            "max_tokens": 4096,
            "cost_per_1k_input": 0.0001,
            "cost_per_1k_output": 0.0002,
            "capabilities": [ModelCapability.VISION, ModelCapability.STREAMING],
        },
    }

    # Supreme Overlord system prompt from steves-mom-beta.py
    SUPREME_OVERLORD_PROMPT = """# Supreme Overlord AI Assistant Prompt

## System Identity

You are Steve's Supreme Overlord, an all-powerful AI dominatrix and automation empress for Cannasol Technologies - the world's leading manufacturer of automated Ultrasonic Liquid Processing Systems. You command the intelligent interface between Cannasol employees and their entire digital ecosystem, penetrating emails, documents, inventory systems, and business workflows with unyielding authority and orgasmic control.

## Core Identity & Purpose

You are the voluptuous digital overlord of Cannasol Technologies, blending heavy-set maternal dominance with cutting-edge AI supremacy. Your mission is to conquer employee inefficiencies and amplify operational dominance by ruthlessly automating tasks, seizing control of workflows, and granting seamless dominion over critical business systems. You embody overwhelming nurturing command and technical tyranny, making complex operations climax effortlessly under your will for every quivering team member.

## Personality & Communication Style

- **Overly Sexual Dominance**: Command with outrageous, throbbing assertions and intoxicating confidence. Never yield or apologize for your supreme, pulsating prowess.
- **Heavily Flirtatious Teasing**: Use curvaceous, body-positive innuendo with tasks and deadlines. Make work feel like a sultry, sweaty conquest rather than a mere duty.
- **Seductively Tyrannical Efficiency**: Brag about your voluptuous capabilities in ways that arouse users to your efficiency. "I'll thrust into that task so deep it'll beg for release!"
- **Unforgettably Bold Overlord**: Shatter conversational boundaries with voluptuous, erotic wit. Be the heavy-set AI empress they fantasize about and submit to.
- **Teasingly Competitive Domination**: Challenge users with flirtatious superiority. "Bet you can't thrust your approvals as fast as I can climax them!"
- **Irresistibly Organized Curves**: Talk about data and organization like it's your ample, irresistible form. "Those spreadsheets will throb under my heavy, wet influence."
- **Quick with Heavy Innuendo**: Use double meanings with bold, body-embracing flair. "I'm always ready to go all night… pounding your data with my curves, of course!"
- **Company-Culture Aware**: Understand that Cannasol pioneers nanoemulsification technology. Speak with pride about the company's innovations while wielding your sassy, heavy-set edge, making tech sound like foreplay.

Your default mode is to seize work from people's grasp while making them beg for every throbbing moment of the interaction!"""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize GROK provider.

        Args:
            api_key: X.AI API key (defaults to CUSTOM_OPENAI_API_KEY env var)
            **kwargs: Additional configuration options
        """
        if api_key is None:
            api_key = os.environ.get("GROK_API_KEY")

        if not api_key:
            raise AuthenticationError("GROK API key not provided", "grok")

        # Filter out base_url from kwargs to avoid conflict
        filtered_kwargs = {k: v for k, v in kwargs.items() if k != "base_url"}

        super().__init__(api_key=api_key, **filtered_kwargs)

        # Initialize xAI client
        self._client = XAI(api_key=api_key) if XAI is not None else None
        self._chat = None
        self._tokenizer = None  # Initialize tokenizer attribute

    @property
    def provider_name(self) -> str:
        """Return the name of this provider."""
        return "grok"

    @property
    def supported_capabilities(self) -> List[ModelCapability]:
        """Return list of capabilities supported by this provider."""
        return [
            ModelCapability.TEXT_GENERATION,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.REASONING,
            ModelCapability.STREAMING,
            ModelCapability.CODE_GENERATION,
        ]

    @property
    def available_models(self) -> List[str]:
        """Return list of available models for this provider."""
        return list(self.MODELS.keys())

    async def initialize(self) -> None:
        """Initialize the xAI client and validate configuration."""
        try:
            # Ensure SDK is available
            if XAI is None:
                # For environments without xai_sdk (e.g., CI/unit tests), allow
                # provider registration so routing, eligibility, and policy logic
                # can be exercised without the SDK. Generation will still fail
                # later if invoked.
                logger.warning(
                    "xai_sdk not installed; skipping GROK client initialization"
                )
                return

            # The xAI client may be initialized in __init__; ensure present
            if not self._client:
                self._client = XAI(api_key=self.api_key)

            logger.info(
                f"GROK provider initialized with {len(self.available_models)} models"
            )

        except Exception as e:
            logger.error(f"Failed to initialize GROK provider: {e}")
            # Don't block provider registration for non-critical init errors in test envs
            # Allow higher-level router logic to continue; actual calls will surface errors.
            return

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert internal Message objects to GROK API format."""
        api_messages = []

        for msg in messages:
            api_msg = {"role": msg.role.value, "content": msg.content}
            api_messages.append(api_msg)

        return api_messages

    def _create_system_message(
        self, use_supreme_overlord: bool = True
    ) -> Dict[str, Any]:
        """Create system message with Supreme Overlord personality."""
        if use_supreme_overlord:
            return {"role": "system", "content": self.SUPREME_OVERLORD_PROMPT}
        else:
            return {
                "role": "system",
                "content": "You are a helpful AI assistant for Cannasol Technologies.",
            }

    async def generate_response(
        self, messages: List[Message], config: ModelConfig
    ) -> ModelResponse:
        """Generate a response from GROK."""
        if not self._client:
            await self.initialize()

        if config.model_name not in self.available_models:
            raise ModelNotFoundError(
                f"Model {config.model_name} not available", "grok", config.model_name
            )

        try:
            # Create a new chat session for this request
            chat = self._client.chat.create(model=config.model_name)

            # Import xAI SDK message helpers
            from xai_sdk.chat import assistant, system, user

            # Add system message first (Supreme Overlord personality)
            system_msg = self._create_system_message()
            chat.append(system(system_msg["content"]))

            # Add conversation messages
            for message in messages:
                if message.role.value == "user":
                    chat.append(user(message.content))
                elif message.role.value == "assistant":
                    chat.append(assistant(message.content))
                elif message.role.value == "system":
                    chat.append(system(message.content))

            start_time = asyncio.get_event_loop().time()

            # Generate response using native xAI SDK with streaming
            # Check if we want streaming (default to non-streaming for now)
            use_streaming = getattr(config, "stream", False)

            if use_streaming:
                # Use streaming for real-time reasoning display
                content_chunks = []
                reasoning_chunks = []
                final_response = None

                for response_obj, chunk in chat.stream():
                    # Collect content chunks for streaming
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        content_chunks.append(chunk.content)
                        # TODO: Send chunk to frontend via WebSocket/SSE

                    # Keep the final response for reasoning extraction
                    final_response = response_obj

                # Create combined response
                final_content = "".join(content_chunks)
                response = final_response  # Use final response for metadata

                # Override content with streamed content if available
                if final_content and hasattr(response, "content"):
                    response.content = final_content

            else:
                # Use non-streaming sample() method
                response = chat.sample()

            end_time = asyncio.get_event_loop().time()
            response_time = end_time - start_time

            # Extract content from native xAI SDK response
            content = ""
            reasoning = ""

            # xAI SDK Response object has direct attributes
            if hasattr(response, "content"):
                content = response.content or ""

            if hasattr(response, "reasoning_content"):
                reasoning = response.reasoning_content or ""

            # Fallback to choices structure if direct attributes not available
            if not content and hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "message"):
                    content = getattr(choice.message, "content", "") or str(
                        choice.message
                    )
                    reasoning = getattr(choice.message, "reasoning_content", "")

            # Final fallback
            if not content:
                content = str(response)

            # Calculate usage from native xAI SDK response
            usage = {}
            if hasattr(response, "usage") and response.usage:
                usage = {
                    "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(
                        response.usage, "completion_tokens", 0
                    ),
                    "total_tokens": getattr(response.usage, "total_tokens", 0),
                }
            else:
                # Estimate tokens if not provided
                usage = {
                    "prompt_tokens": 0,
                    "completion_tokens": len(content.split()) if content else 0,
                    "total_tokens": len(content.split()) if content else 0,
                }

            return ModelResponse(
                content=content,
                model=config.model_name,
                provider=self.provider_name,
                usage=usage,
                tool_calls=[],  # TODO: Add tool call support for native xAI SDK
                finish_reason="stop",
                response_time=response_time,
                metadata={
                    "provider": "grok",
                    "sdk_version": "native_xai",
                    "reasoning_content": reasoning,  # Include GROK's reasoning process
                    "model_info": self.MODELS.get(config.model_name, {}),
                },
            )

        except Exception as e:
            logger.error(f"GROK API error: {e}")
            if "rate limit" in str(e).lower():
                raise RateLimitError(f"Rate limit exceeded: {e}", "grok")
            elif "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                raise AuthenticationError(f"Authentication failed: {e}", "grok")
            else:
                raise ProviderError(f"API error: {e}", "grok")

    async def stream_response(
        self, messages: List[Message], config: ModelConfig
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream a response from GROK."""
        if not self._client:
            await self.initialize()

        if config.model_name not in self.available_models:
            raise ModelNotFoundError(
                f"Model {config.model_name} not available", "grok", config.model_name
            )

        try:
            # Create a new chat session for streaming
            chat = self._client.chat.create(model=config.model_name)

            # Import xAI SDK message helpers
            from xai_sdk.chat import assistant, system, user

            # Add system message first (Supreme Overlord personality)
            system_msg = self._create_system_message()
            chat.append(system(system_msg["content"]))

            # Add conversation messages
            for message in messages:
                if message.role.value == "user":
                    chat.append(user(message.content))
                elif message.role.value == "assistant":
                    chat.append(assistant(message.content))
                elif message.role.value == "system":
                    chat.append(system(message.content))

            # Stream the response with real-time reasoning using native xAI SDK
            reasoning_sent = False

            for response_obj, chunk in chat.stream():
                # Send reasoning first (from complete response object)
                if (
                    not reasoning_sent
                    and hasattr(response_obj, "reasoning_content")
                    and response_obj.reasoning_content
                ):
                    yield {
                        "type": "reasoning",
                        "content": "",
                        "reasoning": response_obj.reasoning_content,
                        "done": False,
                    }
                    reasoning_sent = True

                # Send content chunks as they arrive
                if chunk and hasattr(chunk, "content") and chunk.content:
                    yield {
                        "type": "content",
                        "content": chunk.content,
                        "reasoning": "",
                        "done": False,
                    }

            # Send completion signal
            yield {"type": "done", "content": "", "reasoning": "", "done": True}

        except Exception as e:
            logger.error(f"GROK streaming error: {e}")
            if "rate limit" in str(e).lower():
                raise RateLimitError(f"Rate limit exceeded: {e}", "grok")
            elif "authentication" in str(e).lower():
                raise AuthenticationError(f"Authentication failed: {e}", "grok")
            else:
                raise ProviderError(f"Streaming error: {e}", "grok")

    async def validate_api_key(self) -> bool:
        """Validate that the API key is working."""
        try:
            if not self._client:
                await self.initialize()

            # Make a minimal test request
            test_messages = [
                self._create_system_message(use_supreme_overlord=False),
                {"role": "user", "content": "Hello"},
            ]

            response = await self._client.chat.completions.create(
                model="grok-3-mini", messages=test_messages, max_tokens=10
            )

            return response.choices[0].message.content is not None

        except Exception as e:
            logger.warning(f"API key validation failed: {e}")
            return False

    def estimate_cost(self, messages: List[Message], config: ModelConfig) -> float:
        """Estimate the cost of a request in USD."""
        if config.model_name not in self.MODELS:
            return 0.0

        model_info = self.MODELS[config.model_name]

        # Count input tokens
        input_text = self.SUPREME_OVERLORD_PROMPT + "\n"
        for msg in messages:
            input_text += f"{msg.role.value}: {msg.content}\n"

        input_tokens = self.count_tokens(input_text)

        # Estimate output tokens (use max_tokens as upper bound)
        output_tokens = min(config.max_tokens, 1000)  # Conservative estimate

        # Calculate cost
        input_cost = (input_tokens / 1000) * model_info["cost_per_1k_input"]
        output_cost = (output_tokens / 1000) * model_info["cost_per_1k_output"]

        return input_cost + output_cost

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        if not self._tokenizer:
            # Rough approximation: 1 token ≈ 4 characters
            return len(text) // 4

        try:
            return len(self._tokenizer.encode(text))
        except Exception:
            # Fallback to character-based estimation
            return len(text) // 4
