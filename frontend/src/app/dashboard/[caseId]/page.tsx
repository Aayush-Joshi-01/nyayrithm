"use client"

import { use } from "react"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import {
  FileText, Play, Globe, Scale, Layers, Clock, ChevronRight,
} from "lucide-react"
import { casesApi, simulationsApi } from "@/lib/api"
import { SimulationPrompt } from "@/components/simulation/SimulationPrompt"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import { formatDistanceToNow } from "date-fns"
import type { Simulation } from "@/types/api"

const SIM_STATUS: Record<string, { label: string; variant: "success" | "warning" | "muted" | "info" | "outline" }> = {
  draft: { label: "Draft", variant: "info" },
  running: { label: "Running", variant: "success" },
  paused: { label: "Paused", variant: "warning" },
  completed: { label: "Completed", variant: "muted" },
  failed: { label: "Failed", variant: "outline" },
}

const MODE_LABELS: Record<string, string> = {
  courtroom: "Courtroom Trial",
  deposition: "Deposition",
  strategy: "Strategy Session",
}

export default function CaseOverviewPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params)

  const { data: case_, isLoading: caseLoading } = useQuery({
    queryKey: ["case", caseId],
    queryFn: () => casesApi.get(caseId),
  })

  const { data: sims, isLoading: simsLoading } = useQuery({
    queryKey: ["simulations", caseId],
    queryFn: () => simulationsApi.list(caseId),
  })

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Case header */}
      {caseLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-8 w-72" />
          <Skeleton className="h-4 w-96" />
          <Skeleton className="h-4 w-48" />
        </div>
      ) : case_ ? (
        <div>
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
                <Scale className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">{case_.title}</h1>
                <p className="text-white/40 text-sm mt-0.5">{case_.description}</p>
              </div>
            </div>
            <Link href={`/dashboard/${caseId}/evidence`}>
              <Button variant="outline" size="sm" className="flex-shrink-0">
                <FileText className="w-3.5 h-3.5 mr-1.5" />
                Evidence
              </Button>
            </Link>
          </div>

          <div className="flex items-center gap-2 mt-4 flex-wrap">
            <span className="inline-flex items-center gap-1.5 text-xs text-white/30">
              <Globe className="w-3.5 h-3.5" />
              {case_.country}
            </span>
            <Badge variant="outline" className="text-xs border-white/10 text-white/30">
              {case_.legal_system?.replace("_", " ")}
            </Badge>
            {case_.jurisdiction && (
              <Badge variant="outline" className="text-xs border-white/10 text-white/30">
                {case_.jurisdiction}
              </Badge>
            )}
          </div>
        </div>
      ) : null}

      {/* New simulation prompt */}
      <div className="rounded-2xl border border-white/10 bg-white/3 p-6">
        <div className="flex items-center gap-2 mb-5">
          <Layers className="w-4 h-4 text-amber-400" />
          <h2 className="text-sm font-semibold text-white/70">Start a simulation</h2>
        </div>
        <SimulationPrompt caseId={caseId} />
      </div>

      {/* Past simulations */}
      <div>
        <h2 className="text-sm font-semibold text-white/40 uppercase tracking-wider mb-3">
          Previous Simulations
        </h2>

        {simsLoading ? (
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-16 rounded-xl" />)}
          </div>
        ) : sims && sims.length > 0 ? (
          <div className="space-y-2">
            {sims.map((sim: Simulation) => {
              const cfg = SIM_STATUS[sim.status] ?? SIM_STATUS.draft
              return (
                <Link
                  key={sim.id}
                  href={`/dashboard/${caseId}/simulation/${sim.id}`}
                >
                  <Card className="hover:border-amber-500/20 transition-all group cursor-pointer">
                    <CardContent className="p-4 flex items-center gap-4">
                      <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center flex-shrink-0">
                        <Play className="w-3.5 h-3.5 text-white/40" />
                      </div>

                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white/80 truncate">{sim.title}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-xs text-white/30">
                            {MODE_LABELS[sim.mode] ?? sim.mode}
                          </span>
                          <span className="text-white/15">·</span>
                          <span className="text-xs text-white/30 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            Turn {sim.current_turn}/{sim.max_turns}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        <Badge variant={cfg.variant} className={cn("text-xs", sim.status === "running" && "animate-pulse-slow")}>
                          {cfg.label}
                        </Badge>
                        <span className="text-xs text-white/20">
                          {formatDistanceToNow(new Date(sim.created_at), { addSuffix: true })}
                        </span>
                        <ChevronRight className="w-3.5 h-3.5 text-white/20 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              )
            })}
          </div>
        ) : (
          <p className="text-sm text-white/25 py-6 text-center">
            No simulations yet — describe a scenario above to begin.
          </p>
        )}
      </div>
    </div>
  )
}
