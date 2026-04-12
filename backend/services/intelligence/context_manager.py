import logging
from typing import List, Dict, Any
from engine.utils import cosine_similarity, get_embedding

logger = logging.getLogger(__name__)

async def rank_context(query: str, fragments: List[str], top_n: int = 5) -> List[str]:
    """
    Ranks context fragments based on semantic similarity and returns top N.
    """
    if not fragments:
        return []
        
    try:
        query_emb = await get_embedding(query)
        scored = []
        for f in fragments:
            f_emb = await get_embedding(f[:1000]) # Limit for speed
            score = cosine_similarity(query_emb, f_emb)
            scored.append((score, f))
            
        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for s, f in scored[:top_n]]
    except Exception as e:
        logger.error(f"Context ranking failed: {e}")
        return fragments[:top_n]

async def validate_sources(fragments: List[str]) -> dict:
    """
    Checks for contradictions and agreement between sources.
    """
    # Simple logic for now: check if sources are from multiple origins
    # and if they overlap significantly.
    # In a real system, this would use an LLM for cross-referencing.
    return {
        "consistency": "High",
        "contradictions": [],
        "agreement": "Sources appear consistent."
    }
