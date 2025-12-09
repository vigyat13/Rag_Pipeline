# app/services/faiss_store.py

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Tuple

import faiss  # pip install faiss-cpu
import numpy as np

logger = logging.getLogger(__name__)

# Base directory for FAISS index files
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
INDEX_DIR = os.path.join(BASE_DIR, "..", "data", "faiss_indexes")
os.makedirs(INDEX_DIR, exist_ok=True)

# In-memory cache to avoid reloading on every call
# key = user_id (str) -> (faiss.Index, List[Dict[str, Any]])
_INDEX_CACHE: Dict[str, Tuple[faiss.Index, List[Dict[str, Any]]]] = {}


def _user_paths(user_id: str) -> Tuple[str, str]:
    """
    Paths for a given user's index + metadata.
    """
    uid = str(user_id)
    index_path = os.path.join(INDEX_DIR, f"{uid}.index")
    meta_path = os.path.join(INDEX_DIR, f"{uid}.meta.json")
    return index_path, meta_path


def _load_user_index(user_id: str, dim: int | None = None) -> Tuple[faiss.Index, List[Dict[str, Any]]]:
    """
    Load (or create) a FAISS index + metadata list for this user.

    If there is no existing index, we create a new IndexFlatL2(dim)
    when dim is provided. If dim is None and no index exists, that's an error
    for callers that want to add vectors.
    """
    uid = str(user_id)
    if uid in _INDEX_CACHE:
        return _INDEX_CACHE[uid]

    index_path, meta_path = _user_paths(uid)

    if os.path.exists(index_path):
        # Existing index: load it
        index = faiss.read_index(index_path)
        logger.info("Loaded FAISS index for user %s from %s", uid, index_path)
    else:
        if dim is None:
            raise ValueError(
                f"No existing index for user {uid} and no dim provided to create one."
            )
        index = faiss.IndexFlatL2(dim)
        logger.info(
            "Created new FAISS index for user %s with dim=%d at %s",
            uid,
            dim,
            index_path,
        )

    # Load metadata
    metadata: List[Dict[str, Any]] = []
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as e:
            logger.warning(
                "Failed to load metadata for user %s from %s: %s",
                uid,
                meta_path,
                e,
            )
            metadata = []

    # If lengths mismatch, truncate to safe size
    if metadata and len(metadata) != index.ntotal:
        n = min(len(metadata), int(index.ntotal))
        metadata = metadata[:n]
        if index.ntotal != n:
            logger.warning(
                "Metadata length and index.ntotal mismatch for user %s; "
                "using first %d entries. (index.ntotal=%d, len(meta)=%d)",
                uid,
                n,
                index.ntotal,
                len(metadata),
            )

    _INDEX_CACHE[uid] = (index, metadata)
    return index, metadata


def _save_user_index(user_id: str, index: faiss.Index, metadata: List[Dict[str, Any]]) -> None:
    """
    Persist index + metadata to disk and update cache.
    """
    uid = str(user_id)
    index_path, meta_path = _user_paths(uid)

    faiss.write_index(index, index_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)

    _INDEX_CACHE[uid] = (index, metadata)
    logger.info(
        "Saved FAISS index for user %s: ntotal=%d, meta_len=%d",
        uid,
        index.ntotal,
        len(metadata),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_embeddings(
    user_id: str,
    vectors: np.ndarray,
    metadatas: List[Dict[str, Any]],
) -> None:
    """
    Add vectors + metadata for a given user.

    Called from documents.upload:
        vectors = embed_texts([...])  -> shape (n, dim)
        metadatas = [{ chunk_id, document_id, filename, text }, ...]
    """
    uid = str(user_id)

    if vectors is None or len(vectors) == 0:
        logger.info("add_embeddings called with empty vectors for user %s; skipping.", uid)
        return

    if len(vectors) != len(metadatas):
        raise ValueError(
            f"add_embeddings: vectors length {len(vectors)} != metadatas length {len(metadatas)}"
        )

    # Ensure float32 numpy array
    vectors = np.asarray(vectors, dtype="float32")
    dim = int(vectors.shape[1])

    # Load or create index
    index, meta = _load_user_index(uid, dim=dim)

    # Add and append metadata
    index.add(vectors)
    meta.extend(metadatas)

    _save_user_index(uid, index, meta)


def search(
    user_id: str,
    query_vec: np.ndarray,
    top_k: int = 8,
    filter_doc_ids: List[str] | None = None,
) -> List[Dict[str, Any]]:
    """
    Search per-user FAISS index.

    Returns a list of metadata dicts, each with at least:
        { "chunk_id": ..., "document_id": ..., "filename": ..., "text": ... }

    filter_doc_ids: if provided, only return hits whose 'document_id' is in that list.
    """
    uid = str(user_id)
    try:
        index, meta = _load_user_index(uid)
    except ValueError:
        # No index yet for this user -> nothing to retrieve
        logger.info("search called for user %s but no index exists yet.", uid)
        return []

    if index.ntotal == 0:
        logger.info("search: index for user %s is empty.", uid)
        return []

    if query_vec is None:
        logger.info("search: query_vec is None for user %s.", uid)
        return []

    # Ensure correct shape (1, dim)
    q = np.asarray(query_vec, dtype="float32")
    if q.ndim == 1:
        q = q.reshape(1, -1)

    k = min(top_k, int(index.ntotal))
    distances, indices = index.search(q, k)  # shapes: (1, k)

    results: List[Dict[str, Any]] = []
    filter_set = set(filter_doc_ids) if filter_doc_ids else None

    for pos in indices[0]:
        if pos < 0:
            continue
        if pos >= len(meta):
            continue

        m = meta[int(pos)]

        # Optional document filtering
        doc_id = m.get("document_id")
        if filter_set is not None and doc_id not in filter_set:
            continue

        results.append(m)

    logger.info(
        "search: user=%s, k=%d, returned=%d (filter_doc_ids=%s)",
        uid,
        k,
        len(results),
        filter_doc_ids,
    )

    return results
