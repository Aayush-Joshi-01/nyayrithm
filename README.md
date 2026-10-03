# Nyayrithm

> Multi-agent courtroom simulation for law firms.
> _"nyay" (justice) + "rithm" (from algorithm)._

A firm uploads the evidence in a matter. A court of AI agents, each playing a legal role with its
own knowledge and its own model, argues it out. **Every claim points back to the passage it came
from, every legal citation is checked, and the whole proceeding is kept on a tamper-evident
record.**

Nyayrithm is a **simulation and preparation tool**. It does not give legal advice, does not
predict outcomes, and its agents can be wrong. Read
[Trust and security](docs/pages/trust-and-security.md) before relying on it.

| | |
|---|---|
| **Project documentation** | <https://aayush-joshi-01.github.io/nyayrithm/> (source in [`docs/`](docs/)) |
| **Landing page and app** | [nyayrithm.aayushjoshi.dev](https://nyayrithm.aayushjoshi.dev) · [nyayrithm.ai.aayushjoshi.dev](https://nyayrithm.ai.aayushjoshi.dev) |
| **Author** | [Aayush Joshi](https://aayushjoshi.dev) · aayushjoshi.dev@gmail.com |
| **License** | [MIT](LICENSE) |

> **Status:** pre-launch.

---

## What it is

- **Argues from your record.** PDFs, Word files, scans, photographs, audio and video are read,
  transcribed and indexed. Each agent retrieves only what its role may know.
- **Plays the whole court.** Judge, prosecutor, defence, plaintiff, accused, witnesses,
  investigator, expert. Agents can call in specialists mid-hearing; each seat can run on a
  different model (Gemini, OpenAI, Anthropic, or a local Ollama model).
- **Keeps procedure.** Courtroom stages from opening to judgment; an objection hands the floor
  to the judge for a ruling; procedural slips are flagged.
- **Checks its own law.** Statutes, articles and cases cited by agents are verified against a
  jurisdiction pack (a starter Indian pack is bundled). Impossible citations are flagged and the
  agent is told.
- **Leaves a record.** Each turn's provenance is hash-chained; one click verifies it.
- **Built for firms.** Subscriptions, owner/admin/attorney roles, email invitations, case
  sharing, per-firm isolation, plan limits enforced on the server.
- **Operable.** A separate admin portal for firms, plans, subscriptions, users, system health
  and LLMOps (per-call usage, cost estimates, latency, failures, quota use).

Start with the [Product tour](docs/pages/product-tour.md) and [How it works](docs/pages/how-it-works.md).

## Quick start

You need Docker (with Compose) and `make`. Nothing else.

```bash
git clone https://github.com/Aayush-Joshi-01/nyayrithm.git && cd nyayrithm
make env      # creates .env from the development template
# edit .env: set GEMINI_API_KEY (free: https://aistudio.google.com/app/apikey)
make dev      # builds and starts the stack; no login needed
```

| | |
|---|---|
| Firm portal | <http://localhost:3000> |
| Admin portal | <http://localhost:3001> |
| API docs | <http://localhost:8000/docs> |
| Keycloak | <http://localhost:8080> |
| Mailpit (invitation emails) | <http://localhost:8025> |

`make dev` runs in **open** mode (no login in either portal). `make dev-creds` runs with real
Keycloak sign-in and static development accounts, listed on the dev login screens. Both seed a
"Dev Firm" with a sample case. `make reset` wipes all local data and starts fresh.

Details, troubleshooting and per-OS notes: [Running locally](docs/pages/running-locally.md) ·
[Windows](docs/pages/setup-windows.md) · [macOS](docs/pages/setup-macos.md) ·
[Linux](docs/pages/setup-linux.md).

## Architecture in one picture

```
 Firm portal :3000        Admin portal :3001        (Next.js 15)
        \                      /
         v                    v
        FastAPI backend :8000  ----  Celery workers
         |      |        |      |         |
   PostgreSQL  MongoDB  Qdrant  Redis     LLM providers
   (relational, (turns,  (vectors) (queue,  (Gemini, OpenAI,
    audit chain) usage)            events)   Anthropic, Ollama)
         Keycloak (identity)
```

PostgreSQL holds firms, people, plans, cases, proceedings and the audit chain; MongoDB holds
turns, extracted evidence text and LLM usage events; Qdrant holds vectors. Everything runs under
Docker Compose, which is the only deployment mechanism.
See [Architecture](docs/pages/architecture.md).

## Repository layout

```
backend/    FastAPI + Python: API, agents, simulation engine, RAG, legal checks, metering
frontend/   Next.js 15 firm portal (App Router, shadcn/ui, Bun)
admin/      Next.js 15 operations console (separate app, own Keycloak client)
keycloak/   Realm files: realm-prod.json (no users) and realm-dev.json (static dev accounts)
docker/     Container support files
docs/       The project documentation site (GitHub Pages / Jekyll)
.github/    CI and image-publish workflows
```

## Documentation

The rendered site is at <https://aayush-joshi-01.github.io/nyayrithm/>; the sources are in
[`docs/`](docs/):

- **Overview:** [Vision and aims](docs/pages/vision.md) · [Product tour](docs/pages/product-tour.md) · [How it works](docs/pages/how-it-works.md)
- **Platform:** [Core concepts](docs/pages/concepts.md) · [Firms and access](docs/pages/firms-and-access.md) · [Admin portal and LLMOps](docs/pages/admin-and-llmops.md) · [Legal accuracy](docs/pages/legal-accuracy.md) · [Architecture](docs/pages/architecture.md) · [Trust and security](docs/pages/trust-and-security.md)
- **Project:** [Roadmap](docs/pages/roadmap.md) · [FAQ and glossary](docs/pages/faq.md)
- **Guides:** [Running locally](docs/pages/running-locally.md) · [LLM providers](docs/pages/llm-providers.md) · [Deployment](docs/pages/deployment.md)

## Development

```bash
make test             # backend tests (SQLite + in-memory Mongo; no Docker needed)
make lint             # ruff + mypy
make lint-frontend    # firm portal: eslint + tsc
make lint-admin       # admin portal: eslint + tsc
```

The backend suite covers every route and the firm boundary, the legal checks, the audit chain,
metering, entitlements, invitations and a whole simulation with a scripted LLM. See
[CONTRIBUTING.md](CONTRIBUTING.md).

### Extending

| To add | Where |
|---|---|
| An LLM provider | implement `LLMProvider` in `backend/app/llm/`, register it in `registry.py` (it is metered automatically) |
| An embedder | `backend/app/rag/embedder.py`, register in `embedder_factory.py` |
| A vector store | implement `VectorStore` in `backend/app/vector_db/`, register in its factory |
| A jurisdiction pack | a JSON file in `backend/app/legal/packs/` or `LEGAL_PACKS_DIR` ([schema](docs/pages/legal-accuracy.md)) |
| A model (table or collection) | a dataclass in `backend/app/models/`, a repository in `app/db/repositories/` |

## Deploying

Production uses the same Compose file, without the development overlay:
[Deployment](docs/pages/deployment.md).

## Contributing and security

[CONTRIBUTING.md](CONTRIBUTING.md) · [SECURITY.md](SECURITY.md) · [MIT license](LICENSE)
