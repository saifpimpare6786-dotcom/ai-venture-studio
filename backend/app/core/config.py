import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings for the FastAPI backend.
    Loads configurations from environment variables or a .env file.
    """
    PROJECT_NAME: str = "AI Venture Studio API"
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    NVIDIA_NIM_API_KEY: str
    GEMINI_API_KEY: str
    CHROMA_DB_PATH: str = "./chroma_db"
    PORT: int = 8000
    
    # Allow reading from a .env file if it exists
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
