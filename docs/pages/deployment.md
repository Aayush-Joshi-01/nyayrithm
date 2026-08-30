---
title: Deployment
nav_order: 8
permalink: /deployment/
---

# Deployment

Nyayrithm runs on **two domains** in production:

| Domain | Serves | Indexed? |
|---|---|---|
| `nyayrithm.aayushjoshi.dev` | the landing page (`/`) and documentation (`/docs`) | yes |
| `nyayrithm.ai.aayushjoshi.dev` | the app: sign-in, dashboard, evidence, proceedings | no (auth pages carry `noindex`) |

Search engines and answer engines see one clean marketing surface; people who click "Convene a proceeding" cross over to the app. The two can be the **same deployment** with two domains pointed at it, or **two deployments**.

---

## How the split is wired

Two build-time environment variables drive it (both `NEXT_PUBLIC_*`, so they are inlined at build time):

```bash
NEXT_PUBLIC_MARKETING_URL=https://nyayrithm.aayushjoshi.dev
NEXT_PUBLIC_APP_URL=https://nyayrithm.ai.aayushjoshi.dev
```

- `src/lib/site.ts` exposes `MARKETING_URL` and `appHref("/path")`.
- `metadataBase`, canonicals, `sitemap.ts`, `robots.ts`, `opengraph-image`, and the `Organization` JSON-LD use **`MARKETING_URL`**.
- Every link into the product: "Convene a proceeding", "Sign in" on the landing and docs, uses **`appHref()`**, which returns an absolute `APP_URL` link when the var is set and a same-origin relative link when it is not.
- Leave both **unset locally**; links stay relative and everything runs on `localhost:3000`.

If `NEXT_PUBLIC_APP_URL` is unset, the split collapses to a single-domain app with no code changes.

---

## Option A: one deployment, two domains (recommended)

Deploy the Next.js app once. Point both hostnames at it.

1. Build with both URLs set (Docker example):

   ```bash
   docker build ./frontend \
     --build-arg NEXT_PUBLIC_MARKETING_URL=https://nyayrithm.aayushjoshi.dev \
     --build-arg NEXT_PUBLIC_APP_URL=https://nyayrithm.ai.aayushjoshi.dev \
     --build-arg NEXT_PUBLIC_API_URL=https://api.nyayrithm.aayushjoshi.dev \
     --build-arg NEXT_PUBLIC_WS_URL=wss://api.nyayrithm.aayushjoshi.dev \
     --build-arg NEXT_PUBLIC_KEYCLOAK_URL=https://auth.nyayrithm.aayushjoshi.dev \
     --build-arg NEXT_PUBLIC_KEYCLOAK_REALM=nyayrithm \
     --build-arg NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=nyayrithm-app \
     -t nyayrithm-frontend:prod
   ```

   (On a platform like Vercel or Netlify, set these as environment variables in the project settings instead of build args.)

2. Run it. The Dockerfile uses `output: "standalone"`, so `node server.js` on port 3000.

3. DNS: an `A` / `AAAA` (or `CNAME` on a PaaS) record for **each** hostname pointing at the same target.

4. Reverse proxy / edge: route both hostnames to the container. No host-based rules are needed, the app serves every route on both.

**Downside:** `nyayrithm.aayushjoshi.dev/dashboard` also resolves (to the login wall). If you want the marketing domain to be strictly marketing, add a redirect at the edge: on `nyayrithm.aayushjoshi.dev`, 308-redirect anything that is not `/`, `/docs`, `/sitemap.xml`, `/robots.txt`, `/llms*.txt`, `/opengraph-image`, or `/_next/*` to the same path on `nyayrithm.ai.aayushjoshi.dev`.

## Option B: two deployments

- **Marketing** (`nyayrithm.aayushjoshi.dev`): deploy the same repo, but only `/` and `/docs` matter. Set `NEXT_PUBLIC_APP_URL` to the app domain so the CTAs cross over. You can leave the backend vars pointing anywhere valid: the marketing routes never call the API.
- **App** (`nyayrithm.ai.aayushjoshi.dev`): full deployment with real API / WS / Keycloak URLs. Set `NEXT_PUBLIC_APP_URL` to its own domain (so absolute links resolve to itself).

This keeps the marketing surface small and independently cacheable at the cost of building twice.

---

## Backend

The API is a separate service (`api.nyayrithm.aayushjoshi.dev` in the examples above). It ships via the manual **Deploy Backend** GitHub Action (`.github/workflows/deploy-backend.yml`) to AWS ECR + ECS, or by any means that runs the `backend/` Docker image. The `infra/terraform/` modules provision VPC, RDS, ElastiCache, ECS, S3, and Qdrant when enabled per environment.

**CORS:** the backend must allow both frontend origins.

```bash
CORS_ORIGINS=https://nyayrithm.aayushjoshi.dev,https://nyayrithm.ai.aayushjoshi.dev
```

## Keycloak

The realm's `nyayrithm-app` client must trust both domains. In the realm export (`infra/keycloak/realm-export.json`) or the admin console, set on that client:

- **Valid redirect URIs**
  - `https://nyayrithm.ai.aayushjoshi.dev/*`
  - `https://nyayrithm.aayushjoshi.dev/*` (only if Option A without the redirect)
- **Web origins**
  - `https://nyayrithm.ai.aayushjoshi.dev`
  - `+` (to mirror the redirect URIs) or the explicit list

The frontend's `/api/auth/*` route handlers call Keycloak server-side, so they need `KEYCLOAK_URL` (the server-reachable URL) in addition to the browser-facing `NEXT_PUBLIC_KEYCLOAK_URL`.

## Checklist

- [ ] Change every default password (`SECURITY.md`)
- [ ] `NEXT_PUBLIC_DEV_MODE` unset or `false` in every non-local environment
- [ ] `NEXT_PUBLIC_MARKETING_URL` and `NEXT_PUBLIC_APP_URL` set at build time
- [ ] Backend `CORS_ORIGINS` lists both frontend domains
- [ ] Keycloak client redirect URIs and web origins cover the app domain
- [ ] `https://nyayrithm.aayushjoshi.dev/sitemap.xml` and `/robots.txt` resolve after deploy
- [ ] Submit the sitemap in Google Search Console for `nyayrithm.aayushjoshi.dev`
