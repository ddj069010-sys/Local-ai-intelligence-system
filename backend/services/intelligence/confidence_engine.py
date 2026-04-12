import logging

logger = logging.getLogger(__name__)

def compute_confidence(sources: list, consistency: str, query_type: str) -> str:
    """
    Computes a confidence score (High/Medium/Low) for the final response.
    """
    score = 0
    if len(sources) >= 3:
        score += 2
    elif len(sources) >= 1:
        score += 1
        
    if consistency == "High":
        score += 2
    elif consistency == "Medium":
        score += 1
        
    if query_type == "simple":
        score += 1
        
    if score >= 4:
        return "High"
    elif score >= 2:
        return "Medium"
    else:
        return "Low"
