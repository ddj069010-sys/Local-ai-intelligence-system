import httpx
import random
import asyncio
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
]

class Fetcher:
    def __init__(self, timeout: int = 15, retries: int = 2):
        self.timeout = timeout
        self.retries = retries
        self.client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
            headers={"Accept-Language": "en-US,en;q=0.9"}
        )

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://www.google.com/"
        }

    async def fetch(self, url: str) -> Optional[str]:
        """Fetch URL content with retries and rotating headers."""
        for attempt in range(self.retries + 1):
            try:
                # Small random delay to avoid detection
                await asyncio.sleep(random.uniform(0.2, 0.8))
                
                response = await self.client.get(url, headers=self._get_headers())
                response.raise_for_status()
                return response.text
            except Exception as e:
                logger.warning(f"Fetch failed for {url} (attempt {attempt+1}/{self.retries+1}): {e}")
                if attempt == self.retries:
                    return None
                await asyncio.sleep(1 * (attempt + 1)) # Exponential backoff
        return None

    async def close(self):
        await self.client.aclose()
