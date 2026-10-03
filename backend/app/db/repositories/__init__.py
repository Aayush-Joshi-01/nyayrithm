from __future__ import annotations

"""One repository class per model. Which store a model lives in is decided here."""

from app.db.adapters.mongodb import MongoRepository
from app.db.adapters.postgres import PostgresRepository
from app.models.agent import AgentDefinition
from app.models.audit import AuditEvent
from app.models.case import Case
from app.models.documents import EvidenceContent, LlmPrice, LlmUsage
from app.models.evidence import Evidence
from app.models.simulation import Simulation
from app.models.tenancy import (
    AdminEvent,
    CaseMember,
    Invite,
    Membership,
    Organization,
    Plan,
    Subscription,
    UsageCounter,
)
from app.models.turn import Turn


def _pg(name: str, table: str, model: type) -> type:
    return type(name, (PostgresRepository,), {"table_name": table, "model_cls": model})


def _mongo(name: str, collection: str, model: type) -> type:
    return type(name, (MongoRepository,), {"collection_name": collection, "model_cls": model})


# PostgreSQL: relational and transactional
PG_REPOSITORIES: dict[str, type] = {
    "organization": _pg("OrganizationRepository", "organizations", Organization),
    "membership": _pg("MembershipRepository", "memberships", Membership),
    "invite": _pg("InviteRepository", "invites", Invite),
    "plan": _pg("PlanRepository", "plans", Plan),
    "subscription": _pg("SubscriptionRepository", "subscriptions", Subscription),
    "case_member": _pg("CaseMemberRepository", "case_members", CaseMember),
    "usage_counter": _pg("UsageCounterRepository", "usage_counters", UsageCounter),
    "admin_event": _pg("AdminEventRepository", "admin_events", AdminEvent),
    "case": _pg("CaseRepository", "cases", Case),
    "simulation": _pg("SimulationRepository", "simulations", Simulation),
    "agent": _pg("AgentRepository", "agent_definitions", AgentDefinition),
    "evidence": _pg("EvidenceRepository", "evidence", Evidence),
    "audit": _pg("AuditRepository", "audit_events", AuditEvent),
}

# MongoDB: documents and high-volume events
MONGO_REPOSITORIES: dict[str, type] = {
    "turn": _mongo("TurnRepository", "turns", Turn),
    "evidence_content": _mongo("EvidenceContentRepository", "evidence_content", EvidenceContent),
    "llm_usage": _mongo("LlmUsageRepository", "llm_usage", LlmUsage),
    "llm_price": _mongo("LlmPriceRepository", "llm_prices", LlmPrice),
}
