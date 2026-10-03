from __future__ import annotations

"""A small client for Keycloak's admin REST API (user enable/disable, role grants)."""

from typing import Any

import httpx

from app.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError, NyayrithmError


class KeycloakAdminError(NyayrithmError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "KEYCLOAK_UNAVAILABLE")


class KeycloakAdmin:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client
        self._settings = get_settings()

    def _http(self) -> httpx.AsyncClient:
        return self._client or httpx.AsyncClient(timeout=15.0)

    @property
    def _base(self) -> str:
        return self._settings.KEYCLOAK_URL.rstrip("/")

    @property
    def _realm(self) -> str:
        return self._settings.NEXT_PUBLIC_KEYCLOAK_REALM

    async def _token(self, http: httpx.AsyncClient) -> str:
        s = self._settings
        if not (s.KEYCLOAK_ADMIN_USER and s.KEYCLOAK_ADMIN_PASS):
            raise KeycloakAdminError("Keycloak admin credentials are not configured.")
        resp = await http.post(
            f"{self._base}/realms/master/protocol/openid-connect/token",
            data={"grant_type": "password", "client_id": "admin-cli",
                  "username": s.KEYCLOAK_ADMIN_USER, "password": s.KEYCLOAK_ADMIN_PASS},
        )
        if resp.status_code != 200:
            raise KeycloakAdminError("Could not authenticate to Keycloak as admin.")
        return resp.json()["access_token"]

    async def _call(self, method: str, path: str, **kw: Any) -> httpx.Response:
        owns = self._client is None
        http = self._http()
        try:
            token = await self._token(http)
            resp = await http.request(
                method, f"{self._base}/admin/realms/{self._realm}{path}",
                headers={"Authorization": f"Bearer {token}"}, **kw,
            )
            return resp
        except httpx.HTTPError as exc:
            raise KeycloakAdminError(f"Keycloak is unreachable: {exc}") from exc
        finally:
            if owns:
                await http.aclose()

    async def set_enabled(self, user_id: str, enabled: bool) -> None:
        got = await self._call("GET", f"/users/{user_id}")
        if got.status_code == 404:
            raise NotFoundError("User", user_id)
        if got.status_code != 200:
            raise KeycloakAdminError(f"Keycloak returned {got.status_code}.")
        user = got.json()
        user["enabled"] = enabled
        put = await self._call("PUT", f"/users/{user_id}", json=user)
        if put.status_code not in (200, 204):
            raise KeycloakAdminError(f"Keycloak returned {put.status_code}.")
        if not enabled:
            # Kill live sessions so a disabled user is out immediately, not at token expiry.
            await self._call("POST", f"/users/{user_id}/logout")

    async def grant_role_by_email(self, email: str, role: str = "platform_admin") -> str:
        found = await self._call("GET", "/users", params={"email": email, "exact": "true"})
        users = found.json() if found.status_code == 200 else []
        if not users:
            raise NotFoundError("User", email)
        user_id = users[0]["id"]
        role_rep = await self._call("GET", f"/roles/{role}")
        if role_rep.status_code != 200:
            raise ConflictError(f"The realm has no role '{role}'. Re-import the realm file.")
        resp = await self._call("POST", f"/users/{user_id}/role-mappings/realm",
                                json=[role_rep.json()])
        if resp.status_code not in (200, 204):
            raise KeycloakAdminError(f"Keycloak returned {resp.status_code}.")
        return user_id
