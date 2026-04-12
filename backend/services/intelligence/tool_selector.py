import logging
from engine.utils import call_ollama_json
from engine.config import OLLAMA_MODEL

logger = logging.getLogger(__name__)

async def select_tools(enhanced_query: dict) -> dict:
    """
    Decides which tools/workflows to trigger based on the enhanced query and intent.
    """
    query = enhanced_query.get("enhanced_query", "")
    intent = enhanced_query.get("intent", "general")
    
    prompt = f"""
    Based on the enhanced query and intent, decide which tools to use.
    
    QUERY: "{query}"
    INTENT: "{intent}"
    
    AVAILABLE TOOLS:
    1. chat: General discussion.
    2. web_search: Real-time data, current events.
    3. rag: Local documents, personal notes.
    4. execution: Running code, math, logic.
    5. video: Video analysis.
    6. deep_search: Comprehensive multi-step research.
    
    RESPONSE FORMAT (JSON ONLY):
    {{
      "primary_tool": "tool_name",
      "secondary_tools": ["tool1", "tool2"],
      "reasoning": "why these tools",
      "multi_step_needed": true/false
    }}
    """
    # --- HYBRID REASONING ENGINE: STEP 0 (NATIVE RULES) ---
    RAG_TAGS = ["@rag", "@doc", "@memory", "@knowledge"]
    CODE_MARKERS = ["def ", "import ", "print(", "class ", "function ", "const ", "var "]
    WEB_MARKERS = ["http://", "https://", "www.", ".com", ".org", "latest news", "current"]

    # 1. Direct RAG Hook
    if any(tag in query.lower() for tag in RAG_TAGS):
        logger.info("Hybrid Router -> Fast-Track: RAG")
        return {"primary_tool": "rag", "secondary_tools": [], "reasoning": "Explicit RAG tag detected.", "multi_step_needed": False}
    
    # 2. Direct Execution/Code Hook
    if any(marker in query for marker in CODE_MARKERS):
        logger.info("Hybrid Router -> Fast-Track: EXECUTION")
        return {"primary_tool": "execution", "secondary_tools": ["chat"], "reasoning": "Code syntax detected.", "multi_step_needed": False}

    # 3. Direct Web Hook
    if any(marker in query.lower() for marker in WEB_MARKERS):
        logger.info("Hybrid Router -> Fast-Track: WEB_SEARCH")
        return {"primary_tool": "web_search", "secondary_tools": [], "reasoning": "URL or search marker detected.", "multi_step_needed": False}

    # --- STEP 1 (LLM REASONING) ---
    has_rag_tag = any(tag in query.lower() for tag in RAG_TAGS)
    
    try:
        decision = await call_ollama_json(prompt, OLLAMA_MODEL)
        if decision and decision.get("primary_tool"):
            # Enforce Tag Rule
            if decision["primary_tool"] == "rag" and not has_rag_tag:
                logger.info("RAG suggested by LLM but NO TAG found. Forcing 'chat' mode.")
                decision["primary_tool"] = "chat"
                decision["reasoning"] += " (RAG suppressed: no explicit tag found)"
            
            return decision
    except Exception as e:
        logger.error(f"Tool selection failed: {e}")
    
    # Fallback
    return {
        "primary_tool": "chat",
        "secondary_tools": [],
        "reasoning": "Fallback due to error.",
        "multi_step_needed": False
    }
