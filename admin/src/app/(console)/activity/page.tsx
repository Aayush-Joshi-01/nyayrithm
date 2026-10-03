"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { adminApi } from "@/lib/api"
import { ErrorNote, Loading, PageHeader, Table, Td } from "@/components/kit"
import { Button } from "@/components/ui/button"
import { fmtDateTime } from "@/lib/utils"

export default function ActivityPage() {
  const [page, setPage] = useState(1)
  const events = useQuery({ queryKey: ["events", page], queryFn: () => adminApi.events({ page }) })
  const pages = events.data ? Math.max(1, Math.ceil(events.data.total / events.data.size)) : 1

  return (
    <>
      <PageHeader title="Activity" intro="Every change made from this console, newest first." />
      <ErrorNote error={events.error} />
      {events.isLoading ? (
        <Loading />
      ) : (
        <Table head={["When", "Who", "What", "On", "Details"]} empty="Nothing has been changed yet." rowCount={events.data?.items.length ?? 0}>
          {events.data?.items.map((e) => (
            <tr key={e.id}>
              <Td>{fmtDateTime(e.created_at)}</Td>
              <Td mono>{e.actor}</Td>
              <Td><span className="font-medium text-bone">{e.action}</span></Td>
              <Td mono>{e.target_type ? `${e.target_type}:${e.target_id.slice(0, 8)}` : "–"}</Td>
              <Td className="max-w-[320px] truncate font-mono text-[0.72rem] text-foreground/45" >
                <span title={JSON.stringify(e.details)}>{Object.entries(e.details).map(([k, v]) => `${k}=${String(v)}`).join(" · ") || "–"}</span>
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
