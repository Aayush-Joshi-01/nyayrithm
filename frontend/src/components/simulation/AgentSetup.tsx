"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Play, Trash2, Plus, Loader2 } from "lucide-react"
import { simulationsApi } from "@/lib/api"
import { formatRole, roleStyle, ROLE_SIGIL } from "@/lib/utils"
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
    <div className="mx-auto w-full max-w-2xl space-y-7 p-8">
      <div>
        <h3 className="font-serif text-lg font-medium text-bone">Seat the bench</h3>
        <p className="mt-1 text-[0.85rem] leading-relaxed text-foreground/45">
          A default roster was seeded for this scenario. Add or strike roles, then call the
          proceeding to order. Two agents is the minimum.
        </p>
      </div>

      <div className="divide-y divide-hairline border-y border-hairline">
        {isLoading && <p className="py-3 font-mono text-[0.72rem] text-foreground/40">Loading the roster</p>}
        {agents.map((a) => {
          return (
            <div key={a.id} className="flex items-center gap-3 py-2.5">
              <span
                className="grid h-5 w-5 flex-shrink-0 place-items-center rounded-sm border font-mono text-[0.6rem] font-semibold"
                style={roleStyle(a.role as AgentRole)}
              >
                {ROLE_SIGIL[a.role as AgentRole]}
              </span>
              <span className="flex-1 truncate font-serif text-[0.9rem] font-medium text-foreground/85">{a.name}</span>
              <span className="font-mono text-[0.68rem] uppercase tracking-wide text-foreground/40">{formatRole(a.role)}</span>
              <span className="hidden font-mono text-[0.64rem] text-foreground/45 sm:inline">{a.llm_model}</span>
              <button
                onClick={() => removeMutation.mutate(a.id)}
                disabled={removeMutation.isPending}
                className="text-foreground/25 transition-colors hover:text-oxblood-bright"
                title="Strike from the roster"
              >
                <Trash2 className="h-3.5 w-3.5" strokeWidth={1.75} />
              </button>
            </div>
          )
        })}
        {!isLoading && agents.length === 0 && (
          <p className="py-3 text-[0.82rem] text-brass-text">No agents yet. Add at least two to run a proceeding.</p>
        )}
      </div>

      <div className="flex items-end gap-2">
        <Input
          placeholder="Agent name (optional)"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="h-9 flex-1"
        />
        <Select value={role} onValueChange={(v) => setRole(v as AgentRole)}>
          <SelectTrigger className="h-9 w-44"><SelectValue /></SelectTrigger>
          <SelectContent>
            {ROLES.map((r) => (
              <SelectItem key={r} value={r}>{formatRole(r)}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button size="sm" variant="outline" onClick={() => addMutation.mutate()} disabled={addMutation.isPending} className="h-9">
          <Plus className="mr-1 h-3.5 w-3.5" strokeWidth={2} /> Add
        </Button>
      </div>

      {(addMutation.isError || removeMutation.isError) && (
        <p className="text-[0.78rem] text-oxblood-bright">Could not update the roster. Is the backend running?</p>
      )}

      <div className="border-t border-hairline pt-4">
        <Button
          onClick={() => startMutation.mutate()}
          disabled={startMutation.isPending || agents.length < 2}
          className="w-full"
        >
          {startMutation.isPending
            ? <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            : <Play className="mr-2 h-4 w-4" strokeWidth={2} />}
          Call to order
        </Button>
        {startMutation.isError && (
          <p className="mt-2 text-center text-[0.78rem] text-oxblood-bright">
            Could not start. Check the backend and try again.
          </p>
        )}
      </div>
    </div>
  )
}
