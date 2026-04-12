import httpx
import logging
from typing import List, Optional
from core.config import settings
from core.logger import logger

class EmbeddingService:
    """
    Wraps Ollama embedding API for vector generation.
    Used for FAISS and RAG tasks.
    """
    
    def __init__(self):
        self.logger = logger
        self.model = settings.EMBEDDING_MODEL

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generates a single vector for the given text."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.OLLAMA_API_URL}/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text
                    },
                    timeout=settings.REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    return response.json().get("embedding")
                else:
                    self.logger.error(f"❌ [EMBEDDINGS] API failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"❌ [EMBEDDINGS] Error: {e}")
            return None

    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a list of texts (Sequentially to keep it simple for now)."""
        embeddings = []
        for text in texts:
            emb = await self.get_embedding(text)
            if emb:
                embeddings.append(emb)
        return embeddings

# Singleton
embedding_service = EmbeddingService()
