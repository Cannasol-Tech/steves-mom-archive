"""
Test Script for Steve's Mom Agent

This script tests the updated Steve's Mom agent with the new provider system
and complete Supreme Overlord personality.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

import asyncio
import logging
import os
from typing import Any, Dict

from ai.providers import ProviderType, validate_providers
from ai.steves_mom import SupremeOverlordAgent, create_supreme_overlord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_steves_mom_initialization():
    """Test Steve's Mom agent initialization."""
    logger.info("Testing Steve's Mom initialization...")

    try:
        # Create Steve's Mom with default provider
        steves_mom = create_supreme_overlord(enable_tools=True, memory_size=5)

        # Get memory summary
        memory_summary = steves_mom.get_memory_summary()
        logger.info(f"Memory summary: {memory_summary}")

        # Get provider status
        provider_status = await steves_mom.get_provider_status()
        logger.info(f"Provider status: {provider_status}")

        return {
            "initialized": True,
            "memory_summary": memory_summary,
            "provider_status": provider_status,
        }

    except Exception as e:
        logger.error(f"Steve's Mom initialization failed: {e}")
        return {"initialized": False, "error": str(e)}


async def test_steves_mom_chat():
    """Test Steve's Mom chat functionality."""
    logger.info("Testing Steve's Mom chat...")

    try:
        # Create Steve's Mom
        steves_mom = create_supreme_overlord(
            enable_tools=False
        )  # Disable tools for simple test

        # Test basic chat
        test_message = "Hello Steve's Mom, how are you today?"

        response = await steves_mom.chat(
            message=test_message, user_id="test_user", session_id="test_session"
        )

        logger.info(f"Steve's Mom response: {response.content[:200]}...")

        return {
            "chat_successful": True,
            "response_length": len(response.content),
            "provider_used": response.metadata.get("provider_used"),
            "response_time_ms": response.response_time_ms,
            "personality_detected": "supreme" in response.content.lower()
            or "overlord" in response.content.lower(),
        }

    except Exception as e:
        logger.error(f"Steve's Mom chat test failed: {e}")
        return {"chat_successful": False, "error": str(e)}


async def test_steves_mom_memory():
    """Test Steve's Mom memory functionality."""
    logger.info("Testing Steve's Mom memory...")

    try:
        # Create Steve's Mom with small memory
        steves_mom = create_supreme_overlord(memory_size=2, enable_tools=False)

        # Have a conversation
        messages = [
            "My name is Stephen",
            "What's my name?",
            "I work at Cannasol Technologies",
            "Where do I work?",
        ]

        responses = []
        for i, msg in enumerate(messages):
            response = await steves_mom.chat(msg, user_id="memory_test")
            responses.append(
                {
                    "message": msg,
                    "response": (
                        response.content[:100] + "..."
                        if len(response.content) > 100
                        else response.content
                    ),
                    "memory_count": len(steves_mom.memory),
                }
            )
            logger.info(f"Message {i+1}: Memory has {len(steves_mom.memory)} items")

        return {
            "memory_test_successful": True,
            "conversation": responses,
            "final_memory_count": len(steves_mom.memory),
        }

    except Exception as e:
        logger.error(f"Steve's Mom memory test failed: {e}")
        return {"memory_test_successful": False, "error": str(e)}


async def test_provider_fallback():
    """Test provider fallback functionality."""
    logger.info("Testing provider fallback...")

    try:
        # Test with different provider types
        provider_results = {}

        for provider_type in [ProviderType.LOCAL, ProviderType.GROK]:
            try:
                steves_mom = create_supreme_overlord(
                    provider_type=provider_type, enable_tools=False
                )

                provider_status = await steves_mom.get_provider_status()
                provider_results[provider_type.value] = {
                    "available": provider_status.get("available", False),
                    "status": provider_status.get("status", "unknown"),
                }

            except Exception as e:
                provider_results[provider_type.value] = {
                    "available": False,
                    "error": str(e),
                }

        return {"fallback_test_successful": True, "provider_results": provider_results}

    except Exception as e:
        logger.error(f"Provider fallback test failed: {e}")
        return {"fallback_test_successful": False, "error": str(e)}


async def run_all_tests():
    """Run all Steve's Mom tests."""
    logger.info("Starting Steve's Mom comprehensive tests...")

    # First validate provider configuration
    provider_validation = validate_providers()
    logger.info(f"Provider validation: {provider_validation}")

    results = {
        "provider_validation": provider_validation,
        "initialization": await test_steves_mom_initialization(),
        "chat": await test_steves_mom_chat(),
        "memory": await test_steves_mom_memory(),
        "fallback": await test_provider_fallback(),
    }

    logger.info("Steve's Mom tests completed")
    return results


def main():
    """Main test function."""
    try:
        results = asyncio.run(run_all_tests())

        print("\n" + "=" * 60)
        print("STEVE'S MOM AGENT TEST RESULTS")
        print("=" * 60)

        for test_name, result in results.items():
            print(f"\n{test_name.upper().replace('_', ' ')}:")
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"  {key}: {value}")
            else:
                print(f"  {result}")

        # Overall status
        initialization_ok = results.get("initialization", {}).get("initialized", False)
        chat_ok = results.get("chat", {}).get("chat_successful", False)
        memory_ok = results.get("memory", {}).get("memory_test_successful", False)

        overall_success = initialization_ok and chat_ok and memory_ok

        print(f"\nOVERALL STATUS: {'✅ PASS' if overall_success else '❌ FAIL'}")

        if overall_success:
            print("\n🎉 Steve's Mom is ready to dominate your business operations!")
        else:
            print("\n⚠️  Steve's Mom needs some adjustments before full deployment.")

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\nTEST EXECUTION FAILED: {e}")


if __name__ == "__main__":
    main()
