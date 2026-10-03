// Development auth mode, set by `make dev` (open) or `make dev-creds` (credentials).
//   off          production: every request needs a platform_admin session
//   open         no login; the API treats token-less requests as the seeded dev user
//   credentials  real Keycloak login with the static accounts listed on the login screen
export type DevAuthMode = "off" | "open" | "credentials"

export const DEV_AUTH_MODE: DevAuthMode =
  (process.env.NEXT_PUBLIC_DEV_AUTH_MODE as DevAuthMode | undefined) ?? "off"

export const DEV_OPEN = DEV_AUTH_MODE === "open"
export const IS_DEV = DEV_AUTH_MODE !== "off"

export interface DevAccount { role: string; email: string; password: string }

export function devAccounts(): DevAccount[] {
  try {
    const raw = process.env.NEXT_PUBLIC_DEV_ACCOUNTS
    return raw ? (JSON.parse(raw) as DevAccount[]) : []
  } catch {
    return []
  }
}
