import { create } from "zustand";
import type { Turn, Agent, AgentGraph, WsEvent } from "@/types/api";

interface StreamingTurn {
  agentId: string;
  agentName: string;
  role: string;
  content: string;
}

interface SimulationState {
  turns: Turn[];
  agents: Agent[];
  graph: AgentGraph;
  streaming: StreamingTurn | null;
  status: string;
  currentTurn: number;

  setTurns: (turns: Turn[]) => void;
  setAgents: (agents: Agent[]) => void;
  setGraph: (graph: AgentGraph) => void;
  setStatus: (status: string) => void;

  handleWsEvent: (event: WsEvent) => void;
}

export const useSimulationStore = create<SimulationState>((set, get) => ({
  turns: [],
  agents: [],
  graph: { nodes: [], edges: [] },
  streaming: null,
  status: "draft",
  currentTurn: 0,

  setTurns: (turns) => set({ turns }),
  setAgents: (agents) => set({ agents }),
  setGraph: (graph) => set({ graph }),
  setStatus: (status) => set({ status }),

  handleWsEvent: (event) => {
    switch (event.event) {
      case "turn.started":
        set({
          streaming: {
            agentId: event.data.agent_id,
            agentName: event.data.agent_name,
            role: event.data.role,
            content: "",
          },
          currentTurn: event.data.turn_number,
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
          id: crypto.randomUUID(),
          simulation_id: "",
          agent_id: event.data.agent_id,
          turn_number: event.data.turn_number,
          content: event.data.content,
          content_edited: null,
          citations: event.data.citations,
          spawned_agents: event.data.spawned_agents,
          is_human_override: false,
          token_count: 0,
          latency_ms: 0,
          created_at: new Date().toISOString(),
        };
        set((state) => ({
          turns: [...state.turns, completedTurn],
          streaming: null,
        }));
        break;
      }

      case "agent.spawned": {
        const { data } = event;
        set((state) => ({
          graph: {
            nodes: [
              ...state.graph.nodes,
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
              ...state.graph.edges,
              { source: data.parent_id, target: data.agent_id, reason: data.reason },
            ],
          },
        }));
        break;
      }

      case "simulation.completed":
        set({ status: "completed", streaming: null });
        break;

      case "simulation.paused":
        set({ status: "paused", streaming: null });
        break;
    }
  },
}));
