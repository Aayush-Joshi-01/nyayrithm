# Nyayrithm

> Multi-modal, agent-driven legal reasoning and courtroom simulation platform.

AI agents assume legal roles — judge, prosecutor, defense, witnesses, investigators — and simulate realistic court proceedings using evidence ingested from PDFs, audio recordings, video, and plain text. Every agent thinks, argues, cites evidence, and can spawn specialist sub-agents on the fly.

---

## Contents

- [What it does](#what-it-does)
- [Architecture overview](#architecture-overview)
- [Quick start — Docker](#quick-start--docker-recommended)
- [Running locally for free with Gemini](#running-locally-for-free-with-gemini)
- [LLM provider guide](#llm-provider-guide)
- [Embedder options](#embedder-options)
- [Configuration reference](#configuration-reference)
- [API reference](#api-reference)
- [WebSocket events](#websocket-events)
- [Extending the platform](#extending-the-platform)
- [Development commands](#development-commands)
- [Project structure](#project-structure)

### Platform setup guides
- [Windows setup](docs/setup-windows.md) — Docker Desktop, native + WSL2, or fully offline Ollama
- [macOS setup](docs/setup-macos.md) — Docker Desktop, Homebrew native, or Apple Silicon Ollama
- [Linux setup](docs/setup-linux.md) — Docker Compose, native, systemd services, GPU acceleration

---

## What it does

| Feature | Details |
|---------|---------|
| **8 agent roles** | Judge · Prosecutor · Defense · Plaintiff · Accused · Witness · Investigator · Expert Witness |
| **Dynamic agent graph** | Agents spawn specialist sub-agents mid-simulation; orchestrator auto-spawns when gaps are detected |
| **Multi-modal evidence** | Ingest PDF, DOCX, audio (Whisper), video (ffmpeg + Whisper), images |
| **RAG per role** | Each agent retrieves only the evidence its role is permitted to see |
| **Citation system** | Agents cite `[EVIDENCE:uuid:chunk_idx]` inline; frontend renders hoverable chips |
| **Three simulation modes** | Courtroom · Deposition · Strategy session |
| **Multi-LLM** | Mix OpenAI, Anthropic, Gemini, Ollama per agent — or use a single free provider |
| **Any database** | PostgreSQL · MongoDB · SQLite · DynamoDB — swap via one env var |
| **Streaming UI** | Real-time token streaming to the browser via WebSocket |

---

## Architecture overview

```
┌──────────────────────────────────────────────────────────┐
│  Next.js 15 frontend (App Router + shadcn/ui dark theme) │
│  SimulationShell · TurnFeed · react-flow AgentGraph      │
└────────────────────────┬─────────────────────────────────┘
                         │  REST + WebSocket
┌────────────────────────▼─────────────────────────────────┐
│  FastAPI backend                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │ Agent       │  │ Simulation   │  │ RAG Pipeline   │   │
│  │ Orchestrator│  │ Engine       │  │ Embed·Retrieve │   │
│  │ + AgentGraph│  │ (3 modes)    │  │ ·Citation      │   │
│  └─────────────┘  └──────────────┘  └────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Abstraction layer  (all swappable via env vars)    │ │
│  │  LLMProvider · FileStorage · VectorStore · Repo[T]  │ │
│  └─────────────────────────────────────────────────────┘ │
└────────────────────────┬─────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    PostgreSQL /      Qdrant /       Redis +
    MongoDB /         Chroma /       Celery
    SQLite            Pinecone       workers
```

Extended architecture notes: [`docs/architecture.md`](docs/architecture.md)

---

## Quick start — Docker (recommended)

**Requires:** Docker Desktop · Docker Compose v2

```bash
# 1. Clone
git clone https://github.com/your-org/nyayrithm.git
cd nyayrithm

# 2. Create .env from template
make env          # copies .env.example → .env

# 3. Add at least one LLM API key to .env
#    (see "Running locally for free" below for zero-cost option)
nano .env         # or open in your editor

# 4. Start everything
make dev          # postgres + redis + qdrant + minio + keycloak + backend + frontend

# 5. Apply database migrations
make migrate
```

> **First run:** Keycloak takes ~30 seconds to finish importing the realm on first start. The frontend is ready once http://localhost:8080 responds.

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API docs | http://localhost:8000/docs |
| Keycloak admin | http://localhost:8080 (`admin` / `admin`) |
| Qdrant dashboard | http://localhost:6333/dashboard |
| MinIO console | http://localhost:9001 (`minioadmin` / `minioadmin`) |

```bash
make stop    # stop all containers
make clean   # stop + wipe volumes + remove __pycache__
```

---

## Running locally for free with Gemini

Google's Gemini API includes a **free tier** — Gemini 2.0 Flash at 15 RPM and 1.5M tokens/day (as of 2025) — which is more than enough to run complete simulations at zero cost.

### Step 1 — Get a free Gemini API key

1. Visit https://aistudio.google.com/app/apikey
2. Click **Create API key** — no credit card required on the free tier
3. Copy the key (starts with `AIza…`)

### Step 2 — Configure `.env` for a zero-cost stack

```env
# ── LLM: Gemini (free tier) ──────────────────────────────
LLM_DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=AIza...your-key...

# ── Embedder: Sentence Transformers (runs locally) ───────
EMBEDDER_BACKEND=sentence-transformers
EMBEDDING_DIMENSION=384

# ── Database: SQLite (no container needed) ───────────────
DB_BACKEND=sqlite
SQLITE_PATH=./nyayrithm.db

# ── Vector DB: Chroma (in-process, no container) ─────────
VECTOR_DB_BACKEND=chroma
CHROMA_HOST=localhost
CHROMA_PORT=8001

# ── File storage: local filesystem ───────────────────────
STORAGE_BACKEND=local
STORAGE_LOCAL_ROOT=./storage

# ── Task queue: still needs Redis ────────────────────────
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

> **Tip:** If you want zero Docker at all, replace Redis with a simple in-memory broker by setting `CELERY_BROKER_URL=memory://` — fine for dev and single-worker setups.

### Step 3 — Run without Docker

```bash
# Python deps (backend)
cd backend && uv pip install -e ".[dev]"

# Frontend deps
cd ../frontend && bun install

# Terminal 1 — API server
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Terminal 2 — Celery worker
cd backend && uv run celery -A app.tasks.celery_app worker --loglevel=info \
    -Q evidence,simulation,default

# Terminal 3 — Next.js dev server
cd frontend && bun dev
```

Open http://localhost:3000. No cloud accounts, no billing, no containers.

### Recommended Gemini model assignments (free tier)

Edit `backend/app/llm/registry.py`:

```python
ROLE_PROVIDER_MAP = {
    "judge":          ("gemini", "gemini-2.5-flash"),       # best free reasoning
    "prosecutor":     ("gemini", "gemini-2.5-flash"),
    "defense":        ("gemini", "gemini-2.5-flash"),
    "plaintiff":      ("gemini", "gemini-2.5-flash-lite"),  # lightest model
    "accused":        ("gemini", "gemini-2.5-flash-lite"),
    "witness":        ("gemini", "gemini-2.5-flash-lite"),
    "investigator":   ("gemini", "gemini-2.5-flash"),
    "expert_witness": ("gemini", "gemini-2.5-flash"),
    "custom":         ("gemini", "gemini-2.5-flash-lite"),
}
```

> ⚠️ **Gemini 2.0 Flash was deprecated (shut down June 1, 2026).** Use `gemini-2.5-flash` or `gemini-2.5-flash-lite`.

**Free tier quotas (May 2026):**

| Model | Requests/day | Notes |
|-------|-------------|-------|
| Gemini 2.5 Flash | 1,500 | Best reasoning on free tier |
| Gemini 2.5 Flash-Lite | 1,500 | Lightest, good for simple roles |
| Gemini 2.5 Pro | 50 | Very limited — use for judge only |

A typical simulation (20 turns, 6 agents) uses well under 1,500 daily requests.

---

## LLM provider guide

Every agent's LLM provider and model is independently configurable. The defaults live in `backend/app/llm/registry.py` (`ROLE_PROVIDER_MAP`) and can be overridden per-agent in the simulation setup UI.

### OpenAI

```env
LLM_DEFAULT_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

| Model | Best for | Cost (approx) |
|-------|---------|--------------|
| `gpt-4o` | Prosecutor, Defense, Investigator | ~$5/1M input tokens |
| `gpt-4o-mini` | Witnesses, Plaintiff, Accused | ~$0.15/1M input tokens |
| `o1-mini` | Judge (strong reasoning) | ~$3/1M input tokens |

### Anthropic (Claude)

```env
LLM_DEFAULT_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

| Model | Best for | Cost (approx) |
|-------|---------|--------------|
| `claude-opus-4-5` | Judge (complex legal reasoning) | ~$15/1M input tokens |
| `claude-sonnet-4-6` | Prosecutor, Defense, Expert Witness | ~$3/1M input tokens |
| `claude-haiku-4-5-20251001` | Witnesses, Plaintiff, Accused | ~$0.25/1M input tokens |

### Gemini (Google)

```env
LLM_DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=AIza...
```

Recommended free models: `gemini-2.5-flash` (best reasoning) · `gemini-2.5-flash-lite` (lightest).
See [Running locally for free with Gemini](#running-locally-for-free-with-gemini) and [`docs/llm-providers.md`](docs/llm-providers.md).

### Ollama — fully local, offline

Run open-weight models on your own hardware. No API key, no cost, full data privacy.

```bash
# Install Ollama from https://ollama.com
ollama pull llama3.1:8b       # good balance for most roles
ollama pull llama3.1:70b      # best quality if you have the VRAM
ollama pull mistral-nemo      # lightweight alternative
ollama serve                  # starts server at http://localhost:11434
```

```env
LLM_DEFAULT_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

```python
# registry.py — Ollama example
ROLE_PROVIDER_MAP = {
    "judge":      ("ollama", "llama3.1:70b"),  # 64 GB RAM recommended
    "prosecutor": ("ollama", "llama3.1:8b"),
    "defense":    ("ollama", "llama3.1:8b"),
    "witness":    ("ollama", "mistral-nemo"),
    ...
}
```

**Minimum hardware:** 16 GB RAM for 8B models · 64 GB RAM for 70B models · GPU strongly recommended for 70B.

### Mixing providers across roles

```python
# registry.py — example mixed setup
ROLE_PROVIDER_MAP = {
    "judge":          ("anthropic", "claude-opus-4-5"),   # premium reasoning
    "prosecutor":     ("openai",    "gpt-4o"),
    "defense":        ("openai",    "gpt-4o"),
    "plaintiff":      ("gemini",    "gemini-2.5-flash"),   # free
    "accused":        ("gemini",    "gemini-2.5-flash"),   # free
    "witness":        ("ollama",    "llama3.1:8b"),         # local
    "investigator":   ("openai",    "gpt-4o"),
    "expert_witness": ("anthropic", "claude-sonnet-4-6"),
    "custom":         ("gemini",    "gemini-2.5-flash-lite"),
}
```

---

## Embedder options

The embedder converts evidence text into vector representations used by the RAG retriever.

| `EMBEDDER_BACKEND` | Model | Dim | Cost | Notes |
|-------------------|-------|-----|------|-------|
| `openai` | `text-embedding-3-small` | 1536 | ~$0.02/1M tokens | Default; best quality |
| `openai` | `text-embedding-3-large` | 3072 | ~$0.13/1M tokens | Higher quality |
| `gemini` | `text-embedding-004` | 768 | Free tier available | Good multilingual |
| `cohere` | `embed-multilingual-v3.0` | 1024 | Free trial | Best multilingual |
| `sentence-transformers` | `all-MiniLM-L6-v2` | 384 | Free / local | No internet required |
| `local` | any Hugging Face model | varies | Free / local | Fully offline |

**For the fully-free stack:**

```env
EMBEDDER_BACKEND=sentence-transformers
EMBEDDING_DIMENSION=384
```

Runs on CPU, no API key. Quality is slightly below OpenAI embeddings but fully adequate for most case sizes (< 500 chunks).

---

## Configuration reference

Copy `.env.example` → `.env` then edit. All settings load through `backend/app/config.py`.

### App

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | `development` · `staging` · `production` |
| `SECRET_KEY` | — | Long random string for JWT signing |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed frontend origins (JSON array) |
| `DEBUG` | `true` | Enables verbose logging and error details |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_BACKEND` | `postgres` | `postgres` · `mongodb` · `sqlite` · `dynamodb` |
| `DATABASE_URL` | postgres local | asyncpg connection string (postgres only) |
| `SQLITE_PATH` | `./nyayrithm.db` | SQLite file path (sqlite only) |
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DB` | `nyayrithm` | MongoDB database name |
| `DYNAMODB_REGION` | `us-east-1` | AWS region (dynamodb only) |

### Vector database

| Variable | Default | Description |
|----------|---------|-------------|
| `VECTOR_DB_BACKEND` | `qdrant` | `qdrant` · `chroma` · `pinecone` · `pgvector` |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `QDRANT_API_KEY` | — | Qdrant Cloud API key (leave blank for local) |
| `CHROMA_HOST` | `localhost` | Chroma host |
| `CHROMA_PORT` | `8001` | Chroma port |
| `PINECONE_API_KEY` | — | Pinecone API key |

### File storage

| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_BACKEND` | `local` | `local` · `s3` · `minio` · `gcs` · `azure_blob` |
| `STORAGE_LOCAL_ROOT` | `./storage` | Directory for local file storage |
| `S3_BUCKET` | `nyayrithm-evidence` | S3 bucket name |
| `S3_ENDPOINT_URL` | — | Override for MinIO (`http://localhost:9000`) |

### LLM

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_DEFAULT_PROVIDER` | `openai` | `openai` · `anthropic` · `gemini` · `ollama` |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `GEMINI_API_KEY` | — | Google AI Studio API key |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server (local) |

### Embedder

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDER_BACKEND` | `openai` | `openai` · `gemini` · `cohere` · `sentence-transformers` · `local` |
| `EMBEDDING_DIMENSION` | `1536` | Must match your chosen embedder's output dimension |
| `COHERE_API_KEY` | — | Cohere API key |

### Task queue / cache

| Variable | Default | Description |
|----------|---------|-------------|
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | Celery result store |
| `REDIS_URL` | `redis://localhost:6379/2` | App-level cache |

### Auth / Keycloak

| Variable | Default | Description |
|----------|---------|-------------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT expiry (24 hours) |
| `NEXT_PUBLIC_KEYCLOAK_URL` | `http://localhost:8080` | Browser-facing Keycloak URL |
| `KEYCLOAK_URL` | `http://localhost:8080` | Server-side URL (Docker: `http://keycloak:8080`) |
| `NEXT_PUBLIC_KEYCLOAK_REALM` | `nyayrithm` | Keycloak realm name |
| `NEXT_PUBLIC_KEYCLOAK_CLIENT_ID` | `nyayrithm-app` | Keycloak client (Direct Access Grants enabled) |
| `KEYCLOAK_ADMIN_USER` | `admin` | Keycloak master-realm admin (server-side only) |
| `KEYCLOAK_ADMIN_PASS` | `admin` | Keycloak master-realm admin password |

> **Two-URL pattern:** `NEXT_PUBLIC_KEYCLOAK_URL` is the browser-facing URL; `KEYCLOAK_URL` is used server-side by Next.js API routes. Inside Docker, `KEYCLOAK_URL` must be `http://keycloak:8080` (the Docker service name). For `bun dev` outside Docker, both point to `http://localhost:8080`. The `make env` command creates `frontend/.env.local` with the correct local values automatically.

> **`NEXT_PUBLIC_DEV_MODE=true`** — set this in `.env` to bypass authentication entirely in local dev (no Keycloak required).

---

## API reference

Interactive docs: **http://localhost:8000/docs** (Swagger UI) · **http://localhost:8000/redoc**

### Cases

```
POST   /api/v1/cases/                    Create a case
GET    /api/v1/cases/                    List cases (paginated)
GET    /api/v1/cases/{id}                Get case detail
PUT    /api/v1/cases/{id}                Update case
DELETE /api/v1/cases/{id}                Delete case
GET    /api/v1/cases/{id}/summary        AI-generated case summary
```

### Evidence

```
POST   /api/v1/cases/{id}/evidence/             Upload evidence file (multipart)
GET    /api/v1/cases/{id}/evidence/             List evidence
GET    /api/v1/cases/{id}/evidence/{ev_id}      Get evidence + processing status
DELETE /api/v1/cases/{id}/evidence/{ev_id}      Delete + de-index from vector store
POST   /api/v1/cases/{id}/evidence/{ev_id}/reindex  Re-ingest with current embedder
GET    /api/v1/cases/{id}/evidence/{ev_id}/chunks   Retrieve stored chunks
POST   /api/v1/cases/{id}/search                Semantic search across all evidence
```

Evidence `status` lifecycle: `pending` → `processing` → `indexed` | `error`

### Simulations

```
POST   /api/v1/cases/{id}/simulations/          Create simulation + define agents
GET    /api/v1/cases/{id}/simulations/          List simulations for a case
GET    /api/v1/simulations/{sim_id}             Get simulation state + turn count
POST   /api/v1/simulations/{sim_id}/start       Start (dispatches Celery background task)
POST   /api/v1/simulations/{sim_id}/pause       Pause after current turn completes
POST   /api/v1/simulations/{sim_id}/stop        Stop + mark as completed
GET    /api/v1/simulations/{sim_id}/agents      List all agents (predefined + spawned)
POST   /api/v1/simulations/{sim_id}/agents      Add a predefined agent before start
GET    /api/v1/simulations/{sim_id}/turns       Turn history (paginated, newest first)
PATCH  /api/v1/simulations/{sim_id}/turns/{id}  Human override of a turn's content
GET    /api/v1/simulations/{sim_id}/graph       Agent graph (nodes + edges for react-flow)
```

### Agents

```
GET    /api/v1/agents/{agent_id}           Get agent definition + LLM config
GET    /api/v1/agents/{agent_id}/memory    Current memory state (short-term + case)
DELETE /api/v1/agents/{agent_id}/memory    Clear agent memory
GET    /api/v1/agents/roles/               List all roles + their default LLM assignments
GET    /api/v1/agents/providers/           List configured and available LLM providers
```

---

## WebSocket events

Connect: `ws://localhost:8000/ws/simulations/{sim_id}`

```typescript
type WsEvent =
  | { type: "turn.started";        turn_number: number; agent_id: string; agent_name: string; role: string }
  | { type: "turn.token";          agent_id: string; token: string }          // streaming delta
  | { type: "turn.completed";      turn_number: number; agent_id: string; content: string; citations: Citation[]; spawned_agents: string[] }
  | { type: "agent.spawned";       agent_id: string; role: string; name: string; parent_id: string | null; reason: string; auto: boolean }
  | { type: "conflict.detected";   agent_id: string; conflicting_agent_id: string; evidence_ids: string[] }
  | { type: "simulation.paused";   turn_number: number }
  | { type: "simulation.completed"; total_turns: number }
  | { type: "error";               message: string }
```

The frontend Zustand store (`frontend/src/store/simulationStore.ts`) handles all event types via `handleWsEvent()` — plugging a new UI consumer in is a matter of subscribing to the store slice.

---

## Extending the platform

### Add a new LLM provider

1. Create `backend/app/llm/myprovider.py` implementing `LLMProvider` (see `app/llm/base.py`):

```python
class MyProvider:
    provider_name = "myprovider"

    def __init__(self, model: str, api_key: str): ...

    @property
    def model_name(self) -> str: return self._model

    async def complete(self, messages, temperature=0.7, max_tokens=2048, **kw) -> LLMResponse: ...

    async def stream(self, messages, temperature=0.7, max_tokens=2048, **kw) -> AsyncIterator[str]: ...
```

2. Register in `backend/app/llm/registry.py`:

```python
from app.llm.myprovider import MyProvider
register_provider("myprovider", MyProvider)
```

3. Add `MYPROVIDER_API_KEY` to `Settings` in `config.py` and to `.env.example`.
4. Set `LLM_DEFAULT_PROVIDER=myprovider` in `.env`.

### Add a new embedder

1. Implement `Embedder` protocol in `backend/app/rag/embedder.py`
2. Register in `backend/app/rag/embedder_factory.py`
3. Set `EMBEDDER_BACKEND=myembedder` and `EMBEDDING_DIMENSION=<dim>` in `.env`

### Add a new database backend

1. Create `backend/app/db/adapters/mybackend.py` extending `BaseRepository`
2. Add to `get_repository()` factory in `backend/app/db/factory.py`
3. Set `DB_BACKEND=mybackend` in `.env`

### Add a new vector store

1. Create `backend/app/vector_db/mystore.py` implementing `VectorStore` protocol
2. Register in `backend/app/vector_db/factory.py`
3. Set `VECTOR_DB_BACKEND=mystore` in `.env`

---

## Development commands

```bash
make dev              # Start full Docker stack (build if needed)
make stop             # Stop all containers
make logs             # Follow backend + celery worker logs
make migrate          # Run pending Alembic migrations
make migrate-down     # Roll back one migration
make migrate-create   # Create new migration (prompts for name)

make run-backend      # Backend only (uvicorn --reload, no Docker)
make run-worker       # Celery worker only
make run-frontend     # Next.js dev server only

make lint             # ruff + mypy (backend) · eslint + tsc (frontend)
make test             # pytest with coverage report

make clean            # Stop containers + wipe volumes + remove caches
make tf-plan          # Terraform plan (infra/terraform/environments/dev)
make tf-apply         # Terraform apply
```

---

## Project structure

```
nyayrithm/
├── backend/
│   ├── app/
│   │   ├── agents/          BaseAgent, 8 role classes, AgentGraph, Orchestrator
│   │   ├── api/v1/          REST endpoints (cases, evidence, simulations, agents, turns)
│   │   ├── api/websockets/  Simulation streaming WebSocket
│   │   ├── db/              Repository[T] protocol + Postgres / Mongo / SQLite adapters
│   │   ├── ingestion/       PDF, DOCX, audio, video, image ingesters
│   │   ├── llm/             LLMProvider protocol + OpenAI / Anthropic / Gemini / Ollama
│   │   ├── models/          Plain Python dataclasses (Case, Evidence, Agent, Simulation, Turn)
│   │   ├── rag/             Embedder, Chunker, Indexer, Retriever, CitationParser
│   │   ├── schemas/         Pydantic request/response schemas
│   │   ├── services/        CaseService, EvidenceService, SimulationService
│   │   ├── simulation/      SimulationEngine + courtroom / deposition / strategy modes
│   │   ├── storage/         FileStorage protocol + Local / S3 implementations
│   │   ├── tasks/           Celery tasks (evidence ingestion, simulation runs)
│   │   └── vector_db/       VectorStore protocol + Qdrant / Chroma implementations
│   ├── alembic/             SQL migrations (raw SQL, no ORM)
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/          Login + signup pages (custom forms → Keycloak APIs)
│   │   │   ├── api/auth/        Server-side auth routes (login, register, logout)
│   │   │   ├── dashboard/       Protected dashboard pages
│   │   │   ├── docs/            In-app documentation page
│   │   │   └── page.tsx         Landing page (3D globe, agent roles, features)
│   │   ├── components/      SimulationShell, TurnFeed, AgentGraph, CitationChip, …
│   │   ├── hooks/           useSimulationSocket, useCases, useEvidence
│   │   ├── lib/             api.ts, ws.ts (WebSocket client with auto-reconnect)
│   │   ├── store/           Zustand stores (simulation, case, ui)
│   │   └── types/           TypeScript types mirroring backend models
│   ├── .env.local           Local dev env (created by `make env` — git-ignored)
│   └── middleware.ts        Protects /dashboard/* via kc_access_token cookie
├── infra/
│   ├── docker/              Dockerfiles + nginx config
│   ├── keycloak/
│   │   └── realm-export.json    Keycloak realm auto-imported on first start
│   └── terraform/           Conditional AWS modules (VPC, RDS, ECS, S3, ElastiCache, …)
├── docs/
│   ├── architecture.md      System design decisions + data flow diagrams
│   ├── llm-providers.md     Full provider configuration guide
│   └── running-locally.md   Step-by-step local dev without Docker
├── .github/workflows/       CI (lint, test, docker build, deploy)
├── docker-compose.yml
├── .env.example
└── Makefile
```