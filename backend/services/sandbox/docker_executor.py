import docker
import logging
import asyncio
import os
import tempfile

logger = logging.getLogger(__name__)

class DockerExecutor:
    """
    Secure Python Sandbox Execution Environment.
    Uses moby-engine/docker to safely execute LLM-generated code.
    """
    def __init__(self):
        try:
            self.client = docker.from_env()
            # Pre-pull the slim python image if not exists
            logger.info("🐳 [SANDBOX] Connecting to Docker Daemon...")
            try:
                self.client.images.get("python:3.12-slim")
            except docker.errors.ImageNotFound:
                logger.info("🐳 [SANDBOX] Pulling python:3.12-slim image (this may take a moment)...")
                self.client.images.pull("python:3.12-slim")
            logger.info("✅ [SANDBOX] Secure Execution Environment ready.")
            self.is_active = True
        except Exception as e:
            logger.warning(f"⚠️ [SANDBOX] Docker daemon unavailable. Code execution disabled. Error: {e}")
            self.client = None
            self.is_active = False

    async def execute_python(self, code: str, timeout: int = 10) -> dict:
        """Executes python code string securely in an ephemeral container."""
        if not self.is_active:
            return {"status": "error", "output": "Sandbox environment is offline. Is Docker running?"}
            
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, "script.py")
            with open(script_path, "w") as f:
                f.write(code)
                
            try:
                logger.info("🐳 [SANDBOX] Spawning ephemeral container execution...")
                container = self.client.containers.run(
                    "python:3.12-slim",
                    command=f"python /sandbox/script.py",
                    volumes={tmpdir: {'bind': '/sandbox', 'mode': 'ro'}},
                    working_dir="/sandbox",
                    network_mode="none", # Strict isolation (no internet)
                    mem_limit="100m",    # RAM protection
                    detach=True
                )
                
                # Await completion
                try:
                    result = container.wait(timeout=timeout)
                    logs = container.logs().decode('utf-8')
                    container.remove(force=True)
                    
                    if result['StatusCode'] == 0:
                        logger.info("✅ [SANDBOX] Execution succeeded.")
                        return {"status": "success", "output": logs.strip()}
                    else:
                        logger.warning(f"⚠️ [SANDBOX] Execution failed with status {result['StatusCode']}.")
                        return {"status": "error", "output": logs.strip()}
                except Exception as wait_e:
                    container.remove(force=True)
                    return {"status": "error", "output": f"Execution timed out or failed: {wait_e}"}
                    
            except Exception as e:
                logger.error(f"❌ [SANDBOX] Container launch failed: {e}")
                return {"status": "error", "output": str(e)}

docker_sandbox = DockerExecutor()
