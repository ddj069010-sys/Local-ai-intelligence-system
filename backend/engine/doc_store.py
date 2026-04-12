"""
engine/doc_store.py
-------------------
In-memory document version store for iterative editing and undo/redo.
Each chat session maintains its own version history.
"""

import time
import uuid
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class DocVersion:
    """A single snapshot of a document."""
    __slots__ = ("version_id", "content", "doc_type", "tone", "action", "timestamp", "metadata")

    def __init__(self, content: str, doc_type: str = "report", tone: str = "professional",
                 action: str = "create", metadata: Optional[Dict] = None):
        self.version_id = str(uuid.uuid4())[:8]
        self.content = content
        self.doc_type = doc_type
        self.tone = tone
        self.action = action
        self.timestamp = time.time()
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "version_id": self.version_id,
            "doc_type": self.doc_type,
            "tone": self.tone,
            "action": self.action,
            "timestamp": self.timestamp,
            "content_length": len(self.content),
            "preview": self.content[:200] + "..." if len(self.content) > 200 else self.content,
        }


class DocVersionStore:
    """Per-session document version history with undo support."""

    def __init__(self):
        self._store: Dict[str, List[DocVersion]] = {}

    def save_version(self, chat_id: str, content: str, doc_type: str = "report",
                     tone: str = "professional", action: str = "create",
                     metadata: Optional[Dict] = None) -> DocVersion:
        """Save a new version and return it."""
        if chat_id not in self._store:
            self._store[chat_id] = []
        version = DocVersion(content, doc_type, tone, action, metadata)
        self._store[chat_id].append(version)
        logger.info(f"[DocStore] Saved v{len(self._store[chat_id])} for chat {chat_id} (action={action})")
        return version

    def get_latest(self, chat_id: str) -> Optional[DocVersion]:
        """Return the most recent version for a chat, or None."""
        versions = self._store.get(chat_id, [])
        return versions[-1] if versions else None

    def get_version(self, chat_id: str, index: int) -> Optional[DocVersion]:
        """Return a specific version by index (0-based)."""
        versions = self._store.get(chat_id, [])
        if 0 <= index < len(versions):
            return versions[index]
        return None

    def undo(self, chat_id: str) -> Optional[DocVersion]:
        """Remove the latest version and return the new latest (previous version)."""
        versions = self._store.get(chat_id, [])
        if len(versions) > 1:
            versions.pop()
            return versions[-1]
        return None

    def list_versions(self, chat_id: str) -> List[dict]:
        """Return metadata for all versions in a chat."""
        versions = self._store.get(chat_id, [])
        return [v.to_dict() for v in versions]

    def get_version_count(self, chat_id: str) -> int:
        return len(self._store.get(chat_id, []))

    def clear(self, chat_id: str):
        """Clear all versions for a chat session."""
        self._store.pop(chat_id, None)


# ─── Global Singleton ────────────────────────────────────────────────────────
doc_version_store = DocVersionStore()
