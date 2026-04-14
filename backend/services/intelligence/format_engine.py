import logging
import json
import re
from typing import Dict, Any, List
from engine.utils import call_ollama_json
from engine.config import OLLAMA_MODEL

logger = logging.getLogger(__name__)

# --- STEP 1: INTENT DETECTION ---
INTENTS = [
    "Explain", "Summarize", "Compare", "Analyze", 
    "Learn (tutorial)", "Debug", "Research", 
    "Extract info", "Decision making"
]

# --- STEP 2: CONTENT TYPE DETECTION ---
CONTENT_TYPES = [
    "Blog / Article", "Tutorial / Guide", "News", 
    "Documentation", "Research / Technical", "Product / Tool", 
    "Video / Media", "Forum / Discussion", "Code / GitHub", 
    "Data / Report", "Mixed / Unknown"
]

# --- STEP 3: FORMAT DEFINITIONS ---
FORMATS = {
    # BASIC
    "Direct Answer": "Concise answer to the question.",
    "Bullet Summary": "Key points in bullet form.",
    "TL;DR + Details": "Short summary followed by technical/deep details.",
    "Explanation Breakdown": "Conceptual breakdown of the topic.",
    "Key Insights": "Key takeaways and high-level findings.",
    
    # LEARNING
    "Step-by-Step Guide": "Ordered list of instructions.",
    "Concept + Example": "Definition followed by a concrete example.",
    "Beginner Explanation": "Simple language, analogies, no jargon.",
    "Advanced Explanation": "Deep dive into internals and low-level details.",
    "FAQ Format": "Question and Answer pairs.",
    
    # ANALYSIS
    "Pros & Cons": "Comparison of advantages and disadvantages.",
    "Comparison Table": "Structured markdown table comparing items.",
    "Decision Guide": "Framework for making a choice.",
    "Risk Analysis": "Identification of potential pitfalls.",
    "Impact Analysis": "Assessment of effects (short/long term).",
    
    # TECHNICAL
    "System Design": "High-level architectural components.",
    "Architecture Overview": "Diagram-like description of the system.",
    "Code Explanation": "Line-by-line or block-based logic breakdown.",
    "Debug Report": "Error analysis, root cause, and fix.",
    "Technical Deep Dive": "Exhaustive technical documentation.",
    
    # CONTENT-SPECIFIC
    "News Summary": "Who, what, where, when, why, and impact.",
    "Research Breakdown": "Methodology, findings, and conclusion.",
    "Documentation Guide": "How to use the library/tool.",
    "Product Breakdown": "Features, pricing, and use cases.",
    "Feature Analysis": "Deep dive into specific functionality.",
    
    # MEDIA
    "Video Summary": "Summary of the video content.",
    "Key Moments": "Timestamps with descriptions.",
    "Scene Breakdown": "Visual and narrative segments.",
    "Audio Insights": "Key quotes and audio-specific details.",
    "Visual Analysis": "Focus on what is shown on screen.",
    
    # DISCUSSION
    "Question + Answers": "Summary of thread and top answers.",
    "Community Insights": "What the users are saying/consensus.",
    "Debate Summary": "Different viewpoints in a thread.",
    "Consensus View": "The agreed-upon final answer.",
    
    # DATA
    "Data Summary": "Overview of statistics/metrics.",
    "Trend Analysis": "Changes over time.",
    "Statistics Breakdown": "Detailed numerical analysis.",
    "Insight Extraction": "What the data actually means.",
    
    # ADVANCED
    "Hybrid Format": "Combination of summary, details, and context.",
    "Deep Research Format": "Exhaustive multi-source synthesis."
}

async def detect_features(query: str, content_preview: str) -> Dict[str, str]:
    """Step 1 & 2: Detect Intent and Content Type using LLM."""
    prompt = f"""
    Analyze the following query and content preview.
    QUERY: "{query}"
    CONTENT PREVIEW: "{str(content_preview)[:1000]}"
    
    TASKS:
    1. Classify USER INTENT from: {INTENTS}
    2. Classify CONTENT TYPE from: {CONTENT_TYPES}
    
    Output MUST be valid JSON.
    """
    try:
        res = await call_ollama_json(prompt, OLLAMA_MODEL)
        return {
            "intent": res.get("intent", "Summarize"),
            "content_type": res.get("content_type", "Mixed / Unknown")
        }
    except Exception as e:
        logger.error(f"Feature detection failed: {e}")
        return {"intent": "Summarize", "content_type": "Mixed / Unknown"}

def select_format(intent: str, content_type: str) -> str:
    """Step 3 & 4: Select the best format based on Intent and Content Type."""
    # Logic mapping (simplified for implementation)
    if "Tutorial" in content_type or "Guide" in content_type:
        if intent == "Learn": return "Step-by-Step Guide"
        return "Explanation Breakdown"
        
    if "Code" in content_type:
        if intent == "Debug": return "Debug Report"
        return "Code Explanation"
        
    if "News" in content_type:
        return "News Summary"
        
    if "Video" in content_type or "Media" in content_type:
        return "Video Summary"
        
    if intent == "Compare":
        return "Comparison Table"
        
    if intent == "Research":
        return "Deep Research Format"
        
    if intent == "Analyze":
        return "Key Insights"
        
    return "Hybrid Format" # Fallback

async def get_format_instruction(format_name: str, query: str) -> str:
    """Returns specific instructions and structure for the chosen format."""
    format_desc = FORMATS.get(format_name, "Provide a helpful response.")
    
    return f"""
    PERSONA: Act as a Lead AI Research Engineer at Antigravity. Your tone is authoritative, highly intellectual, yet accessible.
    
    FORMAT: {format_name}
    DESCRIPTION: {format_desc}
    
    VISUAL POLISH RULES:
    1. Use **bolding** for all technical terms and key concepts.
    2. Use > blockquotes for important definitions or foundational principles.
    3. Use markdown tables ALWAYS when comparing more than 2 items.
    4. Maintain a high visual hierarchy with consistent header usage.
    
    STRICT STRUCTURE RULES:
        - ALWAYS start with: ## [Professional Descriptive Title]
    - ALWAYS follow with a: ### 🧠 Intelligence Overview (Dense 2-sentence executive summary)
    - MAIN CONTENT: Structured as {format_name}. Use subheaders like `#### Technical Components` or `#### Implementation Logic`.
    - INSERT: ### 🧠 Neural Reflection (Brief insight into 'why' this matters or a 'meta-thought' on the topic)
    - END WITH: ### 🚀 Strategic Takeaways (High-impact, actionable bullet points)
    - HEADER: Start with exactly what we are doing here.
    - CONTENT: Deliver the response in a sophisticated, clear GPT-style tone. Structured as {format_name}.
    - FOOTER: End with exactly one relevant follow-up question in italics.
    
    SPECIAL RULES:
    - IF Code: Use clear syntax-highlighted blocks with concise comments.
    - IF Research: Cite sources using [Source Name](URL) format.
    """
