"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Scale, FolderOpen, Settings, LayoutDashboard } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Cases", icon: LayoutDashboard },
  { href: "/dashboard", label: "Evidence", icon: FolderOpen },
  { href: "/dashboard", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-16 flex flex-col items-center py-6 gap-6 border-r border-border bg-card">
      <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/30">
        <Scale className="w-5 h-5 text-amber-400" />
      </div>
      <nav className="flex flex-col gap-2 flex-1">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={label}
            href={href}
            title={label}
            className={cn(
              "flex items-center justify-center w-10 h-10 rounded-lg transition-colors",
              pathname === href
                ? "bg-accent text-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
            )}
          >
            <Icon className="w-5 h-5" />
          </Link>
        ))}
      </nav>
    </aside>
  );
}
