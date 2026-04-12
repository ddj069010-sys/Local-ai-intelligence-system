import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class KnowledgeGraph:
    """
    Implements a Persistent Neural Knowledge Graph for Entity-Relationship mapping.
    Links projects, technologies, and project-logic into a unified context.
    """
    
    def __init__(self, storage_path: str = "backend/data/knowledge_graph.json"):
        self.storage_path = storage_path
        self.graph = self._load_graph()

    def _load_graph(self) -> Dict[str, Any]:
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r") as f:
                return json.load(f)
        return {"entities": {}, "relations": []}

    def _save_graph(self):
        with open(self.storage_path, "w") as f:
            json.dump(self.graph, f, indent=2)

    def extract_and_link(self, text: str, source_id: str):
        """
        Extracts entities and links them to the source.
        [MOCK IMPLEMENTATION for now, will use LLM in future]
        """
        # Placeholder for NER logic
        entities = ["Project", "AI", "Python"] # Sample
        for ent in entities:
             if ent not in self.graph["entities"]:
                 self.graph["entities"][ent] = {"mentions": 0, "first_seen": str(datetime.now())}
             self.graph["entities"][ent]["mentions"] += 1
             self.graph["relations"].append({
                 "from": ent,
                 "to": source_id,
                 "type": "mentioned_in",
                 "timestamp": str(datetime.now())
             })
        self._save_graph()

    def get_related_context(self, entity: str) -> List[str]:
        """Finds all related context for a given entity."""
        related = []
        for rel in self.graph["relations"]:
            if rel["from"] == entity:
                related.append(f"Linked to {rel['to']} ({rel['type']})")
        return related

import os
knowledge_graph = KnowledgeGraph()
