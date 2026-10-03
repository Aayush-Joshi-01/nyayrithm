"use client"

import { Suspense, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Loader2 } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme/ThemeToggle"
import { DEV_AUTH_MODE, devAccounts } from "@/lib/dev"

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  )
}

function LoginForm() {
  const router = useRouter()
  const redirect = useSearchParams().get("redirect") ?? "/"
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)
  const accounts = DEV_AUTH_MODE === "credentials" ? devAccounts() : []

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError("")
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    })
    const data = await res.json().catch(() => ({}))
    setBusy(false)
    if (!res.ok) return setError(data.error ?? "Sign in failed.")
    router.push(redirect)
    router.refresh()
  }

  return (
    <div className="relative flex min-h-[100dvh] items-center justify-center bg-ink px-4 py-12">
      <div className="absolute right-4 top-4"><ThemeToggle /></div>
      <div className="w-full max-w-md">
        <p className="mb-8 text-center font-serif text-[0.95rem] font-semibold tracking-[0.18em] text-bone">
          NYAYRITHM <span className="ml-1 font-mono text-[0.65rem] tracking-widest text-foreground/40">ADMIN</span>
        </p>
        <form onSubmit={submit} className="rounded-lg border border-border bg-ink-raised/80 p-8 shadow-chamber">
          <h1 className="font-serif text-[1.45rem] font-medium tracking-tight text-bone">Operations console</h1>
          <p className="mt-1.5 text-[0.85rem] text-foreground/50">For platform administrators only.</p>

          <div className="mt-6 space-y-4">
            <label className="block space-y-1.5">
              <span className="text-[0.78rem] font-medium text-foreground/60">Email</span>
              <Input type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </label>
            <label className="block space-y-1.5">
              <span className="text-[0.78rem] font-medium text-foreground/60">Password</span>
              <Input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </label>
            {error && <p role="alert" className="text-[0.8rem] text-oxblood-bright">{error}</p>}
            <Button type="submit" className="w-full" disabled={busy}>
              {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" />} Sign in
            </Button>
          </div>
        </form>

        {accounts.length > 0 && (
          <div className="mt-5 rounded-lg border border-dashed border-brass/40 p-4">
            <p className="font-mono text-[0.65rem] uppercase tracking-widest text-brass-text">Development accounts</p>
            <ul className="mt-2 space-y-1.5">
              {accounts.map((a) => (
                <li key={a.email}>
                  <button
                    type="button"
                    onClick={() => { setEmail(a.email); setPassword(a.password) }}
                    className="flex w-full items-baseline justify-between gap-3 text-left text-[0.78rem] text-foreground/65 hover:text-foreground"
                  >
                    <span>{a.role}</span>
                    <span className="font-mono text-[0.7rem] text-foreground/40">{a.email}</span>
                  </button>
                </li>
              ))}
            </ul>
            <p className="mt-2 text-[0.7rem] text-foreground/40">Only the platform admin can sign in here.</p>
          </div>
        )}
      </div>
    </div>
  )
}
