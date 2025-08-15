import pytest
from backend.functions.intent.intent_detector import IntentDetector
from backend.functions.intent.schemas import Intent

@pytest.mark.asyncio
async def test_detect_create_task_intent():
    """Test that the 'create_task' intent is correctly detected."""
    detector = IntentDetector()
    query = "Can you create a task to follow up with John?"
    result = await detector.detect_intent(query)
    assert result.intent == Intent.CREATE_TASK
    assert result.confidence > 0.8
    assert result.needs_confirmation is True

@pytest.mark.asyncio
async def test_detect_send_email_intent():
    """Test that the 'send_email' intent is correctly detected."""
    detector = IntentDetector()
    query = "I need to send an email to the team about the project update."
    result = await detector.detect_intent(query)
    assert result.intent == Intent.SEND_EMAIL
    assert result.confidence > 0.8
    assert result.needs_confirmation is True

@pytest.mark.asyncio
async def test_detect_schedule_meeting_intent():
    """Test that the 'schedule_meeting' intent is correctly detected."""
    detector = IntentDetector()
    query = "Let's schedule a meeting for tomorrow at 10 AM."
    result = await detector.detect_intent(query)
    assert result.intent == Intent.SCHEDULE_MEETING
    assert result.confidence > 0.8
    assert result.needs_confirmation is True

@pytest.mark.asyncio
async def test_detect_general_conversation():
    """Test that a general query is classified as 'general_conversation'."""
    detector = IntentDetector()
    query = "What's the weather like today?"
    result = await detector.detect_intent(query)
    assert result.intent == Intent.GENERAL_CONVERSATION
    assert result.confidence <= 0.5
    assert result.needs_confirmation is False
