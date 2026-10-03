import ky, { HTTPError } from "ky"
import { clearAccessToken, getAccessToken, redirectToLogin } from "@/lib/auth-token"

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const client = ky.create({
  prefixUrl: `${BASE}/api/v1/admin`,
  timeout: 30000,
  hooks: {
    beforeRequest: [
      async (request) => {
        const token = await getAccessToken()
        if (token) request.headers.set("Authorization", `Bearer ${token}`)
      },
    ],
    afterResponse: [
      async (_req, _opts, response) => {
        if (response.status === 401) {
          clearAccessToken()
          redirectToLogin()
        }
      },
    ],
  },
})

/** The API's message for a failed call (our errors carry `message`, FastAPI's carry `detail`). */
export async function errorMessage(err: unknown): Promise<string> {
  if (err instanceof HTTPError) {
    try {
      const body = await err.response.clone().json()
      if (typeof body.message === "string") return body.message
      if (typeof body.detail === "string") return body.detail
      if (Array.isArray(body.detail)) return body.detail.map((d: { msg: string }) => d.msg).join("; ")
    } catch {
      /* fall through */
    }
    return `Request failed (${err.response.status})`
  }
  return err instanceof Error ? err.message : "Something went wrong"
}

// ── types ─────────────────────────────────────────────────────────────────────
export interface Seats { used: number; pending: number; limit: number }
export interface Usage { period: string; tokens: number; cost_usd: number; simulations: number; turns: number }

export interface Overview {
  firms: { total: number; active: number; suspended: number }
  users: number
  subscriptions: Record<string, number>
  this_month: Usage
}

export interface FirmRow {
  id: string; name: string; slug: string; status: string; created_at: string
  plan: string | null; subscription_status: string | null; period_end: string | null
  seats: Seats; usage: Usage
}

export interface Plan {
  code: string; name: string; seat_limit: number; monthly_simulations: number
  monthly_tokens: number; max_turns_per_sim: number; storage_mb: number
  features: Record<string, unknown>; is_active: boolean; firms?: number
}

export interface FirmDetail extends FirmRow {
  plan_detail: Plan | null
  subscription: {
    status: string; seats: number; current_period_start: string
    current_period_end: string | null; invoice_ref: string
  } | null
  members: { user_id: string; email: string; display_name: string; role: string; status: string; last_seen_at: string | null }[]
  pending_invites: { id: string; email: string; role: string; expires_at: string }[]
  counts: { cases: number; simulations: number; evidence: number }
  usage_history: Usage[]
}

export interface UserRow {
  user_id: string; email: string; display_name: string; last_seen_at: string | null
  firms: { org_id: string; name: string; role: string; status: string }[]
}

export interface AdminEvent {
  id: string; actor: string; action: string; target_type: string; target_id: string
  details: Record<string, unknown>; created_at: string
}

export interface Page<T> { items: T[]; total: number; page: number; size: number }

export interface LlmSummary {
  days: number; requests: number; errors: number; error_rate: number
  input_tokens: number; output_tokens: number; tokens: number; cost_usd: number
  latency_ms: { avg: number | null; p50: number | null; p95: number | null }
  avg_ttft_ms: number | null; estimated_share: number; unpriced_requests: number; note: string
}
export interface SeriesPoint { t: string; requests: number; errors: number; tokens: number; cost_usd: number; avg_latency_ms: number | null }
export interface BreakdownRow {
  key: string; requests: number; errors: number; error_rate: number; tokens: number
  input_tokens: number; output_tokens: number; cost_usd: number; avg_latency_ms: number | null
}
export interface FailureRow {
  created_at: string; kind: string; provider: string; model: string; error_code: string | null
  firm: string | null; agent_role: string | null; simulation_id: string | null; latency_ms: number | null
}
export interface QuotaRow {
  org_id: string; name: string; plan: string | null; status: string; subscription_status: string | null
  tokens: number; token_limit: number; token_utilisation: number | null
  simulations: number; simulation_limit: number; simulation_utilisation: number | null; cost_usd: number
}
export interface PriceRow { provider: string; model: string; input_per_mtok: number; output_per_mtok: number; source?: string; updated_by?: string }
export interface Prices { defaults: PriceRow[]; overrides: PriceRow[]; note: string }
export interface HealthCheck { name: string; ok: boolean; latency_ms: number; detail: string }

export type Breakdown = "model" | "provider" | "role" | "firm" | "kind"

// ── endpoints ─────────────────────────────────────────────────────────────────
export const adminApi = {
  overview: () => client.get("overview").json<Overview>(),
  system: () => client.get("system").json<{ ok: boolean; checks: HealthCheck[] }>(),
  events: (params: { page?: number; action?: string }) =>
    client.get("events", { searchParams: clean(params) }).json<Page<AdminEvent>>(),

  firms: (params: { q?: string; status?: string; page?: number }) =>
    client.get("firms", { searchParams: clean(params) }).json<Page<FirmRow>>(),
  firm: (id: string) => client.get(`firms/${id}`).json<FirmDetail>(),
  createFirm: (body: {
    name: string; plan_code: string; seats: number; owner_email: string
    period_end?: string | null; invoice_ref?: string; notes?: string; status?: string
  }) => client.post("firms", { json: body }).json<FirmRow & { owner_invite_url: string }>(),
  updateFirm: (id: string, body: { name?: string; status?: string }) =>
    client.patch(`firms/${id}`, { json: body }).json<FirmRow>(),
  inviteOwner: (id: string, email: string) =>
    client.post(`firms/${id}/owner-invite`, { json: { email } }).json<{ email: string; invite_url: string }>(),
  setSubscription: (id: string, body: {
    plan_code: string; status: string; seats: number
    period_end?: string | null; invoice_ref?: string; notes?: string
  }) => client.put(`firms/${id}/subscription`, { json: body }).json<FirmRow>(),

  plans: () => client.get("plans").json<Plan[]>(),
  savePlan: (code: string, body: Omit<Plan, "code" | "firms">) =>
    client.put(`plans/${encodeURIComponent(code)}`, { json: body }).json<Plan>(),
  retirePlan: (code: string) => client.delete(`plans/${encodeURIComponent(code)}`),

  users: (params: { q?: string; page?: number }) =>
    client.get("users", { searchParams: clean(params) }).json<Page<UserRow>>(),
  setUserEnabled: (userId: string, enabled: boolean) =>
    client.post(`users/${encodeURIComponent(userId)}/${enabled ? "enable" : "disable"}`),

  llm: {
    summary: (days: number, orgId?: string) =>
      client.get("llmops/summary", { searchParams: clean({ days, org_id: orgId }) }).json<LlmSummary>(),
    series: (days: number, bucket: "day" | "hour", orgId?: string) =>
      client.get("llmops/timeseries", { searchParams: clean({ days, bucket, org_id: orgId }) }).json<SeriesPoint[]>(),
    breakdown: (by: Breakdown, days: number, orgId?: string) =>
      client.get("llmops/breakdown", { searchParams: clean({ by, days, org_id: orgId }) }).json<BreakdownRow[]>(),
    failures: (days: number) =>
      client.get("llmops/failures", { searchParams: clean({ days }) }).json<FailureRow[]>(),
    quota: () => client.get("llmops/quota").json<QuotaRow[]>(),
    prices: () => client.get("llmops/prices").json<Prices>(),
    setPrice: (body: PriceRow) => client.put("llmops/prices", { json: body }),
    clearPrice: (provider: string, model: string) =>
      client.delete(`llmops/prices/${encodeURIComponent(provider)}/${encodeURIComponent(model)}`),
  },
}

function clean(params: Record<string, string | number | undefined | null>) {
  const out: Record<string, string | number> = {}
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== "") out[k] = v
  return out
}
