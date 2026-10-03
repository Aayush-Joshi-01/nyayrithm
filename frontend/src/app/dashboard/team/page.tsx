"use client"

import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Copy, Mail, RefreshCw, Trash2, UserMinus } from "lucide-react"
import { apiError, firmApi } from "@/lib/api"
import { useFirm } from "@/components/firm/FirmProvider"
import { PageScroll } from "@/components/layout/PageScroll"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type { FirmRole, Invite } from "@/types/api"

const ROLE_HELP: Record<FirmRole, string> = {
  owner: "Everything, including billing and other owners.",
  admin: "Manages the team and sees every case in the firm.",
  attorney: "Works on their own cases and any shared with them.",
}

export default function TeamPage() {
  const { firm, role, isManager, subscription } = useFirm()
  const qc = useQueryClient()
  const orgId = firm.org_id

  const members = useQuery({ queryKey: ["members", orgId], queryFn: () => firmApi.members(orgId) })
  const invites = useQuery({ queryKey: ["invites", orgId], queryFn: () => firmApi.invites(orgId), enabled: isManager })
  const [notice, setNotice] = useState<{ tone: "ok" | "bad"; text: string } | null>(null)
  const [fresh, setFresh] = useState<Invite | null>(null)

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["members", orgId] })
    qc.invalidateQueries({ queryKey: ["invites", orgId] })
    qc.invalidateQueries({ queryKey: ["subscription", orgId] })
  }
  const fail = async (e: unknown) => setNotice({ tone: "bad", text: (await apiError(e)).message })

  const changeRole = useMutation({
    mutationFn: (v: { userId: string; role: FirmRole }) => firmApi.changeRole(orgId, v.userId, v.role),
    onSuccess: () => { setNotice({ tone: "ok", text: "Role updated." }); refresh() },
    onError: fail,
  })
  const remove = useMutation({
    mutationFn: (userId: string) => firmApi.removeMember(orgId, userId),
    onSuccess: () => { setNotice({ tone: "ok", text: "Removed from the firm. Their cases stay with the firm." }); refresh() },
    onError: fail,
  })
  const resend = useMutation({
    mutationFn: (id: string) => firmApi.resendInvite(orgId, id),
    onSuccess: (inv) => { setFresh(inv); setNotice({ tone: "ok", text: `A new invitation was sent to ${inv.email}.` }); refresh() },
    onError: fail,
  })
  const revoke = useMutation({
    mutationFn: (id: string) => firmApi.revokeInvite(orgId, id),
    onSuccess: refresh,
    onError: fail,
  })

  const seats = subscription?.seats
  const roleOptions: FirmRole[] = role === "owner" ? ["owner", "admin", "attorney"] : ["admin", "attorney"]

  return (
    <PageScroll>
      <div className="mx-auto w-full max-w-4xl px-6 py-8">
        <header className="mb-7">
          <h1 className="font-serif text-[1.6rem] font-medium tracking-tight text-bone">Team</h1>
          <p className="mt-1 text-[0.88rem] text-foreground/50">
            People in {firm.name}.
            {seats && <> {seats.used} of {seats.limit} seats used{seats.pending > 0 && `, ${seats.pending} reserved by invitations`}.</>}
          </p>
        </header>

        {notice && (
          <p role={notice.tone === "bad" ? "alert" : "status"}
            className={`mb-5 rounded-md border px-3 py-2 text-[0.82rem] ${notice.tone === "bad" ? "border-oxblood-bright/30 bg-oxblood-bright/10 text-oxblood-bright" : "border-role-witness/30 bg-role-witness/10 text-role-witness"}`}>
            {notice.text}
          </p>
        )}

        <section aria-labelledby="members-h" className="mb-10">
          <h2 id="members-h" className="mb-3 font-serif text-[1.05rem] text-bone">Members</h2>
          <div className="overflow-x-auto rounded-md border border-border">
            <table className="w-full min-w-[560px] text-[0.85rem]">
              <thead>
                <tr className="border-b border-hairline text-left font-mono text-[0.62rem] uppercase tracking-widest text-foreground/40">
                  <th className="px-3 py-2.5 font-medium">Person</th><th className="px-3 py-2.5 font-medium">Role</th><th className="px-3 py-2.5" />
                </tr>
              </thead>
              <tbody>
                {(members.data ?? []).map((m) => {
                  const canEdit = isManager && (role === "owner" || m.role !== "owner")
                  return (
                    <tr key={m.user_id} className="border-b border-hairline last:border-0">
                      <td className="px-3 py-2.5">
                        <span className="font-medium text-bone">{m.display_name || m.email}</span>
                        <span className="block font-mono text-[0.72rem] text-foreground/40">{m.email}</span>
                      </td>
                      <td className="px-3 py-2.5">
                        {canEdit ? (
                          <Select value={m.role} onValueChange={(v) => changeRole.mutate({ userId: m.user_id, role: v as FirmRole })}>
                            <SelectTrigger className="h-8 w-32" aria-label={`Role for ${m.email}`}><SelectValue /></SelectTrigger>
                            <SelectContent>
                              {(m.role === "owner" && role !== "owner" ? [m.role] : roleOptions).map((r) => (
                                <SelectItem key={r} value={r}>{r}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        ) : (
                          <Badge variant={m.role === "owner" ? "warning" : "muted"}>{m.role}</Badge>
                        )}
                      </td>
                      <td className="px-3 py-2.5 text-right">
                        {canEdit && (
                          <Button size="sm" variant="ghost" aria-label={`Remove ${m.email}`} disabled={remove.isPending}
                            onClick={() => { if (window.confirm(`Remove ${m.email} from ${firm.name}? Their cases stay with the firm.`)) remove.mutate(m.user_id) }}>
                            <UserMinus className="h-3.5 w-3.5" />
                          </Button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {members.isLoading && <p className="px-3 py-6 text-center text-foreground/40">Loading…</p>}
          </div>
        </section>

        {isManager ? (
          <>
            <InviteForm orgId={orgId} role={role} onInvited={(inv) => { setFresh(inv); setNotice({ tone: "ok", text: `Invitation sent to ${inv.email}.` }); refresh() }} onError={fail} roleOptions={roleOptions} />

            {fresh?.invite_url && (
              <div className="mb-8 rounded-md border border-brass/30 bg-brass/5 p-4">
                <p className="text-[0.82rem] text-foreground/70">
                  Email can be slow. Send {fresh.email} this one-time link yourself if you like. It only works for that address and expires in 7 days.
                </p>
                <div className="mt-2 flex gap-2">
                  <Input readOnly aria-label="Invitation link" value={fresh.invite_url} onFocus={(e) => e.currentTarget.select()} className="font-mono text-[0.74rem]" />
                  <Button size="sm" variant="outline" onClick={() => navigator.clipboard?.writeText(fresh.invite_url!)}><Copy className="mr-1.5 h-3.5 w-3.5" />Copy</Button>
                </div>
              </div>
            )}

            <section aria-labelledby="invites-h">
              <h2 id="invites-h" className="mb-3 font-serif text-[1.05rem] text-bone">Pending invitations</h2>
              {(invites.data?.length ?? 0) === 0 ? (
                <p className="rounded-md border border-border px-4 py-6 text-center text-[0.84rem] text-foreground/40">No invitations waiting.</p>
              ) : (
                <ul className="divide-y divide-hairline rounded-md border border-border">
                  {invites.data!.map((i) => (
                    <li key={i.id} className="flex flex-wrap items-center gap-3 px-4 py-3">
                      <Mail className="h-4 w-4 text-foreground/35" aria-hidden />
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-mono text-[0.82rem] text-bone">{i.email}</p>
                        <p className="text-[0.74rem] text-foreground/40">{i.role} · expires {new Date(i.expires_at).toLocaleDateString("en-GB", { day: "2-digit", month: "short" })}</p>
                      </div>
                      <Button size="sm" variant="outline" disabled={resend.isPending} onClick={() => resend.mutate(i.id)}><RefreshCw className="mr-1.5 h-3.5 w-3.5" />Resend</Button>
                      <Button size="sm" variant="ghost" aria-label={`Withdraw invitation to ${i.email}`} onClick={() => revoke.mutate(i.id)}><Trash2 className="h-3.5 w-3.5" /></Button>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        ) : (
          <p className="rounded-md border border-border px-4 py-4 text-[0.84rem] text-foreground/50">Only owners and admins can invite people or change roles.</p>
        )}
      </div>
    </PageScroll>
  )
}

function InviteForm({ orgId, role, roleOptions, onInvited, onError }: {
  orgId: string; role: FirmRole; roleOptions: FirmRole[]
  onInvited: (i: Invite) => void; onError: (e: unknown) => void
}) {
  const [email, setEmail] = useState("")
  const [inviteRole, setInviteRole] = useState<FirmRole>("attorney")
  const send = useMutation({
    mutationFn: () => firmApi.invite(orgId, email.trim(), inviteRole),
    onSuccess: (inv) => { setEmail(""); onInvited(inv) },
    onError,
  })
  return (
    <section aria-labelledby="invite-h" className="mb-8">
      <h2 id="invite-h" className="mb-3 font-serif text-[1.05rem] text-bone">Invite an attorney</h2>
      <form onSubmit={(e) => { e.preventDefault(); send.mutate() }} className="flex flex-wrap items-end gap-3 rounded-md border border-border p-4">
        <label className="min-w-[240px] flex-1 space-y-1.5">
          <span className="text-[0.78rem] font-medium text-foreground/60">Email address</span>
          <Input type="email" required placeholder="name@yourfirm.com" value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="w-40 space-y-1.5">
          <span className="text-[0.78rem] font-medium text-foreground/60">Role</span>
          <Select value={inviteRole} onValueChange={(v) => setInviteRole(v as FirmRole)}>
            <SelectTrigger aria-label="Role"><SelectValue /></SelectTrigger>
            <SelectContent>{roleOptions.map((r) => <SelectItem key={r} value={r}>{r}</SelectItem>)}</SelectContent>
          </Select>
        </label>
        <Button type="submit" disabled={!email.includes("@") || send.isPending}>Send invitation</Button>
        <p className="basis-full text-[0.74rem] text-foreground/40">{ROLE_HELP[inviteRole]} {role !== "owner" && "Only owners can invite owners."}</p>
      </form>
    </section>
  )
}
