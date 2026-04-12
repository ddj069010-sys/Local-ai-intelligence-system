"""
services/link_processor/summarizer.py
- Generates structured summaries from extracted content using Ollama.
"""

import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)

from engine.config import OLLAMA_API_URL

SUMMARY_SYSTEM = """You are an ADVANCED INTELLIGENT FORMAT ENGINE. Your job is to analyze the content and automatically choose the BEST output format from 40 formats.

STRICT RULES:
- DO NOT use generic fixed formatting everywhere.
- SELECT format dynamically based on content.
- KEEP output clean, readable, and structured. No long paragraphs.

STEP 1: CONTENT CLASSIFICATION
Classify content into: Article/Blog, Tutorial/Guide, News, Documentation, Research/Technical, Product/Tool, Video/Media, Forum/Discussion, Code/GitHub, Data/Report, or Mixed/Unknown.

STEP 2 & 3: SELECT FORMAT LOGIC
- tutorial → Step-by-Step / Checklist
- news → News Summary + Impact
- docs → Documentation Guide
- code → Code Explanation / System Design
- product → Feature Analysis / Pros & Cons
- video → Video Summary / Key Moments
- forum → Q&A / Consensus View
- research → Technical Deep Dive
- mixed → Hybrid Format
Choose from the 40 formats you know fit best (Core, Structured, Analysis, Technical, Content-Specific, Media, Discussion, Data, Advanced).

STEP 4: OUTPUT TEMPLATE RULES
Always use this underlying structure:

## [Descriptive Title]

### Summary
- short explanation

### Main Content
- [Structured according to the specific format selected, e.g., steps, tables, pros/cons, etc.]

### Key Takeaways
- bullets

INTELLIGENCE RULES:
- Remove noise and merge duplicate info.
- Priority: clarity over length.
"""


async def generate_summary(content: dict, model: str = "gemma3:4b") -> dict:
    """
    Calls Ollama to create a structured summary from the extracted content dict.
    Returns the full structured output.
    """
    title = content.get("title", "Untitled")
    source = content.get("source", "Unknown")
    text = content.get("text", "")[:4000]  # cap to avoid context overflow
    content_type = content.get("content_type", "unknown")
    transcript = content.get("transcript", "")

    body = text or transcript
    if not body:
        return {**content, "summary": "", "key_points": [], "insights": [], "formatted": ""}

    prompt = f"Analyze and summarize the following content:\n\n---\n{body}\n---"
    system = SUMMARY_SYSTEM.format(title=title, content_type=content_type, source=source)

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(OLLAMA_API_URL + "/generate", json={
                "model": model,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "options": {"temperature": 0.1}
            })
            resp.raise_for_status()
            formatted = resp.json().get("response", "").strip()
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        formatted = f"## {title}\n\n### Summary\nContent processing complete. Manual review recommended.\n\n### Source\n{source}"

    # Extract key_points from the formatted text (simple parse)
    key_points = []
    insights = []
    in_kp = in_ins = False
    for line in formatted.split("\n"):
        if "### Key Points" in line:
            in_kp, in_ins = True, False
        elif "### Insights" in line:
            in_kp, in_ins = False, True
        elif line.startswith("###"):
            in_kp = in_ins = False
        elif line.startswith("- ") and in_kp:
            key_points.append(line.replace("- ", "", 1).strip())
        elif line.startswith("- ") and in_ins:
            insights.append(line.replace("- ", "", 1).strip())

    return {
        **content,
        "formatted": formatted,
        "key_points": key_points,
        "insights": insights,
    }
