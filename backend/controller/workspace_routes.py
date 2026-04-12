from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

router = APIRouter()
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspace"))

# Ensure workspace exists
os.makedirs(WORKSPACE_DIR, exist_ok=True)

class FileWriteRequest(BaseModel):
    content: str

def safe_path(filename: str):
    path = os.path.abspath(os.path.join(WORKSPACE_DIR, filename))
    if not path.startswith(WORKSPACE_DIR):
        raise HTTPException(status_code=403, detail="Access denied: Path is outside workspace.")
    return path

@router.get("/files")
async def list_files():
    try:
        files = os.listdir(WORKSPACE_DIR)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{name}")
async def read_file(name: str):
    path = safe_path(name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found.")
    try:
        with open(path, "r") as f:
            return {"name": name, "content": f.read()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/files/{name}")
async def write_file(name: str, request: FileWriteRequest):
    path = safe_path(name)
    try:
        with open(path, "w") as f:
            f.write(request.content)
        return {"status": "success", "message": f"File '{name}' written."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
