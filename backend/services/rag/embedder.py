"""
embedder.py — Local sentence-transformer embeddings.
Model: all-MiniLM-L6-v2 (22MB, fast, laptop-friendly).
Singleton model to avoid repeated loading.
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)

_MODEL = None
_MODEL_NAME = "all-MiniLM-L6-v2"


import asyncio
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=1)
_MODEL_LOCK = asyncio.Lock()

async def _get_model():
    global _MODEL
    async with _MODEL_LOCK:
        if _MODEL is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"[RAG] Loading embedding model: {_MODEL_NAME}...")
                # Load in a thread to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                _MODEL = await loop.run_in_executor(_executor, SentenceTransformer, _MODEL_NAME)
                logger.info("[RAG] Embedding model loaded successfully.")
            except ImportError:
                logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
                return None
            except Exception as e:
                logger.error(f"[RAG] Failed to load embedding model: {e}")
                return None
        return _MODEL


async def embed(text: str) -> np.ndarray | None:
    """Embed a single text string. Returns float32 numpy array or None on error."""
    model = await _get_model()
    if model is None:
        return None
    try:
        loop = asyncio.get_event_loop()
        # model.encode is CPU intensive, run in thread
        vec = await loop.run_in_executor(_executor, model.encode, text, True)
        return vec.astype("float32")
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        return None


async def embed_batch(texts: list[str]) -> list[np.ndarray]:
    """Embed a list of texts. Returns list of float32 arrays."""
    model = await _get_model()
    if model is None:
        return []
    try:
        loop = asyncio.get_event_loop()
        vecs = await loop.run_in_executor(
            _executor, 
            lambda: model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
        )
        return [v.astype("float32") for v in vecs]
    except Exception as e:
        logger.error(f"Batch embedding error: {e}")
        return []


def embedding_dim() -> int:
    """Return the embedding dimension of the model (hardcoded for speed)."""
    return 384
