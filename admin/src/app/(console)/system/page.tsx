"use client"

import { useQuery } from "@tanstack/react-query"
import { RefreshCw } from "lucide-react"
import { adminApi } from "@/lib/api"
import { ErrorNote, Loading, PageHeader, Table, Td } from "@/components/kit"
import { Button } from "@/components/ui/button"
import { cn, fmtMs } from "@/lib/utils"

export default function SystemPage() {
  const system = useQuery({ queryKey: ["system"], queryFn: adminApi.system, refetchInterval: 30_000 })
  return (
    <>
      <PageHeader
        title="System"
        intro="Whether each service the platform depends on is answering. Checked live, refreshed every 30 seconds."
        actions={
          <Button size="sm" variant="outline" onClick={() => system.refetch()} disabled={system.isFetching}>
            <RefreshCw className={cn("mr-1.5 h-3.5 w-3.5", system.isFetching && "animate-spin")} /> Check now
          </Button>
        }
      />
      <ErrorNote error={system.error} />
      {system.isLoading ? (
        <Loading />
      ) : (
        <>
          <p role="status" className={cn("mb-4 text-[0.9rem]", system.data?.ok ? "text-role-witness" : "text-oxblood-bright")}>
            {system.data?.ok ? "Everything is answering." : "Something is not answering. See the red rows."}
          </p>
          <Table head={["Service", "State", "Latency", "Detail"]} rowCount={system.data?.checks.length ?? 0}>
            {system.data?.checks.map((c) => (
              <tr key={c.name}>
                <Td><span className="font-medium text-bone">{c.name}</span></Td>
                <Td>
                  <span className={cn("inline-flex items-center gap-2", c.ok ? "text-role-witness" : "text-oxblood-bright")}>
                    <span className={cn("h-1.5 w-1.5 rounded-full", c.ok ? "bg-role-witness" : "bg-oxblood-bright")} aria-hidden />
                    {c.ok ? "Healthy" : "Down"}
                  </span>
                </Td>
                <Td mono>{fmtMs(c.latency_ms)}</Td>
                <Td className="font-mono text-[0.74rem] text-foreground/50">{c.detail || "–"}</Td>
              </tr>
            ))}
          </Table>
        </>
      )}
    </>
  )
}
