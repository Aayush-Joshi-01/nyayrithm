from __future__ import annotations

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from jose import jwt

from app.core.auth import AuthError, KeycloakVerifier
from app.dependencies import authenticate_token
from tests.conftest import ISSUER, FakeKeycloak


def make_verifier(kc: FakeKeycloak, issuers: set[str] | None = None) -> KeycloakVerifier:
    return KeycloakVerifier(issuers=issuers or {ISSUER}, fetch_jwks=kc.fetch, cache_seconds=3600)


async def test_valid_token_yields_user(keycloak: FakeKeycloak):
    user = await make_verifier(keycloak).verify(
        keycloak.token("alice", roles=["user", "admin"])
    )
    assert user.id == "alice"
    assert user.email == "alice@example.test"
    assert user.is_admin
    assert "user" in user.roles


async def test_non_admin_is_not_admin(keycloak: FakeKeycloak):
    user = await make_verifier(keycloak).verify(keycloak.token("bob", roles=["user"]))
    assert not user.is_admin


async def test_expired_token_rejected(keycloak: FakeKeycloak):
    with pytest.raises(AuthError):
        await make_verifier(keycloak).verify(keycloak.token(expires_in=-600))


async def test_wrong_issuer_rejected(keycloak: FakeKeycloak):
    with pytest.raises(AuthError, match="issuer"):
        await make_verifier(keycloak).verify(
            keycloak.token(issuer="http://evil.test/realms/nyayrithm")
        )


async def test_either_configured_issuer_is_accepted(keycloak: FakeKeycloak):
    internal = "http://keycloak.test:8080/realms/nyayrithm"
    verifier = make_verifier(keycloak, {ISSUER, internal})
    assert (await verifier.verify(keycloak.token(issuer=internal))).id == "user-a"
    assert (await verifier.verify(keycloak.token(issuer=ISSUER))).id == "user-a"


async def test_token_signed_with_foreign_key_rejected(keycloak: FakeKeycloak):
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = other.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    with pytest.raises(AuthError):
        await make_verifier(keycloak).verify(keycloak.token(private_pem=pem))


async def test_unknown_kid_rejected(keycloak: FakeKeycloak):
    with pytest.raises(AuthError, match="Unknown signing key"):
        await make_verifier(keycloak).verify(keycloak.token(kid="rotated-away"))


async def test_hs256_token_rejected_even_if_secret_matches(keycloak: FakeKeycloak):
    # Algorithm-confusion guard: only RS256 from the JWKS is ever accepted.
    forged = jwt.encode({"sub": "mallory", "iss": ISSUER}, "change-me-in-production",
                        algorithm="HS256", headers={"kid": keycloak.kid})
    with pytest.raises(AuthError, match="algorithm"):
        await make_verifier(keycloak).verify(forged)


async def test_alg_none_rejected(keycloak: FakeKeycloak):
    import base64
    import json

    def b64(d: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()

    unsigned = f"{b64({'alg': 'none', 'kid': keycloak.kid})}.{b64({'sub': 'm', 'iss': ISSUER})}."
    with pytest.raises(AuthError):
        await make_verifier(keycloak).verify(unsigned)


async def test_garbage_token_rejected(keycloak: FakeKeycloak):
    with pytest.raises(AuthError):
        await make_verifier(keycloak).verify("not-a-jwt")


async def test_token_without_subject_rejected(keycloak: FakeKeycloak):
    token = jwt.encode(
        {"iss": ISSUER, "exp": 9999999999}, keycloak._private_pem,
        algorithm="RS256", headers={"kid": keycloak.kid},
    )
    with pytest.raises(AuthError, match="subject"):
        await make_verifier(keycloak).verify(token)


async def test_jwks_is_cached_between_verifications(keycloak: FakeKeycloak):
    keycloak.fetch_count = 0
    verifier = make_verifier(keycloak)
    for _ in range(3):
        await verifier.verify(keycloak.token())
    assert keycloak.fetch_count == 1


async def test_key_rotation_triggers_one_refresh(keycloak: FakeKeycloak):
    verifier = make_verifier(keycloak)
    await verifier.verify(keycloak.token())
    keycloak.fetch_count = 0

    rotated = FakeKeycloak(kid="key-2")
    swapped = {"keys": keycloak.jwks["keys"] + rotated.jwks["keys"]}

    async def fetch() -> dict:
        keycloak.fetch_count += 1
        return swapped

    verifier._fetch = fetch
    assert (await verifier.verify(rotated.token("carol"))).id == "carol"
    assert keycloak.fetch_count == 1


async def test_jwks_outage_is_an_auth_error_not_a_crash():
    async def broken() -> dict:
        raise ConnectionError("keycloak down")

    verifier = KeycloakVerifier(issuers={ISSUER}, fetch_jwks=broken)
    kc = FakeKeycloak()
    with pytest.raises(AuthError, match="signing keys"):
        await verifier.verify(kc.token())


# ── dependency behaviour ──────────────────────────────────────────────────────
async def test_missing_token_is_401(db_path, keycloak: FakeKeycloak):
    with pytest.raises(HTTPException) as exc:
        await authenticate_token(None, make_verifier(keycloak))
    assert exc.value.status_code == 401
    assert exc.value.headers == {"WWW-Authenticate": "Bearer"}


async def test_dev_bypass_only_applies_without_a_token(
    db_path, keycloak: FakeKeycloak, monkeypatch: pytest.MonkeyPatch
):
    from app.config import get_settings

    monkeypatch.setenv("AUTH_DEV_BYPASS", "true")
    get_settings.cache_clear()
    verifier = make_verifier(keycloak)

    assert (await authenticate_token(None, verifier)).id == "00000000-0000-4000-8000-0000000000b1"
    # A presented-but-invalid token is still rejected; bypass is not a skip-validation flag.
    with pytest.raises(HTTPException):
        await authenticate_token("garbage", verifier)
    assert (await authenticate_token(keycloak.token("alice"), verifier)).id == "alice"


def test_production_refuses_dev_bypass(monkeypatch: pytest.MonkeyPatch):
    from pydantic import ValidationError

    from app.config import Settings

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AUTH_DEV_BYPASS", "true")
    monkeypatch.setenv("SECRET_KEY", "a-real-secret")
    with pytest.raises(ValidationError, match="Dev authentication"):
        Settings()


def test_production_refuses_default_secret(monkeypatch: pytest.MonkeyPatch):
    from pydantic import ValidationError

    from app.config import Settings

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AUTH_DEV_BYPASS", "false")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None)


def test_unimplemented_backends_fail_at_startup(monkeypatch: pytest.MonkeyPatch):
    from pydantic import ValidationError

    from app.config import Settings

    monkeypatch.setenv("VECTOR_DB_BACKEND", "chroma")
    with pytest.raises(ValidationError):
        Settings()
