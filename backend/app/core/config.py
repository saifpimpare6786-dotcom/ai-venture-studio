import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Venture Studio Backend"
    VERSION: str = "2.2.0"
    DEBUG: bool = True
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    # Default LLM Provider: 'ollama' or 'cloud'
    DEFAULT_LLM_PROVIDER: str = "ollama"
    PREFER_LOCAL_OLLAMA: bool = True

    # Local Ollama Settings (Default: gemma4:12b)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma4:12b"

    # Cloud Provider API Key Rotation Pools
    GROQ_API_KEYS: str = ""
    NVIDIA_NIM_API_KEYS: str = ""
    GEMINI_API_KEYS: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    NVIDIA_MODEL: str = "meta/llama-3.2-11b-vision-instruct"
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    # Live Web Search
    TAVILY_API_KEY: str = ""

    # Supabase (Optional)
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Local Storage Paths
    CHROMA_DB_PATH: str = "./data/chroma_db"
    SQLITE_DB_PATH: str = "./data/venture_studio.db"
    UPLOAD_DIR: str = "./data/uploads"
    KNOWLEDGE_BASE_PATH: str = "./knowledge_base"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def groq_key_list(self) -> List[str]:
        return [k.strip() for k in self.GROQ_API_KEYS.split(",") if k.strip()]

    @property
    def nvidia_key_list(self) -> List[str]:
        return [k.strip() for k in self.NVIDIA_NIM_API_KEYS.split(",") if k.strip()]

    @property
    def gemini_key_list(self) -> List[str]:
        return [k.strip() for k in self.GEMINI_API_KEYS.split(",") if k.strip()]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.SQLITE_DB_PATH) or "./data", exist_ok=True)
os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
