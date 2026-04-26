from __future__ import annotations

import dataclasses
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.factory import get_repository
from app.db.session import get_session
from app.schemas.turn import TurnEditRequest, TurnListResponse, TurnResponse

router = APIRouter()


async def _turn_repo(session=Depends(get_session)):
    return get_repository("turn", session)


@router.get("/simulations/{sim_id}/turns", response_model=TurnListResponse)
async def list_turns(
    sim_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(50, le=200),
    repo=Depends(_turn_repo),
):
    items, total = await repo.list(
        filters={"simulation_id": sim_id},
        page=page, size=size,
        order_by="turn_number",
    )
    return TurnListResponse(
        items=[TurnResponse(**dataclasses.asdict(t)) for t in items],
        total=total, page=page, size=size,
    )


@router.patch("/simulations/{sim_id}/turns/{turn_id}", response_model=TurnResponse)
async def edit_turn(sim_id: str, turn_id: str, body: TurnEditRequest, repo=Depends(_turn_repo)):
    turn = await repo.get(turn_id)
    if not turn or str(turn.simulation_id) != sim_id:
        raise HTTPException(status_code=404, detail="Turn not found")
    updated = await repo.update(turn_id, {
        "content_edited": body.content,
        "is_human_override": True,
    })
    return TurnResponse(**dataclasses.asdict(updated))
