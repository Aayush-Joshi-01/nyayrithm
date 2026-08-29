"use client";

import Link from "next/link";
import { useQuery, useQueries } from "@tanstack/react-query";
import { FolderOpen, FileText, ArrowRight } from "lucide-react";
import { casesApi, evidenceApi } from "@/lib/api";
import { cn, formatBytes } from "@/lib/utils";
import type { Evidence } from "@/types/api";

const STATUS_STYLES: Record<string, string> = {
  pending: "text-slate-400 bg-slate-400/10",
  processing: "text-amber-400 bg-amber-400/10",
  indexed: "text-emerald-400 bg-emerald-400/10",
  error: "text-red-400 bg-red-400/10",
};

export default function EvidencePage() {
  const { data: casesData, isLoading: casesLoading } = useQuery({
    queryKey: ["cases"],
    queryFn: () => casesApi.list({ size: 100 }),
  });

  const cases = casesData?.items ?? [];

  const evidenceQueries = useQueries({
    queries: cases.map((c) => ({
      queryKey: ["evidence", c.id],
      queryFn: () => evidenceApi.list(c.id, { size: 100 }),
      refetchInterval: 5000,
    })),
  });

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
          <FolderOpen className="w-5 h-5 text-white/50" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Evidence</h1>
          <p className="text-white/40 text-sm mt-0.5">All evidence across your cases</p>
        </div>
      </div>

      {casesLoading && (
        <div className="space-y-2">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="h-24 rounded-xl bg-white/5 border border-white/10 animate-pulse" />
          ))}
        </div>
      )}

      {!casesLoading && cases.length === 0 && (
        <div className="rounded-2xl border border-white/10 bg-white/3 p-8 text-center">
          <p className="text-white/30 text-sm">No cases yet. Create a case to add evidence.</p>
        </div>
      )}

      {cases.map((c, i) => {
        const items = evidenceQueries[i]?.data?.items ?? [];
        return (
          <div key={c.id} className="rounded-xl border border-white/10 bg-white/3 overflow-hidden">
            <Link
              href={`/dashboard/${c.id}/evidence`}
              className="flex items-center justify-between px-4 py-3 border-b border-white/8 hover:bg-white/5 transition-colors"
            >
              <span className="text-sm font-semibold text-white/90">{c.title}</span>
              <span className="flex items-center gap-1 text-xs text-white/40">
                {items.length} item{items.length === 1 ? "" : "s"} · manage
                <ArrowRight className="w-3.5 h-3.5" />
              </span>
            </Link>

            {items.length === 0 ? (
              <p className="px-4 py-3 text-xs text-white/25">No evidence uploaded for this case.</p>
            ) : (
              <div className="divide-y divide-white/5">
                {items.map((ev: Evidence) => (
                  <div key={ev.id} className="flex items-center gap-3 px-4 py-2.5">
                    <FileText className="w-4 h-4 text-white/30 flex-shrink-0" />
                    <span className="text-sm text-white/80 flex-1 truncate">{ev.title}</span>
                    <span className="text-xs text-white/30">{formatBytes(ev.file_size)}</span>
                    {ev.chunk_count > 0 && (
                      <span className="text-xs text-white/30">{ev.chunk_count} chunks</span>
                    )}
                    <span className={cn("text-xs px-2 py-0.5 rounded-full", STATUS_STYLES[ev.status])}>
                      {ev.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
