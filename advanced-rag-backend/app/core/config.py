# app/core/config.py

import os
from functools import lru_cache
from typing import List

from pydantic import BaseSettings


class Settings(BaseSettings):
    # Basic app meta
    PROJECT_NAME: str = "RAG Pipeline"
    API_PREFIX: str = "/api"

    # CORS – include local + Vercel frontend
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://rag-pipeline-lake.vercel.app",
    ]

    # DB – Render is currently using SQLite file by default
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./rag_pipeline.db",
    )

    # Auth / JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Groq LLM
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # Embeddings
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
