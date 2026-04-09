import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./legal_backend.db").strip()
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))

SUPPORTED_LANGUAGES = {
    "english": "English",
    "kannada": "Kannada",
    "tamil": "Tamil",
    "hindi": "Hindi",
    "malayalam": "Malayalam",
}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

UPLOAD_DIR = "uploads"