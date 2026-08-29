"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Pencil, Check, X } from "lucide-react";
import { useSimulationStore } from "@/store/simulationStore";
import { simulationsApi } from "@/lib/api";
import { roleStyle, roleVar, ROLE_SIGIL, formatRole, cn } from "@/lib/utils";
import { CitationChip } from "../shared/CitationChip";
import type { AgentRole, Turn } from "@/types/api";

/* Provenance for a turn: a cited claim carries at least one citation; a
   human-overridden turn is disputed; everything else is inference on the
   record but not yet tied to a passage. (raise: challenger-provenance-ribbon) */
function turnProv(turn: Turn): "cited" | "inferred" | "disputed" {
  if (turn.is_human_override) return "disputed";
  if ((turn.citations?.length ?? 0) > 0) return "cited";
  return "inferred";
}

function TurnLine({ turn, simId, agentName, role, latest }: {
  turn: Turn;
  simId: string;
  agentName: string;
  role: AgentRole;
  latest: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(turn.content_edited ?? turn.content);
  const qc = useQueryClient();
  const prov = turnProv(turn);

  const editMutation = useMutation({
    mutationFn: (content: string) => simulationsApi.editTurn(simId, turn.id, content),
    onSuccess: () => { setEditing(false); qc.invalidateQueries({ queryKey: ["turns", simId] }); },
  });

  const content = turn.content_edited ?? turn.content;

  return (
    <div
      className={cn(
        "group record-line px-4 py-3.5 hairline-b transition-colors hover:bg-accent/20",
        latest ? "struck" : "afterglow"
      )}
    >
      <div className="lineno">{turn.turn_number}</div>

      <div className="custody-line min-w-0" data-prov={prov}>
        <div className="mb-1.5 flex items-center gap-2">
          <span
            className="grid h-5 w-5 flex-shrink-0 place-items-center rounded-sm border font-mono text-[0.62rem] font-semibold"
            style={roleStyle(role)}
          >
            {ROLE_SIGIL[role]}
          </span>
          <span className="font-serif text-[0.92rem] font-medium text-foreground">{agentName}</span>
          <span
            className="rounded-sm border px-1 py-px font-mono text-[0.6rem] uppercase tracking-wide"
            style={{ color: roleVar(role), borderColor: `color-mix(in srgb, ${roleVar(role)} 30%, transparent)` }}
          >
            {formatRole(role)}
          </span>
          {turn.is_human_override && (
            <span className="rounded-sm bg-oxblood-bright/12 px-1 py-px font-mono text-[0.58rem] uppercase tracking-wide text-oxblood-bright">
              overridden
            </span>
          )}
          <span className="ml-auto flex items-center gap-2 font-mono text-[0.62rem] text-foreground/30 opacity-0 transition-opacity group-hover:opacity-100">
            <span
              className={
                prov === "cited" ? "text-brass-text" : prov === "disputed" ? "text-oxblood-bright" : "text-foreground/45"
              }
            >
              {prov}
            </span>
            <span className="tabular">{turn.latency_ms}ms</span>
            {!editing && (
              <button
                onClick={() => setEditing(true)}
                className="text-foreground/40 hover:text-foreground"
                title="Enter an override"
              >
                <Pencil className="h-3 w-3" strokeWidth={1.75} />
              </button>
            )}
          </span>
        </div>

        {editing ? (
          <div className="space-y-2">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={6}
              className="w-full resize-none rounded-sm border border-border bg-ink-raised px-3 py-2 text-sm leading-relaxed focus:border-brass focus:outline-none"
            />
            <div className="flex gap-2">
              <button
                onClick={() => editMutation.mutate(draft)}
                disabled={editMutation.isPending}
                className="inline-flex items-center gap-1 rounded-sm bg-brass px-3 py-1 text-xs font-semibold text-primary-foreground"
              >
                <Check className="h-3 w-3" strokeWidth={2.5} /> Enter override
              </button>
              <button
                onClick={() => setEditing(false)}
                className="inline-flex items-center gap-1 rounded-sm border border-border px-3 py-1 text-xs text-foreground/55"
              >
                <X className="h-3 w-3" strokeWidth={2} /> Cancel
              </button>
            </div>
          </div>
        ) : (
          <>
            <p className="whitespace-pre-wrap text-[0.9rem] leading-relaxed text-foreground/85">{content}</p>
            {(turn.citations?.length ?? 0) > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {turn.citations.map((c, i) => <CitationChip key={i} citation={c} />)}
              </div>
            )}
          </>
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
        <div className="flex h-full flex-col items-center justify-center px-8 text-center">
          <p className="font-serif text-[1.05rem] text-foreground/55">Nothing is on the record yet.</p>
          <p className="mt-2 max-w-xs text-[0.85rem] leading-relaxed text-foreground/40">
            When the proceeding is called to order, each turn is entered here with
            its citations and its standing in the margin.
          </p>
        </div>
      )}

      {turns.map((turn, i) => {
        const agent = agentMap.get(turn.agent_id);
        return (
          <TurnLine
            key={turn.id}
            turn={turn}
            simId={simId}
            agentName={agent?.name ?? "Unknown agent"}
            role={(agent?.role ?? "custom") as AgentRole}
            latest={i === turns.length - 1 && !streaming}
          />
        );
      })}

      {streaming && (
        <div className="record-line struck px-4 py-3.5">
          <div className="lineno">{turns.length + 1}</div>
          <div className="custody-line arrive min-w-0" data-prov="inferred">
            <div className="mb-1.5 flex items-center gap-2">
              <span
                className="grid h-5 w-5 flex-shrink-0 place-items-center rounded-sm border font-mono text-[0.62rem] font-semibold"
                style={roleStyle((streaming.role as AgentRole) ?? "custom")}
              >
                {ROLE_SIGIL[(streaming.role as AgentRole) ?? "custom"]}
              </span>
              <span className="font-serif text-[0.92rem] font-medium text-foreground">{streaming.agentName}</span>
              <span className="font-mono text-[0.6rem] uppercase tracking-wide text-ember-text">speaking</span>
            </div>
            <p className="streaming-cursor whitespace-pre-wrap text-[0.9rem] leading-relaxed text-foreground/85">
              {streaming.content}
            </p>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
