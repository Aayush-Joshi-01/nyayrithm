from __future__ import annotations

"""Firm (tenant) models: organizations, members, invites, plans, subscriptions, usage."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


def _now() -> datetime:
    return datetime.now(timezone.utc)


# Firm-level roles. Platform administration is a separate Keycloak realm role.
ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_ATTORNEY = "attorney"
ORG_ROLES = (ROLE_OWNER, ROLE_ADMIN, ROLE_ATTORNEY)


@dataclass
class Organization:
    name: str
    slug: str
    id: UUID = field(default_factory=uuid4)
    status: str = "active"  # active | suspended
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)


@dataclass
class Membership:
    org_id: UUID
    user_id: str  # Keycloak subject
    email: str
    role: str  # owner | admin | attorney
    id: UUID = field(default_factory=uuid4)
    display_name: str = ""
    status: str = "active"  # active | removed
    created_at: datetime = field(default_factory=_now)
    last_seen_at: datetime | None = None


@dataclass
class Invite:
    org_id: UUID
    email: str
    role: str
    token_hash: str  # SHA-256 of the emailed token; the token itself is never stored
    invited_by: str
    expires_at: datetime
    id: UUID = field(default_factory=uuid4)
    status: str = "pending"  # pending | accepted | revoked
    accepted_by: str | None = None
    accepted_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)


@dataclass
class Plan:
    code: str
    name: str
    id: UUID = field(default_factory=uuid4)
    seat_limit: int = 5
    monthly_simulations: int = 50
    monthly_tokens: int = 2_000_000
    max_turns_per_sim: int = 100
    storage_mb: int = 5_000
    features: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=_now)


@dataclass
class Subscription:
    org_id: UUID
    plan_code: str
    id: UUID = field(default_factory=uuid4)
    status: str = "active"  # trialing | active | past_due | cancelled
    seats: int = 5
    current_period_start: datetime = field(default_factory=_now)
    current_period_end: datetime | None = None
    invoice_ref: str = ""
    notes: str = ""
    set_by: str = ""
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)


@dataclass
class CaseMember:
    """An attorney a case has been shared with (owners/admins see every case anyway)."""

    case_id: UUID
    user_id: str
    added_by: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=_now)


@dataclass
class UsageCounter:
    org_id: UUID
    period: str  # YYYY-MM
    id: UUID = field(default_factory=uuid4)
    tokens: int = 0
    cost_usd: float = 0.0
    simulations: int = 0
    turns: int = 0
    updated_at: datetime = field(default_factory=_now)


@dataclass
class AdminEvent:
    actor: str
    action: str
    target_type: str = ""
    target_id: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=_now)
