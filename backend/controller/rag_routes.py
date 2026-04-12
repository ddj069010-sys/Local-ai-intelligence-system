"""
rag_routes.py — FastAPI routes for RAG document management.
- POST /rag/upload    → ingest a document
- GET  /rag/files     → list indexed files
- DELETE /rag/files/{filename} → remove a file
- POST /rag/query     → debug query endpoint
"""

import os
import shutil
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../data/rag_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a document into the RAG index."""
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    save_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save error: {e}")

    # Non-blocking ingestion
    try:
        from services.rag.pipeline import async_ingest_file
        result = await async_ingest_file(save_path)
        return result
    except Exception as e:
        logger.error(f"[RAG Upload] Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion error: {e}")


@router.get("/files")
async def list_indexed_files():
    """Return a list of all indexed document filenames."""
    try:
        from services.rag.pipeline import get_indexed_files
        files = get_indexed_files()
        return {"files": files, "count": len(files)}
    except Exception as e:
        logger.error(f"[RAG Files] Error listing files: {e}")
        return {"files": [], "count": 0}


@router.delete("/files/{filename}")
async def delete_indexed_file(filename: str):
    """Remove a file from the RAG index."""
    try:
        from services.rag.pipeline import delete_indexed_file
        success = delete_indexed_file(filename)

        # Also remove upload
        upload_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(upload_path):
            os.remove(upload_path)

        return {"status": "deleted" if success else "not_found", "file": filename}
    except Exception as e:
        logger.error(f"[RAG Delete] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class RAGQueryRequest(BaseModel):
    question: str
    top_k: int = 5


@router.post("/query")
async def rag_query(req: RAGQueryRequest):
    """Debug endpoint: run a RAG query and return raw chunks."""
    try:
        from services.rag.pipeline import query_rag
        chunks = query_rag(req.question, top_k=req.top_k)
        return {"question": req.question, "chunks": chunks, "count": len(chunks)}
    except Exception as e:
        logger.error(f"[RAG Query] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/speculate")
async def speculate_rag(req: RAGQueryRequest):
    """Speculative pre-fetching for faster interface response."""
    try:
        from memory.manager import speculate_memory
        await speculate_memory(req.question)
        return {"status": "primed"}
    except Exception as e:
        logger.error(f"[RAG Speculate] Error: {e}")
        return {"status": "error", "detail": str(e)}
