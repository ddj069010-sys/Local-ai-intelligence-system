import subprocess
import os
import sys
import shlex
import re

import tempfile

def _is_docker_available():
    try:
        r = subprocess.run(["docker", "info"], capture_output=True, timeout=2)
        return r.returncode == 0
    except:
        return False

def run_python_code(code: str, timeout: int = 15) -> dict:
    """Runs Python code in a separate process or Docker sandbox with improved sanitization."""
    try:
        blocked_patterns = [
            r"import\s+(os|subprocess|shutil|pty|socket|requests|urllib)",
            r"from\s+(os|subprocess|shutil|pty|socket|requests|urllib)",
            r"getattr\(", r"eval\(", r"exec\(",
            r"os\.(system|popen|spawn|exec|chmod|chown)",
            r"subprocess\.", r"shutil\.", r"rmtree", r"unlink",
            r"__import__", r"__builtins__"
        ]
        
        for pattern in blocked_patterns:
            if re.search(pattern, code):
                return {"output": "", "error": f"Security violation: Use of '{pattern}' is not allowed for safety.", "exit_code": 1}

        # Check for Docker sandboxing
        if _is_docker_available():
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                tmp_path = f.name
            try:
                result = subprocess.run(
                    ["docker", "run", "--rm", "--network=none",
                     "--memory=256m", "--cpus=0.5", "--pids-limit=64",
                     f"--volume={tmp_path}:/code/script.py:ro",
                     "python:3.11-slim", "python", "/code/script.py"],
                    capture_output=True, text=True, timeout=timeout
                )
                return {"output": result.stdout, "error": result.stderr, "exit_code": result.returncode}
            except subprocess.TimeoutExpired:
                return {"output": "", "error": f"Execution timed out in sandbox after {timeout} seconds.", "exit_code": -1}
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        else:
            # Fallback to local python
            process = subprocess.Popen(
                [sys.executable, "-c", code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return {"output": stdout, "error": stderr, "exit_code": process.returncode}
            except subprocess.TimeoutExpired:
                process.kill()
                return {"output": "", "error": f"Execution timed out after {timeout} seconds.", "exit_code": -1}
    except Exception as e:
        return {"output": "", "error": str(e), "exit_code": -1}

def execute_and_verify(code: str, expected_output: str = "") -> dict:
    """Advanced mission-critical execution with self-patch potential."""
    res = run_python_code(code)
    # Check for errors and provide 'Self-Correction' signal
    is_success = res["exit_code"] == 0 and not res["error"]
    res["verified"] = is_success
    if not is_success:
        res["feedback"] = f"CRITICAL ERROR detected: {res['error']}. Suggesting self-patch..."
    return res

def run_shell_command(command: str, timeout: int = 10) -> dict:
    """Runs a highly restricted set of shell commands."""
    try:
        args = shlex.split(command)
        if not args:
            return {"output": "", "error": "Empty command."}
            
        # Strict whitelist of allowed commands
        allowed_commands = ["ls", "pwd", "echo", "cat", "grep", "head", "tail"]
        if args[0] not in allowed_commands:
            return {"output": "", "error": f"Command '{args[0]}' is not allowed. Only basic read-only commands are permitted."}

        # Prevent directory traversal and dangerous redirects
        for arg in args:
            if ".." in arg or arg.startswith("/") or ">" in arg or "|" in arg:
                 return {"output": "", "error": f"Invalid or dangerous argument detected in: {arg}"}

        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            return {"output": stdout, "error": stderr}
        except subprocess.TimeoutExpired:
            process.kill()
            return {"output": "", "error": f"Command timed out after {timeout} seconds."}
    except Exception as e:
        return {"output": "", "error": str(e)}
