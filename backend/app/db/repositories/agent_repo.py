from __future__ import annotations

from app.db.adapters.postgres import PostgresRepository
from app.db.adapters.mongodb import MongoRepository
from app.models.agent import AgentDefinition


class AgentPostgresRepository(PostgresRepository[AgentDefinition]):
    table_name = "agent_definitions"
    model_cls = AgentDefinition


class AgentMongoRepository(MongoRepository[AgentDefinition]):
    collection_name = "agent_definitions"
    model_cls = AgentDefinition
