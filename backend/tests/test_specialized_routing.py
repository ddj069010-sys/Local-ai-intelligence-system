import asyncio
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.model_manager import ModelManager

async def test_specialized_routing():
    print("🚀 Starting Specialized Routing Tests...")
    
    # Test cases: (query, expected_specialty)
    test_cases = [
        ("how to fix a python recursion error", "coding"),
        ("derive the proof for quantum entanglement", "reasoning"),
        ("what are the latest trends in renewable energy", "research"),
        ("hello, how are you today?", "general")
    ]
    
    # Mock call_ollama_json to simulate ModelManager behavior
    mock_responses = {
        "how to fix a python recursion error": {"specialty": "coding"},
        "derive the proof for quantum entanglement": {"specialty": "reasoning"},
        "what are the latest trends in renewable energy": {"specialty": "research"},
        "hello, how are you today?": {"specialty": "general"}
    }

    async def mock_call_ollama_json(prompt, model=None):
        for query, resp in mock_responses.items():
            if query in prompt:
                return resp
        return {"specialty": "general"}

    with patch("engine.utils.call_ollama_json", side_effect=mock_call_ollama_json):
        for query, expected in test_cases:
            print(f"\n🔍 Testing query: '{query}'")
            specialty = await ModelManager.get_specialized_intent(query)
            print(f"✅ Result: {specialty} (Expected: {expected})")
            assert specialty == expected, f"Failed: Got {specialty}, expected {expected}"

    print("\n✨ All Routing Tests Passed!")

async def test_model_chaining():
    print("\n⛓️ Starting Model Chaining Tests...")
    
    from services.orchestrator.orchestrator import orchestrator
    
    steps = [
        ("vision", "What is in this error screenshot?"),
        ("logic", "Why did this happen?"),
        ("code", "Provide a fix.")
    ]
    
    async def mock_call_ollama(prompt, model, system=None):
        return f"Mock response for {model} with system: {system[:30]}..."

    with patch("services.orchestrator.orchestrator.call_ollama", side_effect=mock_call_ollama):
        with patch("engine.model_manager.ModelManager.fetch_available_models", return_value=["llama3.1:8b", "qwen3-coder:30b", "deepseek-r1:32b"]):
            response = await orchestrator.run_sequenced_chain(steps, "User provided a bug screenshot.")
            print(f"✅ Chain Response: {response}")
            assert "Mock response" in response

    print("\n✨ Chaining Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_specialized_routing())
    asyncio.run(test_model_chaining())
