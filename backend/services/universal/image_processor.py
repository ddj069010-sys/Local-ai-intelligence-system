import logging
from typing import Dict, Any
from services.link_processor.processors.image import process_image_file

logger = logging.getLogger(__name__)

async def process_image(file_path: str, filename: str) -> Dict[str, Any]:
    """Analyzes images using a vision-capable model."""
    try:
        res = await process_image_file(file_path, filename)
        return {
            "type": "image",
            "source": filename,
            "text": res.get("text", ""),
            "description": res.get("description", ""),
            "error": res.get("error")
        }
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        return {"error": str(e), "type": "image"}
