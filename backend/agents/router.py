from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

EMBED_MODEL = "all-MiniLM-L6-v2"

# Each agent is described by representative domain phrases.
# The router embeds both the query and these signatures,
# then picks the closest accessible agent.
AGENT_SIGNATURES = {
    "admissions": (
        "admission application eligibility criteria deadline fee payment "
        "scholarship hostel enrollment documents required how to apply intake process"
    ),
    "academics": (
        "course subject curriculum timetable class schedule attendance semester "
        "exam grade CGPA syllabus elective project backlog supplementary result"
    ),
    "student": (
        "student conduct library rules hostel curfew clubs activities grievance "
        "health centre anti-ragging dress code mobile phone handbook"
    ),
    "faculty": (
        "faculty pay salary scale research publication incentive leave policy "
        "sabbatical FDP teaching load lab resources annual target performance"
    ),
    "admin": (
        "certificate transcript bonafide IT portal ERP login WiFi password "
        "transport bus parking procurement emergency contact data privacy registrar"
    ),
}

# Which agents each role is permitted to query
ROLE_ACCESS = {
    "student": ["admissions", "academics", "student"],
    "faculty": ["academics",  "faculty"],
    "admin":   ["admissions", "academics", "student", "faculty", "admin"],
    "general": ["admissions", "academics", "student"],
}

# Lazy singletons — loaded once, reused on every call
_model:      SentenceTransformer       | None = None
_agent_vecs: dict[str, np.ndarray]     | None = None


def _load() -> tuple[SentenceTransformer, dict[str, np.ndarray]]:
    global _model, _agent_vecs
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    if _agent_vecs is None:
        _agent_vecs = {
            name: _model.encode(sig)
            for name, sig in AGENT_SIGNATURES.items()
        }
    return _model, _agent_vecs


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def route(query: str, role: str = "student") -> dict:
    """
    Semantically match a query to the best accessible agent.

    Returns:
        agent      — winning agent key
        score      — cosine similarity (0–1)
        role       — role applied
        allowed    — agents this role can access
        all_scores — scores for every agent (useful for debugging)
    """
    model, agent_vecs = _load()

    query_vec  = model.encode(query)
    all_scores = {
        name: round(_cosine(query_vec, vec), 4)
        for name, vec in agent_vecs.items()
    }

    # Filter to only agents this role may access
    allowed    = ROLE_ACCESS.get(role, ROLE_ACCESS["general"])
    accessible = {k: v for k, v in all_scores.items() if k in allowed}

    best = max(accessible, key=accessible.get)

    return {
        "agent":      best,
        "score":      accessible[best],
        "role":       role,
        "allowed":    allowed,
        "all_scores": all_scores,
    }