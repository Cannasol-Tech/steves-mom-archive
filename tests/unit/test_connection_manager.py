import pytest

from backend.api.connection_manager import ConnectionManager


class FakeWebSocket:
    def __init__(self):
        self.accepted = False
        self.sent = []

    async def accept(self):
        self.accepted = True

    async def send_text(self, message: str):
        self.sent.append(message)


@pytest.mark.asyncio
async def test_connect_broadcast_disconnect():
    mgr = ConnectionManager()
    ws1 = FakeWebSocket()
    ws2 = FakeWebSocket()

    # Connect two websockets
    await mgr.connect(ws1)
    await mgr.connect(ws2)

    assert ws1.accepted and ws2.accepted
    assert len(mgr.active_connections) == 2

    # Broadcast a message
    await mgr.broadcast("hello")
    assert ws1.sent == ["hello"]
    assert ws2.sent == ["hello"]

    # Disconnect one
    mgr.disconnect(ws1)
    assert len(mgr.active_connections) == 1
    assert mgr.active_connections[0] is ws2
