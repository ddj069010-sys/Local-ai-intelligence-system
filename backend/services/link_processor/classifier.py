"""
services/link_processor/classifier.py
- Detects the type of a given URL or file path.
- Supported types: webpage, youtube, video, audio, document, unknown
"""

import re
from pathlib import Path

YOUTUBE_PATTERNS = [
    r"youtube\.com/watch",
    r"youtu\.be/",
    r"youtube\.com/shorts",
]

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
VIDEO_EXT = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv"}
AUDIO_EXT = {".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a"}
DOC_EXT   = {".pdf", ".docx", ".doc", ".txt", ".md"}


def classify_url(url: str) -> str:
    """Return the content type of a URL string."""
    url_lower = url.lower().strip()

    # YouTube videos
    for pattern in YOUTUBE_PATTERNS:
        if re.search(pattern, url_lower):
            return "youtube"

    # Direct file links (by extension in the URL)
    for ext in IMAGE_EXT:
        if url_lower.endswith(ext) or f"{ext}?" in url_lower:
            return "image"
    for ext in VIDEO_EXT:
        if url_lower.endswith(ext) or f"{ext}?" in url_lower:
            return "video"
    for ext in AUDIO_EXT:
        if url_lower.endswith(ext) or f"{ext}?" in url_lower:
            return "audio"
    for ext in DOC_EXT:
        if url_lower.endswith(ext) or f"{ext}?" in url_lower:
            return "document"

    # Fallback: treat as standard webpage
    if url_lower.startswith("http://") or url_lower.startswith("https://"):
        return "webpage"

    return "unknown"


def classify_file(filename: str) -> str:
    """Return the content type of an uploaded file by its extension."""
    ext = Path(filename).suffix.lower()
    if ext in IMAGE_EXT:
        return "image"
    if ext in VIDEO_EXT:
        return "video"
    if ext in AUDIO_EXT:
        return "audio"
    if ext in DOC_EXT:
        return "document"
    return "unknown"
