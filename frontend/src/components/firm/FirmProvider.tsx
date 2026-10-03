"use client"

import { createContext, useCallback, useContext, useMemo, useState } from "react"
import Link from "next/link"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { AlertTriangle, Loader2, LogOut, MailQuestion } from "lucide-react"
import { firmApi } from "@/lib/api"
import { getActiveOrg, setActiveOrg } from "@/lib/firm"
import { IS_DEV, DEV_AUTH_MODE } from "@/lib/dev"
import type { FirmRole, FirmSubscription, FirmSummary, Me } from "@/types/api"

interface FirmContextValue {
  me: Me
  firm: FirmSummary
  role: FirmRole
  isManager: boolean
  subscription: FirmSubscription | undefined
  switchFirm: (orgId: string) => void
}

const FirmContext = createContext<FirmContextValue | null>(null)

export function useFirm(): FirmContextValue {
  const ctx = useContext(FirmContext)
  if (!ctx) throw new Error("useFirm must be used inside <FirmProvider>")
  return ctx
}

const INACTIVE = new Set(["past_due", "cancelled"])

export function FirmProvider({ children }: { children: React.ReactNode }) {
  const qc = useQueryClient()
  const [stored, setStored] = useState<string | null>(() => getActiveOrg())
  const me = useQuery({ queryKey: ["me"], queryFn: firmApi.me, retry: false, staleTime: 60_000 })

  const firm = useMemo(() => {
    const firms = me.data?.firms ?? []
    return firms.find((f) => f.org_id === stored) ?? firms[0]
  }, [me.data, stored])

  const subscription = useQuery({
    queryKey: ["subscription", firm?.org_id],
    queryFn: () => firmApi.subscription(firm!.org_id),
    enabled: !!firm && firm.status === "active",
    refetchInterval: 60_000,
  })

  const switchFirm = useCallback((orgId: string) => {
    setActiveOrg(orgId)
    setStored(orgId)
    qc.clear() // everything cached belonged to the other firm
    qc.invalidateQueries()
  }, [qc])

  if (me.isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-ink" role="status" aria-label="Loading">
        <Loader2 className="h-5 w-5 animate-spin text-foreground/40" />
      </div>
    )
  }
  if (me.isError || !me.data) {
    return <Blocked icon={<AlertTriangle className="h-6 w-6" />} title="We could not reach the server"
      body="Check your connection and reload. If this keeps happening, tell your administrator." />
  }
  if (!firm) {
    return (
      <Blocked
        icon={<MailQuestion className="h-6 w-6" />}
        title="You are not part of a firm yet"
        body={`Nyayrithm is used through a firm's subscription. Ask your firm's administrator to invite ${me.data.user.email ?? "you"}, then open the link in the invitation email.`}
        showSignOut
      />
    )
  }
  if (firm.status === "suspended") {
    return (
      <Blocked
        icon={<AlertTriangle className="h-6 w-6" />}
        title={`${firm.name} is suspended`}
        body="Access to this firm has been paused. Contact your firm's administrator, or Nyayrithm support if you are the administrator."
        showSignOut
      />
    )
  }

  const value: FirmContextValue = {
    me: me.data, firm, role: firm.role, isManager: firm.role === "owner" || firm.role === "admin",
    subscription: subscription.data, switchFirm,
  }
  return <FirmContext.Provider value={value}>{children}</FirmContext.Provider>
}

/** A strip above the page for things the firm needs to know: dev mode, lapsed plan, near quota. */
export function FirmNotices() {
  const { subscription, isManager } = useFirm()
  const notices: { tone: "warn" | "bad" | "dev"; text: React.ReactNode }[] = []

  if (IS_DEV) {
    notices.push({
      tone: "dev",
      text: `Development mode · ${DEV_AUTH_MODE === "open" ? "open access, no login" : "static dev credentials"}`,
    })
  }
  const sub = subscription?.subscription
  if (subscription && (!sub || INACTIVE.has(sub.status))) {
    notices.push({
      tone: "bad",
      text: sub
        ? `Your firm's subscription is ${sub.status.replace("_", " ")}. You can read existing work, but cannot create cases or run proceedings.`
        : "Your firm has no active subscription. You can read existing work, but cannot create cases or run proceedings.",
    })
  } else if (subscription?.plan) {
    const used = subscription.usage.tokens / Math.max(1, subscription.plan.monthly_tokens)
    if (used >= 1) {
      notices.push({ tone: "bad", text: "The firm's monthly token allowance is used up. Running proceedings pause until it renews or the plan is raised." })
    } else if (used >= 0.9) {
      notices.push({ tone: "warn", text: `The firm has used ${Math.round(used * 100)}% of this month's token allowance.` })
    }
    const seats = subscription.seats
    if (isManager && seats.limit > 0 && seats.used + seats.pending >= seats.limit) {
      notices.push({ tone: "warn", text: `All ${seats.limit} seats are taken. Free one up or ask for more to invite someone.` })
    }
  }
  if (notices.length === 0) return null
  return (
    <div className="flex-shrink-0" role="region" aria-label="Notices">
      {notices.map((n, i) => (
        <p
          key={i}
          role={n.tone === "dev" ? "status" : "alert"}
          className={
            n.tone === "bad"
              ? "border-b border-oxblood-bright/30 bg-oxblood-bright/10 px-6 py-2 text-[0.8rem] text-oxblood-bright"
              : n.tone === "warn"
                ? "border-b border-brass/30 bg-brass/10 px-6 py-2 text-[0.8rem] text-brass-text"
                : "border-b border-brass/30 bg-brass/10 px-6 py-1.5 text-center font-mono text-[0.68rem] uppercase tracking-widest text-brass-text"
          }
        >
          {n.text}
        </p>
      ))}
    </div>
  )
}

function Blocked({ icon, title, body, showSignOut }: {
  icon: React.ReactNode; title: string; body: string; showSignOut?: boolean
}) {
  async function signOut() {
    await fetch("/api/auth/logout", { method: "POST" })
    window.location.href = "/login"
  }
  return (
    <div className="flex min-h-screen items-center justify-center bg-ink px-4">
      <div className="w-full max-w-md rounded-lg border border-border bg-ink-raised/80 p-8 text-center shadow-chamber">
        <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-full border border-border text-brass-text">{icon}</div>
        <h1 className="font-serif text-[1.35rem] font-medium text-bone">{title}</h1>
        <p className="mt-2 text-[0.88rem] leading-relaxed text-foreground/55">{body}</p>
        <div className="mt-6 flex justify-center gap-3">
          <Link href="/" className="text-[0.82rem] text-brass-text hover:underline">Back to the site</Link>
          {showSignOut && (
            <button onClick={signOut} className="inline-flex items-center gap-1.5 text-[0.82rem] text-foreground/55 hover:text-foreground">
              <LogOut className="h-3.5 w-3.5" /> Sign out
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
