"""Tamper-evident audit trail for simulations.

Each event stores the hash of the one before it, so editing, deleting or reordering any
past event breaks every hash after it. That does not stop a database administrator from
rewriting the whole chain, but it makes silent edits detectable and lets the head hash be
exported or anchored elsewhere. The database additionally refuses UPDATEs on the table
(see migration 002).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.db.factory import get_repository
from app.models.audit import AuditEvent

GENESIS_HASH = "0" * 64
_MAX_APPEND_ATTEMPTS = 5


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_hash(
    simulation_id: str, seq: int, event_type: str, actor: str,
    payload: dict[str, Any], prev_hash: str,
) -> str:
    canonical = json.dumps(
        {
            "simulation_id": str(simulation_id),
            "seq": seq,
            "event_type": event_type,
            "actor": actor,
            "payload": payload,
            "prev_hash": prev_hash,
        },
        sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str,
    )
    return sha256_text(canonical)


def verify_chain(events: list[AuditEvent]) -> dict[str, Any]:
    """Check linkage, sequence and hash of every event, oldest first."""
    prev = GENESIS_HASH
    for expected_seq, ev in enumerate(events):
        problem = None
        if ev.seq != expected_seq:
            problem = f"expected sequence {expected_seq}, found {ev.seq} (event missing or reordered)"
        elif ev.prev_hash != prev:
            problem = "previous-hash link does not match the preceding event"
        elif ev.hash != compute_hash(
            str(ev.simulation_id), ev.seq, ev.event_type, ev.actor, ev.payload, ev.prev_hash
        ):
            problem = "event content does not match its recorded hash"
        if problem:
            return {"valid": False, "events": len(events), "broken_at": ev.seq,
                    "reason": problem, "head_hash": None}
        prev = ev.hash
    return {"valid": True, "events": len(events), "broken_at": None, "reason": None,
            "head_hash": prev if events else None}


class AuditLog:
    def __init__(self, session: Any) -> None:
        self.session = session
        self.repo = get_repository("audit", session)

    async def _last(self, simulation_id: UUID | str) -> AuditEvent | None:
        items, _ = await self.repo.list(
            filters={"simulation_id": str(simulation_id)}, size=1, order_by="seq DESC"
        )
        return items[0] if items else None

    async def append(
        self, simulation_id: UUID | str, event_type: str, actor: str, payload: dict[str, Any]
    ) -> AuditEvent:
        body = {**payload, "ts": datetime.now(timezone.utc).isoformat()}
        last_error: Exception | None = None
        for _ in range(_MAX_APPEND_ATTEMPTS):
            last = await self._last(simulation_id)
            seq = last.seq + 1 if last else 0
            prev = last.hash if last else GENESIS_HASH
            event = AuditEvent(
                simulation_id=simulation_id,  # type: ignore[arg-type]
                seq=seq, event_type=event_type, actor=actor, payload=body, prev_hash=prev,
                hash=compute_hash(str(simulation_id), seq, event_type, actor, body, prev),
            )
            try:
                return await self.repo.create(event)
            except Exception as exc:  # noqa: BLE001 - unique (simulation_id, seq) race; retry
                last_error = exc
                rollback = getattr(self.session, "rollback", None)
                if rollback:
                    await rollback()
        raise RuntimeError(f"Could not append audit event: {last_error}")

    async def events(self, simulation_id: UUID | str, page: int = 1, size: int = 100) -> tuple[list[AuditEvent], int]:
        return await self.repo.list(
            filters={"simulation_id": str(simulation_id)}, page=page, size=size, order_by="seq"
        )

    async def verify(self, simulation_id: UUID | str) -> dict[str, Any]:
        events: list[AuditEvent] = []
        page = 1
        while True:
            batch, total = await self.events(simulation_id, page=page, size=500)
            events.extend(batch)
            if len(events) >= total or not batch:
                break
            page += 1
        return verify_chain(events)
