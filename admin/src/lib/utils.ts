import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function fmtInt(n: number | null | undefined): string {
  return n == null ? "–" : new Intl.NumberFormat("en-US").format(Math.round(n));
}

/** 1_234_567 -> "1.23M" */
export function fmtCompact(n: number | null | undefined): string {
  if (n == null) return "–";
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 }).format(n);
}

export function fmtUsd(n: number | null | undefined): string {
  if (n == null) return "–";
  const digits = Math.abs(n) >= 100 ? 0 : Math.abs(n) >= 1 ? 2 : 4;
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: digits, minimumFractionDigits: Math.min(2, digits) }).format(n);
}

export function fmtMs(n: number | null | undefined): string {
  if (n == null) return "–";
  return n >= 1000 ? `${(n / 1000).toFixed(1)} s` : `${Math.round(n)} ms`;
}

export function fmtPct(n: number | null | undefined, digits = 1): string {
  return n == null ? "–" : `${(n * 100).toFixed(digits)}%`;
}

export function fmtDate(value: string | null | undefined): string {
  if (!value) return "–";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? "–" : d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

export function fmtDateTime(value: string | null | undefined): string {
  if (!value) return "–";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? "–" : d.toLocaleString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}
