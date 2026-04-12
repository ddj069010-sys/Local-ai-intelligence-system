import json
import os
import logging

logger = logging.getLogger(__name__)

# Persistent storage path
WORKSPACE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "workspace.json")

# Unified Workspace State
# Structure: { sessionId: { "docs": [], "chunks": [], "embeddings": [], "metadata": {} } }
WORKSPACE = {}

def save_workspace():
    """Persists the current WORKSPACE state to disk."""
    try:
        os.makedirs(os.path.dirname(WORKSPACE_FILE), exist_ok=True)
        with open(WORKSPACE_FILE, 'w') as f:
            json.dump(WORKSPACE, f)
        logger.info(f"Workspace saved to {WORKSPACE_FILE}")
    except Exception as e:
        logger.error(f"Failed to save workspace: {e}")

def load_workspace():
    """Loads the WORKSPACE state from disk if available."""
    global WORKSPACE
    if os.path.exists(WORKSPACE_FILE):
        try:
            with open(WORKSPACE_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    WORKSPACE.update(data)
                    logger.info(f"Workspace loaded from {WORKSPACE_FILE}")
        except Exception as e:
            logger.error(f"Failed to load workspace: {e}")

# Auto-load on initialization
load_workspace()

# Legacy alias for backward compatibility
GLOBAL_DOCUMENT_MEMORY = WORKSPACE
