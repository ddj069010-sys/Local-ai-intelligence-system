"""
controller/doc_routes.py
------------------------
API routes for document version management.
"""

import logging
from fastapi import APIRouter, HTTPException

from engine.doc_store import doc_version_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/doc", tags=["document-engine"])


@router.get("/versions/{chat_id}")
async def list_versions(chat_id: str):
    """List all document versions for a chat session."""
    versions = doc_version_store.list_versions(chat_id)
    return {
        "chat_id": chat_id,
        "count": len(versions),
        "versions": versions,
    }


@router.get("/versions/{chat_id}/{version_id}")
async def get_version(chat_id: str, version_id: str):
    """Get a specific document version by its ID."""
    versions = doc_version_store._store.get(chat_id, [])
    for v in versions:
        if v.version_id == version_id:
            return {
                "version_id": v.version_id,
                "doc_type": v.doc_type,
                "tone": v.tone,
                "action": v.action,
                "timestamp": v.timestamp,
                "content": v.content,
            }
    raise HTTPException(status_code=404, detail="Version not found")


@router.post("/versions/{chat_id}/undo")
async def undo_version(chat_id: str):
    """Revert to the previous document version."""
    result = doc_version_store.undo(chat_id)
    if result:
        return {
            "status": "reverted",
            "current_version": result.version_id,
            "content": result.content,
        }
    raise HTTPException(status_code=400, detail="No previous version to revert to")
