"use client";

import { use } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { FileText, Play, Plus } from "lucide-react";
import { casesApi, simulationsApi } from "@/lib/api";
import { CaseCreateModal } from "@/components/case/CaseCreateModal";
import { useState } from "react";

export default function CaseOverviewPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  const [showSim, setShowSim] = useState(false);
  const qc = useQueryClient();

  const { data: case_ } = useQuery({
    queryKey: ["case", caseId],
    queryFn: () => casesApi.get(caseId),
  });

  const { data: sims } = useQuery({
    queryKey: ["simulations", caseId],
    queryFn: () => simulationsApi.list(caseId),
  });

  const createSim = useMutation({
    mutationFn: (body: { title: string; mode?: string }) =>
      simulationsApi.create(caseId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["simulations", caseId] });
      setShowSim(false);
    },
  });

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Case header */}
      <div>
        <h1 className="text-2xl font-bold">{case_?.title}</h1>
        <p className="text-muted-foreground mt-1">{case_?.description}</p>
        <div className="flex gap-3 mt-3 text-sm text-muted-foreground">
          <span>{case_?.country}</span>
          <span>·</span>
          <span>{case_?.legal_system?.replace("_", " ")}</span>
          <span>·</span>
          <span>{case_?.jurisdiction}</span>
        </div>
      </div>

      {/* Quick links */}
      <div className="flex gap-3">
        <Link
          href={`/dashboard/${caseId}/evidence`}
          className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg text-sm hover:bg-accent/20 transition-colors"
        >
          <FileText className="w-4 h-4" />
          Manage Evidence
        </Link>
        <button
          onClick={() => setShowSim(true)}
          className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-400 text-black rounded-lg text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Simulation
        </button>
      </div>

      {/* Simulations */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Simulations</h2>
        <div className="space-y-2">
          {sims?.map((sim) => (
            <Link
              key={sim.id}
              href={`/dashboard/${caseId}/simulation/${sim.id}`}
              className="flex items-center gap-4 p-4 rounded-lg border border-border bg-card hover:border-amber-500/30 transition-colors"
            >
              <Play className="w-4 h-4 text-muted-foreground" />
              <div className="flex-1">
                <p className="text-sm font-medium">{sim.title}</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {sim.mode} · Turn {sim.current_turn}/{sim.max_turns}
                </p>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full ${
                sim.status === "running" ? "text-emerald-400 bg-emerald-400/10" :
                sim.status === "completed" ? "text-slate-400 bg-slate-400/10" :
                "text-amber-400 bg-amber-400/10"
              }`}>
                {sim.status}
              </span>
            </Link>
          ))}
          {sims?.length === 0 && (
            <p className="text-sm text-muted-foreground py-6 text-center">
              No simulations yet — create one to begin
            </p>
          )}
        </div>
      </div>

      {/* Create simulation modal (reuses CaseCreateModal pattern) */}
      {showSim && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/60" onClick={() => setShowSim(false)} />
          <div className="relative w-full max-w-sm mx-4 bg-card border border-border rounded-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold">New Simulation</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const fd = new FormData(e.currentTarget);
                createSim.mutate({
                  title: fd.get("title") as string,
                  mode: fd.get("mode") as string,
                });
              }}
              className="space-y-3"
            >
              <input
                name="title"
                required
                placeholder="Simulation title"
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm"
              />
              <select name="mode" className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm">
                <option value="courtroom">Courtroom</option>
                <option value="deposition">Deposition</option>
                <option value="strategy">Strategy Session</option>
              </select>
              <button
                type="submit"
                disabled={createSim.isPending}
                className="w-full py-2 bg-amber-500 hover:bg-amber-400 text-black rounded-lg text-sm font-medium"
              >
                {createSim.isPending ? "Creating..." : "Create"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
