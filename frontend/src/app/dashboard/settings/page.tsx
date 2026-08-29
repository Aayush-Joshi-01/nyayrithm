import { PageScroll } from "@/components/layout/PageScroll"

export default function SettingsPage() {
  return (
    <PageScroll>
    <div className="mx-auto max-w-2xl">
      <h1 className="font-serif text-2xl font-medium tracking-tight text-bone">Settings</h1>
      <p className="mt-1 text-[0.88rem] text-foreground/45">Workspace preferences.</p>

      <div className="mt-8 rounded-lg border border-border bg-ink-raised/60 px-8 py-16 text-center">
        <p className="font-serif text-[1.05rem] text-foreground/55">Nothing to configure yet.</p>
        <p className="mx-auto mt-2 max-w-xs text-[0.85rem] leading-relaxed text-foreground/40">
          Provider keys, database, and storage are set in <code className="font-mono text-brass-text">.env</code>.
          Per-workspace settings will land here.
        </p>
      </div>
    </div>
    </PageScroll>
  )
}
