"""Configuration management for Scribo."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "courses"
TEMP_DIR = BASE_DIR / "temp"

# Ensure essential runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)


class Settings:
    """Application settings and defaults."""

    def __init__(self):
        # API Keys
        self.GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        self.GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

        # Model & Provider Defaults
        self.DEFAULT_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        self.DEFAULT_STT_PROVIDER: str = os.getenv("STT_PROVIDER", "gemini")  # "gemini", "groq", "openai"

        # Audio Compression Defaults
        self.AUDIO_BITRATE: str = os.getenv("AUDIO_BITRATE", "48k")
        self.AUDIO_SAMPLE_RATE: int = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
        self.AUDIO_CHANNELS: int = int(os.getenv("AUDIO_CHANNELS", "1"))

        # Storage Paths
        self.COURSES_DATA_DIR: Path = DATA_DIR
        self.TEMP_STORAGE_DIR: Path = TEMP_DIR

    def validate_gemini_key(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self.GEMINI_API_KEY and not self.GEMINI_API_KEY.startswith("your_"))

    def validate_groq_key(self) -> bool:
        """Check if Groq API key is configured."""
        return bool(self.GROQ_API_KEY and not self.GROQ_API_KEY.startswith("your_"))

    def validate_openai_key(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.OPENAI_API_KEY and not self.OPENAI_API_KEY.startswith("your_"))

    def get_available_stt_providers(self) -> list[str]:
        """List providers with valid API keys."""
        providers = []
        if self.validate_gemini_key():
            providers.append("gemini")
        if self.validate_groq_key():
            providers.append("groq")
        if self.validate_openai_key():
            providers.append("openai")
        return providers


settings = Settings()
