# app/schemas/chat.py

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict

from pydantic import BaseModel


class AgentMode(str, Enum):
    default = "default"
    research = "research"
    summarizer = "summarizer"
    brainstorm = "brainstorm"


class ChatQueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    selected_document_ids: Optional[List[str]] = None
    agent_mode: Optional[AgentMode] = AgentMode.default


class SourceChunk(BaseModel):
    id: str
    document_id: str
    filename: str
    snippet: str


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    used_agent_mode: AgentMode
    token_usage: TokenUsage
    latency_ms: float
    conversation_id: str
    created_at: datetime
