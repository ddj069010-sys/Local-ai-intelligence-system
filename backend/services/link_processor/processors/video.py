"""
services/link_processor/processors/video.py
- Downloads video, extracts audio via FFmpeg, transcribes via Whisper.
- Works for YouTube (via yt-dlp) and direct video links.
"""

import os
import tempfile
import subprocess
import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
import yt_dlp
import requests

logger = logging.getLogger(__name__)

WHISPER_MODEL_SIZE = "small"
_faster_whisper_cache = None

def _get_faster_whisper():
    global _faster_whisper_cache
    if _faster_whisper_cache is None:
        try:
            from faster_whisper import WhisperModel
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            logger.info(f"Loading Faster-Whisper model ({WHISPER_MODEL_SIZE}) on {device}...")
            _faster_whisper_cache = WhisperModel(WHISPER_MODEL_SIZE, device=device, compute_type=compute_type)
        except Exception as e:
            logger.error(f"Failed to load Faster-Whisper: {e}")
            return None
    return _faster_whisper_cache


def _extract_audio_from_file(video_path: str, out_path: str) -> bool:
    """Use ffmpeg to extract audio from a local video file."""
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-ac", "1", "-ar", "16000", out_path],
        capture_output=True, text=True
    )
    return result.returncode == 0

def _extract_frames_from_file(video_path: str, out_dir: str, interval: int = 10) -> List[str]:
    """Use ffmpeg to extract frames every N seconds."""
    frames_dir = os.path.join(out_dir, "frames")
    if not os.path.exists(frames_dir): os.makedirs(frames_dir)
    
    # Extract 1 frame every 'interval' seconds
    # -vf format=yuvj420p is for better quality extraction
    result = subprocess.run([
        "ffmpeg", "-y", "-i", video_path, 
        "-vf", f"fps=1/{interval}", 
        "-q:v", "2", 
        os.path.join(frames_dir, "frame_%04d.jpg")
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        frames = [os.path.join(frames_dir, f) for f in sorted(os.listdir(frames_dir))]
        return frames
    return []


def _download_youtube_audio(url: str, out_dir: str) -> tuple:
    """Download audio from YouTube using yt-dlp. Returns (path, title, description) tuple."""
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": os.path.join(out_dir, "audio.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
        }],
        "quiet": True,
        "no_warnings": True,
    }
    
    # --- PART 1: YT-DLP JS RUNTIME FIX ---
    try:
        # Check if node or nodejs exists
        for js_executable in ["node", "nodejs"]:
            node_check = subprocess.run([js_executable, "-v"], capture_output=True, text=True)
            if node_check.returncode == 0:
                logger.info(f"{js_executable} detected, enabling yt-dlp JS runtimes.")
                ydl_opts["js_runtimes"] = {js_executable: {}}
                break
        else:
            logger.warning("Node.js not detected. yt-dlp may have issues with some YouTube videos.")
    except Exception:
        logger.warning("Failed to check for Node.js. Continuing without JS runtimes.")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "Unknown Video")
            description = info.get("description", "")[:500]

        wav_path = os.path.join(out_dir, "audio.wav")
        if os.path.exists(wav_path):
            return wav_path, title, description
    except Exception as e:
        logger.error(f"yt-dlp error: {e}")
    return None, "Unknown", ""


def _fetch_transcript_v2(url: str) -> tuple:
    """Tries to fetch the transcript/subtitles directly from YouTube first."""
    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en", ".*"],
        "quiet": True,
        "js_runtimes": {"node": {}}
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "Unknown Video")
            description = info.get("description", "")[:500]
            
            # Check for subtitles
            subtitles = info.get("requested_subtitles")
            if subtitles:
                # This is complex to parse directly, but usually yt-dlp fetches them.
                # For simplicity in this local-first environment, 
                # if we can't easily parse them, we fall back to Whisper.
                pass
            
            return None, title, description # Fallback to Whisper for now, but title/desc fetched
    except Exception as e:
        logger.error(f"Transcript fetch error: {e}")
    return None, "Unknown", ""

async def process_video(url: str) -> dict:
    """Process a video URL: try transcript first, then fallback to Whisper."""
    with tempfile.TemporaryDirectory() as tmpdir:
        is_youtube = "youtube.com" in url or "youtu.be" in url
        
        # --- PART 3: TRANSCRIPT-FIRST PIPELINE ---
        transcript = ""
        segments = []
        title = "Unknown"
        description = ""
        duration = 0
        
        if is_youtube:
            # 1. Try fetching existing metadata and transcript
            _, title, description = _fetch_transcript_v2(url)
            # (In a real scenario, we'd parse subtitles here if available)
            
            # 2. Fallback to Audio extraction + Whisper
            audio_path, yt_title, yt_desc = _download_youtube_audio(url, tmpdir)
            if yt_title != "Unknown": title = yt_title
            if yt_desc: description = yt_desc
            
            # 3. 🖼️ EXTRACT FRAMES FOR VISUAL INTELLIGENCE
            # We use yt-dlp to download 1 small, low-res video file temporarily for frame extraction
            video_frames = []
            try:
                # Optimized for fast sampling
                frame_ydl_opts = {
                    "format": "worst", # Smallest video for frame extraction
                    "outtmpl": os.path.join(tmpdir, "video.mp4"),
                    "quiet": True,
                    "noplaylist": True,
                    "max_filesize": 50 * 1024 * 1024 # Limit to 50MB
                }
                with yt_dlp.YoutubeDL(frame_ydl_opts) as ydl:
                    ydl.download([url])
                video_frames = _extract_frames_from_file(os.path.join(tmpdir, "video.mp4"), tmpdir)
            except: pass
        else:
            # Direct video link: download then extract
            try:
                video_path = os.path.join(tmpdir, "video.mp4")
                with requests.get(url, stream=True, timeout=30) as r:
                    with open(video_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                audio_path = os.path.join(tmpdir, "audio.wav")
                title = url.split("/")[-1]
                video_frames = _extract_frames_from_file(video_path, tmpdir)
                if not _extract_audio_from_file(video_path, audio_path):
                    audio_path = None
            except Exception as e:
                logger.error(f"Direct download failed: {e}")
                audio_path = None

        if not audio_path or not os.path.exists(audio_path):
            return {
                "source": url,
                "title": title,
                "description": description,
                "transcript": "Audio/Transcript extraction failed. Using metadata summary.",
                "text": f"Title: {title}\nDescription: {description}",
                "segments": [],
                "error": "Audio extraction failed",
                "duration": duration
            }

        # Transcribe via Faster-Whisper
        try:
            model_engine = _get_faster_whisper()
            if not model_engine:
                raise Exception("Faster-Whisper engine not loaded")
                
            # beam_size=1 for maximum speed in research context (Turbo Mode)
            segments_gen, info = model_engine.transcribe(audio_path, beam_size=1)
            segments_list = list(segments_gen)
            
            transcript = " ".join([s.text for s in segments_list]).strip()
            segments = [{"start": s.start, "end": s.end, "text": s.text} for s in segments_list]
            
            # Duration detection
            duration = info.duration
            
            # 🧩 MULTIMODAL SYNC (Fusion of Sight & Sound)
            scene_narrative = []
            if video_frames:
                try:
                    from services.link_processor.processors.image import process_image_file
                    
                    # Run VLM extraction on all sampled frames async
                    async def extract_visual(frame_path, timestamp_idx):
                        try:
                            v_res = await process_image_file(frame_path, f"frame_{timestamp_idx}")
                            txt = v_res.get("text", "")
                            if txt: return f"[Frame {timestamp_idx}]: {txt}"
                        except: pass
                        return None
                    
                    tasks = [extract_visual(f, i*10) for i, f in enumerate(video_frames[:5])] # Limit to 5 frames max for speed
                    v_results = await asyncio.gather(*tasks)
                    scene_narrative = [r for r in v_results if r]
                except Exception as ve:
                    logger.error(f"VLM Visual extraction failed: {ve}")
                    scene_narrative = ["Video contains visual content. VLM extraction failed."]
            
            if not scene_narrative:
                scene_narrative = ["Video processing ran, but no clear visual narrative generated."]
            
        except Exception as e:
            logger.error(f"Whisper/Video processing failed: {e}")
            return {"error": str(e), "transcript": "", "source": url}

        return {
            "source": url,
            "title": title,
            "description": description,
            "transcript": transcript,
            "text": transcript,
            "segments": segments,
            "scenes": scene_narrative,
            "duration": duration,
            "error": None,
        }


def process_video_file(file_path: str, filename: str) -> dict:
    """Process an uploaded video file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.wav")
        if not _extract_audio_from_file(file_path, audio_path):
            return {"error": "FFmpeg extraction failed", "transcript": "", "source": filename}
        try:
            model_engine = _get_faster_whisper()
            if not model_engine:
                return {"error": "Faster-Whisper not loaded", "transcript": "", "source": filename}
                
            # beam_size=1 for maximum speed in research context (Turbo Mode)
            segments_gen, info = model_engine.transcribe(audio_path, beam_size=1)
            segments_list = list(segments_gen)
            transcript = " ".join([s.text for s in segments_list]).strip()
            segments = [{"start": s.start, "end": s.end, "text": s.text} for s in segments_list]
        except Exception as e:
            return {"error": str(e), "transcript": "", "source": filename}

    return {
        "source": filename,
        "title": filename,
        "transcript": transcript,
        "text": transcript,
        "segments": segments,
        "error": None,
    }
