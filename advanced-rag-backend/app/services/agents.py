# app/services/agents.py

from typing import List
from app.schemas.chat import AgentMode


def plan_research_steps(query: str) -> List[str]:
    """
    Very simple planner for 'research' mode.

    In a real system you'd call an LLM here to generate sub-questions,
    but this is enough to keep the backend stable and the flow clear.
    """
    query = (query or "").strip()
    if not query:
        return ["Clarify the user's question."]

    return [
        f"Restate and clarify the main question: {query}",
        f"Identify key concepts, entities, and terms related to: {query}",
        f"Search for definitions and high-level explanations for: {query}",
        f"Collect practical examples, use-cases, or code patterns related to: {query}",
        f"Synthesize a final, well-structured answer that directly addresses: {query}",
    ]


def build_rag_prompt(
    query: str,
    context_chunks: List[str],
    mode: AgentMode,
) -> str:
    """
    Build the main LLM prompt for all agent modes.

    IMPORTANT:
    - If there is NO context, don't force the model to say
      "I cannot find it in the uploaded documents."
    - Default mode should behave like a normal assistant when no docs are available.
    """

    has_context = len(context_chunks) > 0

    if mode == AgentMode.default:
        if has_context:
            mode_prefix = (
                "You are a precise RAG assistant. Prefer using the context below to answer. "
                "If the answer is clearly not in the context, you may still answer from your "
                "general knowledge, but briefly mention that the uploaded documents did not "
                "contain that specific information."
            )
        else:
            mode_prefix = (
                "You are a helpful assistant. There is currently NO document context available. "
                "Answer the user's question from your own knowledge. Do NOT say that you cannot "
                "read documents; just answer normally."
            )

    elif mode == AgentMode.research:
        mode_prefix = (
            "You are a rigorous research assistant. Use the context to build a multi-step, "
            "well-structured analysis. If information is missing, clearly say what is missing "
            "instead of guessing."
        )

    elif mode == AgentMode.summarizer:
        mode_prefix = (
            "You are a document summarization assistant. Create a clear, structured summary "
            "with sections like 'Overview', 'Key Points', and 'Important Details'. Only use "
            "what is in the context; do not invent new facts."
        )

    else:  # AgentMode.brainstorm
        mode_prefix = (
            "You are a creative ideation assistant. Use the context as grounding when available, "
            "but generate multiple concrete ideas, options, or next steps. Be practical and specific."
        )

    if has_context:
        context_text = "\n\n".join(
            f"[Snippet {i+1}]\n{chunk}" for i, chunk in enumerate(context_chunks)
        )
        context_block = context_text
    else:
        context_block = "[No document context is available for this query.]"

    return (
        f"{mode_prefix}\n\n"
        f"=== USER QUERY ===\n{query}\n\n"
        f"=== CONTEXT SNIPPETS ===\n{context_block}\n\n"
        "Now produce your final answer."
    )
