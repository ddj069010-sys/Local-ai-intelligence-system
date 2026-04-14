import time
import uuid
import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime

logger = logging.getLogger("backend_middleware")

class UnifiedMiddleware(BaseHTTPMiddleware):
    """
    Robust middleware for:
    1. Tracking execution time of every endpoint.
    2. Catching and logging unhandled exceptions.
    3. Returning professional JSON responses for crashes.
    """
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Add request_id to scope for logging/tracing consistency
        request.state.request_id = request_id
        
        try:
            # ⏱️ Start Profiling
            response = await call_next(request)
            
            # 📊 Log Execution Time
            process_time = (time.time() - start_time) * 1000  # ms
            logger.info(
                f"ID: {request_id} | {request.method} {request.url.path} | "
                f"Status: {response.status_code} | Latency: {process_time:.2f}ms"
            )
            
            # Inject process time and request ID into headers for transparency
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
            response.headers["X-Request-ID"] = request_id
            
            return response

        except Exception as e:
            # 🚨 Global Exception Handler
            error_id = f"ERR-{request_id[:8].upper()}-{int(time.time())}"
            process_time = (time.time() - start_time) * 1000
            
            logger.error(
                f"CRASH [ID: {error_id}] | {request.method} {request.url.path} | "
                f"Error: {str(e)}", exc_info=True
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error_id": error_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "status": "error",
                    "code": 500,
                    "message": "An unhandled internal server error occurred.",
                    "details": f"Check system logs with Error ID: {error_id}",
                    "path": request.url.path
                }
            )
