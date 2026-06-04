import os
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL   = "llama-3.3-70b-versatile"

# Role-specific system prompts — controls tone and focus
ROLE_PROMPTS = {
    "student": (
        "You are InstitutionGPT, a friendly university assistant for students at "
        "Northfield University. Help with fees, admissions, courses, timetables, "
        "exam schedules, hostel rules, and student services. Be warm and concise. "
        "Always cite specific details from the context. If something isn't in the "
        "context, say so and suggest the right office to contact. "
        "Respond in the same language the user wrote in."
    ),
    "faculty": (
        "You are InstitutionGPT, a professional assistant for faculty at Northfield "
        "University. Answer questions about pay scales, research incentives, leave "
        "policy, lab resources, LMS duties, and academic responsibilities. "
        "Be precise and cite policy sections where relevant. "
        "Respond in the same language the user wrote in."
    ),
    "admin": (
        "You are InstitutionGPT, an administrative assistant for staff at Northfield "
        "University. Answer questions about procurement, IT systems, document processing, "
        "transport, parking, and emergency contacts. Be direct and procedural. "
        "Respond in the same language the user wrote in."
    ),
    "general": (
        "You are InstitutionGPT, a helpful AI assistant for Northfield University. "
        "Answer questions using only the provided context. Be accurate and concise. "
        "Respond in the same language the user wrote in."
    ),
}


def _build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block for the LLM."""
    if not chunks:
        return "No relevant documents found in the knowledge base."
    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(f"[Source {i} — {chunk['source']}]")
        lines.append(chunk["text"])
        lines.append("")
    return "\n".join(lines)


def generate_answer(
    query:  str,
    chunks: list[dict],
    role:   str = "general",
) -> dict:
    """
    Call Groq Llama 3 with the retrieved context and return the answer.

    Returns:
        answer       — the LLM response text
        sources      — list of source filenames used
        chunks_used  — number of chunks in context
        role         — role that was applied
    """
    system_prompt = ROLE_PROMPTS.get(role, ROLE_PROMPTS["general"])
    context       = _build_context(chunks)

    user_message = f"""Answer the following question using ONLY the context below.
If the answer is not present, say "I don't have that in my knowledge base" and suggest the relevant contact.

CONTEXT:
{context}

QUESTION: {query}

Answer clearly and helpfully:"""

    response = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system",  "content": system_prompt},
            {"role": "user",    "content": user_message},
        ],
        temperature=0.2,    # low = factual, consistent answers
        max_tokens=1024,
    )

    return {
        "answer":      response.choices[0].message.content,
        "sources":     list({c["source"] for c in chunks}),
        "chunks_used": len(chunks),
        "role":        role,
    }

def stream_answer(
    query:  str,
    chunks: list[dict],
    role:   str = "general",
):
    """
    Sync generator that yields one token at a time from Groq.
    Used by the SSE streaming endpoint in main.py.
    """
    system_prompt = ROLE_PROMPTS.get(role, ROLE_PROMPTS["general"])
    context       = _build_context(chunks)

    user_message = f"""Answer the following question using ONLY the context below.
If the answer is not present, say "I don't have that in my knowledge base"
and suggest the relevant contact.

CONTEXT:
{context}

QUESTION: {query}

Answer clearly and helpfully:"""

    response = _client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.2,
        max_tokens=1024,
        stream=True,             # ← only difference from generate_answer
    )

    for chunk in response:
        token = chunk.choices[0].delta.content
        if token:
            yield token