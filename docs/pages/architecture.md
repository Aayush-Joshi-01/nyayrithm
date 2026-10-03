---
title: Architecture
nav_order: 7
permalink: /architecture/
---

# Architecture

How Nyayrithm is built: the services, where data lives, how a request and a proceeding flow
through them, and how the pieces are kept swappable. For *what the system does*, start with
[How it works]({{ '/how-it-works/' | relative_url }}).

---

## Table of contents

- [System overview](#system-overview)
- [Authentication](#authentication)
- [Data stores](#data-stores)
- [Agent system](#agent-system)
- [RAG pipeline](#rag-pipeline)
- [Simulation engine](#simulation-engine)
- [Legal accuracy]({{ '/legal-accuracy/' | relative_url }})
- [WebSocket streaming](#websocket-streaming)
- [Infrastructure flexibility](#infrastructure-flexibility)
- [Frontend & production topology](#frontend--production-topology)
- [Firms, tenancy and metering](#firms-tenancy-and-metering)

---

## System overview

Everything runs as containers under Docker Compose. There is no other deployment mechanism.

```
 Firm portal (Next.js)        Admin portal (Next.js)
  :3000                         :3001
     |  REST + WebSocket          |  REST (platform_admin only)
     v                            v
 +-------------------- FastAPI backend :8000 -----------------------+
 |  routes -> services -> AccessService (firm boundary)             |
 |              |                                                   |
 |              +- cases, evidence, simulations, agents             |
 |              +- orgs, invites, entitlements                      |
 |              +- admin, llmops, system health                     |
 |              +- legal: packs, citation checker, procedure, audit |
 +------+-----------------+------------------+--------------+-------+
        |                 |                  |              |
        v                 v                  v              v
   PostgreSQL          MongoDB            Qdrant        Redis <-> Celery workers
   relational,         documents &        vectors       broker,    evidence ingestion,
   transactional,      events                           event bus  simulation runs
   audit chain
        |
   Keycloak (identity; its own database on the same server)
```

A browser talks only to the two portals and the API. Long-running work (evidence ingestion
and simulation runs) happens in Celery workers; they publish events to Redis, which the API
relays to the browser over a WebSocket.

### Services

| Service | Role |
|---|---|
| `frontend` | Firm portal. Server-side routes sign users in against Keycloak and hand the browser a bearer token. |
| `admin` | Operations console. Own Keycloak client and cookies; only `platform_admin`. |
| `backend` | The API, the live WebSocket, and on startup: Mongo indexes, default plans, optional dev seeding. |
| `celery_worker` | Runs evidence ingestion and whole simulations. |
| `db` | PostgreSQL. Also hosts Keycloak's database. |
| `mongo` | MongoDB. |
| `redis` | Celery broker and the simulation event bus. |
| `qdrant` | Vector store, one collection per case. |
| `keycloak` | Identity provider. |
| `migrate` | One-shot `alembic upgrade head` before the backend starts. |
| `mailpit` (dev) | Catches invitation emails. |
| `minio` (optional, `--profile s3`) | S3-compatible evidence storage. |

### Request path

A request carries a bearer token. `get_current_user` verifies it; `get_org_user` resolves the
user's firm and firm role (from the `X-Org-Id` header, or their only firm); the route calls a
service, and every resource lookup goes through `AccessService`. Services take a `Stores`
object holding both databases and never name a driver.

---

## Authentication

Nyayrithm uses **Keycloak 26** as its identity provider. Users never see the Keycloak admin UI, authentication is fully embedded in the Next.js frontend through custom login and registration pages that call Keycloak APIs server-side.

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

The login/register API routes run **server-side inside the Docker network**. Inside Docker, containers reach each other by service name, not `localhost`. This requires two separate Keycloak URL environment variables:

| Variable | Value (Docker) | Value (native `bun dev`) | Used by |
|----------|---------------|--------------------------|---------|
| `NEXT_PUBLIC_KEYCLOAK_URL` | `http://localhost:8080` | `http://localhost:8080` | Browser JS (client-side) |
| `KEYCLOAK_URL` | `http://keycloak:8080` | `http://localhost:8080` | Next.js API routes (server-side) |

`KEYCLOAK_URL` is set in `docker-compose.yml` for the Docker case and in `frontend/.env.local` for native dev (`make env` creates this file automatically).

### Key files

| File | Purpose |
|------|---------|
| `frontend/src/app/api/auth/login/route.ts` | `POST /api/auth/login`, Direct Access Grant → httpOnly cookies |
| `frontend/src/app/api/auth/register/route.ts` | `POST /api/auth/register`, Admin API user creation → auto-login |
| `frontend/src/app/api/auth/logout/route.ts` | `POST /api/auth/logout`, clears cookies |
| `frontend/src/app/api/auth/token/route.ts` | `GET /api/auth/token`, returns/refreshes the bearer token for the API client |
| `frontend/src/middleware.ts` | Protects `/dashboard/*` via cookie check |
| `backend/app/core/auth.py` | Keycloak JWKS verification (`KeycloakVerifier`) |
| `backend/app/services/access.py` | The firm boundary: who may see which case |
| `infra/keycloak/realm-export.json` | Realm config auto-imported on first Keycloak start |
| `frontend/.env.local` | Local dev env vars (created by `make env`, git-ignored) |

### Backend token verification

The FastAPI backend does not trust the frontend. Every `/api/v1` route, and the simulation WebSocket, requires a Keycloak-issued bearer token, verified in `backend/app/core/auth.py`:

- The token must be **RS256**-signed by a key published in the realm's JWKS (`/realms/nyayrithm/protocol/openid-connect/certs`). Keys are cached and refetched once when an unknown `kid` appears, so key rotation needs no restart. `HS256` and `alg: none` tokens are rejected outright.
- The `iss` claim must be one of the realm URLs derived from `KEYCLOAK_URL` and `NEXT_PUBLIC_KEYCLOAK_URL` (tokens minted from inside Docker carry the internal host, browser-minted ones the public host). Add others with `KEYCLOAK_EXTRA_ISSUERS`.
- Expired tokens are rejected (10 s clock leeway). The `sub` claim identifies the user. The `platform_admin` realm role unlocks the admin API and nothing else: it grants no access to any firm's data.

The browser cannot read the httpOnly cookies, so `GET /api/auth/token` (a Next.js route) returns the access token, refreshing it from the refresh-token cookie when it has expired. `frontend/src/lib/api.ts` attaches it as `Authorization: Bearer …`; the WebSocket sends it as `?token=` because browsers cannot set headers on a socket. A rejected socket is closed with code `4401` (bad token) or `4403` (not your simulation).

**Access.** Cases belong to a firm; simulations, evidence, agents and turns inherit access from their case (`backend/app/services/access.py`). Anything the caller may not see answers `404`, exactly like something that does not exist, so ids cannot be probed. See [Firms and access]({{ '/firms-and-access/' | relative_url }}).

### Dev modes

A development stack has two ways to run, chosen with one variable (`DEV_AUTH_MODE`, set by
`make dev` or `make dev-creds`):

| Mode | Behaviour |
|---|---|
| `open` | No login in either portal. Token-less requests to the API act as the seeded dev owner. |
| `credentials` | Real Keycloak sign-in with the static accounts in `keycloak/realm-dev.json`, listed on the dev login screens. |

The bypass only applies to requests that carry **no** token; a presented but invalid token is
still a 401. With `SEED_DEV_DATA=true` the backend creates "Dev Firm", the default plans, an
active subscription, memberships matching the dev accounts and a sample case, idempotently.
The backend refuses to start with any of these on when `APP_ENV=production`.

---

## Data stores

Data is split by shape across two databases. Both are always on.

| PostgreSQL: relational, transactional | MongoDB: documents, high volume |
|---|---|
| organizations, memberships, invites, plans, subscriptions | `turns`: the full text of each turn, its legal review, procedure review and provenance |
| cases, case sharing, simulations, agent definitions | `evidence_content`: extracted text, transcripts, OCR output, segments |
| evidence rows (file, status, counts) | `llm_usage`: one document per model call |
| usage counters (per firm, per month) | `llm_prices`: operator price overrides |
| the audit hash chain, admin events | |

The reasoning: firms, plans and cases are relational and need constraints and transactions
(a seat count must not race); an audit chain needs an append-only guarantee a trigger can give;
turns, extracted text and usage events are large, schemaless and append-heavy, and are queried by
simulation or by time window. Per-firm monthly counters are kept in Postgres even though raw
usage events are in Mongo, so that quota checks are one indexed row.

Vectors live in Qdrant. Original files live on disk or S3-compatible storage.

### Models are plain dataclasses

All models are **plain Python `@dataclass` objects**: no ORM, no ODM. The application layer is
decoupled from storage, and serialisation is handled inside each repository adapter. IDs are
generated by the application (`uuid4`), so objects can be built before they are saved.

### Repositories and `Stores`

```
app/db/stores.py          Stores(pg: AsyncSession, mongo: Database); get_stores(), open_stores()
app/db/repositories/      one repository per model, split into PG_REPOSITORIES / MONGO_REPOSITORIES
app/db/adapters/          PostgresRepository (SQLAlchemy Core, raw SQL)  |  MongoRepository (Motor)
app/db/factory.py         get_repository(model, stores)  ->  the right adapter for that model
```

`get_repository("turn", stores)` returns a Mongo repository; `get_repository("case", stores)`
returns a Postgres one. Both implement the same protocol (`get`, `list`, `create`, `update`,
`delete`, `delete_where`, `count`), so a service does not know or care which it has. Ordering
follows one convention across both: `"field"` ascends, `"field DESC"` descends, and no
ordering means newest first.

SQLAlchemy *Core* is used rather than the ORM, so models stay pure dataclasses and the SQL is
explicit and auditable.

### Migrations

PostgreSQL schema is managed by Alembic (`backend/alembic/versions`). MongoDB is schemaless;
the backend ensures its indexes at startup. Compose runs the `migrate` service before the
backend.

### Adding a model

Add the dataclass in `app/models/`, register its repository in `app/db/repositories/__init__.py`
under the store that suits it, and (for Postgres) add a migration.

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
  ↓  calls LLMProvider.stream(), emits tokens via stream_callback for WS broadcast
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
| `judge` | No restrictions, sees all evidence |
| `prosecutor` / `defense` | No restrictions, strategy access |
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
Determine next agent
  ├── courtroom / deposition: the procedure engine names the role for this stage
  │   (and hands the floor to the judge after a counsel's objection)
  └── strategy: turn_order[current_turn % len(turn_order)]
  ↓
Build context: stage directive, applicable-law excerpts, any registry correction
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
Review the turn: verify legal citations, check procedure, append audit events
  ↓
Check for contradictions (_check_contradiction)
  └── If detected: broadcast conflict.detected, set flag for judge interjection
  ↓
Persist Turn to DB (content, citations, legal review + procedure in metadata, token_count, latency_ms)
  ↓
Increment Simulation.current_turn, persist
  ↓
Broadcast turn.completed event
```

### Celery background execution

Simulations run as Celery tasks in the `simulation` queue. The WebSocket endpoint handles connection management separately, the Celery task calls `broadcast()` which fan-outs to all connected sockets for that simulation ID via the in-memory connection registry.

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

Service choices are driven by environment variables. Application code never imports a
specific driver; only the factory functions do.

```
app/db/factory.py              get_repository()      by model: PostgreSQL or MongoDB
app/vector_db/factory.py       get_vector_store()    VECTOR_DB_BACKEND (qdrant)
app/storage/factory.py         get_file_storage()    STORAGE_BACKEND (local | s3 | minio)
app/rag/embedder_factory.py    get_embedder()        EMBEDDER_BACKEND (openai | gemini | sentence-transformers | local)
app/llm/factory.py             build_llm_provider()  per agent: openai | anthropic | gemini | ollama
```

Only backends that are actually implemented are accepted: a typo or an unbuilt option fails
at startup, not on the first request. Adding an option is three steps: implement the
protocol, register it in the factory, add its setting to `config.py`.

---

## Frontend & production topology

The frontend is Next.js 15 (App Router) with a hand-built design system, **"The Night Court"**: a dual light/dark theme documented in [`DESIGN.md`](https://github.com/Aayush-Joshi-01/nyayrithm/blob/main/DESIGN.md). Theme is set pre-paint by an inline script (localStorage key `nyay-theme`); all motion is CSS-only, with no animation library.

In production the two surfaces are split across domains, resolved by `frontend/src/lib/site.ts`:

| Env var | Purpose |
|---|---|
| `NEXT_PUBLIC_MARKETING_URL` | Landing + in-app docs, canonical URLs, sitemap, OG tags |
| `NEXT_PUBLIC_APP_URL` | The app (`/login`, `/signup`, `/dashboard`). When set, marketing CTAs point at it absolutely; when unset, everything stays same-origin for local dev. |

See [Deployment]({{ '/deployment/' | relative_url }}) for the full topology, CORS, and Keycloak redirect URIs.

---

## Firms, tenancy and metering

**Tenancy.** A firm is the tenant. `cases`, `simulations` and `evidence` carry an `org_id`.
`AccessService` is the single place the boundary is enforced: a case is visible if it is in
the caller's firm and the caller is an owner or admin, created it, or has it shared with
them. Simulations, evidence, agents and turns inherit from their case. The same service
guards the WebSocket. The platform-admin role is checked separately (`require_platform_admin`)
and grants nothing here.

**Entitlements.** `EntitlementService` reads a firm's subscription and plan and enforces them:
seats on invite and accept, status on create and start, simulations per month on first start,
storage on upload, and the monthly token budget at start **and before every turn** inside the
simulation engine.

**Metering.** `build_llm_provider` wraps every provider in `MeteredLLM`, and
`get_embedder` wraps embedders in `MeteredEmbedder`; vision calls are recorded in
`transcribe_image`. Attribution (firm, user, simulation, agent role) travels in a `ContextVar`
set by the engine, so providers and agents need no changes. Each call becomes an `llm_usage`
document in Mongo and bumps the firm's monthly counter in Postgres. Recording is best-effort
and never fails a turn.

**Invitations.** Created by an owner or admin; a random token whose hash is stored; delivered
by a Celery task over SMTP (Mailpit in development).

For the permission rules see [Firms and access]({{ '/firms-and-access/' | relative_url }});
for the operator side see [Admin portal and LLMOps]({{ '/admin-and-llmops/' | relative_url }}).
