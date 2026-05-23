"use client";

import { useSimulationStore } from "@/store/simulationStore";
import { ROLE_COLORS, ROLE_HEX, formatRole, cn } from "@/lib/utils";
import type { AgentRole } from "@/types/api";

export function AgentPanel({ simId: _simId }: { simId: string }) {
  const { agents, streaming } = useSimulationStore();

  return (
    <div className="w-56 flex-shrink-0 border-r border-border overflow-y-auto p-3 space-y-2">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider px-1 mb-3">
        Agents ({agents.length})
      </p>
      {agents.map((agent) => {
        const isActive = streaming?.agentId === agent.id;
        return (
          <div
            key={agent.id}
            className={cn(
              "p-2.5 rounded-lg border transition-all",
              isActive
                ? "border-amber-500/40 bg-amber-500/5"
                : "border-transparent hover:border-border hover:bg-accent/20"
            )}
          >
            <div className="flex items-center gap-2 mb-1">
              <div
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: ROLE_HEX[agent.role as AgentRole] ?? "#94a3b8" }}
              />
              <span className="text-xs font-medium truncate">{agent.name}</span>
              {isActive && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse ml-auto" />}
            </div>
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className={cn("text-xs px-1.5 py-0.5 rounded border", ROLE_COLORS[agent.role as AgentRole] ?? "text-slate-400 bg-slate-400/10 border-slate-400/30")}>
                {formatRole(agent.role as AgentRole)}
              </span>
              {!agent.is_predefined && (
                <span className="text-xs text-violet-400 bg-violet-400/10 px-1 py-0.5 rounded">spawned</span>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-1 truncate">
              {agent.llm_provider}/{agent.llm_model.split("-").slice(0, 2).join("-")}
            </p>
          </div>
        );
      })}
    </div>
  );
}
