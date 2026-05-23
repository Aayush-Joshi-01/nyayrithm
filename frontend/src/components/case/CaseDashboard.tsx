"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Plus, FolderOpen, Search, Scale } from "lucide-react"
import { casesApi } from "@/lib/api"
import { CaseCard } from "./CaseCard"
import { CaseCreateModal } from "./CaseCreateModal"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
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

  const statusCounts = cases.reduce<Record<string, number>>((acc, c) => {
    acc[c.status] = (acc[c.status] ?? 0) + 1
    return acc
  }, {})

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Cases</h1>
          <p className="text-sm text-white/40 mt-1">
            Manage legal cases and courtroom simulations
          </p>
        </div>
        <Button variant="amber" onClick={() => setOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Case
        </Button>
      </div>

      {/* Stats */}
      {!isLoading && cases.length > 0 && (
        <div className="flex items-center gap-3 flex-wrap">
          <div className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-white/50 flex items-center gap-2">
            <Scale className="w-3.5 h-3.5 text-amber-400" />
            <span className="font-medium text-white/70">{cases.length}</span>
            total cases
          </div>
          {statusCounts.open && (
            <Badge variant="success" className="text-xs">{statusCounts.open} open</Badge>
          )}
          {statusCounts.in_simulation && (
            <Badge variant="warning" className="text-xs animate-pulse-slow">
              {statusCounts.in_simulation} simulating
            </Badge>
          )}
          {statusCounts.closed && (
            <Badge variant="muted" className="text-xs">{statusCounts.closed} closed</Badge>
          )}
        </div>
      )}

      {/* Search */}
      {!isLoading && cases.length > 0 && (
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
          <Input
            placeholder="Search cases…"
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      )}

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-48 rounded-xl" />
          ))}
        </div>
      ) : filtered.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((c) => (
            <CaseCard key={c.id} case_={c} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mb-4">
            <FolderOpen className="w-7 h-7 text-amber-400/60" />
          </div>
          <h3 className="text-white/60 font-semibold mb-1">
            {search ? "No cases found" : "No cases yet"}
          </h3>
          <p className="text-white/30 text-sm mb-6">
            {search ? "Try a different search term." : "Create your first case to get started."}
          </p>
          {!search && (
            <Button variant="amber" onClick={() => setOpen(true)}>
              <Plus className="w-4 h-4 mr-2" />
              New Case
            </Button>
          )}
        </div>
      )}

      <CaseCreateModal
        open={open}
        onClose={() => setOpen(false)}
        onSubmit={(data) => createMutation.mutate(data)}
        loading={createMutation.isPending}
      />
    </div>
  )
}
