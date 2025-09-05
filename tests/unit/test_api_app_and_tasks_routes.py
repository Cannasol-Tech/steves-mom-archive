import asyncio
import json
import uuid
from typing import Any, Dict

import pytest
from starlette.testclient import TestClient

from backend.api.app import app, _parse_animation_cmd, stream_response
from backend.api.schemas import ChatMessage, ChatRequest
from backend.api import app as app_module
from backend.database import get_db
from backend.ai.model_router import ProviderError
from backend.api.routes import tasks as tasks_routes


@pytest.fixture(autouse=True)
def restore_dependency_overrides():
    # Ensure dependency overrides are cleared after each test
    old = dict(app.dependency_overrides)
    yield
    app.dependency_overrides = old


def test_health_and_api_health_ok():
    client = TestClient(app)
    r1 = client.get("/health")
    assert r1.status_code == 200
    assert r1.json() == {"status": "ok"}

    r2 = client.get("/api/health")
    assert r2.status_code == 200
    assert r2.json() == {"status": "ok"}


def test_chat_returns_503_when_router_unavailable():
    client = TestClient(app)
    # Ensure global model_router is None
    app_module.model_router = None

    req = {
        "messages": [{"role": "user", "content": "hi"}],
        "model": "grok-3-mini",
    }
    resp = client.post("/api/chat", json=req)
    assert resp.status_code == 503
    assert resp.json()["detail"] == "Model router is not available"


@pytest.mark.asyncio
async def test_stream_response_mock_path_on_no_providers():
    # Force model_router to raise ProviderError with specific text
    class BadRouter:
        async def stream_request(self, *args: Any, **kwargs: Any):
            raise ProviderError("No eligible providers available for streaming", provider_name="stub")  # type: ignore[arg-type]

    app_module.model_router = BadRouter()  # type: ignore[assignment]

    req = ChatRequest(messages=[ChatMessage(role="user", content="hello")])

    chunks = []
    async for part in stream_response(req):
        chunks.append(part)
        if len(chunks) > 10:
            break

    text = "".join(chunks)
    assert "Steve's Mom AI assistant" in text
    # Should stream piecewise (contains spaces added incrementally)
    assert " " in text


def test_parse_animation_cmd_variants():
    # JSON block
    js = '{"type":"smom","action":"wave"}'
    assert _parse_animation_cmd(f"prefix {js} suffix") == {"type": "smom", "action": "wave"}

    # HTML comment envelope
    comment = "<!-- smom: {\"action\": \"dance\"} -->"
    out = _parse_animation_cmd(comment)
    assert out["type"] == "smom" and out["action"] == "dance"

    # DSL fallback
    dsl = "[smom action=smile side=left intensity=low]"
    out = _parse_animation_cmd(dsl)
    assert out == {"type": "smom", "action": "smile", "side": "left", "intensity": "low"}

    # No match
    assert _parse_animation_cmd("no directives here") is None


def test_tasks_endpoints_404_branches(monkeypatch):
    client = TestClient(app)

    class FakeQuery:
        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return None

        def count(self):
            return 0

        def offset(self, n):
            return self

        def limit(self, n):
            return self

        def all(self):
            return []

    class FakeDB:
        def query(self, *args, **kwargs):
            return FakeQuery()

        def add(self, *a, **k):
            pass

        def commit(self):
            pass

        def refresh(self, *a, **k):
            pass

        def delete(self, *a, **k):
            pass

    def override_get_db():
        yield FakeDB()

    app.dependency_overrides[get_db] = override_get_db

    missing_id = str(uuid.uuid4())

    # read_task 404
    r = client.get(f"/api/tasks/{missing_id}")
    assert r.status_code == 404

    # update_task 404
    r = client.put(f"/api/tasks/{missing_id}", json={})
    assert r.status_code == 404

    # delete_task 204 when found would return 204, but with None -> 404
    r = client.delete(f"/api/tasks/{missing_id}")
    assert r.status_code == 404

    # approve_task 404
    r = client.post(f"/api/tasks/{missing_id}/approve")
    assert r.status_code == 404

    # reject_task 404
    r = client.post(f"/api/tasks/{missing_id}/reject")
    assert r.status_code == 404

    # analytics with zero counts - call function directly to avoid path ambiguity
    result = tasks_routes.get_task_analytics(next(override_get_db()))
    assert result == {
        "totalTasks": 0,
        "accepted": 0,
        "rejected": 0,
        "modified": 0,
    }
