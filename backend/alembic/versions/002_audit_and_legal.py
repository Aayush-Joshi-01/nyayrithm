"""Audit trail for simulations

Revision ID: 002
Revises: 001
Create Date: 2026-10-03
"""
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS audit_events (
        id            UUID PRIMARY KEY,
        simulation_id UUID NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
        seq           INT NOT NULL,
        event_type    TEXT NOT NULL,
        actor         TEXT NOT NULL DEFAULT '',
        payload       JSONB NOT NULL DEFAULT '{}',
        prev_hash     TEXT NOT NULL,
        hash          TEXT NOT NULL,
        created_at    TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE (simulation_id, seq)
    )
    """)

    # Append-only: an event may be removed with its simulation, but never rewritten.
    op.execute("""
    CREATE OR REPLACE FUNCTION audit_events_reject_update() RETURNS trigger AS $$
    BEGIN
        RAISE EXCEPTION 'audit_events rows are immutable';
    END;
    $$ LANGUAGE plpgsql
    """)
    op.execute("DROP TRIGGER IF EXISTS audit_events_no_update ON audit_events")
    op.execute("""
    CREATE TRIGGER audit_events_no_update
        BEFORE UPDATE ON audit_events
        FOR EACH ROW EXECUTE FUNCTION audit_events_reject_update()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_events_no_update ON audit_events")
    op.execute("DROP FUNCTION IF EXISTS audit_events_reject_update()")
    op.execute("DROP TABLE IF EXISTS audit_events")
