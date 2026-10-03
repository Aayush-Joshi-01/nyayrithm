// Which firm the signed-in person is acting for. Most people belong to one firm, in which
// case nothing is stored and the API picks it; with several, the choice is remembered here
// and sent as X-Org-Id on every request.
const KEY = "nyay-org"

export function getActiveOrg(): string | null {
  if (typeof window === "undefined") return null
  try {
    return window.localStorage.getItem(KEY)
  } catch {
    return null
  }
}

export function setActiveOrg(orgId: string | null): void {
  try {
    if (orgId) window.localStorage.setItem(KEY, orgId)
    else window.localStorage.removeItem(KEY)
  } catch {
    /* storage unavailable: the API falls back to the oldest firm */
  }
}
