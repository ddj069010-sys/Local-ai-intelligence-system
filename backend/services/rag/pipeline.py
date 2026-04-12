"""
pipeline.py — RAG orchestrator.
Handles:
  - ingest_file(path) → chunk → embed → store
  - query(text) → retrieve → rerank → build_context
  - build_rag_prompt(query, chunks) → formatted prompt with citations
"""

import os
import asyncio
import logging
from .loader import load_document
from .chunker import chunk_pages
from .embedder import embed_batch
from .store import get_store
from .retriever import retrieve
from .reranker import rerank

logger = logging.getLogger(__name__)


async def ingest_file(file_path: str) -> dict:
    """
    Full ingestion pipeline for a single file.
    Returns status dict with chunk count.
    """
    filename = os.path.basename(file_path)
    logger.info(f"[RAG Pipeline] Ingesting: {filename}")

    # Step 1: Load pages (Synchronous file IO, but in thread pool)
    loop = asyncio.get_event_loop()
    pages = await loop.run_in_executor(None, load_document, file_path)
    if not pages:
        return {"status": "error", "message": "Could not extract text from file.", "file": filename}

    # Step 2: Chunk
    chunks = chunk_pages(pages)
    if not chunks:
        return {"status": "error", "message": "No usable chunks produced.", "file": filename}

    # Step 3: Embed
    texts = [c["text"] for c in chunks]
    embeddings = await embed_batch(texts)
    if not embeddings or len(embeddings) != len(chunks):
        return {"status": "error", "message": "Embedding failed.", "file": filename}

    # Step 4: Store
    store = get_store()
    store.load()  # Load existing index first
    store.add_chunks(chunks, embeddings)

    logger.info(f"[RAG Pipeline] Ingested {len(chunks)} chunks from '{filename}'.")
    return {
        "status": "ok",
        "file": filename,
        "chunks": len(chunks),
        "pages": len(pages)
    }


async def async_ingest_file(file_path: str) -> dict:
    """Retained for compatibility, now just calls async version directly."""
    return await ingest_file(file_path)


async def query_rag(question: str, top_k: int = 5) -> list[dict]:
    """Retrieve and rerank chunks for a query."""
    chunks = await retrieve(question, top_k=top_k)
    if not chunks:
        return []
    # Reranking is CPU intensive, but short.
    return rerank(question, chunks)


def build_rag_prompt(question: str, chunks: list[dict]) -> str:
    """
    Build a structured RAG prompt with context and citation instructions.
    """
    if not chunks:
        return question

    context_lines = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source", "Unknown")
        page = chunk.get("page", "?")
        text = chunk["text"]
        context_lines.append(f"[Source {i}: {source}, Page {page}]\n{text}\n")

    context_block = "\n---\n".join(context_lines)

    prompt = f"""You are a precise document analyst. Answer the question using ONLY the provided context below.

CONTEXT:
{context_block}

QUESTION:
{question}

INSTRUCTIONS:
- Answer factually using ONLY the above context.
- Structure your response as:

## Answer

### Summary
[Concise 2-3 sentence answer]

### From Documents
[Key extracted points as bullet list]

### Sources
[List each source file and page number used]

- If the context does NOT contain relevant information, say: "The provided documents do not contain enough information to answer this question."
- Do NOT hallucinate or use outside knowledge.
- Always cite sources in the format: filename (Page X)."""

    return prompt


def get_indexed_files() -> list[str]:
    """Return list of all indexed filenames."""
    store = get_store()
    store.load()
    return store.list_files()


async def delete_indexed_file(filename: str) -> bool:
    """Remove a file from the index."""
    store = get_store()
    store.load()
    return await store.delete_file(filename)
