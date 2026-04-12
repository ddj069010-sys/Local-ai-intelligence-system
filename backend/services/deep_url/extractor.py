from bs4 import BeautifulSoup
import logging
from typing import Dict, Any, List
import re

logger = logging.getLogger(__name__)

class Extractor:
    def extract(self, html: str, url: str) -> Dict[str, Any]:
        """Extract main content and metadata from HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove noise
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                tag.decompose()

            # Metadata
            title = soup.title.string.strip() if soup.title else "No Title"
            meta_desc = ""
            desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
            if desc_tag:
                meta_desc = desc_tag.get("content", "").strip()

            # Content
            content_blocks = []
            
            # Headings
            headings = []
            for h in soup.find_all(["h1", "h2", "h3"]):
                text = h.get_text().strip()
                if text:
                    headings.append(text)
            
            # Main Paragraphs
            paragraphs = []
            for p in soup.find_all("p"):
                text = p.get_text().strip()
                if len(text) > 30: # Filter short snippets
                    paragraphs.append(text)
            
            # Tables (Basic extraction)
            tables = []
            for table in soup.find_all("table"):
                table_text = table.get_text(separator=" | ").strip()
                if table_text:
                    tables.append(table_text)

            return {
                "url": url,
                "title": title,
                "description": meta_desc,
                "headings": headings,
                "paragraphs": paragraphs,
                "tables": tables,
                "full_text": "\n\n".join([title] + headings + paragraphs)
            }
        except Exception as e:
            logger.error(f"Extraction failed for {url}: {e}")
            return {"url": url, "error": str(e), "full_text": ""}

    def get_links(self, html: str, base_domain: str) -> List[str]:
        """Extract internal links from the same domain."""
        links = set()
        try:
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                # Filter internal links
                if href.startswith("/") or base_domain in href:
                    if not any(ext in href.lower() for ext in [".pdf", ".jpg", ".png", ".zip", ".exe"]):
                        # Normalize a bit (strip fragment)
                        full_url = href.split("#")[0]
                        if full_url and full_url != "/":
                            links.add(full_url)
        except Exception as e:
            logger.warning(f"Link extraction error: {e}")
        
        return list(links)
