import pytest
from fastapi.testclient import TestClient

from backend.api import app as app_module


@pytest.mark.asyncio
async def test_websocket_connect_and_disconnect(monkeypatch):
    """Covers `/ws` connect/receive/disconnect path in `backend/api/app.py`."""
    events = {"connected": 0, "disconnected": 0}

    class FakeManager:
        async def connect(self, websocket):
            # Must accept to complete the WS handshake
            await websocket.accept()
            events["connected"] += 1

        def disconnect(self, websocket):
            events["disconnected"] += 1

        async def broadcast(self, message: str):  # not used here
            pass

    # Swap the global manager in the app module
    monkeypatch.setattr(app_module, "manager", FakeManager(), raising=True)

    client = TestClient(app_module.app)

    # Connect to WebSocket, send a message to drive the receive loop once, then exit context
    with client.websocket_connect("/ws") as ws:
        ws.send_text("hello")
        # Server does not echo; success is no exception and our FakeManager recorded connect
        assert events["connected"] == 1

    # On context exit, disconnect should have been called
    assert events["disconnected"] == 1
