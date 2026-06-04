from __future__ import annotations

import asyncio
import json
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib    import Path
from typing     import AsyncGenerator

import uvicorn
from fastapi             import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses   import StreamingResponse

# ── ensure backend/ is always on the path ─────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from agents.agents       import AGENT_REGISTRY
from agents.orchestrator import process
from agents.router       import ROLE_ACCESS, route as semantic_route
from api.models          import (
    AgentInfo, ChatRequest, ChatResponse, HealthResponse, RoutingInfo,
)
from rag.generator import stream_answer
from rag.retriever import _get_collection, retrieve

# ── In-memory session store ────────────────────────────────────────────────────
# Resets on server restart — swap for Redis in production
sessions: dict[str, list[dict]] = {}
MAX_HISTORY = 20

VALID_ROLES = {"student", "faculty", "admin", "general"}

# ── Build inverse role-access map (agent → which roles can reach it) ───────────
def _inverse_access() -> dict[str, list[str]]:
    inv: dict[str, list[str]] = {k: [] for k in AGENT_REGISTRY}
    for role, agents in ROLE_ACCESS.items():
        if role == "general":
            continue
        for a in agents:
            if role not in inv[a]:
                inv[a].append(role)
    return inv

AGENT_ROLES = _inverse_access()


# ── Lifespan — warm up the embedding model before first request ────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n  InstitutionGPT starting up...")
    try:
        semantic_route("warmup", role="student")   # loads MiniLM into memory
        col = _get_collection()
        print(f"  Models ready. {col.count()} chunks in ChromaDB.\n")
    except Exception as e:
        print(f"  Startup warning: {e}\n")
    yield
    print("\n  InstitutionGPT shutting down.")


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "InstitutionGPT API",
    description = (
        "Agentic AI assistant for Northfield University. "
        "Powered by RAG + Groq Llama 3 + ChromaDB."
    ),
    version     = "1.0.0",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],      # tighten to your domain in production
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
#  SYSTEM ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.get(
    "/api/health",
    response_model = HealthResponse,
    tags           = ["System"],
    summary        = "Health check",
)
def health():
    """Confirms the API is up and returns ChromaDB chunk count."""
    try:
        col = _get_collection()
        n   = col.count()
        return HealthResponse(
            status        = "ok",
            version       = "1.0.0",
            models_loaded = True,
            chunks_in_db  = n,
            message       = f"InstitutionGPT is running. {n} chunks indexed.",
        )
    except Exception as e:
        return HealthResponse(
            status        = "degraded",
            version       = "1.0.0",
            models_loaded = False,
            chunks_in_db  = 0,
            message       = f"ChromaDB not ready: {e}",
        )


# ─────────────────────────────────────────────────────────────────────────────
#  AGENT + ROLE INFO
# ─────────────────────────────────────────────────────────────────────────────

@app.get(
    "/api/agents",
    response_model = list[AgentInfo],
    tags           = ["Agents"],
    summary        = "List all agents",
)
def list_agents():
    """Returns every agent and the roles that can access it."""
    return [
        AgentInfo(
            key           = key,
            name          = cfg.name,
            description   = cfg.description,
            accessible_by = AGENT_ROLES.get(key, []),
        )
        for key, cfg in AGENT_REGISTRY.items()
    ]


@app.get(
    "/api/roles",
    tags    = ["Agents"],
    summary = "List all roles and their accessible agents",
)
def list_roles():
    role_descriptions = {
        "student": "UG/PG students — admissions, academics, student services",
        "faculty": "Teaching staff — academics and faculty resources",
        "admin":   "Administrative staff — full access to all agents",
        "general": "Guest / public access — admissions and basic info",
    }
    return {
        role: {"agents": agents, "description": role_descriptions.get(role, "")}
        for role, agents in ROLE_ACCESS.items()
    }


# ─────────────────────────────────────────────────────────────────────────────
#  CHAT — STANDARD (full response at once)
# ─────────────────────────────────────────────────────────────────────────────

@app.post(
    "/api/chat",
    response_model = ChatResponse,
    tags           = ["Chat"],
    summary        = "Send a query and get a cited answer",
)
def chat(req: ChatRequest):
    """
    Main chat endpoint.

    1. Validates the role.
    2. Routes the query to the best accessible agent (semantic routing).
    3. Retrieves relevant chunks from ChromaDB.
    4. Generates a cited answer via Groq Llama 3.
    5. Saves the turn to the session history.
    """
    if req.role not in VALID_ROLES:
        raise HTTPException(
            status_code = 400,
            detail      = f"Invalid role '{req.role}'. Choose from: {sorted(VALID_ROLES)}",
        )

    session_id = req.session_id or str(uuid.uuid4())
    sessions.setdefault(session_id, [])

    try:
        result = process(query=req.query, role=req.role, top_k=5, debug=True)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Agent error: {exc}")

    # Persist conversation turn
    sessions[session_id].extend([
        {"role": "user",      "content": req.query},
        {"role": "assistant", "content": result["answer"]},
    ])
    # Keep history bounded
    if len(sessions[session_id]) > MAX_HISTORY:
        sessions[session_id] = sessions[session_id][-MAX_HISTORY:]

    routing_info = RoutingInfo(**result["routing"]) if req.debug else None

    return ChatResponse(
        answer     = result["answer"],
        agent      = result["agent"],
        sources    = result["sources"],
        role       = req.role,
        session_id = session_id,
        routing    = routing_info,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  CHAT — STREAMING  (Server-Sent Events)
# ─────────────────────────────────────────────────────────────────────────────

@app.post(
    "/api/chat/stream",
    tags    = ["Chat"],
    summary = "Streaming chat via Server-Sent Events",
)
async def chat_stream(req: ChatRequest):
    """
    SSE streaming endpoint — powers the typing effect in the React UI.

    Event types emitted:
      {"type": "meta",  "agent": "...", "sources": [...], "session_id": "..."}
      {"type": "token", "content": "..."}    — one per token
      {"type": "done"}                        — stream complete
      {"type": "error", "message": "..."}    — on failure
    """
    if req.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role '{req.role}'")

    session_id = req.session_id or str(uuid.uuid4())

    # Do routing + retrieval synchronously before opening the stream
    # (fast, no LLM — no need to defer to async)
    routing   = semantic_route(req.query, role=req.role)
    agent_key = routing["agent"]
    cfg       = AGENT_REGISTRY[agent_key]
    chunks    = retrieve(req.query, top_k=5, agent_filter=cfg.agent_filter)
    sources   = list({c["source"] for c in chunks})

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            # ── 1. Metadata event ──────────────────────────────────────────
            yield f"data: {json.dumps({'type': 'meta', 'agent': cfg.name, 'sources': sources, 'session_id': session_id})}\n\n"

            # ── 2. Token events (sync generator → async via executor) ──────
            loop     = asyncio.get_event_loop()
            gen      = stream_answer(req.query, chunks, role=cfg.role)
            full: list[str] = []

            def _next_token():
                try:
                    return next(gen)
                except StopIteration:
                    return None

            while True:
                token = await loop.run_in_executor(None, _next_token)
                if token is None:
                    break
                full.append(token)
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # ── 3. Done event ──────────────────────────────────────────────
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

            # ── 4. Save to session ─────────────────────────────────────────
            sessions.setdefault(session_id, [])
            sessions[session_id].extend([
                {"role": "user",      "content": req.query},
                {"role": "assistant", "content": "".join(full)},
            ])

        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type = "text/event-stream",
        headers    = {
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",        # disable nginx buffering
            "Access-Control-Allow-Origin": "*",
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
#  SESSION ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.get(
    "/api/session/{session_id}",
    tags    = ["Session"],
    summary = "Get conversation history",
)
def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "messages": sessions[session_id]}


@app.delete(
    "/api/session/{session_id}",
    tags    = ["Session"],
    summary = "Clear conversation history",
)
def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return {"message": "Session cleared", "session_id": session_id}


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)