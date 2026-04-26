from __future__ import annotations

from app.db.adapters.postgres import PostgresRepository
from app.db.adapters.mongodb import MongoRepository
from app.models.case import Case


class CasePostgresRepository(PostgresRepository[Case]):
    table_name = "cases"
    model_cls = Case


class CaseMongoRepository(MongoRepository[Case]):
    collection_name = "cases"
    model_cls = Case
