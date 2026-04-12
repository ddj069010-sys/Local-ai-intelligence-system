import httpx
import os
import subprocess
import logging
import psutil
from typing import Optional, Tuple, List
from core.config import settings, ModelTier
from core.logger import resource_logger

# Optional dependency for NVIDIA monitoring
try:
    import pynvml
    _NVML_AVAILABLE = True
except ImportError:
    _NVML_AVAILABLE = False

class ModelSelector:
    """
    Handles hardware-aware model selection and resource guarding.
    Ensures the system doesn't crash by overloading VRAM/RAM.
    """
    
    def __init__(self):
        self.logger = resource_logger
        self._nvml_active = False
        if _NVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self._nvml_active = True
            except Exception as e:
                self.logger.warning(f"⚠️ [RESOURCES] NVML initialization failed: {e}")

    async def discover_models(self):
        """Fetches all pulled models from Ollama and updates settings (Non-blocking)."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.OLLAMA_API_URL}/tags")
                if response.status_code == 200:
                    models = [m["name"] for m in response.json().get("models", [])]
                    settings.AVAILABLE_MODELS = models
                    self.logger.info(f"🔍 [SELECTOR] Discovered {len(models)} models: {models}")
                else:
                    self.logger.error(f"❌ [SELECTOR] Failed to fetch models from Ollama: {response.status_code}")
        except Exception as e:
            self.logger.error(f"❌ [SELECTOR] Error connecting to Ollama: {e}")

    def get_vram_info(self) -> Tuple[int, int, int]:
        """Returns (used_mb, total_mb, free_mb) for NVIDIA GPUs."""
        if self._nvml_active:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                return info.used // 1024**2, info.total // 1024**2, info.free // 1024**2
            except Exception:
                pass
        
        # Fallback to nvidia-smi parsing
        try:
            res = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=memory.used,memory.total,memory.free", "--format=csv,nounits,noheader"],
                encoding="utf-8"
            )
            used, total, free = map(int, res.strip().split(","))
            return used, total, free
        except Exception:
            return 0, 0, 0

    def get_ram_info(self) -> Tuple[int, int, int]:
        """Returns (used_mb, total_mb, free_mb) for system RAM."""
        vm = psutil.virtual_memory()
        return vm.used // 1024**2, vm.total // 1024**2, vm.available // 1024**2

    def select_best_model(self, requested_tier: ModelTier = ModelTier.MEDIUM, manual_override: Optional[str] = None) -> str:
        """
        Selects the best available model based on remaining resources.
        Downgrades tier if VRAM is insufficient.
        """
        if manual_override:
            self.logger.info(f"🎯 [SELECTOR] Manual override detected: {manual_override}")
            return manual_override

        used_vram, total_vram, free_vram = self.get_vram_info()
        used_ram, total_ram, free_ram = self.get_ram_info()
        
        self.logger.info(f"📊 [RESOURCES] VRAM: {free_vram}MB free | RAM: {free_ram}MB free")

        # 1. Hardware Guard: If we have NO GPU info, fallback to CPU-friendly LOW tier
        if total_vram == 0:
            self.logger.warning("⚠️ [SELECTOR] No GPU detected. Forcing LOW tier (CPU fallback).")
            return settings.TIER_MODELS[ModelTier.LOW]

        # 2. VRAM Guard: Check if requested tier fits
        current_tier = requested_tier
        while current_tier != ModelTier.LOW:
            # Simple heuristic: 14b+ needs ~10GB, 8b needs ~6GB, 4b needs ~3GB
            # Note: In production, these should be in ModelConfig settings
            vram_needed = {
                ModelTier.ULTRA: 20000, # 20GB+
                ModelTier.HIGH: 10000,  # 10GB
                ModelTier.MEDIUM: 6000,  # 6GB
                ModelTier.LOW: 3000      # 3GB
            }.get(current_tier, 4000)

            if free_vram >= vram_needed:
                break
            
            # Downgrade tier
            old_tier = current_tier
            if current_tier == ModelTier.ULTRA: current_tier = ModelTier.HIGH
            elif current_tier == ModelTier.HIGH: current_tier = ModelTier.MEDIUM
            elif current_tier == ModelTier.MEDIUM: current_tier = ModelTier.LOW
            
            self.logger.warning(f"📉 [SELECTOR] Insufficient VRAM for {old_tier}. Downgrading to {current_tier}.")

        final_model = settings.TIER_MODELS.get(current_tier, settings.DEFAULT_MODEL)
        self.logger.info(f"✅ [SELECTOR] Final Selection: {final_model} (Tier: {current_tier})")
        return final_model

    def load_guard(self) -> bool:
        """Returns True if the system is safe to run a heavy AI task."""
        _, _, free_ram = self.get_ram_info()
        if free_ram < settings.MIN_FREE_RAM_MB:
            self.logger.error(f"🛑 [LOAD_GUARD] CRITICAL: Not enough RAM ({free_ram}MB free). Blocking task.")
            return False
        return True

# Singleton instance
model_selector = ModelSelector()
