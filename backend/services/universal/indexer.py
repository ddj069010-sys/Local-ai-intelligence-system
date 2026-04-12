import os
import logging
import asyncio
import uuid
from pathlib import Path
from core.config import settings
from services.universal.doc_registry import doc_registry
from engine.state import WORKSPACE, save_workspace
from engine.utils import get_embedding

logger = logging.getLogger(__name__)

async def deep_workspace_index(session_id: str = "default"):
    """
    --- BEYOND-GPT: DEEP WORKSPACE INDEXER ---
    Scans the uploads directory, registers files, and builds the semantic map.
    """
    logger.info("🚀 [INDEXER] Starting Deep Workspace Index...")
    
    upload_dir = settings.UPLOAD_DIR
    if not upload_dir.exists():
        upload_dir.mkdir(parents=True, exist_ok=True)
        
    supported_extensions = {".txt", ".md", ".pdf", ".py", ".js", ".json", ".html", ".css", ".docx", ".csv"}
    
    indexed_docs = []
    semantic_tree = {} # Path -> Metadata
    
    # Ensuring workspace exists for session
    if session_id not in WORKSPACE:
        WORKSPACE[session_id] = {"docs": [], "chunks": [], "embeddings": [], "metadata": {}}

    logger.info(f"📁 [INDEXER] Scanning root: {settings.ROOT_DIR}")
    
    # 🔎 PHASE 1: SEMANTIC TREE MAPPING (Project Structure)
    for root, dirs, files in os.walk(settings.ROOT_DIR):
        # Skip hidden and venv
        if any(x in root for x in [".git", "venv", "__pycache__", "node_modules"]):
            continue
            
        rel_root = os.path.relpath(root, settings.ROOT_DIR)
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in supported_extensions:
                full_path = Path(root) / file
                rel_path = os.path.relpath(full_path, settings.ROOT_DIR)
                
                semantic_tree[rel_path] = {
                    "name": file,
                    "type": ext[1:].upper(),
                    "size": full_path.stat().st_size,
                    "depth": rel_path.count(os.sep)
                }

    # 🔎 PHASE 2: DEEP CONTENT INDEXING
    search_dirs = [settings.UPLOAD_DIR, settings.ROOT_DIR / "backend" / "data"]
    for s_dir in search_dirs:
        if not s_dir.exists(): continue
        for file_path in s_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    content = ""
                    # Enhanced Loader Logic
                    if file_path.suffix.lower() in {".txt", ".md", ".py", ".js", ".json", ".css", ".html", ".csv"}:
                        content = file_path.read_text(errors="ignore")
                    elif file_path.suffix.lower() == ".docx":
                        # Placeholder for DOCX - could use docx2txt or similar
                        content = f"[DOCX Content Placeholder for {file_path.name}]" 
                    
                    if not content: continue
                    
                    # Register and Embed
                    doc_id = str(uuid.uuid4())
                    short_name = doc_registry.register(doc_id, file_path.name, chunks=[content])
                    
                    indexed_docs.append({
                        "id": doc_id,
                        "name": file_path.name,
                        "short_name": short_name,
                        "type": file_path.suffix[1:].upper(),
                        "path": str(file_path.relative_to(settings.ROOT_DIR))
                    })
                    
                    # Limit chunking to important docs
                    if len(content) > 10:
                        chunk = content[:3000]
                        emb = await get_embedding(chunk)
                        WORKSPACE[session_id]["chunks"].append(f"### [FILE_INDEX: {file_path.name}]\n{chunk}")
                        if emb: WORKSPACE[session_id]["embeddings"].append(emb)

                except Exception as e:
                    logger.error(f"❌ [INDEXER] Failed {file_path.name}: {e}")

    WORKSPACE[session_id]["docs"] = indexed_docs
    WORKSPACE[session_id]["semantic_tree"] = semantic_tree
    WORKSPACE[session_id]["metadata"]["last_index"] = datetime.now().isoformat()
    
    save_workspace()
    logger.info(f"🏁 [INDEXER] Deep Workspace Index Complete. Tree nodes: {len(semantic_tree)}")
    return indexed_docs
    from datetime import datetime



    WORKSPACE[session_id]["docs"] = indexed_docs
    WORKSPACE[session_id]["metadata"]["last_index"] = str(asyncio.get_event_loop().time())
    
    save_workspace()
    logger.info(f"🏁 [INDEXER] Deep Workspace Index Complete. Total docs: {len(indexed_docs)}")
    return indexed_docs

if __name__ == "__main__":
    # For manual testing
    asyncio.run(deep_workspace_index())
