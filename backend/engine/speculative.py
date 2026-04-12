import asyncio
import logging
from typing import List, Dict, Any, Callable

logger = logging.getLogger(__name__)

class SpeculativeOrchestrator:
    """
    Executes multiple intelligence gathering tools in parallel to reduce latency.
    """
    @staticmethod
    async def scatter_gather(tasks: List[Callable]) -> List[Any]:
        """
        Runs identified tool tasks concurrently and returns gathered results.
        """
        try:
            results = await asyncio.gather(*[task() for task in tasks], return_exceptions=True)
            valid_results = []
            for res in results:
                if isinstance(res, Exception):
                    logger.error(f"Speculative Task Failed: {res}")
                else:
                    valid_results.append(res)
            return valid_results
        except Exception as e:
            logger.error(f"Orchestration Error: {e}")
            return []

    @staticmethod
    async def identify_parallel_paths(prompt: str) -> List[str]:
        """
        Heuristic-based parallel path identification.
        """
        paths = []
        lower_prompt = prompt.lower()
        if any(kw in lower_prompt for kw in ["search", "find", "latest", "who is", "what is"]):
            paths.append("web_search")
        if any(kw in lower_prompt for kw in ["code", "script", "fix", "error", "debug"]):
            paths.append("code_verify")
        if any(kw in lower_prompt for kw in ["read", "scrape", "url", "extract"]):
            paths.append("web_scrape")
        if any(kw in lower_prompt for kw in ["memory", "past", "history", "recall"]):
            paths.append("memory_recall")
        return paths
