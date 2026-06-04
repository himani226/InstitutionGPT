import os
from pathlib import Path
from typing import Optional
import chromadb
from sentence_transformers import SentenceTransformer

BASE       = Path(__file__).parent.parent
CHROMA_DIR = BASE / "chroma_db"
EMBED_MODEL = "all-MiniLM-L6-v2"

# Singletons — loaded once, reused on every query
_model:      SentenceTransformer | None = None
_collection: chromadb.Collection  | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def _get_collection() -> chromadb.Collection:
    global _collection
    if _collection is None:
        client      = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_collection("northfield_docs")
    return _collection


def retrieve(
    query:        str,
    top_k:        int           = 5,
    agent_filter: Optional[str] = None,   # e.g. "admissions", "faculty"
) -> list[dict]:
    """
    Embed query, search ChromaDB, return top_k matching chunks.

    Each result dict contains:
        text       — the raw chunk text
        source     — original filename
        agent_type — admissions / academics / student / faculty / admin
        score      — cosine similarity (0–1, higher = more relevant)
    """
    model      = _get_model()
    collection = _get_collection()

    query_vec = model.encode([query]).tolist()[0]
    where     = {"agent_type": agent_filter} if agent_filter else None

    results = collection.query(
        query_embeddings=[query_vec],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text":       doc,
            "source":     meta["source"],
            "agent_type": meta["agent_type"],
            "score":      round(1 - dist, 4),   # cosine distance → similarity
        })

    return chunks