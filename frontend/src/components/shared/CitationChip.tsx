"use client";

import { useState } from "react";
import { FileText, Mic, Film, Image } from "lucide-react";
import type { Citation } from "@/types/api";
import { cn } from "@/lib/utils";

const MODALITY_ICONS: Record<string, React.ElementType> = {
  text: FileText,
  audio: Mic,
  video: Film,
  image: Image,
};

export function CitationChip({ citation }: { citation: Citation }) {
  const [open, setOpen] = useState(false);
  const Icon = MODALITY_ICONS[citation.modality] ?? FileText;

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setOpen(!open)}
        className={cn(
          "flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border transition-colors",
          "text-amber-400 bg-amber-400/10 border-amber-400/30 hover:bg-amber-400/20"
        )}
      >
        <Icon className="w-3 h-3" />
        <span className="font-mono">{citation.evidence_title ?? citation.evidence_id.slice(0, 8)}</span>
        <span className="text-amber-400/60">#{citation.chunk_index}</span>
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-30" onClick={() => setOpen(false)} />
          <div className="absolute bottom-full mb-2 left-0 z-40 w-72 p-3 bg-card border border-border rounded-lg shadow-xl text-xs space-y-1.5">
            <div className="flex items-center gap-1.5 font-semibold text-foreground">
              <Icon className="w-3.5 h-3.5 text-amber-400" />
              {citation.evidence_title ?? "Evidence"}
              <span className="ml-auto text-muted-foreground">score: {citation.score.toFixed(2)}</span>
            </div>
            <p className="text-muted-foreground leading-relaxed line-clamp-6">
              {citation.chunk_text}
            </p>
          </div>
        </>
      )}
    </div>
  );
}
