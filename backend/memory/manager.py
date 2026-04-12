import json
import os
import uuid
import math
import httpx
import logging
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from engine.config import OLLAMA_API_URL

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data"
_CHATS_DIR = _DATA_DIR / "chats"
_POOL_FILE = _DATA_DIR / "memory_pool.json"

_CHATS_DIR.mkdir(parents=True, exist_ok=True)
if not _POOL_FILE.exists():
    with open(_POOL_FILE, "w") as f:
        json.dump({"entries": [], "clusters": []}, f)

# --- PART 1: CHAT SESSION PERSISTENCE ---

def create_chat(chat_id: str, title: str = "New Chat") -> Dict[str, Any]:
    path = _CHATS_DIR / f"{chat_id}.json"
    data = {
        "chat_id": str(chat_id),
        "title": str(title),
        "messages": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data

def load_chat(chat_id: str) -> Dict[str, Any]:
    path = _CHATS_DIR / f"{chat_id}.json"
    if not path.exists():
        return create_chat(chat_id)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return create_chat(chat_id)

def save_chat(chat_id: str, messages: List[Dict[str, Any]], title: Optional[str] = None) -> None:
    path = _CHATS_DIR / f"{chat_id}.json"
    
    # Load existing to preserve metadata
    current_data = {}
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        except: pass
    
    # Robust length limiting
    msg_list = list(messages)
    if len(msg_list) > 100:
        new_list = []
        # Manual slice for linter
        start_idx = len(msg_list) - 100
        for i in range(start_idx, len(msg_list)):
            new_list.append(msg_list[i])
        msg_list = new_list
        
    data = {
        "chat_id": str(chat_id),
        "title": str(title) if title else str(current_data.get("title", "Active Research")),
        "created_at": str(current_data.get("created_at", datetime.now(timezone.utc).isoformat())),
        "messages": msg_list,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def append_message(chat_id: str, role: str, content: str, model: str = None, **kwargs) -> None:
    chat = load_chat(chat_id)
    new_msg = {"role": str(role), "content": str(content), "timestamp": datetime.now(timezone.utc).isoformat()}
    new_msg.update(kwargs)
    
    msgs = list(chat.get("messages", []))
    msgs.append(new_msg)
    save_chat(chat_id, msgs)
    
    # Safely trigger auto-extraction if we have at least one message pair (or just the user msg)
    if role == "assistant" and len(msgs) >= 2:
        try:
            user_msg = msgs[-2].get("content", "")
            asyncio.create_task(auto_extract_memory(chat_id, str(user_msg), str(content)))
            asyncio.create_task(auto_name_chat(chat_id, str(user_msg)))
            
            # PEARL RECURSION: Compress if history is deep
            if len(msgs) > 60:
                asyncio.create_task(compress_session(chat_id))
        except: pass

# --- PART 2: SEMANTIC POOL ORCHESTRATION ---

_EMBEDDING_CACHE = {}

async def get_embedding(text: str, model: str = "nomic-embed-text:latest") -> List[float]:
    try:
        content_str = str(text).strip()
        if len(content_str) > 1500:
            content_str = content_str[0:1500]
            
        if content_str in _EMBEDDING_CACHE:
            return _EMBEDDING_CACHE[content_str]

        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{OLLAMA_API_URL}/embeddings", json={"model": model, "prompt": content_str}, timeout=30.0)
            result = resp.json().get("embedding", [])
            emb = [float(x) for x in result]
            if emb:
                _EMBEDDING_CACHE[content_str] = emb
            return emb
    except Exception as e: 
        logger.error(f"Embedding failed: {e}")
        return []
    return []

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2): return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    mag = math.sqrt(sum(a*a for a in v1)) * math.sqrt(sum(a*a for a in v2))
    return float(dot / mag) if mag > 0 else 0.0

async def push_to_pool(chat_id: str, content: str, metadata: Dict[str, Any]) -> None:
    try:
        with open(_POOL_FILE, "r") as f:
            pool = json.load(f)
        
        chat_data = load_chat(chat_id)
        chat_title = chat_data.get("title", "Active Session")
        
        entry_id = str(uuid.uuid4())
        embedding = await get_embedding(content)
        
        entry = {
            "id": entry_id,
            "chat_id": str(chat_id),
            "chat_title": chat_title,
            "content": str(content),
            "summary": str(metadata.get("summary", "Neural Entry")),
            "tags": list(metadata.get("tags", ["auto"])),
            "entities": list(metadata.get("entities", [])),
            "embedding": embedding,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        pool["entries"].insert(0, entry)
        
        with open(_POOL_FILE, "w") as f:
            json.dump(pool, f, indent=2)
            
        logger.info(f"Pushed entry to pool: {entry_id}")
            
    except Exception as e:
        logger.error(f"Failed to push to pool: {e}")

async def pull_from_pool(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Vector-based memory retrieval."""
    try:
        query_emb = await get_embedding(query)
        if not query_emb:
            return []
            
        entries = get_all_pool_entries()
        scored_results = []
        
        for entry in entries:
            entry_emb = entry.get("embedding")
            if entry_emb:
                score = cosine_similarity(query_emb, entry_emb)
                
                # Boost identity facts
                if "identity" in entry.get("tags", []):
                    score += 0.20
                
                if score >= 0.75: # Raised Relevance Threshold Gate
                    scored_results.append({**entry, "score": score})
        
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        # Always inject top identity facts if relevant
        identity_facts = [r for r in scored_results if "identity" in r.get("tags", [])]
        other_facts = [r for r in scored_results if "identity" not in r.get("tags", [])]
        
        final_results = identity_facts[:3] + other_facts
        return final_results[:limit]
    except Exception as e:
        logger.error(f"Pull from pool failed: {e}")
        return []

# Alias for backward compatibility with Intelligence HQ routes
search_data_pool = pull_from_pool

def get_all_pool_entries() -> List[Dict[str, Any]]:
    try:
        with open(_POOL_FILE, "r") as f:
            return json.load(f).get("entries", [])
    except: return []

def delete_from_pool(entry_id: str) -> bool:
    try:
        with open(_POOL_FILE, "r") as f:
            pool = json.load(f)
        
        initial_len = len(pool["entries"])
        pool["entries"] = [e for e in pool["entries"] if e["id"] != entry_id]
        
        if len(pool["entries"]) < initial_len:
            with open(_POOL_FILE, "w") as f:
                json.dump(pool, f, indent=2)
            return True
    except: pass
    return False

def list_all_chats() -> List[Dict[str, Any]]:
    chats = []
    for f in _CHATS_DIR.glob("*.json"):
        try:
            with open(f, "r") as content:
                data = json.load(content)
                chats.append(data)
        except: pass
    return sorted(chats, key=lambda x: x.get("updated_at", ""), reverse=True)

def get_chats() -> List[Dict[str, Any]]:
    """Alias for backward compatibility."""
    return list_all_chats()

def get_context_messages(chat_id: str, n: int = 10) -> List[Dict[str, Any]]:
    """Retrieves last N messages for chat context."""
    chat = load_chat(chat_id)
    return chat.get("messages", [])[-n:]

def cleanup_memory() -> None:
    """Maintenance tasks for memory pool."""
    pass

def delete_chat(chat_id: str) -> bool:
    path = _CHATS_DIR / f"{chat_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False

async def rerank_results(query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    --- BEYOND-GPT: MEMORY RERANKING ---
    Uses a small model to find the absolute best semantic matches 
    from a list of vector candidates.
    """
    if not query or not results: return results
    
    candidates = []
    for i, res in enumerate(results[:10]):
        candidates.append(f"[{i}] {res.get('summary', 'Neural Note')}: {res.get('content', '')[:300]}")
    
    candidates_text = "\n".join(candidates)
    prompt = f"""QUERY: {query}
HISTORICAL DATA CANDIDATES:
{candidates_text}

TASK: Rank the top 3 candidates by RELEVANCE to the query. 
Only output the indices in order, e.g., [2, 0, 5]. 
If none are relevant, output []."""

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{OLLAMA_API_URL}/generate", json={
                "model": "gemma3:1b", # Low latency 1b model for reranking
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0}
            }, timeout=10.0)
            
            if resp.status_code == 200:
                response_text = resp.json().get("response", "[]")
                indices = [int(n) for n in re.findall(r"\d+", response_text)]
                
                reranked = []
                # Add ranked items first
                for idx in indices:
                    if idx < len(results):
                        reranked.append(results[idx])
                
                # Append rest
                seen_ids = [r.get("id") for r in reranked]
                for res in results:
                    if res.get("id") not in seen_ids:
                        reranked.append(res)
                return reranked
    except Exception as e:
        logger.error(f"Reranking failed: {e}")
    
    # Keyword fallback if model rerank fails
    query_words = set(str(query).lower().split())
    for res in results:
        score = 1.0
        content = str(res.get("content", "")).lower()
        for word in query_words:
            if word in content: score += 0.2
        res["rerank_score"] = score
    return sorted(results, key=lambda x: x.get("rerank_score", 1.0), reverse=True)


async def auto_name_chat(chat_id: str, question: str):
    """Naming logic helper: Extracts core essence of the question with emojis."""
    try:
        chat = load_chat(chat_id)
        # Only rename if it's currently a default title
        if chat.get("title") in ["New Chat", "🌟 New Encounter", "Active Session", "Active Research"]:
            # Clean and capitalize
            words = [w for w in str(question).strip().split() if len(w) > 1]
            if not words: return
            
            # Intelligent prefixing based on content
            q_lower = question.lower()
            emoji = "💬"
            if any(k in q_lower for k in ["code", "python", "js", "fix", "debug"]): emoji = "💻"
            elif any(k in q_lower for k in ["research", "what", "how", "why"]): emoji = "🔍"
            elif any(k in q_lower for k in ["write", "essay", "report", "create"]): emoji = "✍️"
            elif any(k in q_lower for k in ["math", "calculate", "solve"]): emoji = "🔢"
            elif any(k in q_lower for k in ["design", "css", "style", "ui"]): emoji = "🎨"
            
            core_words = words[:4]
            name_base = " ".join(core_words).capitalize()
            if len(words) > 4: name_base += "..."
            
            new_title = f"{emoji} {name_base}"
            save_chat(chat_id, chat.get("messages", []), title=new_title)
            logger.info(f"Auto-named chat {chat_id} -> {new_title}")
    except Exception as e:
        logger.error(f"Auto-naming failed: {e}")

async def auto_extract_memory(chat_id: str, user_q: str, ai_a: str) -> None:
    """
    True Long-Term Memory (Identity Reflection).
    Extracts explicit personal facts and project context.
    """
    try:
        if not user_q or len(user_q.split()) < 2:
            return

        chat = load_chat(chat_id)
        history = chat.get("messages", [])[-4:]
        history_str = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in history])

        # Proper f-string with escaped quotes and literal braces for JSON
        prompt = (
            f"CHAT HISTORY:\n{history_str}\n\n"
            "Extract any newly revealed personal details, names, strict preferences, or overarching project contexts about the USER. "
            "Do not extract generic tech skills unless the user explicitly owns them. "
            "Return JSON: {\"facts\": [\"fact 1\", \"fact 2\"]}. If none, return empty list."
        )

        payload = {
            "model": "gemma3:4b",
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1}
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{OLLAMA_API_URL}/generate", json=payload, timeout=20.0)
            if resp.status_code == 200:
                data = resp.json()
                result = json.loads(data.get("response", "{}"))
                facts = result.get("facts", [])
                
                for fact in facts:
                    # Deduplicate: Check if a very similar fact already exists
                    existing = await pull_from_pool(fact, limit=1)
                    if existing and existing[0].get("score", 0) > 0.9:
                        continue
                        
                    await push_to_pool(
                        chat_id, 
                        f"USER FACT: {fact}", 
                        {
                            "summary": "Personal Context", 
                            "tags": ["identity", "persistent"], 
                            "entities": []
                        }
                    )
    except Exception as e:
        logger.error(f"Auto-extraction failed: {e}")

async def compress_session(chat_id: str):
    """
    Recursive Knowledge Pearls.
    Condenses deep history into a single 'system' context pearl.
    """
    try:
        from engine.utils import call_ollama
        chat = load_chat(chat_id)
        msgs = chat.get("messages", [])
        if len(msgs) < 50: return

        to_compress = msgs[:40]
        remaining = msgs[40:]
        
        history_text = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in to_compress])
        prompt = f"HISTORY:\n{history_text}\n\nCONCISE KNOWLEDGE PEARL: Extract the absolute essence of this chat including user name, project names, and hard preferences into 1 paragraph. NO FLUFF."
        
        pearl = await call_ollama(prompt, model="phi3:mini")
        if pearl and len(pearl) > 10:
            refined_msgs = [{"role": "system", "content": f"📜 MEMORY PEARL: {pearl}"}] + list(remaining)
            save_chat(chat_id, refined_msgs)
            logger.info(f"💾 Compressed chat {chat_id} into a Memory Pearl.")
    except Exception as e:
        logger.error(f"Session compression failed: {e}")

async def speculate_memory(query: str):
    """Speculative Pre-fetching helper."""
    return await pull_from_pool(query, limit=10)
