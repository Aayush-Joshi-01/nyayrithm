"use client";

import Link from "next/link";
import { Globe, Scale, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Case } from "@/types/api";

const STATUS_STYLES: Record<string, string> = {
  open: "text-emerald-400 bg-emerald-400/10",
  in_simulation: "text-amber-400 bg-amber-400/10 animate-pulse-slow",
  closed: "text-slate-400 bg-slate-400/10",
  archived: "text-slate-600 bg-slate-600/10",
};

export function CaseCard({ case_ }: { case_: Case }) {
  return (
    <Link href={`/dashboard/${case_.id}/evidence`}>
      <div className="group relative p-5 rounded-xl border border-border bg-card hover:border-amber-500/30 hover:bg-card/80 transition-all cursor-pointer">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
              <Scale className="w-4 h-4 text-amber-400" />
            </div>
            <span
              className={cn(
                "text-xs font-medium px-2 py-0.5 rounded-full",
                STATUS_STYLES[case_.status] ?? "text-slate-400 bg-slate-400/10"
              )}
            >
              {case_.status.replace("_", " ")}
            </span>
          </div>
          <ArrowRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>

        <h3 className="font-semibold text-foreground line-clamp-2 mb-1">{case_.title}</h3>
        <p className="text-sm text-muted-foreground line-clamp-2 mb-4">{case_.description}</p>

        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Globe className="w-3 h-3" />
            {case_.country}
          </span>
          <span className="px-2 py-0.5 rounded bg-muted">
            {case_.legal_system.replace("_", " ")}
          </span>
        </div>
      </div>
    </Link>
  );
}
