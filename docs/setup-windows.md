# Windows Setup Guide

Step-by-step instructions for running Nyayrithm on Windows 10 (21H2+) or Windows 11.
Default LLM: **Gemini 2.5 Flash** (free tier, no credit card required).

---

## Contents

- [Prerequisites](#prerequisites)
- [Option A — Docker Desktop (recommended)](#option-a--docker-desktop-recommended)
- [Option B — Native (no Docker)](#option-b--native-no-docker)
- [Option C — Fully offline with Ollama](#option-c--fully-offline-with-ollama)
- [Configuring LLM providers](#configuring-llm-providers)
- [Verify the installation](#verify-the-installation)
- [Windows-specific tips](#windows-specific-tips)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Windows Subsystem for Linux 2 (WSL2)

WSL2 is required for Redis (no native Windows build) and strongly recommended for the overall dev experience.

Open **PowerShell as Administrator** and run:

```powershell
wsl --install
```

This installs WSL2 with Ubuntu by default. **Restart your PC** when prompted.

After restart, open Ubuntu from the Start menu and complete first-time setup (create a Unix username + password).

Verify:
```powershell
wsl --status
# Should show: Default Version: 2
```

### 2. Git

Download and install from https://git-scm.com/download/win  
Use the default options. Ensure "Git Bash" is included.

Verify:
```powershell
git --version
# git version 2.47+
```

---

## Option A — Docker Desktop (recommended)

The cleanest Windows setup. All services run in containers.

### Step 1 — Install Docker Desktop

1. Download from https://www.docker.com/products/docker-desktop/
2. Run the installer — ensure **"Use WSL2 instead of Hyper-V"** is checked
3. Start Docker Desktop and wait for the green "Engine running" indicator
4. In Docker Desktop → Settings → Resources → WSL Integration → enable your Ubuntu distro

Verify:
```powershell
docker --version
# Docker version 27+
docker compose version
# Docker Compose version v2.30+
```

### Step 2 — Install Node.js 24 LTS

Download the Windows installer from https://nodejs.org (choose **24 LTS**)  
Or use `winget`:
```powershell
winget install OpenJS.NodeJS.LTS
```

Verify:
```powershell
node --version   # v24.x.x
npm --version    # 10+
```

### Step 3 — Install Bun

Bun is the JavaScript runtime and package manager used by Nyayrithm (replaces pnpm/npm).

```powershell
powershell -c "irm bun.sh/install.ps1 | iex"
```

Close and reopen your terminal, then verify:
```powershell
bun --version   # 1.x.x
```

### Step 4 — Clone and configure

```powershell
git clone https://github.com/Aayush-Joshi-01/nyayrithm.git
cd nyayrithm

# Create .env from template
copy .env.example .env
```

Open `.env` in your editor (VS Code, Notepad++, etc.) and set at minimum:

```env
# ── Gemini (free tier — default) ─────────────────────────
LLM_DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=AIza...your-key...   # https://aistudio.google.com/app/apikey

# Leave all other defaults as-is for Docker setup
```

> **Get a free Gemini API key:** Visit https://aistudio.google.com/app/apikey → **Create API key** — no credit card required.

### Step 5 — Start the stack

```powershell
# From the nyayrithm\ directory:
docker compose up --build -d

# Apply database migrations
docker compose exec backend uv run alembic upgrade head
```

> On first run, Docker pulls ~2 GB of images. Subsequent starts take ~10 seconds.

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API docs | http://localhost:8000/docs |
| Keycloak admin | http://localhost:8080 (`admin` / `admin`) |
| Qdrant dashboard | http://localhost:6333/dashboard |
| MinIO console | http://localhost:9001 (minioadmin / minioadmin) |

> **Keycloak first-start:** Allow ~30 seconds after `docker compose up` for Keycloak to import the `nyayrithm` realm. The frontend login/register won't work until this completes.

### Step 6 — Install frontend dependencies (first time only)

```powershell
cd frontend
bun install
```

The Next.js dev server runs inside the `frontend` Docker container — `bun install` is only needed if you want to run it natively outside Docker.

### Stopping and restarting

```powershell
docker compose down          # stop all containers (keeps data)
docker compose down -v       # stop + wipe all volumes (full reset)
docker compose up -d         # restart without rebuilding
docker compose up --build -d # rebuild images + restart
```

---

## Option B — Native (no Docker)

Runs everything directly on Windows + WSL2 (Redis in WSL2, app code on Windows).

### Step 1 — Install Python 3.13

Download from https://www.python.org/downloads/windows/ — choose **Python 3.13.x (64-bit)**

During install:
- ✅ Check **"Add python.exe to PATH"**
- ✅ Check **"Install for all users"** (recommended)

Verify in a new PowerShell window:
```powershell
python --version   # Python 3.13.x
```

### Step 2 — Install uv

`uv` is a fast Python package manager (replaces pip + virtualenv):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen PowerShell, then verify:
```powershell
uv --version   # uv 0.6+
```

### Step 3 — Install Node.js 24 LTS + Bun

```powershell
winget install OpenJS.NodeJS.LTS
powershell -c "irm bun.sh/install.ps1 | iex"
```

### Step 4 — Install Redis via WSL2

Redis has no official native Windows build. Use WSL2 (Ubuntu):

```bash
# Open Ubuntu (WSL2) terminal
sudo apt update && sudo apt install -y redis-server
sudo service redis-server start

# Verify
redis-cli ping    # should print PONG
```

Set Redis to start automatically:
```bash
sudo systemctl enable redis-server
```

Redis listens on `localhost:6379` — accessible from Windows apps because WSL2 bridges the network.

### Step 5 — Install Chroma (optional — replaces Qdrant for simpler setup)

Chroma runs in-process inside the Python backend. No separate install needed — just set:
```env
VECTOR_DB_BACKEND=chroma
```

### Step 6 — Clone and configure

In PowerShell:
```powershell
git clone https://github.com/Aayush-Joshi-01/nyayrithm.git
cd nyayrithm
copy .env.example .env
```

Edit `.env` for native setup:

```env
# ── LLM: Gemini (free tier) ──────────────────────────────
LLM_DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=AIza...your-key...

# ── Embedder: local sentence-transformers ────────────────
EMBEDDER_BACKEND=sentence-transformers
EMBEDDING_DIMENSION=384

# ── DB: SQLite (no container) ────────────────────────────
DB_BACKEND=sqlite
SQLITE_PATH=./nyayrithm.db

# ── Vector DB: Chroma (in-process) ───────────────────────
VECTOR_DB_BACKEND=chroma
CHROMA_HOST=localhost
CHROMA_PORT=8001

# ── Storage: local filesystem ────────────────────────────
STORAGE_BACKEND=local
STORAGE_LOCAL_ROOT=./storage

# ── Task queue: Redis via WSL2 ───────────────────────────
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
REDIS_URL=redis://localhost:6379/2

# ── Frontend ─────────────────────────────────────────────
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Step 7 — Install backend dependencies

```powershell
cd backend
uv pip install -e ".[dev]"
```

### Step 8 — Install frontend dependencies

```powershell
cd ..\frontend
bun install
```

### Step 9 — Run (three terminals)

**Terminal 1 — API server:**
```powershell
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Celery worker:**
```powershell
cd backend
uv run celery -A app.tasks.celery_app worker --loglevel=info -Q evidence,simulation,default
```

**Terminal 3 — Frontend:**
```powershell
cd frontend
bun dev
```

> **Native dev + Keycloak:** Ensure `frontend\.env.local` exists with `KEYCLOAK_URL=http://localhost:8080`. The `make env` command (from Git Bash or WSL2) creates it automatically. You still need Keycloak running — start it with `docker compose up keycloak -d`.

Open http://localhost:3000.

---

## Option C — Fully offline with Ollama

No internet required after initial setup. Uses local LLMs via Ollama.

### Step 1 — Install Ollama

Download the Windows installer from https://ollama.com/download/windows  
Run the installer — Ollama installs as a background service.

Verify:
```powershell
ollama --version
```

### Step 2 — Download models

```powershell
ollama pull llama3.1:8b       # ~4.7 GB — recommended all-rounder
ollama pull mistral-nemo      # ~7.1 GB — good alternative
# For 70B (needs 64+ GB RAM):
# ollama pull llama3.1:70b
```

Models are cached at `%USERPROFILE%\.ollama\models`.

Verify Ollama is running:
```powershell
ollama list    # lists downloaded models
```

### Step 3 — Configure `.env` for offline use

```env
LLM_DEFAULT_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434

EMBEDDER_BACKEND=sentence-transformers
EMBEDDING_DIMENSION=384

DB_BACKEND=sqlite
VECTOR_DB_BACKEND=chroma
STORAGE_BACKEND=local
```

Then follow Steps 7–9 from Option B.

---

## Configuring LLM providers

### Default: Gemini 2.5 Flash (free, recommended)

```env
LLM_DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=AIza...
```

Update `backend/app/llm/registry.py` for best free-tier model assignments:

```python
ROLE_PROVIDER_MAP = {
    "judge":          ("gemini", "gemini-flash-lite-latest"),         # best free reasoning
    "prosecutor":     ("gemini", "gemini-flash-lite-latest"),
    "defense":        ("gemini", "gemini-flash-lite-latest"),
    "plaintiff":      ("gemini", "gemini-flash-lite-latest"),    # lightest / most quota
    "accused":        ("gemini", "gemini-flash-lite-latest"),
    "witness":        ("gemini", "gemini-flash-lite-latest"),
    "investigator":   ("gemini", "gemini-flash-lite-latest"),
    "expert_witness": ("gemini", "gemini-flash-lite-latest"),
    "custom":         ("gemini", "gemini-flash-lite-latest"),
}
```

> ⚠️ **Note:** Gemini 2.0 Flash was deprecated and shut down June 1, 2026. Use `gemini-flash-lite-latest` or `gemini-flash-lite-latest` instead.

**Free tier quotas (May 2026):**

| Model | RPD (requests/day) | Notes |
|-------|-------------------|-------|
| Gemini 2.5 Flash | 1,500 | Best balance |
| Gemini 2.5 Flash-Lite | 1,500 | Lightest, most quota |
| Gemini 2.5 Pro | 50 | Limited free quota |

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

### Mix providers per role

Edit `backend/app/llm/registry.py`:
```python
ROLE_PROVIDER_MAP = {
    "judge":      ("anthropic", "claude-opus-4-5"),     # premium
    "prosecutor": ("openai",    "gpt-4o"),
    "witness":    ("gemini",    "gemini-flash-lite-latest"),     # free
    "accused":    ("ollama",    "llama3.1:8b"),          # local
    ...
}
```

---

## Verify the installation

```powershell
# Check all containers are up (Option A)
docker compose ps

# Check backend health
curl http://localhost:8000/health

# Check backend API docs load
start http://localhost:8000/docs

# Check frontend loads
start http://localhost:3000
```

Expected `curl http://localhost:8000/health` response:
```json
{"status": "ok", "version": "0.1.0"}
```

---

## Windows-specific tips

### Use Windows Terminal

Install from the Microsoft Store — much better than the default console. Set Ubuntu (WSL2) as the default profile for Redis management.

### Path separator

The backend uses Python's `pathlib.Path` throughout, so `/` vs `\` is handled automatically. However, if you set `SQLITE_PATH` or `STORAGE_LOCAL_ROOT` in `.env`, use forward slashes or double backslashes:

```env
SQLITE_PATH=./nyayrithm.db          # ✅ works
STORAGE_LOCAL_ROOT=./storage        # ✅ works
SQLITE_PATH=C:\\Users\\you\\app.db  # ✅ works
SQLITE_PATH=C:\Users\you\app.db     # ❌ backslash escape issue
```

### Firewall prompt

On first run, Windows Firewall may ask for permission for Python and Node. Allow access on private networks.

### File watching (hot reload)

`uvicorn --reload` uses file system events. On Windows, set:
```powershell
$env:WATCHFILES_FORCE_POLLING=true
uv run uvicorn app.main:app --reload --port 8000
```

Or add to `.env`:
```env
WATCHFILES_FORCE_POLLING=true
```

### Long path support (optional)

Some Python packages have deep paths. Enable long path support:
```powershell
# Run as Administrator
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
    -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

---

## Troubleshooting

### `docker: command not found` after installing Docker Desktop

Docker Desktop needs to be started (look for the whale icon in the system tray). Then restart your terminal.

### Redis `Connection refused` (Option B)

Make sure Redis is running in WSL2:
```bash
# In Ubuntu terminal
sudo service redis-server start
redis-cli ping    # should return PONG
```

If WSL2 shuts down between sessions, restart Redis:
```bash
wsl -e bash -c "sudo service redis-server start"
```

### `uv: command not found`

The uv installer adds to PATH, but the change only takes effect in a new terminal window. Close and reopen PowerShell.

### Celery worker `[ERROR] consumer: Cannot connect to redis`

Redis is not reachable. Verify:
```powershell
# From Windows PowerShell
redis-cli -h localhost ping   # if redis-cli is installed
# or
Test-NetConnection -ComputerName localhost -Port 6379
```

### `sentence-transformers` hangs on first run

The model (~90 MB) is downloaded from Hugging Face. If behind a proxy or firewall, set:
```powershell
$env:HF_HUB_URL = "https://hf-mirror.com"  # China mirror, or use a VPN
```

After first download, model is cached at `%USERPROFILE%\.cache\huggingface`.

### Port 8000 already in use

Another process is using port 8000 (common with IIS or other dev servers):
```powershell
netstat -ano | findstr :8000
taskkill /PID <pid> /F
# or change the backend port:
uv run uvicorn app.main:app --reload --port 8001
# update NEXT_PUBLIC_API_URL=http://localhost:8001 in .env
```

### WSL2 network not bridging

If `localhost:6379` isn't reachable from Windows after WSL2 starts:
```powershell
# Get WSL2 IP (should be localhost-bridged in WSL2 by default)
wsl hostname -I
# If not localhost, update CELERY_BROKER_URL to use the WSL2 IP
```

Modern WSL2 (Windows 11 22H2+) uses `--network-mode=mirrored` by default and bridges localhost automatically. Ensure you're on an up-to-date WSL2 build:
```powershell
wsl --update
```
