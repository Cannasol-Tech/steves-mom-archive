"""
Additional edge-case tests for backend.ai.context_manager.ContextManager

Covers:
- Context window when system-only tokens exceed max (returns empty but truncated)
- delete_session() return values for missing/present sessions
- get_session_info() returns None for missing session
- _estimate_tokens() properly handles dict content via JSON serialization
- shutdown() cancels background cleanup task cleanly
"""

import sys
from pathlib import Path
import asyncio
import json
import pytest

# Ensure backend package is importable
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.ai.context_manager import ContextManager
from backend.ai.providers.base import Message, MessageRole


@pytest.fixture
async def cm_no_bg(monkeypatch):
    """ContextManager with background cleanup task disabled."""
    monkeypatch.setattr(
        "backend.ai.context_manager.ContextManager._start_cleanup_task", lambda self: None
    )
    cm = ContextManager(max_context_tokens=64, summarization_threshold=10_000)
    try:
        yield cm
    finally:
        # Ensure clean shutdown just in case
        await cm.shutdown()


@pytest.mark.asyncio
async def test_context_window_system_only_too_big(cm_no_bg: ContextManager):
    session_id = await cm_no_bg.create_session("user-sysbig")

    # Create a very long system message so that system tokens alone exceed max_tokens
    long_text = "A" * 1000
    await cm_no_bg.add_message(session_id, MessageRole.SYSTEM, long_text)

    window = await cm_no_bg.get_context_window(session_id, max_tokens=10)

    assert window.truncated is True
    assert window.messages == []
    assert window.total_tokens == 0
    assert window.max_tokens == 10


@pytest.mark.asyncio
async def test_delete_session_return_values(cm_no_bg: ContextManager):
    # Deleting a non-existent session returns False
    assert await cm_no_bg.delete_session("missing-123") is False

    # Create and then delete to get True
    sid = await cm_no_bg.create_session("user-del")
    assert await cm_no_bg.delete_session(sid) is True


@pytest.mark.asyncio
async def test_get_session_info_none_for_missing(cm_no_bg: ContextManager):
    assert await cm_no_bg.get_session_info("nope") is None


@pytest.mark.asyncio
async def test_estimate_tokens_handles_dict_content(cm_no_bg: ContextManager):
    sid = await cm_no_bg.create_session("user-dict")
    data = {"a": 1, "b": "two", "nested": {"ok": True}}
    await cm_no_bg.add_message(sid, MessageRole.USER, data)

    # Fetch raw messages to pass into _estimate_tokens
    messages = await cm_no_bg.get_session_messages(sid)
    # Ensure it doesn't throw and returns a positive integer
    est = cm_no_bg._estimate_tokens(messages)
    assert isinstance(est, int)
    assert est > 0


@pytest.mark.asyncio
async def test_shutdown_cancels_background_task():
    """Instantiate without monkeypatch to start the cleanup task and ensure shutdown cancels it."""
    cm = ContextManager(max_context_tokens=64)

    # The cleanup task should exist
    assert cm._cleanup_task is not None
    assert not cm._cleanup_task.cancelled()

    await cm.shutdown()

    # After shutdown the task should be cancelled
    assert cm._cleanup_task is None or cm._cleanup_task.cancelled()
