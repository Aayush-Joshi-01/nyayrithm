import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

export function middleware(request: NextRequest) {
  // In dev mode, bypass auth check
  if (process.env.NEXT_PUBLIC_DEV_AUTH_MODE === "open" || process.env.NEXT_PUBLIC_DEV_MODE === "true") {
    return NextResponse.next()
  }

  // The access token is short-lived; a surviving refresh token lets /api/auth/token
  // mint a new one, so either cookie counts as a live session.
  const token =
    request.cookies.get("kc_access_token")?.value ??
    request.cookies.get("kc_refresh_token")?.value

  if (!token) {
    const loginUrl = new URL("/login", request.url)
    loginUrl.searchParams.set("redirect", request.nextUrl.pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/dashboard/:path*"],
}
