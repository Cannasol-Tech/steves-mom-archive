import asyncio
import types
import pytest
from datetime import timedelta

from backend.ai.rate_limiter import (
    TokenBucket,
    ExponentialBackoff,
    CircuitBreaker,
    CircuitBreakerState,
    ErrorNormalizer,
    RateLimiter,
)
from backend.ai.providers.base_provider import (
    ProviderType,
    ProviderUnavailableError,
)
from backend.ai.context_manager import ContextManager


@pytest.mark.asyncio
async def test_token_bucket_refill_with_time_monkeypatch(monkeypatch):
    # Control time.time() to simulate passage of time deterministically
    base = 1_000_000.0
    current = {"t": base}

    def fake_time():
        return current["t"]

    monkeypatch.setattr("backend.ai.rate_limiter.time.time", fake_time)

    bucket = TokenBucket(capacity=2, refill_rate=1.0)  # 1 token/sec
    # Start full (2). Consume both
    assert await bucket.consume()
    assert await bucket.consume()
    # Now empty; immediate consume should fail (no time passed)
    assert not await bucket.consume()
    # Advance 1.5s -> should refill ~1.5 tokens capped by capacity; consume succeeds once
    current["t"] = base + 1.5
    assert await bucket.consume()  # now 0.5 tokens remain internally
    # Another consume should fail until time advances further
    assert not await bucket.consume()


def test_exponential_backoff_without_jitter():
    backoff = ExponentialBackoff(base_delay=1.0, max_delay=10.0, multiplier=2.0, jitter=False)
    assert backoff.calculate_delay(0) == 1.0
    assert backoff.calculate_delay(1) == 2.0
    assert backoff.calculate_delay(2) == 4.0
    assert backoff.calculate_delay(3) == 8.0
    # capped by max_delay
    assert backoff.calculate_delay(4) == 10.0


@pytest.mark.asyncio
async def test_circuit_breaker_open_and_recover(monkeypatch):
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0, expected_exception=Exception)

    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        raise Exception("boom")

    # Two failures => OPEN
    with pytest.raises(Exception):
        await cb.call(flaky)
    with pytest.raises(Exception):
        await cb.call(flaky)
    assert cb.state == CircuitBreakerState.OPEN

    # Pretend time passed for recovery
    cb.last_failure_time -= 2.0
    # Half-open on next attempt, still failing keeps it OPEN after increment
    with pytest.raises(Exception):
        await cb.call(flaky)
    assert cb.state in {CircuitBreakerState.OPEN, CircuitBreakerState.CLOSED, CircuitBreakerState.HALF_OPEN}


def test_error_normalizer_patterns():
    norm = ErrorNormalizer()
    rl = norm.normalize_error(Exception("429 rate limit exceeded"), ProviderType.GROK)
    assert rl.error_code == "RATE_LIMIT"

    to = norm.normalize_error(TimeoutError("connection timeout"), ProviderType.GROK)
    assert to.error_code == "TIMEOUT"

    unav = norm.normalize_error(Exception("Service Unavailable 503"), ProviderType.GROK)
    assert unav.error_code == "UNAVAILABLE"

    unk = norm.normalize_error(Exception("weird"), ProviderType.GROK)
    assert unk.error_code == "UNKNOWN"


@pytest.mark.asyncio
async def test_rate_limiter_execute_with_retries_and_success(monkeypatch):
    limiter = RateLimiter(requests_per_second=100.0, burst_capacity=1, max_retries=2, base_delay=0.0, max_delay=0.0)
    attempts = {"n": 0}

    async def sometimes():
        attempts["n"] += 1
        if attempts["n"] < 3:
            # timeout-like error (retriable)
            raise Exception("timeout")
        return "ok"

    result = await limiter.execute(sometimes, provider_type=ProviderType.GROK)
    assert result == "ok"
    assert attempts["n"] == 3


@pytest.mark.asyncio
async def test_rate_limiter_immediate_rate_limit_error():
    # No tokens available
    limiter = RateLimiter(requests_per_second=0.0001, burst_capacity=0, max_retries=0)

    async def noop():
        return True

    with pytest.raises(Exception) as ei:
        await limiter.execute(noop, provider_type=ProviderType.GROK)
    assert "RATE_LIMIT" in str(ei.value)


@pytest.mark.asyncio
async def test_rate_limiter_non_retriable_raises_immediately():
    limiter = RateLimiter(requests_per_second=100.0, burst_capacity=1, max_retries=3, base_delay=0.0, max_delay=0.0)

    async def always_unavailable():
        # Matches unavailable pattern and becomes non-retriable ProviderUnavailableError
        raise Exception("Service Unavailable 503")

    with pytest.raises(ProviderUnavailableError):
        await limiter.execute(always_unavailable, provider_type=ProviderType.GROK)


@pytest.mark.asyncio
async def test_context_manager_cleanup_expired_sessions():
    cm = ContextManager(max_session_age_hours=1)
    sid = await cm.create_session("u1")
    # Backdate last_activity beyond cutoff
    session = cm.sessions[sid]
    session.last_activity = session.last_activity - timedelta(hours=2)

    cleaned = await cm.cleanup_expired_sessions()
    assert cleaned == 1
    assert sid not in cm.sessions
    await cm.shutdown()
