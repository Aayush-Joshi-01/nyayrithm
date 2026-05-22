FROM node:24-alpine AS base
RUN npm install -g pnpm@latest

# ── Dev stage (used by docker-compose) ───────────────────────────────────────
# Installs deps only. Source code is mounted as a volume at runtime so
# hot-reload sees host file changes. node_modules stays inside the container.
FROM base AS dev
WORKDIR /app
ENV CI=true
COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml* ./
RUN pnpm install
EXPOSE 3000
CMD ["pnpm", "dev"]

# ── Builder stage (production image) ─────────────────────────────────────────
# Self-contained: installs deps and runs next build in a single stage so
# pnpm's virtual store is never copied across layer boundaries.
FROM base AS builder
WORKDIR /app
ENV CI=true
COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml* ./
RUN pnpm install
COPY . .
RUN pnpm build

# ── Production stage ──────────────────────────────────────────────────────────
FROM node:24-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
