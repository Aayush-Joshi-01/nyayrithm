"use client"

import Link from "next/link"
import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Plus, Search } from "lucide-react"
import { adminApi, errorMessage } from "@/lib/api"
import { Busy, ErrorNote, Field, Loading, PageHeader, StatusBadge, Table, Td } from "@/components/kit"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import { fmtCompact, fmtDate } from "@/lib/utils"

export default function FirmsPage() {
  const [q, setQ] = useState("")
  const [status, setStatus] = useState("all")
  const [page, setPage] = useState(1)
  const [creating, setCreating] = useState(false)

  const firms = useQuery({
    queryKey: ["firms", q, status, page],
    queryFn: () => adminApi.firms({ q, status: status === "all" ? undefined : status, page }),
  })
  const pages = firms.data ? Math.max(1, Math.ceil(firms.data.total / firms.data.size)) : 1

  return (
    <>
      <PageHeader
        title="Firms"
        intro="Each firm buys a subscription, then invites its own attorneys."
        actions={<Button size="sm" onClick={() => setCreating(true)}><Plus className="mr-1 h-3.5 w-3.5" /> New firm</Button>}
      />

      <div className="mb-4 flex flex-wrap gap-3">
        <div className="relative min-w-[220px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/35" />
          <Input
            aria-label="Search firms"
            placeholder="Search by name"
            className="pl-9"
            value={q}
            onChange={(e) => { setQ(e.target.value); setPage(1) }}
          />
        </div>
        <Select value={status} onValueChange={(v) => { setStatus(v); setPage(1) }}>
          <SelectTrigger className="w-40" aria-label="Filter by status"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="suspended">Suspended</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <ErrorNote error={firms.error} />
      {firms.isLoading ? (
        <Loading />
      ) : (
        <Table
          head={["Firm", "Status", "Plan", "Subscription", "Seats", "Tokens this month", "Renews"]}
          empty="No firms match."
          rowCount={firms.data?.items.length ?? 0}
        >
          {firms.data?.items.map((f) => (
            <tr key={f.id}>
              <Td>
                <Link href={`/firms/${f.id}`} className="font-medium text-bone hover:text-brass-text">{f.name}</Link>
                <span className="block font-mono text-[0.68rem] text-foreground/35">{f.slug}</span>
              </Td>
              <Td><StatusBadge value={f.status} /></Td>
              <Td>{f.plan ?? <span className="text-foreground/30">none</span>}</Td>
              <Td><StatusBadge value={f.subscription_status} /></Td>
              <Td mono>
                {f.seats.used}/{f.seats.limit}
                {f.seats.pending > 0 && <span className="text-foreground/40"> +{f.seats.pending}</span>}
              </Td>
              <Td mono>{fmtCompact(f.usage.tokens)}</Td>
              <Td>{fmtDate(f.period_end)}</Td>
            </tr>
          ))}
        </Table>
      )}

      {pages > 1 && (
        <div className="mt-4 flex items-center justify-end gap-3 text-[0.8rem] text-foreground/55">
          <Button size="sm" variant="outline" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</Button>
          <span className="tabular">Page {page} of {pages}</span>
          <Button size="sm" variant="outline" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</Button>
        </div>
      )}

      <CreateFirmDialog open={creating} onOpenChange={setCreating} />
    </>
  )
}

function CreateFirmDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const qc = useQueryClient()
  const plans = useQuery({ queryKey: ["plans"], queryFn: adminApi.plans, enabled: open })
  const [form, setForm] = useState({
    name: "", plan_code: "", seats: "5", owner_email: "", period_end: "", invoice_ref: "", status: "active",
  })
  const [created, setCreated] = useState<{ url: string; name: string } | null>(null)
  const [error, setError] = useState("")

  const make = useMutation({
    mutationFn: () =>
      adminApi.createFirm({
        name: form.name.trim(),
        plan_code: form.plan_code,
        seats: Number(form.seats),
        owner_email: form.owner_email.trim(),
        period_end: form.period_end ? new Date(form.period_end).toISOString() : null,
        invoice_ref: form.invoice_ref.trim(),
        status: form.status,
      }),
    onSuccess: (r) => {
      setCreated({ url: r.owner_invite_url, name: r.name })
      qc.invalidateQueries({ queryKey: ["firms"] })
      qc.invalidateQueries({ queryKey: ["overview"] })
    },
    onError: async (e) => setError(await errorMessage(e)),
  })

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [k]: e.target.value })
  const valid = form.name.trim().length >= 2 && form.plan_code && form.owner_email.includes("@") && Number(form.seats) >= 1

  function close(o: boolean) {
    if (!o) { setCreated(null); setError(""); setForm({ ...form, name: "", owner_email: "", invoice_ref: "" }) }
    onOpenChange(o)
  }

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent>
        {created ? (
          <>
            <DialogHeader>
              <DialogTitle>{created.name} is set up</DialogTitle>
              <DialogDescription>
                The owner has been emailed an invitation. If the email is slow, send them this one-time link yourself.
              </DialogDescription>
            </DialogHeader>
            <Input readOnly value={created.url} aria-label="Owner invitation link" onFocus={(e) => e.currentTarget.select()} className="font-mono text-[0.75rem]" />
            <DialogFooter><Button onClick={() => close(false)}>Done</Button></DialogFooter>
          </>
        ) : (
          <form onSubmit={(e) => { e.preventDefault(); setError(""); make.mutate() }} className="space-y-4">
            <DialogHeader>
              <DialogTitle>New firm</DialogTitle>
              <DialogDescription>Creates the firm and its subscription, and invites the first owner.</DialogDescription>
            </DialogHeader>
            <Field label="Firm name"><Input value={form.name} onChange={set("name")} required /></Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Plan">
                <Select value={form.plan_code} onValueChange={(v) => setForm({ ...form, plan_code: v })}>
                  <SelectTrigger aria-label="Plan"><SelectValue placeholder="Choose a plan" /></SelectTrigger>
                  <SelectContent>
                    {plans.data?.filter((p) => p.is_active).map((p) => (
                      <SelectItem key={p.code} value={p.code}>{p.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Seats"><Input type="number" min={1} value={form.seats} onChange={set("seats")} /></Field>
            </div>
            <Field label="Owner email" hint="They become the firm's owner when they accept."><Input type="email" value={form.owner_email} onChange={set("owner_email")} required /></Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Paid until"><Input type="date" value={form.period_end} onChange={set("period_end")} /></Field>
              <Field label="Invoice reference"><Input value={form.invoice_ref} onChange={set("invoice_ref")} /></Field>
            </div>
            <ErrorNote error={error ? new Error(error) : null} />
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => close(false)}>Cancel</Button>
              <Button type="submit" disabled={!valid || make.isPending}>{make.isPending && <Busy />} Create firm</Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}
