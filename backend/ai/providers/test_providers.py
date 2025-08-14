"""
Provider System Test Script

This script tests the provider abstraction layer and configuration management.

Author: Cannasol Technologies
Date: 2025-08-13
Version: 1.0.0
"""

import asyncio
import logging
import os
from typing import Dict, Any

from . import (
    config_manager, get_primary_provider, get_all_providers, validate_providers,
    ProviderType, GROKProvider
)
from .base import Message, MessageRole

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_provider_configuration():
    """Test provider configuration and validation."""
    logger.info("Testing provider configuration...")
    
    # Get configuration summary
    summary = config_manager.get_configuration_summary()
    logger.info(f"Configuration summary: {summary}")
    
    # Validate configuration
    validation = validate_providers()
    logger.info(f"Validation results: {validation}")
    
    return validation["valid"]


async def test_provider_creation():
    """Test provider creation and initialization."""
    logger.info("Testing provider creation...")
    
    # Get all providers
    providers = get_all_providers()
    logger.info(f"Created providers: {list(providers.keys())}")
    
    # Test each provider initialization
    results = {}
    for provider_type, provider in providers.items():
        try:
            initialized = await provider.initialize()
            results[provider_type.value] = {
                "initialized": initialized,
                "capabilities": [cap.value for cap in provider.supported_capabilities],
                "provider_name": provider.provider_name
            }
            logger.info(f"{provider_type.value}: initialized={initialized}")
        except Exception as e:
            results[provider_type.value] = {"error": str(e)}
            logger.error(f"{provider_type.value} initialization failed: {e}")
    
    return results


async def test_grok_provider():
    """Test GROK provider specifically if available."""
    logger.info("Testing GROK provider...")
    
    # Check if GROK is available
    grok_provider = config_manager.create_provider(ProviderType.GROK)
    if not grok_provider:
        logger.warning("GROK provider not available")
        return {"available": False}
    
    try:
        # Initialize provider
        initialized = await grok_provider.initialize()
        if not initialized:
            return {"available": True, "initialized": False}
        
        # Test health check
        health = await grok_provider.health_check()
        logger.info(f"GROK health check: {health}")
        
        # Test basic generation (if API key is available)
        if os.environ.get("CUSTOM_OPENAI_API_KEY"):
            test_messages = [
                Message(role=MessageRole.USER, content="Hello, test message")
            ]
            
            response = await grok_provider.generate(test_messages)
            logger.info(f"GROK test response: {response.content[:100]}...")
            
            return {
                "available": True,
                "initialized": True,
                "health": health,
                "test_response": response.content[:100]
            }
        else:
            return {
                "available": True,
                "initialized": True,
                "health": health,
                "note": "No API key for full test"
            }
            
    except Exception as e:
        logger.error(f"GROK provider test failed: {e}")
        return {"available": True, "error": str(e)}


async def test_provider_fallback():
    """Test provider fallback mechanism."""
    logger.info("Testing provider fallback...")
    
    # Get available providers in priority order
    available = config_manager.get_available_providers()
    logger.info(f"Available providers in order: {[p.provider_type.value for p in available]}")
    
    # Test primary provider
    primary = get_primary_provider()
    if primary:
        logger.info(f"Primary provider: {type(primary).__name__}")
        return {"primary_provider": type(primary).__name__}
    else:
        logger.warning("No primary provider available")
        return {"primary_provider": None}


async def run_all_tests():
    """Run all provider tests."""
    logger.info("Starting provider system tests...")
    
    results = {
        "configuration": await test_provider_configuration(),
        "creation": await test_provider_creation(),
        "grok_specific": await test_grok_provider(),
        "fallback": await test_provider_fallback()
    }
    
    logger.info("Provider tests completed")
    return results


def main():
    """Main test function."""
    try:
        results = asyncio.run(run_all_tests())
        
        print("\n" + "="*60)
        print("PROVIDER SYSTEM TEST RESULTS")
        print("="*60)
        
        for test_name, result in results.items():
            print(f"\n{test_name.upper()}:")
            if isinstance(result, dict):
                for key, value in result.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {result}")
        
        # Overall status
        config_valid = results.get("configuration", False)
        has_providers = bool(results.get("creation", {}))
        
        print(f"\nOVERALL STATUS: {'✅ PASS' if config_valid and has_providers else '❌ FAIL'}")
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"\nTEST EXECUTION FAILED: {e}")


if __name__ == "__main__":
    main()
