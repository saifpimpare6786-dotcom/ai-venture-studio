import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

from pydantic import Field, AliasChoices

class Settings(BaseSettings):
    """
    Application settings for the FastAPI backend.
    Loads configurations from environment variables or a .env file.
    """
    PROJECT_NAME: str = "AI Venture Studio API"
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str = Field(
        validation_alias=AliasChoices("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SECRET_KEY")
    )
    GROQ_API_KEY: Optional[str] = None
    GROQ_API_KEYS: Optional[str] = None
    NVIDIA_NIM_API_KEY: Optional[str] = None
    NVIDIA_API_KEYS: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_API_KEYS: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    CHROMA_DB_PATH: str = "./chroma_db"
    PORT: int = 8000
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
        description="Comma-separated list of allowed CORS origins"
    )

    def get_groq_keys(self) -> List[str]:
        """Returns list of configured Groq API keys."""
        keys = []
        if self.GROQ_API_KEYS:
            keys.extend([k.strip() for k in self.GROQ_API_KEYS.split(",") if k.strip()])
        if not keys and self.GROQ_API_KEY:
            keys.extend([k.strip() for k in self.GROQ_API_KEY.split(",") if k.strip()])
        return keys

    def get_nvidia_keys(self) -> List[str]:
        """Returns list of configured NVIDIA NIM API keys."""
        keys = []
        if self.NVIDIA_API_KEYS:
            keys.extend([k.strip() for k in self.NVIDIA_API_KEYS.split(",") if k.strip()])
        if not keys and self.NVIDIA_NIM_API_KEY:
            keys.extend([k.strip() for k in self.NVIDIA_NIM_API_KEY.split(",") if k.strip()])
        return keys

    def get_gemini_keys(self) -> List[str]:
        """Returns list of configured Gemini API keys."""
        keys = []
        if self.GEMINI_API_KEYS:
            keys.extend([k.strip() for k in self.GEMINI_API_KEYS.split(",") if k.strip()])
        if not keys and self.GEMINI_API_KEY:
            keys.extend([k.strip() for k in self.GEMINI_API_KEY.split(",") if k.strip()])
        return keys
    
    # Allow reading from a .env file if it exists
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
