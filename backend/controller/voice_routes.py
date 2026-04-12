"""
controller/voice_routes.py
- FastAPI router exposes STT and TTS endpoints.
"""

import logging
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from fastapi.responses import Response

from services.voice.stt import transcribe_audio_bytes
from services.voice.tts import text_to_speech_bytes, get_available_voices

router = APIRouter(prefix="/voice", tags=["voice"])
logger = logging.getLogger(__name__)


@router.post("/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    """Transcribe uploaded audio to text using Whisper."""
    filename = audio.filename or "audio.webm"
    ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ".webm"
    audio_bytes = await audio.read()
    result = await transcribe_audio_bytes(audio_bytes, ext)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Transcription failed"))
    return {"text": result["text"]}


@router.get("/tts")
async def text_to_speech(
    text: str = Query(..., min_length=1, max_length=5000),
    voice: str = Query(default="en-US-AriaNeural")
):
    """Convert text to MP3 audio stream using edge-tts."""
    audio_bytes = await text_to_speech_bytes(text, voice)
    if not audio_bytes:
        raise HTTPException(status_code=500, detail="TTS generation failed")
    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.get("/voices")
async def list_voices():
    """Return a list of available TTS voices."""
    return get_available_voices()
