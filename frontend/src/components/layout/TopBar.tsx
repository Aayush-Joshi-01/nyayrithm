"use client";

import { Scale } from "lucide-react";

export function TopBar() {
  return (
    <header className="h-14 flex items-center px-6 border-b border-border bg-card/50 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <Scale className="w-5 h-5 text-amber-400" />
        <span className="font-semibold tracking-tight text-foreground">Nyayrithm</span>
        <span className="text-xs text-muted-foreground px-2 py-0.5 rounded bg-muted">
          Legal Reasoning Platform
        </span>
      </div>
    </header>
  );
}
