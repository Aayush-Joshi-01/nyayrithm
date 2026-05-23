# Architecture

This document covers system design decisions, data flow, and the reasoning behind key abstractions in Nyayrithm.

---

## Table of contents

- [System overview](#system-overview)
- [Authentication](#authentication)
- [Data models](#data-models)
- [Repository pattern](#repository-pattern)
- [Agent system](#agent-system)
- [RAG pipeline](#rag-pipeline)
- [Simulation engine](#simulation-engine)
- [WebSocket streaming](#websocket-streaming)
- [Infrastructure flexibility](#infrastructure-flexibility)

---

## System overview

```
Browser
  │
  │  HTTP (REST)           WebSocket (streaming)
  ▼                        ▼
FastAPI ──────────────── /ws/simulations/{id}
  │                        │
  │ async                  │ broadcast_fn
  ▼                        ▼
Services             AgentOrchestrator
  │                    │         │
  │             AgentGraph   turn_processor
  │                    │
  │            BaseAgent.run_turn()
  │               ├── perceive()
  │               ├── retrieve()  ──► VectorStore
  │               ├── respond()   ──► LLMProvider (streaming)
  │               └── maybe_spawn()
  │
  ▼
Repository[T]  ──►  Postgres / MongoDB / SQLite / DynamoDB
  │
  ▼
Celery workers (evidence queue + simulation queue)
  │
  ├── EvidenceIngester → Chunker → Embedder → VectorStore.upsert()
  └── SimulationEngine.run_next_turn()
```

---

## Authentication

Nyayrithm uses **Keycloak 26** as its identity provider. Users never see the Keycloak admin UI — authentication is fully embedded in the Next.js frontend through custom login and registration pages that call Keycloak APIs server-side.

### Flow

```
Browser (login page)
  │  POST /api/auth/login  { email, password }
  ▼
Next.js API Route (server-side, inside Docker)
  │  POST http://keycloak:8080/realms/nyayrithm/protocol/openid-connect/token
  │       grant_type=password, client_id=nyayrithm-app
  ▼
Keycloak 26 (Docker service, port 8080)
  │  returns { access_token, refresh_token, expires_in }
  ▼
Next.js sets httpOnly cookies
  │  kc_access_token  (httpOnly, maxAge=expires_in)
  │  kc_refresh_token (httpOnly, maxAge=30 days)
  ▼
Browser redirects to /dashboard
  │
  │  All subsequent requests include cookies automatically
  ▼
Next.js middleware (src/middleware.ts)
  │  checks kc_access_token cookie exists
  │  redirects to /login if missing
  ▼
Protected pages (/dashboard/*)
```

### Registration flow

```
Browser (signup page)
  │  POST /api/auth/register  { firstName, lastName, email, password }
  ▼
Next.js API Route
  │  1. GET admin token from master realm (admin-cli, KEYCLOAK_ADMIN_USER/PASS)
  │  2. POST /admin/realms/nyayrithm/users  (creates user via Admin REST API)
  │  3. POST token endpoint (auto-login after successful registration)
  ▼
Sets cookies + redirects to /dashboard
```

### Two-URL pattern

The login/register API routes run **server-side inside the Docker network**. Inside Docker, containers reach each other by service name — not `localhost`. This requires two separate Keycloak URL environment variables:

| Variable | Value (Docker) | Value (native `bun dev`) | Used by |
|----------|---------------|--------------------------|---------|
| `NEXT_PUBLIC_KEYCLOAK_URL` | `http://localhost:8080` | `http://localhost:8080` | Browser JS (client-side) |
| `KEYCLOAK_URL` | `http://keycloak:8080` | `http://localhost:8080` | Next.js API routes (server-side) |

`KEYCLOAK_URL` is set in `docker-compose.yml` for the Docker case and in `frontend/.env.local` for native dev (`make env` creates this file automatically).

### Key files

| File | Purpose |
|------|---------|
| `frontend/src/app/api/auth/login/route.ts` | `POST /api/auth/login` — Direct Access Grant → httpOnly cookies |
| `frontend/src/app/api/auth/register/route.ts` | `POST /api/auth/register` — Admin API user creation → auto-login |
| `frontend/src/app/api/auth/logout/route.ts` | `POST /api/auth/logout` — clears cookies |
| `frontend/src/middleware.ts` | Protects `/dashboard/*` via cookie check |
| `infra/keycloak/realm-export.json` | Realm config auto-imported on first Keycloak start |
| `frontend/.env.local` | Local dev env vars (created by `make env`, git-ignored) |

### Dev mode bypass

Set `NEXT_PUBLIC_DEV_MODE=true` in `.env` to skip all authentication checks in local dev. This is useful when Keycloak is not running.

---

## Data models

All models are **plain Python `@dataclass` objects** — no SQLAlchemy ORM, no Beanie, no ODM. This is intentional:

- The application layer is completely decoupled from the storage layer
- The same dataclass can be persisted to PostgreSQL (as rows), MongoDB (as documents), SQLite (as rows with JSON blobs), or DynamoDB (as attribute maps)
- Serialisation/deserialisation is handled entirely inside each `Repository` adapter

### JSON/dict fields

Fields typed as `dict` or `list` are stored differently per backend:

| Backend | Storage |
|---------|---------|
| PostgreSQL | `JSONB` column |
| MongoDB | Native embedded document |
| SQLite | JSON-serialised `TEXT` column |
| DynamoDB | Native `Map` or `List` attribute |

The adapter translates transparently — the application always sees a Python `dict` or `list`.

### UUIDs

IDs are generated at the **application layer** (not the database), using `uuid.uuid4()`. This makes IDs portable across all backends and allows objects to be constructed with a stable ID before they are persisted.

---

## Repository pattern

```
app/db/repository_base.py
    Repository(Protocol[T])       ← structural protocol (type-checking only)
    BaseRepository(Generic[T])    ← concrete base with shared helpers

app/db/adapters/
    postgres.py   PostgresRepository   (SQLAlchemy Core, raw SQL — NOT ORM)
    mongodb.py    MongoRepository      (Motor async pymongo)
    sqlite.py     SQLiteRepository     (aiosqlite)

app/db/factory.py
    get_repository(model, session) → correct adapter based on DB_BACKEND env var
```

### Why SQLAlchemy Core instead of ORM?

The ORM requires models to inherit from `DeclarativeBase`, which couples model definitions to the storage layer. Using SQLAlchemy Core with raw SQL strings:
- Keeps models as pure dataclasses
- Makes the SQL explicit and auditable
- Is straightforward to port to other SQL dialects

### Adding a new backend

Create `app/db/adapters/mybackend.py`:

```python
from app.db.repository_base import BaseRepository
from app.models.case import Case   # any model

class MyBackendRepository(BaseRepository[Case]):
    async def get(self, id: str) -> Case | None: ...
    async def list(self, filters, page, size, order_by) -> tuple[list[Case], int]: ...
    async def create(self, entity: Case) -> Case: ...
    async def update(self, id: str, data: dict) -> Case: ...
    async def delete(self, id: str) -> bool: ...
    async def query(self, raw_query, **kwargs) -> list[Case]: ...
```

Register in `app/db/factory.py` and set `DB_BACKEND=mybackend` in `.env`.

---

## Agent system

### Class hierarchy

```
BaseAgent  (app/agents/base.py)
├── JudgeAgent
├── ProsecutorAgent
├── DefenseAgent
├── PlaintiffAgent
├── AccusedAgent
├── WitnessAgent
├── InvestigatorAgent
└── ExpertWitnessAgent
```

### Turn pipeline

Each call to `BaseAgent.run_turn()` executes five ordered steps:

```
perceive(context)
  ↓  filters TurnContext to agent's knowledge scope
  ↓  returns PerceivedContext with agent-visible turns + query string

retrieve(query, case_id, vector_store)
  ↓  role-scoped vector search (witnesses see only linked evidence, etc.)
  ↓  returns list[SearchResult] with chunk text + citation metadata

respond(perceived, retrieved, stream_callback)
  ↓  builds system prompt (role template + country + jurisdiction + prior statements)
  ↓  calls LLMProvider.stream() — emits tokens via stream_callback for WS broadcast
  ↓  parses [EVIDENCE:uuid:chunk_idx] citation markers from output
  ↓  returns AgentResponse

maybe_spawn(response)
  ↓  role-specific logic decides if a sub-agent should be requested
  ↓  returns list[SpawnRequest] (empty for most turns)

memory.record(perceived, response)
  ↓  ShortTermMemory: appends to sliding window (last 20 turns)
  ↓  CaseMemory: stores claims for has_stated() contradiction checks
```

### Agent memory

`CombinedAgentMemory` is composed of two layers:

| Layer | Storage | Purpose |
|-------|---------|---------|
| `ShortTermMemory` | In-memory `deque` (maxlen=20) | Recent context window formatted as LLM messages |
| `CaseMemory` | Persistent list + keyword index | Long-term claim tracking; `has_stated(claim)` for contradiction detection |

### Agent graph

```
AgentGraph
├── root_agents: list[UUID]          ← predefined agents (is_predefined=True)
├── nodes: dict[UUID, AgentNode]
└── edges: list[AgentEdge]           ← directed: parent → spawned child

spawn_agent(spawn_request, parent_id=None, auto=False)
  → creates AgentDefinition (is_predefined=False, parent_agent_id set)
  → instantiates the correct role class via ROLE_AGENT_MAP
  → inserts into Simulation.turn_order after the parent's next turn
  → returns AgentNode

to_json()
  → serialised for react-flow frontend visualisation
  → also broadcast via agent.spawned WebSocket event
```

**`auto=True`** means the orchestrator initiated the spawn (not an agent's `maybe_spawn()`). This distinction is recorded in `AgentDefinition.spawn_reason` and shown in the frontend graph with a different edge style.

### Orchestrator auto-spawn

`AgentOrchestrator._maybe_auto_spawn()` runs after every turn. It checks:

1. Does the turn content mention forensic keywords (`DNA`, `fingerprint`, `ballistic`, `toxicology`, …)?
2. Is there already an `expert_witness` agent in the graph?

If yes to (1) and no to (2), it auto-spawns an `ExpertWitnessAgent` with a generated persona fitted to the evidence type detected. Additional trigger patterns can be added to `FORENSIC_KEYWORDS` in `orchestrator.py`.

### Role knowledge restrictions

Defined in `app/rag/retriever.py` as `ROLE_KNOWLEDGE_RESTRICTIONS`:

| Role | Restriction |
|------|------------|
| `witness` | Only retrieves evidence in `Evidence.linked_participants` for their agent ID |
| `accused` | Excludes evidence of type `confession` unless they authored it |
| `judge` | No restrictions — sees all evidence |
| `prosecutor` / `defense` | No restrictions — strategy access |
| `investigator` | No restrictions |
| `expert_witness` | Filtered to evidence matching their specialisation domain |

---

## RAG pipeline

### Evidence ingestion flow

```
Evidence file (upload)
  ↓
EvidenceIngester (type-matched via mime_type + evidence_type)
  ├── PDFIngester      → pdfplumber → text + page metadata
  ├── DOCXIngester     → python-docx → text + structure
  ├── AudioIngester    → faster-whisper → transcript + speaker segments
  ├── VideoIngester    → ffmpeg (audio track + keyframes) → transcript + frame metadata
  └── ImageIngester    → PIL/Pillow → raw bytes + EXIF

  ↓
Chunker (modality-aware)
  ├── RecursiveTextChunker  → ~512 tokens, 50-token overlap, paragraph/sentence/word split
  └── TimeWindowChunker     → 30-second windows with 5-second overlap (audio/video)

  ↓
EmbedderRouter (selects embedder based on Evidence.modality)
  ├── text/PDF/DOCX → OpenAIEmbedder / SentenceTransformerEmbedder
  ├── audio → WhisperEmbedder (transcript → text embedder)
  ├── video → GeminiMultimodalEmbedder (frames + transcript)
  └── image → OpenAIVisionEmbedder / GeminiMultimodalEmbedder

  ↓
VectorStore.upsert(collection=case_id, chunks)
  each chunk carries: { text, embedding, modality, evidence_id, chunk_index, metadata }

  ↓
Evidence.status = "indexed"
Evidence.embedder_used = "<backend>"
Evidence.chunk_count = N
```

### Retrieval per turn

```
agent.retrieve(query, case_id)
  ↓
EvidenceRetriever.retrieve_for_agent(role, query, case_id, top_k=5)
  ├── embed query with primary text embedder
  ├── apply role-based filters (linked_participants, exclusions)
  ├── apply modality filter if agent has preference
  ├── VectorStore.search(collection=case_id, query_embedding, top_k, filters)
  └── return list[SearchResult]
        { text, score, evidence_id, chunk_index, evidence_title, modality }
```

### Citation format

Agents are instructed (via system prompt) to cite evidence inline:

```
[EVIDENCE:550e8400-e29b-41d4-a716-446655440000:3]
```

`app/rag/citation.py` parses these with a regex, validates that the UUID and chunk index exist, and stores structured references in `Turn.citations`:

```json
[
  {
    "evidence_id": "550e8400-...",
    "chunk_index": 3,
    "chunk_text": "...",
    "evidence_title": "Forensic report",
    "score": 0.91
  }
]
```

The frontend `CitationChip` component renders these as clickable badges with a hover popover showing the chunk preview.

---

## Simulation engine

### Three modes

| Mode | Turn order | Special rules |
|------|-----------|--------------|
| `courtroom` | Judge → Prosecutor → Defense → Witnesses (cycling) | Judge can interject any turn; objections routed to Judge immediately |
| `deposition` | Questioner ↔ Witness alternation | Two primary agents; others observe |
| `strategy` | Free-form (no fixed order) | No judge; agents spawn sub-agents freely for research |

### Turn lifecycle

```
SimulationEngine.run_next_turn(sim_id)
  ↓
Load Simulation + AgentGraph from DB
  ↓
Determine next agent from turn_order[current_turn % len(turn_order)]
  ↓
Broadcast turn.started event via WebSocket
  ↓
agent.run_turn(context, vector_store, stream_callback)
  (stream_callback emits turn.token events token-by-token)
  ↓
Process SpawnRequests from TurnResult
  ├── graph.spawn_agent(spawn_request, parent_id)
  ├── Persist new AgentDefinition to DB
  └── Broadcast agent.spawned event
  ↓
Check for contradictions (_check_contradiction)
  └── If detected: broadcast conflict.detected, set flag for judge interjection
  ↓
Persist Turn to DB (content, citations, spawned_agents, token_count, latency_ms)
  ↓
Increment Simulation.current_turn, persist
  ↓
Broadcast turn.completed event
```

### Celery background execution

Simulations run as Celery tasks in the `simulation` queue. The WebSocket endpoint handles connection management separately — the Celery task calls `broadcast()` which fan-outs to all connected sockets for that simulation ID via the in-memory connection registry.

For production multi-process deployments, replace the in-memory `_connections` dict in `app/api/websockets/simulation_ws.py` with a Redis pub/sub channel.

---

## WebSocket streaming

```
/ws/simulations/{sim_id}

Connection management:
  _connections: dict[str, list[WebSocket]]
  ↑ keyed by simulation_id

broadcast(sim_id, event_type, payload)
  → asyncio.gather(*[ws.send_json(...) for ws in _connections[sim_id]])

make_broadcast_fn(sim_id)
  → returns async callable passed into AgentOrchestrator
  → orchestrator calls it with ("turn.token", {"token": "..."}) each streaming chunk
```

The frontend `SimulationWebSocket` class (`frontend/src/lib/ws.ts`) implements exponential-backoff reconnection and delivers all events to the Zustand store via a typed listener system.

---

## Infrastructure flexibility

All service choices are driven by environment variables. The abstraction layers ensure application code never imports a specific driver directly — only the factory functions do.

```
app/db/factory.py          get_repository()     → selected by DB_BACKEND
app/vector_db/factory.py   get_vector_store()   → selected by VECTOR_DB_BACKEND
app/storage/factory.py     get_file_storage()   → selected by STORAGE_BACKEND
app/rag/embedder_factory.py get_embedder()      → selected by EMBEDDER_BACKEND
app/llm/factory.py         build_llm_provider() → selected by LLM_DEFAULT_PROVIDER
```

Adding a new option to any category is a three-step process: implement the protocol, register in the factory, add env var support in `config.py`.
