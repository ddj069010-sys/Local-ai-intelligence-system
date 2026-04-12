"""
services/voice/tts.py
- Text-to-Speech using edge-tts.
- Returns audio bytes (MP3 stream).
"""

import logging
import io
import asyncio
import edge_tts

logger = logging.getLogger(__name__)

DEFAULT_VOICE = "en-US-AriaNeural"


async def text_to_speech_bytes(text: str, voice: str = DEFAULT_VOICE) -> bytes:
    """Convert text to MP3 audio bytes using edge-tts."""
    try:
        communicate = edge_tts.Communicate(text, voice)
        audio_buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buf.write(chunk["data"])
        return audio_buf.getvalue()
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return b""


def get_available_voices() -> list:
    """Return a static list of recommended voices."""
    return [
        {"id": "en-US-AriaNeural", "name": "Aria (US, Female)"},
        {"id": "en-US-GuyNeural", "name": "Guy (US, Male)"},
        {"id": "en-GB-SoniaNeural", "name": "Sonia (UK, Female)"},
        {"id": "en-IN-NeerjaNeural", "name": "Neerja (IN, Female)"},
    ]
