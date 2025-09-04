import asyncio
import pytest

from backend.ai.context_manager import ContextManager
from backend.ai.providers.base import Message, MessageRole
from backend.functions.intent.intent_detector import IntentDetector
from backend.functions.intent.schemas import Intent


@pytest.mark.asyncio
async def test_session_lifecycle_and_get_session_info():
    cm = ContextManager(max_context_tokens=64, summarization_threshold=1000)
    try:
        sid = await cm.create_session(user_id="u1")
        await cm.add_message(sid, MessageRole.SYSTEM, "You are helpful")
        await cm.add_message(sid, MessageRole.USER, "hello")

        info = await cm.get_session_info(sid)
        assert info is not None
        assert info["session_id"] == sid
        assert info["message_count"] == 2

        msgs = await cm.get_session_messages(sid)
        assert len(msgs) == 2

        users_sessions = await cm.get_user_sessions("u1")
        assert sid in users_sessions

        ok = await cm.delete_session(sid)
        assert ok is True
        assert await cm.get_session_info(sid) is None
    finally:
        await cm.shutdown()


@pytest.mark.asyncio
async def test_context_window_truncation_prioritizes_system_messages():
    cm = ContextManager(max_context_tokens=16, summarization_threshold=1000)
    try:
        sid = await cm.create_session(user_id="u2")
        # Add a system message and many user/assistant messages
        await cm.add_message(sid, MessageRole.SYSTEM, "SYSTEM-PRIORITY")
        for i in range(20):
            await cm.add_message(sid, MessageRole.USER, f"u{i}")
            await cm.add_message(sid, MessageRole.ASSISTANT, f"a{i}")

        window = await cm.get_context_window(sid)
        # System message should be included; truncation likely True
        assert any(m.role == MessageRole.SYSTEM for m in window.messages)
        assert window.truncated is True
        assert window.total_tokens <= window.max_tokens
    finally:
        await cm.shutdown()


@pytest.mark.asyncio
async def test_enforce_max_sessions_per_user_removes_oldest():
    cm = ContextManager(max_sessions_per_user=2, summarization_threshold=1000)
    try:
        s1 = await cm.create_session("userX")
        s2 = await cm.create_session("userX")
        # Touch s2 so it's newer than s1
        await cm.add_message(s2, MessageRole.USER, "ping")
        s3 = await cm.create_session("userX")  # triggers enforcement

        sessions = await cm.get_user_sessions("userX")
        # Only two should remain, and the oldest (s1) likely deleted
        assert len(sessions) == 2
        assert s1 not in sessions
        assert s2 in sessions and s3 in sessions
    finally:
        await cm.shutdown()


@pytest.mark.asyncio
async def test_cleanup_expired_sessions_removes_old_sessions(monkeypatch):
    cm = ContextManager(max_session_age_hours=0)  # treat everything as expired
    try:
        s1 = await cm.create_session("userY")
        removed = await cm.cleanup_expired_sessions()
        # At least one session removed
        assert removed >= 1
        assert s1 not in cm.sessions
    finally:
        await cm.shutdown()


@pytest.mark.asyncio
async def test_intent_detector_rules_and_default():
    det = IntentDetector()
    res = await det.detect_intent("Please create a task to call mom")
    assert res.intent == Intent.CREATE_TASK
    assert res.needs_confirmation is True

    res2 = await det.detect_intent("Let's just chat about the weather")
    assert res2.intent == Intent.GENERAL_CONVERSATION
    assert res2.confidence == 0.5
