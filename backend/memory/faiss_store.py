import faiss
import numpy as np
import json
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from core.config import settings
from core.logger import logger

class FAISSStore:
    """
    Scalable vector storage using FAISS for high-speed semantic retrieval.
    Replaces the legacy JSON memory search.
    """
    
    def __init__(self, dimension: int = 768):
        self.logger = logger
        self.dimension = dimension
        self.index_path = settings.FAISS_INDEX_PATH
        self.metadata_path = settings.METADATA_PATH
        
        # Initialize Index
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(str(self.index_path))
                self.logger.info(f"📁 [MEMORY] Loaded FAISS index from {self.index_path}")
            except Exception as e:
                self.logger.error(f"❌ [MEMORY] Failed to load index: {e}")
                self.index = faiss.IndexFlatL2(dimension)
        else:
            self.index = faiss.IndexFlatL2(dimension)
            self.logger.info("🆕 [MEMORY] Created new FAISS index (FlatL2)")
            
        # Load Metadata
        self.metadata: List[Dict[str, Any]] = []
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
            except Exception:
                pass

    def save(self):
        """Persists the index and metadata to disk."""
        try:
            faiss.write_index(self.index, str(self.index_path))
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=4)
            self.logger.debug("💾 [MEMORY] Saved FAISS index and metadata.")
        except Exception as e:
            self.logger.error(f"❌ [MEMORY] Save failed: {e}")

    def add(self, vector: List[float], metadata: Dict[str, Any]):
        """Adds a new vector and its associated metadata."""
        v_np = np.array([vector]).astype('float32')
        self.index.add(v_np)
        self.metadata.append(metadata)
        self.save()

    def search(self, vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Returns the top K matches from the index."""
        if self.index.ntotal == 0:
            return []
            
        v_np = np.array([vector]).astype('float32')
        distances, indices = self.index.search(v_np, k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and idx < len(self.metadata):
                item = self.metadata[idx].copy()
                item['score'] = float(dist)
                results.append(item)
                
        return results

# Singleton (Default dimension for Nomic Embed text)
faiss_store = FAISSStore(dimension=768)
