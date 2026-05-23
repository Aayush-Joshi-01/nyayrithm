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
  | { event: "turn.completed"; data: { turn_number: number; agent_id: string; agent_name: string; role: AgentRole; content: string; citations: Citation[]; spawned_agents: string[] } }
  | { event: "agent.spawned"; data: { agent_id: string; role: AgentRole; name: string; parent_id: string; reason: string } }
  | { event: "simulation.completed"; data: { simulation_id: string } }
  | { event: "simulation.paused"; data: { simulation_id: string } }
  | { event: "conflict.detected"; data: { agent_id: string; conflicting_agent_id: string; evidence_ids: string[]; turn_number: number } }
  | { event: "error"; data: { message: string } }
  | { event: "ping" | "pong" };
