import { FolderOpen } from "lucide-react"

export default function EvidencePage() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
          <FolderOpen className="w-5 h-5 text-white/50" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Evidence</h1>
          <p className="text-white/40 text-sm mt-0.5">All evidence across your cases</p>
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/3 p-8 text-center">
        <p className="text-white/30 text-sm">
          Select a case from the Cases page to manage its evidence.
        </p>
      </div>
    </div>
  )
}
