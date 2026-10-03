from __future__ import annotations

import os
import sqlite3
import time
import uuid
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk, jwt

# Settings are cached on first use, so the test environment is fixed before app import.
os.environ.update({
    "APP_ENV": "development",
    "DEBUG": "false",
    "DB_BACKEND": "sqlite",
    "AUTH_DEV_BYPASS": "false",
    "KEYCLOAK_URL": "http://keycloak.test:8080",
    "NEXT_PUBLIC_KEYCLOAK_URL": "http://localhost:8080",
    "NEXT_PUBLIC_KEYCLOAK_REALM": "nyayrithm",
    "STORAGE_BACKEND": "local",
    "GEMINI_API_KEY": "",
    "OPENAI_API_KEY": "",
    "ANTHROPIC_API_KEY": "",
})

ISSUER = "http://localhost:8080/realms/nyayrithm"
KID = "test-key-1"

SQLITE_SCHEMA = """
CREATE TABLE cases (
    id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT DEFAULT '',
    country TEXT NOT NULL, jurisdiction TEXT DEFAULT '', legal_system TEXT DEFAULT 'common_law',
    status TEXT DEFAULT 'open', created_by TEXT NOT NULL, metadata TEXT DEFAULT '{}',
    created_at TEXT, updated_at TEXT
);
CREATE TABLE evidence (
    id TEXT PRIMARY KEY, case_id TEXT NOT NULL, title TEXT NOT NULL, description TEXT DEFAULT '',
    evidence_type TEXT NOT NULL, file_path TEXT NOT NULL, file_size INTEGER DEFAULT 0,
    mime_type TEXT NOT NULL, modality TEXT DEFAULT 'text', raw_text TEXT, transcription TEXT,
    embedder_used TEXT, metadata TEXT DEFAULT '{}', status TEXT DEFAULT 'pending',
    linked_participants TEXT DEFAULT '[]', vector_collection TEXT, chunk_count INTEGER DEFAULT 0,
    tags TEXT DEFAULT '[]', error_message TEXT, indexed_at TEXT, uploaded_by TEXT NOT NULL,
    created_at TEXT
);
CREATE TABLE simulations (
    id TEXT PRIMARY KEY, case_id TEXT NOT NULL, title TEXT NOT NULL, mode TEXT DEFAULT 'courtroom',
    status TEXT DEFAULT 'draft', current_turn INTEGER DEFAULT 0, max_turns INTEGER DEFAULT 50,
    turn_order TEXT DEFAULT '[]', config TEXT DEFAULT '{}', started_at TEXT, ended_at TEXT,
    created_by TEXT NOT NULL, created_at TEXT, updated_at TEXT
);
CREATE TABLE agent_definitions (
    id TEXT PRIMARY KEY, simulation_id TEXT NOT NULL, parent_agent_id TEXT, spawn_reason TEXT,
    is_predefined INTEGER DEFAULT 1, role TEXT NOT NULL, name TEXT NOT NULL,
    persona TEXT DEFAULT '{}', llm_provider TEXT NOT NULL, llm_model TEXT NOT NULL,
    system_prompt TEXT DEFAULT '', knowledge_scope TEXT DEFAULT '{}',
    jurisdiction_context TEXT DEFAULT '{}', status TEXT DEFAULT 'active', initial_instruction TEXT,
    spawned_at TEXT
);
CREATE TABLE turns (
    id TEXT PRIMARY KEY, simulation_id TEXT NOT NULL, agent_id TEXT NOT NULL,
    turn_number INTEGER NOT NULL, content TEXT NOT NULL, content_edited TEXT,
    reasoning_trace TEXT DEFAULT '{}', citations TEXT DEFAULT '[]',
    retrieved_chunks TEXT DEFAULT '[]', spawned_agents TEXT DEFAULT '[]',
    is_human_override INTEGER DEFAULT 0, token_count INTEGER DEFAULT 0, latency_ms INTEGER DEFAULT 0,
    metadata TEXT DEFAULT '{}', created_at TEXT
);
CREATE TABLE audit_events (
    id TEXT PRIMARY KEY, simulation_id TEXT NOT NULL, seq INTEGER NOT NULL,
    event_type TEXT NOT NULL, actor TEXT NOT NULL DEFAULT '', payload TEXT DEFAULT '{}',
    prev_hash TEXT NOT NULL, hash TEXT NOT NULL, created_at TEXT
);
"""


# ── Keycloak stand-in ─────────────────────────────────────────────────────────
class FakeKeycloak:
    """An RSA keypair, a JWKS document, and a token minting helper."""

    def __init__(self, kid: str = KID) -> None:
        self.kid = kid
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self._private_pem = self.private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        public_pem = self.private_key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        jwk_dict = jwk.construct(public_pem, "RS256").to_dict()
        self.jwks = {"keys": [{
            **{k: (v.decode() if isinstance(v, bytes) else v) for k, v in jwk_dict.items()},
            "kid": kid, "use": "sig",
        }]}
        self.fetch_count = 0

    async def fetch(self) -> dict:
        self.fetch_count += 1
        return self.jwks

    def token(
        self,
        sub: str = "user-a",
        *,
        issuer: str = ISSUER,
        expires_in: int = 300,
        roles: list[str] | None = None,
        kid: str | None = None,
        private_pem: bytes | None = None,
        **extra,
    ) -> str:
        now = int(time.time())
        claims = {
            "sub": sub, "iss": issuer, "aud": "account", "iat": now, "exp": now + expires_in,
            "email": f"{sub}@example.test", "preferred_username": sub,
            "realm_access": {"roles": roles if roles is not None else ["user"]},
            **extra,
        }
        return jwt.encode(
            claims, private_pem or self._private_pem, algorithm="RS256",
            headers={"kid": kid or self.kid},
        )


@pytest.fixture(scope="session")
def keycloak() -> FakeKeycloak:
    return FakeKeycloak()


@pytest.fixture
def auth_headers(keycloak: FakeKeycloak) -> Callable[..., dict[str, str]]:
    def make(sub: str = "user-a", **kw) -> dict[str, str]:
        return {"Authorization": f"Bearer {keycloak.token(sub, **kw)}"}
    return make


# ── App, database, storage ────────────────────────────────────────────────────
@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A fresh SQLite database (and storage dir) per test, with every cache reset."""
    from app.config import get_settings
    from app.core.auth import get_verifier
    from app.db import session as db_session
    from app.storage.factory import get_file_storage

    path = tmp_path / "test.db"
    conn = sqlite3.connect(path)
    conn.executescript(SQLITE_SCHEMA)
    conn.commit()
    conn.close()

    monkeypatch.setenv("SQLITE_PATH", str(path))
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", str(tmp_path / "storage"))
    for cached in (get_settings, get_verifier, get_file_storage,
                   db_session._make_engine, db_session._make_session_factory):
        cached.cache_clear()
    yield path
    for cached in (get_settings, get_verifier, get_file_storage,
                   db_session._make_engine, db_session._make_session_factory):
        cached.cache_clear()


@pytest.fixture
def queued(monkeypatch: pytest.MonkeyPatch) -> dict[str, MagicMock]:
    """Celery tasks must never reach a broker in tests."""
    from app.tasks.evidence_tasks import ingest_evidence
    from app.tasks.simulation_tasks import run_simulation

    mocks = {"ingest": MagicMock(), "run": MagicMock()}
    monkeypatch.setattr(ingest_evidence, "delay", mocks["ingest"])
    monkeypatch.setattr(run_simulation, "delay", mocks["run"])
    return mocks


@pytest.fixture
def fake_idp(monkeypatch: pytest.MonkeyPatch, keycloak: FakeKeycloak, db_path: Path) -> FakeKeycloak:
    """Point the verifier at the fake JWKS instead of a real Keycloak."""
    from app.core.auth import get_verifier

    monkeypatch.setattr("app.core.auth._fetch_jwks", keycloak.fetch)
    get_verifier.cache_clear()
    keycloak.fetch_count = 0
    return keycloak


@pytest.fixture
def app(db_path: Path, fake_idp: FakeKeycloak, queued):
    from app.main import create_app

    return create_app()


@pytest_asyncio.fixture
async def client(app) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── Seeding helpers (synchronous sqlite3, independent of the app's event loop) ─
class Seeder:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _insert(self, table: str, **cols) -> str:
        conn = sqlite3.connect(self.path)
        keys = ", ".join(cols)
        marks = ", ".join("?" for _ in cols)
        conn.execute(f"INSERT INTO {table} ({keys}) VALUES ({marks})", list(cols.values()))
        conn.commit()
        conn.close()
        return cols["id"]

    def case(self, owner: str = "user-a", **kw) -> str:
        return self._insert(
            "cases", id=str(uuid.uuid4()), title=kw.pop("title", "State v. Test"),
            country="India", created_by=owner,
            created_at="2026-01-01T00:00:00+00:00", updated_at="2026-01-01T00:00:00+00:00", **kw,
        )

    def simulation(self, case_id: str, owner: str = "user-a", **kw) -> str:
        return self._insert(
            "simulations", id=str(uuid.uuid4()), case_id=case_id, title="Sim", created_by=owner,
            created_at="2026-01-01T00:00:00+00:00", updated_at="2026-01-01T00:00:00+00:00", **kw,
        )

    def agent(self, sim_id: str, role: str = "judge", **kw) -> str:
        return self._insert(
            "agent_definitions", id=str(uuid.uuid4()), simulation_id=sim_id, role=role,
            name=kw.pop("name", "Agent"), llm_provider="gemini", llm_model="m",
            spawned_at="2026-01-01T00:00:00+00:00", **kw,
        )

    def turn(self, sim_id: str, agent_id: str, number: int = 0, content: str = "Hello") -> str:
        return self._insert(
            "turns", id=str(uuid.uuid4()), simulation_id=sim_id, agent_id=agent_id,
            turn_number=number, content=content, created_at="2026-01-01T00:00:00+00:00",
        )

    def evidence(self, case_id: str, owner: str = "user-a", **kw) -> str:
        return self._insert(
            "evidence", id=str(uuid.uuid4()), case_id=case_id, title="Exhibit A",
            evidence_type="text", file_path="cases/x/a.txt", mime_type="text/plain",
            uploaded_by=owner, created_at="2026-01-01T00:00:00+00:00", **kw,
        )


@pytest.fixture
def seed(db_path: Path) -> Seeder:
    return Seeder(db_path)
