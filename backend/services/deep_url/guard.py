import logging
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
import hashlib

logger = logging.getLogger(__name__)

class Guard:
    def __init__(self, max_pages_per_domain: int = 15, max_chars: int = 100000):
        self.max_pages = max_pages_per_domain
        self.max_chars = max_chars
        self.visited_urls = set()
        self.content_hashes = set()
        self.robots_cache = {}

    def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched based on robots.txt and limits."""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        # 1. Total page limit per crawl
        if len(self.visited_urls) >= self.max_pages:
            return False
        
        # 2. Visited check
        if url in self.visited_urls:
            return False
            
        # 3. Robots.txt (Lazy load)
        if domain not in self.robots_cache:
            rp = RobotFileParser()
            rp.set_url(f"{domain}/robots.txt")
            try:
                rp.read()
                self.robots_cache[domain] = rp
            except:
                self.robots_cache[domain] = None # Treat as allow if fail
        
        rp = self.robots_cache[domain]
        if rp and not rp.can_fetch("*", url):
            logger.info(f"Robots.txt restricted: {url}")
            return False
            
        return True

    def is_duplicate(self, content: str) -> bool:
        """Check for content duplication using MD5 hash."""
        c_hash = hashlib.md5(content.encode()).hexdigest()
        if c_hash in self.content_hashes:
            return True
        self.content_hashes.add(c_hash)
        return False

    def mark_visited(self, url: str):
        self.visited_urls.add(url)
