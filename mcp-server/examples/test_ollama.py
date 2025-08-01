#!/usr/bin/env python3
"""
Simple script to test if Ollama is running and the AI agent is accessible.
"""

import asyncio
import aiohttp
import json

async def test_ollama_connection():
    """Test if Ollama is running and accessible."""
    print("=== Ollama AI Agent Status Check ===\n")
    
    # Test 1: Check if Ollama server is running
    print("1. Checking if Ollama server is running...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/version") as response:
                if response.status == 200:
                    version_data = await response.json()
                    print(f"✅ Ollama server is running (version: {version_data.get('version', 'unknown')})")
                else:
                    print(f"❌ Ollama server responded with status: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama server: {e}")
        print("   Make sure Ollama is running with: ollama serve")
        return False
    
    # Test 2: Check if the required model is available
    print("\n2. Checking if required model is available...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags") as response:
                if response.status == 200:
                    models_data = await response.json()
                    models = [model['name'] for model in models_data.get('models', [])]
                    required_model = "qwen2.5-coder:1.5b"
                    
                    if required_model in models:
                        print(f"✅ Required model '{required_model}' is available")
                    else:
                        print(f"❌ Required model '{required_model}' not found")
                        print(f"   Available models: {', '.join(models)}")
                        print(f"   Install with: ollama pull {required_model}")
                        return False
                else:
                    print(f"❌ Cannot get model list: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False
    
    # Test 3: Test a simple AI generation
    print("\n3. Testing AI generation...")
    try:
        payload = {
            "model": "qwen2.5-coder:1.5b",
            "prompt": "Say 'Hello, AI is working!' in one sentence.",
            "system": "You are a helpful assistant. Keep responses brief.",
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 50
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    ai_response = result.get("response", "").strip()
                    print(f"✅ AI generation successful!")
                    print(f"   Response: {ai_response}")
                else:
                    error_text = await response.text()
                    print(f"❌ AI generation failed: {response.status} - {error_text}")
                    return False
    except Exception as e:
        print(f"❌ Error testing AI generation: {e}")
        return False
    
    print("\n🎉 All tests passed! Your AI agent is running correctly on Ollama.")
    return True

if __name__ == "__main__":
    asyncio.run(test_ollama_connection()) 