import os
from collections import deque
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from core.config import settings
from resources.vram_monitor import vram_monitor

# Template setup
templates = Jinja2Templates(directory="ui/templates")

router = APIRouter(prefix="/ui")

# In-memory store for recent traces (UI only)
trace_history = deque(maxlen=20)

def add_trace_to_ui(trace_data: dict):
    """Callback to add a new trace to the UI history."""
    trace_history.appendleft(trace_data)

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Renders the main intelligence dashboard."""
    # Build hardware stats
    health = vram_monitor.check_health()
    hardware = {
        "vram_free": health.vram_free,
        "vram_percent": min(100, (health.vram_free / 8000) * 100), # Assume 8GB for visualization
        "ram_free": health.ram_free,
        "ram_percent": min(100, (health.ram_free / 16000) * 100), # Assume 16GB for visualization
        "cpu_temp": health.cpu_temp
    }
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "version": settings.VERSION,
        "default_model": settings.DEFAULT_MODEL,
        "vision_model": settings.VISION_MODEL,
        "available_models": settings.AVAILABLE_MODELS,
        "hardware": hardware,
        "traces": list(trace_history)
    })

@router.get("/refresh", response_class=HTMLResponse)
async def refresh_stats(request: Request):
    """HTMX endpoint for partial dashboard updates."""
    health = vram_monitor.check_health()
    hardware = {
        "vram_free": health.vram_free,
        "vram_percent": min(100, (health.vram_free / 8000) * 100),
        "ram_free": health.ram_free,
        "ram_percent": min(100, (health.ram_free / 16000) * 100),
        "cpu_temp": health.cpu_temp
    }
    
    # Return both hardware and trace components as a combined update
    hw_html = templates.get_template("partials/hardware.html").render({"hardware": hardware})
    tr_html = templates.get_template("partials/traces.html").render({"traces": list(trace_history)})
    
    # Simple HTMX response format
    return HTMLResponse(content=f'<div hx-swap-oob="innerHTML:#hardware-stats">{hw_html}</div><div hx-swap-oob="innerHTML:#trace-history">{tr_html}</div>')

# Singleton-like router setup
ui_router = router
