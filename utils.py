import json
import os
import re
from typing import Any, List
from config import SUPPORTED_LANGUAGES, ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_MB


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def validate_language(language: str) -> str:
    if not language:
        raise ValueError("Language is required.")
    normalized = language.strip().lower()
    if normalized not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language. Supported: {', '.join(SUPPORTED_LANGUAGES.keys())}")
    return normalized


def validate_file(filename: str, size_bytes: int) -> None:
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Only PDF, DOCX, and TXT files are supported.")

    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise ValueError(f"File too large. Max allowed is {MAX_UPLOAD_SIZE_MB} MB.")


def chunk_text(text: str, chunk_size: int = 9000, overlap: int = 500) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def safe_json_loads(data: str, default: Any) -> Any:
    try:
        return json.loads(data)
    except Exception:
        return default


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def preview_text(text: str, max_len: int = 500) -> str:
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def now_iso() -> str:
    from datetime import datetime
    return datetime.utcnow().isoformat()