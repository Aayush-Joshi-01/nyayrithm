---
title: Windows setup
nav_order: 13
permalink: /setup/windows/
---

# Windows setup

Windows 10 (22H2) or 11. Everything runs in containers, so the only things to install are Docker,
Git and a way to run `make`.

## 1. Install the tools

**Docker Desktop** with the WSL 2 backend:

```powershell
wsl --install                      # once; reboot when asked
winget install Docker.DockerDesktop
```

Start Docker Desktop and wait until it says it is running. Give it at least **4 CPUs and 8 GB
of memory** (Settings → Resources; with WSL 2 that is the `.wslconfig` file in your user
folder). The backend image is large and Keycloak and MongoDB each want memory.

**Git** and **make**:

```powershell
winget install Git.Git
winget install GnuWin32.Make       # or: choco install make
```

No `make`? Every target is a short `docker compose` command, shown in the
[Makefile](https://github.com/Aayush-Joshi-01/nyayrithm/blob/main/Makefile); you can paste
those instead.

Check:

```powershell
docker --version ; docker compose version ; git --version ; make --version
```

## 2. Clone

Clone into the **Linux file system** if you can (for example inside your WSL distro under
`~/`), because bind-mounted source reloads far faster there than from `C:\`. Cloning to
`C:\` works too.

```powershell
git clone https://github.com/Aayush-Joshi-01/nyayrithm.git
cd nyayrithm
```

Line endings are handled by the repository's `.gitattributes`, so `core.autocrlf=true` is fine.

## 3. Configure and start

```powershell
make env          # creates .env from the development template
notepad .env      # set GEMINI_API_KEY (free key: https://aistudio.google.com/app/apikey)
make dev          # builds and starts everything, no login needed
```

Open the firm portal at <http://localhost:3000> and the admin portal at <http://localhost:3001>.
The first start takes several minutes. Continue with [Running locally]({{ '/running-locally/' | relative_url }})
for the two development modes, what is seeded, and everyday commands.

## Windows specifics

**Docker Desktop must be running** before any `make` target. "error during connect" or
"cannot find the file specified (dockerDesktopLinuxEngine)" means it isn't.

**Ports.** 3000, 3001, 8000, 8080, 5432, 6379, 6333 and 27017 must be free. Find a holder with
`netstat -ano | findstr :5432` and stop it. A locally installed PostgreSQL is the usual cause
for 5432.

**Slow file watching.** If hot reload is slow, move the clone into WSL (`\\wsl$\...`), or run
the stack without the dev overlay and rebuild when you change code.

**Antivirus.** Real-time scanning of the project folder and Docker's data directory can slow
builds dramatically. Exclude both if you can.

**Running tests without Docker.** The backend tests need only Python 3.11+ and
[uv](https://docs.astral.sh/uv/):

```powershell
winget install astral-sh.uv
cd backend ; uv run pytest
```

**Using a local model.** Install [Ollama for Windows](https://ollama.com/download), pull a model
(`ollama pull llama3.1:8b`), and in `.env` set `LLM_DEFAULT_PROVIDER=ollama` and
`OLLAMA_BASE_URL=http://host.docker.internal:11434`. See [LLM providers]({{ '/llm-providers/' | relative_url }}).

## Stopping and cleaning up

```powershell
make stop         # stop, keep data
make reset        # wipe every volume and start fresh
```
