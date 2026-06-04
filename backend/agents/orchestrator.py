from .router import route
from .agents import AGENT_REGISTRY

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # ensure backend/ is on path
from rag.pipeline import ask as rag_ask


def process(
    query:  str,
    role:   str  = "student",
    top_k:  int  = 5,
    debug:  bool = False,
) -> dict:
    """
    Full multi-agent pipeline — one function called by the API.

      Step 1  Semantic router picks the best accessible agent
      Step 2  That agent's ChromaDB filter retrieves relevant chunks
      Step 3  Groq Llama 3 generates a cited, role-aware answer

    Args:
        query  — natural language question
        role   — "student" | "faculty" | "admin" | "general"
        top_k  — number of chunks to retrieve (default 5)
        debug  — attach routing scores and raw chunks to response

    Returns:
        answer   — the generated answer string
        agent    — human-readable agent name that handled the query
        sources  — list of source filenames cited
        role     — role that was applied
        (+ routing and chunks keys when debug=True)
    """
    # ── Step 1: Route ────────────────────────────────────────────────────
    routing   = route(query, role=role)
    agent_key = routing["agent"]
    cfg       = AGENT_REGISTRY[agent_key]

    # ── Step 2 + 3: RAG with this agent's filter ─────────────────────────
    rag_result = rag_ask(
        query        = query,
        role         = cfg.role,
        agent_filter = cfg.agent_filter,
        top_k        = top_k,
    )

    # ── Assemble response ─────────────────────────────────────────────────
    response = {
        "answer":  rag_result["answer"],
        "agent":   cfg.name,
        "sources": rag_result["sources"],
        "role":    role,
    }

    if debug:
        response["routing"]     = routing
        response["chunks"]      = rag_result["retrieved_chunks"]
        response["chunks_used"] = rag_result["chunks_used"]

    return response