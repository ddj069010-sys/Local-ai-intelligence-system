import re

class ResponseOptimizer:
    """Enhances clarity and removals redundancies from final LLM response."""
    
    @staticmethod
    def optimize(content: str, mode: str = "chat") -> str:
        """Improve clarity, remove repetition, and ensure structural flow."""
        if not content:
            return content
            
        # 1. Deduplicate consecutive duplicate titles/headers
        lines = content.split('\n')
        optimized_lines = []
        seen_headers = set()
        for line in lines:
            trimmed = line.strip()
            if trimmed.startswith('#'):
                # Normalize header to avoid minor variation duplication
                normalized = re.sub(r'[^a-zA-Z0-9#]', '', trimmed).lower()
                if normalized in seen_headers and len(normalized) > 3:
                    continue
                seen_headers.add(normalized)
            optimized_lines.append(line)
        
        optimized = '\n'.join(optimized_lines)
        
        # 2. Prune common redundant prefix fillers
        redundant_fillers = [
            r"^In summary,.*",
            r"^To conclude,.*",
            r"^Based on my analysis,.*",
            r"^I have analyzed the query and.*"
        ]
        for filler in redundant_fillers:
            optimized = re.sub(filler, "", optimized, flags=re.MULTILINE | re.IGNORECASE)
            
        # 3. Ensure a professional structure (ONLY for formal modes)
        conversational = ["chat", "simple", "direct", "wellness"]
        if "## " not in optimized and len(optimized) > 400 and mode not in conversational:
            optimized = f"## Intelligence Synthesis\n\n### Summary\n" + optimized
            
        return optimized.strip()
            
        return optimized.strip()
