import os
import psutil
import logging
from typing import Dict, Any, Optional
from core.config import settings
from core.logger import resource_logger

# NVIDIA monitoring dependency
try:
    import pynvml
    _NVML_AVAILABLE = True
except ImportError:
    _NVML_AVAILABLE = False

class SystemHealth:
    """Represents the current hardware health state."""
    def __init__(self, is_safe: bool, free_vram_mb: int, free_ram_mb: int, cpu_temp: float, message: str = ""):
        self.is_safe = is_safe
        self.vram_free = free_vram_mb
        self.ram_free = free_ram_mb
        self.cpu_temp = cpu_temp
        self.message = message

class VRAMMonitor:
    """
    Provides real-time hardware metrics and safety evaluations.
    Specialized for laptop thermal/resource safety.
    """
    
    def __init__(self):
        self.logger = resource_logger
        self._nvml_active = False
        if _NVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self._nvml_active = True
            except Exception as e:
                self.logger.warning(f"⚠️ [MONITOR] NVML init failed: {e}")

    def get_vram_free(self) -> int:
        """Returns free VRAM in MB."""
        if not self._nvml_active:
            return 0
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            return info.free // 1024**2
        except Exception:
            return 0

    def get_ram_free(self) -> int:
        """Returns free system RAM in MB."""
        return psutil.virtual_memory().available // 1024**2

    def get_cpu_temp(self) -> float:
        """Returns CPU temperature in Celsius (if available)."""
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                return 0.0
            # Try to find core or package temp
            for name, entries in temps.items():
                if name in ['coretemp', 'cpu-thermal', 'soc_thermal']:
                    return entries[0].current
            return 0.0
        except Exception:
            return 0.0

    def check_health(self) -> SystemHealth:
        """Evaluates overall system health against thresholds."""
        vram_free = self.get_vram_free()
        ram_free = self.get_ram_free()
        cpu_temp = self.get_cpu_temp()
        
        is_safe = True
        warnings = []
        
        if ram_free < settings.MIN_FREE_RAM_MB:
            is_safe = False
            warnings.append(f"CRITICAL RAM: {ram_free}MB < {settings.MIN_FREE_RAM_MB}MB")

        if cpu_temp > settings.MAX_CPU_TEMP_C:
            is_safe = False
            warnings.append(f"CRITICAL TEMP: {cpu_temp}°C > {settings.MAX_CPU_TEMP_C}°C")
            
        if self._nvml_active and vram_free < settings.MIN_FREE_VRAM_MB:
            warnings.append(f"LOW VRAM: {vram_free}MB < {settings.MIN_FREE_VRAM_MB}MB")

        msg = " | ".join(warnings) if warnings else "System healthy"
        return SystemHealth(is_safe, vram_free, ram_free, cpu_temp, msg)

# Singleton
vram_monitor = VRAMMonitor()
