import logging
from typing import Dict, Any, Optional
from services.link_processor.processors.document import process_document_file
from engine.state import WORKSPACE, save_workspace
from datetime import datetime

logger = logging.getLogger(__name__)

async def process_document(file_path: str, filename: str, chat_id: Optional[str] = None) -> Dict[str, Any]:
    """Wraps existing RAG logic to process documents."""
    try:
        res = await process_document_file(file_path, filename)
        # 🚫 TAG-BASED MODE: NO automatic document ingestion/persistence
        # from .doc_registry import doc_registry
        # short_name = doc_registry.register(filename, filename, res.get("chunks", []))
        short_name = filename[:20] # Simple identifier for immediate UI response
        
        # 🚫 Storing in WORKSPACE disabled for auto-persistence avoidance
        # if chat_id and not res.get("error"):
        #     if chat_id not in WORKSPACE:
        #         WORKSPACE[chat_id] = {"docs": [], "chunks": [], "embeddings": [], "metadata": {}}
        #     WORKSPACE[chat_id]["chunks"].extend(res.get("chunks", []))
        #     WORKSPACE[chat_id]["embeddings"].extend(res.get("embeddings", []))
        #     if "docs_metadata" not in WORKSPACE[chat_id]:
        #         WORKSPACE[chat_id]["docs_metadata"] = []
        #     WORKSPACE[chat_id]["docs_metadata"].append({
        #         "name": filename,
        #         "short_name": short_name,
        #         "full_text": res.get("full_text", ""),
        #         "timestamp": datetime.now().isoformat()
        #     })
        #     save_workspace()
            
        return {
            "type": "document",
            "source": filename,
            "short_name": short_name,
            "text": res.get("text", ""),
            "title": res.get("title", filename),
            "format": res.get("format", "TXT"),
            "error": res.get("error")
        }
    except Exception as e:
        logger.error(f"Document processing error: {e}")
        return {"error": str(e), "type": "document"}
