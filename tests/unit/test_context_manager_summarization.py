import pytest

from backend.ai.context_manager import ContextManager
from backend.models.ai_models import MessageRole


@pytest.mark.asyncio
async def test_summarization_triggers_and_restructures_messages():
    # Very low threshold to force summarization once messages > 10
    cm = ContextManager(summarization_threshold=1)
    sid = await cm.create_session("u1")

    # Add 12 non-system messages to exceed the 10-message requirement
    for i in range(12):
        await cm.add_message(sid, MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT, f"msg-{i}")

    msgs = await cm.get_session_messages(sid)

    # After summarization:
    # - There should be exactly 1 system summary message with metadata.type == 'summary'
    # - Only last 10 non-system messages are kept
    summary_msgs = [m for m in msgs if m.role == MessageRole.SYSTEM]
    other_msgs = [m for m in msgs if m.role != MessageRole.SYSTEM]

    assert len(summary_msgs) == 1
    assert summary_msgs[0].metadata.get("type") == "summary"
    assert len(other_msgs) == 10

    info = await cm.get_session_info(sid)
    assert info is not None
    assert "conversation_summary" in info["metadata"]
    assert "summarized_at" in info["metadata"]

    await cm.shutdown()


@pytest.mark.asyncio
async def test_context_window_exact_boundary_not_truncated():
    cm = ContextManager()
    sid = await cm.create_session("u2")

    # Choose max_tokens such that one message is exactly equal to limit.
    # Token heuristic: tokens = (len(content)+3)//4 + 5
    # Set tokens == 10  => (len+3)//4 == 5 => len == 17
    content = "a" * 17
    await cm.add_message(sid, MessageRole.USER, content)

    window = await cm.get_context_window(sid, max_tokens=10)

    assert window.truncated is False
    assert len(window.messages) == 1

    await cm.shutdown()


@pytest.mark.asyncio
async def test_get_session_messages_returns_copy():
    cm = ContextManager()
    sid = await cm.create_session("u3")
    await cm.add_message(sid, MessageRole.USER, "hello")
    returned = await cm.get_session_messages(sid)
    # Mutate the returned list
    returned.clear()

    # Internal messages should remain intact
    internal_after = await cm.get_session_messages(sid)
    assert len(internal_after) == 1

    await cm.shutdown()
