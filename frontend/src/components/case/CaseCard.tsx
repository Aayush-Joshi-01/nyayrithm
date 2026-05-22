"use client"

import Link from "next/link"
import { Globe, Scale, ArrowRight, FileText, Play } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Card, CardHeader, CardContent, CardFooter } from "@/components/ui/card"
import { formatDistanceToNow } from "date-fns"
import type { Case } from "@/types/api"

const STATUS_CONFIG: Record<string, { label: string; variant: "success" | "warning" | "muted" | "outline" }> = {
  open: { label: "Open", variant: "success" },
  in_simulation: { label: "Simulating", variant: "warning" },
  closed: { label: "Closed", variant: "muted" },
  archived: { label: "Archived", variant: "muted" },
}

const LEGAL_SYSTEM_LABELS: Record<string, string> = {
  common_law: "Common Law",
  civil_law: "Civil Law",
  sharia: "Sharia",
  hybrid: "Hybrid",
}

export function CaseCard({ case_ }: { case_: Case }) {
  const statusCfg = STATUS_CONFIG[case_.status] ?? { label: case_.status, variant: "outline" as const }

  return (
    <Link href={`/dashboard/${case_.id}`}>
      <Card className="group cursor-pointer hover:border-amber-500/30 hover:shadow-lg hover:shadow-amber-500/5 transition-all duration-200 h-full">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center flex-shrink-0">
                <Scale className="w-4 h-4 text-amber-400" />
              </div>
              <Badge variant={statusCfg.variant} className="text-xs">
                {statusCfg.label}
              </Badge>
            </div>
            <ArrowRight className="w-4 h-4 text-white/20 opacity-0 group-hover:opacity-100 group-hover:text-amber-400 transition-all flex-shrink-0 mt-0.5" />
          </div>

          <h3 className="font-semibold text-white/90 line-clamp-2 leading-snug mt-2 text-sm">
            {case_.title}
          </h3>
        </CardHeader>

        <CardContent className="pb-3">
          <p className="text-xs text-white/40 line-clamp-2 leading-relaxed mb-3">
            {case_.description || "No description provided."}
          </p>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="inline-flex items-center gap-1 text-xs text-white/30">
              <Globe className="w-3 h-3" />
              {case_.country}
            </span>
            <Badge variant="outline" className="text-xs border-white/10 text-white/30 bg-transparent">
              {LEGAL_SYSTEM_LABELS[case_.legal_system] ?? case_.legal_system}
            </Badge>
            {case_.jurisdiction && (
              <Badge variant="outline" className="text-xs border-white/10 text-white/30 bg-transparent">
                {case_.jurisdiction}
              </Badge>
            )}
          </div>
        </CardContent>

        <CardFooter className="pt-3 border-t border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-3 text-xs text-white/25">
            <span className="flex items-center gap-1">
              <FileText className="w-3 h-3" />
              Evidence
            </span>
            <span className="flex items-center gap-1">
              <Play className="w-3 h-3" />
              Simulate
            </span>
          </div>
          <span className="text-xs text-white/20">
            {formatDistanceToNow(new Date(case_.created_at), { addSuffix: true })}
          </span>
        </CardFooter>
      </Card>
    </Link>
  )
}
