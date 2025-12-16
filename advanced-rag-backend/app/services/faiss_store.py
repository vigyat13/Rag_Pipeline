import os
import pickle
import faiss
import numpy as np
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Directory where FAISS indices are saved
INDICES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data", "indices")
os.makedirs(INDICES_DIR, exist_ok=True)

# Global in-memory cache for indices and metadata
# Format: { user_id_str: { "index": faiss_index, "metadata": [dict, dict, ...] } }
indices: Dict[str, Dict[str, Any]] = {}

def _get_user_index_path(user_id: str) -> str:
    return os.path.join(INDICES_DIR, f"{user_id}.index")

def _get_user_metadata_path(user_id: str) -> str:
    return os.path.join(INDICES_DIR, f"{user_id}.pkl")

def load_user_index(user_id: str):
    """
    Load user's FAISS index and metadata from disk if not already in memory.
    """
    user_id = str(user_id)
    if user_id in indices:
        return indices[user_id]

    index_path = _get_user_index_path(user_id)
    meta_path = _get_user_metadata_path(user_id)

    if os.path.exists(index_path) and os.path.exists(meta_path):
        logger.info(f"Loading existing index for user {user_id}")
        index = faiss.read_index(index_path)
        with open(meta_path, "rb") as f:
            metadata = pickle.load(f)
        indices[user_id] = {"index": index, "metadata": metadata}
    else:
        logger.info(f"Creating new index for user {user_id}")
        # Dimension 384 for standard embeddings (e.g., all-MiniLM-L6-v2)
        # Adjust if using a different model dimension
        dimension = 384  
        index = faiss.IndexFlatL2(dimension)
        indices[user_id] = {"index": index, "metadata": []}
    
    return indices[user_id]

def save_user_index(user_id: str):
    """
    Save user's in-memory index and metadata to disk.
    """
    user_id = str(user_id)
    if user_id not in indices:
        return

    data = indices[user_id]
    index_path = _get_user_index_path(user_id)
    meta_path = _get_user_metadata_path(user_id)

    faiss.write_index(data["index"], index_path)
    with open(meta_path, "wb") as f:
        pickle.dump(data["metadata"], f)
    
    logger.info(f"Saved index for user {user_id}")

def add_embeddings(user_id: str, embeddings: np.ndarray, metadatas: List[Dict[str, Any]]):
    """
    Add embeddings to the user's FAISS index.
    """
    user_data = load_user_index(user_id)
    index = user_data["index"]
    
    # Add vectors to FAISS
    # Ensure embeddings are float32
    if embeddings.dtype != "float32":
        embeddings = embeddings.astype("float32")
        
    index.add(embeddings)
    
    # Append metadata
    user_data["metadata"].extend(metadatas)
    
    # Save to disk
    save_user_index(user_id)

def search_index(user_id: str, query_vector: np.ndarray, top_k: int = 5):
    """
    Search the user's FAISS index for similar vectors.
    """
    user_data = load_user_index(user_id)
    index = user_data["index"]
    metadata = user_data["metadata"]

    if index.ntotal == 0:
        return []

    # Ensure query vector is float32 and correct shape
    if query_vector.dtype != "float32":
        query_vector = query_vector.astype("float32")
    
    # FAISS expects (n_queries, dimension)
    if len(query_vector.shape) == 1:
        query_vector = np.expand_dims(query_vector, axis=0)

    distances, indices_found = index.search(query_vector, top_k)
    
    results = []
    # indices_found[0] contains the IDs of the nearest neighbors
    # distances[0] contains the distances
    for dist, idx in zip(distances[0], indices_found[0]):
        if idx != -1 and idx < len(metadata):
            doc_meta = metadata[idx]
            results.append({
                "score": float(dist),
                "metadata": doc_meta
            })
            
    return results

def clear_user_index(user_id: str):
    """
    Completely wipe the user's FAISS index and metadata from memory and disk.
    Used when deleting documents to prevent 'Ghost Memory'.
    """
    user_id = str(user_id)
    
    # 1. Remove from Memory
    if user_id in indices:
        del indices[user_id]
        logger.info(f"Cleared in-memory index for user {user_id}")

    # 2. Remove from Disk
    index_path = _get_user_index_path(user_id)
    meta_path = _get_user_metadata_path(user_id)

    if os.path.exists(index_path):
        os.remove(index_path)
        logger.info(f"Deleted index file: {index_path}")

    if os.path.exists(meta_path):
        os.remove(meta_path)
        logger.info(f"Deleted metadata file: {meta_path}")
