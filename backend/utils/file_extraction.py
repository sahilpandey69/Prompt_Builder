"""Extract text from uploaded files. 10MB limit enforced by caller."""
from __future__ import annotations

import io
from typing import BinaryIO


MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


def extract_file_content(raw: bytes, filename: str) -> str:
    """Extract text from file bytes. Raises ValueError if size > 10MB or unsupported type."""
    if len(raw) > MAX_SIZE_BYTES:
        raise ValueError(f"File size exceeds {MAX_SIZE_BYTES // (1024*1024)}MB limit")
    ext = (filename or "").lower().split(".")[-1]
    if ext == "txt":
        return raw.decode("utf-8", errors="replace")
    if ext == "pdf":
        return _extract_pdf(raw)
    if ext == "docx":
        return _extract_docx(raw)
    if ext in ("xlsx", "xls"):
        return _extract_xlsx(raw)
    if ext == "csv":
        return _extract_csv(raw)
    # Fallback: try UTF-8 decode
    return raw.decode("utf-8", errors="replace")


def _extract_pdf(raw: bytes) -> str:
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(raw))
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts).strip()
    except Exception as e:
        return f"[PDF extraction failed: {e}]\n"


def _extract_docx(raw: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(raw))
        return "\n".join(p.text for p in doc.paragraphs).strip()
    except Exception as e:
        return f"[DOCX extraction failed: {e}]\n"


def _extract_xlsx(raw: bytes) -> str:
    try:
        import pandas as pd
        df = pd.read_excel(io.BytesIO(raw), sheet_name=0, header=None)
        return df.to_string(index=False, header=False)
    except Exception as e:
        return f"[XLSX extraction failed: {e}]\n"


def _extract_csv(raw: bytes) -> str:
    try:
        import pandas as pd
        text = raw.decode("utf-8", errors="replace")
        df = pd.read_csv(io.StringIO(text), header=None)
        return df.to_string(index=False, header=False)
    except Exception as e:
        return f"[CSV extraction failed: {e}]\n"
