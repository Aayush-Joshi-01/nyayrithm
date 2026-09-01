---
title: macOS setup
nav_order: 3
permalink: /setup/macos/
---

# macOS Setup Guide

Step-by-step instructions for running Nyayrithm on macOS 13 Ventura or later (Intel and Apple Silicon).
Default LLM: **Gemini 2.5 Flash** (free tier, no credit card required).

---

## Contents

- [Prerequisites](#prerequisites)
- [Option A: Docker Desktop (recommended)](#option-a--docker-desktop-recommended)
- [Option B: Native (no Docker)](#option-b--native-no-docker)
- [Option C: Fully offline with Ollama](#option-c--fully-offline-with-ollama)
- [Configuring LLM providers](#configuring-llm-providers)
- [Verify the installation](#verify-the-installation)
- [Apple Silicon notes](#apple-silicon-notes)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Homebrew

If not already installed:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the post-install instructions to add Homebrew to your PATH (especially on Apple Silicon, adds `/opt/homebrew/bin`).

Verify:
```bash
brew --version   # Homebrew 4.x
```

### 2. Git

macOS ships with Git, but the Homebrew version is newer:
```bash
brew install git
git --version   # git version 2.47+
```

### 3. Xcode Command Line Tools

Required for native Python extensions:
```bash
xcode-select --install
```

---

## Option A: Docker Desktop (recommended)

### Step 1: Install Docker Desktop

Download from https://www.docker.com/products/docker-desktop/

- **Apple Silicon (M1/M2/M3/M4):** download the **Apple Silicon** `.dmg`
- **Intel Mac:** download the **Intel** `.dmg`

Open the `.dmg`, drag Docker to Applications, launch it, and wait for the status bar icon to show "Docker Desktop is running".

Verify:
```bash
docker --version          # Docker version 27+
docker compose version    # Docker Compose version v2.30+
```

### Step 2: Install Node.js 24 LTS + Bun

```bash
brew install node@24
echo 'export PATH="/opt/homebrew/opt/node@24/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Install Bun (JS runtime + package manager)
curl -fsSL https://bun.sh/install | bash
```

Verify:
```bash
node --version    # v24.x.x
bun --version     # 1.x.x
```

### Step 3: Clone and configure

```bash
git clone https://github.com/Aayush-Joshi-01/nyayrithm.git
cd nyayrithm

# Create .env from template
cp .env.example .env
```

Open `.env` in your editor and set:

```env
# ── Gemini (free tier, default) ─────────────────────────
LLM_DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=AIza...your-key...   # https://aistudio.google.com/app/apikey
```

> **Get a free Gemini API key:** Visit https://aistudio.google.com/app/apikey → **Create API key**: no credit card required.

### Step 4: Start the stack

```bash
docker compose up --build -d

# Apply database migrations
docker compose exec backend uv run alembic upgrade head
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API docs | http://localhost:8000/docs |
| Keycloak admin | http://localhost:8080 (`admin` / `admin`) |
| Qdrant dashboard | http://localhost:6333/dashboard |
| MinIO console | http://localhost:9001 (minioadmin / minioadmin) |

> **Keycloak first-start:** Allow ~30 seconds after `docker compose up` for the `nyayrithm` realm to be imported. The frontend login/register won't work until this completes. Check progress with `docker compose logs keycloak`.

### Stopping and restarting

```bash
docker compose down          # stop, keep data
docker compose down -v       # stop + wipe volumes
docker compose up -d         # restart
docker compose up --build -d # rebuild + restart
docker compose logs -f backend celery_worker   # follow logs
```

---

## Option B: Native (no Docker)

All services run natively on macOS. Best for development, faster hot-reload, no Docker overhead.

### Step 1: Install Python 3.13

```bash
brew install python@3.13
# Add to PATH (Apple Silicon)
echo 'export PATH="/opt/homebrew/opt/python@3.13/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Verify:
```bash
python3.13 --version   # Python 3.13.x
```

### Step 2: Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Close and reopen your terminal, then verify:
```bash
uv --version   # uv 0.6+
```

### Step 3: Install Node.js 24 LTS + Bun

```bash
brew install node@24
echo 'export PATH="/opt/homebrew/opt/node@24/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
curl -fsSL https://bun.sh/install | bash
```

### Step 4: Install Redis

```bash
brew install redis
brew services start redis    # starts Redis and enables auto-start on login
```

Verify:
```bash
redis-cli ping    # PONG
```

### Step 5: Clone and configure

```bash
git clone https://github.com/Aayush-Joshi-01/nyayrithm.git
cd nyayrithm
cp .env.example .env
```

Edit `.env` for native setup:

```env
# ── LLM: Gemini (free tier) ──────────────────────────────
LLM_DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=AIza...your-key...

# ── Embedder: local sentence-transformers ────────────────
EMBEDDER_BACKEND=sentence-transformers
EMBEDDING_DIMENSION=384

# ── DB: SQLite (no container needed) ─────────────────────
DB_BACKEND=sqlite
SQLITE_PATH=./nyayrithm.db

# ── Vector DB: Chroma (in-process, no container) ─────────
VECTOR_DB_BACKEND=chroma
CHROMA_HOST=localhost
CHROMA_PORT=8001

# ── Storage: local filesystem ────────────────────────────
STORAGE_BACKEND=local
STORAGE_LOCAL_ROOT=./storage

# ── Task queue: local Redis ──────────────────────────────
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
REDIS_URL=redis://localhost:6379/2

# ── Frontend ─────────────────────────────────────────────
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Step 6: Install backend dependencies

```bash
cd backend
uv pip install -e ".[dev]"
```

### Step 7: Install frontend dependencies

```bash
cd ../frontend
bun install
```

### Step 8: Run (three terminal tabs)

Open three tabs in Terminal or iTerm2.

**Tab 1, API server:**
```bash
cd nyayrithm/backend
uv run uvicorn app.main:app --reload --port 8000
```

**Tab 2, Celery worker:**
```bash
cd nyayrithm/backend
uv run celery -A app.tasks.celery_app worker --loglevel=info -Q evidence,simulation,default
```

**Tab 3, Frontend:**
```bash
cd nyayrithm/frontend
bun dev
```

> **Native dev + Keycloak:** Ensure `frontend/.env.local` exists. Run `make env` once to create it. You still need Keycloak running, start it with `docker compose up keycloak -d`.

Open http://localhost:3000.

---

## Option C: Fully offline with Ollama

No internet required after initial model download.

### Step 1: Install Ollama

```bash
brew install ollama
```

Or download directly from https://ollama.com/download (macOS `.dmg` app).

### Step 2: Download models

```bash
ollama pull llama3.1:8b       # ~4.7 GB, good balance of speed vs quality
ollama pull mistral-nemo      # ~7.1 GB, alternative
# For Apple Silicon M2/M3/M4 Ultra with enough RAM:
# ollama pull llama3.1:70b    # ~40 GB, best quality
```

### Step 3: Start Ollama server

If you installed via Homebrew:
```bash
ollama serve
```

If you installed the macOS app, Ollama starts automatically and runs in the menu bar.

Verify:
```bash
curl http://localhost:11434/api/tags   # lists downloaded models
```

### Step 4: Configure `.env`

```env
LLM_DEFAULT_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434

EMBEDDER_BACKEND=sentence-transformers
EMBEDDING_DIMENSION=384

DB_BACKEND=sqlite
VECTOR_DB_BACKEND=chroma
STORAGE_BACKEND=local
```

Then follow Steps 6-8 from Option B.

**Recommended Ollama models for Apple Silicon:**

| Chip | Unified Memory | Recommended model |
|------|---------------|-------------------|
| M1/M2 (base) | 8 GB | `mistral-nemo`, `llama3.2:3b` |
| M1/M2 Pro/Max | 16-32 GB | `llama3.1:8b`, `gemma2:9b` |
| M2/M3 Max/Ultra | 64-96 GB | `llama3.1:70b` |
| M4 Max/Ultra | 128 GB+ | `llama3.1:70b` (fast) |

Apple Silicon runs inference entirely on the Neural Engine + GPU, significantly faster than Intel Macs for local models.

---

## Configuring LLM providers

### Default: Gemini 2.5 Flash (free, recommended)

```env
LLM_DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=AIza...
```

Update `backend/app/llm/registry.py`:

```python
ROLE_PROVIDER_MAP = {
    "judge":          ("gemini", "gemini-flash-lite-latest"),
    "prosecutor":     ("gemini", "gemini-flash-lite-latest"),
    "defense":        ("gemini", "gemini-flash-lite-latest"),
    "plaintiff":      ("gemini", "gemini-flash-lite-latest"),   # lightest
    "accused":        ("gemini", "gemini-flash-lite-latest"),
    "witness":        ("gemini", "gemini-flash-lite-latest"),
    "investigator":   ("gemini", "gemini-flash-lite-latest"),
    "expert_witness": ("gemini", "gemini-flash-lite-latest"),
    "custom":         ("gemini", "gemini-flash-lite-latest"),
}
```

> ⚠️ **Gemini 2.0 Flash was deprecated.** Use `gemini-flash-lite-latest` or `gemini-flash-lite-latest` going forward.

**Free tier quotas (May 2026):**

| Model | RPD | Best for |
|-------|-----|---------|
| `gemini-flash-lite-latest` | 1,500 | Most roles, best reasoning on free tier |
| `gemini-flash-lite-latest` | 1,500 | High-frequency simple roles |
| `gemini-2.5-pro` | 50 | Judge only (very limited free quota) |

### OpenAI

```env
LLM_DEFAULT_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

### Anthropic

```env
LLM_DEFAULT_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

### Ollama (local)

```env
LLM_DEFAULT_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

### Mixing providers

```python
# backend/app/llm/registry.py
ROLE_PROVIDER_MAP = {
    "judge":          ("anthropic", "claude-opus-4-5"),
    "prosecutor":     ("openai",    "gpt-4o"),
    "defense":        ("openai",    "gpt-4o"),
    "plaintiff":      ("gemini",    "gemini-flash-lite-latest"),   # free
    "accused":        ("gemini",    "gemini-flash-lite-latest"),   # free
    "witness":        ("ollama",    "llama3.1:8b"),         # local (Apple Silicon)
    "investigator":   ("openai",    "gpt-4o-mini"),
    "expert_witness": ("anthropic", "claude-sonnet-4-6"),
    "custom":         ("gemini",    "gemini-flash-lite-latest"),
}
```

---

## Verify the installation

```bash
# Check all services running
curl -s http://localhost:8000/health
# {"status": "ok", "version": "0.1.0"}

# Open docs in browser
open http://localhost:8000/docs
open http://localhost:3000
```

### Run tests

```bash
cd backend
uv run pytest --cov=app --cov-report=term-missing -v
```

### Run linters

```bash
# Backend
cd backend && uv run ruff check . && uv run mypy app/

# Frontend
cd frontend && bun run lint && bun run tsc --noEmit
```

---

## Apple Silicon notes

### Docker performance

Docker Desktop on Apple Silicon uses a lightweight Linux VM (Virtualization.framework). Performance is excellent, comparable to native speeds for most workloads.

If you encounter `platform: linux/amd64` image compatibility warnings, add to `docker-compose.yml`:
```yaml
services:
  backend:
    platform: linux/arm64   # prefer native ARM images
```

Most images (postgres, redis, qdrant) have native ARM64 builds.

### Homebrew paths

On Apple Silicon, Homebrew installs to `/opt/homebrew` instead of `/usr/local`. If a tool is missing from PATH:

```bash
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Rosetta 2 (if needed)

Some older Python packages may require Rosetta 2 if they lack ARM64 wheels:
```bash
softwareupdate --install-rosetta --agree-to-license
```

This is rarely needed in 2026, most packages have ARM64 wheels.

### faster-whisper on Apple Silicon

Audio transcription via `faster-whisper` uses CoreML acceleration on Apple Silicon automatically when `ctranslate2` detects the chip. Transcription runs 3-5x faster than on Intel.

---

## Troubleshooting

### `brew: command not found`

Homebrew PATH not set. Add to `~/.zshrc` (Apple Silicon):
```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
source ~/.zshrc
```

### Docker containers keep OOM-killing

Docker Desktop defaults to 50% of RAM. Increase in Docker Desktop → Settings → Resources → Memory. For the full stack (postgres + qdrant + minio + backend + frontend), allocate at least 6 GB.

### Port 5432 already in use

You have a local PostgreSQL running. Either stop it or switch to SQLite:
```bash
brew services stop postgresql@16
# or:
DB_BACKEND=sqlite SQLITE_PATH=./nyayrithm.db
```

### Redis `Connection refused`

```bash
brew services list | grep redis   # check if running
brew services restart redis
redis-cli ping                    # should return PONG
```

### `ModuleNotFoundError` on backend start

Virtual environment not activated or deps not installed:
```bash
cd backend
uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload --port 8000
```

Always prefix commands with `uv run`, it automatically activates the project's virtual environment.

### Celery workers not processing tasks

Check broker connectivity:
```bash
cd backend
uv run celery -A app.tasks.celery_app inspect active
```

If that fails, check Redis is up (`redis-cli ping`) and `CELERY_BROKER_URL` in `.env` is correct.

### `sentence-transformers` slow on first run

~90 MB model downloaded on first `embed_text()` call. Cached at `~/.cache/huggingface/hub`. Subsequent runs are instant.

### Frontend `EADDRINUSE: address already in use :::3000`

Another process is on port 3000:
```bash
lsof -ti:3000 | xargs kill -9
bun dev
# or use a different port:
bun dev --port 3001
# update CORS_ORIGINS in .env to include http://localhost:3001
```
