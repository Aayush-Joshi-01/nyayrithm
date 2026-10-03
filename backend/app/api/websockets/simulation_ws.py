from __future__ import annotations

import asyncio
import json
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.api.websockets.event_bus import make_broadcast_fn, subscribe
from app.core.auth import get_verifier
from app.core.exceptions import ForbiddenError, NotFoundError
from app.db.stores import open_stores
from app.dependencies import authenticate_token
from app.services.access import AccessService
from app.services.orgs import resolve_org_user

logger = structlog.get_logger()

websocket_router = APIRouter()

# Re-exported so existing imports (`from ...simulation_ws import make_broadcast_fn`)
# keep working — the implementation now lives in event_bus and goes over Redis so
# it bridges the uvicorn <-> Celery-worker process boundary.
__all__ = ["websocket_router", "make_broadcast_fn"]


async def _pump_events(websocket: WebSocket, simulation_id: str) -> None:
    """Forward every Redis event for this simulation to one browser socket."""
    async for frame in subscribe(simulation_id):
        await websocket.send_text(json.dumps(frame))


# Close codes (4000-4999 are application-defined).
WS_UNAUTHORIZED = 4401
WS_FORBIDDEN = 4403


async def _authorize(websocket: WebSocket, simulation_id: str) -> int | None:
    """Return a close code if the socket may not watch this simulation, else None.

    Browsers cannot set an Authorization header on a WebSocket, so the access token
    comes in the ``token`` query parameter.
    """
    try:
        user = await authenticate_token(
            websocket.query_params.get("token"), get_verifier()
        )
    except HTTPException:
        return WS_UNAUTHORIZED

    try:
        UUID(simulation_id)
    except ValueError:
        return WS_FORBIDDEN

    try:
        async with open_stores() as stores:
            org_user = await resolve_org_user(stores, user, websocket.query_params.get("org"))
            await AccessService(stores, org_user).simulation(simulation_id)
    except (NotFoundError, ForbiddenError):
        return WS_FORBIDDEN
    return None


@websocket_router.websocket("/ws/simulations/{simulation_id}")
async def simulation_websocket(websocket: WebSocket, simulation_id: str):
    await websocket.accept()
    denied = await _authorize(websocket, simulation_id)
    if denied is not None:
        await websocket.close(code=denied)
        return
    logger.info("ws_connected", simulation_id=simulation_id)

    pump = asyncio.create_task(_pump_events(websocket, simulation_id))

    try:
        await websocket.send_text(json.dumps({
            "event": "connected",
            "data": {"simulation_id": simulation_id},
        }))

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"event": "pong"}))
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"event": "ping"}))

    except WebSocketDisconnect:
        logger.info("ws_disconnected", simulation_id=simulation_id)
    except Exception as exc:
        logger.error("ws_error", error=str(exc))
    finally:
        pump.cancel()
        try:
            await pump
        except (asyncio.CancelledError, Exception):
            pass
