"""
services/link_processor/processors/image.py
- Processes images using Ollama Vision models (llava, bakllava).
"""

import logging
import base64
import os
from engine.config import OLLAMA_API_URL
from engine.model_manager import ModelManager
import httpx

logger = logging.getLogger(__name__)

async def process_image_file(file_path: str, filename: str) -> dict:
    """Analyze an image using Ollama vision model."""
    try:
        with open(file_path, "rb") as f:
            img_bytes = f.read()
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')

        # Dynamically find a vision model
        vision_model, _ = await ModelManager.get_best_model(mode="chat", question="Analyze this image", has_images=True)
        
        payload = {
            "model": vision_model,
            "prompt": "Describe this image in detail. What is in it? Analyze any text or objects visible.",
            "stream": False,
            "images": [img_b64]
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{OLLAMA_API_URL}/generate", json=payload)
            if resp.status_code == 200:
                description = resp.json().get("response", "")
                return {
                    "source": filename,
                    "title": filename,
                    "text": description,
                    "description": description,
                    "error": None
                }
            else:
                return {"error": f"Ollama vision error: {resp.status_code}", "text": "", "source": filename}
                
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        return {"error": str(e), "text": "", "source": filename}
