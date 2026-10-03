"use client"

import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Info, Trash2 } from "lucide-react"
import { adminApi, errorMessage, type Breakdown } from "@/lib/api"
import { BarChart } from "@/components/charts"
import { Busy, ErrorNote, Field, Kpi, Loading, PageHeader, Section, StatusBadge, Table, Td, UtilBar } from "@/components/kit"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { fmtCompact, fmtDateTime, fmtInt, fmtMs, fmtPct, fmtUsd } from "@/lib/utils"

const RANGES = [{ days: 7, label: "7 days" }, { days: 30, label: "30 days" }, { days: 90, label: "90 days" }]
const BREAKDOWNS: { id: Breakdown; label: string }[] = [
  { id: "model", label: "Model" }, { id: "provider", label: "Provider" }, { id: "role", label: "Agent role" },
  { id: "firm", label: "Firm" }, { id: "kind", label: "Call type" },
]
type Metric = "tokens" | "cost" | "requests"

export default function LlmOpsPage() {
  const [days, setDays] = useState(30)
  const [by, setBy] = useState<Breakdown>("model")
  const [metric, setMetric] = useState<Metric>("tokens")

  const summary = useQuery({ queryKey: ["llm-summary", days], queryFn: () => adminApi.llm.summary(days) })
  const series = useQuery({
    queryKey: ["llm-series", days],
    queryFn: () => adminApi.llm.series(days, days <= 7 ? "hour" : "day"),
  })
  const rows = useQuery({ queryKey: ["llm-breakdown", by, days], queryFn: () => adminApi.llm.breakdown(by, days) })
  const quota = useQuery({ queryKey: ["llm-quota"], queryFn: adminApi.llm.quota })
  const failures = useQuery({ queryKey: ["llm-failures", days], queryFn: () => adminApi.llm.failures(Math.min(days, 30)) })
  const s = summary.data

  const chart = (series.data ?? []).map((p) => ({
    label: p.t.replace("T", " "),
    value: metric === "tokens" ? p.tokens : metric === "cost" ? p.cost_usd : p.requests,
    errors: p.errors,
  }))
  const fmtMetric = metric === "tokens" ? fmtCompact : metric === "cost" ? fmtUsd : fmtInt

  return (
    <>
      <PageHeader
        title="LLMOps"
        intro="Every model call the platform makes: who it was for, what it used, how long it took."
        actions={
          <Tabs value={String(days)} onValueChange={(v) => setDays(Number(v))}>
            <TabsList aria-label="Time range">
              {RANGES.map((r) => <TabsTrigger key={r.days} value={String(r.days)}>{r.label}</TabsTrigger>)}
            </TabsList>
          </Tabs>
        }
      />
      <ErrorNote error={summary.error} />

      {summary.isLoading || !s ? (
        <Loading rows={2} />
      ) : (
        <>
          <div className="mb-3 grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Kpi label="Requests" value={fmtCompact(s.requests)} sub={`${fmtInt(s.errors)} failed (${fmtPct(s.error_rate)})`} tone={s.error_rate > 0.05 ? "bad" : undefined} />
            <Kpi label="Tokens" value={fmtCompact(s.tokens)} sub={`${fmtCompact(s.input_tokens)} in · ${fmtCompact(s.output_tokens)} out`} />
            <Kpi label="Est. cost" value={fmtUsd(s.cost_usd)} sub={s.unpriced_requests ? `${s.unpriced_requests} calls have no price` : "all calls priced"} tone={s.unpriced_requests ? "warn" : undefined} />
            <Kpi label="Latency p50 / p95" value={`${fmtMs(s.latency_ms.p50)} / ${fmtMs(s.latency_ms.p95)}`} sub={`first token ≈ ${fmtMs(s.avg_ttft_ms)}`} />
          </div>
          <p className="mb-8 flex items-start gap-2 text-[0.76rem] leading-relaxed text-foreground/40">
            <Info className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" aria-hidden />
            {s.note} {fmtPct(s.estimated_share, 0)} of calls in this period used estimated token counts.
          </p>
        </>
      )}

      <Section
        title="Over time"
        actions={
          <Tabs value={metric} onValueChange={(v) => setMetric(v as Metric)}>
            <TabsList aria-label="Metric">
              <TabsTrigger value="tokens">Tokens</TabsTrigger>
              <TabsTrigger value="cost">Cost</TabsTrigger>
              <TabsTrigger value="requests">Requests</TabsTrigger>
            </TabsList>
          </Tabs>
        }
      >
        <div className="rounded-md border border-border p-4">
          {series.isLoading ? <Loading rows={2} /> : (
            <BarChart data={chart} format={fmtMetric} ariaLabel={`${metric} per ${days <= 7 ? "hour" : "day"}`} />
          )}
        </div>
      </Section>

      <Section
        title="Breakdown"
        actions={
          <Tabs value={by} onValueChange={(v) => setBy(v as Breakdown)}>
            <TabsList aria-label="Group by">
              {BREAKDOWNS.map((b) => <TabsTrigger key={b.id} value={b.id}>{b.label}</TabsTrigger>)}
            </TabsList>
          </Tabs>
        }
      >
        {rows.isLoading ? <Loading /> : (
          <Table head={[BREAKDOWNS.find((b) => b.id === by)!.label, "Requests", "Tokens", "Est. cost", "Avg latency", "Errors"]} empty="No calls in this period." rowCount={rows.data?.length ?? 0}>
            {rows.data?.map((r) => (
              <tr key={r.key}>
                <Td><span className="font-medium text-bone">{r.key}</span></Td>
                <Td mono>{fmtInt(r.requests)}</Td>
                <Td mono>{fmtCompact(r.tokens)}</Td>
                <Td mono>{fmtUsd(r.cost_usd)}</Td>
                <Td mono>{fmtMs(r.avg_latency_ms)}</Td>
                <Td mono className={r.errors ? "text-oxblood-bright" : ""}>{r.errors ? `${r.errors} (${fmtPct(r.error_rate)})` : "0"}</Td>
              </tr>
            ))}
          </Table>
        )}
      </Section>

      <Section title="Quota use this month" hint="highest first">
        {quota.isLoading ? <Loading /> : (
          <Table head={["Firm", "Plan", "Tokens", "Simulations", "Est. cost"]} empty="No firms yet." rowCount={quota.data?.length ?? 0}>
            {quota.data?.map((q) => (
              <tr key={q.org_id}>
                <Td>
                  <span className="font-medium text-bone">{q.name}</span>{" "}
                  {q.status !== "active" && <StatusBadge value={q.status} />}
                </Td>
                <Td>{q.plan ?? "–"} {q.subscription_status && q.subscription_status !== "active" && <StatusBadge value={q.subscription_status} />}</Td>
                <Td>
                  <UtilBar value={q.token_utilisation} label={`${fmtCompact(q.tokens)} of ${fmtCompact(q.token_limit)} tokens`} />
                  <span className="font-mono text-[0.68rem] text-foreground/35">{fmtCompact(q.tokens)} / {fmtCompact(q.token_limit)}</span>
                </Td>
                <Td>
                  <UtilBar value={q.simulation_utilisation} label={`${q.simulations} of ${q.simulation_limit} simulations`} />
                  <span className="font-mono text-[0.68rem] text-foreground/35">{q.simulations} / {q.simulation_limit}</span>
                </Td>
                <Td mono>{fmtUsd(q.cost_usd)}</Td>
              </tr>
            ))}
          </Table>
        )}
      </Section>

      <Section title="Recent failures" hint="no prompts or content are stored here">
        {failures.isLoading ? <Loading /> : (
          <Table head={["When", "Firm", "Call", "Model", "Error", "Role"]} empty="No failed calls. 🎉" rowCount={failures.data?.length ?? 0}>
            {failures.data?.map((f, i) => (
              <tr key={i}>
                <Td>{fmtDateTime(f.created_at)}</Td>
                <Td>{f.firm ?? <span className="text-foreground/30">–</span>}</Td>
                <Td>{f.kind}</Td>
                <Td mono>{f.provider}/{f.model}</Td>
                <Td mono className="text-oxblood-bright">{f.error_code ?? "error"}</Td>
                <Td>{f.agent_role ?? "–"}</Td>
              </tr>
            ))}
          </Table>
        )}
      </Section>

      <PriceEditor />
    </>
  )
}

function PriceEditor() {
  const qc = useQueryClient()
  const prices = useQuery({ queryKey: ["llm-prices"], queryFn: adminApi.llm.prices })
  const [f, setF] = useState({ provider: "", model: "", input: "", output: "" })
  const [error, setError] = useState("")
  const refresh = () => qc.invalidateQueries({ queryKey: ["llm-prices"] })

  const save = useMutation({
    mutationFn: () => adminApi.llm.setPrice({
      provider: f.provider.trim(), model: f.model.trim(),
      input_per_mtok: Number(f.input), output_per_mtok: Number(f.output),
    }),
    onSuccess: () => { refresh(); setF({ provider: "", model: "", input: "", output: "" }) },
    onError: async (e) => setError(await errorMessage(e)),
  })
  const clear = useMutation({
    mutationFn: (v: { provider: string; model: string }) => adminApi.llm.clearPrice(v.provider, v.model),
    onSuccess: refresh,
  })
  const valid = f.provider.trim() && f.model.trim() && f.input !== "" && f.output !== "" && Number(f.input) >= 0 && Number(f.output) >= 0
  const effective = new Set((prices.data?.overrides ?? []).map((o) => `${o.provider}/${o.model}`))

  return (
    <Section title="Prices" hint="USD per million tokens">
      <p className="mb-3 text-[0.8rem] leading-relaxed text-foreground/45">{prices.data?.note}</p>
      <form onSubmit={(e) => { e.preventDefault(); setError(""); save.mutate() }} className="mb-4 grid gap-3 rounded-md border border-border p-4 sm:grid-cols-5">
        <Field label="Provider"><Input placeholder="openai" value={f.provider} onChange={(e) => setF({ ...f, provider: e.target.value })} /></Field>
        <Field label="Model" hint="exact name"><Input placeholder="gpt-4o-mini" value={f.model} onChange={(e) => setF({ ...f, model: e.target.value })} /></Field>
        <Field label="Input $/M"><Input type="number" min={0} step="any" value={f.input} onChange={(e) => setF({ ...f, input: e.target.value })} /></Field>
        <Field label="Output $/M"><Input type="number" min={0} step="any" value={f.output} onChange={(e) => setF({ ...f, output: e.target.value })} /></Field>
        <div className="flex items-end"><Button type="submit" size="sm" disabled={!valid || save.isPending}>{save.isPending && <Busy />} Set override</Button></div>
        {error && <p role="alert" className="text-[0.8rem] text-oxblood-bright sm:col-span-5">{error}</p>}
      </form>

      {(prices.data?.overrides.length ?? 0) > 0 && (
        <div className="mb-4">
          <Table head={["Your overrides", "Input $/M", "Output $/M", ""]} rowCount={prices.data!.overrides.length}>
            {prices.data!.overrides.map((o) => (
              <tr key={`${o.provider}/${o.model}`}>
                <Td mono>{o.provider}/{o.model}</Td><Td mono>{o.input_per_mtok}</Td><Td mono>{o.output_per_mtok}</Td>
                <Td className="text-right">
                  <Button size="sm" variant="ghost" aria-label={`Remove override for ${o.model}`} onClick={() => clear.mutate({ provider: o.provider, model: o.model })}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </Td>
              </tr>
            ))}
          </Table>
        </div>
      )}
      <Table head={["Reference prices", "Input $/M", "Output $/M"]} rowCount={prices.data?.defaults.length ?? 0}>
        {prices.data?.defaults.map((d) => (
          <tr key={`${d.provider}/${d.model}`} className={effective.has(`${d.provider}/${d.model}`) ? "opacity-40" : ""}>
            <Td mono>{d.provider}/{d.model === "*" ? "(any model)" : d.model}</Td><Td mono>{d.input_per_mtok}</Td><Td mono>{d.output_per_mtok}</Td>
          </tr>
        ))}
      </Table>
    </Section>
  )
}
