# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.db import Base, engine
from app.routers import auth, documents, chat, analytics

# ✅ Import models so SQLAlchemy registers them before create_all
from app.models import user, document  # noqa: F401

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME)

  origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # Vercel frontend
    "https://rag-pipeline-eat7-9p776ht0f-vigyat13s-projects.vercel.app",
]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ✅ Make sure all models (User, Document, DocumentChunk) are imported above
    Base.metadata.create_all(bind=engine)

    # ✅ Routers
    app.include_router(auth.router, prefix=settings.API_PREFIX)
    app.include_router(documents.router, prefix=settings.API_PREFIX)
    app.include_router(chat.router, prefix=settings.API_PREFIX)
    app.include_router(analytics.router, prefix=settings.API_PREFIX)

    return app


app = create_app()


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "advanced-rag-backend",
        "message": "Backend is running.",
    }
