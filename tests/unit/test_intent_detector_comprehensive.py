"""
Comprehensive unit tests for backend.functions.intent.intent_detector

Tests intent detection functionality including:
- IntentDetector class initialization and configuration
- Intent detection with keyword matching
- Confidence scoring and entity extraction
- Edge cases and error handling
- Schema validation for Intent and IntentDetectionResult

Author: Cannasol Technologies
Date: 2025-01-04
Version: 1.0.0
"""

import pytest
import asyncio

import sys
from pathlib import Path

# Ensure backend package is importable
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.functions.intent.intent_detector import IntentDetector
from backend.functions.intent.schemas import Intent, IntentDetectionResult


class TestIntentDetector:
    """Test IntentDetector class functionality."""

    def test_intent_detector_initialization(self):
        """Test IntentDetector initialization."""
        detector = IntentDetector()

        assert detector is not None
        assert hasattr(detector, 'rules')
        assert isinstance(detector.rules, dict)

        # Check that rules contain expected intents
        assert Intent.CREATE_TASK in detector.rules
        assert Intent.SEND_EMAIL in detector.rules
        assert Intent.SCHEDULE_MEETING in detector.rules

    def test_intent_detector_rules_structure(self):
        """Test that rules are properly structured."""
        detector = IntentDetector()

        # Each rule should map to a list of keywords
        for intent, keywords in detector.rules.items():
            assert isinstance(intent, Intent)
            assert isinstance(keywords, list)
            assert len(keywords) > 0

            # Each keyword should be a string
            for keyword in keywords:
                assert isinstance(keyword, str)
                assert len(keyword) > 0

    @pytest.mark.asyncio
    async def test_detect_intent_create_task(self):
        """Test intent detection for CREATE_TASK."""
        detector = IntentDetector()

        test_queries = [
            "create a task for tomorrow",
            "I need to create a task",
            "new task: finish the report",
            "add a to-do item",
            "CREATE A TASK please"  # Test case insensitivity
        ]

        for query in test_queries:
            result = await detector.detect_intent(query)
            assert result.intent == Intent.CREATE_TASK
            assert result.confidence == 0.9
            assert result.entities == {}
            assert result.needs_confirmation is True

    @pytest.mark.asyncio
    async def test_detect_intent_send_email(self):
        """Test intent detection for SEND_EMAIL."""
        detector = IntentDetector()

        test_queries = [
            "send an email to John",
            "I want to send an email",
            "email to the team",
            "write an email about the meeting",
            "SEND AN EMAIL please"  # Test case insensitivity
        ]

        for query in test_queries:
            result = await detector.detect_intent(query)
            assert result.intent == Intent.SEND_EMAIL
            assert result.confidence == 0.9
            assert result.entities == {}
            assert result.needs_confirmation is True

    @pytest.mark.asyncio
    async def test_detect_intent_schedule_meeting(self):
        """Test intent detection for SCHEDULE_MEETING."""
        detector = IntentDetector()

        test_queries = [
            "schedule a meeting with the team",
            "setup a meeting for next week",
            "meeting with John tomorrow",
            "I need to schedule a meeting",
            "SCHEDULE A MEETING please"  # Test case insensitivity
        ]

        for query in test_queries:
            result = await detector.detect_intent(query)
            assert result.intent == Intent.SCHEDULE_MEETING
            assert result.confidence == 0.9
            assert result.entities == {}
            assert result.needs_confirmation is True

    @pytest.mark.asyncio
    async def test_detect_intent_general_conversation(self):
        """Test intent detection for general conversation."""
        detector = IntentDetector()

        test_queries = [
            "hello there",
            "how are you doing?",
            "what's the weather like?",
            "tell me a joke",
            "random conversation text",
            ""  # Empty string
        ]

        for query in test_queries:
            result = await detector.detect_intent(query)
            assert result.intent == Intent.GENERAL_CONVERSATION
            assert result.confidence == 0.5
            assert result.entities == {}
            assert result.needs_confirmation is False

    @pytest.mark.asyncio
    async def test_detect_intent_case_insensitivity(self):
        """Test that intent detection is case insensitive."""
        detector = IntentDetector()

        test_cases = [
            ("CREATE A TASK", Intent.CREATE_TASK),
            ("create a task", Intent.CREATE_TASK),
            ("Create A Task", Intent.CREATE_TASK),
            ("SEND AN EMAIL", Intent.SEND_EMAIL),
            ("send an email", Intent.SEND_EMAIL),
            ("Send An Email", Intent.SEND_EMAIL),
            ("SCHEDULE A MEETING", Intent.SCHEDULE_MEETING),
            ("schedule a meeting", Intent.SCHEDULE_MEETING),
            ("Schedule A Meeting", Intent.SCHEDULE_MEETING)
        ]

        for query, expected_intent in test_cases:
            result = await detector.detect_intent(query)
            assert result.intent == expected_intent

    @pytest.mark.asyncio
    async def test_detect_intent_partial_matches(self):
        """Test intent detection with partial keyword matches."""
        detector = IntentDetector()

        # Test queries that contain keywords as part of larger text
        test_cases = [
            ("I really need to create a task for the project", Intent.CREATE_TASK),
            ("Can you help me send an email to the client?", Intent.SEND_EMAIL),
            ("Let's schedule a meeting for next Tuesday", Intent.SCHEDULE_MEETING),
            ("The task creation process is complex", Intent.CREATE_TASK),
            ("Email to confirm the appointment", Intent.SEND_EMAIL)
        ]

        for query, expected_intent in test_cases:
            result = await detector.detect_intent(query)
            assert result.intent == expected_intent
            assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_detect_intent_first_match_wins(self):
        """Test that first matching intent is returned when multiple matches exist."""
        detector = IntentDetector()

        # Query that could match multiple intents
        # The order in the rules dict determines which one wins
        query = "create a task and send an email"

        result = await detector.detect_intent(query)
        # Should match the first intent found in the iteration order
        assert result.intent in [Intent.CREATE_TASK, Intent.SEND_EMAIL]
        assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_detect_intent_unicode_handling(self):
        """Test intent detection with Unicode characters."""
        detector = IntentDetector()

        test_queries = [
            "créate a task with émojis 🚀",
            "send an email with 中文 characters",
            "schedule a meeting with special chars: ñáéíóú"
        ]

        for query in test_queries:
            result = await detector.detect_intent(query)
            # Should still detect intents despite Unicode characters
            assert result.intent in [Intent.CREATE_TASK, Intent.SEND_EMAIL, Intent.SCHEDULE_MEETING]

    @pytest.mark.asyncio
    async def test_detect_intent_whitespace_handling(self):
        """Test intent detection with various whitespace scenarios."""
        detector = IntentDetector()

        test_queries = [
            "  create a task  ",  # Leading/trailing spaces
            "create\ta\ttask",   # Tabs
            "create\na\ntask",   # Newlines
            "create  a  task",   # Multiple spaces
        ]

        for query in test_queries:
            result = await detector.detect_intent(query)
            assert result.intent == Intent.CREATE_TASK


class TestIntentDetectionResult:
    """Test IntentDetectionResult schema functionality."""

    def test_intent_detection_result_creation(self):
        """Test creating IntentDetectionResult instances."""
        result = IntentDetectionResult(
            intent=Intent.CREATE_TASK,
            confidence=0.9,
            entities={"task_name": "finish report"},
            needs_confirmation=True
        )

        assert result.intent == Intent.CREATE_TASK
        assert result.confidence == 0.9
        assert result.entities == {"task_name": "finish report"}
        assert result.needs_confirmation is True

    def test_intent_detection_result_defaults(self):
        """Test IntentDetectionResult with default values."""
        result = IntentDetectionResult(
            intent=Intent.GENERAL_CONVERSATION,
            confidence=0.5
        )

        assert result.intent == Intent.GENERAL_CONVERSATION
        assert result.confidence == 0.5
        assert result.entities == {}  # Default empty dict
        assert result.needs_confirmation is False  # Default False

    def test_intent_detection_result_confidence_validation(self):
        """Test confidence field validation."""
        # Valid confidence values (0.0 to 1.0)
        valid_confidences = [0.0, 0.1, 0.5, 0.9, 1.0]

        for confidence in valid_confidences:
            result = IntentDetectionResult(
                intent=Intent.CREATE_TASK,
                confidence=confidence
            )
            assert result.confidence == confidence

        # Invalid confidence values should raise ValidationError
        from pydantic import ValidationError

        invalid_confidences = [-0.1, 1.1, 2.0, -1.0]

        for confidence in invalid_confidences:
            with pytest.raises(ValidationError):
                IntentDetectionResult(
                    intent=Intent.CREATE_TASK,
                    confidence=confidence
                )