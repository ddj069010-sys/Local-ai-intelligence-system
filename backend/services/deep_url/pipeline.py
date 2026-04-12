import logging
import asyncio
from typing import Dict, Any, List, Optional
from .fetcher import Fetcher
from .extractor import Extractor
from .guard import Guard
from .crawler import Crawler

logger = logging.getLogger(__name__)

class DeepURLPipeline:
    def __init__(self):
        self.fetcher = Fetcher()
        self.extractor = Extractor()
        
    async def run(self, url: str, depth: Optional[int] = None, query: str = "") -> Dict[str, Any]:
        """Run the full analysis pipeline."""
        # 1. Determine Depth
        if depth is None:
            depth = self._heuristics(query)
        
        guard = Guard(max_pages_per_domain=(5 if depth == 2 else 15 if depth == 3 else 1))
        crawler = Crawler(self.fetcher, self.extractor, guard)

        try:
            logger.info(f"Deep URL Analysis started for {url} (Depth {depth})")
            results = await crawler.crawl(url, depth)
            
            if not results:
                return {"error": "Failed to extract content from URL", "url": url}

            # 2. Merge & Deduplicate
            merged_content = self._merge(results)
            
            return {
                "url": url,
                "depth_used": depth,
                "pages_crawled": len(results),
                "title": results[0].get("title", "No Title"),
                "full_text": merged_content,
                "sources": [r["url"] for r in results]
            }

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return {"error": str(e), "url": url}

    def _heuristics(self, query: str) -> int:
        """Adaptive depth selection based on query intent."""
        query = query.lower()
        if any(w in query for w in ["deep", "full analysis", "research", "thorough"]):
            return 3
        if any(w in query for w in ["explain", "detailed", "guide", "how-to", "steps"]):
            return 2
        return 1

    def _merge(self, results: List[Dict[str, Any]]) -> str:
        """Merge multiple page results into a single context."""
        merged = []
        for i, res in enumerate(results):
            prefix = f"--- Page {i+1} : {res['url']} ---"
            merged.append(f"{prefix}\n{res['full_text']}")
        return "\n\n".join(merged)

    async def cleanup(self):
        await self.fetcher.close()

# Singleton instance
deep_url_pipeline = DeepURLPipeline()
