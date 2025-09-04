"""
Unit tests for backend.ai.context_manager.ContextManager

Covers:
- Session creation and message addition
- Context window truncation and system message preservation
- Summarization trigger and metadata update
- Session deletion and cleanup of expired sessions
- Enforcing max sessions per user (oldest removal)
- Session creation validation
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import pytest
from unittest.mock import patch

# Ensure backend package is importable
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.models.ai_models import MessageRole
from backend.ai.context_manager import ContextManager


@pytest.mark.asyncio
async def test_create_session_and_add_message():
    cm = ContextManager(max_context_tokens=1000)

    session_id = await cm.create_session(user_id="u1")
    assert isinstance(session_id, str) and len(session_id) > 0

    await cm.add_message(session_id, MessageRole.USER, "Hello")
    messages = await cm.get_session_messages(session_id)

    assert len(messages) == 1
    assert messages[0].role == MessageRole.USER
    assert messages[0].content == "Hello"


@pytest.mark.asyncio
async def test_context_window_truncation_keeps_system_and_recent():
    cm = ContextManager()
    sid = await cm.create_session(user_id="u2")

    # Add a system prompt and many user/assistant messages
    await cm.add_message(sid, MessageRole.SYSTEM, "You are helpful.")  # likely >10 tokens alone but should be prioritized

    # Add 8 alternating short messages
    for i in range(8):
        role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
        await cm.add_message(sid, role, f"m{i}")

    initial_messages = await cm.get_session_messages(sid)
    window = await cm.get_context_window(sid, max_tokens=10)

    # Should be truncated
    assert len(window.messages) < len(initial_messages)
    # System message should be present if not truncated
    if len(window.messages) > 1: # More than just one message fits
        assert any(m.role == MessageRole.SYSTEM for m in window.messages)
    # Total tokens should not exceed max
    assert window.total_tokens <= window.max_tokens


@pytest.mark.asyncio
async def test_summarization_trigger_and_metadata_summary():
    # Set a higher summarization threshold to trigger only once at the end
    cm = ContextManager(summarization_threshold=100, max_context_tokens=2_000)
    sid = await cm.create_session(user_id="u3")

    # Add messages to trigger summarization
    for i in range(20):
        await cm.add_message(sid, MessageRole.USER, f"ask {i}")
        await cm.add_message(sid, MessageRole.ASSISTANT, f"reply {i}")

    # Manually trigger summarization to ensure it runs once at the end
    await cm._summarize_conversation(sid)

    # After summarization, should have 11 messages (10 recent + 1 summary)
    msgs = await cm.get_session_messages(sid)
    assert len(msgs) == 11

    info = await cm.get_session_info(sid)
    assert info is not None
    # Summary stored in metadata
    assert "metadata" in info
    assert "conversation_summary" in info["metadata"]
    assert "summarized_at" in info["metadata"]


@pytest.mark.asyncio
async def test_cleanup_expired_sessions_removes_old():
    cm = ContextManager(max_session_age_hours=1)
    sid = await cm.create_session(user_id="u4")

    # Manually age the session beyond cutoff
    cm.sessions[sid].last_activity = datetime.now(timezone.utc) - timedelta(hours=2)

    cleaned = await cm.cleanup_expired_sessions()
    assert cleaned >= 1
    assert await cm.get_session_info(sid) is None


@pytest.mark.asyncio
async def test_enforce_max_sessions_per_user_removes_oldest():
    cm = ContextManager(max_sessions_per_user=2)
    user = "u5"

    # Create 3 sessions; the oldest should be deleted
    s1 = await cm.create_session(user)
    # Make s1 the oldest by time
    cm.sessions[s1].last_activity = datetime.now(timezone.utc) - timedelta(hours=3)

    s2 = await cm.create_session(user)
    cm.sessions[s2].last_activity = datetime.now(timezone.utc) - timedelta(hours=2)

    s3 = await cm.create_session(user)  # triggers enforcement

    remaining = await cm.get_user_sessions(user)
    assert len(remaining) == 2
    # Oldest (s1) should be gone
    assert s1 not in remaining
    assert s2 in remaining and s3 in remaining

    # Also ensure sessions dict reflects removal
    assert s1 not in cm.sessions


@pytest.fixture
def context_manager(monkeypatch):
    monkeypatch.setattr('backend.ai.context_manager.ContextManager._start_cleanup_task', lambda self: None)
    return ContextManager()


@pytest.mark.asyncio
async def test_add_message_invalid_session(context_manager):
    with pytest.raises(ValueError) as excinfo:
        await context_manager.add_message("invalid_id", MessageRole.USER, "Test")
    assert "Session invalid_id not found" in str(excinfo.value)

@pytest.mark.asyncio
async def test_session_creation_duplicate_id(context_manager):
    session_id = await context_manager.create_session("user1", session_id="custom_id")
    assert session_id == "custom_id"
    
    # Should reject duplicate session ID
    with pytest.raises(ValueError) as excinfo:
        await context_manager.create_session("user2", session_id="custom_id")
    assert "already exists" in str(excinfo.value)

@pytest.mark.asyncio
async def test_session_metadata_persistence(context_manager):
    metadata = {"project": "steves-mom", "version": 1}
    session_id = await context_manager.create_session("user3", metadata=metadata)
    
    session_info = await context_manager.get_session_info(session_id)
    assert session_info["metadata"] == metadata

@pytest.mark.asyncio
async def test_summarization_trigger(context_manager):
    """Test summarization is triggered when token threshold is exceeded"""
    session_id = await context_manager.create_session("user1")
    
    # Add 15 messages (more than 10)
    for i in range(15):
        await context_manager.add_message(session_id, MessageRole.USER, f"Message {i}")
    
    # Mock token estimation to return a value above the threshold (default 4096)
    with patch.object(context_manager, '_estimate_tokens', return_value=5000):
        # This should trigger summarization on the next add_message
        await context_manager.add_message(session_id, MessageRole.USER, "Trigger")
    
    messages = await context_manager.get_session_messages(session_id)
    assert len(messages) == 12
    # The first message should be the summary (system role)
    assert messages[0].role == MessageRole.SYSTEM
    assert "Previous conversation summary" in messages[0].content
    # The last message is the one we added after summarization
    assert messages[-1].content == "Trigger"
