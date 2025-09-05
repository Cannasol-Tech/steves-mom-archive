import asyncio
import pytest

from backend.ai.model_router import ModelRouter, RoutingPolicy, RoutingStrategy
from backend.ai.providers.base import Message, MessageRole, ModelConfig


@pytest.mark.asyncio
async def test_stream_request_no_eligible_providers_raises():
    router = ModelRouter()
    with pytest.raises(Exception) as exc:
        async for _ in router.stream_request(
            [Message(role=MessageRole.USER, content="hi")],
            ModelConfig(model_name="grok-3-mini"),
        ):
            pass
    assert "No eligible providers" in str(exc.value)


def test_update_default_policy_invalid_strategy_raises(monkeypatch):
    router = ModelRouter()
    policy = RoutingPolicy()
    # Corrupt the strategy to a non-enum value to exercise validation branch
    monkeypatch.setattr(policy, "strategy", "bogus")
    with pytest.raises(ValueError):
        router.update_default_policy(policy)  # type: ignore[arg-type]


def test_update_provider_config_unknown_provider_raises():
    router = ModelRouter()
    with pytest.raises(ValueError):
        router.update_provider_config("nope", {"enabled": True})


@pytest.mark.asyncio
async def test_update_provider_config_validations_and_enable_disable(monkeypatch):
    router = ModelRouter()

    # Create a minimal fake provider
    class P:
        provider_name = "p"
        async def initialize(self):
            return None
    p = P()
    await router.add_provider(p)  # type: ignore[arg-type]

    # Priority must be positive
    with pytest.raises(ValueError):
        router.update_provider_config("p", {"priority": 0})
    # Weight must be positive
    with pytest.raises(ValueError):
        router.update_provider_config("p", {"weight": 0})
    # Max req/min must be positive
    with pytest.raises(ValueError):
        router.update_provider_config("p", {"max_requests_per_minute": 0})
    # Max cost must be positive
    with pytest.raises(ValueError):
        router.update_provider_config("p", {"max_cost_per_request": 0.0})
    # Fallback order must be non-negative
    with pytest.raises(ValueError):
        router.update_provider_config("p", {"fallback_order": -1})

    # Apply valid updates
    router.update_provider_config("p", {
        "priority": 5,
        "weight": 2.5,
        "enabled": False,
        "max_requests_per_minute": 120,
        "max_cost_per_request": 0.2,
        "fallback_order": 3,
    })
    snap = router.get_configuration_snapshot()
    prov = snap["providers"]["p"]
    assert prov["priority"] == 5
    assert prov["weight"] == 2.5
    assert prov["max_requests_per_minute"] == 120
    assert prov["max_cost_per_request"] == 0.2
    assert prov["enabled"] is False
    assert prov["fallback_order"] == 3

    # Enable/disable provider success paths
    router.enable_provider("p")
    router.disable_provider("p")

    # Enable/disable unknown raises
    with pytest.raises(ValueError):
        router.enable_provider("nope")
    with pytest.raises(ValueError):
        router.disable_provider("nope")


def test_check_rate_limit_and_record_request_and_reset_breakers(monkeypatch):
    router = ModelRouter()
    # Seed internal maps for a provider name without actually adding one
    name = "prov"
    router.providers[name] = type("PC", (), {"max_requests_per_minute": 2, "provider": None, "priority":1, "weight":1.0, "fallback_order":0, "enabled":True})()  # type: ignore
    # Patch time.time so we can control the cutoff logic and ensure both entries are within last 60s
    monkeypatch.setattr("time.time", lambda: 200.5)
    # With now=200.5, cutoff=140.5; use recent timestamps so len == max_requests
    router._request_counts[name] = [180.6, 199.9]  # both within last 60 seconds
    router._latency_history[name] = []
    router._error_counts[name] = 3
    router._circuit_breakers[name] = True

    # If we already have 2 within window and limit=2, next check should be False
    ok = router._check_rate_limit(name)
    assert ok is False

    # Record a new request and ensure metrics updated and breaker reset
    router._record_request(name, latency=0.123)
    assert router._error_counts[name] == 0
    assert router._circuit_breakers[name] is False
    assert router._latency_history[name][-1] == pytest.approx(0.123, rel=1e-6)

    # Record error increments and may set breaker when threshold exceeded
    for _ in range(6):
        router._record_error(name)
    assert router._circuit_breakers[name] is True


@pytest.mark.asyncio
async def test_reset_circuit_breakers_and_get_provider_status(monkeypatch):
    router = ModelRouter()

    class P:
        provider_name = "p"
        async def initialize(self):
            return None
        async def health_check(self):
            return {"ok": True}
    p = P()
    await router.add_provider(p)  # type: ignore[arg-type]

    # Trip error and breaker
    for _ in range(6):
        router._record_error("p")
    assert router._circuit_breakers["p"] is True

    await router.reset_circuit_breakers()
    assert router._circuit_breakers["p"] is False
    assert router._error_counts["p"] == 0

    status = await router.get_provider_status()
    assert "p" in status
    assert status["p"]["circuit_breaker"] is False


def test_get_configuration_snapshot_structure():
    router = ModelRouter()
    snap = router.get_configuration_snapshot()
    assert "default_policy" in snap
    assert "providers" in snap
    assert snap["default_policy"]["strategy"] in {s.value for s in RoutingStrategy}
