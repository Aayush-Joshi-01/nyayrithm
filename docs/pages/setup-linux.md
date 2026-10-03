---
title: Linux setup
nav_order: 15
permalink: /setup/linux/
---

# Linux setup

Any recent distribution that runs Docker. The examples use Ubuntu/Debian; other distributions
differ only in the package manager.

## 1. Install the tools

**Docker Engine and the Compose plugin**, from Docker's own repository (the distribution
packages are often too old):

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"      # then log out and in
```

**Git and make:**

```bash
sudo apt update && sudo apt install -y git make
```

Check:

```bash
docker --version && docker compose version && git --version && make --version
docker run --rm hello-world
```

You need roughly **4 CPUs and 8 GB of memory** free for the stack.

## 2. Clone, configure, start

```bash
git clone https://github.com/Aayush-Joshi-01/nyayrithm.git && cd nyayrithm
make env              # creates .env from the development template
${EDITOR:-nano} .env  # set GEMINI_API_KEY (free key: https://aistudio.google.com/app/apikey)
make dev              # builds and starts everything, no login needed
```

Open the firm portal at <http://localhost:3000> and the admin portal at <http://localhost:3001>.
The first start takes several minutes. Continue with [Running locally]({{ '/running-locally/' | relative_url }})
for the two development modes, what is seeded, and everyday commands.

## Linux specifics

**Permissions.** If `docker` says *permission denied*, you are not in the `docker` group yet:
log out and back in after `usermod`, or run `newgrp docker`.

**Ports.** 3000, 3001, 8000, 8080, 5432, 6379, 6333 and 27017 must be free: `sudo ss -ltnp | grep :5432`.
A system PostgreSQL service is the usual cause for 5432: `sudo systemctl stop postgresql`.

**Bind mounts and file ownership.** The dev overlay mounts the source tree into containers. If
files created in a container appear owned by root, `sudo chown -R "$USER": .` restores them.

**Memory.** If containers die with exit code 137 the host is out of memory; close other
applications or add swap.

**Firewall.** To reach the stack from another machine, open the ports you need. In development
the databases are published on the host; do not do this on an untrusted network.

**Running tests without Docker.** The backend tests need only Python 3.11+ and
[uv](https://docs.astral.sh/uv/):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
cd backend && uv run pytest
```

**Using a local model.** Install [Ollama](https://ollama.com/download), pull a model
(`ollama pull llama3.1:8b`), and in `.env` set `LLM_DEFAULT_PROVIDER=ollama` and
`OLLAMA_BASE_URL=http://host.docker.internal:11434`. On Linux, containers do not resolve
`host.docker.internal` by default; add `extra_hosts: ["host.docker.internal:host-gateway"]` to
the `backend` and `celery_worker` services, or point `OLLAMA_BASE_URL` at the host's address.
See [LLM providers]({{ '/llm-providers/' | relative_url }}).

## Stopping and cleaning up

```bash
make stop             # stop, keep data
make reset            # wipe every volume and start fresh
```

## Running for real

For a server deployment, see [Deployment]({{ '/deployment/' | relative_url }}): it uses the
production compose file, not `make dev`.
