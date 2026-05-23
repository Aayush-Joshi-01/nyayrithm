from __future__ import annotations

import asyncio

import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.simulation_tasks.run_simulation_turn", bind=True)
def run_simulation_turn(self, simulation_id: str):
    """Runs a single simulation turn in the background."""
    # Clear cached engine/session-factory so asyncio.run()'s fresh event loop
    # gets its own asyncpg connection pool — reusing a pool from a closed loop
    # raises "Future attached to a different loop".
    from app.db.session import _make_engine, _make_session_factory
    _make_engine.cache_clear()
    _make_session_factory.cache_clear()
    asyncio.run(_run_turn_async(simulation_id))


async def _run_turn_async(simulation_id: str) -> None:
    from app.simulation.engine import SimulationEngine
    engine = SimulationEngine()
    await engine.run_next_turn(simulation_id)
