FROM oven/bun:1.3-alpine AS base

# ── Dev stage (used by docker-compose) ───────────────────────────────────────
# Install deps only. Source code is mounted as a volume so hot-reload works.
# node_modules lives inside the container (anonymous volume) not on the host.
FROM base AS dev
WORKDIR /app
ENV CI=true
# Install musl compat libs needed by Next.js SWC binary on Alpine
RUN apk add --no-cache libc6-compat
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile
EXPOSE 3000
CMD ["bun", "run", "dev"]

# ── Builder stage ─────────────────────────────────────────────────────────────
FROM base AS builder
WORKDIR /app
ENV CI=true
RUN apk add --no-cache libc6-compat
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile
COPY . .
RUN bun run build

# ── Production stage ──────────────────────────────────────────────────────────
FROM node:24-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
RUN apk add --no-cache libc6-compat
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
