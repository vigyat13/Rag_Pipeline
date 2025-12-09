# app/core/config.py

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    # Basic metadata
    PROJECT_NAME: str = "Advanced RAG Backend"
    API_PREFIX: str = "/api"

    # Auth / security
    SECRET_KEY: str = "CHANGE_ME_IN_ENV"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # --- DATABASE CONFIG ---
    # Your existing code (core/db.py) uses `settings.DATABASE_URL`
    # Render / future code might use SQLALCHEMY_DATABASE_URL.
    # So we expose BOTH, same default.
    DATABASE_URL: str = "sqlite:///./app.db"
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./app.db"

    # LLM / Groq
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # Embeddings
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
