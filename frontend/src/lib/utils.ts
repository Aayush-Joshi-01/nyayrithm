import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import type { AgentRole } from "@/types/api";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const ROLE_COLORS: Record<AgentRole, string> = {
  judge: "text-amber-400 bg-amber-400/10 border-amber-400/30",
  prosecutor: "text-red-400 bg-red-400/10 border-red-400/30",
  defense: "text-blue-400 bg-blue-400/10 border-blue-400/30",
  plaintiff: "text-violet-400 bg-violet-400/10 border-violet-400/30",
  accused: "text-pink-400 bg-pink-400/10 border-pink-400/30",
  witness: "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
  investigator: "text-orange-400 bg-orange-400/10 border-orange-400/30",
  expert_witness: "text-cyan-400 bg-cyan-400/10 border-cyan-400/30",
  custom: "text-slate-400 bg-slate-400/10 border-slate-400/30",
};

export const ROLE_HEX: Record<AgentRole, string> = {
  judge: "#f59e0b",
  prosecutor: "#ef4444",
  defense: "#3b82f6",
  plaintiff: "#8b5cf6",
  accused: "#ec4899",
  witness: "#10b981",
  investigator: "#f97316",
  expert_witness: "#06b6d4",
  custom: "#94a3b8",
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
