import pytest

from backend.ai.context_manager import ContextManager
from backend.ai.providers.base import MessageRole


@pytest.mark.asyncio
async def test_empty_session_window_has_no_truncation():
    cm = ContextManager()
    sid = await cm.create_session("u-empty")

    window = await cm.get_context_window(sid, max_tokens=50)
    assert window.messages == []
    assert window.total_tokens == 0
    assert window.truncated is False


@pytest.mark.asyncio
async def test_exact_token_boundary_includes_all_that_fit():
    cm = ContextManager()
    sid = await cm.create_session("u-boundary")

    # Add one system and two user messages; compute exact token budget to include all
    await cm.add_message(sid, MessageRole.SYSTEM, "sys-xxxx")  # 8 chars
    await cm.add_message(sid, MessageRole.USER, "u-xxxxxxxx")  # 10 chars
    await cm.add_message(sid, MessageRole.ASSISTANT, "a-xxxxxx")  # 8 chars

    # Compute exact tokens using the manager's estimator
    msgs = await cm.get_session_messages(sid)
    total = cm._estimate_tokens(msgs)  # type: ignore[attr-defined]

    window = await cm.get_context_window(sid, max_tokens=total)
    assert len(window.messages) == 3
    # System should remain first
    assert window.messages[0].role == MessageRole.SYSTEM
    assert window.total_tokens == total
    assert window.truncated is False


@pytest.mark.asyncio
async def test_preserve_non_summary_system_messages_on_summarization():
    # Force low threshold to trigger summarization with small messages
    cm = ContextManager(summarization_threshold=10)
    sid = await cm.create_session("u-sum-preserve")

    # Add a non-summary system message that should be preserved
    await cm.add_message(sid, MessageRole.SYSTEM, "policy: keep me")

    # Add enough alternating messages to trigger summarization (>10 non-system)
    for i in range(12):
        await cm.add_message(
            sid,
            MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
            f"m{i}"
        )

    messages = await cm.get_session_messages(sid)
    system_msgs = [m for m in messages if m.role == MessageRole.SYSTEM]
    non_summary_system = [m for m in system_msgs if m.metadata.get("type") != "summary"]
    summary_msgs = [m for m in system_msgs if m.metadata.get("type") == "summary"]

    # Expect exactly one preserved non-summary system and exactly one summary
    assert len(non_summary_system) == 1
    assert "policy: keep me" in non_summary_system[0].content
    assert len(summary_msgs) == 1

    # Ensure only the last 10 non-system messages remain
    others = [m for m in messages if m.role != MessageRole.SYSTEM]
    assert len(others) == 10
