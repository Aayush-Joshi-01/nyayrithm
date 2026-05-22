"use client"

import { useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Play, Pause, Square, Share2 } from "lucide-react"
import { simulationsApi } from "@/lib/api"
import { useSimulationStore } from "@/store/simulationStore"
import { SimulationWebSocket } from "@/lib/ws"
import { TurnFeed } from "./TurnFeed"
import { AgentPanel } from "./AgentPanel"
import { AgentGraph } from "./AgentGraph"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"

const STATUS_BADGE: Record<string, { label: string; variant: "success" | "warning" | "muted" | "info" | "outline" }> = {
  draft: { label: "Draft", variant: "info" },
  running: { label: "Running", variant: "success" },
  paused: { label: "Paused", variant: "warning" },
  completed: { label: "Completed", variant: "muted" },
  failed: { label: "Failed", variant: "outline" },
}

export function SimulationShell({ simId }: { caseId: string; simId: string }) {
  const qc = useQueryClient()
  const { setTurns, setAgents, setGraph, setStatus, handleWsEvent, status, currentTurn } =
    useSimulationStore()

  const { data: sim } = useQuery({
    queryKey: ["simulation", simId],
    queryFn: () => simulationsApi.get(simId),
  })
  const { data: turnsData } = useQuery({
    queryKey: ["turns", simId],
    queryFn: () => simulationsApi.listTurns(simId, { size: 200 }),
  })
  const { data: agents } = useQuery({
    queryKey: ["agents", simId],
    queryFn: () => simulationsApi.listAgents(simId),
  })
  const { data: graph } = useQuery({
    queryKey: ["graph", simId],
    queryFn: () => simulationsApi.getGraph(simId),
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
    onSuccess: () => { setStatus("running"); qc.invalidateQueries({ queryKey: ["simulation", simId] }) },
  })
  const pauseMutation = useMutation({
    mutationFn: () => simulationsApi.pause(simId),
    onSuccess: () => setStatus("paused"),
  })
  const stopMutation = useMutation({
    mutationFn: () => simulationsApi.stop(simId),
    onSuccess: () => setStatus("completed"),
  })

  const statusCfg = STATUS_BADGE[status] ?? STATUS_BADGE.draft

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/8 bg-card/50 backdrop-blur-sm flex-shrink-0 gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <h2 className="font-semibold text-sm text-white/90 truncate">
            {sim?.title ?? "Simulation"}
          </h2>
          <Badge variant={statusCfg.variant} className={cn("text-xs flex-shrink-0", status === "running" && "animate-pulse-slow")}>
            {statusCfg.label}
          </Badge>
          <span className="text-xs text-white/30 flex-shrink-0 hidden sm:block">
            Turn {currentTurn} / {sim?.max_turns ?? "—"}
          </span>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {(status === "draft" || status === "paused") && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => startMutation.mutate()}
              disabled={startMutation.isPending}
              className="text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/10 h-8"
            >
              <Play className="w-3.5 h-3.5 mr-1" />
              {status === "paused" ? "Resume" : "Start"}
            </Button>
          )}
          {status === "running" && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => pauseMutation.mutate()}
              className="text-amber-400 border border-amber-500/30 hover:bg-amber-500/10 h-8"
            >
              <Pause className="w-3.5 h-3.5 mr-1" />
              Pause
            </Button>
          )}
          {status !== "completed" && status !== "failed" && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => stopMutation.mutate()}
              className="text-red-400 border border-red-500/30 hover:bg-red-500/10 h-8"
            >
              <Square className="w-3.5 h-3.5 mr-1" />
              Stop
            </Button>
          )}
          <Button size="sm" variant="ghost" className="text-white/30 h-8 w-8 p-0">
            <Share2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      {/* Main */}
      <Tabs defaultValue="courtroom" className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-shrink-0 border-b border-white/8 px-4 py-1.5 bg-card/30">
          <TabsList className="h-8 bg-white/5 gap-1">
            <TabsTrigger value="courtroom" className="text-xs h-6 px-3 data-[state=active]:bg-white/10">
              Courtroom
            </TabsTrigger>
            <TabsTrigger value="graph" className="text-xs h-6 px-3 data-[state=active]:bg-white/10">
              Agent Graph
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="courtroom" className="flex-1 flex overflow-hidden m-0 mt-0">
          <AgentPanel simId={simId} />
          <div className="flex-1 flex flex-col overflow-hidden">
            <TurnFeed simId={simId} />
          </div>
        </TabsContent>

        <TabsContent value="graph" className="flex-1 overflow-hidden m-0 mt-0">
          <AgentGraph />
        </TabsContent>
      </Tabs>
    </div>
  )
}
