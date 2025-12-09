# app/core/config.py

from functools import lru_cache
from typing import List

from pydantic import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "RAG Pipeline"
    API_PREFIX: str = "/api"

    # JWT
    SECRET_KEY: str = "change-me-in-env"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # DB
    DATABASE_URL: str = "sqlite:///./rag_pipeline.db"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
