"""
reranker.py — Lightweight chunk reranking.
Re-scores candidates via cosine similarity + keyword boost.
Returns top 4 final chunks for context injection.
"""

import re
import numpy as np
import logging
from .embedder import embed

logger = logging.getLogger(__name__)

FINAL_TOP_K = 4

class SemanticReranker:
    def __init__(self):
        try:
            from rerankers import Reranker
            logger.info("🧠 [RERANKER] Starting initialization of Neural Cross-Encoder...")
            self.model = Reranker("cross-encoder", model_type='cross-encoder')
            logger.info("✅ [RERANKER] Semantic Neural Cross-Encoder initialized.")
            self.is_active = True
        except Exception as e:
            logger.warning(f"⚠️ [RERANKER] Initialization failed: {e}. Will fallback to heuristic FAISS match.")
            self.is_active = False

    def rerank(self, query: str, docs: list[dict], top_k: int = FINAL_TOP_K) -> list[dict]:
        if not self.is_active or not docs:
            return _fallback_rerank(query, docs)
            
        try:
            texts = [d.get("text", "") for d in docs if "text" in d]
            if not texts: return docs[:top_k]
            
            results = self.model.rank(query=query, docs=texts)
            reranked_docs = []
            for r in results.top_k(top_k):
                for d in docs:
                    if d.get("text") == r.text:
                        d['final_score'] = float(r.score)
                        reranked_docs.append(d)
                        break
            return reranked_docs if len(reranked_docs) > 0 else docs[:top_k]
        except Exception as e:
            logger.error(f"❌ [RERANKER] Neural reranking failed: {e}")
            return _fallback_rerank(query, docs)

neural_reranker = SemanticReranker()

def rerank(query: str, chunks: list[dict]) -> list[dict]:
    return neural_reranker.rerank(query, chunks)

def _fallback_rerank(query: str, chunks: list[dict]) -> list[dict]:
    """
    Rerank retrieved chunks using:
    1. Cosine similarity of query vs chunk embedding
    2. Keyword overlap boost

    Returns top FINAL_TOP_K chunks sorted by final score.
    """
    if not chunks:
        return []

    query_vec = embed(query)
    query_terms = set(re.findall(r"\b\w{4,}\b", query.lower()))

    scored = []
    for chunk in chunks:
        base_score = chunk.get("score", 0.0)

        # Keyword boost
        chunk_terms = set(re.findall(r"\b\w{4,}\b", chunk["text"].lower()))
        overlap = len(query_terms & chunk_terms)
        keyword_boost = min(overlap * 0.04, 0.2)  # cap at 0.2

        # Cosine re-score if embedder is available
        cosine_score = base_score
        if query_vec is not None:
            chunk_vec = embed(chunk["text"])
            if chunk_vec is not None:
                cosine_score = float(np.dot(query_vec, chunk_vec))

        final_score = (cosine_score * 0.7) + (base_score * 0.2) + (keyword_boost * 0.1)
        scored.append({**chunk, "final_score": final_score})

    scored.sort(key=lambda x: x["final_score"], reverse=True)
    top = scored[:FINAL_TOP_K]
    logger.info(f"[RAG Reranker] {len(chunks)} → {len(top)} chunks after reranking.")
    return top
