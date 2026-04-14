"""
engine/config.py
----------------
Central configuration for all chatbot modes.
"""
import os
from dotenv import load_dotenv

# Load .env from backend root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434/api")
if not OLLAMA_API_URL.endswith("/api"):
    OLLAMA_API_URL += "/api"

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")

# --- UPGRADE: ANTI-CRASH POLICY ---
# These models are never auto-selected by the orchestrator.
# They require explicit manual selection in the UI.
ULTRA_TIER_MODELS = [
    "deepseek-v2:32b", "qwen2:32b", "llama3:70b", 
    "deepseek-r1:32b", "qwen2.5:32b", "phi3:14b",
    "qwen3:14b", "qwen2.5:14b" # 14B models are now strictly excluded from auto-logic
]

# --- UPGRADE: HIGH-FIDELITY ROUTING ---
DYNAMIC_ROUTING_ENABLED = True
ROUTING_FALLBACK_MODEL = "llama3.1:8b"
PRIMARY_REASONING_MODEL = "deepseek-r1:32b"
PRIMARY_CODING_MODEL = "qwen3-coder:30b"

MODE_CONFIG = {
    "fast-web": {
        "title": "⚡ Fast Web Search",
        "short": "Quick answers using live web data",
        "description": "Fetches top web results and generates a fast summary. Skips deep verification for speed.",
        "use_case": "Use for quick facts, general questions, or when speed matters",
        "example": "latest AI trends"
    },
    "deep": {
        "title": "🔍 Deep Research",
        "short": "Accurate, verified multi-step research",
        "description": "Performs multi-step search, filtering, and verification. Produces structured, high-confidence reports.",
        "use_case": "Use for reports, analysis, or important topics",
        "example": "economic impact of climate change"
    },
    "code": {
        "title": "💻 Code Assistant",
        "short": "Write, debug, and explain code",
        "description": "Uses specialized coding models to generate and fix code. Provides step-by-step explanations.",
        "use_case": "Use for programming, debugging, and system design",
        "example": "fix python recursion error"
    },
    "write": {
        "title": "✍️ Writing Assistant",
        "short": "Generate structured content",
        "description": "Creates essays, reports, and formatted content. Focuses on clarity and structure.",
        "use_case": "Use for blogs, reports, notes",
        "example": "write report on blockchain"
    },
    "chat": {
        "title": "💬 General Chat",
        "short": "Conversational AI assistant",
        "description": "Handles casual conversation, brainstorming, and general queries.",
        "use_case": "Use for normal chatting or creative thinking",
        "example": "give me startup ideas"
    },
    "summarize": {
        "title": "🧾 Summarizer",
        "short": "Condense long content",
        "description": "Reduces long text into key points and summaries.",
        "use_case": "Use for articles, notes, documents",
        "example": "summarize this article"
    },
    "translate": {
        "title": "🌍 Translator",
        "short": "Translate between languages",
        "description": "Translates text while preserving meaning and tone.",
        "use_case": "Use for multilingual tasks",
        "example": "translate to hindi"
    },
    "rag": {
        "title": "📂 Local Knowledge",
        "short": "Answer using your own data",
        "description": "Uses embeddings to retrieve answers from local documents.",
        "use_case": "Use for personal notes or uploaded files",
        "example": "search in my documents"
    },
    "optimize": {
        "title": "🧠 Query Optimizer",
        "short": "Improve search queries",
        "description": "Rewrites vague questions into precise search queries.",
        "use_case": "Use before research for better results",
        "example": "blockchain types"
    },
    "sources": {
        "title": "🔎 Source Finder",
        "short": "Get relevant sources only",
        "description": "Returns top relevant links without summaries.",
        "use_case": "Use for research and validation",
        "example": "sources for AI ethics"
    },
    "compare": {
        "title": "📊 Compare",
        "short": "Compare two entities",
        "description": "Generates side-by-side comparisons of two items.",
        "use_case": "Use for decision making",
        "example": "Tesla vs BYD"
    },
    "explain": {
        "title": "🧠 Explain",
        "short": "Explain concepts clearly",
        "description": "Provides simple or deep explanations depending on query.",
        "use_case": "Use for learning concepts",
        "example": "explain AI simply"
    },
    "fact-check": {
        "title": "🧾 Fact Checker",
        "short": "Verify claims with evidence",
        "description": "Checks accuracy of statements using sources.",
        "use_case": "Use to validate information",
        "example": "is AI replacing jobs"
    },
    "learn": {
        "title": "📚 Learning Mode",
        "short": "Structured study notes",
        "description": "Breaks topics into concepts, examples, and summaries.",
        "use_case": "Use for studying",
        "example": "learn python basics"
    },
    "plan": {
        "title": "🧠 Planner",
        "short": "Create step-by-step plans",
        "description": "Generates structured plans for goals or learning.",
        "use_case": "Use for roadmap creation",
        "example": "plan to learn AI"
    },
    "debug": {
        "title": "🧪 Debug Assistant",
        "short": "Analyze errors and logs",
        "description": "Finds root cause and fixes for errors.",
        "use_case": "Use for debugging",
        "example": "fix this stack trace"
    },
    "memory": {
        "title": "🧠 Memory Insight",
        "short": "Use past conversation",
        "description": "Retrieves relevant past interactions.",
        "use_case": "Use for follow-ups",
        "example": "what did I ask before"
    },
    "url": {
        "title": "🔗 URL Summarizer",
        "short": "Summarize a webpage",
        "description": "Extracts and summarizes content from a given link.",
        "use_case": "Use for reading web pages quickly",
        "example": "summarize https://..."
    },
    "doc": {
        "title": "📝 Document Engine",
        "short": "Create & edit professional documents",
        "description": "Creates reports, essays, emails, notes, and code docs with iterative editing and version control.",
        "use_case": "Use for writing, editing, or reformatting documents",
        "example": "write a report on AI"
    }
}
