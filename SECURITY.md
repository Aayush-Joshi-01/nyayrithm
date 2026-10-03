# Security Policy

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

Email **aayushjoshi.dev@gmail.com** with:

- a description of the issue and its impact,
- steps to reproduce (or a proof of concept),
- the affected version or commit.

You will get an acknowledgement within a few days. Once a fix is available it will be released and the report credited unless you ask otherwise.

## Scope

This is a pre-launch, self-hostable project. When you run it:

- **Change every default credential** before exposing anything to a network: the Keycloak admin, `POSTGRES_PASSWORD`, `MONGO_PASSWORD`, `MINIO_ROOT_PASSWORD` and the app's `SECRET_KEY`. Start from `.env.example`, never `.env.dev`.
- **Never enable development authentication in production.** `DEV_AUTH_MODE`, `AUTH_DEV_BYPASS` and `SEED_DEV_DATA` are refused by the backend when `APP_ENV=production`, and `keycloak/realm-dev.json` (static accounts) must never be mounted outside development.
- Restrict the admin portal (IP allow-list or VPN) and grant `platform_admin` sparingly. The role manages access and usage; it grants no access to firms' case data.
- Evidence files and vector data are only as private as the storage and database you point the app at.

## Supported versions

The `main` branch is the only supported version while the project is pre-1.0.
