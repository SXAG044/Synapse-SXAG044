import os
import uuid
import pdfplumber
from docx import Document as DocxDocument
from fastapi import UploadFile
from config import UPLOAD_DIR
from utils import ensure_dir, validate_file, clean_text


def save_upload_file(upload_file: UploadFile) -> str:
    ensure_dir(UPLOAD_DIR)
    unique_name = f"{uuid.uuid4().hex}_{upload_file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    content = upload_file.file.read()
    validate_file(upload_file.filename, len(content))

    with open(file_path, "wb") as f:
        f.write(content)

    upload_file.file.seek(0)
    return file_path


def extract_text_from_file(file_path: str) -> str:
    lower = file_path.lower()

    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_path)

    if lower.endswith(".docx"):
        return extract_text_from_docx(file_path)

    if lower.endswith(".txt"):
        return extract_text_from_txt(file_path)

    raise ValueError("Unsupported file type.")


def extract_text_from_pdf(file_path: str) -> str:
    texts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            texts.append(page_text)
    combined = "\n".join(texts)
    combined = clean_text(combined)
    if not combined.strip():
        raise ValueError(
            "No readable text found in PDF. This compact MVP supports text-based PDFs, not scanned-image PDFs."
        )
    return combined


def extract_text_from_docx(file_path: str) -> str:
    doc = DocxDocument(file_path)
    texts = [p.text for p in doc.paragraphs if p.text.strip()]
    combined = "\n".join(texts)
    return clean_text(combined)


def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return clean_text(f.read())