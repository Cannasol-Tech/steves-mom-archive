"""
Unit tests for typed configuration snapshot/load in ModelRouter (1.4.MY.4.T)

Covers:
- configuration snapshot includes typed policy fields and provider entries
- invalid updates raise clear errors
- round-trip load_configuration/get_configuration_snapshot preserves schema
"""

import sys
from pathlib import Path
from typing import Any, Dict
import pytest

# Ensure backend is importable
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.ai.model_router import ModelRouter, RoutingPolicy, RoutingStrategy
from backend.ai.providers.base import ModelCapability, ModelConfig


def test_configuration_snapshot_schema():
    router = ModelRouter()

    # Snapshot with no providers
    snap = router.get_configuration_snapshot()
    assert "default_policy" in snap and "providers" in snap

    policy = snap["default_policy"]
    assert set(["strategy", "max_cost_threshold", "max_latency_threshold", "required_capabilities", "preferred_providers", "fallback_enabled", "retry_attempts"]).issubset(policy.keys())

    # Types
    assert isinstance(policy["strategy"], str)
    assert isinstance(policy["max_cost_threshold"], float)
    assert isinstance(policy["max_latency_threshold"], float)
    assert isinstance(policy["required_capabilities"], list)
    assert isinstance(policy["preferred_providers"], list)
    assert isinstance(policy["fallback_enabled"], bool)
    assert isinstance(policy["retry_attempts"], int)


def test_invalid_updates_raise_errors():
    router = ModelRouter()
    with pytest.raises(ValueError):
        router.update_provider_config("missing", {"priority": 1})

    # Add a fake provider via minimal monkeypatch on router internals is avoided; rely on ValueError path only here.


def test_round_trip_load_and_snapshot_preserves_schema():
    router = ModelRouter()

    cfg: Dict[str, Any] = {
        "default_policy": {
            "strategy": "capability_based",
            "max_cost_threshold": 0.12,
            "max_latency_threshold": 10.0,
            "required_capabilities": [ModelCapability.TEXT_GENERATION.value],
            "preferred_providers": ["local"],
            "fallback_enabled": True,
            "retry_attempts": 4,
        },
        "providers": {
            "local": {
                "priority": 5,
                "weight": 2.0,
                "max_requests_per_minute": 120,
                "max_cost_per_request": 0.05,
                "enabled": True,
                "fallback_order": 0,
            }
        },
    }

    router.load_configuration(cfg)
    snap = router.get_configuration_snapshot()

    # Validate keys exist after round-trip
    assert set(cfg.keys()) == set(snap.keys())
    dp = snap["default_policy"]
    assert dp["strategy"] == "capability_based"
    assert dp["retry_attempts"] == 4
    assert isinstance(dp["required_capabilities"], list)
    assert isinstance(snap["providers"], dict)

