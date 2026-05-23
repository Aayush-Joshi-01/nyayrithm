# Running Locally

This guide covers every way to run Nyayrithm on your machine — from the full Docker stack down to a completely container-free, zero-cost setup.

---

## Option A — Full Docker stack (simplest)

**Requires:** Docker Desktop (Mac/Windows) or Docker Engine + Compose plugin (Linux)

```bash
git clone https://github.com/your-org/nyayrithm.git
cd nyayrithm

# Create .env and fill in at least one LLM API key
make env
nano .env          # or open in your editor

# Build and start all services
make dev

# Apply DB migrations
make migrate
```

What starts:
- `backend` — FastAPI on port 8000
- `celery_worker` — ingestion + simulation task worker
- `celery_beat` — scheduled tasks
- `frontend` — Next.js dev server on port 3000
- `db` — PostgreSQL 16 on port 5432
- `redis` — Redis 7 on port 6379
- `qdrant` — Qdrant vector DB on port 6333
- `minio` — S3-compatible local storage on ports 9000 / 9001
- `keycloak` — Keycloak 26 identity provider on port 8080

> **Keycloak note:** On first start Keycloak takes ~30 seconds to import the realm. The `nyayrithm` realm and `nyayrithm-app` client are auto-created from `infra/keycloak/realm-export.json`. Admin UI: http://localhost:8080 (`admin` / `admin`).

Open http://localhost:3000.

---

## Option B — Minimal Docker (no local Python/Node needed)

If you only want containers for infra services (DB, Redis, Qdrant) and run app code natively:

```bash
# Start only infrastructure
docker compose up db redis qdrant -d

# Backend
cd backend
uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload --port 8000

# Worker (new terminal)
cd backend
uv run celery -A app.tasks.celery_app worker --loglevel=info \
    -Q evidence,simulation,default

# Frontend (new terminal)
cd frontend
bun install
bun dev
```

---

## Option C — No Docker at all (fully local, zero cost)

The lightest possible setup. Uses SQLite, Chroma (in-process), local file storage, and Gemini free tier (or Ollama for fully offline).

### Prerequisites

| Tool | Install |
|------|---------|
| Python 3.12+ | https://python.org or `pyenv install 3.12` |
| `uv` (fast Python package manager) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js 20+ | https://nodejs.org or `nvm install 20` |
| `bun` (JS runtime + package manager) | `curl -fsSL https://bun.sh/install \| bash` |
| Redis | See below |

**Redis without Docker:**
```bash
# macOS
brew install redis && brew services start redis

# Ubuntu/Debian
sudo apt install redis-server && sudo systemctl start redis

# Windows (WSL2)
sudo apt install redis-server && redis-server --daemonize yes
```

> Redis is needed for Celery. If you want truly zero dependencies, set `CELERY_BROKER_URL=memory://` in `.env` to use an in-memory broker (single-worker, non-persistent — fine for local testing).

### `.env` for Option C

```env
# App
APP_ENV=development
DEBUG=true
SECRET_KEY=local-dev-secret-change-me
CORS_ORIGINS=["http://localhost:3000"]

# DB — SQLite (no container)
DB_BACKEND=sqlite
SQLITE_PATH=./nyayrithm.db

# Vector DB — Chroma (runs in-process)
VECTOR_DB_BACKEND=chroma
CHROMA_HOST=localhost
CHROMA_PORT=8001

# Storage — local filesystem
STORAGE_BACKEND=local
STORAGE_LOCAL_ROOT=./storage

# Task queue
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
REDIS_URL=redis://localhost:6379/2

# LLM — Gemini free tier
LLM_DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=AIza...your-key...

# Embedder — local sentence-transformers (no API key)
EMBEDDER_BACKEND=sentence-transformers
EMBEDDING_DIMENSION=384

# Auth
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Start the app (Option C)

Open three terminals:

**Terminal 1 — API server**
```bash
cd backend
uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Celery worker**
```bash
cd backend
uv run celery -A app.tasks.celery_app worker --loglevel=info \
    -Q evidence,simulation,default
```

**Terminal 3 — Frontend**
```bash
cd frontend
bun install   # first time only
bun dev
```

> **Note:** For native dev (`bun dev` outside Docker), you need `frontend/.env.local` with Keycloak vars. Run `make env` — it creates both `.env` and `frontend/.env.local` automatically.

Open http://localhost:3000.

---

## Option D — Fully offline with Ollama

No internet connection required after initial model download.

### Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows — download installer from https://ollama.com/download
```

### Download models (one-time, needs internet)

```bash
ollama pull llama3.1:8b      # ~4.7 GB — recommended balance
ollama pull mistral-nemo     # ~7.1 GB — alternative
```

### Configure `.env` for offline mode

```env
LLM_DEFAULT_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434

EMBEDDER_BACKEND=sentence-transformers
EMBEDDING_DIMENSION=384

DB_BACKEND=sqlite
VECTOR_DB_BACKEND=chroma
STORAGE_BACKEND=local
```

### Start Ollama + app

```bash
# Terminal 1 — Ollama server
ollama serve

# Terminals 2–4 — same as Option C (backend, worker, frontend)
```

Everything now runs locally. No API keys, no external services, no network calls during simulation.

---

## First run walkthrough

Once the app is running:

### 1. Create a case

Open http://localhost:3000, click **New Case**, fill in:
- Title and description of the legal matter
- Country (e.g. `India`, `United States`, `United Kingdom`)
- Jurisdiction (e.g. `Maharashtra`, `California`, `England and Wales`)
- Legal system (`common_law`, `civil_law`, `sharia`, `hybrid`)

### 2. Upload evidence

Go to the case → Evidence tab. Drag and drop any supported file:
- PDF (court documents, contracts, reports)
- DOCX (written statements, affidavits)
- MP3/WAV/M4A (audio recordings)
- MP4/MOV (video footage)
- JPG/PNG (photographs, exhibits)
- TXT (plain text statements)

The file is sent to Celery for ingestion. Status updates from `pending` → `processing` → `indexed` in real time. Once indexed, chunks are searchable by agents.

### 3. Create a simulation

Click **New Simulation** on the case page:
- Choose a mode: **Courtroom**, **Deposition**, or **Strategy**
- Set max turns (10–50 recommended for local testing)
- Add predefined agents: pick roles, names, personas, and optionally override the LLM provider/model per agent

### 4. Start the simulation

Click **Start**. A WebSocket connection opens and the TurnFeed begins streaming:
- Each agent's turn appears as a role-colored bubble
- Tokens stream in real time as the agent "speaks"
- Evidence citations appear as hoverable chips
- The AgentGraph on the right updates when agents spawn sub-agents

### 5. Intervene (optional)

- Click any turn bubble → **Edit** to override an agent's statement (sets `is_human_override=true`)
- Click **Pause** to pause after the current turn completes
- Click **Resume** to continue

---

## Database migrations

```bash
# Apply all pending migrations
make migrate

# Create a new migration after model changes
make migrate-create
# > Migration name: add_case_verdict_field

# Roll back one migration
make migrate-down
```

Migrations only apply to SQL backends (PostgreSQL and SQLite). MongoDB and DynamoDB are schema-less — collections/tables are created automatically on first write.

---

## Running tests

```bash
# Full test suite with coverage
make test

# Backend tests only
cd backend && uv run pytest -v

# Specific test file
cd backend && uv run pytest tests/test_agents.py -v

# Frontend linting + type check
cd frontend && bun run lint && bun run tsc --noEmit
```

Tests use an in-memory SQLite database and mock LLM/vector store responses — no real API calls are made.

---

## Environment variables cheat sheet

```bash
# Switch to SQLite instantly
DB_BACKEND=sqlite
SQLITE_PATH=./nyayrithm.db

# Switch to Chroma for vector DB
VECTOR_DB_BACKEND=chroma

# Use Gemini for free
LLM_DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=AIza...

# Use local sentence-transformers for embeddings
EMBEDDER_BACKEND=sentence-transformers
EMBEDDING_DIMENSION=384

# Use Ollama for fully offline LLM
LLM_DEFAULT_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

---

## Troubleshooting

### Backend fails to start: `connection refused` to Postgres

You're using `DB_BACKEND=postgres` but PostgreSQL isn't running. Either:
- Run `make dev` to start the Docker stack, or
- Switch to `DB_BACKEND=sqlite` in `.env` for local dev

### Celery worker not processing evidence

Check that the broker is reachable:
```bash
cd backend && uv run celery -A app.tasks.celery_app inspect active
```

If Redis is down: `redis-cli ping` should return `PONG`. Start Redis or use `CELERY_BROKER_URL=memory://`.

### Evidence stuck at `processing`

The Celery worker handles ingestion. Make sure the worker is running (Terminal 2 in the walkthrough above). Check worker logs for errors:
```bash
make logs    # if using Docker
# or check Terminal 2 output
```

### Gemini API rate limit errors (`429`)

You've hit the free tier RPM (15 requests/min). Solutions:
- Reduce simulation speed (add `TURN_DELAY_SECONDS=5` to `.env`)
- Use `gemini-2.5-flash-lite` for simple roles (higher daily request quota)
- Spread agents across multiple providers

### Qdrant collection already exists error

This can happen when restarting after a schema change. Drop and recreate:
```bash
# If using Docker
docker compose exec qdrant ash -c "rm -rf /qdrant/storage/collections/case_*"
docker compose restart qdrant
```

Or switch to `VECTOR_DB_BACKEND=chroma` for local dev.

### `sentence-transformers` slow first run

The model is downloaded on first use (~90 MB). Subsequent runs use the cached model. If you're behind a proxy, set `HF_HUB_OFFLINE=1` after the initial download.

### Frontend can't connect to backend

Ensure `NEXT_PUBLIC_API_URL=http://localhost:8000` is set in `.env`. The Next.js dev server reads this at build time — restart `bun dev` after changing it.

### Login/register returns "Could not reach authentication server" (503)

This usually means Next.js API routes can't reach Keycloak. Check:

1. **Docker setup:** `KEYCLOAK_URL` must be `http://keycloak:8080` (the Docker service name), not `localhost:8080`. This is set automatically in `docker-compose.yml`.
2. **Native dev:** Ensure `frontend/.env.local` exists with `KEYCLOAK_URL=http://localhost:8080`. Run `make env` to create it.
3. **Keycloak not started:** Wait ~30 seconds after `make dev` for Keycloak to finish realm import. Check with `docker compose logs keycloak`.
