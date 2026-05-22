import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

export function middleware(request: NextRequest) {
  // In dev mode, bypass auth check
  if (process.env.NEXT_PUBLIC_DEV_MODE === "true") {
    return NextResponse.next()
  }

  // Check for access token cookie set by Keycloak callback handler
  const token = request.cookies.get("kc_access_token")?.value

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
