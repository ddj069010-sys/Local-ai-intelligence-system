"""
retriever.py — Query the vector store and return top-K relevant chunks.
"""

import logging
from .embedder import embed
from .store import get_store

logger = logging.getLogger(__name__)

TOP_K = 5
AUTO_TRIGGER_THRESHOLD = 0.55  # Minimum score to consider auto-triggering RAG


async def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Embed query and retrieve top_k most relevant chunks.
    Returns list of chunk dicts (with score).
    """
    store = get_store()

    if store.total_chunks == 0:
        return []

    vec = await embed(query)
    if vec is None:
        return []

    results = store.search(vec, top_k=top_k)
    logger.info(f"[RAG Retriever] Query='{query[:60]}' → {len(results)} chunks retrieved.")
    return results


async def should_auto_trigger(query: str) -> bool:
    """
    Heuristic to decide if RAG should automatically activate.
    Returns True if:
      - Query contains doc-related keywords, OR
      - Top retrieved chunk has a high similarity score
    """
    doc_keywords = [
        "in my document", "in the document", "in the file", "in the pdf",
        "according to", "based on", "from the report", "in my report",
        "in my notes", "what does the document", "what does it say",
        "the file says", "uploaded", "attachment", "my doc"
    ]
    lower_q = query.lower()
    for kw in doc_keywords:
        if kw in lower_q:
            return True

    # Score-based check
    results = await retrieve(query, top_k=1)
    if results and results[0].get("score", 0) >= AUTO_TRIGGER_THRESHOLD:
        return True

    return False
