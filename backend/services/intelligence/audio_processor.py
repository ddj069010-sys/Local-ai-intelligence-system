import logging
import os
import asyncio
import torch
from pydub import AudioSegment
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

logger = logging.getLogger(__name__)

class AudioProcessor:
    """
    High-fidelity Audio Intelligence Engine.
    Uses OpenAI Whisper (Local) + Pydub slicing for deep transcription.
    """
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🎵 [AUDIO] Audio Intelligence initialized (Device: {self.device}).")

    async def _load_model(self):
        """Lazy load the Faster-Whisper model into VRAM."""
        if self.model is None and WhisperModel:
            try:
                # 'small' is ideal for 24GB RAM (likely 8GB VRAM)
                # compute_type="float16" for GPU, "int8" for CPU
                compute_type = "float16" if self.device == "cuda" else "int8"
                logger.info(f"🎵 [AUDIO] Loading Faster-Whisper model (small) on {self.device} ({compute_type})...")
                
                # Faster-Whisper loading is relatively fast but we still run in executor
                loop = asyncio.get_event_loop()
                self.model = await loop.run_in_executor(
                    None, 
                    lambda: WhisperModel("small", device=self.device, compute_type=compute_type)
                )
                logger.info("✅ [AUDIO] Faster-Whisper model loaded successfully.")
            except Exception as e:
                logger.error(f"❌ [AUDIO] Failed to load Faster-Whisper: {e}")

    async def process_audio(self, file_path: str) -> str:
        """
        Transcribes audio files into high-fidelity text.
        Handles slicing and format conversion automatically.
        """
        await self._load_model()
        
        if not self.model:
            return {"error": "Faster-Whisper engine not available."}

        try:
            # 1. Acoustic Pre-processing
            audio_info = AudioSegment.from_file(file_path)
            duration_sec = len(audio_info) / 1000.0
            
            # 2. Transcription Burst
            logger.info(f"🎵 [AUDIO] Transcribing {os.path.basename(file_path)} ({duration_sec:.1f}s)...")
            
            loop = asyncio.get_event_loop()
            # Faster-Whisper transcribe returns a generator (segments) and info
            def _run_transcribe():
                segments, info = self.model.transcribe(file_path, beam_size=5)
                # We MUST convert the generator to a list to actually run it in the thread
                return list(segments), info

            segments, info = await loop.run_in_executor(None, _run_transcribe)
            
            transcript_text = " ".join([s.text for s in segments]).strip()
            segment_data = [{"start": s.start, "end": s.end, "text": s.text} for s in segments]
            
            # 3. Intelligence Report Construction
            report = [
                "### [VOICE INTELLIGENCE REPORT]",
                f"**File**: {os.path.basename(file_path)}",
                f"**Duration**: {duration_sec:.2f} seconds",
                f"**Detected Language**: {info.language} (Confidence: {info.language_probability:.2f})",
                "\n**TRANSCRIPT**:",
                transcript_text or "[No speech detected]"
            ]
            
            logger.info(f"✅ [AUDIO] Transcription complete for {file_path}")
            return {
                "transcript": "\n".join(report),
                "text": transcript_text,
                "segments": segment_data,
                "duration": duration_sec,
                "language": info.language
            }
            
        except Exception as e:
            logger.error(f"❌ [AUDIO] Processing error for {file_path}: {e}")
            return {"error": str(e), "type": "audio"}

audio_intelligence = AudioProcessor()
