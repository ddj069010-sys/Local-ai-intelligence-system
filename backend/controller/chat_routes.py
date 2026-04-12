import os
import json
import uuid
import logging
from typing import List, Dict, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["chats"])

CHAT_STORE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chats")
os.makedirs(CHAT_STORE_DIR, exist_ok=True)

class ChatSession(BaseModel):
    chat_id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[Dict] = []

def get_chat_path(chat_id: str) -> str:
    return os.path.join(CHAT_STORE_DIR, f"{chat_id}.json")

def load_chat(chat_id: str) -> Optional[ChatSession]:
    path = get_chat_path(chat_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return ChatSession(**data)
        except Exception as e:
            logger.error(f"Failed to load chat {chat_id}: {e}")
    return None

def save_chat(session: ChatSession):
    path = get_chat_path(session.chat_id)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(session.model_dump_json())
    except Exception as e:
        logger.error(f"Failed to save chat {session.chat_id}: {e}")

@router.get("")
async def list_chats():
    chats = []
    for filename in os.listdir(CHAT_STORE_DIR):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(CHAT_STORE_DIR, filename), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    chats.append({
                        "id": data.get("chat_id"),
                        "title": data.get("title", "New Conversation"),
                        "updated_at": data.get("updated_at")
                    })
            except Exception:
                pass
    chats.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return chats

@router.post("")
async def create_chat():
    """Generates a UUID session state and returns it to the UI."""
    chat_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    session = ChatSession(
        chat_id=chat_id,
        title="🌟 New Encounter",
        created_at=now,
        updated_at=now,
        messages=[]
    )
    save_chat(session)
    return {"chat_id": chat_id, "title": session.title}

@router.get("/{chat_id}")
async def get_chat(chat_id: str):
    session = load_chat(chat_id)
    if not session:
        if chat_id == "default":
            now = datetime.utcnow().isoformat()
            session = ChatSession(chat_id="default", title="Root Session", created_at=now, updated_at=now, messages=[])
            save_chat(session)
            return session
        raise HTTPException(status_code=404, detail="Chat not found")
    return dict(session)

from fastapi import APIRouter, HTTPException, BackgroundTasks

@router.delete("/{chat_id}")
async def delete_chat(chat_id: str):
    path = get_chat_path(chat_id)
    if os.path.exists(path):
        os.remove(path)
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Chat not found")

async def _generate_chat_title(chat_id: str, first_prompt: str):
    """Background task to generate a beautiful chat title."""
    try:
        from engine.utils import call_ollama
        
        prompt = f"Generate a very short, concise conversational title (max 5 words) for a new chat session that starts with this user message. Include one relevant emoji at the very beginning. Message: '{first_prompt[:500]}'"
        
        title = await call_ollama(
            prompt=prompt, 
            model="gemma3:4b", 
            system="You are a title generator. Return strictly the unquoted title string starting with an emoji. Do NOT wrap in quotes. Do NOT provide preamble."
        )
        
        if title:
            title = title.strip('\'" \n')
            session = load_chat(chat_id)
            if session:
                session.title = title
                session.updated_at = datetime.utcnow().isoformat()
                save_chat(session)
                logger.info(f"✅ Auto-named chat {chat_id} -> {title}")
    except Exception as e:
        logger.error(f"❌ Auto-naming failed: {e}")

@router.post("/{chat_id}/sync")
async def sync_chat_messages(chat_id: str, payload: dict, background_tasks: BackgroundTasks):
    """
    Syncs the entire UI state message block down to the backend.
    """
    session = load_chat(chat_id)
    if not session:
        now = datetime.utcnow().isoformat()
        session = ChatSession(chat_id=chat_id, title="Restored Session", created_at=now, updated_at=now, messages=[])
        
    messages = payload.get("messages", [])
    session.messages = messages
    
    # Auto-Naming logic (Triggers background LLM task)
    if session.title in ["🌟 New Encounter", "New Conversation", "Restored Session", "New Chat"] and len(messages) > 0:
        first_prompt = next((m.get("content") for m in messages if m.get("sender") == "user"), None)
        if first_prompt:
            # Tell UI that we are generating...
            session.title = "✨ Generating..."
            background_tasks.add_task(_generate_chat_title, chat_id, first_prompt)
            
    session.updated_at = datetime.utcnow().isoformat()
    save_chat(session)
    
    return {"status": "synced", "title": session.title}
