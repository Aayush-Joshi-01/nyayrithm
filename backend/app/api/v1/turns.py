from __future__ import annotations

import dataclasses
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access
from app.core.exceptions import NotFoundError
from app.db.factory import get_repository
from app.legal.audit import AuditLog, sha256_text
from app.schemas.turn import TurnEditRequest, TurnListResponse, TurnResponse
from app.services.access import AccessService

router = APIRouter()


def _out(turn) -> TurnResponse:
    data = dataclasses.asdict(turn)
    meta = data.get("metadata") or {}
    return TurnResponse(
        **data, legal_review=meta.get("legal_review"), procedure=meta.get("procedure")
    )


@router.get("/simulations/{sim_id}/turns", response_model=TurnListResponse)
async def list_turns(
    sim_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    access: AccessService = Depends(get_access),
):
    await access.simulation(sim_id)
    repo = get_repository("turn", access.session)
    items, total = await repo.list(
        filters={"simulation_id": str(sim_id)}, page=page, size=size, order_by="turn_number"
    )
    return TurnListResponse(items=[_out(t) for t in items], total=total, page=page, size=size)


@router.patch("/simulations/{sim_id}/turns/{turn_id}", response_model=TurnResponse)
async def edit_turn(
    sim_id: UUID,
    turn_id: UUID,
    body: TurnEditRequest,
    access: AccessService = Depends(get_access),
):
    await access.simulation(sim_id)
    repo = get_repository("turn", access.session)
    turn = await repo.get(str(turn_id))
    if not turn or str(turn.simulation_id) != str(sim_id):
        raise NotFoundError("Turn", str(turn_id))
    updated = await repo.update(str(turn_id), {
        "content_edited": body.content,
        "is_human_override": True,
    })
    # Human edits are the one way the record can diverge from what the agent said, so the
    # audit trail keeps both versions' hashes.
    await AuditLog(access.session).append(sim_id, "turn.edited", f"user:{access.user.id}", {
        "turn_id": str(turn_id),
        "turn_number": turn.turn_number,
        "original_sha256": sha256_text(turn.content_edited or turn.content),
        "edited_sha256": sha256_text(body.content),
    })
    return _out(updated)
