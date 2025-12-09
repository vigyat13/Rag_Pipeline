# app/models/query_analytics.py

import uuid
from sqlalchemy import Column, String, DateTime, Float, Integer, Text, func
from sqlalchemy.orm import relationship

from app.core.db import Base


class QueryAnalytics(Base):
    __tablename__ = "query_analytics"

    # store IDs as plain strings (UUID text)
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # also store user_id as string (matching users.id type)
    user_id = Column(String, nullable=False)

    query = Column(String, nullable=False)
    mode = Column(String, nullable=False)

    latency_ms = Column(Float, nullable=False)

    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)

    # store list of document IDs as comma-separated string
    document_ids = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
