import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.ai.providers.base import ModelResponse
from backend.api import app as app_module


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    # Ensure no GROK_API_KEY leaks between tests
    monkeypatch.delenv("GROK_API_KEY", raising=False)


def get_client() -> TestClient:
    return TestClient(app_module.app)


def test_health_ok():
    client = get_client()
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_chat_router_not_available_returns_503(monkeypatch):
    # Simulate router failing to load
    monkeypatch.setattr(app_module, "model_router", None)

    client = get_client()
    payload = {
        "messages": [{"role": "user", "content": "Hello"}],
        "model": "grok-3-mini",
    }
    r = client.post("/api/chat", json=payload)
    assert r.status_code == 503
    assert "Model router is not available" in r.json()["detail"]




def test_parse_animation_cmd_variants():
    # JSON block
    json_text = "Some text {\"type\":\"smom\",\"action\":\"wave\"} more"
    cmd = app_module._parse_animation_cmd(json_text)
    assert cmd and cmd["type"] == "smom" and cmd["action"] == "wave"

    # HTML comment style
    comment_text = "before <!-- smom: {\"action\":\"dance\"} --> after"
    cmd = app_module._parse_animation_cmd(comment_text)
    assert cmd and cmd["type"] == "smom" and cmd["action"] == "dance"

    # DSL style
    dsl_text = "answer [smom action=nod side=left] trailing"
    cmd = app_module._parse_animation_cmd(dsl_text)
    assert cmd and cmd["type"] == "smom" and cmd["action"] == "nod" and cmd["side"] == "left"

    # No match
    assert app_module._parse_animation_cmd("no directive here") is None


def test_chat_streaming_success_with_mocked_router_and_broadcast(monkeypatch):

    # Capture broadcasts
    class FakeManager:
        def __init__(self):
            self.sent = []

        async def broadcast(self, message: str):
            self.sent.append(message)

    fake_manager = FakeManager()
    monkeypatch.setattr(app_module, "manager", fake_manager, raising=True)

    # Mock the model router's stream_request method
    mock_router = AsyncMock()
    
    async def mock_stream_generator(*args, **kwargs):
        yield "ok "
        yield "<!-- smom: "
        yield '{"action": "blink"} -->'

    # Replace the async method with a regular mock that returns the async generator
    mock_router.stream_request = MagicMock(return_value=mock_stream_generator())
    monkeypatch.setattr(app_module, "model_router", mock_router)

    client = get_client()
    payload = {
        "messages": [
            {"role": "user", "content": "Hi"},
        ]
    }

    # Use stream=True to consume the response
    with client.stream("POST", "/api/chat", json=payload) as r:
        assert r.status_code == 200
        
        # Collect chunks
        chunks = [chunk for chunk in r.iter_text()]
        full_text = "".join(chunks)

    assert "ok <!-- smom: {\"action\": \"blink\"} -->" in full_text
    assert len(fake_manager.sent) == 1
    assert '"action": "blink"' in fake_manager.sent[0]
