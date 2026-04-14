from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from engine.research import run_research
from fastapi.responses import StreamingResponse
import httpx
import json
import asyncio
from datetime import datetime, timezone
from engine.config import OLLAMA_API_URL
from engine.model_manager import ModelManager

# Standardized Memory System Integration
try:
    from memory.manager import (
        create_chat, load_chat, save_chat, 
        delete_chat, list_all_chats, push_to_pool, pull_from_pool, 
        cleanup_memory, get_all_pool_entries, delete_from_pool
    )
    _MEMORY_ENABLED = True
except ImportError:
    _MEMORY_ENABLED = False
    def create_chat(cid, t): return {}
    def load_chat(cid): return {}
    def save_chat(cid, m, title=None): pass
    def delete_chat(cid): return False
    def list_all_chats(): return []
    def push_to_pool(cid, c, meta): pass
    def pull_from_pool(q): return []
    def get_all_pool_entries(): return []
    def delete_from_pool(eid): return False
    def cleanup_memory(): pass

router = APIRouter()

class ChatRequest(BaseModel):
    model: str = "gemma3:4b"
    mode: str = "research"
    messages: List[Dict[str, Any]]
    session_id: str = "default" 
    web_enabled: bool = False
    speed_mode: str = "auto"
    deep_search: bool = False
    concentrated: bool = False
    images: Optional[List[str]] = None

class MemoryEntry(BaseModel):
    title: str = "Chat Snippet"
    content: str
    tags: List[str] = []
    chat_id: str = "manual"

@router.post("/chat")
async def chat(request: ChatRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                OLLAMA_API_URL + "/chat",
                json={"model": request.model, "messages": request.messages, "stream": False},
                timeout=120.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat_stream")
async def chat_stream(request: ChatRequest, fast_req: Request):
    question = ""
    for msg in reversed(request.messages):
        if msg.get("role") == "user":
            question = msg.get("content", "")
            break
    if not question and not request.images:
        raise HTTPException(status_code=400, detail="No user message found")
    
    # Use a default prompt if image is present but text is empty
    if not question and request.images:
        question = "Please analyze this image and describe what you see."

    async def event_generator():
        try:
            async for progress in run_research(
                question, 
                request.model, 
                request.mode, 
                chat_id=request.session_id, 
                web_enabled=request.web_enabled, 
                speed_mode=request.speed_mode, 
                deep_search=request.deep_search, 
                concentrated=request.concentrated,
                images=request.images
            ):
                if await fast_req.is_disconnected():
                    break
                yield f"data: {json.dumps(progress)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/chats")
async def get_chats():
    return list_all_chats()

@router.post("/chats")
async def create_new_chat(title: str = "New Chat"):
    import uuid
    chat_id = str(uuid.uuid4())
    return create_chat(chat_id, title)

@router.get("/chats/{chat_id}")
async def get_chat_details(chat_id: str):
    return load_chat(chat_id)

@router.delete("/chats/{chat_id}")
async def delete_chat_handler(chat_id: str):
    success = delete_chat(chat_id)
    return {"status": "deleted" if success else "not found"}

@router.patch("/chats/{chat_id}")
async def rename_chat_handler(chat_id: str, title: str):
    chat_meta = load_chat(chat_id)
    # Ensure it's a dict before updating
    if isinstance(chat_meta, dict):
        messages = chat_meta.get("messages", [])
        save_chat(chat_id, messages, title=title)
        return {"status": "renamed", "title": title}
    return {"status": "error", "message": "Chat not found"}

@router.post("/chats/{chat_id}/sync")
async def sync_chat_handler(chat_id: str, request: Request):
    try:
        data = await request.json()
        messages = data.get("messages", [])
        title = data.get("title")
        save_chat(chat_id, messages, title=title)
        return {"status": "synced", "message_count": len(messages)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory")
async def get_memory_pool():
    if not _MEMORY_ENABLED: return []
    return get_all_pool_entries()

@router.get("/memory/search")
async def search_memory(q: str = ""):
    if not _MEMORY_ENABLED: return []
    return pull_from_pool(q)

@router.post("/memory")
async def add_to_memory(entry: MemoryEntry):
    if not _MEMORY_ENABLED: return {"status": "error", "message": "Memory disabled"}
    # Use the corrected push_to_pool signature
    await push_to_pool(entry.chat_id, entry.content, {"summary": entry.title, "tags": entry.tags, "entities": []})
    return {"status": "added"}

@router.delete("/memory/{entry_id}")
async def remove_memory_entry(entry_id: str):
    if not _MEMORY_ENABLED: return {"status": "error", "message": "Memory disabled"}
    success = delete_from_pool(entry_id)
    return {"status": "deleted" if success else "not found"}

@router.get("/database/stats")
async def get_db_stats():
    chats = list_all_chats()
    memories = get_all_pool_entries()
    return {
        "status": "online",
        "chat_count": len(chats),
        "memory_count": len(memories),
        "last_sync": datetime.now(timezone.utc).isoformat() if _MEMORY_ENABLED else None
    }

@router.get("/models")
async def list_models():
    models = await ModelManager.fetch_available_models()
    if not models:
        return ["auto", "gemma3:4b", "gemma3:27b", "llama3:8b"]
    return ["auto"] + models

@router.post("/models/unload")
async def unload_model_handler(model: str):
    success = await ModelManager.unload_model(model)
    return {"status": "unloaded" if success else "failed"}
