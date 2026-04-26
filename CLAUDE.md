# Nyayrithm — Developer Guide

## What this project is
Multi-modal, agent-driven legal reasoning and courtroom simulation platform. AI agents play legal roles (judge, prosecutor, defense, witnesses, etc.) and simulate realistic court proceedings using evidence ingested from PDFs, audio, video, and other sources.

## Monorepo Layout
```
backend/    FastAPI + Python — all agent/simulation/RAG logic
frontend/   Next.js 15 (App Router) + shadcn/ui — dark UI
infra/      Terraform modules + Docker configs
.github/    CI/CD workflows
```

## Quick Start
```bash
make env        # copy .env.example → .env (fill in API keys)
make dev        # docker compose up --build (postgres, redis, qdrant, minio)
make migrate    # run alembic migrations
```
Then open http://localhost:3000 (frontend) and http://localhost:8000/docs (API docs).

## Key Architectural Decisions

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
cd frontend && pnpm lint && pnpm tsc --noEmit
```
