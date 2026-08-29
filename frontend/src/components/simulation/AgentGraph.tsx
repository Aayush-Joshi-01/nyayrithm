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
import { ROLE_HEX, ROLE_SIGIL, formatRole } from "@/lib/utils"
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

  // count per level so each row can be centred
  const totalPerLevel: Record<number, number> = {}
  for (const n of nodes) {
    const lv = levels[n.id] ?? 0
    totalPerLevel[lv] = (totalPerLevel[lv] ?? 0) + 1
  }

  const COL = 190
  const ROW = 130
  const MAX_PER_ROW = 6 // wrap wide levels into a block instead of one long line
  const seen: Record<number, number> = {}
  const positions: { x: number; y: number }[] = []

  // running vertical offset per level (levels with wrapped rows push later levels down)
  const levelY: Record<number, number> = {}
  const sortedLevels = [...new Set(Object.values(levels))].sort((a, b) => a - b)
  let yCursor = 0
  for (const lv of sortedLevels) {
    levelY[lv] = yCursor
    const rowsInLevel = Math.ceil((totalPerLevel[lv] ?? 1) / MAX_PER_ROW)
    yCursor += Math.max(1, rowsInLevel) * ROW + ROW * 0.4
  }

  for (const n of nodes) {
    const lv = levels[n.id] ?? 0
    const idx = seen[lv] ?? 0
    seen[lv] = idx + 1

    const perRow = Math.min(totalPerLevel[lv] ?? 1, MAX_PER_ROW)
    const col = idx % perRow
    const subRow = Math.floor(idx / perRow)
    const rowWidth = (perRow - 1) * COL
    positions.push({
      x: col * COL - rowWidth / 2,
      y: (levelY[lv] ?? lv * ROW) + subRow * ROW,
    })
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

  const dormant = isDismissed || isSuspended

  return (
    <div
      className="relative min-w-[150px] rounded-sm px-3 py-2.5 text-center"
      style={{
        background: dormant ? "#10141C" : `${data.color}12`,
        border: `1px ${isSpawned ? "dashed" : "solid"} ${data.color}${dormant ? "33" : "66"}`,
        opacity: dormant ? 0.4 : 1,
        boxShadow: data.status === "active" ? `-2px 0 0 0 #FF7A3D` : "none",
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: data.color, border: "none", width: 5, height: 5 }} />

      <div className="mb-1 flex items-center justify-center gap-1.5">
        <span
          className="grid h-4 w-4 place-items-center rounded-sm font-mono text-[0.56rem] font-semibold"
          style={{ color: data.color, backgroundColor: `${data.color}1e`, border: `1px solid ${data.color}44` }}
        >
          {ROLE_SIGIL[data.role]}
        </span>
        <span className="font-mono text-[0.58rem] uppercase tracking-wide" style={{ color: data.color }}>
          {formatRole(data.role)}
        </span>
      </div>

      {/* the graph canvas is always a dark blueprint, so node text is fixed light */}
      <div
        className="mx-auto max-w-[150px] truncate font-serif text-[0.8rem] font-medium leading-tight"
        style={{ color: "rgba(236,227,210,0.9)" }}
      >
        {data.label}
      </div>

      {isSpawned && (
        <div
          className="mt-1 font-mono text-[0.56rem] uppercase tracking-wide"
          style={{ color: "rgba(236,227,210,0.32)" }}
        >
          spawned
        </div>
      )}

      <Handle type="source" position={Position.Bottom} style={{ background: data.color, border: "none", width: 5, height: 5 }} />
    </div>
  )
}

const nodeTypes = { agent: AgentNode }

export function AgentGraph() {
  const { graph } = useSimulationStore()
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState([])
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState([])
  const instanceRef = useRef<ReactFlowInstance | null>(null)
  const wrapRef = useRef<HTMLDivElement | null>(null)

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
        color: ROLE_HEX[n.role] ?? "#8A8578",
      },
    }))

    // Descent is carried by the line itself; reasons repeat across a fan-out and
    // only add noise, so no edge labels.
    const edges: Edge[] = graph.edges.map((e, i) => ({
      id: `e-${i}`,
      source: e.source,
      target: e.target,
      style: { stroke: "#3A4250", strokeDasharray: "4 3", strokeWidth: 1 },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#5A6270", width: 11, height: 11 },
    }))

    setRfNodes(nodes)
    setRfEdges(edges)
    // Re-fit once the new node set has painted (double rAF is enough for layout).
    requestAnimationFrame(() =>
      requestAnimationFrame(() => instanceRef.current?.fitView({ padding: 0.24, duration: 300 }))
    )
  }, [graph, setRfNodes, setRfEdges])

  const onInit = useCallback((instance: ReactFlowInstance) => {
    instanceRef.current = instance
    instance.fitView({ padding: 0.24 })
  }, [])

  // keep the graph fitted when the pane resizes (tab switch, window, sidebar)
  useEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const ro = new ResizeObserver(() => {
      instanceRef.current?.fitView({ padding: 0.24, duration: 200 })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  return (
    <div className="flex h-full min-h-0 w-full flex-col">
      <div className="flex-shrink-0 border-b border-hairline px-4 py-2.5">
        <p className="font-mono text-[0.66rem] uppercase tracking-[0.2em] text-foreground/35">
          The spawn graph
          {graph.nodes.length > 0 && (
            <span className="ml-2 tabular normal-case tracking-normal text-foreground/40">
              {graph.nodes.length} agents, {graph.edges.length} lines of descent
            </span>
          )}
        </p>
      </div>
      <div ref={wrapRef} className="relative min-h-0 flex-1">
        <ReactFlow
          className="absolute inset-0"
          nodes={rfNodes}
          edges={rfEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.24 }}
          minZoom={0.15}
          nodesDraggable
          nodesConnectable={false}
          proOptions={{ hideAttribution: true }}
          onInit={onInit}
          style={{ background: "transparent" }}
        >
          <Background variant={BackgroundVariant.Dots} gap={22} size={1} color="#1B222E" />
          <Controls showInteractive={false} />
          <MiniMap
            nodeColor={(node) => (node.data as AgentNodeData).color + "88"}
            maskColor="rgba(11,14,20,0.86)"
            style={{
              background: "rgba(16,20,28,0.92)",
              border: "1px solid rgba(236,227,210,0.16)",
              borderRadius: 3,
            }}
          />
        </ReactFlow>
      </div>
    </div>
  )
}
