from __future__ import annotations

from app.db.adapters.postgres import PostgresRepository
from app.db.adapters.mongodb import MongoRepository
from app.models.turn import Turn


class TurnPostgresRepository(PostgresRepository[Turn]):
    table_name = "turns"
    model_cls = Turn


class TurnMongoRepository(MongoRepository[Turn]):
    collection_name = "turns"
    model_cls = Turn
