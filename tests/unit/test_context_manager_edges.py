import pytest
from datetime import datetime, timedelta, timezone

from backend.ai.context_manager import ContextManager
from backend.ai.providers.base import MessageRole


@pytest.mark.asyncio
async def test_system_only_too_large_truncation_branch():
    # Make the token budget tiny and system message very large
    cm = ContextManager(max_context_tokens=5, summarization_threshold=10_000)
    sid = await cm.create_session("user-x")

    await cm.add_message(sid, MessageRole.SYSTEM, "S" * 200)
    await cm.add_message(sid, MessageRole.USER, "hello")

    cw = await cm.get_context_window(sid)
    # When system tokens alone exceed budget, window should be empty and truncated
    assert cw.messages == []
    assert cw.truncated is True
    assert cw.total_tokens == 0

    await cm.shutdown()


@pytest.mark.asyncio
async def test_token_estimator_handles_dict_content_via_get_session_info():
    cm = ContextManager(summarization_threshold=10_000)
    sid = await cm.create_session("user-y")

    # Add a dict content to exercise json.dumps code path in _estimate_tokens
    await cm.add_message(sid, MessageRole.USER, {"foo": "bar", "n": 42})

    info = await cm.get_session_info(sid)
    assert info is not None
    # Should compute estimated_tokens without error and be >= fixed overhead
    assert info["estimated_tokens"] >= 1

    await cm.shutdown()


@pytest.mark.asyncio
async def test_cleanup_expired_sessions_removes_old_sessions():
    cm = ContextManager(max_session_age_hours=1)
    sid = await cm.create_session("user-z")

    # Force last_activity to be old
    session = cm.sessions[sid]
    session.last_activity = datetime.now(timezone.utc) - timedelta(hours=2)

    cleaned = await cm.cleanup_expired_sessions()
    assert cleaned == 1
    assert sid not in cm.sessions

    await cm.shutdown()


@pytest.mark.asyncio
async def test_generate_session_id_format():
    cm = ContextManager()
    sid = cm._generate_session_id("abc")
    assert isinstance(sid, str)
    assert len(sid) == 16
    # All hex characters
    int(sid, 16)
    await cm.shutdown()
