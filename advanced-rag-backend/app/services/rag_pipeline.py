from __future__ import annotations

import os
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from groq import Groq  # Import Groq client

from app.core.config import get_settings
from app.schemas.chat import AgentMode
from app.services.agents import plan_research_steps, build_rag_prompt

# Retrieval imports
from app.services.embeddings import embed_texts
# FIX: Import 'search_index' instead of 'search'
from app.services.faiss_store import search_index as faiss_search
from app.models.document import Document, DocumentChunk
from app.services.analytics import record_query_analytics

logger = logging.getLogger(__name__)
settings = get_settings()

# ----------------------------
# Groq Setup (Enabled)
# ----------------------------
# Ensure GROQ_API_KEY is set in your Render Env Vars
client = Groq(api_key=settings.GROQ_API_KEY)


def _call_llm(prompt: str, mode: AgentMode) -> Tuple[str, Dict[str, int]]:
    """
    Real call to Groq LLM.
    """
    # Select model based on agent_mode
    # Updated to Llama 3.1/3.3 models (Current as of late 2024/2025)
    if mode == AgentMode.research:
        model_name = "llama-3.3-70b-versatile"  # Smarter, latest model
    else:
        model_name = "llama-3.1-8b-instant"     # Extremely fast model

    try:
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful AI assistant. Answer strictly based on the provided context."
                },
                {"role": "user", "content": prompt}
            ],
            model=model_name,
            temperature=0.1,  # Low temp for factual accuracy
        )

        answer = completion.choices[0].message.content
        
        # Safe access to usage stats
        usage = completion.usage
        token_usage = {
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0
        }
        return answer, token_usage

    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        return "I'm sorry, I encountered an error connecting to the AI model.", {
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0
        }


# ----------------------------
# Retrieval (embeddings + FAISS)
# ----------------------------

def _retrieve_context(
    db: Session,
    user_id: Optional[Any],
    query: str,
    selected_document_ids: Optional[List[str]] = None,
    top_k: int = 8,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Retrieves relevant chunks from the vector DB.
    """
    if not user_id:
        logger.info("No user_id provided to _retrieve_context; returning empty context.")
        return [], []

    try:
        uid = uuid.UUID(str(user_id))
    except (ValueError, TypeError):
        logger.warning(f"Invalid user_id {user_id} passed to _retrieve_context.")
        return [], []

    if selected_document_ids is None:
        selected_document_ids = []

    # 1) Embed query
    try:
        # embed_texts returns a list of vectors, take the first one
        query_vectors = embed_texts([query])
        q_vec = query_vectors[0]
    except Exception as e:
        logger.warning(f"Failed to embed query: {e}")
        return [], []

    # 2) FAISS search
    try:
        # We use 'search_index' which is imported as 'faiss_search'
        faiss_results = faiss_search(
            user_id=str(uid),
            query_vector=q_vec,
            top_k=top_k
        )
    except Exception as e:
        logger.warning(f"FAISS search failed: {e}")
        return [], []

    if not faiss_results:
        return [], []

    # 3) Collect chunk IDs and fetch text from DB
    # faiss_results is a list of dicts: {'score': float, 'metadata': dict}
    # metadata contains 'chunk_id', 'document_id', 'text', etc.
    
    context_chunks: List[str] = []
    sources: List[Dict[str, Any]] = []

    # Filter by selected_document_ids if provided
    # Convert selected_document_ids to set of strings for faster lookup
    selected_ids_set = set(str(d) for d in selected_document_ids) if selected_document_ids else None

    for res in faiss_results:
        meta = res["metadata"]
        doc_id = meta.get("document_id")
        
        # If filtering is active and this doc is not selected, skip
        if selected_ids_set and str(doc_id) not in selected_ids_set:
            continue
            
        text = meta.get("text", "")
        if text:
            context_chunks.append(text)
            sources.append({
                "id": meta.get("chunk_id"),
                "document_id": doc_id,
                "filename": meta.get("filename", "Unknown"),
                "snippet": text[:300],
                "score": res["score"]
            })

    return context_chunks, sources


# ----------------------------
# Main RAG entry point
# ----------------------------

def run_rag_query(
    db: Session,
    user_id: Optional[str],
    query: str,
    agent_mode: AgentMode,
    selected_document_ids: Optional[List[str]] = None,
) -> Tuple[str, List[Dict[str, Any]], Dict[str, int], float]:
    """
    Core RAG pipeline.
    """
    start = time.perf_counter()

    # Normalize agent_mode
    if isinstance(agent_mode, str):
        try:
            agent_mode = AgentMode(agent_mode)
        except ValueError:
            agent_mode = AgentMode.default

    if selected_document_ids is None:
        selected_document_ids = []

    # 1) Retrieval
    context_chunks, sources = _retrieve_context(
        db=db,
        user_id=user_id,
        query=query,
        selected_document_ids=selected_document_ids,
        top_k=8,
    )

    token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # 2) Agent Logic
    if agent_mode == AgentMode.research:
        steps = plan_research_steps(query)
        sub_answers = []
        for step in steps:
            step_prompt = build_rag_prompt(step, context_chunks, agent_mode)
            step_answer, step_usage = _call_llm(step_prompt, agent_mode)
            sub_answers.append(f"Sub-question: {step}\nAnswer: {step_answer}\n")
            
            # Sum usage
            for k in token_usage:
                token_usage[k] += step_usage.get(k, 0)

        synth_prompt = (
            "Combine these sub-answers into a coherent final answer:\n"
            f"{chr(10).join(sub_answers)}"
        )
        answer, synth_usage = _call_llm(synth_prompt, agent_mode)
        for k in token_usage:
            token_usage[k] += synth_usage.get(k, 0)

    elif agent_mode == AgentMode.summarizer:
        summary_query = f"Summarize the following context for: {query}"
        prompt = build_rag_prompt(summary_query, context_chunks, agent_mode)
        answer, token_usage = _call_llm(prompt, agent_mode)

    elif agent_mode == AgentMode.brainstorm:
        brainstorm_query = f"Brainstorm ideas based on context for: {query}"
        prompt = build_rag_prompt(brainstorm_query, context_chunks, agent_mode)
        answer, token_usage = _call_llm(prompt, agent_mode)

    else:
        # Standard RAG
        prompt = build_rag_prompt(query, context_chunks, agent_mode)
        answer, token_usage = _call_llm(prompt, agent_mode)

    latency_ms = (time.perf_counter() - start) * 1000.0

    # 3) Analytics
    try:
        doc_ids = list({src["document_id"] for src in sources if "document_id" in src})
        record_query_analytics(
            db=db,
            user_id=user_id or "",
            query=query,
            agent_mode=agent_mode.value if isinstance(agent_mode, AgentMode) else str(agent_mode),
            latency_ms=latency_ms,
            token_usage=token_usage,
            document_ids=doc_ids,
        )
    except Exception as e:
        logger.warning(f"Failed to record analytics: {e}")

    return answer, sources, token_usage, latency_ms
