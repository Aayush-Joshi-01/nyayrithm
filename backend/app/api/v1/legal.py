from __future__ import annotations

import dataclasses
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import get_access
from app.core.auth import AuthenticatedUser
from app.dependencies import get_current_user
from app.legal.audit import AuditLog
from app.legal.corpus import get_corpus
from app.legal.disclaimer import DISCLAIMER
from app.legal.procedure import ProcedureEngine
from app.legal.review import LegalReviewer
from app.services.access import AccessService

router = APIRouter()


class VerifyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20_000)
    case_id: UUID | None = None
    country: str | None = None
    jurisdiction: str | None = None


# ── jurisdiction packs & citation checking ────────────────────────────────────
@router.get("/legal/disclaimer")
async def disclaimer():
    return {"disclaimer": DISCLAIMER}


@router.get("/legal/jurisdictions")
async def list_jurisdictions(_: AuthenticatedUser = Depends(get_current_user)):
    return {"jurisdictions": get_corpus().list(), "disclaimer": DISCLAIMER}


@router.get("/legal/provisions")
async def search_provisions(
    q: str = Query(..., min_length=2, max_length=300),
    jurisdiction: str = "IN",
    limit: int = Query(8, ge=1, le=25),
    _: AuthenticatedUser = Depends(get_current_user),
):
    pack = get_corpus().get(jurisdiction)
    if pack is None:
        raise HTTPException(status_code=404, detail=f"No jurisdiction pack '{jurisdiction}'")
    return {
        "jurisdiction": pack.id,
        "pack_status": pack.status,
        "notice": pack.notice,
        "provisions": [dataclasses.asdict(p) for p in pack.search(q, limit=limit)],
        "cases": [dataclasses.asdict(c) for c in pack.search_cases(q, limit=3)],
    }


@router.post("/legal/verify")
async def verify_citations(body: VerifyRequest, access: AccessService = Depends(get_access)):
    """Check the legal citations in any text against the jurisdiction pack."""
    country, jurisdiction = body.country, body.jurisdiction
    if body.case_id is not None:
        case = await access.case(body.case_id)
        country, jurisdiction = case.country, case.jurisdiction
    reviewer = LegalReviewer()
    result = reviewer.review(body.text, country, jurisdiction).to_dict()
    pack = reviewer.pack_for(country, jurisdiction)
    result["pack_status"] = pack.status if pack else None
    result["notice"] = pack.notice if pack else (
        "No jurisdiction pack is available for this country, so citations cannot be checked."
    )
    result["disclaimer"] = DISCLAIMER
    return result


# ── per-simulation: audit trail and procedure ─────────────────────────────────
@router.get("/simulations/{sim_id}/audit")
async def list_audit_events(
    sim_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=500),
    access: AccessService = Depends(get_access),
):
    await access.simulation(sim_id)
    events, total = await AuditLog(access.session).events(sim_id, page=page, size=size)
    return {
        "items": [
            {
                "seq": e.seq, "event_type": e.event_type, "actor": e.actor,
                "payload": e.payload, "prev_hash": e.prev_hash, "hash": e.hash,
                "created_at": e.created_at,
            }
            for e in events
        ],
        "total": total, "page": page, "size": size,
    }


@router.get("/simulations/{sim_id}/audit/verify")
async def verify_audit_chain(sim_id: UUID, access: AccessService = Depends(get_access)):
    await access.simulation(sim_id)
    return await AuditLog(access.session).verify(sim_id)


@router.get("/simulations/{sim_id}/procedure")
async def get_procedure(sim_id: UUID, access: AccessService = Depends(get_access)):
    sim = await access.simulation(sim_id)
    case = await access.case(sim.case_id)
    pack = LegalReviewer().pack_for(case.country, case.jurisdiction)

    enforced = bool(sim.config.get("enforce_procedure", True))
    engine = ProcedureEngine.for_mode(
        sim.mode, sim.max_turns, pack.procedure_notes if pack else None
    ) if enforced else None
    if engine is None:
        return {"enforced": False, "mode": sim.mode, "stages": [], "current_stage": None}

    current = engine.slot(sim.current_turn).stage
    return {
        "enforced": True,
        "mode": sim.mode,
        "stages": engine.plan(),
        "current_stage": current.key,
        "current_turn": sim.current_turn,
    }
