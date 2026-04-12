"""
loader.py — Document text extraction.
Supports PDF (pdfplumber), DOCX (python-docx), TXT.
Returns list of {text, source, page} dicts.
"""

import os
import logging

logger = logging.getLogger(__name__)


def load_document(file_path: str) -> list[dict]:
    """
    Extract text from a document file.
    Returns a list of page dicts: [{text, source, page}]
    """
    ext = os.path.splitext(file_path)[-1].lower()
    filename = os.path.basename(file_path)

    if ext == ".pdf":
        return _load_pdf(file_path, filename)
    elif ext in (".docx", ".doc"):
        return _load_docx(file_path, filename)
    elif ext == ".txt":
        return _load_txt(file_path, filename)
    else:
        logger.warning(f"Unsupported file type: {ext}")
        return []


def _load_pdf(path: str, source: str) -> list[dict]:
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append({"text": text, "source": source, "page": i + 1})
        return pages
    except ImportError:
        logger.error("pdfplumber not installed. Run: pip install pdfplumber")
        return []
    except Exception as e:
        logger.error(f"PDF load error for {path}: {e}")
        return []


def _load_docx(path: str, source: str) -> list[dict]:
    try:
        from docx import Document
        doc = Document(path)
        full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return [{"text": full_text, "source": source, "page": 1}]
    except ImportError:
        logger.error("python-docx not installed. Run: pip install python-docx")
        return []
    except Exception as e:
        logger.error(f"DOCX load error for {path}: {e}")
        return []


def _load_txt(path: str, source: str) -> list[dict]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        return [{"text": text, "source": source, "page": 1}]
    except Exception as e:
        logger.error(f"TXT load error for {path}: {e}")
        return []
