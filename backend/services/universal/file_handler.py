import os
import logging
import mimetypes
import subprocess
from typing import Dict, Any, Optional
from .document_processor import process_document
from .image_processor import process_image
from .video_processor import process_video_file
from services.intelligence.audio_processor import audio_intelligence

logger = logging.getLogger(__name__)

SUPPORTED_DOCS = {".pdf", ".docx", ".doc", ".txt", ".csv", ".xlsx", ".xls", ".pptx"}
SUPPORTED_IMAGES = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_VIDEOS = {".mp4", ".mov", ".mkv", ".avi"}
SUPPORTED_AUDIO = {".mp3", ".wav", ".flac", ".m4a", ".aac"}

async def handle_file(file_path: str, filename: str, chat_id: Optional[str] = None, user_input: str = "") -> Dict[str, Any]:
    """Detects file type and routes to the appropriate processor."""
    ext = os.path.splitext(filename)[1].lower()
    mime_type, _ = mimetypes.guess_type(filename)
    
    try:
        # Advanced Hybrid Routing: checking extension or accurate mime signature
        if ext in SUPPORTED_DOCS or (mime_type and 'text' in mime_type):
            return await process_document(file_path, filename, chat_id)
        elif ext in SUPPORTED_IMAGES or (mime_type and 'image' in mime_type):
            return await process_image(file_path, filename)
        elif ext in SUPPORTED_VIDEOS or (mime_type and 'video' in mime_type):
            return await process_video_file(file_path, filename, user_input=user_input)
        elif ext in SUPPORTED_AUDIO or (mime_type and 'audio' in mime_type):
             # Audio transcription: Async request
             transcript = await audio_intelligence.process_audio(file_path)
             return {"type": "audio", "source": filename, "transcript": transcript}
        else:
            return {"error": f"Unsupported hybrid type: {ext} [{mime_type}]", "type": "unknown"}
    except Exception as e:
        logger.error(f"Error handling file {filename}: {e}")
        return {"error": str(e), "type": "error"}

async def fast_local_scan(directory: str, keyword: str) -> Dict[str, Any]:
    """Uses Rust's ripgrep for lightning-fast codebase scanning instead of native Python loops."""
    try:
        # Tries to run ripgrep. If unavailable, flags for installation rather than crashing.
        cmd = ["rg", "-n", "--max-count=10", keyword, directory]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return {"type": "scan_result", "hits": result.stdout, "status": "success"}
        elif result.returncode == 1:
            return {"type": "scan_result", "hits": "No matches found.", "status": "empty"}
        else:
            return {"error": f"Ripgrep scan failed: {result.stderr}", "type": "error"}
    except FileNotFoundError:
         return {"error": "ripgrep ('rg') is not installed on this system. Install it for hyper-fast local execution.", "type": "error"}
