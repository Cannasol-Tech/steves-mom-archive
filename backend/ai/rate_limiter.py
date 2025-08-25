"""
Rate limiting and backoff mechanisms for AI providers.

This module implements:
- Token bucket rate limiting algorithm
- Exponential backoff with jitter for retries
- Circuit breaker pattern for provider failures
- Error normalization across different providers

Author: Cannasol Technologies
Date: 2025-08-15
Version: 1.0.0
"""

import asyncio
import random
import re
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional

from .providers.base_provider import (ProviderError, ProviderRateLimitError,
                                      ProviderTimeoutError, ProviderType,
                                      ProviderUnavailableError)


class TokenBucket:
    """
    Token bucket rate limiting algorithm.

    Allows burst traffic up to capacity, then limits to refill rate.
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum number of tokens in bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)  # Start with full bucket
        self.last_refill = time.time()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill

        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            bool: True if tokens were consumed, False if not available
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False


class ExponentialBackoff:
    """
    Exponential backoff with jitter for retries.

    Implements exponential backoff with optional jitter to avoid thundering herd.
    """

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter: bool = True,
    ):
        """
        Initialize exponential backoff.

        Args:
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            multiplier: Backoff multiplier
            jitter: Whether to add random jitter
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number.

        Args:
            attempt: Retry attempt number (0-based)

        Returns:
            Delay in seconds
        """
        delay = self.base_delay * (self.multiplier**attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add jitter: random factor between 0.5 and 1.5
            jitter_factor = 0.5 + random.random()
            delay *= jitter_factor

        return delay

    async def wait(self, attempt: int) -> None:
        """
        Wait for calculated delay.

        Args:
            attempt: Retry attempt number
        """
        delay = self.calculate_delay(attempt)
        await asyncio.sleep(delay)


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Circuit breaker pattern for provider failures.

    Prevents cascading failures by temporarily blocking calls to failing services.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery
            expected_exception: Exception type that counts as failure
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitBreakerState.CLOSED

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset to half-open."""
        if self.state != CircuitBreakerState.OPEN:
            return False

        if self.last_failure_time is None:
            return False

        return time.time() - self.last_failure_time >= self.recovery_timeout

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        # Check if we should attempt reset
        if self._should_attempt_reset():
            self.state = CircuitBreakerState.HALF_OPEN

        # Reject calls if circuit is open
        if self.state == CircuitBreakerState.OPEN:
            raise Exception("Circuit breaker is open")

        try:
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success - reset failure count and close circuit
            self.failure_count = 0
            self.state = CircuitBreakerState.CLOSED
            return result

        except self.expected_exception as e:
            # Failure - increment count and potentially open circuit
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
            else:
                self.state = CircuitBreakerState.CLOSED

            raise e


class ErrorNormalizer:
    """
    Error normalization across different providers.

    Converts provider-specific errors to standardized error types.
    """

    def __init__(self):
        """Initialize error normalizer with pattern mappings."""
        self.rate_limit_patterns = [
            r"rate limit",
            r"too many requests",
            r"quota exceeded",
            r"throttled",
            r"429",
        ]

        self.timeout_patterns = [
            r"timeout",
            r"timed out",
            r"connection timeout",
            r"read timeout",
        ]

        self.unavailable_patterns = [
            r"service unavailable",
            r"server error",
            r"internal server error",
            r"bad gateway",
            r"circuit breaker is open",
            r"502",
            r"503",
            r"504",
        ]

    def _matches_patterns(self, error_message: str, patterns: list) -> bool:
        """Check if error message matches any pattern."""
        error_lower = error_message.lower()
        return any(re.search(pattern, error_lower) for pattern in patterns)

    def normalize_error(
        self, error: Exception, provider_type: ProviderType
    ) -> ProviderError:
        """
        Normalize error to standard provider error type.

        Args:
            error: Original exception
            provider_type: Provider that generated the error

        Returns:
            Normalized provider error
        """
        error_message = str(error)

        # Check for rate limit errors
        if self._matches_patterns(error_message, self.rate_limit_patterns):
            return ProviderRateLimitError(
                message=error_message,
                provider_type=provider_type,
                error_code="RATE_LIMIT",
            )

        # Check for timeout errors
        if isinstance(error, TimeoutError) or self._matches_patterns(
            error_message, self.timeout_patterns
        ):
            return ProviderTimeoutError(
                message=error_message, provider_type=provider_type, error_code="TIMEOUT"
            )

        # Check for service unavailable errors
        if self._matches_patterns(error_message, self.unavailable_patterns):
            return ProviderUnavailableError(
                message=error_message,
                provider_type=provider_type,
                error_code="UNAVAILABLE",
            )

        # Default to generic provider error
        return ProviderError(
            message=error_message, provider_type=provider_type, error_code="UNKNOWN"
        )


class RateLimiter:
    """
    Integrated rate limiter with all components.

    Combines token bucket, exponential backoff, circuit breaker, and error normalization.
    """

    def __init__(
        self,
        requests_per_second: float = 10.0,
        burst_capacity: Optional[int] = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: float = 60.0,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Rate limit (requests per second)
            burst_capacity: Burst capacity (defaults to 2x rate)
            max_retries: Maximum retry attempts
            base_delay: Base delay for exponential backoff
            max_delay: Maximum delay for exponential backoff
            circuit_breaker_threshold: Failures before opening circuit
            circuit_breaker_timeout: Circuit breaker recovery timeout
        """
        if burst_capacity is None:
            burst_capacity = int(requests_per_second * 2)

        self.max_retries = max_retries

        # Initialize components
        self.token_bucket = TokenBucket(
            capacity=burst_capacity, refill_rate=requests_per_second
        )

        self.backoff = ExponentialBackoff(
            base_delay=base_delay, max_delay=max_delay, multiplier=2.0, jitter=True
        )

        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_threshold,
            recovery_timeout=circuit_breaker_timeout,
            expected_exception=Exception,
        )

        self.error_normalizer = ErrorNormalizer()

    async def execute(
        self,
        func: Callable,
        provider_type: Optional[ProviderType] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with rate limiting, retries, and circuit breaking.

        Args:
            func: Function to execute
            provider_type: Provider type for error normalization
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            ProviderError: Normalized provider error
        """
        # Check rate limit
        if not await self.token_bucket.consume():
            raise ProviderRateLimitError(
                message="Rate limit exceeded",
                provider_type=provider_type or ProviderType.LOCAL,
                error_code="RATE_LIMIT",
            )

        # Execute with circuit breaker and retries
        for attempt in range(self.max_retries + 1):
            try:
                return await self.circuit_breaker.call(func, *args, **kwargs)

            except Exception as e:
                # Normalize error
                if provider_type:
                    normalized_error = self.error_normalizer.normalize_error(
                        e, provider_type
                    )
                else:
                    normalized_error = e

                # If the error is a non-retriable ProviderError, raise it immediately.
                if (
                    isinstance(normalized_error, ProviderError)
                    and not normalized_error.retriable
                ):
                    raise normalized_error

                # Don't retry on last attempt
                if attempt == self.max_retries:
                    raise normalized_error

                # Wait before retry
                await self.backoff.wait(attempt)

        # Should not reach here
        raise ProviderError(
            message="Maximum retries exceeded",
            provider_type=provider_type or ProviderType.LOCAL,
            error_code="MAX_RETRIES",
        )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get rate limiter statistics.

        Returns:
            Dictionary with current stats
        """
        return {
            "tokens_available": self.token_bucket.tokens,
            "tokens_capacity": self.token_bucket.capacity,
            "refill_rate": self.token_bucket.refill_rate,
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "circuit_breaker_failures": self.circuit_breaker.failure_count,
            "max_retries": self.max_retries,
        }
