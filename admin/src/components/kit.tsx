"use client"

import { Loader2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

export function PageHeader({ title, intro, actions }: { title: string; intro?: string; actions?: React.ReactNode }) {
  return (
    <header className="mb-7 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="font-serif text-[1.7rem] font-medium tracking-tight text-bone">{title}</h1>
        {intro && <p className="mt-1 max-w-2xl text-[0.88rem] leading-relaxed text-foreground/50">{intro}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </header>
  )
}

export function Section({
  title, hint, actions, children, className,
}: {
  title: string; hint?: string; actions?: React.ReactNode; children: React.ReactNode; className?: string
}) {
  return (
    <section className={cn("mb-8", className)}>
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-serif text-[1.05rem] font-medium text-bone">
          {title}
          {hint && <span className="ml-2 font-sans text-[0.75rem] font-normal text-foreground/40">{hint}</span>}
        </h2>
        {actions}
      </div>
      {children}
    </section>
  )
}

export function Kpi({
  label, value, sub, tone,
}: {
  label: string; value: React.ReactNode; sub?: React.ReactNode; tone?: "warn" | "bad"
}) {
  return (
    <div className="rounded-md border border-border bg-card/60 px-4 py-3.5">
      <p className="font-mono text-[0.62rem] uppercase tracking-widest text-foreground/40">{label}</p>
      <p
        className={cn(
          "mt-1.5 font-serif text-[1.55rem] leading-none tabular text-bone",
          tone === "warn" && "text-brass-text",
          tone === "bad" && "text-oxblood-bright",
        )}
      >
        {value}
      </p>
      {sub && <p className="mt-1.5 text-[0.74rem] text-foreground/45">{sub}</p>}
    </div>
  )
}

export function Table({
  head, children, empty, rowCount,
}: {
  head: React.ReactNode[]; children: React.ReactNode; empty?: string; rowCount?: number
}) {
  const rows = rowCount ?? (Array.isArray(children) ? children.length : children ? 1 : 0)
  return (
    <div className="overflow-x-auto rounded-md border border-border">
      <table className="w-full min-w-[640px] border-collapse text-[0.84rem]">
        <thead>
          <tr className="border-b border-hairline bg-ink-raised/60 text-left">
            {head.map((h, i) => (
              <th
                key={i}
                className="whitespace-nowrap px-3 py-2.5 font-mono text-[0.62rem] font-medium uppercase tracking-widest text-foreground/40"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="[&>tr:not(:last-child)]:border-b [&>tr]:border-hairline [&>tr:hover]:bg-accent/20">
          {children}
        </tbody>
      </table>
      {rows === 0 && (
        <p className="px-3 py-8 text-center text-[0.84rem] text-foreground/40">{empty ?? "Nothing to show."}</p>
      )}
    </div>
  )
}

export function Td({
  children, className, mono,
}: {
  children?: React.ReactNode; className?: string; mono?: boolean
}) {
  return (
    <td className={cn("px-3 py-2.5 align-middle", mono && "font-mono text-[0.78rem] tabular", className)}>
      {children}
    </td>
  )
}

const STATUS_VARIANT: Record<string, "success" | "warning" | "destructive" | "muted" | "info" | "live"> = {
  active: "success", trialing: "info", past_due: "warning", cancelled: "muted", suspended: "destructive",
  owner: "warning", admin: "info", attorney: "muted", ok: "success", error: "destructive", removed: "muted",
}

export function StatusBadge({ value }: { value: string | null | undefined }) {
  if (!value) return <span className="text-foreground/30">–</span>
  return <Badge variant={STATUS_VARIANT[value] ?? "muted"}>{value.replace("_", " ")}</Badge>
}

export function Loading({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-2" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  )
}

export function Busy() {
  return <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
}

export function ErrorNote({ error }: { error: unknown }) {
  if (!error) return null
  const msg = error instanceof Error ? error.message : String(error)
  return (
    <p role="alert" className="rounded-md border border-oxblood-bright/30 bg-oxblood-bright/10 px-3 py-2 text-[0.82rem] text-oxblood-bright">
      {msg}
    </p>
  )
}

export function Field({ label, children, hint }: { label: string; children: React.ReactNode; hint?: string }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-[0.78rem] font-medium text-foreground/60">{label}</span>
      {children}
      {hint && <span className="block text-[0.72rem] text-foreground/40">{hint}</span>}
    </label>
  )
}

export function UtilBar({ value, label }: { value: number | null; label?: string }) {
  const pct = Math.max(0, Math.min(1, value ?? 0))
  const tone = pct >= 1 ? "bg-oxblood-bright" : pct >= 0.8 ? "bg-brass" : "bg-role-witness"
  return (
    <div className="flex items-center gap-2" title={label}>
      <div
        className="h-1.5 w-24 overflow-hidden rounded-full bg-foreground/10"
        role="img"
        aria-label={label ?? `${Math.round(pct * 100)} percent`}
      >
        <div className={cn("h-full rounded-full", tone)} style={{ width: `${pct * 100}%` }} />
      </div>
      <span className="font-mono text-[0.72rem] tabular text-foreground/55">
        {value == null ? "–" : `${Math.round(pct * 100)}%`}
      </span>
    </div>
  )
}
