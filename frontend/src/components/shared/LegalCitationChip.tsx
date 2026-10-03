"use client";

import { useState } from "react";
import { Scale, ShieldAlert, ShieldCheck, ShieldQuestion } from "lucide-react";
import { cn } from "@/lib/utils";
import type { LegalCitation, LegalCitationStatus } from "@/types/api";

/* A legal authority an agent cited, with the registry's verdict beside it.
   "verified" is stitched in brass like an evidence citation; anything the
   registry could not stand behind is marked, never hidden. */
const STATUS: Record<
  LegalCitationStatus,
  { label: string; tone: string; Icon: React.ElementType }
> = {
  verified: { label: "In the index", tone: "text-brass-text/90", Icon: ShieldCheck },
  superseded: { label: "Repealed — see successor", tone: "text-foreground/60", Icon: Scale },
  unindexed: { label: "Not in the index", tone: "text-foreground/50", Icon: ShieldQuestion },
  unverified: { label: "Could not be verified", tone: "text-ember-text", Icon: ShieldQuestion },
  mismatch: { label: "Citation does not match", tone: "text-oxblood-bright", Icon: ShieldAlert },
  nonexistent: { label: "Does not exist", tone: "text-oxblood-bright", Icon: ShieldAlert },
};

export function LegalCitationChip({ citation }: { citation: LegalCitation }) {
  const [open, setOpen] = useState(false);
  const { label, tone, Icon } = STATUS[citation.status];
  const flagged = citation.severity === "error" || citation.severity === "warning";

  return (
    <span className="relative inline-block">
      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className={cn(
          "inline-flex items-center gap-1 rounded-sm border px-1.5 py-px font-mono text-[0.7rem] transition-colors hover:bg-accent/30",
          tone,
          flagged ? "border-current/40" : "border-hairline",
        )}
      >
        <Icon className="h-3 w-3" strokeWidth={1.75} />
        {citation.raw}
        {citation.successor && <span className="text-foreground/40">→ {citation.successor}</span>}
      </button>

      {open && (
        <>
          <span className="fixed inset-0 z-30 block" onClick={() => setOpen(false)} />
          <span
            role="dialog"
            className="absolute bottom-full left-0 z-40 mb-2 block w-80 origin-bottom-left rounded-sm border border-border bg-popover p-3 shadow-chamber animate-in fade-in-0 zoom-in-95 slide-in-from-bottom-1 duration-150"
          >
            <span className={cn("mb-1 flex items-center gap-1.5 font-serif text-[0.82rem] font-medium", tone)}>
              <Icon className="h-3.5 w-3.5" strokeWidth={1.75} />
              {label}
            </span>
            <span className="block text-[0.78rem] leading-relaxed text-foreground/70">
              {citation.message}
            </span>
            <span className="mt-2 block text-[0.68rem] leading-snug text-foreground/40">
              Checked against a starter reference index, not the full statute book. Confirm
              against the official text before relying on it.
            </span>
          </span>
        </>
      )}
    </span>
  );
}
