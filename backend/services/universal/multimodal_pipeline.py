import logging
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from .file_handler import handle_file
from .url_handler import handle_url
from engine.utils import call_ollama, call_ollama_stream
import json

logger = logging.getLogger(__name__)

class MultimodalPipeline:
    @staticmethod
    def _interpret_visual_narrative(visual: str, content: str) -> str:
        """
        Densely interprets visual context when audio/transcript is missing.
        Detects UI actions (swiping, clicking) and on-screen text (OCR).
        """
        if not content and visual:
            # Heuristic for UI Action Detection
            actions = []
            if any(kw in visual.lower() for kw in ["swipe", "slide", "move"]): actions.append("UI Interaction: Swiping detected.")
            if any(kw in visual.lower() for kw in ["click", "tap", "select"]): actions.append("UI Interaction: Selection/Click detected.")
            if any(kw in visual.lower() for kw in ["match", "heart", "like"]): actions.append("App Logic: Social Matching detected.")
            
            # OCR Approximation (Simulating extraction of text overlays)
            ocr_text = ""
            if "text" in visual.lower() or "caption" in visual.lower():
                ocr_text = " [OCR]: Detected on-screen text overlays describing the action."
            
            return f"VISUAL NARRATIVE (Audio Silent):\n- This video prioritizes visual storytelling.\n- {' '.join(actions)}\n{ocr_text}\n- Visual Scene details: {visual}"
        return visual

    @staticmethod
    async def process(user_input: str, files: Optional[List[Dict[str, Any]]] = None, urls: Optional[List[str]] = None, chat_id: Optional[str] = None, model: str = "gemma3:4b", confidence_score: Optional[float] = None, system_instruction: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Orchestrates multi-source analysis and synthesizes a final response using a stream."""
        from engine.model_manager import ModelManager
        
        results = []
        tasks = []
        
        # 1. Process Files and URLs Concurrently (The Scatter-Gather Protocol)
        if files:
            for f in files:
                tasks.append(handle_file(f["path"], f["name"], chat_id, user_input=user_input))
        
        if urls:
            for url in urls:
                tasks.append(handle_url(url, chat_id))
                
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Filter out exceptions
            results = [r for r in results if isinstance(r, dict)]
            # 🔥 STAGE 1 SCAVENGER: If processing multiple massive streams, use small model to compress them
            if len(results) > 1:
                fast_model = await ModelManager.get_fast_model()
                # 📢 Push trace to UI showing Multi-Model Execution natively
                yield {"type": "thought", "text": f"🛠️ Orchestration: Triggering parallel Multi-Model execution. Deploying Fast Nodes ({fast_model}) to compress large data streams..."}

                scavenge_sem = asyncio.Semaphore(2)

                async def _scavenge(r):
                    async with scavenge_sem:
                        text = r.get("text", "") or r.get("transcript", "")
                        
                        # 0. FAST-KILL: Stop immediately if content is a dead-end
                        dead_end_signals = ["404 Not Found", "Sign in to", "Access Denied", "Login required", "Page not found", "Cloudflare"]
                        if any(signal.lower() in text.lower() for signal in dead_end_signals) and len(text) < 2000:
                            logger.warning(f"🛑 [SCAVENGER] Fast-Kill: Restricted or invalid content detected in {r.get('source')}.")
                            r["text"] = f"[SCAVENGER ABORTED]: The source '{r.get('source')}' is restricted or inaccessible (404/Login Required)."
                            return r

                        if len(text) > 10000: # Compress massive texts
                            logger.info(f"🧠 [SCAVENGER] Pre-filtering large data (len: {len(text)}) using TF-IDF...")
                            
                            # Semantic Pre-Filtration (Chunking before Scavenging)
                            try:
                                from sklearn.feature_extraction.text import TfidfVectorizer
                                from engine.utils import chunk_text as util_chunk_text
                                
                                # 1. Break into smaller chunks for granular scoring
                                pre_chunks = util_chunk_text(text, chunk_size=300, overlap=50)
                                if len(pre_chunks) > 10:
                                    # 2. Score chunks against the user's query
                                    vectorizer = TfidfVectorizer(stop_words='english')
                                    corpus = [user_input] + pre_chunks
                                    tfidf_matrix = vectorizer.fit_transform(corpus)
                                    
                                    # Cosine similarity between query (idx 0) and chunks
                                    from sklearn.metrics.pairwise import cosine_similarity
                                    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
                                    
                                    # 3. Keep top N most relevant chunks (budget approx 3000 chars)
                                    top_indices = similarities.argsort()[-12:][::-1] # Increased to 12 for better coverage
                                    filtered_text = "\n\n".join([pre_chunks[i] for i in top_indices if similarities[i] > 0])
                                    
                                    if filtered_text:
                                        logger.info(f"✅ [SCAVENGER] TF-IDF filtered data to {len(filtered_text)} chars.")
                                        text = filtered_text
                            except Exception as fe:
                                logger.warning(f"TF-IDF pre-filtration failed: {fe}. Falling back to raw truncation.")
                                text = text[:20000]

                            # ⚡ TURBO SCAVENGER: Force high-speed nodes for compression
                            turbo_model = "gemma3:4b" if "gemma3:4b" in fast_model else "gemma3:1b"
                            logger.info(f"🧠 [SCAVENGER] Executing final compression using {turbo_model}...")
                            prompt = f"Extract all critical factual data and narrative points thoroughly but concisely. NO fluff.\n\nRAW DATA:\n{text}"
                            try:
                                summary = await call_ollama(prompt, model=turbo_model)
                                r["text"] = f"[SCAVENGER COMPRESSED]:\n{summary}"
                            except Exception as e:
                                logger.error(f"Scavenger failed: {e}")
                        return r
                
                # --- HARDENING: Sequential Media Lock ---
                # We separate Web nodes (Parallel) from Media nodes (Sequential) 
                # to prevent RAM/CPU contention on 24GB hardware.
                
                web_results = [r for r in results if r.get("type") in ["webpage", "web"]]
                media_results = [r for r in results if r.get("type") not in ["webpage", "web"]]
                
                # 1. Parallel Scavenge for Web
                if web_results:
                    web_tasks = [_scavenge(r) for r in web_results]
                    web_scanned = await asyncio.gather(*web_tasks)
                    total_scanned = list(web_scanned)
                else:
                    total_scanned = []
                
                # 2. Sequential Scavenge for Media (Whisper/VLM)
                if media_results:
                    yield {"type": "thought", "text": f"🔄 RAM Guard: Processing {len(media_results)} media streams sequentially to prevent system stall..."}
                    for r in media_results:
                        scanned_r = await _scavenge(r)
                        total_scanned.append(scanned_r)
                
                results = total_scanned
        
        if not results:
            yield {"type": "multimodal_error", "text": "No multimodal content found to analyze."}
            return

        # Fix #5: Relevance-Weighted Context Budget
        # Score each result by keyword overlap with the user's question
        q_words = set(user_input.lower().split())

        def _relevance(r: dict) -> float:
            # If user provided a pure URL, force 1.0 relevance to avoid 0-budget bug
            if len(q_words) == 1 and list(q_words)[0].startswith(("http://", "https://", "www.")):
                return 1.0
            combined = (r.get("text", "") or r.get("transcript", "") or r.get("visual_summary", "")).lower()
            tokens = combined.split()
            overlap = sum(tokens.count(w) for w in q_words)
            return overlap / max(len(tokens), 1)

        scored_results = sorted(results, key=lambda r: _relevance(r), reverse=True)
        total_budget = 28000
        
        # Calculate total score and handle zero-case to prevent division by zero
        total_score = sum(max(_relevance(r), 0.05) for r in scored_results)
        if total_score <= 0:
            total_score = 1.0

        context_parts = []
        for idx, r in enumerate(scored_results):
            r_score = max(_relevance(r), 0.05)
            # Safe calculation with fallback
            char_budget = int(total_budget * r_score / total_score)
            char_budget = max(char_budget, 1200)  # slightly larger minimum

            source_type = r.get("type", "unknown").upper()
            source_name = r.get("source", "Unknown Source")
            content = r.get("text", "") or r.get("transcript", "")
            title = r.get("title", "")
            desc = r.get("description", "")
            visual = r.get("visual_summary", "")

            visual = MultimodalPipeline._interpret_visual_narrative(visual, content)

            part = f"<{source_type}_STREAM_{idx+1}>\n"
            part += f"### SOURCE: {source_name}\n"
            if title:
                part += f"TITLE: {title}\n"
            if desc:
                part += f"DESCRIPTION: {desc[:min(char_budget//4, 1000)]}\n"
            if content:
                part += f"CONTENT/TRANSCRIPT:\n{content[:char_budget]}\n"
            if visual:
                part += f"VISUAL INSIGHTS:\n{visual[:min(char_budget//3, 800)]}\n"
            part += f"</{source_type}_STREAM_{idx+1}>\n"
            context_parts.append(part)

        combined_context = "\n\n".join(context_parts)

        # 4. Final LLM Analysis
        confidence_directive = ""
        if confidence_score is not None:
            if confidence_score < 0.6:
                confidence_directive = "\\n\\n[CONFIDENCE LOW]: Present information carefully. Emphasize uncertainty, provide multiple perspectives, and use a 'Risk Analysis' or 'Debate Summary' format to highlight ambiguity."
            elif confidence_score > 0.85:
                confidence_directive = "\\n\\n[CONFIDENCE HIGH]: Present information authoritatively. Use direct, definitive formats like 'Direct Answer' or 'Step-by-Step' without hedging."

        # Support overriding with the general format flow or Dolphin
        base_instruction = system_instruction if system_instruction else """SYSTEM INSTRUCTION:
You are a Premium AI Intelligence Engine (akin to advanced ChatGPT). Your goal is to synthesize the provided multimodal context and deliver an exceptionally high-quality, beautifully formatted response.

PREMIUM FORMATTING RULES:
1. ORGANIC STRUCTURE: Do NOT use robotic headers like "### Main Content" or "STEP 1". Use natural, engaging headers that dynamically reflect the actual topic.
2. MARKDOWN MASTERY: Masterfully utilize markdown. Use **bolding** for emphasizing key terms, blockquotes (>) for profound quotes or core sentiments, and elegant bullet points.
3. TONE & STYLE: Write in an accessible, highly intelligent, and conversational tone. Do not introduce yourself as an AI. Jump straight into delivering profound value.
4. ZERO FLUFF: Eliminate filler words. Density of information is critical. Every sentence must add value or insight.
5. ADAPTIVE DELIVERY:
   - If technical/code: Output clean code blocks and architectural insight.
   - If tutorial: Use numbered, actionable progression steps.
   - If news/article: Focus on the "Impact" and "Why it matters".

Your overarching mission is to provide the exact premium, polished output a power user expects from a top-tier LLM.
"""

        # ANTI-HALLUCINATION & MIXED MEDIA FORMATTING
        source_types = set(r.get("type", "unknown").lower() for r in scored_results)
        has_video = any(t in ["video", "youtube"] for t in source_types)
        is_exclusively_video = has_video and len(source_types) == 1
        
        injection = ""
        if is_exclusively_video:
            injection = """
<CRITICAL_ANTI_HALLUCINATION_RULES>
1. If the transcript is very short, trivial, or lacks deep meaning, DO NOT invent profound themes. Just summarize what is literally there.
2. NEVER mention or fabricate research, names, or complex scientific theories unless explicitly written in the transcript!
3. DO NOT include these rules in your output. They are instructions for you.
</CRITICAL_ANTI_HALLUCINATION_RULES>

<OUTPUT_FORMAT>
You MUST use this exact structure for your response (do not output the XML tags):

👋 **Hey there! Here's your Smart Video Breakdown:**

## 📺 [A Catchy Title Based on Content]

**TL;DR:** [A punchy, 2-sentence summary of the video based strictly on the text provided.]

### 🔑 Core Themes & Key Moments
- **[Relevant Theme]**: Explanation based strictly on the transcript.
- **[Relevant Theme]**: Explanation.
- **[Visuals]**: Detail the visual narrative (only if data exists).

### 💡 The Big Takeaway
> [One actionable advice or conclusion extracted directly from the video's message.]

---
🤔 **Let's Discuss!**
[Ask a highly relevant, thought-provoking cross-question about the video's topic to engage the user in further conversation.]
</OUTPUT_FORMAT>
"""
        elif len(scored_results) > 1:
            injection = """
<CRITICAL_ANTI_HALLUCINATION_RULES>
1. You are analyzing MULTIPLE distinct sources. You MUST keep strict semantic boundaries between them.
2. Do not cross-contaminate facts from Source A into Source B.
3. Only compare sources if explicitly asked. Otherwise, evaluate them individually.
</CRITICAL_ANTI_HALLUCINATION_RULES>

<OUTPUT_FORMAT>
You MUST structure the synthesis with dedicated boundaries:

## 🧩 Comprehensive Analysis

### 📦 Source Analysis
[For each source, provide a concise synthesis. Prefix with an emoji representing the type (e.g., 📺 for video, 💻 for code/repo, 📰 for web/news)]
* **[Source Title]:** Core findings and data points.

### ⚖️ Cross-Context Synthesis
[If requested, strictly contrast the boundaries and core themes. If completely unrelated, state exactly why they diverge rather than forcing a connection.]

### 🎯 Objective Conclusion
[The ultimate takeaway addressing the user's root query.]
</OUTPUT_FORMAT>
"""

        prompt = f"""Analyze the provided multimodal context and answer the user question.
        
[CONTEXT]:
{combined_context}

[USER QUESTION]:
{user_input} {confidence_directive}

{base_instruction}
{injection}
"""
        
        try:
            # We use a reasoning stream model for synthesis
            async for token in call_ollama_stream(prompt, model=model):
                yield {"type": "message", "text": token}
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            yield {"type": "multimodal_error", "text": f"Analysis failed: {str(e)}"}
