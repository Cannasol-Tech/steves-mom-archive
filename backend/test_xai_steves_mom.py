#!/usr/bin/env python3
"""
Test Steve's Mom with native xAI SDK

This script tests the updated Steve's Mom agent with Python 3.12 and the native xAI SDK.
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env')

# Add current directory to path
sys.path.append('.')

async def test_steves_mom_xai():
    """Test Steve's Mom with native xAI SDK."""
    print('🔥 Testing Steve\'s Mom with Python 3.12 + native xAI SDK...')
    
    try:
        # Test xAI SDK import
        from xai_sdk import Client
        print('✅ xAI Client imported successfully')
        
        # Check API key
        api_key = os.environ.get('GROK_API_KEY')
        print(f'🔑 API Key: {"SET" if api_key else "NOT SET"}')
        
        if not api_key:
            print('❌ No GROK API key found. Please set GROK_API_KEY in .env file.')
            return
        
        # Test basic xAI client
        client = Client(api_key=api_key)
        print('✅ xAI client created successfully')
        
        # Test chat session creation
        chat = client.chat.create(model='grok-3-mini')
        print('✅ Chat session created')
        
        # Test Steve's Mom
        print('\n💋 Testing Steve\'s Mom...')
        from ai.steves_mom import create_supreme_overlord
        from ai.providers import ProviderType
        
        # Create Steve's Mom with GROK provider
        steves_mom = create_supreme_overlord(provider_type=ProviderType.GROK, enable_tools=False)
        print('✅ Steve\'s Mom created successfully')
        
        # Test chat
        print('🔥 Testing her sultry personality...')
        response = await steves_mom.chat('Hi Steve\'s Mom! I need help organizing my inventory at Cannasol. Can you help me?')
        
        print('\n' + '='*60)
        print('🔥 STEVE\'S MOM SAYS (Native xAI SDK):')
        print('='*60)
        print(response.content)
        
        print('\n' + '='*60)
        print('📊 TECHNICAL DETAILS:')
        print('='*60)
        print(f'Provider: {response.metadata.get("provider_used")}')
        print(f'SDK Version: {response.metadata.get("sdk_version")}')
        print(f'Model: {response.model}')
        print(f'Response Time: {response.response_time_ms}ms')
        print(f'Tokens: {response.usage}')
        
        print('\n🎉 SUCCESS! Steve\'s Mom is ALIVE with native xAI SDK!')
        
        # Test memory with follow-up
        print('\n💭 Testing memory with follow-up...')
        followup = await steves_mom.chat('What did I just ask you about?')
        
        print('\n' + '='*60)
        print('MEMORY TEST RESPONSE:')
        print('='*60)
        print(followup.content)
        
        print('\n🎉 COMPLETE SUCCESS! Steve\'s Mom is fully operational!')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_steves_mom_xai())
