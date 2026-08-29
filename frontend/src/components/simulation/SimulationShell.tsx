"use client"

import { useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Play, Pause, Square, X } from "lucide-react"
import { simulationsApi } from "@/lib/api"
import { useSimulationStore } from "@/store/simulationStore"
import { SimulationWebSocket } from "@/lib/ws"
import { TurnFeed } from "./TurnFeed"
import { AgentPanel } from "./AgentPanel"
import { AgentGraph } from "./AgentGraph"
import { AgentSetup } from "./AgentSetup"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"

const STATUS_BADGE: Record<string, { label: string; variant: "success" | "warning" | "muted" | "info" | "outline" | "live" }> = {
  draft: { label: "Draft", variant: "info" },
  running: { label: "In session", variant: "live" },
  paused: { label: "Recessed", variant: "warning" },
  completed: { label: "Adjourned", variant: "muted" },
  failed: { label: "Mistrial", variant: "outline" },
}

export function SimulationShell({ simId }: { caseId: string; simId: string }) {
  const qc = useQueryClient()
  const { setTurns, setAgents, setGraph, setStatus, handleWsEvent, status, currentTurn, error, clearError } =
    useSimulationStore()

  const live = status === "running"

  const { data: sim } = useQuery({
    queryKey: ["simulation", simId],
    queryFn: () => simulationsApi.get(simId),
    refetchInterval: live ? 5000 : false,
  })
  const { data: turnsData } = useQuery({
    queryKey: ["turns", simId],
    queryFn: () => simulationsApi.listTurns(simId, { size: 200 }),
    refetchInterval: live ? 5000 : false,
  })
  const { data: agents } = useQuery({
    queryKey: ["agents", simId],
    queryFn: () => simulationsApi.listAgents(simId),
    refetchInterval: live ? 5000 : false,
  })
  const { data: graph } = useQuery({
    queryKey: ["graph", simId],
    queryFn: () => simulationsApi.getGraph(simId),
    refetchInterval: live ? 5000 : false,
  })

  useEffect(() => { if (turnsData?.items) setTurns(turnsData.items) }, [turnsData, setTurns])
  useEffect(() => { if (agents) setAgents(agents) }, [agents, setAgents])
  useEffect(() => { if (graph) setGraph(graph) }, [graph, setGraph])
  useEffect(() => { if (sim) setStatus(sim.status) }, [sim, setStatus])

  useEffect(() => {
    const ws = new SimulationWebSocket(simId)
    ws.connect()
    const off = ws.on((event) => {
      handleWsEvent(event)
      if (event.event === "agent.spawned") qc.invalidateQueries({ queryKey: ["graph", simId] })
    })
    return () => { off(); ws.disconnect() }
  }, [simId, handleWsEvent, qc])

  const startMutation = useMutation({
    mutationFn: () => simulationsApi.start(simId),
    onSuccess: () => { clearError(); setStatus("running"); qc.invalidateQueries({ queryKey: ["simulation", simId] }) },
    onError: () => useSimulationStore.setState({ error: "Failed to start the simulation." }),
  })
  const pauseMutation = useMutation({
    mutationFn: () => simulationsApi.pause(simId),
    onSuccess: () => setStatus("paused"),
    onError: () => useSimulationStore.setState({ error: "Failed to pause." }),
  })
  const stopMutation = useMutation({
    mutationFn: () => simulationsApi.stop(simId),
    onSuccess: () => setStatus("completed"),
    onError: () => useSimulationStore.setState({ error: "Failed to stop." }),
  })

  const statusCfg = STATUS_BADGE[status] ?? STATUS_BADGE.draft

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      {/* Header */}
      <div className="podium-edge flex flex-shrink-0 items-center justify-between gap-3 px-4 py-3">
        <div className="flex min-w-0 items-center gap-3">
          <h2 className="truncate font-serif text-[0.95rem] font-medium text-foreground">
            {sim?.title ?? "Proceeding"}
          </h2>
          <Badge variant={statusCfg.variant} className="flex-shrink-0">
            {statusCfg.label}
          </Badge>
          <span className="hidden flex-shrink-0 font-mono text-[0.72rem] text-foreground/35 tabular sm:block">
            turn {currentTurn} / {sim?.max_turns ?? "?"}
          </span>
        </div>

        <div className="flex flex-shrink-0 items-center gap-2">
          {(status === "paused" || status === "failed") && (
            <Button size="sm" variant="outline" onClick={() => startMutation.mutate()} disabled={startMutation.isPending}>
              <Play className="mr-1 h-3.5 w-3.5" strokeWidth={2} />
              Resume
            </Button>
          )}
          {status === "running" && (
            <Button size="sm" variant="outline" onClick={() => pauseMutation.mutate()}>
              <Pause className="mr-1 h-3.5 w-3.5" strokeWidth={2} />
              Recess
            </Button>
          )}
          {(status === "running" || status === "paused") && (
            <Button size="sm" variant="destructive" onClick={() => stopMutation.mutate()}>
              <Square className="mr-1 h-3.5 w-3.5" strokeWidth={2} />
              Adjourn
            </Button>
          )}
        </div>
      </div>

      {error && (
        <div className="flex flex-shrink-0 items-center justify-between gap-3 border-b border-oxblood-bright/30 bg-oxblood-bright/10 px-4 py-2 text-xs text-oxblood-bright">
          <span className="truncate">{error}</span>
          <button onClick={clearError} className="flex-shrink-0 opacity-70 hover:opacity-100">
            <X className="h-3 w-3" strokeWidth={2} />
          </button>
        </div>
      )}

      {status === "draft" ? (
        <div className="flex-1 overflow-y-auto">
          <AgentSetup simId={simId} onStarted={() => setStatus("running")} />
        </div>
      ) : (
      /* Main */
      <Tabs defaultValue="courtroom" className="flex flex-1 flex-col overflow-hidden">
        <div className="flex-shrink-0 border-b border-hairline px-4 py-1.5">
          <TabsList>
            <TabsTrigger value="courtroom">The record</TabsTrigger>
            <TabsTrigger value="graph">The spawn graph</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="courtroom" className="m-0 mt-0 flex min-h-0 flex-1 overflow-hidden data-[state=inactive]:hidden">
          <AgentPanel simId={simId} />
          <div className="flex flex-1 flex-col overflow-hidden">
            <TurnFeed simId={simId} />
          </div>
        </TabsContent>

        <TabsContent value="graph" className="m-0 mt-0 flex min-h-0 flex-1 overflow-hidden data-[state=inactive]:hidden">
          <AgentGraph />
        </TabsContent>
      </Tabs>
      )}
    </div>
  )
}
