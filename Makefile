.PHONY: dev stop migrate migrate-down lint test frontend install-backend install-frontend clean

# ── Development ───────────────────────────────────────────────────────────────

dev:
	@echo "Starting Nyayrithm dev stack..."
	docker compose up --build -d
	@echo "Backend:  http://localhost:8000/docs"
	@echo "Frontend: http://localhost:3000"
	@echo "Qdrant:   http://localhost:6333"
	@echo "MinIO:    http://localhost:9001"

stop:
	docker compose down

logs:
	docker compose logs -f backend celery_worker

# ── Database ──────────────────────────────────────────────────────────────────

migrate:
	cd backend && uv run alembic upgrade head

migrate-down:
	cd backend && uv run alembic downgrade -1

migrate-create:
	@read -p "Migration name: " name; \
	cd backend && uv run alembic revision --autogenerate -m "$$name"

# ── Backend ───────────────────────────────────────────────────────────────────

install-backend:
	cd backend && uv pip install -e ".[dev]"

run-backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

run-worker:
	cd backend && uv run celery -A app.tasks.celery_app worker --loglevel=info -Q evidence,simulation,default

lint:
	cd backend && uv run ruff check . && uv run mypy app/

test:
	cd backend && uv run pytest --cov=app --cov-report=term-missing -v

# ── Frontend ──────────────────────────────────────────────────────────────────

install-frontend:
	cd frontend && bun install

run-frontend:
	cd frontend && bun dev

build-frontend:
	cd frontend && bun run build

lint-frontend:
	cd frontend && bun run lint && bun run tsc --noEmit

# ── Infrastructure ────────────────────────────────────────────────────────────

tf-init:
	cd infra/terraform/environments/dev && terraform init

tf-plan:
	cd infra/terraform/environments/dev && terraform plan

tf-apply:
	cd infra/terraform/environments/dev && terraform apply -auto-approve

# ── Utilities ─────────────────────────────────────────────────────────────────

clean:
	docker compose down -v
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -name "*.pyc" -delete 2>/dev/null || true

env:
	@cp -n .env.example .env && echo ".env created from .env.example" || echo ".env already exists"
