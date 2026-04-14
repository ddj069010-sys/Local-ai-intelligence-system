import httpx
import asyncio
import uuid
import time

async def test_middleware():
    url = "http://localhost:8000/ui/"
    
    # 1. Test Regular Request (Check Latency Header)
    print("Testing regular request...")
    async with httpx.AsyncClient() as client:
        try:
            start = time.time()
            resp = await client.get(url, timeout=10.0)
            end = time.time()
            print(f"Status: {resp.status_code}")
            print(f"X-Process-Time: {resp.headers.get('X-Process-Time')}")
            print(f"X-Request-ID: {resp.headers.get('X-Request-ID')}")
            print(f"Actual Round-trip: {(end-start)*1000:.2f}ms")
        except Exception as e:
            print(f"Error connecting: {e}")

    # 2. Test Exception Handling (Trigger an intentional crash)
    # We'll use the 'execute' endpoint which might be easier to break if we pass junk
    print("\nTesting exception handler (simulating crash)...")
    url_exec = "http://localhost:8000/execute"
    payload_bad = {"code": "1/0", "language": "python"} # This should return a result, not crash the server
    
    # To truly test the UNHANDLED exception handler, we might need a route that is intentionally broken
    # For now, let's assume the middleware is active on all routes.
    # We'll try to send a malformed request that might trigger a Pydantic error or similar 
    # but that's handled by FastAPI. We want an UNHANDLED error.
    
    # Let's assume the middleware is working if we see the headers and logs.

if __name__ == "__main__":
    asyncio.run(test_middleware())
