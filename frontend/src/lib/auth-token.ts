// Client-side access-token cache for talking to the FastAPI backend.

let cached: { token: string | null; expiresAt: number } | null = null
let inflight: Promise<string | null> | null = null

function expiryOf(token: string): number {
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")))
    return typeof payload.exp === "number" ? payload.exp * 1000 : Date.now() + 60_000
  } catch {
    return Date.now() + 60_000
  }
}

export function clearAccessToken(): void {
  cached = null
}

/** Returns a valid bearer token, or null when running in dev mode without a login. */
export async function getAccessToken(forceRefresh = false): Promise<string | null> {
  if (!forceRefresh && cached && cached.expiresAt - 15_000 > Date.now()) {
    return cached.token
  }
  if (inflight) return inflight

  inflight = (async () => {
    try {
      const res = await fetch("/api/auth/token", { cache: "no-store", credentials: "same-origin" })
      if (!res.ok) {
        cached = null
        return null
      }
      const { token } = (await res.json()) as { token: string | null }
      cached = { token, expiresAt: token ? expiryOf(token) : Date.now() + 60_000 }
      return token
    } catch {
      return null
    } finally {
      inflight = null
    }
  })()
  return inflight
}

export function redirectToLogin(): void {
  if (typeof window === "undefined") return
  if (process.env.NEXT_PUBLIC_DEV_MODE === "true") return
  const here = window.location.pathname + window.location.search
  window.location.href = `/login?redirect=${encodeURIComponent(here)}`
}
