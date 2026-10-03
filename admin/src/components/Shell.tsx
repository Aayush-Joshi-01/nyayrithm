"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { Activity, Building2, CreditCard, Gauge, HeartPulse, LayoutDashboard, LogOut, Users } from "lucide-react"
import { ThemeToggle } from "@/components/theme/ThemeToggle"
import { DEV_AUTH_MODE, IS_DEV } from "@/lib/dev"
import { cn } from "@/lib/utils"

const NAV = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/firms", label: "Firms", icon: Building2 },
  { href: "/plans", label: "Plans", icon: CreditCard },
  { href: "/users", label: "Users", icon: Users },
  { href: "/llmops", label: "LLMOps", icon: Gauge },
  { href: "/system", label: "System", icon: HeartPulse },
  { href: "/activity", label: "Activity", icon: Activity },
]

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()

  async function signOut() {
    await fetch("/api/auth/logout", { method: "POST" })
    router.push("/login")
    router.refresh()
  }

  const isActive = (href: string) => (href === "/" ? pathname === "/" : pathname.startsWith(href))

  return (
    <div className="flex min-h-[100dvh] bg-background">
      <aside className="sticky top-0 hidden h-[100dvh] w-56 flex-shrink-0 flex-col border-r border-hairline bg-ink-raised/60 md:flex">
        <div className="px-5 py-5">
          <p className="font-serif text-[0.95rem] font-semibold tracking-[0.16em] text-bone">NYAYRITHM</p>
          <p className="mt-0.5 font-mono text-[0.62rem] uppercase tracking-widest text-foreground/40">Operations</p>
        </div>
        <nav className="flex-1 space-y-0.5 px-2" aria-label="Main">
          {NAV.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              aria-current={isActive(href) ? "page" : undefined}
              className={cn(
                "flex items-center gap-2.5 rounded-sm px-3 py-2 text-[0.85rem] transition-colors",
                isActive(href)
                  ? "bg-accent/70 text-foreground"
                  : "text-foreground/55 hover:bg-accent/40 hover:text-foreground",
              )}
            >
              <Icon className="h-4 w-4" strokeWidth={1.75} />
              {label}
            </Link>
          ))}
        </nav>
        <div className="border-t border-hairline p-3">
          <div className="flex items-center justify-between">
            <ThemeToggle />
            {DEV_AUTH_MODE !== "open" && (
              <button
                onClick={signOut}
                className="flex items-center gap-1.5 text-[0.78rem] text-foreground/50 hover:text-foreground"
              >
                <LogOut className="h-3.5 w-3.5" strokeWidth={1.75} /> Sign out
              </button>
            )}
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        {IS_DEV && (
          <div
            role="status"
            className="border-b border-brass/30 bg-brass/10 px-4 py-1.5 text-center font-mono text-[0.68rem] uppercase tracking-widest text-brass-text"
          >
            Development mode · {DEV_AUTH_MODE === "open" ? "open access, no login" : "static dev credentials"}
          </div>
        )}
        <nav className="flex gap-1 overflow-x-auto border-b border-hairline px-2 py-2 md:hidden" aria-label="Main (mobile)">
          {NAV.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                "whitespace-nowrap rounded-sm px-3 py-1.5 text-[0.8rem]",
                isActive(href) ? "bg-accent/70 text-foreground" : "text-foreground/55",
              )}
            >
              {label}
            </Link>
          ))}
        </nav>
        <main className="mx-auto w-full max-w-[1200px] flex-1 px-4 py-8 sm:px-8">{children}</main>
      </div>
    </div>
  )
}
