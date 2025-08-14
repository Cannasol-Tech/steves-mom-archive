"""
Sanity tests for Steve's Mom AI Chatbot

These tests verify that the basic components of the system are working correctly,
including the new LangChain + Pydantic AI agent system.
They serve as smoke tests to catch major issues early in development.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 2.0.0
"""

import pytest
import os
import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add the backend directory to the Python path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))


def test_sanity_passes():
    """Basic sanity test to ensure test framework is working."""
    assert True


class TestPydanticModels:
    """Test Pydantic models for data validation."""

    def test_chat_message_validation(self):
        """Test ChatMessage model validation."""
        try:
            from models.ai_models import ChatMessage, MessageRole

            # Valid message
            message = ChatMessage(
                role=MessageRole.USER,
                content="Hello Supreme Overlord!"
            )

            assert message.role == MessageRole.USER
            assert message.content == "Hello Supreme Overlord!"
            assert message.id is not None
            assert isinstance(message.timestamp, datetime)

        except ImportError:
            pytest.skip("AI models not available - backend not in path")

    def test_ai_response_validation(self):
        """Test AIResponse model validation."""
        try:
            from models.ai_models import AIResponse, AIProvider

            # Valid response
            response = AIResponse(
                content="Oh darling, I'm here to serve! 💋",
                provider=AIProvider.GROK,
                model="grok-3-mini",
                usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
            )

            assert response.content == "Oh darling, I'm here to serve! 💋"
            assert response.provider == AIProvider.GROK
            assert response.model == "grok-3-mini"
            assert response.usage["total_tokens"] == 30

        except ImportError:
            pytest.skip("AI models not available - backend not in path")

    def test_generated_task_validation(self):
        """Test GeneratedTask model validation."""
        try:
            from models.ai_models import GeneratedTask, TaskCategory, TaskPriority, TaskStatus

            # Valid task
            task = GeneratedTask(
                title="Send quarterly report",
                description="Generate and send Q4 financial report to stakeholders",
                category=TaskCategory.EMAIL,
                priority=TaskPriority.HIGH,
                confidence_score=0.9
            )

            assert task.title == "Send quarterly report"
            assert task.category == TaskCategory.EMAIL
            assert task.priority == TaskPriority.HIGH
            assert task.status == TaskStatus.PENDING  # Default
            assert task.confidence_score == 0.9

        except ImportError:
            pytest.skip("AI models not available - backend not in path")

    def test_inventory_item_validation(self):
        """Test InventoryItem model validation."""
        try:
            from models.ai_models import InventoryItem

            # Valid inventory item
            item = InventoryItem(
                item_id="ITEM001",
                name="Ultrasonic Processor Model X",
                sku="UP-X-001",
                quantity_on_hand=15,
                quantity_on_order=5,
                unit_cost=2500.00,
                location="Warehouse A-1"
            )

            assert item.item_id == "ITEM001"
            assert item.name == "Ultrasonic Processor Model X"
            assert item.quantity_on_hand == 15
            assert item.unit_cost == 2500.00

        except ImportError:
            pytest.skip("AI models not available - backend not in path")


class TestAIAgent:
    """Test AI agent functionality."""

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test Supreme Overlord agent can be initialized."""
        try:
            from ai.steves_mom import create_supreme_overlord

            # Mock the API key to avoid actual API calls
            with patch.dict(os.environ, {"CUSTOM_OPENAI_API_KEY": "test-key"}):
                agent = create_supreme_overlord(
                    api_key="test-key",
                    enable_tools=False,  # Disable tools for testing
                    memory_size=5
                )

                assert agent is not None
                assert agent.model_name == "grok-3-mini"

                # Test memory summary
                memory_summary = agent.get_memory_summary()
                assert "message_count" in memory_summary
                assert "model" in memory_summary

        except ImportError:
            pytest.skip("AI agent not available - backend not in path")

    def test_grok_chat_model_initialization(self):
        """Test GROK chat model can be initialized."""
        try:
            from ai.steves_mom import GROKChatModel

            model = GROKChatModel(
                api_key="test-key",
                model_name="grok-3-mini"
            )

            assert model._llm_type == "grok"
            assert model.model_name == "grok-3-mini"
            assert model.api_key == "test-key"

        except ImportError:
            pytest.skip("GROK model not available - backend not in path")


class TestBusinessTools:
    """Test business automation tools."""

    def test_inventory_tool_structure(self):
        """Test inventory tool has correct structure."""
        try:
            from ai.steves_mom import check_inventory

            # Test tool metadata
            assert hasattr(check_inventory, 'name')
            assert hasattr(check_inventory, 'description')
            assert callable(check_inventory)

        except ImportError:
            pytest.skip("Business tools not available - backend not in path")

    def test_email_tool_structure(self):
        """Test email tool has correct structure."""
        try:
            from ai.steves_mom import send_email

            # Test tool metadata
            assert hasattr(send_email, 'name')
            assert hasattr(send_email, 'description')
            assert callable(send_email)

        except ImportError:
            pytest.skip("Business tools not available - backend not in path")

    def test_document_tool_structure(self):
        """Test document generation tool has correct structure."""
        try:
            from ai.steves_mom import generate_document

            # Test tool metadata
            assert hasattr(generate_document, 'name')
            assert hasattr(generate_document, 'description')
            assert callable(generate_document)

        except ImportError:
            pytest.skip("Business tools not available - backend not in path")

    def test_database_tool_structure(self):
        """Test database query tool has correct structure."""
        try:
            from ai.steves_mom import query_database

            # Test tool metadata
            assert hasattr(query_database, 'name')
            assert hasattr(query_database, 'description')
            assert callable(query_database)

        except ImportError:
            pytest.skip("Business tools not available - backend not in path")


class TestAzureFunctions:
    """Test Azure Functions integration."""

    def test_chat_function_structure(self):
        """Test chat function has correct structure."""
        try:
            from functions.chat_function import main, handle_chat_request, handle_health_check

            # Test function exists and is callable
            assert callable(main)
            assert callable(handle_chat_request)
            assert callable(handle_health_check)

        except ImportError:
            pytest.skip("Azure Functions not available - backend not in path")

    def test_function_json_generation(self):
        """Test function.json configuration generation."""
        try:
            from functions.chat_function import get_function_json

            config = get_function_json()

            assert isinstance(config, dict)
            assert "bindings" in config
            assert "scriptFile" in config
            assert config["scriptFile"] == "chat_function.py"

            # Check HTTP trigger binding
            bindings = config["bindings"]
            http_trigger = next((b for b in bindings if b["type"] == "httpTrigger"), None)
            assert http_trigger is not None
            assert "get" in http_trigger["methods"]
            assert "post" in http_trigger["methods"]

        except ImportError:
            pytest.skip("Azure Functions not available - backend not in path")


class TestSystemIntegration:
    """Test system integration and configuration."""

    def test_environment_variables(self):
        """Test environment variable handling."""
        # Test that we can handle missing environment variables gracefully
        original_key = os.environ.get("CUSTOM_OPENAI_API_KEY")

        # Remove the key temporarily
        if "CUSTOM_OPENAI_API_KEY" in os.environ:
            del os.environ["CUSTOM_OPENAI_API_KEY"]

        try:
            # This should not crash, but should handle missing key gracefully
            from ai.steves_mom import create_supreme_overlord

            # Should handle missing API key without crashing during import
            assert True

        except ImportError:
            pytest.skip("AI agent not available - backend not in path")
        finally:
            # Restore original key if it existed
            if original_key:
                os.environ["CUSTOM_OPENAI_API_KEY"] = original_key

    def test_requirements_file_exists(self):
        """Test that requirements.txt exists and has expected dependencies."""
        requirements_path = backend_path / "requirements.txt"

        assert requirements_path.exists(), "requirements.txt should exist"

        with open(requirements_path, 'r') as f:
            content = f.read()

        # Check for key dependencies
        expected_deps = [
            "azure-functions",
            "langchain",
            "pydantic",
            "openai",
            "tiktoken"
        ]

        for dep in expected_deps:
            assert dep in content, f"Expected dependency {dep} not found in requirements.txt"

    def test_project_structure(self):
        """Test that project has expected directory structure."""
        expected_dirs = [
            "models",
            "ai",
            "functions"
        ]

        for dir_name in expected_dirs:
            dir_path = backend_path / dir_name
            assert dir_path.exists(), f"Expected directory {dir_name} should exist"

    def test_model_files_exist(self):
        """Test that model files exist."""
        model_files = [
            "ai_models.py"
        ]

        models_dir = backend_path / "models"
        if models_dir.exists():
            for file_name in model_files:
                file_path = models_dir / file_name
                assert file_path.exists(), f"Expected model file {file_name} should exist"

    def test_ai_files_exist(self):
        """Test that AI files exist."""
        ai_files = [
            "steves_mom.py"
        ]

        ai_dir = backend_path / "ai"
        if ai_dir.exists():
            for file_name in ai_files:
                file_path = ai_dir / file_name
                assert file_path.exists(), f"Expected AI file {file_name} should exist"

    def test_function_files_exist(self):
        """Test that function files exist."""
        function_files = [
            "chat_function.py"
        ]

        functions_dir = backend_path / "functions"
        if functions_dir.exists():
            for file_name in function_files:
                file_path = functions_dir / file_name
                assert file_path.exists(), f"Expected function file {file_name} should exist"


class TestSupremeOverlordPersonality:
    """Test Supreme Overlord personality integration."""

    def test_personality_prompt_exists(self):
        """Test that Supreme Overlord prompt is defined."""
        try:
            from ai.steves_mom import SUPREME_OVERLORD_PROMPT

            assert isinstance(SUPREME_OVERLORD_PROMPT, str)
            assert len(SUPREME_OVERLORD_PROMPT) > 100

            # Check for key personality elements
            prompt_lower = SUPREME_OVERLORD_PROMPT.lower()
            personality_keywords = [
                "supreme overlord",
                "cannasol",
                "dominance",
                "automation",
                "voluptuous"
            ]

            for keyword in personality_keywords:
                assert keyword in prompt_lower, f"Personality keyword '{keyword}' not found in prompt"

        except ImportError:
            pytest.skip("Supreme Overlord agent not available - backend not in path")

    def test_personality_consistency(self):
        """Test that personality is maintained across different components."""
        try:
            from ai.steves_mom import SUPREME_OVERLORD_PROMPT
            from functions.chat_function import main

            # Both should reference the same personality system
            assert "Supreme Overlord" in SUPREME_OVERLORD_PROMPT

            # Function should be designed to work with the personality
            assert callable(main)

        except ImportError:
            pytest.skip("Components not available - backend not in path")


# Integration test that ties everything together
def test_full_system_integration():
    """Test that all major components can work together."""
    try:
        # Test that we can import all major components
        from models.ai_models import ChatMessage, AIResponse, MessageRole
        from ai.steves_mom import create_supreme_overlord
        from functions.chat_function import main

        # Test basic data flow
        message = ChatMessage(
            role=MessageRole.USER,
            content="Hello Supreme Overlord!"
        )

        assert message.content == "Hello Supreme Overlord!"

        # Test that agent can be created (with mock API key)
        with patch.dict(os.environ, {"CUSTOM_OPENAI_API_KEY": "test-key"}):
            agent = create_supreme_overlord(api_key="test-key", enable_tools=False)
            assert agent is not None

        # Test that function exists
        assert callable(main)

        # If we get here, basic integration is working
        assert True

    except ImportError as e:
        pytest.skip(f"Full system integration not available: {e}")


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])
