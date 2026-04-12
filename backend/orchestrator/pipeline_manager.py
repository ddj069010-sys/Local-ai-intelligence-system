import logging
from typing import Dict, Any, Optional
from core.config import settings, ModelTier
from core.tracing import get_trace
from routing.hybrid_router import hybrid_router, Intent
from routing.model_selector import model_selector
from orchestrator.task_classifier import task_classifier
from services.intelligence.response_proofer import evaluate_response, refine_response
from ui.dashboard import add_trace_to_ui
from core.logger import pipeline_logger

class PipelineManager:
    """
    The central coordinator for all AI request pipelines.
    Handles the request lifecycle: Tracing -> Routing -> Selection -> Execution.
    """
    
    def __init__(self):
        self.logger = pipeline_logger

    async def process_request(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processes a single user request through the AI pipeline.
        """
        has_files = bool(context and context.get("files"))
        
        # 1. Initialize Trace
        with get_trace() as trace:
            
            # 2. Resource Guard: Is the laptop thermal/RAM safe?
            if not model_selector.load_guard():
                return {
                    "output": "⚠️ [SYSTEM] Request blocked due to high system workload or low RAM. Please wait.",
                    "status": "blocked",
                    "trace_id": trace.request_id
                }

            # 3. Step: Intent Routing
            trace.start_stage("routing")
            decision = hybrid_router.route(query, has_files=has_files)
            
            intent = decision.intent
            complexity = ModelTier.MEDIUM

            reason = decision.reason
            
            # Fallback to LLM Classifier if rule confidence is low
            if decision.is_fallback:
                intent, reason, complexity = await task_classifier.classify(query)
            
            trace.finish_stage("routing", intent=intent, reason=reason)
            
            # 4. Step: Model Selection (Worker Node)
            trace.start_stage("selection")
            # For GPT-Lifestyle, we use WORKER_MODEL for initial execution
            selected_model = settings.WORKER_MODEL if settings.VERIFICATION_ENABLED else model_selector.select_best_model(requested_tier=complexity)
            trace.finish_stage("selection", model=selected_model, tier="worker")

            # 5. Step: Tool Execution (Worker Phase)
            trace.start_stage("execution")
            raw_output = self._mock_execution(intent, selected_model, query)
            trace.finish_stage("execution")

            # 6. Step: Response Synthesis & Verification (Architect Phase)
            trace.start_stage("proofing")
            # Architect Node verifies and formats the final output
            synthesis_model = settings.ARCHITECT_MODEL
            evaluation = await evaluate_response(query, raw_output)

            # --- BEYOND-GPT: STRICT EXECUTION MODE ---
            # If evaluation suggests missing information, force a COMMAND output instead of an apology
            if evaluation.get("missing_info") and not any(cmd in raw_output for cmd in ["[SEARCH", "[FILE"]):
                raw_output = f"### [STRICT_EXECUTION_MODE]\nMissing critical data for '{query}'. Proposing system actions:\n- [SEARCH_COMMAND(q='{query}')]\n- [FILE_READ_CMD(path='workspace/relevant_docs')]"

            # Refine using the Architect model for 90% less hallucination
            refined_content = await refine_response(query, raw_output, evaluation)
            score = float((evaluation.get("clarity_score", 5) + evaluation.get("completeness_score", 5)) / 2)
            trace.finish_stage("proofing", model=synthesis_model, score=score)



            res = {
                "output": refined_content,
                "intent": intent,
                "model": selected_model,
                "status": "success",
                "proof_score": f"{score:.2f}",
                "trace_id": trace.request_id,
                "latency": f"{trace.total_time:.2f}s"
            }
            
            # Add to UI history
            add_trace_to_ui(res)
            
            return res

    def _mock_execution(self, intent: Intent, model: str, query: str) -> str:
        """Temporary mock for tool execution until Phase 4."""
        return f"### [MOCK] Action: {intent.upper()} Mode\n- Model: {model}\n- Intent: {intent}\n- Query: {query}\n\n*This is a mock response pending full Tool integration.*"

# Singleton instance
pipeline_manager = PipelineManager()
