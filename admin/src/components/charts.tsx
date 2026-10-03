"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"

/** A dependency-free bar chart. Hover or focus a bar to read its exact value. */
export function BarChart({
  data, height = 140, format, ariaLabel, tone = "brass",
}: {
  data: { label: string; value: number; errors?: number }[]
  height?: number
  format: (n: number) => string
  ariaLabel: string
  tone?: "brass" | "witness"
}) {
  const [hover, setHover] = useState<number | null>(null)
  const max = Math.max(1, ...data.map((d) => d.value))
  if (data.length === 0) {
    return <p className="py-10 text-center text-[0.84rem] text-foreground/40">No data in this period.</p>
  }
  const active = hover != null ? data[hover] : null
  return (
    <figure className="m-0" aria-label={ariaLabel}>
      <div className="mb-2 h-5 font-mono text-[0.72rem] tabular text-foreground/55" aria-live="polite">
        {active ? (
          <>
            {active.label} · <span className="text-bone">{format(active.value)}</span>
            {active.errors ? <span className="ml-2 text-oxblood-bright">{active.errors} failed</span> : null}
          </>
        ) : (
          <span className="text-foreground/30">Hover a bar for the exact value</span>
        )}
      </div>
      <div className="flex items-end gap-[3px]" style={{ height }} role="list">
        {data.map((d, i) => (
          <button
            key={d.label}
            role="listitem"
            type="button"
            aria-label={`${d.label}: ${format(d.value)}`}
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(null)}
            onFocus={() => setHover(i)}
            onBlur={() => setHover(null)}
            className="group relative flex h-full flex-1 items-end focus-visible:outline-none"
          >
            <span
              className={cn(
                "block w-full min-h-[2px] rounded-t-[2px] transition-colors",
                tone === "brass" ? "bg-brass/60 group-hover:bg-brass group-focus-visible:bg-brass" : "bg-role-witness/60 group-hover:bg-role-witness",
                d.errors ? "ring-1 ring-inset ring-oxblood-bright/60" : "",
              )}
              style={{ height: `${(d.value / max) * 100}%` }}
            />
          </button>
        ))}
      </div>
      <div className="mt-1.5 flex justify-between font-mono text-[0.62rem] text-foreground/35">
        <span>{data[0].label}</span>
        <span>{data[data.length - 1].label}</span>
      </div>
    </figure>
  )
}
