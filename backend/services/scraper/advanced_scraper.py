import httpx
import logging
import asyncio
import random
import trafilatura
import os
import tempfile
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from exa_py import Exa
from services.scraper.dynamic_scraper import dynamic_scraper

logger = logging.getLogger(__name__)

# GPT-Level Concurrency Constants
STRICT_TIMEOUT = 2.5  # Max seconds to wait for ANY website
MAX_BROWSER_TABS = 5  # Max Playwright tabs in 24GB RAM machine

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
]

class AdvancedScraper:
    """
    GPT-4 Style 'Hyper-Search' Engine.
    Uses Neural Snippets (Exa) + Simultaneous Playwright + Async Fetch.
    """

    def __init__(self, concurrency: int = MAX_BROWSER_TABS):
        self.concurrency = concurrency
        self.exa = None
        exa_key = os.getenv("EXA_API_KEY")
        if exa_key:
            self.exa = Exa(exa_key)
        
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1"
        }

    async def _fetch_with_timeout(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        """Fetch a single URL with strict GPT-speed timeouts."""
        try:
            headers = {**self.headers, "User-Agent": random.choice(USER_AGENTS)}
            # We enforce a hard 2.5s limit. If the site is slow, we drop it.
            resp = await client.get(url, headers=headers, timeout=STRICT_TIMEOUT, follow_redirects=True)
            if resp.status_code == 200:
                return resp.text
        except Exception as e:
            logger.warning(f"⚠️ [HYPER-SEARCH] Fast-fetch failed for {url} ({e}). Triggering Dynamic Fallback...")
        return None

    def _extract_content(self, html: str, url: str) -> Dict[str, Any]:
        """Precise content extraction using Trafilatura."""
        if not html:
            return {"error": "No content", "source": url}
        
        try:
            downloaded = trafilatura.extract(html, url=url, include_links=True, output_format="txt")
            metadata = trafilatura.extract_metadata(html)
            
            return {
                "text": downloaded or "",
                "title": metadata.title if metadata else "Snippet Result",
                "source": url,
                "author": metadata.author if metadata else None
            }
        except Exception as e:
            logger.error(f"❌ [HYPER-SEARCH] Extraction error: {e}")
            return {"error": str(e), "source": url}

    async def hyper_scrape(self, urls: List[str], query: str = "") -> List[Dict[str, Any]]:
        """
        [CORE ENGINE]: Executes parallel fetches for all URLs simultaneously.
        """
        # 1. Neural Snippet Layer (Exa) - Instant 0ms VRAM cost
        snippet_results = []
        if self.exa and query:
            try:
                # Exa returns direct text snippets from its neural index
                search_res = self.exa.search_and_contents(
                    query, type="neural", use_autoprompt=True, num_results=3, text=True
                )
                for res in search_res.results:
                    snippet_results.append({
                        "text": res.text,
                        "title": res.title,
                        "source": res.url,
                        "score": res.score
                    })
                logger.info(f"🧠 [HYPER-SEARCH] Neural layer retrieved {len(snippet_results)} snippets.")
            except Exception as e:
                logger.error(f"❌ [HYPER-SEARCH] Exa Layer failed: {e}")

        # 2. Deep Link Discovery (Level 5 Scavenger)
        # If the query is complex (pricing, specs), we discover sub-links to fetch simultaneously
        extra_urls = []
        if query and urls:
            logger.info("🕵️ [HYPER-SEARCH] Analyzing deep links for recursive intelligence...")
            limit_count = 2 if len(urls) >= 2 else len(urls)
            discovery_tasks = []
            for i in range(limit_count):
                discovery_tasks.append(global_url_analyser.discover_related_links(urls[i], query))
            
            discovery_results = await asyncio.gather(*discovery_tasks)
            for d_links in discovery_results:
                extra_urls.extend(d_links)
        
        combined_urls = list(urls) + list(extra_urls)
        all_target_urls = list(set(combined_urls))
        if len(all_target_urls) > 8:
            all_target_urls = all_target_urls[:8]
        
        # 3. Parallel Fast-Fetch Layer (httpx + trafilatura)
        results = []
        async with httpx.AsyncClient() as client:
            # We use a dynamic timeout: 2.5s base, 8s for high-priority domains
            high_value_domains = ["stripe.com", "aws.amazon.com", "microsoft.com", "apple.com", "nvidia.com"]
            
            async def smart_fetch(url):
                timeout = 8.0 if any(d in url for d in high_value_domains) else STRICT_TIMEOUT
                try:
                    resp = await client.get(url, headers={**self.headers, "User-Agent": random.choice(USER_AGENTS)}, timeout=timeout, follow_redirects=True)
                    if resp.status_code == 200: return resp.text
                except: pass
                
                # Fallback to Playwright if fast-fetch fails or if it's a high-value domain (JS-heavy)
                if any(d in url for d in high_value_domains) or "pricing" in url:
                    # We pass a temp dir for screenshot storage
                    with tempfile.TemporaryDirectory() as scrape_tmp:
                        rich_data = await dynamic_scraper.fetch_rich_context(url, scrape_tmp)
                        return rich_data.get("html") if rich_data else None
                return None

            html_payloads = await asyncio.gather(*[smart_fetch(u) for u in all_target_urls])
            
            for i, html in enumerate(html_payloads):
                if html:
                    results.append(self._extract_content(html, all_target_urls[i]))
        
        # Combine snippets and raw page results
        return snippet_results + results

    async def hyper_scrape_fast(self, query: str) -> List[Dict[str, Any]]:
        """
        [SPECULATIVE ENGINE]: Rapid scan across neural snippets and top 3 results.
        No deep discovery, optimized for ultra-low latency.
        """
        # 1. Neural Snippets (Instant)
        snippet_results = []
        if self.exa:
            try:
                search_res = self.exa.search_and_contents(
                    query, type="neural", use_autoprompt=True, num_results=3, text=True
                )
                for res in search_res.results:
                    snippet_results.append({
                        "text": res.text,
                        "title": res.title,
                        "source": res.url
                    })
            except: pass
            
        # 2. Fast Web Scarch (DuckDuckGo or direct)
        from duckduckgo_search import DDGS
        target_urls = []
        try:
             with DDGS() as ddgs:
                results = [r for r in ddgs.text(query, max_results=3)]
                target_urls = [r['href'] for r in results]
        except: pass
        
        # 3. Parallel Fetch top 3
        fetch_results = []
        if target_urls:
             async with httpx.AsyncClient() as client:
                html_payloads = await asyncio.gather(*[client.get(u, timeout=2.0, follow_redirects=True) for u in target_urls], return_exceptions=True)
                for i, resp in enumerate(html_payloads):
                    if not isinstance(resp, Exception) and resp.status_code == 200:
                        fetch_results.append(self._extract_content(resp.text, target_urls[i]))
        
        return snippet_results + fetch_results

class GlobalUrlAnalyser:
    """
    Identifies relevant sub-links within a page for multi-hop research.
    """
    
    @staticmethod
    def identify_deep_links(html: str, base_url: str, query: str, limit: int = 3) -> List[str]:
        """Parses HTML and scores links based on relevance to the user question."""
        if not html: return []
        
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        parsed_base = urlparse(base_url)
        domain = parsed_base.netloc
        q_terms = set(query.lower().split())
        
        # High value keywords for deep-diving
        priority_keywords = ["pricing", "fees", "international", "transaction", "limits", "documentation", "api"]
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(base_url, href)
            # Only same-domain links or direct pricing subdomains
            if urlparse(full_url).netloc == domain:
                score = sum(2 for term in q_terms if term in full_url.lower())
                score += sum(1 for kw in priority_keywords if kw in full_url.lower())
                
                # Prevent cycles and redundant root links
                if full_url.strip("/") != base_url.strip("/") and score > 0:
                    links.append((score, full_url))
        
        links.sort(key=lambda x: x[0], reverse=True)
        # Unique links only
        seen = set()
        unique_links = []
        for s, l in links:
            if l not in seen:
                seen.add(l)
                unique_links.append(l)
        
        return list(unique_links)[:limit]

    async def discover_related_links(self, url: str, query: str = "") -> List[str]:
        """Auto-discovery of relevant nodes by performing a fast-fetch on the root URL."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=3.0, follow_redirects=True)
                if resp.status_code == 200:
                    return self.identify_deep_links(resp.text, url, query)
        except: pass
        return []

advanced_scraper = AdvancedScraper()
global_url_analyser = GlobalUrlAnalyser()
