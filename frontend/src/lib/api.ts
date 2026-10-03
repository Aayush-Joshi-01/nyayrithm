import ky from "ky";
import type {
  Case, Evidence, Simulation, Agent, Turn, AgentGraph,
  ProcedureInfo, AuditVerification, LegalReview,
} from "@/types/api";
import { clearAccessToken, getAccessToken, redirectToLogin } from "@/lib/auth-token";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Every request carries the user's Keycloak access token. A 401 means the session
// is gone (refresh failed), so send the user back to the login page.
const authed = ky.create({
  prefixUrl: `${BASE}/api/v1`,
  timeout: 30000,
  hooks: {
    beforeRequest: [
      async (request) => {
        const token = await getAccessToken();
        if (token) request.headers.set("Authorization", `Bearer ${token}`);
      },
    ],
    afterResponse: [
      async (_request, _options, response) => {
        if (response.status === 401) {
          clearAccessToken();
          redirectToLogin();
        }
      },
    ],
  },
});

// JSON by default; multipart uploads use `authed` so the browser sets the boundary.
const client = authed.extend({ headers: { "Content-Type": "application/json" } });

// ── Cases ─────────────────────────────────────────────────────────────────────
export const casesApi = {
  list: (params?: { page?: number; size?: number; status?: string }) =>
    client.get("cases/", { searchParams: params ?? {} }).json<{ items: Case[]; total: number }>(),

  get: (id: string) => client.get(`cases/${id}`).json<Case>(),

  create: (body: {
    title: string;
    description?: string;
    country: string;
    jurisdiction?: string;
    legal_system?: string;
  }) => client.post("cases/", { json: body }).json<Case>(),

  update: (id: string, body: Partial<Case>) =>
    client.put(`cases/${id}`, { json: body }).json<Case>(),

  delete: (id: string) => client.delete(`cases/${id}`),
};

// ── Evidence ──────────────────────────────────────────────────────────────────
export const evidenceApi = {
  list: (caseId: string, params?: { page?: number; size?: number }) =>
    client
      .get(`cases/${caseId}/evidence/`, { searchParams: params ?? {} })
      .json<{ items: Evidence[]; total: number }>(),

  upload: (caseId: string, file: File, title?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (title) form.append("title", title);
    return authed.post(`cases/${caseId}/evidence/`, { body: form, timeout: 120000 }).json<Evidence>();
  },

  reindex: (caseId: string, evidenceId: string) =>
    client.post(`cases/${caseId}/evidence/${evidenceId}/reindex`).json(),

  delete: (caseId: string, evidenceId: string) =>
    client.delete(`cases/${caseId}/evidence/${evidenceId}`),

  search: (caseId: string, query: string, top_k = 5) =>
    client.post(`cases/${caseId}/search`, { json: { query, top_k } }).json<
      Array<{
        chunk_id: string;
        evidence_id: string;
        evidence_title: string;
        text: string;
        modality: string;
        score: number;
      }>
    >(),
};

// ── Simulations ───────────────────────────────────────────────────────────────
export const simulationsApi = {
  list: (caseId: string) =>
    client.get(`cases/${caseId}/simulations/`).json<Simulation[]>(),

  get: (simId: string) => client.get(`simulations/${simId}`).json<Simulation>(),

  create: (
    caseId: string,
    body: { title: string; mode?: string; max_turns?: number; config?: Record<string, unknown> },
  ) => client.post(`cases/${caseId}/simulations/`, { json: body }).json<Simulation>(),

  start: (simId: string) => client.post(`simulations/${simId}/start`).json(),
  pause: (simId: string) => client.post(`simulations/${simId}/pause`).json(),
  stop: (simId: string) => client.post(`simulations/${simId}/stop`).json(),
  remove: (simId: string) => client.delete(`simulations/${simId}`),
  clone: (simId: string) => client.post(`simulations/${simId}/clone`).json<Simulation>(),

  getGraph: (simId: string) =>
    client.get(`simulations/${simId}/graph`).json<AgentGraph>(),

  listAgents: (simId: string) =>
    client.get(`simulations/${simId}/agents`).json<Agent[]>(),

  addAgent: (simId: string, body: {
    role: string;
    name: string;
    llm_provider?: string;
    llm_model?: string;
    persona?: Record<string, unknown>;
  }) => client.post(`simulations/${simId}/agents`, { json: body }).json<Agent>(),

  deleteAgent: (simId: string, agentId: string) =>
    client.delete(`simulations/${simId}/agents/${agentId}`),

  listTurns: (simId: string, params?: { page?: number; size?: number }) =>
    client.get(`simulations/${simId}/turns`, { searchParams: params ?? {} })
      .json<{ items: Turn[]; total: number }>(),

  editTurn: (simId: string, turnId: string, content: string) =>
    client.patch(`simulations/${simId}/turns/${turnId}`, { json: { content } }).json<Turn>(),
};

// ── Legal accuracy ────────────────────────────────────────────────────────────
export const legalApi = {
  procedure: (simId: string) =>
    client.get(`simulations/${simId}/procedure`).json<ProcedureInfo>(),

  verifyAudit: (simId: string) =>
    client.get(`simulations/${simId}/audit/verify`).json<AuditVerification>(),

  verifyText: (body: { text: string; case_id?: string; country?: string }) =>
    client.post("legal/verify", { json: body }).json<LegalReview & { notice: string }>(),
};

// ── Agents ────────────────────────────────────────────────────────────────────
export const agentsApi = {
  listRoles: () => client.get("agents/roles/").json<Record<string, { provider: string; model: string }>>(),
  listProviders: () => client.get("agents/providers/").json<{ providers: string[] }>(),
};
