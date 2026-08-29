"use client"

import { useCallback, useEffect, useState } from "react"
import { Sun, Moon } from "lucide-react"
import { THEME_STORAGE_KEY, THEME_TITLES } from "./theme-init"

type Resolved = "light" | "dark"

function resolve(): Resolved {
  if (typeof document === "undefined") return "dark"
  const attr = document.documentElement.getAttribute("data-theme")
  if (attr === "light" || attr === "dark") return attr
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
}

/* Keeps the tab title in step with the resolved theme. The server-rendered
   <title> stays the stable SEO string; this only rewrites document.title on the
   client once the theme is known, and follows the system when unset. */
function syncTitle(theme: Resolved) {
  const base = "Nyayrithm"
  document.title = `${base}: ${THEME_TITLES[theme]}`
}

export function ThemeToggle({ className = "" }: { className?: string }) {
  const [theme, setTheme] = useState<Resolved>("dark")
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const t = resolve()
    setTheme(t)
    syncTitle(t)

    const mq = window.matchMedia("(prefers-color-scheme: dark)")
    const onSystem = () => {
      if (!localStorage.getItem(THEME_STORAGE_KEY)) {
        const t2 = mq.matches ? "dark" : "light"
        setTheme(t2)
        syncTitle(t2)
      }
    }
    mq.addEventListener("change", onSystem)
    return () => mq.removeEventListener("change", onSystem)
  }, [])

  const toggle = useCallback(() => {
    const next: Resolved = resolve() === "dark" ? "light" : "dark"
    document.documentElement.setAttribute("data-theme", next)
    document.documentElement.style.colorScheme = next
    try {
      localStorage.setItem(THEME_STORAGE_KEY, next)
    } catch {}
    setTheme(next)
    syncTitle(next)
  }, [])

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={
        mounted
          ? `Switch to ${theme === "dark" ? "the court in session (light)" : "the court after hours (dark)"}`
          : "Switch theme"
      }
      className={`relative grid h-8 w-8 place-items-center overflow-hidden rounded-sm text-foreground/55 transition-colors hover:bg-accent/60 hover:text-foreground ${className}`}
    >
      <Sun
        className={`col-start-1 row-start-1 h-4 w-4 transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] ${
          mounted && theme === "dark" ? "rotate-0 scale-100 opacity-100" : "-rotate-90 scale-50 opacity-0"
        }`}
        strokeWidth={1.75}
        style={{ gridArea: "1 / 1" }}
      />
      <Moon
        className={`col-start-1 row-start-1 h-4 w-4 transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] ${
          mounted && theme === "dark" ? "rotate-90 scale-50 opacity-0" : "rotate-0 scale-100 opacity-100"
        }`}
        strokeWidth={1.75}
        style={{ gridArea: "1 / 1" }}
      />
    </button>
  )
}
