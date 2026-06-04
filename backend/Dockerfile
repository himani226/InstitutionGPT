# ── Build stage ────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# System deps needed by chromadb C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps (cached as a layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Pre-bake the MiniLM model into the image ────────────────────────
# Without this, every cold start downloads ~80 MB from HuggingFace.
# Including it here means cold starts take ~5s instead of ~40s.
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('all-MiniLM-L6-v2'); \
print('Model cached.')"

# Copy all backend files, including the pre-built chroma_db/
COPY . .

EXPOSE 8000

# Render sets $PORT automatically; fall back to 8000 for local Docker runs
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]