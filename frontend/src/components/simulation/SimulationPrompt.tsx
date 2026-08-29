"use client"

import { useState, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import { useMutation } from "@tanstack/react-query"
import { ArrowUp } from "lucide-react"
import { simulationsApi } from "@/lib/api"
import { cn } from "@/lib/utils"
import { Textarea } from "@/components/ui/textarea"

const MODES = [
  { id: "courtroom" as const, label: "Courtroom" },
  { id: "deposition" as const, label: "Deposition" },
  { id: "strategy" as const, label: "Strategy session" },
]

const SCENARIOS = [
  { label: "Full criminal trial", mode: "courtroom" as const, prompt: "A full criminal trial: judge, prosecutor, defense counsel, and the witnesses each side calls." },
  { label: "Civil deposition", mode: "deposition" as const, prompt: "A civil deposition. Plaintiff and defense counsel question the deponent under oath." },
  { label: "Defense strategy", mode: "strategy" as const, prompt: "A closed strategy session. Defense counsel works through the theory of the case and its weak points." },
  { label: "Cross-examination", mode: "courtroom" as const, prompt: "The prosecution's cross-examination of the two key defense witnesses." },
]

export function SimulationPrompt({ caseId }: { caseId: string }) {
  const [message, setMessage] = useState("")
  const [mode, setMode] = useState<"courtroom" | "deposition" | "strategy">("courtroom")
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const router = useRouter()

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = "auto"
    el.style.height = `${Math.min(el.scrollHeight, 180)}px`
  }, [])

  const createMutation = useMutation({
    mutationFn: (scenario: string) =>
      simulationsApi.create(caseId, {
        title: scenario ? scenario.slice(0, 80) : `${MODES.find((m) => m.id === mode)?.label} proceeding`,
        mode,
        max_turns: 50,
        config: { scenario, mode },
      }),
    onSuccess: (sim) => router.push(`/dashboard/${caseId}/simulation/${sim.id}`),
  })

  return (
    <div className="mx-auto w-full max-w-2xl">
      <div className="overflow-hidden rounded-md border border-border bg-ink focus-within:border-brass/40">
        <Textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => { setMessage(e.target.value); adjustHeight() }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) createMutation.mutate(message.trim())
          }}
          placeholder="Describe the scenario to argue, or pick one below."
          rows={2}
          className="min-h-[56px] resize-none border-0 bg-transparent px-4 py-3.5 text-sm leading-relaxed focus-visible:bg-transparent"
          style={{ overflow: "hidden" }}
        />
        <div className="flex items-center justify-between border-t border-hairline px-3 py-2">
          <div className="flex items-center gap-1">
            {MODES.map((m) => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                className={cn(
                  "rounded-sm px-2 py-1 text-[0.72rem] transition-colors",
                  mode === m.id
                    ? "bg-ink-higher text-foreground shadow-[inset_0_-2px_0_0_#C88A4A]"
                    : "text-foreground/35 hover:text-foreground/60"
                )}
              >
                {m.label}
              </button>
            ))}
          </div>
          <button
            onClick={() => createMutation.mutate(message.trim())}
            disabled={createMutation.isPending}
            className="grid h-7 w-7 place-items-center rounded-sm bg-brass text-[#12100A] transition-colors hover:bg-brass-lit disabled:opacity-40"
            aria-label="Convene"
          >
            <ArrowUp className="h-4 w-4" strokeWidth={2.5} />
          </button>
        </div>
      </div>

      {createMutation.isError && (
        <p className="mt-3 text-center text-[0.78rem] text-oxblood-bright">
          Could not open the proceeding. Check that the backend is running, then try again.
        </p>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {SCENARIOS.map((s) => (
          <button
            key={s.label}
            onClick={() => { setMessage(s.prompt); setMode(s.mode); setTimeout(adjustHeight, 10) }}
            className="rounded-sm border border-hairline px-2.5 py-1.5 font-mono text-[0.7rem] text-foreground/40 transition-colors hover:border-brass/30 hover:text-foreground/70"
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  )
}
