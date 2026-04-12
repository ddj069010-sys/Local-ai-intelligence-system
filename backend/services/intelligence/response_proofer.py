import logging
from engine.utils import call_ollama_json
from .format_engine import detect_features, select_format, get_format_instruction

logger = logging.getLogger(__name__)

async def evaluate_response(query: str, response: str) -> dict:
    """
    Evaluates the response for clarity, completeness, and relevance.
    """
    prompt = f"""
    Evaluate the following AI response based on the user query.
    
    QUERY: "{query}"
    RESPONSE: "{response}"
    
    RESPONSE FORMAT (JSON ONLY):
    {{
      "clarity_score": 0-10,
      "completeness_score": 0-10,
      "relevance_score": 0-10,
      "missing_info": ["point 1", "point 2"],
      "quality_summary": "overall thought"
    }}
    """
    try:
        from engine.model_manager import ModelManager
        fast_model = await ModelManager.get_fast_model()
        return await call_ollama_json(prompt, fast_model)
    except Exception as e:
        logger.error(f"Response evaluation failed: {e}")
        return {"clarity_score": 5, "completeness_score": 5, "relevance_score": 5}

async def refine_response(query: str, response: str, evaluation: dict, style: str = "detailed", context_preview: str = "") -> str:
    """
    Refines the response using the Intelligent Format Engine.
    """
    # 1. Intelligent Feature Detection (Step 1 & 2)
    features = await detect_features(query, context_preview or response)
    intent = features.get("intent", "Summarize")
    content_type = features.get("content_type", "Mixed / Unknown")
    
    # 2. Format Selection (Step 3 & 4)
    format_name = select_format(intent, content_type)
    format_instr = await get_format_instruction(format_name, query)
    
    # 3. Refinement with Format Instructions
    prompt = f"""
    Refine the following AI response according to the specified INTIGELLENT FORMAT.
    
    USER QUERY: "{query}"
    INTENT: {intent}
    CONTENT TYPE: {content_type}
    ORIGINAL RESPONSE: "{response}"
    EVALUATION/FEEDBACK: {evaluation}
    
    {format_instr}
    
    TASKS (Steps 6-10):
    1. Apply the structure rules strictly.
    2. Remove noise and duplicates.
    3. Adapt for content length (Short -> Concise, Long -> Detailed).
    4. IF unsure or mixed, use HYBRID FORMAT.
    5. DO NOT hallucinate. Keep facts only.
    """
    try:
        from engine.utils import call_ollama
        from engine.model_manager import ModelManager
        fast_model = await ModelManager.get_fast_model()
        return await call_ollama(prompt, fast_model)
    except Exception as e:
        logger.error(f"Response refinement failed: {e}")
        return response
