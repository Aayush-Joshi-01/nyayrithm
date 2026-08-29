"use client"

import { usePathname } from "next/navigation"
import Link from "next/link"
import { ChevronRight } from "lucide-react"
import { ThemeToggle } from "@/components/theme/ThemeToggle"

function useBreadcrumbs() {
  const pathname = usePathname()
  const segments = pathname.split("/").filter(Boolean)

  const crumbs: { label: string; href: string }[] = []
  let path = ""
  for (const seg of segments) {
    path += `/${seg}`
    const isUuid = /^[0-9a-f-]{36}$/i.test(seg)
    let label = seg
    if (seg === "dashboard") label = "Cases"
    else if (seg === "evidence") label = "Evidence"
    else if (seg === "simulation") label = "Proceeding"
    else if (isUuid) label = seg.slice(0, 8)
    else label = seg.charAt(0).toUpperCase() + seg.slice(1)
    crumbs.push({ label, href: path })
  }
  return crumbs
}

export function TopBar() {
  const crumbs = useBreadcrumbs()

  return (
    <header className="flex h-16 flex-shrink-0 items-center justify-between border-b border-hairline bg-ink-raised/40 px-6">
      <nav className="flex items-center gap-1.5 font-mono text-[0.78rem]">
        {crumbs.map((crumb, i) => (
          <span key={crumb.href} className="flex items-center gap-1.5">
            {i > 0 && <ChevronRight className="h-3 w-3 text-foreground/20" />}
            {i === crumbs.length - 1 ? (
              <span className="text-foreground/75">{crumb.label}</span>
            ) : (
              <Link href={crumb.href} className="text-foreground/35 transition-colors hover:text-foreground/60">
                {crumb.label}
              </Link>
            )}
          </span>
        ))}
      </nav>

      <div className="flex items-center gap-4">
        <span className="hidden items-center gap-2 font-mono text-[0.7rem] uppercase tracking-wide text-foreground/30 sm:flex">
          <span className="h-1.5 w-1.5 rounded-full bg-role-witness" />
          API connected
        </span>
        <ThemeToggle />
      </div>
    </header>
  )
}
