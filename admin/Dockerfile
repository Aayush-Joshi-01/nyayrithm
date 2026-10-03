FROM oven/bun:1.3-alpine AS base

# ── Dev stage (used by docker-compose.dev.yml): source is bind-mounted for hot reload ──
FROM base AS dev
WORKDIR /app
ENV CI=true
RUN apk add --no-cache libc6-compat
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile
EXPOSE 3001
CMD ["bun", "run", "dev"]

# ── Builder ──
FROM base AS builder
WORKDIR /app
ENV CI=true
RUN apk add --no-cache libc6-compat
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile
COPY . .
# NEXT_PUBLIC_* values are inlined at build time.
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_KEYCLOAK_URL
ARG NEXT_PUBLIC_KEYCLOAK_REALM=nyayrithm
ARG NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=nyayrithm-admin
ARG NEXT_PUBLIC_DEV_AUTH_MODE=off
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_KEYCLOAK_URL=$NEXT_PUBLIC_KEYCLOAK_URL \
    NEXT_PUBLIC_KEYCLOAK_REALM=$NEXT_PUBLIC_KEYCLOAK_REALM \
    NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=$NEXT_PUBLIC_KEYCLOAK_CLIENT_ID \
    NEXT_PUBLIC_DEV_AUTH_MODE=$NEXT_PUBLIC_DEV_AUTH_MODE
RUN mkdir -p public && bun run build

# ── Production ──
FROM node:24-alpine AS production
WORKDIR /app
ENV NODE_ENV=production PORT=3001 HOSTNAME=0.0.0.0
RUN apk add --no-cache libc6-compat
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3001
CMD ["node", "server.js"]
