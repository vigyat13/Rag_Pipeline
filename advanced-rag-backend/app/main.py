# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.db import Base, engine
from app.routers import auth, documents, chat, analytics

# ✅ import models so SQLAlchemy registers tables
from app.models import user, document, analytics as analytics_model  # noqa: F401

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME)

    # 🔥 THIS IS THE IMPORTANT PART – add all your frontends here
    origins = [
        # local dev
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # vercel frontends
        "https://rag-pipeline-l99j.vercel.app",
        "https://rag-pipeline-lake.vercel.app",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ✅ create DB tables
    Base.metadata.create_all(bind=engine)

    # ✅ all API routes are under /api/...
    app.include_router(auth.router, prefix=settings.API_PREFIX)
    app.include_router(documents.router, prefix=settings.API_PREFIX)
    app.include_router(chat.router, prefix=settings.API_PREFIX)
    app.include_router(analytics.router, prefix=settings.API_PREFIX)

    @app.get("/")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
