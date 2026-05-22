"use client"

import Link from "next/link"
import { Scale, FileSearch, Zap, Users, ChevronRight, Gavel } from "lucide-react"
import { WebGLShader } from "@/components/ui/web-gl-shader"
import { LiquidButton } from "@/components/ui/liquid-glass-button"

export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-black overflow-x-hidden">
      <WebGLShader />

      {/* Nav */}
      <nav className="relative z-20 flex items-center justify-between px-6 py-5 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center">
            <Scale className="w-4 h-4 text-amber-400" />
          </div>
          <span className="text-white font-bold tracking-tight text-lg">Nyayrithm</span>
        </div>
        <div className="flex items-center gap-4">
          <Link
            href="#features"
            className="text-white/60 hover:text-white text-sm transition-colors hidden md:block"
          >
            Features
          </Link>
          <Link
            href="/login"
            className="px-4 py-2 text-sm text-white/80 hover:text-white border border-white/20 hover:border-white/40 rounded-lg transition-all backdrop-blur-sm bg-white/5"
          >
            Sign In
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 flex flex-col items-center justify-center min-h-[85vh] px-6 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 text-amber-400 text-xs font-medium mb-8">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-400" />
          </span>
          AI-Powered Legal Reasoning Platform
        </div>

        <h1 className="text-5xl md:text-7xl lg:text-8xl font-extrabold tracking-tighter text-white mb-6 leading-[0.9]">
          Simulate the
          <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-orange-400 to-red-400">
            Courtroom.
          </span>
        </h1>

        <p className="text-xl md:text-2xl text-white/50 font-light mb-4 tracking-wide">
          Every argument. Every witness. Every verdict.
        </p>

        <p className="max-w-xl text-white/40 text-base mb-12 leading-relaxed">
          Multi-agent AI simulation platform where judge, prosecutor, defense, witnesses and more
          collaborate in realistic courtroom proceedings — powered by your evidence.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-4 mb-16">
          <Link href="/login">
            <LiquidButton
              size="xl"
              className="text-white border border-white/30 rounded-full font-semibold"
            >
              Enter Platform
              <ChevronRight className="w-4 h-4 ml-1 inline" />
            </LiquidButton>
          </Link>
          <Link
            href="#features"
            className="px-8 py-3 text-white/60 hover:text-white text-sm border border-white/10 hover:border-white/20 rounded-full transition-all"
          >
            Learn More
          </Link>
        </div>

        <div className="flex items-center gap-6 text-xs text-white/30">
          <span className="flex items-center gap-1.5">
            <Gavel className="w-3.5 h-3.5" />9 Agent Roles
          </span>
          <span className="w-1 h-1 rounded-full bg-white/20" />
          <span className="flex items-center gap-1.5">
            <FileSearch className="w-3.5 h-3.5" />
            Evidence RAG
          </span>
          <span className="w-1 h-1 rounded-full bg-white/20" />
          <span className="flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5" />
            Real-time Streaming
          </span>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative z-10 px-6 py-24 max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Production-grade legal simulation
          </h2>
          <p className="text-white/40 max-w-xl mx-auto">
            Built for researchers, law schools, and legal-tech builders who need realistic AI courtroom environments.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              icon: Users,
              title: "Multi-Agent Courtroom",
              desc: "Judge, prosecutor, defense counsel, witnesses, investigators — all driven by role-specific AI with distinct personas and knowledge scopes.",
              color: "text-amber-400",
              bg: "bg-amber-500/10 border-amber-500/20",
            },
            {
              icon: FileSearch,
              title: "Evidence RAG",
              desc: "Ingest PDFs, audio, video and documents. Agents retrieve only the evidence they're allowed to know, producing inline citations.",
              color: "text-blue-400",
              bg: "bg-blue-500/10 border-blue-500/20",
            },
            {
              icon: Zap,
              title: "Live Streaming",
              desc: "Watch agents speak in real-time via WebSocket streaming. Agents can spawn new expert witnesses mid-simulation when forensic topics arise.",
              color: "text-emerald-400",
              bg: "bg-emerald-500/10 border-emerald-500/20",
            },
          ].map(({ icon: Icon, title, desc, color, bg }) => (
            <div
              key={title}
              className="relative p-6 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm hover:border-white/20 transition-all"
            >
              <div className={`w-10 h-10 rounded-xl border ${bg} flex items-center justify-center mb-4`}>
                <Icon className={`w-5 h-5 ${color}`} />
              </div>
              <h3 className="text-white font-semibold mb-2">{title}</h3>
              <p className="text-white/40 text-sm leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/10 px-6 py-8 text-center">
        <p className="text-white/20 text-sm">
          © 2026 Nyayrithm — Built for legal research and AI simulation
        </p>
      </footer>
    </div>
  )
}
