from __future__ import annotations

import asyncio
import json
from typing import Any

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = structlog.get_logger()

websocket_router = APIRouter()

# In-memory connection registry: sim_id -> list of WebSocket connections
_connections: dict[str, list[WebSocket]] = {}


async def broadcast(simulation_id: str, event_type: str, payload: dict[str, Any]) -> None:
    """Broadcast a structured event to all subscribers of a simulation."""
    conns = _connections.get(simulation_id, [])
    if not conns:
        return
    message = json.dumps({"event": event_type, "data": payload})
    dead = []
    for ws in conns:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        conns.remove(ws)


def make_broadcast_fn(simulation_id: str):
    async def _broadcast(event_type: str, payload: dict) -> None:
        await broadcast(simulation_id, event_type, payload)
    return _broadcast


@websocket_router.websocket("/ws/simulations/{simulation_id}")
async def simulation_websocket(websocket: WebSocket, simulation_id: str):
    await websocket.accept()
    _connections.setdefault(simulation_id, []).append(websocket)
    logger.info("ws_connected", simulation_id=simulation_id)

    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "event": "connected",
            "data": {"simulation_id": simulation_id},
        }))

        # Keep alive — client may send control messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                msg = json.loads(data)

                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"event": "pong"}))

            except asyncio.TimeoutError:
                # Send keepalive ping
                await websocket.send_text(json.dumps({"event": "ping"}))

    except WebSocketDisconnect:
        logger.info("ws_disconnected", simulation_id=simulation_id)
    except Exception as exc:
        logger.error("ws_error", error=str(exc))
    finally:
        conns = _connections.get(simulation_id, [])
        if websocket in conns:
            conns.remove(websocket)
