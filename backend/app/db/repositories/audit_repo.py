from __future__ import annotations

from app.db.adapters.mongodb import MongoRepository
from app.db.adapters.postgres import PostgresRepository
from app.models.audit import AuditEvent


class AuditPostgresRepository(PostgresRepository[AuditEvent]):
    table_name = "audit_events"
    model_cls = AuditEvent


class AuditMongoRepository(MongoRepository[AuditEvent]):
    collection_name = "audit_events"
    model_cls = AuditEvent
