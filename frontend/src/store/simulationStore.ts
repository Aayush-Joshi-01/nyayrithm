import { create } from "zustand";
import type { Turn, Agent, AgentGraph, WsEvent } from "@/types/api";

interface StreamingTurn {
  agentId: string;
  agentName: string;
  role: string;
  content: string;
  turnNumber: number;
}

interface Conflict {
  agentId: string;
  conflictingAgentId: string;
  evidenceIds: string[];
  turnNumber: number;
}

interface SimulationState {
  turns: Turn[];
  agents: Agent[];
  graph: AgentGraph;
  streaming: StreamingTurn | null;
  status: string;
  currentTurn: number;
  error: string | null;
  conflicts: Conflict[];

  setTurns: (turns: Turn[]) => void;
  setAgents: (agents: Agent[]) => void;
  setGraph: (graph: AgentGraph) => void;
  setStatus: (status: string) => void;
  clearError: () => void;

  handleWsEvent: (event: WsEvent) => void;
}

// Streaming turns are added to `turns` with a synthetic id so React keys stay
// stable; when the authoritative row is later fetched from the API it replaces
// the synthetic one (matched on agent_id + turn_number).
const syntheticId = (agentId: string, turnNumber: number) =>
  `live:${turnNumber}:${agentId}`;

function mergeTurns(existing: Turn[], incoming: Turn[]): Turn[] {
  const key = (t: Turn) => `${t.turn_number}:${t.agent_id}`;
  const map = new Map<string, Turn>();
  for (const t of existing) map.set(key(t), t);
  for (const t of incoming) map.set(key(t), t); // API rows win over synthetic
  return [...map.values()].sort((a, b) => a.turn_number - b.turn_number);
}

export const useSimulationStore = create<SimulationState>((set) => ({
  turns: [],
  agents: [],
  graph: { nodes: [], edges: [] },
  streaming: null,
  status: "draft",
  currentTurn: 0,
  error: null,
  conflicts: [],

  setTurns: (turns) =>
    set((state) => ({ turns: mergeTurns(state.turns, turns) })),
  setAgents: (agents) => set({ agents }),
  setGraph: (graph) => set({ graph }),
  setStatus: (status) => set({ status }),
  clearError: () => set({ error: null }),

  handleWsEvent: (event) => {
    switch (event.event) {
      case "turn.started":
        set({
          streaming: {
            agentId: event.data.agent_id,
            agentName: event.data.agent_name,
            role: event.data.role,
            content: "",
            turnNumber: event.data.turn_number,
          },
          currentTurn: event.data.turn_number,
          error: null,
        });
        break;

      case "turn.token":
        set((state) => ({
          streaming: state.streaming
            ? { ...state.streaming, content: state.streaming.content + event.data.token }
            : null,
        }));
        break;

      case "turn.completed": {
        const completedTurn: Turn = {
          id: syntheticId(event.data.agent_id, event.data.turn_number),
          simulation_id: "",
          agent_id: event.data.agent_id,
          turn_number: event.data.turn_number,
          content: event.data.content,
          content_edited: null,
          citations: event.data.citations ?? [],
          spawned_agents: event.data.spawned_agents ?? [],
          is_human_override: false,
          token_count: 0,
          latency_ms: 0,
          created_at: new Date().toISOString(),
        };
        set((state) => ({
          turns: mergeTurns(state.turns, [completedTurn]),
          streaming: null,
        }));
        break;
      }

      case "agent.spawned": {
        const { data } = event;
        set((state) => ({
          graph: {
            nodes: [
              ...state.graph.nodes.filter((n) => n.id !== data.agent_id),
              {
                id: data.agent_id,
                role: data.role,
                name: data.name,
                status: "active",
                is_predefined: false,
                llm_provider: "",
                llm_model: "",
                parent_id: data.parent_id,
              },
            ],
            edges: [
              ...state.graph.edges.filter((e) => e.target !== data.agent_id),
              { source: data.parent_id, target: data.agent_id, reason: data.reason },
            ],
          },
        }));
        break;
      }

      case "conflict.detected":
        set((state) => ({
          conflicts: [
            ...state.conflicts,
            {
              agentId: event.data.agent_id,
              conflictingAgentId: event.data.conflicting_agent_id,
              evidenceIds: event.data.evidence_ids ?? [],
              turnNumber: event.data.turn_number,
            },
          ],
        }));
        break;

      case "simulation.completed":
        set({ status: "completed", streaming: null });
        break;

      case "simulation.paused":
        set({ status: "paused", streaming: null });
        break;

      case "error":
        set({ error: event.data.message, streaming: null });
        break;

      case "connected":
      case "ping":
      case "pong":
        break;

      default:
        console.warn("Unhandled simulation event", event);
    }
  },
}));
