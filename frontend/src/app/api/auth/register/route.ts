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
const KC_ADMIN_USER = process.env.KEYCLOAK_ADMIN_USER ?? "admin"
const KC_ADMIN_PASS = process.env.KEYCLOAK_ADMIN_PASS ?? "admin"

async function getAdminToken(): Promise<string> {
  const res = await fetch(`${KC_URL}/realms/master/protocol/openid-connect/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "password",
      client_id: "admin-cli",
      username: KC_ADMIN_USER,
      password: KC_ADMIN_PASS,
    }),
  })
  if (!res.ok) throw new Error("Failed to get admin token")
  const data = await res.json()
  return data.access_token
}

export async function POST(req: NextRequest) {
  const { firstName, lastName, email, password } = await req.json()

  if (!firstName || !lastName || !email || !password) {
    return NextResponse.json({ error: "All fields are required" }, { status: 400 })
  }

  let adminToken: string
  try {
    adminToken = await getAdminToken()
  } catch {
    return NextResponse.json({ error: "Could not reach authentication server" }, { status: 503 })
  }

  const createRes = await fetch(`${KC_URL}/admin/realms/${KC_REALM}/users`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${adminToken}`,
    },
    body: JSON.stringify({
      firstName,
      lastName,
      email,
      username: email,
      enabled: true,
      emailVerified: true,
      credentials: [{ type: "password", value: password, temporary: false }],
    }),
  })

  if (createRes.status === 409) {
    return NextResponse.json({ error: "An account with this email already exists" }, { status: 409 })
  }

  if (!createRes.ok) {
    const body = await createRes.json().catch(() => ({}))
    return NextResponse.json({ error: body.errorMessage ?? "Registration failed" }, { status: 400 })
  }

  // Auto-login after successful registration
  const tokenRes = await fetch(`${KC_URL}/realms/${KC_REALM}/protocol/openid-connect/token`, {
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

  if (!tokenRes.ok) {
    return NextResponse.json({ ok: true, redirect: "/login" })
  }

  const tokens = await tokenRes.json()
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
