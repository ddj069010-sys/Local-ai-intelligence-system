"""
chunker.py — Text chunking with overlap and metadata preservation.
Chunk size: 400 words, overlap: ~12% (48 words), keeps source/page metadata.
"""

import re
import logging

logger = logging.getLogger(__name__)

CHUNK_WORDS = 400
OVERLAP_WORDS = 48  # ~12% of 400


def chunk_pages(pages: list[dict]) -> list[dict]:
    """
    Takes a list of page dicts ({text, source, page}) and
    returns a flat list of chunk dicts.
    """
    all_chunks = []
    for page in pages:
        chunks = _chunk_text(
            text=page["text"],
            source=page["source"],
            page=page["page"]
        )
        all_chunks.extend(chunks)
    return all_chunks


def _chunk_text(text: str, source: str, page: int) -> list[dict]:
    """Split a single text into overlapping word-based chunks."""
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()

    if not words:
        return []

    chunks = []
    start = 0
    chunk_idx = 0

    while start < len(words):
        end = min(start + CHUNK_WORDS, len(words))
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)

        if len(chunk_words) >= 20:  # Skip tiny chunks (< 20 words)
            chunks.append({
                "text": chunk_text,
                "source": source,
                "page": page,
                "chunk_id": f"{source}__p{page}__c{chunk_idx}",
                "word_count": len(chunk_words)
            })
            chunk_idx += 1

        if end == len(words):
            break

        # Slide forward with overlap
        start = end - OVERLAP_WORDS

    return chunks
