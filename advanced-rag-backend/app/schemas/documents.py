# app/schemas/documents.py

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class DocumentBase(BaseModel):
    id: str
    filename: str
    size_bytes: int
    content_type: str
    created_at: str
    num_chunks: Optional[int] = 0

    class Config:
        # Pydantic v2
        from_attributes = True


class DocumentResponse(DocumentBase):
    """
    Single document response (used for DELETE, etc.).
    """
    pass


class DocumentListResponse(BaseModel):
    """
    Response wrapper for list/upload endpoints:
    {
      "documents": [DocumentBase, ...]
    }
    """
    documents: List[DocumentBase]
