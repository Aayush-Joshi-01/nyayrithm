"""Firms (tenancy), plans, usage; turns and evidence text move to MongoDB

Revision ID: 003
Revises: 002
Create Date: 2026-10-03

Local data was reset when this landed, so there is no backfill: new columns are nullable
and the dev seeder (or an admin) creates firms.
"""
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Turns and extracted evidence text are documents: they live in MongoDB now ──
    op.execute("DROP TABLE IF EXISTS turns CASCADE")
    op.execute("ALTER TABLE evidence DROP COLUMN IF EXISTS raw_text")
    op.execute("ALTER TABLE evidence DROP COLUMN IF EXISTS transcription")

    # ── Tenancy ──
    op.execute("""
    CREATE TABLE IF NOT EXISTS organizations (
        id          UUID PRIMARY KEY,
        name        TEXT NOT NULL,
        slug        TEXT NOT NULL UNIQUE,
        status      TEXT NOT NULL DEFAULT 'active',
        created_at  TIMESTAMPTZ DEFAULT NOW(),
        updated_at  TIMESTAMPTZ DEFAULT NOW()
    )
    """)
    op.execute("""
    CREATE TABLE IF NOT EXISTS memberships (
        id            UUID PRIMARY KEY,
        org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        user_id       TEXT NOT NULL,
        email         TEXT NOT NULL,
        role          TEXT NOT NULL,
        display_name  TEXT NOT NULL DEFAULT '',
        status        TEXT NOT NULL DEFAULT 'active',
        created_at    TIMESTAMPTZ DEFAULT NOW(),
        last_seen_at  TIMESTAMPTZ,
        UNIQUE (org_id, user_id)
    )
    """)
    op.execute("""
    CREATE TABLE IF NOT EXISTS invites (
        id           UUID PRIMARY KEY,
        org_id       UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        email        TEXT NOT NULL,
        role         TEXT NOT NULL,
        token_hash   TEXT NOT NULL UNIQUE,
        invited_by   TEXT NOT NULL,
        expires_at   TIMESTAMPTZ NOT NULL,
        status       TEXT NOT NULL DEFAULT 'pending',
        accepted_by  TEXT,
        accepted_at  TIMESTAMPTZ,
        created_at   TIMESTAMPTZ DEFAULT NOW()
    )
    """)
    op.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        id                  UUID PRIMARY KEY,
        code                TEXT NOT NULL UNIQUE,
        name                TEXT NOT NULL,
        seat_limit          INT NOT NULL DEFAULT 5,
        monthly_simulations INT NOT NULL DEFAULT 50,
        monthly_tokens      BIGINT NOT NULL DEFAULT 2000000,
        max_turns_per_sim   INT NOT NULL DEFAULT 100,
        storage_mb          INT NOT NULL DEFAULT 5000,
        features            JSONB NOT NULL DEFAULT '{}',
        is_active           BOOLEAN NOT NULL DEFAULT TRUE,
        created_at          TIMESTAMPTZ DEFAULT NOW()
    )
    """)
    op.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id                   UUID PRIMARY KEY,
        org_id               UUID NOT NULL UNIQUE REFERENCES organizations(id) ON DELETE CASCADE,
        plan_code            TEXT NOT NULL,
        status               TEXT NOT NULL DEFAULT 'active',
        seats                INT NOT NULL DEFAULT 5,
        current_period_start TIMESTAMPTZ DEFAULT NOW(),
        current_period_end   TIMESTAMPTZ,
        invoice_ref          TEXT NOT NULL DEFAULT '',
        notes                TEXT NOT NULL DEFAULT '',
        set_by               TEXT NOT NULL DEFAULT '',
        created_at           TIMESTAMPTZ DEFAULT NOW(),
        updated_at           TIMESTAMPTZ DEFAULT NOW()
    )
    """)
    op.execute("""
    CREATE TABLE IF NOT EXISTS case_members (
        id         UUID PRIMARY KEY,
        case_id    UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        user_id    TEXT NOT NULL,
        added_by   TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE (case_id, user_id)
    )
    """)
    op.execute("""
    CREATE TABLE IF NOT EXISTS usage_counters (
        id          UUID PRIMARY KEY,
        org_id      UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        period      TEXT NOT NULL,
        tokens      BIGINT NOT NULL DEFAULT 0,
        cost_usd    DOUBLE PRECISION NOT NULL DEFAULT 0,
        simulations INT NOT NULL DEFAULT 0,
        turns       INT NOT NULL DEFAULT 0,
        updated_at  TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE (org_id, period)
    )
    """)
    op.execute("""
    CREATE TABLE IF NOT EXISTS admin_events (
        id          UUID PRIMARY KEY,
        actor       TEXT NOT NULL,
        action      TEXT NOT NULL,
        target_type TEXT NOT NULL DEFAULT '',
        target_id   TEXT NOT NULL DEFAULT '',
        details     JSONB NOT NULL DEFAULT '{}',
        created_at  TIMESTAMPTZ DEFAULT NOW()
    )
    """)

    for table in ("cases", "simulations", "evidence"):
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES organizations(id)")
        op.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_org ON {table}(org_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_memberships_user ON memberships(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_invites_email ON invites(lower(email))")
    op.execute("CREATE INDEX IF NOT EXISTS idx_admin_events_created ON admin_events(created_at DESC)")


def downgrade() -> None:
    for table in ("cases", "simulations", "evidence"):
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS org_id")
    for table in ("admin_events", "usage_counters", "case_members", "subscriptions", "plans",
                  "invites", "memberships", "organizations"):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    op.execute("ALTER TABLE evidence ADD COLUMN IF NOT EXISTS raw_text TEXT")
    op.execute("ALTER TABLE evidence ADD COLUMN IF NOT EXISTS transcription TEXT")
