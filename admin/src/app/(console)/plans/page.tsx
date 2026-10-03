"use client"

import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Pencil, Plus } from "lucide-react"
import { adminApi, errorMessage, type Plan } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Busy, ErrorNote, Field, Loading, PageHeader, Table, Td } from "@/components/kit"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { fmtCompact, fmtInt } from "@/lib/utils"

const BLANK: Plan = {
  code: "", name: "", seat_limit: 10, monthly_simulations: 100, monthly_tokens: 5_000_000,
  max_turns_per_sim: 100, storage_mb: 10_000, features: {}, is_active: true,
}

export default function PlansPage() {
  const qc = useQueryClient()
  const plans = useQuery({ queryKey: ["plans"], queryFn: adminApi.plans })
  const [editing, setEditing] = useState<{ plan: Plan; isNew: boolean } | null>(null)
  const [error, setError] = useState("")

  const retire = useMutation({
    mutationFn: (code: string) => adminApi.retirePlan(code),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plans"] }),
    onError: async (e) => setError(await errorMessage(e)),
  })

  return (
    <>
      <PageHeader
        title="Plans"
        intro="The limits a subscription grants. Changes apply to every firm on the plan straight away."
        actions={<Button size="sm" onClick={() => setEditing({ plan: BLANK, isNew: true })}><Plus className="mr-1 h-3.5 w-3.5" /> New plan</Button>}
      />
      <ErrorNote error={error ? new Error(error) : plans.error} />
      {plans.isLoading ? (
        <Loading />
      ) : (
        <Table
          head={["Plan", "Seats", "Simulations / mo", "Tokens / mo", "Max turns", "Storage", "Firms", ""]}
          rowCount={plans.data?.length ?? 0}
        >
          {plans.data?.map((p) => (
            <tr key={p.code} className={p.is_active ? "" : "opacity-50"}>
              <Td>
                <span className="font-medium text-bone">{p.name}</span>
                <span className="block font-mono text-[0.68rem] text-foreground/35">{p.code}</span>
              </Td>
              <Td mono>{fmtInt(p.seat_limit)}</Td>
              <Td mono>{fmtInt(p.monthly_simulations)}</Td>
              <Td mono>{fmtCompact(p.monthly_tokens)}</Td>
              <Td mono>{fmtInt(p.max_turns_per_sim)}</Td>
              <Td mono>{p.storage_mb >= 1000 ? `${(p.storage_mb / 1000).toFixed(1)} GB` : `${p.storage_mb} MB`}</Td>
              <Td mono>{p.firms ?? 0}</Td>
              <Td className="text-right">
                {!p.is_active && <Badge variant="muted" className="mr-2">retired</Badge>}
                <Button size="sm" variant="ghost" aria-label={`Edit ${p.name}`} onClick={() => setEditing({ plan: p, isNew: false })}><Pencil className="h-3.5 w-3.5" /></Button>
                {p.is_active && (
                  <Button
                    size="sm" variant="ghost"
                    onClick={() => { setError(""); if (window.confirm(`Retire the ${p.name} plan? It can no longer be assigned.`)) retire.mutate(p.code) }}
                  >
                    Retire
                  </Button>
                )}
              </Td>
            </tr>
          ))}
        </Table>
      )}
      {editing && <PlanDialog key={editing.plan.code || "new"} {...editing} onClose={() => setEditing(null)} />}
    </>
  )
}

function PlanDialog({ plan, isNew, onClose }: { plan: Plan; isNew: boolean; onClose: () => void }) {
  const qc = useQueryClient()
  const [f, setF] = useState({
    code: plan.code, name: plan.name, seat_limit: String(plan.seat_limit),
    monthly_simulations: String(plan.monthly_simulations), monthly_tokens: String(plan.monthly_tokens),
    max_turns_per_sim: String(plan.max_turns_per_sim), storage_mb: String(plan.storage_mb),
  })
  const [error, setError] = useState("")
  const save = useMutation({
    mutationFn: () =>
      adminApi.savePlan(f.code.trim().toLowerCase(), {
        name: f.name.trim(), seat_limit: Number(f.seat_limit),
        monthly_simulations: Number(f.monthly_simulations), monthly_tokens: Number(f.monthly_tokens),
        max_turns_per_sim: Number(f.max_turns_per_sim), storage_mb: Number(f.storage_mb),
        features: plan.features, is_active: true,
      }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["plans"] }); onClose() },
    onError: async (e) => setError(await errorMessage(e)),
  })
  const num = (k: keyof typeof f, label: string, hint?: string) => (
    <Field label={label} hint={hint}>
      <Input type="number" min={0} value={f[k]} onChange={(e) => setF({ ...f, [k]: e.target.value })} />
    </Field>
  )
  const valid = /^[a-z0-9-]{2,30}$/.test(f.code.trim().toLowerCase()) && f.name.trim().length > 0

  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent>
        <form onSubmit={(e) => { e.preventDefault(); setError(""); save.mutate() }} className="space-y-4">
          <DialogHeader>
            <DialogTitle>{isNew ? "New plan" : `Edit ${plan.name}`}</DialogTitle>
            <DialogDescription>Token and simulation allowances reset on the first of each month.</DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Code" hint="Lowercase, e.g. boutique">
              <Input value={f.code} disabled={!isNew} onChange={(e) => setF({ ...f, code: e.target.value })} />
            </Field>
            <Field label="Name"><Input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Field>
            {num("seat_limit", "Seat limit")}
            {num("monthly_simulations", "Simulations per month")}
            {num("monthly_tokens", "Tokens per month")}
            {num("max_turns_per_sim", "Max turns per simulation")}
            {num("storage_mb", "Evidence storage (MB)")}
          </div>
          <ErrorNote error={error ? new Error(error) : null} />
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={!valid || save.isPending}>{save.isPending && <Busy />} Save plan</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
