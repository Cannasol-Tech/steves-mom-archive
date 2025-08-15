"""
Unit tests for rate limiting and backoff mechanisms.

Tests cover:
- Token bucket rate limiting algorithm
- Exponential backoff with jitter for retries
- Circuit breaker pattern for provider failures
- Error normalization across different providers

Author: Cannasol Technologies
Date: 2025-08-15
Version: 1.0.0
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.ai.rate_limiter import (
    TokenBucket,
    ExponentialBackoff,
    CircuitBreaker,
    ErrorNormalizer,
    RateLimiter
)
from backend.ai.providers.base_provider import (
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderType
)


class TestTokenBucket:
    """Test token bucket rate limiting algorithm."""
    
    @pytest.mark.asyncio
    async def test_token_bucket_initialization(self):
        """Test token bucket initializes with correct capacity and refill rate."""
        bucket = TokenBucket(capacity=10, refill_rate=2.0)
        
        assert bucket.capacity == 10
        assert bucket.refill_rate == 2.0
        assert bucket.tokens == 10  # Starts full
        assert bucket.last_refill is not None
    
    @pytest.mark.asyncio
    async def test_token_bucket_consume_tokens(self):
        """Test consuming tokens from bucket with controlled time."""
        with patch('time.time') as mock_time:
            # Initialize bucket at time 0
            mock_time.return_value = 0.0
            bucket = TokenBucket(capacity=10, refill_rate=2.0)
            assert bucket.tokens == 10

            # Consume 3 tokens at the same time
            assert await bucket.consume(3) is True
            assert bucket.tokens == 7

            # Consume 7 more tokens at the same time
            assert await bucket.consume(7) is True
            assert bucket.tokens == 0

            # Try to consume 1 more token, should fail
            assert await bucket.consume(1) is False
            assert bucket.tokens == 0
    
    @pytest.mark.asyncio
    async def test_token_bucket_refill(self):
        """Test token bucket refills over time."""
        bucket = TokenBucket(capacity=10, refill_rate=5.0)  # 5 tokens per second
        
        # Consume all tokens
        await bucket.consume(10)
        assert bucket.tokens == 0
        
        # Wait for refill (0.4 seconds = 2 tokens at 5/sec)
        await asyncio.sleep(0.4)
        bucket._refill()
        
        # Should have approximately 2 tokens (allowing for timing variance)
        assert 1 <= bucket.tokens <= 3
    
    @pytest.mark.asyncio
    async def test_token_bucket_max_capacity(self):
        """Test token bucket doesn't exceed capacity during refill."""
        bucket = TokenBucket(capacity=5, refill_rate=10.0)
        
        # Wait longer than needed to fill bucket
        await asyncio.sleep(1.0)
        bucket._refill()
        
        # Should not exceed capacity
        assert bucket.tokens <= 5


class TestExponentialBackoff:
    """Test exponential backoff with jitter."""
    
    def test_exponential_backoff_initialization(self):
        """Test backoff initializes with correct parameters."""
        backoff = ExponentialBackoff(
            base_delay=1.0,
            max_delay=30.0,
            multiplier=2.0,
            jitter=True
        )
        
        assert backoff.base_delay == 1.0
        assert backoff.max_delay == 30.0
        assert backoff.multiplier == 2.0
        assert backoff.jitter is True
    
    def test_exponential_backoff_delay_calculation(self):
        """Test delay calculation follows exponential pattern."""
        backoff = ExponentialBackoff(
            base_delay=1.0,
            max_delay=30.0,
            multiplier=2.0,
            jitter=False  # No jitter for predictable testing
        )
        
        # Test exponential progression
        assert backoff.calculate_delay(0) == 1.0
        assert backoff.calculate_delay(1) == 2.0
        assert backoff.calculate_delay(2) == 4.0
        assert backoff.calculate_delay(3) == 8.0
        assert backoff.calculate_delay(4) == 16.0
        assert backoff.calculate_delay(5) == 30.0  # Capped at max_delay
    
    def test_exponential_backoff_with_jitter(self):
        """Test jitter adds randomness to delay."""
        backoff = ExponentialBackoff(
            base_delay=1.0,
            max_delay=30.0,
            multiplier=2.0,
            jitter=True
        )
        
        # With jitter, delay should vary
        delays = [backoff.calculate_delay(2) for _ in range(10)]
        
        # All delays should be different (very high probability)
        assert len(set(delays)) > 1
        
        # All delays should be within reasonable bounds (0.5x to 1.5x base)
        for delay in delays:
            assert 2.0 <= delay <= 6.0  # 4.0 * (0.5 to 1.5)
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_wait(self):
        """Test async wait functionality."""
        backoff = ExponentialBackoff(
            base_delay=0.1,  # Short delay for testing
            max_delay=1.0,
            multiplier=2.0,
            jitter=False
        )
        
        start_time = time.time()
        await backoff.wait(1)  # Should wait ~0.2 seconds
        elapsed = time.time() - start_time
        
        # Allow some tolerance for timing
        assert 0.15 <= elapsed <= 0.25


class TestCircuitBreaker:
    """Test circuit breaker pattern."""
    
    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initializes in closed state."""
        breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60.0,
            expected_exception=Exception
        )
        
        assert breaker.failure_count == 0
        assert breaker.state == "closed"
        assert breaker.last_failure_time is None
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker allows calls in closed state."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)
        
        # Mock successful function
        mock_func = AsyncMock(return_value="success")
        
        result = await breaker.call(mock_func)
        assert result == "success"
        assert breaker.state == "closed"
        assert breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_counting(self):
        """Test circuit breaker counts failures correctly."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)
        
        # Mock failing function
        mock_func = AsyncMock(side_effect=Exception("test error"))
        
        # First two failures should be allowed through
        for i in range(2):
            with pytest.raises(Exception):
                await breaker.call(mock_func)
            assert breaker.failure_count == i + 1
            assert breaker.state == "closed"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after failure threshold."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60.0)
        
        # Mock failing function
        mock_func = AsyncMock(side_effect=Exception("test error"))
        
        # Trigger failures to reach threshold
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(mock_func)
        
        # Circuit should now be open
        assert breaker.state == "open"
        
        # Next call should be rejected immediately
        with pytest.raises(Exception, match="Circuit breaker is open"):
            await breaker.call(mock_func)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker transitions to half-open for recovery."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        # Mock failing function
        mock_func = AsyncMock(side_effect=Exception("test error"))
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(mock_func)
        
        assert breaker.state == "open"
        
        # Wait for recovery timeout
        await asyncio.sleep(0.15)
        
        # Mock successful function for recovery
        mock_func.side_effect = None
        mock_func.return_value = "recovered"
        
        # Should transition to half-open and allow one call
        result = await breaker.call(mock_func)
        assert result == "recovered"
        assert breaker.state == "closed"  # Should close after successful call
        assert breaker.failure_count == 0


class TestErrorNormalizer:
    """Test error normalization across providers."""
    
    def test_error_normalizer_initialization(self):
        """Test error normalizer initializes correctly."""
        normalizer = ErrorNormalizer()
        assert normalizer is not None
    
    def test_normalize_rate_limit_errors(self):
        """Test normalization of rate limit errors."""
        normalizer = ErrorNormalizer()
        
        # Test different provider rate limit errors
        grok_error = Exception("Rate limit exceeded")
        openai_error = Exception("Rate limit reached for requests")
        claude_error = Exception("Too many requests")
        
        # Should normalize to ProviderRateLimitError
        normalized = normalizer.normalize_error(grok_error, ProviderType.GROK)
        assert isinstance(normalized, ProviderRateLimitError)
        assert normalized.provider_type == ProviderType.GROK
        
        normalized = normalizer.normalize_error(openai_error, ProviderType.OPENAI)
        assert isinstance(normalized, ProviderRateLimitError)
        
        normalized = normalizer.normalize_error(claude_error, ProviderType.CLAUDE)
        assert isinstance(normalized, ProviderRateLimitError)
    
    def test_normalize_timeout_errors(self):
        """Test normalization of timeout errors."""
        normalizer = ErrorNormalizer()
        
        timeout_errors = [
            Exception("Request timeout"),
            Exception("Connection timeout"),
            Exception("Read timeout"),
            TimeoutError("Operation timed out")
        ]
        
        for error in timeout_errors:
            normalized = normalizer.normalize_error(error, ProviderType.GROK)
            assert isinstance(normalized, ProviderTimeoutError)
            assert normalized.provider_type == ProviderType.GROK
    
    def test_normalize_unavailable_errors(self):
        """Test normalization of service unavailable errors."""
        normalizer = ErrorNormalizer()
        
        unavailable_errors = [
            Exception("Service unavailable"),
            Exception("Server error"),
            Exception("Internal server error"),
            Exception("Bad gateway")
        ]
        
        for error in unavailable_errors:
            normalized = normalizer.normalize_error(error, ProviderType.OPENAI)
            assert isinstance(normalized, ProviderUnavailableError)
            assert normalized.provider_type == ProviderType.OPENAI
    
    def test_normalize_unknown_errors(self):
        """Test normalization of unknown errors."""
        normalizer = ErrorNormalizer()
        
        unknown_error = Exception("Some unknown error")
        normalized = normalizer.normalize_error(unknown_error, ProviderType.CLAUDE)
        
        # Should wrap in generic ProviderError
        assert isinstance(normalized, ProviderError)
        assert normalized.provider_type == ProviderType.CLAUDE
        assert "Some unknown error" in str(normalized)


class TestRateLimiter:
    """Test integrated rate limiter with all components."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test rate limiter initializes with all components."""
        limiter = RateLimiter(
            requests_per_second=10,
            burst_capacity=20,
            max_retries=3,
            base_delay=1.0
        )
        
        assert limiter.token_bucket.capacity == 20
        assert limiter.token_bucket.refill_rate == 10.0
        assert limiter.backoff.base_delay == 1.0
        assert limiter.circuit_breaker.failure_threshold == 5  # Default
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_within_limit(self):
        """Test rate limiter allows requests within rate limit."""
        limiter = RateLimiter(requests_per_second=10, burst_capacity=10)
        
        # Mock successful function
        mock_func = AsyncMock(return_value="success")
        
        # Should allow multiple requests within burst capacity
        for _ in range(5):
            result = await limiter.execute(mock_func)
            assert result == "success"
    
    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_requests_over_limit(self):
        """Test rate limiter blocks requests over rate limit."""
        limiter = RateLimiter(requests_per_second=1, burst_capacity=2)
        
        # Mock successful function
        mock_func = AsyncMock(return_value="success")
        
        # First two requests should succeed
        await limiter.execute(mock_func)
        await limiter.execute(mock_func)
        
        # Third request should be rate limited
        with pytest.raises(ProviderRateLimitError):
            await limiter.execute(mock_func)
    
    @pytest.mark.asyncio
    async def test_rate_limiter_retries_with_backoff(self):
        """Test rate limiter retries failed requests with backoff."""
        limiter = RateLimiter(
            requests_per_second=10,
            burst_capacity=10,
            max_retries=2,
            base_delay=0.1
        )
        
        # Mock function that fails twice then succeeds
        call_count = 0
        async def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Temporary failure")
            return "success"
        
        # Should retry and eventually succeed
        result = await limiter.execute(mock_func)
        assert result == "success"
        assert call_count == 3  # Initial call + 2 retries
    
    @pytest.mark.asyncio
    async def test_rate_limiter_circuit_breaker_integration(self):
        """Test rate limiter integrates with circuit breaker."""
        limiter = RateLimiter(
            requests_per_second=10,
            burst_capacity=10,
            circuit_breaker_threshold=2,
            circuit_breaker_timeout=0.1
        )
        
        # Mock function that always fails
        mock_func = AsyncMock(side_effect=Exception("Always fails"))
        
        # Should fail twice and open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await limiter.execute(mock_func, provider_type=ProviderType.LOCAL)
        
        # Circuit should now be open
        assert limiter.circuit_breaker.state == "open"
        
        # Next call should be rejected by circuit breaker and normalized
        with pytest.raises(ProviderUnavailableError, match="Circuit breaker is open"):
            await limiter.execute(mock_func, provider_type=ProviderType.LOCAL)
