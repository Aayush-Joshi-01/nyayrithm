"use client"

import { useQuery } from "@tanstack/react-query"
import { firmApi } from "@/lib/api"
import { useFirm } from "@/components/firm/FirmProvider"
import { PageScroll } from "@/components/layout/PageScroll"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

const compact = (n: number) => new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(n)
const date = (v: string | null) => (v ? new Date(v).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }) : "No end date")

function Meter({ label, used, limit, format = (n: number) => String(n) }: {
  label: string; used: number; limit: number; format?: (n: number) => string
}) {
  const pct = limit > 0 ? Math.min(1, used / limit) : 0
  const tone = pct >= 1 ? "bg-oxblood-bright" : pct >= 0.9 ? "bg-brass" : "bg-role-witness"
  return (
    <div className="rounded-md border border-border p-4">
      <div className="flex items-baseline justify-between">
        <p className="font-mono text-[0.62rem] uppercase tracking-widest text-foreground/40">{label}</p>
        <p className="font-mono text-[0.78rem] tabular text-foreground/60">{format(used)} / {format(limit)}</p>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-foreground/10" role="img" aria-label={`${label}: ${Math.round(pct * 100)} percent used`}>
        <div className={cn("h-full rounded-full transition-[width]", tone)} style={{ width: `${pct * 100}%` }} />
      </div>
    </div>
  )
}

export default function BillingPage() {
  const { firm } = useFirm()
  const q = useQuery({ queryKey: ["subscription", firm.org_id], queryFn: () => firmApi.subscription(firm.org_id) })
  const d = q.data
  const sub = d?.subscription
  const plan = d?.plan
  const ok = sub && (sub.status === "active" || sub.status === "trialing")

  return (
    <PageScroll>
      <div className="mx-auto w-full max-w-4xl px-6 py-8">
        <header className="mb-7">
          <h1 className="font-serif text-[1.6rem] font-medium tracking-tight text-bone">Plan &amp; usage</h1>
          <p className="mt-1 text-[0.88rem] text-foreground/50">What {firm.name} has subscribed to, and how much of it this month has been used.</p>
        </header>

        {q.isLoading || !d ? (
          <p className="text-foreground/40">Loading…</p>
        ) : !sub || !plan ? (
          <p role="alert" className="rounded-md border border-oxblood-bright/30 bg-oxblood-bright/10 px-4 py-3 text-[0.88rem] text-oxblood-bright">
            This firm has no subscription. Contact Nyayrithm to set one up.
          </p>
        ) : (
          <>
            <div className="mb-6 rounded-md border border-border bg-card/60 p-5">
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="font-serif text-[1.3rem] text-bone">{plan.name}</h2>
                <Badge variant={ok ? "success" : "destructive"}>{sub.status.replace("_", " ")}</Badge>
              </div>
              <dl className="mt-4 grid gap-x-8 gap-y-3 text-[0.84rem] sm:grid-cols-3">
                <div><dt className="text-foreground/40">Seats</dt><dd className="text-bone tabular">{sub.seats}</dd></div>
                <div><dt className="text-foreground/40">Paid until</dt><dd className="text-bone">{date(sub.current_period_end)}</dd></div>
                <div><dt className="text-foreground/40">Invoice</dt><dd className="font-mono text-bone">{sub.invoice_ref || "–"}</dd></div>
              </dl>
              <p className="mt-4 text-[0.78rem] leading-relaxed text-foreground/40">
                Plans are arranged with Nyayrithm directly and invoiced offline. To change seats, renew, or move plan, contact support and quote the invoice reference.
              </p>
            </div>

            <h2 className="mb-3 font-serif text-[1.05rem] text-bone">This month <span className="ml-1 font-sans text-[0.75rem] text-foreground/40">{d.usage.period}</span></h2>
            <div className="mb-8 grid gap-3 sm:grid-cols-2">
              <Meter label="Tokens" used={d.usage.tokens} limit={plan.monthly_tokens} format={compact} />
              <Meter label="Simulations started" used={d.usage.simulations} limit={plan.monthly_simulations} />
              <Meter label="Seats" used={d.seats.used + d.seats.pending} limit={d.seats.limit} />
              <Meter label="Evidence storage" used={Math.round((d.storage_used_bytes ?? 0) / 1048576)} limit={plan.storage_mb} format={(n) => `${n} MB`} />
            </div>

            <h2 className="mb-3 font-serif text-[1.05rem] text-bone">Limits on this plan</h2>
            <ul className="space-y-1.5 text-[0.85rem] text-foreground/60">
              <li>Up to <span className="text-bone tabular">{plan.max_turns_per_sim}</span> turns in a single proceeding.</li>
              <li>Allowances reset on the first of each month. A proceeding pauses, and can be resumed, when the token allowance runs out.</li>
            </ul>
          </>
        )}
      </div>
    </PageScroll>
  )
}
