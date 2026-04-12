"""
services/modeSelector/selector.py
----------------------------------
Selects best mode for the detected intent.
"""

class ModeSelector:
    @staticmethod
    def get_mode(intent: str, original_mode: str) -> str:
        """
        Only auto-selects if current mode is 'chat'.
        """
        if original_mode != "chat":
            return original_mode # Do not override manual selection
            
        mapping = {
            "coding": "code",
            "comparison": "compare",
            "explanation": "explain",
            "research": "fast-web", # Use fast-web for research intent in chat
            "summarization": "summarize",
            "simple chat": "chat"
        }
        
        return mapping.get(intent, "chat")
