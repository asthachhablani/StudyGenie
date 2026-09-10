"""
StudyGenie AI — Application Configuration
Loads settings from environment variables via .env
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Flask ──────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    PORT = int(os.environ.get("PORT", 5000))

    # ── SQLite ─────────────────────────────────────────────────────────────
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "studygenie.db")

    # ── File uploads ───────────────────────────────────────────────────────
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 50 * 1024 * 1024))  # 50 MB
    ALLOWED_EXTENSIONS = {"pdf"}

    # ── Groq ───────────────────────────────────────────────────────────────
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama3-8b-8192")

    # ── IBM watsonx.ai ─────────────────────────────────────────────────────
    IBM_WATSONX_URL = os.environ.get("IBM_WATSONX_URL", "")
    IBM_WATSONX_API_KEY = os.environ.get("IBM_WATSONX_API_KEY", "")
    IBM_PROJECT_ID = os.environ.get("IBM_PROJECT_ID", "")
    IBM_MODEL_ID = os.environ.get("IBM_MODEL_ID", "ibm/granite-13b-instruct-v2")

    # ── IBM Orchestrate ────────────────────────────────────────────────────
    IBM_ORCHESTRATE_URL = os.environ.get("IBM_ORCHESTRATE_URL", "")
    IBM_ORCHESTRATE_API_KEY = os.environ.get("IBM_ORCHESTRATE_API_KEY", "")

    # ── Vector store ───────────────────────────────────────────────────────
    VECTOR_STORE_PATH = os.environ.get("VECTOR_STORE_PATH", "vector_store")
    CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 500))
    CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", 50))
    TOP_K_RESULTS = int(os.environ.get("TOP_K_RESULTS", 5))

    # ── Session ────────────────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    @classmethod
    def db_path(cls) -> str:
        """Always read from environment at call time (supports testing with tmp paths)."""
        return os.environ.get("DATABASE_PATH", cls.DATABASE_PATH)

    @classmethod
    def ibm_configured(cls) -> bool:
        return bool(cls.IBM_WATSONX_API_KEY and cls.IBM_PROJECT_ID and cls.IBM_WATSONX_URL)

    @classmethod
    def groq_configured(cls) -> bool:
        return bool(cls.GROQ_API_KEY)

    @classmethod
    def ibm_orchestrate_configured(cls) -> bool:
        return bool(cls.IBM_ORCHESTRATE_URL and cls.IBM_ORCHESTRATE_API_KEY)
