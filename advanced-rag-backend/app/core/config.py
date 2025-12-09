from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Advanced RAG Backend"
    API_PREFIX: str = "/api"

    # DB – use Supabase Postgres connection string
    DATABASE_URL: str

    # Auth / JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Groq
    GROQ_API_KEY: str
    GROQ_MODEL_NAME: str = "llama-3.1-70b-versatile"

    # Paths
    UPLOAD_DIR: str = "./data/uploads"
    FAISS_DIR: str = "./data/faiss_indexes"

    # CORS
    FRONTEND_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
