"use client"

import { useCallback, useEffect, useRef } from "react"
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  Handle,
  Position,
  NodeProps,
  MarkerType,
  ReactFlowInstance,
} from "reactflow"
import "reactflow/dist/style.css"
import { useSimulationStore } from "@/store/simulationStore"
import { ROLE_HEX, formatRole } from "@/lib/utils"
import type { AgentRole } from "@/types/api"

function buildLayout(
  nodes: Array<{ id: string; role: string; name: string; is_predefined: boolean; parent_id: string | null }>
): { x: number; y: number }[] {
  const levels: Record<string, number> = {}
  const queue = nodes.filter((n) => !n.parent_id)
  let level = 0
  const visited = new Set<string>()

  while (queue.length) {
    const next: typeof nodes = []
    for (const n of queue) {
      if (!visited.has(n.id)) {
        visited.add(n.id)
        levels[n.id] = level
        nodes.filter((c) => c.parent_id === n.id).forEach((c) => next.push(c))
      }
    }
    queue.splice(0, queue.length, ...next)
    level++
  }

  // count per level first so each row can be centred
  const totalPerLevel: Record<number, number> = {}
  for (const n of nodes) {
    const lv = levels[n.id] ?? 0
    totalPerLevel[lv] = (totalPerLevel[lv] ?? 0) + 1
  }

  const COL = 230
  const ROW = 160
  const seen: Record<number, number> = {}
  const positions: { x: number; y: number }[] = []

  for (const n of nodes) {
    const lv = levels[n.id] ?? 0
    const idx = seen[lv] ?? 0
    seen[lv] = idx + 1
    const rowWidth = (totalPerLevel[lv] - 1) * COL
    positions.push({ x: idx * COL - rowWidth / 2, y: lv * ROW })
  }

  return positions
}

interface AgentNodeData {
  label: string
  role: AgentRole
  status: string
  is_predefined: boolean
  color: string
}

function AgentNode({ data }: NodeProps<AgentNodeData>) {
  const isSpawned = !data.is_predefined
  const isDismissed = data.status === "dismissed"
  const isSuspended = data.status === "suspended"

  return (
    <div
      className="relative px-3 py-2.5 rounded-lg text-center min-w-[140px]"
      style={{
        background: `${data.color}12`,
        border: `1.5px ${isSpawned ? "dashed" : "solid"} ${data.color}${isDismissed ? "40" : "80"}`,
        opacity: isDismissed || isSuspended ? 0.5 : 1,
        boxShadow: `0 0 16px ${data.color}15`,
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: data.color, border: "none", width: 6, height: 6 }} />

      <div
        className="text-[10px] font-semibold uppercase tracking-wider mb-1"
        style={{ color: data.color }}
      >
        {formatRole(data.role)}
      </div>

      <div className="text-xs font-medium text-white/80 leading-tight truncate max-w-[130px] mx-auto">
        {data.label}
      </div>

      {isSpawned && (
        <div className="mt-1.5 inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-white/5 text-[9px] text-white/30">
          <span className="w-1 h-1 rounded-full bg-white/30" />
          AI Spawned
        </div>
      )}

      {data.status === "active" && (
        <span
          className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full border border-background"
          style={{ background: data.color }}
        />
      )}

      <Handle type="source" position={Position.Bottom} style={{ background: data.color, border: "none", width: 6, height: 6 }} />
    </div>
  )
}

const nodeTypes = { agent: AgentNode }

export function AgentGraph() {
  const { graph } = useSimulationStore()
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState([])
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState([])
  const instanceRef = useRef<ReactFlowInstance | null>(null)

  useEffect(() => {
    const positions = buildLayout(graph.nodes)

    const nodes: Node<AgentNodeData>[] = graph.nodes.map((n, i) => ({
      id: n.id,
      type: "agent",
      position: positions[i] ?? { x: 0, y: 0 },
      data: {
        label: n.name,
        role: n.role,
        status: n.status,
        is_predefined: n.is_predefined,
        color: ROLE_HEX[n.role] ?? "#94a3b8",
      },
    }))

    const edges: Edge[] = graph.edges.map((e, i) => ({
      id: `e-${i}`,
      source: e.source,
      target: e.target,
      label: e.reason ? e.reason.slice(0, 28) + (e.reason.length > 28 ? "…" : "") : undefined,
      labelStyle: { fontSize: 9, fill: "#64748b", fontFamily: "inherit" },
      labelBgStyle: { fill: "#0f172a", fillOpacity: 0.8 },
      labelBgPadding: [4, 2],
      style: { stroke: "#334155", strokeDasharray: "5 3", strokeWidth: 1.5 },
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed, color: "#475569", width: 12, height: 12 },
    }))

    setRfNodes(nodes)
    setRfEdges(edges)
    // Re-fit after the DOM paints the new node set.
    requestAnimationFrame(() => {
      instanceRef.current?.fitView({ padding: 0.25, duration: 300 })
    })
  }, [graph, setRfNodes, setRfEdges])

  const onInit = useCallback((instance: ReactFlowInstance) => {
    instanceRef.current = instance
    setTimeout(() => instance.fitView({ padding: 0.25 }), 50)
  }, [])

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-2.5 border-b border-white/8 flex-shrink-0">
        <p className="text-xs font-semibold text-white/40 uppercase tracking-wider">
          Agent Graph
          {graph.nodes.length > 0 && (
            <span className="ml-2 text-white/20 normal-case font-normal">
              {graph.nodes.length} agents · {graph.edges.length} connections
            </span>
          )}
        </p>
      </div>
      <div className="flex-1 min-h-0">
        <ReactFlow
          nodes={rfNodes}
          edges={rfEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.3 }}
          nodesDraggable
          nodesConnectable={false}
          onInit={onInit}
          style={{ background: "transparent" }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#1e293b" />
          <Controls
            showInteractive={false}
            style={{
              background: "rgba(15,23,42,0.8)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 8,
            }}
          />
          <MiniMap
            nodeColor={(node) => (node.data as AgentNodeData).color + "80"}
            maskColor="rgba(10,15,26,0.85)"
            style={{
              background: "rgba(10,15,26,0.9)",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: 8,
            }}
          />
        </ReactFlow>
      </div>
    </div>
  )
}
