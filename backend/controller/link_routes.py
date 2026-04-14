"""
controller/link_routes.py
- FastAPI router for the link processing API.
- Handles both URL input and file uploads.
"""

import os
import tempfile
import logging
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from services.link_processor.classifier import classify_url, classify_file
from services.link_processor.classifier import classify_url, classify_file
from services.link_processor.processors.web import process_webpage
from services.universal.video_processor import process_video_url as process_video, process_video_file
from services.link_processor.processors.audio import process_audio_file
from services.universal.document_processor import process_document
from services.universal.image_processor import process_image as process_image_file
from services.link_processor.summarizer import generate_summary
from engine.state import WORKSPACE, save_workspace
from engine.model_manager import ModelManager

router = APIRouter(prefix="/link", tags=["link"])
logger = logging.getLogger(__name__)


class LinkRequest(BaseModel):
    url: str
    model: Optional[str] = "gemma3:4b"
    chat_id: Optional[str] = None


@router.post("/process")
async def process_link(request: LinkRequest):
    """Classify and process a URL, returning a structured summary."""
    url = request.url.strip()
    content_type = classify_url(url)

    try:
        if content_type == "webpage":
            raw = process_webpage(url)
        elif content_type in ("youtube", "video"):
            raw = await process_video(url)
        elif content_type == "document":
            # For direct document URLs, download and process
            import httpx as httpx_lib
            ext = "." + url.split(".")[-1].split("?")[0]
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                async with httpx_lib.AsyncClient() as client:
                    resp = await client.get(url, timeout=30.0)
                    tmp.write(resp.content)
                    tmp_path = tmp.name
            try:
                processed_content = await process_document(tmp_path, url.split("/")[-1], request.chat_id)
                if request.chat_id and not processed_content.get("error"):
                    if request.chat_id not in WORKSPACE:
                        WORKSPACE[request.chat_id] = {"docs": [], "chunks": [], "embeddings": [], "metadata": {}}
                    
                    WORKSPACE[request.chat_id]["chunks"].extend(processed_content.get("chunks", []))
                    WORKSPACE[request.chat_id]["embeddings"].extend(processed_content.get("embeddings", []))
                    
                    # Store metadata for Universal Engine (Raw Text Sync)
                    if "docs_metadata" not in WORKSPACE[request.chat_id]:
                        WORKSPACE[request.chat_id]["docs_metadata"] = []
                    
                    WORKSPACE[request.chat_id]["docs_metadata"].append({
                        "name": url.split("/")[-1],
                        "full_text": processed_content.get("full_text", ""),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    save_workspace()
                    raw = processed_content
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        elif content_type == "image":
            # Direct image URLs
            import requests as req_lib
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                r = req_lib.get(url, timeout=20)
                tmp.write(r.content)
                tmp_path = tmp.name
            raw = await process_image_file(tmp_path, url.split("/")[-1])
            os.unlink(tmp_path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported URL type: {content_type}")

        if raw.get("error"):
            return JSONResponse(status_code=206, content={"warning": raw["error"], **raw})

        raw["content_type"] = content_type
        extraction_model, _ = await ModelManager.get_best_model(mode="summarize", purpose="extraction")
        result = await generate_summary(raw, model=extraction_model)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Link processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def process_upload(
    file: UploadFile = File(...),
    model: str = Form(default="gemma3:4b"),
    chat_id: str = Form(default=None)
):
    """Process an uploaded file (video, audio, document)."""
    filename = file.filename or "upload"
    content_type = classify_file(filename)

    if content_type == "unknown":
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {filename}")

    # Save to temp file
    contents = await file.read()
    with tempfile.NamedTemporaryFile(
        suffix=os.path.splitext(filename)[1],
        delete=False,
        mode='wb'
    ) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        if content_type == "document":
            raw = await process_document(tmp_path, filename, chat_id)
            # Backward compatibility metadata storage
            if chat_id:
                if chat_id not in WORKSPACE:
                    WORKSPACE[chat_id] = {"docs": [], "chunks": [], "embeddings": [], "metadata": {}}
                
                # Summary for UI display
                extraction_model, _ = await ModelManager.get_best_model(mode="summarize", purpose="extraction")
                summary_data = await generate_summary(raw, model=extraction_model)
                
                WORKSPACE[chat_id]["docs"].append({
                    "name": filename,
                    "path": tmp_path,
                    "content": summary_data.get("formatted", ""),
                    "full_text": raw.get("full_text", ""),
                    "timestamp": datetime.now().isoformat()
                })
                save_workspace()
        elif content_type == "video":
            raw = await process_video_file(tmp_path, filename)
        elif content_type == "audio":
            raw = process_audio_file(tmp_path, filename)
        elif content_type == "image":
            raw = await process_image_file(tmp_path, filename)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        if raw.get("error"):
            return JSONResponse(status_code=206, content={"warning": raw["error"], **raw})

        raw["content_type"] = content_type
        result = await generate_summary(raw, model=model)
        if content_type == "document":
            result["short_name"] = raw.get("short_name", "")
        return result
    finally:
        os.unlink(tmp_path)
