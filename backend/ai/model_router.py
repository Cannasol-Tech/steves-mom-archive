"""
Model Router for Steve's Mom AI Chatbot

This module implements intelligent routing between different AI providers
based on cost, latency, capability, and availability policies.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

import asyncio
import os
import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import time

from .providers.base import (
    LLMProvider, Message, ModelResponse, ModelConfig,
    ModelCapability, ProviderError, RateLimitError
)
from .providers.grok_provider import GROKProvider
from .providers.config_manager import ProviderConfigManager, config_manager

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Enumeration of routing strategies."""
    COST_OPTIMIZED = "cost_optimized"
    LATENCY_OPTIMIZED = "latency_optimized"
    CAPABILITY_BASED = "capability_based"
    ROUND_ROBIN = "round_robin"
    FAILOVER = "failover"
    LOAD_BALANCED = "load_balanced"


@dataclass
class ProviderConfig:
    """Configuration for a provider in the router."""
    provider: LLMProvider
    priority: int = 1  # Higher number = higher priority
    weight: float = 1.0  # For load balancing
    max_requests_per_minute: int = 60
    max_cost_per_request: float = 0.10
    enabled: bool = True
    fallback_order: int = 0  # 0 = primary, 1 = first fallback, etc.


@dataclass
class RoutingPolicy:
    """Policy for routing decisions."""
    strategy: RoutingStrategy = RoutingStrategy.COST_OPTIMIZED
    max_cost_threshold: float = 0.05
    max_latency_threshold: float = 10.0  # seconds
    required_capabilities: List[ModelCapability] = None
    preferred_providers: List[str] = None
    fallback_enabled: bool = True
    retry_attempts: int = 3
    
    def __post_init__(self):
        if self.required_capabilities is None:
            self.required_capabilities = []
        if self.preferred_providers is None:
            self.preferred_providers = []


class ModelRouter:
    """
    Intelligent router for AI model providers.
    
    Routes requests to the most appropriate provider based on
    cost, latency, capabilities, and availability.
    """
    
    def __init__(self, default_policy: Optional[RoutingPolicy] = None):
        """
        Initialize the model router.
        
        Args:
            default_policy: Default routing policy to use
        """
        self.providers: Dict[str, ProviderConfig] = {}
        self.default_policy = default_policy or RoutingPolicy()
        self._request_counts: Dict[str, List[float]] = {}
        self._latency_history: Dict[str, List[float]] = {}
        self._error_counts: Dict[str, int] = {}
        self._circuit_breakers: Dict[str, bool] = {}
        
    async def add_provider(
        self,
        provider: LLMProvider,
        priority: int = 1,
        weight: float = 1.0,
        max_requests_per_minute: int = 60,
        max_cost_per_request: float = 0.10,
        enabled: bool = True,
        fallback_order: int = 0
    ) -> None:
        """
        Add a provider to the router.
        
        Args:
            provider: LLM provider instance
            priority: Provider priority (higher = more preferred)
            weight: Weight for load balancing
            max_requests_per_minute: Rate limit
            max_cost_per_request: Cost limit
            enabled: Whether provider is enabled
            fallback_order: Fallback order (0 = primary)
        """
        await provider.initialize()
        
        config = ProviderConfig(
            provider=provider,
            priority=priority,
            weight=weight,
            max_requests_per_minute=max_requests_per_minute,
            max_cost_per_request=max_cost_per_request,
            enabled=enabled,
            fallback_order=fallback_order
        )
        
        self.providers[provider.provider_name] = config
        self._request_counts[provider.provider_name] = []
        self._latency_history[provider.provider_name] = []
        self._error_counts[provider.provider_name] = 0
        self._circuit_breakers[provider.provider_name] = False
        
        logger.info(f"Added provider: {provider.provider_name}")
    
    async def route_request(
        self,
        messages: List[Message],
        config: ModelConfig,
        policy: Optional[RoutingPolicy] = None
    ) -> ModelResponse:
        """
        Route a request to the best available provider.
        
        Args:
            messages: Conversation messages
            config: Model configuration
            policy: Routing policy (uses default if None)
            
        Returns:
            ModelResponse from the selected provider
        """
        policy = policy or self.default_policy
        
        # Get eligible providers
        eligible_providers = await self._get_eligible_providers(
            messages, config, policy
        )
        
        if not eligible_providers:
            raise ProviderError("No eligible providers available", "router")
        
        # Try providers in order with fallback
        last_error = None
        
        for attempt in range(policy.retry_attempts):
            for provider_name in eligible_providers:
                if self._circuit_breakers.get(provider_name, False):
                    continue
                
                try:
                    provider_config = self.providers[provider_name]
                    
                    # Check rate limits
                    if not self._check_rate_limit(provider_name):
                        logger.warning(f"Rate limit exceeded for {provider_name}")
                        continue
                    
                    # Make request
                    start_time = time.time()
                    response = await provider_config.provider.generate_response(
                        messages, config
                    )
                    end_time = time.time()
                    
                    # Record metrics
                    self._record_request(provider_name, end_time - start_time)
                    
                    logger.info(f"Request routed to {provider_name}")
                    return response
                    
                except RateLimitError as e:
                    logger.warning(f"Rate limit hit for {provider_name}: {e}")
                    last_error = e
                    continue
                    
                except ProviderError as e:
                    logger.error(f"Provider error for {provider_name}: {e}")
                    self._record_error(provider_name)
                    last_error = e
                    
                    # Circuit breaker logic
                    if self._error_counts[provider_name] > 5:
                        self._circuit_breakers[provider_name] = True
                        logger.warning(f"Circuit breaker activated for {provider_name}")
                    
                    continue
            
            # Wait before retry
            if attempt < policy.retry_attempts - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # All providers failed
        if last_error:
            raise last_error
        else:
            raise ProviderError("All providers failed", "router")
    
    async def _get_eligible_providers(
        self,
        messages: List[Message],
        config: ModelConfig,
        policy: RoutingPolicy
    ) -> List[str]:
        """Get list of eligible providers based on policy."""
        eligible = []
        
        for name, provider_config in self.providers.items():
            if not provider_config.enabled:
                continue
            
            provider = provider_config.provider
            
            # Check capabilities
            if policy.required_capabilities:
                if not all(provider.supports_capability(cap) 
                          for cap in policy.required_capabilities):
                    continue
            
            # Check model availability
            if config.model_name not in provider.available_models:
                continue
            
            # Check cost threshold
            estimated_cost = provider.estimate_cost(messages, config)
            if estimated_cost > policy.max_cost_threshold:
                continue
            
            # Check provider-specific cost limit
            if estimated_cost > provider_config.max_cost_per_request:
                continue
            
            eligible.append(name)
        
        # Sort by routing strategy
        return self._sort_providers(eligible, policy)
    
    def _sort_providers(
        self,
        provider_names: List[str],
        policy: RoutingPolicy
    ) -> List[str]:
        """Sort providers based on routing strategy."""
        if policy.strategy == RoutingStrategy.COST_OPTIMIZED:
            # Sort by estimated cost (ascending)
            return sorted(provider_names, key=lambda name: 
                         self.providers[name].provider.estimate_cost([], ModelConfig("grok-3-mini")))
        
        elif policy.strategy == RoutingStrategy.LATENCY_OPTIMIZED:
            # Sort by average latency (ascending)
            return sorted(provider_names, key=lambda name: 
                         self._get_average_latency(name))
        
        elif policy.strategy == RoutingStrategy.CAPABILITY_BASED:
            # Sort by number of capabilities (descending)
            return sorted(provider_names, 
                         key=lambda name: len(self.providers[name].provider.supported_capabilities),
                         reverse=True)
        
        elif policy.strategy == RoutingStrategy.ROUND_ROBIN:
            # Simple round-robin (could be improved with state)
            return provider_names
        
        elif policy.strategy == RoutingStrategy.FAILOVER:
            # Sort by fallback order
            return sorted(provider_names, 
                         key=lambda name: self.providers[name].fallback_order)
        
        elif policy.strategy == RoutingStrategy.LOAD_BALANCED:
            # Weighted random selection
            return self._weighted_shuffle(provider_names)
        
        else:
            # Default: sort by priority
            return sorted(provider_names, 
                         key=lambda name: self.providers[name].priority,
                         reverse=True)
    
    def _weighted_shuffle(self, provider_names: List[str]) -> List[str]:
        """Shuffle providers based on their weights."""
        weighted_providers = []
        for name in provider_names:
            weight = self.providers[name].weight
            weighted_providers.extend([name] * int(weight * 10))
        
        random.shuffle(weighted_providers)
        
        # Remove duplicates while preserving order
        result = []
        seen = set()
        for name in weighted_providers:
            if name not in seen:
                result.append(name)
                seen.add(name)
        
        return result
    
    def _check_rate_limit(self, provider_name: str) -> bool:
        """Check if provider is within rate limits."""
        now = time.time()
        requests = self._request_counts[provider_name]
        
        # Remove requests older than 1 minute
        cutoff = now - 60
        self._request_counts[provider_name] = [
            req_time for req_time in requests if req_time > cutoff
        ]
        
        # Check limit
        max_requests = self.providers[provider_name].max_requests_per_minute
        return len(self._request_counts[provider_name]) < max_requests
    
    def _record_request(self, provider_name: str, latency: float) -> None:
        """Record a successful request."""
        now = time.time()
        self._request_counts[provider_name].append(now)
        self._latency_history[provider_name].append(latency)
        
        # Keep only recent latency data
        if len(self._latency_history[provider_name]) > 100:
            self._latency_history[provider_name] = self._latency_history[provider_name][-50:]
        
        # Reset error count on success
        self._error_counts[provider_name] = 0
        self._circuit_breakers[provider_name] = False
    
    def _record_error(self, provider_name: str) -> None:
        """Record an error for a provider."""
        self._error_counts[provider_name] += 1
    
    def _get_average_latency(self, provider_name: str) -> float:
        """Get average latency for a provider."""
        latencies = self._latency_history.get(provider_name, [])
        if not latencies:
            return float('inf')  # Unknown latency = lowest priority
        return sum(latencies) / len(latencies)
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        status = {}
        
        for name, config in self.providers.items():
            provider_status = await config.provider.health_check()
            
            status[name] = {
                **provider_status,
                "enabled": config.enabled,
                "priority": config.priority,
                "weight": config.weight,
                "circuit_breaker": self._circuit_breakers.get(name, False),
                "error_count": self._error_counts.get(name, 0),
                "average_latency": self._get_average_latency(name),
                "recent_requests": len(self._request_counts.get(name, []))
            }
        
        return status
    
    async def reset_circuit_breakers(self) -> None:
        """Reset all circuit breakers."""
        for name in self._circuit_breakers:
            self._circuit_breakers[name] = False
            self._error_counts[name] = 0
        
        logger.info("All circuit breakers reset")


# Factory function for easy setup
async def create_default_router() -> ModelRouter:
    """Create a router with default GROK provider."""
    router = ModelRouter()
    
    # Add GROK provider as primary
    grok_provider = GROKProvider()
    await router.add_provider(
        grok_provider,
        priority=10,
        weight=1.0,
        max_requests_per_minute=60,
        max_cost_per_request=0.10,
        enabled=True,
        fallback_order=0
    )
    
    return router


# Environment-based setup utilities
def _policy_from_env() -> RoutingPolicy:
    """Build a RoutingPolicy from environment variables.

    Env vars:
    - AI_ROUTING_STRATEGY: one of cost_optimized, latency_optimized, capability_based, round_robin, failover, load_balanced
    - AI_MAX_COST_THRESHOLD: float (USD)
    - AI_MAX_LATENCY_MS: int/float milliseconds; converted to seconds internally
    - AI_RETRY_ATTEMPTS: int
    """
    strategy_str = os.environ.get("AI_ROUTING_STRATEGY", RoutingStrategy.COST_OPTIMIZED.value)
    # Normalize case and map to enum if possible
    strategy_map = {s.value.lower(): s for s in RoutingStrategy}
    strategy = strategy_map.get(strategy_str.lower(), RoutingStrategy.COST_OPTIMIZED)

    max_cost = float(os.environ.get("AI_MAX_COST_THRESHOLD", "0.05"))
    max_latency_ms = float(os.environ.get("AI_MAX_LATENCY_MS", "10000"))
    retry_attempts = int(os.environ.get("AI_RETRY_ATTEMPTS", "3"))

    return RoutingPolicy(
        strategy=strategy,
        max_cost_threshold=max_cost,
        max_latency_threshold=max_latency_ms / 1000.0,
        retry_attempts=retry_attempts,
    )


async def create_router_from_env() -> ModelRouter:
    """Create a ModelRouter based on environment configuration.

    Uses ProviderConfigManager to instantiate available providers in ascending
    priority (lower number means higher priority). Fallback order is derived
    from that order. Default routing policy is derived from env via _policy_from_env().
    """
    policy = _policy_from_env()
    router = ModelRouter(default_policy=policy)

    # Use a fresh instance to ensure current env is reflected (tests set env at runtime)
    pcm: ProviderConfigManager = ProviderConfigManager()

    # Get available providers in priority order
    available = pcm.get_available_providers()
    for idx, cred in enumerate(available):
        provider = pcm.create_provider(cred.provider_type)
        if not provider:
            continue
        # Use priority to hint at fallback order by list position
        await router.add_provider(
            provider,
            priority=max(1, 100 - cred.priority),  # invert so lower priority value => higher router priority
            weight=1.0,
            max_requests_per_minute=60,
            max_cost_per_request=0.10,
            enabled=True,
            fallback_order=idx,
        )

    return router
