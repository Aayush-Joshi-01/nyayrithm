import { NextRequest, NextResponse } from "next/server"

const KC_URL =
  process.env.KEYCLOAK_URL ?? process.env.NEXT_PUBLIC_KEYCLOAK_URL ?? "http://localhost:8080"
const KC_REALM = process.env.NEXT_PUBLIC_KEYCLOAK_REALM ?? "nyayrithm"
const KC_CLIENT_ID = process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID ?? "nyayrithm-admin"

function realmRoles(accessToken: string): string[] {
  try {
    const payload = JSON.parse(Buffer.from(accessToken.split(".")[1], "base64url").toString())
    return payload?.realm_access?.roles ?? []
  } catch {
    return []
  }
}

export async function POST(req: NextRequest) {
  const { email, password } = await req.json()
  if (!email || !password) {
    return NextResponse.json({ error: "Email and password are required" }, { status: 400 })
  }

  let kcRes: Response
  try {
    kcRes = await fetch(`${KC_URL}/realms/${KC_REALM}/protocol/openid-connect/token`, {
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
    return NextResponse.json({ error: "Invalid email or password" }, { status: 401 })
  }

  const { access_token, refresh_token, expires_in } = await kcRes.json()
  // A valid Keycloak account is not enough: this console is for platform operators only.
  if (!realmRoles(access_token).includes("platform_admin")) {
    return NextResponse.json(
      { error: "This account is not a platform administrator." },
      { status: 403 },
    )
  }

  const res = NextResponse.json({ ok: true })
  const secure = process.env.NODE_ENV === "production"
  res.cookies.set("kc_admin_access_token", access_token, {
    httpOnly: true, secure, sameSite: "strict", maxAge: expires_in, path: "/",
  })
  res.cookies.set("kc_admin_refresh_token", refresh_token, {
    httpOnly: true, secure, sameSite: "strict", maxAge: 60 * 60 * 8, path: "/",
  })
  return res
}
