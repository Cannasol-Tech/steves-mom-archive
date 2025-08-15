"""
TDD for 4.2.3: Environment-based provider selection and default routing policy

Covers:
- Building router from environment using ProviderConfigManager
- Respect provider enablement and priority
- Derive default RoutingPolicy from environment
"""

import os
import sys
from pathlib import Path
from typing import List

import pytest

# Make backend importable
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.ai.model_router import ModelRouter, RoutingPolicy, RoutingStrategy
from backend.ai.providers.config_manager import ProviderConfigManager, ProviderType


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    # Clear provider flags to deterministic defaults for tests
    for p in ["GROK", "OPENAI", "CLAUDE", "LOCAL"]:
        monkeypatch.delenv(f"{p}_ENABLED", raising=False)
        monkeypatch.delenv(f"{p}_PRIORITY", raising=False)
        monkeypatch.delenv(f"{p}_MODEL", raising=False)
        monkeypatch.delenv(f"{p}_BASE_URL", raising=False)
    # Clear generic router env
    for k in [
        "AI_ROUTING_STRATEGY",
        "AI_MAX_COST_THRESHOLD",
        "AI_MAX_LATENCY_MS",
        "AI_RETRY_ATTEMPTS",
    ]:
        monkeypatch.delenv(k, raising=False)


@pytest.mark.asyncio
async def test_create_router_from_env_respects_enabled_and_priority(monkeypatch):
    # Enable only LOCAL and GROK; make GROK priority 1, LOCAL 5
    monkeypatch.setenv("GROK_ENABLED", "true")
    monkeypatch.setenv("LOCAL_ENABLED", "true")
    monkeypatch.setenv("OPENAI_ENABLED", "false")
    monkeypatch.setenv("CLAUDE_ENABLED", "false")
    monkeypatch.setenv("GROK_PRIORITY", "1")
    monkeypatch.setenv("LOCAL_PRIORITY", "5")

    # Provide a dummy GROK key so GROK becomes available
    monkeypatch.setenv("GROK_API_KEY", "test-key")

    # Late import to pick up envs in config manager
    from backend.ai.model_router import create_router_from_env

    router = await create_router_from_env()

    # Should include two providers added in failover order: GROK then LOCAL
    names = list(router.providers.keys())
    assert "GROKProvider" not in names  # keys should be provider_name strings like "grok"
    assert "grok" in names and "local" in names

    # FAILOVER sorting should prefer grok first when eligible
    policy = RoutingPolicy(strategy=RoutingStrategy.FAILOVER)
    eligible = await router._get_eligible_providers(
        messages=[],
        config=__import__("backend.ai.providers.base", fromlist=["ModelConfig"]).ModelConfig("grok-3-mini"),
        policy=policy,
    )
    assert eligible[0] == "grok"


@pytest.mark.asyncio
async def test_default_policy_from_env(monkeypatch):
    # Strategy and thresholds from env
    monkeypatch.setenv("AI_ROUTING_STRATEGY", "FAILOVER")
    monkeypatch.setenv("AI_MAX_COST_THRESHOLD", "0.02")
    monkeypatch.setenv("AI_MAX_LATENCY_MS", "5000")
    monkeypatch.setenv("AI_RETRY_ATTEMPTS", "2")

    # Enable local only so creation succeeds without keys
    monkeypatch.setenv("LOCAL_ENABLED", "true")

    from backend.ai.model_router import create_router_from_env

    router = await create_router_from_env()
    policy = router.default_policy

    assert policy.strategy == RoutingStrategy.FAILOVER
    assert abs(policy.max_cost_threshold - 0.02) < 1e-9
    # model_router stores seconds, we pass ms in env; expect conversion
    assert abs(policy.max_latency_threshold - 5.0) < 1e-9
    assert policy.retry_attempts == 2
