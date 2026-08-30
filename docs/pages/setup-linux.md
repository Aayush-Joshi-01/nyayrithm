---
title: Linux setup
nav_order: 4
permalink: /setup/linux/
---

# Linux Setup Guide

Step-by-step instructions for running Nyayrithm on Ubuntu 22.04 / 24.04 LTS, Debian 12, Fedora 40+, and Arch Linux.
Default LLM: **Gemini 2.5 Flash** (free tier, no credit card required).

---

## Contents

- [Prerequisites](#prerequisites)
- [Option A: Docker Compose (recommended)](#option-a--docker-compose-recommended)
- [Option B: Native (no Docker)](#option-b--native-no-docker)
- [Option C: Fully offline with Ollama](#option-c--fully-offline-with-ollama)
- [Configuring LLM providers](#configuring-llm-providers)
- [Verify the installation](#verify-the-installation)
- [Systemd service setup (production-like)](#systemd-service-setup-production-like)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Git

**Ubuntu / Debian:**
```bash
sudo apt update && sudo apt install -y git curl wget
```

**Fedora:**
```bash
sudo dnf install -y git curl wget
```

**Arch:**
```bash
sudo pacman -S git curl wget
```

Verify:
```bash
git --version   # 2.43+
```

---

## Option A: Docker Compose (recommended)

The simplest setup, one command starts everything.

### Step 1: Install Docker Engine + Compose plugin

**Ubuntu / Debian (official Docker repo):**
```bash
# Remove old versions
sudo apt remove docker docker-engine docker.io containerd runc 2>/dev/null

# Add Docker's GPG key and repo
sudo apt update
sudo apt install -y ca-certificates gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

**Fedora:**
```bash
sudo dnf install -y dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl start docker && sudo systemctl enable docker
```

**Arch:**
```bash
sudo pacman -S docker docker-compose
sudo systemctl start docker && sudo systemctl enable docker
```

**Post-install, run Docker without sudo:**
```bash
sudo usermod -aG docker $USER
newgrp docker    # apply group change in current shell
```

Verify:
```bash
docker --version          # Docker version 27+
docker compose version    # Docker Compose version v2.30+
docker run hello-world    # confirm it works
```

### Step 2: Install Node.js 24 LTS + Bun

**Ubuntu / Debian (via NodeSource):**
```bash
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt install -y nodejs
```

**Fedora:**
```bash
sudo dnf install -y nodejs   # or use NodeSource: curl -fsSL https://rpm.nodesource.com/setup_24.x | sudo bash -
```

**Arch:**
```bash
sudo pacman -S nodejs npm
```

**Bun (all distros, JS runtime + package manager):**
```bash
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

cp .env.example .env
nano .env    # or: code .env / vim .env
```

Set at minimum:

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

> **Keycloak first-start:** Allow ~30 seconds after `docker compose up` for the `nyayrithm` realm to be imported. Check progress with `docker compose logs keycloak`.

```bash
docker compose down              # stop, keep data
docker compose down -v           # stop + wipe volumes
docker compose logs -f backend   # follow backend logs
```

---

## Option B: Native (no Docker)

All services run natively. Best for development, fastest hot-reload, direct access to all logs.

### Step 1: Install Python 3.13

**Ubuntu 24.04 (ships with 3.12, add 3.13 via deadsnakes PPA):**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.13 python3.13-venv python3.13-dev
```

**Ubuntu 22.04:**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.13 python3.13-venv python3.13-dev python3.13-distutils
```

**Fedora 40+:**
```bash
sudo dnf install -y python3.13
```

**Arch:**
```bash
sudo pacman -S python   # ships current stable (3.13)
```

Verify:
```bash
python3.13 --version   # Python 3.13.x
```

### Step 2: Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env   # add to current shell
```

For permanent PATH setup, add to `~/.bashrc` or `~/.zshrc`:
```bash
echo 'source $HOME/.local/bin/env' >> ~/.bashrc
source ~/.bashrc
```

Verify:
```bash
uv --version   # uv 0.6+
```

### Step 3: Install Node.js 24 LTS + Bun

(Same as Option A, Step 2 above.)

### Step 4: Install Redis

**Ubuntu / Debian:**
```bash
sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server    # start on boot
redis-cli ping    # PONG
```

**Fedora:**
```bash
sudo dnf install -y redis
sudo systemctl start redis
sudo systemctl enable redis
```

**Arch:**
```bash
sudo pacman -S redis
sudo systemctl start redis
sudo systemctl enable redis
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

### Step 8: Run (three terminals)

**Terminal 1, API server:**
```bash
cd nyayrithm/backend
uv run uvicorn app.main:app --reload --port 8000
```

**Terminal 2, Celery worker:**
```bash
cd nyayrithm/backend
uv run celery -A app.tasks.celery_app worker --loglevel=info -Q evidence,simulation,default
```

**Terminal 3, Frontend:**
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
curl -fsSL https://ollama.com/install.sh | sh
```

This installs the `ollama` binary and creates a systemd service.

Verify:
```bash
ollama --version
systemctl status ollama   # should be active (running)
```

### Step 2: Download models

```bash
ollama pull llama3.1:8b       # ~4.7 GB, recommended
ollama pull mistral-nemo      # ~7.1 GB, alternative
# For 70B (needs 64+ GB RAM + good GPU):
# ollama pull llama3.1:70b
```

Models are cached at `~/.ollama/models`.

Verify:
```bash
ollama list    # shows downloaded models
curl http://localhost:11434/api/tags   # JSON list via API
```

### Step 3: Configure `.env`

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

**GPU acceleration:** If you have an NVIDIA GPU, install CUDA and `nvidia-container-toolkit`. Ollama detects CUDA automatically and offloads layers to GPU for significantly faster inference.

```bash
# NVIDIA CUDA setup (Ubuntu)
sudo apt install -y nvidia-cuda-toolkit
# Then restart the ollama service
sudo systemctl restart ollama
```

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

> ⚠️ **Gemini 2.0 Flash was deprecated and shut down June 1, 2026.** Use `gemini-flash-lite-latest` or `gemini-flash-lite-latest` instead.

**Free tier quotas (May 2026):**

| Model | RPD (requests/day) | Notes |
|-------|-------------------|-------|
| `gemini-flash-lite-latest` | 1,500 | Best reasoning on free tier |
| `gemini-flash-lite-latest` | 1,500 | Lightest, good for simple roles |
| `gemini-2.5-pro` | 50 | Very limited, use sparingly |

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

### Ollama (fully local)

```env
LLM_DEFAULT_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

Recommended Ollama models on Linux (NVIDIA GPU):

| VRAM | Model | Notes |
|------|-------|-------|
| 6 GB | `llama3.2:3b`, `phi3:mini` | Minimal quality |
| 8 GB | `mistral-nemo`, `gemma2:9b-q4` | Good |
| 12 GB | `llama3.1:8b` (full precision) | Very good |
| 24 GB | `llama3.1:8b` (fast) + `codellama:13b` | Excellent |
| 80 GB | `llama3.1:70b` | Best open-source |

### Mixing providers

```python
ROLE_PROVIDER_MAP = {
    "judge":          ("anthropic", "claude-opus-4-5"),
    "prosecutor":     ("openai",    "gpt-4o"),
    "defense":        ("openai",    "gpt-4o"),
    "plaintiff":      ("gemini",    "gemini-flash-lite-latest"),    # free
    "accused":        ("gemini",    "gemini-flash-lite-latest"),    # free
    "witness":        ("ollama",    "llama3.1:8b"),          # local GPU
    "investigator":   ("openai",    "gpt-4o-mini"),
    "expert_witness": ("anthropic", "claude-sonnet-4-6"),
    "custom":         ("gemini",    "gemini-flash-lite-latest"),
}
```

---

## Verify the installation

```bash
# Backend health check
curl -s http://localhost:8000/health
# Expected: {"status": "ok", "version": "0.1.0"}

# List available LLM providers
curl -s http://localhost:8000/api/v1/agents/providers/ | python3 -m json.tool

# Frontend
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# Expected: 200
```

### Run the test suite

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

## Systemd service setup (production-like)

For running Nyayrithm as persistent background services (e.g., on a server or home lab), create systemd unit files.

### Backend service

```bash
sudo nano /etc/systemd/system/nyayrithm-backend.service
```

```ini
[Unit]
Description=Nyayrithm FastAPI backend
After=network.target redis.service

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/nyayrithm/backend
EnvironmentFile=/path/to/nyayrithm/.env
ExecStart=/home/YOUR_USERNAME/.local/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Celery worker service

```bash
sudo nano /etc/systemd/system/nyayrithm-worker.service
```

```ini
[Unit]
Description=Nyayrithm Celery worker
After=network.target redis.service

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/nyayrithm/backend
EnvironmentFile=/path/to/nyayrithm/.env
ExecStart=/home/YOUR_USERNAME/.local/bin/uv run celery -A app.tasks.celery_app worker \
    --loglevel=info -Q evidence,simulation,default
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable nyayrithm-backend nyayrithm-worker
sudo systemctl start nyayrithm-backend nyayrithm-worker

# Check status
sudo systemctl status nyayrithm-backend
sudo journalctl -u nyayrithm-backend -f   # follow logs
```

---

## Troubleshooting

### `docker: Got permission denied`

Add your user to the docker group and apply the change:
```bash
sudo usermod -aG docker $USER
newgrp docker
# Or log out and back in
```

### `uv: command not found`

Add uv to PATH:
```bash
echo 'source $HOME/.local/bin/env' >> ~/.bashrc
source ~/.bashrc
```

### Redis `Connection refused`

```bash
sudo systemctl status redis-server    # check status
sudo systemctl start redis-server
redis-cli ping    # should return PONG
```

### Celery worker exits with `billiard` multiprocessing error

Some Linux kernels restrict `fork()` in threads. Use the `solo` pool for development:
```bash
uv run celery -A app.tasks.celery_app worker --pool=solo --loglevel=info \
    -Q evidence,simulation,default
```

For production, use `prefork` (default), this issue only appears in restricted environments.

### Port 8000 already in use

```bash
lsof -i :8000      # find the PID
kill -9 <PID>
```

### `sentence-transformers` fails to install

Install build dependencies first:
```bash
# Ubuntu / Debian
sudo apt install -y build-essential python3.13-dev

# Fedora
sudo dnf install -y gcc python3-devel

# Then retry
uv pip install -e ".[dev]"
```

### `faster-whisper` CUDA errors

If you have CUDA but get errors on audio ingestion:
```bash
# Check CUDA is detected
python3 -c "import torch; print(torch.cuda.is_available())"

# If False, reinstall ctranslate2 with CUDA
uv pip install ctranslate2 --extra-index-url https://download.pytorch.org/whl/cu121
```

For CPU-only mode, set in `.env`:
```env
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
```

### `chroma` import error: `sqlite3` version too low

Chroma requires SQLite 3.35+. Ubuntu 22.04 ships 3.31. Fix:
```bash
# Option 1: use pysqlite3-binary
uv pip install pysqlite3-binary

# Option 2: upgrade to Ubuntu 24.04 (ships sqlite 3.45+)
```

If using `pysqlite3-binary`, set the env variable before starting:
```bash
export CHROMA_SQLITE3_BINARY=1
uv run uvicorn app.main:app --reload --port 8000
```

### `node_modules` error / corrupted install

```bash
# Clear Bun cache and reinstall
rm -rf frontend/node_modules
cd frontend && bun install
```

### Ollama `out of memory` error

Model too large for available RAM/VRAM:
```bash
# Use a quantized smaller version
ollama pull llama3.1:8b-instruct-q4_K_M    # 4-bit quantized, ~4.9 GB
```

Or reduce context size via Modelfile:
```bash
cat <<EOF | ollama create nyayrithm-judge -f -
FROM llama3.1:8b
PARAMETER num_ctx 4096
EOF
```

Then use `nyayrithm-judge` as the model name in `registry.py`.

### Firewall blocking services

```bash
# Allow ports locally (Ubuntu UFW)
sudo ufw allow 8000/tcp comment "Nyayrithm backend"
sudo ufw allow 3000/tcp comment "Nyayrithm frontend"
sudo ufw allow 6333/tcp comment "Qdrant"

# Verify
sudo ufw status
```
