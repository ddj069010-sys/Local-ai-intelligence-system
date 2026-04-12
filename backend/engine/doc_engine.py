"""
engine/doc_engine.py
--------------------
Document Creation Engine — 6-Layer GPT-like Document System.

Layers:
  1. Doc Controller  — Detect intent (create/edit/summarize/expand/rewrite/format)
  2. Doc Planner     — Generate outline BEFORE writing
  3. Doc Generator   — Write content following the plan
  4. Doc Formatter   — Apply professional markdown formatting
  5. Doc Editor      — Handle iterative edits on existing documents
  6. Master Pipeline — Orchestrate all layers as a single async generator
"""

import json
import logging
import re
from typing import Optional, Dict, Any

from .utils import call_ollama, call_ollama_stream, call_ollama_json
from .doc_store import doc_version_store, DocVersion
from .formatter import FormatEngine

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 1 — DOC CONTROLLER (INTENT DETECTION)
# ═══════════════════════════════════════════════════════════════════════════════

DOC_CONTROLLER_PROMPT = """You are a document intent classifier.
Analyze the user's message and return ONLY valid JSON:
{
  "doc_action": "create | edit | summarize | expand | rewrite | format",
  "doc_type": "report | essay | email | notes | blog | code_doc",
  "tone": "formal | casual | professional",
  "length": "short | medium | long",
  "target_section": null or "section name to edit"
}

CLASSIFICATION RULES:
1. "write", "create", "make", "draft", "generate", "compose" → create
2. "improve", "fix", "edit", "update", "modify", "change" → edit
3. "summarize", "shorten", "condense", "make shorter", "tldr" → summarize
4. "expand", "elaborate", "add more", "add details", "add examples" → expand
5. "rewrite", "rephrase", "convert to", "transform", "make it" → rewrite
6. "format", "style", "restructure", "layout" → format
7. If the user references a SPECIFIC SECTION (e.g. "fix the intro"), set target_section.
8. Default tone = professional, default length = medium, default type = report.

RETURN JSON ONLY. NO EXPLANATION."""

# Fast keyword-based fallback (no LLM call needed for obvious cases)
_ACTION_KEYWORDS = {
    "create": ["write", "create", "make a ", "draft", "generate", "compose", "make me"],
    "edit": ["improve", "fix", "edit", "update", "modify", "change", "correct"],
    "summarize": ["summarize", "shorten", "condense", "make shorter", "make it shorter", "tldr", "brief"],
    "expand": ["expand", "elaborate", "add more", "add detail", "add example", "longer", "make it longer"],
    "rewrite": ["rewrite", "rephrase", "convert to", "transform to", "turn into", "make it a", "convert into"],
    "format": ["format", "restructure", "restyle", "layout", "beautify"],
}

_TYPE_KEYWORDS = {
    "report": ["report", "analysis", "study", "paper", "research"],
    "essay": ["essay", "article", "piece", "composition"],
    "email": ["email", "mail", "message", "letter"],
    "notes": ["notes", "memo", "minutes", "jot", "outline"],
    "blog": ["blog", "post", "blog post"],
    "code_doc": ["readme", "documentation", "api doc", "code doc", "docstring"],
}

_TONE_KEYWORDS = {
    "formal": ["formal", "academic", "scholarly"],
    "casual": ["casual", "informal", "relaxed", "friendly", "fun"],
    "professional": ["professional", "business", "corporate"],
}


def _fast_classify(query: str) -> Dict[str, Any]:
    """Keyword-based fast classification — no LLM call required."""
    q = query.lower().strip()
    result = {
        "doc_action": "create",
        "doc_type": "report",
        "tone": "professional",
        "length": "medium",
        "target_section": None,
    }

    # Detect action
    for action, keywords in _ACTION_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            result["doc_action"] = action
            break

    # Detect doc type
    for doc_type, keywords in _TYPE_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            result["doc_type"] = doc_type
            break

    # Detect tone
    for tone, keywords in _TONE_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            result["tone"] = tone
            break

    # Detect length signals
    if any(kw in q for kw in ["short", "brief", "concise", "quick"]):
        result["length"] = "short"
    elif any(kw in q for kw in ["long", "detailed", "comprehensive", "in-depth", "thorough"]):
        result["length"] = "long"

    return result


async def detect_doc_intent(query: str, model: str = "gemma3:4b") -> Dict[str, Any]:
    """Layer 1: Classify user intent — uses fast keyword match with LLM fallback."""
    # Try fast path first
    fast_result = _fast_classify(query)

    # For ambiguous cases, use LLM for precision
    q_lower = query.lower().strip()
    is_ambiguous = (
        len(q_lower.split()) > 12
        or "it" in q_lower.split()[:3]
        or not any(any(kw in q_lower for kw in kws) for kws in _ACTION_KEYWORDS.values())
    )

    if is_ambiguous:
        try:
            llm_result = await call_ollama_json(query, model=model, system=DOC_CONTROLLER_PROMPT)
            if isinstance(llm_result, dict) and llm_result.get("doc_action"):
                return llm_result
        except Exception as e:
            logger.warning(f"[DocController] LLM classification failed: {e}")

    return fast_result


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 2 — DOC PLANNER (STRUCTURE GENERATION)
# ═══════════════════════════════════════════════════════════════════════════════

DOC_PLANNER_PROMPT = """You are a document structure planner.
Create an outline for the requested document. Return ONLY valid JSON:
{
  "title": "Document Title",
  "sections": ["Section 1", "Section 2", "Section 3", ...]
}

STRUCTURE RULES BY TYPE:
- report: ["Introduction", "Background", "Analysis", "Key Findings", "Conclusion", "Recommendations"]
- essay: ["Introduction", "Thesis", "Body", "Counter-Arguments", "Conclusion"]
- email: ["Subject Line", "Greeting", "Body", "Call to Action", "Sign-off"]
- notes: ["Overview", "Key Points", "Details", "Action Items"]
- blog: ["Hook", "Introduction", "Main Content", "Practical Tips", "Conclusion"]
- code_doc: ["Overview", "Installation", "Usage", "API Reference", "Examples", "Contributing"]

RULES:
1. Adapt sections to the TOPIC — add relevant domain-specific sections.
2. Keep 4-8 sections max.
3. Title should be clear and professional.
RETURN JSON ONLY."""

# Static fallback templates
_PLAN_TEMPLATES = {
    "report": ["Introduction", "Background", "Analysis", "Key Findings", "Conclusion"],
    "essay": ["Introduction", "Thesis", "Body", "Conclusion"],
    "email": ["Subject Line", "Greeting", "Body", "Call to Action", "Sign-off"],
    "notes": ["Overview", "Key Points", "Details", "Action Items"],
    "blog": ["Hook", "Introduction", "Main Content", "Tips", "Conclusion"],
    "code_doc": ["Overview", "Installation", "Usage", "API Reference", "Examples"],
}


async def plan_document(query: str, intent: Dict, model: str = "gemma3:4b") -> Dict:
    """Layer 2: Generate document structure/outline."""
    doc_type = intent.get("doc_type", "report")

    try:
        planning_prompt = f"Document type: {doc_type}\nTone: {intent.get('tone', 'professional')}\nUser request: {query}"
        plan = await call_ollama_json(planning_prompt, model=model, system=DOC_PLANNER_PROMPT)

        if isinstance(plan, dict) and plan.get("title") and plan.get("sections"):
            return plan
    except Exception as e:
        logger.warning(f"[DocPlanner] LLM planning failed: {e}")

    # Static fallback
    words = query.split()
    topic = " ".join(w for w in words if w.lower() not in {"write", "create", "make", "a", "an", "the", "about", "on"})
    title = topic.strip().title() if topic.strip() else "Document"
    return {
        "title": title,
        "sections": _PLAN_TEMPLATES.get(doc_type, _PLAN_TEMPLATES["report"]),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 3 — DOC GENERATOR (CONTENT CREATION)
# ═══════════════════════════════════════════════════════════════════════════════

def _build_generator_prompt(intent: Dict, plan: Dict) -> str:
    """Builds a precise system prompt for the document generator."""
    tone = intent.get("tone", "professional")
    length = intent.get("length", "medium")
    doc_type = intent.get("doc_type", "report")

    length_guide = {
        "short": "Keep each section to 2-3 sentences. Total document under 300 words.",
        "medium": "Write 1-2 paragraphs per section. Total document 500-800 words.",
        "long": "Write detailed, comprehensive paragraphs. Total document 1000-1500 words.",
    }

    return f"""You are a professional document writer.

DOCUMENT SPEC:
- Type: {doc_type}
- Tone: {tone}
- Length: {length_guide.get(length, length_guide['medium'])}

STRUCTURE TO FOLLOW:
Title: {plan.get('title', 'Document')}
Sections: {', '.join(plan.get('sections', []))}

STRICT RULES:
1. Write the document using EXACTLY the sections provided above.
2. Use # for the title, ## for each section heading.
3. Maintain {tone} tone throughout — no breaks in voice.
4. Write coherent, flowing prose — no bullet-point dumps unless it's notes/code_doc type.
5. No emojis (unless tone is casual).
6. No unnecessary repetition or filler phrases.
7. No meta-commentary ("In this section, we will...") — just write the content directly.
8. End with a strong concluding thought, not a question.

OUTPUT FORMAT: Clean markdown document. Start immediately with # Title."""


async def generate_document(query: str, intent: Dict, plan: Dict, model: str):
    """Layer 3: Generate full document content as a stream."""
    system = _build_generator_prompt(intent, plan)
    section_list = "\n".join(f"- {s}" for s in plan.get("sections", []))
    prompt = f"Write the following document:\nTopic: {query}\n\nSections:\n{section_list}"

    async for token in call_ollama_stream(prompt, model, system=system):
        yield token


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 4 — DOC FORMATTER (PROFESSIONAL LAYOUT)
# ═══════════════════════════════════════════════════════════════════════════════

def format_document(content: str, doc_type: str = "report") -> str:
    """Layer 4: Apply professional markdown formatting to generated content."""
    if not content:
        return ""

    text = content.strip()

    # 1. Ensure title is H1
    lines = text.split("\n")
    if lines and not lines[0].startswith("# "):
        first_line = lines[0].strip().lstrip("#").strip()
        if first_line and len(first_line) < 100:
            lines[0] = f"# {first_line}"
            text = "\n".join(lines)

    # 2. Ensure sections are H2
    text = re.sub(r"^(?!#)((?:Introduction|Background|Analysis|Conclusion|Summary|"
                  r"Overview|Key (?:Points|Findings)|Recommendations|Body|"
                  r"Subject Line|Greeting|Sign-off|Call to Action|"
                  r"Hook|Main Content|Tips|Installation|Usage|API Reference|Examples|"
                  r"Thesis|Counter-Arguments|Details|Action Items|Contributing)[:\s]*$)",
                  r"## \1", text, flags=re.MULTILINE | re.IGNORECASE)

    # 3. Clean up spacing — ensure blank line before headers
    text = re.sub(r"(\S)\n(#{1,3} )", r"\1\n\n\2", text)

    # 4. Clean double blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 5. Email-specific formatting
    if doc_type == "email":
        # Don't apply heavy report formatting to emails
        text = text.replace("## Subject Line", "**Subject:**")
        text = text.replace("## Greeting", "")
        text = text.replace("## Sign-off", "")
        text = text.replace("## Call to Action", "")
        text = text.replace("## Body", "")

    # 6. Apply emoji hydration for non-email types
    if doc_type != "email":
        try:
            text = FormatEngine._hydrate_emojis(text)
        except Exception:
            pass

    # 7. Apply layout polish
    try:
        text = FormatEngine.polish_markdown_layout(text)
    except Exception:
        pass

    return text.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 5 — DOC EDITOR (ITERATIVE EDITING)
# ═══════════════════════════════════════════════════════════════════════════════

DOC_EDITOR_PROMPT = """You are a professional document editor.
You will receive an EXISTING DOCUMENT and an EDIT INSTRUCTION.

STRICT RULES:
1. Modify ONLY the parts requested by the edit instruction.
2. Keep ALL other content UNCHANGED — do not rewrite sections that aren't mentioned.
3. Maintain the same document structure (headings, sections).
4. Preserve the original tone unless the instruction changes it.
5. If asked to "make it shorter" → condense each section, remove redundancy, keep key points.
6. If asked to "add examples" → insert concrete examples in relevant sections.
7. If asked to "rewrite professionally" → elevate vocabulary, formalize structure.
8. If asked to "convert to email/report/etc" → restructure the ENTIRE document into the new format.
9. Output the COMPLETE edited document, not just the changed parts.

OUTPUT: The full edited document in clean markdown. Start with # Title."""


async def edit_document(query: str, existing_content: str, intent: Dict, model: str):
    """Layer 5: Edit an existing document based on user instruction."""
    doc_action = intent.get("doc_action", "edit")
    target_section = intent.get("target_section")

    # Build edit instruction
    section_note = f"\nFOCUS ON SECTION: {target_section}" if target_section else ""

    prompt = (
        f"EDIT INSTRUCTION: {query}\n"
        f"ACTION TYPE: {doc_action}{section_note}\n\n"
        f"EXISTING DOCUMENT:\n{existing_content}"
    )

    async for token in call_ollama_stream(prompt, model, system=DOC_EDITOR_PROMPT):
        yield token


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 6 — MASTER PIPELINE (ORCHESTRATOR)
# ═══════════════════════════════════════════════════════════════════════════════

async def doc_creation_pipeline(question: str, model: str, chat_id: str = "default"):
    """
    Master Document Pipeline — entry point for the doc mode.
    Routes: detect intent → plan → generate → format (create)
            detect intent → edit (edit/summarize/expand/rewrite)
    Stores each version in DocVersionStore.
    """
    from .model_manager import ModelManager

    # ── STEP 1: INTENT DETECTION ──
    yield {"type": "thought", "text": "📝 Doc Engine: Analyzing document intent..."}

    logic_model = await ModelManager.get_best_model(
        mode="chat", question=question, requested_model="gemma3:4b", purpose="extraction"
    )
    intent = await detect_doc_intent(question, model=logic_model)
    doc_action = intent.get("doc_action", "create")
    doc_type = intent.get("doc_type", "report")
    tone = intent.get("tone", "professional")

    yield {"type": "thought", "text": f"📋 Intent: {doc_action.upper()} → {doc_type} ({tone} tone)"}

    # ── STEP 2: CHECK FOR EXISTING DOCUMENT (Edit Path) ──
    latest = doc_version_store.get_latest(chat_id)
    is_edit = doc_action in ("edit", "summarize", "expand", "rewrite", "format") and latest is not None

    if is_edit:
        # ── EDIT PATH ──
        version_num = doc_version_store.get_version_count(chat_id)
        yield {"type": "thought", "text": f"✏️ Editor: Modifying v{version_num} ({doc_action})..."}

        gen_model = await ModelManager.get_best_model(
            mode="chat", question=question, requested_model=model, purpose="reasoning"
        )

        edited_content = ""
        async for token in edit_document(question, latest.content, intent, gen_model):
            edited_content += token
            yield {"type": "message", "text": token}

        # Format the edited content
        final_content = format_document(edited_content, doc_type=intent.get("doc_type", latest.doc_type))

        # If formatting changed the content, send the update
        if final_content != edited_content:
            yield {"type": "message_update", "text": final_content}

        # Save new version
        doc_version_store.save_version(
            chat_id, final_content,
            doc_type=intent.get("doc_type", latest.doc_type),
            tone=intent.get("tone", latest.tone),
            action=doc_action,
        )
        new_count = doc_version_store.get_version_count(chat_id)
        yield {"type": "thought", "text": f"💾 Version saved: v{new_count} ({doc_action})"}
        return

    # ── CREATE PATH ──
    # ── STEP 3: PLAN ──
    yield {"type": "thought", "text": "🗂️ Planner: Building document structure..."}
    plan = await plan_document(question, intent, model=logic_model)
    title = plan.get("title", "Document")
    sections = plan.get("sections", [])

    yield {"type": "thought", "text": f"📐 Structure: \"{title}\" — {len(sections)} sections: {', '.join(sections[:4])}{'...' if len(sections) > 4 else ''}"}

    # ── STEP 4: GENERATE ──
    gen_model = await ModelManager.get_best_model(
        mode="chat", question=question, requested_model=model, purpose="reasoning"
    )
    yield {"type": "thought", "text": f"✍️ Generator: Writing document via {gen_model}..."}

    raw_content = ""
    async for token in generate_document(question, intent, plan, gen_model):
        raw_content += token
        yield {"type": "message", "text": token}

    # ── STEP 5: FORMAT ──
    yield {"type": "thought", "text": "🎨 Formatter: Applying professional layout..."}
    final_content = format_document(raw_content, doc_type=doc_type)

    if final_content != raw_content:
        yield {"type": "message_update", "text": final_content}

    # ── STEP 6: SAVE VERSION ──
    doc_version_store.save_version(
        chat_id, final_content,
        doc_type=doc_type,
        tone=tone,
        action="create",
    )
    yield {"type": "thought", "text": "💾 Version saved: v1 (original)"}
