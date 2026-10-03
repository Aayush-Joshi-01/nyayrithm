"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ShieldCheck, ShieldAlert } from "lucide-react";
import { legalApi } from "@/lib/api";
import { cn } from "@/lib/utils";

/* One slim strip under the header: where the proceeding stands procedurally,
   the standing notice that this is a simulation, and a button that re-derives
   the audit chain and says whether the record has been altered. */
export function ProceedingBar({
  simId,
  currentTurn,
  live,
  disclaimer,
}: {
  simId: string;
  currentTurn: number;
  live: boolean;
  disclaimer?: string;
}) {
  const { data: procedure } = useQuery({
    queryKey: ["procedure", simId],
    queryFn: () => legalApi.procedure(simId),
    refetchInterval: live ? 15000 : false,
  });
  const [checked, setChecked] = useState(false);
  const verify = useMutation({
    mutationFn: () => legalApi.verifyAudit(simId),
    onSuccess: () => setChecked(true),
  });

  const stages = procedure?.enforced ? procedure.stages : [];
  const stage = stages.find((s) => currentTurn >= s.start_turn && currentTurn <= s.end_turn)
    ?? stages[stages.length - 1];
  const stageIndex = stage ? stages.indexOf(stage) : -1;
  const result = verify.data;

  return (
    <div className="flex flex-shrink-0 flex-wrap items-center gap-x-4 gap-y-1 border-b border-hairline px-4 py-1.5 text-[0.7rem]">
      {stage && (
        <div className="flex items-center gap-2" title={stage.note ?? undefined}>
          <span className="font-mono uppercase tracking-wide text-foreground/35">stage</span>
          <span className="font-serif text-[0.8rem] text-foreground/80">{stage.label}</span>
          <span className="font-mono text-foreground/35 tabular">
            {stageIndex + 1}/{stages.length}
          </span>
          <span className="hidden gap-0.5 sm:flex" aria-hidden>
            {stages.map((s, i) => (
              <span
                key={s.key}
                className={cn(
                  "h-1 w-4 rounded-full",
                  i < stageIndex ? "bg-brass-text/60" : i === stageIndex ? "bg-ember-text" : "bg-foreground/10",
                )}
              />
            ))}
          </span>
        </div>
      )}

      <span
        className="min-w-0 flex-1 truncate text-foreground/40"
        title={disclaimer}
      >
        Simulation for training and education — not legal advice. Verify every authority.
      </span>

      <button
        onClick={() => verify.mutate()}
        disabled={verify.isPending}
        className={cn(
          "inline-flex items-center gap-1 font-mono transition-colors",
          checked && result?.valid === false
            ? "text-oxblood-bright"
            : checked
              ? "text-brass-text"
              : "text-foreground/45 hover:text-foreground/80",
        )}
        title="Recompute the hash chain over every recorded event"
      >
        {checked && result?.valid === false ? (
          <ShieldAlert className="h-3 w-3" strokeWidth={1.75} />
        ) : (
          <ShieldCheck className="h-3 w-3" strokeWidth={1.75} />
        )}
        {verify.isPending
          ? "checking…"
          : !checked || !result
            ? "verify record"
            : result.valid
              ? `record intact · ${result.events} events · ${result.head_hash?.slice(0, 8) ?? ""}`
              : `record altered at event ${result.broken_at}`}
      </button>
    </div>
  );
}
