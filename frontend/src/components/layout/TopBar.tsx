"use client"

import { usePathname } from "next/navigation"
import Link from "next/link"
import { ChevronRight, Circle } from "lucide-react"
import { cn } from "@/lib/utils"

function useBreadcrumbs() {
  const pathname = usePathname()
  const segments = pathname.split("/").filter(Boolean)

  const crumbs: { label: string; href: string }[] = []
  let path = ""

  for (const seg of segments) {
    path += `/${seg}`
    // Make it readable — UUIDs show as "..." and known segments are labeled
    const isUuid = /^[0-9a-f-]{36}$/i.test(seg)
    let label = seg
    if (seg === "dashboard") label = "Cases"
    else if (seg === "evidence") label = "Evidence"
    else if (seg === "simulation") label = "Simulation"
    else if (isUuid) label = seg.slice(0, 8) + "…"
    else label = seg.charAt(0).toUpperCase() + seg.slice(1)
    crumbs.push({ label, href: path })
  }

  return crumbs
}

export function TopBar() {
  const crumbs = useBreadcrumbs()

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-white/8 bg-card/50 backdrop-blur-sm flex-shrink-0">
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-1 text-sm">
        {crumbs.map((crumb, i) => (
          <span key={crumb.href} className="flex items-center gap-1">
            {i > 0 && <ChevronRight className="w-3.5 h-3.5 text-white/20" />}
            {i === crumbs.length - 1 ? (
              <span className="text-white/80 font-medium">{crumb.label}</span>
            ) : (
              <Link href={crumb.href} className="text-white/40 hover:text-white/60 transition-colors">
                {crumb.label}
              </Link>
            )}
          </span>
        ))}
      </nav>

      {/* Right side */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-xs text-emerald-400">
          <Circle className={cn("w-2 h-2 fill-current animate-pulse-slow")} />
          <span className="hidden sm:block text-white/30">API Connected</span>
        </div>
      </div>
    </header>
  )
}
