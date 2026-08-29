"use client"

import { useState, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import { useMutation } from "@tanstack/react-query"
import {
  Gavel, FileText, Users, MessageSquare, ArrowUp, Paperclip,
} from "lucide-react"
import { simulationsApi } from "@/lib/api"
import { cn } from "@/lib/utils"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"

const QUICK_ACTIONS = [
  { icon: Gavel, label: "Criminal Trial", mode: "courtroom" as const, prompt: "Full criminal trial with judge, prosecutor, defense, and witnesses" },
  { icon: FileText, label: "Civil Deposition", mode: "deposition" as const, prompt: "Civil deposition with plaintiff and defense attorneys" },
  { icon: Users, label: "Strategy Session", mode: "strategy" as const, prompt: "Legal strategy session with defense counsel analyzing the case" },
  { icon: MessageSquare, label: "Cross-Examination", mode: "courtroom" as const, prompt: "Intensive cross-examination of key witnesses by prosecution" },
]

interface Props {
  caseId: string
}

export function SimulationPrompt({ caseId }: Props) {
  const [message, setMessage] = useState("")
  const [mode, setMode] = useState<"courtroom" | "deposition" | "strategy">("courtroom")
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const router = useRouter()

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = "48px"
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [])

  const createMutation = useMutation({
    mutationFn: (scenario: string) =>
      simulationsApi.create(caseId, {
        title: scenario || `${mode.charAt(0).toUpperCase() + mode.slice(1)} Simulation`,
        mode,
        max_turns: 50,
        config: { scenario, mode },
      }),
    onSuccess: (sim) => {
      router.push(`/dashboard/${caseId}/simulation/${sim.id}`)
    },
  })

  const handleSubmit = () => {
    createMutation.mutate(message.trim())
  }

  const handleQuickAction = (action: typeof QUICK_ACTIONS[0]) => {
    setMessage(action.prompt)
    setMode(action.mode)
    setTimeout(adjustHeight, 10)
  }

  const canSubmit = !createMutation.isPending

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="relative bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 overflow-hidden shadow-2xl shadow-black/40">
        <Textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => { setMessage(e.target.value); adjustHeight() }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit()
          }}
          placeholder="Describe your courtroom scenario, or pick one below…"
          className={cn(
            "w-full px-4 py-4 resize-none border-none bg-transparent text-white text-sm",
            "focus-visible:ring-0 focus-visible:ring-offset-0 placeholder:text-white/25 min-h-[52px]"
          )}
          style={{ overflow: "hidden" }}
        />

        <div className="flex items-center justify-between px-3 py-2.5 border-t border-white/8">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" className="w-8 h-8 text-white/30 hover:text-white/60">
              <Paperclip className="w-4 h-4" />
            </Button>
            <div className="flex items-center gap-1">
              {(["courtroom", "deposition", "strategy"] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={cn(
                    "px-2.5 py-1 rounded-full text-xs font-medium transition-all",
                    mode === m
                      ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                      : "text-white/30 hover:text-white/50 hover:bg-white/5"
                  )}
                >
                  {m.charAt(0).toUpperCase() + m.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <Button
            onClick={handleSubmit}
            disabled={!canSubmit}
            size="icon"
            className="w-8 h-8 rounded-full bg-amber-500 hover:bg-amber-400 text-black disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ArrowUp className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {createMutation.isError && (
        <p className="text-center text-xs text-red-400 mt-3">
          Could not create the simulation. Check that the backend is running and try again.
        </p>
      )}

      {/* Quick actions */}
      <div className="flex items-center justify-center flex-wrap gap-2 mt-4">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action.label}
            onClick={() => handleQuickAction(action)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-white/10 bg-white/5 text-white/40 hover:text-white/70 hover:border-white/20 hover:bg-white/8 transition-all text-xs"
          >
            <action.icon className="w-3.5 h-3.5" />
            {action.label}
          </button>
        ))}
      </div>
    </div>
  )
}
