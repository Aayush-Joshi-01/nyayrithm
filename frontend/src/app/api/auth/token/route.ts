import { NextRequest, NextResponse } from "next/server"

// Hands the browser a short-lived bearer token for calling the FastAPI backend.
// The tokens themselves live in httpOnly cookies, so client JS can't read them
// directly; this route is the one place that does, refreshing when needed.
const KC_URL =
  process.env.KEYCLOAK_URL ??
  process.env.NEXT_PUBLIC_KEYCLOAK_URL ??
  "http://localhost:8080"
const KC_REALM = process.env.NEXT_PUBLIC_KEYCLOAK_REALM ?? "nyayrithm"
const KC_CLIENT_ID = process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID ?? "nyayrithm-app"

const NO_STORE = { "Cache-Control": "no-store" }

export async function GET(req: NextRequest) {
  const access = req.cookies.get("kc_access_token")?.value
  if (access) {
    return NextResponse.json({ token: access }, { headers: NO_STORE })
  }

  const refresh = req.cookies.get("kc_refresh_token")?.value
  if (!refresh) {
    // Dev mode runs without a login wall; the backend accepts token-less requests then.
    if (process.env.NEXT_PUBLIC_DEV_AUTH_MODE === "open" || process.env.NEXT_PUBLIC_DEV_MODE === "true") {
      return NextResponse.json({ token: null }, { headers: NO_STORE })
    }
    return NextResponse.json({ error: "Not authenticated" }, { status: 401, headers: NO_STORE })
  }

  let kcRes: Response
  try {
    kcRes = await fetch(`${KC_URL}/realms/${KC_REALM}/protocol/openid-connect/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "refresh_token",
        client_id: KC_CLIENT_ID,
        refresh_token: refresh,
      }),
    })
  } catch {
    return NextResponse.json(
      { error: "Could not reach authentication server" },
      { status: 503, headers: NO_STORE },
    )
  }

  if (!kcRes.ok) {
    const res = NextResponse.json(
      { error: "Session expired" },
      { status: 401, headers: NO_STORE },
    )
    res.cookies.delete("kc_access_token")
    res.cookies.delete("kc_refresh_token")
    return res
  }

  const { access_token, refresh_token, expires_in } = await kcRes.json()
  const res = NextResponse.json({ token: access_token }, { headers: NO_STORE })
  const secure = process.env.NODE_ENV === "production"
  res.cookies.set("kc_access_token", access_token, {
    httpOnly: true,
    secure,
    sameSite: "lax",
    maxAge: expires_in,
    path: "/",
  })
  res.cookies.set("kc_refresh_token", refresh_token, {
    httpOnly: true,
    secure,
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 30,
    path: "/",
  })
  return res
}
