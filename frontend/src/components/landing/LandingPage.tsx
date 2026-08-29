"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { ChevronDown } from "lucide-react"
import { LiveRecord } from "@/components/landing/LiveRecord"
import { FAQ_ITEMS } from "@/components/landing/faq-data"
import { ThemeToggle } from "@/components/theme/ThemeToggle"
import { roleStyle, ROLE_SIGIL, formatRole } from "@/lib/utils"
import type { AgentRole } from "@/types/api"

/* one word of the hero line swaps with the resolved theme */
function ThemeWord() {
  const [word, setWord] = useState("after hours")
  useEffect(() => {
    const read = () => {
      const attr = document.documentElement.getAttribute("data-theme")
      const dark =
        attr === "dark" ||
        (attr !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches)
      setWord(dark ? "after hours" : "in session")
    }
    read()
    const obs = new MutationObserver(read)
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] })
    const mq = window.matchMedia("(prefers-color-scheme: dark)")
    mq.addEventListener("change", read)
    return () => {
      obs.disconnect()
      mq.removeEventListener("change", read)
    }
  }, [])
  return <span className="italic">{word}</span>
}

/* Scroll-driven reveal via CSS `animation-timeline: view()` (globals.css).
   Content is always in the DOM and visible by default; the animation is pure
   enhancement and cannot leave a section hidden if it never fires. */
function Reveal({
  children,
  as: Tag = "div",
  className = "",
}: {
  children: React.ReactNode
  as?: "div" | "section" | "h2" | "li" | "ol" | "ul"
  delay?: number
  className?: string
}) {
  return <Tag className={`reveal ${className}`}>{children}</Tag>
}

const NAV = [
  { href: "#proceeding", label: "The proceeding" },
  { href: "#bench", label: "The bench" },
  { href: "#self-hosting", label: "Self-hosting" },
  { href: "/docs", label: "Docs" },
]

const MOVES = [
  {
    n: "1",
    verb: "Enter the evidence",
    body: "Attach the case file: pleadings, depositions, call recordings, video. Each document is transcribed, chunked, and indexed as it lands.",
    note: "PDF, DOCX, audio, video, image",
  },
  {
    n: "2",
    verb: "Seat the bench",
    body: "Pick the roster and assign a model to each role, or let one free provider carry the whole court. Set what each agent is allowed to see.",
    note: "9 roles, a model each, scoped retrieval",
  },
  {
    n: "3",
    verb: "Call it to order",
    body: "The proceeding runs live over the record. Agents argue, object, and cross-examine; a specialist is spawned when a domain question opens.",
    note: "token streaming, dynamic spawning",
  },
]

const CLUSTERS: { label: string; roles: { role: AgentRole; mandate: string }[] }[] = [
  {
    label: "The bench",
    roles: [{ role: "judge", mandate: "Runs the proceeding, rules on objections, delivers the verdict. Sees the whole record." }],
  },
  {
    label: "Counsel",
    roles: [
      { role: "prosecutor", mandate: "Puts the state's case and cross-examines the defense. Sees prosecution evidence." },
      { role: "defense", mandate: "Advocates for the accused and challenges what is admissible. Sees defense evidence." },
      { role: "plaintiff", mandate: "Brings the civil claim and testifies to the harm. Sees its own filings." },
      { role: "accused", mandate: "Answers the charges and testifies under oath. Sees the charges and its own statements." },
    ],
  },
  {
    label: "The stand",
    roles: [
      { role: "witness", mandate: "Gives testimony bounded to its knowledge window. Sees one linked exhibit." },
      { role: "investigator", mandate: "Presents forensic findings and chain of custody. Sees the investigation file." },
      { role: "expert_witness", mandate: "A domain specialist spawned mid-proceeding when a technical question opens. Sees the matter it was called for." },
    ],
  },
]

const STACK = [
  "OpenAI", "Anthropic", "Gemini", "Ollama", "PostgreSQL", "SQLite", "MongoDB",
  "DynamoDB", "Qdrant", "Chroma", "Pinecone", "pgvector", "MinIO", "S3",
  "local disk", "sentence-transformers",
]

function RoleRow({ role, mandate }: { role: AgentRole; mandate: string }) {
  return (
    <li className="flex items-baseline gap-3 py-2.5">
      <span
        className="mt-0.5 grid h-5 w-5 flex-shrink-0 place-items-center self-start rounded-sm border font-mono text-[0.62rem] font-semibold"
        style={roleStyle(role)}
      >
        {ROLE_SIGIL[role]}
      </span>
      <span className="w-24 flex-shrink-0 font-serif text-[0.92rem] font-medium text-foreground">
        {formatRole(role)}
      </span>
      <p className="text-[0.86rem] leading-relaxed text-foreground/55">{mandate}</p>
    </li>
  )
}

export function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-x-hidden bg-ink">
      <div className="pointer-events-none fixed inset-0 z-[1] court-grain" />

      {/* nav */}
      <header className="fixed inset-x-0 top-0 z-50 podium-edge">
        <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5">
          <Link href="/" className="font-serif text-[0.95rem] font-semibold tracking-[0.16em] text-bone">
            NYAYRITHM
          </Link>
          <div className="hidden items-center gap-7 md:flex">
            {NAV.map((n) => (
              <Link
                key={n.href}
                href={n.href}
                className="text-[0.82rem] text-foreground/55 transition-colors hover:text-foreground"
              >
                {n.label}
              </Link>
            ))}
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <ThemeToggle />
            <Link
              href="/docs"
              className="text-[0.82rem] text-foreground/55 transition-colors hover:text-foreground md:hidden"
            >
              Docs
            </Link>
            <Link
              href="/login"
              className="text-[0.82rem] text-foreground/55 transition-colors hover:text-foreground"
            >
              Sign in
            </Link>
            <Link
              href="/signup"
              className="rounded-sm bg-ember px-3 py-1.5 text-[0.78rem] font-semibold text-[#12100A] transition-[background-color,transform] hover:brightness-105 active:translate-y-px sm:px-3.5 sm:text-[0.8rem]"
            >
              Convene<span className="hidden sm:inline"> a proceeding</span>
            </Link>
          </div>
        </nav>
      </header>

      {/* hero */}
      <section className="relative flex min-h-[100dvh] items-center px-5 pt-24 pb-16">
        <div className="pointer-events-none absolute inset-0 bench-light" />
        <div className="relative mx-auto grid w-full max-w-6xl items-center gap-14 lg:grid-cols-[1fr_minmax(0,540px)]">
          <div>
            <motion.h1
              initial={{ opacity: 0, y: 22 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.85, ease: [0.16, 1, 0.3, 1] }}
              className="font-serif text-[clamp(2.7rem,6vw,4.9rem)] font-medium leading-[0.98] tracking-tight text-bone"
            >
              The court,
              <br />
              <ThemeWord />.
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.2 }}
              className="mt-6 max-w-lg text-[1.02rem] leading-relaxed text-foreground/60"
            >
              A graph of AI agents argues your case from your evidence. Each
              plays a scoped legal role; every claim is seamed to its source.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.35 }}
              className="mt-9 flex flex-wrap items-center gap-4"
            >
              <Link
                href="/signup"
                className="rounded-sm bg-ember px-6 py-3 text-[0.9rem] font-semibold text-[#12100A] transition-[filter,transform] hover:brightness-105 active:translate-y-px"
              >
                Convene a proceeding
              </Link>
              <Link
                href="/docs"
                className="rounded-sm border border-border px-5 py-3 font-mono text-xs uppercase tracking-wide text-foreground/55 transition-colors hover:border-brass/40 hover:text-foreground"
              >
                Read the docs
              </Link>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
            className="justify-self-center lg:justify-self-end"
          >
            <LiveRecord />
          </motion.div>
        </div>
      </section>

      {/* order of proceedings: a numbered progression, not cards */}
      <section id="proceeding" className="relative border-t border-hairline px-5 py-20 sm:py-28">
        <div className="mx-auto max-w-4xl">
          <Reveal as="h2" className="max-w-xl font-serif text-[clamp(1.9rem,3.5vw,2.9rem)] font-medium leading-tight tracking-tight text-bone">
            The order of proceedings.
          </Reveal>

          <ol className="mt-14">
            {MOVES.map((m, i) => (
              <Reveal
                as="li"
                key={m.n}
                delay={i * 0.06}
                className="grid grid-cols-[2.5rem_1fr] gap-x-5 border-t border-hairline py-8 sm:grid-cols-[3rem_1fr_12rem]"
              >
                <span className="font-mono text-[0.95rem] text-brass-text tabular">{m.n}.</span>
                <div>
                  <h3 className="font-serif text-xl font-medium text-foreground">{m.verb}</h3>
                  <p className="mt-2 max-w-md text-[0.94rem] leading-relaxed text-foreground/55">{m.body}</p>
                </div>
                <p className="col-start-2 mt-3 font-mono text-[0.68rem] text-foreground/35 sm:col-start-3 sm:mt-1 sm:text-right">
                  {m.note}
                </p>
              </Reveal>
            ))}
          </ol>
        </div>
      </section>

      {/* provenance */}
      <section className="relative border-t border-hairline px-5 py-20 sm:py-28">
        <div className="mx-auto grid max-w-6xl items-center gap-14 lg:grid-cols-2">
          <Reveal className="order-2 lg:order-1">
            <div className="rounded-lg border border-border bg-ink-raised/80 p-5 shadow-chamber-sm">
              {[
                { n: 88, role: "Witness", prov: "cited", text: "I signed for the package at the loading dock that morning.", tag: "cited: dock-log.pdf p.3", tone: "text-brass-text" },
                { n: 89, role: "Prosecution", prov: "inferred", text: "Which means the defendant knew the contents before noon.", tag: "inferred: not on the record", tone: "text-foreground/45" },
                { n: 90, role: "Defense", prov: "disputed", text: "Objection. The signature on that log is contested.", tag: "disputed", tone: "text-oxblood-bright" },
              ].map((r, i) => (
                <div key={r.n} className={`record-line py-2 ${i === 2 ? "struck" : "afterglow"} ${i > 0 ? "border-t border-hairline" : ""}`} data-prov={r.prov}>
                  <div className="lineno">{r.n}</div>
                  <div className="custody-line" data-prov={r.prov}>
                    <div className="mb-1 font-serif text-[0.85rem] text-foreground">{r.role}</div>
                    <p className="text-[0.82rem] leading-relaxed text-foreground/75">{r.text}</p>
                    <span className={`font-mono text-[0.6rem] uppercase tracking-wide ${r.tone}`}>{r.tag}</span>
                  </div>
                </div>
              ))}
            </div>
          </Reveal>

          <Reveal delay={0.1} className="order-1 lg:order-2">
            <h2 className="font-serif text-[clamp(1.9rem,3.5vw,2.9rem)] font-medium leading-tight tracking-tight text-bone">
              Every claim keeps its receipts.
            </h2>
            <p className="mt-5 max-w-md text-[1rem] leading-relaxed text-foreground/60">
              The rule in the margin tells you where a line stands. Solid means it
              is tied to a passage you can open. Dashed means an agent inferred it
              and the court has not accepted it. Red means it is contested.
            </p>
            <p className="mt-4 max-w-md text-[1rem] leading-relaxed text-foreground/60">
              Retrieval is scoped by role, so a witness cannot borrow the
              judge&apos;s view of the file. The asymmetry is what makes the
              argument worth reading.
            </p>
          </Reveal>
        </div>
      </section>

      {/* the bench: grouped */}
      <section id="bench" className="relative border-t border-hairline px-5 py-20 sm:py-28">
        <div className="mx-auto max-w-5xl">
          <Reveal as="h2" className="font-serif text-[clamp(1.9rem,3.5vw,2.9rem)] font-medium leading-tight tracking-tight text-bone">
            Who is in the room.
          </Reveal>
          <p className="mt-4 max-w-lg text-[0.98rem] leading-relaxed text-foreground/55">
            Eight standing roles, plus custom. Each has a mandate, a reserved
            mark, and a knowledge window it cannot step outside.
          </p>

          <div className="mt-12 space-y-10">
            {CLUSTERS.map((c) => (
              <Reveal key={c.label}>
                <h3 className="font-serif text-[1.15rem] font-medium text-brass-text">
                  {c.label}
                </h3>
                <ul className="mt-2 border-t border-hairline">
                  {c.roles.map((r) => (
                    <RoleRow key={r.role} role={r.role} mandate={r.mandate} />
                  ))}
                </ul>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* self-hosting */}
      <section id="self-hosting" className="relative overflow-hidden border-t border-hairline py-20 sm:py-24">
        <div className="pointer-events-none absolute inset-0 bench-light-tight opacity-70" />
        <div className="relative mx-auto max-w-3xl px-5 text-center">
          <Reveal as="h2" className="font-serif text-[clamp(1.9rem,3.5vw,2.9rem)] font-medium leading-tight tracking-tight text-bone">
            It runs on your machine, or on your cluster.
          </Reveal>
          <Reveal delay={0.08}>
            <p className="mx-auto mt-5 max-w-xl text-[1rem] leading-relaxed text-foreground/60">
              A free Gemini key and SQLite is enough for a full proceeding on a
              laptop. Swap the model, the database, the vector store, and the
              file storage for your own. Each is one environment variable, no
              code change, no account required.
            </p>
          </Reveal>
        </div>

        <div className="relative mt-14 flex select-none overflow-hidden [mask-image:linear-gradient(90deg,transparent,#000_12%,#000_88%,transparent)]">
          <div className="flex shrink-0 animate-marquee items-center gap-3 pr-3">
            {[...STACK, ...STACK].map((s, i) => (
              <span
                key={i}
                className="whitespace-nowrap rounded-sm border border-hairline px-3 py-1.5 font-mono text-[0.74rem] text-foreground/45"
              >
                {s}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* faq */}
      <section className="relative border-t border-hairline px-5 py-20 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <Reveal as="h2" className="font-serif text-[clamp(1.9rem,3.5vw,2.9rem)] font-medium leading-tight tracking-tight text-bone">
            Questions from the gallery.
          </Reveal>
          <dl className="mt-12 border-t border-hairline">
            {FAQ_ITEMS.map((item) => (
              <details key={item.q} className="group border-b border-hairline py-5">
                <summary className="flex cursor-pointer list-none items-start justify-between gap-4">
                  <dt className="font-serif text-[1.05rem] font-medium text-foreground">{item.q}</dt>
                  <ChevronDown className="mt-1 h-4 w-4 flex-shrink-0 text-foreground/35 transition-transform group-open:rotate-180" strokeWidth={1.75} />
                </summary>
                <dd className="mt-3 max-w-2xl text-[0.94rem] leading-relaxed text-foreground/60">{item.a}</dd>
              </details>
            ))}
          </dl>
        </div>
      </section>

      {/* close */}
      <section className="relative border-t border-hairline px-5 py-24 text-center sm:py-32">
        <div className="pointer-events-none absolute inset-0 bench-light" />
        <Reveal className="relative">
          <h2 className="font-serif text-[clamp(3rem,8vw,6rem)] font-medium leading-none tracking-tight text-bone">
            All rise.
          </h2>
          <p className="mx-auto mt-6 max-w-sm text-[0.98rem] leading-relaxed text-foreground/55">
            Bring a case, seat the bench, and read what a well-argued proceeding
            actually looks like.
          </p>
          <Link
            href="/signup"
            className="mt-10 inline-block rounded-sm bg-ember px-7 py-3 text-[0.9rem] font-semibold text-[#12100A] transition-[filter,transform] hover:brightness-105 active:translate-y-px"
          >
            Convene a proceeding
          </Link>
        </Reveal>
      </section>

      {/* footer */}
      <footer className="border-t border-hairline px-5 py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-6 md:flex-row md:items-center">
          <span className="font-serif text-[0.85rem] font-semibold tracking-[0.16em] text-foreground/60">
            NYAYRITHM
          </span>
          <p className="max-w-sm text-[0.78rem] leading-relaxed text-foreground/35">
            Open source and self-hostable. No account is required to run it
            locally. Pre-launch: there are no customers to name yet.
          </p>
          <div className="flex items-center gap-5 text-[0.78rem] text-foreground/40">
            <Link href="/docs" className="transition-colors hover:text-foreground/70">Docs</Link>
            <Link href="#bench" className="transition-colors hover:text-foreground/70">The bench</Link>
            <Link href="/login" className="transition-colors hover:text-foreground/70">Sign in</Link>
          </div>
        </div>
        <p className="mx-auto mt-8 max-w-6xl font-mono text-[0.68rem] text-foreground/45">
          © 2026 Nyayrithm
        </p>
      </footer>
    </div>
  )
}
