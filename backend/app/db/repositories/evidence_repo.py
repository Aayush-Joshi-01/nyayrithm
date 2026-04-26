from __future__ import annotations

from app.db.adapters.postgres import PostgresRepository
from app.db.adapters.mongodb import MongoRepository
from app.models.evidence import Evidence


class EvidencePostgresRepository(PostgresRepository[Evidence]):
    table_name = "evidence"
    model_cls = Evidence


class EvidenceMongoRepository(MongoRepository[Evidence]):
    collection_name = "evidence"
    model_cls = Evidence
