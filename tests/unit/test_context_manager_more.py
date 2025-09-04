import pytest
from typing import List

from backend.ai.context_manager import ContextManager
from backend.ai.providers.base import Message, MessageRole


@pytest.mark.asyncio
async def test_add_message_and_context_window_truncation():
    cm = ContextManager(max_context_tokens=30, summarization_threshold=10_000)
    sid = await cm.create_session("u1")

    # System message plus several user messages
    await cm.add_message(sid, MessageRole.SYSTEM, "System preface long enough to take tokens")
    for i in range(10):
        await cm.add_message(sid, MessageRole.USER, f"msg-{i}")

    cw = await cm.get_context_window(sid)

    # System message is retained, truncated should likely be True
    assert any(m.role == MessageRole.SYSTEM for m in cw.messages)
    assert cw.truncated is True
    assert cw.total_tokens <= cm.max_context_tokens

    await cm.shutdown()


@pytest.mark.asyncio
async def test_get_session_info_and_delete():
    cm = ContextManager()
    sid = await cm.create_session("u2")
    await cm.add_message(sid, MessageRole.USER, "hello")

    info = await cm.get_session_info(sid)
    assert info is not None
    assert info["session_id"] == sid
    assert info["user_id"] == "u2"
    assert info["message_count"] >= 1

    deleted = await cm.delete_session(sid)
    assert deleted is True
    assert await cm.get_session_info(sid) is None

    await cm.shutdown()


@pytest.mark.asyncio
async def test_enforce_max_sessions_per_user_removes_oldest():
    cm = ContextManager(max_sessions_per_user=2)

    s1 = await cm.create_session("u3")
    s2 = await cm.create_session("u3")
    s3 = await cm.create_session("u3")  # should trigger removal of oldest

    sessions = await cm.get_user_sessions("u3")
    # Only 2 should remain
    assert len(sessions) == 2
    # Oldest should be gone
    assert s1 not in cm.sessions

    await cm.shutdown()


@pytest.mark.asyncio
async def test_summarization_trigger_inserts_summary_message():
    # Force summarization via very low threshold and >10 non-system messages
    cm = ContextManager(summarization_threshold=1, max_context_tokens=8192)
    sid = await cm.create_session("u4")

    # Add >10 alternating messages to trigger summarization path
    for i in range(12):
        role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
        await cm.add_message(sid, role, f"content-{i} " + ("x" * 50))

    # After additions, check metadata and presence of a system summary message
    session = cm.sessions[sid]
    assert "conversation_summary" in session.metadata
    assert any(m.role == MessageRole.SYSTEM and m.metadata.get("type") == "summary" for m in session.messages)

    await cm.shutdown()
