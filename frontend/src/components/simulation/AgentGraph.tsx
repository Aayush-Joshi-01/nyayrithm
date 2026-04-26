"use client";

import { useCallback } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
} from "reactflow";
import "reactflow/dist/style.css";
import { useSimulationStore } from "@/store/simulationStore";
import { ROLE_HEX, formatRole } from "@/lib/utils";
import type { AgentRole } from "@/types/api";
import { useEffect } from "react";

function buildLayout(
  nodes: Array<{ id: string; role: string; name: string; is_predefined: boolean; parent_id: string | null }>
): { x: number; y: number }[] {
  // Simple vertical layout by level
  const levels: Record<string, number> = {};
  const queue = nodes.filter((n) => !n.parent_id);
  let level = 0;
  const visited = new Set<string>();

  while (queue.length) {
    const next: typeof nodes = [];
    for (const n of queue) {
      if (!visited.has(n.id)) {
        visited.add(n.id);
        levels[n.id] = level;
        nodes.filter((c) => c.parent_id === n.id).forEach((c) => next.push(c));
      }
    }
    queue.splice(0, queue.length, ...next);
    level++;
  }

  const countPerLevel: Record<number, number> = {};
  const positions: { x: number; y: number }[] = [];

  for (const n of nodes) {
    const lv = levels[n.id] ?? 0;
    const idx = countPerLevel[lv] ?? 0;
    countPerLevel[lv] = idx + 1;
    positions.push({ x: idx * 180, y: lv * 120 });
  }

  return positions;
}

export function AgentGraph() {
  const { graph } = useSimulationStore();
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    const positions = buildLayout(graph.nodes);

    const nodes: Node[] = graph.nodes.map((n, i) => ({
      id: n.id,
      position: positions[i] ?? { x: 0, y: 0 },
      data: { label: n.name, role: n.role, is_predefined: n.is_predefined },
      style: {
        background: `${ROLE_HEX[n.role as AgentRole] ?? "#94a3b8"}15`,
        border: `1px solid ${ROLE_HEX[n.role as AgentRole] ?? "#94a3b8"}50`,
        borderRadius: 8,
        color: ROLE_HEX[n.role as AgentRole] ?? "#94a3b8",
        fontSize: 11,
        fontWeight: 600,
        padding: "6px 10px",
        minWidth: 130,
        textAlign: "center",
      },
    }));

    const edges: Edge[] = graph.edges.map((e, i) => ({
      id: `e-${i}`,
      source: e.source,
      target: e.target,
      label: e.reason ? e.reason.slice(0, 30) : undefined,
      labelStyle: { fontSize: 9, fill: "#64748b" },
      style: { stroke: "#334155", strokeDasharray: "4 2" },
      animated: true,
    }));

    setRfNodes(nodes);
    setRfEdges(edges);
  }, [graph, setRfNodes, setRfEdges]);

  return (
    <div className="h-full bg-card/30" style={{ height: "100%" }}>
      <div className="px-3 py-2 border-b border-border">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Agent Graph
        </p>
      </div>
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        nodesDraggable
        nodesConnectable={false}
        style={{ height: "calc(100% - 36px)", background: "transparent" }}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#1e293b" />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
