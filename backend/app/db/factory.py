from __future__ import annotations

from app.db.repositories import MONGO_REPOSITORIES, PG_REPOSITORIES
from app.db.repository_base import BaseRepository
from app.db.stores import Stores


def get_repository(model: str, stores: Stores) -> BaseRepository:
    """The repository for ``model``, bound to the store that model lives in.

    PostgreSQL: organization, membership, invite, plan, subscription, case_member,
    usage_counter, admin_event, case, simulation, agent, evidence, audit.
    MongoDB: turn, evidence_content, llm_usage, llm_price.
    """
    if model in PG_REPOSITORIES:
        return PG_REPOSITORIES[model](stores.pg)
    if model in MONGO_REPOSITORIES:
        return MONGO_REPOSITORIES[model](stores.mongo)
    raise KeyError(f"Unknown model '{model}'")
