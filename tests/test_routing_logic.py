import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from engine.model_manager import ModelManager

async def test_routing():
    print("🚀 Starting Intelligence Routing Verification...")
    
    test_cases = [
        {"q": "How do I implement a binary search tree in Python?", "expected_specialty": "coding", "desc": "Coding Intent"},
        {"q": "Prove that the square root of 2 is irrational.", "expected_specialty": "reasoning", "desc": "Reasoning Intent"},
        {"q": "Analyze this dataset for trends.", "expected_specialty": "research", "desc": "Research Intent"},
        {"q": "Hello assistant, how are you today?", "expected_specialty": "general", "desc": "General Chat"},
    ]
    
    for case in test_cases:
        specialty = await ModelManager.get_specialized_intent(case["q"])
        model, reason = await ModelManager.get_best_model("chat", case["q"], purpose=specialty)
        dna = ModelManager.get_model_system_prompt(model)
        
        print(f"\n[TEST] {case['desc']}")
        print(f"  Query: {case['q']}")
        print(f"  Detected Specialty: {specialty} (Expected: {case['expected_specialty']})")
        print(f"  Selected Model: {model}")
        print(f"  DNA applied: {'Yes' if dna else 'No'}")
        
        if specialty == case["expected_specialty"]:
            print("  ✅ PASS")
        else:
            print(f"  ⚠️ FAIL: Expected {case['expected_specialty']}, got {specialty}")

if __name__ == "__main__":
    asyncio.run(test_routing())
