import logging
import re
from typing import Dict, Any, Optional
from .file_handler import handle_file
from .document_processor import process_document
from .image_processor import process_image
from .video_processor import process_video_url
import httpx
import tempfile
import os

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*')

async def handle_url(url: str, chat_id: Optional[str] = None) -> Dict[str, Any]:
    """Detects URL type and routes to the correct processor."""
    url = url.strip()
    
    # 1. Check if it's a YouTube URL
    if "youtube.com" in url or "youtu.be" in url:
        return await process_video_url(url)
    
    # 2. Check extension for direct links
    path_name = url.split("?")[0].split("/")[-1]
    ext = os.path.splitext(path_name)[1].lower()
    
    if ext in (".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".mp4", ".mov"):
        # Download and process as file
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    tmp.write(resp.content)
                    tmp_path = tmp.name
                
                try:
                    return await handle_file(tmp_path, path_name, chat_id)
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
        except Exception as e:
            logger.error(f"Failed to download direct link {url}: {e}")
            return {"error": f"Download failed: {e}", "type": "url"}
    # 2.5 Check additional data extensions explicitly
    data_extensions = (".csv", ".json", ".md", ".xml", ".mp3", ".wav", ".ogg", ".gif", ".webp", ".zip")
    if ext in data_extensions:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, follow_redirects=True)
                resp.raise_for_status()
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    tmp.write(resp.content)
                    tmp_path = tmp.name
                try:
                    return await handle_file(tmp_path, path_name, chat_id)
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
        except Exception as e:
            logger.error(f"Failed to download supplemental direct link {url}: {e}")
            return {"error": f"Download supplemental failed: {e}", "type": "url"}
            
    # 2.6 Inspect headers for content type if extension is missing
    if not ext:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                head_resp = await client.head(url, follow_redirects=True)
                content_type = head_resp.headers.get("content-type", "").lower()
                detected_ext = ""
                if "application/pdf" in content_type: detected_ext = ".pdf"
                elif "image/jpeg" in content_type: detected_ext = ".jpg"
                elif "image/png" in content_type: detected_ext = ".png"
                elif "text/csv" in content_type: detected_ext = ".csv"
                elif "audio/" in content_type: detected_ext = ".mp3"
                elif "video/" in content_type: detected_ext = ".mp4"
                
                if detected_ext:
                    resp = await client.get(url, follow_redirects=True)
                    resp.raise_for_status()
                    with tempfile.NamedTemporaryFile(suffix=detected_ext, delete=False) as tmp:
                        tmp.write(resp.content)
                        tmp_path = tmp.name
                    try:
                        return await handle_file(tmp_path, f"downloaded{detected_ext}", chat_id)
                    finally:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
        except Exception as e:
            logger.warning(f"Header inspection failed or skipped for {url}: {e}")
            
    # 2.7 Specialized Platforms Logging
    is_social_media = any(domain in url.lower() for domain in ["twitter.com", "x.com", "tiktok.com", "instagram.com"])
    if is_social_media:
        logger.info(f"Social media link detected: {url}. Applying standard webpage processor with extra context handling.")
    if "github.com" in url or "gitlab.com" in url:
        logger.info(f"Developer Platform URL detected: {url}")

    # 3. Fallback: Treat as a webpage for scraping (Deep Intelligence Engine)
    from services.link_processor.processors.web import process_webpage
    try:
        # Now async and uses Hyper-Search
        res = await process_webpage(url)
        return {
            "type": "webpage",
            "source": url,
            "text": res.get("text", "")[:7000], # Increased limit to ensure Stripe tables aren't cut
            "title": res.get("title", "Webpage Intelligence"),
            "error": res.get("error")
        }
    except Exception as e:
        logger.error(f"Webpage processing failed for {url}: {e}")
        return {"error": str(e), "type": "webpage"}
