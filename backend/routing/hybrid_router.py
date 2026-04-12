import re
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from core.logger import logger

class Intent(str, Enum):
    CHAT = "chat"
    RAG = "rag"
    CODE = "code"
    VISION = "vision"
    WEB = "web"
    RESEARCH = "research"
    FILE = "file"

class RoutingDecision:
    """Represents a final routing decision."""
    def __init__(self, intent: Intent, confidence: float, reason: str, is_fallback: bool = False):
        self.intent = intent
        self.confidence = confidence
        self.reason = reason
        self.is_fallback = is_fallback

class HybridRouter:
    """
    Intelligent Hybrid Router that balances rule-based speed 
    with LLM-based reasoning fallback.
    """
    
    RAG_TAGS = ["@rag", "@doc", "@memory", "@knowledge", "@local"]
    CODE_MARKERS = [
        r"\bdef\b", r"\bclass\b", r"\bimport\b", 
        r"traceback", r"error:", r"exception", 
        r"stack trace", r"printf", r"segfault",
        r"npm install", r"pip install", r"docker"
    ]
    WEB_TAGS = ["@web", "@search", "@online", "@google"]
    
    def __init__(self):
        self.logger = logger
    
    def route(self, query: str, has_files: bool = False) -> RoutingDecision:
        """
        Main entry point for routing logic.
        Rule-based -> Fast, Deterministic.
        Fallback -> LLM Reasoning.
        """
        query_lower = query.lower()
        
        # 1. Multimedia/File Rule
        if has_files:
            return RoutingDecision(Intent.FILE, 1.0, "Input contains attached files/multimedia")
            
        # 2. RAG Tags Rule
        if any(tag in query_lower for tag in self.RAG_TAGS):
            return RoutingDecision(Intent.RAG, 1.0, "Explicit RAG tag detected in query")
            
        # 3. Web Tags Rule
        if any(tag in query_lower for tag in self.WEB_TAGS):
            return RoutingDecision(Intent.WEB, 1.0, "Explicit Web search tag detected in query")

        # 4. Code Pattern Rule
        for pattern in self.CODE_MARKERS:
            if re.search(pattern, query_lower):
                return RoutingDecision(Intent.CODE, 0.9, f"Code pattern '{pattern}' detected")
        
        # 5. Simple Interaction Rule
        if len(query.split()) < 4 and any(greet in query_lower for greet in ["hi", "hello", "hey", "thanks", "bye"]):
            return RoutingDecision(Intent.CHAT, 0.95, "Simple greeting or acknowledgment detected")

        # 6. LLM Fallback (Placeholder for the actual LLM call via ToolSelector)
        self.logger.info("  ⚠️ [ROUTER] Low rule confidence. Falling back to LLM reasoning...")
        return RoutingDecision(Intent.CHAT, 0.5, "Default fallback to Chat mode (Rule-based routing inconclusive)", is_fallback=True)

# Singleton instance
hybrid_router = HybridRouter()
