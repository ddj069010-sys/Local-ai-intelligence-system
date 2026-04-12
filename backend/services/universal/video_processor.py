import os
import logging
import tempfile
import subprocess
import json
from typing import Dict, Any, List
from services.link_processor.processors.video import process_video_file as base_process_video_file, process_video as base_process_video_url
from services.link_processor.processors.image import process_image_file
from engine.utils import call_ollama_json
from engine.config import OLLAMA_MODEL
import asyncio

logger = logging.getLogger(__name__)

# --- UPGRADE 5: DEEP VIDEO ANALYSIS (REWRITE -> CHUNK -> SEARCH) ---

async def deep_video_transcript_search(transcript: str, segments: List[Dict[str, Any]], query: str, model: str = "gemma3:4b") -> Dict[str, Any]:
    """
    Step 5 Upgrade: Rewrite -> Chunk -> Search for precise video insights.
    """
    # 1. Rewrite for Video Context
    rewrite_prompt = f"Optimize this user query for searching a video transcript: '{query}'. Return JSON: {{\"optimized_query\": \"...\"}}"
    re_res = await call_ollama_json(rewrite_prompt, model)
    opt_query = re_res.get("optimized_query", query)
    
    # 2. Chunk with Timestamps (Logical Blocks)
    # We group segments into ~2 min chunks
    chunks = []
    current_chunk = []
    chunk_start = 0
    for seg in segments:
        current_chunk.append(seg.get("text", ""))
        if seg.get("end", 0) - chunk_start > 120:
            chunks.append({
                "text": " ".join(current_chunk),
                "start": chunk_start,
                "end": seg.get("end")
            })
            current_chunk = []
            chunk_start = seg.get("end")
            
    if current_chunk:
        chunks.append({"text": " ".join(current_chunk), "start": chunk_start, "end": segments[-1].get("end") if segments else chunk_start + 60})

    # 3. Search for best match
    search_prompt = f"Video Transcript Chunks:\n"
    for i, c in enumerate(chunks[:15]):
        search_prompt += f"[{i}] ({c['start']}s - {c['end']}s): {c['text'][:300]}...\n"
    
    search_prompt += f"\nQuery: {opt_query}\nTask: Identify which chunk indices [0-14] are most relevant. Return JSON: {{\"relevant_indices\": [0, 2]}}"
    search_res = await call_ollama_json(search_prompt, model)
    indices = search_res.get("relevant_indices", [0])
    
    top_context = "\n---\n".join([f"({chunks[idx]['start']}s): {chunks[idx]['text']}" for idx in indices if idx < len(chunks)])
    
    return {"context": top_context, "optimized_query": opt_query}

async def extract_frames(video_path: str, output_dir: str, interval: int = 5, max_frames: int = 15) -> List[Dict[str, Any]]:
    """Extracts key frames at specific intervals for visual analysis."""
    frames_data = []
    try:
        # Get video duration using ffprobe
        cmd_duration = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", video_path
        ]
        result = subprocess.run(cmd_duration, capture_output=True, text=True, check=False)
        duration = float(result.stdout.strip()) if result.stdout.strip() else 60.0
        
        # Determine extraction points
        all_ts = [i for i in range(0, int(min(duration, 300)), interval)]
        timestamps = []
        for i in range(min(len(all_ts), max_frames)):
            timestamps.append(all_ts[i])
        
        for ts in timestamps:
            frame_path = os.path.join(output_dir, f"frame_{ts}.jpg")
            # Seek to timestamp and extract one frame
            cmd = [
                "ffmpeg", "-y", "-ss", str(ts), "-i", video_path,
                "-frames:v", "1", "-q:v", "2", "-vf", "scale=640:-1", frame_path
            ]
            subprocess.run(cmd, capture_output=True, check=False)
            if os.path.exists(frame_path):
                frames_data.append({"path": frame_path, "timestamp": ts})
                
    except Exception as e:
        logger.error(f"Frame extraction failed: {e}")
    return frames_data

async def analyze_video_content(video_path: str, filename: str, style_preference: str = "detailed", duration: float = 0.0) -> Dict[str, Any]:
    """Enhanced video analysis: Combined Audio + Visual Intelligence with Length-Aware logic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Pipeline: Extract components
        res = base_process_video_file(video_path, filename)
        transcript = res.get("transcript", "")
        segments = res.get("segments", [])
        video_duration = duration if duration > 0 else res.get("duration", 0.0)
        
        # --- PART 5: LENGTH-AWARE PROCESSING ---
        mode = "normal"
        if video_duration > 0:
            if video_duration < 60: mode = "short"
            elif video_duration > 600: mode = "long"
        
        # Frame extraction: limit frequency for performance (Part 9)
        interval = 10 if mode == "long" else 5
        max_f = 10 if mode == "short" else 20
        frames_data = await extract_frames(video_path, tmpdir, interval=interval, max_frames=max_f)
        
        viz_results = []
        if mode != "short": # Skip deep visual analysis for very short videos (Part 5)
            async def process_single_frame(f_data):
                try:
                    vision_res = await process_image_file(f_data["path"], f"frame_{f_data['timestamp']}")
                    if vision_res.get("text"):
                        return f"[{f_data['timestamp']}s]: {vision_res['text']}"
                except Exception: return None

            viz_tasks = [process_single_frame(f) for f in frames_data]
            viz_results = await asyncio.gather(*viz_tasks)
        
        visual_insights = [r for r in viz_results if r]

        # --- PART 6 & 7: MULTI-LEVEL SUMMARIZATION & ANTI-HALLUCINATION ---
        anti_hallucination = "STRICT RULE: ONLY use information explicitly present in transcript or frames. DO NOT infer emotions or intent."
        
        if mode == "long":
            # Chunking transcript (Part 5)
            chunk_summaries = []
            words = transcript.split()
            # Approx 5 mins chunks (assuming 150 wpm)
            chunk_size = 750 
            for i in range(0, len(words), chunk_size):
                chunk_text = " ".join(words[i:i + chunk_size])
                chunk_prompt = f"Summarize this section of the video transcript concisely.\nSECTION: {chunk_text}\n{anti_hallucination}"
                summary = await call_ollama_json(chunk_prompt, OLLAMA_MODEL)
                chunk_summaries.append(summary.get("summary", ""))
            
            transcript_context = "COMBINED SECTION SUMMARIES:\n" + "\n".join(chunk_summaries)
        else:
            transcript_context = f"TRANSCRIPT SEGMENTS:\n{json.dumps(segments[:50], indent=2)}"

        # --- UPGRADE 5: INTEGRATED DEEP SEARCH ---
        deep_search_context = ""
        if style_preference != "concise" and transcript:
            deep_res = await deep_video_transcript_search(transcript, segments, filename, OLLAMA_MODEL)
            deep_search_context = f"\nDEEP TRANSCRIPT INSIGHTS:\n{deep_res['context']}"

        prompt = f"""
        Analyze this video content based on the provided context.
        
        VIDEO FILENAME: {filename}
        DURATION: {video_duration}s
        ANALYSIS MODE: {mode}
        
        {transcript_context}
        {deep_search_context}
        
        VISUAL CONTEXT:
        {" | ".join([str(vi) for vi in visual_insights]) if visual_insights else "No visual data available."}
        
        {anti_hallucination}
        
        TASKS:
        1. Multi-level summary: Short Summary, Key Points, Deep Insights.
        2. Content Breakdown: Logical segments (Intro, Main, Conclusion).
        3. Confidence score (High/Medium/Low).
        4. Specific Timing: Mention key timestamps for important moments.
        """
        
        analysis = await call_ollama_json(prompt, OLLAMA_MODEL)
        
        # --- PART 8: FORMAT CONTROL ---
        if mode == "short":
            formatted_output = f"""
## Video Summary: {filename} (Short)
- **Summary**: {analysis.get('short_summary', analysis.get('summary', ''))}
- **Key Points**: {analysis.get('key_points', 'N/A')}
- **Confidence**: {analysis.get('confidence', 'Medium')}
"""
        else:
            formatted_output = f"""
## Video Analysis: {filename}

### Summary
{analysis.get('short_summary', analysis.get('summary', ''))}

### Key Points
{analysis.get('key_points', 'N/A')}

### Content Breakdown
- **Intro**: {analysis.get('segmentation', {}).get('intro', 'N/A')}
- **Main**: {analysis.get('segmentation', {}).get('main', 'N/A')}
- **Conclusion**: {analysis.get('segmentation', {}).get('conclusion', 'N/A')}

### Confidence
**{analysis.get('confidence', 'Medium')}**
"""
        res["text"] = formatted_output
        res["duration"] = video_duration
        return res

async def process_video_file(file_path: str, filename: str, user_input: str = "") -> Dict[str, Any]:
    """Entry point for local video file processing with style detection."""
    # Detect style from user query
    style = "detailed"
    user_query = user_input.lower()
    if any(word in user_query for word in ["short", "brief", "concise", "quick"]):
        style = "concise"
    elif any(word in user_query for word in ["technical", "how it works", "deep dive", "under the hood"]):
        style = "technical"
    elif any(word in user_query for word in ["insight", "meaning", "interpretation", "why"]):
        style = "insight"
    
    return await analyze_video_content(file_path, filename, style_preference=style)

async def process_video_url(url: str) -> Dict[str, Any]:
    """Entry point for video URL processing."""
    res = await base_process_video_url(url)
    res["type"] = "video"
    
    # Check for duration and run length-aware analysis if possible
    # For URLs, we often only have audio/transcript.
    duration = res.get("duration", 0)
    # We don't have a local path for visual analysis here without downloading the full video,
    # so we'll stick to text-based analysis for now to keep it lightweight.
    return res
