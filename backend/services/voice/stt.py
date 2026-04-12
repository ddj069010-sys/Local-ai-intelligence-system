"""
services/voice/stt.py
- Speech-to-Text using OpenAI Whisper.
- Receives audio blob, returns transcribed text.
"""

import os
import logging
import tempfile

logger = logging.getLogger(__name__)

_whisper_model_cache = None


def _get_whisper():
    global _whisper_model_cache
    if _whisper_model_cache is None:
        import whisper
        logger.info("Loading Whisper STT model...")
        _whisper_model_cache = whisper.load_model("base")
    return _whisper_model_cache


async def transcribe_audio_bytes(audio_bytes: bytes, extension: str = ".webm") -> dict:
    """Transcribe raw audio bytes using Whisper. Returns transcribed text."""
    try:
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        model = _get_whisper()
        result = model.transcribe(tmp_path, fp16=False)
        text = result.get("text", "").strip()
        os.unlink(tmp_path)

        return {"success": True, "text": text}
    except Exception as e:
        logger.error(f"STT error: {e}")
        return {"success": False, "text": "", "error": str(e)}
