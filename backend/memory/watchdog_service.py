import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

class AOTIndexHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        # In a full FAISS implementation, we'd initialize the dense vector store here.
        # Self-indexing pool queue
        self.pending_files = set()

    def _trigger_index(self, event_type, path):
        if path.endswith(('.py', '.js', '.ts', '.md', '.txt')):
            logger.info(f"AOT Watchdog [{event_type}]: Quietly indexing {path} into local vector pool.")
            self.pending_files.add(path)
            # Future integration: push to vector DB

    def on_created(self, event):
        if not event.is_directory:
            self._trigger_index("CREATE", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._trigger_index("MODIFY", event.src_path)

def start_memory_watchdog(directory_to_watch: str):
    logger.info(f"Starting AOT Memory Watchdog on {directory_to_watch}")
    event_handler = AOTIndexHandler()
    observer = Observer()
    observer.schedule(event_handler, path=directory_to_watch, recursive=True)
    observer.start()
    return observer
