from __future__ import annotations

import asyncio

import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="app.tasks.simulation_tasks.run_simulation_turn", bind=True)
def run_simulation_turn(self, simulation_id: str):
    """Runs a single simulation turn in the background."""
    asyncio.run(_run_turn_async(simulation_id))


async def _run_turn_async(simulation_id: str) -> None:
    from app.simulation.engine import SimulationEngine
    engine = SimulationEngine()
    await engine.run_next_turn(simulation_id)
