import asyncio
import logging
from typing import List, Dict, Any, Set
from .fetcher import Fetcher
from .extractor import Extractor
from .guard import Guard
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

class Crawler:
    def __init__(self, fetcher: Fetcher, extractor: Extractor, guard: Guard):
        self.fetcher = fetcher
        self.extractor = extractor
        self.guard = guard

    async def crawl(self, start_url: str, max_depth_level: int = 1) -> List[Dict[str, Any]]:
        """Perform multi-level crawling based on depth settings."""
        results = []
        queue = [(start_url, 1)] # (url, current_depth)
        visited = {start_url}
        parsed_start = urlparse(start_url)
        base_domain = f"{parsed_start.scheme}://{parsed_start.netloc}"

        # Depth mapping: Level 1 (1 page), Level 2 (3-5 pages), Level 3 (10-15 pages)
        max_pages = 1
        if max_depth_level == 2: max_pages = 5
        elif max_depth_level == 3: max_pages = 15

        headers = []

        while queue and len(results) < max_pages:
            url, depth = queue.pop(0)
            
            if not self.guard.can_fetch(url):
                continue

            html = await self.fetcher.fetch(url)
            if not html:
                continue
            
            data = self.extractor.extract(html, url)
            if data and data.get("full_text"):
                results.append(data)
                self.guard.mark_visited(url)

                # Collect links if we need more pages
                if len(results) < max_pages:
                    links = self.extractor.get_links(html, parsed_start.netloc)
                    for link in links:
                        full_link = urljoin(base_domain, link)
                        if full_link not in visited:
                            visited.add(full_link)
                            queue.append((full_link, depth + 1))
            
            # Rate limit
            await asyncio.sleep(0.5)

        return results
