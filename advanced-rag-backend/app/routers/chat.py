# app/routers/chat.py

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db          # ✅ matches your main.py (Base, engine)
from app.models.user import User
from app.routers.dependencies import get_current_user
from app.schemas.chat import ChatQueryRequest, ChatResponse, AgentMode
from app.services.rag_pipeline import run_rag_query

# ✅ Define router BEFORE using @router.post
router = APIRouter(prefix="/chat", tags=["Chat"])  # final path: /api/chat/... because main.py adds /api


@router.post("/query", response_model=ChatResponse)
def chat_query(
    body: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Main RAG chat endpoint.

    Request body (ChatQueryRequest) matches your contract:
      {
        "query": string,
        "conversation_id"?: string,
        "selected_document_ids"?: string[],
        "agent_mode"?: "default" | "research" | "summarizer" | "brainstorm"
      }
    """
    # Normalize agent_mode: fall back to default if missing/null
    requested_mode = body.agent_mode or AgentMode.default

    answer, sources, token_usage, latency_ms = run_rag_query(
        db=db,
        user_id=str(current_user.id),
        query=body.query,
        agent_mode=requested_mode,
        selected_document_ids=body.selected_document_ids,
    )

    return ChatResponse(
        answer=answer,
        sources=sources,
        used_agent_mode=requested_mode,
        token_usage=token_usage,
        latency_ms=latency_ms,
        conversation_id=body.conversation_id or "",
        created_at=datetime.utcnow(),
    )
