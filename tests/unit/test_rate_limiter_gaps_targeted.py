"""
Targeted tests to improve coverage for backend/ai/rate_limiter.py

Covers:
- Token bucket immediate denial path (rate limit exceeded pre-execution)
- Non-retriable ProviderError raised immediately without retries
- Last-attempt retry path raises normalized error
- Backoff wait is invoked expected number of times
- get_stats returns expected shape and values update
"""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from backend.ai.rate_limiter import RateLimiter, ExponentialBackoff, CircuitBreaker, TokenBucket
from backend.ai.providers.base_provider import (
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderType,
)


@pytest.mark.asyncio
async def test_token_bucket_denies_when_empty():
    # With burst_capacity=0, bucket starts empty and consume should fail immediately
    limiter = RateLimiter(requests_per_second=0.0, burst_capacity=0)

    async def ok():
        return "ok"

    with pytest.raises(ProviderRateLimitError):
        await limiter.execute(ok, provider_type=ProviderType.LOCAL)


@pytest.mark.asyncio
async def test_non_retriable_provider_error_raises_immediately():
    limiter = RateLimiter(requests_per_second=10, burst_capacity=1, max_retries=3)

    async def fail():
        # Simulate a non-retriable provider error
        raise ProviderError(message="bad", provider_type=ProviderType.GROK, error_code="X", retriable=False)

    with pytest.raises(ProviderError) as ei:
        await limiter.execute(fail, provider_type=ProviderType.GROK)
    assert ei.value.retriable is False


@pytest.mark.asyncio
async def test_last_attempt_raises_normalized_timeout():
    limiter = RateLimiter(requests_per_second=10, burst_capacity=1, max_retries=1, base_delay=0.01)

    async def always_timeout():
        raise Exception("Request timeout while connecting")

    with pytest.raises(ProviderTimeoutError):
        await limiter.execute(always_timeout, provider_type=ProviderType.GROK)


@pytest.mark.asyncio
async def test_backoff_wait_called_expected_times():
    # Set max_retries=2 so we expect 2 sleeps (after attempt 0 and 1)
    limiter = RateLimiter(requests_per_second=10, burst_capacity=2, max_retries=2, base_delay=0.01)

    async def always_fail():
        raise Exception("temporary failure")

    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        with pytest.raises(Exception):
            await limiter.execute(always_fail)  # provider_type None, original exception raised on last attempt
        # Expect exactly 2 waits for retries before the final raise
        assert mock_sleep.await_count == 2


@pytest.mark.asyncio
async def test_get_stats_reports_values_and_changes():
    limiter = RateLimiter(requests_per_second=5, burst_capacity=2)
    stats_before = limiter.get_stats()

    # Consume one token by executing a successful call
    async def ok():
        return "ok"

    result = await limiter.execute(ok)
    assert result == "ok"

    stats_after = limiter.get_stats()

    # Basic shape and some consistency checks
    for key in ("tokens_available", "tokens_capacity", "refill_rate", "circuit_breaker_state", "circuit_breaker_failures", "max_retries"):
        assert key in stats_after

    assert stats_before["tokens_capacity"] == 2
    assert stats_after["tokens_capacity"] == 2
    assert stats_after["circuit_breaker_state"] in ("closed", "open", "half_open")
    # tokens should not increase across a single immediate call; allow small floating variations
    assert stats_after["tokens_available"] <= stats_before["tokens_available"]


@pytest.mark.asyncio
async def test_exponential_backoff_wait_direct_no_jitter_monotonic_delay():
    """Directly exercise ExponentialBackoff.wait() without jitter and ensure asyncio.sleep is awaited with expected delay.

    Covers lines in ExponentialBackoff.wait and calculate_delay paths that were previously missed by integration-style tests.
    """
    backoff = ExponentialBackoff(base_delay=0.01, max_delay=1.0, multiplier=2.0, jitter=False)

    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        # attempt 0 -> delay = 0.01
        await backoff.wait(0)
        # attempt 2 -> delay = 0.04
        await backoff.wait(2)

        # Assert awaited with expected delays (called twice)
        assert mock_sleep.await_count == 2
        called_with = [call.args[0] for call in mock_sleep.await_args_list]
        assert called_with[0] == pytest.approx(0.01, rel=1e-3, abs=1e-6)
        assert called_with[1] == pytest.approx(0.04, rel=1e-3, abs=1e-6)


@pytest.mark.asyncio
async def test_exponential_backoff_wait_direct_with_jitter_calls_sleep():
    """Ensure ExponentialBackoff.wait() with jitter still awaits asyncio.sleep (delay value is random so we only assert it was called)."""
    backoff = ExponentialBackoff(base_delay=0.02, max_delay=1.0, multiplier=2.0, jitter=True)

    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        await backoff.wait(1)  # base 0.04, but jitter applies
        assert mock_sleep.await_count == 1
        # Ensure a reasonable delay range (0 < delay <= max_delay)
        delay_value = mock_sleep.await_args_list[0].args[0]
        assert 0 < delay_value <= 1.0


@pytest.mark.asyncio
async def test_retriable_provider_error_retries_then_succeeds():
    """When a retriable ProviderError is raised, RateLimiter should retry and eventually succeed."""
    limiter = RateLimiter(requests_per_second=10, burst_capacity=3, max_retries=2, base_delay=0.001)

    attempts = {"count": 0}

    async def sometimes_timeout():
        attempts["count"] += 1
        if attempts["count"] < 3:
            # Raise a retriable provider error twice, then succeed
            raise ProviderTimeoutError(message="timeout", provider_type=ProviderType.GROK, error_code="TIMEOUT", retriable=True)
        return "ok"

    # Patch sleep to avoid real delays and assert it was awaited for the two retries
    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        result = await limiter.execute(sometimes_timeout, provider_type=ProviderType.GROK)
        assert result == "ok"
        assert attempts["count"] == 3
        # Two retries -> two sleeps
        assert mock_sleep.await_count == 2


@pytest.mark.asyncio
async def test_circuit_breaker_sync_function_paths_and_half_open():
    """Cover CircuitBreaker.call() sync path and half-open recovery transition."""
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05, expected_exception=Exception)

    # Define synchronous functions to hit non-async branch
    def fail_sync():
        raise Exception("sync fail")

    def ok_sync():
        return "ok"

    # Trigger two failures to open circuit
    for _ in range(2):
        with pytest.raises(Exception):
            await breaker.call(fail_sync)

    assert breaker.state == "open"

    # Not enough time yet -> still open and should raise immediately if called again
    with pytest.raises(Exception, match="Circuit breaker is open"):
        await breaker.call(ok_sync)

    # Wait for recovery timeout, then next call should transition to half-open and allow
    await asyncio.sleep(0.06)
    res = await breaker.call(ok_sync)
    assert res == "ok"
    assert breaker.state == "closed"


@pytest.mark.asyncio
async def test_circuit_breaker_open_no_reset_then_attempt_reset_paths():
    """Cover _should_attempt_reset branches when OPEN with/without last_failure_time and before timeout."""
    from backend.ai.rate_limiter import CircuitBreaker

    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.2, expected_exception=Exception)

    # Force open state by triggering a failure
    with pytest.raises(Exception):
        await breaker.call(lambda: (_ for _ in ()).throw(Exception("boom")))

    assert breaker.state == "open"

    # Case 1: OPEN but not enough time elapsed -> remains open
    with pytest.raises(Exception, match="Circuit breaker is open"):
        await breaker.call(lambda: "anything")

    # Case 2: Wait enough time to attempt reset -> should become half_open then closed on success
    await asyncio.sleep(0.25)
    res = await breaker.call(lambda: "ok")
    assert res == "ok"
    assert breaker.state == "closed"


@pytest.mark.asyncio
async def test_rate_limiter_max_retries_zero_no_backoff_and_normalized_error():
    """When max_retries=0, failures raise immediately without awaiting backoff; ensure normalization occurs."""
    limiter = RateLimiter(requests_per_second=10, burst_capacity=2, max_retries=0, base_delay=0.5)

    async def fail_once():
        raise Exception("server error: 503 Service Unavailable")

    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        with pytest.raises(ProviderUnavailableError):
            await limiter.execute(fail_once, provider_type=ProviderType.GROK)
        # No retries -> no sleeps
        assert mock_sleep.await_count == 0


@pytest.mark.asyncio
async def test_get_stats_reflects_circuit_breaker_failures():
    """Ensure get_stats reports circuit breaker failure count after failures occur."""
    limiter = RateLimiter(requests_per_second=10, burst_capacity=2, max_retries=0)

    async def fail():
        raise Exception("temporary error")

    # Trigger two failures to increment breaker failure_count
    for _ in range(2):
        with pytest.raises(Exception):
            await limiter.execute(fail)

    stats = limiter.get_stats()
    assert "circuit_breaker_failures" in stats
    assert stats["circuit_breaker_failures"] >= 1


@pytest.mark.asyncio
async def test_circuit_breaker_open_with_none_last_failure_time_stays_open():
    """If state is OPEN but last_failure_time is None, breaker should not attempt reset and should raise immediately."""
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1, expected_exception=Exception)
    breaker.state = "open"
    breaker.last_failure_time = None

    with pytest.raises(Exception, match="Circuit breaker is open"):
        await breaker.call(lambda: "ok")


@pytest.mark.asyncio
async def test_circuit_breaker_failures_below_threshold_remain_closed_and_reraise():
    """When failures are below threshold, state remains CLOSED but exceptions are re-raised; last_failure_time is set."""
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0, expected_exception=Exception)

    def fail():
        raise Exception("boom")

    # Two failures, threshold is 3 -> should remain CLOSED after each
    for i in range(2):
        with pytest.raises(Exception):
            await breaker.call(fail)
        assert breaker.state == "closed"
        assert breaker.failure_count == i + 1
        assert isinstance(breaker.last_failure_time, float)


@pytest.mark.asyncio
async def test_token_bucket_refill_and_insufficient_paths():
    """Cover TokenBucket _refill math and insufficient tokens path."""
    bucket = TokenBucket(capacity=2, refill_rate=1.0)

    # Drain tokens and force time passage to test refill math and capping at capacity
    bucket.tokens = 0.0
    bucket.last_refill -= 10.0  # simulate 10s elapsed
    ok = await bucket.consume(1)
    assert ok is True
    # After refill, tokens should have been capped at capacity before consume -> now 1 left
    assert 0.0 <= bucket.tokens <= 1.0

    # Test insufficient tokens path by requesting more than available
    bucket.tokens = 0.5
    not_ok = await bucket.consume(2)
    assert not_ok is False


def test_exponential_backoff_max_delay_cap_no_jitter():
    """ExponentialBackoff.calculate_delay should cap at max_delay when attempts are large (no jitter)."""
    backoff = ExponentialBackoff(base_delay=0.1, max_delay=0.5, multiplier=3.0, jitter=False)
    # attempt 0: 0.1, 1: 0.3, 2: 0.9 -> cap at 0.5
    assert backoff.calculate_delay(0) == pytest.approx(0.1)
    assert backoff.calculate_delay(1) == pytest.approx(0.3)
    assert backoff.calculate_delay(2) == pytest.approx(0.5)
    assert backoff.calculate_delay(5) == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_rate_limiter_provider_type_none_raises_raw_exception():
    """When provider_type is None, errors should not be normalized and the raw exception should propagate."""
    limiter = RateLimiter(requests_per_second=10, burst_capacity=1, max_retries=0)

    async def fail_raw():
        raise Exception("rate limit exceeded")

    with pytest.raises(Exception) as ei:
        await limiter.execute(fail_raw)
    # Ensure it's not normalized to ProviderError
    assert not isinstance(ei.value, ProviderError)


@pytest.mark.asyncio
async def test_rate_limiter_normalizes_when_provider_type_given():
    """When provider_type is provided, exception messages should be normalized accordingly (e.g., rate limit)."""
    limiter = RateLimiter(requests_per_second=10, burst_capacity=1, max_retries=0)

    async def fail_rate_limit():
        raise Exception("Too Many Requests: rate limit exceeded")

    with pytest.raises(ProviderRateLimitError):
        await limiter.execute(fail_rate_limit, provider_type=ProviderType.GROK)
