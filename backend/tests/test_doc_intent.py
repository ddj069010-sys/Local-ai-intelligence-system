import asyncio
import json
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.orchestrator.orchestrator import orchestrator

async def test_intent(query):
    print(f"Testing query: '{query}'")
    res = await orchestrator.detect_intent(query)
    print(f"Result: {json.dumps(res, indent=2)}")
    return res

async def run_tests():
    queries = [
        "search doc about the revenue report",
        "what does the doc say about the project timeline?",
        "lookup doc for the meeting notes",
        "doc search: system architecture",
        "tell me more about the uploaded file"
    ]
    for q in queries:
        await test_intent(q)

if __name__ == "__main__":
    asyncio.run(run_tests())
