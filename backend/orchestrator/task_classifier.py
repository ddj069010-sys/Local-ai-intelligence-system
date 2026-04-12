import json
import logging
import httpx
from typing import Dict, Any, Tuple
from core.config import settings, ModelTier
from core.logger import logger
from routing.hybrid_router import Intent

class TaskClassifier:
    """
    Handles deep intent classification (fallback) and complexity scoring.
    Determines if a task is 'Ultra', 'High', 'Medium', or 'Low'.
    """
    
    def __init__(self):
        self.logger = logger

    async def classify(self, query: str) -> Tuple[Intent, str, ModelTier]:
        """
        Uses a lightweight LLM call to classify intent and complexity.
        """
        prompt = f"""
        Analyze the following query and classify it into:
        1. INTENT: One of [chat, rag, code, vision, web, research]
        2. COMPLEXITY: One of [low, medium, high, ultra]
        3. REASON: A brief explanation.

        Query: "{query}"

        Return ONLY a JSON object:
        {{
            "intent": "...",
            "complexity": "...",
            "reason": "..."
        }}
        """
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.OLLAMA_API_URL}/generate",
                    json={
                        "model": settings.DEFAULT_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=settings.REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    res_json = json.loads(data.get("response", "{}"))
                    
                    intent = Intent(res_json.get("intent", "chat"))
                    complexity = ModelTier(res_json.get("complexity", "medium"))
                    reason = res_json.get("reason", "Inferred by LLM Classifier")
                    
                    self.logger.info(f"🧠 [CLASSIFIER] Intent: {intent.upper()} | Complexity: {complexity.upper()}")
                    return intent, reason, complexity
                
        except Exception as e:
             self.logger.warning(f"⚠️ [CLASSIFIER] LLM Classification failed: {e}. Falling back to default.")
        
        # Safe Default
        return Intent.CHAT, "Default fallback (LLM Classifier error)", ModelTier.MEDIUM

# Singleton instance
task_classifier = TaskClassifier()
