"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Plus, Search } from "lucide-react"
import { casesApi } from "@/lib/api"
import { CaseCard } from "./CaseCard"
import { CaseCreateModal } from "./CaseCreateModal"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import type { Case } from "@/types/api"

export function CaseDashboard() {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState("")
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ["cases"],
    queryFn: () => casesApi.list({ size: 50 }),
  })

  const createMutation = useMutation({
    mutationFn: casesApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cases"] })
      setOpen(false)
    },
  })

  const cases: Case[] = data?.items ?? []
  const filtered = search.trim()
    ? cases.filter(
        (c) =>
          c.title.toLowerCase().includes(search.toLowerCase()) ||
          c.description?.toLowerCase().includes(search.toLowerCase())
      )
    : cases

  const counts = cases.reduce<Record<string, number>>((acc, c) => {
    acc[c.status] = (acc[c.status] ?? 0) + 1
    return acc
  }, {})

  return (
    <div className="mx-auto max-w-6xl">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl font-medium tracking-tight text-bone">Cases</h1>
          <p className="mt-1 text-[0.85rem] text-foreground/45">
            {cases.length > 0 ? (
              <span className="tabular font-mono text-[0.78rem]">
                {cases.length} on the docket
                {counts.in_simulation ? `, ${counts.in_simulation} in session` : ""}
                {counts.closed ? `, ${counts.closed} closed` : ""}
              </span>
            ) : (
              "Assemble evidence, seat a bench, run a proceeding."
            )}
          </p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus className="mr-2 h-4 w-4" strokeWidth={2} />
          New case
        </Button>
      </div>

      {!isLoading && cases.length > 0 && (
        <div className="relative mt-8 max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-foreground/25" strokeWidth={1.75} />
          <Input
            placeholder="Search the docket"
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      )}

      <div className="mt-8">
        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="h-44" />
            ))}
          </div>
        ) : filtered.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filtered.map((c) => (
              <CaseCard key={c.id} case_={c} />
            ))}
          </div>
        ) : search ? (
          <div className="border-t border-hairline py-20 text-center">
            <p className="font-serif text-[1.05rem] text-foreground/55">
              Nothing on the docket matches &ldquo;{search}&rdquo;.
            </p>
            <button
              onClick={() => setSearch("")}
              className="mt-3 font-mono text-xs uppercase tracking-wide text-brass-text hover:text-brass-lit"
            >
              Clear search
            </button>
          </div>
        ) : (
          <div className="relative overflow-hidden rounded-lg border border-border bg-ink-raised/60 px-8 py-16 text-center">
            <div className="pointer-events-none absolute inset-0 bench-light-tight opacity-60" />
            <div className="relative">
              <p className="font-serif text-xl font-medium text-bone">The docket is empty.</p>
              <p className="mx-auto mt-3 max-w-sm text-[0.9rem] leading-relaxed text-foreground/50">
                A case holds the evidence for one matter and every proceeding you
                run against it. Open the first one to begin.
              </p>
              <Button className="mt-7" onClick={() => setOpen(true)}>
                <Plus className="mr-2 h-4 w-4" strokeWidth={2} />
                Open a case
              </Button>
            </div>
          </div>
        )}
      </div>

      <CaseCreateModal
        open={open}
        onClose={() => setOpen(false)}
        onSubmit={(d) => createMutation.mutate(d)}
        loading={createMutation.isPending}
      />
    </div>
  )
}
