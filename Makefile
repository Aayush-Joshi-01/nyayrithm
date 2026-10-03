.PHONY: dev dev-creds stop reset logs migrate migrate-down lint test env admin-user clean prod-up prod-down \
        install-backend install-frontend install-admin lint-frontend lint-admin

COMPOSE     = docker compose
COMPOSE_DEV = docker compose -f docker-compose.yml -f docker-compose.dev.yml

# ── Development (Docker Compose only) ─────────────────────────────────────────

# Open mode: no login in either portal; the API treats token-less requests as the seeded dev user.
dev: env
	DEV_AUTH_MODE=open $(COMPOSE_DEV) up --build -d
	@$(MAKE) --no-print-directory urls MODE=open

# Credentials mode: real Keycloak login with the static dev accounts (see keycloak/realm-dev.json).
dev-creds: env
	DEV_AUTH_MODE=credentials $(COMPOSE_DEV) up --build -d
	@$(MAKE) --no-print-directory urls MODE=credentials

urls:
	@echo ""
	@echo "Nyayrithm dev stack ($(MODE) auth)"
	@echo "  Firm portal   http://localhost:3000"
	@echo "  Admin portal  http://localhost:3001"
	@echo "  API docs      http://localhost:8000/docs"
	@echo "  Keycloak      http://localhost:8080"
	@echo "  Mailpit       http://localhost:8025   (invite emails)"
	@echo "  Qdrant        http://localhost:6333/dashboard"
	@echo "Keycloak takes ~30 s on first boot to import the realm."

stop:
	$(COMPOSE_DEV) down

logs:
	$(COMPOSE_DEV) logs -f backend celery_worker

# Wipe ALL local data (Postgres, Mongo, Qdrant, Redis, Keycloak, evidence files) and start fresh.
reset:
	$(COMPOSE_DEV) down -v --remove-orphans
	$(MAKE) dev

# ── Production-shaped stack ───────────────────────────────────────────────────

prod-up:
	$(COMPOSE) up -d --build

prod-down:
	$(COMPOSE) down

# ── Database ──────────────────────────────────────────────────────────────────

migrate:
	$(COMPOSE_DEV) run --rm migrate

migrate-down:
	$(COMPOSE_DEV) run --rm migrate alembic downgrade -1

migrate-create:
	@read -p "Migration name: " name; \
	cd backend && uv run alembic revision -m "$$name"

# ── Backend / frontends (native tooling) ──────────────────────────────────────

install-backend:
	cd backend && uv pip install -e ".[dev]"

install-frontend:
	cd frontend && bun install

install-admin:
	cd admin && bun install

lint:
	cd backend && uv run ruff check . && uv run mypy app/

test:
	cd backend && uv run pytest --cov=app --cov-report=term-missing -v

lint-frontend:
	cd frontend && bun run lint && bun run tsc --noEmit

lint-admin:
	cd admin && bun run lint && bun run tsc --noEmit

# ── Utilities ─────────────────────────────────────────────────────────────────

# Grant the platform_admin role to an existing Keycloak user:  make admin-user EMAIL=you@firm.com
admin-user:
	@test -n "$(EMAIL)" || (echo "usage: make admin-user EMAIL=you@example.com" && exit 1)
	$(COMPOSE) run --rm backend python -m scripts.grant_platform_admin "$(EMAIL)"

clean:
	$(COMPOSE_DEV) down -v --remove-orphans
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -name "*.pyc" -delete 2>/dev/null || true

# Creates .env from the dev template (only if missing). Put API keys in .env, not .env.dev.
env:
	@cp -n .env.dev .env && echo ".env created from .env.dev (add your GEMINI_API_KEY)" || echo ".env already exists"
