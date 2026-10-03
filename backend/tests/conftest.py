from __future__ import annotations

import os
import sqlite3
import time
import uuid
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import mongomock
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk, jwt

# Settings are cached on first use, so the test environment is fixed before app import.
os.environ.update({
    "APP_ENV": "development",
    "DEBUG": "false",
    "DEV_AUTH_MODE": "off",
    "AUTH_DEV_BYPASS": "false",
    "SEED_DEV_DATA": "false",
    "KEYCLOAK_URL": "http://keycloak.test:8080",
    "NEXT_PUBLIC_KEYCLOAK_URL": "http://localhost:8080",
    "NEXT_PUBLIC_KEYCLOAK_REALM": "nyayrithm",
    "STORAGE_BACKEND": "local",
    "GEMINI_API_KEY": "",
    "OPENAI_API_KEY": "",
    "ANTHROPIC_API_KEY": "",
})

ISSUER = "http://localhost:8080/realms/nyayrithm"
_SYNC_MONGO = None  # set per test by the db_path fixture
KID = "test-key-1"

SQLITE_SCHEMA = """
CREATE TABLE cases (
    id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT DEFAULT '',
    country TEXT NOT NULL, jurisdiction TEXT DEFAULT '', legal_system TEXT DEFAULT 'common_law',
    status TEXT DEFAULT 'open', created_by TEXT NOT NULL, metadata TEXT DEFAULT '{}',
    org_id TEXT, created_at TEXT, updated_at TEXT
);
CREATE TABLE evidence (
    id TEXT PRIMARY KEY, case_id TEXT NOT NULL, title TEXT NOT NULL, description TEXT DEFAULT '',
    evidence_type TEXT NOT NULL, file_path TEXT NOT NULL, file_size INTEGER DEFAULT 0,
    mime_type TEXT NOT NULL, modality TEXT DEFAULT 'text', org_id TEXT,
    embedder_used TEXT, metadata TEXT DEFAULT '{}', status TEXT DEFAULT 'pending',
    linked_participants TEXT DEFAULT '[]', vector_collection TEXT, chunk_count INTEGER DEFAULT 0,
    tags TEXT DEFAULT '[]', error_message TEXT, indexed_at TEXT, uploaded_by TEXT NOT NULL,
    created_at TEXT
);
CREATE TABLE simulations (
    id TEXT PRIMARY KEY, case_id TEXT NOT NULL, title TEXT NOT NULL, mode TEXT DEFAULT 'courtroom',
    status TEXT DEFAULT 'draft', current_turn INTEGER DEFAULT 0, max_turns INTEGER DEFAULT 50,
    turn_order TEXT DEFAULT '[]', config TEXT DEFAULT '{}', org_id TEXT, started_at TEXT,
    ended_at TEXT, created_by TEXT NOT NULL, created_at TEXT, updated_at TEXT
);
CREATE TABLE agent_definitions (
    id TEXT PRIMARY KEY, simulation_id TEXT NOT NULL, parent_agent_id TEXT, spawn_reason TEXT,
    is_predefined INTEGER DEFAULT 1, role TEXT NOT NULL, name TEXT NOT NULL,
    persona TEXT DEFAULT '{}', llm_provider TEXT NOT NULL, llm_model TEXT NOT NULL,
    system_prompt TEXT DEFAULT '', knowledge_scope TEXT DEFAULT '{}',
    jurisdiction_context TEXT DEFAULT '{}', status TEXT DEFAULT 'active', initial_instruction TEXT,
    spawned_at TEXT
);
CREATE TABLE organizations (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, slug TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'active', created_at TEXT, updated_at TEXT
);
CREATE TABLE memberships (
    id TEXT PRIMARY KEY, org_id TEXT NOT NULL, user_id TEXT NOT NULL, email TEXT NOT NULL,
    role TEXT NOT NULL, display_name TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT, last_seen_at TEXT, UNIQUE (org_id, user_id)
);
CREATE TABLE invites (
    id TEXT PRIMARY KEY, org_id TEXT NOT NULL, email TEXT NOT NULL, role TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE, invited_by TEXT NOT NULL, expires_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', accepted_by TEXT, accepted_at TEXT, created_at TEXT
);
CREATE TABLE plans (
    id TEXT PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL, seat_limit INTEGER DEFAULT 5,
    monthly_simulations INTEGER DEFAULT 50, monthly_tokens INTEGER DEFAULT 2000000,
    max_turns_per_sim INTEGER DEFAULT 100, storage_mb INTEGER DEFAULT 5000,
    features TEXT DEFAULT '{}', is_active INTEGER DEFAULT 1, created_at TEXT
);
CREATE TABLE subscriptions (
    id TEXT PRIMARY KEY, org_id TEXT NOT NULL UNIQUE, plan_code TEXT NOT NULL,
    status TEXT DEFAULT 'active', seats INTEGER DEFAULT 5, current_period_start TEXT,
    current_period_end TEXT, invoice_ref TEXT DEFAULT '', notes TEXT DEFAULT '',
    set_by TEXT DEFAULT '', created_at TEXT, updated_at TEXT
);
CREATE TABLE case_members (
    id TEXT PRIMARY KEY, case_id TEXT NOT NULL, user_id TEXT NOT NULL, added_by TEXT NOT NULL,
    created_at TEXT, UNIQUE (case_id, user_id)
);
CREATE TABLE usage_counters (
    id TEXT PRIMARY KEY, org_id TEXT NOT NULL, period TEXT NOT NULL, tokens INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0, simulations INTEGER DEFAULT 0, turns INTEGER DEFAULT 0,
    updated_at TEXT, UNIQUE (org_id, period)
);
CREATE TABLE admin_events (
    id TEXT PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, target_type TEXT DEFAULT '',
    target_id TEXT DEFAULT '', details TEXT DEFAULT '{}', created_at TEXT
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
def auth_headers(keycloak: FakeKeycloak, seed) -> Callable[..., dict[str, str]]:
    """Bearer headers for a user. By default the user is given a firm of their own first;
    pass ``provision=False`` for someone who must not belong to any firm, and ``org=`` to
    act for a specific firm (X-Org-Id)."""
    def make(sub: str = "user-a", *, provision: bool = True, org: str | None = None,
             **kw) -> dict[str, str]:
        if provision:
            seed.ensure_user(sub)
        headers = {"Authorization": f"Bearer {keycloak.token(sub, **kw)}"}
        if org:
            headers["X-Org-Id"] = org
        return headers
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

    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{path}")
    monkeypatch.setenv("STORAGE_LOCAL_ROOT", str(tmp_path / "storage"))
    for cached in (get_settings, get_verifier, get_file_storage,
                   db_session._make_engine, db_session._make_session_factory):
        cached.cache_clear()

    # MongoDB is replaced by an in-memory mongomock database shared between the app
    # (through an async wrapper) and the synchronous Seeder.
    from mongomock_motor import AsyncMongoMockClient

    sync_client = mongomock.MongoClient(tz_aware=True)
    monkeypatch.setattr(
        "app.db.mongo.get_mongo_db",
        lambda: AsyncMongoMockClient(mock_mongo_client=sync_client)["nyayrithm_test"],
    )
    monkeypatch.setattr("tests.conftest._SYNC_MONGO", sync_client["nyayrithm_test"], raising=False)
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
    """Direct inserts into the test databases.

    Every user id used by a test is auto-provisioned a firm of their own (an active
    subscription, one owner membership), so by default two users are in *different* firms.
    Tests that need a shared firm create it with ``org()`` / ``member()``.
    """

    NOW = "2026-01-01T00:00:00+00:00"

    def __init__(self, path: Path) -> None:
        self.path = path
        self._plan_ready = False
        self._firm_of: dict[str, str] = {}

    def _insert(self, table: str, **cols) -> str:
        conn = sqlite3.connect(self.path)
        keys = ", ".join(cols)
        marks = ", ".join("?" for _ in cols)
        conn.execute(f"INSERT INTO {table} ({keys}) VALUES ({marks})", list(cols.values()))
        conn.commit()
        conn.close()
        return cols["id"]

    # ── firms ─────────────────────────────────────────────────────────────────
    def plan(self, code: str = "pro", **limits) -> str:
        conn = sqlite3.connect(self.path)
        row = conn.execute("SELECT id FROM plans WHERE code = ?", [code]).fetchone()
        conn.close()
        if row:
            return row[0]
        values = {"seat_limit": 50, "monthly_simulations": 1000, "monthly_tokens": 100_000_000,
                  "max_turns_per_sim": 500, "storage_mb": 10_000, **limits}
        return self._insert("plans", id=str(uuid.uuid4()), code=code, name=code.title(),
                            created_at=self.NOW, **values)

    def org(self, name: str = "Acme LLP", *, status: str = "active", plan: str = "pro",
            seats: int = 10, sub_status: str = "active", period_end: str | None = None,
            plan_limits: dict | None = None) -> str:
        self.plan(plan, **(plan_limits or {}))
        org_id = self._insert(
            "organizations", id=str(uuid.uuid4()), name=name,
            slug=f"{name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}",
            status=status, created_at=self.NOW, updated_at=self.NOW,
        )
        self._insert(
            "subscriptions", id=str(uuid.uuid4()), org_id=org_id, plan_code=plan,
            status=sub_status, seats=seats, current_period_start=self.NOW,
            current_period_end=period_end, created_at=self.NOW, updated_at=self.NOW,
        )
        return org_id

    def member(self, org_id: str, user_id: str, role: str = "attorney",
               status: str = "active") -> str:
        self._firm_of.setdefault(user_id, org_id)
        return self._insert(
            "memberships", id=str(uuid.uuid4()), org_id=org_id, user_id=user_id,
            email=f"{user_id}@example.test", role=role, display_name=user_id,
            status=status, created_at=self.NOW,
        )

    def ensure_user(self, user_id: str) -> str:
        """The firm this user belongs to, creating a personal one on first use."""
        if user_id not in self._firm_of:
            conn = sqlite3.connect(self.path)
            row = conn.execute(
                "SELECT org_id FROM memberships WHERE user_id = ? AND status = 'active'",
                [user_id]).fetchone()
            conn.close()
            if row:
                self._firm_of[user_id] = row[0]
            else:
                self.member(self.org(f"Firm of {user_id}"), user_id, "owner")
        return self._firm_of[user_id]

    # ── case data ─────────────────────────────────────────────────────────────
    def case(self, owner: str = "user-a", org: str | None = None, **kw) -> str:
        return self._insert(
            "cases", id=str(uuid.uuid4()), title=kw.pop("title", "State v. Test"),
            country="India", created_by=owner, org_id=org or self.ensure_user(owner),
            created_at=self.NOW, updated_at=self.NOW, **kw,
        )

    def simulation(self, case_id: str, owner: str = "user-a", **kw) -> str:
        conn = sqlite3.connect(self.path)
        (org_id,) = conn.execute("SELECT org_id FROM cases WHERE id = ?", [case_id]).fetchone()
        conn.close()
        return self._insert(
            "simulations", id=str(uuid.uuid4()), case_id=case_id, title="Sim", created_by=owner,
            org_id=org_id, created_at=self.NOW, updated_at=self.NOW, **kw,
        )

    def agent(self, sim_id: str, role: str = "judge", **kw) -> str:
        return self._insert(
            "agent_definitions", id=str(uuid.uuid4()), simulation_id=sim_id, role=role,
            name=kw.pop("name", "Agent"), llm_provider="gemini", llm_model="m",
            spawned_at=self.NOW, **kw,
        )

    def turn(self, sim_id: str, agent_id: str, number: int = 0, content: str = "Hello",
             **extra) -> str:
        """Turns live in MongoDB."""
        from datetime import datetime, timezone

        turn_id = str(uuid.uuid4())
        _SYNC_MONGO["turns"].insert_one({
            "id": turn_id, "simulation_id": sim_id, "agent_id": agent_id,
            "turn_number": number, "content": content,
            "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc), **extra,
        })
        return turn_id

    def evidence(self, case_id: str, owner: str = "user-a", **kw) -> str:
        conn = sqlite3.connect(self.path)
        (org_id,) = conn.execute("SELECT org_id FROM cases WHERE id = ?", [case_id]).fetchone()
        conn.close()
        return self._insert(
            "evidence", id=str(uuid.uuid4()), case_id=case_id, title="Exhibit A",
            evidence_type="text", file_path="cases/x/a.txt", mime_type="text/plain",
            uploaded_by=owner, org_id=org_id, created_at=self.NOW, **kw,
        )


@pytest.fixture
def seed(db_path: Path) -> Seeder:
    return Seeder(db_path)
