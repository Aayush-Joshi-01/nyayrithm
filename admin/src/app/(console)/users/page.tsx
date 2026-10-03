"use client"

import { useState } from "react"
import { useMutation, useQuery } from "@tanstack/react-query"
import { Search } from "lucide-react"
import { adminApi, errorMessage } from "@/lib/api"
import { ErrorNote, Loading, PageHeader, StatusBadge, Table, Td } from "@/components/kit"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { fmtDateTime } from "@/lib/utils"

export default function UsersPage() {
  const [q, setQ] = useState("")
  const [page, setPage] = useState(1)
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const users = useQuery({ queryKey: ["users", q, page], queryFn: () => adminApi.users({ q, page }) })
  const pages = users.data ? Math.max(1, Math.ceil(users.data.total / users.data.size)) : 1

  const toggle = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean; email: string }) => adminApi.setUserEnabled(id, enabled),
    onSuccess: (_r, v) => { setError(""); setNotice(`${v.email} ${v.enabled ? "enabled" : "disabled and signed out"}.`) },
    onError: async (e) => { setNotice(""); setError(await errorMessage(e)) },
  })

  return (
    <>
      <PageHeader
        title="Users"
        intro="Everyone who belongs to a firm. Disabling an account signs them out everywhere and blocks sign-in, in every firm."
      />
      <div className="relative mb-4 max-w-md">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/35" />
        <Input aria-label="Search users" placeholder="Search by name or email" className="pl-9" value={q}
          onChange={(e) => { setQ(e.target.value); setPage(1) }} />
      </div>
      <ErrorNote error={error ? new Error(error) : users.error} />
      {notice && <p role="status" className="mb-3 text-[0.82rem] text-role-witness">{notice}</p>}
      {users.isLoading ? (
        <Loading />
      ) : (
        <Table head={["Person", "Firms", "Last seen", ""]} empty="No users match." rowCount={users.data?.items.length ?? 0}>
          {users.data?.items.map((u) => (
            <tr key={u.user_id}>
              <Td>
                <span className="font-medium text-bone">{u.display_name || u.email}</span>
                <span className="block font-mono text-[0.72rem] text-foreground/40">{u.email}</span>
              </Td>
              <Td>
                <div className="flex flex-wrap gap-x-4 gap-y-1">
                  {u.firms.map((f) => (
                    <span key={f.org_id} className="inline-flex items-center gap-1.5 text-[0.8rem]">
                      {f.name} <StatusBadge value={f.status === "active" ? f.role : f.status} />
                    </span>
                  ))}
                </div>
              </Td>
              <Td>{fmtDateTime(u.last_seen_at)}</Td>
              <Td className="whitespace-nowrap text-right">
                <Button size="sm" variant="ghost" disabled={toggle.isPending}
                  onClick={() => toggle.mutate({ id: u.user_id, enabled: true, email: u.email })}>Enable</Button>
                <Button size="sm" variant="destructive" disabled={toggle.isPending}
                  onClick={() => { if (window.confirm(`Disable ${u.email}? They are signed out immediately.`)) toggle.mutate({ id: u.user_id, enabled: false, email: u.email }) }}>
                  Disable
                </Button>
              </Td>
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
    </>
  )
}
