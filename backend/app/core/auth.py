from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

import httpx
from jose import JWTError, jwt

from app.config import get_settings

JWKSFetcher = Callable[[], Awaitable[dict[str, Any]]]


class AuthError(Exception):
    """Raised when a bearer token cannot be trusted."""


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str | None = None
    username: str | None = None
    roles: frozenset[str] = field(default_factory=frozenset)
    # The firm this request acts for; filled in by get_org_user from the user's membership.
    org_id: str | None = None
    org_role: str | None = None  # owner | admin | attorney

    @property
    def is_platform_admin(self) -> bool:
        """Platform operator (Keycloak realm role). Never grants access to firm data."""
        return "platform_admin" in self.roles

    @property
    def is_firm_manager(self) -> bool:
        return self.org_role in ("owner", "admin")


async def _fetch_jwks() -> dict[str, Any]:
    url = get_settings().keycloak_jwks_url
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


class KeycloakVerifier:
    """Verifies Keycloak-issued RS256 access tokens against the realm's JWKS.

    Keys are cached; an unknown ``kid`` triggers one forced refresh so key rotation
    does not require a restart.
    """

    def __init__(
        self,
        issuers: set[str],
        fetch_jwks: JWKSFetcher = _fetch_jwks,
        cache_seconds: int = 3600,
        leeway: int = 10,
    ) -> None:
        self._issuers = issuers
        self._fetch = fetch_jwks
        self._cache_seconds = cache_seconds
        self._leeway = leeway
        self._keys: dict[str, dict[str, Any]] = {}
        self._fetched_at = 0.0

    async def _refresh(self) -> None:
        try:
            jwks = await self._fetch()
        except Exception as exc:  # noqa: BLE001
            raise AuthError(f"Could not load signing keys: {exc}") from exc
        self._keys = {k["kid"]: k for k in jwks.get("keys", []) if "kid" in k}
        self._fetched_at = time.monotonic()

    async def _key_for(self, kid: str) -> dict[str, Any]:
        stale = time.monotonic() - self._fetched_at > self._cache_seconds
        if stale or kid not in self._keys:
            await self._refresh()
        key = self._keys.get(kid)
        if key is None:
            raise AuthError("Unknown signing key")
        return key

    async def verify(self, token: str) -> AuthenticatedUser:
        try:
            header = jwt.get_unverified_header(token)
        except JWTError as exc:
            raise AuthError("Malformed token") from exc
        if header.get("alg") != "RS256" or not header.get("kid"):
            raise AuthError("Unsupported token algorithm")

        key = await self._key_for(header["kid"])
        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                # Keycloak access tokens carry aud="account"; issuer is checked below
                # because we accept both the internal and public hostnames.
                options={"verify_aud": False, "verify_iss": False, "leeway": self._leeway},
            )
        except JWTError as exc:
            raise AuthError(f"Invalid token: {exc}") from exc

        if claims.get("iss") not in self._issuers:
            raise AuthError("Untrusted token issuer")
        sub = claims.get("sub")
        if not sub:
            raise AuthError("Token has no subject")

        roles = frozenset((claims.get("realm_access") or {}).get("roles", []))
        return AuthenticatedUser(
            id=str(sub),
            email=claims.get("email"),
            username=claims.get("preferred_username"),
            roles=roles,
        )


@lru_cache
def get_verifier() -> KeycloakVerifier:
    settings = get_settings()
    return KeycloakVerifier(
        issuers=settings.keycloak_issuers,
        # Resolved at call time so the fetcher can be swapped out (tests, custom IdPs).
        fetch_jwks=lambda: _fetch_jwks(),
        cache_seconds=settings.AUTH_JWKS_CACHE_SECONDS,
    )


def dev_user() -> AuthenticatedUser:
    settings = get_settings()
    return AuthenticatedUser(
        id=settings.DEV_USER_ID,
        email="owner@devfirm.nyayrithm.dev",
        username="dev",
        # In open dev mode the one bypass identity is both the firm owner and the platform admin.
        roles=frozenset({"user", "platform_admin"}),
    )
