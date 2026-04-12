import re
import math
import asyncio
import numpy as np
import httpx
import logging
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import json
from engine.config import OLLAMA_API_URL

# Set up logging
logger = logging.getLogger(__name__)

# Memory integration: disk-based web cache (L2, behind in-memory L1)
try:
    from memory.manager import get_cached, cache_web as _cache_web_disk
    _DISK_CACHE_ENABLED = True
except ImportError:
    _DISK_CACHE_ENABLED = False
    def get_cached(_): return ""
    def _cache_web_disk(u, c): pass

BAD_PATTERNS = [
    "Special:", "Help:", "Portal:",
    "login", "signup", "edit", "history"
]

# Simple in-memory cache for a single session
class SessionCache:
    def __init__(self):
        self.pages = {}  # url -> extracted text

    def get(self, url):
        return self.pages.get(url)

    def set(self, url, text):
        self.pages[url] = text

    def clear(self):
        self.pages.clear()

session_cache = SessionCache()

def score_source(url: str) -> int:
    url_lower = url.lower()
    if any(bp.lower() in url_lower for bp in BAD_PATTERNS):
        return -1 # Filter out
    
    if ".gov" in url_lower or ".edu" in url_lower:
        return 5
    if any(news in url_lower for news in ["reuters.com", "bbc.com", "nytimes.com", "cnn.com", "theguardian.com", "apnews.com"]):
        return 4
    if "wikipedia.org" in url_lower:
        return 3
    return 1

# Part 1: Standardized headers for all web requests
_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def extract_cleaned_text(url: str, force_fetch=False) -> str:
    """Fetches URL, strips nav/footer/ads, returning clean visible paragraphs."""
    # L1: in-memory cache
    if not force_fetch and session_cache.get(url):
        return session_cache.get(url)

    # L2: disk cache (Part 6)
    if not force_fetch and _DISK_CACHE_ENABLED:
        cached = get_cached(url)
        if cached:
            session_cache.set(url, cached)  # promote to L1
            logger.debug(f"[cache hit] {url}")
            return cached

    try:
        # Part 1: Use proper headers + timeout=10
        resp = requests.get(url, headers=_REQUEST_HEADERS, timeout=10)

        # Part 1: Skip non-200 responses
        if resp.status_code != 200:
            logger.warning(f"Skipping {url}: HTTP {resp.status_code}")
            return ""

        # Part 2: Wrap extraction in try/except so one bad URL never breaks the loop
        try:
            soup = BeautifulSoup(resp.content, "html.parser")

            # Part 2: Remove all non-content tags (expanded list)
            for tag in soup(["script", "style", "nav", "footer", "header",
                             "aside", "form", "iframe", "noscript", "figure",
                             "figcaption", "button", "input", "select"]):
                tag.decompose()

            paragraphs = []
            for p in soup.find_all("p"):
                text = p.get_text(separator=" ", strip=True)
                # Part 2: Raised min length 40 → 60 for higher quality chunks
                if len(text) > 60:
                    paragraphs.append(text)

            # Fallback: extract visible text from body if no <p> tags found
            if not paragraphs:
                body = soup.find("body")
                raw = body.get_text(separator=" ", strip=True) if body else soup.get_text(separator=" ", strip=True)
                text = str(re.sub(r'\s+', ' ', raw)).strip()
            else:
                text = " ".join(paragraphs)

            # Part 2: Collapse all whitespace
            text = str(re.sub(r'\s+', ' ', text)).strip()

            session_cache.set(url, text)
            # Part 6: Persist to disk cache
            if _DISK_CACHE_ENABLED:
                _cache_web_disk(url, text)
            return text

        except Exception as extraction_err:
            # Part 2: Skip URL if extraction fails — never crash the loop
            logger.error(f"Extraction failed for {url}: {extraction_err}")
            return ""

    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return ""

def chunk_text(text: str, chunk_size=800, overlap=100) -> list[str]:
    """Splits text into sliding windows of words."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

async def get_embedding(text: str) -> list[float]:
    """Calls Ollama to get the embedding vector for the given text."""
    payload = {"model": "nomic-embed-text:latest", "prompt": text}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{OLLAMA_API_URL}/embeddings", json=payload, timeout=60.0)
            resp.raise_for_status()
            data = resp.json()
            return data.get("embedding", [])
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return []

def cosine_similarity(vec_a, vec_b):
    if not vec_a or not vec_b:
        return 0.0
    a = np.array(vec_a)
    b = np.array(vec_b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return np.dot(a, b) / (norm_a * norm_b)

def cluster_and_rerank(chunks: list, embeddings: list, query_emb: list, query_text: str = "", top_n: int = 5) -> list:
    """
    Groups chunks into clusters based on semantic similarity, 
    then reranks results to ensure diversity and relevance.
    FALLBACK: If embeddings fail, uses keyword overlap scoring.
    """
    if not chunks:
        return []
    
    # --- FALLBACK: KEYWORD MATCHING (if embeddings unavailable) ---
    if not query_emb or not embeddings:
        logger.info("Embeddings unavailable, falling back to keyword matching.")
        from re import sub
        clean_query = sub(r'[^\w\s]', '', query_text.lower())
        query_words = set(clean_query.split())
        
        fallback_results = []
        for chunk in chunks:
            clean_chunk = sub(r'[^\w\s]', '', chunk.lower())
            chunk_words = set(clean_chunk.split())
            intersection = query_words.intersection(chunk_words)
            score = len(intersection) / len(query_words) if query_words else 0
            fallback_results.append({"score": score, "text": chunk})
        
        fallback_results.sort(key=lambda x: x["score"], reverse=True)
        return [c["text"] for c in fallback_results[:top_n]]

    # --- ADVANCED SEMANTIC SEARCH ---
    # 1. Calculate similarity to query for all chunks
    scored_chunks = []
    for i, emb in enumerate(embeddings):
        sim = cosine_similarity(query_emb, emb)
        scored_chunks.append({"text": chunks[i], "emb": emb, "score": sim})
    
    # 2. Sort by initial similarity
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    
    # 3. Simple Clustering-based Reranking (Centroid approach)
    # We pick the top result, then penalize items too similar to what's already picked (MMR-lite)
    selected_texts = []
    candidates_list = []
    for i in range(min(len(scored_chunks), 15)):
        # RELEVANCE CLAMPING: Discard facts that are less than 50% relevant
        if scored_chunks[i]["score"] >= 0.50:
            candidates_list.append(scored_chunks[i])
    
    while candidates_list and len(selected_texts) < top_n:
        best_cand = candidates_list.pop(0)
        selected_texts.append(str(best_cand["text"]))
        
        # Penalize remaining candidates similar to the one we just picked
        for cand in candidates_list:
            redundancy = cosine_similarity(best_cand["emb"], cand["emb"])
            if redundancy > 0.85: # High redundancy threshold
                cand["score"] -= 0.2 # Penalty
        
        candidates_list.sort(key=lambda x: x["score"], reverse=True)
        
    return selected_texts

# --- REFACTORED CORE FUNCTIONS ---

_GLOBAL_SYSTEM_PROMPT = """
## CORE OUTPUT BEHAVIOR:

1. NATURAL CHAT EXPERIENCE:
   - Respond conversationally and naturally, similar to ChatGPT.
   - Do NOT force responses into structured sections, tables, or step-by-step formats unless explicitly requested.
   - Speak directly to the human without robotic filler.

2. CODE GUIDELINES:
   - If providing code, always use proper fenced code blocks (```language).
"""

async def call_ollama(prompt: str, model: str, system: str = None, format: str = None) -> str:
    final_system = _GLOBAL_SYSTEM_PROMPT
    if system:
        final_system = f"{_GLOBAL_SYSTEM_PROMPT}\n\n### STRICT MODE-SPECIFIC RULES (PRIORITIZE THESE):\n{system}"
    
    payload = {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}, "system": final_system, "keep_alive": -1}
    if format: payload["format"] = format
    
    max_retries = 2
    for attempt in range(max_retries + 1):
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{OLLAMA_API_URL}/generate", json=payload, timeout=120.0)
                if resp.status_code == 500 and attempt < max_retries:
                    logger.warning(f"Ollama returned 500 (attempt {attempt+1}/{max_retries+1}). Retrying...")
                    await asyncio.sleep(1)
                    continue
                resp.raise_for_status()
                return str(resp.json().get("response", "")).strip()
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"Ollama call failed after {max_retries+1} attempts: {e}")
                    return f"Error: Ollama model '{model}' failed with status {getattr(e, 'response', {}).status_code if hasattr(e, 'response') else 'unknown'}. Detail: {str(e)}"
                logger.warning(f"Ollama attempt {attempt+1} failed: {e}. Retrying...")
                await asyncio.sleep(1)
    return ""

async def call_ollama_stream(prompt: str, model: str, system: str = None, format: str = None, yield_dicts: bool = False):
    """Async generator yielding chunks of tokens from Ollama."""
    final_system = _GLOBAL_SYSTEM_PROMPT
    if system:
        final_system = f"{_GLOBAL_SYSTEM_PROMPT}\n\n### STRICT MODE-SPECIFIC RULES (PRIORITIZE THESE):\n{system}"
    
    payload = {"model": model.lower(), "prompt": prompt, "stream": True, "options": {"temperature": 0.2}, "system": final_system, "keep_alive": -1}
    if format: payload["format"] = format
    
    in_thought = False
    buffer = ""
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream("POST", f"{OLLAMA_API_URL}/generate", json=payload) as resp:
                if resp.status_code != 200:
                    error_msg = "⚠️ API Error: Unable to connect to local brain."
                    yield {"type": "message", "text": error_msg} if yield_dicts else error_msg
                    return
                async for line in resp.aiter_lines():
                    if not line: continue
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            chunk = data["response"]
                            if not yield_dicts:
                                yield chunk
                                continue
                            
                            buffer += chunk
                            while True:
                                if not in_thought:
                                    if "<think>" in buffer:
                                        start_idx = buffer.find("<think>")
                                        before = buffer[:start_idx]
                                        if before:
                                            yield {"type": "message", "text": before}
                                        in_thought = True
                                        buffer = buffer[start_idx + len("<think>"):]
                                    else:
                                        to_yield = buffer[:-7] if len(buffer) > 7 else ""
                                        if to_yield:
                                            yield {"type": "message", "text": to_yield}
                                            buffer = buffer[-7:]
                                        break
                                else:
                                    if "</think>" in buffer:
                                        end_idx = buffer.find("</think>")
                                        thought_content = buffer[:end_idx]
                                        if thought_content:
                                            yield {"type": "thought", "text": thought_content}
                                        in_thought = False
                                        buffer = buffer[end_idx + len("</think>"):]
                                    else:
                                        to_yield = buffer[:-8] if len(buffer) > 8 else ""
                                        if to_yield:
                                            yield {"type": "thought", "text": to_yield}
                                            buffer = buffer[-8:]
                                        break
                        if data.get("done") and yield_dicts:
                            if buffer:
                                yield {"type": "thought" if in_thought else "message", "text": buffer}
                            break
                    except Exception: continue
        except Exception as e:
            logger.error(f"Ollama stream failed: {e}")
            msg = "⚠️ Connection dropped. Retrying with thought buffer..."
            yield {"type": "message", "text": msg} if yield_dicts else msg

def search_web_scored(queries: list) -> list:
    ddgs = DDGS()
    scored_results = []
    seen = set()
    for q in queries:
        try:
            for r in ddgs.text(q, max_results=5):
                href = r['href']
                if href not in seen:
                    seen.add(href)
                    score = score_source(href)
                    if score > 0:
                        scored_results.append((score, r))
        except Exception as e:
            logger.error(f"DDG error for {q}: {e}")
            
    scored_results.sort(key=lambda x: x[0], reverse=True)
    final_urls = []
    domains = set()
    for s, r in scored_results:
        href = r['href']
        domain = href.split('/')[2] if '//' in href else href
        if len(domains) < 6 and len(final_urls) < 10:
            domains.add(domain)
            final_urls.append(href)
    return final_urls

async def call_ollama_json(prompt: str, model: str = "gemma3:4b", system: str = "") -> dict:
    """Calls Ollama and enforces JSON output."""
    try:
        url = f"{OLLAMA_API_URL}/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system + "\nOutput MUST be valid JSON only. No markdown formatting, no preamble.",
            "stream": False,
            "format": "json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                return json.loads(result.get("response", "{}"))
    except Exception as e:
        logger.error(f"Ollama JSON Error: {e}")
    return {}
