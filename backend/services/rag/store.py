"""
store.py — FAISS-backed local vector store.
Persists index + metadata JSON to /data/rag_index/.
Supports add, save, load, list_files, delete_file.
"""

import os
import json
import logging
import numpy as np

logger = logging.getLogger(__name__)

RAG_INDEX_DIR = os.path.join(os.path.dirname(__file__), "../../data/rag_index")
INDEX_FILE = os.path.join(RAG_INDEX_DIR, "faiss.index")
META_FILE = os.path.join(RAG_INDEX_DIR, "metadata.json")


class RAGStore:
    def __init__(self):
        self._index = None
        self._meta: list[dict] = []
        os.makedirs(RAG_INDEX_DIR, exist_ok=True)

    def _get_index(self, dim: int = 384):
        if self._index is None:
            try:
                import faiss
                self._index = faiss.IndexFlatL2(dim)
            except ImportError:
                logger.error("faiss-cpu not installed. Run: pip install faiss-cpu")
        return self._index

    def add_chunks(self, chunks: list[dict], embeddings: list[np.ndarray]):
        """Add chunk embeddings + metadata to the store."""
        if not chunks or not embeddings:
            return

        dim = embeddings[0].shape[0]
        index = self._get_index(dim)
        if index is None:
            return

        matrix = np.vstack(embeddings).astype("float32")
        index.add(matrix)

        for chunk in chunks:
            self._meta.append(chunk)

        self.save()
        logger.info(f"[RAG Store] Added {len(chunks)} chunks. Total: {len(self._meta)}")

    def save(self):
        """Persist FAISS index and metadata JSON to disk."""
        try:
            import faiss
            if self._index and self._index.ntotal > 0:
                faiss.write_index(self._index, INDEX_FILE)
            with open(META_FILE, "w") as f:
                json.dump(self._meta, f)
        except Exception as e:
            logger.error(f"[RAG Store] Save error: {e}")

    def load(self):
        """Load index and metadata from disk only if changed."""
        try:
            import faiss
            # Check modification time to avoid redundant loads
            mtime = 0
            if os.path.exists(INDEX_FILE):
                mtime = os.path.getmtime(INDEX_FILE)
            
            if mtime <= self._last_loaded and self._index is not None:
                return # Already up to date

            if os.path.exists(INDEX_FILE):
                self._index = faiss.read_index(INDEX_FILE)
                logger.info(f"[RAG Store] Loaded FAISS index with {self._index.ntotal} vectors.")
            
            if os.path.exists(META_FILE):
                with open(META_FILE, "r") as f:
                    self._meta = json.load(f)
            
            self._last_loaded = mtime
        except Exception as e:
            logger.error(f"[RAG Store] Load error: {e}")

    def search(self, query_vec: np.ndarray, top_k: int = 5) -> list[dict]:
        """Search for top-K nearest chunks. Returns list of chunk dicts with score."""
        index = self._get_index()
        if index is None or index.ntotal == 0:
            return []

        self.load()  # Ensure fresh data

        q = query_vec.reshape(1, -1).astype("float32")
        k = min(top_k, index.ntotal)
        distances, indices = index.search(q, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._meta):
                continue
            chunk = dict(self._meta[idx])
            chunk["score"] = float(1 / (1 + dist))  # Convert L2 distance to a 0-1 score
            results.append(chunk)

        return results

    def list_files(self) -> list[str]:
        """Return a deduplicated list of indexed source filenames."""
        self.load()
        return list({m["source"] for m in self._meta})

    async def delete_file(self, filename: str) -> bool:
        """Remove all chunks from a given source file and rebuild the index."""
        self.load()
        original_count = len(self._meta)
        self._meta = [m for m in self._meta if m["source"] != filename]

        if len(self._meta) == original_count:
            return False  # File not found

        # Rebuild index from scratch (necessary for FAISS flat index)
        self._index = None
        if self._meta:
            from services.rag.embedder import embed_batch, embedding_dim
            texts = [m["text"] for m in self._meta]
            vecs = await embed_batch(texts)
            if vecs:
                import faiss
                dim = embedding_dim()
                self._index = faiss.IndexFlatL2(dim)
                matrix = np.vstack(vecs).astype("float32")
                self._index.add(matrix)

        self.save()
        logger.info(f"[RAG Store] Deleted file '{filename}'. Remaining chunks: {len(self._meta)}")
        return True

    @property
    def total_chunks(self) -> int:
        return len(self._meta)


# Singleton
_store = RAGStore()


def get_store() -> RAGStore:
    return _store
