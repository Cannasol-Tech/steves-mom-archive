"""
Additional coverage for backend.functions.intent.intent_detector.IntentDetector

Covers:
- Case-insensitive matching
- Partial phrase matching
- Default GENERAL_CONVERSATION when no rule matches
- Ensure needs_confirmation True on positive match
"""

import pytest

from backend.functions.intent.intent_detector import IntentDetector
from backend.functions.intent.schemas import Intent


@pytest.mark.asyncio
async def test_case_insensitive_and_partial_matches():
    d = IntentDetector()

    # Case-insensitive
    res = await d.detect_intent("PLEASE Create A Task for me")
    assert res.intent == Intent.CREATE_TASK
    assert res.needs_confirmation is True
    assert res.confidence >= 0.8

    # Partial phrase within text
    res2 = await d.detect_intent("I would like to setup a meeting with the team next week")
    assert res2.intent == Intent.SCHEDULE_MEETING


@pytest.mark.asyncio
async def test_no_match_defaults_to_general():
    d = IntentDetector()
    res = await d.detect_intent("what's the weather like today?")
    assert res.intent == Intent.GENERAL_CONVERSATION
    assert res.confidence == 0.5
