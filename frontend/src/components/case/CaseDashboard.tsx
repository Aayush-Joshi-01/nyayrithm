"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { casesApi } from "@/lib/api";
import { CaseCard } from "./CaseCard";
import { CaseCreateModal } from "./CaseCreateModal";
import type { Case } from "@/types/api";

export function CaseDashboard() {
  const [open, setOpen] = useState(false);
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["cases"],
    queryFn: () => casesApi.list({ size: 50 }),
  });

  const createMutation = useMutation({
    mutationFn: casesApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cases"] });
      setOpen(false);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Cases</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage legal cases and courtroom simulations
          </p>
        </div>
        <button
          onClick={() => setOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-400 text-black rounded-lg text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Case
        </button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-48 rounded-xl bg-card border border-border animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.items.map((c: Case) => (
            <CaseCard key={c.id} case_={c} />
          ))}
          {data?.items.length === 0 && (
            <div className="col-span-3 flex flex-col items-center justify-center py-20 text-muted-foreground">
              <p className="text-lg">No cases yet</p>
              <p className="text-sm mt-1">Create your first case to get started</p>
            </div>
          )}
        </div>
      )}

      <CaseCreateModal
        open={open}
        onClose={() => setOpen(false)}
        onSubmit={(data) => createMutation.mutate(data)}
        loading={createMutation.isPending}
      />
    </div>
  );
}
