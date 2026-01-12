"""Configuration for Customer Service Agent."""
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Models (you can change these without touching code)
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
STT_MODEL = os.getenv("STT_MODEL", "gpt-4o-mini-transcribe")
TTS_MODEL = os.getenv("TTS_MODEL", "gpt-4o-mini-tts")  # if your account supports; else change to a supported TTS model

# Storage
DB_PATH = os.getenv("DB_PATH", "data/app.db")

# Caching
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))  # 5 min
CACHE_MAXSIZE = int(os.getenv("CACHE_MAXSIZE", "2048"))

# Rate limiting (per session)
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "20"))  # requests per minute

def validate_config() -> None:
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not set. Add it to Streamlit secrets or a local .env file."
        )
