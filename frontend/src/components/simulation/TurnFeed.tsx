"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Edit3, Check, X } from "lucide-react";
import { useSimulationStore } from "@/store/simulationStore";
import { simulationsApi } from "@/lib/api";
import { ROLE_COLORS, ROLE_HEX, formatRole, cn } from "@/lib/utils";
import { CitationChip } from "../shared/CitationChip";
import type { AgentRole, Turn } from "@/types/api";

function TurnBubble({ turn, simId, agentName, role }: {
  turn: Turn;
  simId: string;
  agentName: string;
  role: AgentRole;
}) {
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState(turn.content_edited ?? turn.content);
  const qc = useQueryClient();

  const editMutation = useMutation({
    mutationFn: (content: string) => simulationsApi.editTurn(simId, turn.id, content),
    onSuccess: () => { setEditing(false); qc.invalidateQueries({ queryKey: ["turns", simId] }); },
  });

  const displayContent = turn.content_edited ?? turn.content;

  return (
    <div className="group px-4 py-3 hover:bg-accent/10 transition-colors">
      <div className="flex items-start gap-3 max-w-4xl">
        {/* Role avatar */}
        <div
          className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold mt-0.5"
          style={{ backgroundColor: `${ROLE_HEX[role]}20`, color: ROLE_HEX[role], border: `1px solid ${ROLE_HEX[role]}40` }}
        >
          {agentName[0]?.toUpperCase()}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-semibold text-foreground">{agentName}</span>
            <span className={cn("text-xs px-1.5 py-0.5 rounded border", ROLE_COLORS[role])}>
              {formatRole(role)}
            </span>
            {turn.is_human_override && (
              <span className="text-xs text-violet-400 bg-violet-400/10 px-1.5 py-0.5 rounded">edited</span>
            )}
            <span className="text-xs text-muted-foreground ml-auto opacity-0 group-hover:opacity-100 transition-opacity">
              Turn {turn.turn_number} · {turn.latency_ms}ms
            </span>
          </div>

          {editing ? (
            <div className="space-y-2">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                rows={6}
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500 resize-none"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => editMutation.mutate(editContent)}
                  disabled={editMutation.isPending}
                  className="flex items-center gap-1 px-3 py-1 bg-amber-500 text-black rounded text-xs font-medium"
                >
                  <Check className="w-3 h-3" /> Save
                </button>
                <button
                  onClick={() => setEditing(false)}
                  className="flex items-center gap-1 px-3 py-1 border border-border rounded text-xs text-muted-foreground"
                >
                  <X className="w-3 h-3" /> Cancel
                </button>
              </div>
            </div>
          ) : (
            <>
              <p className="text-sm text-foreground/90 leading-relaxed whitespace-pre-wrap">{displayContent}</p>
              {(turn.citations?.length ?? 0) > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {turn.citations.map((c, i) => <CitationChip key={i} citation={c} />)}
                </div>
              )}
            </>
          )}
        </div>

        {!editing && (
          <button
            onClick={() => setEditing(true)}
            className="opacity-0 group-hover:opacity-100 transition-opacity mt-0.5 text-muted-foreground hover:text-foreground"
            title="Edit statement"
          >
            <Edit3 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}

export function TurnFeed({ simId }: { simId: string }) {
  const { turns, streaming, agents } = useSimulationStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, streaming]);

  const agentMap = new Map(agents.map((a) => [a.id, a]));

  return (
    <div className="flex-1 overflow-y-auto">
      {turns.length === 0 && !streaming && (
        <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
          Start the simulation to begin proceedings
        </div>
      )}

      {turns.map((turn) => {
        const agent = agentMap.get(turn.agent_id);
        return (
          <TurnBubble
            key={turn.id}
            turn={turn}
            simId={simId}
            agentName={agent?.name ?? "Unknown Agent"}
            role={(agent?.role ?? "custom") as AgentRole}
          />
        );
      })}

      {/* Streaming turn */}
      {streaming && (
        <div className="px-4 py-3 bg-accent/5">
          <div className="flex items-start gap-3 max-w-4xl">
            <div
              className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold mt-0.5"
              style={{ backgroundColor: `${ROLE_HEX[streaming.role as AgentRole] ?? "#94a3b8"}20`, color: ROLE_HEX[streaming.role as AgentRole] ?? "#94a3b8" }}
            >
              {streaming.agentName[0]?.toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-semibold">{streaming.agentName}</span>
                <span className={cn("text-xs px-1.5 py-0.5 rounded border", ROLE_COLORS[streaming.role as AgentRole] ?? "text-slate-400")}>
                  {formatRole(streaming.role as AgentRole)}
                </span>
                <span className="text-xs text-muted-foreground animate-pulse">typing...</span>
              </div>
              <p className="text-sm text-foreground/90 leading-relaxed whitespace-pre-wrap streaming-cursor">
                {streaming.content}
              </p>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
