import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

// Everything except the login page and the auth routes needs a session. In open dev mode
// there is no login wall. The API itself re-checks the platform_admin role on every call.
export function middleware(request: NextRequest) {
  if (process.env.NEXT_PUBLIC_DEV_AUTH_MODE === "open") return NextResponse.next()

  const session =
    request.cookies.get("kc_admin_access_token")?.value ??
    request.cookies.get("kc_admin_refresh_token")?.value
  if (!session) {
    const url = new URL("/login", request.url)
    if (request.nextUrl.pathname !== "/") url.searchParams.set("redirect", request.nextUrl.pathname)
    return NextResponse.redirect(url)
  }
  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!login|api/auth|_next/static|_next/image|icon.svg|favicon.ico).*)"],
}
