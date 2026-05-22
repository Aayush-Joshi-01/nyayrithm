"use client"

import { useEffect, useRef, useState } from "react"
import Link from "next/link"
import { motion, useInView, useScroll, useTransform } from "framer-motion"
import {
  Scale, Gavel, FileSearch, Zap, Users, Brain,
  ChevronRight, BookOpen, Quote, ArrowRight,
  Shield, Database, Network, Cpu, FileText,
} from "lucide-react"
import { WebGLShader } from "@/components/ui/web-gl-shader"
import { MetalButton } from "@/components/ui/liquid-glass-button"

/* ─── Animated section wrapper ──────────────────────────────── */
function FadeUp({ children, delay = 0, className = "" }: {
  children: React.ReactNode
  delay?: number
  className?: string
}) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: "-60px" })
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 32 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.7, delay, ease: [0.16, 1, 0.3, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

/* ─── Section label ──────────────────────────────────────────── */
function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="font-display text-[10px] tracking-[0.35em] uppercase text-amber-500/70 mb-3">
      {children}
    </p>
  )
}

/* ─── Data ───────────────────────────────────────────────────── */
const features = [
  {
    icon: Users,
    title: "Multi-Agent Orchestration",
    desc: "Nine distinct legal roles — judge, prosecutor, defense, witnesses, investigator, plaintiff, accused, expert witness, and custom roles — each with separate knowledge scopes, behavioral constraints, and AI personas.",
    accent: "amber",
    tag: "Core",
  },
  {
    icon: FileSearch,
    title: "Evidence RAG Pipeline",
    desc: "Ingest PDFs, audio, video, and documents through role-matched ingesters. Retrieval is scoped per agent — witnesses only retrieve their linked evidence, judges see everything.",
    accent: "blue",
    tag: "Intelligence",
  },
  {
    icon: Zap,
    title: "Real-time Token Streaming",
    desc: "Watch the courtroom unfold live over WebSocket. Each token is streamed as agents speak. Turn transitions, objections, and verdicts broadcast instantly.",
    accent: "emerald",
    tag: "Live",
  },
  {
    icon: Network,
    title: "Dynamic Agent Spawning",
    desc: "When forensic or technical domains surface mid-trial, the orchestrator autonomously spawns domain expert witnesses on the fly — a DNA analyst, a forensic accountant, a cybersecurity expert.",
    accent: "purple",
    tag: "Adaptive",
  },
  {
    icon: Quote,
    title: "Citation Engine",
    desc: "Every agent claim is annotated with inline evidence markers — [EVIDENCE:uuid:chunk_index] — resolved back to exact document passages, timestamps, or audio windows.",
    accent: "orange",
    tag: "Precision",
  },
  {
    icon: Cpu,
    title: "Multi-Provider LLM",
    desc: "Each role maps to an independent LLM provider and model. GPT-4o judges, Claude 3.5 defense counsels, Gemini witnesses — mix and match with per-agent overrides.",
    accent: "cyan",
    tag: "Flexible",
  },
]

const roles = [
  { name: "Judge", desc: "Oversees proceedings, rules on objections, delivers verdict", color: "#f59e0b", emoji: "⚖️" },
  { name: "Prosecutor", desc: "Presents the state's case, cross-examines defense witnesses", color: "#ef4444", emoji: "⚔️" },
  { name: "Defense Counsel", desc: "Advocates for the accused, challenges evidence admissibility", color: "#3b82f6", emoji: "🛡️" },
  { name: "Plaintiff", desc: "Brings the civil case, testifies to harm suffered", color: "#8b5cf6", emoji: "📜" },
  { name: "Accused", desc: "Responds to charges, testifies under oath, can plead", color: "#ec4899", emoji: "👤" },
  { name: "Witness", desc: "Provides testimony scoped strictly to their knowledge window", color: "#10b981", emoji: "🗣️" },
  { name: "Investigator", desc: "Presents forensic findings and chain of custody reports", color: "#f97316", emoji: "🔍" },
  { name: "Expert Witness", desc: "AI-spawned domain specialist — forensic, medical, financial", color: "#06b6d4", emoji: "🧬" },
]

const steps = [
  {
    n: "01",
    title: "Upload Evidence",
    desc: "Attach PDFs, audio recordings, video footage, and documents to your case. The ingestion pipeline chunks and embeds everything automatically.",
    icon: FileText,
  },
  {
    n: "02",
    title: "Configure the Court",
    desc: "Define your agent roster, assign LLM providers per role, set knowledge access rules, and configure the simulation parameters.",
    icon: Shield,
  },
  {
    n: "03",
    title: "Call the Court to Order",
    desc: "Launch the simulation and watch AI agents argue, object, cross-examine, and deliver verdicts in real-time with full citation tracking.",
    icon: Gavel,
  },
]

const accentClasses: Record<string, { icon: string; tag: string }> = {
  amber:   { icon: "text-amber-400",   tag: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
  blue:    { icon: "text-blue-400",    tag: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
  emerald: { icon: "text-emerald-400", tag: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
  purple:  { icon: "text-purple-400",  tag: "bg-purple-500/10 text-purple-400 border-purple-500/20" },
  orange:  { icon: "text-orange-400",  tag: "bg-orange-500/10 text-orange-400 border-orange-500/20" },
  cyan:    { icon: "text-cyan-400",    tag: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20" },
}

/* ─── Component ──────────────────────────────────────────────── */
export default function LandingPage() {
  const heroRef = useRef(null)
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ["start start", "end start"] })
  const heroOpacity = useTransform(scrollYProgress, [0, 0.6], [1, 0])
  const heroY = useTransform(scrollYProgress, [0, 1], [0, 80])

  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  return (
    <div className="relative min-h-screen bg-black overflow-x-hidden">

      {/* WebGL background */}
      <div className="fixed inset-0 z-0">
        <WebGLShader />
      </div>

      {/* Frosted overlay — improves text readability over shader */}
      <div className="fixed inset-0 z-[1] pointer-events-none bg-gradient-to-b from-black/55 via-black/30 to-black/70" />

      {/* Legal watermark texture */}
      <div className="fixed inset-0 z-[2] pointer-events-none legal-watermark opacity-60" />

      {/* ── Navbar ─────────────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50">
        <div className="mx-auto max-w-7xl px-6 py-4">
          <div className="frosted-card rounded-2xl px-6 py-3 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center group-hover:bg-amber-500/30 transition-colors">
                <Scale className="w-5 h-5 text-amber-400" />
              </div>
              <span className="font-display text-white font-semibold tracking-wide text-base">NYAYRITHM</span>
            </Link>
            <div className="hidden md:flex items-center gap-1">
              <Link href="#how-it-works" className="px-4 py-2 text-sm text-white/50 hover:text-white/90 transition-colors rounded-lg hover:bg-white/5">
                How It Works
              </Link>
              <Link href="#features" className="px-4 py-2 text-sm text-white/50 hover:text-white/90 transition-colors rounded-lg hover:bg-white/5">
                Features
              </Link>
              <Link href="#roles" className="px-4 py-2 text-sm text-white/50 hover:text-white/90 transition-colors rounded-lg hover:bg-white/5">
                Agent Roles
              </Link>
              <Link href="/docs" className="px-4 py-2 text-sm text-white/50 hover:text-white/90 transition-colors rounded-lg hover:bg-white/5">
                Docs
              </Link>
            </div>
            <div className="flex items-center gap-3">
              <Link href="/login" className="text-sm text-white/60 hover:text-white/90 transition-colors hidden sm:block">
                Sign In
              </Link>
              <Link href="/signup">
                <MetalButton variant="primary" className="text-sm font-semibold px-5 py-2 h-9">
                  Get Started
                </MetalButton>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────────── */}
      <section ref={heroRef} className="relative z-10 min-h-screen flex flex-col items-center justify-center px-6 text-center pt-24">
        <motion.div style={{ opacity: heroOpacity, y: heroY }} className="w-full flex flex-col items-center">

          {/* Status badge */}
          {mounted && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, ease: "backOut" }}
              className="inline-flex items-center gap-2.5 px-4 py-2 mb-10 rounded-full border border-red-500/30 bg-red-500/10 backdrop-blur-sm"
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-red-400" />
              </span>
              <span className="font-display text-[10px] tracking-[0.3em] uppercase text-red-300">
                The Court Is Now In Session
              </span>
            </motion.div>
          )}

          {/* Main heading */}
          {mounted && (
            <motion.h1
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.9, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
              className="font-serif text-6xl md:text-8xl lg:text-[108px] font-bold tracking-tight text-white leading-[0.92] mb-6 max-w-5xl"
            >
              Justice Has a{" "}
              <em className="not-italic shimmer-text">
                New
              </em>
              <br />
              <span className="text-white">Intelligence.</span>
            </motion.h1>
          )}

          {/* Sub-headline */}
          {mounted && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.3 }}
              className="max-w-2xl mb-12"
            >
              <p className="text-lg md:text-xl text-white/50 leading-relaxed">
                Nyayrithm simulates the full arc of legal proceedings — from evidence ingestion to final verdict — using a dynamic graph of AI agents, each playing a distinct legal role with scoped knowledge and real-time reasoning.
              </p>
            </motion.div>
          )}

          {/* CTAs */}
          {mounted && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.45 }}
              className="flex flex-col sm:flex-row items-center gap-4 mb-16"
            >
              <Link href="/signup">
                <MetalButton variant="primary" className="text-base font-bold px-8 py-3 h-12 rounded-full">
                  Enter the Courtroom
                  <ChevronRight className="w-4 h-4 ml-1.5 inline" />
                </MetalButton>
              </Link>
              <Link
                href="/docs"
                className="px-8 py-3 h-12 inline-flex items-center gap-2 text-white/60 hover:text-white text-base border border-white/15 hover:border-white/30 rounded-full transition-all frosted-card"
              >
                <BookOpen className="w-4 h-4" />
                Read the Docs
              </Link>
            </motion.div>
          )}

          {/* Stats pills */}
          {mounted && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.6 }}
              className="flex flex-wrap items-center justify-center gap-3"
            >
              {[
                { icon: Users, label: "9 Agent Roles" },
                { icon: Database, label: "Multi-modal RAG" },
                { icon: Zap, label: "WebSocket Streaming" },
                { icon: Brain, label: "Multi-Provider LLM" },
                { icon: FileSearch, label: "Citation Engine" },
              ].map(({ icon: Icon, label }) => (
                <div
                  key={label}
                  className="flex items-center gap-2 px-3.5 py-1.5 rounded-full frosted-card text-white/40 text-xs"
                >
                  <Icon className="w-3.5 h-3.5 text-amber-500/60" />
                  {label}
                </div>
              ))}
            </motion.div>
          )}
        </motion.div>

        {/* Scroll hint */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
        >
          <div className="w-px h-10 bg-gradient-to-b from-transparent to-white/20" />
          <p className="font-display text-[9px] tracking-[0.3em] text-white/20 uppercase">Scroll</p>
        </motion.div>
      </section>

      {/* ── Court Divider ───────────────────────────────────── */}
      <div className="relative z-10 flex items-center gap-6 px-6 py-4 max-w-5xl mx-auto">
        <div className="court-divider flex-1" />
        <Scale className="w-5 h-5 text-amber-500/50 flex-shrink-0" />
        <div className="court-divider flex-1" />
      </div>

      {/* ── How It Works ────────────────────────────────────── */}
      <section id="how-it-works" className="relative z-10 px-6 py-28 max-w-6xl mx-auto">
        <FadeUp className="text-center mb-20">
          <SectionLabel>Proceedings</SectionLabel>
          <h2 className="font-serif text-4xl md:text-5xl font-bold text-white mb-4">
            Order in the Court
          </h2>
          <p className="text-white/40 max-w-lg mx-auto text-base">
            Three steps from raw evidence to a fully reasoned verdict.
          </p>
        </FadeUp>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          {/* Connecting line */}
          <div className="hidden md:block absolute top-12 left-[calc(16.67%+1rem)] right-[calc(16.67%+1rem)] h-px bg-gradient-to-r from-transparent via-amber-500/30 to-transparent" />

          {steps.map(({ n, title, desc, icon: Icon }, i) => (
            <FadeUp key={n} delay={i * 0.15} className="relative">
              <div className="frosted-card rounded-2xl p-8 h-full group hover:border-amber-500/20 transition-all duration-300">
                <div className="flex items-start gap-4 mb-5">
                  <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center flex-shrink-0 group-hover:bg-amber-500/20 transition-colors">
                    <Icon className="w-6 h-6 text-amber-400" />
                  </div>
                  <span className="font-display text-4xl font-bold text-amber-500/20 group-hover:text-amber-500/30 transition-colors mt-1">
                    {n}
                  </span>
                </div>
                <h3 className="font-serif text-xl font-semibold text-white mb-3">{title}</h3>
                <p className="text-white/40 text-sm leading-relaxed">{desc}</p>
              </div>
            </FadeUp>
          ))}
        </div>
      </section>

      {/* ── Features ────────────────────────────────────────── */}
      <section id="features" className="relative z-10 px-6 py-28 max-w-6xl mx-auto">
        <FadeUp className="text-center mb-20">
          <SectionLabel>Presenting the Evidence</SectionLabel>
          <h2 className="font-serif text-4xl md:text-5xl font-bold text-white mb-4">
            Built for the Courtroom
          </h2>
          <p className="text-white/40 max-w-lg mx-auto text-base">
            Production-grade infrastructure for researchers, law schools, and legal-tech builders.
          </p>
        </FadeUp>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map(({ icon: Icon, title, desc, accent, tag }, i) => {
            const a = accentClasses[accent]
            return (
              <FadeUp key={title} delay={i * 0.08}>
                <div className="frosted-card rounded-2xl p-7 h-full group transition-all duration-300">
                  <div className="flex items-start justify-between mb-5">
                    <div
                      className="w-11 h-11 rounded-xl bg-white/5 flex items-center justify-center group-hover:bg-white/10 transition-colors border border-white/10"
                    >
                      <Icon className={`w-5 h-5 ${a.icon}`} />
                    </div>
                    <span className={`text-[10px] font-display tracking-widest uppercase px-2.5 py-1 rounded-full border ${a.tag}`}>
                      {tag}
                    </span>
                  </div>
                  <h3 className="font-serif text-lg font-semibold text-white mb-2.5">{title}</h3>
                  <p className="text-white/40 text-sm leading-relaxed">{desc}</p>
                </div>
              </FadeUp>
            )
          })}
        </div>
      </section>

      {/* ── Agent Roles ─────────────────────────────────────── */}
      <section id="roles" className="relative z-10 px-6 py-28 max-w-6xl mx-auto">
        <FadeUp className="text-center mb-20">
          <SectionLabel>Roles of Counsel</SectionLabel>
          <h2 className="font-serif text-4xl md:text-5xl font-bold text-white mb-4">
            Meet the Court
          </h2>
          <p className="text-white/40 max-w-lg mx-auto text-base">
            Every simulation runs a full bench. Each agent has a distinct persona, knowledge scope, and behavioral mandate.
          </p>
        </FadeUp>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {roles.map(({ name, desc, color, emoji }, i) => (
            <FadeUp key={name} delay={i * 0.06}>
              <div
                className="frosted-card rounded-2xl p-6 group cursor-default transition-all duration-300 hover:scale-[1.02]"
                style={{ "--role-color": color } as React.CSSProperties}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center text-xl flex-shrink-0 transition-transform group-hover:scale-110"
                    style={{ background: `${color}18`, border: `1px solid ${color}30` }}
                  >
                    {emoji}
                  </div>
                  <div
                    className="w-1.5 h-8 rounded-full opacity-60"
                    style={{ background: `linear-gradient(to bottom, ${color}, transparent)` }}
                  />
                </div>
                <h3
                  className="font-serif text-base font-semibold mb-1.5 transition-colors"
                  style={{ color }}
                >
                  {name}
                </h3>
                <p className="text-white/35 text-xs leading-relaxed">{desc}</p>
              </div>
            </FadeUp>
          ))}
        </div>
      </section>

      {/* ── Architecture callout ────────────────────────────── */}
      <section className="relative z-10 px-6 py-20 max-w-6xl mx-auto">
        <FadeUp>
          <div className="frosted-card rounded-3xl p-10 md:p-16 text-center relative overflow-hidden">
            {/* Background glow */}
            <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 via-transparent to-blue-500/5 pointer-events-none" />

            <div className="relative z-10">
              <div className="w-16 h-16 rounded-2xl bg-amber-500/15 border border-amber-500/25 flex items-center justify-center mx-auto mb-8 animate-float">
                <Gavel className="w-8 h-8 text-amber-400" />
              </div>
              <p className="font-display text-[10px] tracking-[0.35em] uppercase text-amber-500/60 mb-4">Architecture</p>
              <h2 className="font-serif text-3xl md:text-4xl font-bold text-white mb-6 max-w-2xl mx-auto">
                Every component is modular,<br />
                <span className="text-amber-400">swappable, and production-ready.</span>
              </h2>
              <p className="text-white/40 max-w-xl mx-auto mb-10 leading-relaxed">
                FastAPI backend with a pluggable DB layer (Postgres, MongoDB, SQLite, DynamoDB), vector stores (Qdrant, Chroma, Pinecone), storage backends (local, S3, MinIO), and LLM providers — all controlled by a single <code className="font-mono text-amber-400/70 text-sm">.env</code> file.
              </p>

              <div className="flex flex-wrap justify-center gap-3">
                {[
                  { label: "FastAPI", color: "emerald" },
                  { label: "Next.js 15", color: "blue" },
                  { label: "Qdrant", color: "purple" },
                  { label: "Keycloak", color: "orange" },
                  { label: "Celery", color: "amber" },
                  { label: "WebSockets", color: "cyan" },
                  { label: "Redis", color: "red" },
                  { label: "PostgreSQL", color: "blue" },
                ].map(({ label, color }) => (
                  <span key={label} className={`px-3 py-1.5 text-xs font-mono rounded-lg border border-white/10 text-white/50 bg-white/[0.03] hover:text-white/80 hover:bg-white/[0.06] transition-colors cursor-default`}>
                    {label}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </FadeUp>
      </section>

      {/* ── Final CTA ───────────────────────────────────────── */}
      <section className="relative z-10 px-6 py-32 text-center">
        <FadeUp>
          <SectionLabel>Verdict</SectionLabel>
          <h2 className="font-serif text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-6 leading-tight">
            All Rise.
          </h2>
          <p className="font-serif text-xl md:text-2xl text-amber-400/80 italic mb-4">
            "Every argument deserves to be heard."
          </p>
          <p className="text-white/40 max-w-md mx-auto mb-12 text-base leading-relaxed">
            The most advanced AI courtroom simulation platform. Built for those who believe the future of legal reasoning is intelligent, evidence-driven, and real.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/signup">
              <MetalButton variant="primary" className="text-base font-bold px-10 py-3.5 h-12 rounded-full">
                Enter the Courtroom
                <ArrowRight className="w-4 h-4 ml-2 inline" />
              </MetalButton>
            </Link>
            <Link href="/docs" className="px-8 py-3.5 inline-flex items-center gap-2 text-white/50 hover:text-white text-sm border border-white/10 hover:border-white/25 rounded-full transition-all frosted-card">
              <BookOpen className="w-4 h-4" />
              Documentation
            </Link>
          </div>
        </FadeUp>
      </section>

      {/* ── Footer ──────────────────────────────────────────── */}
      <footer className="relative z-10 border-t border-white/8 px-6 py-10">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
              <Scale className="w-4 h-4 text-amber-400" />
            </div>
            <span className="font-display text-white/60 text-sm tracking-widest">NYAYRITHM</span>
          </div>
          <div className="flex items-center gap-6 text-xs text-white/30">
            <Link href="/docs" className="hover:text-white/60 transition-colors">Documentation</Link>
            <Link href="#features" className="hover:text-white/60 transition-colors">Features</Link>
            <Link href="#roles" className="hover:text-white/60 transition-colors">Agent Roles</Link>
            <Link href="/login" className="hover:text-white/60 transition-colors">Sign In</Link>
          </div>
          <p className="text-white/20 text-xs font-mono">
            © 2026 Nyayrithm
          </p>
        </div>
      </footer>
    </div>
  )
}
