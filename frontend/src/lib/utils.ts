import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import type { AgentRole } from "@/types/api";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/* Each legal role carries one reserved hue and one sigil letter, applied
   identically in the graph, the transcript, and setup. Hues are theme-aware
   CSS variables (see globals.css); ROLE_HEX keeps literals for the ReactFlow
   canvas, which stays a dark blueprint in both themes. */
export const ROLE_HEX: Record<AgentRole, string> = {
  judge: "#D69B58",
  prosecutor: "#C0453C",
  defense: "#5B7FA6",
  plaintiff: "#8E7BB0",
  accused: "#B26E8A",
  witness: "#6E9E86",
  investigator: "#C77F4A",
  expert_witness: "#5E93A0",
  custom: "#8A8578",
};

const ROLE_VAR: Record<AgentRole, string> = {
  judge: "--role-judge",
  prosecutor: "--role-prosecutor",
  defense: "--role-defense",
  plaintiff: "--role-plaintiff",
  accused: "--role-accused",
  witness: "--role-witness",
  investigator: "--role-investigator",
  expert_witness: "--role-expert-witness",
  custom: "--role-custom",
};

export function roleVar(role: AgentRole): string {
  return `rgb(var(${ROLE_VAR[role] ?? "--role-custom"}))`;
}

/** Filled role chip: theme-aware hue at low-alpha fill + hairline border. */
export function roleStyle(role: AgentRole): React.CSSProperties {
  const v = roleVar(role);
  return {
    color: v,
    backgroundColor: `color-mix(in srgb, ${v} 13%, transparent)`,
    borderColor: `color-mix(in srgb, ${v} 34%, transparent)`,
  };
}

export const ROLE_SIGIL: Record<AgentRole, string> = {
  judge: "J",
  prosecutor: "P",
  defense: "D",
  plaintiff: "Π",
  accused: "A",
  witness: "W",
  investigator: "I",
  expert_witness: "E",
  custom: "·",
};

export function formatRole(role: AgentRole): string {
  return role.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}
