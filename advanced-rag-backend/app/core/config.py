# app/core/config.py

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import AnyUrl


class Settings(BaseSettings):
    # --- Basic app info ---
    PROJECT_NAME: str = "RAG Pipeline"
    API_PREFIX: str = "/api"

    # --- Database ---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./app.db",   # default for local / Render free tier
    )

    # --- Auth / JWT ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-prod")  # override in Render env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- LLM / Groq ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # --- Embeddings ---
    EMBEDDING_MODEL_NAME: str = os.getenv(
        "EMBEDDING_MODEL_NAME",
        "sentence-transformers/all-MiniLM-L6-v2",
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
