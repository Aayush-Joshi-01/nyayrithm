"use client";

import Link from "next/link";
import { useQuery, useQueries } from "@tanstack/react-query";
import { FileText, ArrowRight } from "lucide-react";
import { casesApi, evidenceApi } from "@/lib/api";
import { cn, formatBytes } from "@/lib/utils";
import type { Evidence } from "@/types/api";
import { PageScroll } from "@/components/layout/PageScroll";

const STATUS_STYLES: Record<string, string> = {
  pending: "text-foreground/40 bg-bone/[0.05]",
  processing: "text-brass-text bg-brass/12",
  indexed: "text-role-witness bg-role-witness/12",
  error: "text-oxblood-bright bg-oxblood-bright/12",
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
    <PageScroll>
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <h1 className="font-serif text-2xl font-medium tracking-tight text-bone">Evidence</h1>
        <p className="mt-1 text-[0.88rem] text-foreground/45">Exhibits across every case.</p>
      </div>

      {casesLoading && (
        <div className="space-y-2">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="h-24 animate-pulse rounded-lg border border-hairline bg-bone/[0.04]" />
          ))}
        </div>
      )}

      {!casesLoading && cases.length === 0 && (
        <div className="rounded-lg border border-border bg-ink-raised/60 px-8 py-14 text-center">
          <p className="text-[0.88rem] text-foreground/35">No cases yet. Open a case to attach evidence.</p>
        </div>
      )}

      {cases.map((c, i) => {
        const items = evidenceQueries[i]?.data?.items ?? [];
        return (
          <div key={c.id} className="overflow-hidden rounded-lg border border-border bg-ink-raised/50">
            <Link
              href={`/dashboard/${c.id}/evidence`}
              className="flex items-center justify-between border-b border-hairline px-4 py-3 transition-colors hover:bg-accent/40"
            >
              <span className="font-serif text-[0.95rem] font-medium text-foreground/90">{c.title}</span>
              <span className="flex items-center gap-1 font-mono text-[0.7rem] text-foreground/40">
                {items.length} exhibit{items.length === 1 ? "" : "s"}
                <ArrowRight className="h-3.5 w-3.5" strokeWidth={1.75} />
              </span>
            </Link>

            {items.length === 0 ? (
              <p className="px-4 py-3 font-mono text-[0.7rem] text-foreground/45">Nothing entered for this case.</p>
            ) : (
              <div className="divide-y divide-hairline">
                {items.map((ev: Evidence) => (
                  <div key={ev.id} className="flex items-center gap-3 px-4 py-2.5">
                    <FileText className="h-4 w-4 flex-shrink-0 text-foreground/30" strokeWidth={1.5} />
                    <span className="flex-1 truncate text-[0.86rem] text-foreground/80">{ev.title}</span>
                    <span className="font-mono text-[0.68rem] text-foreground/30 tabular">{formatBytes(ev.file_size)}</span>
                    {ev.chunk_count > 0 && (
                      <span className="hidden font-mono text-[0.68rem] text-foreground/30 tabular sm:inline">{ev.chunk_count} chunks</span>
                    )}
                    <span className={cn("rounded-sm px-1.5 py-0.5 font-mono text-[0.62rem] uppercase tracking-wide", STATUS_STYLES[ev.status])}>
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
    </PageScroll>
  );
}
