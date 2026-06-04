import os
import uuid
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

BASE       = Path(__file__).parent.parent        # backend/
DATA_DIR   = BASE / "data"
CHROMA_DIR = BASE / "chroma_db"
EMBED_MODEL = "all-MiniLM-L6-v2"

# Which agent owns each document
DOC_AGENT_MAP = {
    "admissions_guide.txt":  "admissions",
    "fee_structure.txt":     "admissions",
    "course_catalog.txt":    "academics",
    "academic_calendar.txt": "academics",
    "student_handbook.txt":  "student",
    "faculty_handbook.txt":  "faculty",
    "admin_policy.txt":      "admin",
}


def chunk_document(text: str, max_words: int = 300, overlap_paras: int = 1) -> list[str]:
    """
    Split text into overlapping chunks that respect paragraph boundaries.
    Keeps the last `overlap_paras` paragraphs in the next chunk for context.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, current, current_words = [], [], 0

    for para in paragraphs:
        para_words = len(para.split())
        if current_words + para_words > max_words and current:
            chunks.append("\n\n".join(current))
            current      = current[-overlap_paras:]
            current_words = sum(len(p.split()) for p in current)
        current.append(para)
        current_words += para_words

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def ingest_all(force: bool = False) -> None:
    """
    Load every .txt file → chunk → embed → store in ChromaDB.
    Set force=True to wipe and re-ingest from scratch.
    """
    print("\n  Loading embedding model (downloads ~80 MB on first run)...")
    model = SentenceTransformer(EMBED_MODEL)
    print("  Embedding model ready.\n")

    client     = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection_name = "northfield_docs"

    if force:
        try:
            client.delete_collection(collection_name)
            print("  Deleted existing collection.\n")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    existing = collection.count()
    if existing > 0 and not force:
        print(f"  Collection already has {existing} chunks. "
              "Pass force=True to re-ingest.\n")
        return

    total_chunks = 0

    for filename, agent_type in DOC_AGENT_MAP.items():
        filepath = DATA_DIR / filename
        if not filepath.exists():
            print(f"  SKIP  {filename} (file not found)")
            continue

        text   = filepath.read_text(encoding="utf-8")
        chunks = chunk_document(text)

        # Embed all chunks in one batch (fast)
        embeddings = model.encode(chunks, show_progress_bar=False).tolist()

        ids       = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [
            {"source": filename, "agent_type": agent_type, "chunk_index": i}
            for i in range(len(chunks))
        ]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )

        print(f"  Ingested  {filename:<35} {len(chunks):>2} chunks   [{agent_type}]")
        total_chunks += len(chunks)

    print(f"\n  Total chunks stored : {total_chunks}")
    print(f"  ChromaDB persisted  : {CHROMA_DIR}\n")


if __name__ == "__main__":
    ingest_all(force=True)