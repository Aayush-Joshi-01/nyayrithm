from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.auth import AuthenticatedUser
from app.core.exceptions import NotFoundError
from app.db.factory import get_repository
from app.db.stores import Stores
from app.models.agent import AgentDefinition
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.simulation import Simulation


class AccessService:
    """Resolves resources on behalf of a user and enforces ownership.

    A case belongs to the user who created it; simulations, evidence, agents and
    turns inherit access from their case. Anything the user does not own is reported
    as *not found* (404) rather than forbidden, so ids cannot be probed.
    """

    def __init__(self, stores: Stores, user: AuthenticatedUser) -> None:
        self.stores = stores
        self.user = user

    def _repo(self, model: str):
        return get_repository(model, self.stores)

    def _can_see(self, case: Case) -> bool:
        return self.user.is_admin or case.created_by == self.user.id

    async def case(self, case_id: UUID | str) -> Case:
        case = await self._repo("case").get(str(case_id))
        if case is None or not self._can_see(case):
            raise NotFoundError("Case", str(case_id))
        return case

    async def simulation(self, sim_id: UUID | str) -> Simulation:
        sim = await self._repo("simulation").get(str(sim_id))
        if sim is None:
            raise NotFoundError("Simulation", str(sim_id))
        try:
            await self.case(sim.case_id)
        except NotFoundError:
            raise NotFoundError("Simulation", str(sim_id)) from None
        return sim

    async def evidence(self, case_id: UUID | str, evidence_id: UUID | str) -> Evidence:
        await self.case(case_id)
        ev = await self._repo("evidence").get(str(evidence_id))
        if ev is None or str(ev.case_id) != str(case_id):
            raise NotFoundError("Evidence", str(evidence_id))
        return ev

    async def agent(self, agent_id: UUID | str) -> AgentDefinition:
        agent = await self._repo("agent").get(str(agent_id))
        if agent is None:
            raise NotFoundError("Agent", str(agent_id))
        try:
            await self.simulation(agent.simulation_id)
        except NotFoundError:
            raise NotFoundError("Agent", str(agent_id)) from None
        return agent
