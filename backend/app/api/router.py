from fastapi import APIRouter

from app.api.v1 import health, cases, evidence, simulations, agents, turns

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(evidence.router, tags=["evidence"])
api_router.include_router(simulations.router, tags=["simulations"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(turns.router, tags=["turns"])
