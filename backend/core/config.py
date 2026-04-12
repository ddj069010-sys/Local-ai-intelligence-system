import os
from dotenv import load_dotenv
from enum import Enum
from pathlib import Path

# Load .env explicitly
load_dotenv()
from typing import Dict, List, Optional, Union
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Root directory of the project
ROOT_DIR = Path(__file__).resolve().parent.parent

class ModelTier(str, Enum):
    ULTRA = "ultra"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ModelConfig(BaseSettings):
    """Configuration for a specific AI model."""
    name: str
    tier: ModelTier
    context_length: int = 4096
    vram_requirement_gb: float
    description: str

class Settings(BaseSettings):
    """Global system settings."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # API Configuration
    PROJECT_NAME: str = "Antigravity Agent"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(default="development-secret-key-change-me")
    
    # Ollama Backend
    OLLAMA_API_URL: str = Field(default="http://127.0.0.1:11434/api")
    DEFAULT_MODEL: str = Field(default="gemma3:4b")
    EMBEDDING_MODEL: str = Field(default="nomic-embed-text:latest")
    VISION_MODEL: str = Field(default="llava")

    # Model Tiers (Standard Recommendations)
    TIER_MODELS: Dict[ModelTier, str] = {
        ModelTier.ULTRA: "qwen3:14b",
        ModelTier.HIGH: "gemma3:12b",
        ModelTier.MEDIUM: "dolphin3:8b",
        ModelTier.LOW: "gemma3:4b"
    }
    
    # Specialized GPT-Lifestyle Roles
    WORKER_MODEL: str = "dolphin3:8b"     # Efficient retrieval/extraction
    ARCHITECT_MODEL: str = "qwen3:14b"    # High-accuracy verification/synthesis
    VERIFICATION_ENABLED: bool = True
    
    # Store all discovered models here
    AVAILABLE_MODELS: List[str] = []

    # Resource Thresholds
    MIN_FREE_VRAM_MB: int = Field(default=1024)  # 1GB
    MIN_FREE_RAM_MB: int = Field(default=2048)   # 2GB

    MAX_CPU_TEMP_C: int = Field(default=85)
    
    # Paths
    LOG_DIR: Path = ROOT_DIR / "logs"
    UPLOAD_DIR: Path = ROOT_DIR / "uploads"
    MEMORY_DIR: Path = ROOT_DIR / "memory_store"
    FAISS_INDEX_PATH: Path = MEMORY_DIR / "faiss_index.bin"
    METADATA_PATH: Path = MEMORY_DIR / "metadata.json"

    # Tracing & Observability
    ENABLE_TRACING: bool = Field(default=True)
    DEMO_MODE: bool = Field(default=False)
    
    # Search & Crawling
    MAX_SEARCH_RESULTS: int = 5
    CRAWL_DEPTH: int = 1
    REQUEST_TIMEOUT: int = 30

    def get_dynamic_context_length(self, complexity: ModelTier) -> int:
        """--- BEYOND-GPT: DYNAMIC WINDOW SIZING ---"""
        base_length = 4096
        if complexity == ModelTier.ULTRA:
            return 32768  # 32k for ultra high complexity
        if complexity == ModelTier.HIGH:
            return 16384  # 16k for deep research
        return base_length


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.MEMORY_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
