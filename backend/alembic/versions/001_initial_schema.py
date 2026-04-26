"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id              UUID PRIMARY KEY,
        title           TEXT NOT NULL,
        description     TEXT DEFAULT '',
        country         TEXT NOT NULL,
        jurisdiction    TEXT DEFAULT '',
        legal_system    TEXT DEFAULT 'common_law',
        status          TEXT DEFAULT 'open',
        created_by      TEXT NOT NULL,
        metadata        JSONB DEFAULT '{}',
        created_at      TIMESTAMPTZ DEFAULT NOW(),
        updated_at      TIMESTAMPTZ DEFAULT NOW()
    )
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS evidence (
        id                  UUID PRIMARY KEY,
        case_id             UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        title               TEXT NOT NULL,
        description         TEXT DEFAULT '',
        evidence_type       TEXT NOT NULL,
        file_path           TEXT NOT NULL,
        file_size           BIGINT DEFAULT 0,
        mime_type           TEXT NOT NULL,
        modality            TEXT DEFAULT 'text',
        raw_text            TEXT,
        transcription       TEXT,
        embedder_used       TEXT,
        metadata            JSONB DEFAULT '{}',
        status              TEXT DEFAULT 'pending',
        linked_participants JSONB DEFAULT '[]',
        vector_collection   TEXT,
        chunk_count         INT DEFAULT 0,
        tags                JSONB DEFAULT '[]',
        error_message       TEXT,
        indexed_at          TIMESTAMPTZ,
        uploaded_by         TEXT NOT NULL,
        created_at          TIMESTAMPTZ DEFAULT NOW()
    )
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS simulations (
        id              UUID PRIMARY KEY,
        case_id         UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        title           TEXT NOT NULL,
        mode            TEXT DEFAULT 'courtroom',
        status          TEXT DEFAULT 'draft',
        current_turn    INT DEFAULT 0,
        max_turns       INT DEFAULT 50,
        turn_order      JSONB DEFAULT '[]',
        config          JSONB DEFAULT '{}',
        started_at      TIMESTAMPTZ,
        ended_at        TIMESTAMPTZ,
        created_by      TEXT NOT NULL,
        created_at      TIMESTAMPTZ DEFAULT NOW(),
        updated_at      TIMESTAMPTZ DEFAULT NOW()
    )
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS agent_definitions (
        id                   UUID PRIMARY KEY,
        simulation_id        UUID NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
        parent_agent_id      UUID REFERENCES agent_definitions(id),
        spawn_reason         TEXT,
        is_predefined        BOOLEAN DEFAULT TRUE,
        role                 TEXT NOT NULL,
        name                 TEXT NOT NULL,
        persona              JSONB DEFAULT '{}',
        llm_provider         TEXT NOT NULL,
        llm_model            TEXT NOT NULL,
        system_prompt        TEXT DEFAULT '',
        knowledge_scope      JSONB DEFAULT '{}',
        jurisdiction_context JSONB DEFAULT '{}',
        status               TEXT DEFAULT 'active',
        initial_instruction  TEXT,
        spawned_at           TIMESTAMPTZ DEFAULT NOW()
    )
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS turns (
        id               UUID PRIMARY KEY,
        simulation_id    UUID NOT NULL REFERENCES simulations(id) ON DELETE CASCADE,
        agent_id         UUID NOT NULL REFERENCES agent_definitions(id),
        turn_number      INT NOT NULL,
        content          TEXT NOT NULL,
        content_edited   TEXT,
        reasoning_trace  JSONB DEFAULT '{}',
        citations        JSONB DEFAULT '[]',
        retrieved_chunks JSONB DEFAULT '[]',
        spawned_agents   JSONB DEFAULT '[]',
        is_human_override BOOLEAN DEFAULT FALSE,
        token_count      INT DEFAULT 0,
        latency_ms       INT DEFAULT 0,
        metadata         JSONB DEFAULT '{}',
        created_at       TIMESTAMPTZ DEFAULT NOW()
    )
    """)

    # Indices
    op.execute("CREATE INDEX IF NOT EXISTS idx_evidence_case ON evidence(case_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_simulations_case ON simulations(case_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_agents_simulation ON agent_definitions(simulation_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_turns_simulation ON turns(simulation_id, turn_number)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS turns CASCADE")
    op.execute("DROP TABLE IF EXISTS agent_definitions CASCADE")
    op.execute("DROP TABLE IF EXISTS simulations CASCADE")
    op.execute("DROP TABLE IF EXISTS evidence CASCADE")
    op.execute("DROP TABLE IF EXISTS cases CASCADE")
