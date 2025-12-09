# app/services/embeddings.py

from functools import lru_cache
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Lazy-load and cache the sentence-transformers model.
    You can change the model name if you want something heavier.
    """
    # Small, fast model – good enough for local RAG
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Embed a list of texts -> shape (n, dim) float32 numpy array.
    Used when indexing document chunks.
    """
    if not texts:
        return np.zeros((0, 384), dtype="float32")  # dim=384 for MiniLM

    model = get_embedding_model()
    vectors = model.encode(
        texts,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=False,
    )
    return vectors.astype("float32")


def embed_query(text: str) -> np.ndarray:
    """
    Embed a single query string -> shape (dim,) float32 numpy array.
    Used at retrieval time.
    """
    if not text:
        # same dim as above, avoid crashes
        return np.zeros((384,), dtype="float32")

    vectors = embed_texts([text])
    # vectors: (1, dim)
    return vectors[0]
