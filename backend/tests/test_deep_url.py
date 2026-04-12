import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.deep_url.pipeline import deep_url_pipeline

async def test_deep_url(url, query=""):
    print(f"\n--- Testing URL: {url} | Query: '{query}' ---")
    result = await deep_url_pipeline.run(url, query=query)
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Depth Used: {result['depth_used']}")
        print(f"Pages Crawled: {result['pages_crawled']}")
        print(f"Title: {result['title']}")
        print(f"Content Length: {len(result['full_text'])} chars")
        print(f"Sources: {', '.join(result['sources'])}")

async def run_tests():
    # Test Level 1 (Default)
    await test_deep_url("https://example.com", "what is this site?")
    
    # Test Level 2 (Detailed)
    await test_deep_url("https://www.wikipedia.org/", "give me a detailed explanation of wikipedia")
    
    # Test Level 3 (Deep)
    await test_deep_url("https://www.python.org/", "deep research on python features")

if __name__ == "__main__":
    asyncio.run(run_tests())
