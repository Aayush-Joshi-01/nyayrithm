from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.db.repository_base import BaseRepository


def get_repository(model: str, session: Any) -> BaseRepository:
    """
    Factory that returns the correct repository adapter for the configured DB backend.

    Args:
        model: one of "case", "evidence", "agent", "simulation", "turn"
        session: AsyncSession (SQL) or AsyncIOMotorDatabase (Mongo)
    """
    settings = get_settings()
    backend = settings.DB_BACKEND

    from app.db.repositories.case_repo import CasePostgresRepository, CaseMongoRepository
    from app.db.repositories.evidence_repo import EvidencePostgresRepository, EvidenceMongoRepository
    from app.db.repositories.agent_repo import AgentPostgresRepository, AgentMongoRepository
    from app.db.repositories.simulation_repo import SimulationPostgresRepository, SimulationMongoRepository
    from app.db.repositories.turn_repo import TurnPostgresRepository, TurnMongoRepository

    SQL_MAP = {
        "case": CasePostgresRepository,
        "evidence": EvidencePostgresRepository,
        "agent": AgentPostgresRepository,
        "simulation": SimulationPostgresRepository,
        "turn": TurnPostgresRepository,
    }
    MONGO_MAP = {
        "case": CaseMongoRepository,
        "evidence": EvidenceMongoRepository,
        "agent": AgentMongoRepository,
        "simulation": SimulationMongoRepository,
        "turn": TurnMongoRepository,
    }

    if backend in ("postgres", "sqlite"):
        cls = SQL_MAP[model]
    elif backend == "mongodb":
        cls = MONGO_MAP[model]
    else:
        raise NotImplementedError(f"DB backend '{backend}' not yet supported for model '{model}'")

    return cls(session)
