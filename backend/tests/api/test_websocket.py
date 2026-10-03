from __future__ import annotations

import asyncio

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


@pytest.fixture
def no_redis(monkeypatch):
    """The socket handler subscribes to Redis; keep it idle instead of connecting."""
    async def idle(_sim_id):
        await asyncio.Event().wait()
        yield {}

    monkeypatch.setattr("app.api.websockets.simulation_ws.subscribe", idle)


@pytest.fixture
def sim(seed) -> str:
    return seed.simulation(seed.case("user-a"), "user-a")


def connect(app, sim_id: str, token: str | None):
    client = TestClient(app)
    suffix = f"?token={token}" if token else ""
    return client.websocket_connect(f"/ws/simulations/{sim_id}{suffix}")


def test_owner_with_a_valid_token_is_connected(app, no_redis, sim, keycloak):
    with connect(app, sim, keycloak.token("user-a")) as ws:
        frame = ws.receive_json()
        assert frame == {"event": "connected", "data": {"simulation_id": sim}}


def test_missing_token_is_closed_with_4401(app, no_redis, sim):
    with pytest.raises(WebSocketDisconnect) as exc, connect(app, sim, None) as ws:
        ws.receive_json()
    assert exc.value.code == 4401


def test_garbage_token_is_closed_with_4401(app, no_redis, sim):
    with pytest.raises(WebSocketDisconnect) as exc, connect(app, sim, "garbage") as ws:
        ws.receive_json()
    assert exc.value.code == 4401


def test_expired_token_is_closed_with_4401(app, no_redis, sim, keycloak):
    with pytest.raises(WebSocketDisconnect) as exc, \
            connect(app, sim, keycloak.token("user-a", expires_in=-600)) as ws:
        ws.receive_json()
    assert exc.value.code == 4401


def test_other_users_simulation_is_closed_with_4403(app, no_redis, sim, keycloak):
    with pytest.raises(WebSocketDisconnect) as exc, \
            connect(app, sim, keycloak.token("user-b")) as ws:
        ws.receive_json()
    assert exc.value.code == 4403


def test_unknown_or_malformed_simulation_is_closed_with_4403(app, no_redis, keycloak):
    for sim_id in ("6f1c3a3e-0000-4000-8000-000000000000", "not-a-uuid"):
        with pytest.raises(WebSocketDisconnect) as exc, \
                connect(app, sim_id, keycloak.token("user-a")) as ws:
            ws.receive_json()
        assert exc.value.code == 4403


def test_ping_gets_a_pong(app, no_redis, sim, keycloak):
    with connect(app, sim, keycloak.token("user-a")) as ws:
        ws.receive_json()
        ws.send_json({"type": "ping"})
        assert ws.receive_json() == {"event": "pong"}
