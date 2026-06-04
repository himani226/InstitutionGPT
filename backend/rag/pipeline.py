from .retriever import retrieve
from .generator import generate_answer


def ask(
    query:        str,
    role:         str           = "student",
    agent_filter: str | None    = None,
    top_k:        int           = 5,
) -> dict:
    """
    Full RAG pipeline — one function to call from the API.

    Args:
        query        : the user's natural language question
        role         : "student" | "faculty" | "admin" | "general"
        agent_filter : optionally restrict retrieval to one agent type
                       e.g. "admissions", "academics", "faculty"
        top_k        : number of chunks to retrieve

    Returns dict with: answer, sources, chunks_used, role,
                       and retrieved_chunks (for debugging)
    """
    chunks = retrieve(query, top_k=top_k, agent_filter=agent_filter)
    result = generate_answer(query, chunks, role=role)
    result["retrieved_chunks"] = chunks    # useful for the debug view
    return result