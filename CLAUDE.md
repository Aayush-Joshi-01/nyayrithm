# Nyayrithm — Developer Guide

## What this project is
Multi-modal, agent-driven legal reasoning and courtroom simulation platform. AI agents play legal roles (judge, prosecutor, defense, witnesses, etc.) and simulate realistic court proceedings using evidence ingested from PDFs, audio, video, and other sources.

## Monorepo Layout
```
backend/    FastAPI + Python — all agent/simulation/RAG logic
frontend/   Next.js 15 (App Router) + shadcn/ui — dark UI
infra/      Terraform modules + Docker configs + Keycloak realm
.github/    CI/CD workflows
```

## Quick Start
```bash
make env        # copies .env.example → .env AND creates frontend/.env.local
make dev        # docker compose up --build (postgres, redis, qdrant, minio, keycloak)
make migrate    # run alembic migrations
```
Then open http://localhost:3000 (frontend), http://localhost:8000/docs (API docs), and http://localhost:8080 (Keycloak admin, admin/admin).

> **Note:** Keycloak takes ~30 s on first boot to import the realm. Watch with `docker compose logs -f keycloak`.

## Key Architectural Decisions

### Auth — Keycloak + Custom Frontend
Authentication is handled by **Keycloak 26** (Docker service, port 8080). Users never see the Keycloak UI — login and register pages are built into the frontend and call Keycloak APIs via Next.js server-side API routes.

- `frontend/src/app/api/auth/login/route.ts` — `POST /api/auth/login` → Keycloak Direct Access Grants → sets `kc_access_token` httpOnly cookie
- `frontend/src/app/api/auth/register/route.ts` — `POST /api/auth/register` → Keycloak admin REST API (master realm, admin-cli) → auto-login
- `frontend/src/app/api/auth/logout/route.ts` — `POST /api/auth/logout` → clears cookies
- `frontend/src/middleware.ts` — protects `/dashboard/*` via `kc_access_token` cookie check
- `infra/keycloak/realm-export.json` — realm config auto-imported on first Keycloak start; `nyayrithm-app` client has Direct Access Grants enabled
- Set `NEXT_PUBLIC_DEV_MODE=true` in `.env` to bypass auth in local dev

#### Keycloak URL split — important
Next.js API routes run **server-side inside the `frontend` Docker container**. `localhost:8080` inside that container resolves to the container itself, not Keycloak. Two separate env vars handle this:

| Var | Value (Docker) | Value (local `bun dev`) | Used by |
|---|---|---|---|
| `KEYCLOAK_URL` | `http://keycloak:8080` | `http://localhost:8080` | API routes (server-side) |
| `NEXT_PUBLIC_KEYCLOAK_URL` | `http://localhost:8080` | `http://localhost:8080` | Browser JS only |

`KEYCLOAK_URL` is set directly in `docker-compose.yml` for Docker. For local `bun dev` it comes from `frontend/.env.local` (created by `make env`). API routes always read `KEYCLOAK_URL` first, falling back to `NEXT_PUBLIC_KEYCLOAK_URL`.

### DB Abstraction
Models are **plain Python dataclasses** — not SQLAlchemy ORM. The `Repository[T]` protocol in `app/db/repository_base.py` is implemented by backend-specific adapters (`PostgresRepository`, `MongoRepository`, etc.). Select via `DB_BACKEND` env var.

### Agent System
- `BaseAgent` in `app/agents/base.py` — all agents inherit from this
- Role-specific behavior in `app/agents/roles/` — 8 roles + custom
- `AgentGraph` manages the dynamic spawn graph
- `AgentOrchestrator` controls turn-taking, spawning, conflict detection
- Agents can be **predefined** (user-created) or **AI-spawned** at runtime

### LLM Providers
Each role has a default provider/model in `ROLE_PROVIDER_MAP` (`app/llm/registry.py`). Override per-agent by setting `AgentDefinition.llm_provider` + `.llm_model`. Add new providers by implementing `LLMProvider` protocol and registering in the registry.

### RAG
- Evidence → `EvidenceIngester` (type-matched) → `TextChunker` / `TimeWindowChunker` → `Embedder` → `VectorStore`
- Retrieval is **role-scoped**: witnesses can only retrieve their linked evidence, judges see everything
- Citations use `[EVIDENCE:uuid:chunk_index]` inline markers, parsed by `app/rag/citation.py`

### Infrastructure Flexibility
All service choices are env-var driven (see `.env.example`). Terraform modules are optional — enable/disable per environment in `terraform.tfvars`.

### Frontend Stack
- **Package manager / runtime**: Bun (replaced pnpm — `bun.lock` is the lock file)
- **Fonts**: Inter (body), Playfair Display (serif headings), Cinzel (display/labels) via `next/font/google`
- **Key pages**: `/` landing, `/login`, `/signup`, `/dashboard`, `/docs`
- **UI components**: shadcn/ui in `frontend/src/components/ui/` — includes `cobe-globe-pulse.tsx` (3D globe, `cobe` package)
- **Local env**: `frontend/.env.local` — created by `make env`, read by `bun dev`, gitignored

## Rebuilding a Single Container
```bash
# Remove old image and rebuild only the frontend (e.g. after env var changes):
docker compose stop frontend && docker compose rm -f frontend && docker rmi nyayrithm-frontend -f && docker compose up -d --build frontend

# Tail logs to confirm startup:
docker compose logs -f frontend
```

## Adding a New LLM Provider
1. Create `backend/app/llm/myprovider.py` implementing the `LLMProvider` protocol
2. Add to `PROVIDER_REGISTRY` in `app/llm/registry.py`
3. Set API key in `.env` and add to `Settings.get_api_key()`

## Adding a New Embedder
1. Create class in `backend/app/rag/embedder.py` implementing `Embedder` protocol
2. Register in `backend/app/rag/embedder_factory.py`

## Adding a New DB Backend
1. Create `backend/app/db/adapters/mybackend.py` extending `BaseRepository`
2. Add to `SQL_MAP` / `MONGO_MAP` in `backend/app/db/factory.py`

## Adding a New Vector Store
1. Create `backend/app/vector_db/mystore.py` implementing `VectorStore` protocol
2. Register in `backend/app/vector_db/factory.py`

## WebSocket Events (simulation streaming)
```
turn.started    { turn_number, agent_id, agent_name, role }
turn.token      { agent_id, token }           ← streaming delta
turn.completed  { turn_number, agent_id, content, citations, spawned_agents }
agent.spawned   { agent_id, role, name, parent_id, reason }
simulation.completed / simulation.paused
conflict.detected { agent_id, conflicting_agent_id, evidence_ids }
```

## Running Tests
```bash
cd backend && uv run pytest -v
```

## Linting
```bash
cd backend && uv run ruff check . && uv run mypy app/
cd frontend && bun run lint && bun run tsc --noEmit
# or: make lint && make lint-frontend
```
