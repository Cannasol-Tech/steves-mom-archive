"""
More unit tests for backend.ai.model_router.ModelRouter

Covers:
- get_provider_status aggregates provider health and metrics
- reset_circuit_breakers clears breakers and error counts
- update_provider_config validates and applies updates
- create_router_from_env uses ProviderConfigManager and sets priorities/fallbacks
"""

import types
import pytest

from backend.ai.model_router import ModelRouter, RoutingPolicy, create_router_from_env
from backend.ai.providers.base import LLMProvider, Message, MessageRole, ModelConfig, ModelResponse, ModelCapability


class TinyProvider(LLMProvider):
    def __init__(self, name: str, models=None, cost: float = 0.01):
        super().__init__(api_key="k")
        self._name = name
        self._models = models or ["grok-3-mini"]
        self._cost = cost

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def supported_capabilities(self):
        return [ModelCapability.TEXT_GENERATION]

    @property
    def available_models(self):
        return self._models

    async def initialize(self):
        return None

    async def generate_response(self, messages, config):
        return ModelResponse(content="x", model=config.model_name, provider=self._name, usage={"prompt_tokens":1, "completion_tokens":1, "total_tokens":2})

    async def stream_response(self, messages, config):
        yield "x"

    def estimate_cost(self, messages, config):
        return self._cost

    async def health_check(self):
        return {"ok": True, "provider": self._name}


@pytest.mark.asyncio
async def test_get_provider_status_and_reset_breakers():
    r = ModelRouter()
    p = TinyProvider("p")
    await r.add_provider(p)

    # Simulate traffic and an error
    r._record_request("p", latency=0.25)
    r._record_error("p")

    status = await r.get_provider_status()
    assert "p" in status
    assert status["p"]["enabled"] is True
    assert status["p"]["average_latency"] > 0
    assert status["p"]["error_count"] >= 1

    # Activate and then reset breaker
    for _ in range(6):
        r._record_error("p")
    assert r._circuit_breakers["p"] is True

    await r.reset_circuit_breakers()
    assert r._circuit_breakers["p"] is False
    assert r._error_counts["p"] == 0


@pytest.mark.asyncio
async def test_update_provider_config_validations_and_updates():
    r = ModelRouter()
    p = TinyProvider("p")
    await r.add_provider(p)

    # Valid updates
    r.update_provider_config("p", {"priority": 5, "weight": 2.0, "enabled": False, "max_requests_per_minute": 120, "max_cost_per_request": 0.2, "fallback_order": 3})
    cfg = r.providers["p"]
    assert cfg.priority == 5
    assert cfg.weight == 2.0
    assert cfg.enabled is False
    assert cfg.max_requests_per_minute == 120
    assert abs(cfg.max_cost_per_request - 0.2) < 1e-9
    assert cfg.fallback_order == 3

    # Invalids
    with pytest.raises(ValueError):
        r.update_provider_config("p", {"priority": 0})
    with pytest.raises(ValueError):
        r.update_provider_config("p", {"weight": 0})
    with pytest.raises(ValueError):
        r.update_provider_config("p", {"max_requests_per_minute": 0})
    with pytest.raises(ValueError):
        r.update_provider_config("p", {"max_cost_per_request": 0})
    with pytest.raises(ValueError):
        r.update_provider_config("p", {"fallback_order": -1})


@pytest.mark.asyncio
async def test_create_router_from_env_uses_pcm(monkeypatch):
    # Fake credentials objects with attributes provider_type and priority
    class Cred:
        def __init__(self, provider_type, priority):
            self.provider_type = provider_type
            self.priority = priority

    # Create distinct provider_type values; they can be any hashables used by PCM
    PT_A = type("PT_A", (), {"value": "a"})()
    PT_B = type("PT_B", (), {"value": "b"})()

    class PCM:
        def get_available_providers(self):
            return [Cred(PT_A, 1), Cred(PT_B, 2)]  # PT_A higher priority

        def create_provider(self, provider_type):
            # Return TinyProvider instances tagged by the value
            return TinyProvider(f"prov-{getattr(provider_type, 'value', 'x')}")

    # Monkeypatch importlib to return our fake PCM
    import importlib
    fake_mod = types.SimpleNamespace(ProviderConfigManager=lambda: PCM())
    monkeypatch.setattr(importlib, "import_module", lambda name: fake_mod)

    router = await create_router_from_env()

    # We expect two providers added with fallback orders 0,1 and inverted priority mapping
    names = list(router.providers.keys())
    assert set(names) == {"prov-a", "prov-b"}
    assert router.providers["prov-a"].fallback_order == 0
    assert router.providers["prov-b"].fallback_order == 1
    # priority inversion: priority=max(1,100 - cred.priority)
    assert router.providers["prov-a"].priority == 99
    assert router.providers["prov-b"].priority == 98
