import pytest

from backend.ai.context_manager import ContextManager
from backend.ai.providers.base import MessageRole


@pytest.mark.asyncio
async def test_shutdown_cancels_cleanup_task():
    cm = ContextManager()
    assert cm._cleanup_task is not None  # background task started
    await cm.shutdown()
    # After shutdown, task should be cancelled
    assert cm._cleanup_task.cancelled() is True


@pytest.mark.asyncio
async def test_get_context_window_system_only_too_big_returns_empty_truncated():
    cm = ContextManager()
    sid = await cm.create_session("user-sys")

    # Create a very long system message so that even with tiny max_tokens it's too large
    long_system = "X" * 1000
    await cm.add_message(sid, MessageRole.SYSTEM, long_system)

    # Force a very small max token limit
    window = await cm.get_context_window(sid, max_tokens=1)

    assert window.messages == []
    assert window.truncated is True
    assert window.total_tokens == 0


@pytest.mark.asyncio
async def test_delete_session_missing_returns_false_and_success_when_present():
    cm = ContextManager()

    # Missing
    assert await cm.delete_session("nope") is False

    # Present
    sid = await cm.create_session("user-del")
    # Add something to ensure indexes update
    await cm.add_message(sid, MessageRole.USER, "hi")

    assert await cm.delete_session(sid) is True
    # Ensure removed from maps
    assert sid not in cm.sessions
    assert "user-del" not in cm.user_sessions or sid not in cm.user_sessions.get("user-del", [])


@pytest.mark.asyncio
async def test_get_session_info_missing_returns_none():
    cm = ContextManager()
    assert await cm.get_session_info("missing") is None


@pytest.mark.asyncio
async def test_summarization_triggers_and_restructures_messages():
    # Lower the threshold so our small messages trigger summarization
    cm = ContextManager(summarization_threshold=10)
    sid = await cm.create_session("user-sum")

    # Add some system setup
    await cm.add_message(sid, MessageRole.SYSTEM, "system preface")

    # Add 12 non-system messages to exceed both length (>10) and tokens (>10)
    for i in range(12):
        await cm.add_message(sid, MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT, f"m{i}")

    # After the last add, summarization should have run
    msgs = await cm.get_session_messages(sid)

    # There should be exactly 1 system summary message plus last 10 non-system messages
    system_msgs = [m for m in msgs if m.role == MessageRole.SYSTEM]
    other_msgs = [m for m in msgs if m.role != MessageRole.SYSTEM]
    assert len(system_msgs) == 1
    assert system_msgs[0].metadata.get("type") == "summary"
    assert len(other_msgs) == 10

    info = await cm.get_session_info(sid)
    assert info is not None
    # Metadata should contain conversation_summary and summarized_at
    assert "conversation_summary" in info["metadata"]
    assert "summarized_at" in info["metadata"]


@pytest.mark.asyncio
async def test_enforce_max_sessions_per_user_removes_oldest():
    cm = ContextManager(max_sessions_per_user=2)
    user = "u1"

    # Create 3 sessions; oldest one should be removed automatically
    s1 = await cm.create_session(user)
    s2 = await cm.create_session(user)
    s3 = await cm.create_session(user)

    # Only two most recent should remain
    sessions = await cm.get_user_sessions(user)
    assert s1 not in sessions
    assert set(sessions) == {s2, s3}


@pytest.mark.asyncio
async def test_cleanup_expired_sessions_removes_by_last_activity(monkeypatch):
    cm = ContextManager(max_session_age_hours=1)
    user = "u2"
    sid = await cm.create_session(user)

    # Make the session appear old by patching last_activity
    from datetime import datetime, timezone, timedelta

    cm.sessions[sid].last_activity = datetime.now(timezone.utc) - timedelta(hours=2)

    removed = await cm.cleanup_expired_sessions()
    assert removed >= 1
    assert sid not in cm.sessions
