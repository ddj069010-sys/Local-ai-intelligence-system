import chromadb
import json
import logging
import os
from chromadb.config import Settings

logger = logging.getLogger(__name__)

class AgenticMemoryStore:
    """
    Persistent Agentic Memory using ChromaDB.
    Enables long-term entity-relationship recall across sessions.
    """
    def __init__(self, db_path="./data/chroma_memory"):
        self.db_path = db_path
        os.makedirs(self.db_path, exist_ok=True)
        try:
            self.client = chromadb.PersistentClient(path=self.db_path, settings=Settings(allow_reset=True))
            self.collection = self.client.get_or_create_collection(
                name="agentic_entities",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"🧠 [CHROMADB] Persistent Agentic Memory initialized at {self.db_path}.")
        except Exception as e:
            logger.error(f"❌ [CHROMADB] Initialization failed: {e}")
            self.client = None
            self.collection = None

    def memorize_entity(self, entity_id: str, struct_data: dict, text_context: str):
        """Save a structured JSON entity to long-term memory."""
        if not self.collection: return False
        try:
            # We store the raw string context for embedding, and the dict in metadata
            self.collection.add(
                documents=[text_context],
                metadatas=[{"json_data": json.dumps(struct_data)}],
                ids=[entity_id]
            )
            logger.info(f"💾 [CHROMADB] Entity '{entity_id}' memorized permanently.")
            return True
        except Exception as e:
            logger.error(f"❌ [CHROMADB] Failed to memorize entity: {e}")
            return False

    def recall_entities(self, query: str, limit: int = 3) -> list:
        """Recall top entities related to the semantic query."""
        if not self.collection: return []
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            entities = []
            if results and 'metadatas' in results and results['metadatas']:
                for metadata_list in results['metadatas']:
                    for meta in metadata_list:
                        if 'json_data' in meta:
                            entities.append(json.loads(meta['json_data']))
            return entities
        except Exception as e:
            logger.error(f"❌ [CHROMADB] Recall failed: {e}")
            return []

agentic_memory = AgenticMemoryStore()
