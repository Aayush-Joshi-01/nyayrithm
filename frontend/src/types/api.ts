export interface Case {
  id: string;
  title: string;
  description: string;
  country: string;
  jurisdiction: string;
  legal_system: string;
  status: "open" | "in_simulation" | "closed" | "archived";
  created_by: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Evidence {
  id: string;
  case_id: string;
  title: string;
  description: string;
  evidence_type: string;
  modality: "text" | "audio" | "video" | "image" | "multimodal";
  file_path: string;
  file_size: number;
  mime_type: string;
  status: "pending" | "processing" | "indexed" | "error";
  chunk_count: number;
  tags: string[];
  linked_participants: string[];
  metadata: Record<string, unknown>;
  embedder_used: string | null;
  indexed_at: string | null;
  created_at: string;
}

export interface Agent {
  id: string;
  simulation_id: string;
  parent_agent_id: string | null;
  spawn_reason: string | null;
  is_predefined: boolean;
  role: AgentRole;
  name: string;
  llm_provider: string;
  llm_model: string;
  persona: Record<string, unknown>;
  knowledge_scope: Record<string, unknown>;
  status: "active" | "suspended" | "dismissed";
  spawned_at: string;
}

export type AgentRole =
  | "judge"
  | "prosecutor"
  | "defense"
  | "plaintiff"
  | "accused"
  | "witness"
  | "investigator"
  | "expert_witness"
  | "custom";

export interface Simulation {
  id: string;
  case_id: string;
  title: string;
  mode: "courtroom" | "deposition" | "strategy";
  status: "draft" | "running" | "paused" | "completed" | "failed";
  current_turn: number;
  max_turns: number;
  turn_order: string[];
  config: Record<string, unknown>;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
  disclaimer?: string;
}

export interface Citation {
  evidence_id: string;
  chunk_index: number;
  chunk_text: string;
  score: number;
  evidence_title: string | null;
  modality: string;
}

export interface Turn {
  id: string;
  simulation_id: string;
  agent_id: string;
  turn_number: number;
  content: string;
  content_edited: string | null;
  citations: Citation[];
  spawned_agents: string[];
  is_human_override: boolean;
  token_count: number;
  latency_ms: number;
  created_at: string;
  legal_review?: LegalReview | null;
  procedure?: ProcedureReview | null;
}

/* Legal accuracy: every legal authority an agent cites is checked against the
   jurisdiction pack. "unverified"/"unindexed" mean "could not be checked", not "wrong". */
export type LegalCitationStatus =
  | "verified"
  | "superseded"
  | "unindexed"
  | "unverified"
  | "mismatch"
  | "nonexistent";

export interface LegalCitation {
  kind: "statute" | "constitution" | "case";
  raw: string;
  status: LegalCitationStatus;
  severity: "ok" | "notice" | "warning" | "error";
  message: string;
  ref: string | null;
  title: string | null;
  successor: string | null;
}

export interface LegalReview {
  pack_id: string | null;
  status: "clean" | "notices" | "flagged" | "no_pack";
  counts: Record<string, number>;
  citations: LegalCitation[];
}

export interface ProcedureReview {
  stage: string;
  stage_label: string;
  objection: { ground: string | null } | null;
  ruling: "sustained" | "overruled" | null;
  violations: { code: string; message: string }[];
}

export interface ProcedureStage {
  key: string;
  label: string;
  start_turn: number;
  end_turn: number;
  turns: number;
  speakers: string[];
  note: string | null;
}

export interface ProcedureInfo {
  enforced: boolean;
  mode: string;
  stages: ProcedureStage[];
  current_stage: string | null;
  current_turn?: number;
}

export interface AuditVerification {
  valid: boolean;
  events: number;
  broken_at: number | null;
  reason: string | null;
  head_hash: string | null;
}

export interface AgentGraphNode {
  id: string;
  role: AgentRole;
  name: string;
  status: string;
  is_predefined: boolean;
  llm_provider: string;
  llm_model: string;
  parent_id: string | null;
}

export interface AgentGraphEdge {
  source: string;
  target: string;
  reason: string | null;
}

export interface AgentGraph {
  nodes: AgentGraphNode[];
  edges: AgentGraphEdge[];
}

// WebSocket event types
export type WsEvent =
  | { event: "connected"; data: { simulation_id: string } }
  | { event: "turn.started"; data: { turn_number: number; agent_id: string; agent_name: string; role: AgentRole } }
  | { event: "turn.token"; data: { agent_id: string; token: string } }
  | { event: "turn.completed"; data: { turn_number: number; agent_id: string; agent_name: string; role: AgentRole; content: string; citations: Citation[]; spawned_agents: string[]; legal_review?: LegalReview | null; procedure?: ProcedureReview | null } }
  | { event: "citation.flagged"; data: { agent_id: string; turn_number: number; citations: LegalCitation[] } }
  | { event: "agent.spawned"; data: { agent_id: string; role: AgentRole; name: string; parent_id: string; reason: string } }
  | { event: "simulation.completed"; data: { simulation_id: string } }
  | { event: "simulation.paused"; data: { simulation_id: string } }
  | { event: "conflict.detected"; data: { agent_id: string; conflicting_agent_id: string; evidence_ids: string[]; turn_number: number } }
  | { event: "quota.exceeded"; data: { reason: string; message: string } }
  | { event: "error"; data: { message: string } }
  | { event: "ping" | "pong" };

// ── Firms (tenancy) ───────────────────────────────────────────────────────────
export type FirmRole = "owner" | "admin" | "attorney";

export interface FirmSummary {
  org_id: string;
  name: string;
  slug: string;
  status: "active" | "suspended";
  role: FirmRole;
}

export interface Me {
  user: { id: string; email: string | null; name: string | null; platform_admin: boolean };
  firms: FirmSummary[];
  roles: FirmRole[];
}

export interface Member {
  user_id: string;
  email: string;
  display_name: string;
  role: FirmRole;
  created_at: string;
}

export interface Invite {
  id: string;
  email: string;
  role: FirmRole;
  status: string;
  expires_at: string;
  created_at: string;
  invite_url: string | null;
}

export interface InvitePreview {
  org_name: string;
  email: string;
  role: FirmRole;
  expires_at: string;
}

export interface FirmSubscription {
  subscription: {
    status: "trialing" | "active" | "past_due" | "cancelled";
    seats: number;
    current_period_start: string;
    current_period_end: string | null;
    invoice_ref: string;
  } | null;
  plan: {
    code: string;
    name: string;
    seat_limit: number;
    monthly_simulations: number;
    monthly_tokens: number;
    max_turns_per_sim: number;
    storage_mb: number;
  } | null;
  seats: { used: number; pending: number; limit: number };
  usage: { period: string; tokens: number; cost_usd: number; simulations: number; turns: number };
  storage_used_bytes?: number;
}

export interface CaseShare {
  user_id: string;
  email: string;
  added_by: string;
  created_at: string;
}
