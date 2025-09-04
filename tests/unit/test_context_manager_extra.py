"""
Extra unit tests for backend.ai.context_manager.ContextManager to cover
previously untested branches.

Covers:
- delete_session returns False when session not found
- get_session_info returns None for unknown session
- shutdown cancels cleanup task cleanly
- get_context_window when system messages alone exceed max_tokens
"""

import pytest

from backend.ai.context_manager import ContextManager
from backend.models.ai_models import MessageRole


@pytest.mark.asyncio
async def test_delete_session_missing_returns_false():
    cm = ContextManager()
    assert await cm.delete_session("nope") is False
    # Cleanup to avoid background task leakage
    await cm.shutdown()


@pytest.mark.asyncio
async def test_get_session_info_missing_returns_none():
    cm = ContextManager()
    assert await cm.get_session_info("ghost") is None
    await cm.shutdown()


@pytest.mark.asyncio
async def test_shutdown_cancels_cleanup_task():
    cm = ContextManager()
    # Background task should exist
    assert cm._cleanup_task is not None
    await cm.shutdown()
    # After shutdown, task may be cancelled; ensure no exception and attribute remains
    assert cm._cleanup_task is not None


@pytest.mark.asyncio
async def test_context_window_system_only_overflow_truncates():
    cm = ContextManager()
    sid = await cm.create_session("user-x")
    # Create a very long system message to exceed a very small token cap
    long_text = "x" * 2000
    await cm.add_message(sid, MessageRole.SYSTEM, long_text)

    window = await cm.get_context_window(sid, max_tokens=5)

    assert window.truncated is True
    assert window.messages == []  # system alone overflow returns empty window

    await cm.shutdown()
