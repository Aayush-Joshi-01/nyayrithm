"use client";

import { useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Play, Pause, Square } from "lucide-react";
import { simulationsApi } from "@/lib/api";
import { useSimulationStore } from "@/store/simulationStore";
import { SimulationWebSocket } from "@/lib/ws";
import { TurnFeed } from "./TurnFeed";
import { AgentPanel } from "./AgentPanel";
import { AgentGraph } from "./AgentGraph";
import { cn } from "@/lib/utils";

export function SimulationShell({ caseId, simId }: { caseId: string; simId: string }) {
  const qc = useQueryClient();
  const { setTurns, setAgents, setGraph, setStatus, handleWsEvent, status, currentTurn } =
    useSimulationStore();

  // Load initial data
  const { data: sim } = useQuery({
    queryKey: ["simulation", simId],
    queryFn: () => simulationsApi.get(simId),
  });

  const { data: turnsData } = useQuery({
    queryKey: ["turns", simId],
    queryFn: () => simulationsApi.listTurns(simId, { size: 200 }),
  });

  const { data: agents } = useQuery({
    queryKey: ["agents", simId],
    queryFn: () => simulationsApi.listAgents(simId),
  });

  const { data: graph } = useQuery({
    queryKey: ["graph", simId],
    queryFn: () => simulationsApi.getGraph(simId),
  });

  useEffect(() => {
    if (turnsData?.items) setTurns(turnsData.items);
  }, [turnsData, setTurns]);

  useEffect(() => {
    if (agents) setAgents(agents);
  }, [agents, setAgents]);

  useEffect(() => {
    if (graph) setGraph(graph);
  }, [graph, setGraph]);

  useEffect(() => {
    if (sim) setStatus(sim.status);
  }, [sim, setStatus]);

  // WebSocket connection
  useEffect(() => {
    const ws = new SimulationWebSocket(simId);
    ws.connect();
    const off = ws.on((event) => {
      handleWsEvent(event);
      if (event.event === "agent.spawned") {
        qc.invalidateQueries({ queryKey: ["graph", simId] });
      }
    });
    return () => { off(); ws.disconnect(); };
  }, [simId, handleWsEvent, qc]);

  const startMutation = useMutation({
    mutationFn: () => simulationsApi.start(simId),
    onSuccess: () => { setStatus("running"); qc.invalidateQueries({ queryKey: ["simulation", simId] }); },
  });
  const pauseMutation = useMutation({
    mutationFn: () => simulationsApi.pause(simId),
    onSuccess: () => setStatus("paused"),
  });
  const stopMutation = useMutation({
    mutationFn: () => simulationsApi.stop(simId),
    onSuccess: () => setStatus("completed"),
  });

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] overflow-hidden">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-card/50 flex-shrink-0">
        <div className="flex items-center gap-3">
          <h2 className="font-semibold text-sm">{sim?.title ?? "Simulation"}</h2>
          <span className={cn(
            "text-xs px-2 py-0.5 rounded-full",
            status === "running" ? "text-emerald-400 bg-emerald-400/10 animate-pulse-slow" :
            status === "paused" ? "text-amber-400 bg-amber-400/10" :
            status === "completed" ? "text-slate-400 bg-slate-400/10" :
            "text-blue-400 bg-blue-400/10"
          )}>
            {status}
          </span>
          <span className="text-xs text-muted-foreground">Turn {currentTurn} / {sim?.max_turns}</span>
        </div>

        <div className="flex items-center gap-2">
          {status === "draft" || status === "paused" ? (
            <button
              onClick={() => startMutation.mutate()}
              disabled={startMutation.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-lg text-xs font-medium transition-colors"
            >
              <Play className="w-3.5 h-3.5" />
              {status === "paused" ? "Resume" : "Start"}
            </button>
          ) : status === "running" ? (
            <button
              onClick={() => pauseMutation.mutate()}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-lg text-xs font-medium transition-colors"
            >
              <Pause className="w-3.5 h-3.5" />
              Pause
            </button>
          ) : null}
          {status !== "completed" && status !== "failed" && (
            <button
              onClick={() => stopMutation.mutate()}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg text-xs font-medium transition-colors"
            >
              <Square className="w-3.5 h-3.5" />
              Stop
            </button>
          )}
        </div>
      </div>

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Agent Panel — left */}
        <AgentPanel simId={simId} />

        {/* Turn Feed — center */}
        <div className="flex-1 flex flex-col overflow-hidden border-r border-border">
          <TurnFeed simId={simId} />
        </div>

        {/* Agent Graph — right */}
        <div className="w-72 flex-shrink-0">
          <AgentGraph />
        </div>
      </div>
    </div>
  );
}
