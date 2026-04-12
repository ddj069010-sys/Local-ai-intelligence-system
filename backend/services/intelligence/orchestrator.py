import logging
from .query_enhancer import enhance_query
from .tool_selector import select_tools
from .context_manager import rank_context, validate_sources
from .response_proofer import evaluate_response, refine_response
from .confidence_engine import compute_confidence
from engine.utils import call_ollama_json
from engine.config import OLLAMA_MODEL

logger = logging.getLogger(__name__)

class IntelligenceOrchestrator:
    """
    Middleware orchestrator that coordinates all intelligence layers.
    """
    def __init__(self, model=OLLAMA_MODEL):
        self.model = model

    async def process_request(self, query: str, context_fetcher=None):
        """
        Coordinates the intelligence pipeline for a given query.
        """
        # 1. Query Enhancement
        yield {"type": "thought", "text": "Enhancing query intelligence..."}
        enhanced = await enhance_query(query)
        
        # 2. Tool Selection
        yield {"type": "thought", "text": "Analyzing intent and choosing tools..."}
        tools = await select_tools(enhanced)
        
        # 3. Context Prioritization (if context_fetcher provided)
        final_context = ""
        context_fragments = []
        if context_fetcher:
            yield {"type": "thought", "text": "Building prioritized context..."}
            # Fetch raw context first
            raw_context = await context_fetcher(enhanced["enhanced_query"])
            # Split raw context into fragments (simple split for demonstration)
            raw_fragments = raw_context.split("\n\n")
            context_fragments = await rank_context(enhanced["enhanced_query"], raw_fragments)
            final_context = "\n\n".join(context_fragments)
            
        yield {
            "type": "intelligence_data",
            "enhanced": enhanced,
            "tools": tools,
            "context": final_context,
            "fragments": context_fragments
        }

    async def finalize_response(self, query: str, response: str, fragments: list, query_type: str):
        """
        Evaluates and refines the final response.
        """
        # 1. Validation
        val = await validate_sources(fragments)
        
        # 2. Evaluation
        eval_res = await evaluate_response(query, response)
        
        # 3. Refinement using Intelligent Format Engine
        context_preview = fragments[0] if fragments else response
        refined = await refine_response(query, response, eval_res, context_preview=context_preview)
        
        # 4. Confidence
        confidence = compute_confidence(fragments, val["consistency"], query_type)
        
        return {
            "text": refined,
            "confidence": confidence,
            "metadata": {
                "mode": "IntelligenceLayer v1.0",
                "sources": len(fragments),
                "consistency": val["consistency"]
            }
        }

intelligence_orchestrator = IntelligenceOrchestrator()
