from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import structlog

from app.tasks.celery_app import celery_app
from app.tasks.loop_utils import clear_loop_bound_caches as _clear_loop_bound_caches

logger = structlog.get_logger()


@celery_app.task(
    name="app.tasks.simulation_tasks.run_simulation",
    bind=True,
    acks_late=False,
    max_retries=0,
)
def run_simulation(self, simulation_id: str):
    """Run a full simulation to completion in the background."""
    _clear_loop_bound_caches()
    asyncio.run(_run_async(simulation_id))


# Backwards-compatible alias (older callers / docs referenced this name).
run_simulation_turn = run_simulation


async def _run_async(simulation_id: str) -> None:
    from app.api.websockets.event_bus import make_broadcast_fn
    from app.db.factory import get_repository
    from app.db.session import get_session
    from app.simulation.engine import SimulationEngine

    broadcast_fn = make_broadcast_fn(simulation_id)
    engine = SimulationEngine()
    try:
        await engine.run_simulation(simulation_id, broadcast_fn=broadcast_fn)
    except Exception as exc:
        logger.error("simulation_run_failed", simulation_id=simulation_id, error=str(exc))
        async for session in get_session():
            sim_repo = get_repository("simulation", session)
            await sim_repo.update(simulation_id, {
                "status": "failed",
                "ended_at": datetime.now(timezone.utc),
            })
        await broadcast_fn("error", {"message": f"Simulation failed: {exc}"})
        await broadcast_fn("simulation.completed", {
            "simulation_id": simulation_id, "total_turns": 0,
        })
