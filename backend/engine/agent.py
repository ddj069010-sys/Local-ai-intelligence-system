import json
import logging
import asyncio
import hashlib
import time
from services.orchestrator.orchestrator import orchestrator
from services.execution.executor import run_python_code, run_shell_command
from controller.workspace_routes import safe_path, WORKSPACE_DIR
from services.intelligence.orchestrator import intelligence_orchestrator
from engine.utils import call_ollama
import os

logger = logging.getLogger(__name__)

# ─── Fix #7: Response Cache ───────────────────────────────────────────────────
_RESPONSE_CACHE: dict = {}
_CACHE_TTL = 3600  # 1 hour

def _cache_key(query: str, model: str) -> str:
    return hashlib.sha256(f"{query.strip().lower()}::{model}".encode()).hexdigest()[:20]

def _cache_get(query: str, model: str):
    key = _cache_key(query, model)
    entry = _RESPONSE_CACHE.get(key)
    if entry and (time.time() - entry["ts"]) < _CACHE_TTL:
        return entry["text"]
    return None

def _cache_set(query: str, model: str, text: str):
    if len(text.split()) >= 10:  # Only cache substantive responses
        _RESPONSE_CACHE[_cache_key(query, model)] = {"text": text, "ts": time.time()}

# ─── Fix #8: Complexity-Adaptive Model Selector ───────────────────────────────
def _select_model(question: str, base_model: str) -> str:
    """Picks the lightest capable model for the task. Strictly excludes Ultra-Tier from auto-selection."""
    from engine.config import ULTRA_TIER_MODELS
    
    # 🚫 UPGRADE: Anti-Crash Guard
    # If the user has manually selected an Ultra-Tier model, we respect it,
    # but we NEVER auto-select them here.
    if base_model in ULTRA_TIER_MODELS:
        return base_model

    q = question.lower()
    wc = len(question.split())
    # Code specialist
    if any(kw in q for kw in ["code","function","debug","fix the","write a script","class "]):
        return "gemma3:8b" # Sniper for complex tasks
    # Ultra-light for greetings
    if wc < 8 and not "?" in question:
        return "gemma3:4b" # Point-Man
    return "gemma3:4b" # Default to Point-Man for orchestration


async def run_agent_mode(question: str, model: str, chat_id: str = "default"):
    # 🏎️ STEP 1: ULTRA-FAST PATH (GREETINGS & SHORT CHINESE/CHAT)
    import re
    from engine.modes import compact_chat
    from engine.model_manager import ModelManager
    
    q_clean = question.strip().lower()
    words = q_clean.split()
    is_greeting = re.match(r"^(hi|hello|hey|greetings|yo|thanks|bye|good morning|how are you|test|hi there)$", q_clean)
    is_extremely_short = len(words) < 5 and not "?" in q_clean
    
    if is_greeting or is_extremely_short:
        # Use only small model, skip all logic
        f_model = await ModelManager.get_best_model(mode="chat", question=question, requested_model="gemma3:4b", purpose="extraction")
        async for event in compact_chat(question, f_model):
            yield event
        return

    # 🏎️ STEP 2: GLOBAL CONTROLLER (Complexity & Pipeline Decision)
    from engine.modes import GPT_GLOBAL_CONTROLLER_PROMPT, gpt_high_fidelity_pipeline
    from engine.utils import call_ollama_json
    
    c_model = await ModelManager.get_best_model(mode="chat", question=question, requested_model="gemma3:4b", purpose="extraction")
    
    yield {"type": "thought", "text": f"🎯 Master Controller: Analyzing complexity (Engine: {c_model})..."}
    controller_dec = await call_ollama_json(question, model=c_model, system=GPT_GLOBAL_CONTROLLER_PROMPT)
    
    # Standardize result
    if not isinstance(controller_dec, dict): controller_dec = {}
    action = controller_dec.get("action", "answer")
    complexity = controller_dec.get("complexity", "medium")

    # STEP 3: MODEL SELECTION FIX (Tiered Hardware Allocation)
    if complexity == "low":
        target_model = await ModelManager.get_best_model(mode="chat", question=question, requested_model="gemma3:4b", purpose="extraction")
    elif complexity == "medium":
        target_model = await ModelManager.get_best_model(mode="chat", question=question, requested_model="gemma3:8b", purpose="reasoning")
    else:
        target_model = await ModelManager.get_best_model(mode="research", question=question, requested_model=model, purpose="reasoning")

    if action in ["answer", "clarify", "execute"]:
        generated_output = ""
        search_snippets = []
        async for event in gpt_high_fidelity_pipeline(question, target_model, chat_id=chat_id, controller_dec=controller_dec):
            if isinstance(event, dict) and event.get("type") == "audit_full_result":
                generated_output = event.get("output", "")
                search_snippets = event.get("search_snippets", [])
            elif isinstance(event, dict) and event.get("type") == "clarification_needed":
                yield event
                return # STRICT STOP: Do not proceed to audit
            else:
                yield event
        
        # ── PASS 2: NEURAL AUDIT (Quality Check) ──
        from engine.modes import run_system_evaluation, run_system_correction
        yield {"type": "thought", "text": "🛡️ Neural Audit: Verifying fact-integrity and GPT-parity..."}
        
        eval_meta = {"model": target_model, "complexity": complexity, "routing": True}
        evaluation = await run_system_evaluation(question, generated_output, eval_meta)
        
        # ── PASS 3: SELF-HEALING (Fix if accuracy < 9 or hallucination) ──
        if isinstance(evaluation, dict):
            acc = evaluation.get("accuracy", 10)
            halluc = evaluation.get("hallucination", False)
            
            if acc < 9 or halluc:
                yield {"type": "thought", "text": "🩹 Self-Healing: Correcting detected factual inaccuracy..."}
                correction = await run_system_correction(question, generated_output, evaluation, search_snippets)
                
                if isinstance(correction, dict) and correction.get("fix_required", False):
                    fixed_answer = correction.get("final_answer", "")
                    if fixed_answer and fixed_answer != generated_output:
                        yield {"type": "thought", "text": "✅ Verified: Applying corrected GPT-parity response."}
                        yield {"type": "message_update", "text": fixed_answer}
        return
    
    # ═══════════════════════════════════════════════════════════════════
    # FALLBACK: Existing Mode System (Step 4 - Ensure Orchestrator runs ONCE)
    # ═══════════════════════════════════════════════════════════════════
    from engine.modes import _classify_question_type, compact_chat as _compact_chat
    _gate_density, _ = _classify_question_type(question)
    if _gate_density == 0:
        yield {"type": "thought", "text": "⚡ Fast-Lane: Routing to compact logic."}
        async for event in _compact_chat(question, target_model):
            yield event
        return
    # ═══════════════════════════════════════════════════════════════════

    # ── SOLUTION C: Backend Thought Dedup ──────────────────────────────
    # Two parallel async generators (Intelligence Orchestrator + fallback)
    # emit identical thoughts through different code paths. Dedup at source.
    seen_thoughts: set = set()

    def _yield_thought(text: str):
        """Dedup-safe thought emitter — silently drops duplicates."""
        if text not in seen_thoughts:
            seen_thoughts.add(text)
            return {"type": "thought", "text": text}
        return None
    # ──────────────────────────────────────────────────────────────────

    t = _yield_thought("Analyzing request with Orchestrator (BRAIN)...")
    if t: yield t
    
    # --- INTELLIGENCE LAYER: STEP 1 & 2 ---
    enhanced_data = None
    decision = {}
    enhanced_query = question
    try:
        async for event in intelligence_orchestrator.process_request(question):
            if isinstance(event, dict) and event.get("type") == "intelligence_data":
                enhanced_data = event
                decision = event["tools"]
                enhanced_query = event["enhanced"]["enhanced_query"]
            elif isinstance(event, dict) and event.get("type") == "thought":
                # Apply dedup to all thoughts forwarded from the orchestrator
                t = _yield_thought(event.get("text", ""))
                if t: yield t
            else:
                yield event
                
        intent = decision.get("primary_tool", "chat")
        reason = decision.get("reasoning", "Intelligence optimized.")
        t = _yield_thought(f"Intelligence Layer: Intent={intent}, Reason={reason}")
        if t: yield t
        
    except Exception as e:
        logger.error(f"Intelligence Layer error: {e}. Falling back to default orchestrator.")
        # FALLBACK: Step 1 (Original Detect Intent)
        decision = await orchestrator.detect_intent(question)
        intent = decision.get("intent", "chat")
        reason = decision.get("reason", "Standard intent detection.")
        enhanced_query = question
        t = _yield_thought(f"Fallback Intent: {intent}. Reason: {reason}")
        if t: yield t

    
    # 2. Execute Tool based on Intent
    if intent == "execution":
        code = decision.get("code", "")
        lang = decision.get("language", "python")
        yield {"type": "thought", "text": f"Executing {lang} code..."}
        
        if lang == "python":
            result = run_python_code(code)
        else:
            result = run_shell_command(code)
            
        output = result.get("output", "")
        error = result.get("error", "")
        
        yield {"type": "execution_result", "output": output, "error": error, "language": lang}
        
        # Follow up with the result
        follow_up_prompt = f"The user asked: {question}\nI executed this {lang} code:\n```\n{code}\n```\nOutput:\n{output}\nError:\n{error}\n\nPlease summarize the result for the user."
        from engine.utils import call_ollama
        summary = await call_ollama(follow_up_prompt, model)
        yield {"type": "message", "text": summary}

    elif intent == "file_system":
        op = decision.get("file_op", "list")
        name = decision.get("file_name", "")
        content = decision.get("file_content", "")
        
        yield {"type": "thought", "text": f"File System operation: {op} on {name or 'workspace'}..."}
        
        res_text = ""
        try:
            if op == "list":
                files = os.listdir(WORKSPACE_DIR)
                res_text = f"Files in workspace: {', '.join(files) if files else 'empty'}"
            elif op == "read" and name:
                path = safe_path(name)
                if os.path.exists(path):
                    with open(path, "r") as f:
                        res_text = f"Content of {name}:\n{f.read()}"
                else:
                    res_text = f"File {name} not found."
            elif op == "write" and name:
                path = safe_path(name)
                with open(path, "w") as f:
                    f.write(content)
                res_text = f"Successfully wrote to {name}."
            else:
                res_text = "Invalid file operation."
        except Exception as e:
            res_text = f"Error: {str(e)}"
            
        yield {"type": "file_result", "operation": op, "file": name, "result": res_text}
        
        # Follow up
        follow_up_prompt = f"The user asked: {question}\nI performed file operation: {op} {name}\nResult:\n{res_text}\n\nPlease provide a final response to the user."
        from engine.utils import call_ollama
        summary = await call_ollama(follow_up_prompt, model)
        yield {"type": "message", "text": summary}

    elif intent == "web_search" or intent == "memory":
        # 🌐 Upgrade 1: Unified Hybrid Search (RAG + Web)
        from engine.research import unified_hybrid_search
        query = decision.get("search_query", question)
        yield {"type": "thought", "text": f"Synthesis Engine: Launching Unified Hybrid Search (Local RAG + Parallel Web)..."}
        async for event in unified_hybrid_search(query, model, chat_id=chat_id):
            yield event

    else: # Default chat — Fix #2: Smart pre-router to lightest correct mode
        from engine.formatter import FormatEngine
        from engine.modes import detect_density_and_style
        q_lower = enhanced_query.lower()
        wc = len(enhanced_query.split())
        
        # --- Adaptive Intelligence: Analyze signals before routing ---
        signals = detect_density_and_style(enhanced_query)
        density = signals["density"]
        is_greeting_or_compact = signals["is_greeting"] or density == 0
        has_style_override = signals["style"] is not None

        # Check cache first (Fix #7)
        cached = _cache_get(enhanced_query, model)
        if cached:
            yield {"type": "thought", "text": "⚡ Serving from response cache..."}
            yield {"type": "message", "text": cached}
            return

        # Adaptive model (Fix #8)
        effective_model = _select_model(enhanced_query, model)

        # Route to lightest correct mode (Fix #2)
        is_greeting = (wc < 8 and not "?" in enhanced_query and
                       any(kw in q_lower for kw in ["hi","hello","hey","thanks","bye","good "]))
        is_compare  = any(kw in q_lower for kw in [" vs "," versus ","compare ","difference between","which is better"])
        is_summary  = any(kw in q_lower for kw in ["summarize","tldr","brief","summary of","in short"])
        is_code     = any(kw in q_lower for kw in ["write code","fix this","debug","function that","python script","javascript"])
        
        # 🎭 Upgrade 4 & 10: High-Fidelity Synthesis Engine
        is_hp_requested = any(kw in q_lower for kw in ["gpt", "chatgpt", "professional", "high fidelity", "fidelity", "perfectly", "research", "deep"])
        
        # ⚠️ UPGRADE: VRAM Safety Alert
        from engine.config import ULTRA_TIER_MODELS
        if effective_model in ULTRA_TIER_MODELS and (is_hp_requested or wc >= 15):
             yield {"type": "thought", "text": "⚠️ VRAM Safety: Ultra-Tier model (30B+) active. Deep research may cause latency or OOM. Proceeding with caution..."}

        if is_greeting or is_greeting_or_compact:
            from engine.modes import compact_chat as _mode
            mode_gen = _mode(enhanced_query, effective_model)
        elif is_hp_requested or wc >= 15:  # Auto-Escalation to Full GPT Pipeline
            from engine.modes import gpt_high_fidelity_pipeline
            yield {"type": "thought", "text": "🎚️ GPT Pipeline: Query complexity high. Activating High-Fidelity Synthesis workflow..."}
            async for event in gpt_high_fidelity_pipeline(enhanced_query, effective_model, chat_id=chat_id):
                yield event
            return
        elif is_summary:
            from engine.modes import summarize_text_mode as _mode
            mode_gen = _mode(enhanced_query, effective_model)
        elif is_code:
            from engine.modes import code_assistant as _mode
            mode_gen = _mode(enhanced_query, effective_model)
        elif is_compare:
            from engine.modes import simple_chat as _mode
            mode_gen = _mode(enhanced_query, effective_model, chat_id=chat_id)
        elif wc < 12:   # Short factual questions — no heavy report
            from engine.modes import simple_chat as _mode
            mode_gen = _mode(enhanced_query, effective_model, chat_id=chat_id)
        else:           # Full general chat for complex questions
            from engine.modes import general_chat as _mode
            mode_gen = _mode(enhanced_query, effective_model, chat_id=chat_id)

        # Fix #4: Paragraph-chunk streaming with in-flight emoji injection
        final_response_list = []
        para_buffer = ""
        gen_start = time.time()
        token_count = 0
        async for event in mode_gen:
            if isinstance(event, dict) and event.get("type") == "message":
                token = str(event.get("text", ""))
                final_response_list.append(token)
                para_buffer += token
                token_count += max(1, len(token.split()))  # Gap 3 Fix: word-level velocity, not paragraph-flush count
                # Flush complete paragraphs (double newline boundary)
                if "\n\n" in para_buffer:
                    para, para_buffer = para_buffer.rsplit("\n\n", 1)
                    try:
                        para = FormatEngine._hydrate_emojis(para)
                    except Exception:
                        pass
                    yield {"type": "message", "text": para + "\n\n"}
                else:
                    yield event
            else:
                yield event
        # Flush remaining buffer
        if para_buffer.strip():
            try:
                para_buffer = FormatEngine._hydrate_emojis(para_buffer)
            except Exception:
                pass
            yield {"type": "message", "text": para_buffer}

        final_response = "".join(final_response_list)
        gen_end = time.time()
        gen_time = round(gen_end - gen_start, 2)
        tps = round(token_count / gen_time, 1) if gen_time > 0 else 0
        
        yield {"type": "metadata", "data": {
            "generationTime": gen_time,
            "tokensPerSecond": tps,
            "model": effective_model
        }}
        
        _cache_set(enhanced_query, model, final_response)  # Cache for next time

        # --- INTELLIGENCE LAYER: STEP 5 & 6 (Evaluation & Refinement) ---
        # 🔴 STYLE GATE: Skip the refinement pass if a Style Override was detected.
        # Refinement would destroy the tone the user explicitly requested.
        if is_greeting_or_compact or has_style_override:
            logger.info("Refinement pass SKIPPED — Natural/Style Gate active.")
            return

        if enhanced_data:
            try:
                yield {"type": "thought", "text": "Evaluating and refining response quality..."}
                proofer_res = await intelligence_orchestrator.finalize_response(
                    enhanced_query,
                    final_response,
                    enhanced_data.get("fragments", []),
                    enhanced_data["enhanced"]["type"]
                )

                from engine.formatter import FormatEngine
                base_text = proofer_res["text"] if proofer_res["text"] != final_response else final_response
                polished_text = FormatEngine.ensure_standard_format(base_text, enhanced_data["enhanced"]["type"])
                if polished_text != final_response:
                    yield {"type": "thought", "text": "Improving response structure and clarity..."}
                    yield {"type": "message_update", "text": polished_text}

                yield {"type": "metadata", "data": proofer_res["metadata"], "confidence": proofer_res["confidence"]}

            except Exception as e:
                logger.error(f"Response proofing failed: {e}")
                try:
                    from engine.formatter import FormatEngine
                    polished_text = FormatEngine.ensure_standard_format(final_response, "chat")
                    if polished_text != final_response:
                        yield {"type": "message_update", "text": polished_text}
                except Exception:
                    pass
        else:
            # Apply full layout polish on the complete response
            try:
                word_count = len(final_response.split())
                if word_count >= 8:
                    from engine.formatter import FormatEngine
                    polished_text = FormatEngine.ensure_standard_format(final_response, "chat")
                    if polished_text != final_response:
                        yield {"type": "message_update", "text": polished_text}
            except Exception as e:
                logger.error(f"Standalone formatting failed: {e}")

