/* The project runs on two domains in production:
 *   MARKETING_URL — the public landing page and docs (indexed)
 *   APP_URL       — where people sign in and run proceedings
 * Both may point at the same deployment. Locally these are unset, so links
 * into the product stay same-origin and relative.
 */

export const MARKETING_URL =
  process.env.NEXT_PUBLIC_MARKETING_URL || "https://nyayrithm.aayushjoshi.dev"

const RAW_APP_URL = process.env.NEXT_PUBLIC_APP_URL || ""

/** Absolute URL into the app (sign-up, sign-in, dashboard) when a separate app
 *  domain is configured; a same-origin relative path otherwise. */
export function appHref(path: `/${string}`): string {
  return RAW_APP_URL ? `${RAW_APP_URL.replace(/\/$/, "")}${path}` : path
}

export const HAS_SEPARATE_APP_DOMAIN = Boolean(RAW_APP_URL)
