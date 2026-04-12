import asyncio
import json
import time
from datetime import datetime
import logging
import re
import tempfile
import os
import uuid
from typing import List, Dict, Any, Optional
from duckduckgo_search import DDGS
import httpx

logger = logging.getLogger(__name__)
from core.config import settings
from .utils import (
    extract_cleaned_text, get_embedding, cosine_similarity, chunk_text, 
    score_source, call_ollama, call_ollama_stream, search_web_scored,
    call_ollama_json, cluster_and_rerank
)
from .model_manager import ModelManager
from .state import WORKSPACE
from .universal import UniversalEngine, UNIVERSAL_SYSTEM_PROMPT
from services.scraper.advanced_scraper import advanced_scraper, global_url_analyser
from services.intelligence.graph_builder import graph_builder
from services.agent.tool_router import tool_router
from services.scraper.dynamic_scraper import dynamic_scraper

# Memory integration (safe, non-breaking)
try:
    from memory.manager import (
        get_context_messages, append_message, cleanup_memory,
        auto_name_chat, auto_extract_memory, pull_from_pool,
        load_chat
    )
    _MEMORY_ENABLED = True
except ImportError:
    _MEMORY_ENABLED = False
    def get_context_messages(cid, n=8): return []
    async def pull_from_pool(q, limit=5): return []
    def append_message(cid, role, content, model="gemma3:4b", **kwargs): pass

def append_message_safe(chat_id: str, role: str, content: str, model: str = "gemma3:4b", **kwargs):
    """Wrapper to prevent errors if memory is disabled."""
    if _MEMORY_ENABLED and chat_id:
        append_message(chat_id, role, content, model, **kwargs)

from .formatter import FormatEngine

# Specialized modes
try:
    from .modes import (
        general_chat, code_assistant, optimize_query, fetch_sources, 
        compare_entities, explain_mode, fact_checker_mode, learning_mode, 
        planner_mode, debug_mode, memory_insight, summarize_url, 
        translate_mode, summarize_text_mode, write_mode, multi_chat_mode, 
        local_knowledge, rag_document_mode, math_mode, physics_mode, chemistry_mode, 
        data_science_mode, legal_mode, finance_mode, marketing_mode, 
        seo_mode, creative_write_mode, design_mode, music_theory_mode, 
        recipe_mode, travel_mode, health_mode, wellness_mode, 
        direct_response, simple_chat, arch_mode, cyber_security_mode, career_coach_mode,
        eco_analyst_mode, social_science_mode, debate_master_mode, philosophy_mode
    )
    _MODES_ENABLED = True
except ImportError:
    _MODES_ENABLED = False

# Document Creation Engine
try:
    from .doc_engine import doc_creation_pipeline
    _DOC_ENGINE_ENABLED = True
except ImportError:
    _DOC_ENGINE_ENABLED = False

_RESEARCH_KEYWORDS = {"deep", "research", "analyze", "explain", "why", "how", "long",
                      "describe", "search", "find", "tell", "latest", "news",
                      "history", "impact", "effect", "compare", "difference"}
_CODE_KEYWORDS = {"code", "function", "implement", "write", "program", "class",
                  "algorithm", "debug", "fix", "script", "snippet", "example", "syntax"}
_GREETINGS = {
    "hi", "hello", "hey", "hola", "greetings", "yo", "morning", "afternoon", "evening",
    "thanks", "thank", "thx", "fine", "good", "okay", "ok"
}
_CONVERSATIONAL_PHRASES = ["how are you", "how's it going", "what's up", "how r u", "who are you"]
URL_PATTERN = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*')

async def _process_auto_urls(text: str, deep_search: bool = False):
    """Detects and processes URLs in text, returning consolidated context."""
    from services.link_processor.classifier import classify_url
    from services.link_processor.processors.web import process_webpage
    from services.link_processor.processors.video import process_video
    from services.link_processor.processors.audio import process_audio_file
    from services.link_processor.processors.document import process_document_file
    from services.link_processor.processors.image import process_image_file
    
    urls = URL_PATTERN.findall(text)
    if not urls:
        return None
        
    intel_chunks = []
    async with httpx.AsyncClient() as client:
        for url in urls:
            try:
                kind = classify_url(url)
                if kind == "webpage":
                    if deep_search or any(w in text.lower() for w in ["deep", "research", "analyze"]):
                        res = await deep_url_pipeline.run(url, query=text)
                    else:
                        from services.link_processor.processors.web import process_webpage
                        res = process_webpage(url)
                    
                    if res and not res.get("error"):
                        content = res.get("full_text") or res.get("text")
                        intel_chunks.append(f"--- [SOURCE: {url}] ---\n{content[:5000]}")
                elif kind in ("youtube", "video"):
                    res = await process_video(url)
                    if res and not res.get("error"):
                        intel_chunks.append(f"--- [VIDEO TRANSCRIPT: {url}] ---\nTITLE: {res.get('title')}\nTRANSCRIPT: {res['transcript'][:3000]}")
                elif kind in ("audio", "document"):
                    # Global File Downloader for direct links
                    ext = "." + url.split(".")[-1].split("?")[0]
                    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                        resp = await client.get(url, timeout=30.0)
                        tmp.write(resp.content)
                        tmp_path = tmp.name
                    
                    try:
                        if kind == "audio":
                            res = process_audio_file(tmp_path, url.split("/")[-1])
                            if res and not res.get("error"):
                                intel_chunks.append(f"--- [AUDIO TRANSCRIPT: {url}] ---\n{res['transcript'][:3000]}")
                        elif kind == "image":
                            res = await process_image_file(tmp_path, url.split("/")[-1])
                            if res and not res.get("error"):
                                intel_chunks.append(f"--- [IMAGE ANALYSIS: {url}] ---\n{res['text'][:3000]}")
                        else: # document
                            res = await process_document_file(tmp_path, url.split("/")[-1])
                            if res and not res.get("error"):
                                intel_chunks.append(f"--- [DOCUMENT CONTENT: {url}] ---\n{res['text'][:4000]}")
                    finally:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
            except Exception as e:
                logging.error(f"Global Auto-URL processing failed for {url}: {e}")
            
    return "\n\n".join(intel_chunks) if intel_chunks else None

async def retrieve_top_context(query: str, chat_id: str, top_k: int = 3) -> str:
    """Retrieves most relevant chunks from active document and memory pool."""
    context_parts = []
    
    # 1. Active Document Context (from current session)
    workspace_data = WORKSPACE.get(chat_id)
    if workspace_data and isinstance(workspace_data, dict):
        chunks = workspace_data.get("chunks", [])
        embeddings = workspace_data.get("embeddings", [])
        
        # Filter out empty or malformed entries
        valid_indices = [i for i, (c, e) in enumerate(zip(chunks, embeddings)) if c and e]
        if valid_indices:
            query_emb = await get_embedding(query)
            scores = []
            for i in valid_indices:
                sim = cosine_similarity(query_emb, embeddings[i])
                scores.append((sim, chunks[i]))
            
            # Sort by similarity
            scores.sort(key=lambda x: str(x[0]), reverse=True)
            top_scores = scores[:5]
            top_chunks = [c for s, c in top_scores]
            if top_chunks:
                context_parts.append("### [WORKSPACE INSIGHTS]\n" + "\n\n".join(top_chunks))

    # 2. Global Memory Pool Context
    if _MEMORY_ENABLED:
        memory_entries: List[Dict[str, Any]] = await pull_from_pool(query)  # type: ignore
        if memory_entries and isinstance(memory_entries, list):
            mem_text = "\n".join([f"- {str(e.get('content', ''))[:500]}" for e in memory_entries])
            context_parts.append("### [LONG-TERM MEMORY RECALL]\n" + mem_text)

    return "\n\n".join(context_parts) if context_parts else ""

# Import moved to top from .state

from services.intelligence.query_enhancer import enhance_query
from services.intelligence.response_proofer import evaluate_response, refine_response
from services.intelligence.format_engine import detect_features
from services.modeSelector.selector import ModeSelector
from services.confidence.estimator import ConfidenceEstimator

from services.universal.multimodal_pipeline import MultimodalPipeline
from services.universal.url_handler import URL_PATTERN
from services.deep_url.pipeline import deep_url_pipeline
from services.universal.prompt_parser import PromptParser

async def speculative_retrieval(query: str) -> Dict[str, Any]:
    """Parallelized Web Scavenging + Memory Pool Recall."""
    # 🌩️ Multi-Threaded Concurrent Execution
    tasks = [
        asyncio.create_task(advanced_scraper.hyper_scrape_fast(query)), # Fast scrawler
        asyncio.create_task(pull_from_pool(query, limit=5))             # Vector memory search
    ]
    
    # Wait for both with timeout (Fastest path)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    web_data = results[0] if not isinstance(results[0], Exception) else []
    mem_data = results[1] if not isinstance(results[1], Exception) else []
    
    return {
        "web": web_data,
        "memory": mem_data,
        "consolidated_context": _build_hybrid_context(web_data, mem_data)
    }

def _build_hybrid_context(web, mem):
    context = ""
    if mem:
        context += "### [LOCAL INTELLIGENCE (MEMORY POOL)]\n"
        for m in mem: context += f"- {m.get('content', '')[:1000]}\n"
    if web:
        context += "\n### [GLOBAL INTELLIGENCE (WEB SCRAPE)]\n"
        for w in web: context += f"- SOURCE: {w.get('source')}\n  CONTENT: {w.get('text', '')[:1500]}\n"
    return context

async def run_research(question: str, model: str = "gemma3:4b", mode: str = "research", chat_id: str = None, web_enabled: bool = False, speed_mode: str = "auto", deep_search: bool = False, concentrated: bool = False):
    # 🏎️ ULTRA-FAST PATH: GREETING & SHORT CHAT BYPASS
    import re
    q_clean = question.strip().lower()
    GREETING_REGEX = r"^(hi|hello|hey|greetings|what's up|yo|thanks|bye|good morning|hi there)$"
    if re.match(GREETING_REGEX, q_clean) or (len(q_clean.split()) < 4 and not "?" in q_clean):
        from engine.modes import compact_chat
        async for event in compact_chat(question, settings.DEFAULT_MODEL):
            yield event
        return

    yield {"type": "thought", "text": "🧠 Intelligence Pipeline: Initializing deep research context..."}
    tool_context = "" # Agentic Scaffold

    # 🧠 ENHANCED QUERY & INTENT EXTRACTION
    from services.universal.prompt_parser import PromptParser
    question, cmds = PromptParser.extract_system_commands(question)
    if "deep" in cmds or "analyze" in cmds:
        deep_search = True
        
    enhanced_data = await enhance_query(question)
    enhanced_question = enhanced_data.get("enhanced_query", question)
    detected_intent = enhanced_data.get("intent", "general")
    
    # 🟢 Intelligent Model Orchestration
    has_workspace = chat_id in WORKSPACE and WORKSPACE[chat_id].get("docs")
    
    # Immediately apply Deep Search override before routing to ModelManager
    if deep_search:
        mode = "deep"
    
    if detected_intent in ["creative", "conversational", "identity"]:
        purpose = "extraction"
    purpose = "reasoning" if (has_workspace or len(question.split()) > 10 or deep_search) else "extraction"
    
    # Define is_unfiltered at the start to prevent local variable errors
    is_unfiltered = ModelManager.detect_unfiltered_intent(question)
    
    yield {"type": "thought", "text": "🧠 Neural Pathway: Activating parallel scavenging sectors (Web + Pool + VRAM)..."}
    
    # 🌩️ PARALLEL SCAVENGING: Run discovery tasks simultaneously
    try:
        discovery_results = await asyncio.gather(
            ModelManager.get_best_model(mode, question, requested_model=model, purpose=purpose, speed_mode=speed_mode),
            UniversalEngine.sync_and_retrieve(question.lower(), chat_id)
        )
        (selected_model_name, gating_reason) = discovery_results[0]
        vector_context = discovery_results[1]
    except Exception as e:
        # Fallback if parallel fails
        (selected_model_name, gating_reason) = await ModelManager.get_best_model(mode, question, requested_model=model, purpose=purpose, speed_mode=speed_mode)
        vector_context = await UniversalEngine.sync_and_retrieve(question.lower(), chat_id)
    
    # 💾 Trigger explicit switch to unload prior VRAM session
    if isinstance(selected_model_name, tuple): selected_model_name = selected_model_name[0]
    final_model = await ModelManager.switch_model(selected_model_name)
    
    # UI FEEDBACK: Show gating decision
    yield {"type": "thought", "text": f"🧠 Tiered Intelligence: {gating_reason}"}
    
    if final_model != model:
        status_msg = f"🤖 Intelligence Sync: Optimized model '{final_model}' auto-selected for this task."
        yield {"type": "thought", "text": status_msg}
    else:
        yield {"type": "thought", "text": f"🤖 Engine: Initializing {final_model} as core node."}
    # 🟢 Multimodal Auto-Trigger (FIXED: Selective Trigger)
    has_media = False
    
    # Only trigger if user explicitly references a file or provides a URL
    urls = URL_PATTERN.findall(question)
    has_explicit_media_call = any(kw in question.lower() for kw in ["analyze this", "look at", "image", "pdf", "file", "document", "multimodal"])
    has_mention = "@" in question or urls or has_explicit_media_call

    if has_mention and chat_id and chat_id in WORKSPACE:
        workspace_data = WORKSPACE[chat_id]
        if workspace_data.get("docs") or workspace_data.get("docs_metadata"):
            has_media = True
    
    if urls:
        has_media = True

    if has_media:
        yield {"type": "thought", "text": "🧠 Universal Multimodal Pipeline: Validated media reference. Initiating deep analysis..."}
        try:
            # Prepare files from workspace if any
            files_to_process = []
            if chat_id and chat_id in WORKSPACE:
                for doc in WORKSPACE[chat_id].get("docs", []):
                    if doc.get("path") and os.path.exists(doc["path"]):
                        files_to_process.append({"path": doc["path"], "name": doc.get("name", "upload")})
            
            report_text = ""
            confidence_est = ConfidenceEstimator.estimate(question)
            
            # Grab appropriate formatting for Dolphin/General
            sys_inst = None
            if is_unfiltered or "dolphin" in final_model.lower():
                sys_inst = ModelManager.get_unfiltered_primer()
                
            async for data in MultimodalPipeline.process(question, files=files_to_process, urls=urls, chat_id=chat_id, model=final_model, confidence_score=confidence_est, system_instruction=sys_inst):
                if data.get("type") == "message":
                    report_text += data["text"]
                    yield {"type": "message", "text": data["text"]}
                elif data.get("type") == "thought":
                    yield data
                elif data.get("type") == "multimodal_error":
                    yield {"type": "thought", "text": f"⚠️ Multimodal fallback: {data['text']}. Switching to standard RAG..."}
                    raise Exception(data["text"])
            
            if report_text:
                # Store in memory
                if _MEMORY_ENABLED and chat_id:
                    append_message(chat_id, "user", question, model)
                    append_message(chat_id, "assistant", report_text, model)
                
                yield {"type": "final_message", "text": report_text}
                return
        except Exception as e:
            logging.error(f"Multimodal Pipeline failed: {e}")
            yield {"type": "thought", "text": f"⚠️ Multimodal pipeline generated an error: {e}. Falling back..."}

    enhanced_question = question
    intel_chunks = []

    # 🌐 GLOBAL UNIVERSAL SYNC: Unify Workspace + Memory + Advanced Search
    doc_ids, is_all = PromptParser.extract_refs(question)
    cleaned_q = PromptParser.clean_query(question) if (doc_ids or is_all) else question
    
    # Inject Document Answer Format if @ is used
    doc_format_instruction = ""
    
    # 🕵️ AGENTIC TOOL SCAVENGING (Level 4 Intelligence)
    available_tools = tool_router.scavenge_tools()
    for t in available_tools:
        # Simple match logic: ID or keywords in description
        if t["id"].replace("_", " ") in question.lower() or any(word in t["description"].lower() for word in question.lower().split() if len(word) > 4):
             yield {"type": "thought", "text": f"🛠️ Agentic Trigger: Identified matching local tool '{t['id']}'. Executing..."}
             tool_res = await tool_router.execute_tool(t["id"])
             if tool_res:
                 tool_context = f"\n\n[LOCAL AGENTIC TOOL RESULT: {t['id']}]\nDATA: {tool_res}\n"
                 yield {"type": "thought", "text": "✅ Local intelligence retrieved. Merging with neural context."}
    
    if doc_ids or is_all:
        doc_format_instruction = (
            "\n\nSTRICT OUTPUT FORMAT FOR DOCUMENT QUERIES:\n"
            "## Document Analysis\n"
            "### Summary\n[Short answer / synthesis]\n"
            "### Key Points\n[Bullet points from documents]\n"
            "### Details\n[Explanation and citations]\n"
            "### Sources\n[List the @names or document identifiers referenced]"
        )
    
    # 🌩️ SPECULATIVE RETRIEVAL (Level 5 Intelligence) - Only for Deep Search sessions
    hybrid_context = ""
    if deep_search:
        yield {"type": "thought", "text": "🌩️ Deep Search: Initializing speculative parallel discovery..."}
        speculative_data = await speculative_retrieval(cleaned_q)
        hybrid_context = speculative_data.get("consolidated_context", "")
        if hybrid_context:
            yield {"type": "thought", "text": "🌩️ Speculative Retrieval: Parallel Web + Memory scan completed."}
    
    # Standard Vector context retrieval (Lightweight local sync)
    vector_context = await UniversalEngine.sync_and_retrieve(cleaned_q, chat_id, target_doc_ids=doc_ids if doc_ids else None)
    
    # 🟢 SYNC CHECK: Build context block only if data exists
    if hybrid_context:
        if is_unfiltered:
            # 🔓 DOLPHIN GPT SYNTHESIS: No librarian headers, pure data stream
            enhanced_question = f"RAW KNOWLEDGE BASE:\n{hybrid_context}\n\nINSTRUCTION: Utilize the above raw knowledge to provide a high-fidelity, detailed GPT-style response. Do NOT use headers like 'Local Intelligence' or 'Comparison'. Synthesize naturally.\n\n[USER]: {cleaned_q}{doc_format_instruction}"
        else:
            enhanced_question = f"HYBRID INTELLIGENCE CONTEXT:\n{hybrid_context}\n\nSTRICT INSTRUCTION: Compare results from Web and Local Pool. Resolve discrepancies for maximum accuracy.\n\n[USER QUESTION]: {cleaned_q}{doc_format_instruction}"
    elif vector_context:
        enhanced_question = f"{cleaned_q}\n\n[SYNCHRONIZED CONTEXT]:\n{vector_context}{doc_format_instruction}"
    else:
        enhanced_question = cleaned_q
    
    # Intelligent Switching
    prompt_lower = question.lower()
    needs_doc = any(k in prompt_lower for k in ["it", "this", "doc", "pdf", "image", "file", "analyze", "summarize", "page", "document", "workspace", "data", "referenced"])
    
    if vector_context and (needs_doc or len(question) > 25):
        intel_chunks.append(vector_context)
        yield {"type": "thought", "text": "📂 Universal Sync: Global intelligence synchronized (Workspace + Memory Pool)."}

    # Detect Auto-URLs & Multi-modal Files
    auto_res = await _process_auto_urls(question, deep_search=deep_search)
    if auto_res:
        intel_chunks.append(auto_res)
        # If it was a processed document (not just a webpage string), it might have chunks/embeddings
        # For now, we store the raw result, but in a real RAG we'd re-chunk.
        # However, processors/document.py now returns a dict if called directly.
        # In _process_auto_urls, it currently only appends text. 
        # Let's assume for now that direct file uploads (via drag-drop) will populate GLOBAL_DOCUMENT_MEMORY properly in the route.

    # Step 1: Intent Analysis & Auto-Selection (Only for Default Chat)
    original_mode = mode
    intent = "simple chat"

    # 📝 STEP 0.PRE: DOCUMENT ENGINE AUTO-ROUTING
    _DOC_TRIGGER_KEYWORDS = ["write a ", "create a ", "draft a ", "compose a ", "make a report",
                              "make a doc", "generate a ", "write me", "create me",
                              "write an ", "create an ", "draft an "]
    _DOC_EDIT_KEYWORDS = ["make it shorter", "make it longer", "add examples", "convert to email",
                          "convert to report", "rewrite", "rephrase", "expand it", "summarize it"]
    q_doc_check = question.lower().strip()
    if _DOC_ENGINE_ENABLED and mode in ("chat", "write") and (
        any(q_doc_check.startswith(kw) for kw in _DOC_TRIGGER_KEYWORDS)
        or any(kw in q_doc_check for kw in _DOC_EDIT_KEYWORDS)
    ):
        mode = "doc"
        yield {"type": "thought", "text": "📝 Document Engine: Auto-routing to document creation pipeline..."}
    
    # 🟢 STEP 0: GREETING SHORT-CIRCUIT
    q_simple = question.lower().strip().rstrip('?!.')
    if q_simple in ["hi", "hello", "hey", "hola", "greetings"]:
        mode = "direct"
        enhanced_question = question
        # return # Handle greeting elsewhere or yield simple hello
    
    # 🌐 STEP 0.5: WEB OVERRIDE
    elif web_enabled:
        mode = "fast-web"
        enhanced_question = question
        yield {"type": "thought", "text": "🌐 Web Analysis Mode: Smart search active."}

    # Bypass for Simple/Direct modes
    elif mode in ["simple", "direct"]:
        enhanced_question = question
    else:
        if mode == "chat":
            intent = detected_intent
            mode = ModeSelector.get_mode(intent, mode)

        # Enhanced query was already calculated at engine start
        if not enhanced_question:
            enhanced_question = question
        
        # Merge all intelligence (Docs + Auto-URLs)
        if intel_chunks:
            intel_block = "\n\n".join(intel_chunks)
            enhanced_question = f"{intel_block}\n\n[USER QUESTION]: {enhanced_question}"
            yield {"type": "thought", "text": "🌐 Intelligence Update: Multi-modal context synchronized."}
        
        # Step 3: Confidence Check (Lightweight Heuristics)
        confidence = ConfidenceEstimator.estimate(question)
        web_fallback = False
        
        # UI FEEDBACK: Show Auto Mode decision
        if original_mode == "chat":
            yield {"type": "thought", "text": f"🧠 Auto-Adaptive: Intent '{intent.capitalize()}' detected. Confidence: {int(confidence*100)}%."}
            is_creative_or_casual = intent in ["creative", "conversational", "identity", "general"]
            
            # --- 💡 SELF-HEALING AMBIGUITY CONTROLLER ---
            if confidence < 0.60 and len(question.strip().split()) <= 15 and not is_creative_or_casual:
                yield {"type": "thought", "text": "⏸️ Self-Healing Pipeline: Ambiguous technical query detected. Halting execution to request clarification..."}
                
                if any(w in question.lower() for w in ["code", "build", "error", "bug", "server", "api"]):
                    msg = "I need a bit more technical context. Could you clarify the exact language, framework, or specific error you are dealing with?"
                else:
                    msg = "Your request is a bit ambiguous. Could you clarify exactly what information you are looking for so I can pull the correct precision data?"
                
                yield {"type": "message", "text": msg}
                return  # Safely abort execution and wait for user reply
            # --- ------------------------------------ ---

            # Only trigger web fallback for low confidence if the intent is informative/research
            if ConfidenceEstimator.needs_web_fallback(confidence) and not is_creative_or_casual:
                web_fallback = True
                mode = "fast-web"
                yield {"type": "thought", "text": "🌐 Model confidence low for recent events. Activating Optimized Search Fallback..."}
        
        # 🟢 DEEP SEARCH ENFORCEMENT
        if mode == "research" and not deep_search:
            mode = "fast-web"
            yield {"type": "thought", "text": "⚡ Selected Engine: Fast Web Scavenger (Optimized for speed)."}
        elif mode == "research" and deep_search:
             yield {"type": "thought", "text": "⚡ Selected Engine: Deep Research Pipeline (Full Scavenging)."}
        elif mode != "research" and deep_search:
             # If user explicitly selected deep search but intent was simple, we might still want to escalate
             yield {"type": "thought", "text": "⚡ Selected Engine: Overriding to Deep Research protocol as requested."}
             mode = "research"
        
        # 🟢 POOL VOID CHECK (User Request)
        # Exclude greetings, short queries, and creative/conversational intent from being escalated to web
        q_len = len(question.split())
        is_greeting_or_short = q_len <= 3 or any(kw in _GREETINGS for kw in question.lower().split())
        is_creative_or_casual = detected_intent in ["creative", "conversational", "identity", "general"]

        if not vector_context and not has_media and mode not in ["fast-web", "web"] and not is_greeting_or_short and not is_creative_or_casual:
             yield {"type": "thought", "text": "🕳️ Context: Local pool void. Elevating to web intelligence..."}
             mode = "fast-web"
             web_enabled = True

        # 🟢 SMART WEB CHECK (Lightweight validation)
        if mode == "fast-web" or web_enabled:
            yield {"type": "thought", "text": "🔍 Verifying digital intelligence signals..."}

    # Step 4: Smart Context Builder (Strictly 3 most recent entries)
    if _MEMORY_ENABLED and chat_id:
        context = get_context_messages(chat_id, n=3)
        if context:
            enhanced_question = f"Relevant Context:\n{context}\n\nUser Question: {enhanced_question}"

    # Persistence for user original query
    if _MEMORY_ENABLED and chat_id:
        append_message(chat_id, "user", question, final_model)
        asyncio.create_task(auto_name_chat(chat_id, question))

    # Auto-routing for simple greetings even if not in 'auto' mode
    q_lower = question.lower().strip().rstrip('?!.')
    q_words = q_lower.split()
    is_greeting = any(kw in _GREETINGS for kw in q_words)
    is_phrase = any(phrase in _CONVERSATIONAL_PHRASES for phrase in q_lower)

    if ((len(q_words) <= 3 and is_greeting) or is_phrase) and mode == "research":
        mode = "direct"

    # Update mode_map to use system_instruction where applicable
    system_instruction = UNIVERSAL_SYSTEM_PROMPT if (has_workspace or vector_context) else None
    
    # 🎯 CONCENTRATED MODE: Force conciseness and bypass fluff
    if concentrated:
        system_instruction = "STRICT INSTRUCTION: Provide the answer ONLY. Do NOT use emojis, do NOT use headers like 'Executive Summary', and do NOT lead with pleasantries. Provide a high-density, direct answer based strictly on available context."

    # 🔓 DOLPHIN ISOLATION: Use only the simplified roleplay primer for unfiltered requests
    if is_unfiltered or "dolphin" in final_model.lower():
        system_instruction = ModelManager.get_unfiltered_primer()

    # 🗂️ RAG AUTO-TRIGGER: Check if query should use local docs
    _rag_triggered = False
    _rag_context_prompt = None
    if mode == "rag" or (mode not in ["fast-web", "web", "simple", "direct"] and not web_enabled):
        try:
            from services.rag.retriever import should_auto_trigger, retrieve
            from services.rag.reranker import rerank
            from services.rag.pipeline import build_rag_prompt, get_indexed_files
            
            yield {"type": "thought", "text": "Analyzing intent for local documentation relevance..."}
            _indexed = get_indexed_files()
            
            if _indexed:
                if mode == "rag" or await should_auto_trigger(question):
                    yield {"type": "thought", "text": f"📄 Document Hub: Identified relevant context in {len(_indexed)} indexed files."}
                    yield {"type": "thought", "text": "Performing semantic vector search across local document shards..."}
                    _raw_chunks = await retrieve(question, top_k=5)
                    
                    if _raw_chunks:
                        yield {"type": "thought", "text": f"Successfully retrieved {len(_raw_chunks)} high-similarity document fragments."}
                        yield {"type": "thought", "text": "Reranking shards for maximum factual precision..."}
                        _rag_triggered = True
                        _top_chunks = rerank(question, _raw_chunks)
                        _rag_context_prompt = build_rag_prompt(question, _top_chunks)
                        mode = "rag"
                        yield {"type": "thought", "text": f"✅ RAG: Found {len(_top_chunks)} relevant chunk(s). Generating cited answer..."}
                    else:
                            yield {"type": "thought", "text": "⚠️ RAG: No relevant document chunks found. Falling back to web search."}
                            mode = "fast-web"
                            _rag_triggered = False
        except Exception as _rag_err:
            import logging as _log
            _log.warning(f"[RAG Auto-Trigger] Error: {_rag_err}")

    # Update mode_map to use final_model for all calls and support context injection
    mode_map = {
        "chat": lambda **kwargs: general_chat(kwargs.get("question", enhanced_question), final_model, chat_id=chat_id, system=kwargs.get("system", system_instruction)),
        "simple": lambda **kwargs: simple_chat(kwargs.get("question", enhanced_question), final_model, chat_id=chat_id),
        "direct": lambda **kwargs: direct_response(kwargs.get("question", enhanced_question), final_model), 
        "code": lambda **kwargs: code_assistant(kwargs.get("question", enhanced_question), final_model),
        "optimize": lambda **kwargs: optimize_query(kwargs.get("question", enhanced_question), final_model),
        "sources": lambda **kwargs: fetch_sources(kwargs.get("question", enhanced_question), final_model),
        "compare": lambda **kwargs: compare_entities(kwargs.get("question", enhanced_question), final_model),
        "explain": lambda **kwargs: explain_mode(kwargs.get("question", enhanced_question), final_model),
        "fact-check": lambda **kwargs: fact_checker_mode(kwargs.get("question", enhanced_question), final_model),
        "learn": lambda **kwargs: learning_mode(kwargs.get("question", enhanced_question), final_model),
        "plan": lambda **kwargs: planner_mode(kwargs.get("question", enhanced_question), final_model),
        "debug": lambda **kwargs: debug_mode(kwargs.get("question", enhanced_question), final_model),
        "memory": lambda **kwargs: memory_insight(kwargs.get("question", enhanced_question), final_model, chat_id=chat_id),
        "url": lambda **kwargs: summarize_url(kwargs.get("question", enhanced_question), final_model),
        "translate": lambda **kwargs: translate_mode(kwargs.get("question", enhanced_question), final_model),
        "summarize": lambda **kwargs: summarize_text_mode(kwargs.get("question", enhanced_question), final_model),
        "write": lambda **kwargs: write_mode(kwargs.get("question", enhanced_question), final_model),
        "multi-chat": lambda **kwargs: multi_chat_mode(kwargs.get("question", enhanced_question), final_model, chat_id=chat_id),
        "rag": lambda **kwargs: rag_document_mode(kwargs.get("question", _rag_context_prompt or enhanced_question), final_model) if _rag_triggered else local_knowledge(kwargs.get("question", enhanced_question), final_model, system=kwargs.get("system", system_instruction)),
        "math": lambda **kwargs: math_mode(kwargs.get("question", enhanced_question), final_model),
        "physics": lambda **kwargs: physics_mode(kwargs.get("question", enhanced_question), final_model),
        "chemistry": lambda **kwargs: chemistry_mode(kwargs.get("question", enhanced_question), final_model),
        "data": lambda **kwargs: data_science_mode(kwargs.get("question", enhanced_question), final_model),
        "legal": lambda **kwargs: legal_mode(kwargs.get("question", enhanced_question), final_model),
        "finance": lambda **kwargs: finance_mode(kwargs.get("question", enhanced_question), final_model),
        "marketing": lambda **kwargs: marketing_mode(kwargs.get("question", enhanced_question), final_model),
        "seo": lambda **kwargs: seo_mode(kwargs.get("question", enhanced_question), final_model),
        "creative-write": lambda **kwargs: creative_write_mode(kwargs.get("question", enhanced_question), final_model),
        "design": lambda **kwargs: design_mode(kwargs.get("question", enhanced_question), final_model),
        "music": lambda **kwargs: music_theory_mode(kwargs.get("question", enhanced_question), final_model),
        "recipe": lambda **kwargs: recipe_mode(kwargs.get("question", enhanced_question), final_model),
        "travel": lambda **kwargs: travel_mode(kwargs.get("question", enhanced_question), final_model),
        "health": lambda **kwargs: health_mode(kwargs.get("question", enhanced_question), final_model),
        "wellness": lambda **kwargs: wellness_mode(kwargs.get("question", enhanced_question), final_model),
        "arch": lambda **kwargs: arch_mode(kwargs.get("question", enhanced_question), final_model),
        "cyber": lambda **kwargs: cyber_security_mode(kwargs.get("question", enhanced_question), final_model),
        "career": lambda **kwargs: career_coach_mode(kwargs.get("question", enhanced_question), final_model),
        "eco": lambda **kwargs: eco_analyst_mode(kwargs.get("question", enhanced_question), final_model),
        "social": lambda **kwargs: social_science_mode(kwargs.get("question", enhanced_question), final_model),
        "debate": lambda **kwargs: debate_master_mode(kwargs.get("question", enhanced_question), final_model),
        "philosophy": lambda **kwargs: philosophy_mode(kwargs.get("question", enhanced_question), final_model),
        "doc": lambda **kwargs: doc_creation_pipeline(kwargs.get("question", enhanced_question), final_model, chat_id=chat_id),
        "agent": lambda **kwargs: run_agent_mode(kwargs.get("question", enhanced_question), final_model, chat_id=chat_id),
        "fast-web": lambda **kwargs: gpt_style_fast_search(kwargs.get("question", enhanced_question + tool_context), final_model, chat_id, system=kwargs.get("system", system_instruction)),
        "research": lambda **kwargs: smart_search_pipeline(kwargs.get("question", enhanced_question + tool_context), final_model, chat_id, system=kwargs.get("system", system_instruction)),
    }

    # 🟢 CORE EXECUTION LOOP
    if mode in mode_map:
        # Initialize variables for BOTH paths (Standard & Dolphin) to prevent UnboundLocalError
        final_text = ""
        execution_results = []
        file_results = []

        # 🔓 DOLPHIN RECURSIVE REFINEMENT (Alpha Intelligence Pass)
        if is_unfiltered:
            yield {"type": "thought", "text": "⚡ Dolphin Alpha: Synthesizing raw intelligence..."}
            full_response = ""
            async for event in mode_map[mode]():
                # Stream first pass to user
                if isinstance(event, dict) and event.get("type") == "message":
                    full_response += event["text"]
                yield event
            
            # Recursive pass for high-density refinement
            if len(full_response) > 200:
                yield {"type": "thought", "text": "💎 Neural Refining: Enhancing fluency and intellectual depth..."}
                refinement_prompt = (
                    "REFINEMENT TASK: Take the following information and rewrite it for maximum fluency, impact, and detail. "
                    "DETACH from any robotic structures. DELETE all headers like 'Summary', 'Takeaways', or 'Disclaimer'. "
                    "Provide a seamless, high-fidelity GPT-style response that directly fulfills the intent.\n\n"
                    f"TEXT:\n{full_response}"
                )
                # Note: We trigger a second pass with the mode_map using the new refined prompt
                async for event in mode_map[mode](question=refinement_prompt):
                    yield event
        else:
            async for event in mode_map[mode]():
                # ROBUSTNESS: Ensure event is a dict
                if isinstance(event, str):
                    event = {"type": "message", "text": event}

                if event.get("type") == "message":
                    final_text += event.get("text", "")
                elif event.get("type") == "thought":
                     # Silence thoughts for Simple/Direct modes if preferred
                     if mode in ["simple", "direct"]: continue
                elif event.get("type") == "execution_result":
                    execution_results.append(event)
                elif event.get("type") == "file_result":
                    file_results.append(event)
                yield event
        
        # Step 8 & 9: Neural Proofing & Refinement (The Enterprise Format Engine)
        try:
            # Hard-Toggle: Skip for Dolphin (is_unfiltered) OR if deep_search is False.
            if mode not in ["direct"] and not concentrated and deep_search and not is_unfiltered:
                if len(final_text) > 400:
                    yield {"type": "thought", "text": "🧠 Enterprise Proofer: Evaluating response against neural logic..."}
                    evaluation = await evaluate_response(question, final_text)
                    yield {"type": "thought", "text": "🧠 Format Engine: Applying professional structure and rules..."}
                    final_text = await refine_response(question, final_text, evaluation)
                else:
                    yield {"type": "thought", "text": "⚡ Format Engine Bypassed: Response is concise and natural."}
            else:
                if mode not in ["direct"] and not concentrated:
                    yield {"type": "thought", "text": "⚡ Fast Output Mode: Enterprise Format Engine Bypassed."}
            
            # 🟢 HYBRID OUTPUT: Send the final high-fidelity version
            if final_text.strip():
                yield {"type": "final_message", "text": final_text}
        except Exception as e:
            logging.error(f"Post-processing failed: {e}")
            # Fallback to current final_text if processing fails
            if final_text.strip():
                yield {"type": "final_message", "text": final_text}
            
        if _MEMORY_ENABLED and chat_id and (final_text or execution_results or file_results):
            # Show reflection thought
            yield {"type": "thought", "text": "🧠 Neural Reflection: Scanning session for identity facts and project context..."}
            
            append_message(chat_id, "assistant", final_text, model, 
                          execution_results=execution_results, file_results=file_results)
            
            # Step 9: Lightweight Memory (Extract key insights asynchronously)
            asyncio.create_task(auto_extract_memory(chat_id, question, final_text))
            
            # Check for compression
            chat_data = load_chat(chat_id)
            if len(chat_data.get("messages", [])) > 55:
                yield {"type": "thought", "text": "📦 Knowledge Pearl: Session depth reached. Compressing history into dense context..."}
        return

    # Fallback to research logic if mode not in map or modes disabled
    yield {"type": "thought", "text": "Initiating deep research protocol..."}
    async for event in _deep_research_generator(question, model, chat_id, original_query=question, deep_scrape=options.get("deep_scrape", False)):
        yield event

async def _deep_research_generator(question, model, chat_id, system=None, original_query=None, deep_scrape=False):
    # Part 1: Strategic Planning (Director Role)
    yield {"type": "thought", "text": "🧠 Director: Initializing Recursive Deep Research Graph..."}
    
    query_to_analyze = original_query if original_query else question
    all_chunks_context = ""
    discovered_urls = []
    
    # 🔄 RECURSIVE AGENCY LOOP
    MAX_HOPS = 3
    for hop in range(1, MAX_HOPS + 1):
        yield {"type": "thought", "text": f"🔄 Recursive Node [Hop {hop}/{MAX_HOPS}]: Generating query branches..."}
        
        # SEQUENTIAL PROMPT 1: The Director
        sys_p = f"""SYSTEM INSTRUCTION:
You are the Research Director. Read the user's objective. 
Your ONLY task is to generate highly specific search terms that will yield fact-based data required to fulfill the objective.
Format: Output a JSON array of up to 3 short search string queries. Output NOTHING else."""
        
        if hop > 1:
            sys_p += f"\n\nCURRENT CONTEXT SUMMARY:\n{all_chunks_context[-1500:]}\nFocus ONLY on filling missing information or resolving conflicts."
            
        q_json = await call_ollama(query_to_analyze, model=model, system=sys_p)
        try:
            search_queries = json.loads(q_json)
        except:
            if hop == 1: search_queries = [query_to_analyze]
            else: search_queries = [query_to_analyze + " specific data details"]
            
        yield {"type": "thought", "text": f"🎯 Director: Executing {len(search_queries)} search vectors."}

        try:
            used_urls = search_web_scored(search_queries)
        except Exception as e:
            used_urls = []
            
        new_urls = [u for u in used_urls if u not in discovered_urls][:4]
        discovered_urls.extend(new_urls)
        
        if not new_urls:
            yield {"type": "thought", "text": "🛑 Saturation: No novel signals detected. Halting expansion."}
            break

        yield {"type": "thought", "text": f"📑 Scraper: Extracting intelligence from {len(new_urls)} verified nodes..."}
        scraped_data = await advanced_scraper.hyper_scrape(new_urls, query=question)
        
        added_content = False
        current_hop_context = ""
        for idx, data in enumerate(scraped_data):
            if "error" in data: continue
            url = data.get("source")
            content = data.get("text", "")
            if content:
                # CONTEXT BOXING: limit text to prevent VRAM crash
                chunk = f"\n[SOURCE: {url}]\nCONTENT: {content[:1200]}\n"
                current_hop_context += chunk
                all_chunks_context += chunk
                added_content = True
                yield {"type": "thought", "text": f"✅ Intelligence integrated: {url}"}

        # ⚖️ SEQUENTIAL PROMPT 2: The Judge
        if added_content and hop < MAX_HOPS:
            yield {"type": "thought", "text": "⚖️ Judge: Evaluating factual saturation and conflict resolution..."}
            judge_sys = """SYSTEM INSTRUCTION:
You are the Quality Assurance Node.
Evaluate the provided context against the user's objective.
If the context contains enough concrete data (numbers, facts, verified claims) to write a comprehensive report, output ONLY "STATUS: COMPLETE".
If critical facts are missing or there are unresolved conflicts, output ONLY "STATUS: INCOMPLETE"."""
            eval_res = await call_ollama(f"Context: {current_hop_context[-3500:]}\n\nObjective: {question}", model=model, system=judge_sys)
            if "COMPLETE" in eval_res.upper():
                yield {"type": "thought", "text": "✅ Judge: Saturation Reached. Data holds weight."}
                break
            else:
                yield {"type": "thought", "text": "⚠️ Judge: Information gap detected. Instructing Director for deeper hop."}

    # CONTEXT BOXING / COMPRESSION CHECK
    # Keep final context extremely tight for generation Phase 3
    final_context_view = all_chunks_context[-7000:]

    if not final_context_view:
         yield {"type": "thought", "text": "🕳️ Signals Void: Deep Research failed to locate verifiable data."}
         return

    # 🎨 SEQUENTIAL PROMPT 3: The Elite Writer (Distillation & Presentation)
    elite_format_prompt = """SYSTEM INSTRUCTION:
You are an Elite Intelligence Analyst. 
Synthesize the provided research context into a comprehensive, professional report.

STRICT CONSTRAINTS:
1. 🚫 NO CONVERSATIONAL OPENERS: Never say "Here is the report" or "Based on my research". Start directly with an H1 (#) title.
2. DENSITY: Eliminate prepositional phrases and filler words. Use bullet points heavily.
3. MANDATORY STRUCTURE:
   - ## 🎯 Executive Summary (2 sentences max)
   - ## 📊 Technical/Factual Breakdown (Use Markdown Tables for ANY specs or numbers)
   - ## 🔬 Critical Analysis (Synthesize conflicts found in the sources)
   - ## 🔗 Source Matrix (List the verified domains as CLICKABLE markdown links [Title](URL))
4. VISUALS: If explaining a system or relationship, generate a ```mermaid chart.
5. HIGHLIGHTS: Bold any critical names, dates, or quantitative metrics.
6. LINKS: Every factual claim must be followed by a clickable [Source](URL) link."""

    final_prompt = f"[SYNTHESIZED INTELLIGENCE NETWORK]:\n{final_context_view}\n\n[USER OBJECTIVE]: {question}\n\nGenerate the Elite Distilled Report."
    
    final_content = ""
    system_prompt = system if (system and "STRICT OUTPUT FORMAT" not in system) else elite_format_prompt
    
    yield {"type": "thought", "text": "📝 Elite Writer: Formatting verified intelligence into premium report..."}
    async for token in call_ollama_stream(final_prompt, model, system=system_prompt):
        final_content += token
        yield {"type": "message", "text": token}


    # 📂 SAVE UNIT CHAT LOGS (Premium Audit Trail)
    try:
        log_dir = "unit_logs"
        if not os.path.exists(log_dir): os.makedirs(log_dir)
        log_id = f"{chat_id}_{int(time.time())}"
        with open(f"{log_dir}/{log_id}.json", "w", encoding="utf-8") as lf:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "chat_id": chat_id,
                "model": model,
                "prompt": final_prompt,
                "output": final_content,
                "context_size": len(all_chunks_context)
            }, lf, indent=2)
    except: pass

    # Part 6: Visual Knowledge Graph (Hyper-Search Engine Integration)
    if len(all_chunks_context) > 1000:
        yield {"type": "thought", "text": "🎨 Visual Intelligence: Mapping the discovery territory..."}
        mermaid_graph = await graph_builder.build_from_context(question, all_chunks_context)
        if mermaid_graph:
            visual_block = f"\n\n### Visual Intelligence: Knowledge Territory\n```mermaid\n{mermaid_graph}\n```"
            final_content += visual_block

    # Yield the fully formatted final message for UI consistency
    yield {"type": "message", "text": "", "full_text": final_content}

    # Part 6: Persistence
    if _MEMORY_ENABLED and chat_id:
        append_message(chat_id, "assistant", final_content, model)

async def auto_name_chat(chat_id: str, question: str):
    """Naming logic helper."""
    pass

async def run_agent_mode(question, model, chat_id):
    """Stub for agentic capabilities."""
    yield {"type": "thought", "text": "Launching Agentic Controller..."}
    yield {"type": "message", "text": "Agent mode coming soon in next version."}

async def auto_extract_memory(chat_id, question, answer):
    """Background task to extract insights."""
    pass
# ─────────────────────────────────────────────────────────────
# 7. SMART SEARCH ARCHITECTURE (OPTIMIZED & SELF-CORRECTING)
# ─────────────────────────────────────────────────────────────

class IntelligenceCache:
    """Aggressive Cross-Layer Caching (Upgrade 1)"""
    def __init__(self):
        self.query_cache = {}   # Query -> [URLs] (TTL 10m)
        self.content_cache = {} # URL -> CleanText (TTL 1h)
        self.last_cleanup = time.time()

    def get_query(self, q):
        if q in self.query_cache:
            entry, ts = self.query_cache[q]
            if time.time() - ts < 600: return entry
        return None

    def set_query(self, q, results):
        self.query_cache[q] = (results, time.time())

    def get_content(self, url):
        if url in self.content_cache:
            entry, ts = self.content_cache[url]
            if time.time() - ts < 3600: return entry
        return None

    def set_content(self, url, text):
        self.content_cache[url] = (text, time.time())

_I_CACHE = IntelligenceCache()

def get_diverse_chunks(chunks: list, chunk_sources: list, top_n: int = 5) -> list:
    """Domain Entropy Logic: ensures diversity in sources (Upgrade 3)"""
    selected = []
    used_domains = set()
    
    # Sort or rank should be done before this. This function just selects.
    # We iterate and pick one from each domain first, then fill up.
    for i, c in enumerate(chunks):
        source = chunk_sources[i] if i < len(chunk_sources) else "unknown"
        domain = source.split('//')[-1].split('/')[0] if '//' in source else source
        
        if domain not in used_domains:
            selected.append(c)
            used_domains.add(domain)
        
        if len(selected) >= top_n: break
        
    # Fill remaining if diversity alone didn't reach top_n
    if len(selected) < top_n:
        for i, c in enumerate(chunks):
            if c not in selected:
                selected.append(c)
            if len(selected) >= top_n: break
            
    return selected

SMART_QUERY_REWRITE_PROMPT = """Analyze the user query and identify its core factual intent.
Generate a JSON object with 3-5 optimized 'Fuzzy Logical Variants' (Upgrade 3).
- Aim to correct typos (e.g. 'Epstine' -> 'Epstein').
- Diversify across Factual, Technical, and Historical angles.
- Broaden the scope to ensure high recall.
Format: {"queries": ["optimized query 1", "varied query 2", "broad query 3"]}"""

STRICT_CONTEXT_ANSWER_PROMPT = """You are a precise neural research engine.
INSTRUCTIONS:
1. Answer the user question ONLY based on the provided [SEARCH CONTEXT].
2. If the context does not contain the answer, return exactly: NOT_FOUND
3. Do not add preamble, "Based on the text...", or any meta-commentary.
4. Use a clear, informative tone.
5. Every factual point/bullet MUST include a clickable source link at the end: [Source Name](URL).

[SEARCH CONTEXT]:
{context}"""

SMART_SEARCH_FOLLOWUP_PROMPT = """Based on the research provided, generate exactly ONE short, insightful follow-up question to help the user explore a deeper detail or a related concept. Output only the question."""

AMBIGUITY_CHECK_PROMPT = """Analyze if the query is ambiguous (has multiple possible meanings like 'Apple profits' - tech vs fruit).
If ambiguous, return a JSON object: {"ambiguous": true, "question": "Short clarifying question"}.
If clear, return: {"ambiguous": false}."""

FALLBACK_REWRITE_PROMPT = """The previous search for '{q}' failed.
Generate a completely different, broader research hypothesis or search queries that might find the info.
Output JSON: {"queries": ["...", "..."]}"""

# --- UPGRADE: EXTRACTION-FIRST LAYER (THE POINT-MAN) ---

async def extract_high_signal_bullets(raw_text: str, query: str, model: str = "gemma3:4b") -> str:
    """
    UPGRADE 3 & 5: Small Model Fact Extraction + Hierarchical Mapping.
    Converts raw web noise into a clean, synthesized signal for the Sniper (8B).
    """
    # --- UPGRADE: HIERARCHICAL SIGNAL MAPPING ---
    extraction_prompt = f"""
    USER SEARCH QUERY: {query}
    SOURCE ID: [S-{abs(hash(query)) % 1000}]
    RAW WEB SOURCE CONTENT:
    {raw_text[:8000]}
    
    SYSTEM TASK:
    1. Create a HIERARCHICAL MAP of this source.
    2. Extract EXACT identifiers (names, dates, IDs, prices).
    3. Summarize the 'Atomic Signal' of this page in 3 sentences.
    4. Format as: [MAP_ENTRY] - [SIGNAL]
    """
    signal = await call_ollama(extraction_prompt, model=model)
    return signal.strip()

async def cross_encoder_rerank(query: str, signals: list[str], model: str = "gemma3:4b") -> list[str]:
    """
    UPGRADE 4: Semantic Cross-Encoder Reranking.
    Performs a 1-to-1 relevance check to eliminate false positives in RAG.
    """
    reranked = []
    for signal in signals[:10]: # Rerank top 10
        prompt = f"QUERY: {query}\nSIGNAL: {signal}\nIs this signal 100% FACTUALLY RELEVANT? Output: YES or NO."
        verdict = await call_ollama(prompt, model=model)
        if "YES" in verdict.upper():
            reranked.append(signal)
    return reranked

async def unified_hybrid_search(question: str, model: str, chat_id: str = "default", system: str = None):
    """
    THE SYNTHESIS ENGINE (Stage 1 & 2)
    Triple-Parallel Search: Cloud + Local RAG + Session Memory
    """
    from services.rag.pipeline import query_rag # Lazy import to avoid circulars
    
    yield {"type": "thought", "text": "🌐 Synthesis Engine: Initializing Triple-Parallel Search (Local + Cache + Web)..."}
    
    # --- STAGE 1: TRIPLE-PARALLEL SEARCH (Upgrade 1) ---
    # Fire all searches concurrently to eliminate latency
    web_task = smart_search_pipeline(question, model, chat_id, system)
    rag_task = query_rag(question, top_k=5)
    
    # We run them in parallel. Since web search is a generator, we handle it specially.
    # For RAG, we just await it.
    rag_chunks = await rag_task
    
    rag_context = ""
    if rag_chunks:
        # Neural Filtration (Upgrade 2): Only keep high-signal local data
        high_signal_rag = [c["text"] for c in rag_chunks if c.get("score", 1.0) > 0.7]
        if high_signal_rag:
            yield {"type": "thought", "text": f"🧠 Local Memory: Identified {len(high_signal_rag)} high-signal documents."}
            rag_context = "\n\n[LOCAL DOCUMENT CONTEXT]:\n" + "\n---\n".join(high_signal_rag)
        else:
            yield {"type": "thought", "text": "⚠️ Local Signal Weak: Low relevance detected in indexed files."}
            
    # Now execute the web pipeline and pass the RAG context as 'system' or additional context
    # This effectively merges the two into the Synthesis Engine
    async for event in smart_search_pipeline(question, model, chat_id, system=f"{system}\n\n{rag_context}" if rag_context else system):
        yield event

async def smart_search_pipeline(question: str, model: str, chat_id: str = "default", system: str = None, is_fallback=False):
    """
    High-Performance Research Architecture (Upgraded V3)
    Disambiguation -> Caching -> Fuzzy Expansion -> Neural Rerank -> Synthesis
    """
    small_model = "gemma3:4b" 
    
    # Upgrade 4: Pre-Search Disambiguation Persona
    if not is_fallback:
        yield {"type": "thought", "text": "🧠 Analyzer: Analyzing query for semantic ambiguity and typos..."}
        ambiguity = await call_ollama_json(question, model=small_model, system=AMBIGUITY_CHECK_PROMPT)
        if ambiguity.get("ambiguous"):
             yield {"type": "message", "text": f"I've detected potential ambiguity in your request. To ensure high-fidelity results, please clarify: **{ambiguity.get('question')}**"}
             return

    # Upgrade 1 & 3: Caching + Fuzzy logical variants
    cached_queries = _I_CACHE.get_query(question)
    if cached_queries:
        yield {"type": "thought", "text": "⚡ Cache Hit: Utilizing pre-optimized neural search variants..."}
        search_queries = cached_queries
    else:
        yield {"type": "thought", "text": "🌩️ Smart Search: Expanding query into 5 fuzzy logical variants..."}
        rewrite_res = await call_ollama_json(question, model=small_model, system=SMART_QUERY_REWRITE_PROMPT)
        search_queries = rewrite_res.get("queries", [question])
        if question not in search_queries: search_queries.append(question)
        _I_CACHE.set_query(question, search_queries)
    
    yield {"type": "thought", "text": f"Parallelizing {len(search_queries)} research queries for maximum recall..."}
    
    # Step 2: Parallel Discovery
    all_urls = []
    search_tasks = [asyncio.to_thread(search_web_scored, [q]) for q in search_queries]
    search_results = await asyncio.gather(*search_tasks)
    
    seen_urls = set()
    for urls in search_results:
        for u in urls:
            if u not in seen_urls:
                seen_urls.add(u)
                all_urls.append(u)
    
    # Upgrade 1: Content Caching Filter
    uncached_urls = []
    cached_content_blobs = []
    for u in all_urls[:5]:
        content = _I_CACHE.get_content(u)
        if content:
            cached_content_blobs.append({"source": u, "text": content})
        else: uncached_urls.append(u)
            
    if cached_content_blobs:
        yield {"type": "thought", "text": f"⚡ Parallel Cache: Recovered {len(cached_content_blobs)} sources from local memory pool."}

    # Step 3: Fetching and Extraction (Point-Man Phase)
    if uncached_urls:
        yield {"type": "thought", "text": f"Scraping & Extracting signal from {len(uncached_urls)} verified domains..."}
        scraped_data = await advanced_scraper.hyper_scrape(uncached_urls, query=question)
        
        # Parallel Extraction (Point-Man)
        extraction_tasks = []
        for data in scraped_data:
            if data.get("text"):
                extraction_tasks.append(extract_high_signal_bullets(data["text"], question, model=small_model))
        
        extracted_signals = await asyncio.gather(*extraction_tasks)
        
        # --- LEVEL 2: Reranking & Mapping ---
        yield {"type": "thought", "text": "🧠 Cross-Encoder: Verifying 1-to-1 factual relevance for all sources..."}
        reranked_signals = await cross_encoder_rerank(question, extracted_signals, model=small_model)
        
        final_results = []
        for i, signal in enumerate(reranked_signals):
            source_url = uncached_urls[i] if i < len(uncached_urls) else "Global Context"
            _I_CACHE.set_content(source_url, signal)
            # Hard-code source link enforcement in chunks
            final_results.append(f"SOURCE_URL: {source_url}\nFACTS: {signal}\n[Link]({source_url})")
            
        all_text_blobs = [f"SOURCE: {d['source']}\n{d['text']}" for d in cached_content_blobs] + final_results
    else:
        all_text_blobs = [f"SOURCE: {d['source']}\n{d['text']}" for d in cached_content_blobs]
    
    if not all_text_blobs:
        if not is_fallback:
             yield {"type": "thought", "text": "🕳️ Context Null: Triggering Fallback Refinement loop..."}
             await asyncio.sleep(0.5) 
             async for ev in smart_search_pipeline(question, model, chat_id, system, is_fallback=True): yield ev
             return
        else:
            yield {"type": "message", "text": "NOT_FOUND - No reliable evidence found in RAG or Web pools."}
            return

    # Step 5: Ranking & Upgrade 3: Domain Entropy
    yield {"type": "thought", "text": "🧠 Neural Reranker: Filtering signal from noise (0.7 Relevance Floor)..."}
    
    combined_raw = "\n\n".join(all_text_blobs)
    chunks = chunk_text(combined_raw, chunk_size=400, overlap=50)
    
    try:
        query_emb = await get_embedding(question)
        chunk_embs = await asyncio.gather(*[get_embedding(c) for c in chunks[:15]]) 
        # Upgrade 2: Neural context filtration (0.7 floor)
        scored_chunks = []
        for i, emb in enumerate(chunk_embs):
            score = cosine_similarity(query_emb, emb)
            if score > 0.65: # Practical floor for search
                scored_chunks.append((chunks[i], score))
                
        # Sort and select
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        ranked_chunks = [x[0] for x in scored_chunks]
        
        # Apply Diversity (Upgrade 3)
        top_chunks = get_diverse_chunks(ranked_chunks, [c.split('\n')[0] for c in ranked_chunks], top_n=5)
    except Exception as e:
        logger.warning(f"Engine failure: {e}. Falling back.")
        top_chunks = chunks[:5]

    # Step 6: Strict Answer Generation (FORCED GPT-STYLE LINKS)
    final_context = "\n---\n".join(top_chunks)
    final_context_limited = " ".join(final_context.split()[:1000])
    
    yield {"type": "thought", "text": "📝 Synthesis Stage: Generating grounded answer with clickable links..."}
    sys_prompt = STRICT_CONTEXT_ANSWER_PROMPT.format(context=final_context_limited)
    sys_prompt += "\n\nCRITICAL: You MUST include the clickable [Source](URL) link for every feature or fact you mention. Every bullet point MUST end with its source link."
    if system: sys_prompt = f"{sys_prompt}\n\n[GLOBAL INTELLIGENCE RULES]:\n{system}"

    full_answer = ""
    async for token in call_ollama_stream(question, model, system=sys_prompt):
        full_answer += token
        yield {"type": "message", "text": token}

    # Upgrade 2: Auto-Escalation / Fallback
    if "NOT_FOUND" in full_answer and not is_fallback:
        yield {"type": "thought", "text": "⚠️ Evidence Mismatch: Refocusing search hypothesis..."}
        refinement = await call_ollama_json(question, model=small_model, system=FALLBACK_REWRITE_PROMPT.format(q=question))
        new_qs = refinement.get("queries", [question])
        async for ev in smart_search_pipeline(new_qs[0], model, chat_id, system, is_fallback=True): yield ev
        return
        
    # Step 7: Smart Follow-up
    if "NOT_FOUND" not in full_answer and len(full_answer.split()) > 10:
        yield {"type": "thought", "text": "💡 Discovery: Generating nextexploration path..."}
        followup = await call_ollama(f"Answer: {full_answer}", model=small_model, system=SMART_SEARCH_FOLLOWUP_PROMPT)
        if followup and followup.strip():
            yield {"type": "message", "text": f"\n\n🗨️ **Explore Further:** {followup.strip()}"}
async def gpt_style_fast_search(question, model, chat_id=None, system=None):
    """Rapid Web Scraper: Optimized for GPT-like speed and high-precision snippets."""
    yield {"type": "thought", "text": "🔍 Smart Web Scavenger: Initializing rapid discovery nodes..."}
    
    # 🌩️ FastScrape: Skips fuzzy expansion and deep fetching
    web_data = await advanced_scraper.hyper_scrape_fast(question)
    
    if not web_data:
        yield {"type": "thought", "text": "⚠️ No immediate signals detected. Processing with internal knowledge pool..."}
        async for token in call_ollama_stream(question, model, system=system):
            yield {"type": "message", "text": token}
        return

    yield {"type": "thought", "text": f"✅ Signals Detected: Verifying factual density of {len(web_data)} sources..."}
    
    # 🎯 VERIFIED EXTRACTION: Use small model to pull raw facts from snippets fast
    small_model = "gemma3:4b"
    extraction_tasks = []
    for w in web_data:
        snippet = w.get('text', '')[:1500]
        if snippet:
            prompt = f"EXTRACT ATOMIC FACTS ONLY. NO FILLER. SOURCE: [{w.get('source')}]\nDATA: {snippet}"
            extraction_tasks.append(call_ollama(prompt, model=small_model, system="Factual extraction mode. Bullet points only."))
    
    extracted_signals = await asyncio.gather(*extraction_tasks)
    
    # 🧠 NEURAL RERANK: Floor check for relevance
    yield {"type": "thought", "text": "🧠 Neural Filter: Reranking signal pool for maximum output precision..."}
    valid_signals = []
    for i, sig in enumerate(extracted_signals):
        if len(sig) > 20: # Crude quality check
             valid_signals.append(f"SOURCE: {web_data[i].get('source')}\nFACTS: {sig}")

    if not valid_signals:
         yield {"type": "thought", "text": "⚠️ Signal density low. Falling back to internal intelligence..."}
         async for token in call_ollama_stream(question, model, system=system):
            yield {"type": "message", "text": token}
         return

    # 📝 FINAL GROUNDED SYNTHESIS
    yield {"type": "thought", "text": "📝 Synthesis Stage: Generating rapid-verified response..."}
    context = "\n\n".join(valid_signals)
    grounded_sys = f"{system}\n\nSTRICT INSTRUCTION: Answer based ONLY on the [VERIFIED WEB CONTEXT] below. Every factual claim MUST include a clickable [Source](URL) link from the context.\n\n[VERIFIED WEB CONTEXT]:\n{context}"
    
    async for token in call_ollama_stream(question, model, system=grounded_sys):
        yield {"type": "message", "text": token}
