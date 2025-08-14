"""
GROK Provider Implementation for Steve's Mom AI Chatbot

This module implements the GROK AI provider using the X.AI API,
building on the existing steves-mom-beta.py prototype.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from openai import OpenAI, AsyncOpenAI
import tiktoken

from .base import (
    LLMProvider, Message, ModelResponse, ModelConfig, ToolCall,
    ModelCapability, MessageRole, ProviderError, RateLimitError,
    AuthenticationError, ModelNotFoundError
)

logger = logging.getLogger(__name__)


class GROKProvider(LLMProvider):
    """
    GROK AI provider implementation using X.AI API.
    
    This provider integrates with GROK models through the X.AI API,
    supporting the Supreme Overlord personality from steves-mom-beta.py.
    """
    
    # GROK model configurations
    MODELS = {
        "grok-3-mini": {
            "max_tokens": 4096,
            "cost_per_1k_input": 0.0001,  # Estimated - update with actual pricing
            "cost_per_1k_output": 0.0002,
            "capabilities": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.REASONING,
                ModelCapability.STREAMING
            ]
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
                ModelCapability.CODE_GENERATION
            ]
        }
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
            api_key = os.environ.get("CUSTOM_OPENAI_API_KEY")
        
        if not api_key:
            raise AuthenticationError("GROK API key not provided", "grok")
        
        super().__init__(
            api_key=api_key,
            base_url="https://api.x.ai",
            **kwargs
        )
        
        self._sync_client = None
        self._async_client = None
        self._tokenizer = None
    
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
            ModelCapability.CODE_GENERATION
        ]
    
    @property
    def available_models(self) -> List[str]:
        """Return list of available models for this provider."""
        return list(self.MODELS.keys())
    
    async def initialize(self) -> None:
        """Initialize the GROK client and validate configuration."""
        try:
            # Initialize sync client for compatibility
            self._sync_client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
            
            # Initialize async client
            self._async_client = AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
            
            # Initialize tokenizer (using GPT-4 tokenizer as approximation)
            try:
                self._tokenizer = tiktoken.encoding_for_model("gpt-4")
            except Exception:
                self._tokenizer = tiktoken.get_encoding("cl100k_base")
            
            logger.info(f"GROK provider initialized with {len(self.available_models)} models")
            
        except Exception as e:
            logger.error(f"Failed to initialize GROK provider: {e}")
            raise ProviderError(f"Initialization failed: {e}", "grok")
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert internal Message objects to GROK API format."""
        api_messages = []
        
        for msg in messages:
            api_msg = {
                "role": msg.role.value,
                "content": msg.content
            }
            api_messages.append(api_msg)
        
        return api_messages
    
    def _create_system_message(self, use_supreme_overlord: bool = True) -> Dict[str, Any]:
        """Create system message with Supreme Overlord personality."""
        if use_supreme_overlord:
            return {
                "role": "system",
                "content": self.SUPREME_OVERLORD_PROMPT
            }
        else:
            return {
                "role": "system",
                "content": "You are a helpful AI assistant for Cannasol Technologies."
            }
    
    async def generate_response(
        self,
        messages: List[Message],
        config: ModelConfig
    ) -> ModelResponse:
        """Generate a response from GROK."""
        if not self._async_client:
            await self.initialize()
        
        if config.model_name not in self.available_models:
            raise ModelNotFoundError(
                f"Model {config.model_name} not available",
                "grok",
                config.model_name
            )
        
        try:
            # Convert messages and add system prompt
            api_messages = [self._create_system_message()]
            api_messages.extend(self._convert_messages(messages))
            
            # Prepare request parameters
            request_params = {
                "model": config.model_name,
                "messages": api_messages,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "frequency_penalty": config.frequency_penalty,
                "presence_penalty": config.presence_penalty,
                "stream": False
            }
            
            # Add tools if provided
            if config.tools:
                request_params["tools"] = config.tools
            
            # Add stop sequences if provided
            if config.stop_sequences:
                request_params["stop"] = config.stop_sequences
            
            start_time = asyncio.get_event_loop().time()
            
            # Make API call
            response = await self._async_client.chat.completions.create(**request_params)
            
            end_time = asyncio.get_event_loop().time()
            response_time = end_time - start_time
            
            # Extract response data
            choice = response.choices[0]
            content = choice.message.content or ""
            
            # Handle tool calls
            tool_calls = []
            if choice.message.tool_calls:
                for tool_call in choice.message.tool_calls:
                    tool_calls.append(ToolCall(
                        id=tool_call.id,
                        function_name=tool_call.function.name,
                        arguments=tool_call.function.arguments
                    ))
            
            # Calculate usage
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
            
            return ModelResponse(
                content=content,
                model=config.model_name,
                provider=self.provider_name,
                usage=usage,
                tool_calls=tool_calls if tool_calls else None,
                finish_reason=choice.finish_reason,
                response_time=response_time,
                metadata={
                    "api_response_id": response.id,
                    "created": response.created
                }
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
        self,
        messages: List[Message],
        config: ModelConfig
    ) -> AsyncGenerator[str, None]:
        """Stream a response from GROK."""
        if not self._async_client:
            await self.initialize()
        
        if config.model_name not in self.available_models:
            raise ModelNotFoundError(
                f"Model {config.model_name} not available",
                "grok",
                config.model_name
            )
        
        try:
            # Convert messages and add system prompt
            api_messages = [self._create_system_message()]
            api_messages.extend(self._convert_messages(messages))
            
            # Prepare request parameters
            request_params = {
                "model": config.model_name,
                "messages": api_messages,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "stream": True
            }
            
            # Make streaming API call
            stream = await self._async_client.chat.completions.create(**request_params)
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
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
            if not self._async_client:
                await self.initialize()
            
            # Make a minimal test request
            test_messages = [
                self._create_system_message(use_supreme_overlord=False),
                {"role": "user", "content": "Hello"}
            ]
            
            response = await self._async_client.chat.completions.create(
                model="grok-3-mini",
                messages=test_messages,
                max_tokens=10
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
