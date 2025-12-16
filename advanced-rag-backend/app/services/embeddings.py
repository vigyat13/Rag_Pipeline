from functools import lru_cache
from typing import List

import numpy as np
from fastembed import TextEmbedding

@lru_cache(maxsize=1)
def get_embedding_model() -> TextEmbedding:
    """
    Lazy-load and cache the FastEmbed model.
    This replaces SentenceTransformer. It does not need PyTorch.
    It downloads a small, optimized version of the model (~200MB) automatically.
    """
    # This model name matches the performance of "all-MiniLM-L6-v2"
    return TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Embed a list of texts -> shape (n, dim) float32 numpy array.
    Used when indexing document chunks.
    """
    if not texts:
        # 384 is the dimension for all-MiniLM-L6-v2
        return np.zeros((0, 384), dtype="float32")

    model = get_embedding_model()
    
    # model.embed(texts) returns a Python generator. 
    # We convert it to a list, then to a numpy array.
    vectors = list(model.embed(texts))
    
    return np.array(vectors, dtype="float32")


def embed_query(text: str) -> np.ndarray:
    """
    Embed a single query string -> shape (dim,) float32 numpy array.
    Used at retrieval time.
    """
    if not text:
        return np.zeros((384,), dtype="float32")

    # Reuse the function above
    vectors = embed_texts([text])
    
    # Return the first (and only) vector, flattened
    return vectors[0]
