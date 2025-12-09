# app/services/analytics.py

from __future__ import annotations

import logging
import uuid
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.analytics import QueryAnalytics

logger = logging.getLogger(__name__)


def record_query_analytics(
    db: Session,
    user_id: str,
    query: str,
    agent_mode: str,
    latency_ms: float,
    token_usage: Dict[str, int],
    document_ids: Optional[List[str]] = None,
) -> None:
    """
    Insert a single query analytics record.

    This MUST NOT crash the main request. Caller wraps in try/except anyway.
    """
    try:
        doc_ids_str = ""
        if document_ids:
            # store as comma-separated string
            doc_ids_str = ",".join(str(d) for d in document_ids)

        qa = QueryAnalytics(
            id=str(uuid.uuid4()),
            user_id=str(user_id),
            query=query,
            mode=str(agent_mode),
            latency_ms=float(latency_ms),
            prompt_tokens=int(token_usage.get("prompt_tokens", 0)),
            completion_tokens=int(token_usage.get("completion_tokens", 0)),
            total_tokens=int(token_usage.get("total_tokens", 0)),
            document_ids=doc_ids_str or None,
        )

        db.add(qa)
        db.commit()
    except Exception as e:
        logger.warning("record_query_analytics failed: %s", e)
        db.rollback()
