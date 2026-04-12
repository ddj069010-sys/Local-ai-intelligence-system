import json
import logging
from engine.utils import call_ollama

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, model="gemma3:4b"):
        self.model = model

    async def detect_intent(self, user_input: str) -> dict:
        """Determines the user's intent and which tool to use."""
        system_prompt = """You are the BRAIN of a JARVIS-like agent. 
Analyze the user input and decide which tool or workflow is needed.

AVAILABLE TOOLS:
1. chat: General conversation, greetings, simple questions.
2. web_search: When user asks for current events, facts, or things needing internet.
3. memory: When user refers to past conversations or facts about themselves.
4. execution: When user wants to run code (Python/shell) or solve a math/logic problem with code.
5. file_system: When user wants to read, write, or list files in their workspace.
6. universal: When user provides a URL, file, image, or video for analysis. ALSO trigger this if user explicitly asks to "search doc", "search file", "lookup doc", or refers to their uploaded documents (e.g. "what does the doc say?").
7. deep_url: When user specifically asks for "deep search", "deep scan", "full analysis", or toggles the Deep Search mode for a URL.

RESPONSE FORMAT (JSON ONLY):
{
  "intent": "tool_name",
  "reason": "short explanation",
  "search_query": "query for web_search (if applicable)",
  "code": "code to execute (if applicable)",
  "language": "python/shell (if applicable)",
  "file_op": "read/write/list (if applicable)",
  "file_name": "filename (if applicable)",
  "file_content": "content to write (if applicable)"
}
"""
        try:
            response = await call_ollama(user_input, self.model, system=system_prompt)
            # Find JSON block
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "{" in response:
                response = "{" + response.split("{", 1)[1].rsplit("}", 1)[0] + "}"
            
            return json.loads(response.strip())
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            return {"intent": "chat", "reason": "Fallback due to error"}

orchestrator = Orchestrator()
