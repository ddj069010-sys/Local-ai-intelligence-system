from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.execution.executor import run_python_code, run_shell_command

router = APIRouter()

class ExecuteRequest(BaseModel):
    language: str
    code: str
    timeout: int = 10

@router.post("/execute")
async def execute(request: ExecuteRequest):
    if request.language.lower() == "python":
        result = run_python_code(request.code, timeout=request.timeout)
    elif request.language.lower() == "shell":
        result = run_shell_command(request.code, timeout=request.timeout)
    else:
        raise HTTPException(status_code=400, detail="Unsupported language. Use 'python' or 'shell'.")
    
    return result
