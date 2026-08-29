"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Play, Trash2, Plus, Loader2 } from "lucide-react"
import { simulationsApi } from "@/lib/api"
import { formatRole } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import type { AgentRole } from "@/types/api"

const ROLES: AgentRole[] = [
  "judge", "prosecutor", "defense", "plaintiff", "accused",
  "witness", "investigator", "expert_witness", "custom",
]

export function AgentSetup({ simId, onStarted }: { simId: string; onStarted: () => void }) {
  const qc = useQueryClient()
  const [name, setName] = useState("")
  const [role, setRole] = useState<AgentRole>("witness")

  const { data: agents = [], isLoading } = useQuery({
    queryKey: ["agents", simId],
    queryFn: () => simulationsApi.listAgents(simId),
  })

  const invalidate = () => qc.invalidateQueries({ queryKey: ["agents", simId] })

  const addMutation = useMutation({
    mutationFn: () => simulationsApi.addAgent(simId, { role, name: name.trim() || formatRole(role) }),
    onSuccess: () => { setName(""); invalidate() },
  })

  const removeMutation = useMutation({
    mutationFn: (agentId: string) => simulationsApi.deleteAgent(simId, agentId),
    onSuccess: invalidate,
  })

  const startMutation = useMutation({
    mutationFn: () => simulationsApi.start(simId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["simulation", simId] })
      onStarted()
    },
  })

  return (
    <div className="max-w-2xl mx-auto w-full p-6 space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-foreground">Agent roster</h3>
        <p className="text-xs text-muted-foreground mt-1">
          A default roster was seeded for this scenario. Add or remove roles, then start the proceedings.
        </p>
      </div>

      <div className="space-y-2">
        {isLoading && <p className="text-xs text-muted-foreground">Loading agents…</p>}
        {agents.map((a) => (
          <div key={a.id} className="flex items-center gap-3 rounded-lg border border-border bg-card/50 px-3 py-2">
            <span className="text-sm font-medium text-foreground flex-1 truncate">{a.name}</span>
            <span className="text-xs text-muted-foreground">{formatRole(a.role)}</span>
            <span className="text-[10px] font-mono text-muted-foreground/60">{a.llm_model}</span>
            <button
              onClick={() => removeMutation.mutate(a.id)}
              disabled={removeMutation.isPending}
              className="text-muted-foreground hover:text-red-400 transition-colors"
              title="Remove agent"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
        {!isLoading && agents.length === 0 && (
          <p className="text-xs text-amber-400">No agents yet — add at least two to run a simulation.</p>
        )}
      </div>

      <div className="flex items-end gap-2">
        <div className="flex-1">
          <Input
            placeholder="Agent name (optional)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="h-9 text-sm"
          />
        </div>
        <Select value={role} onValueChange={(v) => setRole(v as AgentRole)}>
          <SelectTrigger className="h-9 w-40 text-sm"><SelectValue /></SelectTrigger>
          <SelectContent>
            {ROLES.map((r) => (
              <SelectItem key={r} value={r} className="text-sm">{formatRole(r)}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => addMutation.mutate()}
          disabled={addMutation.isPending}
          className="h-9 border border-border"
        >
          <Plus className="w-3.5 h-3.5 mr-1" /> Add
        </Button>
      </div>

      {(addMutation.isError || removeMutation.isError) && (
        <p className="text-xs text-red-400">Could not update the roster. Is the backend running?</p>
      )}

      <div className="pt-2 border-t border-border">
        <Button
          onClick={() => startMutation.mutate()}
          disabled={startMutation.isPending || agents.length < 2}
          className="w-full bg-emerald-500 hover:bg-emerald-400 text-black"
        >
          {startMutation.isPending
            ? <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            : <Play className="w-4 h-4 mr-2" />}
          Start Proceedings
        </Button>
        {startMutation.isError && (
          <p className="text-xs text-red-400 mt-2 text-center">Failed to start. Check the backend and try again.</p>
        )}
      </div>
    </div>
  )
}
