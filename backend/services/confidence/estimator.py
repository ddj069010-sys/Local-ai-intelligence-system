class ConfidenceEstimator:
    """Estimates AI model confidence based on query type and content."""
    
    _FACTUAL_KEYWORDS = {
        "latest", "news", "today", "current", "2024", "2025", "now", "recent",
        "stock price", "weather", "who is", "what is", "president", "yesterday"
    }
    
    @staticmethod
    def estimate(query: str) -> float:
        """Returns a confidence score from 0.0 to 1.0."""
        q = query.lower().strip()
        words = q.split()
        
        # Heuristic 1: Query length (Short = Vague = Low confidence for research)
        if len(words) < 3:
            return 0.4
            
        # Heuristic 2: Factual/Recent keywords (Needs external knowledge)
        if any(kw in q for kw in ConfidenceEstimator._FACTUAL_KEYWORDS):
            return 0.3
            
        # Heuristic 3: Complex technical queries (Usually LLM is good)
        if any(kw in q for kw in ["code", "function", "refactor", "algorithm", "explain"]):
            return 0.9
            
        # Heuristic 4: Small talk (LLM is high confidence)
        if any(kw in q for kw in ["hi", "hello", "how are you", "thanks"]):
            return 1.0
            
        # Default
        return 0.7

    @staticmethod
    def needs_web_fallback(confidence: float, threshold: float = 0.5) -> bool:
        """Decides if we should trigger web search."""
        return confidence < threshold
