import logging
from engine.utils import call_ollama_json
from engine.config import OLLAMA_MODEL

logger = logging.getLogger(__name__)

async def enhance_query(query: str) -> dict:
    """
    Expands and clarifies user query to improve retrieval and answer quality.
    """
    prompt = f"""
    Analyze the following user query and provide an enhanced version that is more descriptive and clear.
    Also, detect the query type and intent.
    
    USER QUERY: "{query}"
    
    RESPONSE FORMAT (JSON ONLY):
    {{
      "original_query": "{query}",
      "enhanced_query": "Smarter/expanded version of the query",
      "intent": "e.g. informative, technical, creative, debugging, comparative",
      "type": "e.g. simple, complex, conversational",
      "clarification_needed": true/false
    }}
    """
    try:
        enhanced = await call_ollama_json(prompt, OLLAMA_MODEL)
        if enhanced and enhanced.get("enhanced_query"):
            return enhanced
    except Exception as e:
        logger.error(f"Query enhancement failed: {e}")
    
    # Fallback to original
    return {
        "original_query": query,
        "enhanced_query": query,
        "intent": "general",
        "type": "simple",
        "clarification_needed": False
    }
