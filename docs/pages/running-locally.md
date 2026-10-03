---
title: Running locally
nav_order: 12
permalink: /running-locally/
---

# Running locally

Everything runs under Docker Compose, including on your laptop. You need Docker (with Compose)
and `make`; you do **not** need Python, Node or a database installed. For per-OS installation
of Docker and the tools, see the [Windows]({{ '/setup/windows/' | relative_url }}),
[macOS]({{ '/setup/macos/' | relative_url }}) and [Linux]({{ '/setup/linux/' | relative_url }}) guides.

## The short version

```bash
git clone https://github.com/Aayush-Joshi-01/nyayrithm.git && cd nyayrithm
make env      # creates .env from the development template
# edit .env: add GEMINI_API_KEY (free at https://aistudio.google.com/app/apikey)
make dev      # builds and starts the stack, no login needed
```

Then open:

| | URL |
|---|---|
| Firm portal | <http://localhost:3000> |
| Admin portal | <http://localhost:3001> |
| API docs | <http://localhost:8000/docs> |
| Keycloak console | <http://localhost:8080> |
| Mailpit (invitation emails) | <http://localhost:8025> |
| Qdrant dashboard | <http://localhost:6333/dashboard> |

The first start takes several minutes: it pulls images, builds the backend and both portals,
and Keycloak imports its realm (about thirty seconds). Watch with
`docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f backend`.

## The two development modes

A development stack runs in one of two authentication modes, for **both portals**.

### Open mode: `make dev`

No login anywhere. Both portals open straight to the dashboard and the API treats token-less
requests as the seeded dev user: the owner of **Dev Firm**, who is also a platform admin. A
banner on both portals says "Development mode · open access". This is the fastest way to
click around.

### Credentials mode: `make dev-creds`

Real sign-in through Keycloak, with static accounts from `keycloak/realm-dev.json` and
`.env.dev`. The development login screens list them and fill the form when you click one.
There is a platform admin (for the admin portal), a firm owner and an attorney (for the firm
portal, in **Dev Firm**). Use this mode to try roles, invitations and the real token flow.

Switching modes just restarts the stack with a different `DEV_AUTH_MODE`:

```bash
make dev-creds     # credentials mode
make dev           # open mode
```

### What gets seeded

With `SEED_DEV_DATA=true` (set by the dev overlay) the backend creates, idempotently:
the default plans, a firm called **Dev Firm** with an active subscription, memberships for the
dev owner and attorney, and a sample case. It runs on every start and changes nothing if
everything is already there.

These accounts and passwords are committed, deliberately, and are for development only. The
backend refuses to start in production with dev authentication or seeding switched on, and the
production compose file never mounts the dev realm.

## Trying the features

1. **A proceeding.** In the firm portal open the sample case, add a text file as evidence,
   create a proceeding (courtroom mode, 12 turns), and start it. Watch it stream.
2. **An invitation.** In credentials mode, sign in as the owner, go to **Team**, invite
   `someone@example.com`. Open Mailpit to read the email, or copy the link shown after you
   send it. Open the link in a private window, register with that address, and accept.
3. **LLMOps.** Run a proceeding, then open the admin portal's **LLMOps** page.
4. **Plans.** In the admin portal, lower **Trial**'s token allowance and watch a firm on it hit
   the pause.

## Configuration

`make env` copies `.env.dev` to `.env` if there is no `.env`. Put secrets (your API key) in
`.env`, never in `.env.dev`. The most useful settings:

| Variable | Meaning |
|---|---|
| `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | At least one, unless you use Ollama. |
| `LLM_DEFAULT_PROVIDER` | Provider used when an agent's own isn't configured. |
| `EMBEDDER_BACKEND` | `gemini`, `openai`, or `sentence-transformers` for fully local embeddings. |
| `SIMULATION_TURN_DELAY_SECONDS` | Pause between turns; keeps free-tier providers under rate limits. |
| `MAX_UPLOAD_MB` | Largest evidence upload. |
| `LEGAL_PACKS_DIR` | Extra jurisdiction packs. |

See [LLM providers]({{ '/llm-providers/' | relative_url }}) for models, free tiers and running with no external calls at all.

## Everyday commands

```bash
make dev            # start (open mode)
make dev-creds      # start (credentials mode)
make stop           # stop, keep data
make logs           # follow backend and worker logs
make migrate        # run database migrations
make reset          # wipe ALL local data and start fresh
make test           # backend test suite
make lint           # ruff + mypy
make lint-frontend  # firm portal lint + typecheck
make lint-admin     # admin portal lint + typecheck
```

### Resetting

`make reset` runs `docker compose down -v` and starts again. That deletes **every** volume:
PostgreSQL (firms, cases, proceedings), MongoDB (turns, evidence text, usage), Qdrant, Redis,
Keycloak (registered users) and uploaded evidence files. Use it when you want a clean slate.

### Rebuilding one service

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build backend
```

## Running tests

The backend suite needs no Docker services and no network:

```bash
cd backend
uv run pytest -v            # unit + API + a full simulation with a scripted LLM
uv run pytest --cov=app     # with coverage
```

It uses a throwaway SQLite database per test (standing in for PostgreSQL), an in-memory
MongoDB double, a locally generated RSA key in place of Keycloak, mocked Celery tasks and
scripted LLMs. Frontend checks:

```bash
cd frontend && bun run lint && bun run tsc --noEmit
cd admin    && bun run lint && bun run tsc --noEmit
```

## Troubleshooting

**The first build is very slow.** The backend image installs ffmpeg and its libraries. Later
builds reuse the cache.

**A page loads but data is missing, or the dashboard shows "We could not reach the server".**
The backend isn't up yet. Check `docker compose ps` and the backend logs; wait for Keycloak's
first import to finish.

**"You are not part of a firm yet".** In credentials mode, you signed in with an account that
isn't in **Dev Firm**. Use one of the listed development accounts, or accept an invitation.

**Login fails in credentials mode.** Keycloak imports the realm only on first start with an
empty volume. If you changed `keycloak/realm-dev.json`, run `make reset`.

**Invitation emails don't arrive.** In development they go to Mailpit, not to a real inbox:
<http://localhost:8025>.

**A simulation stops with "Turn failed" or pauses by itself.** Usually a provider rate limit
or a missing key; the message says which. Resume it. If it says the token allowance is used up,
raise the plan in the admin portal.

**Port already in use.** Something else is on 3000, 3001, 8000, 8080, 5432, 6379, 6333 or
27017. Stop it, or change the published port in `docker-compose.dev.yml`.

**Docker can't pull images (TLS timeout).** A network hiccup reaching Docker Hub; retry.
