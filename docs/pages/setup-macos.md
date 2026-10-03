---
title: macOS setup
nav_order: 14
permalink: /setup/macos/
---

# macOS setup

macOS 13 or later, Intel or Apple silicon. Everything runs in containers, so you need Docker,
Git and `make`.

## 1. Install the tools

With [Homebrew](https://brew.sh):

```bash
brew install --cask docker        # Docker Desktop
brew install git make
```

Open Docker Desktop once and wait until it reports it is running. Under Settings → Resources,
give it at least **4 CPUs and 8 GB of memory**. On Apple silicon, enable *Use Rosetta for
x86_64/amd64 emulation* only if an image you need is Intel-only (the images used here are
multi-architecture).

Check:

```bash
docker --version && docker compose version && git --version && make --version
```

Command Line Tools provide `make` as well; `xcode-select --install` works if you prefer.

## 2. Clone, configure, start

```bash
git clone https://github.com/Aayush-Joshi-01/nyayrithm.git && cd nyayrithm
make env              # creates .env from the development template
open -e .env          # set GEMINI_API_KEY (free key: https://aistudio.google.com/app/apikey)
make dev              # builds and starts everything, no login needed
```

Open the firm portal at <http://localhost:3000> and the admin portal at <http://localhost:3001>.
The first start takes several minutes. Continue with [Running locally]({{ '/running-locally/' | relative_url }})
for the two development modes, what is seeded, and everyday commands.

## macOS specifics

**Port 5000/7000.** Not used here, but if you add services, AirPlay Receiver occupies them.
Ports 3000, 3001, 8000, 8080, 5432, 6379, 6333 and 27017 must be free; find a holder with
`lsof -i :5432`. A Homebrew PostgreSQL on 5432 is the usual culprit: `brew services stop postgresql`.

**File sharing performance.** Bind mounts are fast with the default VirtioFS file sharing
(Docker Desktop → Settings → General). If hot reload feels slow, check it is selected.

**Memory.** If containers are killed with exit code 137, raise Docker's memory limit.

**Running tests without Docker.** The backend tests need only Python 3.11+ and
[uv](https://docs.astral.sh/uv/):

```bash
brew install uv
cd backend && uv run pytest
```

**Using a local model.** Install [Ollama](https://ollama.com/download), pull a model
(`ollama pull llama3.1:8b`), and in `.env` set `LLM_DEFAULT_PROVIDER=ollama` and
`OLLAMA_BASE_URL=http://host.docker.internal:11434`. See [LLM providers]({{ '/llm-providers/' | relative_url }}).

## Stopping and cleaning up

```bash
make stop             # stop, keep data
make reset            # wipe every volume and start fresh
```
