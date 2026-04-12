import os
import glob
import logging
import importlib.util
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ToolRouter:
    """
    Scavenges and manages dynamic custom tools for the Agentic Brain.
    Turns local scripts into usable AI capabilities in real-time.
    """
    def __init__(self, tools_dir: str = "backend/tools_custom"):
        self.tools_dir = tools_dir
        self.active_tools = {} # name -> metadata

    def scavenge_tools(self) -> List[Dict[str, Any]]:
        """
        Scans the custom tools directory and builds dynamic capability manifests.
        """
        tool_files = glob.glob(os.path.join(self.tools_dir, "*.py"))
        capabilities = []
        
        for file_path in tool_files:
            file_name = os.path.basename(file_path)
            tool_id = file_name.replace(".py", "")
            
            try:
                # Basic metadata extraction (using docstrings)
                with open(file_path, "r") as f:
                    content = f.read()
                    doc_match = content.split('"""')
                    description = doc_match[1].strip() if len(doc_match) > 2 else "No description available."
                
                tool_meta = {
                    "id": tool_id,
                    "path": file_path,
                    "description": description,
                    "type": "custom_script"
                }
                
                self.active_tools[tool_id] = tool_meta
                capabilities.append(tool_meta)
                logger.info(f"🛠️ [AGENCY] Scavenged custom tool: {tool_id}")
            except Exception as e:
                logger.error(f"❌ [AGENCY] Failed to scavenge {file_name}: {e}")
                
        return capabilities

    async def execute_tool(self, tool_id: str, args: str = "") -> str:
        """
        Safely executes a custom tool script in a child process.
        """
        if tool_id not in self.active_tools:
            return f"Error: Tool '{tool_id}' not found."

        tool_path = self.active_tools[tool_id]["path"]
        logger.info(f"⚙️ [AGENCY] Executing dynamic tool: {tool_id} (Args: {args})")
        
        try:
            # We use an OS call to ensure sandbox-like execution if needed
            # For now, we use a simple subprocess call
            import subprocess
            cmd = ["python", tool_path, str(args)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                 return result.stdout.strip()
            else:
                 return f"[Tool Error: {result.stderr.strip()}]"
        except Exception as e:
            return f"[Execution Error: {str(e)}]"

tool_router = ToolRouter()
