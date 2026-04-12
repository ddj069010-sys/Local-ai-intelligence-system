import asyncio
import logging
import sys
import os

# Set up logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# Add current dir to path
sys.path.append(os.getcwd())

from services.universal.indexer import deep_workspace_index

if __name__ == "__main__":
    print("Starting manual indexer test...")
    asyncio.run(deep_workspace_index())
    print("Manual indexer test finished.")
