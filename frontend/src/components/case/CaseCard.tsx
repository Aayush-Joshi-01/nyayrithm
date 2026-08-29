"use client"

import Link from "next/link"
import { formatDistanceToNow } from "date-fns"
import { Badge } from "@/components/ui/badge"
import type { Case } from "@/types/api"

const STATUS_CONFIG: Record<string, { label: string; variant: "success" | "live" | "muted" | "outline" }> = {
  open: { label: "Open", variant: "success" },
  in_simulation: { label: "In session", variant: "live" },
  closed: { label: "Closed", variant: "muted" },
  archived: { label: "Archived", variant: "muted" },
}

const LEGAL_SYSTEM_LABELS: Record<string, string> = {
  common_law: "Common law",
  civil_law: "Civil law",
  sharia: "Sharia",
  hybrid: "Hybrid",
}

export function CaseCard({ case_, stagger = 0 }: { case_: Case; stagger?: number }) {
  const statusCfg = STATUS_CONFIG[case_.status] ?? { label: case_.status, variant: "outline" as const }

  return (
    <Link
      href={`/dashboard/${case_.id}`}
      style={{ "--stagger": stagger } as React.CSSProperties}
      className="stagger-item group flex h-full flex-col rounded-lg border border-border bg-ink-raised p-5 transition-[border-color,transform] duration-200 hover:-translate-y-0.5 hover:border-brass/35"
    >
      <div className="flex items-center justify-between">
        <Badge variant={statusCfg.variant}>{statusCfg.label}</Badge>
        <span className="font-mono text-[0.66rem] text-foreground/45">
          {formatDistanceToNow(new Date(case_.created_at), { addSuffix: true })}
        </span>
      </div>

      <h3 className="mt-3 font-serif text-[1.05rem] font-medium leading-snug text-foreground/90 line-clamp-2">
        {case_.title}
      </h3>
      <p className="mt-2 flex-1 text-[0.83rem] leading-relaxed text-foreground/45 line-clamp-2">
        {case_.description || "No description on file."}
      </p>

      <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-hairline pt-3 font-mono text-[0.68rem] text-foreground/35">
        <span>{case_.country}</span>
        <span className="text-foreground/15">/</span>
        <span>{LEGAL_SYSTEM_LABELS[case_.legal_system] ?? case_.legal_system}</span>
        {case_.jurisdiction && (
          <>
            <span className="text-foreground/15">/</span>
            <span>{case_.jurisdiction}</span>
          </>
        )}
      </div>
    </Link>
  )
}
