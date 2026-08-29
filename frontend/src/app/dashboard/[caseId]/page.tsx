"use client"

import { use } from "react"
import { useRouter } from "next/navigation"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import Link from "next/link"
import { FileText, Copy, Trash2, ChevronRight } from "lucide-react"
import { casesApi, simulationsApi } from "@/lib/api"
import { SimulationPrompt } from "@/components/simulation/SimulationPrompt"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { formatDistanceToNow } from "date-fns"
import type { Simulation } from "@/types/api"
import { PageScroll } from "@/components/layout/PageScroll"

const SIM_STATUS: Record<string, { label: string; variant: "success" | "warning" | "muted" | "info" | "outline" | "live" }> = {
  draft: { label: "Draft", variant: "info" },
  running: { label: "In session", variant: "live" },
  paused: { label: "Recessed", variant: "warning" },
  completed: { label: "Adjourned", variant: "muted" },
  failed: { label: "Mistrial", variant: "outline" },
}

const MODE_LABELS: Record<string, string> = {
  courtroom: "Courtroom",
  deposition: "Deposition",
  strategy: "Strategy session",
}

export default function CaseOverviewPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params)
  const qc = useQueryClient()
  const router = useRouter()

  const { data: case_, isLoading: caseLoading } = useQuery({
    queryKey: ["case", caseId],
    queryFn: () => casesApi.get(caseId),
  })

  const { data: sims, isLoading: simsLoading } = useQuery({
    queryKey: ["simulations", caseId],
    queryFn: () => simulationsApi.list(caseId),
    refetchInterval: 5000,
  })

  const refreshSims = () => qc.invalidateQueries({ queryKey: ["simulations", caseId] })

  const deleteMutation = useMutation({
    mutationFn: (simId: string) => simulationsApi.remove(simId),
    onSuccess: refreshSims,
  })

  const cloneMutation = useMutation({
    mutationFn: (simId: string) => simulationsApi.clone(simId),
    onSuccess: (sim) => {
      refreshSims()
      router.push(`/dashboard/${caseId}/simulation/${sim.id}`)
    },
  })

  return (
    <PageScroll>
    <div className="mx-auto max-w-4xl space-y-10">
      {caseLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-8 w-72" />
          <Skeleton className="h-4 w-96" />
        </div>
      ) : case_ ? (
        <div>
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="font-serif text-2xl font-medium tracking-tight text-bone">{case_.title}</h1>
              <p className="mt-1 max-w-xl text-[0.9rem] leading-relaxed text-foreground/50">{case_.description}</p>
            </div>
            <Link href={`/dashboard/${caseId}/evidence`}>
              <Button variant="outline" size="sm" className="flex-shrink-0">
                <FileText className="mr-1.5 h-3.5 w-3.5" strokeWidth={1.75} />
                Evidence
              </Button>
            </Link>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[0.7rem] text-foreground/35">
            <span>{case_.country}</span>
            <span className="text-foreground/15">/</span>
            <span>{case_.legal_system?.replace("_", " ")}</span>
            {case_.jurisdiction && (
              <>
                <span className="text-foreground/15">/</span>
                <span>{case_.jurisdiction}</span>
              </>
            )}
          </div>
        </div>
      ) : null}

      <div className="rounded-lg border border-border bg-ink-raised/60 p-6">
        <h2 className="mb-5 font-mono text-[0.66rem] uppercase tracking-[0.2em] text-foreground/35">
          Convene a proceeding
        </h2>
        <SimulationPrompt caseId={caseId} />
      </div>

      <div>
        <h2 className="mb-4 font-mono text-[0.66rem] uppercase tracking-[0.2em] text-foreground/35">
          On the docket
        </h2>

        {simsLoading ? (
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-16" />)}
          </div>
        ) : sims && sims.length > 0 ? (
          <div className="divide-y divide-hairline border-y border-hairline">
            {sims.map((sim: Simulation) => {
              const cfg = SIM_STATUS[sim.status] ?? SIM_STATUS.draft
              return (
                <div key={sim.id} className="group flex items-center gap-4 py-3.5">
                  <Link
                    href={`/dashboard/${caseId}/simulation/${sim.id}`}
                    className="flex min-w-0 flex-1 items-center gap-4"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-serif text-[0.95rem] font-medium text-foreground/85">{sim.title}</p>
                      <p className="mt-0.5 font-mono text-[0.7rem] text-foreground/35">
                        {MODE_LABELS[sim.mode] ?? sim.mode}
                        <span className="mx-1.5 text-foreground/15">/</span>
                        <span className="tabular">turn {sim.current_turn}/{sim.max_turns}</span>
                      </p>
                    </div>
                    <Badge variant={cfg.variant} className="flex-shrink-0">{cfg.label}</Badge>
                    <span className="hidden flex-shrink-0 font-mono text-[0.68rem] text-foreground/45 sm:inline">
                      {formatDistanceToNow(new Date(sim.created_at), { addSuffix: true })}
                    </span>
                  </Link>
                  <div className="flex flex-shrink-0 items-center gap-3">
                    <button
                      onClick={() => cloneMutation.mutate(sim.id)}
                      disabled={cloneMutation.isPending}
                      title="Clone with a fresh roster and the latest models"
                      className="text-foreground/25 transition-colors hover:text-brass-text"
                    >
                      <Copy className="h-3.5 w-3.5" strokeWidth={1.75} />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`Delete "${sim.title}"? This removes its turns and agents.`))
                          deleteMutation.mutate(sim.id)
                      }}
                      disabled={deleteMutation.isPending}
                      title="Delete this proceeding"
                      className="text-foreground/25 transition-colors hover:text-oxblood-bright"
                    >
                      <Trash2 className="h-3.5 w-3.5" strokeWidth={1.75} />
                    </button>
                    <ChevronRight className="h-3.5 w-3.5 text-foreground/20 opacity-0 transition-opacity group-hover:opacity-100" />
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <p className="py-8 text-center text-[0.88rem] text-foreground/30">
            Nothing on the docket. Describe a scenario above to open the first proceeding.
          </p>
        )}
      </div>
    </div>
    </PageScroll>
  )
}
