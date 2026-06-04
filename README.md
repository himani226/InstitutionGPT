<div align="center">

# 🎓 InstitutionGPT

### Agentic AI Assistant for Universities

*RAG-powered · Multi-agent · Role-based · Streaming · Free stack*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-F55036?style=flat-square)](https://groq.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5-orange?style=flat-square)](https://trychroma.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**[Live Demo](https://institutiongpt.vercel.app)** · **[API Docs](https://institutiongpt-api.onrender.com/docs)** · **[MindSprout Technologies](https://mindsprout.in)**

</div>

---

## What is InstitutionGPT?

InstitutionGPT is a domain-specific agentic AI assistant built for universities. It lets students, faculty, and administrators ask natural language questions about institutional knowledge — policies, fees, courses, timetables, research resources — and get accurate, cited answers in real time.

It is built entirely on **free APIs and open-source tools**, making it deployable by any institution at zero cost.

```
"What is the last date to apply for B.Tech?"
→ Routes to Admissions Agent
→ Retrieves from admissions_guide.txt
→ "Applications close on 30 April 2025. The NUET entrance test is on 15 May..."
```

---

## Features

- **RAG-powered Q&A** — answers grounded in real institutional documents, not hallucinations
- **Multi-agent routing** — semantic router dispatches each query to the right specialist agent
- **Role-based access** — student, faculty, and admin views with separate knowledge scopes
- **Streaming responses** — token-by-token SSE streaming with a live typing effect
- **Session memory** — conversation history tracked per session
- **Multilingual-ready** — LLM responds in the language the user writes in
- **Embeddable** — ships as an iframe-ready React app for any website
- **Free stack** — Groq free tier + ChromaDB local + sentence-transformers local

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                           │
│          Role selector · Chat UI · SSE streaming                │
└───────────────────────────┬─────────────────────────────────────┘
                            │ POST /api/chat/stream
┌───────────────────────────▼─────────────────────────────────────┐
│                      FastAPI Backend                            │
│               Role validation · Session management              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     Semantic Router                             │
│    Embeds query · Cosine similarity · Role-based access         │
└────────┬──────────────────┬──────────────────┬──────────────────┘
         │                  │                  │
    ┌────▼─────┐      ┌─────▼────┐      ┌─────▼────┐
    │Admissions│      │Academics │      │  Admin   │  ← + Faculty
    │  Agent   │      │  Agent   │      │  Agent   │    + Student
    └────┬─────┘      └─────┬────┘      └─────┬────┘
         │                  │                  │
┌────────▼──────────────────▼──────────────────▼──────────────────┐
│                       RAG Pipeline                              │
│       Retrieve from ChromaDB · Build prompt · Generate          │
└──────────────────────┬──────────────────┬───────────────────────┘
                       │                  │
              ┌────────▼───┐    ┌─────────▼──────┐
              │  ChromaDB  │    │  Groq Llama 3  │
              │ 58 chunks  │    │  free API      │
              └────────────┘    └────────────────┘
```

### Role → Agent access matrix

| Agent | Student | Faculty | Admin |
|---|:---:|:---:|:---:|
| Admissions | ✅ | — | ✅ |
| Academics | ✅ | ✅ | ✅ |
| Student services | ✅ | — | ✅ |
| Faculty | — | ✅ | ✅ |
| Admin | — | — | ✅ |

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| LLM | Groq API · Llama 3.3 70B | Free tier · 14,400 req/day · very fast |
| Embeddings | sentence-transformers · MiniLM-L6-v2 | Free · runs locally · 384-dim |
| Vector DB | ChromaDB | Free · local · persistent · cosine search |
| Backend | FastAPI + Uvicorn | Async · SSE support · auto Swagger docs |
| Frontend | React 18 + Vite | Fast builds · SSE streaming · embeddable |
| Backend deploy | Render (free) | Docker · auto-deploy from GitHub |
| Frontend deploy | Vercel (free) | CDN · instant · env vars |

---

## Project Structure

```
institutiongpt/
├── .gitignore
├── render.yaml               # Render deployment config
├── embed.html                # Iframe snippet for MindSprout website
│
├── backend/
│   ├── Dockerfile
│   ├── main.py               # FastAPI app — 7 endpoints
│   ├── requirements.txt
│   │
│   ├── rag/
│   │   ├── ingestor.py       # Load docs → chunk → embed → store
│   │   ├── retriever.py      # Embed query → cosine search → top-k chunks
│   │   ├── generator.py      # Build prompt → Groq → answer (+ streaming)
│   │   └── pipeline.py       # Orchestrates retrieve + generate
│   │
│   ├── agents/
│   │   ├── router.py         # Semantic router (MiniLM cosine similarity)
│   │   ├── agents.py         # Agent configs (filter, role, contact)
│   │   └── orchestrator.py   # Route → RAG → response
│   │
│   ├── data/                 # University knowledge base (.txt files)
│   │   ├── admissions_guide.txt
│   │   ├── fee_structure.txt
│   │   ├── course_catalog.txt
│   │   ├── academic_calendar.txt
│   │   ├── student_handbook.txt
│   │   ├── faculty_handbook.txt
│   │   └── admin_policy.txt
│   │
│   └── chroma_db/            # Pre-built vector store (committed to git)
│
└── frontend/
    ├── vercel.json
    ├── .env.production
    ├── vite.config.js        # Proxies /api → localhost:8000 in dev
    ├── index.html
    └── src/
        ├── App.jsx           # State management + streaming logic
        ├── index.css         # Design tokens + all component styles
        ├── api/
        │   └── client.js     # Fetch-based SSE stream reader
        └── components/
            ├── Header.jsx        # Logo + role selector
            ├── ChatWindow.jsx    # Message list + suggestions
            ├── MessageBubble.jsx # User/assistant bubbles + cursor
            └── InputBar.jsx      # Auto-resizing textarea + send
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check + ChromaDB chunk count |
| `GET` | `/api/agents` | List all agents and role access |
| `GET` | `/api/roles` | List roles and their accessible agents |
| `POST` | `/api/chat` | Standard chat (full response) |
| `POST` | `/api/chat/stream` | Streaming chat via SSE |
| `GET` | `/api/session/{id}` | Get conversation history |
| `DELETE` | `/api/session/{id}` | Clear conversation history |

Full interactive docs available at `/docs` when the server is running.

### Example request

```bash
curl -X POST https://institutiongpt-api.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the last date to apply for B.Tech?", "role": "student"}'
```

```json
{
  "answer": "The last date for UG applications is 30 April 2025...",
  "agent": "Admissions Agent",
  "sources": ["admissions_guide.txt"],
  "role": "student",
  "session_id": "a1b2c3d4-..."
}
```

---

## Local Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Groq API key — free at [console.groq.com](https://console.groq.com)

### 1. Clone and set up backend

```bash
git clone https://github.com/YOUR_USERNAME/institutiongpt.git
cd institutiongpt/backend

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
# backend/.env
GROQ_API_KEY=your_key_here
```

### 3. Ingest documents into ChromaDB

```bash
python rag/ingestor.py
```

Downloads MiniLM (~80 MB on first run), chunks all 7 documents, stores 58 vectors.

### 4. Start the backend

```bash
python main.py
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### 5. Start the frontend

```bash
cd ../frontend
npm install
npm run dev
# → http://localhost:3000
```

The Vite dev server proxies `/api/*` to `localhost:8000` automatically — no CORS configuration needed.

---

## Deployment

### Backend → Render (free)

1. Push repo to GitHub
2. Connect repo on [render.com](https://render.com)
3. Render detects `render.yaml` automatically
4. Add `GROQ_API_KEY` in Environment Variables
5. Deploy — live in ~6 minutes

### Frontend → Vercel (free)

1. Connect repo on [vercel.com](https://vercel.com)
2. Set root directory to `frontend`
3. Add `VITE_API_URL=https://your-service.onrender.com`
4. Deploy — live in ~60 seconds

### Embed on any website

```html
<iframe
  src="https://YOUR-PROJECT.vercel.app"
  width="100%"
  height="680"
  frameborder="0"
  style="border-radius:16px; box-shadow:0 8px 40px rgba(0,0,0,0.12);"
  title="InstitutionGPT Demo"
></iframe>
```

---

## Adding Your Own Documents

1. Drop `.txt`, `.pdf`, or `.csv` files into `backend/data/`
2. Register them in `backend/rag/ingestor.py` under `DOC_AGENT_MAP`
3. Re-run ingestion:
   ```bash
   python rag/ingestor.py
   ```
4. Commit the updated `chroma_db/` and push — Render redeploys automatically

---

## Roadmap

- [ ] PDF ingestion support (PyPDF already in requirements)
- [ ] Multilingual UI (Hindi, Tamil, Marathi)
- [ ] LMS integration (Moodle REST API)
- [ ] Student ERP portal connector
- [ ] Voice input via Web Speech API
- [ ] Admin dashboard — upload docs, monitor queries
- [ ] Analytics — most-asked questions, unanswered queries
- [ ] Multi-institution support (tenant-aware vector namespaces)

---

## Built By

**MindSprout Technologies**
Building AI-powered products for education and enterprise.

[mindsprout.tech](https://mindsprout.tech) · [LinkedIn](https://www.linkedin.com/company/mindsprout-technologies/)

---

## License

MIT License — free to use, modify, and deploy.

---

<div align="center">

*Built with FastAPI · ChromaDB · Groq · React · sentence-transformers*

⭐ Star this repo if you found it useful

</div>
