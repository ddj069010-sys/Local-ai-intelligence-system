"""
services/link_processor/processors/web.py
- Refactored to use Hyper-Search Engine for deep intelligence extraction.
"""
import logging
import asyncio
from services.scraper.advanced_scraper import advanced_scraper

logger = logging.getLogger(__name__)

async def process_webpage(url: str) -> dict:
    """
    High-performance async webpage processing.
    Utilizes Hyper-Search (Parallel Fetch + Dynamic Rendering) to ensure 
    no data (like Stripe pricing) is missed.
    """
    try:
        logger.info(f"🕸️ [WEB PROCESSOR] Starting deep scavenge for: {url}")
        
        # We leverage the specialized hyper_scrape method 
        # (This handles the 2.5s timeout and Playwright fallback internally)
        results = await advanced_scraper.hyper_scrape([url], query="Extract core content and data")
        
        if not results:
            return {"error": "No results", "text": "", "source": url, "title": "Error"}
            
        if len(results) == 1 and "error" in results[0]:
            return {"error": results[0].get("error", "Scrape failed"), "text": "", "source": url, "title": "Error"}

        # 🌐 AGGREGATE ALL UNIVERSAL SUB-NODES (Root + Discovered Links)
        aggregated_text = ""
        for data in results:
            if not data.get("error"):
                node_source = data.get("source", url)
                node_text = data.get("text", "")
                aggregated_text += f"\n\n--- [MULTI-HOP NODE: {node_source}] ---\n{node_text}"

        return {
            "source": url,
            "title": results[0].get("title", "Universal Multi-Node Intelligence"),
            "text": aggregated_text.strip(),
            "error": None
        }
        
    except Exception as e:
        logger.error(f"❌ [WEB PROCESSOR] Failed to process {url}: {e}")
        return {"error": str(e), "text": "", "source": url}
