from __future__ import annotations

import asyncio
import json

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.websockets.event_bus import make_broadcast_fn, subscribe

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


@websocket_router.websocket("/ws/simulations/{simulation_id}")
async def simulation_websocket(websocket: WebSocket, simulation_id: str):
    await websocket.accept()
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
