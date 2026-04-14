import os
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.middleware import UnifiedMiddleware
from orchestrator.pipeline_manager import pipeline_manager
from ui.dashboard import ui_router

# Existing Controllers (Backward Compatibility)
from controller import routes, execute_routes, workspace_routes
from controller.link_routes import router as link_router
from controller.voice_routes import router as voice_router
from controller.rag_routes import router as rag_router
from controller.chat_routes import router as chat_router
from controller.intelligence_hq_routes import router as intelligence_hq_router
from controller.doc_routes import router as doc_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade local multimodal AI assistant."
)

@app.on_event("startup")
async def startup_event():
    # 🔍 Initial model discovery (Async)
    from routing.model_selector import model_selector
    
    # Forcefully fix the settings object if it's missing /api
    if not settings.OLLAMA_API_URL.endswith("/api"):
        settings.OLLAMA_API_URL += "/api"
        print(f"DEBUG: Forcefully corrected SETTINGS.OLLAMA_API_URL to: {settings.OLLAMA_API_URL}")
    
    import asyncio
    asyncio.create_task(model_selector.discover_models())

# Unified Logging & Exception Middleware
app.add_middleware(UnifiedMiddleware)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. New Modular Routes
app.include_router(ui_router)

@app.post("/api/v1/chat")
async def chat_endpoint(request: Request):
    """
    Unified entry point for all intelligence tasks.
    Uses the new Modular Pipeline.
    """
    body = await request.json()
    query = body.get("query", "")
    context = body.get("context", {})
    
    result = await pipeline_manager.process_request(query, context)
    return result

@app.post("/api/v1/index/deep")
async def deep_index_endpoint(background_tasks: BackgroundTasks):
    """
    Triggers the Gemini-style Deep Workspace Indexing.
    Scales the intelligence and populates the semantic map.
    """
    from services.universal.indexer import deep_workspace_index
    background_tasks.add_task(deep_workspace_index)
    return {"status": "started", "message": "Deep Workspace Indexing initiated in background."}


# 2. Existing Legacy Routes (Preserved)
app.include_router(routes.router)
app.include_router(execute_routes.router, tags=["execution"])
app.include_router(workspace_routes.router, prefix="/workspace", tags=["workspace"])
app.include_router(link_router)
app.include_router(voice_router)
app.include_router(rag_router)
app.include_router(chat_router)
app.include_router(intelligence_hq_router)
app.include_router(doc_router)

if __name__ == "__main__":
    import uvicorn
    # Use environmental overrides if present
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
