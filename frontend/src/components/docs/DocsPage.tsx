"use client"

import { useState } from "react"
import Link from "next/link"
import { ChevronRight, TriangleAlert, Check } from "lucide-react"
import { ThemeToggle } from "@/components/theme/ThemeToggle"
import { cn } from "@/lib/utils"

interface NavItem {
  id: string
  label: string
}

const nav: NavItem[] = [
  { id: "quick-start", label: "Quick start" },
  { id: "architecture", label: "Architecture" },
  { id: "frontend-stack", label: "Frontend stack" },
  { id: "agent-system", label: "Agent system" },
  { id: "rag-pipeline", label: "RAG pipeline" },
  { id: "llm-providers", label: "LLM providers" },
  { id: "websocket-events", label: "WebSocket events" },
  { id: "auth", label: "Authentication" },
  { id: "configuration", label: "Configuration" },
  { id: "extending", label: "Extending" },
]

function Code({ children, lang = "bash" }: { children: string; lang?: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <div className="mb-5 overflow-hidden rounded-md border border-border">
      <div className="flex items-center justify-between border-b border-hairline bg-ink-raised px-4 py-2">
        <span className="font-mono text-[0.68rem] uppercase tracking-wide text-foreground/30">{lang}</span>
        <button
          onClick={() => {
            navigator.clipboard.writeText(children)
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
          }}
          className={cn(
            "inline-flex items-center gap-1 font-mono text-[0.68rem] uppercase tracking-wide transition-colors",
            copied ? "text-role-witness" : "text-foreground/30 hover:text-brass-text"
          )}
        >
          <span className="grid grid-cols-1 grid-rows-1 [&>*]:col-start-1 [&>*]:row-start-1">
            <span className={cn("transition-all duration-200", copied ? "translate-y-0.5 opacity-0" : "opacity-100")}>Copy</span>
            <span className={cn("flex items-center gap-1 transition-all duration-200", copied ? "opacity-100" : "-translate-y-0.5 opacity-0")}>
              <Check className="h-3 w-3" strokeWidth={2.5} /> Copied
            </span>
          </span>
        </button>
      </div>
      <pre className="overflow-x-auto bg-ink-raised/50 p-5">
        <code className="whitespace-pre font-mono text-[0.82rem] leading-relaxed text-foreground/70">{children}</code>
      </pre>
    </div>
  )
}

function H2({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <h2 id={id} className="group mb-5 mt-16 scroll-mt-24 border-t border-hairline pt-10 font-serif text-[1.7rem] font-medium tracking-tight text-bone">
      {children}
      <a href={`#${id}`} className="ml-3 text-foreground/25 opacity-0 transition-opacity group-hover:opacity-100">#</a>
    </h2>
  )
}

function H3({ children }: { children: React.ReactNode }) {
  return <h3 className="mb-3 mt-8 font-serif text-[1.05rem] font-medium text-foreground/90">{children}</h3>
}

function P({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <p className={`mb-4 max-w-[68ch] text-[0.92rem] leading-7 text-foreground/55 ${className}`}>{children}</p>
}

function Callout({ type = "info", children }: { type?: "info" | "warn" | "tip"; children: React.ReactNode }) {
  const styles = {
    info: "border-role-defense/25 bg-role-defense/[0.07] text-role-defense",
    warn: "border-brass/30 bg-brass/[0.07] text-brass-text",
    tip: "border-role-witness/25 bg-role-witness/[0.07] text-role-witness",
  }
  const Icon = type === "tip" ? Check : TriangleAlert
  return (
    <div className={`mb-5 flex gap-3 rounded-md border p-4 text-[0.86rem] leading-relaxed ${styles[type]}`}>
      <Icon className="mt-0.5 h-4 w-4 flex-shrink-0 opacity-80" strokeWidth={1.75} />
      <div className="[&_strong]:text-foreground/80">{children}</div>
    </div>
  )
}

function InlineCode({ children }: { children: string }) {
  return (
    <code className="rounded-sm border border-hairline bg-bone/[0.05] px-1.5 py-0.5 font-mono text-[0.78rem] text-brass-text">
      {children}
    </code>
  )
}

function Table({ headers, rows }: { headers: string[]; rows: string[][] }) {
  return (
    <div className="mb-5 overflow-x-auto rounded-md border border-border">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-hairline bg-ink-raised">
            {headers.map((h) => (
              <th key={h} className="px-4 py-2.5 font-mono text-[0.68rem] font-normal uppercase tracking-wide text-foreground/40">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-hairline last:border-0">
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-2.5 font-mono text-[0.76rem] text-foreground/60">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function DocsPage() {
  return (
    <div className="min-h-screen bg-ink text-foreground">
      <div className="pointer-events-none fixed inset-0 z-[1] court-grain" />

      <header className="podium-edge sticky top-0 z-50">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <Link href="/" className="font-serif text-[0.9rem] font-semibold tracking-[0.16em] text-bone">
              NYAYRITHM
            </Link>
            <ChevronRight className="h-3.5 w-3.5 text-foreground/20" />
            <span className="font-mono text-[0.78rem] text-foreground/40">Documentation</span>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link href="/" className="font-mono text-[0.78rem] text-foreground/40 transition-colors hover:text-foreground/70">
              Home
            </Link>
            <Link
              href="/signup"
              className="rounded-sm bg-ember px-3.5 py-1.5 text-[0.78rem] font-semibold text-[#12100A] transition-colors hover:brightness-105"
            >
              Convene a proceeding
            </Link>
          </div>
        </div>
      </header>

      <div className="relative z-10 mx-auto flex max-w-7xl">
        <aside className="sticky top-16 hidden h-[calc(100vh-4rem)] w-60 flex-shrink-0 overflow-y-auto border-r border-hairline py-8 pl-6 pr-4 lg:block">
          <nav className="space-y-0.5">
            {nav.map(({ id, label }) => (
              <a
                key={id}
                href={`#${id}`}
                className="block px-3 py-1.5 text-[0.82rem] text-foreground/40 transition-colors hover:text-foreground"
              >
                {label}
              </a>
            ))}
          </nav>
        </aside>

        <main className="max-w-3xl flex-1 px-8 py-14 lg:px-12">
          <div className="mb-4">
            <h1 className="font-serif text-[2.6rem] font-medium tracking-tight text-bone">Documentation</h1>
            <P className="mt-3">
              How to run, understand, and extend Nyayrithm: a self-hostable, provider-agnostic
              platform where a graph of AI agents argues a case from ingested evidence.
            </P>
          </div>

          <H2 id="quick-start">Quick start</H2>
          <P>Get the full stack running locally in under five minutes.</P>

          <H3>Prerequisites</H3>
          <P>
            You need <strong className="text-foreground/80">Docker Desktop</strong>,{" "}
            <strong className="text-foreground/80">Bun 1.1 or newer</strong> (frontend runtime), and{" "}
            <strong className="text-foreground/80">Python 3.11 or newer</strong> with{" "}
            <strong className="text-foreground/80">uv</strong> for the backend.
          </P>

          <Callout type="tip">
            To run without any cloud account: a free Gemini key plus SQLite, Chroma, and
            sentence-transformers is a complete stack. See <InlineCode>Configuration</InlineCode> below.
          </Callout>

          <H3>1. Clone and configure</H3>
          <Code lang="bash">{`git clone https://github.com/your-org/nyayrithm.git
cd nyayrithm
make env       # copies .env.example to .env
# open .env and add at least one LLM key`}</Code>

          <H3>2. Start every service</H3>
          <Code lang="bash">{`make dev
# postgres, redis, qdrant, minio, keycloak, backend, frontend`}</Code>

          <Callout type="warn">
            Keycloak takes about 30 seconds on first boot to import the realm. Watch it with{" "}
            <InlineCode>docker compose logs -f keycloak</InlineCode>.
          </Callout>

          <H3>3. Run migrations</H3>
          <Code lang="bash">{`make migrate`}</Code>

          <P>
            Then open <InlineCode>http://localhost:3000</InlineCode> for the app,{" "}
            <InlineCode>http://localhost:8000/docs</InlineCode> for the API, and{" "}
            <InlineCode>http://localhost:8080</InlineCode> for Keycloak (admin / admin).
          </P>

          <Callout type="tip">
            Set <InlineCode>NEXT_PUBLIC_DEV_MODE=true</InlineCode> in <InlineCode>.env</InlineCode> to
            bypass authentication entirely in local development.
          </Callout>

          <H2 id="architecture">Architecture</H2>
          <P>Nyayrithm is a monorepo with four top-level directories:</P>
          <Code lang="text">{`backend/    FastAPI + Python  agents, RAG, simulation engine
frontend/   Next.js 15        UI, auth pages, WebSocket client
infra/      Docker, Terraform, Keycloak realm
.github/    CI/CD workflows`}</Code>

          <H3>Backend module tree</H3>
          <Code lang="text">{`app/
  agents/       BaseAgent, AgentOrchestrator, AgentGraph, roles/
  llm/          LLMProvider protocol, registry, providers
  rag/          ingester, chunker, embedder, citation parser
  db/           Repository[T] protocol (no ORM), adapters/
  vector_db/    VectorStore protocol + factory
  tasks/        Celery tasks (evidence, simulation queues)`}</Code>

          <H3>Database abstraction</H3>
          <P>
            Models are plain Python dataclasses, not an ORM. The{" "}
            <InlineCode>Repository[T]</InlineCode> protocol in{" "}
            <InlineCode>app/db/repository_base.py</InlineCode> is implemented per backend and selected
            with <InlineCode>DB_BACKEND</InlineCode>: postgres, mongodb, sqlite, or dynamodb.
          </P>

          <H2 id="frontend-stack">Frontend stack</H2>
          <P>
            Next.js 15 App Router. Bun is the package manager and dev runtime; the lock file is{" "}
            <InlineCode>bun.lock</InlineCode>.
          </P>

          <H3>Type system</H3>
          <P>
            The design system is &ldquo;The Night Court&rdquo;: a dark chamber where the proceeding
            is the only light. Three faces carry it.
          </P>
          <Table
            headers={["Tailwind class", "Font", "Used for"]}
            rows={[
              ["font-serif", "Spectral", "Headlines and any agent speaking on the record"],
              ["font-sans", "Libre Franklin", "Everything the interface says itself"],
              ["font-mono", "JetBrains Mono", "Line numbers, timestamps, citations, Bates stamps"],
            ]}
          />

          <H3>Role tokens</H3>
          <P>
            Each legal role has one reserved hue and one sigil letter, applied identically in the
            graph, the transcript, and setup. Defined in <InlineCode>tailwind.config.ts</InlineCode>{" "}
            and <InlineCode>src/lib/utils.ts</InlineCode>.
          </P>
          <Table
            headers={["Token", "Color", "Sigil"]}
            rows={[
              ["role.judge", "#D69B58", "J"],
              ["role.prosecutor", "#C0453C", "P"],
              ["role.defense", "#5B7FA6", "D"],
              ["role.plaintiff", "#8E7BB0", "Pi"],
              ["role.accused", "#B26E8A", "A"],
              ["role.witness", "#6E9E86", "W"],
              ["role.investigator", "#C77F4A", "I"],
              ["role.expert_witness", "#5E93A0", "E"],
            ]}
          />

          <H3>Dev commands</H3>
          <Code lang="bash">{`bun install           # install dependencies
bun dev               # dev server on :3000
bun run build         # production build
bun run lint          # ESLint
bun run tsc --noEmit  # TypeScript check`}</Code>

          <H2 id="agent-system">Agent system</H2>
          <P>
            Every agent inherits from <InlineCode>BaseAgent</InlineCode> in{" "}
            <InlineCode>app/agents/base.py</InlineCode>. Role behavior lives in{" "}
            <InlineCode>app/agents/roles/</InlineCode>. Agents are either predefined by the user
            before the proceeding, or spawned by the orchestrator when a domain gap opens.
          </P>
          <Code lang="python">{`AgentDefinition(
    id="witness-001",
    role="witness",
    name="Dr. Sarah Chen",
    persona="Forensic pathologist, 20 years",
    evidence_ids=["autopsy-uuid", "toxicology-uuid"],
    llm_provider="anthropic",     # optional per-agent override
    llm_model="claude-opus-4-5",  # optional per-agent override
)`}</Code>
          <P>
            The <InlineCode>AgentOrchestrator</InlineCode> controls turn-taking, manages the spawn
            graph, detects conflicts between agent claims, and streams WebSocket events to connected
            clients.
          </P>

          <H2 id="rag-pipeline">RAG pipeline</H2>
          <P>Evidence flows ingestion, chunking, embedding, retrieval.</P>
          <Code lang="text">{`Evidence file
  EvidenceIngester   type-matched: PDF, audio, video, image, text
  TextChunker | TimeWindowChunker
  Embedder           OpenAI, Cohere, Gemini, sentence-transformers
  VectorStore        Qdrant, Chroma, Pinecone, pgvector`}</Code>

          <H3>Role-scoped retrieval</H3>
          <P>
            Retrieval is scoped at query time. A witness only retrieves chunks from its linked{" "}
            <InlineCode>evidence_ids</InlineCode>; the judge retrieves from the whole record. An
            agent cannot cite what its role was never permitted to see.
          </P>

          <H3>Citation format</H3>
          <Code lang="text">{`"The defendant was present [EVIDENCE:3a4b:12] and the
analysis confirms [EVIDENCE:7c2d:4] a match."

# Resolved by app/rag/citation.py:
# EVIDENCE:3a4b:12  ->  "CCTV Report", chunk 12, page 4
# EVIDENCE:7c2d:4   ->  "Lab Analysis", timestamp 00:02:34`}</Code>

          <H2 id="llm-providers">LLM providers</H2>
          <P>
            Each role has a default provider and model in <InlineCode>ROLE_PROVIDER_MAP</InlineCode>{" "}
            in <InlineCode>app/llm/registry.py</InlineCode>, overridable per agent.
          </P>
          <Code lang="python">{`# 1. backend/app/llm/myprovider.py implements the LLMProvider protocol
# 2. register in app/llm/registry.py
PROVIDER_REGISTRY["myprovider"] = MyProvider
# 3. add the key to Settings.get_api_key()
# 4. set LLM_DEFAULT_PROVIDER=myprovider in .env`}</Code>

          <H2 id="websocket-events">WebSocket events</H2>
          <P>
            Connect to <InlineCode>{"ws://localhost:8000/ws/simulations/{sim_id}"}</InlineCode> for
            the live proceeding.
          </P>
          <Code lang="typescript">{`{ event: "turn.started",     turn_number, agent_id, agent_name, role }
{ event: "turn.token",       agent_id, token }
{ event: "turn.completed",   turn_number, agent_id, content, citations, spawned_agents }
{ event: "agent.spawned",    agent_id, role, name, parent_id, reason }
{ event: "conflict.detected", agent_id, conflicting_agent_id, evidence_ids }
{ event: "simulation.paused" }
{ event: "simulation.completed" }`}</Code>

          <H2 id="auth">Authentication</H2>
          <P>
            Keycloak 26 runs as a Docker service on port 8080. The frontend has its own login and
            register pages; all Keycloak calls happen server-side in Next.js route handlers, so
            tokens never reach the browser directly.
          </P>
          <Callout type="info">
            Route handlers run inside the frontend container, so they use{" "}
            <InlineCode>KEYCLOAK_URL=http://keycloak:8080</InlineCode> (the Docker service name). For{" "}
            <InlineCode>bun dev</InlineCode> outside Docker,{" "}
            <InlineCode>frontend/.env.local</InlineCode> sets it to{" "}
            <InlineCode>http://localhost:8080</InlineCode>.
          </Callout>
          <P>
            <InlineCode>src/middleware.ts</InlineCode> guards{" "}
            <InlineCode>/dashboard/*</InlineCode>: with no{" "}
            <InlineCode>kc_access_token</InlineCode> cookie the user is redirected to{" "}
            <InlineCode>/login</InlineCode> with a return path.
          </P>

          <H2 id="configuration">Configuration</H2>
          <P>
            Every service choice is an environment variable. Copy{" "}
            <InlineCode>.env.example</InlineCode> to <InlineCode>.env</InlineCode>. Docker Compose
            sets hostnames for you; you supply API keys.
          </P>
          <Code lang="bash">{`# Backend services
DB_BACKEND=sqlite            # postgres | mongodb | sqlite | dynamodb
VECTOR_DB_BACKEND=chroma     # qdrant | chroma | pinecone | pgvector
STORAGE_BACKEND=local        # local | s3 | minio | gcs | azure_blob
EMBEDDER_BACKEND=sentence-transformers

# LLM
LLM_DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=AIza...

# Keycloak
NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:8080
NEXT_PUBLIC_KEYCLOAK_REALM=nyayrithm
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=nyayrithm-app

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_DEV_MODE=false`}</Code>

          <H2 id="extending">Extending the platform</H2>
          <P>
            New LLM providers, embedders, vector stores, and database backends each follow the same
            shape: implement the protocol, register it in the factory, set one environment variable.
            New agent roles subclass <InlineCode>BaseAgent</InlineCode> and implement{" "}
            <InlineCode>generate_turn</InlineCode>.
          </P>
          <Code lang="bash">{`cd backend && uv run pytest -v
cd backend && uv run ruff check . && uv run mypy app/
cd frontend && bun run lint && bun run tsc --noEmit`}</Code>

          <div className="mt-20 rounded-lg border border-border bg-ink-raised/60 p-8 text-center">
            <h3 className="font-serif text-xl font-medium text-bone">Ready to seat a bench?</h3>
            <p className="mx-auto mt-2 max-w-sm text-[0.88rem] text-foreground/45">
              Bring a case and read what a well-argued proceeding looks like.
            </p>
            <Link
              href="/signup"
              className="mt-6 inline-block rounded-sm bg-ember px-6 py-2.5 text-[0.85rem] font-semibold text-[#12100A] transition-colors hover:brightness-105"
            >
              Convene a proceeding
            </Link>
          </div>
        </main>

        <aside className="sticky top-16 hidden h-[calc(100vh-4rem)] w-52 flex-shrink-0 overflow-y-auto py-8 pl-6 xl:block">
          <p className="mb-4 font-mono text-[0.62rem] uppercase tracking-[0.2em] text-foreground/45">
            On this page
          </p>
          <nav className="space-y-1.5">
            {nav.map(({ id, label }) => (
              <a key={id} href={`#${id}`} className="block py-0.5 text-[0.76rem] text-foreground/30 transition-colors hover:text-foreground/70">
                {label}
              </a>
            ))}
          </nav>
        </aside>
      </div>
    </div>
  )
}
