"use client"

import Link from "next/link"
import { useQuery } from "@tanstack/react-query"
import { adminApi } from "@/lib/api"
import { ErrorNote, Kpi, Loading, PageHeader, Section } from "@/components/kit"
import { fmtCompact, fmtInt, fmtUsd } from "@/lib/utils"
import { cn } from "@/lib/utils"

export default function OverviewPage() {
  const overview = useQuery({ queryKey: ["overview"], queryFn: adminApi.overview })
  const system = useQuery({ queryKey: ["system"], queryFn: adminApi.system, refetchInterval: 30_000 })
  const o = overview.data

  return (
    <>
      <PageHeader title="Overview" intro="Who is on the platform, and what they used this month." />
      <ErrorNote error={overview.error} />
      {overview.isLoading || !o ? (
        <Loading rows={3} />
      ) : (
        <>
          <Section title="Firms and people">
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <Kpi label="Firms" value={fmtInt(o.firms.total)} sub={`${o.firms.active} active · ${o.firms.suspended} suspended`} />
              <Kpi label="People" value={fmtInt(o.users)} sub="active members across firms" />
              <Kpi
                label="Paying"
                value={fmtInt((o.subscriptions.active ?? 0) + (o.subscriptions.trialing ?? 0))}
                sub={`${o.subscriptions.trialing ?? 0} on trial`}
              />
              <Kpi
                label="Needs attention"
                value={fmtInt((o.subscriptions.past_due ?? 0) + (o.subscriptions.cancelled ?? 0))}
                sub={`${o.subscriptions.past_due ?? 0} past due · ${o.subscriptions.cancelled ?? 0} cancelled`}
                tone={(o.subscriptions.past_due ?? 0) > 0 ? "warn" : undefined}
              />
            </div>
          </Section>

          <Section title={`This month (${o.this_month.period})`} hint="across all firms" actions={<Link href="/llmops" className="text-[0.8rem] text-brass-text hover:underline">LLMOps →</Link>}>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <Kpi label="Tokens" value={fmtCompact(o.this_month.tokens)} />
              <Kpi label="Est. model cost" value={fmtUsd(o.this_month.cost_usd)} sub="estimate, see LLMOps" />
              <Kpi label="Simulations" value={fmtInt(o.this_month.simulations)} />
              <Kpi label="Turns" value={fmtInt(o.this_month.turns)} />
            </div>
          </Section>
        </>
      )}

      <Section title="System" actions={<Link href="/system" className="text-[0.8rem] text-brass-text hover:underline">Details →</Link>}>
        {system.isLoading ? (
          <Loading rows={1} />
        ) : (
          <div className="flex flex-wrap gap-2">
            {system.data?.checks.map((c) => (
              <span
                key={c.name}
                title={c.detail || undefined}
                className={cn(
                  "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[0.78rem]",
                  c.ok ? "border-border text-foreground/70" : "border-oxblood-bright/40 text-oxblood-bright",
                )}
              >
                <span className={cn("h-1.5 w-1.5 rounded-full", c.ok ? "bg-role-witness" : "bg-oxblood-bright")} aria-hidden />
                {c.name}
                <span className="sr-only">{c.ok ? "healthy" : "unhealthy"}</span>
              </span>
            ))}
          </div>
        )}
      </Section>
    </>
  )
}
