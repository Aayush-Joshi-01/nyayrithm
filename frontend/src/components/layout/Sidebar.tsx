"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import {
  FolderOpen, Settings, LayoutDashboard, BookOpen, LogOut, User, ChevronDown,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const navSections = [
  {
    label: "Chambers",
    items: [
      { href: "/dashboard", label: "Cases", icon: LayoutDashboard, exact: true },
      { href: "/dashboard/evidence", label: "Evidence", icon: FolderOpen, exact: false },
    ],
  },
  {
    label: "System",
    items: [
      { href: "/dashboard/settings", label: "Settings", icon: Settings, exact: false },
      { href: "/docs", label: "Documentation", icon: BookOpen, exact: false },
    ],
  },
]

function NavItem({ href, label, icon: Icon, active }: {
  href: string; label: string; icon: React.ElementType; active: boolean
}) {
  return (
    <Link
      href={href}
      className={cn(
        "relative flex items-center gap-3 px-3 py-2 text-[0.86rem] transition-colors",
        active
          ? "text-foreground"
          : "text-foreground/45 hover:text-foreground/80"
      )}
    >
      {active && (
        <span className="absolute inset-y-1 left-0 w-[2px] rounded-full bg-brass" />
      )}
      <Icon className="h-4 w-4 flex-shrink-0" strokeWidth={1.75} />
      <span className="truncate">{label}</span>
    </Link>
  )
}

export function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()

  const handleLogout = async () => {
    await fetch("/api/auth/logout", { method: "POST" })
    router.push("/login")
  }

  return (
    <aside className="flex h-screen w-60 flex-shrink-0 flex-col border-r border-hairline bg-ink-raised/70">
      <div className="flex h-16 items-center gap-2.5 border-b border-hairline px-5">
        <span className="font-serif text-[0.9rem] font-semibold tracking-[0.16em] text-bone">
          NYAYRITHM
        </span>
      </div>

      <ScrollArea className="flex-1 px-2 py-5">
        {navSections.map((section) => (
          <div key={section.label} className="mb-7">
            <p className="mb-2 px-3 font-mono text-[0.62rem] uppercase tracking-[0.2em] text-foreground/45">
              {section.label}
            </p>
            <div className="space-y-0.5">
              {section.items.map((item) => (
                <NavItem
                  key={item.href}
                  {...item}
                  active={item.exact ? pathname === item.href : pathname.startsWith(item.href)}
                />
              ))}
            </div>
          </div>
        ))}
      </ScrollArea>

      <div className="border-t border-hairline p-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="group flex w-full items-center gap-3 rounded-sm px-2 py-2 transition-colors hover:bg-accent/50">
              <Avatar className="h-7 w-7 rounded-sm">
                <AvatarFallback className="rounded-sm bg-brass/15 text-[0.7rem] text-brass-text">AJ</AvatarFallback>
              </Avatar>
              <div className="min-w-0 flex-1 text-left">
                <p className="truncate text-[0.8rem] font-medium text-foreground/75">Aayush Joshi</p>
                <p className="truncate text-[0.7rem] text-foreground/35">aayushjoshi.dev@gmail.com</p>
              </div>
              <ChevronDown className="h-3.5 w-3.5 flex-shrink-0 text-foreground/25 transition-colors group-hover:text-foreground/45" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent side="top" align="start" className="w-52">
            <DropdownMenuLabel className="font-normal">
              <p className="text-sm font-medium">Aayush Joshi</p>
              <p className="text-xs text-muted-foreground">aayushjoshi.dev@gmail.com</p>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem><User className="mr-2 h-4 w-4" strokeWidth={1.75} />Profile</DropdownMenuItem>
            <DropdownMenuItem><Settings className="mr-2 h-4 w-4" strokeWidth={1.75} />Settings</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-oxblood-bright focus:text-oxblood-bright" onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" strokeWidth={1.75} />Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </aside>
  )
}
