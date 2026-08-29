import Link from "next/link"
import { ThemeToggle } from "@/components/theme/ThemeToggle"

/* The clerk's window: a single lit desk. */
export function AuthShell({
  title,
  intro,
  children,
  footer,
}: {
  title: string
  intro: string
  children: React.ReactNode
  footer: React.ReactNode
}) {
  return (
    <div className="relative flex min-h-[100dvh] items-center justify-center overflow-hidden bg-ink px-4 py-12">
      <div className="pointer-events-none absolute inset-0 bench-light-tight" />
      <div className="pointer-events-none absolute inset-0 court-grain" />

      <div className="pointer-events-none absolute right-4 top-4">
        <div className="pointer-events-auto">
          <ThemeToggle />
        </div>
      </div>

      <div className="relative w-full max-w-md">
        <Link
          href="/"
          className="mb-8 block text-center font-serif text-[0.95rem] font-semibold tracking-[0.18em] text-bone"
        >
          NYAYRITHM
        </Link>

        <div className="rounded-lg border border-border bg-ink-raised/80 p-8 shadow-chamber">
          <h1 className="font-serif text-[1.55rem] font-medium tracking-tight text-bone">{title}</h1>
          <p className="mt-1.5 text-[0.85rem] leading-relaxed text-foreground/45">{intro}</p>

          <div className="mt-7">{children}</div>

          <div className="mt-6 border-t border-hairline pt-5 text-center text-[0.82rem] text-foreground/40">
            {footer}
          </div>
        </div>

        <p className="mt-5 text-center font-mono text-[0.68rem] text-foreground/45">
          Sessions are issued by Keycloak. No account is needed to run Nyayrithm locally.
        </p>
      </div>
    </div>
  )
}

export function AuthField({
  label,
  error,
  children,
}: {
  label: string
  error?: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <label className="block text-[0.78rem] font-medium text-foreground/60">{label}</label>
      {children}
      {error && <p className="text-[0.72rem] text-oxblood-bright">{error}</p>}
    </div>
  )
}
