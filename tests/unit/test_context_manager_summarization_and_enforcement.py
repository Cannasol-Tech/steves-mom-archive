import asyncio
from datetime import datetime, timedelta, timezone
import pytest

from backend.ai.context_manager import ContextManager
from backend.ai.providers.base import Message, MessageRole


@pytest.mark.asyncio
async def test_get_context_window_system_only_exceeds_limit_returns_empty_truncated():
    cm = ContextManager(max_context_tokens=100)
    sid = await cm.create_session("u1")

    # Add a huge system message so that system_tokens > max_tokens override
    big_text = "x" * 1000
    await cm.add_message(sid, MessageRole.SYSTEM, big_text)

    win = await cm.get_context_window(sid, max_tokens=50)
    assert win.messages == []
    assert win.truncated is True
    assert win.max_tokens == 50

    await cm.shutdown()


@pytest.mark.asyncio
async def test_summary_replacement_and_window_summary_propagation():
    cm = ContextManager(summarization_threshold=1)
    sid = await cm.create_session("u2")

    # Seed an existing summary system message (should be replaced)
    await cm.add_message(sid, MessageRole.SYSTEM, "old summary", metadata={"type": "summary"})
    # Add more than 10 non-system messages to trigger summarization path again
    for i in range(11):
        await cm.add_message(sid, MessageRole.USER, f"u{i}")
        await cm.add_message(sid, MessageRole.ASSISTANT, f"a{i}")

    # After summarization, only one summary system message should remain and it should not be the old content
    msgs = await cm.get_session_messages(sid)
    summaries = [m for m in msgs if m.role == MessageRole.SYSTEM and (m.metadata or {}).get("type") == "summary"]
    assert len(summaries) == 1
    assert summaries[0].content != "old summary"

    # get_context_window should propagate session.metadata["conversation_summary"] into ContextWindow.summary
    window = await cm.get_context_window(sid, max_tokens=200)
    assert window.summary is not None and isinstance(window.summary, str)

    await cm.shutdown()


@pytest.mark.asyncio
async def test_enforce_max_sessions_per_user_handles_missing_session_entries():
    cm = ContextManager(max_sessions_per_user=1)
    # Manually create a dangling reference to a non-existent session ID
    cm.user_sessions["dangling_user"] = ["does-not-exist"]
    # Create a real session to trigger enforcement logic
    sid = await cm.create_session("dangling_user")
    await cm.enforce_max_sessions_per_user("dangling_user")
    sessions = await cm.get_user_sessions("dangling_user")
    # Exactly one session should remain and it should be the real one
    assert sessions == [sid]
    await cm.shutdown()


@pytest.mark.asyncio
async def test_get_context_window_truncates_but_keeps_system_and_recent():
    cm = ContextManager(max_context_tokens=200)
    sid = await cm.create_session("u1")

    await cm.add_message(sid, MessageRole.SYSTEM, "rules: be helpful")
    # Add a series of user/assistant messages; ensure only some fit within a small cap
    for i in range(12):
        await cm.add_message(sid, MessageRole.USER, f"q{i} " + ("a" * 40))
        await cm.add_message(sid, MessageRole.ASSISTANT, f"a{i} " + ("b" * 20))

    win = await cm.get_context_window(sid, max_tokens=180)
    # Should be truncated and include the system
    assert win.truncated is True
    assert any(m.role == MessageRole.SYSTEM for m in win.messages)
    # Messages are in chronological order and should be the most recent ones
    # Verify last message corresponds to the last assistant message added
    assert win.messages[-1].content.startswith("a11 ")

    await cm.shutdown()


@pytest.mark.asyncio
async def test_summarization_keeps_single_summary_and_last_10_messages():
    # Low threshold to trigger summarization quickly
    cm = ContextManager(summarization_threshold=1)
    sid = await cm.create_session("u1")

    # Add >10 non-system messages to trigger summarization
    for i in range(12):
        await cm.add_message(sid, MessageRole.USER, f"question {i}")
        await cm.add_message(sid, MessageRole.ASSISTANT, f"answer {i}")

    # After additions, summarization should have happened
    msgs = await cm.get_session_messages(sid)

    # Exactly one system summary should exist with metadata type "summary"
    summaries = [m for m in msgs if m.role == MessageRole.SYSTEM and (m.metadata or {}).get("type") == "summary"]
    assert len(summaries) == 1

    # Last 10 non-system messages retained
    non_system = [m for m in msgs if m.role != MessageRole.SYSTEM]
    assert len(non_system) == 10
    assert non_system[0].content.startswith("question 7") or non_system[0].content.startswith("answer 7")

    # Metadata contains conversation_summary and summarized_at
    info = await cm.get_session_info(sid)
    assert "conversation_summary" in cm.sessions[sid].metadata
    assert "summarized_at" in cm.sessions[sid].metadata
    assert info is not None

    await cm.shutdown()


@pytest.mark.asyncio
async def test_enforce_max_sessions_per_user_deletes_oldest():
    cm = ContextManager(max_sessions_per_user=3)

    # Create 5 sessions; enforcement runs on each creation
    created = []
    for i in range(5):
        sid = await cm.create_session("u1")
        created.append(sid)
        # Space out activity times by adjusting last_activity to ensure creation order reflects older first
        cm.sessions[sid].last_activity = datetime.now(timezone.utc) + timedelta(seconds=i)

    # Only newest 3 should remain
    remaining_sessions = await cm.get_user_sessions("u1")
    assert len(remaining_sessions) == 3

    # Oldest two should be deleted from sessions map
    assert created[0] not in cm.sessions
    assert created[1] not in cm.sessions

    await cm.shutdown()


@pytest.mark.asyncio
async def test_cleanup_expired_sessions_removes_by_age():
    cm = ContextManager(max_session_age_hours=0)  # cutoff is now
    sid = await cm.create_session("u1")

    # Set last_activity in the past (older than cutoff)
    cm.sessions[sid].last_activity = datetime.now(timezone.utc) - timedelta(hours=1)

    removed = await cm.cleanup_expired_sessions()
    assert removed >= 1
    assert sid not in cm.sessions

    await cm.shutdown()
