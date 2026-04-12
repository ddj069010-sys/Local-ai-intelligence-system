import logging
import asyncio
from engine.utils import call_ollama_json
from engine.config import OLLAMA_MODEL

logger = logging.getLogger(__name__)

class KnowledgeGraphBuilder:
    """
    Transforms research context into a Visual Mermaid.js Knowledge Graph.
    Uses zero-shot entity extraction to map the territory of the query.
    """
    
    @staticmethod
    async def build_from_context(question: str, context: str) -> str:
        """
        Extracts relationships from a text blob and returns a valid Mermaid string.
        """
        prompt = f"""
        Analyze the provided research context and extract the top 5-7 core entities and their relationships.
        Goal: Map the mental landscape of the answer.
        
        USER QUESTION: "{question}"
        RESEARCH CONTEXT: "{context[:8000]}"
        
        OUTPUT FORMAT (JSON ONLY):
        {{
          "entities": ["Entity A", "Entity B"],
          "relationships": [
            {{"from": "Entity A", "to": "Entity B", "label": "interacts with"}},
            {{"from": "Entity B", "to": "Entity C", "label": "depends on"}}
          ]
        }}
        """
        
        try:
            data = await call_ollama_json(prompt, OLLAMA_MODEL)
            if not data or "relationships" not in data:
                return ""

            # Standardizing IDs (no spaces or special chars for Mermaid)
            def clean_id(name):
                return "".join(c if c.isalnum() else "_" for c in name)

            # Build the graph string
            # graph TD or flowchart TD
            lines = ["graph TD"]
            
            # Add classes for styling
            lines.append("  classDef default fill:#1e293b,stroke:#3b82f6,color:#fff,stroke-width:2px,rx:10,ry:10;")
            
            for rel in data["relationships"]:
                from_id = clean_id(rel["from"])
                to_id = clean_id(rel["to"])
                label = rel.get("label", "relates to")
                
                # Mermaid syntax: ID["Label Text"] -->|Relationship| ID2["Label Text"]
                lines.append(f"  {from_id}[\"{rel['from']}\"] -->|\"{label}\"| {to_id}[\"{rel['to']}\"]")
            
            return "\n".join(lines)

        except Exception as e:
            logger.error(f"❌ [GRAPH BUILDER] Failed to construct knowledge graph: {e}")
            return ""

graph_builder = KnowledgeGraphBuilder()
