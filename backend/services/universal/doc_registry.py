import re
import logging
import difflib
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class GlobalDocRegistry:
    def __init__(self):
        # Maps short_name -> doc_id
        self.name_map: Dict[str, str] = {}
        # Maps doc_id -> metadata (original_name, short_name, etc.)
        self.docs: Dict[str, Dict[str, Any]] = {}

    def generate_short_name(self, filename: str) -> str:
        """Generate a slug-like short name from a filename."""
        # Remove extension
        name = filename.rsplit('.', 1)[0]
        # Lowercase, remove spaces/special chars, keep alphanumeric
        short = re.sub(r'[^a-z0-9]', '', name.lower())
        # Enforce reasonable length
        return short[:15]

    def register(self, doc_id: str, original_name: str, chunks: Optional[List[str]] = None):
        """Register a document in the global registry."""
        short_name = self.generate_short_name(original_name)
        
        # Handle collisions (rare but possible)
        base_short = short_name
        counter = 1
        while short_name in self.name_map and self.name_map[short_name] != doc_id:
            short_name = f"{base_short[:12]}{counter}"
            counter += 1

        self.name_map[short_name] = doc_id
        self.docs[doc_id] = {
            "id": doc_id,
            "name": original_name,
            "short_name": short_name,
            "chunks": chunks or []
        }
        logger.info(f"Registered doc: {original_name} -> @{short_name}")
        return short_name

    def get_id_by_name(self, short_name: str) -> Optional[str]:
        # 1. Exact match
        if short_name in self.name_map:
            return self.name_map[short_name]
        
        # 2. Advanced Fuzzy Match (catches typos like @docmane -> @docname)
        close_matches = difflib.get_close_matches(short_name, self.name_map.keys(), n=1, cutoff=0.75)
        if close_matches:
            match = close_matches[0]
            logger.info(f"Fuzzy match resolved typos: @{short_name} -> @{match}")
            return self.name_map[match]
            
        return None

    def get_all_ids(self) -> List[str]:
        return list(self.docs.keys())

    def get_metadata(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return self.docs.get(doc_id)

# Singleton
doc_registry = GlobalDocRegistry()
