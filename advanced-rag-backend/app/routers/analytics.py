# app/routers/analytics.py
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.analytics import QueryAnalytics
from app.models.document import Document
from app.routers.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def analytics_overview(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Global platform-level stats.
    """
    total_queries, avg_latency, total_tokens = db.query(
        func.count(QueryAnalytics.id),
        func.avg(QueryAnalytics.latency_ms),
        func.sum(QueryAnalytics.total_tokens),
    ).one()

    # simple document count
    docs_indexed = db.query(func.count(Document.id)).scalar() or 0

    return {
        "total_queries": int(total_queries or 0),
        "unique_documents": int(docs_indexed),
        "avg_latency_ms": float(avg_latency) if avg_latency is not None else None,
        "total_tokens": int(total_tokens or 0),
    }


@router.get("/user")
def user_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Per-user analytics (recent queries, etc.)
    """
    rows: List[QueryAnalytics] = (
        db.query(QueryAnalytics)
        .filter(QueryAnalytics.user_id == current_user.id)
        .order_by(QueryAnalytics.created_at.desc())
        .limit(20)
        .all()
    )

    recent = [
        {
            "id": str(r.id),
            "query": r.query,
            "mode": r.mode,
            "latency_ms": r.latency_ms,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]

    return {
        "recent_queries": recent,
    }
