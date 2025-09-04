"""
Model Router for Steve's Mom AI Chatbot

This module implements intelligent routing between different AI providers
based on cost, latency, capability, and availability policies.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

import asyncio
import logging
import os
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, TypedDict, Protocol, Awaitable

from .providers.base import (LLMProvider, Message, ModelCapability,
                             ModelConfig, ModelResponse, ProviderError,
                             RateLimitError)
from .providers.config_manager import ProviderConfigManager, config_manager
from .providers.grok_provider import GROKProvider

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
    required_capabilities: List[ModelCapability] = field(default_factory=list)
    preferred_providers: List[str] = field(default_factory=list)
    fallback_enabled: bool = True
    retry_attempts: int = 3

    def __post_init__(self) -> None:
        # Defaults handled by dataclass field default_factory; nothing to do
        pass


class ModelRouter:
    """
    Intelligent router for AI model providers.

    Routes requests to the most appropriate provider based on cost, latency,
    capabilities, and availability. Supports multiple routing strategies such
    as cost-optimized, latency-optimized, capability-based, round-robin,
    failover, and weighted load balancing. Implements basic rate limiting and
    circuit breaker behavior per provider.

    Responsibilities:
    - Maintain a registry of provider configurations and runtime metrics
    - Determine eligible providers for a given request and policy
    - Select and invoke providers according to routing strategy
    - Track request counts, latency history, and error counts
    - Expose provider status snapshots for observability
    """
    async def stream_request(
        self,
        messages: List[Message],
        config: ModelConfig,
        policy: Optional[RoutingPolicy] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Route a streaming request to the best available provider.

        Args:
            messages: Conversation messages
            config: Model configuration
            policy: Routing policy (uses default if None)

        Yields:
            Chunks of the response from the selected provider
        """
        policy = policy or self.default_policy
        config.stream = True  # Ensure stream is enabled

        eligible_providers = await self._get_eligible_providers(
            messages, config, policy
        )

        if not eligible_providers:
            raise ProviderError("No eligible providers available for streaming", "router")

        last_error: Optional[Exception] = None

        for attempt in range(policy.retry_attempts):
            for provider_name in eligible_providers:
                if self._circuit_breakers.get(provider_name, False):
                    continue

                try:
                    provider_config = self.providers[provider_name]

                    if not self._check_rate_limit(provider_name):
                        logger.warning(f"Rate limit exceeded for {provider_name}")
                        continue

                    start_time = time.time()
                    async for chunk in provider_config.provider.stream_response(
                        messages, config
                    ):
                        yield chunk
                    end_time = time.time()

                    self._record_request(provider_name, end_time - start_time)
                    logger.info(f"Request streamed via {provider_name}")
                    return  # End generation

                except (ProviderError, Exception) as e:
                    logger.error(f"Provider streaming error for {provider_name}: {e}")
                    self._record_error(provider_name)
                    last_error = e
                    continue

            if attempt < policy.retry_attempts - 1:
                await asyncio.sleep(2**attempt)  # Exponential backoff

        if last_error:
            raise last_error
        else:
            raise ProviderError("All providers failed to stream", "router")

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
        fallback_order: int = 0,
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
            fallback_order=fallback_order,
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
        policy: Optional[RoutingPolicy] = None,
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
        last_error: Optional[Exception] = None

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

                except (ProviderError, Exception) as e:
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
                await asyncio.sleep(2**attempt)  # Exponential backoff

        # All providers failed
        if last_error:
            raise last_error
        else:
            raise ProviderError("All providers failed", "router")

    async def _get_eligible_providers(
        self, messages: List[Message], config: ModelConfig, policy: RoutingPolicy
    ) -> List[str]:
        """Get list of eligible providers based on policy."""
        eligible = []
        # Pre-compute cost map to handle providers where estimate_cost may be async (e.g., AsyncMock)
        cost_map: Dict[str, float] = {}

        for name, provider_config in self.providers.items():
            if not provider_config.enabled:
                continue

            provider = provider_config.provider

            # Check capabilities
            if policy.required_capabilities:
                if not all(
                    provider.supports_capability(cap)
                    for cap in policy.required_capabilities
                ):
                    continue

            # Check model availability
            if config.model_name not in provider.available_models:
                continue

            # Check cost threshold (support both sync and async estimate_cost)
            estimated_cost_val = provider.estimate_cost(messages, config)
            if asyncio.iscoroutine(estimated_cost_val):
                estimated_cost = await estimated_cost_val
            else:
                estimated_cost = estimated_cost_val

            # Cache for later sorting
            cost_map[name] = float(estimated_cost)

            if estimated_cost > policy.max_cost_threshold:
                continue

            # Check provider-specific cost limit
            if estimated_cost > provider_config.max_cost_per_request:
                continue

            eligible.append(name)

        # Sort by routing strategy
        return self._sort_providers(eligible, policy, messages, config, cost_map)

    def _sort_providers(
        self,
        provider_names: List[str],
        policy: RoutingPolicy,
        messages: List[Message],
        config: ModelConfig,
        cost_map: Optional[Dict[str, float]] = None,
    ) -> List[str]:
        """Sort providers based on routing strategy."""
        if policy.strategy == RoutingStrategy.COST_OPTIMIZED:
            # Sort by precomputed estimated cost (ascending) to avoid calling async in sort
            if cost_map is None:
                # Fallback: best-effort synchronous estimate (may not work with AsyncMock)
                return sorted(
                    provider_names,
                    key=lambda name: float(
                        self.providers[name].provider.estimate_cost(messages, config)
                    ),
                )
            return sorted(
                provider_names, key=lambda name: cost_map.get(name, float("inf"))
            )

        elif policy.strategy == RoutingStrategy.LATENCY_OPTIMIZED:
            # Sort by average latency (ascending)
            return sorted(
                provider_names, key=lambda name: self._get_average_latency(name)
            )

        elif policy.strategy == RoutingStrategy.CAPABILITY_BASED:
            # Sort by number of capabilities (descending)
            return sorted(
                provider_names,
                key=lambda name: len(
                    self.providers[name].provider.supported_capabilities
                ),
                reverse=True,
            )

        elif policy.strategy == RoutingStrategy.ROUND_ROBIN:
            # Simple round-robin (could be improved with state)
            return provider_names

        elif policy.strategy == RoutingStrategy.FAILOVER:
            # Sort by fallback order
            return sorted(
                provider_names, key=lambda name: self.providers[name].fallback_order
            )

        elif policy.strategy == RoutingStrategy.LOAD_BALANCED:
            # Weighted random selection
            return self._weighted_shuffle(provider_names)

        else:
            # Default: sort by priority
            return sorted(
                provider_names,
                key=lambda name: self.providers[name].priority,
                reverse=True,
            )

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
            self._latency_history[provider_name] = self._latency_history[provider_name][
                -50:
            ]

        # Reset error count on success
        self._error_counts[provider_name] = 0
        self._circuit_breakers[provider_name] = False

    def _record_error(self, provider_name: str) -> None:
        """Record an error for a provider."""
        self._error_counts[provider_name] += 1

        # Circuit breaker logic
        if self._error_counts[provider_name] > 5:
            self._circuit_breakers[provider_name] = True
            logger.warning(f"Circuit breaker activated for {provider_name}")

    def _get_average_latency(self, provider_name: str) -> float:
        """Get average latency for a provider."""
        latencies = self._latency_history.get(provider_name, [])
        if not latencies:
            return float("inf")  # Unknown latency = lowest priority
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
                "recent_requests": len(self._request_counts.get(name, [])),
            }

        return status

    async def reset_circuit_breakers(self) -> None:
        """Reset all circuit breakers."""
        for name in self._circuit_breakers:
            self._circuit_breakers[name] = False
            self._error_counts[name] = 0

        logger.info("All circuit breakers reset")

    def update_default_policy(self, policy: RoutingPolicy) -> None:
        """Update the default routing policy."""
        if not isinstance(policy.strategy, RoutingStrategy):
            raise ValueError(f"Invalid routing strategy: {policy.strategy}")

        self.default_policy = policy
        logger.info(f"Updated default policy: {policy.strategy.value}")

    def update_provider_config(
        self, provider_name: str, config_updates: Dict[str, Any]
    ) -> None:
        """Update configuration for a specific provider."""
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")

        provider_config = self.providers[provider_name]

        # Validate updates
        if "priority" in config_updates:
            if config_updates["priority"] <= 0:
                raise ValueError("Priority must be positive")
            provider_config.priority = config_updates["priority"]

        if "weight" in config_updates:
            if config_updates["weight"] <= 0:
                raise ValueError("Weight must be positive")
            provider_config.weight = config_updates["weight"]

        if "enabled" in config_updates:
            provider_config.enabled = bool(config_updates["enabled"])

        if "max_requests_per_minute" in config_updates:
            if config_updates["max_requests_per_minute"] <= 0:
                raise ValueError("Max requests per minute must be positive")
            provider_config.max_requests_per_minute = config_updates[
                "max_requests_per_minute"
            ]

        if "max_cost_per_request" in config_updates:
            if config_updates["max_cost_per_request"] <= 0:
                raise ValueError("Max cost per request must be positive")
            provider_config.max_cost_per_request = config_updates[
                "max_cost_per_request"
            ]

        if "fallback_order" in config_updates:
            if config_updates["fallback_order"] < 0:
                raise ValueError("Fallback order must be non-negative")
            provider_config.fallback_order = config_updates["fallback_order"]

        logger.info(f"Updated provider config for {provider_name}: {config_updates}")

    def enable_provider(self, provider_name: str) -> None:
        """Enable a provider."""
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")

        self.providers[provider_name].enabled = True
        logger.info(f"Enabled provider: {provider_name}")

    def disable_provider(self, provider_name: str) -> None:
        """Disable a provider."""
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")

        self.providers[provider_name].enabled = False
        logger.info(f"Disabled provider: {provider_name}")

    def get_configuration_snapshot(self) -> Dict[str, Any]:
        """Get complete configuration snapshot."""
        return {
            "default_policy": {
                "strategy": self.default_policy.strategy.value,
                "max_cost_threshold": self.default_policy.max_cost_threshold,
                "max_latency_threshold": self.default_policy.max_latency_threshold,
                "required_capabilities": [
                    cap.value for cap in self.default_policy.required_capabilities
                ],
                "preferred_providers": self.default_policy.preferred_providers,
                "fallback_enabled": self.default_policy.fallback_enabled,
                "retry_attempts": self.default_policy.retry_attempts,
            },
            "providers": {
                name: {
                    "priority": config.priority,
                    "weight": config.weight,
                    "max_requests_per_minute": config.max_requests_per_minute,
                    "max_cost_per_request": config.max_cost_per_request,
                    "enabled": config.enabled,
                    "fallback_order": config.fallback_order,
                }
                for name, config in self.providers.items()
            },
        }

    def load_configuration(self, config_dict: Dict[str, Any]) -> None:
        """Load configuration from dictionary."""
        # Update default policy
        if "default_policy" in config_dict:
            policy_config = config_dict["default_policy"]

            strategy = RoutingStrategy(policy_config.get("strategy", "cost_optimized"))
            required_capabilities = [
                ModelCapability(cap)
                for cap in policy_config.get("required_capabilities", [])
            ]

            new_policy = RoutingPolicy(
                strategy=strategy,
                max_cost_threshold=policy_config.get("max_cost_threshold", 0.05),
                max_latency_threshold=policy_config.get("max_latency_threshold", 10.0),
                required_capabilities=required_capabilities,
                preferred_providers=policy_config.get("preferred_providers", []),
                fallback_enabled=policy_config.get("fallback_enabled", True),
                retry_attempts=policy_config.get("retry_attempts", 3),
            )

            self.update_default_policy(new_policy)

        # Update provider configurations
        if "providers" in config_dict:
            for provider_name, provider_config in config_dict["providers"].items():
                if provider_name in self.providers:
                    self.update_provider_config(provider_name, provider_config)

        logger.info("Configuration loaded successfully")


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
        fallback_order=0,
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
    strategy_str = os.environ.get(
        "AI_ROUTING_STRATEGY", RoutingStrategy.COST_OPTIMIZED.value
    )
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
    # Late import via importlib so tests can patch
    import importlib

    _cfg_mod = importlib.import_module("backend.ai.providers.config_manager")
    pcm = _cfg_mod.ProviderConfigManager()

    # Get available providers in priority order
    available = pcm.get_available_providers()
    for idx, cred in enumerate(available):
        provider = pcm.create_provider(cred.provider_type)
        if not provider:
            continue
        # Use priority to hint at fallback order by list position
        await router.add_provider(
            provider,
            priority=max(
                1, 100 - cred.priority
            ),  # invert so lower priority value => higher router priority
            weight=1.0,
            max_requests_per_minute=60,
            max_cost_per_request=0.10,
            enabled=True,
            fallback_order=idx,
        )

    return router


# Typed configuration snapshot types (type-only documentation for static checkers)
class PolicySnapshot(TypedDict):
    strategy: str
    max_cost_threshold: float
    max_latency_threshold: float
    required_capabilities: List[str]
    preferred_providers: List[str]
    fallback_enabled: bool
    retry_attempts: int


class ProviderSnapshot(TypedDict):
    priority: int
    weight: float
    max_requests_per_minute: int
    max_cost_per_request: float
    enabled: bool
    fallback_order: int


class ConfigurationSnapshot(TypedDict):
    default_policy: PolicySnapshot
    providers: Dict[str, ProviderSnapshot]
