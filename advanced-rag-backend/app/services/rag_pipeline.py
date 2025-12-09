# app/services/rag_pipeline.py

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.chat import AgentMode
from app.services.agents import plan_research_steps, build_rag_prompt

# NEW: imports for real retrieval
from app.services.embeddings import embed_query
from app.services.faiss_store import search as faiss_search
from app.models.document import Document, DocumentChunk
from app.services.analytics import record_query_analytics

logger = logging.getLogger(__name__)
settings = get_settings()

# ----------------------------
# Groq client (hard-disabled)
# ----------------------------
_groq_client = None  # hard-disable Groq in cloud/demo mode


def _call_llm(prompt: str, mode: AgentMode) -> Tuple[str, Dict[str, int]]:
    """
    Call LLM – but since Groq is hard-disabled, always return a safe fallback.

    This keeps the whole RAG pipeline (retrieval, prompts, analytics)
    working end-to-end without relying on any external LLM provider.
    """
    logger.info("LLM call skipped because Groq client is hard-disabled.")
    fallback = (
        "LLM backend is disabled in this demo environment.\n"
        "The RAG pipeline (document upload, chunking, retrieval, prompts) "
        "ran successfully, but no actual model inference was performed.\n\n"
        "To enable real answers, configure an LLM provider (e.g. Groq) "
        "and wire it into `_call_llm`."
    )
    return fallback, {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


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
    REAL retrieval:

    - Convert user_id → UUID
    - Embed query
    - Search per-user FAISS index
    - Map results back to DocumentChunk + Document
    - Return (context_chunks, sources)
    """
    if not user_id:
        logger.info("No user_id provided to _retrieve_context; returning empty context.")
        return [], []

    try:
        uid = uuid.UUID(str(user_id))
    except (ValueError, TypeError):
        logger.warning(
            "Invalid user_id %r passed to _retrieve_context; returning empty context.",
            user_id,
        )
        return [], []

    if selected_document_ids is None:
        selected_document_ids = []

    # 1) embed query
    try:
        q_vec = embed_query(query)
    except Exception as e:
        logger.warning("Failed to embed query for retrieval: %s", e)
        return [], []

    # 2) FAISS search (per-user index)
    try:
        faiss_results = faiss_search(
            user_id=uid,
            query_vec=q_vec,
            top_k=top_k,
            filter_doc_ids=selected_document_ids or None,
        )
    except Exception as e:
        logger.warning("FAISS search failed: %s", e)
        return [], []

    if not faiss_results:
        logger.info("No FAISS results for user_id=%s query=%r", uid, query)
        return [], []

    # 3) Collect chunk IDs and fetch from DB
    chunk_ids: List[uuid.UUID] = []
    for r in faiss_results:
        cid = r.get("chunk_id")
        if not cid:
            continue
        try:
            chunk_ids.append(uuid.UUID(str(cid)))
        except (ValueError, TypeError):
            continue

    if not chunk_ids:
        return [], []

    # join chunks with documents to get filename etc.
    rows = (
        db.query(DocumentChunk, Document)
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(DocumentChunk.id.in_(chunk_ids))
        .all()
    )

    context_chunks: List[str] = []
    sources: List[Dict[str, Any]] = []

    for ch, doc in rows:
        if not ch.text:
            continue

        context_chunks.append(ch.text)
        sources.append(
            {
                "id": str(ch.id),
                "document_id": str(doc.id),
                "filename": doc.filename,
                "snippet": ch.text[:300],
            }
        )

    logger.info(
        "Retrieved %d context chunks for user_id=%s, query=%r",
        len(context_chunks),
        uid,
        query,
    )

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
    Core RAG pipeline used by /api/chat/query.

    Parameters are shaped to match the router call:
        run_rag_query(db=db, user_id=current_user.id, query=..., agent_mode=..., selected_document_ids=...)

    Returns:
        answer: str
        sources: list of {id, document_id, filename, snippet}
        token_usage: {prompt_tokens, completion_tokens, total_tokens}
        latency_ms: float
    """
    start = time.perf_counter()

    # Normalize agent_mode if we somehow got a raw string
    if isinstance(agent_mode, str):
        try:
            agent_mode = AgentMode(agent_mode)
        except ValueError:
            agent_mode = AgentMode.default

    if selected_document_ids is None:
        selected_document_ids = []

    # 1) retrieval
    context_chunks, sources = _retrieve_context(
        db=db,
        user_id=user_id,
        query=query,
        selected_document_ids=selected_document_ids,
        top_k=8,
    )

    token_usage: Dict[str, int] = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }

    # 2) agent-mode specific behavior
    if agent_mode == AgentMode.research:
        # --- research: planner → multiple LLM calls → synthesis ---
        steps = plan_research_steps(query)
        sub_answers: List[str] = []

        for step in steps:
            step_prompt = build_rag_prompt(step, context_chunks, agent_mode)
            step_answer, step_usage = _call_llm(step_prompt, agent_mode)
            sub_answers.append(f"Sub-question: {step}\nAnswer:\n{step_answer}\n")

            for k in token_usage:
                token_usage[k] += step_usage.get(k, 0)

        synth_prompt = (
            "You are a research synthesis assistant.\n\n"
            "You are given several sub-answers generated in earlier steps. "
            "Combine them into a single, coherent answer that directly addresses "
            "the original user query.\n\n"
            f"=== ORIGINAL QUERY ===\n{query}\n\n"
            f"=== SUB-ANSWERS ===\n{chr(10).join(sub_answers)}"
        )

        answer, synth_usage = _call_llm(synth_prompt, agent_mode)
        for k in token_usage:
            token_usage[k] += synth_usage.get(k, 0)

    elif agent_mode == AgentMode.summarizer:
        # --- summarizer: summary-focused prompt ---
        summary_query = (
            "Create a clear, structured summary of the most relevant information for the user. "
            "Include an overview, key points, and any important caveats.\n\n"
            f"User task/context: {query}"
        )
        prompt = build_rag_prompt(summary_query, context_chunks, agent_mode)
        answer, token_usage = _call_llm(prompt, agent_mode)

    elif agent_mode == AgentMode.brainstorm:
        # --- brainstorm: idea-generation prompt ---
        brainstorm_query = (
            "Generate multiple concrete ideas, suggestions, or next steps for the user, "
            "grounded in the available context where possible.\n\n"
            f"Brainstorm around: {query}"
        )
        prompt = build_rag_prompt(brainstorm_query, context_chunks, agent_mode)
        answer, token_usage = _call_llm(prompt, agent_mode)

    else:
        # --- default: standard single-shot RAG ---
        prompt = build_rag_prompt(query, context_chunks, agent_mode)
        answer, token_usage = __call_llm(prompt, agent_mode)

    latency_ms = (time.perf_counter() - start) * 1000.0

    # 3) Best-effort analytics – never crash the request
    try:
        # (imported at top, but we use a local reference here to be explicit)
        doc_ids = list(
            {src["document_id"] for src in sources if "document_id" in src}
        )

        record_query_analytics(
            db=db,
            user_id=user_id or "",
            query=query,
            agent_mode=agent_mode.value if isinstance(agent_mode, AgentMode) else str(
                agent_mode
            ),
            latency_ms=latency_ms,
            token_usage=token_usage,
            document_ids=doc_ids,
        )
    except Exception as e:
        logger.warning("Failed to record analytics: %s", e)

    return answer, sources, token_usage, latency_ms
