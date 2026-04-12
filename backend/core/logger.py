import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from core.config import settings

# Custom level for TRACE logs (below DEBUG)
TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")

def trace(self, message, *args, **kws):
    if self.isEnabledFor(TRACE_LEVEL):
        self._log(TRACE_LEVEL, message, args, **kws)

logging.Logger.trace = trace

# ANSI Color Codes for Terminal
class Colors:
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"

class CustomFormatter(logging.Formatter):
    """Custom formatter for color-coded terminal output."""
    
    format_str = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"

    FORMATS = {
        logging.DEBUG: Colors.CYAN + format_str + Colors.END,
        logging.INFO: Colors.BLUE + format_str + Colors.END,
        logging.WARNING: Colors.YELLOW + format_str + Colors.END,
        logging.ERROR: Colors.RED + format_str + Colors.END,
        logging.CRITICAL: Colors.BOLD + Colors.RED + format_str + Colors.END,
        TRACE_LEVEL: Colors.GREEN + format_str + Colors.END,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def setup_logger(name: str = "antigravity") -> logging.Logger:
    """Configures and returns a logger instance."""
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if already configured
    if logger.hasHandlers():
        return logger

    # Set base level
    logger.setLevel(logging.DEBUG if settings.DEMO_MODE else logging.INFO)

    # 1. Console Handler (Color)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    logger.addHandler(console_handler)

    # 2. File Handler (Persistent)
    log_file = settings.LOG_DIR / f"{name}.log"
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding="utf-8"
    )
    file_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    return logger

# Global default logger
logger = setup_logger()
system_logger = setup_logger("system")
resource_logger = setup_logger("resource")
pipeline_logger = setup_logger("pipeline")
