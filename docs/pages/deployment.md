---
title: Deployment
nav_order: 8
permalink: /deployment/
---

# Deployment

Nyayrithm deploys with **Docker Compose**, and only Docker Compose. One host, one
`docker-compose.yml`, one `.env`.

For a laptop, use [Running locally]({{ '/running-locally/' | relative_url }}); the development overlay
adds hot reload, Mailpit and static accounts. This page is about a real deployment.

## What you are deploying

| Service | Port | Public? |
|---|---|---|
| `frontend` (firm portal) | 3000 | yes, behind TLS |
| `admin` (operations console) | 3001 | yes, behind TLS, ideally restricted by IP or VPN |
| `backend` (API and WebSocket) | 8000 | yes, behind TLS |
| `keycloak` | 8080 | yes, behind TLS |
| `db`, `mongo`, `redis`, `qdrant` | internal | **no** |
| `celery_worker`, `migrate` | none | no |

The production compose file publishes only the four web-facing ports. It uses built images, no
bind mounts, no auto-reload, no dev auth and no seeding. Put a TLS-terminating reverse proxy
(Caddy, nginx, Traefik, a cloud load balancer) in front of the four public services.

## Hostnames

Five public hostnames are typical:

| Hostname (example) | Serves | Variable |
|---|---|---|
| `nyayrithm.example.com` | landing page and docs (indexed by search engines) | `NEXT_PUBLIC_MARKETING_URL` |
| `app.example.com` | the firm portal | `APP_URL` |
| `admin.example.com` | the operations console | `ADMIN_URL` |
| `api.example.com` | the API and WebSocket | `API_URL`, `WS_URL` |
| `auth.example.com` | Keycloak | `KEYCLOAK_PUBLIC_URL` |

The landing page and the app can be one deployment with two hostnames (the default) or two
deployments; `NEXT_PUBLIC_APP_URL` decides whether marketing links cross over to the app host.
Leave it unset for a single-host setup.

## Steps

**1. Get the code and configure.**

```bash
git clone https://github.com/Aayush-Joshi-01/nyayrithm.git && cd nyayrithm
cp .env.example .env
```

Fill in `.env`. Every value in the template is required unless marked optional. In
particular:

- `SECRET_KEY`, `POSTGRES_PASSWORD`, `MONGO_PASSWORD`, `KEYCLOAK_ADMIN_PASS`: long, random,
  and unique.
- The five public URLs above.
- At least one LLM key (`GEMINI_API_KEY`, `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`), or point
  at Ollama.
- `SMTP_*`: **required**, so that invitations are delivered.

The backend refuses to start in production if `SECRET_KEY` is the default or any development
switch is on.

**2. Start.**

```bash
docker compose up -d --build
```

This builds the images, starts the data services, runs the database migration, then starts the
backend, the worker and both portals. The first Keycloak start imports the realm from
`keycloak/realm-prod.json`, substituting your `APP_URL` and `ADMIN_URL` into the clients'
redirect URIs.

**3. Create the first platform administrator.** Register an account through the firm portal's
sign-up page (or the Keycloak console), then grant it the operator role:

```bash
make admin-user EMAIL=you@example.com
```

Sign out and in again, then open the admin portal.

**4. Create the first firm.** In the admin portal go to **Firms → New firm**: choose a plan,
the seats, the paid-until date and an invoice reference, and enter the owner's email. They
receive an invitation; when they accept, the firm is live. The default plans (Trial,
Professional, Enterprise) exist from the first start and are edited under **Plans**.

**5. Check health.** The admin portal's **System** page shows each service. Everything should
be green; the Celery row confirms a worker answered.

## Reverse proxy notes

- **WebSocket:** proxy `/ws/` on the API host with upgrade headers. Without it, live
  streaming silently falls back to polling.
- **Uploads:** raise the proxy's body-size limit to at least `MAX_UPLOAD_MB`.
- **Keycloak:** it sits behind a proxy, so it runs with `KC_PROXY_HEADERS=xforwarded`; have the
  proxy send `X-Forwarded-For`, `-Proto` and `-Host`.
- **CORS:** the backend allows the portal origins derived from `APP_URL` and `ADMIN_URL`.

## Keycloak

The realm has two public clients, `nyayrithm-app` and `nyayrithm-admin`, each trusting only its
own portal's URL. Registration is open on the firm portal (people who register but belong to no
firm see a page explaining they need an invitation). Turn registration off in the realm if
you would rather every account be created by invitation only.

## Data and backups

| What | Where | Back up |
|---|---|---|
| Firms, cases, proceedings, audit chain | `pgdata` volume | `pg_dump` of the `nyayrithm` database |
| Keycloak users | the `keycloak` database on the same server | `pg_dump` of the `keycloak` database |
| Turns, extracted text, usage events | `mongodata` volume | `mongodump` |
| Vectors | `qdrantdata` volume | Qdrant snapshots (they can also be rebuilt by re-indexing evidence) |
| Original evidence files | `evidence_storage` volume, or your S3 bucket | volume snapshot or bucket versioning |

Back up Postgres and Mongo together, or at least close in time: turns refer to simulations.
Export the head hash that **verify record** returns and keep it outside these systems if you
want to be able to prove the audit chain was not truncated.

## Updating

```bash
git pull
docker compose up -d --build
```

The `migrate` service runs `alembic upgrade head` on every start. Take a backup first when a
release adds a migration.

## Optional: S3-compatible evidence storage

Set `STORAGE_BACKEND=s3` (or `minio`) with the `AWS_*`/`S3_*` variables. To run MinIO from the
same compose file: `docker compose --profile s3 up -d`.

## Publishing images (optional)

The manual **Publish Images** workflow builds the backend, frontend and admin images and pushes
them to GitHub Container Registry, so a host can pull instead of build. Deployment itself is
still `docker compose`.

## Checklist

- [ ] Every secret in `.env` is changed and unique ([SECURITY.md](https://github.com/Aayush-Joshi-01/nyayrithm/blob/main/SECURITY.md))
- [ ] `APP_ENV=production`, and none of `DEV_AUTH_MODE`, `AUTH_DEV_BYPASS`, `SEED_DEV_DATA` set
- [ ] TLS in front of the four public services; databases not exposed
- [ ] Admin portal restricted by IP or VPN where possible
- [ ] `SMTP_*` configured and a test invitation delivered
- [ ] The first platform admin created, and the default Keycloak admin password changed
- [ ] Backups of Postgres, Mongo and the evidence volume scheduled and tested
- [ ] `https://nyayrithm.example.com/sitemap.xml` and `/robots.txt` resolve
