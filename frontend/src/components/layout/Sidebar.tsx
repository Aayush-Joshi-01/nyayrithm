"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Scale, FolderOpen, Settings, LayoutDashboard,
  BookOpen, LogOut, User, ChevronDown,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { getKeycloakLogoutUrl } from "@/lib/keycloak"

const navSections = [
  {
    label: "Workspace",
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
    <Tooltip>
      <TooltipTrigger asChild>
        <Link
          href={href}
          className={cn(
            "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all",
            active
              ? "bg-amber-500/15 text-amber-400 border border-amber-500/20"
              : "text-white/50 hover:text-white/80 hover:bg-white/5"
          )}
        >
          <Icon className="w-4 h-4 flex-shrink-0" />
          <span className="truncate">{label}</span>
        </Link>
      </TooltipTrigger>
      <TooltipContent side="right">{label}</TooltipContent>
    </Tooltip>
  )
}

export function Sidebar() {
  const pathname = usePathname()

  const handleLogout = () => {
    const redirectUri = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000"
    window.location.href = getKeycloakLogoutUrl(redirectUri)
  }

  return (
    <aside className="w-60 flex flex-col h-screen border-r border-white/8 bg-card/80 backdrop-blur-sm flex-shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-white/8">
        <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center flex-shrink-0">
          <Scale className="w-4 h-4 text-amber-400" />
        </div>
        <div>
          <p className="text-sm font-bold text-white tracking-tight">Nyayrithm</p>
          <p className="text-xs text-white/30">Legal Reasoning</p>
        </div>
      </div>

      {/* Nav */}
      <ScrollArea className="flex-1 px-2 py-4">
        {navSections.map((section) => (
          <div key={section.label} className="mb-6">
            <p className="text-xs font-semibold text-white/20 uppercase tracking-wider px-3 mb-2">
              {section.label}
            </p>
            <div className="space-y-1">
              {section.items.map((item) => (
                <NavItem
                  key={item.href}
                  href={item.href}
                  label={item.label}
                  icon={item.icon}
                  active={item.exact ? pathname === item.href : pathname.startsWith(item.href)}
                />
              ))}
            </div>
          </div>
        ))}
      </ScrollArea>

      {/* User */}
      <div className="p-3 border-t border-white/8">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="w-full flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-white/5 transition-colors group">
              <Avatar className="w-7 h-7">
                <AvatarFallback className="text-xs">AJ</AvatarFallback>
              </Avatar>
              <div className="flex-1 text-left min-w-0">
                <p className="text-xs font-medium text-white/70 truncate">Aayush Joshi</p>
                <p className="text-xs text-white/30 truncate">aayushjoshi.dev@gmail.com</p>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-white/20 group-hover:text-white/40 transition-colors flex-shrink-0" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent side="top" align="start" className="w-52">
            <DropdownMenuLabel className="font-normal">
              <p className="text-sm font-medium">Aayush Joshi</p>
              <p className="text-xs text-muted-foreground">aayushjoshi.dev@gmail.com</p>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <User className="w-4 h-4 mr-2" />
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-red-400 focus:text-red-400" onClick={handleLogout}>
              <LogOut className="w-4 h-4 mr-2" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </aside>
  )
}
