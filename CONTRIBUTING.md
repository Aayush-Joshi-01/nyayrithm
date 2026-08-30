# Contributing to Nyayrithm

Thanks for taking the time. Nyayrithm is a solo project ([Aayush Joshi](https://aayushjoshi.dev)) and contributions, issues, and questions are all welcome.

## Getting set up

```bash
git clone https://github.com/Aayush-Joshi-01/nyayrithm.git
cd nyayrithm
make env        # .env.example -> .env, and frontend/.env.local
make dev        # postgres, redis, qdrant, minio, keycloak, backend, frontend
make migrate
```

`NEXT_PUBLIC_DEV_MODE=true` (the default in `.env.example`) skips the auth wall so you can work on `/dashboard/*` without Keycloak. Platform-specific notes: [`docs/setup-windows.md`](docs/setup-windows.md) · [`docs/setup-macos.md`](docs/setup-macos.md) · [`docs/setup-linux.md`](docs/setup-linux.md).

## Before you open a PR

```bash
make lint    # ruff + mypy (backend), eslint + tsc (frontend)
make test    # pytest with coverage
```

Both must pass. For frontend changes also run a production build:

```bash
cd frontend && bun run build
```

## Conventions

- **Branch** off `main` (or `feature`); never commit to `main` directly.
- **Commits** follow Conventional Commits: `feat(frontend): …`, `fix(api): …`, `chore: …`, `docs: …`, `refactor: …`. One logical change per commit.
- **Backend**: models stay plain dataclasses behind the `Repository[T]` protocol, no ORM. New providers / stores / backends implement their protocol and register in the matching factory (see [Extending the platform](README.md#extending-the-platform)).
- **Frontend**: the design system is "The Night Court" — read [`DESIGN.md`](DESIGN.md) before touching UI. Both light and dark themes are first-class; test in both. Motion is CSS-only (no animation library). No em-dashes in UI copy.
- **Docs**: if a change alters setup, configuration, the API, or the WebSocket contract, update the README and the relevant file in `docs/` in the same PR.

## Reporting bugs

Open an issue with what you did, what you expected, what happened, and the relevant logs (`make logs`). Security issues go to [SECURITY.md](SECURITY.md) instead.
