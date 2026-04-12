import time
import uuid
import logging
from typing import Dict, Optional, Any
from core.config import settings
from core.logger import pipeline_logger

class TraceStage:
    """Represents a single stage in the pipeline with timing info."""
    def __init__(self, name: str):
        self.name: str = name
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.duration: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def start(self):
        self.start_time = time.perf_counter()

    def finish(self):
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time

class PipelineTrace:
    """Context manager for tracing the entire request pipeline."""
    
    def __init__(self, request_id: Optional[str] = None):
        self.request_id: str = request_id or str(uuid.uuid4())[:8]
        self.stages: Dict[str, TraceStage] = {}
        self.start_time: float = time.perf_counter()
        self.total_time: float = 0.0

    def __enter__(self):
        pipeline_logger.info(f"🚀 [TRACE] Starting Pipeline Trace | ID: {self.request_id}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.total_time = time.perf_counter() - self.start_time
        self.log_summary()

    def start_stage(self, name: str):
        """Starts a new named stage."""
        stage = TraceStage(name)
        stage.start()
        self.stages[name] = stage
        if settings.DEMO_MODE:
            pipeline_logger.debug(f"  🔹 [STAGE] {name} starting...")

    def finish_stage(self, name: str, **metadata):
        """Finishes a named stage and adds metadata."""
        if name in self.stages:
            stage = self.stages[name]
            stage.finish()
            stage.metadata.update(metadata)
            if settings.DEMO_MODE:
                pipeline_logger.info(f"  ✅ [STAGE] {name} | {stage.duration:.2f}s | {metadata}")
        else:
            pipeline_logger.warning(f"⚠️ [TRACE] Attempted to finish unknown stage: {name}")

    def log_summary(self):
        """Logs a summary of all stages and total time."""
        pipeline_logger.info(f"🏁 [TRACE] Pipeline Summary | ID: {self.request_id}")
        for name, stage in self.stages.items():
            pipeline_logger.info(f"  ├─ {name:15}: {stage.duration:6.2f}s")
        pipeline_logger.info(f"  └─ TOTAL TIME    : {self.total_time:6.2f}s")

def get_trace(request_id: Optional[str] = None) -> PipelineTrace:
    """Helper to create a new trace."""
    return PipelineTrace(request_id)
