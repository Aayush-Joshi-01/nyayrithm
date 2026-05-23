import { NextRequest, NextResponse } from "next/server"

// KEYCLOAK_URL = internal Docker network URL (http://keycloak:8080)
// NEXT_PUBLIC_KEYCLOAK_URL = browser-facing URL (http://localhost:8080)
// API routes run server-side inside Docker, so prefer KEYCLOAK_URL
const KC_URL =
  process.env.KEYCLOAK_URL ??
  process.env.NEXT_PUBLIC_KEYCLOAK_URL ??
  "http://localhost:8080"
const KC_REALM = process.env.NEXT_PUBLIC_KEYCLOAK_REALM ?? "nyayrithm"
const KC_CLIENT_ID = process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID ?? "nyayrithm-app"

export async function POST(req: NextRequest) {
  const { email, password } = await req.json()

  if (!email || !password) {
    return NextResponse.json({ error: "Email and password are required" }, { status: 400 })
  }

  const tokenUrl = `${KC_URL}/realms/${KC_REALM}/protocol/openid-connect/token`

  let kcRes: Response
  try {
    kcRes = await fetch(tokenUrl, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "password",
        client_id: KC_CLIENT_ID,
        username: email,
        password,
        scope: "openid profile email",
      }),
    })
  } catch {
    return NextResponse.json({ error: "Could not reach authentication server" }, { status: 503 })
  }

  if (!kcRes.ok) {
    const body = await kcRes.json().catch(() => ({}))
    const message =
      kcRes.status === 401
        ? "Invalid email or password"
        : body.error_description ?? "Authentication failed"
    return NextResponse.json({ error: message }, { status: 401 })
  }

  const tokens = await kcRes.json()
  const { access_token, refresh_token, expires_in } = tokens

  const res = NextResponse.json({ ok: true })

  res.cookies.set("kc_access_token", access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: expires_in,
    path: "/",
  })

  res.cookies.set("kc_refresh_token", refresh_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 30,
    path: "/",
  })

  return res
}
