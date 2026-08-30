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

- **Change every default credential** before exposing anything to a network: the Keycloak admin (`admin`/`admin`), `KC_BOOTSTRAP_ADMIN_PASSWORD`, `MINIO_ROOT_PASSWORD`, `POSTGRES_PASSWORD`, and the app's `SECRET_KEY`.
- **Never set `NEXT_PUBLIC_DEV_MODE=true` in production** — it disables the auth wall on `/dashboard/*`.
- Evidence files and vector data are only as private as the storage and database you point the app at.

## Supported versions

The `main` branch is the only supported version while the project is pre-1.0.
