const KEYCLOAK_URL = process.env.NEXT_PUBLIC_KEYCLOAK_URL ?? "http://localhost:8080"
const KEYCLOAK_REALM = process.env.NEXT_PUBLIC_KEYCLOAK_REALM ?? "nyayrithm"
const KEYCLOAK_CLIENT_ID = process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID ?? "nyayrithm-app"

function buildAuthUrl(endpoint: string, redirectUri: string, extra?: Record<string, string>): string {
  const base = `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/${endpoint}`
  const params = new URLSearchParams({
    client_id: KEYCLOAK_CLIENT_ID,
    redirect_uri: redirectUri,
    response_type: "code",
    scope: "openid profile email",
    ...extra,
  })
  return `${base}?${params.toString()}`
}

export function getKeycloakLoginUrl(redirectUri: string): string {
  return buildAuthUrl("auth", redirectUri)
}

export function getKeycloakRegisterUrl(redirectUri: string): string {
  return buildAuthUrl("registrations", redirectUri)
}

export function getKeycloakLogoutUrl(redirectUri: string): string {
  const base = `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/logout`
  const params = new URLSearchParams({
    client_id: KEYCLOAK_CLIENT_ID,
    post_logout_redirect_uri: redirectUri,
  })
  return `${base}?${params.toString()}`
}
