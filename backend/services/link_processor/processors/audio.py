"""
services/link_processor/processors/audio.py
- Transcribes audio files using OpenAI Whisper.
"""

import logging

logger = logging.getLogger(__name__)

_faster_whisper_cache = None

def _get_faster_whisper():
    global _faster_whisper_cache
    if _faster_whisper_cache is None:
        try:
            from faster_whisper import WhisperModel
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            logger.info(f"Loading Faster-Whisper model (small) on {device}...")
            _faster_whisper_cache = WhisperModel("small", device=device, compute_type=compute_type)
        except Exception as e:
            logger.error(f"Failed to load Faster-Whisper: {e}")
            return None
    return _faster_whisper_cache


def process_audio_file(file_path: str, filename: str) -> dict:
    """Transcribe a local audio file using Whisper."""
    try:
        model_engine = _get_faster_whisper()
        if not model_engine:
            raise Exception("Faster-Whisper engine not loaded")
            
        segments, info = model_engine.transcribe(file_path, beam_size=5)
        transcript = " ".join([s.text for s in list(segments)]).strip()
        
        return {
            "source": filename,
            "title": filename,
            "transcript": transcript,
            "text": transcript,
            "error": None,
        }
    except Exception as e:
        logger.error(f"Audio transcription failed: {e}")
        return {
            "source": filename,
            "transcript": "",
            "text": "",
            "error": str(e),
        }
