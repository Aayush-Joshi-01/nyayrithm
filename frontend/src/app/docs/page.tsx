"use client"

import { useState } from "react"
import Link from "next/link"
import {
  Scale, ChevronRight, Zap, Database,
  Shield, Users, FileText, Network,
  Settings, AlertTriangle, CheckCircle,
  Package, Cpu, MessageSquare, ArrowRight,
  Layout,
} from "lucide-react"

/* ─── Types ──────────────────────────────────────────────────── */
interface NavItem {
  id: string
  label: string
  icon: React.ElementType
}

/* ─── Sidebar sections ───────────────────────────────────────── */
const nav: NavItem[] = [
  { id: "quick-start",      label: "Quick Start",           icon: Zap },
  { id: "architecture",     label: "Architecture",           icon: Network },
  { id: "frontend-stack",   label: "Frontend Stack",         icon: Layout },
  { id: "agent-system",     label: "Agent System",           icon: Users },
  { id: "rag-pipeline",     label: "RAG Pipeline",           icon: Database },
  { id: "llm-providers",    label: "LLM Providers",          icon: Cpu },
  { id: "websocket-events", label: "WebSocket Events",       icon: MessageSquare },
  { id: "auth",             label: "Authentication",         icon: Shield },
  { id: "configuration",    label: "Configuration",          icon: Settings },
  { id: "extending",        label: "Extending the Platform", icon: Package },
]

/* ─── Code block ─────────────────────────────────────────────── */
function Code({ children, lang = "bash" }: { children: string; lang?: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <div className="relative group rounded-xl overflow-hidden border border-white/8 mb-5">
      <div className="flex items-center justify-between px-4 py-2 bg-white/[0.03] border-b border-white/8">
        <span className="font-mono text-xs text-white/30">{lang}</span>
        <button
          onClick={() => {
            navigator.clipboard.writeText(children)
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
          }}
          className="text-xs text-white/30 hover:text-white/60 transition-colors"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <pre className="p-5 overflow-x-auto">
        <code className="font-mono text-sm text-white/70 leading-relaxed whitespace-pre">{children}</code>
      </pre>
    </div>
  )
}

/* ─── Section heading ────────────────────────────────────────── */
function H2({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <h2
      id={id}
      className="font-serif text-2xl font-bold text-white mt-16 mb-5 flex items-center gap-3 scroll-mt-24 group"
    >
      {children}
      <a
        href={`#${id}`}
        className="opacity-0 group-hover:opacity-40 transition-opacity text-white/40 text-lg"
      >
        #
      </a>
    </h2>
  )
}

function H3({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="font-sans text-base font-semibold text-white/90 mt-8 mb-3">{children}</h3>
  )
}

function P({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <p className={`text-white/50 text-sm leading-7 mb-4 ${className}`}>{children}</p>
}

function Callout({
  type = "info",
  children,
}: {
  type?: "info" | "warn" | "tip"
  children: React.ReactNode
}) {
  const styles = {
    info: "border-blue-500/30 bg-blue-500/8 text-blue-300/80",
    warn: "border-amber-500/30 bg-amber-500/8 text-amber-300/80",
    tip: "border-emerald-500/30 bg-emerald-500/8 text-emerald-300/80",
  }
  const icons = { info: AlertTriangle, warn: AlertTriangle, tip: CheckCircle }
  const Icon = icons[type]
  return (
    <div className={`flex gap-3 p-4 rounded-xl border mb-5 text-sm leading-relaxed ${styles[type]}`}>
      <Icon className="w-4 h-4 flex-shrink-0 mt-0.5 opacity-70" />
      <div>{children}</div>
    </div>
  )
}

function InlineCode({ children }: { children: string }) {
  return (
    <code className="font-mono text-xs bg-white/8 border border-white/10 rounded px-1.5 py-0.5 text-amber-400/80">
      {children}
    </code>
  )
}

/* ─── Table ──────────────────────────────────────────────────── */
function Table({
  headers,
  rows,
}: {
  headers: string[]
  rows: string[][]
}) {
  return (
    <div className="overflow-x-auto mb-5 rounded-xl border border-white/8">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/8 bg-white/[0.03]">
            {headers.map((h) => (
              <th key={h} className="text-left px-4 py-2.5 font-mono text-xs text-white/40 font-normal">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-white/5 last:border-0 hover:bg-white/[0.02]">
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-2.5 font-mono text-xs text-white/60">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* ─── Main component ─────────────────────────────────────────── */
export default function DocsPage() {
  const [activeSection, setActiveSection] = useState("quick-start")

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Top bar */}
      <header className="sticky top-0 z-50 border-b border-white/8 bg-black/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-7 h-7 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
                <Scale className="w-3.5 h-3.5 text-amber-400" />
              </div>
              <span className="font-display text-white/70 text-sm tracking-widest group-hover:text-white transition-colors">
                NYAYRITHM
              </span>
            </Link>
            <ChevronRight className="w-3.5 h-3.5 text-white/20" />
            <span className="text-white/40 text-sm font-mono">Documentation</span>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/" className="text-sm text-white/40 hover:text-white/70 transition-colors">
              ← Back
            </Link>
            <Link href="/signup">
              <button className="px-4 py-1.5 text-xs font-semibold text-black bg-amber-400 hover:bg-amber-300 rounded-lg transition-colors">
                Get Started
              </button>
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto flex">
        {/* Sidebar */}
        <aside className="hidden lg:block w-60 flex-shrink-0 sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto py-8 pr-4 pl-6 border-r border-white/6">
          <nav className="space-y-0.5">
            {nav.map(({ id, label, icon: Icon }) => (
              <a
                key={id}
                href={`#${id}`}
                onClick={() => setActiveSection(id)}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all ${
                  activeSection === id
                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                    : "text-white/40 hover:text-white/70 hover:bg-white/5"
                }`}
              >
                <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                {label}
              </a>
            ))}
          </nav>
        </aside>

        {/* Content */}
        <main className="flex-1 px-8 lg:px-12 py-12 max-w-3xl">
          {/* Title */}
          <div className="mb-12">
            <p className="font-display text-[10px] tracking-[0.35em] uppercase text-amber-500/60 mb-3">
              Reference
            </p>
            <h1 className="font-serif text-4xl font-bold text-white mb-4">Documentation</h1>
            <P>
              Everything you need to understand, run, and extend Nyayrithm — the multi-agent legal
              reasoning and courtroom simulation platform.
            </P>
          </div>

          {/* ── Quick Start ──────────────────────────────────── */}
          <H2 id="quick-start">Quick Start</H2>
          <P>Get the full stack running locally in under five minutes.</P>

          <H3>Prerequisites</H3>
          <P>
            You&apos;ll need <strong className="text-white/80">Docker Desktop</strong>,{" "}
            <strong className="text-white/80">Bun ≥1.1</strong> (frontend package manager &amp;
            runtime), <strong className="text-white/80">Python ≥3.11</strong> with{" "}
            <strong className="text-white/80">uv</strong> (backend dependency management).
          </P>

          <Callout type="info">
            Bun replaces Node.js/npm/pnpm as the frontend runtime. Install it from{" "}
            <InlineCode>bun.sh</InlineCode> — it is significantly faster for installs and dev-server
            startup than npm/pnpm equivalents.
          </Callout>

          <H3>1. Clone and configure environment</H3>
          <Code lang="bash">{`git clone https://github.com/your-org/nyayrithm.git
cd nyayrithm
make env       # copies .env.example → .env
# open .env and fill in your LLM API keys`}</Code>

          <H3>2. Start all services</H3>
          <Code lang="bash">{`make dev
# Starts: PostgreSQL · Redis · Qdrant · MinIO · Keycloak · backend · frontend`}</Code>

          <Callout type="warn">
            Keycloak takes ~30 s on first boot to import the realm. The frontend will show auth
            errors until it is ready. Watch progress with{" "}
            <InlineCode>docker compose logs -f keycloak</InlineCode>.
          </Callout>

          <H3>3. Run database migrations</H3>
          <Code lang="bash">{`make migrate`}</Code>

          <P>
            Open <InlineCode>http://localhost:3000</InlineCode> for the app,{" "}
            <InlineCode>http://localhost:8000/docs</InlineCode> for the interactive API docs, and{" "}
            <InlineCode>http://localhost:8080</InlineCode> for the Keycloak admin console
            (admin / admin).
          </P>

          <Callout type="tip">
            Set <InlineCode>NEXT_PUBLIC_DEV_MODE=true</InlineCode> in{" "}
            <InlineCode>.env</InlineCode> to bypass authentication entirely during local development.
          </Callout>

          {/* ── Architecture ─────────────────────────────────── */}
          <H2 id="architecture">Architecture</H2>

          <P>Nyayrithm is a monorepo with four top-level directories:</P>

          <Code lang="text">{`backend/    FastAPI + Python  — agents, RAG, simulation engine
frontend/   Next.js 15       — UI, auth pages, WebSocket client
infra/      Docker configs, Terraform modules, Keycloak realm
.github/    CI/CD workflows`}</Code>

          <H3>Backend — Module Tree</H3>
          <Code lang="text">{`app/
├── agents/
│   ├── base.py            BaseAgent — all roles inherit from this
│   ├── orchestrator.py    AgentOrchestrator — turn control & conflict detection
│   ├── graph.py           AgentGraph — dynamic spawn graph
│   └── roles/             8 role-specific agent implementations
├── llm/
│   ├── registry.py        ROLE_PROVIDER_MAP + PROVIDER_REGISTRY
│   └── providers/         LLMProvider protocol implementations
├── rag/
│   ├── ingester.py        EvidenceIngester — type-matched (PDF/audio/video/text)
│   ├── chunker.py         TextChunker, TimeWindowChunker
│   ├── embedder.py        Embedder protocol + factory
│   └── citation.py        [EVIDENCE:uuid:chunk_index] inline marker parser
├── db/
│   ├── repository_base.py Repository[T] protocol (no ORM)
│   └── adapters/          PostgresRepository, MongoRepository, …
├── vector_db/             VectorStore protocol + factory
└── tasks/                 Celery task definitions (evidence, simulation queues)`}</Code>

          <H3>Database Abstraction</H3>
          <P>
            Models are <strong>plain Python dataclasses</strong> — not SQLAlchemy ORM. The{" "}
            <InlineCode>Repository[T]</InlineCode> protocol in{" "}
            <InlineCode>app/db/repository_base.py</InlineCode> is implemented by backend-specific
            adapters. Select the backend via the <InlineCode>DB_BACKEND</InlineCode> env var:{" "}
            <InlineCode>postgres</InlineCode> | <InlineCode>mongodb</InlineCode> |{" "}
            <InlineCode>sqlite</InlineCode> | <InlineCode>dynamodb</InlineCode>.
          </P>

          {/* ── Frontend Stack ───────────────────────────────── */}
          <H2 id="frontend-stack">Frontend Stack</H2>

          <P>
            The frontend is a Next.js 15 App Router application. Bun is the package manager and
            dev-server runtime — there is no <InlineCode>package-lock.json</InlineCode> or{" "}
            <InlineCode>pnpm-lock.yaml</InlineCode>; the lock file is{" "}
            <InlineCode>bun.lock</InlineCode>.
          </P>

          <H3>Directory Structure</H3>
          <Code lang="text">{`src/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx       Email + password login form
│   │   └── signup/page.tsx      Registration form (name, email, password)
│   ├── api/auth/
│   │   ├── login/route.ts       POST → Keycloak Direct Access Grants
│   │   ├── register/route.ts    POST → Keycloak admin REST API + auto-login
│   │   └── logout/route.ts      DELETE cookies → redirect /login
│   ├── dashboard/               Protected app shell (middleware-guarded)
│   ├── docs/page.tsx            This documentation page
│   ├── page.tsx                 Public landing page
│   ├── layout.tsx               Root layout — font variables, QueryProvider
│   └── globals.css              CSS variables, utility classes
├── components/
│   ├── ui/                      shadcn/ui base + custom components
│   │   ├── cobe-globe-pulse.tsx  Interactive 3-D WebGL globe (cobe)
│   │   ├── liquid-glass-button.tsx  LiquidButton + MetalButton
│   │   ├── web-gl-shader.tsx    Full-page THREE.js shader background
│   │   └── background-paths.tsx Animated SVG path background
│   ├── layout/                  Sidebar, TopBar, QueryProvider
│   ├── simulation/              AgentGraph, TurnFeed, SimulationShell
│   ├── case/                    CaseCard, CaseDashboard, CaseCreateModal
│   └── evidence/                EvidenceManager
├── lib/
│   ├── keycloak.ts              KC URL helpers (login / logout redirect URLs)
│   └── utils.ts                 cn(), shared utilities
└── middleware.ts                Protects /dashboard/* — checks kc_access_token cookie`}</Code>

          <H3>Fonts</H3>
          <P>
            Three Google Fonts are loaded via <InlineCode>next/font/google</InlineCode> in{" "}
            <InlineCode>layout.tsx</InlineCode> and exposed as Tailwind font-family utilities:
          </P>
          <Table
            headers={["Tailwind class", "Font", "Used for"]}
            rows={[
              ["font-sans",    "Inter",            "Body text, UI labels, paragraphs"],
              ["font-serif",   "Playfair Display", "Page headings, section titles, hero text"],
              ["font-display", "Cinzel",           "ALL CAPS labels, navbar brand, section badges"],
              ["font-mono",    "JetBrains Mono",   "Code blocks, inline code, timestamps"],
            ]}
          />

          <H3>Tailwind Custom Tokens</H3>
          <P>
            Role-based colors are defined in <InlineCode>tailwind.config.ts</InlineCode> under the{" "}
            <InlineCode>role</InlineCode> key and used throughout the simulation UI:
          </P>
          <Table
            headers={["Token", "Color", "Role"]}
            rows={[
              ["role.judge",         "#f59e0b", "Judge"],
              ["role.prosecutor",    "#ef4444", "Prosecutor"],
              ["role.defense",       "#3b82f6", "Defense Counsel"],
              ["role.plaintiff",     "#8b5cf6", "Plaintiff"],
              ["role.accused",       "#ec4899", "Accused"],
              ["role.witness",       "#10b981", "Witness"],
              ["role.investigator",  "#f97316", "Investigator"],
              ["role.expert_witness","#06b6d4", "Expert Witness"],
            ]}
          />

          <H3>Key npm Packages</H3>
          <Table
            headers={["Package", "Purpose"]}
            rows={[
              ["cobe",               "WebGL 3-D globe (landing page)"],
              ["three + @types/three","WebGL shader background"],
              ["framer-motion",      "Scroll-driven animations, page transitions"],
              ["react-hook-form + zod","Form validation (login, signup, case creation)"],
              ["@tanstack/react-query","Server state management"],
              ["reactflow",          "Agent graph visualisation in simulation view"],
              ["keycloak-js",        "Keycloak JS adapter (token refresh helper)"],
            ]}
          />

          <H3>Dev Commands</H3>
          <Code lang="bash">{`bun install           # install dependencies
bun dev               # start dev server on :3000
bun run build         # production build
bun run lint          # ESLint
bun run tsc --noEmit  # TypeScript check
# or use the Makefile shortcuts:
make install-frontend
make run-frontend
make lint-frontend`}</Code>

          {/* ── Agent System ─────────────────────────────────── */}
          <H2 id="agent-system">Agent System</H2>

          <P>
            Every agent inherits from <InlineCode>BaseAgent</InlineCode> in{" "}
            <InlineCode>app/agents/base.py</InlineCode>. Role-specific behavior lives in{" "}
            <InlineCode>app/agents/roles/</InlineCode>.
          </P>

          <H3>Agent Roles</H3>
          <Code lang="python">{`from app.agents.roles import (
    JudgeAgent,
    ProsecutorAgent,
    DefenseCounselAgent,
    PlaintiffAgent,
    AccusedAgent,
    WitnessAgent,
    InvestigatorAgent,
    ExpertWitnessAgent,
)`}</Code>

          <H3>AgentDefinition</H3>
          <P>
            Agents can be predefined (user-created before the simulation) or AI-spawned at runtime
            when the orchestrator detects a knowledge gap.
          </P>
          <Code lang="python">{`AgentDefinition(
    id="witness-001",
    role="witness",
    name="Dr. Sarah Chen",
    persona="Forensic pathologist, 20 years experience",
    evidence_ids=["autopsy-report-uuid", "toxicology-uuid"],
    llm_provider="anthropic",     # optional per-agent override
    llm_model="claude-opus-4-5",  # optional per-agent override
)`}</Code>

          <H3>AgentOrchestrator</H3>
          <P>
            The orchestrator controls turn-taking, manages the spawn graph, detects conflicts
            between agent claims, and streams WebSocket events to connected clients.
          </P>
          <Code lang="python">{`orchestrator = AgentOrchestrator(
    simulation_id=sim.id,
    agents=agent_definitions,
    case_context=case,
    ws_broadcast=websocket_broadcast_fn,
)
await orchestrator.run()`}</Code>

          {/* ── RAG Pipeline ─────────────────────────────────── */}
          <H2 id="rag-pipeline">RAG Pipeline</H2>

          <P>Evidence flows through a four-stage pipeline: ingestion → chunking → embedding → retrieval.</P>

          <Code lang="text">{`Evidence file
  → EvidenceIngester  (type-matched: PDF / audio / video / text)
  → TextChunker | TimeWindowChunker
  → Embedder          (OpenAI / Cohere / Sentence-Transformers)
  → VectorStore       (Qdrant / Chroma / Pinecone / pgvector)`}</Code>

          <H3>Role-Scoped Retrieval</H3>
          <P>
            Retrieval is role-scoped at query time. Witness agents only retrieve chunks from their
            linked <InlineCode>evidence_ids</InlineCode>. The Judge agent retrieves from all
            evidence. This prevents AI agents from &quot;knowing&quot; information they
            shouldn&apos;t possess.
          </P>

          <H3>Citation Format</H3>
          <P>
            Agent responses include inline citation markers that are parsed and resolved to source
            passages:
          </P>
          <Code lang="text">{`"The defendant was present at the scene [EVIDENCE:3a4b:12] and
the forensic analysis confirms [EVIDENCE:7c2d:4] a match."

# Resolved by app/rag/citation.py:
# EVIDENCE:3a4b:12  →  Document "CCTV Report", chunk 12, page 4
# EVIDENCE:7c2d:4   →  Audio "Lab Analysis", timestamp 00:02:34`}</Code>

          {/* ── LLM Providers ────────────────────────────────── */}
          <H2 id="llm-providers">LLM Providers</H2>

          <P>
            Each role has a default provider/model in <InlineCode>ROLE_PROVIDER_MAP</InlineCode> in{" "}
            <InlineCode>app/llm/registry.py</InlineCode>. Override per-agent via{" "}
            <InlineCode>AgentDefinition.llm_provider</InlineCode> and{" "}
            <InlineCode>.llm_model</InlineCode>.
          </P>

          <H3>Adding a New Provider</H3>
          <Code lang="python">{`# 1. Create backend/app/llm/myprovider.py
class MyProvider:
    async def complete(self, messages, stream=False, **kwargs):
        ...  # implement LLMProvider protocol

# 2. Register in app/llm/registry.py
PROVIDER_REGISTRY["myprovider"] = MyProvider

# 3. Add API key to Settings.get_api_key()
# 4. Set LLM_DEFAULT_PROVIDER=myprovider in .env`}</Code>

          {/* ── WebSocket Events ─────────────────────────────── */}
          <H2 id="websocket-events">WebSocket Events</H2>

          <P>
            Connect to{" "}
            <InlineCode>{"ws://localhost:8000/ws/simulation/{id}"}</InlineCode> to receive
            real-time simulation events.
          </P>

          <H3>Event Reference</H3>
          <Code lang="typescript">{`// Simulation turn begins
{ event: "turn.started",     turn_number, agent_id, agent_name, role }

// Streaming token delta (one per token)
{ event: "turn.token",       agent_id, token }

// Turn complete with full content + resolved citations
{ event: "turn.completed",   turn_number, agent_id, content, citations, spawned_agents }

// New agent dynamically spawned mid-simulation
{ event: "agent.spawned",    agent_id, role, name, parent_id, reason }

// Simulation lifecycle
{ event: "simulation.completed" }
{ event: "simulation.paused" }

// Contradiction detected between two agents' claims
{ event: "conflict.detected", agent_id, conflicting_agent_id, evidence_ids }`}</Code>

          <H3>Client Example</H3>
          <Code lang="typescript">{`const ws = new WebSocket(\`ws://localhost:8000/ws/simulation/\${simId}\`)

ws.onmessage = (e) => {
  const msg = JSON.parse(e.data)
  switch (msg.event) {
    case "turn.token":       appendToken(msg.agent_id, msg.token);   break
    case "turn.completed":   finalizeTurn(msg);                       break
    case "agent.spawned":    addAgentToGraph(msg);                    break
    case "conflict.detected":highlightConflict(msg);                  break
  }
}`}</Code>

          {/* ── Auth ─────────────────────────────────────────── */}
          <H2 id="auth">Authentication</H2>

          <P>
            Authentication is handled by <strong>Keycloak 26</strong> running as a Docker service
            on port 8080. The frontend has custom-built login and register pages — users never leave
            the Nyayrithm UI. All Keycloak communication happens server-side through Next.js API
            routes, so credentials and tokens are never exposed to the browser directly.
          </P>

          <Callout type="info">
            Next.js API routes run <strong>server-side inside the frontend Docker container</strong>.
            They use the internal Docker network URL (<InlineCode>http://keycloak:8080</InlineCode>{" "}
            via the <InlineCode>KEYCLOAK_URL</InlineCode> env var) — not the browser-facing{" "}
            <InlineCode>localhost:8080</InlineCode>. When running with <InlineCode>bun dev</InlineCode>{" "}
            outside Docker, <InlineCode>frontend/.env.local</InlineCode> sets{" "}
            <InlineCode>KEYCLOAK_URL=http://localhost:8080</InlineCode> instead.
          </Callout>

          <H3>Login Flow</H3>
          <Code lang="text">{`User submits /login form  (email + password)
  → POST /api/auth/login                    (Next.js Route Handler)
  → POST $KEYCLOAK_URL/realms/nyayrithm/
         protocol/openid-connect/token      (Direct Access Grant — server-to-server)
  ← { access_token, refresh_token, expires_in }
  → kc_access_token cookie  (httpOnly, sameSite=lax, maxAge=expires_in)
  → kc_refresh_token cookie (httpOnly, sameSite=lax, maxAge=30 days)
  → router.push("/dashboard")`}</Code>

          <H3>Registration Flow</H3>
          <Code lang="text">{`User submits /signup form  (firstName, lastName, email, password)
  → POST /api/auth/register                 (Next.js Route Handler)
  → POST {KC_URL}/realms/master/
         protocol/openid-connect/token      (admin-cli client_credentials)
  ← admin access_token
  → POST {KC_URL}/admin/realms/nyayrithm/users
         { firstName, lastName, email, username=email,
           enabled=true, emailVerified=true,
           credentials: [{ type:"password", value, temporary:false }] }
  ← 201 Created
  → Auto-login via Direct Access Grant (same as login flow)
  → router.push("/dashboard")`}</Code>

          <H3>Route Protection</H3>
          <P>
            <InlineCode>frontend/src/middleware.ts</InlineCode> runs on every request to{" "}
            <InlineCode>/dashboard/*</InlineCode>. If the <InlineCode>kc_access_token</InlineCode>{" "}
            cookie is absent, the user is redirected to{" "}
            <InlineCode>/login?redirect=&lt;original-path&gt;</InlineCode>. After login the{" "}
            <InlineCode>redirect</InlineCode> param is used to return the user to where they were
            going.
          </P>

          <H3>Keycloak Realm Config</H3>
          <P>
            The <InlineCode>nyayrithm</InlineCode> realm is defined in{" "}
            <InlineCode>infra/keycloak/realm-export.json</InlineCode> and auto-imported on first
            container start via the <InlineCode>--import-realm</InlineCode> flag. Key settings:
          </P>
          <Table
            headers={["Setting", "Value", "Why"]}
            rows={[
              ["Client ID",              "nyayrithm-app",          "Used by frontend API routes"],
              ["Public client",          "true",                   "No client secret needed"],
              ["Direct Access Grants",   "enabled",                "Required for username/password login"],
              ["Login with email",       "enabled",                "email is the username"],
              ["Duplicate emails",       "disabled",               "One account per email"],
            ]}
          />

          <Callout type="warn">
            Change the Keycloak admin password before deploying. Update{" "}
            <InlineCode>KC_BOOTSTRAP_ADMIN_PASSWORD</InlineCode> in{" "}
            <InlineCode>docker-compose.yml</InlineCode> and set{" "}
            <InlineCode>KEYCLOAK_ADMIN_PASS</InlineCode> in your CI/CD secrets accordingly.
          </Callout>

          {/* ── Configuration ────────────────────────────────── */}
          <H2 id="configuration">Configuration</H2>

          <P>
            All service choices are env-var driven. Copy <InlineCode>.env.example</InlineCode> to{" "}
            <InlineCode>.env</InlineCode> and fill in your values. Docker Compose overrides service
            hostnames automatically — you only need to set API keys.
          </P>

          <Code lang="bash">{`# ── Backend services ──────────────────────────────────────────
DB_BACKEND=postgres         # postgres | mongodb | sqlite | dynamodb
VECTOR_DB_BACKEND=qdrant    # qdrant | chroma | pinecone | weaviate | pgvector
STORAGE_BACKEND=local       # local | s3 | minio | gcs | azure_blob
EMBEDDER_BACKEND=openai     # openai | cohere | gemini | sentence-transformers

# ── LLM providers ──────────────────────────────────────────────
LLM_DEFAULT_PROVIDER=openai
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# ── Keycloak ───────────────────────────────────────────────────
NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:8080
NEXT_PUBLIC_KEYCLOAK_REALM=nyayrithm
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=nyayrithm-app
KEYCLOAK_ADMIN_USER=admin          # master-realm admin (server-side only)
KEYCLOAK_ADMIN_PASS=admin

# ── Frontend ───────────────────────────────────────────────────
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_DEV_MODE=false         # set true to bypass auth locally`}</Code>

          {/* ── Extending ────────────────────────────────────── */}
          <H2 id="extending">Extending the Platform</H2>

          <H3>New Agent Role</H3>
          <Code lang="python">{`# backend/app/agents/roles/mediator.py
from app.agents.base import BaseAgent

class MediatorAgent(BaseAgent):
    role = "mediator"

    async def generate_turn(self, context) -> str:
        # custom reasoning logic
        ...`}</Code>

          <H3>New LLM Provider</H3>
          <P>
            Implement the <InlineCode>LLMProvider</InlineCode> protocol and register it in{" "}
            <InlineCode>app/llm/registry.py</InlineCode>. Add the API key to{" "}
            <InlineCode>Settings.get_api_key()</InlineCode> and to <InlineCode>.env</InlineCode>.
          </P>

          <H3>New Vector Store</H3>
          <P>
            Create <InlineCode>app/vector_db/mystore.py</InlineCode> implementing the{" "}
            <InlineCode>VectorStore</InlineCode> protocol, then register it in{" "}
            <InlineCode>app/vector_db/factory.py</InlineCode>.
          </P>

          <H3>New Embedder</H3>
          <P>
            Create a class in <InlineCode>app/rag/embedder.py</InlineCode> implementing the{" "}
            <InlineCode>Embedder</InlineCode> protocol, then register it in{" "}
            <InlineCode>app/rag/embedder_factory.py</InlineCode>.
          </P>

          <H3>New DB Backend</H3>
          <P>
            Create <InlineCode>backend/app/db/adapters/mybackend.py</InlineCode> extending{" "}
            <InlineCode>BaseRepository</InlineCode>, then add it to{" "}
            <InlineCode>SQL_MAP</InlineCode> / <InlineCode>MONGO_MAP</InlineCode> in{" "}
            <InlineCode>app/db/factory.py</InlineCode>.
          </P>

          <H3>Running Tests</H3>
          <Code lang="bash">{`cd backend && uv run pytest -v
cd backend && uv run pytest --cov=app --cov-report=term-missing -v  # with coverage`}</Code>

          <H3>Linting</H3>
          <Code lang="bash">{`# Backend
cd backend && uv run ruff check .
cd backend && uv run mypy app/

# Frontend
cd frontend && bun run lint
cd frontend && bun run tsc --noEmit

# Or use the Makefile
make lint
make lint-frontend`}</Code>

          {/* Bottom CTA */}
          <div className="mt-20 p-8 rounded-2xl border border-amber-500/20 bg-amber-500/5 text-center">
            <p className="font-display text-[10px] tracking-[0.3em] uppercase text-amber-500/60 mb-3">
              Ready?
            </p>
            <h3 className="font-serif text-2xl font-bold text-white mb-4">Enter the Courtroom</h3>
            <p className="text-white/40 text-sm mb-6">Start your first simulation in minutes.</p>
            <Link href="/signup">
              <button className="inline-flex items-center gap-2 px-6 py-2.5 bg-amber-500 hover:bg-amber-400 text-black font-semibold text-sm rounded-full transition-colors">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </button>
            </Link>
          </div>
        </main>

        {/* Right TOC */}
        <aside className="hidden xl:block w-52 flex-shrink-0 sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto py-8 pl-6">
          <p className="font-display text-[9px] tracking-[0.3em] uppercase text-white/20 mb-4">
            On this page
          </p>
          <nav className="space-y-1.5">
            {nav.map(({ id, label }) => (
              <a
                key={id}
                href={`#${id}`}
                className="block text-xs text-white/30 hover:text-white/70 transition-colors py-0.5"
              >
                {label}
              </a>
            ))}
          </nav>
        </aside>
      </div>
    </div>
  )
}
