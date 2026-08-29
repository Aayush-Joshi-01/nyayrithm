"use client";

import { useState } from "react";
import { FileText, Mic, Film, Image as ImageIcon } from "lucide-react";
import type { Citation } from "@/types/api";

const MODALITY_ICONS: Record<string, React.ElementType> = {
  text: FileText,
  audio: Mic,
  video: Film,
  image: ImageIcon,
};

/* A citation is stitched to its exact source, not floated as a chip. The seam
   underline carries the connective thread; opening it shows the passage.
   (raise: challenger-evidence-quilt) */
export function CitationChip({ citation }: { citation: Citation }) {
  const [open, setOpen] = useState(false);
  const Icon = MODALITY_ICONS[citation.modality] ?? FileText;
  const label = citation.evidence_title ?? (citation.evidence_id ?? "evidence").slice(0, 8);

  return (
    <span className="relative inline-block">
      <button
        onClick={() => setOpen((v) => !v)}
        className="seam inline-flex items-center gap-1 font-mono text-[0.72rem] text-brass-text/85 hover:text-brass-text"
      >
        <Icon className="h-3 w-3" strokeWidth={1.75} />
        {label}
        <span className="text-brass-text/50">p.{citation.chunk_index ?? 0}</span>
      </button>

      {open && (
        <>
          <span className="fixed inset-0 z-30 block" onClick={() => setOpen(false)} />
          <span className="absolute bottom-full left-0 z-40 mb-2 block w-72 origin-bottom-left rounded-sm border border-border bg-popover p-3 shadow-chamber animate-in fade-in-0 zoom-in-95 slide-in-from-bottom-1 duration-150 ease-[cubic-bezier(0.16,1,0.3,1)]">
            <span className="mb-1.5 flex items-center gap-1.5 font-serif text-[0.82rem] font-medium text-foreground">
              <Icon className="h-3.5 w-3.5 text-brass-text" strokeWidth={1.75} />
              {citation.evidence_title ?? "Evidence"}
              <span className="ml-auto font-mono text-[0.62rem] text-foreground/40 tabular">
                match {(citation.score ?? 0).toFixed(2)}
              </span>
            </span>
            <span className="block max-h-32 overflow-hidden text-[0.78rem] leading-relaxed text-foreground/60">
              {citation.chunk_text}
            </span>
          </span>
        </>
      )}
    </span>
  );
}
