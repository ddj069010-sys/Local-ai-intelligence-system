import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.model_manager import ModelManager

async def test_return_type():
    print("Testing ModelManager.get_best_model return type...")
    # Mock available models
    from unittest.mock import patch
    with patch("engine.model_manager.ModelManager.fetch_available_models", return_value=["llama3:8b", "qwen3-coder:30b"]):
        with patch("engine.model_manager.ModelManager.get_specialized_intent", return_value="coding"):
            result = await ModelManager.get_best_model("chat", "write some python code")
            print(f"Result: {result}")
            print(f"Type: {type(result)}")
            if isinstance(result, tuple):
                print(f"Elements: {[type(e) for e in result]}")

if __name__ == "__main__":
    asyncio.run(test_return_type())
