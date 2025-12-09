# app/routers/documents.py
from __future__ import annotations
import logging
import os
import shutil
import uuid
from datetime import datetime
from typing import Any, Dict, List

import pdfplumber
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.routers.dependencies import get_current_user
from app.schemas.documents import DocumentListResponse, DocumentResponse
from app.services.embeddings import embed_texts
from app.services.faiss_store import add_embeddings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# ------------------------------
# Paths
# ------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_ROOT = os.path.join(BASE_DIR, "..", "data", "uploads")
os.makedirs(UPLOAD_ROOT, exist_ok=True)


def _ensure_upload_dir(user_id: uuid.UUID) -> str:
    path = os.path.join(UPLOAD_ROOT, str(user_id))
    os.makedirs(path, exist_ok=True)
    return path


# ------------------------------
# Text extraction + chunking
# ------------------------------

def _extract_text_from_pdf(path: str) -> str:
    """
    Extract text from a PDF using pdfplumber (no PyMuPDF/fitz dependency).
    """
    parts: List[str] = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    parts.append(text)
    except Exception as e:
        logger.warning("Failed to parse PDF %s with pdfplumber: %s", path, e)
        return ""

    text = "\n\n".join(parts)
    logger.info("PDF text extracted from %s, length=%d chars", path, len(text))
    return text


def _extract_text_generic(path: str) -> str:
    """
    Fallback for txt/md/etc. Very simple. You can extend to DOCX later.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        logger.info("Generic text extracted from %s, length=%d chars", path, len(text))
        return text
    except Exception as e:
        logger.warning("Failed to read %s as text: %s", path, e)
        return ""


def _simple_chunk(text: str, max_chars: int = 1000, overlap: int = 200) -> List[str]:
    text = text.strip()
    if not text:
        return []

    chunks: List[str] = []
    n = len(text)
    start = 0

    while start < n:
        end = min(start + max_chars, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = end - overlap

    return [c.strip() for c in chunks if c.strip()]


# ------------------------------
# Routes
# ------------------------------

@router.post("/upload", response_model=DocumentListResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Upload one or more documents, extract text, chunk, embed, push to FAISS.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided",
        )

    user_id = current_user.id
    user_dir = _ensure_upload_dir(user_id)
    created_docs: List[Dict[str, Any]] = []

    for f in files:
        orig_name = f.filename or "document"
        ext = os.path.splitext(orig_name)[1].lower()
        stored_name = f"{uuid.uuid4()}{ext}"
        stored_path = os.path.join(user_dir, stored_name)

        # Save file
        with open(stored_path, "wb") as buffer:
            shutil.copyfileobj(f.file, buffer)

        size_bytes = os.path.getsize(stored_path)
        content_type = f.content_type or "application/octet-stream"

        # Create Document row
        doc = Document(
            id=uuid.uuid4(),
            user_id=user_id,
            filename=orig_name,
            stored_path=stored_path,
            size_bytes=size_bytes,
            content_type=content_type,
            num_chunks=0,
            is_deleted=False,
            created_at=datetime.utcnow(),
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Extract text
        if ext == ".pdf":
            full_text = _extract_text_from_pdf(stored_path)
        else:
            full_text = _extract_text_generic(stored_path)

        if not full_text.strip():
            logger.warning(
                "No extractable text for document %s (path=%s, ext=%s). "
                "num_chunks will stay 0.",
                doc.id,
                stored_path,
                ext,
            )
            created_docs.append(
                {
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "size_bytes": doc.size_bytes,
                    "content_type": doc.content_type,
                    "created_at": doc.created_at.isoformat(),
                    "num_chunks": doc.num_chunks or 0,
                }
            )
            continue

        # Chunk
        chunks = _simple_chunk(full_text, max_chars=1000, overlap=200)
        logger.info(
            "Document %s chunked into %d chunks (len(text)=%d).",
            doc.id,
            len(chunks),
            len(full_text),
        )

        if not chunks:
            logger.warning("Chunking produced 0 chunks for document %s.", doc.id)
            created_docs.append(
                {
                    "id": str(doc.id),
                    "filename": doc.filename,
                    "size_bytes": doc.size_bytes,
                    "content_type": doc.content_type,
                    "created_at": doc.created_at.isoformat(),
                    "num_chunks": doc.num_chunks or 0,
                }
            )
            continue

        # Insert chunks
        chunk_rows: List[DocumentChunk] = []
        for idx, chunk_text in enumerate(chunks):
            ch = DocumentChunk(
                id=uuid.uuid4(),
                document_id=doc.id,
                user_id=user_id,
                chunk_index=idx,
                text=chunk_text,
                created_at=datetime.utcnow(),
            )
            db.add(ch)
            chunk_rows.append(ch)

        db.commit()
        for ch in chunk_rows:
            db.refresh(ch)

        # Embed + FAISS
        texts_for_embed = [c.text for c in chunk_rows]
        vectors = embed_texts(texts_for_embed)
        metadatas = [
            {
                "chunk_id": str(ch.id),
                "document_id": str(doc.id),
                "filename": doc.filename,
                "text": ch.text,
            }
            for ch in chunk_rows
        ]
        add_embeddings(user_id=str(user_id), vectors=vectors, metadatas=metadatas)

        # Update num_chunks
        doc.num_chunks = len(chunk_rows)
        db.add(doc)
        db.commit()
        db.refresh(doc)

        created_docs.append(
            {
                "id": str(doc.id),
                "filename": doc.filename,
                "size_bytes": doc.size_bytes,
                "content_type": doc.content_type,
                "created_at": doc.created_at.isoformat(),
                "num_chunks": doc.num_chunks or 0,
            }
        )

    return {"documents": created_docs}


@router.get("", response_model=DocumentListResponse)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    docs = (
        db.query(Document)
        .filter(
            Document.user_id == current_user.id,
            Document.is_deleted == False,  # noqa
        )
        .order_by(Document.created_at.desc())
        .all()
    )

    return {
        "documents": [
            {
                "id": str(d.id),
                "filename": d.filename,
                "size_bytes": d.size_bytes,
                "content_type": d.content_type,
                "created_at": d.created_at.isoformat(),
                "num_chunks": d.num_chunks or 0,
            }
            for d in docs
        ]
    }


@router.delete("/{document_id}", response_model=DocumentResponse)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document_id")

    doc = (
        db.query(Document)
        .filter(
            Document.id == doc_uuid,
            Document.user_id == current_user.id,
        )
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.is_deleted = True
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "size_bytes": doc.size_bytes,
        "content_type": doc.content_type,
        "created_at": doc.created_at.isoformat(),
        "num_chunks": doc.num_chunks or 0,
    }
