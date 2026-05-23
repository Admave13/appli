"""
config.py — Configuración global de appli.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Claves de API (solo cover letters con IA)
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY:    str = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY:    str = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY:      str = os.getenv("GROQ_API_KEY", "")

AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini")
AI_MODEL:    str = os.getenv("AI_MODEL", "gemini-2.0-flash")

DB_PATH: str = os.getenv("DB_PATH", "data/jobsearch.db")
DB_URL:  str = f"sqlite:///{DB_PATH}"

DIR_CVS:       str = "data/cvs"
DIR_COVERS:    str = "data/covers"
DIR_LOGOS:     str = "data/logos"
DIR_TEMPLATES: str = "templates"
COVER_TEMPLATE_PATH: str = os.path.join(DIR_TEMPLATES, "cover_default.docx")

MATCH_THRESHOLD: float = float(os.getenv("MATCH_THRESHOLD", "0.3"))


def get_backend():
    """Backend de IA (solo usado para cover letters)."""
    from backend.ai_backend import AIBackend
    return AIBackend()


def ai_configured() -> bool:
    keys = {
        "gemini": GEMINI_API_KEY,
        "groq": GROQ_API_KEY,
        "anthropic": ANTHROPIC_API_KEY,
        "openai": OPENAI_API_KEY,
    }
    return bool(keys.get(AI_PROVIDER, ""))
