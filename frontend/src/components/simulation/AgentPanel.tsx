"use client";

import { useSimulationStore } from "@/store/simulationStore";
import { roleStyle, roleVar, ROLE_SIGIL, formatRole, cn } from "@/lib/utils";
import type { AgentRole } from "@/types/api";

export function AgentPanel({ simId: _simId }: { simId: string }) {
  const { agents, streaming } = useSimulationStore();

  return (
    <div className="w-60 flex-shrink-0 overflow-y-auto border-r border-hairline p-3">
      <p className="mb-3 px-1 font-mono text-[0.62rem] uppercase tracking-[0.2em] text-foreground/30">
        The bench, {agents.length}
      </p>
      <div className="space-y-0.5">
        {agents.map((agent) => {
          const role = agent.role as AgentRole;
          const active = streaming?.agentId === agent.id;
          const dormant = agent.status === "suspended" || agent.status === "dismissed";
          return (
            <div
              key={agent.id}
              className={cn(
                "rounded-sm px-2.5 py-2 transition-colors",
                active && "bg-ember/[0.06] shadow-[inset_2px_0_0_0_#FF7A3D]",
                dormant && "ghost"
              )}
            >
              <div className="mb-1 flex items-center gap-2">
                <span
                  className="grid h-4 w-4 flex-shrink-0 place-items-center rounded-sm border font-mono text-[0.56rem] font-semibold"
                  style={roleStyle(role)}
                >
                  {ROLE_SIGIL[role]}
                </span>
                <span className="truncate text-[0.8rem] font-medium text-foreground/85">{agent.name}</span>
                {active && <span className="ml-auto h-1.5 w-1.5 flex-shrink-0 rounded-full bg-ember" />}
              </div>
              <div className="flex flex-wrap items-center gap-1">
                <span
                  className="rounded-sm border px-1 py-px font-mono text-[0.56rem] uppercase tracking-wide"
                  style={{ color: roleVar(role), borderColor: `color-mix(in srgb, ${roleVar(role)} 30%, transparent)` }}
                >
                  {formatRole(role)}
                </span>
                {!agent.is_predefined && (
                  <span className="rounded-sm border border-hairline px-1 py-px font-mono text-[0.56rem] uppercase tracking-wide text-foreground/40">
                    spawned
                  </span>
                )}
              </div>
              <p className="mt-1 truncate font-mono text-[0.64rem] text-foreground/30">
                {agent.llm_provider}/{agent.llm_model.split("-").slice(0, 2).join("-")}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
