"use client"

import Link from "next/link"
import { use, useEffect, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ArrowLeft } from "lucide-react"
import { adminApi, errorMessage, type FirmDetail } from "@/lib/api"
import { Busy, ErrorNote, Field, Kpi, Loading, PageHeader, Section, StatusBadge, Table, Td } from "@/components/kit"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { fmtCompact, fmtDate, fmtDateTime, fmtInt, fmtUsd } from "@/lib/utils"

export default function FirmDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const qc = useQueryClient()
  const firm = useQuery({ queryKey: ["firm", id], queryFn: () => adminApi.firm(id) })
  const plans = useQuery({ queryKey: ["plans"], queryFn: adminApi.plans })
  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["firm", id] })
    qc.invalidateQueries({ queryKey: ["firms"] })
    qc.invalidateQueries({ queryKey: ["overview"] })
  }

  const setStatus = useMutation({
    mutationFn: (status: string) => adminApi.updateFirm(id, { status }),
    onSuccess: refresh,
  })

  const f = firm.data
  if (firm.isLoading) return <Loading />
  if (!f) return <ErrorNote error={firm.error ?? new Error("Firm not found")} />

  const suspended = f.status === "suspended"
  return (
    <>
      <Link href="/firms" className="mb-4 inline-flex items-center gap-1 text-[0.8rem] text-foreground/50 hover:text-foreground">
        <ArrowLeft className="h-3.5 w-3.5" /> All firms
      </Link>
      <PageHeader
        title={f.name}
        intro={`Created ${fmtDate(f.created_at)} · ${f.slug}`}
        actions={
          <>
            <StatusBadge value={f.status} />
            <Button
              size="sm"
              variant={suspended ? "default" : "destructive"}
              disabled={setStatus.isPending}
              onClick={() => {
                if (suspended || window.confirm(`Suspend ${f.name}? Everyone in the firm is locked out immediately.`)) {
                  setStatus.mutate(suspended ? "active" : "suspended")
                }
              }}
            >
              {setStatus.isPending && <Busy />} {suspended ? "Reactivate" : "Suspend"}
            </Button>
          </>
        }
      />
      <ErrorNote error={setStatus.error} />

      <p className="mb-6 rounded-md border border-hairline bg-ink-raised/40 px-4 py-2.5 text-[0.8rem] text-foreground/50">
        You see counts and usage only. A firm&apos;s cases, evidence and proceedings are never visible here.
      </p>

      <div className="mb-8 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Kpi label="Seats" value={`${f.seats.used}/${f.seats.limit}`} sub={f.seats.pending ? `${f.seats.pending} invited` : "none pending"} tone={f.seats.used > f.seats.limit ? "bad" : undefined} />
        <Kpi label="Cases" value={fmtInt(f.counts.cases)} sub={`${f.counts.simulations} simulations · ${f.counts.evidence} files`} />
        <Kpi label="Tokens this month" value={fmtCompact(f.usage.tokens)} sub={f.plan_detail ? `of ${fmtCompact(f.plan_detail.monthly_tokens)}` : undefined} />
        <Kpi label="Est. cost this month" value={fmtUsd(f.usage.cost_usd)} sub={`${f.usage.simulations} simulations started`} />
      </div>

      <Section title="Subscription" hint="billing is manual: record what the firm paid for">
        <SubscriptionForm key={`${f.subscription?.status}-${f.plan}-${f.seats.limit}`} firm={f} plans={plans.data ?? []} onSaved={refresh} />
      </Section>

      <Section title="Members" hint={`${f.members.filter((m) => m.status === "active").length} active`}>
        <Table head={["Name", "Email", "Role", "Status", "Last seen"]} empty="No members yet. Invite the owner below." rowCount={f.members.length}>
          {f.members.map((m) => (
            <tr key={m.user_id}>
              <Td>{m.display_name || "–"}</Td>
              <Td mono>{m.email}</Td>
              <Td><StatusBadge value={m.role} /></Td>
              <Td><StatusBadge value={m.status} /></Td>
              <Td>{fmtDateTime(m.last_seen_at)}</Td>
            </tr>
          ))}
        </Table>
        <OwnerInvite id={id} onDone={refresh} />
        {f.pending_invites.length > 0 && (
          <div className="mt-4">
            <p className="mb-2 text-[0.78rem] text-foreground/45">Pending invitations</p>
            <Table head={["Email", "Role", "Expires"]} rowCount={f.pending_invites.length}>
              {f.pending_invites.map((i) => (
                <tr key={i.id}><Td mono>{i.email}</Td><Td><StatusBadge value={i.role} /></Td><Td>{fmtDate(i.expires_at)}</Td></tr>
              ))}
            </Table>
          </div>
        )}
      </Section>

      <Section title="Usage history">
        <Table head={["Month", "Tokens", "Est. cost", "Simulations", "Turns"]} empty="No usage yet." rowCount={f.usage_history.length}>
          {f.usage_history.map((u) => (
            <tr key={u.period}>
              <Td mono>{u.period}</Td><Td mono>{fmtCompact(u.tokens)}</Td><Td mono>{fmtUsd(u.cost_usd)}</Td>
              <Td mono>{fmtInt(u.simulations)}</Td><Td mono>{fmtInt(u.turns)}</Td>
            </tr>
          ))}
        </Table>
      </Section>
    </>
  )
}

function SubscriptionForm({
  firm, plans, onSaved,
}: {
  firm: FirmDetail; plans: { code: string; name: string; is_active: boolean }[]; onSaved: () => void
}) {
  const sub = firm.subscription
  const [plan, setPlan] = useState(firm.plan ?? "")
  const [status, setStatus] = useState(sub?.status ?? "active")
  const [seats, setSeats] = useState(String(sub?.seats ?? 5))
  const [end, setEnd] = useState(sub?.current_period_end ? sub.current_period_end.slice(0, 10) : "")
  const [invoice, setInvoice] = useState(sub?.invoice_ref ?? "")
  const [error, setError] = useState("")
  const [saved, setSaved] = useState(false)

  useEffect(() => setSaved(false), [plan, status, seats, end, invoice])

  const save = useMutation({
    mutationFn: () =>
      adminApi.setSubscription(firm.id, {
        plan_code: plan, status, seats: Number(seats),
        period_end: end ? new Date(end).toISOString() : null, invoice_ref: invoice,
      }),
    onSuccess: () => { setSaved(true); onSaved() },
    onError: async (e) => setError(await errorMessage(e)),
  })

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); setError(""); save.mutate() }}
      className="grid gap-4 rounded-md border border-border p-4 sm:grid-cols-2 lg:grid-cols-5"
    >
      <Field label="Plan">
        <Select value={plan} onValueChange={setPlan}>
          <SelectTrigger aria-label="Plan"><SelectValue placeholder="Choose" /></SelectTrigger>
          <SelectContent>
            {plans.filter((p) => p.is_active || p.code === plan).map((p) => <SelectItem key={p.code} value={p.code}>{p.name}</SelectItem>)}
          </SelectContent>
        </Select>
      </Field>
      <Field label="Status">
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger aria-label="Status"><SelectValue /></SelectTrigger>
          <SelectContent>
            {["trialing", "active", "past_due", "cancelled"].map((s) => <SelectItem key={s} value={s}>{s.replace("_", " ")}</SelectItem>)}
          </SelectContent>
        </Select>
      </Field>
      <Field label="Seats"><Input type="number" min={1} value={seats} onChange={(e) => setSeats(e.target.value)} /></Field>
      <Field label="Paid until"><Input type="date" value={end} onChange={(e) => setEnd(e.target.value)} /></Field>
      <Field label="Invoice reference"><Input value={invoice} onChange={(e) => setInvoice(e.target.value)} /></Field>
      <div className="flex items-center gap-3 sm:col-span-2 lg:col-span-5">
        <Button type="submit" size="sm" disabled={!plan || save.isPending}>{save.isPending && <Busy />} Save subscription</Button>
        {saved && <span role="status" className="text-[0.8rem] text-role-witness">Saved. Takes effect immediately.</span>}
        {error && <span role="alert" className="text-[0.8rem] text-oxblood-bright">{error}</span>}
      </div>
    </form>
  )
}

function OwnerInvite({ id, onDone }: { id: string; onDone: () => void }) {
  const [email, setEmail] = useState("")
  const [link, setLink] = useState("")
  const [error, setError] = useState("")
  const invite = useMutation({
    mutationFn: () => adminApi.inviteOwner(id, email.trim()),
    onSuccess: (r) => { setLink(r.invite_url); setEmail(""); onDone() },
    onError: async (e) => setError(await errorMessage(e)),
  })
  return (
    <form onSubmit={(e) => { e.preventDefault(); setError(""); setLink(""); invite.mutate() }} className="mt-4 flex flex-wrap items-end gap-3">
      <div className="min-w-[240px] flex-1">
        <Field label="Invite an owner"><Input type="email" placeholder="owner@firm.com" value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
      </div>
      <Button type="submit" size="sm" variant="outline" disabled={!email.includes("@") || invite.isPending}>{invite.isPending && <Busy />} Send invitation</Button>
      {error && <span role="alert" className="basis-full text-[0.8rem] text-oxblood-bright">{error}</span>}
      {link && <Input readOnly aria-label="Invitation link" value={link} onFocus={(e) => e.currentTarget.select()} className="basis-full font-mono text-[0.72rem]" />}
    </form>
  )
}
