"use client"

import { use, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Loader2 } from "lucide-react"
import { apiError, firmApi } from "@/lib/api"
import { getAccessToken } from "@/lib/auth-token"
import { setActiveOrg } from "@/lib/firm"
import { DEV_OPEN } from "@/lib/dev"
import { AuthShell } from "@/components/auth/AuthShell"
import type { InvitePreview } from "@/types/api"

type State =
  | { kind: "loading" }
  | { kind: "gone" | "missing"; message: string }
  | { kind: "ready"; invite: InvitePreview; signedIn: boolean }

export default function InvitePage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params)
  const router = useRouter()
  const [state, setState] = useState<State>({ kind: "loading" })
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const invite = await firmApi.previewInvite(token)
        const signedIn = DEV_OPEN || (await getAccessToken()) !== null
        if (!cancelled) setState({ kind: "ready", invite, signedIn })
      } catch (e) {
        const { message, status } = await apiError(e)
        if (!cancelled) setState({ kind: status === 410 ? "gone" : "missing", message: status === 404 ? "This invitation link is not valid." : message })
      }
    })()
    return () => { cancelled = true }
  }, [token])

  async function accept() {
    setBusy(true)
    setError("")
    try {
      const member = await firmApi.acceptInvite(token)
      setActiveOrg(null) // let the API pick; a new firm member usually has just this one
      void member
      router.push("/dashboard")
    } catch (e) {
      setError((await apiError(e)).message)
      setBusy(false)
    }
  }

  const here = `/invite/${token}`
  return (
    <AuthShell
      title="You have been invited"
      intro="Join your firm on Nyayrithm."
      footer={<Link href="/" className="text-brass-text hover:text-brass-lit">Back to the site</Link>}
    >
      {state.kind === "loading" && (
        <p role="status" className="flex items-center justify-center gap-2 text-foreground/50"><Loader2 className="h-4 w-4 animate-spin" /> Checking the invitation…</p>
      )}

      {(state.kind === "gone" || state.kind === "missing") && (
        <p role="alert" className="rounded-sm border border-oxblood-bright/25 bg-oxblood-bright/10 px-3 py-3 text-center text-[0.85rem] text-oxblood-bright">
          {state.message}
          <span className="mt-1 block text-foreground/50">Ask your firm for a new invitation.</span>
        </p>
      )}

      {state.kind === "ready" && (
        <div className="space-y-5">
          <div className="rounded-md border border-border bg-card/60 p-4 text-center">
            <p className="font-serif text-[1.2rem] text-bone">{state.invite.org_name}</p>
            <p className="mt-1 text-[0.82rem] text-foreground/55">
              You will join as <span className="text-bone">{state.invite.role}</span>
            </p>
            <p className="mt-2 font-mono text-[0.74rem] text-foreground/40">for {state.invite.email}</p>
          </div>

          {state.signedIn ? (
            <>
              <button
                onClick={accept}
                disabled={busy}
                className="flex w-full items-center justify-center gap-2 rounded-sm bg-brass py-2.5 text-[0.85rem] font-semibold text-[#12100A] transition-colors hover:bg-brass-lit disabled:opacity-50"
              >
                {busy && <Loader2 className="h-4 w-4 animate-spin" />} Accept invitation
              </button>
              <p className="text-center text-[0.74rem] text-foreground/40">
                You must be signed in as {state.invite.email}. Signed in as someone else?{" "}
                <Link href={`/login?redirect=${encodeURIComponent(here)}&email=${encodeURIComponent(state.invite.email)}`} className="text-brass-text hover:underline">Switch account</Link>
              </p>
            </>
          ) : (
            <div className="space-y-3">
              <Link
                href={`/signup?redirect=${encodeURIComponent(here)}&email=${encodeURIComponent(state.invite.email)}`}
                className="flex w-full items-center justify-center rounded-sm bg-brass py-2.5 text-[0.85rem] font-semibold text-[#12100A] transition-colors hover:bg-brass-lit"
              >
                Create an account
              </Link>
              <Link
                href={`/login?redirect=${encodeURIComponent(here)}&email=${encodeURIComponent(state.invite.email)}`}
                className="flex w-full items-center justify-center rounded-sm border border-border py-2.5 text-[0.85rem] text-foreground/70 hover:border-brass/40 hover:text-foreground"
              >
                I already have an account
              </Link>
              <p className="text-center text-[0.74rem] text-foreground/40">Use the address the invitation was sent to, {state.invite.email}.</p>
            </div>
          )}
          {error && <p role="alert" className="rounded-sm border border-oxblood-bright/25 bg-oxblood-bright/10 px-3 py-2 text-center text-[0.8rem] text-oxblood-bright">{error}</p>}
        </div>
      )}
    </AuthShell>
  )
}
