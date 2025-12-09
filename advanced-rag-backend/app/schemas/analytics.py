from pydantic import BaseModel, EmailStr
from typing import List
from datetime import datetime


class TopDocumentItem(BaseModel):
    document_id: str
    filename: str
    query_count: int


class TopQueryItem(BaseModel):
    query: str
    count: int


class DailyStatsItem(BaseModel):
    date: str  # YYYY-MM-DD
    query_count: int
    avg_latency_ms: float


class AnalyticsOverviewResponse(BaseModel):
    total_users: int
    total_documents: int
    total_queries: int
    avg_response_time_ms: float
    top_documents: List[TopDocumentItem]
    top_queries: List[TopQueryItem]
    last_7d: List[DailyStatsItem]


class AnalyticsUserResponse(BaseModel):
    user_id: str
    email: EmailStr
    total_queries: int
    total_documents: int
    avg_response_time_ms: float
    last_activity_at: datetime | None
